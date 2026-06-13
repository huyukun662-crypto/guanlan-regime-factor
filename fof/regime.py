"""Regime radar — real indicators -> 0-100 composite risk score -> regime label.

Indicators come from ETF panels (RSRS, MA20 bias, breadth, vol-Z) and *real macro*
(10Y-2Y curve, gold/copper, ERP) via Tushare. Each is mapped to a 0-100 downside-risk
subscore (higher = more defensive). The composite is a weight-renormalized average over
the indicators that are available — any missing macro series is dropped, never NaN-poisons
the gauge. Everything is look-ahead-safe (only trailing data feeds each day's value).

Grounding (see .claude/skills/regime-radar/references/indicators.md):
  RSRS -> Brain rsrs-market-thermometer; 金铜比/期限利差 -> huatai-stagflation-3stage;
  MA20 bias -> lcm-bias; breadth/MA -> jq-etf-cross-section.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .config import FOFConfig
from . import data as datamod

logger = logging.getLogger(__name__)

EQUITY_UNIVERSE = ["510300", "510500", "159915", "512890", "513100"]

# key, name, weight, direction (how the raw value maps to risk), explain, Brain source
INDICATORS = [
    ("rsrs", "RSRS 右偏标准分", 0.20, "lower=risk",
     "高低价 OLS 斜率的标准分；>0.7 趋势，<-0.5 转弱。",
     "rsrs-market-thermometer"),
    ("ma20_bias", "沪深300 MA20乖离", 0.15, "lower=risk",
     "收盘相对 MA20 的乖离；跌破均线偏防御。", "lcm-bias-indicator"),
    ("breadth", "市场宽度(>MA60占比)", 0.15, "lower=risk",
     "权益 ETF 中站上 MA60 的比例；越低越弱。", "jq-etf-cross-section"),
    ("vol_z", "波动率 Z-Score", 0.15, "higher=risk",
     "20日已实现波动的标准分；飙升预示风险。", "rsrs-market-thermometer"),
    ("yield_curve", "10Y-2Y 国债利差", 0.12, "lower=risk",
     "期限利差；走平/倒挂是衰退与风险信号。", "huatai-stagflation-3stage"),
    ("gold_copper", "金铜比 Z-Score", 0.10, "higher=risk",
     "金铜比标准分；走高=增长担忧/避险。", "huatai-stagflation-3stage"),
    ("erp", "股债性价比 ERP", 0.13, "higher_erp=safe",
     "股票盈利收益率 − 10Y国债；越高股票越便宜。", "huatai-stagflation-3stage"),
]
_WEIGHTS = {k: w for k, _, w, *_ in INDICATORS}

BANDS = {"低": 20, "中低": 40, "中高": 60, "高": 80, "极端": 100}


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return float(min(hi, max(lo, x)))


# --------------------------------------------------------- GuanLan 顶/底 双评分层
# 每个指标给出 (顶部分, 底部分)：顶=过热/见顶风险，底=超跌/见底机会。各 0-100。
def _tb(top: float, bottom: float):
    return (_clamp(top), _clamp(bottom))


def _na(_v):
    return (float("nan"), float("nan"))


_TB = {
    "rsrs":        lambda v: _tb(50 + 45 * v, 50 - 45 * v),         # 高=趋势顶热 / 低=超跌底
    "ma20_bias":   lambda v: _tb(50 + 1200 * v, 50 - 1200 * v),     # 乖离正=顶 / 负=底
    "breadth":     lambda v: _tb((v - 0.4) * 200, (0.6 - v) * 200), # 宽度高=顶 / 低=底
    "vol_z":       lambda v: _tb(50 + 30 * v, 50 - 30 * v),         # 波动飙升=顶热
    "yield_curve": lambda v: _tb(50 - 40 * (v - 0.5), 50 + 40 * (v - 0.5)),  # 走平=顶压 / 陡峭=底支
    "gold_copper": lambda v: _tb(50 - 30 * v, 50 + 30 * v),         # 金铜比低=risk-on顶 / 高=避险底
    "erp":         lambda v: _tb(80 - 15 * v, 15 * v - 10),         # ERP低=贵=顶 / 高=便宜=底
    "margin_z":    lambda v: _tb(50 + 30 * v, 50 - 30 * v),         # 杠杆狂热=顶 / 去杠杆=底
    "turnover_z":  lambda v: _tb(50 + 28 * v, 50 - 28 * v),         # 放量=顶 / 地量=底
    "shibor":      lambda v: _tb(50 + 30 * v, 50 - 30 * v),         # 利率收紧=顶压 / 宽松=底支
    "fut_ls":      lambda v: _tb(50 + 30 * v, 50 - 30 * v),         # 净多比z高=多头拥挤顶 / 极低=空头投降底
    "opt_pcr":     lambda v: _tb(50 + (0.9 - v) * 120, 50 + (v - 0.9) * 120),  # PCR低=看涨过度顶 / 高=恐慌底
}

# key, name, weight, display value column, score column, 数据来源, 计算公式, 评分规则, 说明
DISPLAY_SPEC = [
    ("rsrs", "RSRS 右偏标准分", 0.13, "rsrs", "rsrs", "fix2",
     "沪深300 高低价 OLS 斜率（18日）→ 250日标准化",
     "z>0.7 趋势过热→顶 / z<-0.5 超跌→底",
     "高低价回归斜率标准分；趋势强弱的温度计。", "rsrs-market-thermometer"),
    ("ma20_bias", "沪深300 MA20乖离", 0.10, "ma20_bias", "ma20_bias", "pct1",
     "(收盘 − MA20) / MA20", "乖离 >+3%→顶 / <−3%→底",
     "收盘相对 20 日均线的乖离；过度偏离均值回归。", "lcm-bias-indicator"),
    ("breadth", "市场宽度(>MA60占比)", 0.08, "breadth", "breadth", "pct0",
     "权益 ETF 中 close ≥ MA60 的比例", "宽度>80%→顶热 / <20%→底",
     "站上 60 日线的比例；普涨/普跌的广度。", "jq-etf-cross-section"),
    ("vol_z", "波动率 Z-Score", 0.10, "vol_z", "vol_z", "fix2",
     "20日已实现波动 → 250日标准化", "z>+1.5→顶湍 / 整体偏顶热",
     "实现波动的标准分；湍流飙升是风险前兆。", "rsrs-market-thermometer"),
    ("yield_curve", "10Y-2Y 国债利差", 0.07, "yield_curve", "yield_curve", "fix2",
     "中债 10Y − 2Y 即期收益率（yc_cb）", "利差走平/倒挂→顶压 / 陡峭→底支",
     "期限利差；倒挂预示衰退与权益顶部。", "huatai-stagflation-3stage"),
    ("gold_copper", "金铜比 Z-Score", 0.07, "gold_copper", "gold_copper", "fix2",
     "沪金/沪铜 期货收盘比 → 250日标准化", "金铜比高→避险底 / 低→risk-on顶",
     "金铜比标准分；走高=增长担忧/避险。", "huatai-stagflation-3stage"),
    ("erp", "股债性价比 ERP", 0.11, "erp", "erp", "pct2",
     "上证50 盈利收益率(1/PE) − 10Y国债", "ERP>5%→极便宜底 / <1%→贵顶",
     "股票相对债券的性价比；越高越便宜。", "huatai-stagflation-3stage"),
    ("margin_z", "融资余额20日Z-Score", 0.12, "margin_z", "margin_z", "fix2",
     "两市融资余额(rzye)求和 → 20日标准化", "Z>+1.5→杠杆狂热顶 / <−1.5→去杠杆底",
     "杠杆资金偏离度；放杠杆追涨=顶，去杠杆=底。", "margin(Tushare)"),
    ("turnover_z", "全市场成交Z-Score", 0.08, "turnover_z", "turnover_z", "fix2",
     "沪深两市成交额求和 → 20日标准化", "Z>+1.5→放量过热顶 / <−1.5→地量底",
     "成交额偏离度；天量=顶，地量=底。", "daily_info(Tushare)"),
    ("shibor", "货币流动性(Shibor 1W)", 0.06, "shibor", "shibor_z", "pct2",
     "1周 Shibor 利率 → 120日标准化打分", "利率收紧→顶压 / 宽松→底支",
     "银行间 7 天利率；收紧压制估值，宽松托底。", "shibor(Tushare)"),
    ("fut_ls", "IF期货净多比", 0.06, "fut_ls", "fut_ls_z", "pct1",
     "IF主力 top会员 (多−空)/(多+空) → 120日标准化", "净多比z高→多头拥挤顶 / 极低→空头投降底",
     "股指期货前排会员净持仓方向；机构定价的晴雨表。", "fut_holding(Tushare)"),
    ("opt_pcr", "IO期权PCR", 0.06, "opt_pcr", "opt_pcr", "fix2",
     "中金所IO(沪深300)期权 认沽量/认购量", "PCR<0.8 看涨过度→顶 / >1.2 恐慌买PUT→底",
     "沪深300指数期权成交PCR；大资金对冲与方向情绪。", "opt_daily(Tushare)"),
]
_TB_WEIGHTS = {s[0]: s[2] for s in DISPLAY_SPEC}

# 三栏分类（技术面 / 基本面 / 情绪资金）— 不再把价量技术与宏观估值混在一起。
CATEGORIES = ["技术面", "基本面", "情绪资金"]
CATEGORY = {
    "rsrs": "技术面", "ma20_bias": "技术面", "breadth": "技术面", "vol_z": "技术面",
    "yield_curve": "基本面", "gold_copper": "基本面", "erp": "基本面", "shibor": "基本面",
    "fut_ls": "基本面", "opt_pcr": "基本面",          # 期货净多比 + 期权PCR（用户要求加在基本面）
    "margin_z": "情绪资金", "turnover_z": "情绪资金",
}
_CAT_WEIGHTS = {cat: {k: _TB_WEIGHTS[k] for k in CATEGORY if CATEGORY[k] == cat}
                for cat in CATEGORIES}


def _fmt_value(kind: str, v) -> str:
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "N/A"
    if kind == "pct0":
        return f"{v * 100:.0f}%"
    if kind == "pct1":
        return f"{v * 100:.1f}%" if abs(v) < 1 else f"{v:.1f}"
    if kind == "pct2":                         # erp / shibor are already in percent units
        return f"{v:.2f}%"
    return f"{v:.2f}"


def tag_of(top: float, bottom: float) -> str:
    if not (np.isfinite(top) and np.isfinite(bottom)):
        return "—"
    if top >= 60 and top >= bottom:
        return "顶"
    if bottom >= 60 and bottom > top:
        return "底"
    return "中性"


def topbottom_frames(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    top = pd.DataFrame(index=raw.index)
    bot = pd.DataFrame(index=raw.index)
    for key, *_rest in DISPLAY_SPEC:
        score_key = _rest[3]                       # the score column
        if score_key not in raw:
            continue
        fn = _TB.get(key)
        if fn is None:
            continue

        def _apply(v, _fn=fn):
            return _na(v) if not (isinstance(v, (int, float)) and np.isfinite(v)) else _fn(v)
        pairs = raw[score_key].map(_apply)
        top[key] = pairs.map(lambda p: p[0])
        bot[key] = pairs.map(lambda p: p[1])
    return top, bot


def _wcomposite(frame: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    w = pd.Series(weights)
    cols = [c for c in w.index if c in frame.columns]
    if not cols:
        return pd.Series(np.nan, index=frame.index)
    sw, wt = frame[cols], w[cols]
    weighted = sw.mul(wt, axis=1)
    wsum = sw.notna().mul(wt, axis=1).sum(axis=1)
    return (weighted.sum(axis=1) / wsum.replace(0, np.nan)).clip(0, 100)


def _rsrs_z(ohlcv: pd.DataFrame, n: int = 18, m: int = 250) -> pd.Series:
    """RSRS: rolling OLS slope of high~low over n days, standardized over m days."""
    high, low = ohlcv["high"].to_numpy(), ohlcv["low"].to_numpy()
    slopes = np.full(len(high), np.nan)
    for i in range(n - 1, len(high)):
        x, y = low[i - n + 1:i + 1], high[i - n + 1:i + 1]
        if np.isfinite(x).all() and np.isfinite(y).all() and x.std() > 0:
            slopes[i] = np.polyfit(x, y, 1)[0]
    s = pd.Series(slopes, index=ohlcv.index)
    return (s - s.rolling(m, min_periods=m // 2).mean()) / s.rolling(m, min_periods=m // 2).std()


def compute_raw(cfg: FOFConfig) -> pd.DataFrame:
    """Daily raw indicator values aligned to the benchmark trading calendar."""
    bench = datamod.get_ohlcv([cfg.benchmark], cfg.start, cfg.asof).get(cfg.benchmark)
    if bench is None or bench.empty:
        raise RuntimeError("benchmark OHLCV unavailable for regime radar")
    idx = bench.index
    close = bench["close"]

    raw = pd.DataFrame(index=idx)
    raw["rsrs"] = _rsrs_z(bench)
    raw["ma20_bias"] = close / close.rolling(20, min_periods=20).mean() - 1.0
    raw["vol_z"] = _zscore(close.pct_change().rolling(20).std(), 250)
    raw["_trend_up"] = (close >= close.rolling(200, min_periods=100).mean()).astype(float)
    raw["_close"] = close

    eq = datamod.close_panel(EQUITY_UNIVERSE, cfg.start, cfg.asof)
    above = (eq >= eq.rolling(60, min_periods=60).mean())
    raw["breadth"] = above.mean(axis=1).reindex(idx).ffill()

    raw["yield_curve"] = _reindex_macro(datamod.yield_curve_spread(cfg.start, cfg.asof), idx)
    raw["gold_copper"] = _zscore(
        _reindex_macro(datamod.gold_copper_ratio(cfg.start, cfg.asof), idx), 250)
    ey = _reindex_macro(datamod.index_earnings_yield(cfg.start, cfg.asof), idx)
    teny = _reindex_macro(_ten_year_proxy(cfg, idx), idx)
    raw["erp"] = (ey - teny) if ey is not None and teny is not None else np.nan

    # --- 新增 3 个真实情绪/流动性指标（GuanLan 风格） ---
    raw["margin_z"] = _zscore(
        _reindex_macro(datamod.margin_total(cfg.start, cfg.asof), idx), 20)
    raw["turnover_z"] = _zscore(
        _reindex_macro(datamod.total_turnover(cfg.start, cfg.asof), idx), 20)
    shibor = _reindex_macro(datamod.shibor_1w(cfg.start, cfg.asof), idx)
    raw["shibor"] = shibor if shibor is not None else np.nan
    raw["shibor_z"] = _zscore(shibor, 120)

    # --- 衍生品仓位/情绪（基本面面板，bounded recent window）---
    fut = _reindex_macro(datamod.futures_ls_ratio(cfg.asof), idx)
    raw["fut_ls"] = fut if fut is not None else np.nan
    raw["fut_ls_z"] = _zscore(fut, 120)
    pcr = _reindex_macro(datamod.option_pcr(cfg.asof), idx)
    raw["opt_pcr"] = pcr if pcr is not None else np.nan
    return raw


def _ten_year_proxy(cfg: FOFConfig, idx) -> pd.Series | None:
    """10Y yield level for ERP — 与期限利差共用 data._yc_frame 的缓存/取数。

    旧实现每次裸调 yc_cb（无缓存），限流即失败 → ERP 卡 N/A；现走缓存路径，限流时
    回退到本地 parquet，与 yield_curve 指标同生共死。"""
    return datamod.ten_year_yield(cfg.start, cfg.asof)


def _zscore(s: pd.Series | None, window: int) -> pd.Series | float:
    if s is None:
        return np.nan
    return (s - s.rolling(window, min_periods=window // 2).mean()) / \
           s.rolling(window, min_periods=window // 2).std()


def _reindex_macro(s: pd.Series | None, idx) -> pd.Series | None:
    if s is None or (hasattr(s, "empty") and s.empty):
        return None
    return s.reindex(idx).ffill()


# --------------------------------------------------------------------- risk mapping
def _subscore(key: str, val: float) -> float:
    """Map a raw indicator value to a 0-100 downside-risk subscore (higher = defensive)."""
    if val is None or (isinstance(val, float) and not np.isfinite(val)):
        return np.nan
    if key == "rsrs":
        return _clamp(50 - 40 * val)
    if key == "ma20_bias":
        return _clamp(50 - 1000 * val)
    if key == "breadth":
        return _clamp(100 * (1 - val))
    if key == "vol_z":
        return _clamp(50 + 25 * val)
    if key == "yield_curve":
        return _clamp(60 - 50 * val)
    if key == "gold_copper":
        return _clamp(50 + 30 * val)
    if key == "erp":
        return _clamp(80 - 12 * val)
    return np.nan


def subscore_frame(raw: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=raw.index)
    for key, *_ in INDICATORS:
        out[key] = raw[key].map(lambda v: _subscore(key, v)) if key in raw else np.nan
    return out


def composite_series(sub: pd.DataFrame) -> pd.Series:
    """Weight-renormalized average over available subscores (NaN columns dropped per row)."""
    w = pd.Series(_WEIGHTS)
    sw = sub[w.index]
    weighted = sw.mul(w, axis=1)
    wsum = sw.notna().mul(w, axis=1).sum(axis=1)
    return (weighted.sum(axis=1) / wsum.replace(0, np.nan)).clip(0, 100)


def label_series(raw: pd.DataFrame, comp: pd.Series, gate: dict[str, float]) -> pd.Series:
    """Classify trend / ranging / bear from RSRS + 200D trend + composite risk."""
    rsrs = raw["rsrs"]
    trend_up = raw["_trend_up"] > 0.5
    lab = pd.Series("ranging", index=raw.index)
    lab[(rsrs > 0.7) & trend_up] = "trend"
    lab[(rsrs < -0.5) | (~trend_up & (comp >= 60))] = "bear"
    return lab


def band_of(score: float) -> str:
    for name, hi in BANDS.items():
        if score < hi:
            return name
    return "极端"


def _source_label(ref: str) -> str:
    return ref if "(" in ref else f"vault/wiki/sources/{ref}.md"


def build_regime_json(cfg: FOFConfig) -> dict:
    """Snapshot at cfg.asof: gauge + GuanLan 顶/底 cards + 详解 + score trend."""
    raw = compute_raw(cfg)
    comp = composite_series(subscore_frame(raw))           # downside-risk gauge (drives FOF gate)
    labels = label_series(raw, comp, cfg.regime_gate)
    top_f, bot_f = topbottom_frames(raw)
    top_s = _wcomposite(top_f, _TB_WEIGHTS)
    bot_s = _wcomposite(bot_f, _TB_WEIGHTS)

    asof = raw.index[raw.index <= pd.Timestamp(cfg.asof)][-1]
    score = float(comp.loc[asof]) if np.isfinite(comp.loc[asof]) else 50.0
    label = str(labels.loc[asof])
    exposure = cfg.regime_gate.get(label, 0.6)

    cards = []
    for key, name, weight, vkey, skey, fmt, formula, rule, explain, ref in DISPLAY_SPEC:
        val = raw[vkey].loc[asof] if vkey in raw else np.nan
        t = float(top_f[key].loc[asof]) if key in top_f.columns else np.nan
        b = float(bot_f[key].loc[asof]) if key in bot_f.columns else np.nan
        cards.append({
            "key": key, "name": name, "weight": round(weight, 3),
            "category": CATEGORY.get(key, "其它"),
            "value": _fmt_value(fmt, val), "raw_value": _round(val),
            "top": _round(t, 1), "bottom": _round(b, 1), "tag": tag_of(t, b),
            "available": bool(np.isfinite(t) and np.isfinite(b)),
            "explain": explain, "formula": formula, "rule": rule,
            "source": _source_label(ref),
        })

    # per-category composite 顶/底 scores (each panel scored independently)
    category_scores = {}
    for cat in CATEGORIES:
        ts = _wcomposite(top_f, _CAT_WEIGHTS[cat])
        bs = _wcomposite(bot_f, _CAT_WEIGHTS[cat])
        category_scores[cat] = {
            "top": _round(ts.loc[asof], 1) if asof in ts.index else None,
            "bottom": _round(bs.loc[asof], 1) if asof in bs.index else None,
        }

    return {
        "asof": asof.strftime("%Y-%m-%d"),
        "composite_score": round(score, 1), "band": band_of(score),
        "band_thresholds": BANDS, "regime_label": label,
        "equity_exposure": round(exposure, 2),
        "top_score": _round(top_s.loc[asof], 1) if asof in top_s.index else None,
        "bottom_score": _round(bot_s.loc[asof], 1) if asof in bot_s.index else None,
        "advice_baseline": _baseline_advice(label, score, exposure),
        "category_scores": category_scores,
        "indicators": cards,
        "score_trend": _build_trend(cfg, raw, top_s, bot_s),
    }


def _build_trend(cfg: FOFConfig, raw: pd.DataFrame,
                 top_s: pd.Series, bot_s: pd.Series) -> dict:
    """Daily 顶部分/底部分 series + index lines for the GuanLan 风险走势 chart."""
    idx = raw.index

    def aln(s):
        if s is None or (hasattr(s, "empty") and s.empty):
            return None
        return s.reindex(idx).ffill()

    hs = aln(datamod.close_panel(["510300"], cfg.start, cfg.asof).get("510300"))
    zz = aln(datamod.close_panel(["510500"], cfg.start, cfg.asof).get("510500"))
    sse = aln(datamod.index_close("000001.SH", cfg.start, cfg.asof))

    indices: dict[str, list] = {}
    if hs is not None:
        indices["沪深300"] = [_round(v, 2) for v in hs]
    if zz is not None:
        indices["中证500"] = [_round(v, 2) for v in zz]
    if sse is not None:
        indices["上证指数"] = [_round(v, 2) for v in sse]

    return {
        "dates": [d.strftime("%Y-%m-%d") for d in idx],
        "top": [_round(v, 1) for v in top_s.reindex(idx)],
        "bottom": [_round(v, 1) for v in bot_s.reindex(idx)],
        "indices": indices,
    }


def _baseline_advice(label: str, score: float, exposure: float) -> str:
    pct = int(round(exposure * 100))
    if label == "bear":
        return (f"熊市信号（风险分 {score:.0f}）：权益敞口降至 0%，全仓货基/逆回购防守，"
                f"等 RSRS 与 200日趋势修复再进场。")
    if label == "trend":
        return (f"趋势市（风险分 {score:.0f}）：权益敞口 {pct}%，在过铁律2的低回撤 sleeve 间"
                f"风险平价配置，单sleeve≤50%。")
    return (f"震荡市（风险分 {score:.0f}）：权益敞口 {pct}%，精选 2-3 个低回撤 sleeve 风险平价，"
            f"余下转货基控回撤。")


def _round(v, nd: int = 4):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return None
    return round(float(v), nd)


def regime_labels(cfg: FOFConfig) -> pd.Series:
    """Full daily regime-label series (used by the engine + equity-curve spans).

    Dispatches on cfg.regime_source: "hmm" → 大势研判 HMM×ER (fof/master.py, walk-forward,
    look-ahead-safe); "rule" → the legacy RSRS+200MA label_series. The label interface
    (trend/ranging/bear consumed by cfg.regime_gate) is identical either way, so the engine,
    selection, weights and grid_search are untouched.
    """
    if getattr(cfg, "regime_source", "rule") == "hmm":
        from . import master                       # local import avoids circulars at module load
        return master.hmm_label_series(cfg)
    raw = compute_raw(cfg)
    comp = composite_series(subscore_frame(raw))
    return label_series(raw, comp, cfg.regime_gate)
