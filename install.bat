@echo off
title Water Monitoring System - Installation

echo ============================================================
echo           Water Monitoring System - Installation
echo ============================================================
echo.
echo This will install the system. Please wait...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.8 or higher from: https://www.python.org/
    echo.
    pause
    exit /b 1
)

echo [OK] Python is installed
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

echo [OK] Virtual environment created
echo.

REM Install dependencies
echo Installing dependencies, this may take a few minutes...
venv\Scripts\pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo [OK] Dependencies installed
echo.

REM Generate test data
if not exist "water.db" (
    echo Generating test data...
    venv\Scripts\python.exe quick_generate.py
    echo.
)

echo ============================================================
echo              Installation Complete!
echo ============================================================
echo.
echo To start the system, double-click: start.bat
echo.
pause
