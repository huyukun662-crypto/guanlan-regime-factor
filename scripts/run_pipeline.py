"""One-shot FOF research pipeline — stages: data | regime | fof | bundle | report | all.

    python scripts/run_pipeline.py --asof 2026-06-05 --start 2020-01-01
    python scripts/run_pipeline.py --stage regime
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fof.config import DEFAULT_CONFIG
from fof import report, regime as regimemod, engine, sleeves

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")


def _summary(dash: dict) -> None:
    reg, m = dash["regime"], dash["master"]
    print("\n" + "=" * 60)
    print(f"asof {reg['asof']} | 风险分 {reg['composite_score']} ({reg['band']}) | "
          f"regime={reg['regime_label']}")
    print(f"大势研判: {m['verdict']}（大势分 {m['master_score']}）| HMM {m['hmm']['state_name']} | "
          f"ER {m['er']['value']}（{m['er']['tag']}）| 当前状态持续 {m['streak_days']} 交易日")
    print("=" * 60)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all",
                    choices=["data", "regime", "fof", "bundle", "report", "all"])
    ap.add_argument("--asof", default=DEFAULT_CONFIG.asof)
    ap.add_argument("--start", default=DEFAULT_CONFIG.start)
    args = ap.parse_args()
    cfg = replace(DEFAULT_CONFIG, asof=args.asof, start=args.start)

    if args.stage == "data":
        sn, mm = sleeves.build_all_sleeves(cfg)
        regimemod.compute_raw(cfg)
        print(f"[data] cached {sn.shape[1]} sleeves, {sn.shape[0]} rows -> data/cache/")
        return
    if args.stage == "regime":
        reg = regimemod.build_regime_json(cfg)
        report._dump("regime.json", reg)
        print(f"[regime] 风险分 {reg['composite_score']} ({reg['band']}) "
              f"regime={reg['regime_label']} -> outputs/regime.json")
        return
    if args.stage == "report":
        path = report.write_before_after_md()
        print(f"[report] regenerated {path}")
        return

    # bundle / all -> 仪表板装配（大势研判 + 因子看板）。FOF 已从 pipeline 移除（代码留作证据）。
    dash = report.run_all(cfg, write=True)
    print("[bundle] wrote outputs/{regime,master,factors,dashboard}.json")
    _summary(dash)


if __name__ == "__main__":
    main()
