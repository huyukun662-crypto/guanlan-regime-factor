# 观澜 · 大势研判 + 因子研究助手

一个**自包含**的量化研究作业：用一个 Claude Code **agent**（`guanlan-analyst`）+ **4 个自定义 skills**，把"研报检索 → 风险 regime → 大势研判 → 因子研究"整条链路自动化，并用**真实 A 股 ETF / 指数数据**驱动可演示的仪表板。

> **仪表板现状（两页）**：① **大势研判**（`index.html`）—— HMM 4 态隐马尔可夫 × Kaufman 效率比 × 基本面的综合市场状态研判 + 风险仪表盘 + 顶/底指标 + 风险走势 + AI 顾问；② **因子看板**（`factors.html`）—— 12 个真实风格指数代理因子的累积收益/轮动排行/全样本统计。两页侧栏互导。
>
> **FOF 组合模块已从仪表板移除**，但 `fof/{engine,selection,weights,sleeves}.py` + `scripts/grid_search.py` + `outputs/grid_search.csv` + `docs/before-after.md` **作为研究证据链完整保留在仓库**（可 `FOFConfig` 复跑）。下文「前后对比」「4 铁律」描述的是该保留的 FOF 研究成果，非当前仪表板内容。

> 策略思想来自参考文章："别找圣杯了，学着排兵布阵" —— 单策略撞上风格切换就是死局，唯一的免费午餐是**低相关分散 + regime 门控**。本仓库把文章的 **4 铁律**固化为代码（保留作证据）。

---

## 它解决什么

| 痛点（手工研究） | 本助手 |
|---|---|
| 翻几十篇研报、无引用链 | `quant-research-retriever` 秒级检索 `vault` 金工研报，带路径引用 |
| notebook 对数据、改一个参数就重写 | `regime-radar` + `regime-verdict` + `factor-research` 把指标/HMM大势/因子固化，一行命令全链路复跑 |
| 单策略心电图、回撤吓人 | regime 门控风险平价 FOF：最大回撤 **-28.1% → -9.7%**，夏普 **0.77 → 1.05**，卡尔马 **0.72 → 1.14**，月胜率 **53% → 73%** |
| 结果难以审阅 | GuanLan 风格风险仪表盘 + **内嵌实时 Claude 顾问**可质询 |

---

## 前后对比（真实数据，2020-04 → 2026-06，asof=2026-06-09，标的池一致）

| 方案 | 年化收益 | 最大回撤 | 夏普 | 卡尔马 | 月胜率 |
|---|---|---|---|---|---|
| 单一动量策略（圣杯陷阱） | 20.21% | **-28.06%** | 0.77 | 0.72 | 53% |
| 等权静态组合（朴素分散） | 7.98% | -9.50% | 0.84 | 0.84 | 51% |
| **regime 门控风险平价 FOF（进取档）** | **11.11%** | **-9.71%** | **1.05** | **1.14** | **73%** |

> 数字来源 `outputs/before_after.json`（由 `python -c "..."` 直接调 `engine.run_fof(DEFAULT_CONFIG)`+`report.before_after` 重生成，**而非** `run_all`——FOF 已从仪表板 pipeline 移除，作为研究证据链单独保留）。

9 sleeve 的 FOF 把单一策略 -28% 级回撤压到 **-9.7%**，并**在风险调整后指标上超越等权基准**（夏普 0.84→1.05、卡尔马 0.84→1.14、月胜率 51%→73%）；**代价**是 FOF 最大回撤 **-9.71%**（略劣于等权 -9.50%，约 0.2pp）和换手成本上升——这是「进取档」放开单 sleeve 上限（50%→100%）带来的集中度后果，**不是免费午餐**。要回到回撤优先的稳健档，`FOFConfig.max_weight=0.5` 即可（详见 [`docs/before-after.md`](docs/before-after.md) 的诚实局限）。这是**修正数据 bug 后**的诚实结果（早期 1.4 卡尔马源于 510300/512890 被截断到 2024+ 平静期）。

---

## 架构

> 上手用法（装/配/跑/调 skill/常见问题）见 **[docs/usage.md](docs/usage.md)**；Agent + Skills 的分层逻辑见 **[docs/architecture.md](docs/architecture.md)**；**每个 skill 用什么话触发**见 **[docs/skills-triggers.md](docs/skills-triggers.md)**。

