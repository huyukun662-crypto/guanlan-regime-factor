---
type: entity
entity_type: operator
created: 2026-05-16
sources:
  - [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
---

# trade_when算子

## 定义

BRAIN 表达式中的三阶算子，用于设置开平仓条件，灵活实现交易逻辑（如"涨幅超 10% 平仓"）。

## 核心要点

- 嵌套在 [[ts_rank算子]] / [[group算子]] 之上
- 三阶表达式典型层级：trade_when(group(ts_rank(field)))
- 控制换手频率的关键手段（与 [[DK配对换手率控制]] 互补）

## 出处

- [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
