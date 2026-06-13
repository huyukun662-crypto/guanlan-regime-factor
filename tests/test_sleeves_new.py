"""Tests for the new Brain sleeves: alligator_trend + bottom_buyer."""

import numpy as np
import pandas as pd

from fof.sleeves import _alligator_weights, _bottom_buyer_weights

_ALLIGATOR_P = {"jaw": 13, "jaw_sh": 8, "teeth": 8, "teeth_sh": 5, "lips": 5, "lips_sh": 3}
_BOTTOM_P = {"ref": "510300", "hold": "159915", "mdd_win": 750,
             "mdd_thr": 0.20, "pe_pct_thr": 0.10}


def _ohlcv(close: pd.Series) -> pd.DataFrame:
    return pd.DataFrame({"high": close * 1.005, "low": close * 0.995, "close": close},
                        index=close.index)


def test_alligator_holds_in_uptrend():
    idx = pd.bdate_range("2020-01-01", periods=120)
    close = pd.Series(np.linspace(100, 200, 120), index=idx)      # steady uptrend
    w = _alligator_weights(_ohlcv(close), _ALLIGATOR_P)
    assert w["close"].iloc[-1] == 1.0                            # lips>teeth>jaw -> long


def test_alligator_cash_in_downtrend():
    idx = pd.bdate_range("2020-01-01", periods=120)
    close = pd.Series(np.linspace(200, 100, 120), index=idx)      # steady downtrend
    w = _alligator_weights(_ohlcv(close), _ALLIGATOR_P)
    assert w["close"].iloc[-1] == 0.0


def test_bottom_buyer_buys_deep_cheap_dip():
    idx = pd.bdate_range("2019-01-01", periods=800)
    ref = pd.Series(np.concatenate([np.linspace(100, 200, 600),   # rise to 200 peak
                                    np.linspace(200, 150, 200)]),  # -25% from peak
                    index=idx)
    closes = pd.DataFrame({"510300": ref, "159915": ref.copy()})
    cheap = {"pe_pct": pd.Series(0.05, index=idx)}                # PE percentile <= 10%
    expensive = {"pe_pct": pd.Series(0.50, index=idx)}
    assert _bottom_buyer_weights(closes, cheap, _BOTTOM_P)["159915"].iloc[-1] == 1.0
    assert _bottom_buyer_weights(closes, expensive, _BOTTOM_P)["159915"].iloc[-1] == 0.0


def test_bottom_buyer_cash_when_no_drawdown():
    idx = pd.bdate_range("2019-01-01", periods=800)
    ref = pd.Series(np.linspace(100, 300, 800), index=idx)        # only-up, no 20% DD
    closes = pd.DataFrame({"510300": ref, "159915": ref.copy()})
    w = _bottom_buyer_weights(closes, {"pe_pct": pd.Series(0.02, index=idx)}, _BOTTOM_P)
    assert w["159915"].iloc[-1] == 0.0                           # cheap but no dip -> cash
