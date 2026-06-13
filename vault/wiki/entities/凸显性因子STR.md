---
tags: [因子, 行为金融, 极端收益, 凸显理论, Cosemans-Frehen]
created: 2026-05-05
updated: 2026-05-06
type: entity
entity_type: factor
sources:
  - wiki/sources/2026-05-05-quantsplaybook-repo.md
  - wiki/sources/2026-05-06-quantsplaybook-str-deep-dive.md
---

# 凸显性因子 STR

> Salience Theory Return — 用 [[凸显理论]] 衡量极端收益对投资者注意力扭曲的行为金融因子（Cosemans-Frehen 2021）

## 一句话定义

凸显理论（Salience Theory，BGS 2012）认为投资者**注意力被截面凸显的极端回报吸引**而忽略不凸显的回报，从而扭曲决策权重。STR 把这个心理偏差**定量提取为月度因子**：
- ST > 0 → 上行凸显 → 投资者风险寻求 → 未来下跌（看空）
- ST < 0 → 下行凸显 → 投资者过度低估 → 未来上涨（看多）

## 完整公式（Cosemans-Frehen 2021）

### Step 1：凸显度 σ
```
σ(r_{i,d}) = |r_{i,d} - r̄_d| / (|r_{i,d}| + |r̄_d| + 0.1)
```
- r_{i,d}：股票 i 在 d 日的日收益
- r̄_d：d 日截面所有股票平均收益
- 0.1：分母防 0

### Step 2：Salience Weights ω
```
ω_{i,d} = δ^{k_{i,d}} / Σ(δ^{k_{i,d'}} · π_{d'})
```
- k = σ 的截面排序（k=1 凸显最强）
- δ = 0.7（凸显扭曲程度）
- π = 1/N

### Step 3：STR = 月度日度 ω 与收益率协方差
```
STR_i = cov(ω_{i,d}, r_{i,d})    # 滚动 20 天
```

## 三版本对比（A 股本土化演进）

| 维度 | **v1 美股原始** | **v2 方正惊恐**（方大 2022-12）| **v3 广发 STV**（广发 2023-03） |
|---|---|---|---|
| 基准 | 截面平均 | 沪深 300 | 截面平均 |
| 排序 | σ 大小 | 直接乘 σ | σ 含**换手率** |
| 权重 | δ^k | 无（直接 σ）| δ^k |
| 月度合成 | cov(ω, r) | mean + std 等权 | cov(stv_w, r) |
| 适配 A 股 | 弱 | 中（用 HS300）| **强**（应对涨跌停）|
| 子变形 | 1 | **4 个** | 1 |

详见 [[STV凸显性量价因子]] / [[惊恐度因子]]。

## v2 方正"惊恐"系列的 4 个变形

| 因子 | 权重项 | 经济直觉 |
|---|---|---|
| **原始惊恐** | 仅惊恐度 × 收益率 | 守株待兔 + 草木皆兵 |
| **波动率加剧-惊恐** | + 1 分钟频率波动率 | 高频 vol 强化"凸显"感 |
| **个人投资者交易比-惊恐** | + 个人投资者占比（小单 < 4 万）| 散户更易被极端收益吸引 |
| **注意力衰减-惊恐** | + (今日 σ - 过去 2 日 σ 均值)正部分 | 边际新增注意力 |

## v3 广发 STV 凸显性函数（应对 A 股涨跌停）

```
σ(turnover, r) = |r| × 1000,    若 |r| ≥ 10%（涨跌停阈值）
              = turnover_rate,   否则
```

**经济直觉**：
- 涨跌停 → "价"凸显性绝对压倒"量"凸显性（× 1000）
- 非涨跌停 → 用换手率反映散户关注度
- 这是 A 股本土化的关键创新

## Python 实现（[[hugo2046]] in QuantsPlaybook）

