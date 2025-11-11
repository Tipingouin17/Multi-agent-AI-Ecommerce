@echo off
echo DEBUG: Script started
echo DEBUG: enabledelayedexpansion
setlocal enabledelayedexpansion

echo DEBUG: Setting variables
set "PROJECT_ROOT=%~dp0"
echo DEBUG: PROJECT_ROOT=%PROJECT_ROOT%

cls
echo.
echo ===============================================================================
echo.
echo   Multi-Agent E-commerce Platform - Complete System Launcher
echo.
echo   Starting: PostgreSQL + 37 Agents + Frontend UI
echo.
echo ===============================================================================
echo.

echo.
echo ===============================================================================
echo STEP 1: Checking Prerequisites
echo ===============================================================================
echo.

echo DEBUG: About to check Python
python --version
echo DEBUG: Python exit code: %ERRORLEVEL%

echo DEBUG: About to check Node
node --version
echo DEBUG: Node exit code: %ERRORLEVEL%

echo DEBUG: About to check npm
npm --version
echo DEBUG: npm exit code: %ERRORLEVEL%

echo.
echo DEBUG: Reached after all version checks
echo.
echo All prerequisites checked!
echo.

echo DEBUG: About to start Step 2
echo.
echo ===============================================================================
echo STEP 2: This is a test step
echo ===============================================================================
echo.

echo DEBUG: Script completed successfully
pause
