"""On-demand data refresh from the dashboard button.

Optionally updates TUSHARE_TOKEN in the gitignored .env (never logged, never echoed back),
then reruns the full pipeline for *today* and regenerates outputs/*.json + docs/before-after.md.
"""

from __future__ import annotations

import datetime
import os
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env"


def update_token(token: str) -> None:
    """Replace/insert TUSHARE_TOKEN in .env and the live process env. Value is never logged."""
    token = token.strip()
    if not token:
        return
    lines, found = [], False
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("TUSHARE_TOKEN="):
                lines.append(f"TUSHARE_TOKEN={token}")
                found = True
            else:
                lines.append(line)
    if not found:
        lines.append(f"TUSHARE_TOKEN={token}")
    ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.environ["TUSHARE_TOKEN"] = token        # running server uses it immediately


class TokenRequired(Exception):
    """Raised when /api/refresh is called without a Tushare token in the request body."""


def run_refresh(token: str = "") -> dict:
    """Rerun the pipeline for today using the token from the request body.

    Web-UI refresh policy: token MUST come from the form input (never falls back to .env, never
    persisted to disk). The token only lives in this process's env for the duration of the run
    and is cleared again on completion, so a server restart loses it — by design.
    """
    token = (token or "").strip()
    if not token:
        raise TokenRequired("请在输入框填写 Tushare token")
    # Apply for this run only — overwrite any previous value, do NOT write .env.
    prev = os.environ.get("TUSHARE_TOKEN")
    os.environ["TUSHARE_TOKEN"] = token
    try:
        return _run_pipeline()
    finally:
        # Scrub token from this process's env. If there was an older value (e.g. set
        # during process startup from .env when it still had one) restore it; else delete.
        if prev is None:
            os.environ.pop("TUSHARE_TOKEN", None)
        else:
            os.environ["TUSHARE_TOKEN"] = prev


def _run_pipeline() -> dict:
    from fof.config import DEFAULT_CONFIG
    from fof import report, sleeves
    from fof import data as datamod

    today = datetime.date.today().strftime("%Y-%m-%d")
    # 1) ETF sleeves (regime + benchmark use these). bypass get_ohlcv 5-day stale tolerance.
    n_etf = datamod.refresh_tail(sleeves.all_codes(), today)
    # 2) Index codes used by master (HMM benchmark) and factors (12 factor indices + XSEC pool).
    # index_close always hits Tushare and overwrites the parquet, so it implicitly refreshes.
    from fof.config import FACTOR_DEFS, FACTOR_XSEC_POOL
    indices = {DEFAULT_CONFIG.master_index, "000300.SH", "000001.SH"}
    for _k, _d, long_c, short_c, _c in FACTOR_DEFS:
        for code in (long_c, short_c):
            if code and code != "XSEC":
                indices.add(code)
    for code in FACTOR_XSEC_POOL:
        indices.add(code)
    for code in indices:
        try:
            datamod.index_close(code, DEFAULT_CONFIG.start, today)
        except Exception:                       # noqa: BLE001 — fall back to cache, don't fail refresh
            pass

    cfg = replace(DEFAULT_CONFIG, asof=today)
    dash = report.run_all(cfg, write=True)
    # FOF 已从 run_all 移除，dash 只剩 regime/master/factors；before_after.md 不再随刷新重写
    # （它属于 ETF-FOF 证据链，要更新走 scripts/grid_search.py + 手动重生成）。

    reg = dash["regime"]
    master = dash.get("master", {}) or {}
    factors = dash.get("factors", {}) or {}
    # 「最新数据 asof」= 实际数据中最新一根 K 线的日期，取三者最大值（不是 cfg.asof 这个日历日）。
    asof_dates = [d for d in [reg.get("asof"), master.get("asof"),
                              (factors.get("ranking") or {}).get("asof")] if d]
    data_asof = max(asof_dates) if asof_dates else today
    fac_alloc_path = ROOT / "outputs" / "factor_allocation.json"
    fac_alloc = {}
    if fac_alloc_path.exists():
        import json
        try:
            fac_alloc = json.loads(fac_alloc_path.read_text(encoding="utf-8"))
        except Exception:
            fac_alloc = {}
    return {
        "ok": True,
        "asof": data_asof,                     # actual latest data
        "requested_asof": today,               # what we asked for
        "n_etf_updated": int(n_etf),           # 0 on non-trading days / already-fresh
        "composite_score": reg["composite_score"], "band": reg["band"],
        "regime_label": reg["regime_label"], "equity_exposure": reg["equity_exposure"],
        "regime_asof": reg.get("asof"), "master_asof": master.get("asof"),
        "verdict": master.get("verdict"), "master_score": master.get("master_score"),
        "n_factors": factors.get("n_factors"),
        "posture": fac_alloc.get("posture"),
        "overweight": [f["display"] for f in (fac_alloc.get("overweight") or [])],
        "underweight": [f["display"] for f in (fac_alloc.get("underweight") or [])],
    }
