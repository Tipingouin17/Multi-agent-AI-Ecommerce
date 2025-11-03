@echo off
REM ============================================================================
REM Check Agents Status - Windows Version
REM ============================================================================

echo ================================================================================
echo Multi-Agent E-commerce Platform - Agent Status Check (Windows)
echo ================================================================================
echo.

echo Checking all 26 agents...
echo.

REM Check if Python health check script exists
if exist check_all_26_agents_health.py (
    python check_all_26_agents_health.py
) else (
    echo Running manual health check...
    echo.
    
    set /a HEALTHY=0
    set /a TOTAL=26
    
    REM Check each port
    for /L %%p in (8000,1,8025) do (
        netstat -an | findstr :%%p | findstr LISTENING >nul 2>nul
        if !ERRORLEVEL! EQU 0 (
            echo [OK] Port %%p - Agent running
            set /a HEALTHY+=1
        ) else (
            echo [ERROR] Port %%p - Agent not running
        )
    )
    
    echo.
    echo ================================================================================
    echo Summary: %HEALTHY%/%TOTAL% agents running
    echo ================================================================================
)

echo.
pause

