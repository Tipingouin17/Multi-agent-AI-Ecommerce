@echo off
REM Simple Multi-Agent System Starter - Always Works!

echo ========================================
echo Multi-Agent E-commerce System
echo ========================================
echo.

call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Virtual environment not found
    echo Please run install.bat first
    pause
    exit /b 1
)

echo 🤖 Starting Multi-Agent System...
echo.

REM Use the direct Python starter (always works)
python start-agents-direct.py

echo.
echo ========================================
echo System stopped
echo ========================================
echo.
echo Available options:
echo   start-simple.bat        - Auto-detect mode (this script)
echo   start-agents-direct.py --demo  - Force demo mode
echo   start-agents-direct.py --full  - Force full mode
echo.
pause
