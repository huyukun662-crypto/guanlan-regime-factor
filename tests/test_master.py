"""大势研判 tests — ER bounds, HMM state naming/fit, gate mapping, look-ahead isolation.

All network-free: exercises the pure functions in fof/master.py with synthetic series so the
suite stays fast and deterministic. Full build_master_json / hmm_label_series (which fetch the
benchmark) are covered by the pipeline smoke run, not here.
"""

import numpy as np
import pandas as pd

from fof.master import (
    er_series, er_tag, _name_states, _fit_label, _state_to_label,
    _master_history, STATE_NAMES,
)


def test_er_bounds_and_extremes():
    idx = pd.bdate_range("2020-01-01", periods=120)
    # pure uptrend -> ER ~ 1
    up = pd.Series(np.linspace(100, 200, 120), index=idx)
    er_up = er_series(up, 10).dropna()
    assert ((er_up >= 0) & (er_up <= 1)).all()
    assert er_up.iloc[-1] > 0.95
    # sawtooth (oscillates) -> ER ~ 0
    saw = pd.Series([100 + (5 if i % 2 else -5) for i in range(120)], index=idx).astype(float)
    er_saw = er_series(saw, 10).dropna()
    assert ((er_saw >= 0) & (er_saw <= 1)).all()
    assert er_saw.iloc[-1] < 0.1


def test_er_tag():
    assert er_tag(0.8) == "趋势"
    assert er_tag(0.2) == "震荡"
    assert er_tag(0.4) == "中性"
    assert er_tag(float("nan")) == "—"


def test_name_states_semantics():
    # means rows = [logret, vol, er] (standardized). 4 states.
    means = np.array([
        [-2.0, 1.5, 0.0],   # 0: lowest return -> 危机
        [0.1, 0.3, 0.0],    # 1: low return, low vol -> 平静
        [0.5, 2.0, 0.0],    # 2: positive, highest vol -> 履冰
        [0.6, 0.4, 0.0],    # 3: highest return -> 稳态
    ])
    name = _name_states(means)
    assert name[0] == "危机"
    assert name[2] == "履冰"
    assert name[3] == "稳态"
    assert name[1] == "平静"
    assert set(name.values()) == set(STATE_NAMES)


def test_state_to_label_mapping():
    assert _state_to_label("危机", 0.9) == "bear"
    assert _state_to_label("稳态", 0.8) == "trend"
    assert _state_to_label("稳态", 0.2) == "ranging"     # low ER downgrades trend
    assert _state_to_label("履冰", 0.8) == "trend"
    assert _state_to_label("履冰", 0.2) == "ranging"
    assert _state_to_label("平静", 0.9) == "ranging"


def _synthetic_feat(n=400, seed=0):
    rng = np.random.default_rng(seed)
    # two regimes: calm-up then volatile-down, gives the HMM something to separate
    half = n // 2
    r1 = rng.normal(0.0008, 0.006, half)
    r2 = rng.normal(-0.0010, 0.020, n - half)
    logret = np.concatenate([r1, r2])
    idx = pd.bdate_range("2020-01-01", periods=n)
    close = pd.Series(100 * np.exp(np.cumsum(logret)), index=idx)
    lr = np.log(close / close.shift(1))
    vol = lr.rolling(20, min_periods=20).std()
    er = er_series(close, 10)
    return pd.DataFrame({"logret": lr, "vol20": vol, "er": er}).dropna()


def test_fit_label_valid_and_reproducible():
    feat = _synthetic_feat()
    name_a, post_a, _tm_a = _fit_label(feat, k=4, seed=42)
    name_b, post_b, _tm_b = _fit_label(feat, k=4, seed=42)
    assert name_a in STATE_NAMES
    assert abs(sum(post_a.values()) - 1.0) < 1e-6
    assert all(np.isfinite(v) for v in post_a.values())
    # reproducible with fixed seed
    assert name_a == name_b
    assert post_a == post_b


def test_fit_label_lookahead_isolation():
    """Decoding state at m must not depend on data after m: slicing isolates the future."""
    feat = _synthetic_feat(n=400)
    m = feat.index[300]
    label_now, _p, _t = _fit_label(feat.loc[:m], k=4, seed=42)
    # append future bars, then re-slice to [:m] — identical input -> identical verdict
    future = _synthetic_feat(n=120, seed=99)
    future.index = pd.bdate_range(feat.index[-1] + pd.Timedelta(days=1), periods=len(future))
    feat2 = pd.concat([feat, future])
    label_again, _p2, _t2 = _fit_label(feat2.loc[:m], k=4, seed=42)
    assert label_now == label_again


