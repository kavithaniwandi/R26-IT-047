@echo off
powershell.exe -NoProfile -Command "Get-NetTCPConnection -State Listen -LocalPort 8001 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"
cd /d "%~dp0backend"
.\venv\Scripts\python.exe -m uvicorn app.models.main:app --host 0.0.0.0 --port 8001
pause
