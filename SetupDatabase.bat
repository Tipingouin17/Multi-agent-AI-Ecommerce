@echo off
REM Complete Database Setup Script
REM Resets, initializes, and seeds the database in one go

echo ========================================
echo COMPLETE DATABASE SETUP
echo ========================================
echo.
echo This will:
echo 1. Drop and recreate the database
echo 2. Create all tables
echo 3. Populate with sample data
echo.
echo WARNING: This will DELETE ALL EXISTING DATA!
echo.
echo Press Ctrl+C to cancel, or
pause

echo.
echo ========================================
echo STEP 1/3: Resetting Database
echo ========================================
echo.

python reset_database.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to reset database!
    pause
    exit /b 1
)

echo.

echo ========================================
echo STEP 2/3: Creating Tables
echo ========================================
echo.

python init_database.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to create tables!
    pause
    exit /b 1
)

echo.
echo ========================================
echo STEP 3/3: Seeding Data
echo ========================================
echo.

python seed_database.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to seed data!
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ SETUP COMPLETE!
echo ========================================
echo.
echo Your database is ready!
echo.
echo Next steps:
echo 1. Start platform: StartPlatform.bat
echo 2. Open dashboard: http://localhost:5173
echo 3. Login with: merchant1@example.com / merchant123
echo.
pause
