"""Start the dashboard server (detached) and open the browser — cross-platform one-shot.

    python scripts/open_dashboard.py [--port 8000] [--no-browser]

Spawns `uvicorn server.app:app` as a detached background process (keeps running after this
script exits) and opens http://127.0.0.1:<port>. No secrets touched; works with no API key
(the dashboard renders the committed outputs/*.json). Idempotent — if the port is already
serving, it just opens the browser. Server stdout/stderr go to logs/dashboard_server.log.
"""

from __future__ import annotations

import argparse
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from fof._compat import ensure_utf8_stdio
ensure_utf8_stdio()


def _serving(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()
    url = f"http://{args.host}:{args.port}"

    if _serving(args.host, args.port):
        print(f"already serving at {url}")
    else:
        (ROOT / "logs").mkdir(exist_ok=True)
        log = open(ROOT / "logs" / "dashboard_server.log", "ab")
        cmd = [sys.executable, "-m", "uvicorn", "server.app:app",
               "--port", str(args.port), "--host", args.host]
        kw: dict = {"cwd": str(ROOT), "stdout": log, "stderr": log, "stdin": subprocess.DEVNULL}
        if sys.platform == "win32":
            # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP — survives the parent shell.
            kw["creationflags"] = 0x00000008 | 0x00000200
        else:
            kw["start_new_session"] = True
        subprocess.Popen(cmd, **kw)
        for _ in range(60):                      # wait up to ~15s for the port to accept
            if _serving(args.host, args.port):
                break
            time.sleep(0.25)
        print(f"dashboard serving at {url} (logs/dashboard_server.log)")

    if not args.no_browser:
        webbrowser.open(url)
    print(f"  大势研判: {url}    因子看板: {url}/factors.html")


if __name__ == "__main__":
    main()
