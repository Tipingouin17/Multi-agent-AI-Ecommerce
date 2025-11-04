@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM ============================================================================
REM MASTER LAUNCH SCRIPT - Multi-Agent E-Commerce Platform (Windows)
REM ============================================================================

REM Parse command-line arguments
set VERBOSE=0

:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="-v" set VERBOSE=1
if /i "%~1"=="--verbose" set VERBOSE=1
if /i "%~1"=="-h" goto show_help
if /i "%~1"=="--help" goto show_help
if /i "%~1"=="/?" goto show_help
shift
goto parse_args

:show_help
echo Usage: %~nx0 [-v^|--verbose] [-h^|--help]
echo.
echo Options:
echo   -v, --verbose    Enable verbose output with detailed command tracing
echo   -h, --help, /?   Show this help message
echo.
echo Examples:
echo   %~nx0                # Normal mode
echo   %~nx0 --verbose      # Verbose mode with detailed output
echo   %~nx0 -v             # Verbose mode (short form)
exit /b 0

:args_done

REM Note: VERBOSE mode shows detailed results/logs, not command traces

echo ================================================================================
echo MASTER LAUNCH SCRIPT - Multi-Agent E-Commerce Platform
echo ================================================================================
echo.

REM ============================================================================
REM CONFIGURATION
REM ============================================================================

set PROJECT_ROOT=%CD%
set MASTER_LOG_DIR=logs\master
set AGENT_LOG_DIR=logs\agents
set INFRASTRUCTURE_LOG_DIR=logs\infrastructure

REM Create timestamp for log files (using PowerShell for reliability)
for /f "tokens=*" %%a in ('powershell -Command "Get-Date -Format 'yyyyMMdd_HHmmss'"') do set TIMESTAMP=%%a
set STARTUP_LOG=%MASTER_LOG_DIR%\startup_%TIMESTAMP%.log
set PROCESS_TRACKING_FILE=%MASTER_LOG_DIR%\process_tracking.json

echo [%date% %time%] Master Launch Script Started > "%STARTUP_LOG%"
echo [%date% %time%] Master Launch Script Started

REM ============================================================================
REM INITIALIZATION
REM ============================================================================

echo ================================================================================
echo INITIALIZING MASTER LAUNCH SCRIPT
echo ================================================================================
echo.

REM Create all log directories
if not exist "%MASTER_LOG_DIR%" (
    echo [INFO] Creating directory: %MASTER_LOG_DIR%
    mkdir "%MASTER_LOG_DIR%"
)
if not exist "%AGENT_LOG_DIR%" (
    echo [INFO] Creating directory: %AGENT_LOG_DIR%
    mkdir "%AGENT_LOG_DIR%"
)
if not exist "%INFRASTRUCTURE_LOG_DIR%" (
    echo [INFO] Creating directory: %INFRASTRUCTURE_LOG_DIR%
    mkdir "%INFRASTRUCTURE_LOG_DIR%"
)

echo [OK] Created log directories:
echo   - Master logs: %MASTER_LOG_DIR%
echo   - Agent logs: %AGENT_LOG_DIR%
echo   - Infrastructure logs: %INFRASTRUCTURE_LOG_DIR%
echo.

REM Initialize process tracking file
echo {"agents": {}, "infrastructure": {}, "dashboard": {}} > "%PROCESS_TRACKING_FILE%"
echo [OK] Initialized process tracking: %PROCESS_TRACKING_FILE%
echo.
echo [INFO] Master log file: %STARTUP_LOG%
echo.

echo [%date% %time%] Log directories created >> "%STARTUP_LOG%"

REM ============================================================================
REM INFRASTRUCTURE CHECKS
REM ============================================================================

echo ================================================================================
echo CHECKING INFRASTRUCTURE COMPONENTS
echo ================================================================================
echo.

set ALL_OK=1

REM Check Python
echo [INFO] Checking Python installation...
if "%VERBOSE%"=="1" echo   -^> Running: python --version
python --version > "%INFRASTRUCTURE_LOG_DIR%\python.log" 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo [OK] Python: !PYTHON_VERSION!
    if "%VERBOSE%"=="1" for /f "tokens=*" %%i in ('where python') do echo   -^> Python path: %%i
    echo [%date% %time%] Python: !PYTHON_VERSION! >> "%STARTUP_LOG%"
) else (
    echo [ERROR] Python not found
    echo   -^> Please install Python 3.11+ from https://www.python.org/
    echo [%date% %time%] ERROR: Python not found >> "%STARTUP_LOG%"
    set ALL_OK=0
)
echo.

