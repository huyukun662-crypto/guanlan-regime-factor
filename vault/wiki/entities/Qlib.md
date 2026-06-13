---
tags: [量化框架, Microsoft, 工具, AI]
created: 2026-05-05
updated: 2026-05-05
type: entity
entity_type: tool
sources:
  - wiki/sources/2026-05-05-qpb-industry-pricevolume-etf-rotation.md
---

# Qlib

> 微软开源的 AI 驱动量化投资平台

## 基本信息

- **作者**：Microsoft Research
- **GitHub**：[github.com/microsoft/qlib](https://github.com/microsoft/qlib)
- **核心定位**：完整的端到端量化研究框架（数据 + 因子 + 模型 + 回测）

## 内置经典因子库

- **[[Alpha158]]**：158 个经典量价因子
- **Alpha360**：360 个扩展因子
- **支持**：自定义因子（用 Qlib 表达式或 Python）

## 模型支持

- LightGBM / XGBoost / CatBoost
- LSTM / Transformer / GRU
- HMM / 强化学习（DDPG, PPO 等）

## 工作流（典型）

```
qlib.init(provider_uri="data_dir") → 数据
   ↓
DatasetH（特征 / 标签 dataset）
   ↓
Model.train() / .predict()
   ↓
SignalRecord / SigAnaRecord（IC / RankIC 评估）
   ↓
Backtrader 回测
```

## 与同类框架的对比

| 框架 | 特点 |
|---|---|
| **Qlib（本框架）** | 端到端 + AI 驱动 + 完整流水线 |
| Backtrader | 回测引擎（无数据 / 因子层）|
| vectorbt | 高性能向量化回测 |
| Zipline | Quantopian 的开源版本 |

## 在 [[QuantsPlaybook]] 仓库中的应用

- [[2026-05-05-qpb-industry-pricevolume-etf-rotation]] 用 Qlib 跑 192 因子 + Alpha158 对照
- 仓库自身的 README 把 Qlib 列为核心框架之一

## 数据要求

- 需要将 OHLCV 数据**转成 Qlib bin 格式**（`dump_bin.py`）
- 支持自定义数据源（要求 trade_date 字段对齐）

## 在素材中的出现

- [[2026-05-05-qpb-industry-pricevolume-etf-rotation]]：用 Qlib 框架做 ETF 多因子轮动测试

## 相关页面

- 配套：[[Alpha158]]、[[QuantsPlaybook]]
- 替代方案：Backtrader / vectorbt / Zipline
- 主题：[[机器学习选股]]、[[ETF轮动与交易策略]]
