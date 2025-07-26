@echo off
title Amazon Price Tracker
color 0A

echo.
echo ========================================
echo    Amazon Price Tracker - Web Dashboard
echo ========================================
echo.
echo Starting the application...
echo Web dashboard will open at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the application
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

REM Check if requirements are installed
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
)

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating configuration file from template...
    copy .env.example .env
    echo.
    echo ⚠️  IMPORTANT: Please edit .env file and add your SerpAPI key!
    echo    Get your free API key at: https://serpapi.com/users/sign_up
    echo.
    echo Opening .env file for editing...
    notepad .env
    echo.
    echo After setting up your API key, run this script again.
    pause
    exit /b 1
)

REM Run the application
python main.py web --reload

pause
