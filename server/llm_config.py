"""Persist LLM provider config to .env + live process env (UI-driven).

Keys handled (all optional; empty values clear the env var + .env line):
    LLM_PROVIDER, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL,
    ANTHROPIC_API_KEY, OPENAI_API_KEY (so the auto-detect in chat.py picks them up)

Sensitive values (anything containing "_KEY") are never echoed back in the response.
The dashboard then calls /api/health to confirm the resolved provider/model.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env"

_ALLOWED = {"LLM_PROVIDER", "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL",
            "ANTHROPIC_API_KEY", "OPENAI_API_KEY"}


def update_llm_config(payload: dict) -> dict:
    """Apply (only) the keys in payload that are in _ALLOWED. Empty string = delete."""
    updates: dict[str, str] = {}
    for k, v in (payload or {}).items():
        ku = k.strip().upper()
        if ku in _ALLOWED:
            updates[ku] = (v or "").strip()
    if not updates:
        return {"ok": False, "error": "no recognised LLM_* keys in payload"}

    _patch_env_file(updates)
    for k, v in updates.items():
        if v:
            os.environ[k] = v
        else:
            os.environ.pop(k, None)

    # Re-resolve to surface what's effective (never echo the key itself).
    from . import chat
    prov, key, base, model = chat._resolve_provider()
    return {"ok": True, "provider": prov, "model": model,
            "base_url": base or None, "key_available": bool(key)}


def _patch_env_file(updates: dict[str, str]) -> None:
    """Replace or delete the matching KEY=… lines; append new keys at the end."""
    lines: list[str] = []
    if ENV.exists():
        lines = ENV.read_text(encoding="utf-8").splitlines()

    new_lines: list[str] = []
    seen: set[str] = set()
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            new_lines.append(line)
            continue
        head = stripped.split("=", 1)[0].strip()
        if head in updates:
            seen.add(head)
            if updates[head]:                       # rewrite
                new_lines.append(f"{head}={updates[head]}")
            # else: drop the line (delete)
        else:
            new_lines.append(line)

    for k, v in updates.items():
        if v and k not in seen:
            new_lines.append(f"{k}={v}")

    ENV.write_text("\n".join(new_lines).rstrip("\n") + "\n", encoding="utf-8")
