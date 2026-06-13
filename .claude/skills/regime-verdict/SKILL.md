---
name: regime-verdict
description: >
  大势研判 —— 把 HMM 4 态隐马尔可夫后验 × Kaufman 效率比(ER) × 基本面估值三轴融合成一个综合大势
  结论：走强 / 震荡 / 走弱（master_score 0-100），并给 confidence、4×4 月度转移矩阵、各状态收益/
  波动统计、walk-forward 样本外状态色带。Emits outputs/master.json. 触发语：「现在是走强还是走弱」
  「大势研判」「跑一遍 HMM 大势」「该进攻还是防御」"what's the market trend verdict / judge the regime".
  这**不是** 0-100 风险仪表盘（那是 regime-radar），不回测、不交易。
allowed-tools: Bash, Read
---

# regime-verdict（大势研判）

把市场状态识别成一个可解读的大势结论。HMM 给"现在处于哪种 regime"的概率姿态，ER 确认"是单边
趋势还是来回震荡"，基本面给估值底色，三者按 **HMM 0.5 / ER 0.2 / 基本面 0.3** 融合成 master_score
→ 走强(≥60) / 震荡(40–60) / 走弱(≤40)。

## When to use
- 「现在市场什么状态？该进攻还是防御？」/ "is the market trending up or down?"
- 刷新 index.html 顶部「大势研判」栏前重算 `master.json`。

## When NOT to use
- 不出 0-100 综合风险分 + 顶/底评分 —— 那是 **`regime-radar`**（`regime.json`）。
- 不做回测、不配权、不交易。本 skill 只 *研判*。

## Run
```bash
python .claude/skills/regime-verdict/scripts/compute_master.py --asof 2026-06-05
```
先算 `regime.build_regime_json(cfg)`（提供基本面轴），再 `master.build_master_json(cfg, reg)`，
两者都落盘（`outputs/master.json` + `outputs/regime.json`），并打印一行摘要
`{asof, verdict, master_score, confidence, hmm_state, er, unstable}`。脚本是
`fof.master.build_master_json` 的薄包装。

## Output schema (`outputs/master.json`)
顶层键：`{asof, verdict, master_score, confidence, er_capped, unstable,
hmm{state_name, posterior, states_order}, er, fundamental, axes,
transition{labels, matrix, matrix_daily, horizon}, state_stats, segments, history, advice, sources}`。
`transition.matrix` 是**月度**矩阵（= 日频 `matrix_daily` 的 `T^21`）；`segments` 是样本外状态色带。

## 读法与诚实口径
读 verdict、三轴、转移矩阵、state_stats、ER cap / unstable cap、sticky 规则、nowcast vs ffill
对齐、warmup→NaN 的完整细节见 **`references/reading-the-verdict.md`**（汇报前先读，避免把日频对角
误读成月度、或把样本外色带说成全样本平滑）。

## Look-ahead safety
全部委托 `fof.master`：HMM 按月 walk-forward 重拟合、只用 `series.loc[:asof]`；脚本本身不引入未来
数据。历史状态色带为**样本外**判定，非事后平滑。ER 在涨跌停日会虚高（成交位移失真），需在汇报中标注。