REM Check PostgreSQL (with fallback detection)
echo [INFO] Checking PostgreSQL...
if "%VERBOSE%"=="1" echo   -^> Trying: pg_isready -h localhost -p 5432
pg_isready -h localhost -p 5432 > "%INFRASTRUCTURE_LOG_DIR%\postgresql.log" 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] PostgreSQL: Running on port 5432 (verified with pg_isready)
    if "%VERBOSE%"=="1" pg_isready -h localhost -p 5432
    echo [%date% %time%] PostgreSQL: Running >> "%STARTUP_LOG%"
) else (
    REM Fallback: Check if port 5432 is listening
    if "%VERBOSE%"=="1" echo   -^> Fallback: Checking if port 5432 is listening...
    netstat -an | findstr :5432 | findstr LISTENING > nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        echo [OK] PostgreSQL: Port 5432 is listening (pg_isready not available)
        echo [%date% %time%] PostgreSQL: Port listening >> "%STARTUP_LOG%"
    ) else (
        echo [WARNING] PostgreSQL: Not detected (port 5432 not listening)
        echo   -^> PostgreSQL is recommended but not required for basic agent functionality
        echo   -^> To install: https://www.postgresql.org/download/windows/
        echo   -^> Some agents may run in degraded mode without database
        echo [%date% %time%] WARNING: PostgreSQL not detected >> "%STARTUP_LOG%"
    )
)
echo.

REM Check Kafka (optional)
echo [INFO] Checking Kafka...
if "%VERBOSE%"=="1" echo   -^> Running: netstat -an ^| findstr :9092
netstat -an | findstr :9092 | findstr LISTENING > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Kafka: Running on port 9092
    echo Kafka running > "%INFRASTRUCTURE_LOG_DIR%\kafka.log"
    echo [%date% %time%] Kafka: Running >> "%STARTUP_LOG%"
) else (
    echo [WARNING] Kafka: Not running (optional - agents will run in degraded mode)
    echo Kafka not running > "%INFRASTRUCTURE_LOG_DIR%\kafka.log"
    echo [%date% %time%] WARNING: Kafka not running >> "%STARTUP_LOG%"
)
echo.

REM Check Node.js
echo [INFO] Checking Node.js...
if "%VERBOSE%"=="1" echo   -^> Running: node --version
node --version > "%INFRASTRUCTURE_LOG_DIR%\nodejs.log" 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
    echo [OK] Node.js: !NODE_VERSION!
    if "%VERBOSE%"=="1" for /f "tokens=*" %%i in ('where node') do echo   -^> Node.js path: %%i
    echo [%date% %time%] Node.js: !NODE_VERSION! >> "%STARTUP_LOG%"
) else (
    echo [WARNING] Node.js: Not found (dashboard will not start)
    echo   -^> Install Node.js 18+ from https://nodejs.org/
    echo Node.js not found > "%INFRASTRUCTURE_LOG_DIR%\nodejs.log"
    echo [%date% %time%] WARNING: Node.js not found >> "%STARTUP_LOG%"
)
echo.

if %ALL_OK% EQU 0 (
    echo.
    echo ================================================================================
    echo CRITICAL ERROR: Infrastructure prerequisites not met
    echo ================================================================================
    echo [ERROR] Infrastructure check failed. Please fix the issues above.
    echo [%date% %time%] ERROR: Infrastructure check failed >> "%STARTUP_LOG%"
    pause
    exit /b 1
)

echo [OK] All infrastructure components are ready!
echo.

REM ============================================================================
REM START ALL AGENTS
REM ============================================================================

echo ================================================================================
echo STARTING ALL 26 AGENTS
echo ================================================================================
echo.

echo [INFO] Agent startup sequence initiated...
echo [INFO] Startup delay between agents: 2 seconds
echo.

set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/multi_agent_ecommerce

REM Define all agents
set AGENT_COUNT=0

