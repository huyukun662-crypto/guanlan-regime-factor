---
tags: [机器学习, AutoML, 进化算法, Google Brain]
created: 2026-05-05
updated: 2026-05-05
type: entity
entity_type: algorithm
sources:
  - wiki/sources/2026-05-05-openalphas-alphazero-factor-mining.md
---

# AutoML-Zero

> Google Brain 团队 2020 年提出的零先验 AutoML 算法

## 一句话定义

AutoML-Zero 能够**从最基础的数学算子出发**，通过进化算法**自动生成完整的机器学习算法**，无需人工预定义任何模型结构。论文：Real et al., "AutoML-Zero: Evolving Machine Learning Algorithms From Scratch", ICML 2020。

## 核心思想

- 把"模型搜索"变成"程序搜索"
- 用基础数学算子（+ - × ÷ 比较 ...）作为基本操作
- 进化算法搜索"哪些算子组合 + 如何组合 = 好的预测算法"
- **完全随机变异**，期望大量样本中产生有效结构

## 在因子挖掘领域的扩展：[[AlphaZero因子挖掘]]

中信证券将这一思路迁移到 A 股量价因子挖掘，针对原算法的低效率问题做了三大改进：
1. **图状程序表达式**（vs 传统 GP 的树状）
2. **关联变异约束**（vs 完全随机变异）
3. **A 股专用算子**（时序、横截面）+ 长度约束 + 退化变异

## 在素材中的出现

- [[2026-05-05-openalphas-alphazero-factor-mining]]：作为 AlphaZero 因子框架的算法源头被引用

## 相关页面

- 衍生：[[AlphaZero因子挖掘]]
- 主题：[[Alpha挖掘与因子正交性]]
