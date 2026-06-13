---
type: entity
entity_type: rule
created: 2026-05-16
sources:
  - [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
---

# alpha筛选去冗余

## 定义

BRAIN 工作流的关键筛选规则：用 get_alphas_with_filter 拿候选后，同一数据字段仅保留 Sharp 最高的代表 alpha，减少高冗余计算。

## 核心要点

- 与 [[Alpha挖掘与因子正交性]] 同源（去冗余 = 正交性的工程版）
- 负向信号加负号转正向再纳入比较
- **风险**：可能丢掉"低相关 + 中等 Sharp"的稳健 alpha → 需谨慎
- 相关：[[performance_correlation工具]]

## 出处

- [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
