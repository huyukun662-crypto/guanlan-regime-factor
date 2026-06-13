---
tags: [强化学习, Actor-Critic, 异步训练, 经典算法]
created: 2026-05-06
updated: 2026-05-06
type: entity
entity_type: algorithm
sources:
  - wiki/sources/2026-05-06-datou-q-a3c2-paper-reading.md
---

# A3C 强化学习

> Asynchronous Advantage Actor-Critic — DeepMind 2016 提出的经典异步并行 RL 算法

## 一句话定义

A3C 用**多个并行 worker** 与环境交互、各自更新本地参数 + 异步同步到全局参数 → **加速训练 + 解相关样本**。Actor 学策略 π；Critic 估值函数 V；用 **Advantage A = Q - V** 降低梯度方差。

## 历史溯源

- 论文：Mnih et al. (2016), *Asynchronous Methods for Deep Reinforcement Learning* (ICML 2016)
- 来自 Google DeepMind
- 是 Atari / 控制任务的经典 baseline

## 核心架构

```
            [全局参数 θ]
              ↑    ↓
   ┌─────────┼─────────┐
   ↓         ↓         ↓
[worker 1] [worker 2] ... [worker N]
   ↓         ↓
[环境 1]  [环境 2]  ...  [环境 N]
```

每个 worker：
1. 用本地参数与环境交互几步
2. 计算梯度
3. 异步推送到全局参数
4. 拉取最新全局参数
5. 重复

## 关键算法选择

| 选择 | 理由 |
|---|---|
| **异步**（vs 同步 A2C） | 解相关样本 + 加速 |
| **Advantage**（vs 直接用 Q）| 降梯度方差 |
| **Actor-Critic**（vs DQN） | 适合连续动作 / 大动作空间 |
| **n-step return**（vs 单步） | 偏差 - 方差权衡 |

## 在量化金融的应用

### 优势
- 可训练**端到端策略**（输入市场状态 → 输出动作）
- 不需要标签（与监督学习的 [[LightGBM]] 不同）
- 自然适配**序贯决策**（每月再平衡 / 每日调仓）

### 挑战
- 高维特征空间易过拟合（[[Q-A3C²]] 的核心痛点）
- 奖励工程困难（金融市场重尾 + 非平稳）
- 训练不稳定 + 样本效率低
- **回测过拟合风险**：所有 RL 在金融上都面临这问题

## 在素材中的出现

- [[2026-05-06-datou-q-a3c2-paper-reading]]：作为 [[Q-A3C²]] 的基础架构（嵌入 VQC 瓶颈 + 动态聚类）

## 与同类 RL 算法的对比

| 算法 | 类型 | 适用 |
|---|---|---|
| DQN | Value-based | 离散动作 |
| **A3C（本算法）** | Actor-Critic + 异步 | 连续/离散，并行 |
| PPO | Policy gradient + 截断 | 现代主流（更稳定）|
| SAC | 最大熵 RL | 连续动作 |
| DDPG | 确定性策略梯度 | 连续动作 |

⇒ A3C 在**异步 + 简单**之间平衡。但现在工业界更多用 PPO（更稳定）。

## V25 项目集成

- 当前 V25 不用 RL（用规则 + 因子）
- A3C 是较老的 RL 算法（2016），如要集成 RL 应优先考虑 PPO
- **本知识库的 RL 入口**：本实体页（与 [[Q-A3C²]] 一起）

## 相关页面

- 衍生：[[Q-A3C²]]
- 主题：[[机器学习选股]]、[[ETF轮动与交易策略]]
- 来源：[[2026-05-06-datou-q-a3c2-paper-reading]]
