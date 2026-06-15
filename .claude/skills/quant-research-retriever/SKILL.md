---
name: quant-research-retriever
description: >
  Query the repo-bundled quant vault at vault/ (236 digested 金工研报/concepts shipped with the
  repo; override with env QUANT_VAULT_PATH or --vault) to ground FOF/regime recommendations in
  real research with file-path citations; optionally
  cross-check online via WebSearch. Returns ranked source snippets + a citation list for the
  advice panel and the before/after report. Use BEFORE recommending a mechanism — ground it,
  don't assert it. Triggers: "find research on X", "ground this in 金工研报", "查研报".
allowed-tools: Bash, Read, Grep, WebSearch
---

# quant-research-retriever

The grounding step. Turns a topic into ranked citations from the bundled vault so every FOF/regime
recommendation carries a `vault/...` provenance trail.

## When to use
- Before recommending any mechanism (regime gate, risk parity, RSRS, drawdown blacklist).
- Building the rationale block of the agent's final research brief.

## When NOT to use
- Not a data/compute tool — that's `regime-radar` / `regime-verdict` / `factor-research`. This skill only reads docs.

## Vault layout (bundled in repo)
`vault/wiki/sources/*.md` (prioritized S/A/B research pieces) · `vault/wiki/topics/*.md`
(topic hubs) · `vault/wiki/entities/*.md` (concepts). The script reads `sources` + `topics`.
Resolution: env `QUANT_VAULT_PATH` → else repo `vault/`. See `references/source-map.md` for the
curated topic → file map. If the vault is absent the skill returns empty citations (no crash).

## Run
```bash
python .claude/skills/quant-research-retriever/scripts/query_vault.py "risk parity" --top 5
python .claude/skills/quant-research-retriever/scripts/query_vault.py "regime gate" --top 5
```
Output: `{topic, vault, terms, citations:[{path, title, priority, hits, quote}]}` ranked by
keyword hits + frontmatter priority (S>A>B). The script expands a few English↔Chinese synonyms
so English queries hit the Chinese vault.

## WebSearch fallback
Only when the vault is thin on a topic. Clearly label web sources vs vault sources in the output
and prefer S/A-priority vault material when both exist.

## 输出格式（研报级回复）
读完 `query_vault.py` 的 `citations[]` 后产一份「研报溯源」小节（路径逐字照搬、不杜撰标题/路径）：
1. **引用清单（表）**：按相关度（`hits` + 优先级 S>A>B）排序，取 top N —

   | 来源(path) | 标题(title) | 优先级 | 命中(hits) | 关键摘录(quote) |
   |---|---|---|---|---|
2. **锚定结论**：用 **≥2 条** `vault/...` 路径，把当前要主张的机制（regime 门控 / 风险平价 / RSRS / 因子动量）一句话挂到证据上，例如：
   > 低相关分散是「唯一的免费午餐」（`vault/wiki/sources/2026-05-07-jq-etf-cross-section-thinking.md`）；regime 门控依据华泰滞胀三阶段框架（`...2026-04-02-huatai-energy-stagflation-3stage.md`）。
3. **来源标注**：vault 与 WebSearch 结果分开标；两者都有时优先 S/A 优先级的 vault 材料。
4. **覆盖度诚实**：若某主题命中很少（vault 偏薄）→ 明说并触发 WebSearch 补充，不要假装证据充分。

> 质量基线：引用必须真实存在（路径来自脚本输出，不编）；区分 vault 事实与 web 旁证；不堆形容词。

## Output contract（精简版，给 agent 折进简报）
Hand the agent a short rationale that cites **≥2** vault paths verbatim, e.g.:
> 低相关分散是“唯一的免费午餐”（`vault/wiki/sources/2026-05-07-jq-etf-cross-section-thinking.md`）；
> regime 门控依据华泰滞胀三阶段框架（`...2026-04-02-huatai-energy-stagflation-3stage.md`）。
