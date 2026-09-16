@echo off
setlocal

rem ===== Settings =====
set "CONDA_ROOT=%USERPROFILE%\anaconda3"
set "CONDA_ENV=base"
rem ====================

rem Run from this bat's folder so .env and OUTPUT_DIR(./output) resolve here
cd /d "%~dp0"

chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"

if not exist "%CONDA_ROOT%\Scripts\activate.bat" (
    echo [ERROR] Anaconda not found: %CONDA_ROOT%
    echo Edit CONDA_ROOT in %~nx0
    pause
    exit /b 1
)

call "%CONDA_ROOT%\Scripts\activate.bat" %CONDA_ENV%
if errorlevel 1 (
    echo [ERROR] Failed to activate conda env: %CONDA_ENV%
    pause
    exit /b 1
)

python -c "import pyperclip, dotenv, openpyxl" 2>nul
if errorlevel 1 (
    echo Installing requirements...
    python -m pip install -r requirements.txt
)

python scripts\clipboard_watcher\watcher.py

pause
endlocal
