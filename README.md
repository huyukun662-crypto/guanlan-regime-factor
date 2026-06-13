# 观澜 · 大势研判 + 因子研究助手

一个**自包含**的量化研究作业：用一个 Claude Code **agent**（`guanlan-analyst`）+ **4 个自定义 skills**，把"研报检索 → 风险 regime → 大势研判 → 因子研究"整条链路自动化，并用**真实 A 股 ETF / 指数数据**驱动可演示的仪表板。

> **仪表板现状（两页）**：① **大势研判**（`index.html`）—— HMM 4 态隐马尔可夫 × Kaufman 效率比 × 基本面的综合市场状态研判 + 风险仪表盘 + 顶/底指标 + 风险走势 + AI 顾问；② **因子看板**（`factors.html`）—— 12 个真实风格指数代理因子的累积收益/轮动排行/全样本统计。两页侧栏互导。
>
> **不做组合 / 不回测**：项目交付物是「研判 + 配置建议」（read-only 解读），不构建组合、不出权重、不计回测指标。早期 ETF-FOF 回测脚手架 `fof/{engine,selection,weights,sleeves}.py` 留在仓库**仅作历史代码参考**，**未作为主交付，不在文档与仪表板呈现**。

---

## 它解决什么

| 痛点（手工研究） | 本助手 |
|---|---|
| 翻几十篇研报、无引用链 | `quant-research-retriever` 秒级检索 `vault` 金工研报，带路径引用 |
| notebook 对数据、改一个参数就重写 | `regime-radar` + `regime-verdict` + `factor-research` 把指标/HMM大势/因子固化，一行命令全链路复跑 |
| 单策略心电图、回撤吓人 | 大势 verdict + 因子配置建议给「进攻/中性/防御」姿态 + 风格倾斜，研究判断而非组合 |
| 结果难以审阅 | GuanLan 风格风险仪表盘 + **内嵌实时 Claude 顾问**可质询 |

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
> 旧的 FOF tooling（`fof-research-orchestrator` agent + `fof-builder` skill）已退役；ETF-FOF 回测代码 `fof/{engine,selection,weights,sleeves}.py` 仍在仓库**仅作历史参考**，未作主交付。

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

# 4. 单测（防前视等）
python -m pytest tests/test_factor_allocation.py -q   # 纯映射、无网络，秒过
python -m pytest tests -q                             # 全量（需 TUSHARE_TOKEN + 网络）
```

- **无 `TUSHARE_TOKEN`**：仪表板用仓库内置的 `outputs/*.json` 正常渲染（demo）；只有「刷新数据 / 重跑 pipeline」才需要 token。
- **无 `ANTHROPIC_API_KEY`**：pipeline、仪表板、确定性研判建议**全部可用**，仅实时聊天降级为基线建议。
- **研报库**：`quant-research-retriever` 默认读仓库内置 `vault/`；想换成自己的 Obsidian 库，设环境变量 `QUANT_VAULT_PATH` 或传 `--vault`。库缺失时优雅返回空引用（不崩）。
- **🔐 密钥安全**：`.env` 已 gitignore，**绝不入库**。clone 者各自填自己的 token；任何曾在别处明文出现过的 token 请在 tushare.pro **及时轮换**。

**调用 agent**：在 Claude Code 里打开本仓库 → 项目级 `.claude/agents/guanlan-analyst` 自动可用；说「跑一遍大势研判，该进攻还是防御？」即触发整条链路。

---

## 仪表板内容

- **大势研判页** `index.html` —— 沪深300价量日频上 **walk-forward 重拟合 4 态高斯 HMM**（稳态/平静/履冰/危机，依据 Yang 2026 SSRN 6823998）× **Kaufman 效率比 ER** × 基本面 → 走强/震荡/走弱 verdict + 风险仪表盘 + 顶/底指标 + 风险走势 + AI 顾问。12 个 regime 指标拆成 **技术面/基本面/情绪资金 三栏**（基本面含 **IF 期货净多比** + **IO 期权 PCR** 两个衍生品仓位指标），大势栏 6 个可视化（进攻↔防御仪表盘、HMM 4 态概率演化 stacked-area、状态色带时间轴+持续天数、4×4 转移矩阵热力图、三轴罗盘、价格×状态×ER）。
- **因子看板页** `factors.html` —— 12 个真实风格指数代理因子（动量/反转/小市值/微盘/大盘/价值/成长/科技成长/红利/低波/质量/市场）的累积收益多线图 + 近期轮动排行 + 全样本统计 + 月度 IC/ICIR + 因子相关性。

---

## 目录

```
fof/            数据 / regime / 大势研判 / 因子 / 配置建议（核心 Python 包）
.claude/agents/ guanlan-analyst.md
.claude/skills/ regime-radar, regime-verdict, factor-research, factor-allocation, quant-research-retriever
server/         FastAPI（仪表盘 JSON + 静态站点 + 流式 /api/chat）
web/            GuanLan 风格仪表盘（index.html, factors.html, app.js, chat.js, styles.css）
scripts/        run_pipeline.py, open_dashboard.py
outputs/        仪表盘读取的 JSON（入库以保证可移植）
docs/           usage.md, architecture.md, skills-triggers.md
tests/          防前视 / 指标 / 配置建议映射 单测
vault/          内置研报库（236 篇金工研报+概念，retriever 默认读它）
```

## 工程纪律

- **防前视**：指标/选择只用 `series.loc[:asof]`；HMM 每月 walk-forward 只用 `[:m]` 重拟合，`tests/test_regime.py` 断言追加未来 bar 不改变 asof。
- **密钥安全**：`TUSHARE_TOKEN` / `ANTHROPIC_API_KEY` 仅在 gitignored 的 `.env`，不入库、不打日志。
- **诚实交付**：项目不构建组合、不回测、不出权重；`factor-allocation` 给的是**研究建议**，姿态优先于风格 tilt，因子动量历史很弱（IC≈0.04）→ tilt 只是弱倾斜别重押。

---

> ⚠️ 本仓库仅供量化研究参考，不构成任何投资建议。股市有风险，盈亏自负。
