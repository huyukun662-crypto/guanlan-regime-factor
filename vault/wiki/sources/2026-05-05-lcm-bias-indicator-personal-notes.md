---
tags: [公众号, 个人博主, 乖离率, 复刻心得, 通达信, source]
created: 2026-05-05
updated: 2026-05-05
type: source
source_type: wechat_article
source_url: https://mp.weixin.qq.com/s/yoDNm2TSrWCvvedu_Xozgw
author: 个人博主（独立投资笔记）
venue: 微信公众号
pub_date: 2025-09 (减法版后)
priority: A
images: 11
sources: []
---

# 刘晨明乖离率怎么用，我的一点心得

> 来源：[微信公众号](https://mp.weixin.qq.com/s/yoDNm2TSrWCvvedu_Xozgw) | 个人博主 | 2025-09 之后

## 一句话定位

复刻 [[刘晨明]] [[均线偏离度]] 指标的**实操心得 + 通达信公式 + 5 条使用要点**，串联了原创除法版（[[2026-05-05-gf-strategy-mainline-correction-vs-end]]）→ 减法版（[[2026-05-05-gf-strategy-residential-entry-thermometer]]）的演进背景。

## 核心观点

### 一、除法版 → 减法版的演进背景（个人解读）
- 除法版（行业指数标定）：`(ln(close) / 20日EMA) - 1`，阈值 0.6%/2%
- **不适用于绝对值较低的标的**：ETF / 个股 EMA20 ≈ 1 时分母≈0 报错；< 1 时正负值颠倒
- 减法版（ETF 友好）：`ln(close) - ln(ema20)`，阈值 5%/15%（数量级因 *100% 而调整）

### 二、通达信公式（个人复刻）

```
EMA20:= EMA(LN(CLOSE), 20);

LOGBIAS: (LN(CLOSE) - EMA20) * 100;

过热线: 15, COLORRED, DOTLINE;
失速线: 5,  COLORYELLOW, DOTLINE;
止损参考线: -5, COLORGREEN, DOTLINE;
零轴: 0, COLORGRAY, DOTLINE;
```

### 三、5 条使用心得

1. **不上 5% 不够强** — 主线必须能突破 5% 乖离率，否则缺乏"龙头气质"
2. **回抽两步走形态** — 触 5% → 回调到 0 区间获支撑 → 继续向上突破（强势确立）
3. **品种之间择强辅助** — 用乖离率高低做主线对比（如 CS 电池 vs 光伏在同一时点的强度对比）
4. **止损后不轻易入场** — 跌穿 -5% 后，如果再不能站上 5%+，则真的进入主跌浪（电池 2021Q4 / 光伏 2021Q4 / 中概互联 2021-2022）
5. **逆练真经也有效** — 对**非主线 / 价值流标的**（中证银行 / 中证红利 / 中证白酒），把 -5% 当阶段性低点 / 5% 当阶段性高点用作震荡区间

### 四、不适用场景
- 中证白酒 2021 后反弹中乖离率屡屡站上 5%+ 但很容易骗线 → **趋势性弱的品种容易出错**
- 银行、红利等价值流：长期在 [-5%, 5%] 内波动 → 阈值需调整或反向用

## 关键概念

- [[均线偏离度]]（强调减法版 + 通达信实现）
- [[回抽两步走]]（个人提出的强势确立形态，标 INFERRED — 原始报告未提）
- [[逆练真经]]（个人提出的价值流震荡区间用法，标 INFERRED）
- [[刘晨明]]

## 与其他素材的关联

- [[2026-05-05-gf-strategy-mainline-correction-vs-end]]：原创除法版的来源
- [[2026-05-05-gf-strategy-residential-entry-thermometer]]：减法版升级的来源
- 价值：把广发策略的研究**工程化落地**（通达信公式 + 反向用法），降低普通投资者的复刻门槛

## 风险提示与待验证

- "回抽两步走形态" / "逆练真经" 是个人观察 — 未做严格回测验证（INFERRED）
- 通达信公式中 `LN(CLOSE) * 100` 的尺度需注意：本质是 ln(close) - ln(ema20) 后乘 100 让阈值变成 5/15 而非 0.05/0.15
- 个人样本基于通信设备、半导体、CS 电池、光伏、中概互联、中证白酒、中证银行、中证红利等指数 — 不一定泛化到所有品种

## V25/复现 Hook

- 通达信公式可直接用于 V25 项目的 ETF 池监控（中证白酒、银行、红利等）
- 减法版阈值 5%/15% 可作为 V25 的 regime 候选信号之一
- 待办：V25 内实现 `compute_log_bias(price, span=20)` + 单元测试 + 信号回测

## 原文 raw

[../../raw/wechat/2026-05-05-lcm-bias-indicator-personal-notes.md](../../raw/wechat/2026-05-05-lcm-bias-indicator-personal-notes.md)
