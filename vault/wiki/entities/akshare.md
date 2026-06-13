---
tags: [工具, 数据源, Python]
created: 2026-05-05
updated: 2026-05-05
sources:
  - wiki/sources/2026-04-23-openalphas-bottom-style-timing.md
  - wiki/sources/2026-05-05-openalphas-value-quant-revolution.md
  - wiki/sources/2026-05-05-openalphas-lightgbm-bayesian.md
---

# akshare

> 开源 A 股 / 全球金融数据 Python 库，OpenAlphas 笔记中用作行情和估值数据源。

## 用法（来自笔记）

```python
import akshare as ak

# 指数日度行情
df = ak.index_zh_a_hist(symbol="399370", period="daily",
                          start_date="20050101", end_date="20221231")

# 上证综指 PETTM 估值
pe_df = ak.index_value_analysis_em(symbol="000001")
```

## 主要 endpoint（5 篇笔记中用到的）

| 函数 | 用途 | 出现于 |
|---|---|---|
| `index_zh_a_hist` | A 股指数日度 OHLCV 历史数据 | 底部择时 |
| `index_value_analysis_em` | 东财指数估值数据（PETTM / PB / 股息率等） | 底部择时 |
| `stock_zh_a_hist` | A 股个股日度后复权行情 | LightGBM |
| `stock_a_lg_indicator` | A 股基本面指标（PE / PB / ROE_TTM） | LightGBM |
| 中信三级行业分类（自封装） | 行业归属 | 价值量化 |

## 与 efinance 的对比（V25 项目用 efinance）

V25 ETF 项目中使用 `efinance`（参见 `C:/Users/Hu/Desktop/JQ/opt/data_loader.py`），不是 akshare。

| 维度 | akshare | efinance |
|---|---|---|
| ETF 历史 | ✅ `fund_etf_hist_em` 偶被限流 | ✅ `stock.get_quote_history` 更稳定 |
| 国证指数 | ✅ `index_zh_a_hist` 直接支持 | 需 `MarketType.A_stock_index` 显式指定 |
| 估值分位 | ✅ `index_value_analysis_em` | 需自行计算 |
| 复现 OpenAlphas 代码 | ✅ 直接运行 | 需要少量改写 |

## V25 项目集成

如果要复现 OpenAlphas 策略，建议：
1. 在 `opt/openalphas_replicate.py` 中保留原 akshare 调用（少量改动），跑出真实 win_rate
2. 验证后再用 efinance 数据源重写一遍，保证与 V25 复现器使用相同数据基础
3. 把 SRI 因子作为新 regime 维度加进 V25 的 grid_search

## 相关页面

- [[国证成长指数]]
- [[国证价值指数]]
- [[2026-04-23-openalphas-bottom-style-timing]]
