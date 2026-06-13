---
tags: [震荡指标, 趋势识别, regime分类, 技术指标]
created: 2026-05-26
updated: 2026-05-26
type: entity
entity_type: indicator
sources:
  - wiki/sources/2026-05-26-choppiness-index.md
---

# Choppiness Index (CI)

> 由 E.W. Dreiss 提出的**震荡/趋势分类器**，把"价格位移效率"标量化为 0–100：→0 趋势、→100 震荡。

## 公式

```
CIₜ = 100 × log₁₀( Σᵢ₌ₜ₋ₙ₊₁ᵗ TRᵢ / (maxHₙ − minLₙ) ) / log₁₀(n)
TRᵢ = max(Hᵢ−Lᵢ, |Hᵢ−Cᵢ₋₁|, |Lᵢ−Cᵢ₋₁|)
```
- n=14/20；阈值 38.2(φ⁻¹) / 61.8(φ⁻²)
- 直觉：累积波幅 ΣTR 相对净区间 Range 越大 → 价格反复折返(震荡)；越接近净区间 → 单边推进(趋势)

## 与同类指标

| 指标 | 度量 | 起源 |
|--|--|--|
| Choppiness Index | ΣTR / Range（log） | Dreiss |
| Kaufman 效率系数 ER | 净位移 / Σ\|逐日位移\| | Kaufman(AMA核心) |
| [[均线偏离度]] BIAS | price 偏离 EMA | 广发刘晨明 |

→ 三者同属"趋势效率"族，高度相关。

## ETF6.4 验证结论

- 作 regime 分类器在 A 股宽基 ETF 池**无增量**：高 CI(震荡)日 baseline 条件 Sharpe 仍为正(Full 1.04/OOS 1.28)，与 [[AMA]] 结论一致(震荡整体不弱)
- 唯一负子桶(CI>50&高波)OOS 几乎不复现 → 不可作可交易去风险门
- 详见 [[2026-05-26-choppiness-index]]

## 相关页面

- [[2026-05-26-choppiness-index]]
- [[均线偏离度]] · [[分布通道]] · [[AMA]]
