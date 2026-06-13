---
tags: [指标, 策略风险, Regime, 衰减, Fabozzi, 寿命管理]
created: 2026-05-31
updated: 2026-05-31
type: entity
entity_type: indicator
sources:
  - wiki/sources/2026-05-31-dbjg-fabozzi-strategy-decay-risk.md
---

# MRP（Minimum Regime Performance，最小 Regime 表现）

> [[Frank Fabozzi]] 团队论文《Measuring Strategy-Decay Risk》提出的策略寿命指标 —— **跨市场状态切分后取最差 Sharpe Ratio**，衡量"策略在最坏环境下还能不能活"

## 一句话定义

```
MRP = Min(Sharpe across regimes)
```

把历史数据切分为多个市场状态（Regime） → 分别算每个阶段的 Sharpe → 取**最差的一个**。

## 与传统指标的根本区别

| 指标 | 回答什么 |
|---|---|
| Sharpe Ratio | 平均水平 |
| 波动率 / VaR / ES | 当策略**有效时**亏多少 |
| MDD | 历史最大损失 |
| **MRP** | **当策略失效时还能不能活下来** |

→ MRP 衡量的是**策略寿命**，不是**单期收益**。

## Regime 切分维度（论文建议）

- **宏观周期**：宽松周期 / 加息周期 / 危机周期 / 流动性扩张周期
- 实战可扩展：波动率高 / 低、利率上 / 下行、风格切换前 / 后等

## 实证发现（1980-2023 经典因子）

**高 Sharpe ≠ 高稳定性**：

| 因子 | 历史 Sharpe | MRP |
|---|---|---|
| Debt Issuance | 1.14 | **-0.05** |
| Investment | 0.45 | **-1.01** |
| Size | 0.16 | **-0.93** |

→ 历史最赚钱的因子，**在最坏 regime 下几乎完全崩溃**。

## 与 [[衰减风险前沿]] 的关系

```
横轴: Sharpe Ratio  (收益)
纵轴: MRP          (寿命)
       ↓
   Decay-Risk Frontier
```

类比 [[Markowitz 均值方差前沿]]，但优化的是 **收益 × 寿命**。

## Python 实现参考

```python
import numpy as np
import pandas as pd

def compute_mrp(returns: pd.Series, regime_labels: pd.Series,
                annualize: int = 252) -> float:
    """
    Minimum Regime Performance — Fabozzi 2024+
    
    Parameters
    ----------
    returns : 日收益率序列
    regime_labels : 同 index 的 regime 类别
    annualize : 年化系数（A 股日频 252）
    
    Returns
    -------
    最小 regime Sharpe
    """
    df = pd.DataFrame({'r': returns, 'regime': regime_labels})
    sharpe_per_regime = df.groupby('regime')['r'].apply(
        lambda x: x.mean() / x.std() * np.sqrt(annualize) if x.std() > 0 else np.nan
    )
    return float(sharpe_per_regime.dropna().min())
```

## 与本知识库已有素材的协同

### 与 V25 IS-OOS 纪律高度一致

V25 工程心得"**禁止用 OOS 反向调参 / 即使回撤明显**" → 实质上是在防止"高 IS Sharpe + 低 OOS MRP"陷阱。<!-- confidence: INFERRED -->

### 与 [[2026-05-05-qpb-industry-pricevolume-etf-rotation]] 反例对照

华西因子在指数上 Sharpe 漂亮，但 ETF 上完全失效 = 经典的 MRP 反例（不同 regime / 标的下崩溃）。<!-- confidence: INFERRED -->

### 与 [[FIP效应]] / [[BIAS减仓]] / [[VPIN]] 的层次差

| 层次 | 工具 |
|---|---|
| **策略元层**（最高） | **MRP** / [[衰减风险前沿]] |
| 行为金融层 | [[FIP效应]] / [[BIAS减仓]] |
| 微观结构层 | [[VPIN]] / [[VWPIN]] |
| 价格结构层 | [[九转序列]] / [[接受规则]] |

MRP 评估**整个策略**，下三层评估**单标的事中风险**。

## 实施注意

- **Regime 切分需要主观**：维度选择影响结果
- **样本量门槛**：每个 regime 至少要够多观测算可靠 Sharpe（论文未明示阈值，建议 ≥ 60 个交易日）
- **AI 策略尤其重要**：AI 模型学习信息结构，衰减更快 → MRP 在 AI 时代价值更高

## V25 集成 Hook

1. 在 `grid_search_*.py` 输出加 MRP 列
2. **极低 MRP 即使 Sharpe 高也淘汰**（硬约束）
3. Decay-Risk Frontier 帕累托优化（4 目标：Sharpe / DD / Ann / MRP）
4. 滚动 MRP 监控：每月重算最近 5 年，大幅恶化 → 触发策略冻结预警

## 在素材中的出现

- [[2026-05-31-dbjg-fabozzi-strategy-decay-risk]]：完整定义 + 实证 + AI 时代意义

## 相关页面

- 上位框架：[[衰减风险前沿]]、[[策略衰减风险]]、[[策略耐久性]]、[[Alpha半衰期]]
- 配套：[[市场Regime切分]]、[[元风险MetaRisk]]
- 同源主题：[[动量衰竭早期识别]]、[[Alpha挖掘与因子正交性]]
- 作者：[[Frank Fabozzi]]
