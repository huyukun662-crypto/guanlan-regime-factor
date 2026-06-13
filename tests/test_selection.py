"""4 铁律 selection tests on synthetic sleeve NAVs."""

import numpy as np
import pandas as pd

from dataclasses import replace
from fof.config import DEFAULT_CONFIG
from fof.selection import select_sleeves


def _make(navs: dict) -> pd.DataFrame:
    idx = pd.bdate_range("2020-01-01", periods=200)
    return pd.DataFrame({k: pd.Series(v, index=idx) for k, v in navs.items()})


def _rising(idx_n, slope):           # smooth up-trend, tiny drawdown
    return list(np.cumprod([1.0] + [1 + slope] * (idx_n - 1)))


def _dip_recover(idx_n):             # >15% drawdown inside the window, but +momentum lately
    pre = list(np.cumprod([1.002] * (idx_n - 50)))       # idx_n-50 elements
    dip = list(pre[-1] * np.cumprod([0.97] * 8))         # ~ -22% drop
    rec = list(dip[-1] * np.cumprod([1.02] * 42))        # recovery -> last-21d momentum > 0
    return pre + dip + rec                               # length == idx_n


def test_winner_passes_and_crashy_blacklisted():
    cfg = replace(DEFAULT_CONFIG, min_pass=1)
    df = _make({"good": _rising(200, 0.002), "dippy": _dip_recover(200),
                "falling": list(np.cumprod([1.0] + [0.999] * 199))})
    asof = df.index[-1]
    res = select_sleeves(df, asof, cfg)
    picks = [s["sleeve"] for s in res["selected"]]
    bl = {b["sleeve"]: b["reason"] for b in res["blacklisted"]}
    assert "good" in picks
    assert "falling" in bl and bl["falling"] == "momentum<=0"   # 铁律1
    assert "dippy" in bl and "max_dd" in bl["dippy"]            # 铁律2 drawdown blacklist


def test_fallback_to_cash_when_too_few_pass():
    cfg = replace(DEFAULT_CONFIG, min_pass=2)
    df = _make({"good": _rising(200, 0.002),
                "falling": list(np.cumprod([1.0] + [0.999] * 199))})
    res = select_sleeves(df, df.index[-1], cfg)
    assert res["fallback_to_cash"] is True and res["selected"] == []


def test_sharpe_ranking_orders_survivors():
    cfg = replace(DEFAULT_CONFIG, min_pass=1, max_holdings=2, calmar_min=0.0)
    steady = _rising(200, 0.0015)                         # near-zero vol -> huge Sharpe
    noise = [0.03 if i % 2 == 0 else -0.03 for i in range(200)]
    choppy = [p * (1 + n) for p, n in zip(steady, noise)]  # same up-trend, high vol -> low Sharpe
    df = _make({"steady": steady, "choppy": choppy})
    res = select_sleeves(df, df.index[-1], cfg)
    assert res["selected"][0]["sleeve"] == "steady"        # low-vol out-ranks on Sharpe (铁律3)
