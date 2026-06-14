"""CLI wrapper: compute the regime snapshot -> outputs/regime.json.

    python .claude/skills/regime-radar/scripts/compute_regime.py --asof 2026-06-05
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
from fof import regime, report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", default=DEFAULT_CONFIG.asof)
    ap.add_argument("--start", default=DEFAULT_CONFIG.start)
    args = ap.parse_args()
    cfg = replace(DEFAULT_CONFIG, asof=args.asof, start=args.start)
    reg = regime.build_regime_json(cfg)
    report._dump("regime.json", reg)
    print(json.dumps({"asof": reg["asof"], "composite_score": reg["composite_score"],
                      "band": reg["band"], "regime_label": reg["regime_label"],
                      "equity_exposure": reg["equity_exposure"],
                      "n_indicators": sum(c["available"] for c in reg["indicators"])},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
