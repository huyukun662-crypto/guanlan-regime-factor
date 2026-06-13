"""铁律4 risk-parity + cap + gate tests."""

from dataclasses import replace
from fof.config import DEFAULT_CONFIG
from fof.weights import risk_parity_weights, apply_cap_and_gate, build_allocation


def test_risk_parity_inverse_drawdown():
    sel = [{"sleeve": "a", "period_max_dd": -0.05},
           {"sleeve": "b", "period_max_dd": -0.20}]
    w = risk_parity_weights(sel)
    assert abs(sum(w.values()) - 1.0) < 1e-9
    assert w["a"] > w["b"]                       # lower drawdown -> more capital
    assert abs(w["a"] - 0.8) < 1e-6              # (1/.05)/(1/.05+1/.20) = 0.8


def test_cap_no_redistribute_remainder_to_cash():
    cfg = replace(DEFAULT_CONFIG, max_weight=0.5)
    rp = {"a": 1.0}                              # single sleeve
    eq, mm, capped = apply_cap_and_gate(rp, exposure=1.0, cfg=cfg)
    assert capped is True and abs(eq["a"] - 0.5) < 1e-9 and abs(mm - 0.5) < 1e-9


def test_regime_gate_scales_exposure():
    cfg = replace(DEFAULT_CONFIG, max_weight=0.5)
    eq, mm, _ = apply_cap_and_gate({"a": 0.5, "b": 0.5}, exposure=0.6, cfg=cfg)
    assert abs(sum(eq.values()) - 0.6) < 1e-9 and abs(mm - 0.4) < 1e-9


def test_fallback_allocation_is_all_money_market():
    cfg = DEFAULT_CONFIG
    alloc = build_allocation({"selected": [], "fallback_to_cash": True}, 0.0, cfg)
    assert alloc["weights"] == {"money_market": 1.0} and alloc["money_market_weight"] == 1.0
