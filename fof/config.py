"""Configuration for the regime-switch FOF — immutable dataclasses.

`FOFConfig` holds every tunable of the "4 铁律" + regime gate + costs so a run is fully
described by one config object (mirrors the ETF6.5 champion-JSON convention). Sleeve
*metadata* (codes, display names, roles) lives in `SLEEVES`; the per-sleeve trading
*rule* lives in `fof/sleeves.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

# ETF universe — bare 6-digit code -> (display name, Tushare exchange suffix).
ETF_NAMES: dict[str, str] = {
    "510300": "沪深300ETF",
    "510500": "中证500ETF",
    "159915": "创业板ETF",
    "513100": "纳指ETF",
    "512890": "红利低波ETF",
    "518880": "黄金ETF",
    "511260": "十年国债ETF",
    "511380": "可转债ETF",
    "511880": "银华日利(货基)",
}


@dataclass(frozen=True)
class SleeveDef:
    """A FOF building block — one low-correlation sub-strategy over real ETFs."""
    name: str            # machine key, e.g. "momentum_rotation"
    display: str         # Chinese label for the dashboard
    codes: tuple[str, ...]
    rule: str            # rule key dispatched in fof/sleeves.py
    role: str            # 进攻 / 防御 / 宽基锚 / 避险 / 偏债α / 现金
    params: dict[str, Any] = field(default_factory=dict)


# The 5 equity/defensive sleeves + the money-market fallback. `do_t` (intraday) is
# intentionally replaced by `convertible_bond` so every sleeve is a faithful real-data
# replay; a daily `do_t` proxy can be added later as one more SleeveDef.
SLEEVES: tuple[SleeveDef, ...] = (
    SleeveDef("momentum_rotation", "动量轮动",
              ("510300", "510500", "159915", "513100"), "momentum",
              "进攻", {"lookback": 21, "ma": 20}),
    SleeveDef("dividend_defense", "红利低波防御",
              ("512890",), "ma_filter", "防御", {"ma": 60}),
    SleeveDef("broad_index", "宽基锚(沪深300)",
              ("510300",), "ma_filter", "宽基锚", {"ma": 200}),
    SleeveDef("gold_bond_defense", "黄金+国债避险",
              ("518880", "511260"), "static_blend", "避险",
              {"weights": {"518880": 0.5, "511260": 0.5}, "rebalance": "M"}),
    SleeveDef("convertible_bond", "可转债",
              ("511380",), "ma_filter", "偏债α", {"ma": 60}),
    # --- 从内置 vault/ 金工研报新增的策略 sleeve ---
    # Parabolic SAR 抛物线转向：趋势跟踪 + 动态止损（Brain: jq-sar-indicator-explainer）
    SleeveDef("sar_trend", "SAR趋势(沪深300)",
              ("510300",), "sar", "趋势α", {"af_init": 0.02, "af_max": 0.2}),
    # SRI 风格轮动：成长(创业板)↔价值(红利低波) 相对强度切换
    # （Brain: openalphas-bottom-style-timing；此处用 ETF 比值作 SRI 的 ETF 级代理）
    SleeveDef("style_rotation", "SRI风格轮动",
              ("159915", "512890"), "style_sri", "风格α",
              {"growth": "159915", "value": "512890", "lookback": 60}),
    # 双因子抄底：3年滚动MDD≥20% & 上证50 PE分位≤10% → 持创业板抢反弹，否则空仓
    # （Brain: 2026-04-23-openalphas-bottom-style-timing.md）
    SleeveDef("bottom_buyer", "底部双因子抄底",
              ("510300", "159915"), "bottom_buyer", "抄底α",
              {"ref": "510300", "hold": "159915", "mdd_win": 750, "mdd_thr": 0.20,
               "pe_pct_thr": 0.10}),
    # Bill Williams 鳄鱼线：三条位移均线多头排列(lips>teeth>jaw)持有，否则空仓
    # （Brain: 2026-05-05-qpb-alligator-index-timing-rotation.md）
    SleeveDef("alligator_trend", "鳄鱼线趋势",
              ("510300",), "alligator", "趋势α",
              {"jaw": 13, "jaw_sh": 8, "teeth": 8, "teeth_sh": 5, "lips": 5, "lips_sh": 3}),
)

MONEY_MARKET = SleeveDef("money_market", "货基/逆回购", ("511880",), "cash", "现金", {})


@dataclass(frozen=True)
class FOFConfig:
    """All tunables for one FOF backtest run."""
    start: str = "2020-01-01"
    asof: str = "2026-06-05"
    benchmark: str = "510300"

    # 铁律1 — recent-momentum selection lookback (trading days, ~30 calendar).
    mom_lookback: int = 21
    # window over which period-max-DD / calmar / sharpe are evaluated for selection.
    eval_window: int = 63

    # 铁律2 — drawdown blacklist + calmar gate + cash fallback.
    # On the corrected full-window data (2020-2026, incl. the 2022 bear) over the 9-sleeve pool,
    # scripts/grid_search.py (128-config sweep) keeps calmar_min=1.5 + min_pass=1 + ranging-gate
    # 0.8, and — per the user's "收益过低，重新调校" — lifts max_weight 0.50->1.0 (进取档).
    # vs the prior champion: ann 8.5%->11.3%, Sharpe 1.06->1.13, Calmar 1.10->1.20, with DD
    # -9.4% still inside the equal-weight baseline's -9.5%. The ranging de-risk gate is kept;
    # the single-sleeve cap is the lever we relaxed (the momentum winner is no longer diluted
    # into money-market). Evidence: outputs/grid_search.csv.
    dd_blacklist: float = 0.15        # blacklist if period_max_dd worse than -15%
    calmar_min: float = 1.5
    min_pass: int = 1                 # fewer survivors -> 100% money-market

    # 铁律3 — rank survivors by this metric.
    rank_metric: str = "sharpe"
    max_holdings: int = 4

    # 铁律4 — inverse-drawdown risk parity + hard single-sleeve cap.
    # 进取档 (用户调校 2026-06): cap 放到 1.0 = 实质取消单sleeve上限，消除「单survivor截断->超出丢货基」
    # 的现金拖累，年化 8.5%->11.3%。代价：分散度下降（动量赢家可满仓），回撤 -7.96%->-9.4%（仍≤等权）。
    weight_method: str = "risk_parity"
    max_weight: float = 1.0

    # regime gate — total equity exposure multiplier by regime label.
    regime_gate: dict[str, float] = field(
        default_factory=lambda: {"trend": 1.0, "ranging": 0.8, "bear": 0.0})

    # regime 标签来源 — FOF 回测门控。
    # "rule"（默认）: RSRS+200MA 规则（fof/regime.py:label_series）——128 组 grid 实测更优。
    # "hmm" : 大势研判 HMM×ER（fof/master.py，walk-forward 防前视）。实测接入回测后 FOF 明显变差
    #   （年化 11.3%→5.5%、夏普 1.13→0.52、回撤 -9.4%→-12.2%），故 HMM 仅驱动「大势研判」展示栏，
    #   不作回测门控默认；保留此开关供切换/研究。证据：outputs/grid_search.csv + docs/before-after.md。
    regime_source: str = "rule"
    hmm_states: int = 4               # 稳态/平静/履冰/危机
    er_window: int = 10              # Kaufman 效率比窗口
    hmm_seed: int = 42               # hmmlearn 复现种子
    # 大势研判（HMM/ER）的基底指数——中证全指（全市场代表性优于沪深300；用户 2026-06 指定）。
    # 仅影响大势研判展示，不影响 FOF 回测基准（benchmark 不变）。
    master_index: str = "000985.CSI"
    # 大势综合分三轴权重：HMM 姿态 / ER 趋势确认 / 基本面估值。
    master_weights: dict[str, float] = field(
        default_factory=lambda: {"hmm": 0.5, "er": 0.2, "fundamental": 0.3})

    # execution / costs.
    rebalance: str = "M"              # month-end decide, next-open execute
    cost_bps: float = 5.0             # one-way transaction cost in bps
    min_history_days: int = 60        # prune sleeves with shorter underlying history

    def to_dict(self) -> dict:
        return asdict(self)


DEFAULT_CONFIG = FOFConfig()


# 因子看板：真实 A股风格/Smart-beta 指数代理。(key, 显示, long_code, short_code, 类别)
# short_code=None -> 用 long 原始收益（市场因子）；long_code="XSEC" -> 横截面构造（动量/反转）。
FACTOR_DEFS = [
    ("mkt", "市场", "000300.SH", None, "市场"),
    ("smb", "小市值", "000852.SH", "000300.SH", "规模"),
    ("micro", "微盘", "932000.CSI", "000300.SH", "规模"),
    ("large", "大盘", "000016.SH", "000300.SH", "规模"),
    ("hml", "价值", "399371.SZ", "399370.SZ", "价值"),
    ("growth", "成长", "399370.SZ", "000300.SH", "成长"),
    ("chinext", "科技成长", "399006.SZ", "000300.SH", "成长"),
    ("dividend", "红利", "000922.CSI", "000300.SH", "红利"),
    ("lowvol", "低波", "H30269.CSI", "000300.SH", "低波"),
    ("quality", "质量", "931151.CSI", "000300.SH", "质量"),
    ("momentum", "动量", "XSEC", None, "动量"),
    ("reversal", "反转", "XSEC", None, "反转"),
]
# 横截面动量/反转的指数池（按 N 日收益排序做 long-short）
FACTOR_XSEC_POOL = ["000300.SH", "000905.SH", "000852.SH", "399006.SZ",
                    "399370.SZ", "399371.SZ", "000922.CSI"]
