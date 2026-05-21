@echo off
chcp 936 >nul 2>nul
title BookGuard

cd /d %~dp0backend

if not exist "venv\Scripts\python.exe" (
    echo [1/3] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
) else (
    echo [1/3] Virtual environment exists
)

set PY=venv\Scripts\python.exe

echo [2/3] Installing dependencies...
"%PY%" -m pip install -r requirements.txt -q 2>nul
echo Done.

echo [3/3] Starting server...
echo.
echo ================================
echo   Open: http://localhost:8000
echo   Login: admin / admin123
echo   Press Ctrl+C to stop
echo ================================
echo.
"%PY%" -m app.main
pause
