@echo off
REM Windows Batch Script to Run Agent Production Readiness Tests
REM This script will test all agents and generate comprehensive logs

echo ================================================================================
echo MULTI-AGENT E-COMMERCE SYSTEM - PRODUCTION READINESS TEST
echo ================================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Check if we're in the right directory
if not exist "scripts\test_all_agents_with_logging.py" (
    echo ERROR: Please run this script from the project root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo Running agent tests...
echo This may take several minutes...
echo.

REM Run the test script
python scripts\test_all_agents_with_logging.py

REM Capture exit code
set TEST_EXIT_CODE=%ERRORLEVEL%

echo.
echo ================================================================================
echo TEST COMPLETED
echo ================================================================================
echo.

if %TEST_EXIT_CODE% EQU 0 (
    echo Result: ALL TESTS PASSED
    echo Exit Code: 0
) else if %TEST_EXIT_CODE% EQU 1 (
    echo Result: SOME TESTS FAILED
    echo Exit Code: 1
    echo Please check the logs directory for details
) else if %TEST_EXIT_CODE% EQU 2 (
    echo Result: PARTIAL SUCCESS - Some agents have warnings
    echo Exit Code: 2
    echo Please check the logs directory for details
) else (
    echo Result: UNEXPECTED ERROR
    echo Exit Code: %TEST_EXIT_CODE%
)

echo.
echo Log files are available in the 'logs' directory
echo.
echo To view the summary:
echo   - Open logs\summary_*.json in a text editor or JSON viewer
echo.
echo To view individual agent logs:
echo   - Check logs\agents\*.log files
echo.
echo ================================================================================

pause
exit /b %TEST_EXIT_CODE%

