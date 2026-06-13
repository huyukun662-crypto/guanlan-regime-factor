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
        report.write_before_after_md(dash["before_after"], cfg)
        reg, alloc, ba = dash["regime"], dash["fof_allocation"], dash["before_after"]
        picks = ("全仓货基" if alloc["fallback_to_cash"]
                 else ", ".join(f"{s['display']} {int(s['weight'] * 100)}%"
                                for s in alloc["selected_sleeves"]))
        print(f"OK  风险分={reg['composite_score']} ({reg['band']})  regime={reg['regime_label']} "
              f"敞口={reg['equity_exposure']}", flush=True)
        print(f"    配置: {picks} | 货基 {int(alloc['money_market_weight'] * 100)}%", flush=True)
        print(f"    FOF 夏普={ba['treatment']['sharpe']} 卡尔马={ba['treatment']['calmar']} "
              f"最大回撤={ba['treatment']['max_dd']}", flush=True)
        return 0
    except Exception:                       # noqa: BLE001 — log everything for the scheduler
        print("FAILED:\n" + traceback.format_exc(), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
