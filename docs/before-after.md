# 前后效果对比 — agent / skills 对策略研究的实际帮助

> 本文回答作业要求的「前后效果对比」：同一个策略研究问题，**纯手工**做法 vs **观澜 agent + 5 个
> skill** 做法，差在哪、帮多少。文中每个数字都来自**实测**（命令见文末「如何复现」），未测量的不写。

## 0. 诚实框定（先说清楚比什么）

本项目交付的是**研判与配置建议（研究读数）**，**不构建组合、不回测、不出权重**。所以这份对比
**不用**夏普 / 年化 / 回撤这类 **PnL 指标**——那属于早期已移除的 FOF 回测模块，拿来当 agent 的功劳并
不诚实。真正能诚实量化的是**研究工作流本身**：在**耗时、可溯源、防前视、口径一致、可复现、可验证、
可视化、跨工具**八个维度上，agent+skills 把「手工研究」改善了多少。

策略研究方向一句话：**研报检索 → 风险 regime → 大势研判（HMM 4 态 × Kaufman 效率比 × 基本面）→
因子研究**，全程真实 A 股 ETF/指数数据，产出**带溯源**的研判简报。

**交付物**：1 个 agent（`guanlan-analyst`）+ 5 个 skill（`regime-radar` / `regime-verdict` /
`factor-research` / `factor-allocation` / `quant-research-retriever`）。

---

## 1. 对比方法

固定一个真实研究问题：

> **「今天 A 股该进攻还是防御？该超配 / 低配哪些风格？依据是什么？」**

- **方案 A（前 · 纯手工 baseline）**：翻几十篇研报、手写 notebook 拉数据算 RSRS/ERP/HMM/因子、三个分析
  各写各的、asof 容易对不齐、人工汇总成一段话——慢、无引用链、难复现、易引入前视偏差。
- **方案 B（后 · agent + 5 skill）**：一句「跑一遍大势研判，该进攻还是防御」触发 →
  `quant-research-retriever` 检索取证 → 一行 `run_pipeline.py` 在**同一 walk-forward** 下产 3 份 JSON →
  按各 skill 读法解读 → 带溯源研判简报。**或**完全离线：`python scripts/guanlan_brief.py`（零 LLM）。

---

## 2. 前后对比表（八维 · 实测）

| 维度 | 手工（前） | agent + skills（后） | 实测依据 |
|---|---|---|---|
| **端到端耗时** | 半天到一天（翻报告 + 写 notebook + 调口径） | 离线简报 **0.17–1.0 秒**；全量重算一次（含 19 指数 tail + HMM walk-forward）约 15–30 秒 | `guanlan_brief.py` 实测 run1 1.00s / run2 0.17s |
| **研报可溯源** | 0 引用链，凭记忆 | 每个机制 **≥2 条** `vault/...` 路径引用；语料 **34 篇**金工研报（wiki 共 236 篇） | `query_vault "HMM regime" --top 5` 返回 **5 条**带路径+优先级+命中数 |
| **防前视** | 人工算指标极易用到未来数据 | `series.loc[:asof]` + 回测 `nav.pct_change().shift(-1)` **写死在 `fof/`**；HMM 每月只用 `[:m]` 重拟合；单测 `test_rsrs_lookahead_safe` 断言追加未来 bar 不改变 asof 结论 | `tests/test_regime.py` |
| **口径一致** | regime / 大势 / 因子各跑各，asof 漂移（曾出现 regime=06-09 而 master=06-12） | `run_all` 一次在**同一 asof** 下产 `regime+master+factors`，三者对齐 | `fof/report.py:run_all` |
| **可复现** | 凭手稿，难重跑 | **5 份确定性 JSON 契约**；同输入跑两次**字节级一致** | 两次离线简报 SHA256 **完全相同**（`5270A5F4…`） |
| **可验证** | 无测试 | `tests/` **9 个文件 / 45 个测试**；无网络子集 **19 passed in 1.00s** | `pytest` 实测 |
| **可视化 / 可审阅** | 散落的图、难追问 | 两页仪表板（大势研判 + 因子看板）+ **内嵌 AI 顾问**可质询，刷新带 5 阶段进度条 | `web/` + `server/` |
| **工具 / 模型绑定** | 绑死某人的本机环境 | 任意 LLM（⚙ AI 配置：Anthropic/OpenAI/DeepSeek/Kimi/Zhipu/通义/Ollama）；`AGENTS.md` 跨工具；**零 LLM** 也能 `guanlan_brief.py` 直出 | `docs/portable-agent.md` |

