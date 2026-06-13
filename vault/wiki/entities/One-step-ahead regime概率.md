---
type: entity
entity_type: mechanism
created: 2026-06-05
sources:
  - [[2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes]]
---

# One-step-ahead regime概率

## 定义

HMM 在 t 时刻预测下一时点（t+1）各 regime 的边际概率 P[s_{t+1}=k | history_t]。Yang 2026 用此概率作为 MV 优化的输入。

## 核心要点

- 包含转移矩阵效应：当前 regime 概率 × 转移矩阵
- 反映 "下一期可能出现什么状态" 的不确定性
- 喂给 MV 后得到不依赖单一状态判定的稳健权重
- 相关：[[Gaussian Hidden Markov Model]] [[Anchor-Stabilized HMM框架]]

## 出处

- [[2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes]]
