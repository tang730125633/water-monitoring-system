@echo off
title Water Monitoring System

echo ============================================================
echo           Water Monitoring System - Starting
echo ============================================================
echo.
echo Starting system, please wait...
echo.

cd /d "%~dp0"

REM Check virtual environment
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo Please contact technical support.
    echo.
    pause
    exit /b 1
)

REM Check database
if not exist "water.db" (
    echo [INFO] Generating test data...
    venv\Scripts\python.exe quick_generate.py
    echo.
)

echo [OK] System started successfully!
echo.
echo Browser will open automatically...
echo If not, please visit: http://localhost:8501
echo.
echo ============================================================
echo Press any key to close this window and stop the system
echo ============================================================
echo.

REM Set environment variable to skip email prompt
set STREAMLIT_SERVER_HEADLESS=true

REM Start Streamlit and open browser
start "" http://localhost:8501
venv\Scripts\python.exe -m streamlit run app_streamlit.py --server.port 8501

pause
