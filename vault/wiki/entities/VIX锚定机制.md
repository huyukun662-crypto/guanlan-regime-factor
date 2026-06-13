---
type: entity
entity_type: mechanism
created: 2026-06-05
sources:
  - [[2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes]]
---

# VIX锚定机制

## 定义

VIX（隐含波动率）在 Yang 2026 框架中作为 optimizer 的 reference allocation anchor，不作为收益预测变量也不进 HMM likelihood。

## 核心要点

- 角色：稳定参考配置（reference allocation）
- 不作 predictor（响应 [[Ilmanen 2021]] 因子择时质疑）
- 通过 [[Clipping interval稳定化|[0.5, 1.5] clipping]] 限制极端宏观调整
- 相关：[[CAPE锚定机制]] [[Anchor-Stabilized HMM框架]]

## 出处

- [[2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes]]
