# Multi-Agent E-commerce System - Complete Launch Script
# This script launches all components of the system

param(
    [switch]$SkipDocker,
    [switch]$SkipDashboard,
    [switch]$AgentsOnly
)

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Multi-Agent E-commerce System Launcher" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Please copy .env.example to .env and configure it." -ForegroundColor Yellow
    Write-Host "  copy .env.example .env" -ForegroundColor White
    exit 1
}

# Step 1: Activate virtual environment
Write-Host "[1/6] Activating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\Activate.ps1") {
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "  ✓ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "  ✗ Virtual environment not found. Creating..." -ForegroundColor Red
    python -m venv venv
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "  Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
}

# Step 2: Check PostgreSQL
Write-Host ""
Write-Host "[2/6] Checking PostgreSQL..." -ForegroundColor Yellow
try {
    $pgCheck = psql -U postgres -d multi_agent_ecommerce -c "SELECT 1;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ PostgreSQL is running and database exists" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Database connection failed" -ForegroundColor Red
        Write-Host "  Please ensure PostgreSQL is running and database is created" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠ Could not verify PostgreSQL (psql not in PATH)" -ForegroundColor Yellow
}

# Step 3: Start Docker services
if (-not $SkipDocker -and -not $AgentsOnly) {
    Write-Host ""
    Write-Host "[3/6] Starting Docker services..." -ForegroundColor Yellow
    if (Test-Path "infrastructure\docker-compose.yml") {
        Push-Location infrastructure
        docker-compose up -d
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Docker services started" -ForegroundColor Green
            Write-Host "  Waiting for services to be ready..." -ForegroundColor Yellow
            Start-Sleep -Seconds 15
        } else {
            Write-Host "  ✗ Failed to start Docker services" -ForegroundColor Red
            Write-Host "  Please ensure Docker Desktop is running" -ForegroundColor Yellow
        }
        Pop-Location
    } else {
        Write-Host "  ⚠ docker-compose.yml not found, skipping" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "[3/6] Skipping Docker services (use -SkipDocker flag)" -ForegroundColor Gray
}

# Step 4: Start agents
Write-Host ""
Write-Host "[4/6] Starting agents..." -ForegroundColor Yellow
if (Test-Path "agents\start_agents.py") {
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "cd '$PWD'; .\venv\Scripts\Activate.ps1; python agents\start_agents.py"
    )
    Write-Host "  ✓ Agents starting in new window" -ForegroundColor Green
} else {
    Write-Host "  ⚠ agents\start_agents.py not found" -ForegroundColor Yellow
    Write-Host "  Trying alternative method..." -ForegroundColor Yellow
    if (Test-Path "start-agents-direct.py") {
        Start-Process powershell -ArgumentList @(
            "-NoExit",
            "-Command",
            "cd '$PWD'; .\venv\Scripts\Activate.ps1; python start-agents-direct.py"
        )
        Write-Host "  ✓ Agents starting in new window" -ForegroundColor Green
    }
}

# Step 5: Start dashboard
if (-not $SkipDashboard -and -not $AgentsOnly) {
    Write-Host ""
    Write-Host "[5/6] Starting dashboard..." -ForegroundColor Yellow
    if (Test-Path "multi-agent-dashboard\package.json") {
        # Check if node_modules exists
        if (-not (Test-Path "multi-agent-dashboard\node_modules")) {
            Write-Host "  Installing dashboard dependencies..." -ForegroundColor Yellow
            Push-Location multi-agent-dashboard
            npm install
            Pop-Location
        }
        
        Start-Process powershell -ArgumentList @(
            "-NoExit",
            "-Command",
            "cd '$PWD\multi-agent-dashboard'; npm run dev"
        )
        Write-Host "  ✓ Dashboard starting in new window" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Dashboard not found, skipping" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "[5/6] Skipping dashboard" -ForegroundColor Gray
}

# Step 6: Summary
Write-Host ""
Write-Host "[6/6] Launch Summary" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services Status:" -ForegroundColor White
Write-Host "  • PostgreSQL: Check manually" -ForegroundColor White
if (-not $SkipDocker -and -not $AgentsOnly) {
    Write-Host "  • Docker Services: Started" -ForegroundColor Green
    Write-Host "    - Kafka: localhost:9092" -ForegroundColor Gray
    Write-Host "    - Redis: localhost:6379" -ForegroundColor Gray
    Write-Host "    - Prometheus: http://localhost:9090" -ForegroundColor Gray
    Write-Host "    - Grafana: http://localhost:3000 (admin/admin123)" -ForegroundColor Gray
}
Write-Host "  • Agents: Starting in separate window" -ForegroundColor Green
if (-not $SkipDashboard -and -not $AgentsOnly) {
    Write-Host "  • Dashboard: Starting in separate window" -ForegroundColor Green
    Write-Host "    - URL: http://localhost:5173" -ForegroundColor Gray
}
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor White
Write-Host "  1. Wait 30 seconds for all services to initialize" -ForegroundColor Gray
Write-Host "  2. Check agent window for startup messages" -ForegroundColor Gray
Write-Host "  3. Open dashboard at http://localhost:5173" -ForegroundColor Gray
Write-Host "  4. Monitor Grafana at http://localhost:3000" -ForegroundColor Gray
Write-Host ""
Write-Host "To stop everything, run: .\shutdown-all.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "System launch initiated successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

