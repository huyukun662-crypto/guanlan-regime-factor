---
tags: [因子, 底部识别, 估值类]
created: 2026-05-05
updated: 2026-05-05
sources: [wiki/sources/2026-04-23-openalphas-bottom-style-timing.md]
---

# 上证综指 PE 分位

> 衡量当前 PE_TTM 在过去 3 年历史区间中的相对位置，是 [[底部双因子识别]] 中的"估值条件"。

## 定义

$$\text{PE}_{percentile,t} = \frac{\text{Count}(\text{PE}_i < \text{PE}_t,\ i \in [t-250\times3,\ t])}{250 \times 3} \times 100\%$$

代码实现（用 pandas 滚动 rank）：
```python
df["pe_percentile"] = df["sh_pe_ttm"].rolling(
    window=window_3y, min_periods=250).rank(pct=True) * 100
```

数据源：`akshare.index_value_analysis_em(symbol="000001")` 取上证综指 PETTM。

## 阈值

**PE_percentile < 10%** → 市场估值处于历史极低水平，满足底部区域的估值条件。

## 与"在值程度"对照

[[在值程度]]（Moneyness）也是相对位置度量，但：
- 在值程度：可转债"转股价值/转债价格"的相对位置
- PE 分位：市场估值在历史窗口的位置

两者都属于"用相对位置而非绝对值"做信号触发的设计哲学。 <!-- confidence: INFERRED -->

## 注意事项

- 滚动窗口 3 年（250×3=750 日），太短会过敏，太长会迟钝
- `min_periods=250` 保证至少 1 年历史
- PE 分位本身在结构性变化（如 2014 年前后市场风格切换）中有失真风险

## 相关页面

- [[底部双因子识别]]
- [[上证综指3年滚动MDD]]
- [[在值程度]]
- [[2026-04-23-openalphas-bottom-style-timing]]
