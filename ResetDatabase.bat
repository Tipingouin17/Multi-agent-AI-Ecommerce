@echo off
REM Database Reset Script for Windows
REM Drops and recreates the database with fresh schema

echo ========================================
echo DATABASE RESET SCRIPT
echo ========================================
echo.
echo WARNING: This will DELETE ALL DATA in the database!
echo.
echo Press Ctrl+C to cancel, or
pause

echo.
python reset_database.py

if errorlevel 1 (
    echo.
    echo ERROR: Database reset failed!
    pause
    exit /b 1
)

echo.

echo ========================================
echo SUCCESS! Database reset complete.
echo ========================================
echo.
echo Next steps:
echo 1. Run: InitDatabase.bat (create tables)
echo 2. Run: SeedDatabase.bat (populate data)
echo.
pause
