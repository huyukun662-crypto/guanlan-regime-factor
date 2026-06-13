---
tags: [方法, Regime, 状态切分, MRP前置, 宏观周期]
created: 2026-05-31
updated: 2026-05-31
type: entity
entity_type: method
sources:
  - wiki/sources/2026-05-31-dbjg-fabozzi-strategy-decay-risk.md
---

# 市场 Regime 切分

> 把历史数据按市场状态分段的预处理步骤 —— [[MRP最小Regime表现]] 的必要前置；也是 [[策略衰减风险]] 量化的工程入口

## 一句话定义

把连续历史时序按宏观 / 资金面 / 波动率等维度切分成离散市场状态（regime），以便分别评估策略表现。

## Fabozzi 论文建议的切分维度

| 维度 | 类别示例 |
|---|---|
| 宏观周期 | 宽松周期 / 加息周期 |
| 危机状态 | 危机周期 / 非危机周期 |
| 流动性 | 流动性扩张 / 收缩 |

## 实战常用切分（A 股 / ETF，INFERRED）

| 维度 | 切分方法 | 工具 |
|---|---|---|
| 宏观周期 | 沪深 300 滚动 12 月收益分位 → 牛 / 熊 / 震荡 | 价格分位 |
| 利率周期 | R007 趋势上 / 下行 | 利率数据 |
| 波动率 | VIX 或滚动波动率高 / 低 | 波动率分位 |
| 风格 | [[SRI]] 风格相对强度 → 成长 / 价值 | 风格指数 |
| 流动性 | M2 同比扩张 / 收缩 | 宏观数据 |

## 切分方法选择

| 方法 | 优点 | 缺点 |
|---|---|---|
| **阈值法** | 简单透明 | 阈值主观 |
| **分位法**（推荐） | 自适应 | 需较长样本 |
| **HMM（隐马尔可夫）** | 数据驱动 | 模型黑盒 |
| **聚类**（如 [[时序动态聚类]]） | 多维度合成 | 解释性差 |

## 样本量门槛（INFERRED）

- 每个 regime 至少 60 个交易日（论文未明示，建议下限）
- 推荐每个 regime ≥ 252 日（一年）保证 Sharpe 估计稳健
- 总样本 / regime 数 ≥ 60 → 否则切得过细

## 与 [[时序动态聚类]] 的关系

[[Q-A3C²]] 论文（[[2026-05-06-datou-q-a3c2-paper-reading]]）用滚动 K-means 做动态 regime 切分，与 Fabozzi 论文的静态 regime 思路**互补**：
- Fabozzi：事后回顾用 regime
- Q-A3C²：实时识别用 regime（用于策略切换）

## V25 实施 Hook

```python
def split_regimes(df: pd.DataFrame, methods: list) -> pd.Series:
    """
    多维 regime 切分。
    
    methods 示例：['hs300_trend', 'r007_trend', 'vix_quantile']
    返回与 df 同 index 的复合 regime 标签
    """
    labels = []
    if 'hs300_trend' in methods:
        ret_12m = df['hs300_close'].pct_change(252)
        labels.append(pd.cut(ret_12m, [-1, -0.1, 0.1, 1],
                              labels=['bear', 'range', 'bull']))
    # ... 其他维度
    return labels[0] if len(labels) == 1 else \
           pd.Series([tuple(x) for x in zip(*labels)])
```

## 在素材中的出现

- [[2026-05-31-dbjg-fabozzi-strategy-decay-risk]]：MRP 的前置步骤

## 相关页面

- 上位指标：[[MRP最小Regime表现]]、[[衰减风险前沿]]
- 相关方法：[[时序动态聚类]]（动态版）、[[Q-A3C²]]
- 主题：[[动量衰竭早期识别]]
