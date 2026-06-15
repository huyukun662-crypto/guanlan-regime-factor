"""观澜 · 研判简报 — 纯 Python 一站式，不依赖任何 LLM。

把 `guanlan-analyst` agent 的工作流压成确定性命令行：调三个 skill 计算 + 读 vault → 拼一份
Markdown 简报到 stdout（或 -o 写文件）。任何模型/任何工具都能复用——它不要 AI。

    # 用现有 outputs/*.json（不刷新数据，秒级）
    python scripts/guanlan_brief.py

    # 先重算 pipeline 再出简报
    python scripts/guanlan_brief.py --recompute --asof 2026-06-09

    # 写到 docs/latest-brief.md
    python scripts/guanlan_brief.py -o docs/latest-brief.md

    # 省掉顶部「速用指南」（重复/CI 场景）
    python scripts/guanlan_brief.py --no-guide

输出自带 agent 的两条通用行为（与工具无关）：顶部「速用指南」+ 末尾「要打开仪表盘吗？」收尾。
无 TUSHARE_TOKEN 时 --recompute 会失败；其余模式只读 outputs/*.json，纯离线。"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from dataclasses import replace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
OUTPUTS = PROJECT_ROOT / "outputs"

# 这两段把 agent 的「首轮速用指南」+「固定收尾问仪表盘」做成与工具无关的产物：
# 任何 AI 工具 / 纯 CLI / CI 跑这个脚本，输出里都自带它们，不依赖某个工具是否读系统提示。
USAGE_GUIDE = """> 👋 **观澜分析师 · 速用指南** — 研报锚定 → 风险 regime → 大势研判(HMM×效率比×基本面) → 因子研究，产**带溯源**简报（数字全部来自 `outputs/*.json`，绝不编造）。
> **怎么用**：说「跑一遍大势研判，现在该进攻还是防御？」即触发整条链路；也可「只重算因子 / 重建市场仪表盘 / 读当前 regime」。
> **5 个 skill**：`quant-research-retriever`(研报锚定) · `regime-radar`(0–100 风险分) · `regime-verdict`(大势 verdict) · `factor-research`(因子 IC/轮动) · `factor-allocation`(超配/低配建议)。
> **详细说明**：`docs/agent-使用说明.pdf` · `docs/skills-triggers.pdf` · `docs/usage.pdf` · `docs/网页使用展示.pdf`。
"""

DASHBOARD_FOOTER = """
---

