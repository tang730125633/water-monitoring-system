@echo off
title Water Environment Monitoring System
cd /d "%~dp0"

echo ============================================================
echo        Water Environment Monitoring System
echo ============================================================
echo.

REM ========== Step 1: Find Python ==========
echo [1/4] Checking Python environment...

set PYTHON_EXE=
set PIP_CMD=

REM Check embedded Python first
if exist "python_embed\python.exe" (
    set PYTHON_EXE=python_embed\python.exe
    echo       Found embedded Python.
    goto :check_deps
)

REM Check system Python
where python >nul 2>&1
if not errorlevel 1 (
    echo       Found system Python.
    goto :use_system_python
)

where python3 >nul 2>&1
if not errorlevel 1 (
    echo       Found system Python3.
    set PYTHON_EXE=python3
    goto :setup_venv
)

echo.
echo [ERROR] Python is NOT installed on this computer.
echo.
echo Please install Python 3.8+ from: https://www.python.org/
echo IMPORTANT: Check "Add Python to PATH" during installation.
echo.
echo After installing Python, run this file again.
echo.
pause
exit /b 1

:use_system_python
set PYTHON_EXE=python

:setup_venv
if "%PYTHON_EXE%"=="" set PYTHON_EXE=python

REM Create venv if not exists
if exist "venv\Scripts\python.exe" (
    set PYTHON_EXE=venv\Scripts\python.exe
    set PIP_CMD=venv\Scripts\pip.exe
    echo       Virtual environment ready.
    goto :check_deps
)

echo       Creating virtual environment...
%PYTHON_EXE% -m venv venv
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to create virtual environment.
    echo Please make sure Python is installed correctly.
    echo.
    pause
    exit /b 1
)

set PYTHON_EXE=venv\Scripts\python.exe
set PIP_CMD=venv\Scripts\pip.exe
echo       Virtual environment created.
goto :check_deps

:check_deps
REM ========== Step 2: Install Dependencies ==========
if exist ".deps_installed" (
    echo [2/4] Dependencies already installed. Skipping.
    goto :check_db
)

echo [2/4] Installing dependencies (first run only, may take a few minutes)...
echo.

if defined PIP_CMD (
    "%PIP_CMD%" install -r requirements.txt --no-warn-script-location
) else (
    "%PYTHON_EXE%" -m pip install -r requirements.txt --no-warn-script-location
)

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies.
    echo Please check your internet connection and try again.
    echo.
    pause
    exit /b 1
)

echo done > .deps_installed
echo.
echo [OK] Dependencies installed successfully.
echo.

:check_db
REM ========== Step 3: Check Database ==========
if exist "water.db" (
    echo [3/4] Database found. Skipping.
    goto :start_app
)

echo [3/4] Generating test data...
"%PYTHON_EXE%" quick_generate.py
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to generate test data.
    echo.
    pause
    exit /b 1
)
echo [OK] Test data generated.
echo.

:start_app
REM ========== Step 4: Start Application ==========
echo [4/4] Starting system...
echo.
echo ============================================================
echo.
echo   System is running!
echo.
echo   If the browser does not open automatically, visit:
echo   http://localhost:8501
echo.
echo   To stop the system, close this window.
echo.
echo ============================================================
echo.

set STREAMLIT_SERVER_HEADLESS=true

REM Open browser
start "" http://localhost:8501

REM Run streamlit
"%PYTHON_EXE%" -m streamlit run app_streamlit.py --server.port 8501 --browser.gatherUsageStats false

echo.
echo System stopped.
echo.
pause
