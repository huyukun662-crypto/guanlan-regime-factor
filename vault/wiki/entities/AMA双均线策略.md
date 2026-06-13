---
tags: [策略模板, KAMA, 双均线, 金叉死叉, 聚宽, A档]
created: 2026-05-19
updated: 2026-05-19
type: entity
entity_type: strategy_template
aliases: [双 KAMA 金叉策略, AMA Dual Crossover]
sources:
  - wiki/sources/2026-05-19-jq-ama-kaufman-explainer.md
---

# AMA 双均线策略

> 简化版 [[考夫曼自适应均线]] 交易模板：用两条不同周期的 KAMA 做金叉死叉，全仓买入 / 清仓卖出。

## 一句话定义

**fast KAMA 上穿 slow KAMA → 满仓买入；fast KAMA 下穿 slow KAMA → 清仓卖出**。是 KAMA 系列里最简陋但最易复刻的策略原型。

## 聚宽实现（≤ 40 行）

```python
import talib
import numpy as np

def initialize(context):
    g.security = '000001.XSHE'   # 平安银行
    g.fast_ama_period = 10
    g.slow_ama_period = 30
    run_daily(trade, time='every_bar')

def trade(context):
    security = g.security
    hist = attribute_history(security, g.slow_ama_period + 5, '1d',
                             ['close'], skip_paused=True)
    closes = hist['close'].values
    if len(closes) < g.slow_ama_period:
        return

    fast_ama = talib.KAMA(closes, timeperiod=g.fast_ama_period)
    slow_ama = talib.KAMA(closes, timeperiod=g.slow_ama_period)
    cur_fast, prev_fast = fast_ama[-1], fast_ama[-2]
    cur_slow, prev_slow = slow_ama[-1], slow_ama[-2]
    pos = context.portfolio.positions[security].total_amount

    if prev_fast <= prev_slow and cur_fast > cur_slow and pos == 0:
        order_value(security, context.portfolio.total_value)
    elif prev_fast >= prev_slow and cur_fast < cur_slow and pos > 0:
        order_target(security, 0)
```

## 参数

| 参数 | 默认 | 含义 |
|---|---|---|
| `fast_ama_period` | 10 | 快线 KAMA 的 ER 窗口 |
| `slow_ama_period` | 30 | 慢线 KAMA 的 ER 窗口 |
| 仓位策略 | all-in / all-out | 全仓二元切换（极端） |

> TA-Lib `KAMA` 内部的 fast/slow EMA 周期写死 2 / 30，外部只暴露 `timeperiod`。所以两条 KAMA 的真正差异只在 ER 窗口长度上 <!-- confidence: EXTRACTED -->

## 已知缺陷（按 [purpose.md](../../purpose.md) 标尺）

1. **没有过滤器**：原文承认这是简化版，需加 [[标准差过滤器]] 才接近考夫曼原版完整系统 <!-- confidence: EXTRACTED -->
2. **单标的 + 全仓**：完全没有组合思维，不适合直接迁移到 [[ETF轮动与交易策略]]
3. **无止损 / 无防御篮子**：和已有 V25 ETF 项目的 trail stop + 防御篮子机制完全脱节
4. **无业绩对比**：原文未给出 vs SMA / EMA 基准的回测对比
5. **A 股 T+1 适配**：今日金叉，按规则应次日开盘执行，与代码里 `run_daily(time='every_bar')` 的实现需仔细对齐避免前视偏差 <!-- confidence: INFERRED -->

## 改造方向（如要纳入自有策略）

按 V25 ETF 框架的演进路径：

1. **Step 1**：把单标的版本改为 ETF 池横截面版本——每只 ETF 算自己的双 KAMA 信号，金叉买入 / 死叉卖出
2. **Step 2**：加上 [[标准差过滤器]]，把 σ 倍数 `k` 作为 grid_search 新维度
3. **Step 3**：用 [[效率系数]] 做仓位调节，不再 all-in / all-out
4. **Step 4**：和现有动量排序 / 类别上限 / 防御篮子叠加，做严格 IS/OOS 增量评估

## 关键素材

- [[2026-05-19-jq-ama-kaufman-explainer]]：A 档；原始策略模板出处

## 与本知识库其他策略模板的对比

| 策略 | 信号源 | 仓位结构 | 风险管理 |
|---|---|---|---|
| AMA 双均线 | 双 KAMA 交叉 | 全仓二元 | 无 |
| [[ETF动量排序]] | rank by return | top-K 等权 | 类别上限 + trail |
| [[BIAS减仓]] | 价格 vs 20日 EMA 偏离 | 分档减仓 | 偏离阈值 |

AMA 双均线**最大问题是缺少组合维度**，但 KAMA / ER 本身作为底层信号可以嵌入更复杂的框架。

## 复刻 checklist

- [ ] 用本地 backtester 把这个策略在沪深 300 上跑一遍
- [ ] 对比 KAMA(10/30) vs EMA(10/30) 双均线交叉，看 KAMA 是否真的更优
- [ ] 加 σ 过滤器，扫描 `k ∈ [0.5, 1.0, 1.5, 2.0]`
- [ ] 改造为 ETF 池横截面版本，对比与 V25 现有方案的 IS Sharpe 增量
