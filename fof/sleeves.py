"""Sleeve construction — turn real ETF panels into per-sub-strategy NAV series.

Every rule is look-ahead-safe: a weight decided at the close of day t earns the return
over (t, t+1]. `_nav_from_weights` enforces this by shifting weights one day before
applying them to daily returns. Each sleeve's intra-sleeve cash (row weight sum < 1)
earns 0, so a flat sleeve simply stops compounding (never goes negative spuriously).
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .config import SLEEVES, MONEY_MARKET, SleeveDef, FOFConfig
from . import data as datamod

logger = logging.getLogger(__name__)


def _nav_from_weights(weights: pd.DataFrame, closes: pd.DataFrame) -> pd.Series:
    """NAV (start 1.0) from a daily target-weight frame. weights[t] -> return over (t,t+1]."""
    rets = closes.pct_change().reindex(columns=weights.columns)
    applied = weights.shift(1).reindex(rets.index).fillna(0.0)
    port_ret = (applied * rets).sum(axis=1)
    return (1.0 + port_ret).cumprod()


def _momentum_weights(closes: pd.DataFrame, lookback: int, ma_win: int) -> pd.DataFrame:
    """Hold the single ETF with the highest lookback return that is also >= its MA; else cash."""
    mom = closes / closes.shift(lookback) - 1.0
    ma = closes.rolling(ma_win, min_periods=ma_win).mean()
    eligible = mom.where(closes >= ma)
    weights = pd.DataFrame(0.0, index=closes.index, columns=closes.columns)
    # idxmax errors on all-NA rows in pandas 3.0 — only reduce rows with >=1 eligible ETF.
    has_pick = eligible.notna().any(axis=1)
    if has_pick.any():
        choice = eligible.loc[has_pick].idxmax(axis=1)
        for d, code in choice.items():
            weights.at[d, code] = 1.0
    return weights


def _ma_filter_weights(closes: pd.DataFrame, code: str, ma_win: int) -> pd.DataFrame:
    """Single-ETF: fully invested when close >= MA, else cash."""
    ma = closes[code].rolling(ma_win, min_periods=ma_win).mean()
    w = (closes[code] >= ma).astype(float)
    out = pd.DataFrame(0.0, index=closes.index, columns=[code])
    out[code] = w.fillna(0.0)
    return out


def _static_blend_weights(closes: pd.DataFrame, blend: dict[str, float]) -> pd.DataFrame:
    """Fixed-weight blend, continuously rebalanced to target (daily-rebal approximation)."""
    weights = pd.DataFrame(0.0, index=closes.index, columns=list(blend.keys()))
    valid = closes[list(blend.keys())].notna().all(axis=1)
    for code, w in blend.items():
        weights.loc[valid, code] = w
    return weights


def _sar_series(high: pd.Series, low: pd.Series, af_init: float, af_max: float) -> pd.Series:
    """Wilder Parabolic SAR. Look-ahead-safe (each day uses only data up to that day).

    SAR below price -> uptrend (hold); a close crossing below SAR flips to cash.
    Brain: vault/wiki/sources/2026-05-06-jq-sar-indicator-explainer.md
    """
    h, l = high.to_numpy(), low.to_numpy()
    n = len(h)
    sar = np.full(n, np.nan)
    if n < 2:
        return pd.Series(sar, index=high.index)
    up = h[1] >= h[0]
    cur = l[0] if up else h[0]
    ep = h[1] if up else l[1]
    af = af_init
    sar[1] = cur
    for i in range(2, n):
        cur = cur + af * (ep - cur)
        if up:
            cur = min(cur, l[i - 1], l[i - 2])
            if h[i] > ep:
                ep, af = h[i], min(af + af_init, af_max)
            if l[i] < cur:                       # flip to downtrend
                up, cur, ep, af = False, ep, l[i], af_init
        else:
            cur = max(cur, h[i - 1], h[i - 2])
            if l[i] < ep:
                ep, af = l[i], min(af + af_init, af_max)
            if h[i] > cur:                       # flip to uptrend
                up, cur, ep, af = True, ep, h[i], af_init
        sar[i] = cur
    return pd.Series(sar, index=high.index)


def _sar_weights(ohlcv: pd.DataFrame, af_init: float, af_max: float) -> pd.DataFrame:
    """Long (weight 1) when close >= SAR, else cash."""
    sar = _sar_series(ohlcv["high"], ohlcv["low"], af_init, af_max)
    w = (ohlcv["close"] >= sar).astype(float)
    out = pd.DataFrame(0.0, index=ohlcv.index, columns=["close"])
    out["close"] = w.where(sar.notna(), 0.0).fillna(0.0)
    return out


def _style_sri_weights(closes: pd.DataFrame, growth: str, value: str, lookback: int) -> pd.DataFrame:
    """SRI style rotation (ETF-level proxy): hold growth when the growth/value ratio is
    above its own `lookback` trend, else hold value. ETF adaptation of the OpenAlphas SRI
    rule — Brain: 2026-04-23-openalphas-bottom-style-timing.md.
    """
    sri = closes[growth] / closes[value]
    rs = sri / sri.rolling(lookback, min_periods=lookback).mean() - 1.0
    w = pd.DataFrame(0.0, index=closes.index, columns=[growth, value])
    pick_growth = rs > 0
    w.loc[pick_growth & rs.notna(), growth] = 1.0
    w.loc[(~pick_growth) & rs.notna(), value] = 1.0
    return w


def _alligator_weights(ohlcv: pd.DataFrame, p: dict) -> pd.DataFrame:
    """Bill Williams Alligator on median price; long when lips>teeth>jaw, else cash.
    `.shift(+n)` lags each smoothed MA onto the current bar using only past data (no look-ahead)."""
    median = (ohlcv["high"] + ohlcv["low"]) / 2.0
    jaw = median.rolling(p["jaw"], min_periods=p["jaw"]).mean().shift(p["jaw_sh"])
    teeth = median.rolling(p["teeth"], min_periods=p["teeth"]).mean().shift(p["teeth_sh"])
    lips = median.rolling(p["lips"], min_periods=p["lips"]).mean().shift(p["lips_sh"])
    w = ((lips > teeth) & (teeth > jaw)).astype(float)
    out = pd.DataFrame(0.0, index=ohlcv.index, columns=["close"])
    out["close"] = w.fillna(0.0)
    return out


def _bottom_buyer_weights(closes: pd.DataFrame, context: dict | None, p: dict) -> pd.DataFrame:
    """Dual-factor bottom: 3y rolling drawdown >= mdd_thr AND PE percentile <= pe_pct_thr ->
    hold the growth ETF for the rebound, else cash. Look-ahead-safe."""
    ref = closes[p["ref"]]
    mdd = 1.0 - ref / ref.rolling(p["mdd_win"], min_periods=p["mdd_win"] // 2).max()
    pe_pct = (context or {}).get("pe_pct")
    if pe_pct is None:
        pe_pct = pd.Series(np.nan, index=closes.index)
    pe_pct = pe_pct.reindex(closes.index).ffill()
    bottom = (mdd >= p["mdd_thr"]) & (pe_pct <= p["pe_pct_thr"])
    out = pd.DataFrame(0.0, index=closes.index, columns=[p["hold"]])
    out.loc[bottom.fillna(False), p["hold"]] = 1.0
    return out


def build_sleeve_nav(sleeve: SleeveDef, closes: pd.DataFrame,
                     ohlcv: dict[str, pd.DataFrame] | None = None,
                     context: dict | None = None) -> pd.Series:
    """Dispatch a sleeve's rule to a NAV series. `closes` holds the sleeve's adjusted closes;
    `ohlcv` (full OHLCV) is needed for high/low rules (SAR, Alligator); `context` carries
    extra external series (e.g. PE percentile) for rules like bottom_buyer."""
    sub = closes[list(sleeve.codes)].dropna(how="all")
    if sleeve.rule == "momentum":
        w = _momentum_weights(sub, sleeve.params["lookback"], sleeve.params["ma"])
    elif sleeve.rule == "ma_filter":
        w = _ma_filter_weights(sub, sleeve.codes[0], sleeve.params["ma"])
    elif sleeve.rule == "static_blend":
        w = _static_blend_weights(sub, sleeve.params["weights"])
    elif sleeve.rule == "sar":
        bars = (ohlcv or {}).get(sleeve.codes[0])
        if bars is None or bars.empty:
            return pd.Series(dtype=float)
        return _nav_from_weights(_sar_weights(bars, sleeve.params["af_init"],
                                              sleeve.params["af_max"]),
                                 bars[["close"]])
    elif sleeve.rule == "alligator":
        bars = (ohlcv or {}).get(sleeve.codes[0])
        if bars is None or bars.empty:
            return pd.Series(dtype=float)
        return _nav_from_weights(_alligator_weights(bars, sleeve.params), bars[["close"]])
    elif sleeve.rule == "bottom_buyer":
        w = _bottom_buyer_weights(sub, context, sleeve.params)
    elif sleeve.rule == "style_sri":
        w = _style_sri_weights(sub, sleeve.params["growth"], sleeve.params["value"],
                               sleeve.params["lookback"])
    elif sleeve.rule == "cash":
        # money market: NAV = the real 货基 ETF adjusted close, normalized to 1.0.
        s = sub[sleeve.codes[0]].dropna()
        return (s / s.iloc[0]) if len(s) else pd.Series(dtype=float)
    else:
        raise ValueError(f"unknown sleeve rule: {sleeve.rule}")
    return _nav_from_weights(w, sub)


def all_codes() -> list[str]:
    codes: list[str] = []
    for s in (*SLEEVES, MONEY_MARKET):
        for c in s.codes:
            if c not in codes:
                codes.append(c)
    return codes


def build_all_sleeves(cfg: FOFConfig) -> tuple[pd.DataFrame, pd.Series]:
    """Fetch data and build every sleeve NAV. Returns (sleeve_navs, money_market_nav).

    sleeve_navs columns = the 5 equity/defensive sleeve keys; money_market separate.
    Sleeves whose underlying lacks `min_history_days` of data are dropped (with a log).
    """
    ohlcv = datamod.get_ohlcv(all_codes(), cfg.start, cfg.asof)
    cols = {c: df["close"] for c, df in ohlcv.items() if "close" in df.columns}
    closes = pd.DataFrame(cols).sort_index()
    if closes.empty:
        raise RuntimeError("no ETF data fetched — check TUSHARE_TOKEN / network")

    # context for valuation-aware sleeves: rolling PE percentile of 上证50 (fetch extra
    # history so the 750d percentile is well-formed at the start of the window).
    pe = datamod.index_pe("000016.SH", "2017-01-01", cfg.asof)
    pe_pct = None
    if pe is not None and len(pe):
        pe_pct = pe.rolling(750, min_periods=120).apply(
            lambda x: float((x <= x[-1]).mean()), raw=True).reindex(closes.index).ffill()
    context = {"pe_pct": pe_pct}

    navs: dict[str, pd.Series] = {}
    for sleeve in SLEEVES:
        have = [c for c in sleeve.codes if c in closes.columns
                and closes[c].dropna().shape[0] >= cfg.min_history_days]
        if not have:
            logger.warning("sleeve %s dropped — insufficient history for %s",
                           sleeve.name, sleeve.codes)
            continue
        nav = build_sleeve_nav(sleeve, closes, ohlcv, context).dropna()
        if len(nav) >= cfg.min_history_days:
            navs[sleeve.name] = nav

    mm = build_sleeve_nav(MONEY_MARKET, closes, ohlcv, context).dropna()
    sleeve_navs = pd.DataFrame(navs).sort_index()
    return sleeve_navs, mm
