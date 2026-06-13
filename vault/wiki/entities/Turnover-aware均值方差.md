---
type: entity
entity_type: method
created: 2026-06-05
sources:
  - [[2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes]]
---

# Turnover-aware均值方差

## 定义

在标准均值方差目标函数上加 L1 换手率惩罚项：max E[r]'w - lambda * w'Sigma*w - kappa * ||w - w_prev||_1。

## 核心要点

- 全文 75 处 turnover 体现重要性
- 协方差用 [[Ledoit-Wolf协方差收缩]]
- L1 项 = [[L1换手率惩罚]]
- 缓解 input 微变导致的过度交易
- 相关：[[Anchor-Stabilized HMM框架]] [[Long-only protective specification]]

## 出处

- [[2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes]]
