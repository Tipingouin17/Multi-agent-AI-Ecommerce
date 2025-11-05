@echo off
REM ============================================================================
REM Multi-Agent E-commerce Platform - Complete System Launcher (Windows)
REM ============================================================================
REM
REM This script launches the ENTIRE platform in the correct order:
REM 1. Docker infrastructure (PostgreSQL, Redis, Kafka, monitoring)
REM 2. Database initialization
REM 3. All 27 backend agents
REM 4. Frontend UI
REM 5. Verification and monitoring setup
REM
REM Usage: start_platform.bat
REM
REM ============================================================================

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set INFRASTRUCTURE_DIR=%SCRIPT_DIR%infrastructure
set FRONTEND_DIR=%SCRIPT_DIR%multi-agent-dashboard
set LOGS_DIR=%SCRIPT_DIR%logs

echo ===============================================================================
echo.
echo   Multi-Agent E-commerce Platform - Complete System Launcher
echo.
echo   Starting: Docker Infrastructure + 27 Agents + Frontend UI
echo.
echo ===============================================================================
echo.

REM ============================================================================
REM STEP 1: Check Prerequisites
REM ============================================================================

echo ===============================================================================
echo STEP 1: Checking Prerequisites
echo ===============================================================================
echo.

where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed or not in PATH
    exit /b 1
)

where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Docker Compose is not installed or not in PATH
    exit /b 1
)

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    exit /b 1
)

where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not in PATH
    exit /b 1
)

echo [OK] Docker installed
echo [OK] Docker Compose installed
echo [OK] Python installed
echo [OK] Node.js installed
echo.

REM ============================================================================
REM STEP 2: Start Docker Infrastructure
REM ============================================================================

echo ===============================================================================
echo STEP 2: Starting Docker Infrastructure
echo ===============================================================================
echo.

cd /d "%INFRASTRUCTURE_DIR%"

echo Starting Docker containers...
docker-compose up -d

echo.
echo Waiting for services to be healthy...
timeout /t 30 /nobreak >nul

echo.
echo Docker infrastructure is ready!
echo.

docker-compose ps

cd /d "%SCRIPT_DIR%"

REM ============================================================================
REM STEP 3: Initialize Database
REM ============================================================================

echo.
echo ===============================================================================
echo STEP 3: Initializing Database
echo ===============================================================================
echo.

if exist "%SCRIPT_DIR%database\schema.sql" (
    echo Importing database schema...
    docker exec -i multi-agent-postgres psql -U postgres -d ecommerce_db < "%SCRIPT_DIR%database\schema.sql"
    echo Database schema imported!
) else (
    echo Warning: database\schema.sql not found, skipping
)

if exist "%SCRIPT_DIR%database\seed_data.sql" (
    echo Importing seed data...
    docker exec -i multi-agent-postgres psql -U postgres -d ecommerce_db < "%SCRIPT_DIR%database\seed_data.sql"
    echo Seed data imported!
)

REM ============================================================================
REM STEP 4: Start All 27 Agents
REM ============================================================================

echo.
echo ===============================================================================
echo STEP 4: Starting All 27 Backend Agents
echo ===============================================================================
echo.

if exist "%SCRIPT_DIR%start_all_agents.bat" (
    echo Launching agents...
    call "%SCRIPT_DIR%start_all_agents.bat"
    
    echo.
    echo Waiting 10 seconds for agents to initialize...
    timeout /t 10 /nobreak >nul
    
    echo Agents started!
) else (
    echo ERROR: start_all_agents.bat not found!
    exit /b 1
)

REM ============================================================================
REM STEP 5: Verify Agent Health
REM ============================================================================

echo.
echo ===============================================================================
echo STEP 5: Verifying Agent Health
echo ===============================================================================
echo.

if exist "%SCRIPT_DIR%check_all_agents.bat" (
    call "%SCRIPT_DIR%check_all_agents.bat"
) else (
    echo Warning: check_all_agents.bat not found, skipping health check
)

REM ============================================================================
REM STEP 6: Start Frontend UI
REM ============================================================================

echo.
echo ===============================================================================
echo STEP 6: Starting Frontend UI
echo ===============================================================================
echo.

if exist "%FRONTEND_DIR%" (
    cd /d "%FRONTEND_DIR%"
    
    if not exist "node_modules" (
        echo Installing frontend dependencies...
        call npm install
    )
    
    echo Starting Vite development server...
    
    REM Start in background
    start /B cmd /c "npm run dev > %LOGS_DIR%\frontend.log 2>&1"
    
    echo Frontend started
    echo Logs: %LOGS_DIR%\frontend.log
    
    echo Waiting for frontend to be ready...
    timeout /t 20 /nobreak >nul
    
    cd /d "%SCRIPT_DIR%"
) else (
    echo ERROR: Frontend directory not found: %FRONTEND_DIR%
)

REM ============================================================================
REM STEP 7: System Status Summary
REM ============================================================================

echo.
echo ===============================================================================
echo.
echo   SYSTEM STARTUP COMPLETE!
echo.
echo ===============================================================================
echo.
echo ACCESS POINTS:
echo.
echo   User Interfaces:
echo     Frontend UI:         http://localhost:5173
echo     Admin Dashboard:     http://localhost:5173 -^> Select 'Admin Dashboard'
echo     Merchant Portal:     http://localhost:5173 -^> Select 'Merchant Portal'
echo     Customer Portal:     http://localhost:5173 -^> Select 'Customer Portal'
echo.
echo   Monitoring ^& Management:
echo     Grafana:             http://localhost:3000 (admin/admin123)
echo     Prometheus:          http://localhost:9090
echo     pgAdmin:             http://localhost:5050
echo     Kafka UI:            http://localhost:8080
echo.
echo   Backend Services:
echo     System API Gateway:  http://localhost:8100
echo     API Documentation:   http://localhost:8100/docs
echo     Agent Health:        http://localhost:8100/api/agents
echo.
echo   Infrastructure:
echo     PostgreSQL:          localhost:5432 (postgres/postgres)
echo     Redis:               localhost:6379
echo     Kafka:               localhost:9092
echo.
echo ===============================================================================
echo.
echo   Platform is ready! Open http://localhost:5173 to get started!
echo.
echo ===============================================================================
echo.
echo STOP COMMANDS:
echo   Stop Agents:         stop_all_agents.bat
echo   Stop Docker:         cd infrastructure ^&^& docker-compose down
echo   Stop Everything:     stop_platform.bat
echo.
echo LOG FILES:
echo   Agent Logs:          %LOGS_DIR%\agents\
echo   Frontend Log:        %LOGS_DIR%\frontend.log
echo   Docker Logs:         cd infrastructure ^&^& docker-compose logs
echo.
echo All systems operational!
echo.

endlocal
