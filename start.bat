@echo off
rem 观澜 · 大势研判 + 因子看板 — 一键启动仪表盘
rem 双击运行后浏览器打开 http://localhost:8000
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
start "" http://localhost:8000
python -m uvicorn server.app:app --port 8000 --host 127.0.0.1
pause
