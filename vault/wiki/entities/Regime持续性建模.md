---
type: entity
entity_type: concept
created: 2026-06-05
sources:
  - [[2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes]]
---

# Regime持续性建模

## 定义

假设市场 regime 不是 i.i.d.，而是按转移概率从一个状态过渡到另一个。HMM 通过转移矩阵 P[s_t | s_{t-1}] 显式建模这一持续性。

## 核心要点

- 相对 GMM (i.i.d.) 的关键改进
- 一旦进入某 regime，倾向于停留若干期再切换
- 与现实金融市场状态持续观察一致（牛熊不会一日切换）
- 相关：[[Gaussian Hidden Markov Model]] [[Gaussian Mixture Model]]

## 出处

- [[2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes]]
