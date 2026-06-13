---
type: entity
entity_type: rule
created: 2026-05-16
sources:
  - [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
---

# winsorize预处理

## 定义

BRAIN 数据预处理类型之一，对极端值按 3~5 倍标准差聚集（替换为边界值）。

## 核心要点

- 对应 A 股量化常用的 "3σ 去极值"（[[3σ去极值]]）
- 与 ts_backfill、vector vex 等并列的预处理算子族
- V25 已有 3σ 去极值，BRAIN 的 3~5σ 参数可作对照

## 出处

- [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
