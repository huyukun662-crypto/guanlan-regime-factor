---
tags: [择时, RSRS, R²]
created: 2026-05-05
updated: 2026-05-05
type: entity
entity_type: indicator
sources:
  - wiki/sources/2026-05-05-openalphas-rsrs-market-thermometer.md
---

# RSRS 修正标准分

> 用 R² 加权的 [[RSRS标准分]]，降低拟合差的可靠性低标准分对策略的影响

## 公式

```
z_t^修正 = z_t · R_t²
```

其中：
- `z_t` = [[RSRS标准分]]
- `R_t²` = 同一回归窗口的 OLS 决定系数（衡量拟合可靠性）

## 解决什么问题

- [[RSRS标准分]] 在拟合效果差的窗口（R² 低）也可能产生大幅偏离的标准分 → 误信号
- 用 R² 加权后：
  - 拟合好（R² ≈ 1）→ 标准分原值传递
  - 拟合差（R² ≈ 0）→ 标准分接近 0，自动屏蔽

## 在素材中的出现

- [[2026-05-05-openalphas-rsrs-market-thermometer]]：RSRS 数学原理 3.3 节

## 与其他变体的关系

- 进一步派生 [[RSRS右偏标准分]] = 修正标准分 × β_t（× 绝对强度）

## 相关页面

- 配套：[[RSRS]]、[[RSRS标准分]]、[[RSRS右偏标准分]]
