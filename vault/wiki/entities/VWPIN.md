---
tags: [因子, 微观结构, 信息不对称, A股选股, 高频, 动量衰竭]
created: 2026-05-07
updated: 2026-05-07
type: entity
entity_type: factor
sources:
  - wiki/sources/2022-02-21-gf-hfdata-factor-series-6-info-asymmetry.md
---

# VWPIN（交易量加权知情交易概率）

> [[VPIN]] 在 A 股的本土化改进版本 — 由李平等 2020 提出，广发证券 2022 完整因子化实证；解决 VPIN 在 A 股的实证失效问题

## 一句话定义

固定时间区间（典型 5 min × 48）内，每区间计算"主卖笔数 vs 主买笔数的不平衡比例"，再用区间成交量做权重加权求和：

```
VWPIN = Σ_{i=1}^n w_i · |S_i - B_i| / (S_i + B_i)
w_i = TradVol_i / Σ TradVol_i
```

其中 `S_i` / `B_i` 是第 i 区间的主卖/主买**笔数**（用 Lee-Ready 算法判断方向）。

<!-- confidence: EXTRACTED -->
<!-- evidence: 公式取自[[2022-02-21-gf-hfdata-factor-series-6-info-asymmetry]] §三(三)，原论文为李平等 2020《知情交易概率与风险定价》 -->

## 与 VPIN 的关键差异

| 维度 | [[VPIN]]（Easley et al. 2012）| **VWPIN**（李平等 2020 / 广发 2022）|
|---|---|---|
| 时间分桶 | **等成交量**（volume clock）| **等时间**（典型 5 min）|
| 不平衡度量 | 成交量不平衡 (V_buy - V_sell) | 订单**笔数**不平衡 (B - S) |
| 拆小单抗性 | 弱（仅看量）| **强**（看笔数，能识别拆单）|
| 实时性 | 弱（需预设 V）| **强**（固定时间窗，实时可算）|
| 数据要求 | tick / 1min 量价 | 5min 量 + **主买/卖笔数** |
| 学术地位 | 主流 | A 股本土化改进 |

## A 股因子实证表现（广发 2022）

### 全市场，周度调仓

| 指标 | 值 |
|---|---|
| **IC 均值（中性化后）** | **0.063** |
| 正 IC 占比 | 76.59% |
| 近 10 年累计 IC | 38.72 |
| 多头超额（vs 中证 800）年化 | **+19.07%** |
| 信息比率 | **1.18** |
| 最大回撤 | -33.71% |

### 中证 500 范围内，周度调仓（最佳池）

| 指标 | 值 |
|---|---|
| 多空对冲年化 | +17.61% |
| 年化波动 | 9.99% |
| **信息比率** | **1.76** |
| 最大回撤 | -18.60% |

→ 中证 500 是 VWPIN 在 A 股最有效的池（信息比 1.76 显著高于全市场的 1.18）

### 与 BARRA 因子相关性

低相关 → 可作为新维度加入多因子体系。

## 计算流程（5 步）

```
1. 取个股 t 日的 5min K 线（48 区间）+ 5min 主买/卖笔数（用 Lee-Ready 判方向）
2. 对每区间 i：
     Pin_i = |S_i - B_i| / (S_i + B_i)
3. 区间权重：
     w_i = TradVol_i / Σ TradVol_i
4. VWPIN_t = Σ w_i · Pin_i  （得当日因子值）
5. 平滑因子：VWPIN_smooth_t = 周/月内 VWPIN_t 的均值
   预处理：MAD 去极值 + Z-score + 行业/市值中性化
```

## 选股策略（广发原文）

```
调仓日 → 排序所有股票的 VWPIN
        → 买入 VWPIN 最大的组合
        → 卖出 VWPIN 最小的组合（多空对冲）
```

注意 VWPIN 信号方向：
- **市场层（中证全指）**：VWPIN ↑ → 价格 ↓（与理论吻合，知情资金派发）
- **个股层**：VWPIN ↑ → 个股价格 ↑（与理论相反，原因可能与 A 股投资者结构有关）

→ **个股层用 VWPIN 选股要特别注意：买高 VWPIN（不是低 VWPIN）**

