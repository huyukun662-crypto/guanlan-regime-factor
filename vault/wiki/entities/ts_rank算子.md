---
type: entity
entity_type: operator
created: 2026-05-16
sources:
  - [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
---

# ts_rank算子

## 定义

BRAIN 表达式中的一阶算子，对单字段做时间序列排名变换。

## 核心要点

- 时间序列窗口排名 → 信号标准化
- 一阶基础算子，可被二阶 [[group算子]] 和三阶 [[trade_when算子]] 嵌套
- 类比：A 股因子常用的 zscore、minmax 等时序变换

## 出处

- [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
