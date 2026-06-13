---
type: entity
entity_type: mechanism
created: 2026-06-05
sources:
  - [[2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes]]
---

# Clipping interval稳定化

## 定义

VIX/CAPE anchor 调整因子被截断到 [0.5, 1.5] 区间。避免极端宏观读数（如 VIX 80+）对参考配置产生灾难性偏移。

## 核心要点

- 调整因子 = 1 时无修正，0.5 时减仓一半，1.5 时加仓 50%
- 上下界对称，防 anchor 双向极端误导
- 类似 V25 防御篮子 fallback 单仓的保险思路
- 相关：[[VIX锚定机制]] [[CAPE锚定机制]]

## 出处

- [[2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes]]
