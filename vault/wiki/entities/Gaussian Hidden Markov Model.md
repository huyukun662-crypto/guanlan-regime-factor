---
type: entity
entity_type: method
created: 2026-06-05
sources:
  - [[2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes]]
---

# Gaussian Hidden Markov Model

## 定义

高斯隐马尔可夫模型：观测服从 regime-依赖的多元高斯，regime 之间按 Markov 转移矩阵切换。本文用于建模因子横截面收益的 regime 持续与转换。

## 核心要点

- 相对 [[Gaussian Mixture Model|GMM]] 的核心改进：显式建模 regime 持续（[[Regime持续性建模]]）
- 拟合后用 Viterbi / smoothed posterior 推断状态
- 月度 refit 在 expanding window 上
- 相关：[[Regime持续性建模]] [[One-step-ahead regime概率]]

## 出处

- [[2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes]]
