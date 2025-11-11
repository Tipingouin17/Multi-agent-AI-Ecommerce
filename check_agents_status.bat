@echo off
setlocal enabledelayedexpansion
REM ============================================================================
REM Check Agents Status - Windows Version
REM ============================================================================

echo ================================================================================
echo Multi-Agent E-commerce Platform - Agent Status Check (Windows)
echo ================================================================================
echo.

echo Checking all 37 agents...
echo.

set /a HEALTHY=0
set /a TOTAL=37

echo Core Business Agents (Ports 8000-8028):
echo.

REM Check core agents (8000-8028)
for /L %%p in (8000,1,8028) do (
    netstat -an | findstr ":%%p " | findstr "LISTENING" >nul 2>nul
    if !ERRORLEVEL! EQU 0 (
        echo [OK] Port %%p - Agent running
        set /a HEALTHY+=1
    ) else (
        echo [ERROR] Port %%p - Agent not running
    )
)

echo.
echo Feature Agents (Ports 8031-8038):
echo.

REM Check feature agents (8031-8038)
for /L %%p in (8031,1,8038) do (
    netstat -an | findstr ":%%p " | findstr "LISTENING" >nul 2>nul
    if !ERRORLEVEL! EQU 0 (
        echo [OK] Port %%p - Agent running
        set /a HEALTHY+=1
    ) else (
        echo [ERROR] Port %%p - Agent not running
    )
)

echo.
echo ================================================================================
echo Summary: !HEALTHY!/%TOTAL% agents running
echo ================================================================================
echo.

if !HEALTHY! EQU %TOTAL% (
    echo ✓ All agents are healthy!
) else (
    set /a MISSING=%TOTAL%-!HEALTHY!
    echo ⚠ Warning: !MISSING! agents are not running
    echo.
    echo To start all agents, run: StartAllAgents.bat
)

echo.
pause
