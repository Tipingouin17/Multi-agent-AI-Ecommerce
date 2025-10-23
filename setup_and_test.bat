@echo off
REM Windows Batch Wrapper for Setup and Test Script
REM This runs the PowerShell script with proper execution policy

echo ================================================================================
echo Multi-Agent E-commerce System - Setup and Test
echo ================================================================================
echo.

REM Check if PowerShell is available
where powershell >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PowerShell is not available on this system
    echo Please install PowerShell or run the Python scripts manually
    pause
    exit /b 1
)

REM Run the PowerShell script
powershell -ExecutionPolicy Bypass -File "%~dp0setup_and_test.ps1"

pause

