# Curated source map — bundled vault/ (most relevant to regime-switch FOF)

Fast, deterministic retrieval targets. Paths are under `vault/wiki/sources/` unless noted.

## Regime / macro gating
- `2026-04-02-huatai-energy-stagflation-3stage.md` — **(B)** stagflation 3-stage regime template;
  金铜比 z-score, 10Y-2Y curve inversion, inflation breakeven. → the regime gate's macro logic.
- `2026-05-30-huatai-macro-energy-shock-buffer-path.md` — oil supply-shock physics, OVX, ERP framing.

## ETF cross-section / portfolio construction
- `2026-05-07-jq-etf-cross-section-thinking.md` — **(S)** 4-layer framework (候选池→横向打分→组合构建
  →择时风控) + low-correlation "免费午餐". → sleeve pool + risk-parity rationale.
- `2026-05-05-qpb-industry-pricevolume-etf-rotation.md` — NH-NL breadth, industry rotation case.

## Timing / risk thermometer
- `2026-05-05-openalphas-rsrs-market-thermometer.md` — **(A)** RSRS OLS slope + z-score; MA20 +
  volume filters cut drawdown 50%→20%. → `rsrs`, `vol_z`, `ma20_bias` indicators.
- `2026-04-23-openalphas-bottom-style-timing.md` — **(S)** MDD≥20% & PE≤10% bottom dual-factor +
  SRI growth/value style switch. → `style_rotation` sleeve.
- `2026-05-06-jq-sar-indicator-explainer.md` — **(B)** Parabolic SAR (AF 0.02→0.2): 趋势跟踪 +
  动态止损。 → `sar_trend` sleeve.
- `2026-05-26-choppiness-index.md` — Choppiness Index regime classifier. **Evaluated & rejected**:
  the note's own ETF6.4 validation shows no OOS增量 / IS overfit on the ETF pool.
- `2026-05-05-lcm-bias-indicator-personal-notes.md` — **(A)** log BIAS trim, −5% pierce → reduce. → `ma20_bias`.

## Topic hubs (`wiki/topics/`)
- `ETF轮动与交易策略.md` · `宏观regime与能源冲击择时.md` · `底部择时与风格轮动.md` ·
  `技术指标择时.md` · `量化多因子策略.md` · `Alpha挖掘与因子正交性.md`

## Entry point
- `vault/index.md` — vault index with the source-digestion progress table.

## Mapping topics → files (used to answer common queries)
| query | primary citations |
|---|---|
| risk parity / 风险平价 | jq-etf-cross-section-thinking (weight layer) |
| regime gate / 择时 | huatai-stagflation-3stage, huatai-macro-energy-shock |
| RSRS / 波动率 | openalphas-rsrs-market-thermometer |
| max drawdown / 回撤 | lcm-bias-indicator, openalphas-rsrs-market-thermometer |
| low correlation / 分散 | jq-etf-cross-section-thinking |
| style rotation / 风格 | openalphas-bottom-style-timing |
