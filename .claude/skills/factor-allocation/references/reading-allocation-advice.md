# 读懂因子配置建议

`factor_allocation.json` 是「大势定仓位、因子定倾斜」的一句研究建议。按这里的口径读，别把它当成
一个回测出来的组合。

## 两层，顺序不能反
1. **总仓位姿态（先）**：来自大势 verdict —— 走强→**进攻**（equity 高）/ 震荡→**中性**（半仓择优）/
   走弱→**防御**（低权益、现金为主）。这一层决定**多少权益**，是主要决策。
2. **风格倾斜 tilt（后）**：在权益内部该偏哪些风格。这一层是**次要**项，且信号很弱（见下）。

姿态优先于 tilt：先决定多少仓位，再谈配哪些风格。防御期把 tilt 看轻——先降权益。

## tilt 方向怎么定
看 `tilt_basis.ic_mean`（因子轮动月度 IC 的均值，来自 factor-research）：
- **≥ 0 → 动量 tilt**：上月领涨风格倾向延续 → **超配领涨、低配垫底**。
- **< 0 → 反转 tilt**：上月领涨风格倾向回落 → **超配垫底（待反弹）、低配领涨**。
- **≈ 0（|ic_mean|<0.02）→ 中性**：排名对下月无预测力，不主动 tilt，`overweight/underweight` 留空，
  只在 `ranking_top/bottom` 列出领涨/垫底供观察。

## 诚实口径（必须随建议一起讲）
- **因子动量很弱**：历史 IC 均值≈0.04、ICIR≈0.09、胜率≈55%（见 factor-research 的
  `reading-factor-ic.md`）。所以 tilt 只是**弱倾斜**，别据此重仓押注某个风格。
- **这是研究建议、不是组合**：不含权重、未回测、未计成本/滑点/换手。要真正落地组合需另做权重与回测
  （本项目已不提供 FOF skill；ETF-FOF 回测代码仅作证据留在 `fof/`）。
- **仅供量化研究参考，不构成投资建议。**

## 字段速查
`posture`/`equity_hint` 姿态层；`tilt_mode`/`overweight`/`underweight` 倾斜层；`ranking_top`/
`ranking_bottom` 当月领涨/垫底原始排名（透明对照）；`tilt_basis` 给出 IC 依据；`caveats` 是上述诚实
口径；`sources` 透传大势研判的 Brain 引用。
