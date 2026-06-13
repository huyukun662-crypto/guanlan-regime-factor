---
tags: [机器学习, LightGBM, 决策树]
created: 2026-05-05
updated: 2026-05-05
type: entity
entity_type: algorithm
sources:
  - wiki/sources/2026-05-05-openalphas-lightgbm-bayesian.md
---

# Leaf-wise 树生长策略

> 优先选分裂增益最大的叶子节点继续分裂的决策树生长方式

## 一句话定义

LightGBM 采用**带深度限制**的 Leaf-wise（按叶子）生长，而非传统 GBDT 的 Level-wise（按层）生长。每次只对**当前所有叶子中分裂增益最大的那个**进行分裂，效率显著提升。

## Level-wise vs Leaf-wise

| 策略 | 分裂顺序 | 优点 | 缺点 |
|---|---|---|---|
| **Level-wise**（XGBoost 早期 / 传统 GBDT） | 同一层所有节点同时分裂 | 树结构对称、易并行 | **同层无论增益均分裂** → 浪费 |
| **Leaf-wise（本策略）** | 当前叶子中**增益最大**的优先分裂 | 同样深度更优精度，效率高 | 易过拟合，需配合深度限制 |

## 深度限制的必要性

Leaf-wise 不加限制会导致树**长得很深、形状不平衡**，过拟合风险大。LightGBM 提供：
- `max_depth`：最大深度限制
- `num_leaves`：最大叶子数（更直接的复杂度控制）
- `min_data_in_leaf`：单叶最少样本（防长出过拟合的窄叶）

## 在素材中的出现

- [[2026-05-05-openalphas-lightgbm-bayesian]]：LightGBM 四大创新之二

## 相关页面

- 主体：[[LightGBM]]
- 配套：[[直方图算法]]
