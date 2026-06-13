"""Daily refresh — re-pull Tushare data + recompute the FOF pipeline for *today*.

Run nightly by Windows Task Scheduler (see scripts/setup_schedule.ps1). Reads TUSHARE_TOKEN
from the gitignored .env (never hard-coded, never logged). The running dashboard server picks
up the regenerated outputs/dashboard.json on its next request — no restart needed.
"""

from __future__ import annotations

import datetime
import logging
import sys
import traceback
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fof.config import DEFAULT_CONFIG
from fof import report, sleeves
from fof import data as datamod

logging.basicConfig(level=logging.WARNING,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def main() -> int:
    today = datetime.date.today().strftime("%Y-%m-%d")
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n===== {stamp}  daily refresh  asof={today} =====", flush=True)
    try:
        n = datamod.refresh_tail(sleeves.all_codes(), today)   # pull latest trading day
        print(f"  refresh_tail: {n} codes gained new bars", flush=True)
        cfg = replace(DEFAULT_CONFIG, asof=today)
        dash = report.run_all(cfg, write=True)
        # FOF 已从 run_all 移除；只剩 regime/master/factors
        reg = dash["regime"]
        master = dash.get("master", {}) or {}
        factors = dash.get("factors", {}) or {}
        print(f"OK  风险分={reg['composite_score']} ({reg['band']})  regime={reg['regime_label']} "
              f"敞口={reg['equity_exposure']}", flush=True)
        print(f"    大势研判={master.get('verdict')} (分 {master.get('master_score')})  "
              f"因子={factors.get('n_factors')}", flush=True)
        return 0
    except Exception:                       # noqa: BLE001 — log everything for the scheduler
        print("FAILED:\n" + traceback.format_exc(), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
