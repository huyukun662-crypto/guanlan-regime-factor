---
tags: [小红书, 震荡指标, 趋势识别, regime分类, ETF6.4验证]
created: 2026-05-26
updated: 2026-05-26
type: source
source_type: xiaohongshu
sources: []
---

# 2026-05-26 Choppiness Index (CI) 数学原理与应用

> 小红书科普：CI = 100·log₁₀(ΣTRₙ/Rangeₙ)/log₁₀(n)，→0 趋势 / →100 震荡；阈值 38.2/61.8(斐波那契)。原始链接 http://xhslink.com/o/4xiIZ4ukjJU

## 一句话定位

把"价格位移效率"标量化的**震荡/趋势分类器**：ΣTR(累积波幅) 相对 Range(净区间) 越大 → 越震荡(能量在窄幅耗散)；越接近 1 → 越趋势(最小回撤高效推进)。本质 CI ∝ −log₁₀(位移/累积波动)，与 [[均线偏离度]]、Kaufman 效率系数 ER 同属"趋势效率"族。

## 核心机制

- **TRᵢ** = max(Hᵢ−Lᵢ, |Hᵢ−Cᵢ₋₁|, |Lᵢ−Cᵢ₋₁|)
- **CI** = 100·log₁₀(Σₙ TR / (maxH−minL)) / log₁₀(n)，n=14/20
- 阈值：CI<38.2 趋势 / 38.2–61.8 过渡 / CI>61.8 震荡
- 应用：regime 判别、动态仓位 W∝(1−CI/100)^β、GARCH 波动率加项、CI 驱动止损

## ETF6.4 项目本地验证（关键 — 决定可用性）

在 ETF6.4 本地引擎用 510300(沪深300) 算 CI(14)，按 CI 区间拆 baseline 条件 Sharpe(`local/ci_validate.py`)：

| CI 区间 | base_Sh IS·OOS·Full |
|--|--|
| 趋势 CI<38.2 | 0.38 · **3.60** · 1.97 |
| 过渡 38.2-61.8 | 0.47 · 2.23 · 1.27 |
| 震荡 CI>61.8 | **0.82 · 1.28 · 1.04** |

**结论：CI 作 regime 分类器在本 ETF 池无增量** — 高 CI(震荡)日 baseline 仍为正(Full 1.04)，与 [[AMA]] 的 §18d 结论一致("震荡整体不弱")。唯一负子桶 "CI>50 & 高波"(IS −0.94)在 OOS 几乎不复现(仅 7 日)→ 不可作可交易去风险门(IS 过拟合)。即 CI 与 ETF6.4 已有的 "AMA 震荡 + 20d 高波" 门(§18e hivol-derisk)冗余、不更优。

## 关键概念

- [[Choppiness Index]]（新增实体）
- 对照：[[均线偏离度]]、[[RSRS]]（同属指数级 regime/择时，迁移到 ETF 需验证是否失效 — 见华西反例 [[2026-05-05-qpb-industry-pricevolume-etf-rotation]]）

## 与已有素材关联

- 与 [[分布通道]]/[[均线偏离度]]：都是"震荡 vs 趋势"判别工具；CI 用 ΣTR/Range，均线偏离用 EMA 偏离
- ETF6.4 实证规律：**chop 分类器(AMA/ER/CI)都同意 baseline 在震荡不弱；真窟窿是"高波 whipsaw"子段，且任何 chop 门控信号在 A 股 ETF 池上 OOS 多半无增量**（同华西"指数有效≠ETF有效"反例）

## 原文 raw

[../../raw/xiaohongshu/2026-05-26-choppiness-index.md](../../raw/xiaohongshu/2026-05-26-choppiness-index.md)
