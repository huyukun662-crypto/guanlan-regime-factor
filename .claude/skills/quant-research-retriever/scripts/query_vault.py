"""Query the quant vault for grounding citations.

    python .claude/skills/quant-research-retriever/scripts/query_vault.py "risk parity" --top 5

Vault resolution (portable): env QUANT_VAULT_PATH if set, else the repo-bundled `vault/`
(236 digested 金工研报/concepts ship with the repo). Override with --vault for a personal vault.
Ranks wiki/{sources,topics}/*.md by keyword hits + frontmatter priority (S>A>B) and prints a
citation JSON the agent folds into its rationale. Read-only; never writes the vault. If the vault
is missing it degrades to empty citations (no crash) — the agent then falls back to WebSearch.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

# repo root = parents[4] of .claude/skills/quant-research-retriever/scripts/query_vault.py
_REPO_VAULT = Path(__file__).resolve().parents[4] / "vault"
DEFAULT_VAULT = Path(os.environ.get("QUANT_VAULT_PATH") or _REPO_VAULT)
PRIORITY_RANK = {"S": 3, "A": 2, "B": 1}

# light synonym expansion so English queries hit Chinese vault text
SYNONYMS = {
    "risk parity": ["风险平价", "risk parity", "权重"],
    "regime": ["regime", "择时", "市场状态", "宏观"],
    "regime gate": ["regime", "择时", "敞口", "门控", "宏观"],
    "momentum": ["动量", "momentum", "轮动"],
    "drawdown": ["回撤", "drawdown", "止损"],
    "rsrs": ["rsrs", "阻力支撑", "斜率"],
    "low correlation": ["低相关", "相关性", "分散", "correlation"],
    "etf": ["etf", "轮动", "横截面", "cross-section"],
}


def _terms(query: str) -> list[str]:
    q = query.lower().strip()
    terms = set(re.split(r"\s+", q))
    for key, syns in SYNONYMS.items():
        if key in q or any(t in key for t in terms):
            terms.update(syns)
    return [t for t in terms if t]


def _frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in text[3:end].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def _title(text: str, fallback: str) -> str:
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else fallback


def _quote(text: str, terms: list[str]) -> str:
    for line in text.splitlines():
        ls = line.strip()
        if len(ls) > 12 and not ls.startswith(("#", "-", "|", "`", "---")) \
                and any(t in ls.lower() for t in terms):
            return ls[:160]
    return ""


def search(vault: Path, query: str, top: int) -> dict:
    terms = _terms(query)
    hits = []
    for sub in ("wiki/sources", "wiki/topics"):
        for path in (vault / sub).glob("*.md"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            low = text.lower()
            score = sum(low.count(t) for t in terms)
            if score == 0:
                continue
            fm = _frontmatter(text)
            prio = str(fm.get("priority", "")).upper()[:1]
            hits.append({
                "path": str(path), "title": _title(text, path.stem),
                "priority": prio if prio in PRIORITY_RANK else "",
                "hits": score, "quote": _quote(text, terms),
            })
    hits.sort(key=lambda h: (h["hits"] + 3 * PRIORITY_RANK.get(h["priority"], 0)), reverse=True)
    return {"topic": query, "vault": str(vault), "terms": terms, "citations": hits[:top]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--vault", default=str(DEFAULT_VAULT))
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args()
    out = search(Path(args.vault), args.query, args.top)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
