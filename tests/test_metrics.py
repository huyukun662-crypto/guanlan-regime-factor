"""Metric-formula tests on known NAV series."""

import numpy as np
import pandas as pd

from fof.metrics import compute_segment, max_drawdown, trailing_stats, monthly_returns


def _nav(values):
    idx = pd.bdate_range("2020-01-01", periods=len(values))
    return pd.Series(values, index=idx, dtype=float)


def test_max_drawdown_known():
    nav = _nav([1.0, 1.2, 0.9, 1.1])      # peak 1.2 -> trough 0.9 = -25%
    assert abs(max_drawdown(nav) - (-0.25)) < 1e-9


def test_compute_segment_positive_drift():
    nav = _nav(list(np.cumprod([1.0] + [1.001] * 251)))   # ~1 trading year, +0.1%/day
    m = compute_segment(nav, "y")
    assert m.ann_return > 0.25 and m.max_dd == 0.0
    assert np.isnan(m.calmar)                              # no drawdown -> calmar undefined


def test_compute_segment_too_short_is_nan():
    m = compute_segment(_nav([1.0]), "x")
    assert m.n_days == 0 and np.isnan(m.sharpe)


def test_trailing_stats_lookahead_safe():
    rng = np.random.default_rng(0)
    full = _nav(list(np.cumprod(1 + rng.normal(0, 0.01, 400))))
    asof = full.index[300]
    a = trailing_stats(full, asof, 21, 63)
    b = trailing_stats(full.loc[:asof], asof, 21, 63)      # future bars removed
    assert a is not None and a == b                         # asof stats unchanged by the future


def test_monthly_returns_count():
    nav = _nav(list(np.cumprod([1.0] + [1.0005] * 250)))
    assert len(monthly_returns(nav)) >= 10
