---
tags: [因子, 风格择时, 阈值]
created: 2026-05-05
updated: 2026-05-05
sources: [wiki/sources/2026-04-23-openalphas-bottom-style-timing.md]
---

# SRI_balance（风格均衡水平）

> [[SRI]] 指标的合理中枢，定义风格切换的触发阈值。

## 定义

$$\text{SRI}_{balance} = \frac{\text{SRI}_{max} + \text{SRI}_{min}}{2}$$

代码实现：
```python
SRI_max = df["SRI"].max()
SRI_min = df["SRI"].min()
df["SRI_balance"] = (SRI_max + SRI_min) / 2
df["SRI_lower_limit"] = 0.77   # 历史悲观下限
```

## 历史经验值（2005 年至今）

- **静态均衡值 ≈ 0.83**
- **历史悲观下限 = 0.77**

## 切换语义

当 SRI 回落至均衡值附近时：
- 成长与价值风格的性价比回到均衡
- 成长风格的相对劣势基本消失
- **是触发"价值 → 成长"切换的核心信号**

历史回测：6 轮大底中 5 轮在 SRI 回到 0.83 附近触发切换，切换后 6 个月成长平均超额 32.7%。

## 静态 vs 动态均衡

笔记原文同时提到：
- **静态均衡**：全历史区间 SRI 极值均值
- **动态均衡**：240 个月（20 年）滚动窗口的 SRI 均值（适配市场长期结构变化）

代码版本采用静态。

## 注意事项

⚠ **样本量限制**：基于 6 个底部事件得出的 5/6 切换成功率，置信度有限。 <!-- confidence: EXTRACTED -->

## 相关页面

- [[SRI]]
- [[底部双因子识别]]
- [[风格轮动三阶段模型]]
- [[2026-04-23-openalphas-bottom-style-timing]]