```
Tushare Pro ──▶ fof/ (Python 包) ──▶ outputs/*.json ──▶ web/ 仪表盘
  真实ETF+宏观     data→regime→selection→weights→engine→report      (vanilla JS + Chart.js)
                                                          ▲
   .claude/agents/guanlan-analyst  ──────────────────────┤  串起 5 skills
   .claude/skills/{regime-radar, regime-verdict, factor-research, factor-allocation, quant-research-retriever}
                                                          ▼
                               server/ (FastAPI) ──▶ /api/chat 实时 Claude 顾问
```

### Agent
`.claude/agents/guanlan-analyst.md` —— 固定 4 阶段（研报锚定 → 风险 regime → 大势研判 → 因子研究），绝不编造数字、至少引用 2 个研报路径、本身无需 API key。

### 5 个 Skills
| skill | 作用 | 产出 |
|---|---|---|
| `regime-radar` | **12 个真实指标**的**顶/底双评分**（RSRS/MA20/宽度/波动率 + Tushare 宏观金铜比/期限利差/ERP + 情绪融资余额Z/全市场成交Z/Shibor + IF期货净多比/IO期权PCR）→ 0-100 综合风险分 + 顶/底部分 + 风险走势序列 | `outputs/regime.json` |
| `regime-verdict` | **大势研判**：HMM 4 态后验 × Kaufman 效率比 × 基本面三轴融合 → 走强/震荡/走弱 + 转移矩阵 + 状态统计 | `outputs/master.json` |
| `factor-research` | **因子看板**：12 风格因子的累积/轮动排行/月度IC·ICIR/滚动Sharpe/全样本统计/相关性 | `outputs/factors.json` |
| `factor-allocation` | **因子配置建议**（集成上两者）：读 master + factors → **总仓位姿态**（进攻/中性/防御）+ 该**超配/低配哪些风格**（方向由因子 IC 符号定）。纯解读、不建组合、不回测、不出权重 | `outputs/factor_allocation.json` |
| `quant-research-retriever` | 检索 `vault` 金工研报（+可选 WebSearch），带引用 | 引用 JSON |

> **`factor-allocation` 诚实口径**：总仓位姿态优先于风格 tilt；因子动量很弱（IC≈0.04 → tilt 只是弱倾斜别重押）；防御期 tilt 意义小；**这是研究建议、不是组合**（无权重/未回测/未计成本）。详见 `.claude/skills/factor-allocation/references/reading-allocation-advice.md`。
>
> 旧的 FOF tooling（`fof-research-orchestrator` agent + `fof-builder` skill）已退役；ETF-sleeve 版 FOF 回测代码、`outputs/grid_search.csv`、`docs/before-after.md` 仍作研究证据链保留在 `fof/`，可 `FOFConfig` 复跑。

### 怎么触发（说什么话）
在 Claude Code 里**打开本仓库目录**后，直接用自然语言说出意图即可——Claude 把你的话**语义匹配**到各 `SKILL.md` 的 `description`（触发面），命中就自动加载执行。

| 你说（中文 / English） | 触发 |
|---|---|
| 「更新风险评分」「现在什么市场状态」/ "read the current regime" | `regime-radar` → 0-100 风险分 + 顶/底 |
| 「现在是走强还是走弱」「大势研判」「该进攻还是防御」/ "judge the regime" | `regime-verdict` → 走强/震荡/走弱 |
| 「看因子」「因子轮动 IC」「哪个风格在风口」/ "factor board / rotation IC" | `factor-research` → 因子排行/IC/Sharpe |
| 「该超配/低配哪些风格」「按大势和因子给配置建议」/ "factor allocation / tilt advice" | `factor-allocation` → 姿态 + 超配/低配 |
| 「查研报」/ "find research on X" | `quant-research-retriever` → 带引用 |
| **「跑一遍大势研判」「重建市场仪表板」/ "what's the market verdict"** | **agent `guanlan-analyst`** → 整条链路 + 末尾问「要打开仪表盘吗？」 |

要点：① 是**语义**匹配，不必逐字照搬，意思相近即可；② 不确定就**直接点名**——「用 `factor-allocation` 给配置建议」；③ 也可**命令行直跑**脚本（见 [docs/usage.md](docs/usage.md) 方式③），不依赖触发。完整触发语对照与易混点见 **[docs/skills-triggers.md](docs/skills-triggers.md)**。