call :start_agent "order_agent_production_v2" 8000 "order"
call :start_agent "product_agent_production" 8001 "product"
call :start_agent "inventory_agent" 8002 "inventory"
call :start_agent "marketplace_connector_agent" 8003 "marketplace"
call :start_agent "payment_agent_enhanced" 8004 "payment"
call :start_agent "dynamic_pricing_agent" 8005 "dynamic_pricing"
call :start_agent "carrier_selection_agent" 8006 "carrier_selection"
call :start_agent "customer_agent_enhanced" 8007 "customer"
call :start_agent "customer_communication_agent" 8008 "customer_communication"
call :start_agent "returns_agent" 8009 "returns"
call :start_agent "fraud_detection_agent" 8010 "fraud_detection"
call :start_agent "recommendation_agent" 8011 "recommendation"
call :start_agent "promotion_agent" 8012 "promotion"
call :start_agent "risk_anomaly_detection_agent" 8013 "risk_anomaly"
call :start_agent "knowledge_management_agent" 8014 "knowledge_management"
call :start_agent "transport_management_agent_enhanced" 8015 "transport"
call :start_agent "warehouse_agent" 8016 "warehouse"
call :start_agent "document_generation_agent" 8017 "document"
call :start_agent "support_agent" 8018 "support"
call :start_agent "d2c_ecommerce_agent" 8019 "d2c_ecommerce"
call :start_agent "after_sales_agent_production" 8020 "after_sales"
call :start_agent "backoffice_agent_production" 8021 "backoffice"
call :start_agent "infrastructure_agents" 8022 "infrastructure"
call :start_agent "ai_monitoring_agent_self_healing" 8023 "ai_monitoring"
call :start_agent "monitoring_agent" 8024 "monitoring"
call :start_agent "quality_control_agent_production" 8025 "quality_control"

echo.
echo [OK] All 26 agents started successfully!
echo.

REM Wait for agents to initialize
echo [INFO] Waiting 30 seconds for agents to initialize...
timeout /t 30 /nobreak > nul
echo.

REM ============================================================================
REM HEALTH CHECKS
REM ============================================================================

echo ================================================================================
echo CHECKING AGENT HEALTH
echo ================================================================================
echo.

echo [INFO] Performing health checks on all 26 agents...
echo.

set HEALTHY=0
set UNHEALTHY=0
set NOT_RUNNING=0

for /L %%p in (8000,1,8025) do call :check_agent_health %%p

echo.
echo ================================================================================
echo HEALTH CHECK SUMMARY
echo ================================================================================
echo [OK] Healthy:     %HEALTHY%/26
echo [WARNING] Unhealthy:   %UNHEALTHY%/26
echo [ERROR] Not Running: %NOT_RUNNING%/26
echo.

set /a TOTAL_OK=%HEALTHY%+%UNHEALTHY%
set /a PERCENTAGE=%TOTAL_OK%*100/26

echo [INFO] Overall Status: %PERCENTAGE%%% operational
echo.

if %HEALTHY% EQU 26 (
    echo [SUCCESS] ALL AGENTS ARE HEALTHY!
) else (
    echo [WARNING] Some agents are unhealthy or not running
    echo [INFO] Starting automatic recovery process...
    call :retry_unhealthy_agents
)

REM ============================================================================
REM START DASHBOARD
REM ============================================================================

echo ================================================================================
echo STARTING DASHBOARD UI
echo ================================================================================
echo.

if exist start_dashboard.bat (
    echo [INFO] Launching dashboard in new window...
    echo   -^> Command: start "Multi-Agent Dashboard" cmd /c start_dashboard.bat
    start "Multi-Agent Dashboard" cmd /c start_dashboard.bat
    echo [OK] Dashboard started in new window
    echo.
    
    echo [INFO] Waiting for dashboard to be ready (max 60 seconds)...
    set /a WAITED=0
    :wait_dashboard
    if !WAITED! GEQ 60 goto dashboard_timeout
    
    netstat -an | findstr :5173 | findstr LISTENING > nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        echo [OK] Dashboard is ready on http://localhost:5173
        goto dashboard_ready
    )
    
    timeout /t 2 /nobreak > nul
    set /a WAITED+=2
    goto wait_dashboard
    
    :dashboard_timeout
    echo [WARNING] Dashboard did not start within 60 seconds
    echo   -^> Check the dashboard window for errors
    
    :dashboard_ready
) else (
    echo [WARNING] start_dashboard.bat not found, skipping dashboard startup
)

echo.

REM ============================================================================
REM FINAL STATUS REPORT
REM ============================================================================

echo ================================================================================
echo SYSTEM STATUS REPORT
echo ================================================================================
echo.

set REPORT_FILE=%MASTER_LOG_DIR%\status_report_%TIMESTAMP%.txt

