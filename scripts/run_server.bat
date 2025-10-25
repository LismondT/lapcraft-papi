@echo off
chcp 65001 >nul
setlocal

echo ========================================
echo    FastAPI Server Launcher
echo ========================================

set "BAT_DIR=%~dp0"
set "PROJECT_ROOT=%BAT_DIR%.."

:: Переходим в корневую директорию проекта
cd /d "%PROJECT_ROOT%"

echo Project root: %CD%
echo Starting server...

start %CD%/.venv/Scripts/uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload

pause