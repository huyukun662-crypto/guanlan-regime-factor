---
tags: [因子, 风格择时, 风格轮动]
created: 2026-05-05
updated: 2026-05-05
sources: [wiki/sources/2026-04-23-openalphas-bottom-style-timing.md]
---

# SRI（风格相对强度指标）

> 国证成长指数与国证价值指数收盘价之比，是 OpenAlphas 底部风格轮动模型的锚点因子。

## 定义

$$\text{SRI}_t = \frac{\text{Index}_{growth,t}}{\text{Index}_{value,t}}$$

代码实现（来自 [[2026-04-23-openalphas-bottom-style-timing]]）：

```python
df["SRI"] = df["growth_close"] / df["value_close"]
```

## 解释

- **SRI 上行** → 成长风格相对价值风格占优
- **SRI 下行** → 价值风格相对成长风格占优
- **SRI ≈ [[SRI_balance]]（≈ 0.83）** → 风格中枢，相对优劣消失

## 历史经验值

- 2005 年至今静态均衡值（max + min）/ 2 ≈ **0.83**
- 历史悲观下限：**0.77**（5%-10% 极端区间）
- 6 轮历史大底中，底部左侧 SRI 平均下行 147 个交易日 / 跌幅 21.3%

## 注意事项

⚠ 笔记图5 顶部插图给出的另一种表述（涨跌幅差/基准涨跌幅）**不是** 实际公式。**以代码 `growth_close / value_close` 为准**。 <!-- confidence: EXTRACTED -->

## 与已有概念的关系

- [[国证成长指数]] — 分子（399370）
- [[国证价值指数]] — 分母（399371）
- [[SRI_balance]] — 由 SRI 历史 max/min 派生
- [[底部双因子识别]] — SRI 的应用场景前置条件
- [[风格轮动三阶段模型]] — SRI 是三阶段切换的判别变量

## V25 应用候选

可作为 V25 ETF 轮动的新 regime 维度（除现有 CSI 4w-13w 加速度外）：
- SRI > 0.85 → 成长偏向（科技 / AI / 医药 / 半导体板块加权）
- SRI < 0.85 → 价值偏向（红利 / 银行 / 公用 / 周期板块加权）

## 相关页面

- [[SRI_balance]]
- [[国证成长指数]]
- [[国证价值指数]]
- [[底部双因子识别]]
- [[风格轮动三阶段模型]]
- [[2026-04-23-openalphas-bottom-style-timing]]
