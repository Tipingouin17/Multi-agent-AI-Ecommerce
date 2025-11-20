@echo off
REM Stop All V3 Agents Script for Windows
REM This script stops all Python agent processes

echo ==========================================
echo Stopping All 42 Agents
echo ==========================================
echo.

echo Counting running Python processes...
for /f %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FI "IMAGENAME eq python3.exe" /FI "IMAGENAME eq python3.11.exe" ^| find /c /v ""') do set count=%%i

if %count% GTR 0 (
    echo Found Python processes running. Stopping them...
    taskkill /F /IM python.exe /T >nul 2>&1
    taskkill /F /IM python3.exe /T >nul 2>&1
    taskkill /F /IM python3.11.exe /T >nul 2>&1
    echo.
    echo ✓ All agent processes stopped successfully!
) else (
    echo No Python agent processes found running.
)

echo.
echo ✓ Cleanup complete!
echo.
echo   To restart agents, run: StartPlatform.bat
echo.
