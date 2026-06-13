"""Daily FOF backtest — selection (4 铁律) + risk-parity weights + regime gate.

Discipline: at the close of each month-end rebalance date t we decide weights from data
up to t; those weights are shifted one day so they earn returns from t+1 (decide-on-close,
execute-next-open). Transaction cost (cfg.cost_bps) is charged on the execution day.
Returns a result dict consumed by `fof/tables.py` and `fof/report.py`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .config import FOFConfig
from .sleeves import build_all_sleeves
from .selection import select_sleeves
from .weights import build_allocation
from . import regime as regimemod

logger = logging.getLogger(__name__)


@dataclass
class FOFResult:
    nav: pd.Series
    baseline_nav: pd.Series
    benchmark_nav: pd.Series
    labels: pd.Series
    turnover: pd.Series
    rebalances: list[dict] = field(default_factory=list)
    sleeve_navs: pd.DataFrame = field(default_factory=pd.DataFrame)
    mm: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))


def _rebalance_dates(idx: pd.DatetimeIndex, warmup: int) -> list[pd.Timestamp]:
    """Last trading day of each calendar month, after a warmup head."""
    if len(idx) <= warmup:
        return []
    usable = idx[warmup:]
    return [grp[-1] for _, grp in usable.groupby(usable.to_period("M")).items()] \
        if hasattr(usable, "groupby") else _month_ends(usable)


def _month_ends(idx: pd.DatetimeIndex) -> list[pd.Timestamp]:
    s = pd.Series(idx, index=idx)
    return list(s.groupby(idx.to_period("M")).last())


def _nav_from_targets(target_on_rebal: pd.DataFrame, asset_rets: pd.DataFrame,
                      cost_bps: float) -> tuple[pd.Series, pd.Series]:
    """Forward-fill rebalance targets, apply next-day, charge cost on execution day."""
    wdf = target_on_rebal.reindex(asset_rets.index).ffill()
    # warmup rows (before first rebalance) -> sit in money market
    flat = wdf.isna().all(axis=1)
    if "money_market" in wdf.columns:
        wdf.loc[flat, :] = 0.0
        wdf.loc[flat, "money_market"] = 1.0
    wdf = wdf.fillna(0.0)

    turnover = wdf.diff().abs().sum(axis=1) * 0.5
    applied = wdf.shift(1).fillna(0.0)
    port_ret = (applied * asset_rets).sum(axis=1)
    cost = turnover.shift(1).fillna(0.0) * (cost_bps / 1e4)
    nav = (1.0 + (port_ret - cost)).cumprod()
    return nav, turnover


@dataclass
class Prepared:
    """Data that does not depend on selection/weight tunables — reusable across a grid."""
    sleeve_navs: pd.DataFrame
    mm: pd.Series
    labels: pd.Series
    assets: pd.DataFrame
    asset_rets: pd.DataFrame


def prepare(cfg: FOFConfig) -> Prepared:
    sleeve_navs, mm = build_all_sleeves(cfg)
    labels = regimemod.regime_labels(cfg)
    assets = sleeve_navs.copy()
    assets["money_market"] = mm.reindex(sleeve_navs.index).ffill()
    assets = assets.dropna(how="all")
    return Prepared(sleeve_navs, mm, labels, assets, assets.pct_change().fillna(0.0))


def run_fof(cfg: FOFConfig, prepared: Prepared | None = None) -> FOFResult:
    p = prepared or prepare(cfg)
    sleeve_navs, mm, labels = p.sleeve_navs, p.mm, p.labels
    assets, asset_rets = p.assets, p.asset_rets
    idx = assets.index

    warmup = max(cfg.eval_window, cfg.mom_lookback) + 5
    rebal_dates = [d for d in _month_ends(idx) if d >= idx[min(warmup, len(idx) - 1)]]

    rows: dict[pd.Timestamp, dict[str, float]] = {}
    base_rows: dict[pd.Timestamp, dict[str, float]] = {}
    rebalances: list[dict] = []

    for d in rebal_dates:
        label = str(labels.loc[:d].iloc[-1]) if (labels.index <= d).any() else "ranging"
        exposure = cfg.regime_gate.get(label, 0.6)
        sel = select_sleeves(sleeve_navs.loc[:d], d, cfg)
        alloc = build_allocation(sel, exposure, cfg)
        rows[d] = {a: alloc["weights"].get(a, 0.0) for a in assets.columns}

        # baseline: static equal-weight over the sleeves with data at d (no gate/铁律/cap)
        avail = [s for s in sleeve_navs.columns if pd.notna(sleeve_navs[s].loc[:d].iloc[-1])]
        ew = 1.0 / len(avail) if avail else 0.0
        base_rows[d] = {a: (ew if a in avail else 0.0) for a in assets.columns}

        rebalances.append({
            "date": d.strftime("%Y-%m-%d"), "regime_label": label,
            "equity_exposure": round(exposure, 3),
            "selected": sel["selected"], "blacklisted": sel["blacklisted"],
            "money_market_weight": alloc["money_market_weight"],
            "cap_applied": alloc["cap_applied"],
            "fallback_to_cash": alloc["fallback_to_cash"],
        })

    target = pd.DataFrame(rows).T.reindex(columns=assets.columns) if rows else \
        pd.DataFrame(columns=assets.columns)
    base_target = pd.DataFrame(base_rows).T.reindex(columns=assets.columns) if base_rows else \
        pd.DataFrame(columns=assets.columns)

    nav, turnover = _nav_from_targets(target, asset_rets, cfg.cost_bps)
    base_nav, _ = _nav_from_targets(base_target, asset_rets, cfg.cost_bps)

    bench = _benchmark_nav(cfg, idx)

    # trim the leading warmup so curves start at the first rebalance
    start_at = rebal_dates[0] if rebal_dates else idx[0]
    nav = _renorm(nav.loc[start_at:])
    base_nav = _renorm(base_nav.loc[start_at:])
    bench = _renorm(bench.loc[start_at:]) if bench is not None else pd.Series(dtype=float)

    return FOFResult(nav=nav, baseline_nav=base_nav, benchmark_nav=bench,
                     labels=labels.reindex(nav.index).ffill(),
                     turnover=turnover.loc[start_at:], rebalances=rebalances,
                     sleeve_navs=sleeve_navs, mm=mm)


def _benchmark_nav(cfg: FOFConfig, idx) -> pd.Series | None:
    from . import data as datamod
    panel = datamod.close_panel([cfg.benchmark], cfg.start, cfg.asof)
    if panel.empty:
        return None
    return panel[cfg.benchmark].reindex(idx).ffill()


def _renorm(s: pd.Series) -> pd.Series:
    s = s.dropna()
    return s / s.iloc[0] if len(s) else s
