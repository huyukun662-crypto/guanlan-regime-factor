---
tags: [子策略, 微观结构, 信息不对称, 订单流毒性, 动量衰竭]
created: 2026-05-07
updated: 2026-05-07
type: entity
entity_type: indicator
sources:
  - wiki/sources/2012-volume-clock-easley-lopez-de-prado-ohara.md
  - wiki/sources/2012-vpin-overview-lopez-de-prado.md
  - wiki/sources/2022-02-21-gf-hfdata-factor-series-6-info-asymmetry.md
---

# VPIN（Volume-Synchronized Probability of Informed Trading）

> 基于成交量分箱估算"知情交易概率"的微观结构信号 — 用**订单流毒性**度量市场脆弱性，**早于价格**给出动量衰竭与流动性危机预警

## 一句话定义

把成交量切成等量"桶"（不是等时桶），用 **BVC（Bulk Volume Classification）** 把每桶的成交量拆成主动买/主动卖，VPIN = 滚动 N 桶上 `|V_buy − V_sell| / V` 的均值。值越高 → 单向订单流越集中 → 知情交易者在主导 → 流动性提供方将撤出 → 趋势随时崩。

<!-- confidence: EXTRACTED -->
<!-- evidence: Easley, López de Prado, O'Hara (2012) "Flow Toxicity and Liquidity in a High-Frequency World", Review of Financial Studies. 经典论文 -->

## 历史溯源

- **PIN（Probability of Informed Trading）**：Easley & O'Hara 1992 — 基于交易日订单不平衡的最大似然估计
- **VPIN**：Easley, López de Prado, O'Hara 2012 — PIN 的"成交量同步化"版本，避开 PIN 的 MLE 数值不稳定性
- 2010 年 5 月 6 日 **Flash Crash** 前 1 小时 VPIN 出现历史极端值，论文以此论证 VPIN 的预警能力

## 计算流程

```
1. 把连续成交流切成等成交量的 N 个 "桶"（每桶 V_bucket = 总日均量 / N，常用 N=50 或 250 桶）
2. 对每个桶：
     V_buy_i  = V_bucket * Φ((P_close_i − P_close_{i-1}) / σ)
     V_sell_i = V_bucket − V_buy_i
   其中 Φ 是标准正态 CDF（BVC 关键步骤），σ 是分桶收益的滚动标准差
3. VPIN_t = (1/n) * Σ_{i=t-n+1}^{t} |V_buy_i − V_sell_i| / V_bucket
   一般 n=50（即用最近 50 桶估算）
4. 进一步可对 VPIN 做 CDF 转换得到"VPIN 分位数"，方便阈值化
```

<!-- confidence: EXTRACTED -->
<!-- evidence: Easley et al. 2012 公式 (1)-(3)，BVC 在 §III.A -->

## 动量衰竭早期识别机制

VPIN 不是方向信号，是**脆弱性信号**。在 ETF 轮动 / 个股动量场景下：

| VPIN 形态 | 解读 | 对动量策略的提示 |
|---|---|---|
| VPIN 持续低位 + 价格上行 | 公共信息驱动的健康趋势，做市商敢做对手盘 | 持仓 |
| **VPIN 缓慢上升 + 价格仍上行** | 知情资金在持续派发或建仓，被动买盘吸收变难 | **预警**：开始考虑止盈准备 |
| **VPIN 突然飙升至历史 99% 分位** | 流动性即将枯竭，做市商撤出 | **强烈减仓信号**：动量随时反转 |
| VPIN 高位 + 价格震荡 | 知情交易已完成派发，散户接盘阶段 | 不再加仓，等突破方向确认 |
| VPIN 回落至中位 + 价格已大跌 | 信息不对称消化完毕 | 反弹/反转开始具备条件 |

**关键性质**：VPIN 的领先性来自"做市商在感受到毒性后会主动撤单 → 流动性下降 → 价格冲击放大"，这条链条**早于价格本身的衰竭**。

<!-- confidence: INFERRED -->
<!-- evidence: 推理依据：Easley et al. 2012 §V Flash Crash 案例显示 VPIN 在 5/6 当日 11:55 EST 已到历史峰值，价格崩盘发生在 14:30。同样逻辑可推及个股/ETF 动量衰竭场景，但日频 A-share 实证待验 -->

## 与同主题"动量衰竭"指标的对比

