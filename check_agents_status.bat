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

echo Core Business Agents:
echo.

REM Define actual core agent ports (excluding gaps at 8017, 8025)
set "CORE_PORTS=8000 8001 8002 8003 8004 8005 8006 8007 8008 8009 8010 8011 8012 8013 8014 8015 8016 8018 8019 8020 8021 8022 8023 8024 8026 8027 8028"

for %%p in (%CORE_PORTS%) do (
    netstat -an | findstr ":%%p " | findstr "LISTENING" >nul 2>nul
    if !ERRORLEVEL! EQU 0 (
        echo [OK] Port %%p - Agent running
        set /a HEALTHY+=1
    ) else (
        echo [ERROR] Port %%p - Agent not running
    )
)

echo.
echo Feature Agents (Priority 1 ^& 2):
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
    echo To view agent logs: dir logs\agents
    echo To restart all agents: StartAllAgents.bat
    echo To stop all agents: StopAllAgents.bat
)

echo.
pause
