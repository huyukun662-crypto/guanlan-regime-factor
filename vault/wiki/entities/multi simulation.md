---
type: entity
entity_type: mechanism
created: 2026-05-16
sources:
  - [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
---

# multi simulation

## 定义

BRAIN 顾问专属批量回测模式，单次提交 8 个 mode × 10 个子任务 = 80 个并发槽位，复用数据后回测速度显著高于 single simulation。

## 核心要点

- 适用顾问账号；用户只能用 [[single simulation]]
- 一个表达式错误整组失败 → 需逐个子任务排查
- 配合 [[alpha断点续传]] 抗中断
- 配合 [[random_shuffle回测优化]] 控制大规模成本
- 切片建议：顾问按 8×10 切片

## 出处

- [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
