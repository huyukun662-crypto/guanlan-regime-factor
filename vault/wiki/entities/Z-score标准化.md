---
tags: [数据预处理, 量化, 标准化]
created: 2026-05-05
updated: 2026-05-05
type: entity
entity_type: method
sources:
  - wiki/sources/2026-05-05-openalphas-lightgbm-bayesian.md
  - wiki/sources/2026-05-05-openalphas-rsrs-market-thermometer.md
---

# Z-score 标准化

> 减均值除标准差的标准量化预处理

## 公式

```
z = (x - mean(x)) / std(x)
```

## 量化场景中的两种用法

### 1. 时序标准化（用历史窗口）
- 用于动态阈值类指标，如 [[RSRS标准分]]
- 公式：`z_t = (β_t - μ_β) / σ_β`，其中 μ、σ 来自滚动历史

### 2. 截面标准化（用当期所有股票）
- 用于多因子模型预处理，消除因子之间量纲差异
- 公式：`z_{i,t} = (x_{i,t} - mean_t) / std_t`，其中 mean_t、std_t 是当期截面统计量
- 注意：如使用 [[时序划分]] 的训练 / 验证 / 测试，需用**训练期统计量**应用到验证 / 测试期，避免数据泄露

## 与其他标准化方法对比

| 方法 | 公式 | 适用 |
|---|---|---|
| **Z-score（本方法）** | (x - μ) / σ | 近似正态分布的因子 |
| Min-Max | (x - min) / (max - min) | 神经网络输入 |
| Rank | x.rank() / N | 抗极端值，[[ICIR|斯皮尔曼]]隐式使用 |

## 在素材中的出现

- [[2026-05-05-openalphas-lightgbm-bayesian]]：6 步流程第 3 步，配合 [[3σ去极值]] 使用
- [[2026-05-05-openalphas-rsrs-market-thermometer]]：[[RSRS标准分]] 的核心公式

## 相关页面

- 配套：[[3σ去极值]]、[[LightGBM]]、[[RSRS标准分]]
