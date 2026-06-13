---
type: entity
entity_type: method
created: 2026-06-05
sources:
  - [[2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes]]
---

# Expanding window walk-forward

## 定义

回测协议：训练集随时间扩张（不丢早期数据），每个时点用过去全部数据 refit 模型，预测下一时点。Yang 2026 在 2013-2023 严格采用。

## 核心要点

- model selection / HMM estimation / 配置都在 expanding window 中
- 防 leakage（区别于一般因子择时研究可能用长样本预估参数）
- 月度 refit
- 相关：[[Leakage控制协议]] [[Anchor-Stabilized HMM框架]]

## 出处

- [[2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes]]
