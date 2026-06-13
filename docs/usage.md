# 使用说明 — 观澜 · 大势研判 + 因子研究

> 配套阅读：[architecture.md](architecture.md)（agent/skill 的设计逻辑）、[README.md](../README.md)（项目总览）。
> 控制台中文乱码时先设 `$env:PYTHONIOENCODING="utf-8"`（仅显示问题，文件均为 UTF-8）。

---

## 0. 一次性准备（跨平台）

```powershell
# 建议先建虚拟环境（Python ≥ 3.10）
python -m venv venv
# Windows:        venv\Scripts\Activate.ps1
# macOS / Linux:  source venv/bin/activate
python -m pip install -r requirements.txt          # 装依赖
Copy-Item .env.example .env                         # 配密钥（mac/linux: cp .env.example .env）
#   .env 里填 TUSHARE_TOKEN（必填，数据源）；ANTHROPIC_API_KEY（可选，仅仪表板实时聊天用）
```
> 下文命令以 PowerShell 为例；macOS/Linux 把反斜杠路径 `a\b` 换成 `a/b`、`$env:X="y"` 换成 `X=y` 即可。

> **无 token 也能看 demo**：仓库已带 `outputs/*.json`，clone 后直接 `uvicorn` 开仪表板即可浏览；
> 只有「刷新数据 / 重跑 pipeline」才需要 `TUSHARE_TOKEN`。**无 `ANTHROPIC_API_KEY`** 时整条 pipeline、
> 两页仪表板、确定性研判建议全部可用，只有「实时 AI 聊天」降级为基线建议。

> **研报库**：`quant-research-retriever` 默认读仓库内置 `vault/`；自备 Obsidian 库可设 `QUANT_VAULT_PATH` 或 `--vault`。

---

## 1. 最快路径：一条命令出全部 + 看仪表板

```powershell
$env:PYTHONIOENCODING="utf-8"
python scripts\run_pipeline.py --asof 2026-06-09 --start 2020-01-01   # 出 regime/master/factors/dashboard.json
python -m uvicorn server.app:app --port 8000                          # 开后端
```
浏览器打开：
- **http://127.0.0.1:8000** —— 大势研判页（风险仪表盘 + HMM 大势栏 + AI 顾问）
- **http://127.0.0.1:8000/factors.html** —— 因子看板页（累积/轮动/IC·ICIR/滚动Sharpe）

> 打不开时优先用 `127.0.0.1` 而非 `localhost`（避开 https 自动升级/代理劫持）。改了前端 JS 记得 **Ctrl+F5** 强刷。

---

## 2. 三种调用 skill 的方式

### 方式 ① 自然语言（对话里触发）
直接说出意图，Claude 自动匹配并执行对应 skill：

| 你说 | 触发的 skill | 给你什么 |
|---|---|---|
| `现在是走强还是走弱？` / `大势研判一下` | `regime-verdict` | 走强/震荡/走弱 + 置信度 + 转移矩阵 |
| `最近哪个风格在风口？` / `看因子轮动 IC` | `factor-research` | 因子排行 + 月度IC/ICIR + 滚动Sharpe |
| `现在什么市场状态 / 更新风险评分` | `regime-radar` | 0-100 风险分 + 顶/底评分 |
| `现在该超配/低配哪些风格？该进攻还是防御？` | `factor-allocation` | 总仓位姿态 + 超配/低配风格 |
| `查一下风险平价的研报` | `quant-research-retriever` | 带 `vault/...` 路径的引用 |

### 方式 ② 让 agent 一条龙
说 `跑一遍大势研判` / `现在该进攻还是防御，配什么` → `guanlan-analyst` 按固定 5 步走：
研报锚定 → 跑 pipeline → 解读 → 带溯源简报 →（要建议时）`factor-allocation`。
产出每个数字都来自 json、每个机制配 ≥2 条研报引用。

### 方式 ③ 命令行直接跑脚本（最确定性，不必对话）
```powershell
$env:PYTHONIOENCODING="utf-8"
# 大势研判 → outputs/master.json
python .claude\skills\regime-verdict\scripts\compute_master.py --asof 2026-06-09
# 因子看板 → outputs/factors.json
python .claude\skills\factor-research\scripts\compute_factors.py --asof 2026-06-09
# 风险评分 → outputs/regime.json
python .claude\skills\regime-radar\scripts\compute_regime.py --asof 2026-06-09
# 因子配置建议 → outputs/factor_allocation.json（读上面 master+factors，需先有这两份）
python .claude\skills\factor-allocation\scripts\build_factor_allocation.py
# 研报检索
python .claude\skills\quant-research-retriever\scripts\query_vault.py "风险平价" --top 5
```
每个脚本跑完打印一行 JSON 摘要并落盘到 `outputs/`。

> **依赖顺序**：`factor-allocation` 是消费者，只读 `master.json` + `factors.json`。先跑 `regime-verdict`
> + `factor-research`（或 `run_pipeline.py`）生成这两份，再跑它；缺文件时脚本会提示。

---

## 3. 典型场景

| 想做的事 | 怎么做 |
|---|---|
| 每天看盘下判断 | 对话 `跑一遍大势研判，该进攻还是防御？`（agent 一条龙） |
| 只刷新某一块数据 | 命令行跑对应 `compute_*.py` |
| 全量刷新 + 可视化 | `run_pipeline.py` → `uvicorn` → 开网页 |
| 拿一份配置建议 | 对话 `现在该超配/低配哪些风格？` 或跑 `build_factor_allocation.py` |
| 留参数证据 | `python scripts\grid_search.py` → `outputs\grid_search.csv` |

---

## 4. 输出文件一览（`outputs/`）

| 文件 | 由谁产 | 内容 |
|---|---|---|
| `regime.json` | regime-radar / pipeline | 0-100 风险分 + 12 指标顶/底 + 风险走势 |
| `master.json` | regime-verdict / pipeline | 大势 verdict + 三轴 + 转移矩阵 + 状态统计 |
| `factors.json` | factor-research / pipeline | 12 因子累积/排行/IC·ICIR/滚动Sharpe |
| `factor_allocation.json` | factor-allocation | 姿态 + 超配/低配 + tilt 依据 + caveats |
| `dashboard.json` | pipeline | 上面三块的打包快照（仪表板读它） |
| `grid_search.csv` | grid_search.py | 参数网格证据（ETF-FOF 研究证据链）|

---

## 5. 验证 / 自检

```powershell
python -m pytest tests -q          # 单测全过（含防前视断言）
```

---

## 6. 常见问题

- **控制台中文乱码** → `$env:PYTHONIOENCODING="utf-8"`（文件本身是 UTF-8，仅显示问题）。
- **网页打不开 / 被拒绝** → 用 `http://127.0.0.1:8000`（非 localhost）；前端改动后 Ctrl+F5 强刷。
- **`没有接口(yc_cb)访问权限` / `api.waditu.com` 超时** → 已知：yc_cb 是付费接口，自动走 akshare 兜底；
  超时会自动重试。日志里的 WARNING 属正常，不影响结果。
- **`factor-allocation` 报缺 master.json/factors.json** → 先跑 `regime-verdict` + `factor-research`
  或 `run_pipeline.py`。
- **诚实提醒**：因子动量很弱（IC≈0.04），`factor-allocation` 的风格 tilt 只是弱倾斜、姿态优先；
  大势历史色带是 walk-forward 样本外；ER 在涨跌停日虚高。**仅供量化研究参考，不构成投资建议。**
