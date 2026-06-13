"""The 4 铁律 — sleeve selection at a decision date (look-ahead-safe).

铁律1  pick by recent ~30-day (mom_lookback) momentum; only sleeves currently making
       money (mom > 0) are candidates.
铁律2  blacklist any candidate whose period max-drawdown is worse than -dd_blacklist OR
       whose calmar < calmar_min; if fewer than `min_pass` survive -> 100% money market.
铁律3  rank survivors by Sharpe (stability over raw return); keep the top `max_holdings`.
铁律4  (weights, in weights.py) inverse-drawdown risk parity, hard cap, money-market rest.
"""

from __future__ import annotations

import pandas as pd

from .config import FOFConfig
from .metrics import trailing_stats


def select_sleeves(sleeve_navs: pd.DataFrame, asof: pd.Timestamp,
                   cfg: FOFConfig) -> dict:
    """Run 铁律 1-3 at `asof`. Returns selected + blacklisted + fallback flag."""
    stats: dict[str, dict] = {}
    blacklisted: list[dict] = []

    for sleeve in sleeve_navs.columns:
        st = trailing_stats(sleeve_navs[sleeve], asof, cfg.mom_lookback, cfg.eval_window)
        if st is None:
            blacklisted.append({"sleeve": sleeve, "reason": "insufficient_history",
                                "period_max_dd": None})
            continue
        stats[sleeve] = st

    survivors: list[str] = []
    for sleeve, st in stats.items():
        if st["mom"] <= 0:                                          # 铁律1
            blacklisted.append({"sleeve": sleeve, "reason": "momentum<=0",
                                "period_max_dd": round(st["period_max_dd"], 4)})
        elif st["period_max_dd"] < -cfg.dd_blacklist:              # 铁律2 drawdown
            blacklisted.append({"sleeve": sleeve,
                                "reason": f"max_dd {st['period_max_dd']:.3f} < -{cfg.dd_blacklist}",
                                "period_max_dd": round(st["period_max_dd"], 4)})
        elif st["calmar"] < cfg.calmar_min:                       # 铁律2 calmar gate
            blacklisted.append({"sleeve": sleeve,
                                "reason": f"calmar {st['calmar']:.2f} < {cfg.calmar_min}",
                                "period_max_dd": round(st["period_max_dd"], 4)})
        else:
            survivors.append(sleeve)

    if len(survivors) < cfg.min_pass:                             # 铁律2 fallback
        return {"selected": [], "blacklisted": blacklisted, "fallback_to_cash": True}

    survivors.sort(key=lambda s: stats[s][cfg.rank_metric], reverse=True)   # 铁律3
    survivors = survivors[: cfg.max_holdings]

    selected = []
    for rank, sleeve in enumerate(survivors, 1):
        st = stats[sleeve]
        selected.append({
            "sleeve": sleeve, "rank": rank,
            "mom_21d": round(st["mom"], 4),
            "period_max_dd": round(st["period_max_dd"], 4),
            "calmar": round(st["calmar"], 3) if st["calmar"] != float("inf") else 999.0,
            "sharpe": round(st["sharpe"], 3),
            "passed_laws": [1, 2, 3, 4],
        })
    return {"selected": selected, "blacklisted": blacklisted, "fallback_to_cash": False}
