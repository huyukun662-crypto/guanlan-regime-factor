---
tags: [Alpha, 半衰期, 衰减, 策略寿命, AI时代]
created: 2026-05-31
updated: 2026-05-31
type: entity
entity_type: concept
sources:
  - wiki/sources/2026-05-31-dbjg-fabozzi-strategy-decay-risk.md
---

# Alpha 半衰期（Alpha Half-Life）

> 借用核物理"半衰期"概念 —— **Alpha 信号从有效到失效衰减一半所需的时间**，是 [[策略耐久性]] 的核心量化指标

## 一句话定义

策略 Sharpe / IC 衰减至**初始值一半**所经历的时间。Alpha 半衰期越短，策略越"短命"，[[策略衰减风险]] 越高。

## 在 Fabozzi 论文中的提出

> "未来量化行业将从研究 Alpha 转向研究 Alpha Half-Life。**谁能预测策略衰减，谁就拥有下一代 Alpha**。"

这是论文导出的最重要研究方向之一：**研究焦点从"发现 Alpha"转向"延长 Alpha 寿命"**。

## 不同策略类型的预期半衰期 (INFERRED)

| 策略类型 | 估计半衰期 | 衰减驱动 |
|---|---|---|
| **AI / ML 因子** | **最短**（论文明确） | 信息结构变化快 |
| 微观结构 / 高频 | 短 | 监管 / 拥挤 |
| 量价技术 | 中 | 拥挤交易 |
| 基本面因子 | 长 | 经济结构慢变 |
| 行为金融因子 | 较长 | 心理结构稳定 |

→ AI 时代，**模型寿命**比模型精度更重要。

## 与 [[MRP最小Regime表现]] 的关系

| 维度 | MRP | Alpha 半衰期 |
|---|---|---|
| 性质 | 横截面（不同 regime） | 时间序列 |
| 衡量 | 最差 regime 下 Sharpe | 衰减率（指数拟合） |
| 关联 | MRP 是 **当前**指标 | 半衰期是 **未来预测** |

两者互补：MRP 看"现在脆不脆"，半衰期看"还能活多久"。

## 估算方法 (INFERRED)

```python
# 简化版：用滚动 Sharpe 拟合指数衰减
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

def estimate_alpha_half_life(rolling_sharpe: pd.Series) -> float:
    """
    用滚动 Sharpe 序列拟合 S(t) = S0 * exp(-t / tau)
    返回半衰期 = tau * ln(2)
    """
    t = np.arange(len(rolling_sharpe))
    s = rolling_sharpe.values
    def model(t, s0, tau): return s0 * np.exp(-t / tau)
    try:
        popt, _ = curve_fit(model, t, s, p0=[s[0], len(s)/2])
        tau = popt[1]
        return tau * np.log(2)
    except Exception:
        return np.nan
```

## 与同源概念的关系

- [[策略耐久性]]：Alpha 半衰期长 → 策略耐久性高（同一现象的不同表达）
- [[策略衰减风险]]：Alpha 半衰期短 → 策略衰减风险高（互为镜像）
- [[衰减风险前沿]]：把 MRP 替换为 Alpha 半衰期可构造**时序衰减前沿**

## V25 集成 Hook

1. **滚动 IC 的半衰期分析**：现有 V25 IC 输出 + 指数衰减拟合
2. **AI 类策略优先 monitoring**：如 [[Q-A3C²]] 等量子强化学习策略
3. **策略冷启动 vs 老化**：新上线策略持续追踪半衰期，到期前主动退役

## 待解决问题

1. 半衰期的最小样本量？（建议 ≥ 5 年滚动 IC）
2. 用 Sharpe 还是 IC 作为衰减目标变量？
3. 非平稳市场（结构突变）下的半衰期如何修正？

## 在素材中的出现

- [[2026-05-31-dbjg-fabozzi-strategy-decay-risk]]：提出"研究 Alpha → 研究 Alpha Half-Life"的方向切换

## 相关页面

- 同源概念：[[策略耐久性]]、[[策略衰减风险]]、[[MRP最小Regime表现]]
- 上位主题：[[动量衰竭早期识别]]、[[Alpha挖掘与因子正交性]]
- 适用方向：[[机器学习选股]]、[[Q-A3C²]]
- 论文：[[Frank Fabozzi]]
