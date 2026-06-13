"""CLI wrapper: build the pure factor board -> outputs/factors.json.

    python .claude/skills/factor-research/scripts/compute_factors.py --asof 2026-06-05

Thin wrapper over fof.factors.build_factor_board(cfg) with result=None (pure factor board, no FOF
exposure). Look-ahead-safe IC/rolling metrics live in fof.factors — this script adds no logic.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from fof.config import DEFAULT_CONFIG
from fof import factors as factorsmod, report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", default=DEFAULT_CONFIG.asof)
    ap.add_argument("--start", default=DEFAULT_CONFIG.start)
    args = ap.parse_args()
    cfg = replace(DEFAULT_CONFIG, asof=args.asof, start=args.start)

    fac = factorsmod.build_factor_board(cfg)
    report._dump("factors.json", fac)

    rk = (fac.get("ranking") or {}).get("factors") or []
    ic = fac.get("rotation_ic") or {}
    print(json.dumps({"n_factors": fac.get("n_factors"),
                      "top_factor": (rk[0].get("display") if rk else None),
                      "ic_mean": ic.get("ic_mean"), "icir": ic.get("icir"),
                      "hit_rate": ic.get("hit_rate")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
