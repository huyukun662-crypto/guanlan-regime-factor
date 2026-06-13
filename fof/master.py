"""大势研判 — HMM(regime) × ER(Kaufman 效率比) × 基本面 → 综合大势结论 + 引擎门控标签.

Brain 依据：
- HMM：Yang 2026 Anchor-Stabilized Gaussian HMM（SSRN 6823998），4 态 稳态/平静/履冰/危机。
  `vault/wiki/sources/2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes.md`
- ER ：Kaufman 效率比 `ER=|P_t-P_{t-N}|/Σ|ΔP| ∈[0,1]`，`vault/wiki/entities/效率系数.md`

防前视纪律（CLAUDE.md）：HMM **逐月 walk-forward 重拟合** —— 每个月末 m 只用 `features[:m]`
拟合，取 m 当日状态驱动「下一期」门控（收盘决策、次月执行，与引擎 rebalance="M" 一致）。
因此标签序列不含任何未来信息；ER 与特征也只用历史数据。HMM 在指数价量日频上跑（样本足、稳定），
不还原原文 14 因子月度面板（我们样本仅 ~75 个月，高维月度会过拟合）。
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .config import FOFConfig
from . import data as datamod

logger = logging.getLogger(__name__)

# 4 态语义名（Yang 2026）+ 进攻轴(-1 防御 .. +1 进攻) + 历史色带编码。
STATE_NAMES = ["危机", "平静", "履冰", "稳态"]
# 进攻轴（-1 防御 .. +1 进攻）。满标度设计：高置信稳态≈进攻、危机≈防御，
# 避免旧标度(稳态0.6)把大势分压死在 45-60 区间、"进攻/防御"几乎永不触发。
_STATE_OFFENSE = {"危机": -1.0, "平静": 0.0, "履冰": 0.6, "稳态": 1.0}
_STATE_CODE = {"危机": 0, "平静": 1, "履冰": 2, "稳态": 3}

_MIN_FIT = 252            # 不足 1 年历史不信任 HMM → 暖机段标未判定(NaN)
# 黏性阈值：当月多数票状态的平均后验 < thr 时沿用上月状态（regime 持续性先验）。
# temp/diag_sticky.py 实验：thr=0.6 使月度切换 39→20 次且四态语义全部归位
# （危机-10%/平静≈0%低波/履冰+19%反弹/稳态+3%）；thr=0.7 会破坏危机语义，不取。
_STICKY_THR = 0.6
_HMM_CACHE: dict[tuple, pd.DataFrame] = {}
_HMM_EXTRA: dict[tuple, dict] = {}        # 并行缓存：最后一次拟合的命名转移矩阵等

_SOURCES = [
    "vault/wiki/sources/2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes.md",
    "vault/wiki/entities/效率系数.md",
]


def _round(v, nd: int = 4):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return None
    return round(float(v), nd)


# --------------------------------------------------------------- ER (Kaufman)
def er_series(close: pd.Series, n: int = 10) -> pd.Series:
    """考夫曼效率比 ∈ [0,1]；→1 单边趋势，→0 来回震荡。A股涨跌停日会让单日 ER 虚高（已知局限）。"""
    direction = (close - close.shift(n)).abs()
    volatility = close.diff().abs().rolling(n).sum()
    return (direction / volatility.replace(0, np.nan)).clip(0.0, 1.0)


def er_tag(v: float) -> str:
    if v is None or not np.isfinite(v):
        return "—"
    if v >= 0.5:
        return "趋势"
    if v <= 0.3:
        return "震荡"
    return "中性"


# --------------------------------------------------------------- features
_INDEX_DISP = {"000985.CSI": "中证全指", "000985.SH": "中证全指", "000300.SH": "沪深300"}


def index_display(cfg: FOFConfig) -> str:
    return _INDEX_DISP.get(cfg.master_index, cfg.master_index)


def _benchmark_close(cfg: FOFConfig) -> pd.Series:
    """大势研判基底：中证全指（cfg.master_index）；指数取不到时回退 benchmark ETF。"""
    s = datamod.index_close(cfg.master_index, cfg.start, cfg.asof)
    if s is not None and len(s):
        return s.astype(float)
    logger.warning("master_index %s unavailable -> fallback to benchmark ETF", cfg.master_index)
    bench = datamod.get_ohlcv([cfg.benchmark], cfg.start, cfg.asof).get(cfg.benchmark)
    if bench is None or bench.empty:
        raise RuntimeError("master index & benchmark both unavailable for 大势研判 HMM")
    return bench["close"].astype(float)


def _features(close: pd.Series, er_window: int) -> pd.DataFrame:
    """日频 HMM 特征：[对数收益, 20日实现波动, ER]。只用历史，dropna 去暖机段。"""
    logret = np.log(close / close.shift(1))
    vol20 = logret.rolling(20, min_periods=20).std()
    er = er_series(close, er_window)
    return pd.DataFrame({"logret": logret, "vol20": vol20, "er": er}).dropna()


def _month_ends(idx: pd.DatetimeIndex) -> list[pd.Timestamp]:
    s = pd.Series(idx, index=idx)
    return list(s.groupby(idx.to_period("M")).last())


# --------------------------------------------------------------- HMM fit
# 4 态原型坐标（标准化特征空间 [mean logret, mean vol]）——命名 = 全局最优一一指派。
# 序贯贪心（先抢"最低收益=危机"再分剩余）在状态分布交叠时会把高收益低波月份错标"平静"，
# 诊断（temp/diag_hmm_semantics.py）显示其语义错位；原型最近邻 + 匈牙利指派更稳健。
_PROTOTYPES = {
    "危机": (-1.0, 1.0),
    "履冰": (0.3, 1.3),
    "平静": (0.0, -0.7),
    "稳态": (0.7, -0.2),
}


def _name_states(means: np.ndarray) -> dict[int, str]:
    """按状态在 (收益,波动) 平面的位置与 4 原型做全局最优一一指派（匈牙利算法）。"""
    from scipy.optimize import linear_sum_assignment
    ret, vol = means[:, 0], means[:, 1]
    k = len(ret)
    names = list(_PROTOTYPES)
    if k != 4:                                  # 非 4 态退化：仅按收益排名给名
        ranked = sorted(range(k), key=lambda i: ret[i])
        return {raw: names[min(rk, 3)] for rk, raw in enumerate(ranked)}
    cost = np.zeros((4, 4))
    for i in range(4):
        for j, n in enumerate(names):
            pr, pv = _PROTOTYPES[n]
            cost[i, j] = (ret[i] - pr) ** 2 + (vol[i] - pv) ** 2
    rows, cols = linear_sum_assignment(cost)
    return {int(r): names[int(c)] for r, c in zip(rows, cols)}


def _fit_label(window: pd.DataFrame, k: int,
               seed: int) -> tuple[str, dict[str, float], dict[str, dict[str, float]]]:
    """在标准化窗口上拟合高斯 HMM；返回 (当月状态名, 当月平均后验, 命名转移矩阵)。

    当月状态 = 该月内全部交易日解码状态的**多数票**（而非末日单点）——末日快照对
    月末一两天的噪声敏感、跨月易跳变；多数票 + 当月平均后验显著更稳。仍只用 ≤m 数据。"""
    from hmmlearn.hmm import GaussianHMM
    x = window.to_numpy()
    mu, sd = x.mean(0), x.std(0)
    sd[sd == 0] = 1.0
    xs = (x - mu) / sd
    model = GaussianHMM(n_components=k, covariance_type="diag",
                        n_iter=100, tol=1e-3, random_state=seed)
    model.fit(xs)
    states = model.predict(xs)
    name_map = _name_states(model.means_)

    in_month = (window.index.to_period("M") == window.index[-1].to_period("M"))
    m_states = states[np.asarray(in_month)]
    vals, counts = np.unique(m_states, return_counts=True)
    majority = int(vals[int(np.argmax(counts))])

    month_post = model.predict_proba(xs)[np.asarray(in_month)].mean(axis=0)
    named_post = {n: 0.0 for n in STATE_NAMES}
    for raw_i, p in enumerate(month_post):
        named_post[name_map[int(raw_i)]] += float(p)
    # 把 RAW 态序的转移矩阵重排成 STATE_NAMES×STATE_NAMES 命名矩阵
    tm = model.transmat_
    transmat = {a: {b: 0.0 for b in STATE_NAMES} for a in STATE_NAMES}
    for ri in range(len(tm)):
        for rj in range(len(tm)):
            transmat[name_map[int(ri)]][name_map[int(rj)]] = float(tm[ri][rj])
    return name_map[majority], named_post, transmat


def hmm_state_path(cfg: FOFConfig) -> pd.DataFrame:
    """Walk-forward 月度状态路径：每月末用 features[:m] 重拟合 → 状态名 + 4 态后验 + ER。

    防前视：第 m 行只用 ≤m 的数据。结果按 (benchmark,start,asof,states,er_window,seed) 记忆化，
    使 prepare() 与 build_master_json 共享同一次 walk-forward（约 75 次小型拟合）。
    """
    key = (cfg.master_index, cfg.start, cfg.asof, cfg.hmm_states, cfg.er_window, cfg.hmm_seed)
    if key in _HMM_CACHE:
        return _HMM_CACHE[key]
    feat = _features(_benchmark_close(cfg), cfg.er_window)
    rows = []
    last_transmat = None
    prev_state: str | None = None
    for m in _month_ends(feat.index):
        er_m = float(feat["er"].loc[m])
        win = feat.loc[:m]
        if len(win) < _MIN_FIT:
            # 暖机段：历史不足、不信任 HMM → 标"未判定"(NaN)。绝不冒充"平静"——
            # 2020 暖机段实为疫情剧烈波动，假标会污染平静段的语义（诊断脚本证实）。
            rows.append({"date": m, "state": np.nan, "er": er_m,
                         **{n: np.nan for n in STATE_NAMES}})
            continue
        try:
            name, post, transmat = _fit_label(win, cfg.hmm_states, cfg.hmm_seed)
            last_transmat = transmat                     # 保留最后一次（=asof 月末）拟合的转移矩阵
            conf = post.get(name, float("nan"))
            if prev_state is not None and np.isfinite(conf) and conf < _STICKY_THR:
                name = prev_state                        # 置信不足 → 沿用上月（黏性先验）
        except Exception as ex:                          # noqa: BLE001 — degrade, never crash
            logger.warning("HMM fit failed at %s (%s) -> 沿用上月", m.date(), ex)
            name, post = (prev_state or "平静"), {n: np.nan for n in STATE_NAMES}
        rows.append({"date": m, "state": name, "er": er_m, **post})
        prev_state = name
    path = pd.DataFrame(rows).set_index("date")
    _HMM_CACHE[key] = path
    _HMM_EXTRA[key] = {"transmat": last_transmat}
    return path


def _extra(cfg: FOFConfig) -> dict:
    """大势研判附属产物（命名转移矩阵等）——必须在 hmm_state_path 之后调用。"""
    key = (cfg.master_index, cfg.start, cfg.asof, cfg.hmm_states, cfg.er_window, cfg.hmm_seed)
    return _HMM_EXTRA.get(key, {})


# --------------------------------------------------------------- engine gate
def _state_to_label(state: str, er: float, er_thr: float = 0.5) -> str:
    """4 态 × ER → 引擎现有 3 标签 trend/ranging/bear（接口不变、grid 可比）。"""
    if state == "危机":
        return "bear"
    trend_ok = np.isfinite(er) and er >= er_thr          # ER 确认趋势，否则降级为震荡
    if state == "稳态":
        return "trend" if trend_ok else "ranging"
    if state == "履冰":
        return "trend" if trend_ok else "ranging"
    return "ranging"                                     # 平静


def hmm_label_series(cfg: FOFConfig) -> pd.Series:
    """日频 regime 标签（trend/ranging/bear），供引擎门控。

    注意对齐方向：门控必须 **前向 ffill**（m 月末判定 → m+1 月执行，防前视）；
    与之相对，可视化色带用 **同期对齐**（_contemp_state：m 月末模型回看判定 m 月自身，
    nowcast 合法、无前视）。两者用途不同，勿混用。暖机段(NaN)按 "ranging" 兜底。"""
    path = hmm_state_path(cfg)
    monthly = pd.Series(
        [_state_to_label(str(r.state), float(r.er)) if isinstance(r.state, str) else "ranging"
         for r in path.itertuples()],
        index=path.index)
    close = _benchmark_close(cfg)
    return monthly.reindex(close.index, method="ffill").fillna("ranging")


def _contemp_state(path: pd.DataFrame, daily_index: pd.DatetimeIndex,
                   col: str = "state") -> pd.Series:
    """同期对齐（nowcast）：m 月末的判定标给 m 月自身的交易日。供色带/统计用，非门控。"""
    by_month = pd.Series(path[col].values, index=path.index.to_period("M"))
    return pd.Series(daily_index.to_period("M"), index=daily_index).map(by_month)


# --------------------------------------------------------------- master verdict
def _fuse_axes(posterior: dict, er_val: float, fund_axis: float = 0.0,
               weights: dict | None = None) -> tuple[float, float, bool]:
    """三轴融合 → master_score(0-100)。返回 (score, hmm_axis, er_capped)。

    HMM 姿态(后验加权进攻轴) + ER 趋势确认 + 基本面估值。ER 确认压制：score≥60 但 ER<0.5（无
    趋势确认）= 震荡市，封顶 59。`fund_axis` 缺省 0：回测门控用（无 look-ahead-safe 历史基本面
    序列）；实盘快照 build_master_json 传入真实基本面轴。与门控/快照口径一致，复用同一融合。
    """
    w = weights or {"hmm": 0.5, "er": 0.2, "fundamental": 0.3}
    hmm_axis = sum(posterior.get(n, 0.0) * _STATE_OFFENSE[n] for n in STATE_NAMES)
    er_term = (2.0 * er_val - 1.0) * (1.0 if hmm_axis >= 0 else -1.0) if np.isfinite(er_val) else 0.0
    axis = w["hmm"] * hmm_axis + w["er"] * er_term + w["fundamental"] * fund_axis
    score = round(50 + 50 * float(np.clip(axis, -1, 1)), 1)
    er_capped = False
    if score >= 60 and not (np.isfinite(er_val) and er_val >= 0.5):
        score, er_capped = 59.0, True
    return score, hmm_axis, er_capped


def verdict_band(score: float) -> str:
    """master_score → 三档结论：走强(≥60) / 震荡(40-60) / 走弱(≤40)。"""
    return "走强" if score >= 60 else "走弱" if score <= 40 else "震荡"


def _fundamental_axis(regime: dict | None) -> tuple[float | None, str, float]:
    """从 regime 的基本面 顶/底 分折成 −1..+1 估值/宏观轴（底高=超跌便宜=+，顶高=过热贵=−）。"""
    if not regime:
        return None, "—", 0.0
    fund = (regime.get("category_scores") or {}).get("基本面") or {}
    top, bot = fund.get("top"), fund.get("bottom")
    if top is None or bot is None:
        return None, "—", 0.0
    axis = float((bot - top) / 100.0)
    score = round(50 + 50 * float(np.clip(axis, -1, 1)), 1)   # 0..100，>50 偏多/便宜
    tag = "偏多" if score >= 60 else "偏空" if score <= 40 else "中性"
    return score, tag, axis


def build_master_json(cfg: FOFConfig, regime: dict | None = None) -> dict:
    """大势研判快照：HMM 4 态后验 + ER + 基本面 → 综合结论。镜像 build_regime_json，输出 JSON 安全。"""
    path = hmm_state_path(cfg)
    close = _benchmark_close(cfg)
    er = er_series(close, cfg.er_window)

    cur = path.iloc[-1]
    state = str(cur["state"])
    posterior = {n: (float(cur[n]) if np.isfinite(cur[n]) else 0.0) for n in STATE_NAMES}
    er_val = float(er.loc[:cfg.asof].dropna().iloc[-1]) if er.loc[:cfg.asof].notna().any() else float("nan")

    # 三轴融合（HMM 姿态 + ER 趋势确认 + 基本面估值）+ ER 确认压制，抽到 _fuse_axes（与
    # verdict_band 一起，便于复用/单测，行为与旧内联实现一致）。
    fund_score, fund_tag, fund_axis = _fundamental_axis(regime)
    master_score, hmm_axis, er_capped = _fuse_axes(posterior, er_val, fund_axis, cfg.master_weights)
    # 状态不稳定压制：近 4 个月状态切换 ≥2 次（如 危机↔履冰 来回）= regime 不确定的
    # 高波动震荡市 → 强制中性（不进攻也不重防御）。持续单一状态（真熊/真牛）不受影响。
    recent = [s for s in path["state"].tail(4).tolist() if isinstance(s, str)]
    switches = sum(1 for a, b in zip(recent, recent[1:]) if a != b)
    unstable = len(recent) >= 3 and switches >= 2
    if unstable:
        master_score = float(min(max(master_score, 41.0), 59.0))
    # 三档结论（市场状态语言，与风险仪表盘的分档呈现一致）：走强 / 震荡 / 走弱
    verdict = verdict_band(master_score)
    confidence = round(max(posterior.values()) * 100, 0)

    # 三轴罗盘值（0-100，可解释）：HMM 姿态 / ER 趋势 / 基本面
    axes = {
        "HMM姿态": round(float(np.clip(50 + 50 * hmm_axis, 0, 100)), 1),
        "效率比": round(float(np.clip(100 * er_val, 0, 100)), 1) if np.isfinite(er_val) else None,
        "基本面": fund_score,
    }
    streak_days, streak_since = _streak(path, close, cfg.asof)
    # HMM 在日频上拟合 → transmat_ 是【日度】转移矩阵；月度 = 日度^21（21 交易日复利）。
    # 诊断 temp/diag_transmat.py：月度对角 34-63%，与实测月度自持频率(44-62%)对账一致。
    transmat = _extra(cfg).get("transmat")
    trans_monthly = None
    if transmat:
        T = np.array([[transmat[a][b] for b in STATE_NAMES] for a in STATE_NAMES])
        T21 = np.linalg.matrix_power(T, 21)
        trans_monthly = {a: {b: float(T21[i][j]) for j, b in enumerate(STATE_NAMES)}
                         for i, a in enumerate(STATE_NAMES)}

    return {
        "asof": path.index[-1].strftime("%Y-%m-%d"),
        "index_name": index_display(cfg), "index_code": cfg.master_index,
        "verdict": verdict, "master_score": master_score, "confidence": confidence,
        "er_capped": er_capped, "unstable": unstable,
        "gate_label": _state_to_label(state, er_val),
        "streak_days": int(streak_days), "streak_since": streak_since,
        "hmm": {
            "state_name": state,
            "posterior": {n: _round(posterior[n], 3) for n in STATE_NAMES},
            "states_order": STATE_NAMES,
        },
        "er": {"value": _round(er_val, 3), "tag": er_tag(er_val), "window": cfg.er_window},
        "fundamental": {"score": fund_score, "tag": fund_tag},
        "axes": axes,
        "transition": ({"labels": STATE_NAMES, "matrix": trans_monthly,
                        "matrix_daily": transmat,
                        "horizon": "月度（由日度转移矩阵^21 复利推得，已与实测月度切换频率对账）"}
                       if transmat else None),
        "state_stats": state_stats(path, close),
        "segments": state_segments(path, close),
        "advice": _master_advice(verdict, state, er_val, master_score, er_capped, unstable),
        "history": _master_history(path, er, close),
        "sources": _SOURCES,
    }


def _master_advice(verdict: str, state: str, er: float, score: float,
                   er_capped: bool = False, unstable: bool = False) -> str:
    ert = er_tag(er)
    base = f"大势分 {score:.0f}（{verdict}）：HMM 判定『{state}』状态，效率比 {er:.2f}（{ert}）"
    if unstable:
        return (base + "。近月状态频繁切换（危机↔履冰来回）= 高波动震荡市，regime 不确定 → "
                "判为震荡：控制仓位、不追单边，等状态连续 2-3 个月稳定后再表态。")
    if er_capped:
        return (base + f"。HMM 偏多但效率比未达趋势阈值 0.5 —— 无趋势确认不判走强，"
                f"按震荡处理：维持中性敞口、等 ER 放大确认趋势再加。")
    if verdict == "走强":
        return base + "。趋势成立、基本面不拖后腿 → 可提升权益敞口，在低回撤 sleeve 间风险平价。"
    if verdict == "走弱":
        return base + "。状态偏弱或估值压制 → 降敞口、增货基，等趋势与基本面共振再进。"
    return base + "。信号互有强弱 → 维持中性敞口，按 4 铁律精选、控回撤。"


def _master_history(path: pd.DataFrame, er: pd.Series, close: pd.Series,
                    downsample: int = 3) -> dict:
    """日频状态色带 + 4 态后验演化 + ER 线 + 沪深300 价。

    对齐：**同期 nowcast**（m 月末模型回看判定 m 月自身，用了当月数据、无前视）。
    之前的前向 ffill 是门控视角，会把判定整体右移一个月、令色带语义反转
    （诊断 temp/diag_hmm_semantics.py：ffill 下"危机"段实际 +16.7%、"稳态"段 -15.7%；
    同期对齐后 危机 -1.4% / 履冰高波动反弹 +22.5%，语义归位）。暖机段输出 null。"""
    daily_state = _contemp_state(path, close.index)
    dts = list(close.index[::downsample])

    def _st(d):
        v = daily_state.get(d)
        return v if isinstance(v, str) else None

    # 4 态后验日频演化（同期对齐，与色带一致）
    posterior = {}
    for n in STATE_NAMES:
        if n in path.columns:
            daily_p = _contemp_state(path, close.index, col=n)
            posterior[n] = [_round(daily_p.get(d), 3) for d in dts]

    return {
        "dates": [d.strftime("%Y-%m-%d") for d in dts],
        "state_code": [_STATE_CODE.get(_st(d)) for d in dts],
        "state_name": [_st(d) for d in dts],
        "posterior": posterior,
        "er": [_round(er.get(d), 3) for d in dts],
        "benchmark": [_round(close.get(d), 2) for d in dts],
        "legend": _STATE_CODE,
    }


def state_stats(path: pd.DataFrame, close: pd.Series) -> list[dict]:
    """状态画像：各状态（同期对齐）覆盖段的实测年化/波动/月数——语义与数据互证，直接上 UI。"""
    daily = _contemp_state(path, close.index)
    ret = close.pct_change()
    out = []
    for st in STATE_NAMES:
        mask = daily == st
        r = ret[mask].dropna()
        months = int((path["state"] == st).sum())
        if len(r) < 5:
            out.append({"state": st, "months": months, "ann": None, "vol": None})
            continue
        out.append({"state": st, "months": months,
                    "ann": _round(float(r.mean() * 252), 4),
                    "vol": _round(float(r.std() * np.sqrt(252)), 4)})
    return out


def state_segments(path: pd.DataFrame, close: pd.Series, last_n: int = 8) -> list[dict]:
    """近期状态段：把月度状态序列按连续同状态分段，给出起止、时长、区间涨跌。"""
    rows = [(m, s) for m, s in path["state"].items() if isinstance(s, str)]
    if not rows:
        return []
    segs: list[dict] = []
    cur_state, cur_start = rows[0][1], rows[0][0]
    prev_m = rows[0][0]
    for m, s in rows[1:] + [(None, None)]:                 # 哨兵收尾
        if s != cur_state:
            seg_close = close[(close.index.to_period("M") >= cur_start.to_period("M"))
                              & (close.index.to_period("M") <= prev_m.to_period("M"))]
            ret = float(seg_close.iloc[-1] / seg_close.iloc[0] - 1.0) if len(seg_close) > 1 else None
            segs.append({"state": cur_state,
                         "start": cur_start.strftime("%Y-%m"),
                         "end": prev_m.strftime("%Y-%m"),
                         "months": int((prev_m.to_period("M") - cur_start.to_period("M")).n) + 1,
                         "ret": _round(ret, 4)})
            cur_state, cur_start = s, m
        prev_m = m if m is not None else prev_m
    return segs[-last_n:]


def _streak(path: pd.DataFrame, close: pd.Series, asof: str) -> tuple[int, str | None]:
    """当前状态从 asof 往回连续持续的交易日数 + 起始日（同期对齐，与色带一致）。"""
    daily = _contemp_state(path, close.index).loc[:asof].dropna()
    if daily.empty:
        return 0, None
    cur = daily.iloc[-1]
    n = 0
    for v in daily.iloc[::-1]:
        if v == cur:
            n += 1
        else:
            break
    since = daily.index[len(daily) - n]
    return n, since.strftime("%Y-%m-%d")
