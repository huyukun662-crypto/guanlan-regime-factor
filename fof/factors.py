"""Factor board — real A-share style/smart-beta index proxies + FOF/sleeve risk exposure.

Factor returns are built from REAL index long-shorts (no individual-stock cross-section):
market = 沪深300; SMB = 中证1000 − 沪深300; HML = 国证价值 − 国证成长; 低波 = 红利低波 − 沪深300; …
Momentum/Reversal are cross-sectional long-shorts among a pool of real style indices.
Risk exposure = OLS-regress the FOF nav + each sleeve nav on the factor returns -> loadings
(beta) + R². Everything is look-ahead-safe (xsec weights decided at t-1 earn t's return; the
exposure regression is contemporaneous, the standard convention).
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .config import FOFConfig, FACTOR_DEFS, FACTOR_XSEC_POOL, SLEEVES
from .metrics import compute_segment
from . import data as datamod

logger = logging.getLogger(__name__)

_DISP = {d[0]: d[1] for d in FACTOR_DEFS}
_CAT = {d[0]: d[4] for d in FACTOR_DEFS}


def _r(v, nd: int = 4):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return None
    return round(float(v), nd)


def _index_ret(code: str, cfg: FOFConfig) -> pd.Series | None:
    s = datamod.index_close(code, cfg.start, cfg.asof)
    return None if s is None or s.empty else s.pct_change()


def _xsec_factor(cfg: FOFConfig, lookback: int, long_strong: bool) -> pd.Series | None:
    """Cross-sectional long-short among style indices by `lookback`-day return.
    momentum (long_strong=True): long top tercile − short bottom; reversal: the reverse."""
    closes = {}
    for c in FACTOR_XSEC_POOL:
        s = datamod.index_close(c, cfg.start, cfg.asof)
        if s is not None and not s.empty:
            closes[c] = s
    if len(closes) < 4:
        return None
    px = pd.DataFrame(closes).sort_index()
    rets = px.pct_change()
    signal = px / px.shift(lookback) - 1.0           # trailing return (uses data <= t)
    n = px.shape[1]
    k = max(1, n // 3)
    rk = signal.rank(axis=1)                          # 1 = lowest
    top, bot = rk > (n - k), rk <= k
    wlong, wshort = (top, bot) if long_strong else (bot, top)
    wl = wlong.div(wlong.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    ws = wshort.div(wshort.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    return ((wl - ws).shift(1) * rets).sum(axis=1)    # decide close t, earn t+1


def factor_returns(cfg: FOFConfig) -> pd.DataFrame:
    """Daily return per factor (columns = factor keys). Missing indices are dropped."""
    cols: dict[str, pd.Series] = {}
    for key, _disp, long_c, short_c, _cat in FACTOR_DEFS:
        if long_c == "XSEC":
            r = _xsec_factor(cfg, 20 if key == "momentum" else 5, long_strong=(key == "momentum"))
        else:
            rl = _index_ret(long_c, cfg)
            if rl is None:
                logger.warning("factor %s dropped — index %s unavailable", key, long_c)
                continue
            rs = _index_ret(short_c, cfg) if short_c else None
            r = rl if short_c is None else (rl - rs if rs is not None else rl)
        if r is not None:
            cols[key] = r
    return pd.DataFrame(cols).sort_index()


def recent_ranking(fac: pd.DataFrame) -> dict:
    """1M / 3M / YTD cumulative return per factor, ranked by the recent month."""
    if fac.empty:
        return {"asof": None, "factors": []}
    asof = fac.index.max()
    ytd0 = pd.Timestamp(asof.year, 1, 1)
    rows = []
    for key in fac.columns:
        s = fac[key].dropna()

        def cum(window):
            w = s.tail(window)
            return float((1 + w).prod() - 1) if len(w) else None
        ytd = s.loc[s.index >= ytd0]
        rows.append({
            "key": key, "display": _DISP.get(key, key), "category": _CAT.get(key, ""),
            "r_1m": _r(cum(21)), "r_3m": _r(cum(63)),
            "r_ytd": _r(float((1 + ytd).prod() - 1) if len(ytd) else None),
        })
    rows.sort(key=lambda x: (x["r_1m"] is not None, x["r_1m"] if x["r_1m"] is not None else -9),
              reverse=True)
    for i, row in enumerate(rows, 1):
        row["rank"] = i
    return {"asof": asof.strftime("%Y-%m-%d"), "factors": rows}


def loadings(target_ret: pd.Series, fac: pd.DataFrame) -> dict:
    """OLS regress target daily return on factor returns -> betas, annualized alpha, R²."""
    df = pd.concat([target_ret.rename("y"), fac], axis=1).dropna()
    if len(df) < 60 or fac.shape[1] == 0:
        return {"betas": {}, "alpha": None, "r2": None, "n": int(len(df))}
    y = df["y"].to_numpy()
    A = np.column_stack([np.ones(len(y)), df[list(fac.columns)].to_numpy()])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ coef
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else None
    return {
        "betas": {c: _r(float(b)) for c, b in zip(fac.columns, coef[1:])},
        "alpha": _r(float(coef[0]) * 252), "r2": _r(r2), "n": int(len(df)),
    }


def exposure(result, fac: pd.DataFrame) -> dict:
    """Factor loadings for FOF + equal-weight baseline + each sleeve."""
    disp = {s.name: s.display for s in SLEEVES}
    targets = {
        "FOF": loadings(result.nav.pct_change(), fac),
        "等权基准": loadings(result.baseline_nav.pct_change(), fac),
    }
    for col in result.sleeve_navs.columns:
        targets[disp.get(col, col)] = loadings(result.sleeve_navs[col].pct_change(), fac)
    return {"factor_order": list(fac.columns),
            "factor_labels": {k: _DISP.get(k, k) for k in fac.columns},
            "targets": targets}


def factor_correlation(fac: pd.DataFrame, window: int = 120) -> dict:
    rets = fac.dropna(how="all").tail(window)
    corr = rets.corr()
    return {
        "window_days": window,
        "labels": [_DISP.get(c, c) for c in corr.columns],
        "keys": list(corr.columns),
        "matrix": [[None if not np.isfinite(v) else round(float(v), 3) for v in row]
                   for row in corr.to_numpy()],
    }


def cumulative_returns(fac: pd.DataFrame, downsample: int = 3) -> dict:
    """Per-factor cumulative NAV (start 1.0) for the standalone factor page's multi-line chart."""
    nav = (1.0 + fac.fillna(0.0)).cumprod().iloc[::downsample]
    return {
        "dates": [d.strftime("%Y-%m-%d") for d in nav.index],
        "labels": {k: _DISP.get(k, k) for k in nav.columns},
        "series": {k: [round(float(v), 4) for v in nav[k]] for k in nav.columns},
    }


