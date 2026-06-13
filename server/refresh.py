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


def run_refresh(token: str = "") -> dict:
    """Update token (if given), rerun the pipeline for today, return a compact summary."""
    if token and token.strip():
        update_token(token)

    from fof.config import DEFAULT_CONFIG
    from fof import report, sleeves
    from fof import data as datamod

    today = datetime.date.today().strftime("%Y-%m-%d")
    # force-pull the latest trading day (bypass get_ohlcv's 5-day stale tolerance)
    datamod.refresh_tail(sleeves.all_codes(), today)
    cfg = replace(DEFAULT_CONFIG, asof=today)
    dash = report.run_all(cfg, write=True)
    # FOF 已从 run_all 移除，dash 只剩 regime/master/factors；before_after.md 不再随刷新重写
    # （它属于 ETF-FOF 证据链，要更新走 scripts/grid_search.py + 手动重生成）。

    reg = dash["regime"]
    master = dash.get("master", {}) or {}
    factors = dash.get("factors", {}) or {}
    fac_alloc_path = ROOT / "outputs" / "factor_allocation.json"
    fac_alloc = {}
    if fac_alloc_path.exists():
        import json
        try:
            fac_alloc = json.loads(fac_alloc_path.read_text(encoding="utf-8"))
        except Exception:
            fac_alloc = {}
    return {
        "ok": True, "asof": reg["asof"],
        "composite_score": reg["composite_score"], "band": reg["band"],
        "regime_label": reg["regime_label"], "equity_exposure": reg["equity_exposure"],
        "verdict": master.get("verdict"), "master_score": master.get("master_score"),
        "n_factors": factors.get("n_factors"),
        "posture": fac_alloc.get("posture"),
        "overweight": [f["display"] for f in (fac_alloc.get("overweight") or [])],
        "underweight": [f["display"] for f in (fac_alloc.get("underweight") or [])],
    }
