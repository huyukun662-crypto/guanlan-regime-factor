---
tags: [指标, 动量, 比尔威廉斯, 经典技术分析]
created: 2026-05-05
updated: 2026-05-05
type: entity
entity_type: indicator
sources:
  - wiki/sources/2026-05-05-qpb-alligator-index-timing-rotation.md
---

# AO 动量震荡指标

> Awesome Oscillator — 比尔·威廉斯提出，与 [[鳄鱼线]] 配合使用的动量加速度指标

## 一句话定义

衡量短期（5）vs 长期（34）K 线中点的动量差，揭示**动量加速度**变化（在价格变化之前先动）。

## 公式

**原书 / 仓库实现**（中位数差）：
```
AO = SMA(High - Low, 5) - SMA(High - Low, 34)
```

**TradingView 实现**（注意差异）：
```
AO_TV = SMA(High + Low, 5) - SMA(High + Low, 34)
```

⚠ 两版**不同**！仓库 [[hugo2046]] 沿用原书定义。

## 信号规则

> AO 连续 3 个交易日上行 = 加仓信号
> AO 连续 3 个交易日下行 = 减仓信号

## 与 [[鳄鱼线]] 的组合用法

```
看多信号 = AND(Alligator=1, OR(AO=1, Fractal=1))
看空信号 = OR(Alligator=-1, AO=-1, Fractal=-1)
```

⇒ **不对称设计**：A 股博弈多 → 看多严格、看空宽松。

## 经济直觉（威廉斯）

> 在价格变化之前 → 动量先变；动量变化前 → 速度先变；速度变化前 → 成交量先变

AO 是**趋势起始的第一个入场信号**。

## 在素材中的出现

- [[2026-05-05-qpb-alligator-index-timing-rotation]]：作为鳄鱼线的配套加仓 / 减仓指标

## 相关页面

- 主体：[[鳄鱼线]]
- 配套：[[分形突破]]
- 主题：[[技术指标择时]]、[[ETF轮动与交易策略]]
