---
tags: [算法, 微观结构, 订单分类, 高频]
created: 2026-05-07
updated: 2026-05-07
type: entity
entity_type: algorithm
sources:
  - wiki/sources/2012-volume-clock-easley-lopez-de-prado-ohara.md
  - wiki/sources/2022-02-21-gf-hfdata-factor-series-6-info-asymmetry.md
---

# BVC 算法（Bulk Volume Classification）

> Easley-López de Prado-O'Hara 2012 提出的"按比例分配 buy/sell 成交量"算法 — 是 [[VPIN]] 的核心子模块，比 tick-rule 和 [[Lee-Ready算法]] 都更准确

## 一句话定义

不像传统方法那样把每笔交易要么标记为 buy 要么标记为 sell，BVC 把每根 K 线的**总成交量按比例分配**：当价格上涨多时多分给 buy，价格下跌多时多分给 sell。比例由价格变化的 **z-score 经过正态 CDF 转换**得出：

```
V_buy_i  = V_i · Φ((P_i - P_{i-1}) / σ_dP)
V_sell_i = V_i · (1 - Φ((P_i - P_{i-1}) / σ_dP)) = V_i - V_buy_i
```

其中：
- `V_i`：第 i 根 K 线的总成交量
- `P_i - P_{i-1}`：相邻 K 线收盘价变化
- `σ_dP`：价格变化的标准差（一般用滚动 30-60 期）
- `Φ(·)`：标准正态分布的累积分布函数

<!-- confidence: EXTRACTED -->
<!-- evidence: [[2012-volume-clock-easley-lopez-de-prado-ohara]] §"Choice #2" + [[2022-02-21-gf-hfdata-factor-series-6-info-asymmetry]] §三(二) -->

## 与传统算法的关键差异

| 维度 | **Tick-rule** | **Lee-Ready** | **BVC** |
|---|---|---|---|
| 数据要求 | tick 价格 | tick 价格 + quote midpoint | volume / time bars |
| 单笔分类 | 整笔 buy 或 sell | 整笔 buy 或 sell | **比例分配** |
| 准确性 | 中 | 较高 | **最高**（[[2012-volume-clock-easley-lopez-de-prado-ohara]] 证明）|
| 可在 1min K 线上工作 | 否 | 否 | **是** |
| 用于 VPIN | 不推荐 | 不推荐 | **必须** |

## 算法本质

BVC 的核心假设：**价格变化是 informed trading 的可测量信号**。
- ΔP 大正值 → 多数交易在 ask 上发生 → 多分配给 buy
- ΔP 大负值 → 多数交易在 bid 上发生 → 多分配给 sell
- ΔP ≈ 0 → 50/50 平分

正态 CDF 是一个平滑的"概率"映射，避免硬阈值带来的边界效应。

## 关键参数：σ_dP 的选择

广发证券 2022 [[2022-02-21-gf-hfdata-factor-series-6-info-asymmetry]] 与 Easley et al. 论文中的实操经验：

- **窗口**：取近 30-60 期（K 线根数）的滚动标准差
- **基础 K 线频率**：1min 或 5min 都可，BVC 对 K 线频率相对稳健
- **极端情况**：σ_dP 趋于 0 时 → 退化到所有量分给 buy 或 sell（极端价格变化）

## 实施警告（Wikipedia [[2012-vpin-overview-lopez-de-prado]] 强调）

> "Alternative implementations of VPIN will yield results inconsistent with this theory."

VPIN 实施的 4 个常见错误中，**第 2 条**就是关于 BVC：
> "VPIN applies the Bulk Classification algorithm, **not the Tick-rule** for volume classification."

很多复现代码把 BVC 简化成 tick-rule（涨为 buy / 跌为 sell 整笔分配），结果与原论文严重不一致。**BVC 必须做比例分配**。

## Python 实现

```python
import numpy as np
import pandas as pd
from scipy.stats import norm


def bvc_classify(prices: np.ndarray, volumes: np.ndarray,
                 sigma_window: int = 30) -> tuple[np.ndarray, np.ndarray]:
    """Bulk Volume Classification.

    Args:
        prices: 1D array of K线 close prices, length N
        volumes: 1D array of K线 volumes, length N
        sigma_window: rolling window for σ_dP estimation

    Returns:
        v_buy: 1D array of buy volumes for each K line
        v_sell: 1D array of sell volumes for each K line
    """
    rets = np.diff(prices)
    rets = np.concatenate([[0.0], rets])  # 对齐长度

    # 滚动 std
    sigma = pd.Series(rets).rolling(sigma_window, min_periods=sigma_window // 2).std().values

    # buy 比例 = Φ(ret / σ)
    with np.errstate(divide='ignore', invalid='ignore'):
        prob_buy = norm.cdf(np.where(sigma > 1e-12, rets / sigma, 0.0))

    v_buy = volumes * prob_buy
    v_sell = volumes - v_buy
    return v_buy, v_sell
```

## 与 VWPIN 的关系

[[VWPIN]] 在 A 股本土化中**不再使用 BVC**，而是改用 [[Lee-Ready算法]] 在 5min 区间内对每笔订单做整笔分类。原因：
- A 股 Level-2 数据可直接获取每笔订单方向（无需估算）
- BVC 对 σ_dP 敏感，A 股涨跌停制度下 σ 估计可能失真
- VWPIN 度量的是**订单笔数**而非成交量，Lee-Ready 更直接

但在 ETF / 商品期货等没有 L2 笔级数据的场景，BVC 仍是首选。

## 适用场景

- **VPIN 估计**：必须用 BVC（Easley et al. 2012 强调）
- **流动性研究**：作为 trade direction 的标准估计
- **执行算法**：评估订单的 information leakage
- **跨市场对比**：BVC 不依赖 quote midpoint，可在缺少 L1 quote 数据的市场使用

## 局限

- 假设价格变化服从近似正态 → 厚尾市场误差变大
- σ_dP 滚动估计在 regime shift 时滞后
- 对**短窗口**（如 1min）下高噪声的价格变化容易过度分配

## 在素材中的出现

- [[2012-volume-clock-easley-lopez-de-prado-ohara]]（提及 BVC 比 tick-rule 更准）
- [[2012-vpin-overview-lopez-de-prado]]（Wiki 第 2 条避坑警告）
- [[2022-02-21-gf-hfdata-factor-series-6-info-asymmetry]] §三(二)（在 VPIN 推导中给出 BVC 公式）
- 原始论文：Easley, López de Prado, O'Hara (2012) "Bulk Classification of Trading Activity"（SSRN 1989555）

## 相关页面

- 配套：[[VPIN]]、[[VWPIN]]、[[PIN]]
- 替代算法：[[Lee-Ready算法]]、[[Tick-rule]]
- 主题：[[高频交易与市场微观结构]]、[[动量衰竭早期识别]]
