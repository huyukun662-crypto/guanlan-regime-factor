---
tags: [机器学习, 集成学习, 决策树]
created: 2026-05-05
updated: 2026-05-05
type: entity
entity_type: algorithm
sources:
  - wiki/sources/2026-05-05-openalphas-lightgbm-bayesian.md
---

# GBDT

> Gradient Boosting Decision Tree — 梯度提升决策树

## 一句话定义

GBDT 是一种**加法模型**：通过前向分步算法，每一步学习一棵新树拟合**前一步残差的负梯度方向**，最终预测值是所有树输出之和。

## 数学结构

加法模型：
```
ŷ_i = Σ_{k=1..K} f_k(x_i),    f_k ∈ F
```

目标函数（损失 + 正则）：
```
ℒ = Σ_{i=1..n} l(y_i, ŷ_i) + Σ_{k=1..K} Ω(f_k)
```

正则化项（控制单树复杂度）：
```
Ω(f) = γT + (1/2) λ Σ_{j=1..T} w_j²
```

其中 T 是叶节点数，w_j 是叶节点权重。

## 主要实现对比

| 实现 | 优势 | 劣势 |
|---|---|---|
| Scikit-learn `GradientBoostingRegressor` | 简单 | 慢，不适合大数据 |
| **XGBoost** | 经典，工业稳定 | 内存占用大 |
| **[[LightGBM]]** | **快、省内存、大样本友好** | 离散化略损精度 |
| CatBoost | 类别特征友好 | 速度中等 |

## 在量化场景中的角色

- 端到端收益率回归（[[IC选股策略]]）
- 截面排序 → Top-N 选股
- 多因子非线性合成

## 在素材中的出现

- [[2026-05-05-openalphas-lightgbm-bayesian]]：[[LightGBM]] 的算法基础

## 相关页面

- 衍生：[[LightGBM]]
- 主题：[[机器学习选股]]
