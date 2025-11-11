@echo off
REM Database Seed Script for Windows
REM Populates the database with sample data

echo ========================================
echo DATABASE SEED SCRIPT
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Running seed script...
echo.

python seed_database.py

if errorlevel 1 (
    echo.
    echo ERROR: Seed script failed!
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS! Database seeded successfully.
echo ========================================
echo.
echo You can now:
echo 1. Restart the agents: StartPlatform.bat
echo 2. Open the dashboard: http://localhost:5173
echo.
pause
