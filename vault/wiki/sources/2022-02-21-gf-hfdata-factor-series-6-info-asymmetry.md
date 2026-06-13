---
tags: [素材, 券商研报, 高频因子, VWPIN, 信息不对称, A股选股]
created: 2026-05-07
updated: 2026-05-07
type: source
source_type: 券商研报
priority: S
sources:
  - raw/pdfs/2022-02-21-gf-hfdata-factor-series-6-info-asymmetry.md
images: 80
image_paths: []
---

# 广发证券 2022-02-21《高频数据因子研究系列六：信息不对称理论下的因子研究》

> **作者**：陈原文 / 罗军 / 安宁宁（广发金工，SAC: S0260517080003 等）
> **发布**：2022-02-21 | 65 页 | 金融工程·量化投资专题
> **标题**：信息不对称理论下的因子研究 — 高频数据因子研究系列六

## 基本信息

- **类型**：A 股因子量化研报
- **核心提出**：把学术界的 PIN/VPIN 框架在 A 股本土化为 **VWPIN（交易量加权 PIN）因子**，并在全市场及五个指数池上做完整的分档/IC/对冲策略实证
- **历史地位**：将 Easley-López de Prado-O'Hara 的 **2012 RFS VPIN** 落到 A 股选股层面的关键工程文档；引入李平等 2020 的 VWPIN 改进解决了 VPIN 在 A 股的实证失效

## 研究脉络（论文中给出的演进史）

```
1992 Easley-O'Hara: PIN 概念前身
  ↓
1996 Easley-Kiefer-O'Hara-Paperman (JoF): PIN 模型 — 极大似然估计混合泊松分布
  ↓
2008 Easley-Engle-O'Hara-Wu (JFE): dynamic discrete-time estimate
  ↓
2012 Easley-López de Prado-O'Hara (RFS): VPIN — 非参数估计 + 等成交量分桶 + BVC
  ↓
2020 李平等《知情交易概率与风险定价》: VWPIN — 加入订单数量不平衡 + 物理时间窗
  ↓
2022 广发本篇: VWPIN 在 A 股的因子实证（本报告）
```

## 核心观点

### 1. PIN 模型局限

- 数据时间跨度长 → 非公开信息被稀释
- PIN 实际包含非流动性信息（冗余）
- 部分股票数据量过大 → 极大似然数值溢出

### 2. VPIN 的改进与残留问题

VPIN 公式：

```
VPIN = αμ / (αμ + 2ε) ≈ Σ|V_τ^S - V_τ^B| / (n·V)
```

其中 V 为预设篮子总成交量，BVC 算法分配每根 bar 的 buy/sell 比例为 `Z((P_i - P_{i-1}) / σ_dP)`。

**广发指出 VPIN 的两点不足**：
- 没考虑知情交易者**拆小单**的情况 — 仅反映成交量不平衡，未反映**订单数量**不平衡
- 需要预先用历史数据确定篮子 V → 只能回测，不适用实时监测

### 3. VWPIN 的核心改进（李平等 2020）

```
VWPIN = Σ_{i=1}^n w_i · Pin_i = Σ_{i=1}^n w_i · |S_i - B_i| / (S_i + B_i)

w_i = TradVol_i / Σ TradVol_i
```

- `n`：固定时间范围内的交易区间数（论文用 5 分钟一区间，全天 48 区间）
- `S_i / B_i`：第 i 区间的卖单/买单**笔数**（不再是成交量，避免拆小单失效）
- `w_i`：用区间成交量做权重（保留高交易量区间的信息密度）
- 用 **Lee-Ready 算法** 判断每笔交易方向

**优点**：计算简便、综合订单数量+交易量、不受估计区间限制、适应不同股票市场。

### 4. A 股因子构造与日/周/月平滑

- 频率：每天产生一个 VWPIN 值（基于当日 48 个 5min 区间）
- **VWPIN 因子** = 当日 VWPIN
- **VWPIN 平滑因子** = 周/月内 VWPIN 均值（剔除无数据日）
- 预处理：MAD 去极值 + Z-score 标准化 + 行业/市值中性化

### 5. 关键实证结果（最值钱部分）

#### 全市场 VWPIN 因子，周度调仓

