# Multi-Agent E-commerce System - Complete Startup Script (PowerShell)
# Starts Docker infrastructure and all agents with unified monitoring

param(
    [switch]$SkipDocker,
    [switch]$SkipWait
)

$ErrorActionPreference = "Continue"

function Write-Step {
    param([string]$Text)
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param([string]$Text)
    Write-Host "[OK] " -ForegroundColor Green -NoNewline
    Write-Host $Text
}

function Write-Failure {
    param([string]$Text)
    Write-Host "[ERROR] " -ForegroundColor Red -NoNewline
    Write-Host $Text
}

function Write-Warn {
    param([string]$Text)
    Write-Host "[WARNING] " -ForegroundColor Yellow -NoNewline
    Write-Host $Text
}

# Header
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Multi-Agent E-commerce System - Complete Startup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check virtual environment
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Failure "Virtual environment not found!"
    Write-Host "Please run: python -m venv venv"
    Write-Host "Then run: pip install -r requirements.txt"
    pause
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Gray
& ".\venv\Scripts\Activate.ps1"
Write-Success "Virtual environment activated"
Write-Host ""

# Check dependencies
Write-Host "Checking Python dependencies..." -ForegroundColor Gray
$testImport = python -c "import fastapi, uvicorn, pydantic" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Warn "Dependencies missing or not installed"
    Write-Host "Running dependency installer..." -ForegroundColor Yellow
    Write-Host ""
    & ".\check-and-install-dependencies.ps1"
    if ($LASTEXITCODE -ne 0) {
        Write-Failure "Dependency installation failed"
        pause
        exit 1
    }
} else {
    Write-Success "Dependencies OK"
}
Write-Host ""

# Step 1: Check Docker
if (-not $SkipDocker) {
    Write-Step "Step 1: Checking Docker Services"
    
    try {
        $dockerCheck = docker ps 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Failure "Docker is not running!"
            Write-Host "Please start Docker Desktop and try again."
            pause
            exit 1
        }
        Write-Success "Docker is running"
    } catch {
        Write-Failure "Docker is not installed or not accessible"
        pause
        exit 1
    }
    
    # Step 2: Start Docker Infrastructure
    Write-Step "Step 2: Starting Docker Infrastructure"
    
    Push-Location infrastructure
    Write-Host "Starting: PostgreSQL, Kafka, Redis, Prometheus, Grafana, Loki..." -ForegroundColor Gray
    docker-compose up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Failure "Failed to start Docker services!"
        Write-Host "Check Docker Desktop and try again."
        Pop-Location
        pause
        exit 1
    }
    
    Write-Success "Docker services started"
    Pop-Location
    
    if (-not $SkipWait) {
        Write-Host ""
        Write-Host "Waiting for services to initialize (15 seconds)..." -ForegroundColor Gray
        Start-Sleep -Seconds 15
    }
    
    # Step 3: Verify Database Connection
    Write-Step "Step 3: Verifying Database Connection"
    
    $dbCheck = docker exec multi-agent-postgres psql -U postgres -d multi_agent_ecommerce -c "SELECT 1;" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Database connection failed"
        Write-Host "Attempting to create database..." -ForegroundColor Gray
        docker exec multi-agent-postgres psql -U postgres -c "CREATE DATABASE multi_agent_ecommerce;" 2>&1 | Out-Null
        Write-Success "Database created"
    } else {
        Write-Success "Database connection successful"
    }
} else {
    Write-Host "Skipping Docker startup (--SkipDocker flag)" -ForegroundColor Yellow
}

# Step 4: Start All Agents with Unified Monitor
Write-Step "Step 4: Starting All Agents (Unified Monitor)"

Write-Host "This will start all 14 agents in one console with color-coded output" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop all agents" -ForegroundColor Yellow
Write-Host ""
Write-Host "Starting in 3 seconds..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# Start the unified monitor
python start-agents-monitor.py

# Cleanup on exit
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Shutdown Complete" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To restart: .\start-system.ps1" -ForegroundColor Gray
Write-Host "To stop Docker: cd infrastructure; docker-compose down" -ForegroundColor Gray
Write-Host ""