👉 **要打开仪表盘看可视化吗？（大势研判 + 因子两页 + AI 顾问）** 运行 `python scripts/open_dashboard.py` → http://127.0.0.1:8000
"""


def _load(name: str) -> dict:
    p = OUTPUTS / name
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _recompute(asof: str | None) -> None:
    from fof.config import DEFAULT_CONFIG
    from fof import report
    cfg = DEFAULT_CONFIG if not asof else replace(DEFAULT_CONFIG, asof=asof)
    report.run_all(cfg, write=True)


def _vault_citations(topics: list[str], top_per_topic: int = 2) -> list[dict]:
    """Run quant-research-retriever for each topic, dedup, keep top N total."""
    try:
        from importlib.util import spec_from_file_location, module_from_spec
        qv = PROJECT_ROOT / ".claude/skills/quant-research-retriever/scripts/query_vault.py"
        spec = spec_from_file_location("query_vault", qv)
        m = module_from_spec(spec)
        spec.loader.exec_module(m)
    except Exception:
        return []
    hits: dict[str, dict] = {}                                       # dedup by path
    for t in topics:
        try:
            out = m.search(m.DEFAULT_VAULT, t, top_per_topic)
            for c in out.get("citations") or []:
                hits.setdefault(c["path"], {**c, "topic": t})
        except Exception:
            continue
    return list(hits.values())[:8]


def _factor_advice() -> dict:
    """Run factor-allocation mapping if master+factors are present."""
    master, factors = _load("master.json"), _load("factors.json")
    if not master or not factors:
        return {}
    try:
        from fof.advice import factor_allocation_advice
        return factor_allocation_advice(master, factors)
    except Exception:
        return {}


def _structure_sections(master: dict, reg: dict) -> str:
    """信号分解(三轴) + 状态结构(后验/转移) + 触发的非中性风险指标 —— 让简报更专业、可追溯。"""
    out: list[str] = []
    axes = master.get("axes") or {}
    if axes:
        rows = [("HMM 姿态", "0.50", axes.get("HMM姿态")),
                ("效率比 ER", "0.20", axes.get("效率比")),
                ("基本面", "0.30", axes.get("基本面"))]
        out.append("## 信号分解（三轴 → 综合分）\n\n| 轴 | 权重 | 得分(0–100) |\n|---|---|---|\n"
                   + "\n".join(f"| {n} | {w} | {v if v is not None else '—'} |" for n, w, v in rows))
    hmm = master.get("hmm") or {}
    if hmm.get("state_name"):
        post = hmm.get("posterior") or {}
        post_str = "、".join(f"{k} {round(v*100)}%" for k, v in
                             sorted(post.items(), key=lambda kv: -kv[1])) if post else "—"
        trans = master.get("transition") or {}
        nxt = ""
        try:
            mat = trans.get("matrix") or {}
            cur = hmm.get("state_name")
            row = mat.get(cur) if isinstance(mat, dict) else None    # matrix[from][to] = prob
            if isinstance(row, dict) and row:
                self_p = row.get(cur, 0.0)
                others = {k: v for k, v in row.items() if k != cur}
                if others:
                    nx = max(others, key=others.get)
                    nxt = (f"\n- **月度转移**（{trans.get('horizon','月度')[:2]}）：自留 "
                           f"{round(self_p*100)}%；最可能转向 **{nx}** {round(others[nx]*100)}%")
        except Exception:
            nxt = ""
        out.append(f"## 状态结构（HMM · walk-forward 样本外）\n"
                   f"- **当前态**：{hmm.get('state_name')}（已持续 {master.get('streak_days','—')} 交易日）\n"
                   f"- **后验分布**：{post_str}{nxt}")
    inds = [d for d in (reg.get("indicators") or [])
            if d.get("available") and d.get("tag") and d.get("tag") != "中性"]
    if inds:
        lines = "\n".join(f"- **{d.get('name')}** = {d.get('value')} → {d.get('tag')}"
                          f"（{d.get('rule', '')}）" for d in inds[:3])
        out.append(f"## 触发信号（非中性指标 · top {min(3, len(inds))}）\n{lines}")
    return ("\n\n".join(out) + "\n\n") if out else ""


def build_brief(asof: str | None = None, show_guide: bool = True) -> str:
    reg = _load("regime.json")
    master = _load("master.json")
    factors = _load("factors.json")
    if not (reg or master or factors):
        return ("# 观澜 · 研判简报\n\n_未找到 outputs/*.json — 先跑_ "
                "`python scripts/run_pipeline.py` _或加_ `--recompute` _参数_。"
                + DASHBOARD_FOOTER)

    advice = _factor_advice()
    asof_disp = asof or master.get("asof") or reg.get("asof") or "—"
    verdict = master.get("verdict") or "—"
    score = master.get("master_score") or "—"
    conf = master.get("confidence") or "—"
    band = reg.get("band") or "—"
    composite = reg.get("composite_score") or "—"
    regime_lbl = reg.get("regime_label") or "—"
    posture = advice.get("posture") or {
        "走强": "进攻", "震荡": "中性", "走弱": "防御"}.get(verdict, "中性")
    ow = "、".join(f["display"] for f in (advice.get("overweight") or []))
    uw = "、".join(f["display"] for f in (advice.get("underweight") or []))
    tilt_mode = advice.get("tilt_mode") or "—"

    ic = (factors.get("rotation_ic") or {})
    ic_line = (f"因子轮动 IC 均值 {ic.get('ic_mean')}, ICIR {ic.get('icir')}, "
               f"胜率 {round((ic.get('hit_rate') or 0)*100)}%"
               if ic else "（无 factors.json）")

    rk = ((factors.get("ranking") or {}).get("factors")) or []
    def _fmt(fs: list) -> str:
        return "、".join(f"{x.get('display','?')}({(x.get('r_1m') or 0):+.1%})" for x in fs) or "—"
    top3 = _fmt(sorted(rk, key=lambda x: -(x.get("r_1m") or 0))[:3]) if rk else "—"
    bot3 = _fmt(sorted(rk, key=lambda x: (x.get("r_1m") or 0))[:3]) if rk else "—"
    struct_md = _structure_sections(master, reg)

    cites = _vault_citations(["HMM regime 状态", "Kaufman efficiency ratio 效率比",
                              "factor momentum 因子动量", "RSRS 择时"])
    def _rel(p: str) -> str:
        try:
            rel = Path(p).resolve().relative_to(PROJECT_ROOT)
            return str(rel).replace("\\", "/")
        except Exception:
            return p
    cites_md = ("\n".join(f"- `{_rel(c['path'])}` — {c.get('title','')}" for c in cites)
                if cites else "_未读到 vault/ — 或检索失败_")

    today = datetime.date.today().strftime("%Y-%m-%d")
    guide = (USAGE_GUIDE + "\n") if show_guide else ""
    return f"""# 观澜 · 研判简报

