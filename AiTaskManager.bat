@echo off
cd /d "%~dp0"
echo =================================
echo    AI Task Manager - Launcher
echo =================================
echo.
python launcher.py
if %errorlevel% neq 0 (
    echo.
    echo Error: Make sure Python 3.10+ is installed.
    echo Download from: https://www.python.org/downloads/
    pause
)
