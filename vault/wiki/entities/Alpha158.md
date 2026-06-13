---
tags: [因子库, Qlib, 量价因子, Microsoft]
created: 2026-05-05
updated: 2026-05-05
type: entity
entity_type: factor_library
sources:
  - wiki/sources/2026-05-05-qpb-industry-pricevolume-etf-rotation.md
---

# Alpha158

> [[Qlib]] 内置的 **158 个经典量价因子**库

## 一句话定义

微软 Qlib 框架内置的 158 个量价因子集合，涵盖**收益率 / 波动率 / 动量 / 反转 / 成交量 / 资金流 / 量价相关**等多个家族，适用作多因子模型的快速基准。

## 因子类别（典型）

- **K-bar**：开盘 / 最高 / 最低 / 收盘的相对关系
- **Roll**：滚动窗口（5/10/20/30/60 日）的均值 / 标准差 / 偏度 / 峰度
- **Volume**：成交量 / 换手率 / 量价比
- **Mean**：移动平均价格
- **Std**：标准差（波动率）
- **Corr**：量价相关（CORR(close, volume, N)）
- **Rank**：截面排名

具体公式见 Qlib 源码 `qlib.contrib.data.handler.Alpha158`。

## 在素材中的角色（重要负面案例）

[[2026-05-05-qpb-industry-pricevolume-etf-rotation]]：作者发现华西证券提出的 192 个量价因子在 ETF 上**完全失效** → 用 Alpha158 做对照测试 → **同样未跑出理想效果**

⇒ 启示：**ETF 池上多因子模型可能本身不可行**，不是单个因子库的问题。

## 与同类因子库的对比

| 因子库 | 数量 | 来源 |
|---|---|---|
| **Alpha158** | 158 | Qlib 内置 |
| Alpha360 | 360 | Qlib 扩展 |
| WorldQuant 101 | 101 | WorldQuant 论文 |
| 191 因子 | 191 | 中信证券研究所 |
| Open Source Asset Pricing | 200+ | Andrew Chen 学术因子 |

## 在素材中的出现

- [[2026-05-05-qpb-industry-pricevolume-etf-rotation]]：作为对照基准

## 相关页面

- 主体：[[Qlib]]
- 主题：[[机器学习选股]]、[[Alpha挖掘与因子正交性]]、[[ETF轮动与交易策略]]