---

## 3. 实测证据（可复现）

**① 确定性（可复现性的硬证据）** — 离线简报跑两次，输出哈希**完全一致**：
```
brief run1: 1.00s  run2: 0.17s
hash1 = 5270A5F41ECF1AA6…
hash2 = 5270A5F41ECF1AA6…
identical = True      # 同输入 → 字节级相同
```

**② 溯源** — `query_vault.py "HMM regime" --top 5` 返回 5 条带路径的引用（节选）：
```
- vault/wiki/sources/2026-05-05-quantsplaybook-repo.md            | prio S | hits 57
- vault/wiki/sources/2026-05-31-dbjg-fabozzi-strategy-decay-risk.md | prio S | hits 25
- vault/wiki/sources/2026-04-02-huatai-energy-stagflation-3stage.md | prio B | hits 30
- vault/wiki/topics/Regime切换与因子轮动.md                          | hits 29
```

**③ 可验证** — `pytest`：9 文件 / 45 测试；无网络核心子集（selection/weights/perf/factors/allocation）
**19 passed in 1.00s**（其余依赖 Tushare 网络的测试需 token）。

**④ 当前真实读数**（来自 `outputs/*.json`，agent 绝不另编）：
```
大势研判：震荡（大势分 49.5，置信 55%）｜ HMM 履冰 ｜ 效率比 ER 0.245
因子轮动：IC 均值 0.042 ｜ ICIR 0.088 ｜ 胜率 54.5%
配置建议：中性（半仓）｜ 超配 反转/低波/红利 ｜ 低配 质量/微盘/小市值
```

---

## 4. agent / 各 skill 的逐项贡献

- **`guanlan-analyst`（agent）**：把松散问题编排成固定 6 步（取证→计算→解读→简报→建议→问是否开仪表板），
  并强制纪律：**never invent numbers**（每个数字来自 JSON）、**每个机制 ≥2 条引用**、防前视、诚实标注。
  这层「纪律」正是手工最容易省略的部分。
- **`quant-research-retriever`**：把「翻几十篇研报」变成秒级带路径检索 → 解决**无引用链**。
- **`regime-radar`**：12 指标 → 0-100 风险分 + 顶/底评分 → 解决**风险口径不统一**。
- **`regime-verdict`**：HMM×ER×基本面 → 走强/震荡/走弱 + 转移矩阵 → 解决**大势判断主观、难复现**。
- **`factor-research`**：12 风格因子排行 + 月度 IC/ICIR + 滚动 Sharpe → 解决**因子轮动靠感觉**。
- **`factor-allocation`**：读前两者 → 姿态（进攻/中性/防御）+ 超配/低配 → 把研判**落成可执行建议**（纯解读）。

---

## 5. 诚实局限（不夸大）

- **这不是 PnL 提升**：交付是研究读数，不是组合，也未回测；本文对比的是**研究工作流效率与可信度**。
- **因子动量很弱**：IC≈0.04 / ICIR≈0.09 / 胜率≈55% → 风格 tilt 只是**弱倾斜**，别据此重仓。
- **大势是研究读数、非交易信号**；ER 在涨跌停日会**虚高**；历史状态色带是 **walk-forward 样本外**判定，
  非全样本平滑。
- **总仓位姿态优先于风格 tilt**；防御期 tilt 意义小。

---

## 6. 如何复现这份对比

```powershell
$env:PYTHONIOENCODING="utf-8"      # 控制台中文/避免编码问题

# ① 确定性：两次离线简报，哈希应一致
python scripts\guanlan_brief.py > b1.md
python scripts\guanlan_brief.py > b2.md
Get-FileHash b1.md, b2.md | Select-Object Hash

# ② 溯源：检索返回带 vault/ 路径的引用
python .claude\skills\quant-research-retriever\scripts\query_vault.py "HMM regime" --top 5

# ③ 可验证：无网络核心子集
python -m pytest tests/test_factor_allocation.py tests/test_selection.py tests/test_weights.py tests/test_perf.py tests/test_factors.py -q

# ④ 语料规模 / 产物契约
(Get-ChildItem vault\wiki\sources -Filter *.md).Count      # 34
Get-ChildItem outputs -Filter *.json                        # 5 份确定性 JSON
```

> ⚠️ 仅供量化研究参考，不构成投资建议。
