---
type: topic
created: 2026-06-05
sources:
  - [[2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes]]
---

# Regime 切换与因子轮动

> 当市场环境 (regime) 切换时，因子溢价的风险-收益结构会显著改变。本主题汇总把 regime 识别转化为可执行因子配置的方法、对比和实证。

## 核心问题

1. **regime 能否从因子收益本身恢复**？（不依赖宏观变量预测）
2. **regime 持续性怎么建模**？(i.i.d. vs Markov)
3. **regime 信息怎么落到配置权重**？(选模型 vs 连续优化)
4. **宏观变量 (VIX/CAPE) 该作 predictor 还是 anchor**？

## 方法谱系

| 方法 | regime 模型 | 配置机制 | 代表工作 |
|------|------------|---------|---------|
| GMM characterization | i.i.d. 高斯混合 | 仅描述不配置 | [[Botte Bao 2021]] |
| HMM model selection | Markov 持续 | regime → 选模型菜单 | [[Wang Lin Mikhelson 2020]] |
| **HMM 概率 → MV** ⭐ | **Markov 持续** | **regime 概率 → 连续 MV 权重** | [[Anchor-Stabilized HMM框架]] (Yang 2026) |
| Factor timing | 宏观变量 → 因子收益 | 直接预测 → 加减仓 | [[Ilmanen 2021]] 质疑此路 |

## 关键机制

- [[Gaussian Hidden Markov Model]] — regime 持续 + 转移建模
- [[One-step-ahead regime概率]] — 把状态不确定性传递到决策
- [[VIX锚定机制]] / [[CAPE锚定机制]] — Anchor not predictor 范式
- [[Clipping interval稳定化]] — anchor 调整范围限制
- [[L1换手率惩罚]] — regime 切换不带来过度交易

## 实证锚点

- **Yang 2026** 在 2013-2023 美股证明：long-only 实现 Sharpe 1.33 / Max DD -3.64%（vs S&P 500 0.90 / -23.97%）
- 在 [[2020 COVID冲击稳健性|2020 COVID]] + 2022 股债双杀两次极端期均稳健

## 与已有主题的关联

- [[底部择时与风格轮动]] — 风格轮动本质是 regime 状态变迁的实操版
- [[Alpha挖掘与因子正交性]] — 本主题在配置层，alpha 挖掘在信号层，正交关系
- [[动态资产配置与组合优化]] — 本主题提供 regime conditioning，后者提供组合机制

## 待解决问题

- A 股的政策驱动 regime 是否能用 HMM 一致表达？
- HMM 状态数（2/3/4）如何选？月度 refit 会让状态语义跳变吗？
- regime 切换的预警 leading indicator 跟 anchor 怎么协调？

## 相关素材

- [[2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes]]
