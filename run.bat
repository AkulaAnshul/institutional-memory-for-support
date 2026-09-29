@echo off
cd /d "%~dp0"
if exist ".conda\python.exe" (
  set "PY=.conda\python.exe"
) else if exist ".venv\Scripts\python.exe" (
  set "PY=.venv\Scripts\python.exe"
) else (
  set "PY=python"
)
echo Starting on http://127.0.0.1:8000
echo Leave this window open while you record. Close it to stop.
"%PY%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
