---
type: source
source_type: ssrn_paper
title: Harvesting Factor Premia Across Regimes - An Anchor-Stabilized Hidden Markov Framework for Multifactor Portfolios
author: Leyong Yang
affiliation: Columbia University
venue: SSRN Working Paper
date: 2026-05
ssrn_id: 6823998
page_count: 42
ingest_date: 2026-06-05
sources: []
images: 0
image_paths: []
---

# Yang 2026 — Anchor-Stabilized HMM Framework for Multifactor Portfolios

> SSRN 6823998 · Columbia · Working Paper May 2026 · 42 页 · OpenCLI 提取 122k 字符

## 基本信息

| 项 | 内容 |
|----|------|
| 主题 | 用 Anchor-Stabilized Gaussian HMM 把因子横截面 regime 转化为可执行多因子配置 |
| 类型 | 实证 + 方法论工作论文（量化资产配置） |
| 数据窗口 | 2013–2023 美股 |
| 基准对照 | Botte & Bao 2021（Two Sigma GMM）+ Ilmanen et al. 2021（AQR 因子择时）|
| 提取方式 | pymupdf 全文 |

## 一句话总结

把 [[Botte Bao 2021]] 的 i.i.d. GMM regime 扩展为 [[Regime持续性建模|Markov-持续]] 的 HMM，再用 [[Turnover-aware均值方差|换手率感知 MV]] 优化把一步前向 regime 概率映射成实操权重；[[VIX锚定机制|VIX]] 和 [[CAPE锚定机制|CAPE]] **仅作 anchor 不作 predictor**，回避了 [[Ilmanen 2021|Ilmanen 2021]] 的择时质疑。

## 核心贡献（4 条）

1. **From i.i.d. mixture to Markov-persistent**：把 [[Gaussian Mixture Model|GMM]] 升级到 [[Gaussian Hidden Markov Model|HMM]]，显式建模 regime 持续与转移概率
2. **From characterization to allocation**：用 [[One-step-ahead regime概率|一步前向 regime 概率]] 直接进 MV，而非选模型菜单（区别于 [[Wang Lin Mikhelson 2020]]）
3. **Anchor not predictor**：VIX/CAPE 通过 [[Clipping interval稳定化|clipping interval [0.5, 1.5]]] 稳定参考配置，不进 HMM likelihood 也不作单独 return predictor
4. **严格 leakage 控制**：[[Expanding window walk-forward|expanding-window walk-forward]] 贯穿 model selection → HMM estimation → 配置生成，参考 [[Leakage控制协议]]

## 实证结果（2013–2023 美股）

| 规格 | Sharpe | 年化波动 | Max DD | Calmar | 备注 |
|------|--------|---------|--------|--------|------|
| **[[Long-only protective specification]]** | **1.33** | 4.05% | **−3.64%** | **1.48** | 风险调整最优 |
| [[Long-short specification]] | 1.24 | — | −5.78% | 1.19 | 8.03% 年化总收益 |
| S&P 500 基准 | 0.90 | 15.06% | −23.97% | — | 累计收益更高但 DD 大 6 倍 |

**关键检验**：2020 COVID 冲击 + 2022 股债双杀两次极端环境框架表现稳健 → [[2020 COVID冲击稳健性]]

## 方法栈

1. **因子集**：[[因子六维体系|value / momentum / quality / size / low risk / profitability]]（Fama-French + Carhart + AQR + Jensen 谱系）
2. **regime 识别**：Gaussian HMM 拟合因子横截面收益，月度 refit
3. **状态推断**：Viterbi + smoothed posterior 给出一步前向 regime 概率
4. **组合优化**：均值方差目标 = 期望收益 − 风险厌恶 × 方差 + [[L1换手率惩罚]]；协方差用 [[Ledoit-Wolf协方差收缩]]
5. **锚定**：VIX/CAPE 通过 clipping 进入 reference allocation，不作 predictor
6. **评估**：burn-in vs deployment 双段，walk-forward 严格无前视

## 可拿来用的最小单元（按 purpose.md 视角）

| 类型 | 单元 | 用法 |
|------|------|------|
| **新机制** | regime 持续概率 → MV 权重映射 | V25 ETF 轮动可加 regime conditioning 层 |
| **正则化** | Ledoit-Wolf 协方差收缩 | 替代 ridge / 经验协方差，V25 多因子打分可用 |
| **目标函数项** | L1 换手率惩罚 | 缓解 grid_search 的过度交易问题 |
| **方法论** | Anchor not predictor（VIX/CAPE clipping） | 防御篮子触发可用同思路：VIX 高时偏防御，但不直接预测收益 |
| **协议** | model selection + walk-forward 全链条 leakage 控制 | IS/OOS 三段式纪律的学术依据 |
| **极端环境** | 2020 + 2022 双杀环境压力测试 | V25 OOS 验证可加这两个 sub-period 检验 |

## 与已有素材的关联

- [[OpenAlphas]] — alpha 库，本文是 regime-conditioned **配置层**，两者在因子使用层互补
- [[Alpha158]] / [[AlphaZero因子挖掘]] — 因子生成 vs 因子配置，正交关系
- [[3σ去极值]] / [[winsorize预处理]] — Yang 用 Ledoit-Wolf 收缩作正则化，思路相近
- [[底部择时与风格轮动]] — 风格轮动机制本质上是 regime 转换的实操版

## 待解决问题

1. **CHN 适配性**：本文全美股，A 股 regime 持续性（受政策驱动）跟美股差异多大？同框架在 CHN 是否退化？
2. **HMM 状态数选择**：论文用几个状态？月度 refit 是否会让状态语义跳变？
3. **L1 惩罚强度**：换手率惩罚系数怎么选？过强会失敏感，过弱失意义
4. **anchor 截断范围 [0.5, 1.5] 怎么定**：是经验值还是参数搜索结果？
5. **跟 V25 backtester 的 Sharpe 口径是否一致**：本文 Sharpe 用日度还是月度？年化乘数？

## 原文精选（仅作溯源·短引）

> "Two influential industry studies provide complementary benchmarks for dynamic factor allocation. Ilmanen et al. (2021) of AQR show that traditional factor-timing strategies often deliver limited out-of-sample gains, while Botte and Bao (2021) of Two Sigma show that latent market states can be recovered from factor-return panels but do not directly translate regime information into portfolio decisions."

## 备注

- SSRN 工作论文（May 2026），未经正式同行评审，结论可信但应作"前沿假说"对待
- 作者 Leyong Yang（Columbia）非顶级机构 affiliation 但论文方法链条扎实，benchmark 对标 AQR + Two Sigma
- 论文原文：`D:\Claude\Brain\raw\pdfs\2026-06-05-ssrn-6823998.pdf`
- 提取文本：`D:\Claude\Brain\raw\pdfs\2026-06-05-ssrn-6823998-extracted.md`（122k 字符）
