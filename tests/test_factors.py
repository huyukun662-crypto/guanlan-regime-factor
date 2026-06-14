"""Tests for the factor board: OLS loadings, recent ranking, factor correlation."""

import numpy as np
import pandas as pd

from fof.factors import loadings, recent_ranking, factor_correlation, factor_rotation_ic


def _idx(n):
    return pd.bdate_range("2020-01-01", periods=n)


def test_loadings_recovers_known_betas():
    n = 400
    idx = _idx(n)
    rng = np.random.default_rng(0)
    fa = pd.Series(rng.normal(0, 0.01, n), index=idx)
    fb = pd.Series(rng.normal(0, 0.01, n), index=idx)
    fac = pd.DataFrame({"a": fa, "b": fb})
    target = pd.Series(0.8 * fa.values + 0.3 * fb.values + rng.normal(0, 0.0004, n), index=idx)
    r = loadings(target, fac)
    assert abs(r["betas"]["a"] - 0.8) < 0.05
    assert abs(r["betas"]["b"] - 0.3) < 0.05
    assert r["r2"] is not None and r["r2"] > 0.9


def test_loadings_too_short_is_empty():
    idx = _idx(30)
    fac = pd.DataFrame({"a": pd.Series(np.zeros(30), index=idx)})
    r = loadings(pd.Series(np.zeros(30), index=idx), fac)
    assert r["betas"] == {} and r["r2"] is None


def test_recent_ranking_orders_by_recent_month():
    idx = _idx(120)
    fac = pd.DataFrame({"strong": pd.Series(0.003, index=idx),
                        "weak": pd.Series(-0.002, index=idx)})
    # ranking uses real DISPLAY map; "strong"/"weak" aren't defined factors, but the function
    # still ranks by r_1m and falls back to the key as display.
    rk = recent_ranking(fac)
    assert rk["factors"][0]["key"] == "strong" and rk["factors"][0]["rank"] == 1
    assert rk["factors"][-1]["key"] == "weak"


def test_factor_correlation_diag_and_symmetry():
    n = 200
    idx = _idx(n)
    rng = np.random.default_rng(1)
    fac = pd.DataFrame({"a": rng.normal(0, 0.01, n), "b": rng.normal(0, 0.01, n)}, index=idx)
    c = factor_correlation(fac)
    m = c["matrix"]
    assert abs(m[0][0] - 1.0) < 1e-9 and abs(m[1][1] - 1.0) < 1e-9
    assert abs(m[0][1] - m[1][0]) < 1e-9


def test_factor_rotation_ic_empty_dataframe_returns_null_shape():
    out = factor_rotation_ic(pd.DataFrame())
    assert out["dates"] == []
    assert out["ic"] == []
    assert out["icir"] is None


def test_factor_rotation_ic_range_index_returns_null_shape():
    fac = pd.DataFrame({"momentum": [0.01, -0.02, 0.005], "value": [-0.01, 0.01, 0.0]})
    out = factor_rotation_ic(fac)
    assert out["dates"] == []
    assert out["ic"] == []
    assert out["icir"] is None