| 指标 | 数据要求 | 衰竭检测维度 | 信号性质 | 滞后性 |
|---|---|---|---|---|
| [[九转序列]] | OHLC 日频 | 价格结构（连续未创新高/低）| 离散计数 | **中** — N=9 计满才触发 |
| [[低延时趋势]] | 收盘价 | 趋势斜率（频域低频成分）| 连续斜率 | **低** — 频域滤波减相位延迟 |
| **VPIN** | **Tick / 分钟成交量 + 价格** | **订单流毒性（微观结构）** | **概率分位** | **最低** — 早于价格变化 |
| [[均线偏离度]] | 收盘价 | 价格 vs 均值偏离 | 连续 z-score | 中 |
| [[阶矩择时]] | 收益率 | 高阶矩（偏度/峰度）| 连续 | 中（前瞻性） |

→ **VPIN 在三者中理论上最早**，但实施门槛最高（需高频数据）。九转最简，但触发稀疏。低延时居中。

## 在 A 股 / ETF 上的实用化路径

VPIN 原生设计在美股 tick 数据上。A 股要落地需做几层 trade-off：

### Path 1：分钟级近似（推荐起点）
- 数据：1 分钟 OHLCV（聚宽 / Tushare 可得）
- 桶定义：以日均成交量 / 50 为 V_bucket，分钟内累积达到桶大小即收桶（跨多分钟也行）
- BVC σ：用 30 日滚动 1 分钟收益的标准差
- 输出：日终的 VPIN 值 + 滚动 250 日的 VPIN 历史分位
- **可用于 ETF 日频策略的"微观结构 overlay"**：当持仓标的 VPIN 分位 > 0.95 时主动减仓 / 切换

### Path 2：日频强降级（理论近似）
- 数据：日 OHLCV
- BVC：用 (close - prev_close) / σ_close 给出当日"主动买占比"
- 桶：每日就是一个桶
- 缺点：信号粗糙，VPIN 的核心优势（成交量同步化）几乎丢失，仅作为最后选择

### Path 3：tick 级原版（不推荐当前阶段）
- 需 L2 数据 / Level-1 委托单
- 工程复杂度高，A 股个人级别数据成本难承受

<!-- confidence: INFERRED -->
<!-- evidence: 实施路径基于 VPIN 原始定义的扩展，A 股具体阈值需经实证校准；目前 ETF_New 项目尚未跑过 VPIN 离线回测 -->

## 优势

- **预警领先性强** — 理论上比价格信号早 30 分钟到 1 小时（HFT 场景），日频近似下可能领先 1-3 个交易日
- **方向独立** — 给的是"何时趋势会出问题"而不是"涨还是跌"，与 [[低延时趋势]]、MOM_R2 等方向信号正交
- **回测中跨市场表现稳定** — Easley et al. 2012 在 E-mini S&P / 期货 / 个股都验证过

## 劣势 / 已知限制

- **数据成本高** — 真正发挥需 tick 或分钟级数据
- **阈值非平稳** — 必须用滚动分位而非绝对值阈值
- **对方向性预测能力弱** — 只能说"动量将不稳"，不能说"反转方向"
- **A 股 T+1 制度下短卖受限** — 即使 VPIN 给空头预警，可执行性低于美股
- **学界存在批评**：Andersen & Bondarenko 2014 论文指出 VPIN 在某些条件下对 Flash Crash 的预测是"事后看见"而非"事前预测" — 阈值校准至关重要

<!-- confidence: EXTRACTED -->
<!-- evidence: Andersen, T.G. & Bondarenko, O. (2014) "VPIN and the Flash Crash", Journal of Financial Markets — 反驳 Easley 2012 的预测能力主张 -->

## V25 / ETF_New 复现 Hook

