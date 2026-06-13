---
type: entity
entity_type: mechanism
created: 2026-05-16
sources:
  - [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
---

# alpha断点续传

## 定义

BRAIN 批量回测的容错机制：记录已完成的 task 索引，中断后可接续未完成部分。

## 核心要点

- 配合 [[multi simulation]] 必需（单次跑很长）
- 工程价值：避免长任务中断从零开始
- **可借鉴**：自有 grid_search 也可加 task 索引断点

## 出处

- [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
