---
tags: [QuantsPlaybook, ETF轮动, 量价因子, Qlib, 负面发现, source]
created: 2026-05-05
updated: 2026-05-05
type: source
source_type: github_strategy
source_url: https://github.com/hugo2046/QuantsPlaybook/tree/master/B-%E5%9B%A0%E5%AD%90%E6%9E%84%E5%BB%BA%E7%B1%BB/%E8%A1%8C%E4%B8%9A%E6%9C%89%E6%95%88%E9%87%8F%E4%BB%B7%E5%9B%A0%E5%AD%90%E4%B8%8E%E8%A1%8C%E4%B8%9A%E8%BD%AE%E5%8A%A8%E7%AD%96%E7%95%A5
venue: 华西证券金融工程
pub_date: 2023 (约)
priority: B
sources: []
---

# 行业有效量价因子与行业轮动策略（ETF）

> 来源：华西证券金融工程研究报告 | QuantsPlaybook 复现：[[hugo2046]]

## 一句话定位

复现华西证券提出的**192 个量价因子组合**（4 大类因子 × 6 个窗口期 5/10/20/60/120/180）+ 用 [[Qlib]] 框架在 ETF 上轮动。**关键负面发现**：原报告在指数上有效，但**在 ETF 上完全失效** — 这是个非常有价值的"反例"素材。

## 核心机制

### 1. 192 个量价因子（4 大类 × 6 窗口）

研报未给出具体窗口参数，作者用了 5 / 10 / 20 / 60 / 120 / 180 这 6 个常用窗口期，共生成 **192 个因子**。

具体因子计算公式在 ipynb 的"价量因子构造"表格中（节选未完整 OCR）。

### 2. 标的池

- 2020 年前：行业 ETF 数量不足（占比 < 60%）
- 2020 年后：行业 ETF 占比起升
- 作者结论：**ETF 历史时间过短** → 后续使用全部 ETF（不限于行业 ETF）作为标的池

### 3. 流程（基于 [[Qlib]] 框架）

```
ETF 价量数据 → Qlib 数据格式 → 192 因子构造
   ↓
特征 / 标签 dataset → LightGBM / 模型训练
   ↓
预测 → IC / RankIC 评估
   ↓
分组收益（Top - Bottom 多空）
   ↓
Backtrader 回测
```

### 4. Alpha158 对照测试

作者在发现"华西因子在 ETF 上失效"后，用 [[Alpha158]] 因子（Qlib 内置经典 158 因子）做对照测试 — 但 Alpha158 也未在 ETF 上跑出理想效果。

## 关键负面发现（最有价值的部分）

> 作者原话："**华西证券的价量因子虽然在指数上表现较好，但是在 ETF 上的表现可以说是完全失效的**"

**可能的原因**（INFERRED — 仓库未明确分析）：
1. ETF 数量少 + 历史短 → 截面排序的 IC 信号统计意义弱
2. ETF 跟踪误差 → 价量信息已被指数吸收 → 因子在指数上有效但传导到 ETF 时失真
3. ETF 流动性差异大 → 部分因子捕捉的是流动性溢价，不是 alpha
4. 行业 ETF 数量不足以做截面合成

## 关键概念

- [[Alpha158]]（Qlib 内置因子库 — 新增）
- [[Qlib]]（量化框架 — 新增）
- [[ETF轮动]]（主题 / 概念）
- [[QuantsPlaybook]]、[[hugo2046]]

## 启示（对 V25 项目尤其重要）

1. **指数上有效 ≠ ETF 上有效** — 这是个 V25 项目应该立即验证的假设
2. **ETF 数量短 + 历史短** → 多因子模型在 ETF 上的统计稳定性需谨慎
3. 当前知识库中其他指数级别策略（[[均线偏离度]] / [[RSRS]] / [[多信号策略]]）迁移到 ETF 时也要验证是否失效
4. 与 [[2026-05-05-openalphas-lightgbm-bayesian]]（LightGBM + Optuna）的成功案例形成对比 — 那个是个股池，本素材是 ETF 池，**ETF 池的多因子模型可能根本不可行**

## 与已有素材的关联

- 与 [[2026-05-05-openalphas-lightgbm-bayesian]] 形成对照（个股有效 vs ETF 失效）
- 与 [[ICIR]] 概念相关（ETF 上 IC 可能本身偏低）
- 验证"假设迁移"的一个反例

## V25 复现 Hook

- **不优先复现**（B 档：参考价值高，复现价值低）
- 用作 V25 多因子模型 ETF 适配性的**警示**
- 待办：在 V25 项目中如要做"ETF 多因子合成"，先用 Alpha158 做基线测试 → 若 IC < 0.02 则放弃这条路径

## 原文 raw

[../../raw/github/quantsplaybook/2026-05-05-qpb-industry-pricevolume-etf-rotation.md](../../raw/github/quantsplaybook/2026-05-05-qpb-industry-pricevolume-etf-rotation.md)
