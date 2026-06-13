---
tags: [风险, 元概念, Fabozzi]
created: 2026-05-31
updated: 2026-05-31
type: entity
entity_type: concept
sources:
  - wiki/sources/2026-05-31-dbjg-fabozzi-strategy-decay-risk.md
---

# 元风险（Meta Risk）

> [[Frank Fabozzi]] 论文用语 —— **风险之上的风险** —— 不是策略产生多少损失，而是策略本身失去产生 Alpha 的能力

## 一句话定义

传统风险衡量的是 **"策略有效时"** 的损失分布；
元风险衡量的是 **"策略是否还有效"** 这件事本身。

## 层次关系

```
[Layer 0] 元风险 Meta Risk        ← 策略是否还有效
              ↓ 决定
[Layer 1] 传统风险（VaR/MDD/Vol）  ← 给定策略有效，损失多少
              ↓ 决定
[Layer 2] 单笔交易风险             ← 单次决策的损益分布
```

## 论文直接表述

> 量化投资真正的元风险（Meta Risk）并非收益波动，而是：**策略本身失去有效性**。即：Alpha Decay（Alpha 衰减）。

## 衡量工具：[[MRP最小Regime表现]]

## 与已有风险概念的对照

| 概念 | 层次 | 时间尺度 | 救援方式 |
|---|---|---|---|
| 单次交易风险（滑点 / 冲击） | Layer 2 | 日内 | 拆单 / 算法 |
| 传统风险（VaR / MDD / Vol） | Layer 1 | 月年 | 仓位 / 对冲 |
| **元风险** | **Layer 0** | 多年 / 多周期 | **策略报废** |

## 同义 / 近义概念

- [[策略衰减风险]] = 元风险的具体形式
- [[Alpha半衰期]] = 元风险的时间维度量化
- [[策略耐久性]] = 元风险的反面

## 在素材中的出现

- [[2026-05-31-dbjg-fabozzi-strategy-decay-risk]]：明确提出"元风险（Meta Risk）"概念

## 相关页面

- 配套：[[策略衰减风险]]、[[MRP最小Regime表现]]、[[衰减风险前沿]]、[[策略耐久性]]、[[Alpha半衰期]]
- 主题：[[动量衰竭早期识别]]、[[Alpha挖掘与因子正交性]]
- 论文：[[Frank Fabozzi]]
