---
type: entity
entity_type: framework
created: 2026-06-05
sources:
  - [[2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes]]
---

# Anchor-Stabilized HMM框架

## 定义

Yang 2026 提出的多因子动态配置框架：用 Gaussian HMM 拟合因子横截面 regime，把一步前向 regime 概率作为输入，通过 turnover-aware 均值方差优化求权重；VIX 和 CAPE 作 anchor 稳定参考配置而非作收益预测变量。

## 核心要点

- 输入：因子横截面收益 + VIX/CAPE 锚定
- 输出：可执行多因子配置权重
- 实证：long-only Sharpe 1.33 / DD -3.64%（2013-2023 美股）
- 相关：[[Gaussian Hidden Markov Model]] [[Turnover-aware均值方差]] [[VIX锚定机制]] [[CAPE锚定机制]] [[Long-only protective specification]]

## 出处

- [[2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes]]
