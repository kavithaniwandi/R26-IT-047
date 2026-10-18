@echo off
powershell.exe -NoProfile -Command "Get-NetTCPConnection -State Listen -LocalPort 5173 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"
start "Backend" cmd /k call "%~dp0run_backend.bat"
start "Frontend" cmd /k "cd /d ""%~dp0frontend"" && npm run dev"
