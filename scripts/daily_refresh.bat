@echo off
REM Nightly FOF data refresh — invoked by Windows Task Scheduler at 20:00.
REM Token is read from the gitignored .env by the Python code; nothing secret lives here.
cd /d "%~dp0.."
set PYTHONIOENCODING=utf-8
if not exist logs mkdir logs
python "%~dp0daily_refresh.py" >> "logs\daily_refresh.log" 2>&1