(
    echo ================================================================================
    echo MULTI-AGENT E-COMMERCE PLATFORM - STATUS REPORT
    echo ================================================================================
    echo.
    echo Generated: %date% %time%
    echo Project Root: %PROJECT_ROOT%
    echo.
    echo INFRASTRUCTURE:
    pg_isready -h localhost -p 5432 > nul 2>&1
    if !ERRORLEVEL! EQU 0 (echo   - PostgreSQL: Running) else (echo   - PostgreSQL: Not Running)
    netstat -an | findstr :9092 | findstr LISTENING > nul 2>&1
    if !ERRORLEVEL! EQU 0 (echo   - Kafka: Running) else (echo   - Kafka: Not Running)
    node --version > nul 2>&1
    if !ERRORLEVEL! EQU 0 (echo   - Node.js: Installed) else (echo   - Node.js: Not Installed)
    echo.
    echo AGENTS: %HEALTHY%/26 healthy
    echo.
    echo DASHBOARD:
    netstat -an | findstr :5173 | findstr LISTENING > nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        echo   Status: Running
        echo   URL: http://localhost:5173
    ) else (
        echo   Status: Not Running
    )
    echo.
    echo LOG FILES:
    echo   - Master Log: %STARTUP_LOG%
    echo   - Agent Logs: %AGENT_LOG_DIR%\
    echo   - Infrastructure Logs: %INFRASTRUCTURE_LOG_DIR%\
    echo   - Process Tracking: %PROCESS_TRACKING_FILE%
    echo.
    echo ================================================================================
) > "%REPORT_FILE%"

type "%REPORT_FILE%"

echo.
echo [OK] Status report saved: %REPORT_FILE%
echo.

REM ============================================================================
REM FINAL MESSAGE
REM ============================================================================

echo ================================================================================
echo MASTER LAUNCH COMPLETE!
echo ================================================================================
echo.
echo Access Points:
echo   Dashboard:    http://localhost:5173
echo   Primary API:  http://localhost:8000
echo   API Docs:     http://localhost:8000/docs
echo.
echo Logs:
echo   Master Log:   %STARTUP_LOG%
echo   Agent Logs:   %AGENT_LOG_DIR%\
echo   Tracking:     %PROCESS_TRACKING_FILE%
echo.
echo Management:
echo   Stop agents:  stop_all_agents.bat
echo   Check health: python check_all_26_agents_health.py
echo.
echo TIP: Run with -v or --verbose for even more detailed output
echo      Example: master_launch.bat --verbose
echo.
echo ================================================================================
echo.

pause
exit /b 0

REM ============================================================================
REM HELPER FUNCTIONS
REM ============================================================================

:start_agent
set AGENT_FILE=%~1
set AGENT_PORT=%~2
set AGENT_NAME=%~3
set /a AGENT_COUNT+=1

set LOG_FILE=%AGENT_LOG_DIR%\%AGENT_NAME%.log
set PID_FILE=%AGENT_LOG_DIR%\%AGENT_NAME%.pid

echo [%AGENT_COUNT%/26] Starting %AGENT_NAME% on port %AGENT_PORT%...
if "%VERBOSE%"=="1" (
    echo   -^> Command: python agents\%AGENT_FILE%.py
    echo   -^> Port: %AGENT_PORT%
    echo   -^> Log: %LOG_FILE%
)

REM Check if agent file exists
if not exist "agents\%AGENT_FILE%.py" (
    echo [ERROR] Agent file not found: agents\%AGENT_FILE%.py
    echo [%date% %time%] ERROR: Agent file not found: %AGENT_FILE% >> "%STARTUP_LOG%"
    goto :eof
)

set API_PORT=%AGENT_PORT%
if "%VERBOSE%"=="1" echo   -^> Executing: start "%AGENT_NAME% Agent" /B python agents\%AGENT_FILE%.py ^> "%LOG_FILE%" 2^>^&1
start "%AGENT_NAME% Agent" /B python agents\%AGENT_FILE%.py > "%LOG_FILE%" 2>&1

echo   [OK] %AGENT_NAME% started (Port: %AGENT_PORT%)
echo   [OK] Log: %LOG_FILE%
echo [%date% %time%] Started %AGENT_NAME% on port %AGENT_PORT% >> "%STARTUP_LOG%"

REM Wait before starting next agent
timeout /t 2 /nobreak > nul
echo.

goto :eof

:check_agent_health
set PORT=%1

if "%VERBOSE%"=="1" (
    echo [INFO] Checking port %PORT%...
    echo   -^> Running: curl -s -f -m 5 http://localhost:%PORT%/health
)

