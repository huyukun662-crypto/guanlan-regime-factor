---
tags: [投资组合理论, 经验贝叶斯, 参数不确定性, Markowitz]
created: 2026-05-06
updated: 2026-05-06
type: entity
entity_type: method
sources:
  - wiki/sources/2020-quantitative-trading-textbook.md
---

# NPEB 法则

> Nonparametric Empirical Bayes — **非参数经验贝叶斯**最优投资组合权重法则

## 一句话定义

NPEB 是 [[Tze Leung Lai]]（黎子良）团队提出的**处理参数不确定性的投资组合权重计算方法**，解决传统 Markowitz **均值-方差优化对参数估计极度敏感**的问题（"误差最大化机器"问题）。**用 Bootstrap + 经验贝叶斯**估计收益率分布，得到更稳健的权重。

## 解决的问题

### 经典 Markowitz 困境
```
max  w'μ - (γ/2)·w'Σw
s.t. w'1 = 1
```
- μ = 期望收益向量
- Σ = 协方差矩阵
- γ = 风险厌恶

**致命缺陷**：μ 和 Σ 是**估计值** → 估计误差被 max 操作**放大** → 实际表现极不稳定（业界戏称"误差最大化机器"）

### 传统应对方法的不足
- 收缩估计（Shrinkage，James-Stein 1956）：单点估计的改进
- Bayesian Markowitz：依赖先验设定
- 鲁棒优化（Robust Optimization）：保守过头

## NPEB 的核心思路

> **不假设参数分布形式**（非参数）+ **用样本本身估计先验**（经验贝叶斯）

### 步骤
1. **Bootstrap 重抽样**：从历史收益率反复抽样 → 多组 (μ, Σ) 估计
2. **经验贝叶斯**：把这些估计看作来自一个未知先验，用样本估计先验
3. **后验权重**：在所有可能的 (μ, Σ) 上做 mean-variance 最优化的**期望**
4. **加入时序效应**（2.7 节）：进一步引入 ARIMA / GARCH / 鞅回归等时序模型

## 关键参考

- 论文：Lai, T. L. & Xing, H. (2008). *Statistical Models and Methods for Financial Markets* — 本书前 6 章广泛引用 Lai-Xing 2008 作为基础
- Bootstrap 估计：依赖 Efron 1979 经典工作

## 与已有素材的关联

### 与 [[特异市值因子]]（量化拯救散户）的方法论同源
- NPEB：用 Bootstrap 估计**参数分布** → 得到稳健权重
- 特异市值：用 OLS 残差**剥离已知部分** → 得到 alpha 信号
- 都是"基于已知模型 → 提取残差 / 不确定性"的思路

### 与 [[Fama-French三因子模型]]
- Fama-French 是**线性因子模型**，参数是 β、s、h
- NPEB 可作为 Fama-French 之上的**鲁棒权重计算**层
- 解决"Fama-French 估计 β 后如何用 β 配置组合"的问题

### 与本知识库的工程实务
- V25 项目目前用**等权重 + 动量加权**（避免 Markowitz 不稳定）
- NPEB 是从根本上解决这个问题的学术方案
- 但实现复杂度高 → V25 暂不优先

## 优势 / 劣势

✅ **统计学严谨**（不依赖参数分布假设）
✅ 显著降低 Markowitz 的估计误差影响
✅ Bootstrap + 经验贝叶斯都是成熟工具

⚠ 计算成本高（每期需 Bootstrap 多组）
⚠ 实操中**依然依赖样本质量**（极端行情下 Bootstrap 也失效）
⚠ 行业接受度有限（业界更多用收缩估计 / 风险平价等简化方案）

## 在素材中的出现

- [[2020-quantitative-trading-textbook]]：第 2.5 节首次提出 + 2.6-2.7 节扩展到时序模型

## 相关页面

- 主题：[[量化多因子策略]]、[[Alpha挖掘与因子正交性]]、[[高频交易与市场微观结构]]
- 配套：[[Tze Leung Lai]]、[[现代投资组合理论]]（待创建）、[[Fama-French三因子模型]]
- 来源：[[2020-quantitative-trading-textbook]]
