---
type: entity
entity_type: mechanism
created: 2026-05-16
sources:
  - [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
---

# random_shuffle回测优化

## 定义

BRAIN 批量回测的工程优化：用 random_shuffle 把大规模回测任务随机化采样，缩减总成本（无需全量跑）。

## 核心要点

- 配合 [[multi simulation]] 用
- 思想可借鉴到自有 grid_search：先随机采样定方向，再聚焦扫优

## 出处

- [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
