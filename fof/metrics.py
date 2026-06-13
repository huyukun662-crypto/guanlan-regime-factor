"""Performance metrics — ported from ETF6.5 (Sharpe = ann_return/ann_vol, no rf).

`compute_segment` measures a NAV series over a window. `trailing_stats` computes the
selection statistics (recent momentum, period-max-DD, calmar, sharpe) used by the 4 铁律
at a single decision date — strictly from data up to and including that date.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

TRADING_DAYS = 252


@dataclass(frozen=True)
class SegmentMetrics:
    label: str
    n_days: int
    ann_return: float
    ann_vol: float
    sharpe: float
    max_dd: float
    calmar: float
    win_rate: float
    turnover_annual: float

    def to_dict(self) -> dict:
        return asdict(self)


def max_drawdown(nav: pd.Series) -> float:
    """Worst peak-to-trough drawdown of a NAV series (<= 0)."""
    nav = nav.dropna()
    if len(nav) < 2:
        return 0.0
    dd = nav / nav.cummax() - 1.0
    return float(dd.min())


def compute_segment(nav: pd.Series, label: str = "full",
                    turnover_daily: pd.Series | None = None) -> SegmentMetrics:
    """Annualized metrics on a contiguous NAV series."""
    nav = nav.dropna()
    if len(nav) < 2:
        return SegmentMetrics(label, 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan)
    rets = nav.pct_change().dropna()
    n = len(nav)
    years = n / TRADING_DAYS
    total = nav.iloc[-1] / nav.iloc[0] - 1.0
    ann_return = (1.0 + total) ** (1.0 / years) - 1.0 if years > 0 else np.nan
    ann_vol = float(rets.std() * np.sqrt(TRADING_DAYS))
    sharpe = ann_return / ann_vol if ann_vol > 0 else np.nan
    mdd = max_drawdown(nav)
    calmar = ann_return / abs(mdd) if mdd < 0 else np.nan
    win = float((rets > 0).mean()) if len(rets) else np.nan
    turn = (float(turnover_daily.dropna().sum() * (TRADING_DAYS / max(n, 1)))
            if turnover_daily is not None else np.nan)
    return SegmentMetrics(label, n, float(ann_return), ann_vol, float(sharpe),
                          mdd, float(calmar) if not np.isnan(calmar) else np.nan,
                          win, turn)


def trailing_stats(nav: pd.Series, asof: pd.Timestamp, mom_lookback: int,
                   eval_window: int) -> dict | None:
    """Selection stats for one sleeve at `asof` — uses only nav.loc[:asof] (no look-ahead).

    Returns mom (recent return), period_max_dd (<=0), calmar, sharpe over the eval window.
    None when there is insufficient history.
    """
    s = nav.loc[:asof].dropna()
    if len(s) < max(mom_lookback, eval_window) + 1:
        return None
    mom = float(s.iloc[-1] / s.iloc[-mom_lookback - 1] - 1.0)
    win = s.iloc[-eval_window - 1:]
    rets = win.pct_change().dropna()
    if len(rets) < 2:
        return None
    period_max_dd = max_drawdown(win)
    ann_return = (1.0 + (win.iloc[-1] / win.iloc[0] - 1.0)) ** (TRADING_DAYS / len(rets)) - 1.0
    ann_vol = float(rets.std() * np.sqrt(TRADING_DAYS))
    sharpe = ann_return / ann_vol if ann_vol > 0 else 0.0
    calmar = ann_return / abs(period_max_dd) if period_max_dd < 0 else np.inf
    return {"mom": mom, "period_max_dd": period_max_dd,
            "calmar": float(calmar), "sharpe": float(sharpe)}


def monthly_returns(nav: pd.Series) -> pd.Series:
    """Calendar-month returns from a daily NAV series (period index 'YYYY-MM')."""
    nav = nav.dropna()
    if len(nav) < 2:
        return pd.Series(dtype=float)
    m = nav.resample("ME").last()
    return m.pct_change().dropna()


def monthly_max_drawdown(nav: pd.Series) -> pd.Series:
    """Worst intra-month drawdown for each calendar month."""
    nav = nav.dropna()
    if len(nav) < 2:
        return pd.Series(dtype=float)
    out: dict[pd.Timestamp, float] = {}
    for period, grp in nav.groupby(nav.index.to_period("M")):
        out[period.to_timestamp("M")] = max_drawdown(grp)
    return pd.Series(out).sort_index()
