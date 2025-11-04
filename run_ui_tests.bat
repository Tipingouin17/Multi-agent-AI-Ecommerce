@echo off
REM ============================================================================
REM Dashboard UI Testing Script - Windows
REM ============================================================================
REM This script runs comprehensive UI tests for all dashboard interfaces
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo                     DASHBOARD UI TESTING SUITE
echo ============================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo [INFO] Python found
python --version

REM Check if dashboard is running
echo.
echo [INFO] Checking if dashboard is running on http://localhost:5173...
curl -s http://localhost:5173 >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Dashboard is not running on http://localhost:5173
    echo.
    echo Please start the dashboard first using:
    echo   start_dashboard.bat
    echo.
    pause
    exit /b 1
)

echo [SUCCESS] Dashboard is running

REM Install Selenium if not already installed
echo.
echo [INFO] Checking Selenium installation...
python -c "import selenium" 2>nul
if errorlevel 1 (
    echo [INFO] Installing Selenium WebDriver...
    pip install selenium
    if errorlevel 1 (
        echo [ERROR] Failed to install Selenium
        pause
        exit /b 1
    )
)

echo [SUCCESS] Selenium is installed

REM Check for ChromeDriver
echo.
echo [INFO] Checking ChromeDriver...
where chromedriver >nul 2>&1
if errorlevel 1 (
    echo [WARNING] ChromeDriver not found in PATH
    echo.
    echo Please install ChromeDriver:
    echo   1. Download from: https://chromedriver.chromium.org/
    echo   2. Add to PATH or place in project directory
    echo.
    echo Alternatively, install via pip:
    echo   pip install webdriver-manager
    echo.
    pause
    exit /b 1
)

echo [SUCCESS] ChromeDriver found

REM Run the tests
echo.
echo ============================================================================
echo                        RUNNING UI TESTS
echo ============================================================================
echo.

cd /d "%~dp0"

REM Run with headless mode by default (add --headless flag^)
python testing\ui_dashboard_comprehensive_tests.py --url http://localhost:5173 --headless

set TEST_EXIT_CODE=!errorlevel!

echo.
echo ============================================================================
echo                        TEST EXECUTION COMPLETE
echo ============================================================================
echo.

if !TEST_EXIT_CODE! equ 0 (
    echo [SUCCESS] All tests passed!
    echo Exit code: !TEST_EXIT_CODE!
) else (
    echo [WARNING] Some tests failed or encountered errors
    echo Exit code: !TEST_EXIT_CODE!
)

echo.
echo Check the log files and screenshots in the testing directory for details.
echo.

pause
exit /b !TEST_EXIT_CODE!

