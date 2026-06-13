"""因子配置建议映射 —— 姿态/tilt 方向/超配选择，纯 dict→dict、无网络。"""

from __future__ import annotations

from fof.advice import factor_allocation_advice

_FACTORS_BASE = {
    "ranking": {"factors": [
        {"key": "a", "display": "领涨A", "category": "成长", "r_1m": 0.08, "r_3m": 0.12},
        {"key": "b", "display": "次B", "category": "价值", "r_1m": 0.03, "r_3m": 0.05},
        {"key": "c", "display": "中C", "category": "红利", "r_1m": 0.00, "r_3m": 0.01},
        {"key": "d", "display": "弱D", "category": "低波", "r_1m": -0.04, "r_3m": -0.02},
        {"key": "e", "display": "垫底E", "category": "规模", "r_1m": -0.09, "r_3m": -0.07},
    ]},
}


def _factors(ic_mean):
    return {**_FACTORS_BASE, "rotation_ic": {"ic_mean": ic_mean, "icir": 0.1, "hit_rate": 0.55}}


def test_posture_from_verdict():
    assert factor_allocation_advice({"verdict": "走强"}, _factors(0.05))["posture"] == "进攻"
    assert factor_allocation_advice({"verdict": "震荡"}, _factors(0.05))["posture"] == "中性"
    assert factor_allocation_advice({"verdict": "走弱"}, _factors(0.05))["posture"] == "防御"


def test_momentum_tilt_overweights_leaders():
    adv = factor_allocation_advice({"verdict": "走强"}, _factors(0.06))
    assert "动量" in adv["tilt_mode"]
    assert adv["overweight"][0]["key"] == "a"          # 领涨被超配
    assert adv["underweight"][0]["key"] == "e"         # 垫底被低配


def test_reversal_tilt_overweights_laggards():
    adv = factor_allocation_advice({"verdict": "走弱"}, _factors(-0.06))
    assert "反转" in adv["tilt_mode"]
    assert adv["overweight"][0]["key"] == "e"          # 垫底（待反弹）被超配
    assert adv["underweight"][0]["key"] == "a"


def test_neutral_tilt_no_active_picks():
    adv = factor_allocation_advice({"verdict": "震荡"}, _factors(0.0))
    assert "中性" in adv["tilt_mode"]
    assert adv["overweight"] == [] and adv["underweight"] == []
    assert adv["ranking_top"][0]["key"] == "a"         # 仍保留原始排名供观察


def test_caveats_present_and_sources_passthrough():
    adv = factor_allocation_advice(
        {"verdict": "震荡", "sources": ["D:\\Claude\\Brain\\x.md"]}, _factors(0.05))
    assert adv["caveats"] and any("研究建议" in c for c in adv["caveats"])
    assert adv["sources"] == ["D:\\Claude\\Brain\\x.md"]
