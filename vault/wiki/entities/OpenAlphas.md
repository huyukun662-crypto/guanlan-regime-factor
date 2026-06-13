---
tags: [人物, 量化博主, 自研机构]
created: 2026-05-05
updated: 2026-05-05
sources:
  - wiki/sources/2026-04-23-openalphas-bottom-style-timing.md
  - wiki/sources/2026-05-05-openalphas-value-quant-revolution.md
  - wiki/sources/2026-05-05-openalphas-alphazero-factor-mining.md
  - wiki/sources/2026-05-05-openalphas-rsrs-market-thermometer.md
  - wiki/sources/2026-05-05-openalphas-lightgbm-bayesian.md
---

# OpenAlphas

> A 股个人量化博主，公开分享自有量化公司的策略研究，定位"深入浅出的量化技术好文"。

## 基本信息

- **平台**：小红书
- **userId**：681df7d7000000000a03d845
- **博主累计互动**：2987 次赞与收藏（用户分享时口径，非单篇）
- **背景**：自述"过去 10 年深耕投资 & 量化领域"，"自己的量化公司也已经成立了 5 年之久"
- **版权声明**：平台发布的内容均出自本人公司原创，未经同意禁止搬运、洗稿及商用

## 内容定位

- 个人量化 / AI 量化方向
- 偏向"原理 + 公式 + 完整 Python 代码"风格的全流程策略分享
- 标签：#个人量化 #ai量化 #量化 #量化交易 #个人投资者 #大模型

## 已消化的策略（共 5 篇）

| 日期 | 标题 | 主题 | 赞 | 优先级 |
|---|---|---|---|---|
| 2026-04-23 | [[2026-04-23-openalphas-bottom-style-timing]] | 底部风格择时 / SRI 因子 | — | **S** |
| 2026-05-05 | [[2026-05-05-openalphas-value-quant-revolution]] | 价值投资量化（行业壁垒 + 标的筛选） | 27 | A |
| 2026-05-05 | [[2026-05-05-openalphas-alphazero-factor-mining]] | AlphaZero 自动因子挖掘 | 60 | A |
| 2026-05-05 | [[2026-05-05-openalphas-rsrs-market-thermometer]] | RSRS 三层标准化 + MA20 / 量价过滤 | 23 | A |
| 2026-05-05 | [[2026-05-05-openalphas-lightgbm-bayesian]] | LightGBM + Optuna 贝叶斯超参 | 77 | **S** |

## 风格画像（5 篇消化后）

- **覆盖范围**：
  - 选股：基本面（价值量化）、ML 端到端（LightGBM）、自动因子（AlphaZero）
  - 择时：大级别（底部双因子）、中级别（RSRS）
- **写作风格**：原理 → 公式 → 完整 Python 代码 → 数字结论
- **代码可执行度**：原型级别（演示主流程，未含交易成本/涨跌停/滑点）

## 评估观察

- ✅ 公开完整可执行 Python 代码（[[akshare]] 数据源），可复现
- ✅ 公式 / 阈值 / 信号触发逻辑明确
- ✅ 工程纪律完备（[[时序划分]]、[[3σ去极值]]、[[Z-score标准化]]、[[贝叶斯超参优化]]）
- ⚠ 标题数字常为最优化版本（如"胜率 90%"、"年化 40%+"），正文 / 代码输出未必给出实际数值
- ⚠ 多篇笔记的回测起止日期、股票池范围未明确披露
- ⚠ 关键案例样本量小（如底部择时只有 6 个事件，置信区间宽）
- ⚠ 部分笔记代码使用模拟数据（AlphaZero 的 `generate_simulated_data`），真实 A 股需自行复跑

## 后续追踪计划

候选索引尚有 26 篇待消化（[[../../raw/xiaohongshu/openalphas-profile-index.md]]）：
- S 档优先：#10 因子压缩、#13 风险平价 ETF、#23 量化选股
- A 档候选：技术指标系列、量化择时变体
- 用户随手贴短链 → 单篇 ingest（已确认手动方式）

## 相关页面

- [[2026-04-23-openalphas-bottom-style-timing]]
- [[2026-05-05-openalphas-value-quant-revolution]]
- [[2026-05-05-openalphas-alphazero-factor-mining]]
- [[2026-05-05-openalphas-rsrs-market-thermometer]]
- [[2026-05-05-openalphas-lightgbm-bayesian]]
- 主题：[[底部择时与风格轮动]]、[[价值投资量化]]、[[机器学习选股]]、[[技术指标择时]]、[[Alpha挖掘与因子正交性]]