curl -s -f -m 5 http://localhost:%PORT%/health > "%AGENT_LOG_DIR%\port_%PORT%_health.log" 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Port %PORT% - HEALTHY
    if "%VERBOSE%"=="1" (
        echo   -^> Health response:
        type "%AGENT_LOG_DIR%\port_%PORT%_health.log" | findstr /C:"status" /C:"healthy"
    )
    set /a HEALTHY+=1
    goto :eof
)

REM Health check failed, check if port is listening
netstat -an | findstr :%PORT% | findstr LISTENING > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [WARNING] Port %PORT% - UNHEALTHY (port open but /health failed)
    echo   -^> Port is listening but health check failed
    if "%VERBOSE%"=="1" (
        echo   -^> Error output:
        type "%AGENT_LOG_DIR%\port_%PORT%_health.log" 2>nul
    )
    set /a UNHEALTHY+=1
    goto :eof
)

REM Port not listening
echo [ERROR] Port %PORT% - NOT RUNNING
echo   -^> Port is not listening
echo   -^> Check agent log for details
set /a NOT_RUNNING+=1
goto :eof


:retry_unhealthy_agents
echo.
echo ================================================================================
echo AUTOMATIC AGENT RECOVERY
echo ================================================================================
echo.

REM Create list of unhealthy/not-running ports
set UNHEALTHY_PORTS=

REM Check each port and build list of unhealthy ones
for /L %%p in (8000,1,8025) do (
    curl -s -f -m 5 http://localhost:%%p/health > nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        if defined UNHEALTHY_PORTS (
            set UNHEALTHY_PORTS=!UNHEALTHY_PORTS! %%p
        ) else (
            set UNHEALTHY_PORTS=%%p
        )
    )
)

if not defined UNHEALTHY_PORTS (
    echo [INFO] No unhealthy agents found
    goto :eof
)

echo [INFO] Unhealthy agents on ports: %UNHEALTHY_PORTS%
echo.

REM Retry each unhealthy agent
for %%p in (%UNHEALTHY_PORTS%) do (
    call :retry_single_agent %%p
)

echo.
echo ================================================================================
echo RECOVERY COMPLETE
echo ================================================================================
echo.

REM Re-run health check to get updated counts
set HEALTHY=0
set UNHEALTHY=0
set NOT_RUNNING=0

for /L %%p in (8000,1,8025) do (
    curl -s -f -m 5 http://localhost:%%p/health > nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        set /a HEALTHY+=1
    ) else (
        netstat -an | findstr :%%p | findstr LISTENING > nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            set /a UNHEALTHY+=1
        ) else (
            set /a NOT_RUNNING+=1
        )
    )
)

echo [INFO] Post-Recovery Status:
echo   Healthy:     %HEALTHY%/26
echo   Unhealthy:   %UNHEALTHY%/26
echo   Not Running: %NOT_RUNNING%/26
echo.

goto :eof

:retry_single_agent
set RETRY_PORT=%1
set MAX_RETRIES=3
set RETRY_COUNT=0

echo [INFO] Attempting to recover agent on port %RETRY_PORT%...

:retry_loop
set /a RETRY_COUNT+=1
echo.
echo [INFO] Retry attempt %RETRY_COUNT%/%MAX_RETRIES% for port %RETRY_PORT%...

REM Find and stop the agent process
echo   -^> Stopping agent on port %RETRY_PORT%...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%RETRY_PORT% ^| findstr LISTENING') do (
    taskkill /F /PID %%a > nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        echo   -^> Stopped process PID %%a
    )
)

REM Wait for port to be released
timeout /t 5 /nobreak > nul

