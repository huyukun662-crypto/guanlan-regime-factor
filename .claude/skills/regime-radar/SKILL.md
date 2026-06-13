---
name: regime-radar
description: >
  Compute 12 A-share market indicators (RSRS, MA20 bias, breadth, vol-Z, plus Tushare macro:
  10Y-2Y curve, gold/copper, ERP, plus sentiment: 融资余额Z, 全市场成交Z, Shibor-1W liquidity,
  IF 期货净多比, IO 期权 PCR)
  and fold them into a 0-100 composite downside-risk score + a GuanLan-style 顶部分/底部分
  (top/bottom) dual scoring per indicator + a daily risk-score trend series. Emits
  outputs/regime.json for the dashboard gauge, 顶/底 cards, 走势图, and 详解.
  Use when the user asks to "read the current regime", "build the risk gauge", "更新风险评分".
allowed-tools: Bash, Read
---

# regime-radar

Turns raw market + macro data into the dashboard's **综合风险评分** gauge and indicator cards.

## When to use
- "What regime are we in?" / "现在是什么市场状态？"
- Building or refreshing the risk gauge before a FOF allocation run.

## When NOT to use
- Do **not** run the backtest here — the FOF backtest lives in `fof/` as a retained evidence chain
  (no longer a skill). This skill only *reads* the current regime; it never trades. For the 大势
  研判 verdict use `regime-verdict`; for factors use `factor-research`.

## Indicators (12; see `DISPLAY_SPEC` in `fof/regime.py` for 公式/评分规则)
| key | name | source data |
|---|---|---|
| rsrs | RSRS 右偏标准分 | benchmark high/low OLS slope |
| ma20_bias | 沪深300 MA20 乖离 | benchmark close vs MA20 |
| breadth | 市场宽度 >MA60 占比 | equity ETF panel |
| vol_z | 波动率 Z-Score | benchmark 20D realized vol |
| yield_curve | 10Y-2Y 国债利差 | Tushare `yc_cb` |
| gold_copper | 金铜比 Z-Score | Tushare `fut_daily` AU/CU |
| erp | 股债性价比 ERP | Tushare `index_dailybasic` PE − 10Y |
| margin_z | 融资余额20日Z-Score | Tushare `margin` (rzye) |
| turnover_z | 全市场成交Z-Score | Tushare `daily_info` (SH+SZ amount) |
| shibor | 货币流动性(Shibor 1W) | Tushare `shibor` 1w |
| fut_ls | IF期货净多比 | Tushare `fut_holding` (主力 top会员 多/空) — bounded recent window, cached |
| opt_pcr | IO期权PCR | Tushare `opt_daily` (沪深300指数期权 认沽/认购量) — bounded, cached |

Two scoring layers: (a) a **downside-risk subscore** (drives the gauge + FOF regime gate, over the
original 7); (b) a **顶部分/底部分** dual score per indicator (顶=overheat, 底=oversold) → cards +
the daily 风险走势 series. Both are weight-renormalized over the **available** indicators
(missing data is dropped, never NaN-poisons the output).

## Run
```bash
python .claude/skills/regime-radar/scripts/compute_regime.py --asof 2026-06-05
```
Prints a one-line JSON summary and writes `outputs/regime.json`. The CLI is a thin wrapper over
`fof.regime.build_regime_json(cfg)`.

## Output schema (`outputs/regime.json`)
`{asof, composite_score, band, band_thresholds, regime_label, equity_exposure,
advice_baseline, indicators:[{key,name,value,subscore,weight,direction,contribution,
available,explain,source}]}`. Each `indicators[]` entry renders one GuanLan-style card.

## Look-ahead safety
Every indicator uses only trailing data (`series.loc[:asof]`, rolling z-scores). The RSRS slope
uses a trailing OLS window; the engine never sees future bars. Verified by
`tests/test_regime.py::test_rsrs_lookahead_safe`.
