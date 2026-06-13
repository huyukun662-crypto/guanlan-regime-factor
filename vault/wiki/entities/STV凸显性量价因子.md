---
tags: [因子, 行为金融, 凸显理论, A股本土化, 涨跌停, 换手率]
created: 2026-05-06
updated: 2026-05-06
type: entity
entity_type: factor
sources:
  - wiki/sources/2026-05-06-quantsplaybook-str-deep-dive.md
---

# STV 凸显性量价因子

> Salience Theory + Volume — 广发证券 2023-03 提出的 [[凸显性因子STR]] 在 A 股的本土化改造，**加入"量"维度应对涨跌停制度**

## 一句话定义

美股 STR 在 A 股**水土不服**（涨跌停截尾价格信号 + T+1 限制），广发改造为 STV：**收益率超 10% 阈值时按 |r| 排序，未超时按换手率排序** — 把"价"凸显性 + "量"凸显性结合，更适应 A 股监管特征。

## 来源

广发证券《行为金融研究系列之七：凸显理论之 A 股"价""量"应用》 — **2023-03-23**

仓库 PDF：`参考/20230323_广发证券_行为金融研究系列之七.pdf`

## 为什么要改造（A 股 vs 美股）

| 制度 | 美股 | A 股 | 对 STR 的影响 |
|---|---|---|---|
| 涨跌停 | 无（除少数熔断）| **±10% 截尾** | 价格不能充分反映关注度 |
| T+0 / T+1 | 满足条件账户 T+0 | **统一 T+1** | 限制套利效率 |
| 投资者结构 | 机构主导 | **散户主导**（关注度敏感）| 量与关注度高度相关 |

⇒ A 股的"凸显信号"应该既看价，也看量。

## STV 凸显性函数

```
σ(turnover_{i,s}, r_{i,s}) = |r_{i,s}| × 1000,        若 |r_{i,s}| ≥ X (=10%)
                            = turnover_{i,s},          否则
```

**核心设计**：
- × 1000 确保"涨跌停"凸显性绝对压倒"非涨跌停"凸显性
- 非涨跌停时 → 用换手率作为关注度 proxy

## Python 实现（[[hugo2046]]）

```python
def get_stv_feature() -> str:
    """生成 Qlib 表达式"""
    abs_ret = "Abs($close/Ref($close,1)-1)"
    return f"If({abs_ret}>=0.1, {abs_ret}*100, $turnover_rate)"

# 直接用 Qlib 表达式计算
sigma_frame = D.features(POOLS, fields=[get_stv_feature()])
sigma_frame.columns = ['sigma']
sigma_frame = sigma_frame.unstack(level=0)['sigma']

# 与 STR 共用 calc_weight
stv_w = calc_weight(sigma_frame)            # δ=0.7 power weight
STV   = stv_w.rolling(20).cov(pct_chg)      # 20 日滚动协方差
```

## 注意：广发原文 vs hugo2046 实现的微差

- 原文：`× 1000`
- hugo2046 代码：`× 100`（`{abs_ret}*100`）
- 实际**是数量级问题**而非本质 — 只要远大于 turnover_rate（通常 < 5%）即可

## 与 [[凸显性因子STR]] 三版本的位置

| 版本 | 关注维度 | 适配市场 |
|---|---|---|
| v1 美股原始 STR | 价（截面平均基准）| 美股最优 |
| v2 方正惊恐 | 价（HS300 基准）| A 股一般改善 |
| **v3 STV（本因子）** | **价 + 量** | A 股最优（针对涨跌停）|

## 适用与限制

✅ A 股股票池 best fit（针对涨跌停 + 换手率信号设计）
✅ 与 STR 同源 → 可与 STR/惊恐 因子合成
⚠ 创业板 / 科创板涨跌停 20% → 阈值 X 需调整
⚠ 北交所 30% → 也需调整
⚠ 新股 / 次新股股价波动剧烈 → 可能误信号

## V25 集成

- 优先级：A（A 股 best fit）
- 复杂度：低
- 数据：[[akshare]] 或 efinance 都可获取换手率
- 待办：
  1. 实现 `compute_stv(close, turnover, X=0.1)` Python 版（不依赖 Qlib）
  2. 在 V25 个股池上跑 IC 测试
  3. 与 [[凸显性因子STR]] v1/v2 对比

## 在素材中的出现

- [[2026-05-06-quantsplaybook-str-deep-dive]]：完整公式 + Python 实现 + 与 v1/v2 对比

## 相关页面

- 母概念：[[凸显性因子STR]]、[[凸显理论]]
- 配套：[[惊恐度因子]]、[[QuantsPlaybook]]
- 主题：[[Alpha挖掘与因子正交性]]
