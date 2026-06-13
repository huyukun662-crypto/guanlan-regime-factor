"""Derived tables for the dashboard — correlation, monthly heatmaps, equity curve."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import SLEEVES
from .metrics import monthly_returns, monthly_max_drawdown, trailing_stats

_DISPLAY = {s.name: s.display for s in SLEEVES}


def selection_ic(sleeve_navs: pd.DataFrame, cfg) -> dict:
    """Monthly Information Coefficient of the FOF selection signal (momentum).

    At each month-end t: rank each sleeve by its look-ahead-safe trailing momentum (signal),
    Spearman-correlate with each sleeve's *next-month* realized return. A positive IC means
    the 铁律1 momentum signal actually predicts next month's winners. ICIR = mean(IC)/std(IC).
    """
    navs = sleeve_navs.dropna(how="all")
    m = navs.resample("ME").last()
    fwd = m.pct_change().shift(-1)                       # next-month return per sleeve
    ic_idx, ic_val = [], []
    for t in m.index:
        sig = {}
        for s in navs.columns:
            st = trailing_stats(navs[s], t, cfg.mom_lookback, cfg.eval_window)
            if st is not None:
                sig[s] = st["mom"]
        fr = fwd.loc[t].dropna()
        common = [s for s in sig if s in fr.index]
        if len(common) >= 3:
            sv = pd.Series({s: sig[s] for s in common})
            ic = sv.rank().corr(fr[common].rank())      # Spearman = Pearson of ranks
            if pd.notna(ic):
                ic_idx.append(t)
                ic_val.append(float(ic))
    ic = pd.Series(ic_val, index=pd.to_datetime(ic_idx))
    roll = ic.rolling(12, min_periods=6)
    ricir = roll.mean() / roll.std()
    std = ic.std()
    return {
        "signal": "21d momentum (铁律1)",
        "dates": [d.strftime("%Y-%m") for d in ic.index],
        "ic": [round(v, 3) for v in ic],
        "rolling_icir": [None if pd.isna(v) else round(float(v), 3) for v in ricir],
        "icir": round(float(ic.mean() / std), 3) if std and std > 0 else None,
        "ic_mean": round(float(ic.mean()), 3) if len(ic) else None,
        "hit_rate": round(float((ic > 0).mean()), 3) if len(ic) else None,
    }


def rolling_sharpe(sleeve_navs: pd.DataFrame, window: int = 126) -> dict:
    """Per-sleeve rolling annualized Sharpe (window trading days), downsampled to ~weekly."""
    rets = sleeve_navs.dropna(how="all").pct_change()
    mean = rets.rolling(window, min_periods=window // 2).mean()
    std = rets.rolling(window, min_periods=window // 2).std()
    rs = (mean / std * (252 ** 0.5)).iloc[::5]
    return {
        "window": window,
        "dates": [d.strftime("%Y-%m-%d") for d in rs.index],
        "labels": {c: _DISPLAY.get(c, c) for c in rs.columns},
        "series": {c: [None if pd.isna(v) else round(float(v), 3) for v in rs[c]]
                   for c in rs.columns},
    }


def correlation(sleeve_navs: pd.DataFrame, window_days: int = 120) -> dict:
    """Pairwise correlation of sleeve daily returns over the trailing window."""
    rets = sleeve_navs.pct_change().dropna(how="all").tail(window_days)
    corr = rets.corr()
    labels = [_DISPLAY.get(c, c) for c in corr.columns]
    matrix = [[None if not np.isfinite(v) else round(float(v), 3) for v in row]
              for row in corr.to_numpy()]
    return {"window_days": window_days, "labels": labels,
            "keys": list(corr.columns), "matrix": matrix}


def monthly_grids(nav: pd.Series) -> dict:
    """Monthly return + monthly max-drawdown grids, keyed year -> month."""
    rets = monthly_returns(nav)
    dds = monthly_max_drawdown(nav)
    returns: dict[str, dict[str, float]] = {}
    drawdown: dict[str, dict[str, float]] = {}
    for ts, v in rets.items():
        returns.setdefault(str(ts.year), {})[f"{ts.month:02d}"] = round(float(v), 4)
    for ts, v in dds.items():
        drawdown.setdefault(str(ts.year), {})[f"{ts.month:02d}"] = round(float(v), 4)
    years = sorted(set(returns) | set(drawdown))
    return {"returns": returns, "max_drawdown": drawdown,
            "rows": years, "cols": [f"{m:02d}" for m in range(1, 13)]}


def regime_spans(labels: pd.Series) -> list[dict]:
    """Contiguous runs of the same regime label, for shading the equity curve."""
    labels = labels.dropna()
    if labels.empty:
        return []
    spans, cur, start = [], str(labels.iloc[0]), labels.index[0]
    prev = labels.index[0]
    for ts, lab in labels.items():
        if str(lab) != cur:
            spans.append({"label": cur, "start": start.strftime("%Y-%m-%d"),
                          "end": prev.strftime("%Y-%m-%d")})
            cur, start = str(lab), ts
        prev = ts
    spans.append({"label": cur, "start": start.strftime("%Y-%m-%d"),
                  "end": prev.strftime("%Y-%m-%d")})
    return spans


def equity_curve(result, benchmark_code: str) -> dict:
    """Aligned NAV series for FOF / baseline / benchmark + regime shading spans."""
    idx = result.nav.index
    base = result.baseline_nav.reindex(idx).ffill()
    bench = result.benchmark_nav.reindex(idx).ffill() if len(result.benchmark_nav) else None
    return {
        "dates": [d.strftime("%Y-%m-%d") for d in idx],
        "fof_nav": [round(float(v), 4) for v in result.nav],
        "baseline_nav": [round(float(v), 4) for v in base],
        "benchmark_nav": ([round(float(v), 4) for v in bench] if bench is not None else []),
        "benchmark_code": benchmark_code,
        "regime_spans": regime_spans(result.labels.reindex(idx).ffill()),
    }
