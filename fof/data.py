"""Data layer — Tushare Pro primary (ETF行情 + 真实宏观), parquet cache, efinance fallback.

Security: TUSHARE_TOKEN / ANTHROPIC_API_KEY are read from the environment or a gitignored
`.env`; never hard-coded, never logged. `load_token` errors out if the token is unset.

ETF prices are forward-adjusted (close * adj_factor from `fund_adj`) so dividend-paying
sleeves (e.g. 红利低波) are not understated. All fetches cache to `data/cache/*.parquet`
and fetch only the missing tail on reruns.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)
_OHLCV = ["open", "high", "low", "close", "volume", "amount"]


# --------------------------------------------------------------------------- token
def load_token(name: str = "TUSHARE_TOKEN", required: bool = True) -> str | None:
    """Read a secret from env or the gitignored project `.env`. Never logs the value."""
    tok = os.environ.get(name)
    if not tok:
        env = ROOT / ".env"
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith(name + "="):
                    tok = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not tok and required:
        raise RuntimeError(
            f"{name} is required but was not found. Put it in the gitignored .env "
            f"(copy .env.example) — it is never committed.")
    return tok or None


def _pro():
    import tushare as ts
    return ts.pro_api(load_token())


def ts_code(code: str) -> str:
    """Map a bare 6-digit code to a Tushare ts_code with exchange suffix."""
    if code.startswith(("15", "16", "12", "39", "00")):
        return f"{code}.SZ"
    return f"{code}.SH"          # 5xxxxx funds, 6xxxxx, most SH


# ------------------------------------------------------------------------- ETF OHLCV
def _fetch_fund_daily(pro, code: str, start: str, end: str) -> pd.DataFrame | None:
    """Year-paged unadjusted fund_daily; returns OHLCV indexed by date (or None)."""
    tc = ts_code(code)
    frames = []
    for yr in range(int(start[:4]), int(end[:4]) + 1):
        s, e = f"{yr}0101", f"{yr}1231"
        for attempt in range(3):
            try:
                raw = pro.fund_daily(ts_code=tc, start_date=s, end_date=e)
                if raw is not None and len(raw):
                    frames.append(raw)
                break
            except Exception as ex:  # noqa: BLE001 — tushare raises rate/permission errors
                logger.warning("fund_daily %s %s retry %d: %s", code, yr, attempt + 1, ex)
                time.sleep(1.5 * (attempt + 1))
        time.sleep(0.35)
    if not frames:
        return None
    df = pd.concat(frames, ignore_index=True).rename(columns={"vol": "volume"})
    df["date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
    keep = ["date", *[c for c in _OHLCV if c in df.columns]]
    return (df[keep].sort_values("date").drop_duplicates("date")
            .set_index("date"))


def _fetch_adj_factor(pro, code: str, start: str, end: str) -> pd.Series | None:
    """fund_adj adjustment factor series (or None on permission/empty)."""
    try:
        a = pro.fund_adj(ts_code=ts_code(code), start_date=start.replace("-", ""),
                         end_date=end.replace("-", ""))
    except Exception as ex:  # noqa: BLE001
        logger.warning("fund_adj %s unavailable (%s) — using raw prices", code, ex)
        return None
    if a is None or not len(a):
        return None
    a = a.copy()
    a["date"] = pd.to_datetime(a["trade_date"], format="%Y%m%d")
    return a.set_index("date")["adj_factor"].sort_index()


def _adjust(ohlcv: pd.DataFrame, factor: pd.Series | None) -> pd.DataFrame:
    """Forward-adjust OHLC by adj_factor (consistent multiplicative scaling for returns)."""
    if factor is None:
        return ohlcv
    f = factor.reindex(ohlcv.index).ffill().bfill()
    out = ohlcv.copy()
    for col in ("open", "high", "low", "close"):
        if col in out.columns:
            out[col] = out[col] * f
    return out


def _fetch_one(pro, code: str, start: str, end: str) -> pd.DataFrame | None:
    raw = _fetch_fund_daily(pro, code, start.replace("-", ""), end.replace("-", ""))
    if raw is None:
        return _efinance_fallback(code, start, end)
    return _adjust(raw, _fetch_adj_factor(pro, code, start, end))


def _efinance_fallback(code: str, start: str, end: str) -> pd.DataFrame | None:
    """Last resort when a Tushare ETF is rate-limited/forbidden (no token needed)."""
    try:
        import efinance as ef
        df = ef.stock.get_quote_history(code, beg=start.replace("-", ""),
                                        end=end.replace("-", ""))
    except Exception as ex:  # noqa: BLE001
        logger.warning("efinance fallback failed for %s: %s", code, ex)
        return None
    if df is None or not len(df):
        return None
    df = df.rename(columns={"日期": "date", "开盘": "open", "最高": "high",
                            "最低": "low", "收盘": "close", "成交量": "volume",
                            "成交额": "amount"})
    df["date"] = pd.to_datetime(df["date"])
    cols = ["date", *[c for c in _OHLCV if c in df.columns]]
    return df[cols].sort_values("date").set_index("date")


def get_ohlcv(codes: list[str], start: str, end: str,
              refresh: bool = False) -> dict[str, pd.DataFrame]:
    """Adjusted OHLCV per code, cached to parquet; fetches only the missing tail."""
    pro = None
    out: dict[str, pd.DataFrame] = {}
    for code in codes:
        path = CACHE / f"{code}.parquet"
        cached = None
        if path.exists() and not refresh:
            cached = pd.read_parquet(path)
            cached.index = pd.to_datetime(cached.index)
            covers_end = cached.index.max() >= pd.Timestamp(end) - pd.Timedelta(days=5)
            covers_start = cached.index.min() <= pd.Timestamp(start) + pd.Timedelta(days=7)
            if covers_end and covers_start:               # cache spans [start, end]
                out[code] = cached.loc[:end]
                continue
        # fetch the missing range: tail only if the cache already covers `start`,
        # else the full [start, end] so earlier history is BACK-FILLED (not just appended).
        fetch_start = start
        if (cached is not None and len(cached)
                and cached.index.min() <= pd.Timestamp(start) + pd.Timedelta(days=7)):
            fetch_start = (cached.index.max() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        if pro is None:
            pro = _pro()
        fresh = _fetch_one(pro, code, fetch_start, end)
        if fresh is None and cached is None:
            logger.error("no data for %s (Tushare + efinance both failed)", code)
            continue
        merged = fresh if cached is None else (
            cached.combine_first(fresh).sort_index() if fresh is not None else cached)
        merged = merged[~merged.index.duplicated(keep="last")]
        merged.to_parquet(path)
        out[code] = merged.loc[:end]
    return out


def refresh_tail(codes: list[str], end: str) -> int:
    """Force-fetch the latest bars (cache_max+1 .. end) for each cached ETF and merge.

    Used by the explicit dashboard/daily refresh so it always pulls the newest trading day,
    bypassing get_ohlcv's 5-day stale-tolerance shortcut. Returns the number of codes that
    actually gained new rows. On non-trading days it fetches nothing and is a no-op.
    """
    pro = None
    updated = 0
    for code in codes:
        path = CACHE / f"{code}.parquet"
        if not path.exists():
            continue
        cached = pd.read_parquet(path)
        cached.index = pd.to_datetime(cached.index)
        fetch_start = (cached.index.max() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        if pd.Timestamp(fetch_start) > pd.Timestamp(end):
            continue
        if pro is None:
            pro = _pro()
        fresh = _fetch_one(pro, code, fetch_start, end)
        if fresh is not None and len(fresh):
            merged = cached.combine_first(fresh).sort_index()
            merged = merged[~merged.index.duplicated(keep="last")]
            if len(merged) > len(cached):
                merged.to_parquet(path)
                updated += 1
    return updated


def index_refresh_tail(codes: list[str], end: str) -> int:
    """Force-fetch the latest bars for each cached index parquet (`_idx_<code>.parquet`).

    Like `refresh_tail` for ETFs but for stock indices (000300.SH, 000852.SH, 000985.CSI, …).
    Only fetches [cache_last + 1 day .. end] from `pro.index_daily`, bypassing index_close's
    full-history yearly fetcher — which made the dashboard refresh take 60-120s of API calls
    even when only one new trading day was needed. Returns the number of indices that gained
    new rows. Falls back silently on per-code failure (cache still serves stale).
    """
    pro = None
    updated = 0
    for code in codes:
        path = CACHE / f"_idx_{code.replace('.', '_')}.parquet"
        if not path.exists():        # no cache yet: defer to index_close on next read
            continue
        cached = pd.read_parquet(path)
        cached.index = pd.to_datetime(cached.index)
        fetch_start = (cached.index.max() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        if pd.Timestamp(fetch_start) > pd.Timestamp(end):
            continue
        if pro is None:
            try:
                pro = _pro()
            except Exception:                      # noqa: BLE001 — no token, skip the lot
                return updated
        try:
            raw = pro.index_daily(
                ts_code=code,
                start_date=fetch_start.replace("-", ""),
                end_date=end.replace("-", ""))
        except Exception:                          # noqa: BLE001
            continue
        if raw is None or raw.empty:
            continue
        raw["date"] = pd.to_datetime(raw["trade_date"], format="%Y%m%d")
        fresh = raw.set_index("date")["close"].sort_index().to_frame("v")
        merged = cached.combine_first(fresh).sort_index()
        merged = merged[~merged.index.duplicated(keep="last")]
        if len(merged) > len(cached):
            merged.to_parquet(path)
            updated += 1
    return updated


def close_panel(codes: list[str], start: str, end: str) -> pd.DataFrame:
    """Adjusted-close panel: DatetimeIndex rows, bare-code columns (outer-joined)."""
    data = get_ohlcv(codes, start, end)
    cols = {c: df["close"] for c, df in data.items() if "close" in df.columns}
    return pd.DataFrame(cols).sort_index() if cols else pd.DataFrame()


def open_panel(codes: list[str], start: str, end: str) -> pd.DataFrame:
    data = get_ohlcv(codes, start, end)
    cols = {c: df["open"] for c, df in data.items() if "open" in df.columns}
    return pd.DataFrame(cols).sort_index() if cols else pd.DataFrame()


# ------------------------------------------------------------------------- real macro
_YC_MEMO: dict[tuple, pd.DataFrame | None] = {}    # 进程内 memo：一次 pipeline 只调一次 yc_cb


def _yc_frame(start: str, end: str) -> pd.DataFrame | None:
    """国债收益率曲线（1001.CB）-> DataFrame[spread(10Y-2Y), y10]，缓存 _yc_cb.parquet。

    期限利差与 ERP 的 10Y 腿共用这一份数据/缓存。两个教训已修：
    1) yc_cb 单次调用有行数上限，整段请求只回最近一小段 → 必须按年分页（_yearly）；
    2) 旧逻辑"覆盖写"缓存，刷新时把全历史冲成几行 → 改 combine_first 增量合并。"""
    key = (start, end)
    if key in _YC_MEMO:
        return _YC_MEMO[key]
    path = CACHE / "_yc_cb.parquet"
    old: pd.DataFrame | None = None
    if path.exists():
        try:
            old = pd.read_parquet(path)
            old.index = pd.to_datetime(old.index)
        except Exception:  # noqa: BLE001
            old = None

    # 缓存已含 y10 且覆盖 start → 只补尾；否则全量按年回填
    fetch_start = start
    if old is not None and "y10" in old.columns and len(old):
        covers = old.index.min() <= pd.Timestamp(start) + pd.Timedelta(days=10)
        if covers:
            fetch_start = (old.index.max() - pd.Timedelta(days=7)).strftime("%Y-%m-%d")

    new: pd.DataFrame | None = None
    try:                                   # 主源：Tushare yc_cb（积分接口，token 可能无权限）
        pro = _pro()
        df = _yearly(lambda s, e: pro.yc_cb(ts_code="1001.CB", curve_type="0",
                                            start_date=s, end_date=e),
                     fetch_start, end)
        if df is not None and len(df):
            df = df.copy()
            df["date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
            wide = df.pivot_table(index="date", columns="curve_term", values="yield")
            new = pd.DataFrame({
                "spread": wide.get(10.0) - wide.get(2.0),
                "y10": wide.get(10.0),
            }).dropna(how="all").sort_index()
    except Exception as ex:  # noqa: BLE001
        logger.warning("yc_cb unavailable (%s) — trying akshare fallback", ex)

    if new is None or not len(new):        # 备源：akshare 中债收益率（免费、无 token）
        try:
            import akshare as ak
            df = ak.bond_zh_us_rate(start_date=fetch_start.replace("-", ""))
            df = df.set_index(pd.to_datetime(df["日期"]))
            new = pd.DataFrame({
                "spread": df["中国国债收益率10年"] - df["中国国债收益率2年"],
                "y10": df["中国国债收益率10年"],
            }).dropna(how="all").sort_index().loc[:end]
        except Exception as ex:  # noqa: BLE001
            logger.warning("akshare bond rate unavailable (%s) — falling back to cache", ex)

    out = old
    if new is not None and len(new):
        out = new if (old is None or "y10" not in old.columns) else new.combine_first(old)
        out = out.sort_index()
        out.to_parquet(path)
    _YC_MEMO[key] = out
    return out


def yield_curve_spread(start: str, end: str) -> pd.Series | None:
    """10Y-2Y China treasury spread (pct points) from yc_cb. None if no permission."""
    frame = _yc_frame(start, end)
    if frame is None or "spread" not in frame.columns:
        return None
    s = frame["spread"].dropna()
    return s if len(s) else None


def ten_year_yield(start: str, end: str) -> pd.Series | None:
    """10Y 国债即期收益率（%），ERP 的无风险腿；与期限利差共用缓存。"""
    frame = _yc_frame(start, end)
    if frame is None or "y10" not in frame.columns:
        return None                       # 旧版缓存无 y10 列：下次成功取数后自动补齐
    s = frame["y10"].dropna()
    return s if len(s) else None


def index_earnings_yield(start: str, end: str, index_code: str = "000016.SH") -> pd.Series | None:
    """Earnings yield (1/PE) of a large-cap index from index_dailybasic (上证50 default)."""
    path = CACHE / "_idx_pe.parquet"
    try:
        pro = _pro()
        df = pro.index_dailybasic(ts_code=index_code, start_date=start.replace("-", ""),
                                  end_date=end.replace("-", ""), fields="trade_date,pe_ttm")
        if df is None or not len(df):
            return _cached_series(path)
        df = df.copy()
        df["date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
        ey = (1.0 / df.set_index("date")["pe_ttm"].sort_index()).dropna() * 100.0
        ey.to_frame("ey").to_parquet(path)
        return ey
    except Exception as ex:  # noqa: BLE001
        logger.warning("index_dailybasic unavailable (%s) — ERP indicator dropped", ex)
        return _cached_series(path)


def gold_copper_ratio(start: str, end: str) -> pd.Series | None:
    """Gold/Copper futures price ratio from fut_daily (continuous main). None if blocked."""
    path = CACHE / "_au_cu.parquet"
    try:
        pro = _pro()
        au = _fut_close(pro, "AU.SHF", start, end)
        cu = _fut_close(pro, "CU.SHF", start, end)
        if au is None or cu is None:
            return _cached_series(path)
        ratio = (au / cu).dropna()
        ratio.to_frame("ratio").to_parquet(path)
        return ratio.sort_index()
    except Exception as ex:  # noqa: BLE001
        logger.warning("fut_daily unavailable (%s) — gold/copper indicator dropped", ex)
        return _cached_series(path)


def _fut_close(pro, ts: str, start: str, end: str) -> pd.Series | None:
    df = pro.fut_daily(ts_code=ts, start_date=start.replace("-", ""),
                       end_date=end.replace("-", ""))
    if df is None or not len(df):
        return None
    df = df.copy()
    df["date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
    return df.set_index("date")["close"].sort_index()


def _yearly(call, start: str, end: str) -> pd.DataFrame | None:
    """Year-paged fetch for Tushare endpoints with per-call row caps."""
    frames = []
    for yr in range(int(start[:4]), int(end[:4]) + 1):
        for attempt in range(2):
            try:
                df = call(f"{yr}0101", f"{yr}1231")
                if df is not None and len(df):
                    frames.append(df)
                break
            except Exception as ex:  # noqa: BLE001
                logger.warning("yearly fetch %s retry %d: %s", yr, attempt + 1, ex)
                time.sleep(1.2)
        time.sleep(0.35)
    return pd.concat(frames, ignore_index=True) if frames else None


def margin_total(start: str, end: str) -> pd.Series | None:
    """Total A-share 融资余额 (sum of rzye across exchanges), daily. None if no permission."""
    path = CACHE / "_margin.parquet"
    try:
        pro = _pro()
        raw = _yearly(lambda s, e: pro.margin(start_date=s, end_date=e),
                      start.replace("-", ""), end.replace("-", ""))
        if raw is None:
            return _cached_series(path)
        raw["date"] = pd.to_datetime(raw["trade_date"], format="%Y%m%d")
        s = raw.groupby("date")["rzye"].sum().sort_index()
        s.to_frame("v").to_parquet(path)
        return s
    except Exception as ex:  # noqa: BLE001
        logger.warning("margin unavailable (%s)", ex)
        return _cached_series(path)


def total_turnover(start: str, end: str) -> pd.Series | None:
    """Whole-market daily turnover (SH_MARKET + SZ_MARKET amount, 亿元). None if blocked."""
    path = CACHE / "_turnover.parquet"
    try:
        pro = _pro()
        raw = _yearly(lambda s, e: pro.daily_info(
            start_date=s, end_date=e, fields="trade_date,ts_code,amount"),
            start.replace("-", ""), end.replace("-", ""))
        if raw is None:
            return _cached_series(path)
        raw = raw[raw["ts_code"].isin(["SH_MARKET", "SZ_MARKET"])].copy()
        raw["date"] = pd.to_datetime(raw["trade_date"], format="%Y%m%d")
        s = raw.groupby("date")["amount"].sum().sort_index()
        s.to_frame("v").to_parquet(path)
        return s
    except Exception as ex:  # noqa: BLE001
        logger.warning("daily_info turnover unavailable (%s)", ex)
        return _cached_series(path)


def shibor_1w(start: str, end: str) -> pd.Series | None:
    """1-week Shibor (%), a money-market liquidity gauge. None if blocked."""
    path = CACHE / "_shibor.parquet"
    try:
        pro = _pro()
        raw = _yearly(lambda s, e: pro.shibor(start_date=s, end_date=e),
                      start.replace("-", ""), end.replace("-", ""))
        if raw is None or "1w" not in (raw.columns if raw is not None else []):
            return _cached_series(path)
        raw["date"] = pd.to_datetime(raw["date"], format="%Y%m%d")
        s = raw.set_index("date")["1w"].sort_index().astype(float)
        s.to_frame("v").to_parquet(path)
        return s
    except Exception as ex:  # noqa: BLE001
        logger.warning("shibor unavailable (%s)", ex)
        return _cached_series(path)


_INDEX_STALE_DAYS = 5      # 缓存最后日期距 end 在 5 个**日历日**内视为新鲜，直接读盘


def index_close(code: str, start: str, end: str) -> pd.Series | None:
    """Daily close of a stock index (e.g. 000001.SH 上证, 000905.SH 中证500).

    Cache-first: if the local parquet covers up to within ``_INDEX_STALE_DAYS`` of ``end``,
    return the cached slice without hitting Tushare. Otherwise tail-fetch the missing rows
    (incremental, ~1 API call) instead of re-downloading 6 years yearly (~6 API calls/index).
    """
    path = CACHE / f"_idx_{code.replace('.', '_')}.parquet"
    cached = _cached_series(path)
    end_ts = pd.Timestamp(end)
    if cached is not None and not cached.empty \
            and (end_ts - cached.index.max()).days <= _INDEX_STALE_DAYS:
        return cached.loc[cached.index >= pd.Timestamp(start)]
    try:
        pro = _pro()
    except Exception as ex:                            # noqa: BLE001
        logger.warning("tushare unavailable (%s) → cache %s", ex, code)
        return cached
    # Tail-only fetch when cache exists but lags by more than the stale window.
    if cached is not None and not cached.empty:
        try:
            tail_start = (cached.index.max() + pd.Timedelta(days=1)).strftime("%Y%m%d")
            raw = pro.index_daily(ts_code=code, start_date=tail_start,
                                  end_date=end.replace("-", ""))
            if raw is None or raw.empty:
                return cached.loc[cached.index >= pd.Timestamp(start)]
            raw["date"] = pd.to_datetime(raw["trade_date"], format="%Y%m%d")
            tail = raw.set_index("date")["close"].sort_index()
            merged = cached.combine_first(tail).sort_index()
            merged = merged[~merged.index.duplicated(keep="last")]
            merged.to_frame("v").to_parquet(path)
            return merged.loc[merged.index >= pd.Timestamp(start)]
        except Exception as ex:                        # noqa: BLE001
            logger.warning("index_daily tail %s failed (%s) → cache", code, ex)
            return cached.loc[cached.index >= pd.Timestamp(start)]
    # Cold path (no cache): full yearly back-fill.
    try:
        raw = _yearly(lambda s, e: pro.index_daily(ts_code=code, start_date=s, end_date=e),
                      start.replace("-", ""), end.replace("-", ""))
        if raw is None:
            return cached
        raw["date"] = pd.to_datetime(raw["trade_date"], format="%Y%m%d")
        s = raw.set_index("date")["close"].sort_index()
        s.to_frame("v").to_parquet(path)
        return s
    except Exception as ex:                            # noqa: BLE001
        logger.warning("index_daily %s unavailable (%s)", code, ex)
        return cached


DERIV_LOOKBACK_DAYS = 300        # bound the heavy per-date deriv fetch to a recent window


def _trading_days(end: str, lookback_days: int):
    """Trading-day index over [end-lookback, end] from the cached 沪深300 index."""
    start = (pd.Timestamp(end) - pd.Timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    s = index_close("000300.SH", start, end)
    return list(s.index) if s is not None and not s.empty else []


def futures_ls_ratio(end: str, lookback_days: int = DERIV_LOOKBACK_DAYS) -> pd.Series | None:
    """IF (沪深300股指期货) top-member net-long ratio (多−空)/(多+空), daily.
    Per-date `fut_holding` is heavy, so bounded + parquet-cached + incremental tail."""
    path = CACHE / "_fut_ls.parquet"
    cached = _cached_series(path)
    days = _trading_days(end, lookback_days)
    if not days:
        return cached
    have = set(cached.index) if cached is not None else set()
    todo = [d for d in days if d not in have]
    if not todo:
        return cached
    try:
        pro = _pro()
        mp = pro.fut_mapping(ts_code="IF.CFX", start_date=days[0].strftime("%Y%m%d"),
                             end_date=end.replace("-", ""))
        mp["date"] = pd.to_datetime(mp["trade_date"], format="%Y%m%d")
        main_by = mp.set_index("date")["mapping_ts_code"].str.split(".").str[0]
        vals: dict = {}
        for d in todo:
            main = main_by.get(d)
            if main is None:
                continue
            try:
                fh = pro.fut_holding(trade_date=d.strftime("%Y%m%d"))
            except Exception as ex:  # noqa: BLE001
                logger.warning("fut_holding %s: %s", d.date(), ex); time.sleep(1.0); continue
            rows = fh[fh["symbol"] == main]
            lg, sh = rows["long_hld"].sum(), rows["short_hld"].sum()
            if lg + sh > 0:
                vals[d] = float((lg - sh) / (lg + sh))
            time.sleep(0.2)
        return _merge_series(path, cached, pd.Series(vals))
    except Exception as ex:  # noqa: BLE001
        logger.warning("futures_ls_ratio unavailable (%s)", ex)
        return cached


def option_pcr(end: str, lookback_days: int = DERIV_LOOKBACK_DAYS) -> pd.Series | None:
    """中金所 IO (沪深300指数期权) 成交PCR = put_vol/call_vol, daily.
    ts_codes self-encode call/put (IO...-C-/-P-), so no opt_basic join. Bounded + cached."""
    path = CACHE / "_opt_pcr.parquet"
    cached = _cached_series(path)
    days = _trading_days(end, lookback_days)
    if not days:
        return cached
    have = set(cached.index) if cached is not None else set()
    todo = [d for d in days if d not in have]
    if not todo:
        return cached
    try:
        pro = _pro()
        vals: dict = {}
        for d in todo:
            try:
                od = pro.opt_daily(trade_date=d.strftime("%Y%m%d"), fields="ts_code,vol")
            except Exception as ex:  # noqa: BLE001
                logger.warning("opt_daily %s: %s", d.date(), ex); time.sleep(1.0); continue
            io = od[od["ts_code"].str.startswith("IO")]
            cp = io["ts_code"].str.extract(r"-([CP])-")[0]
            cv = io.loc[cp == "C", "vol"].sum()
            pv = io.loc[cp == "P", "vol"].sum()
            if cv > 0:
                vals[d] = float(pv / cv)
            time.sleep(0.2)
        return _merge_series(path, cached, pd.Series(vals))
    except Exception as ex:  # noqa: BLE001
        logger.warning("option_pcr unavailable (%s)", ex)
        return cached


def _merge_series(path: Path, cached: pd.Series | None, new: pd.Series) -> pd.Series | None:
    if new.empty:
        return cached
    merged = new if cached is None else pd.concat([cached, new]).sort_index()
    merged = merged[~merged.index.duplicated(keep="last")]
    merged.to_frame("v").to_parquet(path)
    return merged


def index_pe(code: str = "000016.SH", start: str = "2018-01-01",
             end: str = "2026-12-31") -> pd.Series | None:
    """Daily PE_ttm of a large-cap index (上证50 default) from index_dailybasic.
    Used by the bottom_buyer sleeve for a valuation-percentile bottom signal."""
    path = CACHE / f"_pe_{code.replace('.', '_')}.parquet"
    try:
        pro = _pro()
        raw = _yearly(lambda s, e: pro.index_dailybasic(
            ts_code=code, start_date=s, end_date=e, fields="trade_date,pe_ttm"),
            start.replace("-", ""), end.replace("-", ""))
        if raw is None or "pe_ttm" not in (raw.columns if raw is not None else []):
            return _cached_series(path)
        raw["date"] = pd.to_datetime(raw["trade_date"], format="%Y%m%d")
        s = raw.set_index("date")["pe_ttm"].sort_index().astype(float).dropna()
        s.to_frame("v").to_parquet(path)
        return s
    except Exception as ex:  # noqa: BLE001
        logger.warning("index_dailybasic PE unavailable (%s)", ex)
        return _cached_series(path)


def _cached_series(path: Path) -> pd.Series | None:
    if path.exists():
        s = pd.read_parquet(path).iloc[:, 0]
        s.index = pd.to_datetime(s.index)
        return s.sort_index()
    return None
