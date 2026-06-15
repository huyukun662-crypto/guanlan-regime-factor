---
name: factor-research
description: >
  因子研究 —— 构建并解读 12 个真实 A 股风格指数代理因子（动量/反转/小市值/微盘/大盘/价值/成长/科技成长/
  红利/低波/质量/市场）的因子看板：累积收益曲线、近期轮动排行(1M/3M/YTD)、因子轮动月度 IC + 12 月滚动
  ICIR、各因子滚动 Sharpe、全样本统计(年化/夏普/回撤/波动)、相关性矩阵。Emits outputs/factors.json.
  触发语：「看因子」「因子轮动 IC」「哪个风格在风口」「因子表现怎么样」"factor board / rotation IC /
  which style is leading". 这是风格指数 long-short 序列，**不是**个股选股 IC，也不做组合配权。
allowed-tools: Bash, Read
---

# factor-research（因子研究）

把 12 个真实风格/Smart-beta 指数的 long-short 收益，做成可解读的因子看板：谁在风口（轮动排行）、风格
能不能追涨（轮动 IC）、各因子稳不稳（滚动 Sharpe）、长期值不值（全样本统计）。

## When to use
- 「最近哪个风格因子强？」「风格轮动追涨有用吗？」/ "which factor is leading? is style momentum real?"
- 刷新 `factors.html` 因子看板前重算 `factors.json`。

## When NOT to use
- 不是经典**个股横截面选股 IC**（那需要全市场个股因子暴露，本项目用风格指数序列代理）。
- 不做组合配权/回测（FOF 组合已从仪表板移除，代码留在 `fof/` 作证据）。

## Run
```bash
python .claude/skills/factor-research/scripts/compute_factors.py --asof 2026-06-05
```
`fof.factors.build_factor_board(cfg)`（`result=None` → 纯因子、不含 FOF 暴露）的薄包装，写
`outputs/factors.json`，并打印一行摘要 `{n_factors, top_factor, ic_mean, icir, hit_rate}`。

## Output schema (`outputs/factors.json`)
`{n_factors, ranking{asof, factors:[{key,display,category,r_1m,r_3m,r_ytd,rank}]},
cumulative{dates, series, labels}, tearsheet{factors:[{display,category,ann,sharpe,maxdd,vol}]},
correlation{matrix, labels},
rotation_ic{signal, dates, ic, rolling_icir, icir, ic_mean, hit_rate},
rolling_sharpe{dates, series, labels}}`。

## 输出格式（研报级回复）
读完 `outputs/factors.json` 后产一份「因子研究」小节（数字全来自 JSON 字段、标口径）：
1. **轮动结论**：近 1 月领涨前三 / 垫底后三（`ranking.factors[].r_1m`）→ 哪个风格在风口、哪类在退潮。
2. **信号有效性**：`rotation_ic` 的 IC 均值 / ICIR / 胜率 + 统计口径 → 明确「IC≈0.04、胜率仅略高于 50% = 弱信号、非强 alpha」。
3. **全样本统计（表）**：`tearsheet.factors` 取代表性几只 —

   | 因子 | 年化(ann) | 夏普(sharpe) | 最大回撤(maxdd) | 波动(vol) |
   |---|---|---|---|---|
4. **稳定性**：`rolling_sharpe` / `rotation_ic.rolling_icir` 近端方向（在变强还是变弱）。
5. **分散性**：`correlation.matrix` 点出高相关簇（提示「同涨同跌、分散有限」）。
6. **诚实口径**：风格指数 long-short 代理、**非个股横截面 IC**；不配权不回测；完整读法见 `references/reading-factor-ic.md`；仅供研究参考。

> 质量基线：区分事实/推断/建议；不堆形容词、不写 AI 腔；缺字段就说缺失，不编。

## 读法与诚实口径
**因子轮动月度 IC 的完整读法、当前诚实读数、以及两个口径提醒，见
`references/reading-factor-ic.md`**（与 `factors.html` 网页使用说明同源）。一句话先记住：当前
**IC≈0.04 / ICIR≈0.09 / 胜率≈55% → A 股因子动量很弱，简单"追风口"赚不到稳定钱**——这是真实结果，
汇报时不要美化成 alpha。

## Look-ahead safety
全部委托 `fof.factors`：IC 用"当月排名 → 次月收益"，月度对齐天然防前视；滚动 Sharpe/累积均为 trailing。
脚本不引入未来数据。
