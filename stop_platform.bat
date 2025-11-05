@echo off
REM ============================================================================
REM Multi-Agent E-commerce Platform - Complete System Shutdown (Windows)
REM ============================================================================
REM
REM This script stops the ENTIRE platform in the correct order:
REM 1. Frontend UI
REM 2. All 27 backend agents
REM 3. Docker infrastructure
REM
REM Usage: stop_platform.bat
REM
REM ============================================================================

setlocal

set SCRIPT_DIR=%~dp0
set INFRASTRUCTURE_DIR=%SCRIPT_DIR%infrastructure

echo ===============================================================================
echo.
echo   Multi-Agent E-commerce Platform - System Shutdown
echo.
echo   Stopping: Frontend UI + 27 Agents + Docker Infrastructure
echo.
echo ===============================================================================
echo.

REM ============================================================================
REM STEP 1: Stop Frontend
REM ============================================================================

echo ===============================================================================
echo STEP 1: Stopping Frontend UI
echo ===============================================================================
echo.

echo Stopping Vite processes...
taskkill /F /FI "WINDOWTITLE eq *vite*" >nul 2>nul
taskkill /F /FI "IMAGENAME eq node.exe" /FI "WINDOWTITLE eq *vite*" >nul 2>nul

echo Frontend stopped
echo.

REM ============================================================================
REM STEP 2: Stop All Agents
REM ============================================================================

echo ===============================================================================
echo STEP 2: Stopping All 27 Backend Agents
echo ===============================================================================
echo.

if exist "%SCRIPT_DIR%stop_all_agents.bat" (
    call "%SCRIPT_DIR%stop_all_agents.bat"
    echo All agents stopped
) else (
    echo stop_all_agents.bat not found, killing Python processes...
    taskkill /F /FI "IMAGENAME eq python.exe" >nul 2>nul
    taskkill /F /FI "IMAGENAME eq python3.exe" >nul 2>nul
    echo Python processes stopped
)

echo.

REM ============================================================================
REM STEP 3: Stop Docker Infrastructure
REM ============================================================================

echo ===============================================================================
echo STEP 3: Stopping Docker Infrastructure
echo ===============================================================================
echo.

cd /d "%INFRASTRUCTURE_DIR%"

echo Stopping Docker containers...
docker-compose down

echo Docker infrastructure stopped
echo.

cd /d "%SCRIPT_DIR%"

REM ============================================================================
REM SUMMARY
REM ============================================================================

echo ===============================================================================
echo.
echo   SHUTDOWN COMPLETE!
echo.
echo ===============================================================================
echo.
echo All systems stopped successfully!
echo.
echo To start the platform again:
echo   start_platform.bat
echo.

endlocal
