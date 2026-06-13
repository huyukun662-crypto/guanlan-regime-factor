# Regime indicators — definitions, risk mapping, and Brain grounding

Each indicator is computed look-ahead-safe in `fof/regime.py`, then mapped to a 0-100
**downside-risk subscore** (higher = be defensive). The composite is the weight-renormalized
average over available indicators.

| key | weight | raw definition | risk subscore mapping | direction | Brain source |
|---|---|---|---|---|---|
| `rsrs` | 0.20 | OLS slope of (low → high) over 18d, standardized over 250d | `clamp(50 − 40·z)` | lower z = risk | `wiki/sources/2026-05-05-openalphas-rsrs-market-thermometer.md` |
| `ma20_bias` | 0.15 | `close/MA20 − 1` on 沪深300 | `clamp(50 − 1000·bias)` | below MA = risk | `wiki/sources/2026-05-05-lcm-bias-indicator-personal-notes.md` |
| `breadth` | 0.15 | fraction of equity ETFs with `close ≥ MA60` | `clamp(100·(1−breadth))` | narrow = risk | `wiki/sources/2026-05-07-jq-etf-cross-section-thinking.md` |
| `vol_z` | 0.15 | z-score of 20d realized vol (250d window) | `clamp(50 + 25·z)` | high vol = risk | `wiki/sources/2026-05-05-openalphas-rsrs-market-thermometer.md` |
| `yield_curve` | 0.12 | 10Y−2Y China treasury spread (`yc_cb`) | `clamp(60 − 50·spread)` | inversion = risk | `wiki/sources/2026-04-02-huatai-energy-stagflation-3stage.md` |
| `gold_copper` | 0.10 | gold/copper futures ratio (`fut_daily` AU/CU), z-scored | `clamp(50 + 30·z)` | high = growth fear | `wiki/sources/2026-04-02-huatai-energy-stagflation-3stage.md` |
| `erp` | 0.13 | 上证50 earnings yield (1/PE_ttm) − 10Y yield | `clamp(80 − 12·erp)` | high ERP = cheap = safe | `wiki/sources/2026-05-30-huatai-macro-energy-shock-buffer-path.md` |

## Composite + bands
`composite = Σ wᵢ·subscoreᵢ / Σ wᵢ` over available indicators (NaN dropped, weights renormalized).
Bands: 低 <20, 中低 <40, 中高 <60, 高 <80, 极端 ≥80.

## Regime label (`label_series`)
- `trend`  — RSRS z > 0.7 **and** close ≥ MA200
- `bear`   — RSRS z < −0.5 **or** (below MA200 **and** composite ≥ 60)
- `ranging`— otherwise

The label drives the equity-exposure gate `{trend:1.0, ranging:0.8, bear:0.0}` consumed by the
retained FOF backtest engine in `fof/` (evidence-only; no longer a dashboard skill).

## Why these indicators
The macro trio (金铜比 / 期限利差 / ERP) operationalizes the Huatai stagflation-3-stage regime
template; RSRS + MA20 + breadth + vol are the technical thermometer from the OpenAlphas RSRS
note and the jq cross-section framework. The mix keeps the gauge robust when any single macro
endpoint is unavailable (it is simply dropped and the rest renormalized).