### 4 铁律（`fof/selection.py` + `fof/weights.py`）
1. 30 日动量选（只买正在赚钱的）
2. 15% 回撤拉黑 + 卡尔马门槛；过线 < 2 个 → 100% 货基
3. 夏普排序（求稳不求快）
4. 逆回撤风险平价 + 单 sleeve ≤ 50% + regime 门控敞口（trend 1.0 / ranging 0.8 / bear 0.0）

---

## 快速开始（跨平台，`git clone` 即用）

仓库**自包含**：`vault/`（236 篇金工研报/概念）、`outputs/*.json`（demo 数据）、`.claude/`（agent + 5 skills）全部随仓库分发，不依赖任何本机环境。

```bash
# 1. 建虚拟环境 + 装依赖（Python ≥ 3.10）
python -m venv venv
# Windows:        venv\Scripts\Activate.ps1
# macOS / Linux:  source venv/bin/activate
python -m pip install -r requirements.txt

# 2. 看 demo —— 无需任何 token：仓库已带 outputs/*.json
python scripts/open_dashboard.py        # 一键：起服务(后台)+自动开浏览器到 127.0.0.1:8000
#   或手动： python -m uvicorn server.app:app --port 8000  然后开 http://127.0.0.1:8000 / /factors.html

# 3. 要刷新到最新数据，再配自己的 token
cp .env.example .env          # Windows: Copy-Item .env.example .env
#   .env 填 TUSHARE_TOKEN（必填，去 https://tushare.pro/register 免费领）；ANTHROPIC_API_KEY（可选）
python scripts/run_pipeline.py --asof 2026-06-05 --start 2020-01-01

# 4. 单测（防前视等）+ 网格证据
python -m pytest tests/test_factor_allocation.py -q   # 纯映射、无网络，秒过
python -m pytest tests -q                             # 全量（需 TUSHARE_TOKEN + 网络）
```

- **无 `TUSHARE_TOKEN`**：仪表板用仓库内置的 `outputs/*.json` 正常渲染（demo）；只有「刷新数据 / 重跑 pipeline」才需要 token。
- **无 `ANTHROPIC_API_KEY`**：pipeline、仪表板、确定性研判建议**全部可用**，仅实时聊天降级为基线建议。
- **研报库**：`quant-research-retriever` 默认读仓库内置 `vault/`；想换成自己的 Obsidian 库，设环境变量 `QUANT_VAULT_PATH` 或传 `--vault`。库缺失时优雅返回空引用（不崩）。
- **🔐 密钥安全**：`.env` 已 gitignore，**绝不入库**。clone 者各自填自己的 token；任何曾在别处明文出现过的 token 请在 tushare.pro **及时轮换**。

**调用 agent**：在 Claude Code 里打开本仓库 → 项目级 `.claude/agents/guanlan-analyst` 自动可用；说「跑一遍大势研判，该进攻还是防御？」即触发整条链路。

---

## 真实 ETF Sleeve（低相关）

| sleeve | 代码 | 规则 | 角色 |
|---|---|---|---|
| 动量轮动 | 510300/510500/159915/513100 | 21d 最强且 > MA20 | 进攻 |
| 红利低波防御 | 512890 | ≥ MA60 持有 | 防御 |
| 宽基锚 | 510300 | MA200 趋势滤波 | 锚 |
| 黄金+国债避险 | 518880+511260 | 50/50 月度再平衡 | 避险 |
| 可转债 | 511380 | MA60 滤波 | 偏债α |
| **SAR 趋势** | 510300 | Parabolic SAR：价上方持有、下穿空仓（趋势+动态止损） | 趋势α |
| **SRI 风格轮动** | 159915↔512890 | 成长/价值相对强度切换 | 风格α |
| **鳄鱼线趋势** | 510300 | Bill Williams 三均线多头排列(lips>teeth>jaw)持有 | 趋势α |
| **双因子抄底** | 510300→159915 | 3年MDD≥20% & 上证50 PE分位≤10% 才进攻，否则空仓 | 抄底α |
| 货基兜底 | 511880 | 现金/逆回购代理 | 现金 |