REM Find the agent name and file for this port
set AGENT_NAME=
set AGENT_FILE=
if %RETRY_PORT% EQU 8000 (set AGENT_NAME=order& set AGENT_FILE=order_agent_production_v2)
if %RETRY_PORT% EQU 8001 (set AGENT_NAME=product& set AGENT_FILE=product_agent_production)
if %RETRY_PORT% EQU 8002 (set AGENT_NAME=inventory& set AGENT_FILE=inventory_agent)
if %RETRY_PORT% EQU 8003 (set AGENT_NAME=marketplace& set AGENT_FILE=marketplace_connector_agent)
if %RETRY_PORT% EQU 8004 (set AGENT_NAME=payment& set AGENT_FILE=payment_agent_enhanced)
if %RETRY_PORT% EQU 8005 (set AGENT_NAME=dynamic_pricing& set AGENT_FILE=dynamic_pricing_agent)
if %RETRY_PORT% EQU 8006 (set AGENT_NAME=carrier_selection& set AGENT_FILE=carrier_selection_agent)
if %RETRY_PORT% EQU 8007 (set AGENT_NAME=customer& set AGENT_FILE=customer_agent_enhanced)
if %RETRY_PORT% EQU 8008 (set AGENT_NAME=customer_communication& set AGENT_FILE=customer_communication_agent)
if %RETRY_PORT% EQU 8009 (set AGENT_NAME=returns& set AGENT_FILE=returns_agent)
if %RETRY_PORT% EQU 8010 (set AGENT_NAME=fraud_detection& set AGENT_FILE=fraud_detection_agent)
if %RETRY_PORT% EQU 8011 (set AGENT_NAME=recommendation& set AGENT_FILE=recommendation_agent)
if %RETRY_PORT% EQU 8012 (set AGENT_NAME=promotion& set AGENT_FILE=promotion_agent)
if %RETRY_PORT% EQU 8013 (set AGENT_NAME=risk_anomaly& set AGENT_FILE=risk_anomaly_detection_agent)
if %RETRY_PORT% EQU 8014 (set AGENT_NAME=knowledge_management& set AGENT_FILE=knowledge_management_agent)
if %RETRY_PORT% EQU 8015 (set AGENT_NAME=transport& set AGENT_FILE=transport_management_agent_enhanced)
if %RETRY_PORT% EQU 8016 (set AGENT_NAME=warehouse& set AGENT_FILE=warehouse_agent)
if %RETRY_PORT% EQU 8017 (set AGENT_NAME=document& set AGENT_FILE=document_generation_agent)
if %RETRY_PORT% EQU 8018 (set AGENT_NAME=support& set AGENT_FILE=support_agent)
if %RETRY_PORT% EQU 8019 (set AGENT_NAME=d2c_ecommerce& set AGENT_FILE=d2c_ecommerce_agent)
if %RETRY_PORT% EQU 8020 (set AGENT_NAME=after_sales& set AGENT_FILE=after_sales_agent_production)
if %RETRY_PORT% EQU 8021 (set AGENT_NAME=backoffice& set AGENT_FILE=backoffice_agent_production)
if %RETRY_PORT% EQU 8022 (set AGENT_NAME=infrastructure& set AGENT_FILE=infrastructure_agents)
if %RETRY_PORT% EQU 8023 (set AGENT_NAME=ai_monitoring& set AGENT_FILE=ai_monitoring_agent_self_healing)
if %RETRY_PORT% EQU 8024 (set AGENT_NAME=monitoring& set AGENT_FILE=monitoring_agent)
if %RETRY_PORT% EQU 8025 (set AGENT_NAME=quality_control& set AGENT_FILE=quality_control_agent_production)

if not defined AGENT_NAME (
    echo   [ERROR] Unknown port %RETRY_PORT%, cannot restart
    goto :eof
)

REM Restart the agent
echo   -^> Restarting %AGENT_NAME% agent...
set API_PORT=%RETRY_PORT%
set LOG_FILE=%AGENT_LOG_DIR%\%AGENT_NAME%.log
start "%AGENT_NAME% Agent" /B python agents\%AGENT_FILE%.py > "%LOG_FILE%" 2>&1

REM Wait for agent to initialize
echo   -^> Waiting 15 seconds for initialization...
timeout /t 15 /nobreak > nul

REM Check health
curl -s -f -m 5 http://localhost:%RETRY_PORT%/health > nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo   [SUCCESS] Agent %AGENT_NAME% recovered successfully!
    goto :eof
)

REM Check if we should retry
if %RETRY_COUNT% LSS %MAX_RETRIES% (
    echo   [WARNING] Agent still unhealthy, retrying...
    goto :retry_loop
)

REM Failed after all retries
echo.
echo   [ERROR] Failed to recover agent %AGENT_NAME% after %MAX_RETRIES% attempts
echo   [ERROR] Last 50 lines of log file:
echo   ========================================
if exist "%LOG_FILE%" (
    powershell -Command "Get-Content '%LOG_FILE%' -Tail 50 | ForEach-Object { Write-Host '  ' $_ }"
) else (
    echo   [ERROR] Log file not found: %LOG_FILE%
)
echo   ========================================
echo.

goto :eof


