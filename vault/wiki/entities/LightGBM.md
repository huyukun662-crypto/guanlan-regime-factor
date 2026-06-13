---
tags: [机器学习, GBDT, 工具]
created: 2026-05-05
updated: 2026-05-05
type: entity
entity_type: tool
sources:
  - wiki/sources/2026-05-05-openalphas-lightgbm-bayesian.md
---

# LightGBM

> Light Gradient Boosting Machine — 微软开源的高效 GBDT 框架

## 一句话定义

LightGBM 是微软开源的梯度提升决策树（[[GBDT]]）框架，在传统 GBDT 基础上做了**直方图算法 + Leaf-wise 树生长 + GOSS + EFB** 四项核心创新，**内存占用降低 80%+，训练速度大幅提升**，完美适配量化投资中大样本、高维特征、高噪声的数据分析场景。

## 数学基础

GBDT 加法模型：

```
ŷ_i = Σ_{k=1..K} f_k(x_i),    f_k ∈ F
```

目标函数（损失 + 正则）：

```
ℒ = Σ_{i=1..n} l(y_i, ŷ_i) + Σ_{k=1..K} Ω(f_k)
Ω(f) = γT + (1/2) λ Σ_{j=1..T} w_j²
```

其中：T = 叶子节点数；w_j = 第 j 个叶子的权重；γ、λ = 正则化系数。

## 四大核心算法创新

### 1. [[直方图算法]]（Histogram Algorithm）
- 将连续特征值离散化为 k 个整数分箱
- 构建宽度为 k 的直方图
- 遍历样本时只需累加离散化值到对应分箱，最终遍历直方图找最优分裂点
- **内存占用降低 80%+**，能高效处理百万级样本

### 2. 带深度限制的 [[Leaf-wise树生长策略]]
- 传统 GBDT：Level-wise 按层生长（同层所有节点无论增益均分裂 → 浪费）
- LightGBM：Leaf-wise（优先选分裂增益最大的叶子节点）+ 深度限制（防过拟合）

### 3. GOSS（Gradient-based One-Side Sampling）
- 单边梯度采样：保留大梯度样本 + 随机采样小梯度样本
- 在保持精度的同时大幅减少计算量

### 4. EFB（Exclusive Feature Bundling）
- 互斥特征捆绑：将极少同时非零的特征捆绑成一个特征
- 高维稀疏数据下大幅降低特征维度

## 量化投资场景中的关键超参

| 超参 | 作用 |
|---|---|
| `min_data_in_leaf` | 单叶节点最少样本数 — 在噪声高的股票数据中防过拟合**最关键** |
| `feature_fraction` | 列采样比例 — 提升泛化能力 |
| `bagging_fraction` + `bagging_freq` | 行采样 — 配合 `bagging_freq` |
| `lambda_l1` / `lambda_l2` | 叶权重 L1/L2 正则化系数 |
| `num_leaves` / `max_depth` | 控制模型复杂度 |
| `learning_rate` + `n_estimators` | 学习率 + 迭代次数 |

通常用 [[贝叶斯超参优化]]（[[Optuna]]）做 50 轮搜索，目标函数 = 验证集 IC。

## 适用场景

✅ A 股 / 美股 / 期货收益率回归
✅ 横截面截面 IC 选股
✅ 大样本（>10⁶）+ 高维特征（>100）
✅ 异质性强、非线性关系丰富的金融数据

⚠ 需配合严格的[[时序划分]] + 防数据泄露
⚠ 样本外失效风险高，必须严格 IS/OOS 分离

## 在素材中的出现

- [[2026-05-05-openalphas-lightgbm-bayesian]]：S 档；端到端 5 日收益率预测，年化 38.7% / MDD 12.3%；使用 [[Optuna]] 50 轮贝叶斯搜索

## 与其他实体的关联

- 输入：[[akshare]] 数据
- 验证指标：[[ICIR]]
- 替代方案：[[AlphaZero因子挖掘]]（输出可解释因子，但训练成本更高）；[[BS模型]] / [[ZL模型]] 错误定价因子（机理驱动 vs 数据驱动）

## 相关页面

- 主题：[[机器学习选股]]、[[量化多因子策略]]、[[Alpha挖掘与因子正交性]]
- 配套：[[贝叶斯超参优化]]、[[Optuna]]、[[3σ去极值]]、[[Z-score标准化]]、[[时序划分]]、[[IC选股策略]]