| 指标 | 数值 |
|---|---|
| **IC 均值（中性化后）** | **0.063** |
| 正 IC 占比 | **76.59%** |
| 近 10 年累计 IC | 38.72 |
| 多头 vs 中证 800 年化超额 | **+19.07%** |
| 年化波动 | 16.15% |
| 最大回撤 | -33.71% |
| 信息比率 | **1.18** |

#### 中证 500 范围内，周度调仓（多空对冲表现最佳）

| 指标 | 数值 |
|---|---|
| IC 均值 | 0.04 |
| 正 IC 占比 | 66.12% |
| 多空对冲年化收益 | +17.61% |
| 年化波动 | 9.99% |
| 信息比率 | **1.76** |
| 最大回撤 | -18.60% |

→ **中证 500 是 VWPIN 最有效的池**（信息比 1.76 > 全市场 1.18）

#### 全市场分档单调性

VWPIN 在全市场、中证 1000、中证 800、中证 500、创业板范围内**因子分档单调性显著**（5 档/10 档、月频/周频均验证）。

### 6. 与 BARRA 因子的相关性

> "VWPIN(VWPIN平滑)因子与 BARRA 因子之间的相关性较低，能够将其作为新的高频技术性因子加入多因子模型中。"

→ 横向正交性强，可作为多因子模型的新维度。

### 7. 对手续费的敏感性（重要工程警告）

> "VWPIN 因子由于具有高换手率特征，对手续费费率设置更加敏感。"

平滑因子在千三手续费下，**除沪深 300 外**其他板块仍能在长期获得超额收益；但 VWPIN 原始因子在高费率下显著退化。

## 关键术语 / 公式

- **PIN**：经典模型 = `αμ / (αμ + 2ε)`，需极大似然估计 4 参数 (α, δ, ε, μ)
- **VPIN**：等成交量分桶 + BVC，公式见上
- **VWPIN**：等时间区间（5min）+ 订单笔数不平衡 + 成交量加权
- **BVC（Bulk Volume Classification）**：用 `Z(ΔP / σ_dP)` 分配 buy/sell 比例，比 tick-rule / Lee-Ready 更准
- **Lee-Ready 算法**：基于 quote midpoint 判断每笔交易方向（VWPIN 用此对单笔订单分类）

## 与已有素材 / 实体的关联

- **理论上游**：[[2012-volume-clock-easley-lopez-de-prado-ohara]]、[[2012-vpin-overview-lopez-de-prado]]
- **同主题**：[[2020-quantitative-trading-textbook]]（HFT 教科书第 5 章 LOB / 第 6 章最优执行）
- **本系列其他报告**（论文表 1）：
  - 高频价量数据的因子化方法（系列一）
  - 基于日内高频数据的短周期选股因子（系列二、三）
  - 基于个股羊群效应的选股因子（系列四，与本报告共享 PIN/VPIN 思路）
  - 海量技术指标掘金 Alpha（系列五）
- **A 股因子兄弟**：[[凸显性因子STR]]、[[STV凸显性量价因子]]、[[特异市值因子]] — 都是高频 / 行为金融维度
- **项目应用**：[[ETF_New]]（VWPIN 可作为单 ETF 衰竭检测因子，配合 [[VPIN]] 三层框架）

## 对 ETF_New / V25 项目的启发

1. **VWPIN 比 VPIN 更适合 A 股**：5min 等时间区间比等成交量分桶更易实现；订单笔数 vs 成交量两者都纳入抗拆单
2. **中证 500 是最佳池**（信息比 1.76）— 与 [[ETF_New]] 的 ETF 池中**中盘宽基**（如 510500.SH 中证 500ETF）完全对应
3. **周度调仓最优** — 与 V25 的周频框架天然契合，比日频换手成本更可控
4. **手续费敏感性警示**：VWPIN 平滑版（周/月内均值）抗成本能力更强，原始版本对千三费率敏感 → 上线必须做成本鲁棒性测试
5. **A 股 VWPIN 信号反向**（论文图 4-5）：
   - 全市场层：VWPIN 上升 → 中证全指下跌（与理论吻合）
   - 个股层：VWPIN 上升 → 个股价格走强（与理论相反，作者归因为"国内市场投资者结构特殊")
   - 这条警告非常重要：**ETF 选股层 VWPIN 可能反向使用**

## 原文精彩摘录

> "VWPIN 模型计算了固定时间范围内，交易量加权的订单数量不平衡程度。"

