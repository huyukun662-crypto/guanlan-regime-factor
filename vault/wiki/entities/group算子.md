---
type: entity
entity_type: operator
created: 2026-05-16
sources:
  - [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
---

# group算子

## 定义

BRAIN 表达式中的二阶算子，按横截面分组（市值/波动率/平台分组/自定义分桶）对一阶信号做组内比较。

## 核心要点

- 实现横截面中性化的基础
- 支持自定义分组（市值、波动率分桶）
- 嵌套：group(ts_rank(field))
- 相关：[[ts_rank算子]] [[trade_when算子]] [[neutralization鲁棒性检测]]

## 出处

- [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
