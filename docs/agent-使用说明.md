# guanlan-analyst · agent 使用说明

> 观澜的核心 agent：把「研报检索 → 风险 regime → 大势研判（HMM×效率比×基本面）→ 因子研究」一条龙，
> 产出**带溯源、绝不编数字**的研判简报。本文讲**怎么在对话里直接调用它**。配套：
> [usage.md](usage.md)（仪表板/skill 用法）、[portable-agent.md](portable-agent.md)（跨工具）、
> [before-after.md](before-after.md)（前后效果对比）。

---

## 1. 三种调用方式

### 方式 A — Claude Code 对话里直接说（最简单）
在本仓库目录打开 Claude Code，项目级 `.claude/agents/guanlan-analyst.md` 会被**自动发现**。
直接用自然语言说出意图即可触发：

| 你说 | 触发 |
|---|---|
| `跑一遍大势研判` | 完整六步：取证 → 计算 → 解读 → 简报 → 建议 → 问是否开仪表板 |
| `现在该进攻还是防御？` | 同上，结论落到一句姿态线 |
| `重算研判 + 因子` | 重跑 pipeline 后给读数 |
| `重建市场仪表板` / `what's the market verdict` | 英文同样触发 |

也可**显式点名**：`@guanlan-analyst 现在该不该加仓`，或在 `/agents` 菜单里选 `guanlan-analyst`。

> **只读 / 不联网**：想用已有数据快速出结论、不重算、不要 token，就加一句
> 「**只读现有 outputs，不要重算、不要联网**」。实测 26 秒内返回。

### 方式 B — 其它 AI 工具（Cursor / Codex / Aider / Gemini CLI / Ollama / ChatGPT Web）
这些工具不读 `.claude/agents/`，但仓库根的 **`AGENTS.md`** 就是同一套 agent 的跨工具版系统提示。
加载方式见 [portable-agent.md](portable-agent.md)（Cursor/Codex 自动读 AGENTS.md；其余粘贴为系统提示）。

### 方式 C — 命令行零-LLM（不进对话、不要任何 key）
```bash
python scripts/guanlan_brief.py                 # 直接输出 Markdown 研判简报
python scripts/guanlan_brief.py --recompute     # 先重算到今天（需 TUSHARE_TOKEN）再出
```

---

## 2. agent 会做什么（固定六步工作流）

1. **GROUND 取证** — `quant-research-retriever` 检索内置研报库，每个机制 ≥2 条 `vault/...` 路径引用。
2. **COMPUTE 计算** — 一行 `run_pipeline.py` 同一 walk-forward 产 `regime/master/factors` 三 JSON。
3. **READ 解读** — 按各 skill 的读法解读三份 JSON。
4. **BRIEF 简报** — 大势 verdict + 置信 + 风险 band + 因子读数 + 一句姿态（数字全来自 JSON）。
5. **ADVISE 建议（可选）** — `factor-allocation` 给超配/低配 + 姿态。
6. **OFFER 收尾** — 主动问「要打开仪表盘吗？」，确认后才 `python scripts/open_dashboard.py`。

---

## 3. 它返回什么（真实示例 · 只读调用节选）

```
观澜 · 只读研判简报（asof 2026-06-12）
依据：master.json 引 vault/wiki/sources/2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes.md
      （HMM 状态识别）+ vault/wiki/entities/效率系数.md（Kaufman 效率比）
1. 大势 verdict：震荡，master_score 49.5，confidence 55%；HMM 履冰（已持续 49 天）、ER 0.245
2. 风险 band：composite 39.8（中低）；顶分 52.2 / 底分 42.8，权益敞口 0.8
3. 因子轮动：超配 反转/低波/红利，低配 质量/微盘/小市值；诚实标注 IC≈0.042、ICIR≈0.088、胜率 54.5%（弱信号）
4. 姿态线：中性（半仓/择优）—— 由「震荡 verdict + 中低风险 band」共同决定，非单一数字
仅供研究参考。
```
每个数字都来自 `outputs/*.json`，每个机制带 `vault/` 引用——可逐条回溯、可复现。

---

## 4. 常用问法

- 「现在 A 股什么状态？该进攻还是防御？」
- 「该超配/低配哪些风格？依据是什么？」
- 「重算到今天再给我研判」（会触发 pipeline，需 token）
- 「只读现有数据快速给个结论」（秒级、无 token）
- 「打开仪表盘」（在 agent 问你时回这句，它才启动）

---

## 5. 它不会做什么（边界）

- **不建组合、不回测、不出权重** —— 交付研判读数与配置建议，非可交易组合。
- **不编数字** —— 数字只来自 `outputs/*.json`，缺数据会让你先跑 pipeline。
- **不擅自启动服务** —— 仪表板只有你确认后才开。
- **不替你下单** —— 仅供研究参考，不构成投资建议。

---

## 6. 无密钥也能用

- **看结论 / 跑简报**：仓库自带算好的 `outputs/*.json`，读盘即得，**无需任何 key**。
- **TUSHARE_TOKEN**：只有「刷新到最新数据」才需要（每次输入、不存盘）。
- **LLM key**：只有仪表板的实时 AI 对话框需要；没有就降级为确定性基线建议。
- agent / skill / pipeline 的计算全是本地 Python（numpy/pandas/hmmlearn），**从不调大模型**。

---

## 7. 故障排查

| 现象 | 处理 |
|---|---|
| 说了触发语没反应 | 确认在**本仓库目录**打开 Claude Code（项目级 agent 才加载）；或显式 `@guanlan-analyst` |
| 数据是旧的 | 默认读已有 JSON；要最新就说「重算到今天」或网页点刷新（填 token） |
| 刷新很慢 | 首次含 HMM walk-forward + 指数 tail，约 15–30 秒；进度条会显示阶段 |
| 报缺 outputs | 先 `python scripts/run_pipeline.py --asof <日期> --start 2020-01-01` |

> ⚠️ 仅供量化研究参考，不构成投资建议。
