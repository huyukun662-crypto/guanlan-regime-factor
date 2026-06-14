"""Cross-platform compatibility helpers.

The main use case is Windows consoles whose default encoding (e.g., gbk) cannot
print the Chinese output and math symbols (U+2212) used throughout this project.
Calling `ensure_utf8_stdio()` at the top of each CLI entry point makes scripts
self-contained so users do not need to remember `$env:PYTHONIOENCODING="utf-8"`.
"""

from __future__ import annotations

import sys


def ensure_utf8_stdio() -> None:
    """Reconfigure stdout/stderr to UTF-8 when running on a non-UTF-8 console.

    This is a no-op on platforms/terminals that already use UTF-8, and it
    swallows any ``reconfigure`` errors so the script still runs in restricted
    environments (e.g., piped output where ``reconfigure`` may raise).
    """
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        try:
            encoding = getattr(stream, "encoding", None) or ""
            if encoding.lower() != "utf-8":
                reconfigure = getattr(stream, "reconfigure", None)
                if reconfigure is not None:
                    reconfigure(encoding="utf-8")
        except Exception:  # noqa: BLE001 — best-effort; never break the script
            pass
