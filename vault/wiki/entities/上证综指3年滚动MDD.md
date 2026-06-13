---
tags: [因子, 底部识别, 价格类]
created: 2026-05-05
updated: 2026-05-05
sources: [wiki/sources/2026-04-23-openalphas-bottom-style-timing.md]
---

# 上证综指 3 年滚动 MDD

> 衡量大盘从前期高点的下跌幅度，是 [[底部双因子识别]] 中的"价格条件"。

## 定义

$$\text{MDD}_t = 1 - \frac{\text{Price}_t}{\max(\text{Price}_{t-250\times3}, \dots, \text{Price}_t)}$$

代码实现：
```python
window_3y = 250 * 3   # 750 个交易日 ≈ 3 年
df["sh_3y_max"] = df["sh_close"].rolling(
    window=window_3y, min_periods=250).max()
df["MDD"] = 1 - df["sh_close"] / df["sh_3y_max"]
```

## 阈值

**MDD > 20%** → 市场进入深度调整区间，满足底部区域的价格条件。

## 与已有概念区别

⚠ 这里的 MDD 是 **基于市场指数**（上证综指）的 **3 年滚动**最大回撤，**不是** 个股或策略层面的 MDD。

V25 复现器有自己的 NAV 层 MaxDD（用于 trail stop，[[backtest_v25.py]] 内）。两者可叠加使用。

## V25 应用候选

加进 V25 的 trail / gate 逻辑：
- 当上证综指 MDD ≥ 20% 且 [[上证综指PE分位]] ≤ 10% 同时满足时，触发"底部抄底模式"
- 此时 trail_recover 阈值从 -3% 放宽到 -1%
- 或者直接覆盖 weekly 的全防御决策，切到偏价值篮子

## 相关页面

- [[底部双因子识别]]
- [[上证综指PE分位]]
- [[2026-04-23-openalphas-bottom-style-timing]]
