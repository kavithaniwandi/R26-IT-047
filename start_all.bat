@echo off
start "Backend - port 8001" cmd /c call "%~dp0run_backend.bat"
start "Frontend - port 5173" cmd /k "cd /d ""%~dp0frontend"" && npm run dev"
