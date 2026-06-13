"""Tests for strategy-performance tables: selection IC + rolling Sharpe."""

import numpy as np
import pandas as pd

from dataclasses import replace
from fof.config import DEFAULT_CONFIG
from fof.tables import selection_ic, rolling_sharpe


def _navs() -> pd.DataFrame:
    idx = pd.bdate_range("2020-01-01", periods=700)
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        name: pd.Series(np.cumprod(1 + rng.normal(0.0003 * (i + 1), 0.012, 700)), index=idx)
        for i, name in enumerate(["a", "b", "c", "d"])
    })


def test_selection_ic_bounds_and_shape():
    cfg = replace(DEFAULT_CONFIG, mom_lookback=21, eval_window=63)
    ic = selection_ic(_navs(), cfg)
    assert len(ic["dates"]) >= 10
    assert all(v is None or (-1.0 <= v <= 1.0) for v in ic["ic"])
    assert ic["hit_rate"] is None or (0.0 <= ic["hit_rate"] <= 1.0)
    assert "ICIR" not in ic and "icir" in ic           # key spelled lowercase


def test_selection_ic_detects_momentum_persistence():
    # 4 trending sleeves with distinct, persistent drifts -> momentum ranks should
    # positively relate to forward returns -> mean IC clearly > 0.
    idx = pd.bdate_range("2020-01-01", periods=700)
    drifts = [0.0000, 0.0004, 0.0008, 0.0012]
    rng = np.random.default_rng(1)
    navs = pd.DataFrame({
        f"s{i}": pd.Series(np.cumprod(1 + rng.normal(d, 0.004, 700)), index=idx)
        for i, d in enumerate(drifts)
    })
    cfg = replace(DEFAULT_CONFIG, mom_lookback=21, eval_window=63)
    ic = selection_ic(navs, cfg)
    assert ic["ic_mean"] is not None and ic["ic_mean"] > 0.2


def test_rolling_sharpe_shape():
    rs = rolling_sharpe(_navs(), window=126)
    assert set(rs["series"].keys()) == {"a", "b", "c", "d"}
    n = len(rs["dates"])
    assert all(len(v) == n for v in rs["series"].values())