```python
import numpy as np
from scipy.stats import norm

def compute_vpin(price: np.ndarray, volume: np.ndarray,
                 bucket_size: float, n_buckets: int = 50,
                 sigma_window: int = 30) -> np.ndarray:
    """计算 VPIN 时序（基于 BVC 的等成交量分桶）.

    Args:
        price : 1-min 收盘价序列
        volume: 1-min 成交量序列
        bucket_size: 每桶目标成交量（如日均量/50）
        n_buckets: VPIN 滚动窗口（桶数）
        sigma_window: BVC 用的收益滚动标准差窗口（分钟数）

    Returns:
        bucket_vpin : 每桶结束时的 VPIN 值
    """
    rets = np.diff(np.log(price))
    sigma = pd.Series(rets).rolling(sigma_window, min_periods=sigma_window // 2).std().values

    # 累积成交量分桶
    cum_vol = 0.0
    bucket_vbuy, bucket_vsell = [], []
    cur_vbuy = cur_vsell = 0.0
    for i in range(1, len(price)):
        if np.isnan(sigma[i - 1]) or sigma[i - 1] < 1e-12:
            continue
        prob_buy = norm.cdf(rets[i - 1] / sigma[i - 1])
        v_buy = volume[i] * prob_buy
        v_sell = volume[i] - v_buy
        cur_vbuy += v_buy
        cur_vsell += v_sell
        cum_vol += volume[i]
        if cum_vol >= bucket_size:
            bucket_vbuy.append(cur_vbuy)
            bucket_vsell.append(cur_vsell)
            cum_vol = cur_vbuy = cur_vsell = 0.0

    bucket_vbuy = np.array(bucket_vbuy)
    bucket_vsell = np.array(bucket_vsell)
    imbalance = np.abs(bucket_vbuy - bucket_vsell) / bucket_size
    vpin = pd.Series(imbalance).rolling(n_buckets).mean().values
    return vpin
```

**集成思路**：
- 对 ETF 池 top-1 持仓标的，每日盘后跑 VPIN
- 当 VPIN 分位（滚动 250 日）> 0.95 → 标志该标的"动量风险升高"
- 与 [[均线偏离度]]、[[九转序列]] 形成"三层衰竭过滤"：
  - 微观结构层（VPIN）
  - 趋势导数层（[[低延时趋势]] 斜率拐头）
  - 价格结构层（[[九转序列]] 计数完成）
  
  任意一层报警即触发持仓减半，两层同时报警即清仓。

## A 股本土化：VWPIN（重要扩展）

广发证券 2022 [[2022-02-21-gf-hfdata-factor-series-6-info-asymmetry]] 引入 [[VWPIN]]（基于李平等 2020）作为 VPIN 的 A 股因子化版本：

- 用**等时间区间（5min × 48）** 替代 VPIN 的等成交量分桶 → 实时性更强
- 用**订单笔数不平衡 |S - B| / (S + B)** 替代 VPIN 的成交量不平衡 → 抗拆单能力强
- 全市场周度调仓 IC 0.063 / 信息比 1.18，中证 500 信息比 1.76
- 与 BARRA 因子相关性低，可直接加入多因子模型

→ **A 股工程实践优先选 [[VWPIN]]**，VPIN 作为理论框架理解。

## 在素材中的出现

- [[2012-volume-clock-easley-lopez-de-prado-ohara]]（VPIN 范式宣言论文）
- [[2012-vpin-overview-lopez-de-prado]]（Wiki 综述 + 应用边界与争议）
- [[2022-02-21-gf-hfdata-factor-series-6-info-asymmetry]]（A 股因子化实证 → [[VWPIN]]）

## 研究待办

1. 在 [[ETF_New]] 项目数据上跑 VPIN / VWPIN 离线回测（需切换到 1-5 分钟数据）
2. 验证 2025 年 A 股趋势市中 VPIN 是否能提前给出"主线 ETF 动量衰竭"信号
3. 寻找 A 股 BVC 的最佳 σ 窗口（美股经验是 30-60 分钟，A 股可能不同）
4. 跟踪李平等 2020 原文以及"个股层 VWPIN 信号反向"现象的根本机制

## 相关页面

- 衍生：[[VWPIN]]（A 股本土化版本，工程实践首选）
- 父级：[[PIN]]（理论根基）
- 配套：[[BVC算法]]、[[订单流毒性]]、[[Lee-Ready算法]]
- 主题：[[动量衰竭早期识别]]、[[高频交易与市场微观结构]]、[[ETF轮动与交易策略]]
- 同主题工具：[[九转序列]]、[[低延时趋势]]、[[均线偏离度]]
- 项目：[[ETF_New]]（用例 — 解决 2025 趋势市 dual+STR 失效）
- 学术：[[限价订单簿LOB]]、[[最优执行]]
- 关键人物：[[Maureen O'Hara]]、[[David Easley]]、[[Marcos Lopez de Prado]]
