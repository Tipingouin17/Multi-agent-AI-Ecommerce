@echo off
REM ============================================================================
REM Complete System Startup - Windows Version
REM ============================================================================

echo ================================================================================
echo Multi-Agent E-commerce Platform - Complete System Startup (Windows)
echo ================================================================================
echo.

REM ============================================================================
REM STEP 1: Check Prerequisites
REM ============================================================================

echo ================================================================================
echo STEP 1: Checking Prerequisites
echo ================================================================================
echo.

REM Check Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed
    echo Please install Python 3.11+ from https://www.python.org/
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] Python installed: %PYTHON_VERSION%

REM Check PostgreSQL
pg_isready -h localhost -p 5432 >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PostgreSQL is not running on localhost:5432
    echo Please start PostgreSQL and try again.
    pause
    exit /b 1
)
echo [OK] PostgreSQL is running

REM Check Kafka (optional)
netstat -an | findstr :9092 | findstr LISTENING >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Kafka is running (optional)
) else (
    echo [WARNING] Kafka is not running (agents will run in degraded mode)
)

REM Check Node.js
where node >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
    echo [OK] Node.js installed: %NODE_VERSION%
) else (
    echo [WARNING] Node.js not found (dashboard will not start)
    echo Install Node.js 18+ from https://nodejs.org/
)

echo.

REM ============================================================================
REM STEP 2: Start All Agents
REM ============================================================================

echo ================================================================================
echo STEP 2: Starting All 26 Agents
echo ================================================================================
echo.

echo Launching agents in background...
call start_all_26_agents.bat

echo.
echo Waiting 30 seconds for agents to initialize...
timeout /t 30 /nobreak > nul
echo.

REM ============================================================================
REM STEP 3: Check Agent Health
REM ============================================================================

echo ================================================================================
echo STEP 3: Checking Agent Health
echo ================================================================================
echo.

if exist check_all_26_agents_health.py (
    python check_all_26_agents_health.py
    
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo [OK] Agent health check completed
    ) else (
        echo.
        echo [WARNING] Some agents may not be fully healthy
        echo The system will continue, but some features may not work.
    )
) else (
    echo [WARNING] Health check script not found, skipping...
)

echo.

REM ============================================================================
REM STEP 4: Launch Dashboard
REM ============================================================================

echo ================================================================================
echo STEP 4: Launching Dashboard UI
echo ================================================================================
echo.

if not exist start_dashboard.bat (
    echo [WARNING] start_dashboard.bat not found
    echo You can manually start the dashboard:
    echo   cd multi-agent-dashboard ^&^& npm run dev
    echo.
) else (
    echo Starting dashboard...
    echo.
    
    REM Start dashboard in new window
    start "Dashboard" cmd /c start_dashboard.bat
    
    echo [OK] Dashboard started in new window
    
    REM Wait for dashboard to be ready
    echo.
    echo Waiting for dashboard to be ready...
    
    set /a WAITED=0
    :wait_dashboard
    if %WAITED% GEQ 60 goto dashboard_timeout
    
    curl -s http://localhost:5173 >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Dashboard is ready!
        goto dashboard_ready
    )
    
    timeout /t 2 /nobreak > nul
    set /a WAITED+=2
    goto wait_dashboard
    
    :dashboard_timeout
    echo.
    echo [WARNING] Dashboard did not start within 60 seconds
    echo Check the dashboard window for errors
    
    :dashboard_ready
)

echo.

REM ============================================================================
REM STEP 5: System Status Summary
REM ============================================================================

echo ================================================================================
echo SYSTEM STARTUP COMPLETE!
echo ================================================================================
echo.

echo System Status:
echo.

REM Check key agent ports
set /a HEALTHY_COUNT=0
set /a TOTAL_AGENTS=26

for /L %%p in (8000,1,8025) do (
    netstat -an | findstr :%%p | findstr LISTENING >nul 2>nul
    if !ERRORLEVEL! EQU 0 (
        set /a HEALTHY_COUNT+=1
    )
)

echo   Agents Running: %HEALTHY_COUNT%/%TOTAL_AGENTS%

REM Check dashboard
netstat -an | findstr :5173 | findstr LISTENING >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo   Dashboard: [OK] Running
    echo   Dashboard URL: http://localhost:5173
) else (
    echo   Dashboard: [WARNING] Not running
)

echo.
echo Access Points:
echo.
echo   Dashboard: http://localhost:5173
echo   Admin Interface: http://localhost:5173 -^> Select 'System Administrator'
echo   Merchant Portal: http://localhost:5173 -^> Select 'Merchant Portal'
echo   Customer Interface: http://localhost:5173 -^> Select 'Customer Experience'
echo   Database Test: http://localhost:5173 -^> Select 'Database Integration Test'
echo.
echo   Primary API: http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo.

echo Log Files:
echo.
echo   Agent Logs: logs\agents\
echo   Dashboard Log: Check dashboard window
echo.

echo To Stop the System:
echo.
echo   1. Stop dashboard: Close the dashboard window or press Ctrl+C
echo   2. Stop agents: stop_all_agents.bat
echo.

echo ================================================================================
echo Happy Testing!
echo ================================================================================
echo.

pause

