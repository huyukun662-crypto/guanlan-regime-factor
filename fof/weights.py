"""铁律4 — inverse-drawdown risk parity + hard cap + regime gate -> final allocation.

Risk parity: weight a sleeve in inverse proportion to its recent drawdown (lower DD ->
more capital), so each sleeve contributes roughly equal "damage potential". The hard cap
(`max_weight`) is applied WITHOUT redistribution — excess goes to money market, matching
the article's "单sleeve死活不超过50%，剩下宁愿买逆回购". The regime gate then scales total
equity exposure; whatever is not in equity becomes money market.
"""

from __future__ import annotations

from .config import FOFConfig

_DD_FLOOR = 0.01     # floor |drawdown| to avoid div-by-zero for a flat sleeve


def risk_parity_weights(selected: list[dict]) -> dict[str, float]:
    """Inverse-|drawdown| weights over the selected sleeves, normalized to sum 1."""
    if not selected:
        return {}
    raw = {s["sleeve"]: 1.0 / max(abs(s["period_max_dd"]), _DD_FLOOR) for s in selected}
    total = sum(raw.values())
    return {k: v / total for k, v in raw.items()}


def apply_cap_and_gate(rp: dict[str, float], exposure: float,
                       cfg: FOFConfig) -> tuple[dict[str, float], float, bool]:
    """Cap each sleeve at max_weight (no redistribution), then scale by regime exposure.

    Returns (equity_weights, money_market_weight, cap_applied).
    """
    cap_applied = any(w > cfg.max_weight + 1e-9 for w in rp.values())
    capped = {k: min(w, cfg.max_weight) for k, w in rp.items()}
    equity = {k: w * exposure for k, w in capped.items()}
    money_market = 1.0 - sum(equity.values())
    return equity, round(money_market, 6), cap_applied


def build_allocation(select_result: dict, exposure: float,
                     cfg: FOFConfig) -> dict:
    """Full allocation dict for one rebalance: weights + money-market + flags."""
    if select_result["fallback_to_cash"] or not select_result["selected"]:
        return {"weights": {"money_market": 1.0}, "money_market_weight": 1.0,
                "cap_applied": False, "fallback_to_cash": True,
                "equity_exposure": 0.0}

    rp = risk_parity_weights(select_result["selected"])
    equity, mm, cap_applied = apply_cap_and_gate(rp, exposure, cfg)
    for s in select_result["selected"]:                 # annotate each selected sleeve
        s["weight"] = round(equity.get(s["sleeve"], 0.0), 4)
    weights = {k: round(v, 4) for k, v in equity.items()}
    weights["money_market"] = round(mm, 4)
    return {"weights": weights, "money_market_weight": round(mm, 4),
            "cap_applied": cap_applied, "fallback_to_cash": False,
            "equity_exposure": round(exposure, 4)}
