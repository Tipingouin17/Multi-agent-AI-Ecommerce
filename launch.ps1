################################################################################
# Multi-Agent AI E-commerce Platform - Launch Script (Windows)
# 
# This script automates the complete startup process for the multi-agent system.
# It handles infrastructure services, database initialization, and agent launch.
#
# Usage: .\launch.ps1 [-SkipDeps] [-SkipDb] [-Dev] [-Stop] [-Status]
# Options:
#   -SkipDeps     Skip dependency installation
#   -SkipDb       Skip database initialization
#   -Dev          Start with development tools (pgAdmin, Kafka UI)
#   -Stop         Stop all services
#   -Status       Check system status
################################################################################

param(
    [switch]$SkipDeps,
    [switch]$SkipDb,
    [switch]$Dev,
    [switch]$Stop,
    [switch]$Status
)

# Configuration
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPath = Join-Path $ProjectRoot "venv"
$InfrastructurePath = Join-Path $ProjectRoot "infrastructure"

################################################################################
# Helper Functions
################################################################################

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Blue
    Write-Host $Message -ForegroundColor Blue
    Write-Host "========================================" -ForegroundColor Blue
    Write-Host ""
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Cyan
}

function Test-Command {
    param([string]$Command)
    try {
        if (Get-Command $Command -ErrorAction Stop) {
            Write-Success "$Command is installed"
            return $true
        }
    }
    catch {
        Write-Error "$Command is not installed"
        return $false
    }
}

################################################################################
# Stop Services Function
################################################################################

function Stop-Services {
    Write-Header "Stopping Multi-Agent E-commerce System"
    
    Set-Location $InfrastructurePath
    
    if (Test-Command "docker-compose") {
        docker-compose down
    }
    elseif (Test-Command "docker") {
        docker compose down
    }
    else {
        Write-Error "Docker Compose not found"
        exit 1
    }
    
    Write-Success "All services stopped"
    exit 0
}

################################################################################
# Status Check Function
################################################################################

function Check-Status {
    Write-Header "Multi-Agent E-commerce System Status"
    
    Set-Location $InfrastructurePath
    
    if (Test-Command "docker-compose") {
        docker-compose ps
    }
    elseif (Test-Command "docker") {
        docker compose ps
    }
    else {
        Write-Error "Docker Compose not found"
        exit 1
    }
    
    Write-Host ""
    Write-Info "Access Points:"
    Write-Host "  - Grafana Dashboard: http://localhost:3000 (admin/admin123)"
    Write-Host "  - Prometheus: http://localhost:9090"
    Write-Host "  - API Documentation: http://localhost:8000/docs"
    
    if ($Dev) {
        Write-Host "  - Kafka UI: http://localhost:8080"
        Write-Host "  - pgAdmin: http://localhost:5050"
    }
    
    exit 0
}

################################################################################
# Main Launch Process
################################################################################

if ($Stop) {
    Stop-Services
}

if ($Status) {
    Check-Status
}

Write-Header "Multi-Agent AI E-commerce Platform Launcher"

# Step 1: Check Prerequisites
Write-Info "Checking prerequisites..."

$MissingDeps = $false
$MissingDeps = $MissingDeps -or -not (Test-Command "python")
$MissingDeps = $MissingDeps -or -not (Test-Command "docker")
$MissingDeps = $MissingDeps -or -not (Test-Command "git")

if ($MissingDeps) {
    Write-Error "Missing required dependencies. Please install them first."
    exit 1
}

# Check Docker Compose
$DockerComposeCmd = $null
if (Test-Command "docker-compose") {
    $DockerComposeCmd = "docker-compose"
    Write-Success "docker-compose is installed"
}
elseif (Get-Command docker -ErrorAction SilentlyContinue) {
    try {
        docker compose version | Out-Null
        $DockerComposeCmd = "docker compose"
        Write-Success "docker compose (v2) is installed"
    }
    catch {
        Write-Error "Docker Compose not found"
        exit 1
    }
}
else {
    Write-Error "Docker Compose not found"
    exit 1
}

