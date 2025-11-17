@echo off
REM Add Missing Database Tables
REM This script adds cart, reviews, promotions, and payment_methods tables

echo ========================================
echo ADD MISSING DATABASE TABLES
echo ========================================
echo.
echo This will add the following tables:
echo   - carts
echo   - cart_items
echo   - reviews
echo   - promotions
echo   - payment_methods
echo.
echo Press Ctrl+C to cancel, or
pause

python add_missing_tables.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS!
    echo ========================================
    echo.
    echo Next steps:
    echo 1. Restart agents: StopAllAgents.bat then StartPlatform.bat
    echo 2. Test new features in the UI
    echo.
) else (
    echo.
    echo ========================================
    echo ERROR!
    echo ========================================
    echo.
    echo Please check the error message above.
    echo.
)

pause
