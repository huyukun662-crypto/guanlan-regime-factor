---
tags: [资产定价, 学术经典, 因子模型]
created: 2026-05-05
updated: 2026-05-05
type: entity
entity_type: model
sources:
  - wiki/sources/2026-05-05-yhmrshs-residual-mcap.md
---

# Fama-French 三因子模型

> 1993 年 Fama & French 提出的资产定价模型 — [[CAPM]] 的扩展

## 模型形式

```
R_i - R_f = α_i + β_i · (R_m - R_f)        # 市场因子（CAPM 的 β）
          + s_i · SMB                       # Small Minus Big（市值因子）
          + h_i · HML                       # High Minus Low（账面市值比因子）
          + ε_i                             # 残差（特异收益率 idiosyncratic return）
```

## 三因子定义

| 因子 | 定义 | 经济含义 |
|---|---|---|
| **MKT**（市场） | 全市场收益 - 无风险利率 | 系统性风险溢价 |
| **SMB** | 小市值组合收益 - 大市值组合收益 | 规模溢价 |
| **HML** | 高账面市值比组合 - 低账面市值比组合 | 价值溢价 |

## 在量化中的两种用途

### 1. 风险定价 / 评估
对个股 / 组合做时序回归，得到 α / β / s / h，评估 alpha（α）和风险敞口。

### 2. 残差作为另类 alpha
**残差 ε = 特异收益率（idiosyncratic return）** — 是无法被三因子解释的部分，本身可作为反向 alpha 信号。

## 学术演进

| 模型 | 因子数 | 提出年 |
|---|---|---|
| CAPM | 1（市场） | 1964 (Sharpe) |
| **Fama-French 三因子（本模型）** | 3 | 1993 |
| Fama-French 五因子 | 5（+ 盈利能力 RMW + 投资风格 CMA）| 2015 |
| Carhart 四因子 | 4（+ 动量 UMD） | 1997 |
| Q 因子模型（Hou, Xue, Zhang）| 4 | 2015 |

## 在素材中的出现

- [[2026-05-05-yhmrshs-residual-mcap]]：作者提到"特异收益率有基于 CAPM 模型的，也有基于 Fama-French 的，还有基于 Barra 的"

## A 股的本土化

A 股研究通常用：
- **本土 SMB / HML 构建**（用 A 股自己的市值 / PB 排序）
- **行业 / 风格因子**（[[Barra模型]] 思路）
- **CSI 全指对应 MKT 基准**

## 与 [[特异市值因子]] 的关系

特异市值因子的截面回归思路与 Fama-French **同源**（都是"找出基本面解释 → 残差作为 alpha"），但：
- Fama-French 残差：**收益率**对**因子收益**做时序回归
- 特异市值：**对数市值**对**基本面变量**做截面回归
- 都属于"用 OLS 残差挖 alpha"的家族

## 相关页面

- 配套：[[CAPM]]、[[Barra模型]]、[[特异收益率]]
- 应用：[[特异市值因子]]、[[错误定价因子]]
- 主题：[[Alpha挖掘与因子正交性]]、[[量化多因子策略]]
