---
tags: [素材, 微信公众号, 东北金工, Fabozzi, 策略衰减, MRP, 风险管理, 量化方法论]
created: 2026-05-31
updated: 2026-05-31
type: source
priority: S
sources:
  - raw/wechat/2026-05-31-dbjg-fabozzi-strategy-decay-risk.md
images: 2
image_paths: []
---

# 2026-05-31 东北金工：Fabozzi《Measuring Strategy-Decay Risk》论文导读

> 微信公众号 | 东北金工 | 2026-05-31 | **S 档**（方法论级 / 新研究方向 / 直接呼应 V25 IS-OOS 纪律）

## 基本信息

- **公众号作者**：[[东北金工]]
- **解读论文**：Fabozzi 等《**Measuring Strategy-Decay Risk**》
- **论文作者**：[[Frank Fabozzi]]（金融学经典著作《Bond Markets》系列作者，业内顶级专家）
- **链接**：https://mp.weixin.qq.com/s/Mw24xe-1GUQBH8LSj_pZIA
- **类型**：学术论文导读 / 量化研究方法论批判

## 一句话摘要

> 量化的真正**元风险（Meta Risk）**不是收益波动，而是**策略本身失去有效性**（Alpha Decay）。论文提出 **[[MRP最小Regime表现]] = Min(Sharpe across regimes)** 作为策略寿命指标，构建 **[[衰减风险前沿]]**（Sharpe × MRP），实证发现**高 Sharpe 因子反而最脆弱**（Debt Issuance Sharpe 1.14 / MRP -0.05；Investment Sharpe 0.45 / MRP -1.01；Size Sharpe 0.16 / MRP -0.93），把研究焦点从"发现 Alpha"转向"延长 [[Alpha半衰期]] [[策略耐久性]]"。

## 核心观点

### 1. 传统风险模型回答错了问题

| 传统指标 | 回答的问题 |
|---|---|
| 波动率 / 最大回撤 / VaR / ES | "当策略**有效时**亏多少钱" |
| **MRP（论文提出）** | **"当策略失效时**会发生什么" |

### 2. MRP 公式

```
MRP = Min(Sharpe across regimes)
```

步骤：
1. 把历史数据切分为多个市场状态 / Regime：宽松周期 / 加息周期 / 危机周期 / 流动性扩张周期
2. 分别计算每个阶段的 Sharpe Ratio
3. 取其中最差的一个

### 3. 简单举例

| 策略 | Sharpe | MRP | 解读 |
|---|---|---|---|
| A | 1.2 | **-1.0** | 某阶段几乎完全崩溃 |
| B | 0.8 | **0.3** | 任何市场环境都保持正收益 |

**长期配置角度，B 可能更有价值**。

### 4. 1980-2023 经典因子实证（论文 Table）

| 因子 | 历史 Sharpe | MRP |
|---|---|---|
| Debt Issuance | 1.14 | **-0.05** |
| Investment | 0.45 | **-1.01** |
| Size | 0.16 | **-0.93** |

研究因子：Value / Momentum / Quality / Size / Investment / Profitability

**核心发现**：**高 Sharpe 并不意味着高稳定性**——历史表现最好的因子反而最脆弱。

### 5. Decay-Risk Frontier（衰减风险前沿）

构造的新型二维框架：
- **横轴**：Sharpe Ratio（收益）
- **纵轴**：MRP（寿命）

类比 [[Markowitz 均值方差前沿]]，但优化的是 **收益 × 寿命** 而非 **收益 × 风险**。

> 评价体系切换：过去——谁赚得最多 / 未来——**谁活得最久**。

### 6. AI 时代 MRP 更重要

AI 策略的衰减速度可能**远高于传统因子**：
- 传统因子学习的是**基本面**（缓慢变化）
- AI 模型学习的是**信息结构**（快速变化）

> 未来最大风险不是模型误差，而是 **模型寿命**。

### 7. 新研究方向：Strategy Durability

| 时代 | 研究 | 属性 |
|---|---|---|
| 过去 20 年 | 如何**发现** Alpha | 预测问题 |
| 未来 10 年 | 如何**延长** Alpha 寿命 | **生存**问题 |

> 生存问题，往往比预测问题更重要。

## 关键概念

- [[MRP最小Regime表现]] — 最差 Regime Sharpe，量化策略寿命
- [[策略衰减风险]] — Strategy-Decay Risk，元风险概念
- [[Alpha半衰期]] — Alpha Half-Life，策略有效期定量化
- [[衰减风险前沿]] — Decay-Risk Frontier，Sharpe × MRP 二维框架
- [[策略耐久性]] — Strategy Durability，新研究方向
- [[元风险MetaRisk]] — 策略失效本身的风险（非收益波动）
- [[市场Regime切分]] — MRP 的前提步骤
- [[Frank Fabozzi]] — 论文作者
- [[东北金工]] — 公众号

## 与本知识库的关联

### 直接呼应 V25 项目 IS-OOS 工程纪律

本知识库 [[CLAUDE.md]] 中"V25 ETF2.0 v5i 复盘"已经记录的经验**完美印证 MRP 思想**：

> "**IS/OOS 纪律是硬约束** —— IS 段只用于选参，OOS 段严格只读"
> "**禁止用 OOS 的某个具体事件反向调参** —— 即使回撤明显，动机必须是泛化性结构问题"

