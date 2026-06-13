---
name: factor-allocation
description: >
  因子配置建议（集成大势研判 × 因子看板）—— 读 master.json（大势 verdict 走强/震荡/走弱）+
  factors.json（因子轮动排行 + IC），映射成一句可操作研究建议：**总仓位姿态**（进攻/中性/防御）+
  当前该**超配 / 低配哪些风格**（方向由因子 IC 符号定：动量追涨 or 反转高低切）。触发语：「现在该
  超配/低配哪些风格」「按大势和因子给配置建议」「该进攻还是防御、配哪些风格」「factor allocation /
  tilt advice / 因子配置」。**NOT**：不构建组合、不回测、不出权重、非个股选股、不动仪表板。
allowed-tools: Bash, Read
---

# factor-allocation（因子配置建议）

把两大支柱拼成一句话建议：**大势定仓位姿态，因子定风格倾斜**。纯读取 + 映射 —— 不建组合、不回测、
不出权重，只回答「现在该进攻还是防御 + 该偏哪些风格」。

## When to use
- 「现在该超配/低配哪些风格？该进攻还是防御？」/ "given the trend and factors, what should I tilt toward?"
- 想要一句研究建议（姿态 + 风格倾斜），**不是**要一个回测出来的组合。

## When NOT to use
- 不构建组合 / 不回测 / 不出权重（用户已明确不要 FOF）。
- 非个股选股；不动仪表板 web/、server/。

## 上游依赖（集成点）
读 `outputs/master.json`（由 **regime-verdict** 产）+ `outputs/factors.json`（由 **factor-research** 产）。
两者缺失时脚本会提示先跑这两个 skill，或 `python scripts/run_pipeline.py` 一次性生成。

## 映射逻辑（`fof/advice.py:factor_allocation_advice`）
- **姿态**：走强→进攻 / 震荡→中性 / 走弱→防御（附 equity_hint 高/中/低）。
- **tilt 方向**：看 `factors.rotation_ic.ic_mean` —— ≥0 动量(追涨上月领涨)、<0 反转(高低切)、≈0 中性。
- **超配/低配**：按因子近 1 月收益排序；动量 tilt → 超配领涨/低配垫底，反转 tilt → 反向，中性 → 不主动 tilt。

## Run
```bash
python .claude/skills/factor-allocation/scripts/build_factor_allocation.py
```
写 `outputs/factor_allocation.json`，打印一行 `{asof, verdict, posture, equity_hint, tilt_mode,
overweight[], underweight[]}`。薄包装 `fof.advice.factor_allocation_advice`。

## Output schema (`outputs/factor_allocation.json`)
`{asof, verdict, master_score, confidence, posture, equity_hint, tilt_mode,
tilt_basis{ic_mean,icir,hit_rate}, overweight[], underweight[], ranking_top[], ranking_bottom[],
caveats[], sources[]}`。

## 读法与诚实口径
**先读 `references/reading-allocation-advice.md`** —— 姿态优先于 tilt；因子动量很弱（IC≈0.04）→ tilt 只是
弱倾斜别重押；防御期 tilt 意义小；这是研究建议非组合（无权重/未回测）。caveats 已硬编码进输出，汇报时
照搬、不美化。
