---
tags: [QuantsPlaybook, 凸显理论, STR, STV, 行为金融, 深挖, source]
created: 2026-05-06
updated: 2026-05-06
type: source
source_type: github_strategy
source_url: https://github.com/hugo2046/QuantsPlaybook/tree/master/B-%E5%9B%A0%E5%AD%90%E6%9E%84%E5%BB%BA%E7%B1%BB/%E5%87%B8%E6%98%BE%E7%90%86%E8%AE%BASTR%E5%9B%A0%E5%AD%90
priority: S
ingest_type: deep_dive
sources: []
---

# 凸显理论 STR 因子（QuantsPlaybook 深挖）

> 来源：[QuantsPlaybook B-因子构建类/凸显理论STR因子](https://github.com/hugo2046/QuantsPlaybook/) | 复现：[[hugo2046]] | 2023-04
> **本素材是知识库现有 [[凸显性因子STR]] 实体页的"深挖版"** — 把 stub 升级为含 3 版本对比 + 完整公式 + 源码 + 5 篇参考文献的素材

## 一句话定位

把 [[凸显性因子STR]] 从"招商/方大 2022 年提出的行为金融因子"这个 stub 概念，**深挖到完整 3 版本实现 + 学术源头 + A 股本土化改造**：
- **v1 美股原始 STR**（Cosemans-Frehen 2021）
- **v2 方正"惊恐"系列**（方大证券 2022-12-13） — 守株待兔 + 草木皆兵心理
- **v3 广发 STV**（广发证券 2023-03-23） — 加入"量"的维度，针对 A 股涨跌停制度

## 学术根基（前景理论 → 凸显理论）

### 前景理论（Kahneman-Tversky 1979）
- 投资者的决策权重不等于客观概率
- 给小概率尾部事件赋更高权重
- Barberis 2016 据此构建 TK 价值因子（高 TK 高估，低 TK 低估）

### 凸显理论（BGS 2012, Bordalo-Gennaioli-Shleifer）
- **资产横向比较中，投资者注意力被"凸显"（salient）的回报吸引**
- 不凸显的回报被忽略
- 例子："只记得某只股票当月涨停，不记得它微涨 2% 的时候"
- **Cosemans-Frehen 2021** 据此构建 STR：
  - ST > 0：股票最高回报凸显 → 投资者过度关注上行 → 风险寻求 → 未来下跌
  - ST < 0：股票最低回报凸显 → 投资者过度关注下行 → 过度低估 → 未来上涨

### 凸显理论 vs 前景理论（关键区别）
- **前景理论**：尾部收益获更高权重 = 因为**概率小**
- **凸显理论**：极端收益获更高权重 = 因为**截面上凸显**（相对市场平均）
- 凸显理论同时含**时序信息 + 截面信息**

## 三版本实现完整对比

### v1：美股原始 STR（Cosemans-Frehen 2021）

**Step 1**：股票收益与市场收益的"凸显度" σ
```
σ(r_{i,d}) = |r_{i,d} - r̄_d| / (|r_{i,d}| + |r̄_d| + 0.1)
```
- r_{i,d}：股票 i 在 d 日的日收益
- r̄_d：d 日截面所有股票平均收益
- 0.1：分母防 0 项

**Step 2**：Salience Weights（按 σ 排序计算）
```
ω_{i,d} = δ^{k_{i,d}} / Σ(δ^{k_{i,d}} · π_{d'})
```
- k = σ 的排序（最高 σ 排第 1）
- δ = 0.7（控制凸显扭曲程度）
- π = 1/N（每日均匀基准）
- k=1 凸显性最强；k=max 凸显性最弱

**Step 3**：STR = 月度日度 ω 与收益率的协方差
```
STR_i = cov(ω_{i,d}, r_{i,d})        # 月度日度滚动 20 天
```

**[[hugo2046]] 实现**（`scr/core.py`）：
```python
def calc_sigma(df, bench=None):
    if bench is None: bench = df.mean(axis=1)
    a = df.sub(bench, axis=0).abs()
    b = df.abs().add(bench.abs(), axis=0) + 0.1
    return a.div(b)

def calc_weight(sigma, delta=0.7):
    rank = sigma.rank(axis=1, ascending=False)   # 截面 σ 排序
    a = rank.apply(lambda x: np.power(delta, x), axis=1)
    b = a.mean(axis=1)
    return a.div(b, axis=0)

# 主流程
w   = pct_chg.pipe(calc_sigma).pipe(calc_weight)
STR = w.rolling(20).cov(pct_chg).stack()
```

### v2：方正"惊恐"系列（方大证券 2022-12-13）

**关键差异**（vs v1）：
- 不再用 δ-power weight，而是**直接用"惊恐度" σ 加权收益率**
- 用**沪深 300 收益率**作为基准（替代截面平均收益）
- 把"加权决策分"做月度均值 + 标准差 → 等权合成"原始惊恐"因子

**惊恐度公式**：
```
惊恐度_{i,d} = |r_{i,d} - r_{HS300,d}| / (|r_{i,d}| + |r_{HS300,d}| + 0.1)
```

**4 类惊恐变形**：
| 因子 | 权重项 |
|---|---|
| **原始惊恐**（基础版） | 仅惊恐度 × 收益率 |
| **波动率加剧-惊恐** | + 1 分钟频率波动率（高频 vol） |
| **个人投资者交易比-惊恐** | + 个人投资者占比（小单 < 4 万元）|
| **注意力衰减-惊恐** | + 当日 σ - 过去 2 日 σ 均值（捕捉边际新增关注）|

**因子合成**：
```python
weighted = sigma.mul(pct_chg)              # 加权决策分
avg_score = weighted.rolling(20).mean()    # 惊恐收益（替代 20 日收益）
std_score = weighted.rolling(20).std()     # 惊恐波动（替代 20 日波动率）
terrified = (avg_score + std_score) * 0.5  # 等权合成
```

**心理学解读**：
- 投资者看到极端高收益 → "守株待兔"（认为再来一次） → 买入 → 推高价格 → 未来回落
- 投资者看到极端低收益 → "草木皆兵"（恐惧再亏） → 卖出 → 压低价格 → 未来补涨

### v3：广发 STV（广发证券 2023-03-23）

**关键差异**（vs v1/v2）：
- **加入"量"的维度** — 应对 A 股涨跌停制度
- 收益率超过涨跌停阈值时（10%），按 |r| 排序
- 收益率未达阈值时，按**换手率**排序

**逻辑**：
> 美股不设涨跌停 + 部分账户 T+0 → 价格能充分反映关注 → STR 用"价"足够
> A 股有涨跌停截尾 + T+1 → 价格不能充分反映关注 → 需要加"量"维度

**STV 凸显性函数**：
```
σ(turnover_{i,s}, r_{i,s}) = |r_{i,s}| × 1000,        若 |r_{i,s}| ≥ X (=10%)
                            = turnover_{i,s},          否则
```

`× 1000` 确保超阈值的"价"凸显性绝对压倒"量"凸显性。

**[[hugo2046]] 实现**：
```python
def get_stv_feature():
    abs_ret = "Abs($close/Ref($close,1)-1)"
    return f"If({abs_ret}>=0.1,{abs_ret}*100,$turnover_rate)"

# 用 Qlib 的 D.features 表达式直接计算
sigma = D.features(POOLS, fields=[get_stv_feature()])
stv_w = calc_weight(sigma)
STV   = stv_w.rolling(20).cov(pct_chg)
```

## 三版本对比表

| 维度 | v1 美股原始 STR | v2 方正惊恐 | v3 广发 STV |
|---|---|---|---|
| 来源 | Cosemans-Frehen 2021 | 方大证券 2022-12 | 广发证券 2023-03 |
| 基准 | 截面平均收益 | **沪深 300 收益** | 截面平均（同 v1） |
| 排序信号 | σ 大小 | 直接乘 σ | σ 含**换手率**（量）|
| 权重 | δ^k （δ=0.7） | 无 δ-power（直接 σ）| 同 v1（δ-power） |
| 月度合成 | cov(ω, r) | mean + std 等权 | cov(stv_w, r) |
| 适配 A 股 | 弱（无 T+0 / 涨跌停制度差异）| 中（用 HS300）| **强**（针对涨跌停）|
| 子变形 | 1 | **4 个**（基础+波动率+个人投资者+注意力衰减）| 1 |

## Qlib 工程化（v2/v3 共用）

代码用 [[Qlib]] 框架完整训练 + 回测：

```python
# 数据切分
TRAIN  = ("2014-01-01", "2017-12-31")
VALID  = ("2018-01-01", "2019-12-31")
TEST   = ("2020-01-01", "2023-02-17")

# Qlib 处理器
learn_processors = [DropnaLabel()]
infer_processors = [ProcessInf(), CSRankNorm(), Fillna()]

# 数据加载 + 训练
ds = DatasetH(dh_pr, segments={...})
record = run_model(ds, "gbdt", ...)  # GBDT 多因子合成
```

**最终复合因子**：v1 + v2 + v3 一起放入 GBDT 模型（feature: STR + STV + avg_score + std_score；label: next_ret）

## 与已有素材的关联

### 与 [[特异市值因子]]（量化拯救散户）
**机制完全不同但可正交合成**：
- 特异市值：**截面回归残差**（市值偏离基本面）
- STR：**截面凸显度加权收益**（投资者注意力扭曲）
- 都属"残差/扭曲提取 alpha"思想，但维度不同 → 应**正交性极好**

### 与 [[球队硬币因子]]（方正证券 2022）
方正证券同期出品 — 都是**行为金融因子**家族：
- 球队硬币：体育博彩理论迁移（个股动量）
- STR/惊恐：凸显理论（注意力扭曲）
- 共同点：都用"心理偏差"挖 alpha；都强调"截面相对"

### 与 [[AlphaZero因子挖掘]]
- AlphaZero：**自动**进化生成因子（数据驱动）
- STR/STV：**手工**基于行为金融理论构造（理论驱动）
- 启示：好的行为金融因子（如 STR）可作为 AlphaZero 的**初始种群**

### 与 [[2020-quantitative-trading-textbook]] 教科书
- 教科书第 8 章监管讨论涨跌停制度
- 广发 STV 是涨跌停制度下的因子改造典型案例 → 把教科书的"理论"对接到"实战"

### 与 V25 项目
- **优先级 S**：3 版本都有完整 Python 实现，可直接迁移
- 但需替换 Qlib 数据源 → V25 用 efinance / akshare

## 5 个参考 PDF（待 ingest 候选）

仓库 `参考/` 目录的 PDF 都是高价值候选：

| PDF | 价值 | 待 ingest 优先级 |
|---|---|---|
| **方大证券 2022-12-13《显著效应、极端收益扭曲决策权重和"草木皆兵"因子》** | v2 原始研报 | A |
| 招商证券 2022-12-14《"青出于蓝"系列研究之四：行为金融新视角，"凸显性收益"因子STR》 | 中文 STR 经典 | A |
| **广发证券 2023-03-23《行为金融研究系列之七：凸显理论之 A 股"价""量"应用》** | v3 STV 原始研报 | **S**（A 股本土化关键）|
| Cosemans-Frehen 2021《Salience theory and stock prices: Empirical evidence》 | v1 学术原始论文 | A |
| Bordalo-Gennaioli-Shleifer 2013《Salient Stocks (FMA 2017)》 | 凸显理论应用最早论文 | A |

## 风险与待验证

- **3 版本性能差异**：ipynb 仅展示因子分组回测图（本素材无法 OCR），具体 IC 数字未在 markdown 中给出
- **A 股 STV 的 X 阈值**：广发用 10%，但科创板 / 创业板涨跌停 20% → 需调整
- **"个人投资者交易"判定**：方正用"单笔成交金额 < 4 万元"作 proxy → 是个粗略口径
- **样本期 2014-2023**：完整跨牛熊但样本外 2020-2023 仅 3 年
- **未做样本外滚动验证**（Qlib 训练 + 验证 + 测试单次切分）

## V25 复现 Hook

### 优先级 S（3 个 quick win）
1. **v2 原始惊恐**：最简单 — 只需 σ + 20 日 mean/std + HS300 收益。可立即在 V25 个股池上跑
2. **v3 STV**：稍复杂 — 需要换手率数据（[[akshare]] 有），适配 A 股 best fit
3. **v1 美股 STR**：参考实现，A 股效果可能弱于 v2/v3

### 待办
- 实现 `compute_str_v1(returns)` / `compute_str_v2_terrified(returns, bench)` / `compute_str_v3_stv(returns, turnover)`
- 与 [[特异市值因子]] / [[球队硬币因子]] 做相关性矩阵 — 验证三个行为金融因子是否正交
- 在 V25 ETF 池上**而非个股池**测试（参考 [[2026-05-05-qpb-industry-pricevolume-etf-rotation]] 的失效警示 — ETF 上多因子可能失效）

## 原文 raw

[../../raw/github/quantsplaybook/2026-05-06-quantsplaybook-str-deep-dive.md](../../raw/github/quantsplaybook/2026-05-06-quantsplaybook-str-deep-dive.md)（21 KB，含 39 个 ipynb cells + 3 个 .py 源文件）
