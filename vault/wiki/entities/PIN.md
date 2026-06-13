---
tags: [概念, 微观结构, 信息不对称, 经典模型]
created: 2026-05-07
updated: 2026-05-07
type: entity
entity_type: concept
sources:
  - wiki/sources/2022-02-21-gf-hfdata-factor-series-6-info-asymmetry.md
  - wiki/sources/2012-volume-clock-easley-lopez-de-prado-ohara.md
---

# PIN（Probability of Informed Trading，知情交易概率）

> 市场微观结构理论的奠基模型 — 由 Easley & O'Hara 提出，用混合泊松分布估计市场中"信息优势交易者占比"

## 一句话定义

把买卖订单流建模成"信息优势交易者 + 非信息优势交易者"两类的混合泊松到达过程，用极大似然估计 4 个隐参数 (α, δ, ε, μ)，得：

```
PIN = α·μ / (α·μ + 2·ε)
```

- α：信息事件发生的概率
- δ：信息事件发生时是坏消息的概率
- μ：信息优势交易者订单到达率（泊松参数）
- ε：非信息优势交易者订单到达率（泊松参数）

PIN 越高 → 知情交易者占比越大 → 信息不对称越严重 → 做市商被 adversely selected 风险越大。

<!-- confidence: EXTRACTED -->
<!-- evidence: [[2022-02-21-gf-hfdata-factor-series-6-info-asymmetry]] §二(一) PIN 模型推导 + Easley-Kiefer-O'Hara-Paperman 1996 JoF 原论文 -->

## 历史

- **1992**: Easley & O'Hara 在 Journal of Finance 提出 PIN 概念前身
- **1996**: Easley, Kiefer, O'Hara, Paperman 在 Journal of Finance 正式发表《Liquidity, Information, and Infrequently Traded Stocks》，给出完整 PIN 模型 + 极大似然估计流程
- **2008**: Easley, Engle, O'Hara, Wu 在 Journal of Financial Econometrics 提出 dynamic discrete-time estimate
- **2012**: Easley, López de Prado, O'Hara 提出 [[VPIN]] —— PIN 的高频估计版

## 序贯交易模型（PIN 的微观结构基础）

```
单个交易区间 t
  ├─ 信息事件发生（概率 α）
  │   ├─ 利好（概率 1-δ）
  │   │   ├─ 买单到达率：ε + μ（含信息交易者）
  │   │   └─ 卖单到达率：ε
  │   └─ 利空（概率 δ）
  │       ├─ 买单到达率：ε
  │       └─ 卖单到达率：ε + μ
  └─ 信息事件不发生（概率 1-α）
      ├─ 买单到达率：ε
      └─ 卖单到达率：ε
```

做市商**已知**每种情况的发生概率，但**不知道**当下具体发生哪种 → 用贝叶斯法则更新先验。

## 做市商的 bid-ask spread 推导

基于 PIN，做市商的最优 bid 和 ask：

```
b(t) = E[V_i | t] - μ·P_b(t) / (ε + μ·P_b(t)) · (E[V_i | t] - V_i)
α(t) = E[V_i | t] + μ·P_g(t) / (ε + μ·P_g(t)) · (V_i - E[V_i | t])
```

→ 当 PIN 高，做市商必须**拉宽 bid-ask spread** 以补偿被 informed traders 选择的损失。这是 PIN 模型对市场流动性的核心解释。

<!-- confidence: EXTRACTED -->

## 极大似然估计的局限（PIN 的硬伤）

PIN 用混合泊松分布 + 极大似然法估计 4 参数，存在三大缺陷：

1. **数据时间跨度长** → 非公开信息被稀释或丢失
2. **PIN 实际包含非流动性信息**（冗余）
3. **数值溢出**：部分股票数据量过大，极大似然法计算失败

→ 这正是 [[VPIN]] 出现的原因 — 用非参数法（等成交量分桶 + BVC）替代极大似然，解决以上三个问题。

## PIN vs VPIN vs VWPIN 演进对比

| 维度 | **PIN** (1996) | **VPIN** (2012) | **VWPIN** (2020/2022) |
|---|---|---|---|
| 估计方法 | 极大似然 + 混合泊松 | 非参数（成交量不平衡）| 非参数（订单笔数不平衡）|
| 时间分桶 | 等时间（日/周）| 等成交量（volume clock）| 等时间（5min）|
| 关键观测 | 买卖订单数 | 买卖成交量 | 买卖**笔数** + 成交量加权 |
| 实时性 | 弱 | 中 | **强** |
| A 股适配 | 弱（数据要求）| 中（需 BVC + tick 近似）| **强** |
| 抗拆单 | 弱 | 弱 | **强** |
| 数值稳定性 | 差 | 中 | **好** |

## 应用场景

- **学术研究**：信息不对称程度的直接度量（vs 早期间接代理：买卖价差、换手率、价格方差）
- **资产定价**：PIN 高 → 该股要求更高风险溢价
- **流动性研究**：PIN 解释为什么不同股票 bid-ask spread 差异巨大
- **风险管理**：高 PIN 期间减仓 / 拉宽报价

## 关键术语 / 公式

- **混合泊松分布**：买卖订单服从泊松分布，参数 ε 或 ε+μ 取决于是否有信息事件
- **Sequential trade model**（序贯交易模型）：Easley & O'Hara 1987 提出，PIN 的理论祖先
- **似然函数**：

```
L(M | θ) = Π_{i=1}^I L(B_i, S_i | θ)

L(B, S | θ) = (1-α)·Poisson(B; εT)·Poisson(S; εT)
            + α·δ·Poisson(B; εT)·Poisson(S; (ε+μ)T)
            + α·(1-δ)·Poisson(B; (ε+μ)T)·Poisson(S; εT)
```

## 在素材中的出现

- [[2022-02-21-gf-hfdata-factor-series-6-info-asymmetry]]（广发完整推导 PIN→VPIN→VWPIN 演进）
- [[2012-volume-clock-easley-lopez-de-prado-ohara]]（同三作者范式宣言论文）
- [[2012-vpin-overview-lopez-de-prado]]（Wikipedia 综述）
- [[2020-quantitative-trading-textbook]]（教科书第 4-5 章理论根基）

## 相关页面

- 衍生：[[VPIN]]、[[VWPIN]]
- 配套：[[BVC算法]]、[[Lee-Ready算法]]、[[订单流毒性]]
- 主题：[[高频交易与市场微观结构]]、[[动量衰竭早期识别]]
- 学术追溯：[[限价订单簿LOB]]、[[做市策略]]
- 关键人物：[[Maureen O'Hara]]、[[David Easley]]、[[Marcos Lopez de Prado]]