> 后 4 个 sleeve 由 `vault` 金工研报挖掘新增（SAR：`jq-sar-indicator-explainer`；SRI/抄底：`openalphas-bottom-style-timing`；鳄鱼线：`qpb-alligator-index-timing-rotation`）。Choppiness Index 因源笔记本地验证 OOS 无增量、IS 过拟合而**诚实剔除**。新增「**大势研判**」栏：沪深300价量日频上 **walk-forward 重拟合 4 态高斯 HMM**（稳态/平静/履冰/危机，依据 Yang2026 SSRN 6823998）× **Kaufman 效率比 ER** × 基本面 → 确定性大势结论（进攻/中性/防御）+ 样本外状态色带；**仅作研判展示**——实测把 HMM 接入 FOF 回测门控会全面劣化（详见诚实局限），故 `regime_source` 默认 `rule`、`hmm` 可切换。大势研判页把 12 个 regime 指标拆成 **技术面/基本面/情绪资金 三栏**（基本面含 **IF期货净多比**`fut_holding` + **IO期权PCR**`opt_daily` 两个衍生品仓位指标），并把「大势研判」栏做成 6 个可视化（进攻↔防御仪表盘、HMM 状态概率演化 stacked-area、状态色带时间轴+持续天数、4×4 转移矩阵热力图、三轴罗盘、价格×状态×ER）。**因子看板**独立成页 `factors.html`：12 个真实风格指数代理因子（动量/反转/小市值/微盘/大盘/价值/成长/科技成长/红利/低波/质量/市场）的累积收益多线图 + 近期轮动排行 + 全样本统计 + 因子相关性。（FOF/sleeve 因子暴露回归因依赖已移除的 FOF，故不在仪表板呈现，代码保留作证据。）

---

## 目录

```
fof/            数据/regime/选择/权重/引擎/报告（核心 Python 包）
.claude/agents/ guanlan-analyst.md
.claude/skills/ regime-radar, regime-verdict, factor-research, factor-allocation, quant-research-retriever
server/         FastAPI（仪表盘 JSON + 静态站点 + 流式 /api/chat）
web/            GuanLan 风格仪表盘（index.html, app.js, chat.js, styles.css）
scripts/        run_pipeline.py, grid_search.py
outputs/        仪表盘读取的 JSON（入库以保证可移植）
docs/           before-after.md
tests/          4 铁律 / 风险平价 / 防前视 / 指标 单测
```

## 工程纪律

- **防前视**：指标/选择只用 `series.loc[:asof]`，回测 `ret = nav.pct_change().shift(-1)`（收盘决策、次日兑现），`tests/test_regime.py` 断言追加未来 bar 不改变 asof。
- **密钥安全**：`TUSHARE_TOKEN` / `ANTHROPIC_API_KEY` 仅在 gitignored 的 `.env`，不入库、不打日志。
- **诚实局限**：网格为全窗口 in-sample 调参（128 组，非 OOS 冠军）；进取档放开单 sleeve 上限后年化反超等权（10.8% vs 7.9%）且回撤仍≤等权，但**集中度风险上升**（单 survivor 可吃满整档敞口），非免费午餐；FOF 平均约半仓在权益、其余吃货基利息。
- **HMM 门控负结果（诚实保留）**：把「大势研判」的 HMM×ER regime 接入 FOF 回测门控后，128 组 grid 实测全面劣化（年化 11.3%→约 5.5%、夏普 1.13→0.52、回撤 -9.4%→-12.2%）——月度 HMM 更保守/有滞后。按"新机制须严格超越前代冠军方可替换"，回测**保留 rule 门控**，HMM 仅作展示栏；`FOFConfig.regime_source="hmm"` 可一键复现该负结果。这正是 IS 选参纪律要保护的：不为上线一个机制而牺牲已验证的更优解。
- **证据链 > 漂亮数字（真实复盘）**：搭建中发现 `get_ohlcv` 只向后补尾、不回填早期历史的缓存 bug，导致 510300/512890 被截断到 2024+ 的较平静期，早期跑出"夏普 1.36 / 卡尔马 1.41"的虚高。修正后用完整 2020-2026（含 2022 熊市）重跑+重扫网格，冠军参数回落到 `calmar_min=1.5`（文章原值）、`min_pass=1`，结果诚实落到夏普 0.89 / 回撤 -7.9%。**保留这段复盘正是工程纪律的意义。**

---

> ⚠️ 本仓库仅供量化研究参考，不构成任何投资建议。股市有风险，盈亏自负。