→ 这相当于把"过拟合"作为头号敌人，是 MRP 思想的**预防版**：不让策略在事后看起来有高 Sharpe 但实际上 MRP 很低。<!-- confidence: INFERRED -->

### 与 [[动量衰竭早期识别]] 主题的层次关系

| 层次 | 框架 | 时点 | 单位 |
|---|---|---|---|
| **元风险层**（new） | [[MRP最小Regime表现]] / [[衰减风险前沿]] | 长期跨 Regime | 整个策略 |
| 行为金融层 | [[FIP效应]] / [[BIAS减仓]] | 月度 | 单标的 |
| 微观结构层 | [[VPIN]] / [[VWPIN]] | 日内 | 单标的 |
| 价格结构层 | [[九转序列]] / [[低延时趋势]] / [[接受规则]] | 中期 | 单标的 |

→ MRP 是**最高层次**的策略级寿命预警，[[动量衰竭早期识别]] 是**单标的事中触发**层；两者**层级不同但同属生存研究**。<!-- confidence: INFERRED -->

### 反例对照

| 历史素材 | 与 MRP 的对应关系 |
|---|---|
| [[2026-05-05-qpb-industry-pricevolume-etf-rotation]]（华西因子 ETF 失效） | 这正是 MRP 视角下"高 IS Sharpe + 低 OOS MRP"的经典案例 |
| [[特异市值因子]]（[[2026-05-05-yhmrshs-residual-mcap]]） | 量化拯救散户的 21 日 std 低频化 = 隐含 regime 稳定性优化 |
| [[Alpha158]] 在 ETF 上的负面发现 | MRP 视角下的失效 |

### 协同的方法论素材

- [[2026-05-08-earletf-fip-bias-trim]]：FIP 效应 → 单标的层"涨法连续性 → 动量寿命"
- [[2026-05-07-jq-etf-cross-section-thinking]]：截面思维 4 层框架 → 多层风控降低单层失效冲击
- 本文 → 整个**策略层**的寿命管理

## V25 项目集成 Hook

### 优先级 S（直接可测）

1. **实现 MRP 评估器**：
   ```python
   def compute_mrp(returns, regime_labels):
       """对每个 regime 算 Sharpe → 取最小"""
       df = pd.DataFrame({'r': returns, 'regime': regime_labels})
       sharpe_per_regime = df.groupby('regime')['r'].apply(
           lambda x: x.mean() / x.std() * np.sqrt(252)
       )
       return sharpe_per_regime.min()
   ```

2. **建立 Regime 标签器**：
   - 宏观维度：A 股牛 / 熊 / 震荡 / 单边下跌（按沪深 300 滚动收益分位）
   - 资金面：利率上行 / 下行（按 R007 趋势）
   - 波动率：高 vol / 低 vol（按 VIX 或滚动波动率）

3. **在 grid_search_*.py 输出加 MRP 列**：与现有 Sharpe / DD / Ann 并列，**MRP 极差的参数即使 Sharpe 高也淘汰**

### 优先级 A（升级）

4. **Decay-Risk Frontier 帕累托优化**：现有 V25 v5i 已用"严格非劣解"思想（Sharpe / DD / Ann 多目标），加入 MRP 维度后变成 **4 目标 Pareto**
5. **滚动 MRP 监控**：每月重算最近 5 年的 MRP，若大幅恶化 → 触发策略冻结预警

### 优先级 B（前沿）

6. **AI 策略的 MRP 评估**：本知识库已有 [[Q-A3C²]]（量子强化学习）等 AI 策略，论文明确指出 AI 策略衰减更快 → 优先在 AI 类策略上跑 MRP

## 待解决的问题

1. A 股 Regime 切分的最优维度（宏观 / 资金面 / 风格 / 波动率）应该用几维？
2. MRP 的样本量门槛：每个 Regime 至少需要多少观测才能算可靠 Sharpe？（论文未明示）
3. AMBIGUOUS：论文是否给出了 MRP 的统计显著性检验？仅看文中导读未明
4. MRP 的"看跌选项"性质：低 MRP 是否可作为 short-vol 信号？
5. MRP 与 IS-OOS 纪律的协同：是否可直接把 OOS Sharpe 作为 MRP 的代理？

## 原文精彩摘录

> 量化投资真正的元风险（Meta Risk）并非收益波动，而是策略本身失去有效性。

> 高 Sharpe 并不意味着高稳定性。恰恰相反。很多历史表现最好的因子：反而最脆弱。

> 过去：谁赚得最多。未来：谁活得最久。

> 未来量化行业将从研究 Alpha 转向研究 Alpha Half-Life。谁能预测策略衰减，谁就拥有下一代 Alpha。

> 投资行业最危险的时刻，并不是策略亏损的时候，而是策略开始失效，而投资人尚未察觉的时候。

> 波动率衡量的是风险。回撤衡量的是损失。而 MRP 衡量的则是：一个策略最终还能活多久。

## 信息密度评分

- 原创性：★★★★★（论文级新指标 + 新研究方向）
- 可操作性：★★★★☆（公式简单可立即实现，但 Regime 切分主观）
- 理论深度：★★★★★（Fabozzi 顶级学者 / Markowitz 框架升级）
- A 股适配：★★★★☆（思想完全通用，Regime 切分需本土化）

**综合：S 档** — 罕见的"元风险层"方法论级素材，直接呼应 V25 IS-OOS 工程纪律，可作为整个知识库 [[动量衰竭早期识别]] 主题的**最高层次扩展**。
