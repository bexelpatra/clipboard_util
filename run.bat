@echo off
setlocal

rem ===== Settings =====
set "VENV_DIR=venv"
rem ====================

rem Run from this bat's folder so .env and OUTPUT_DIR(./output) resolve here
cd /d "%~dp0"

chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"

rem 1) Check system Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    echo Install from python.org and check "Add Python to PATH".
    pause
    exit /b 1
)

rem 2) Create venv if missing
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment: %VENV_DIR%
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create venv: %VENV_DIR%
        pause
        exit /b 1
    )
)

set "VPY=%VENV_DIR%\Scripts\python.exe"

rem 3) Install requirements if needed
"%VPY%" -c "import pyperclip, dotenv, openpyxl" 2>nul
if errorlevel 1 (
    echo Installing requirements...
    "%VPY%" -m pip install --upgrade pip
    "%VPY%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install requirements.
        pause
        exit /b 1
    )
)

rem 4) Run
"%VPY%" scripts\clipboard_watcher\watcher.py

pause
endlocal
