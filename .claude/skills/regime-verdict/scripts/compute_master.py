"""CLI wrapper: compute the 大势研判 snapshot -> outputs/master.json.

    python .claude/skills/regime-verdict/scripts/compute_master.py --asof 2026-06-05

Thin wrapper over fof.master.build_master_json(cfg, regime). Builds the regime snapshot first
(it supplies the fundamental axis), then the master verdict; writes both. Look-ahead safety and
the walk-forward HMM live in fof.master — this script adds no logic of its own.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from fof._compat import ensure_utf8_stdio
ensure_utf8_stdio()

from fof.config import DEFAULT_CONFIG
from fof import regime, master as mastermod, report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", default=DEFAULT_CONFIG.asof)
    ap.add_argument("--start", default=DEFAULT_CONFIG.start)
    args = ap.parse_args()
    cfg = replace(DEFAULT_CONFIG, asof=args.asof, start=args.start)

    reg = regime.build_regime_json(cfg)               # 基本面轴来自 regime 快照
    m = mastermod.build_master_json(cfg, reg)
    report._dump("regime.json", reg)
    report._dump("master.json", m)

    print(json.dumps({"asof": m["asof"], "verdict": m["verdict"],
                      "master_score": m["master_score"], "confidence": m.get("confidence"),
                      "hmm_state": m.get("hmm", {}).get("state_name"),
                      "er": m.get("er"), "unstable": m.get("unstable")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
