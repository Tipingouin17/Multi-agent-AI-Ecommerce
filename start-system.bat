@echo off
REM Multi-Agent E-commerce System - Complete Startup Script
REM This script starts Docker infrastructure and all agents with unified monitoring

echo ============================================================
echo Multi-Agent E-commerce System - Complete Startup
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then run: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated
echo.

REM Check dependencies
echo Checking Python dependencies...
python -c "import fastapi, uvicorn, pydantic" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Dependencies missing or not installed
    echo Running dependency installer...
    echo.
    call check-and-install-dependencies.bat
    if errorlevel 1 (
        echo [ERROR] Dependency installation failed
        pause
        exit /b 1
    )
) else (
    echo [OK] Dependencies OK
)
echo.

REM Step 1: Check Docker
echo ============================================================
echo Step 1: Checking Docker Services
echo ============================================================
echo.

docker ps >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [OK] Docker is running
echo.

REM Step 2: Start Docker Infrastructure
echo ============================================================
echo Step 2: Starting Docker Infrastructure
echo ============================================================
echo.

cd infrastructure
echo Starting: PostgreSQL, Kafka, Redis, Prometheus, Grafana, Loki...
docker-compose up -d

if errorlevel 1 (
    echo [ERROR] Failed to start Docker services!
    echo Check Docker Desktop and try again.
    cd ..
    pause
    exit /b 1
)

echo [OK] Docker services started
echo.
echo Waiting for services to initialize (15 seconds)...
timeout /t 15 /nobreak >nul
cd ..

REM Step 3: Verify Database Connection
echo ============================================================
echo Step 3: Verifying Database Connection
echo ============================================================
echo.

docker exec multi-agent-postgres psql -U postgres -d multi_agent_ecommerce -c "SELECT 1;" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Database connection failed
    echo Attempting to create database...
    docker exec multi-agent-postgres psql -U postgres -c "CREATE DATABASE multi_agent_ecommerce;" >nul 2>&1
    echo [OK] Database created
) else (
    echo [OK] Database connection successful
)
echo.

REM Step 4: Start All Agents with Unified Monitor
echo ============================================================
echo Step 4: Starting All Agents (Unified Monitor)
echo ============================================================
echo.
echo This will start all 14 agents in one console with color-coded output
echo Press Ctrl+C to stop all agents
echo.
echo Starting in 3 seconds...
timeout /t 3 /nobreak >nul

REM Start the unified monitor
python start-agents-monitor.py

REM Cleanup on exit
echo.
echo ============================================================
echo Shutdown Complete
echo ============================================================
echo.
echo To restart: run start-system.bat
echo To stop Docker: cd infrastructure ^&^& docker-compose down
echo.
pause

