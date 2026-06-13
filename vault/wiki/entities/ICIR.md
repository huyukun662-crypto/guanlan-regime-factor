---
tags: [因子评价, 信息比率, IC]
created: 2026-05-05
updated: 2026-05-05
type: entity
entity_type: metric
sources:
  - wiki/sources/2026-05-05-openalphas-alphazero-factor-mining.md
  - wiki/sources/2026-05-05-openalphas-lightgbm-bayesian.md
---

# ICIR

> Information Coefficient Information Ratio — 信息系数信息比率

## 一句话定义

ICIR = **IC 均值 / IC 标准差**，衡量因子预测能力的**稳定性**（信号强度的"信噪比"）。ICIR > 0.5 视为有效因子；ICIR > 2 视为优秀因子；ICIR > 5 视为极强因子。

## 公式

```
IC_t   = corr(因子值_t, 未来收益率_{t+1})        # 单期信息系数
ICIR   = mean(IC_t) / std(IC_t)                  # IC 时序均值 / 标准差
```

IC 通常用 [[斯皮尔曼秩相关系数]]（更稳健，不受单点极端值影响）：

```
IC_t = spearman(因子值_t, 未来收益率_{t+1})
```

## 与 IC 均值的关系

- **IC 均值高、ICIR 低**：偶尔大爆发，整体不稳定 → 不适合作为核心信号
- **IC 均值低、ICIR 高**：每期都稳定贡献小幅 alpha → 适合作为核心信号
- 量化研究中**ICIR 比 IC 均值更重要**

## 阈值经验

| ICIR | 评价 |
|---|---|
| > 0.5 | 有效因子 |
| > 1 | 良好因子 |
| > 2 | 优秀因子 |
| > 5 | 极强因子（可能伴随过拟合，需警惕） |
| > 7 | **极少见**，往往因子周期短 / 样本特殊 / 过拟合 |

## 与多空年化、夏普的对应关系

经验上：
- ICIR ≈ 1 → 多空年化 ~ 10-15%
- ICIR ≈ 2 → 多空年化 ~ 20-25%
- ICIR ≈ 5 → 多空年化 ~ 30-40%

但这是**经验级别**，具体取决于换手率、行业暴露、市场状态等。

## 在素材中的出现

- [[2026-05-05-openalphas-alphazero-factor-mining]]：3 个核心因子 ICIR 普遍在 7 以上（标题宣称）— 极少见，需复测验证
- [[2026-05-05-openalphas-lightgbm-bayesian]]：贝叶斯超参优化的目标 = 验证集 IC 最大化（隐含希望 ICIR 提升）

## 与其他评价指标的对比

| 指标 | 优点 | 缺点 |
|---|---|---|
| IC 均值 | 直观 | 受极端值影响 |
| **ICIR** | 衡量稳定性 | 不直接反映绝对预测能力 |
| 多空年化 | 直接反映赚钱能力 | 受换手 / 容量影响 |
| 多空夏普 | 风险调整后 | 同 ICIR，更经济直观 |

## 相关页面

- 主题：[[Alpha挖掘与因子正交性]]
- 配套：[[斯皮尔曼秩相关系数]]、[[信号胜率口径]]
