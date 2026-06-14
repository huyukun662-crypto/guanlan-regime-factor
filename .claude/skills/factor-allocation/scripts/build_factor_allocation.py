"""CLI wrapper: 因子配置建议 —— 读 outputs/master.json + outputs/factors.json -> 配置建议.

    python .claude/skills/factor-allocation/scripts/build_factor_allocation.py

集成：消费 regime-verdict 的 master.json（大势 verdict）+ factor-research 的 factors.json（因子排行/IC），
经 fof.advice.factor_allocation_advice 映射成 总仓位姿态 + 超配/低配风格，写 outputs/factor_allocation.json。
纯读取 + 映射：不构建组合、不回测、不出权重。两份 json 缺失时提示先跑上游 skill 或 run_pipeline。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from fof._compat import ensure_utf8_stdio
ensure_utf8_stdio()

from fof import report                       # noqa: E402  (复用 _dump 的 JSON 安全落盘)
from fof.advice import factor_allocation_advice

OUTPUTS = PROJECT_ROOT / "outputs"


def _load(name: str) -> dict:
    p = OUTPUTS / name
    if not p.exists():
        sys.exit(f"缺 {p.name} —— 先跑 regime-verdict + factor-research（或 "
                 f"`python scripts/run_pipeline.py`）生成 outputs/master.json + factors.json。")
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> None:
    advice = factor_allocation_advice(_load("master.json"), _load("factors.json"))
    report._dump("factor_allocation.json", advice)
    print(json.dumps({
        "asof": advice["asof"], "verdict": advice["verdict"], "posture": advice["posture"],
        "equity_hint": advice["equity_hint"], "tilt_mode": advice["tilt_mode"],
        "overweight": [f["display"] for f in advice["overweight"]],
        "underweight": [f["display"] for f in advice["underweight"]],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
