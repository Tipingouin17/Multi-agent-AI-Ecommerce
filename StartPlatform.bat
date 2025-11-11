@echo off
REM ################################################################################
REM Multi-Agent E-commerce Platform - Windows Launcher (Simplified)
REM ################################################################################

setlocal enabledelayedexpansion

set "PROJECT_ROOT=%~dp0"
set "AGENTS_DIR=%PROJECT_ROOT%agents"
set "FRONTEND_DIR=%PROJECT_ROOT%multi-agent-dashboard"
set "LOGS_DIR=%PROJECT_ROOT%logs"

REM Create logs directory if it doesn't exist
if not exist "%LOGS_DIR%\agents" mkdir "%LOGS_DIR%\agents"

cls
echo.
echo ===============================================================================
echo.
echo   Multi-Agent E-commerce Platform - Complete System Launcher
echo.
echo   Starting: PostgreSQL + 37 Agents + Frontend UI
echo.
echo ===============================================================================
echo.

REM ################################################################################
REM STEP 1: Check Prerequisites
REM ################################################################################

echo.
echo ===============================================================================
echo STEP 1: Checking Prerequisites
echo ===============================================================================
echo.

REM Check Python
python --version 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check Node
node --version 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

REM Check npm
call npm --version 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: npm is not installed or not in PATH
    pause
    exit /b 1
)

echo.
echo ✓ All prerequisites checked!
echo.

REM ################################################################################
REM STEP 2: Start Docker Infrastructure
REM ################################################################################

echo.
echo ===============================================================================
echo STEP 2: Starting Docker Infrastructure
echo ===============================================================================
echo.

REM Check if Docker is installed
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker is not installed or not in PATH
    echo.
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

echo ✓ Docker is installed
echo.

REM Check if Docker is running
docker info >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker is not running
    echo.
    echo Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)

echo ✓ Docker is running
echo.

REM Check if PostgreSQL container exists
echo Checking PostgreSQL container...
docker ps -a --filter "name=multi-agent-postgres" --format "{{.Names}}" | findstr /C:"multi-agent-postgres" >nul 2>nul

if %ERRORLEVEL% EQU 0 (
    echo PostgreSQL container exists, checking status...
    
    REM Check if container is running
    docker ps --filter "name=multi-agent-postgres" --format "{{.Names}}" | findstr /C:"multi-agent-postgres" >nul 2>nul
    
    if %ERRORLEVEL% EQU 0 (
        echo ✓ PostgreSQL container is already running
    ) else (
        echo PostgreSQL container is stopped, restarting...
        docker start multi-agent-postgres
        if %ERRORLEVEL% EQU 0 (
            echo ✓ PostgreSQL container restarted successfully
        ) else (
            echo ERROR: Failed to restart PostgreSQL container
            pause
            exit /b 1
        )
    )
) else (
    echo PostgreSQL container does not exist, creating...
    docker run -d --name multi-agent-postgres -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=multi_agent_ecommerce postgres:16
    
    if %ERRORLEVEL% EQU 0 (
        echo ✓ PostgreSQL container created successfully
    ) else (
        echo ERROR: Failed to create PostgreSQL container
        pause
        exit /b 1
    )
)

echo.
echo Waiting for PostgreSQL to be ready...
echo.

REM Wait for PostgreSQL to be healthy (max 60 seconds)
set /a counter=0
:wait_postgres
if %counter% GEQ 60 (
    echo ERROR: PostgreSQL did not become ready within 60 seconds
    pause
    exit /b 1
)

python -c "import psycopg2; conn = psycopg2.connect(host='localhost', port=5432, user='postgres', password='postgres', dbname='postgres'); conn.close()" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ PostgreSQL is ready and accepting connections!
    goto postgres_ready
)

echo Waiting... (%counter%/60 seconds^)
timeout /t 2 /nobreak >nul
set /a counter=%counter%+2
goto wait_postgres

:postgres_ready
echo.
echo ✓ Docker infrastructure is ready!

REM ################################################################################
REM STEP 3: Start All 37 Agents
REM ################################################################################

echo.
echo ===============================================================================
echo STEP 3: Starting All 37 Backend Agents (8 Feature + 29 Core^)
echo ===============================================================================
echo.

if exist "%PROJECT_ROOT%StartAllAgents.bat" (
    echo Launching agents...
    call "%PROJECT_ROOT%StartAllAgents.bat"
    
    echo.
    echo Waiting 10 seconds for agents to initialize...
    timeout /t 10 /nobreak >nul
    
    echo ✓ Agents started!
) else (
    echo ERROR: StartAllAgents.bat not found!
    pause
    exit /b 1
)

REM ################################################################################
REM STEP 4: Start Frontend UI
REM ################################################################################

echo.
echo ===============================================================================
echo STEP 4: Starting Frontend UI
echo ===============================================================================
echo.

if exist "%FRONTEND_DIR%" (
    cd /d "%FRONTEND_DIR%"
    
    REM Check if node_modules exists
    if not exist "node_modules" (
        echo Installing frontend dependencies (this may take a few minutes^)...
        call npm install
    )
    
    echo Starting Vite development server...
    
    REM Start in background
    start /B "" cmd /c "npm run dev > "%LOGS_DIR%\frontend.log" 2>&1"
    
    echo ✓ Frontend started!
    echo   Logs: %LOGS_DIR%\frontend.log
    
    echo.
    echo Waiting 15 seconds for frontend to be ready...
    timeout /t 15 /nobreak >nul
    
    cd /d "%PROJECT_ROOT%"
) else (
    echo ERROR: Frontend directory not found: %FRONTEND_DIR%
    pause
    exit /b 1
)

REM ################################################################################
REM STEP 5: System Status Summary
REM ################################################################################

echo.
echo ===============================================================================
echo SYSTEM STARTUP COMPLETE! 🎉
echo ===============================================================================
echo.
echo ===============================================================================
echo                        ACCESS POINTS
echo ===============================================================================
echo.
echo 📱 User Interfaces:
echo   Frontend UI:         http://localhost:5173
echo   Admin Dashboard:     http://localhost:5173 -^> Select 'Admin Dashboard'
echo   Merchant Portal:     http://localhost:5173 -^> Select 'Merchant Portal'
echo   Customer Portal:     http://localhost:5173 -^> Select 'Customer Portal'
echo.
echo 🔧 Backend Services:
echo   System API Gateway:  http://localhost:8100
echo   API Documentation:   http://localhost:8100/docs
echo   Agent Health:        http://localhost:8100/api/agents
echo.
echo 🗄️  Infrastructure:
echo   PostgreSQL:          localhost:5432 (postgres/postgres^)
echo.
echo ===============================================================================
echo                        SYSTEM STATUS
echo ===============================================================================
echo.
echo   ✓ Backend Agents:        37 agents launched
echo   ✓ Frontend UI:           Running on port 5173
echo.
echo ===============================================================================
echo                        STOP COMMANDS
echo ===============================================================================
echo.
echo   Stop Agents:         StopAllAgents.bat
echo   Stop Everything:     StopPlatform.bat
echo.
echo ===============================================================================
echo                        LOG FILES
echo ===============================================================================
echo.
echo   Agent Logs:          %LOGS_DIR%\agents\
echo   Frontend Log:        %LOGS_DIR%\frontend.log
echo.
echo ===============================================================================
echo.
echo   🚀 Platform is ready! Open http://localhost:5173 to get started!
echo.
echo ===============================================================================
echo.
echo All systems operational!
echo.

REM Open browser automatically
start http://localhost:5173

pause