<!-- confidence: EXTRACTED -->
<!-- evidence: [[2022-02-21-gf-hfdata-factor-series-6-info-asymmetry]] §四(一)(二) "当 VWPIN 因子上升，股票价格走强；当 VWPIN 因子下降，股票价格走势回落" -->

## 优势

- **A 股专属验证**：在全市场 + 5 大指数池长期分档单调
- **抗拆单**：基于笔数而非成交量
- **正交性高**：与 BARRA 因子相关性低，可独立加入多因子模型
- **数据要求合理**：5min 主买/卖笔数（聚宽 / Wind 可得）

## 劣势 / 已知限制

- **手续费敏感**：原始 VWPIN 因子换手率高，对千三费率敏感；平滑版（周/月均值）抗成本能力更强
- **个股层信号反向**：原文未充分解释为何个股 VWPIN 与价格正相关，需自行验证
- **5min 区间假设**：48 个等时间区间是参数选择；其他区间数（24、96 等）未在论文中比较
- **依赖主买/卖笔数**：需 Lee-Ready 等算法判断方向；如数据源仅提供成交量需先做转换

## 在动量衰竭早期识别框架中的角色

VWPIN 是 [[VPIN]] 在日频 A 股策略中的**实用替代**：
- VPIN 需 1min 等成交量分桶，工程门槛高
- VWPIN 用 5min 等时间区间 + 笔数不平衡，门槛低
- 两者目的相同：度量订单流毒性 / 知情交易集中度
- 在 [[动量衰竭早期识别]] 三层框架中，VWPIN 作为"微观结构层"的工程版

## V25 / ETF_New 复现 Hook

```python
import pandas as pd
import numpy as np

def vwpin_daily(min_data: pd.DataFrame, n_intervals: int = 48) -> float:
    """单股某交易日 VWPIN.

    Args:
        min_data: 1-min 数据 DataFrame，需含列：
            - close, volume, buy_count（主买笔数）, sell_count（主卖笔数）
            按时间升序，全天 ~240 行
        n_intervals: 一天划分的等时间区间数（默认 48 = 5min × 48）

    Returns:
        当日 VWPIN 值（0 到 1 之间）
    """
    g = min_data.groupby(np.arange(len(min_data)) // (len(min_data) // n_intervals))
    iv = g.agg(buy=('buy_count', 'sum'),
               sell=('sell_count', 'sum'),
               vol=('volume', 'sum'))
    pin = (iv['sell'] - iv['buy']).abs() / (iv['sell'] + iv['buy']).replace(0, np.nan)
    w = iv['vol'] / iv['vol'].sum()
    return float((w * pin).sum())


def vwpin_smooth(daily_vwpin: pd.Series, freq: str = 'W-FRI') -> pd.Series:
    """周/月平滑 VWPIN 因子."""
    return daily_vwpin.resample(freq).mean()
```

**对 ETF_New 的应用**：
- 对 ETF 池 top-1 持仓每日计算 VWPIN（用 ETF 自身的分钟数据，方向用 close-to-close）
- VWPIN 7 日均值持续走高 → 衰竭信号 → 触发减仓 / 切换
- 与 [[VPIN]]、[[九转序列]]、[[低延时趋势]] 形成 [[动量衰竭早期识别]] 框架完整版

## 在素材中的出现

- [[2022-02-21-gf-hfdata-factor-series-6-info-asymmetry]]（广发因子化实证主文）

## 待解决的问题

1. 李平等 2020 原论文《知情交易概率与风险定价 — 基于不同 PIN 测度方法的比较研究》——VWPIN 提出处
2. VWPIN 在 ETF 上（不是个股）的实证 — 论文未涉及
3. 5min vs 15min vs 30min 等时间区间数的鲁棒性
4. 个股层信号反向的根本机制
5. VWPIN 与 [[凸显性因子STR]]、[[特异市值因子]] 的多因子合成

## 相关页面

- 父级：[[VPIN]]、[[PIN]]
- 配套：[[BVC算法]]、[[Lee-Ready算法]]、[[订单流毒性]]
- 主题：[[动量衰竭早期识别]]、[[高频交易与市场微观结构]]、[[Alpha挖掘与因子正交性]]、[[量化多因子策略]]
- 同主题因子：[[凸显性因子STR]]、[[STV凸显性量价因子]]、[[特异市值因子]]
- 项目：[[ETF_New]]、[[V25]]
