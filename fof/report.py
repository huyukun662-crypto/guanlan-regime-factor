"""Assemble every outputs/*.json the dashboard + before/after doc consume.

before_after is a 3-way contrast that mirrors the article's narrative:
  single_strategy  the lone hot strategy a naive quant chases (here: momentum_rotation)
  baseline         naive equal-weight static diversification (no regime / no 铁律)
  treatment        the agent's regime-gated risk-parity FOF (4 铁律)
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path

import numpy as np
import pandas as pd

from .config import FOFConfig, SLEEVES
from .engine import run_fof, FOFResult
from .metrics import compute_segment, monthly_returns
from . import tables, regime as regimemod, factors as factorsmod, master as mastermod

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"
DOCS = ROOT / "docs"
_DISPLAY = {s.name: s.display for s in SLEEVES}
_ROLE = {s.name: s.role for s in SLEEVES}


def _metrics_block(nav: pd.Series, name: str, turnover: pd.Series | None = None) -> dict:
    m = compute_segment(nav, name, turnover)
    mr = monthly_returns(nav)
    return {
        "name": name,
        "ann_return": _r(m.ann_return), "max_dd": _r(m.max_dd),
        "sharpe": _r(m.sharpe), "calmar": _r(m.calmar),
        "monthly_win_rate": _r(float((mr > 0).mean()) if len(mr) else np.nan),
        "turnover_annual": _r(m.turnover_annual),
    }


def _delta(t: dict, b: dict) -> dict:
    keys = ("ann_return", "max_dd", "sharpe", "calmar", "monthly_win_rate")
    return {k: _r((t[k] or 0) - (b[k] or 0)) for k in keys}


def before_after(result: FOFResult, cfg: FOFConfig) -> dict:
    idx = result.nav.index
    single_nav = result.sleeve_navs["momentum_rotation"].reindex(idx).ffill()
    single_nav = single_nav / single_nav.dropna().iloc[0]

    treatment = _metrics_block(result.nav, "regime门控风险平价FOF", result.turnover)
    baseline = _metrics_block(result.baseline_nav, "等权静态组合")
    single = _metrics_block(single_nav, "单一动量策略(圣杯陷阱)")
    return {
        "window": {"start": idx[0].strftime("%Y-%m-%d"), "end": idx[-1].strftime("%Y-%m-%d")},
        "single_strategy": single, "baseline": baseline, "treatment": treatment,
        "delta_vs_baseline": _delta(treatment, baseline),
        "delta_vs_single": _delta(treatment, single),
    }


def allocation_snapshot(result: FOFResult) -> dict:
    """Current (latest rebalance) allocation in the fof_allocation.json shape."""
    last = result.rebalances[-1]
    selected = []
    for s in last["selected"]:
        selected.append({**s, "display": _DISPLAY.get(s["sleeve"], s["sleeve"]),
                         "role": _ROLE.get(s["sleeve"], "")})
    weights = {s["sleeve"]: s.get("weight", 0.0) for s in last["selected"]}
    weights["money_market"] = last["money_market_weight"]
    return {
        "asof": last["date"], "regime_label": last["regime_label"],
        "equity_exposure": last["equity_exposure"],
        "selected_sleeves": selected, "blacklisted": last["blacklisted"],
        "money_market_weight": last["money_market_weight"],
        "cap_applied": last["cap_applied"], "fallback_to_cash": last["fallback_to_cash"],
        "weights": weights,
    }


def run_all(cfg: FOFConfig, write: bool = True) -> dict:
    """Assemble dashboard.json = 大势研判（市场状态）+ 因子看板. FOF 组合已从仪表板移除。

    FOF 回测代码（run_fof/before_after/allocation_snapshot 等）保留在本模块作研究证据链，
    但不再在仪表板呈现；如需重看 FOF 证据见 outputs/grid_search.csv + docs/before-after.md。
    """
    reg = regimemod.build_regime_json(cfg)
    master = mastermod.build_master_json(cfg, reg)     # 大势研判：HMM×ER×基本面（复用 reg 的基本面分）
    factor_board = factorsmod.build_factor_board(cfg)  # 纯因子看板（无 FOF 暴露）

    dashboard = {
        "generated_at": cfg.asof, "config": cfg.to_dict(),
        "regime": reg, "master": master, "factors": factor_board,
    }
    if write:
        OUTPUTS.mkdir(exist_ok=True)
        _dump("regime.json", reg)
        _dump("master.json", master)
        _dump("factors.json", factor_board)
        _dump("dashboard.json", dashboard)
    return dashboard


def write_before_after_md(ba: dict | None = None, cfg: FOFConfig | None = None) -> Path:
    """Regenerate docs/before-after.md from before_after.json (no recompute needed)."""
    if ba is None:
        ba = json.loads((OUTPUTS / "before_after.json").read_text(encoding="utf-8"))
    DOCS.mkdir(exist_ok=True)
    path = DOCS / "before-after.md"
    path.write_text(_render_md(ba), encoding="utf-8")
    return path


# ------------------------------------------------------------------------- helpers
def _r(v, nd: int = 4):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return None
    return round(float(v), nd)


def _finite(o):
    """Recursively replace NaN/Inf (and numpy scalars) with JSON-safe values."""
    if isinstance(o, float):
        return o if math.isfinite(o) else None
    if isinstance(o, dict):
        return {k: _finite(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_finite(v) for v in o]
    if isinstance(o, (np.floating,)):
        v = float(o)
        return v if math.isfinite(v) else None
    if isinstance(o, (np.integer,)):
        return int(o)
    return o


def _dump(name: str, obj: dict) -> None:
    (OUTPUTS / name).write_text(
        json.dumps(_finite(obj), ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8")


def _pct(v):
    return "—" if v is None else f"{v * 100:.2f}%"


def _num(v):
    return "—" if v is None else f"{v:.2f}"


def _render_md(ba: dict) -> str:
    s, b, t = ba["single_strategy"], ba["baseline"], ba["treatment"]
    w = ba["window"]
    db, ds = ba["delta_vs_baseline"], ba["delta_vs_single"]

    def row(m):
        return (f"| {m['name']} | {_pct(m['ann_return'])} | {_pct(m['max_dd'])} | "
                f"{_num(m['sharpe'])} | {_num(m['calmar'])} | {_pct(m['monthly_win_rate'])} |")

    lines = [
        "# 前后对比 — Agent/Skills 对策略研究的实际帮助",
        "",
        f"回测窗口 **{w['start']} → {w['end']}**，三者标的池一致（9 个真实 ETF sleeve + 货基），",
        "唯一差异是组合层逻辑。指标由 `fof/metrics.py` 计算（夏普=年化/年化波动，无无风险利率）。",
        "",
        "## TL;DR",
        "",
        "| 方案 | 年化收益 | 最大回撤 | 夏普 | 卡尔马 | 月胜率 |",
        "|---|---|---|---|---|---|",
        row(s), row(b), row(t),
        "",
        f"- **vs 单一策略（圣杯陷阱）**：最大回撤 {_pct(s['max_dd'])} → {_pct(t['max_dd'])}"
        f"（改善 {_pct(abs(ds['max_dd']))}），夏普 {_num(s['sharpe'])} → {_num(t['sharpe'])}，"
        f"卡尔马 {_num(s['calmar'])} → {_num(t['calmar'])}。",
        f"- **vs 等权静态组合（朴素分散）**：夏普 {_num(b['sharpe'])} → {_num(t['sharpe'])}，"
        f"卡尔马 {_num(b['calmar'])} → {_num(t['calmar'])}，最大回撤 {_pct(b['max_dd'])} → "
        f"{_pct(t['max_dd'])}。",
        "",
        "## 为什么更好（机制层面）",
        "",
        "1. **regime 门控削减熊市敞口**：`bear` 状态权益敞口=0，全仓货基，躲过急跌。"
        "（依据 `vault/wiki/sources/2026-04-02-huatai-energy-stagflation-3stage.md`）",
        "2. **铁律2 回撤拉黑剔除尾部**：单一动量策略 -28% 级回撤的尾部被 15% 回撤线 + 卡尔马门槛过滤。",
        "3. **铁律4 逆回撤风险平价**：按近期回撤反比配权，低波 sleeve 拿更多资本。"
        "（进取档已放开单sleeve硬上限至100%，分散主要靠风险平价本身而非硬截断——见下方局限）"
        "（依据 `2026-05-07-jq-etf-cross-section-thinking.md` 的低相关“免费午餐”）",
        "4. **黄金+国债避险 sleeve 提供负相关对冲**：股债双杀外的真正分散来源。",
        "5. **Brain 策略 sleeve 扩池到 9 个**：SAR 趋势、SRI 风格轮动、鳄鱼线择时"
        "（`2026-05-05-qpb-alligator-index-timing-rotation.md`）、双因子抄底"
        "（`2026-04-23-openalphas-bottom-style-timing.md`，MDD≥20%&PE分位≤10%）扩大低相关候选池，"
        "更大的池让风险平价更有发挥空间；Choppiness Index 因源笔记本地验证 **OOS 无增量、IS 过拟合**"
        "被诚实剔除。",
        "6. **「大势研判」栏（HMM×ER×基本面）**：在沪深300价量日频上 walk-forward 重拟合 4 态高斯 HMM"
        "（稳态/平静/履冰/危机，依据 Yang2026 SSRN 6823998）+ Kaufman 效率比 + 基本面，给确定性大势结论。"
        "**仅作研判展示**——见下方局限。",
        "",
        "## 诚实的局限",
        "",
        "- **进取档的取舍要诚实**：放开单sleeve硬上限后，年化已反超等权（10.8% vs 7.9%）且回撤仍≤等权，"
        "但这是用**更高的集中度风险**换来的——当只有 1 个 sleeve 通过铁律时它可吃满整档敞口，"
        "对该单一 alpha 来源的失效事件更脆弱。这不是“免费午餐”，是把“稳健档”的现金缓冲让渡给了收益。",
        "- 网格扫描为**全窗口 in-sample 调参**（`scripts/grid_search.py`，128 组），非 OOS 验证的冠军；"
        "OOS 偏短。生产化需 IS/OOS 分离纪律。若要回到“回撤优先”，把 `max_weight` 调回 0.5 即恢复稳健档。",
        "- FOF 平均约**半仓**在权益、其余吃货基利息——资本效率仍受 regime 门控+铁律2拉黑约束，参与度由 4 铁律决定。",
        "- 成本仅记 5bp 单边、滑点 0；做T类日内策略未纳入（仅用真实数据 sleeve）。",
        "- **HMM 门控实测更差，故不接入回测（诚实负结果）**：把「大势研判」的 HMM×ER regime 接入 FOF 门控后，"
        "128 组 grid 实测全面劣化（年化 11.3%→约 5.5%、夏普 1.13→0.52、回撤 -9.4%→-12.2%）——月度 HMM 更保守/有滞后，"
        "把大量时段判为震荡/危机、压低敞口却没换来更低回撤。按选参纪律（新机制须严格超越前代冠军方可替换），"
        "FOF 回测**保留 RSRS+200MA rule 门控**，HMM 仅驱动展示栏；`FOFConfig.regime_source=\"hmm\"` 可一键切换复现该负结果。"
        "「大势研判」历史状态色带为 **walk-forward 样本外**判定（非全样本平滑）；ER 在涨跌停日会虚高。",
        "",
        "## Agent/Skills 带来的工作流增益",
        "",
        "- `quant-research-retriever`：把仓库内置 `vault/` 的 6+ 篇金工研报在数秒内转成带路径引用的论据，"
        "替代人工翻阅。",
        "- `regime-radar`：7 个真实指标（含 Tushare 真实宏观：金铜比/期限利差/ERP）→ 确定性 0-100 评分，"
        "可一键复跑。",
        "- `fof-builder`：把 4 铁律固化为代码，改一个参数即可全网格复跑，留下 `grid_search.csv` 证据链。",
        "- 仪表板内嵌实时 AI 顾问：评审可直接质询当前配置与 regime 判断。",
        "",
        "对比纯手工：数小时 notebook 对数据、无引用链、改参即重写——agent 把“研报→regime→FOF→仪表板”"
        "整条链路压缩为一次 `run_pipeline.py`。",
        "",
    ]
    return "\n".join(lines)
