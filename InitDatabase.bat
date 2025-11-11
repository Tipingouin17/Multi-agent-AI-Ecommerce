@echo off
REM Database Initialization Script for Windows
REM Creates all required tables in PostgreSQL

echo ========================================
echo DATABASE INITIALIZATION
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Running database initialization...
echo.

python init_database.py

if errorlevel 1 (
    echo.
    echo ERROR: Database initialization failed!
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS! Database initialized.
echo ========================================
echo.
echo Next step: Run SeedDatabase.bat to populate with data
echo.
pause