```python
def calc_sigma(df, bench=None):
    if bench is None: bench = df.mean(axis=1)
    a = df.sub(bench, axis=0).abs()
    b = df.abs().add(bench.abs(), axis=0) + 0.1
    return a.div(b)

def calc_weight(sigma, delta=0.7):
    rank = sigma.rank(axis=1, ascending=False)
    a = rank.apply(lambda x: np.power(delta, x), axis=1)
    b = a.mean(axis=1)
    return a.div(b, axis=0)

# v1 美股原始 STR
w   = pct_chg.pipe(calc_sigma).pipe(calc_weight)
STR = w.rolling(20).cov(pct_chg).stack()

# v2 方正惊恐
sigma_v2 = pct_chg.pipe(calc_sigma, bench=hs300)
weighted = sigma_v2.mul(pct_chg)
avg_score = weighted.rolling(20).mean()
std_score = weighted.rolling(20).std()
terrified = (avg_score + std_score) * 0.5

# v3 广发 STV
def get_stv_feature():
    return "If(Abs($close/Ref($close,1)-1)>=0.1, Abs($close/Ref($close,1)-1)*100, $turnover_rate)"
sigma_stv = D.features(POOLS, fields=[get_stv_feature()])
stv_w = calc_weight(sigma_stv)
STV   = stv_w.rolling(20).cov(pct_chg)
```

## 学术源头（5 篇 PDF 在 QuantsPlaybook 仓库）

| 文献 | 角色 |
|---|---|
| **Bordalo-Gennaioli-Shleifer 2012**（BGS）| 凸显理论原创 |
| **Cosemans-Frehen 2021** | STR 因子构建 |
| 招商证券 2022-12-14 | 中文 STR 经典 |
| **方大证券 2022-12-13** | v2 "惊恐"系列原始研报 |
| **广发证券 2023-03-23** | v3 STV A 股本土化原始研报 |

## 与已有素材的关联

### 行为金融因子三件套（机制不同 → 正交合成潜力大）
- **STR**（本因子）：截面凸显度加权收益 → 注意力扭曲
- [[特异市值因子]]：截面回归残差 → 市值与基本面偏离
- [[球队硬币因子]]：体育博彩动量迁移 → 个股动量识别
- 三个因子机制完全不同 → **应正交性极好** → 适合多因子合成

### 与 [[AlphaZero因子挖掘]]
- AlphaZero：自动进化挖掘
- STR：手工 + 行为金融理论
- 互补：好的行为金融因子（如 STR）可作 AlphaZero 初始种群

### 与 [[2020-quantitative-trading-textbook]] 教科书
- 教科书第 8 章涉及 A 股监管特殊性
- v3 STV 是 A 股监管制度（涨跌停）下的因子工程化典型 — 把教科书理论对接实战

### 与 [[Qlib]] / [[Alpha158]]
- v2/v3 都用 Qlib 框架训练
- 用 GBDT 多因子合成（feature: STR + STV + avg_score + std_score；label: next_ret）

## V25 复现 Hook（优先级 S）

### Quick wins（3 个版本依次实现）
1. **v2 原始惊恐**（最简单 — 只需 σ + 20 日 mean/std + HS300 收益）
2. **v3 STV**（稍复杂 — 需要换手率数据，A 股 best fit）
3. **v1 美股 STR**（参考实现）

### 待办
- 实现 `compute_str_v1` / `compute_str_v2_terrified` / `compute_str_v3_stv`
- 与 [[特异市值因子]] / [[球队硬币因子]] 做相关性矩阵
- 在 V25 个股池上测试（**避免** ETF 池 — 参考 [[2026-05-05-qpb-industry-pricevolume-etf-rotation]] 的"ETF 上多因子失效"警示）
- 数据源切换：QuantsPlaybook 用 Qlib → V25 改用 [[akshare]] / efinance

## 在素材中的出现

- [[2026-05-05-quantsplaybook-repo]]：B-因子构建类（22+）的代表性"行为金融"因子
- **[[2026-05-06-quantsplaybook-str-deep-dive]]：完整 3 版本 + 公式 + 源码（深挖）**

## 相关页面

- 主题：[[Alpha挖掘与因子正交性]]、[[量化多因子策略]]
- 同类：[[特异市值因子]]、[[球队硬币因子]]
- 衍生：[[STV凸显性量价因子]]、[[惊恐度因子]]、[[凸显理论]]
- 配套：[[QuantsPlaybook]]、[[hugo2046]]、[[Qlib]]
