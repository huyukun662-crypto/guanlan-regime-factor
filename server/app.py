"""FastAPI backend — serves the dashboard JSON, the static site, and a streaming chat.

    python -m uvicorn server.app:app --port 8000   (from the project root)

Routes:
  GET  /api/dashboard  -> outputs/dashboard.json (404-safe)
  GET  /api/health     -> {ok, key_available}
  POST /api/chat       -> SSE stream from the Claude advisor (graceful no-key fallback)
  /                    -> static web/ (index.html)
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import chat
from . import refresh as refreshmod

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"
WEB = ROOT / "web"

app = FastAPI(title="Regime-Switch FOF Dashboard")
app.add_middleware(
    CORSMiddleware, allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_methods=["*"], allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    prov, _key, base, model = chat._resolve_provider()
    return {
        "ok": True, "key_available": chat.key_available(),
        "llm_provider": prov, "llm_model": model, "llm_base_url": base or None,
    }


@app.get("/api/dashboard")
def dashboard() -> JSONResponse:
    path = OUTPUTS / "dashboard.json"
    if not path.exists():
        return JSONResponse({"error": "run scripts/run_pipeline.py first"}, status_code=404)
    return JSONResponse(json.loads(path.read_text(encoding="utf-8")))


@app.get("/api/factors")
def factors() -> JSONResponse:
    """Pure factor board (for the standalone factors.html page)."""
    path = OUTPUTS / "factors.json"
    if not path.exists():
        return JSONResponse({"error": "run scripts/run_pipeline.py first"}, status_code=404)
    return JSONResponse(json.loads(path.read_text(encoding="utf-8")))


@app.post("/api/chat")
async def post_chat(body: dict) -> StreamingResponse:
    messages = body.get("messages", [])
    return StreamingResponse(chat.stream_chat(messages), media_type="text/event-stream")


@app.post("/api/refresh")
async def post_refresh(body: dict) -> JSONResponse:
    """Optional Tushare-token update + full pipeline rerun for today. localhost only."""
    token = (body or {}).get("token", "")
    try:
        result = await run_in_threadpool(refreshmod.run_refresh, token)
        return JSONResponse(result)
    except Exception as ex:                 # noqa: BLE001 — report, don't 500 the UI
        return JSONResponse({"ok": False, "error": f"{type(ex).__name__}: {str(ex)[:200]}"})


# static site last so /api/* takes precedence
if WEB.exists():
    app.mount("/", StaticFiles(directory=str(WEB), html=True), name="web")
