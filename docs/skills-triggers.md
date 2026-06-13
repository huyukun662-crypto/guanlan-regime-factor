# Skills 如何被触发（触发参考）

> 配套：[architecture.md](architecture.md)（设计逻辑）、[usage.md](usage.md)（上手用法）。

## 触发机制（先懂原理）

1. **触发面 = 每个 `SKILL.md` frontmatter 的 `description`。** 你在 Claude Code 里说的话，会被**语义匹配**到各 skill 的 description；命中就**自动加载**那个 SKILL.md 并执行。它是**语义**匹配，不是关键词精确匹配——意思相近的说法也会触发。
2. **前提：必须在 Claude Code 里打开本仓库目录。** 这些是**项目级** `.claude/skills/`，只有当前仓库作为工作目录时才会被发现与触发（与你全局 `~/.claude` 下的 skill 互不影响）。
3. **三种触发路径**：
   - ① **自然语言**：说出意图 → 命中 description → 自动跑（最常用）。
   - ② **Agent 编排**：触发 `guanlan-analyst` 后，它在固定工作流里**自动调**这些 skill（你无感）。
   - ③ **命令行直跑**：`python .claude/skills/<name>/scripts/xxx.py` —— 不依赖触发，最确定性。
4. **不确定时直接点名**：例如「**用 factor-allocation 给配置建议**」「**跑 regime-verdict**」，比含糊描述更稳。
5. **防误触**：每个 SKILL 的 `NOT` 段落划清边界，避免「看因子 / 判大势 / 给配置建议」三者互相抢。

---

## 各 Skill 触发语（取自 frontmatter，代表例，非穷举）

| Skill | 一句话职责 | 典型触发语（中文 / English） |
|---|---|---|
| **regime-radar** | 0-100 风险分 + 顶/底双评 | 「更新风险评分」「现在什么市场状态」/ "read the current regime", "build the risk gauge" |
| **regime-verdict** | 大势研判 走强/震荡/走弱 | 「现在是走强还是走弱」「大势研判」「跑一遍 HMM 大势」「该进攻还是防御」/ "what's the market trend verdict", "judge the regime" |
| **factor-research** | 12 因子看板 排行/IC/Sharpe | 「看因子」「因子轮动 IC」「哪个风格在风口」「因子表现怎么样」/ "factor board / rotation IC / which style is leading" |
| **factor-allocation** | 因子配置建议（姿态+超配/低配） | 「现在该超配/低配哪些风格」「按大势和因子给配置建议」「该进攻还是防御、配哪些风格」/ "factor allocation / tilt advice / 因子配置" |
| **quant-research-retriever** | 查内置 vault 研报、带引用 | 「查研报」「ground this in 金工研报」/ "find research on X" |

## Agent 触发语（`guanlan-analyst`，串起以上 skill）

| 触发语 | 行为 |
|---|---|
| 「跑一遍大势研判」「重算研判+因子」「现在该进攻还是防御」「重建市场仪表板」/ "rebuild the market dashboard", "read the current regime and factors", "what's the market verdict" | 固定 6 步：研报锚定 → 跑 pipeline → 解读 → 带溯源简报 →（可选）配置建议 → **末尾问「要打开仪表盘吗？」** |

---

## 几个易混点

- **「该进攻还是防御」**：既可能触发 `regime-verdict`（只判大势），也可能触发 `guanlan-analyst`（整条链路）或 `factor-allocation`（要配哪些风格）。想要哪种就把话说全：
  - 只看方向 → 「**大势研判**一下，现在走强还是走弱」
  - 要组合建议 → 「该进攻还是防御，**配哪些风格**」（→ factor-allocation）
  - 要完整简报 → 「**跑一遍大势研判**」（→ agent）
- **`factor-research` vs `factor-allocation`**：前者是「**看**因子表现/IC」，后者是「**按**因子给配置**建议**」。看数据 → research；要结论 → allocation。
- **触发不了？** 确认是在 Claude Code 里打开了**本仓库目录**（项目级 skill 才会加载）；或直接命令行跑脚本（路径见 [usage.md](usage.md) 方式③）。
