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

## Output contract
Hand the agent a short rationale that cites **≥2** vault paths verbatim, e.g.:
> 低相关分散是“唯一的免费午餐”（`vault/wiki/sources/2026-05-07-jq-etf-cross-section-thinking.md`）；
> regime 门控依据华泰滞胀三阶段框架（`...2026-04-02-huatai-energy-stagflation-3stage.md`）。
