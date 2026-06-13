@echo off
rem 观澜仪表盘常驻服务（计划任务调用；崩溃自动重启）。手动启动请用 start.bat
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
:loop
python -m uvicorn server.app:app --port 8000 --host 127.0.0.1
timeout /t 5 /nobreak >nul
goto loop