def tearsheet(fac: pd.DataFrame) -> dict:
    """Full-sample stats per factor (ann return / Sharpe / maxDD / vol), ranked by Sharpe."""
    rows = []
    for k in fac.columns:
        nav = (1.0 + fac[k].dropna()).cumprod()
        m = compute_segment(nav, k)
        rows.append({
            "key": k, "display": _DISP.get(k, k), "category": _CAT.get(k, ""),
            "ann": _r(m.ann_return), "sharpe": _r(m.sharpe),
            "maxdd": _r(m.max_dd), "vol": _r(m.ann_vol),
        })
    rows.sort(key=lambda x: (x["sharpe"] is not None, x["sharpe"] if x["sharpe"] is not None else -9),
              reverse=True)
    return {"factors": rows}


def factor_rolling_sharpe(fac: pd.DataFrame, window: int = 126) -> dict:
    """每因子 window 日滚动年化 Sharpe（按 ~周降采样）。看哪个风格因子阶段性强/在轮动。"""
    rets = fac.dropna(how="all")
    mean = rets.rolling(window, min_periods=window // 2).mean()
    std = rets.rolling(window, min_periods=window // 2).std()
    rs = (mean / std * (252 ** 0.5)).iloc[::5]
    return {
        "window": window,
        "dates": [d.strftime("%Y-%m-%d") for d in rs.index],
        "labels": {c: _DISP.get(c, c) for c in rs.columns},
        "series": {c: [None if pd.isna(v) else round(float(v), 3) for v in rs[c]]
                   for c in rs.columns},
    }


def factor_rotation_ic(fac: pd.DataFrame) -> dict:
    """因子轮动月度 IC：每月按当月收益给各因子排名，与次月收益做横截面秩相关。

    注：本看板因子是真实风格指数 long-short 的**收益序列**（无个股横截面），故不是经典的
    个股因子 IC，而是**因子动量/轮动可预测性**——IC>0 说明本月赢家因子下月仍占优（动量有效），
    <0 说明反转。ICIR = mean(IC)/std(IC)，12 月滚动 ICIR 看稳定性。
    """
    m = (1.0 + fac.fillna(0.0)).resample("ME").prod() - 1.0   # 月度因子收益
    fwd = m.shift(-1)                                          # 次月收益
    ic_idx, ic_val = [], []
    for t in m.index:
        sig = m.loc[t].dropna()                               # 当月收益=动量信号
        fr = fwd.loc[t].dropna()
        common = [c for c in sig.index if c in fr.index]
        if len(common) >= 4:
            ic = sig[common].rank().corr(fr[common].rank())   # Spearman
            if pd.notna(ic):
                ic_idx.append(t)
                ic_val.append(float(ic))
    ic = pd.Series(ic_val, index=pd.to_datetime(ic_idx))
    roll = ic.rolling(12, min_periods=6)
    ricir = roll.mean() / roll.std()
    std = ic.std()
    return {
        "signal": "因子动量（当月收益排名 → 次月）",
        "dates": [d.strftime("%Y-%m") for d in ic.index],
        "ic": [round(v, 3) for v in ic],
        "rolling_icir": [None if pd.isna(v) else round(float(v), 3) for v in ricir],
        "icir": round(float(ic.mean() / std), 3) if std and std > 0 else None,
        "ic_mean": round(float(ic.mean()), 3) if len(ic) else None,
        "hit_rate": round(float((ic > 0).mean()), 3) if len(ic) else None,
    }


def build_factor_board(cfg: FOFConfig, result=None) -> dict:
    """纯因子看板。`result`（FOFResult）可选——仅当传入时才加 FOF/sleeve 因子暴露回归；
    仪表板移除 FOF 后默认 None，只输出纯因子部分（排行/累积/全样本/相关性/表现）。"""
    fac = factor_returns(cfg)
    board = {
        "n_factors": int(fac.shape[1]),
        "ranking": recent_ranking(fac),
        "correlation": factor_correlation(fac),
        "cumulative": cumulative_returns(fac),
        "tearsheet": tearsheet(fac),
        "rotation_ic": factor_rotation_ic(fac),
        "rolling_sharpe": factor_rolling_sharpe(fac),
    }
    if result is not None:                         # 仅 FOF 在场时才回归因子暴露
        board["exposure"] = exposure(result, fac)
    return board
