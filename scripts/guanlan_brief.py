"""观澜 · 研判简报 — 纯 Python 一站式，不依赖任何 LLM。

把 `guanlan-analyst` agent 的工作流压成确定性命令行：调三个 skill 计算 + 读 vault → 拼一份
Markdown 简报到 stdout（或 -o 写文件）。任何模型/任何工具都能复用——它不要 AI。

    # 用现有 outputs/*.json（不刷新数据，秒级）
    python scripts/guanlan_brief.py

    # 先重算 pipeline 再出简报
    python scripts/guanlan_brief.py --recompute --asof 2026-06-09

    # 写到 docs/latest-brief.md
    python scripts/guanlan_brief.py -o docs/latest-brief.md

无 TUSHARE_TOKEN 时 --recompute 会失败；其余模式只读 outputs/*.json，纯离线。
"""

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


def build_brief(asof: str | None = None) -> str:
    reg = _load("regime.json")
    master = _load("master.json")
    factors = _load("factors.json")
    if not (reg or master or factors):
        return ("# 观澜 · 研判简报\n\n_未找到 outputs/*.json — 先跑_ "
                "`python scripts/run_pipeline.py` _或加_ `--recompute` _参数_。")

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
    return f"""# 观澜 · 研判简报

**asof 数据日：** {asof_disp} ｜ **生成时间：** {today}

## 大势研判
- **结论**：**{verdict}**（大势分 {score}，置信 {conf}%）
- **风险仪表盘**：{composite}（{band}）｜ regime = `{regime_lbl}`
- **HMM 状态**：{master.get('hmm',{}).get('state_name','—')}（已持续 {master.get('streak_days','—')} 交易日）
- **效率比 ER**：{(master.get('er') or {}).get('value','—')} —— {(master.get('er') or {}).get('tag','—')}

## 因子轮动
{ic_line}

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
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--output", help="写入文件（默认 stdout）")
    ap.add_argument("--recompute", action="store_true", help="先跑 run_pipeline 再出简报（要 TUSHARE_TOKEN）")
    ap.add_argument("--asof", default=None, help="重算 asof（仅 --recompute 生效）")
    args = ap.parse_args()
    if args.recompute:
        _recompute(args.asof)
    md = build_brief(args.asof)
    if args.output:
        Path(args.output).write_text(md, encoding="utf-8")
        print(f"wrote {args.output} ({len(md)} chars)")
    else:
        sys.stdout.write(md)


if __name__ == "__main__":
    main()
