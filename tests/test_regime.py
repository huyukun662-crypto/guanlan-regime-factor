"""Regime radar tests — risk-score mapping, composite renormalization, look-ahead safety."""

import numpy as np
import pandas as pd

from fof.regime import _subscore, subscore_frame, composite_series, band_of, _rsrs_z


def test_subscore_directions():
    # higher RSRS -> lower risk; lower breadth -> higher risk
    assert _subscore("rsrs", 1.0) < _subscore("rsrs", -1.0)
    assert _subscore("breadth", 0.9) < _subscore("breadth", 0.2)
    assert _subscore("vol_z", 2.0) > _subscore("vol_z", -2.0)
    for k in ("rsrs", "ma20_bias", "breadth", "vol_z", "erp"):
        assert 0.0 <= _subscore(k, 0.0) <= 100.0


def test_composite_renormalizes_when_macro_missing():
    idx = pd.bdate_range("2020-01-01", periods=3)
    raw = pd.DataFrame(index=idx)
    for k in ("rsrs", "ma20_bias", "breadth", "vol_z", "yield_curve", "gold_copper", "erp"):
        raw[k] = 50.0 if k in ("rsrs",) else np.nan      # only one indicator present-ish
    # build subscores directly: all present at 40, but drop macro to NaN
    sub = pd.DataFrame(index=idx)
    for k in ("rsrs", "ma20_bias", "breadth", "vol_z"):
        sub[k] = 40.0
    for k in ("yield_curve", "gold_copper", "erp"):
        sub[k] = np.nan
    comp = composite_series(sub)
    assert (abs(comp - 40.0) < 1e-9).all()               # missing cols renormalized away


def test_band_thresholds():
    assert band_of(10) == "低" and band_of(50) == "中高" and band_of(95) == "极端"


def test_display_spec_categories():
    from collections import Counter
    from fof.regime import DISPLAY_SPEC, CATEGORY, CATEGORIES
    keys = [s[0] for s in DISPLAY_SPEC]
    assert all(k in CATEGORY for k in keys)                 # every indicator categorized
    assert set(CATEGORY.values()) <= set(CATEGORIES)
    c = Counter(CATEGORY[k] for k in keys)
    assert c["技术面"] == 4 and c["基本面"] == 6 and c["情绪资金"] == 2


def test_rsrs_lookahead_safe():
    rng = np.random.default_rng(2)
    n = 400
    close = np.cumprod(1 + rng.normal(0, 0.01, n))
    idx = pd.bdate_range("2020-01-01", periods=n)
    ohlcv = pd.DataFrame({"high": close * 1.01, "low": close * 0.99}, index=idx)
    full = _rsrs_z(ohlcv)
    asof = 300
    truncated = _rsrs_z(ohlcv.iloc[: asof + 1])
    a, b = full.iloc[asof], truncated.iloc[asof]
    assert (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-9