> "中证 500 指数内，VWPIN 因子 IC 均值为 0.04，正 IC 占比为 66.12%，多空对冲策略年化收益率为 17.61%，年化波动率为 9.99%，信息比为 1.76，最大回撤为 18.60%。"

> "通过对数据预处理后的 VWPIN 因子与 VWPIN 平滑因子和 BARRA 因子进行相关性分析，可以发现 VWPIN(VWPIN平滑) 因子与 BARRA 因子之间的相关性较低，因此能够将其作为新的高频技术性因子加入多因子模型中。"

> "VWPIN 因子由于具有高换手率特征，对手续费费率设置更加敏感。"

## 复现 Hook

```python
import pandas as pd
import numpy as np

def compute_vwpin_intraday(min_data: pd.DataFrame, n_intervals: int = 48) -> float:
    """单股某交易日 VWPIN.

    Args:
        min_data: 1-min 数据，需包含 close 价、buy_count（主买笔数）、sell_count（主卖笔数）、
                  volume，按时间排序，全天约 240 行（每 5 分钟聚合后 48 行）
        n_intervals: 全天分多少个等时间区间（默认 48 = 5min × 48）

    Returns:
        当日 VWPIN 值
    """
    # 聚合成 5min 区间
    g = min_data.groupby(np.arange(len(min_data)) // (len(min_data) // n_intervals))
    intervals = g.agg(buy=('buy_count', 'sum'),
                       sell=('sell_count', 'sum'),
                       vol=('volume', 'sum'))
    intervals['pin_i'] = (intervals['sell'] - intervals['buy']).abs() / (
        intervals['sell'] + intervals['buy']).replace(0, np.nan)
    intervals['w_i'] = intervals['vol'] / intervals['vol'].sum()
    return float((intervals['w_i'] * intervals['pin_i']).sum())


def vwpin_smooth(daily_vwpin: pd.Series, window: str = 'W') -> pd.Series:
    """VWPIN 平滑因子（周/月均值）"""
    return daily_vwpin.resample(window).mean()
```

**集成到 [[ETF_New]] 思路**：
- 对 ETF 池的每只 ETF 算 VWPIN（用其底层成份股加权或直接用 ETF 自身的分钟数据）
- 当持仓 ETF 的 VWPIN 7 日均值持续走高 → 衰竭信号 → 触发减仓
- 与 [[九转序列]]、[[低延时趋势]] 一同纳入 [[动量衰竭早期识别]] 三层框架

## 优先级评分

- A 股实证完整性：⭐⭐⭐⭐⭐ — 全市场 + 5 大指数池 + 多窗口 + 多频率
- 工程可复现性：⭐⭐⭐⭐ — 公式明确，需 5min 主买/卖笔数数据（聚宽/Wind 可得）
- 与 ETF_New 项目契合度：⭐⭐⭐⭐ — 中证 500 作为最佳池天然适配 ETF
- 理论根基：⭐⭐⭐⭐⭐ — 完整继承 Easley-López de Prado-O'Hara 体系
- 警示完整性：⭐⭐⭐⭐ — 明确指出对手续费敏感

**优先级综合：S 档**

## 待解决的问题（后续素材搜集方向）

1. 李平等 2020《知情交易概率与风险定价 — 基于不同 PIN 测度方法的比较研究》原文 — VWPIN 提出处
2. 广发"高频数据因子研究系列"其他 5 篇报告 — 完整高频因子家族
3. VWPIN 在 ETF 上的实证（论文仅涉及个股选股）— 待自行复测
4. VWPIN 信号在个股层"反向"的具体机制（论文给出现象但归因不充分）

## 相关页面

- 实体：[[VPIN]]、[[VWPIN]]、[[PIN]]、[[BVC算法]]、[[订单流毒性]]、[[Lee-Ready算法]]
- 主题：[[高频交易与市场微观结构]]、[[动量衰竭早期识别]]、[[Alpha挖掘与因子正交性]]、[[量化多因子策略]]
- 上游素材：[[2012-volume-clock-easley-lopez-de-prado-ohara]]、[[2012-vpin-overview-lopez-de-prado]]
- 项目：[[ETF_New]]、[[V25]]
- 同发布机构：[[广发证券]]
- 同人物：[[陈原文]]、[[罗军]]、[[安宁宁]]