# Step 2: Setup Python Virtual Environment
if (-not $SkipDeps) {
    Write-Header "Setting up Python Environment"
    
    if (-not (Test-Path $VenvPath)) {
        Write-Info "Creating virtual environment..."
        python -m venv $VenvPath
        Write-Success "Virtual environment created"
    }
    else {
        Write-Info "Virtual environment already exists"
    }
    
    Write-Info "Activating virtual environment..."
    & "$VenvPath\Scripts\Activate.ps1"
    
    Write-Info "Installing Python dependencies..."
    python -m pip install --upgrade pip -q
    pip install -r "$ProjectRoot\requirements.txt" -q
    pip install -e $ProjectRoot -q
    Write-Success "Python dependencies installed"
}
else {
    Write-Warning "Skipping dependency installation"
    if (Test-Path $VenvPath) {
        & "$VenvPath\Scripts\Activate.ps1"
    }
}

# Step 3: Check Environment Variables
Write-Header "Checking Configuration"

$EnvFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $EnvFile)) {
    Write-Warning ".env file not found. Creating from template..."
    
    @"
# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=multi_agent_ecommerce
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres123

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis123

# OpenAI API Key (optional - required for AI features)
OPENAI_API_KEY=

# Application Settings
LOG_LEVEL=INFO
ENVIRONMENT=development
"@ | Out-File -FilePath $EnvFile -Encoding UTF8
    
    Write-Success ".env file created"
    Write-Warning "Please edit .env and add your OPENAI_API_KEY if needed"
}
else {
    Write-Success ".env file exists"
}

# Step 4: Start Infrastructure Services
Write-Header "Starting Infrastructure Services"

Set-Location $InfrastructurePath

if ($Dev) {
    Write-Info "Starting services in development mode (with dev tools)..."
    if ($DockerComposeCmd -eq "docker-compose") {
        docker-compose --profile dev up -d
    }
    else {
        docker compose --profile dev up -d
    }
}
else {
    Write-Info "Starting services..."
    if ($DockerComposeCmd -eq "docker-compose") {
        docker-compose up -d
    }
    else {
        docker compose up -d
    }
}

Write-Info "Waiting for services to be ready..."
Start-Sleep -Seconds 10

# Check service health
Write-Info "Checking service health..."
$Retries = 30
$Healthy = $false

for ($i = 1; $i -le $Retries; $i++) {
    $HealthyContainers = docker ps --filter "health=healthy" | Select-String "multi-agent"
    if ($HealthyContainers) {
        $Healthy = $true
        break
    }
    Write-Host "." -NoNewline
    Start-Sleep -Seconds 2
}
Write-Host ""

if ($Healthy) {
    Write-Success "Infrastructure services are healthy"
}
else {
    Write-Warning "Some services may still be starting up"
}

# Step 5: Initialize Database
if (-not $SkipDb) {
    Write-Header "Initializing Database"
    
    Set-Location $ProjectRoot
    
    Write-Info "Creating database schema..."
    python init_database.py
    
    Write-Info "Creating Kafka topics..."
    python init_kafka_topics.py
    
    Write-Success "Database and Kafka initialization complete"
}
else {
    Write-Warning "Skipping database initialization"
}

# Step 6: Display Access Information
Write-Header "Launch Complete!"

Write-Success "Multi-Agent E-commerce System is running"
Write-Host ""
Write-Info "Access Points:"
Write-Host "  - Grafana Dashboard: http://localhost:3000 (admin/admin123)"
Write-Host "  - Prometheus: http://localhost:9090"
Write-Host "  - PostgreSQL: localhost:5432 (postgres/postgres123)"
Write-Host "  - Redis: localhost:6379 (password: redis123)"
Write-Host "  - Kafka: localhost:9092"
Write-Host ""

if ($Dev) {
    Write-Info "Development Tools:"
    Write-Host "  - Kafka UI: http://localhost:8080"
    Write-Host "  - pgAdmin: http://localhost:5050 (admin@multiagent.com/admin123)"
    Write-Host ""
}

Write-Info "Next Steps:"
Write-Host "  1. Start agents: python agents\start_agents.py"
Write-Host "  2. View logs: cd infrastructure; $DockerComposeCmd logs -f"
Write-Host "  3. Check status: .\launch.ps1 -Status"
Write-Host "  4. Stop system: .\launch.ps1 -Stop"
Write-Host ""

Write-Info "For more information, see README.md and COMPLETE_STARTUP_GUIDE.md"

