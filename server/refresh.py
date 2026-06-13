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
    """Non-streaming variant — kept for tests / programmatic use; the live UI uses
    stream_refresh() (SSE) which surfaces per-stage progress."""
    from fof.config import DEFAULT_CONFIG
    from fof import report, sleeves
    from fof import data as datamod

    today = datetime.date.today().strftime("%Y-%m-%d")
    n_etf = datamod.refresh_tail(sleeves.all_codes(), today)
    n_idx = datamod.index_refresh_tail(_index_codes(), today)
    cfg = replace(DEFAULT_CONFIG, asof=today)
    dash = report.run_all(cfg, write=True)
    return _build_result(today, n_etf, n_idx, dash)


def _index_codes() -> list[str]:
    from fof.config import DEFAULT_CONFIG, FACTOR_DEFS, FACTOR_XSEC_POOL
    indices = {DEFAULT_CONFIG.master_index, "000300.SH", "000001.SH"}
    for _k, _d, long_c, short_c, _c in FACTOR_DEFS:
        for code in (long_c, short_c):
            if code and code != "XSEC":
                indices.add(code)
    for code in FACTOR_XSEC_POOL:
        indices.add(code)
    return list(indices)


def _build_result(today: str, n_etf: int, n_idx: int, dash: dict) -> dict:
    """Compose the final response dict from a freshly-run dashboard."""
    reg = dash["regime"]
    master = dash.get("master", {}) or {}
    factors = dash.get("factors", {}) or {}
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
        "ok": True, "asof": data_asof, "requested_asof": today,
        "n_etf_updated": int(n_etf), "n_idx_updated": int(n_idx),
        "composite_score": reg["composite_score"], "band": reg["band"],
        "regime_label": reg["regime_label"], "equity_exposure": reg["equity_exposure"],
        "regime_asof": reg.get("asof"), "master_asof": master.get("asof"),
        "verdict": master.get("verdict"), "master_score": master.get("master_score"),
        "n_factors": factors.get("n_factors"),
        "posture": fac_alloc.get("posture"),
        "overweight": [f["display"] for f in (fac_alloc.get("overweight") or [])],
        "underweight": [f["display"] for f in (fac_alloc.get("underweight") or [])],
    }


# --- progressed streaming version (SSE) ---
import json as _json                                                          # noqa: E402


def _sse(payload: dict) -> str:
    return f"data: {_json.dumps(payload, ensure_ascii=False)}\n\n"


def stream_refresh(token: str):
    """Yield SSE events ({type, pct, label, ...}) at every pipeline stage so the dashboard
    can render a progress bar. Final event is `done` carrying the same dict as run_refresh.
    Token policy mirrors run_refresh: required per request, scrubbed in finally."""
    token = (token or "").strip()
    if not token:
        yield _sse({"type": "error", "code": "token_required",
                    "error": "请在输入框填写 Tushare token"})
        return
    prev = os.environ.get("TUSHARE_TOKEN")
    os.environ["TUSHARE_TOKEN"] = token
    try:
        from fof.config import DEFAULT_CONFIG
        from fof import report, sleeves, regime as regimemod, master as mastermod, \
            factors as factorsmod, data as datamod

        today = datetime.date.today().strftime("%Y-%m-%d")
        yield _sse({"type": "step", "pct": 5,  "label": "拉取 ETF 数据 (Tushare)…"})
        n_etf = datamod.refresh_tail(sleeves.all_codes(), today)

        yield _sse({"type": "step", "pct": 20, "label": f"已 {n_etf} ETF · 拉取指数数据…"})
        n_idx = datamod.index_refresh_tail(_index_codes(), today)

        cfg = replace(DEFAULT_CONFIG, asof=today)
        yield _sse({"type": "step", "pct": 40, "label": f"已 {n_idx} 指数 · 计算风险研判…"})
        reg = regimemod.build_regime_json(cfg)

        yield _sse({"type": "step", "pct": 65, "label": "HMM 大势研判（walk-forward 重拟合）…"})
        master = mastermod.build_master_json(cfg, reg)

        yield _sse({"type": "step", "pct": 85, "label": "因子看板 · 月度 IC + 滚动 Sharpe…"})
        factor_board = factorsmod.build_factor_board(cfg)

        yield _sse({"type": "step", "pct": 95, "label": "写入 outputs/*.json…"})
        dash = {"generated_at": cfg.asof, "config": cfg.to_dict(),
                "regime": reg, "master": master, "factors": factor_board}
        report._dump("regime.json", reg)
        report._dump("master.json", master)
        report._dump("factors.json", factor_board)
        report._dump("dashboard.json", dash)

        yield _sse({"type": "done", "pct": 100, "result": _build_result(today, n_etf, n_idx, dash)})
    except Exception as ex:                                                   # noqa: BLE001
        yield _sse({"type": "error",
                    "error": f"{type(ex).__name__}: {str(ex)[:200]}"})
    finally:
        if prev is None:
            os.environ.pop("TUSHARE_TOKEN", None)
        else:
            os.environ["TUSHARE_TOKEN"] = prev
