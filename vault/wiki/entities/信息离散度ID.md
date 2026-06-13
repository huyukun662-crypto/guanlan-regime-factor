---
tags: [因子, 行为金融, 动量, FIP, ID指标]
created: 2026-05-08
updated: 2026-05-08
type: entity
entity_type: indicator
sources:
  - wiki/sources/2026-05-08-earletf-fip-bias-trim.md
---

# 信息离散度 ID（Information Discreteness）

> 衡量"涨法连续性"的截面指标 —— [[Da-Gurun-Warachka 2014]] 在 *Journal of Finance* 提出，是 [[FIP效应]] 的核心识别工具

## 一句话定义

把过去 12 个月的累积收益（PRET）拆解为**正收益天数占比**和**负收益天数占比**，用 sign(PRET) 作为方向锚，用占比差作为"涨法分布"测度——**ID → -1 是慢涨/慢跌（连续信息），ID → +1 是暴涨/暴跌（离散信息）**。

## 数学定义

```
ID = sign(PRET) × (%neg − %pos)
```

| 符号 | 含义 |
|---|---|
| PRET | 过去 12 个月（跳过最近 1 个月）累积收益 |
| %pos | 形成期内正收益天数占比 |
| %neg | 形成期内负收益天数占比 |
| sign(PRET) | +1（涨）/ -1（跌）/ 0 |

## 直觉理解

| 场景 | PRET | %pos | %neg | ID | 解读 |
|---|---|---|---|---|---|
| 一年涨 50%，多数日子微涨 | +0.5 | 0.55 | 0.40 | **-0.15** | 连续信息（慢涨） |
| 一年涨 50%，靠 3 天暴涨贡献 | +0.5 | 0.40 | 0.55 | **+0.15** | 离散信息（暴涨） |
| 一年跌 50%，多数日子微跌 | -0.5 | 0.40 | 0.55 | **-0.15** | 连续信息（慢跌） |
| 一年跌 50%，靠 3 天暴跌 | -0.5 | 0.55 | 0.40 | **+0.15** | 离散信息（暴跌） |

> 注意：ID 越**小**（接近 -1）= 越**连续** = **后续动量越强**。

## 关键性质：几乎无持续性

- 自相关系数仅 **0.034**
- 衡量的不是"什么类型的股票"，而是"**信息在这段时间内以什么方式到达**"
- 同一只股票，这一年可能是连续信息，下一年可能是离散信息

## 实测预测力（[[Da-Gurun-Warachka 2014]] Table 2）

按 PRET 分 5 组，每组内按 ID 再分 5 组，6 个月持有：

| ID 组 | 6 月动量收益 |
|---|---|
| 最连续（最低 ID） | **8.86%** |
| 中位 | ~5% |
| 最离散（最高 ID） | 2.91% |
| **差值** | **5.95%**（t = 5.13） |

> 慢涨的动量是暴涨的三倍。

## 核心发现汇总

| 维度 | 连续信息（ID 低） | 离散信息（ID 高） |
|---|---|---|
| 动量幅度 | 8.86% | 2.91% |
| 动量持续期 | **8 月** | 3 月 |
| 三年三因子 alpha | +11.77% | 负 |
| 反转风险 | **无反转** | 有 |
| 订单流后续 | 持续净买入 | 集中获利兑现 |

## Python 实现

```python
import numpy as np
import pandas as pd

def compute_id(returns: pd.Series, lookback: int = 252, skip: int = 21) -> float:
    """
    Information Discreteness, Da-Gurun-Warachka 2014.
    
    Parameters
    ----------
    returns : pd.Series
        Daily returns, ascending datetime index.
    lookback : int
        Formation window in trading days. Default 252 (12 months).
    skip : int
        Skip recent N days to avoid microstructure noise. Default 21.
    
    Returns
    -------
    float
        ID in [-1, +1]. Lower = more continuous = stronger forward momentum.
    """
    window = returns.iloc[-lookback - skip:-skip if skip else None]
    pret = (1 + window).prod() - 1
    pct_pos = (window > 0).mean()
    pct_neg = (window < 0).mean()
    return float(np.sign(pret) * (pct_neg - pct_pos))


def cross_sectional_id(prices: pd.DataFrame, lookback: int = 252, skip: int = 21) -> pd.Series:
    """对一篮子标的同时计算 ID（截面用）。"""
    returns = prices.pct_change()
    return returns.apply(lambda r: compute_id(r.dropna(), lookback, skip))
```

## 与已有指标的关系

### 与 [[均线偏离度]]（BIAS）

| 维度 | ID | BIAS |
|---|---|---|
| 数据 | %pos / %neg / sign(PRET) | close / EMA20 |
| 衡量 | **涨法连续性** | **当前偏离幅度** |
| 时间窗 | 12 个月 | 20 个交易日 |
| 信号方向 | ID 低 = 慢涨 = 持有 | BIAS 低 = 偏离温和 = 持有 |
| 关系 | **互补**（BIAS 是瞬时强度，ID 是路径分布） |

**实战搭配**：
- BIAS 低 + ID 低 = **理想买点**（慢涨累积 + 当前不过热）
- BIAS 高 + ID 高 = **危险**（暴涨集中爆发）
- BIAS 高 + ID 低 = **趋势加速末端**（需要观察）
- BIAS 低 + ID 高 = **暴跌后修复**（ID 是反向）

### 与 [[Jegadeesh-Titman动量]]

- 经典动量：PRET 大 → 后续动量
- FIP 升级：PRET 大 + ID 小 → 后续动量**3 倍**于 PRET 大 + ID 大
- ID 不取代动量，而是**动量的过滤器**

### 与 [[RSRS]]

- RSRS 用高低价回归斜率寻找慢涨
- ID 用 %pos %neg 占比寻找慢涨
- 两者从**不同侧面**捕捉"连续信息"，可作为信号交叉验证

## 在素材中的出现

- [[2026-05-08-earletf-fip-bias-trim]]：完整公式 + 实证 + 作者实操印证

## 局限与注意 (INFERRED)

- 论文样本是 1976-2007 美股个股 → A 股 ETF 需独立回测
- ETF 跟踪误差 → 可能扭曲 %pos %neg
- 极端低流动性标的 → 涨跌天数受成交量虚增干扰
- ID 单独使用 alpha 有限，**必须与 PRET（动量）配合分组**

## V25 实施 Hook

1. 在 V25 indicators 模块加 `compute_id(returns, 252, 21)`
2. 双层排序：动量 Top 20% → ID 最低 50%
3. 与 [[均线偏离度]] 合成 "BIAS-ID 双因子" 看板：四象限决策
4. 滚动验证：每年重算 ID，验证自相关 ~0.034 是否在 A 股 ETF 上一致

## 相关页面

- 主体：[[FIP效应]]、[[动量衰竭早期识别]]
- 配套：[[有限注意力]]、[[BIAS减仓]]
- 对照指标：[[均线偏离度]]、[[RSRS]]、[[Jegadeesh-Titman动量]]
- 主题：[[ETF轮动与交易策略]]
