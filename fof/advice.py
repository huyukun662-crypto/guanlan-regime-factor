"""因子配置建议 —— 把大势研判(master.json) 与因子看板(factors.json) 映射成一句研究建议：
总仓位姿态(进攻/中性/防御) + 该超配/低配哪些风格。

纯 dict→dict，无 IO、无回测、无组合构建、不出权重。诚实口径硬编码（因子动量很弱、姿态优先于 tilt、
这是研究建议非组合）。供 factor-allocation skill 调用，可单测。
"""

from __future__ import annotations

_POSTURE = {"走强": "进攻", "震荡": "中性", "走弱": "防御"}
_EQUITY_HINT = {"走强": "高（可偏满仓权益）", "震荡": "中（半仓 / 择优）", "走弱": "低（防御 / 现金为主）"}
_IC_DEADBAND = 0.02            # |IC 均值| < 0.02 视为无方向 → tilt 中性

_CAVEATS = [
    "总仓位姿态优先于风格 tilt：先按大势决定多少权益，再谈配哪些风格。",
    "因子动量很弱（历史 IC 均值≈0.04、ICIR≈0.09、胜率≈55%）→ 风格 tilt 只是弱倾斜，别据此重仓押注。",
    "防御（走弱）期 tilt 意义小：先降权益，风格选择是次要项。",
    "这是研究建议、不是组合：不含权重、未回测、未计成本/滑点/换手。",
    "仅供量化研究参考，不构成投资建议。",
]


def _pick(factors_ranked: list, n: int) -> list:
    return [{"key": f.get("key"), "display": f.get("display"), "category": f.get("category"),
             "r_1m": f.get("r_1m"), "r_3m": f.get("r_3m")} for f in factors_ranked[:n]]


def factor_allocation_advice(master: dict, factors: dict) -> dict:
    """master.json + factors.json -> 配置建议 dict（posture + 超配/低配 + 诚实 caveats）。"""
    verdict = master.get("verdict", "震荡")
    posture = _POSTURE.get(verdict, "中性")

    ic = (factors.get("rotation_ic") or {})
    ic_mean = ic.get("ic_mean")
    if ic_mean is None or abs(ic_mean) < _IC_DEADBAND:
        tilt_mode = "中性（因子排名对下月无方向，风格切换近随机）"
        momentum = None
    elif ic_mean >= 0:
        tilt_mode = "动量（追涨：上月领涨风格倾向延续）"
        momentum = True
    else:
        tilt_mode = "反转（高低切：上月领涨风格倾向回落）"
        momentum = False

    ranked = list((factors.get("ranking") or {}).get("factors") or [])
    ranked.sort(key=lambda f: (f.get("r_1m") if f.get("r_1m") is not None else float("-inf")),
                reverse=True)
    n = max(1, min(3, len(ranked) // 2)) if ranked else 0
    leaders, laggards = _pick(ranked, n), _pick(list(reversed(ranked)), n)

    if momentum is True:                       # 动量：超配领涨、低配垫底
        overweight, underweight = leaders, laggards
    elif momentum is False:                    # 反转：超配垫底（待反弹）、低配领涨
        overweight, underweight = laggards, leaders
    else:                                      # 中性：不主动 tilt，仅列出供观察
        overweight, underweight = [], []

    sources = list(master.get("sources") or [])
    return {
        "asof": master.get("asof"),
        "verdict": verdict,
        "master_score": master.get("master_score"),
        "confidence": master.get("confidence"),
        "posture": posture,
        "equity_hint": _EQUITY_HINT.get(verdict, "中"),
        "tilt_mode": tilt_mode,
        "tilt_basis": {"ic_mean": ic_mean, "icir": ic.get("icir"), "hit_rate": ic.get("hit_rate")},
        "overweight": overweight,
        "underweight": underweight,
        "ranking_top": leaders,            # 透明起见：当月领涨/垫底原始排名
        "ranking_bottom": laggards,
        "caveats": _CAVEATS,
        "sources": sources,
    }