**asof 数据日：** {asof_disp} ｜ **生成时间：** {today}

{guide}## 大势研判
- **结论**：**{verdict}**（大势分 {score}，置信 {conf}%）
- **风险仪表盘**：{composite}（{band}）｜ regime = `{regime_lbl}`
- **HMM 状态**：{master.get('hmm',{}).get('state_name','—')}（已持续 {master.get('streak_days','—')} 交易日）
- **效率比 ER**：{(master.get('er') or {}).get('value','—')} —— {(master.get('er') or {}).get('tag','—')}

{struct_md}## 因子轮动
- {ic_line}
- **近 1 月居前**：{top3}
- **近 1 月居后**：{bot3}

## 配置建议（research only · 非组合）
- **总仓位姿态**：**{posture}**（{advice.get('equity_hint','—')}）
- **风格 tilt**：{tilt_mode}
- **超配**：{ow or '_（震荡市无主动 tilt）_'}
- **低配**：{uw or '_（震荡市无主动 tilt）_'}

## 研报溯源（来自仓库内置 vault/）
{cites_md}

## 诚实口径
- 因子动量历史很弱（IC≈0.04 / ICIR≈0.09）→ 风格 tilt 只是**弱倾斜**，别据此重仓押注
- 总仓位姿态优先于风格 tilt；防御期 tilt 意义小
- 这是**研究建议**，不是组合 —— 无权重、未回测、未计成本
- 大势历史色带是 walk-forward 样本外；ER 在涨跌停日虚高

> ⚠️ 仅供量化研究参考，不构成投资建议。
{DASHBOARD_FOOTER}"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--output", help="写入文件（默认 stdout）")
    ap.add_argument("--recompute", action="store_true", help="先跑 run_pipeline 再出简报（要 TUSHARE_TOKEN）")
    ap.add_argument("--asof", default=None, help="重算 asof（仅 --recompute 生效）")
    ap.add_argument("--no-guide", action="store_true",
                    help="不输出顶部「速用指南」（如重复/CI 调用时）")
    args = ap.parse_args()
    if args.recompute:
        _recompute(args.asof)
    md = build_brief(args.asof, show_guide=not args.no_guide)
    if args.output:
        Path(args.output).write_text(md, encoding="utf-8")
        print(f"wrote {args.output} ({len(md)} chars)")
    else:
        sys.stdout.write(md)


if __name__ == "__main__":
    main()