def test_fit_label_transition_matrix():
    """Named 4x4 transition matrix: STATE_NAMES rows/cols, each row sums to ~1."""
    feat = _synthetic_feat(n=400)
    _name, _post, transmat = _fit_label(feat, k=4, seed=42)
    assert set(transmat.keys()) == set(STATE_NAMES)
    for a in STATE_NAMES:
        assert set(transmat[a].keys()) == set(STATE_NAMES)
        row_sum = sum(transmat[a].values())
        assert abs(row_sum - 1.0) < 1e-6
        assert all(0.0 <= transmat[a][b] <= 1.0 for b in STATE_NAMES)


def _synthetic_path(close):
    """Monthly state path with the 4 posterior columns (mimics hmm_state_path output)."""
    months = list(pd.Series(close.index, index=close.index).groupby(close.index.to_period("M")).last())
    rows = []
    for m in months:
        rows.append({"date": m, "state": "稳态", "er": 0.5,
                     "危机": 0.05, "平静": 0.15, "履冰": 0.1, "稳态": 0.7})
    return pd.DataFrame(rows).set_index("date")


def test_master_history_finite_and_coded():
    idx = pd.bdate_range("2020-01-01", periods=300)
    close = pd.Series(np.linspace(100, 150, 300), index=idx)
    er = er_series(close, 10)
    path = _synthetic_path(close)
    hist = _master_history(path, er, close, downsample=3)
    assert len(hist["dates"]) == len(hist["state_code"]) == len(hist["er"]) == len(hist["benchmark"])
    for c in hist["state_code"]:
        assert c in (0, 1, 2, 3, None)
    for v in hist["benchmark"] + hist["er"]:
        assert v is None or np.isfinite(v)


def test_master_history_posterior_aligned():
    """Posterior evolution: 4 series aligned to dates, values in [0,1] or None."""
    from fof.master import STATE_NAMES
    idx = pd.bdate_range("2020-01-01", periods=300)
    close = pd.Series(np.linspace(100, 150, 300), index=idx)
    er = er_series(close, 10)
    hist = _master_history(_synthetic_path(close), er, close, downsample=3)
    assert "posterior" in hist
    for n in STATE_NAMES:
        assert n in hist["posterior"]
        assert len(hist["posterior"][n]) == len(hist["dates"])
        for v in hist["posterior"][n]:
            assert v is None or (0.0 <= v <= 1.0)


def test_contemp_alignment_maps_month_to_itself():
    """色带同期对齐：m 月中旬的天应拿到 m 月末的判定（nowcast），而非上月（ffill 会右移）。"""
    from fof.master import _contemp_state
    idx = pd.bdate_range("2024-01-01", periods=64)        # 约 3 个月
    months = list(pd.Series(idx, index=idx).groupby(idx.to_period("M")).last())
    path = pd.DataFrame({"state": ["危机", "稳态", "平静"][:len(months)]}, index=months)
    daily = _contemp_state(path, idx)
    mid_feb = idx[(idx.month == 2)][5]
    assert daily.loc[mid_feb] == "稳态"                    # 2月中旬 -> 2月末的判定
    mid_jan = idx[(idx.month == 1)][5]
    assert daily.loc[mid_jan] == "危机"


def test_warmup_state_is_nan_not_quiet():
    """暖机段（<252 天历史）状态必须是未判定(NaN)，不得冒充'平静'。"""
    from fof.master import _master_history
    idx = pd.bdate_range("2020-01-01", periods=80)
    close = pd.Series(np.linspace(100, 120, 80), index=idx)
    er = er_series(close, 10)
    months = list(pd.Series(close.index, index=close.index).groupby(close.index.to_period("M")).last())
    path = pd.DataFrame({"state": [np.nan] * len(months)}, index=months)   # 全暖机
    hist = _master_history(path, er, close, downsample=3)
    assert all(c is None for c in hist["state_code"])
    assert all(s is None for s in hist["state_name"])


def test_streak_counts_current_run():
    from fof.master import _streak
    idx = pd.bdate_range("2020-01-01", periods=300)
    close = pd.Series(np.linspace(100, 150, 300), index=idx)
    # path: last month 危机, earlier 稳态 -> streak = trading days in the final month run
    months = list(pd.Series(close.index, index=close.index).groupby(close.index.to_period("M")).last())
    states = ["稳态"] * (len(months) - 1) + ["危机"]
    path = pd.DataFrame({"state": states}, index=months)
    days, since = _streak(path, close, str(close.index[-1].date()))
    assert days >= 1
    assert since is not None
