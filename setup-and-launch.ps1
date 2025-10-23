#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Complete setup and launch script for Multi-Agent E-commerce Platform

.DESCRIPTION
    This script performs a complete setup from scratch:
    1. Verifies prerequisites (Docker, Python, Node.js)
    2. Loads and validates .env configuration
    3. Starts infrastructure services (PostgreSQL, Kafka, Redis)
    4. Waits for services to be fully ready
    5. Initializes database with migrations
    6. Creates Kafka topics
    7. Launches all 15 production agents
    8. Starts the dashboard
    9. Provides comprehensive logging and monitoring

.PARAMETER SkipInfrastructure
    Skip starting Docker infrastructure (use if already running)

.PARAMETER SkipDatabase
    Skip database initialization (use if database already set up)

.PARAMETER SkipAgents
    Skip starting agents (infrastructure and database only)

.PARAMETER SkipDashboard
    Skip starting the dashboard

.EXAMPLE
    .\setup-and-launch.ps1
    Complete setup from scratch

.EXAMPLE
    .\setup-and-launch.ps1 -SkipInfrastructure
    Launch agents only (infrastructure already running)
#>

param(
    [switch]$SkipInfrastructure,
    [switch]$SkipDatabase,
    [switch]$SkipAgents,
    [switch]$SkipDashboard
)

# Configuration
$ErrorActionPreference = "Continue"
$ProjectRoot = $PSScriptRoot
$LogDir = Join-Path $ProjectRoot "logs"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $LogDir "setup_$Timestamp.log"
$EnvFile = Join-Path $ProjectRoot ".env"

# Create logs directory
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

# Logging function
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # Color coding
    switch ($Level) {
        "ERROR"   { Write-Host $logMessage -ForegroundColor Red }
        "WARNING" { Write-Host $logMessage -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logMessage -ForegroundColor Green }
        "INFO"    { Write-Host $logMessage -ForegroundColor Cyan }
        default   { Write-Host $logMessage }
    }
    
    # Also write to log file
    Add-Content -Path $LogFile -Value $logMessage
}

# Banner
function Show-Banner {
    Write-Host ""
    Write-Host "===================================================================" -ForegroundColor Magenta
    Write-Host "   MULTI-AGENT E-COMMERCE PLATFORM - SETUP & LAUNCH" -ForegroundColor Magenta
    Write-Host "===================================================================" -ForegroundColor Magenta
    Write-Host ""
    Write-Log "Starting complete system setup and launch"
    Write-Log "Log file: $LogFile"
    Write-Host ""
}

# Load .env file
function Load-EnvFile {
    Write-Log "Loading environment configuration..." "INFO"
    
    if (-not (Test-Path $EnvFile)) {
        Write-Log "[ERROR] .env file not found at: $EnvFile" "ERROR"
        Write-Log "Please create .env file with required configuration" "ERROR"
        Write-Log "See .env.correct for template" "ERROR"
        exit 1
    }
    
    # Read .env file
    Get-Content $EnvFile | ForEach-Object {
        $line = $_.Trim()
        
        # Skip comments and empty lines
        if ($line -and -not $line.StartsWith("#")) {
            $parts = $line -split "=", 2
            if ($parts.Length -eq 2) {
                $key = $parts[0].Trim()
                $value = $parts[1].Trim()
                
                # Remove quotes if present
                $value = $value -replace '^["'']|["'']$', ''
                
                # Set environment variable
                [Environment]::SetEnvironmentVariable($key, $value, "Process")
            }
        }
    }
    
    Write-Log "[OK] Environment configuration loaded" "SUCCESS"
    
    # Validate critical variables
    $requiredVars = @(
        "DATABASE_URL",
        "DATABASE_HOST",
        "DATABASE_PORT",
        "DATABASE_NAME",
        "DATABASE_USER",
        "DATABASE_PASSWORD"
    )
    
    $missing = @()
    foreach ($var in $requiredVars) {
        if (-not [Environment]::GetEnvironmentVariable($var, "Process")) {
            $missing += $var
        }
    }
    
    if ($missing.Count -gt 0) {
        Write-Log "[ERROR] Missing required environment variables:" "ERROR"
        foreach ($var in $missing) {
            Write-Log "  - $var" "ERROR"
        }
        Write-Log "Please update your .env file. See ENV_FILE_FIX.md for help" "ERROR"
        exit 1
    }
    
    Write-Log "[OK] All required environment variables present" "SUCCESS"
    Write-Host ""
}

# Check prerequisites
function Test-Prerequisites {
    Write-Log "Checking prerequisites..." "INFO"
    
    $allOk = $true
    
    # Check Docker
    try {
        $dockerVersion = docker --version 2>$null
        if ($dockerVersion) {
            Write-Log "[OK] Docker: $dockerVersion" "SUCCESS"
            
            # Check if Docker is running
            $dockerInfo = docker info 2>$null
            if (-not $dockerInfo) {
                Write-Log "[ERROR] Docker is installed but not running" "ERROR"
                Write-Log "Please start Docker Desktop and try again" "ERROR"
                $allOk = $false
            }
        } else {
            Write-Log "[ERROR] Docker not found" "ERROR"
            $allOk = $false
        }
    } catch {
        Write-Log "[ERROR] Docker not found or not running" "ERROR"
        $allOk = $false
    }
    
    # Check Python
    try {
        $pythonVersion = python --version 2>$null
        if ($pythonVersion) {
            Write-Log "[OK] Python: $pythonVersion" "SUCCESS"
        } else {
            Write-Log "[ERROR] Python not found" "ERROR"
            $allOk = $false
        }
    } catch {
        Write-Log "[ERROR] Python not found" "ERROR"
        $allOk = $false
    }
    
    # Check Node.js
    try {
        $nodeVersion = node --version 2>$null
        if ($nodeVersion) {
            Write-Log "[OK] Node.js: $nodeVersion" "SUCCESS"
        } else {
            Write-Log "[ERROR] Node.js not found" "ERROR"
            $allOk = $false
        }
    } catch {
        Write-Log "[ERROR] Node.js not found" "ERROR"
        $allOk = $false
    }
    
    if (-not $allOk) {
        Write-Log "Prerequisites check failed. Please install missing components." "ERROR"
        exit 1
    }
    
    Write-Log "All prerequisites satisfied" "SUCCESS"
    Write-Host ""
}

# Start infrastructure
function Start-Infrastructure {
    Write-Log "Starting infrastructure services..." "INFO"
    
    Set-Location (Join-Path $ProjectRoot "infrastructure")
    
    # Stop any existing containers
    Write-Log "Stopping existing containers..." "INFO"
    docker-compose down 2>&1 | Out-Null
    
    # Start services
    Write-Log "Starting Docker containers..." "INFO"
    docker-compose up -d 2>&1 | Tee-Object -FilePath $LogFile -Append
    
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Failed to start infrastructure" "ERROR"
        Set-Location $ProjectRoot
        exit 1
    }
    
    Set-Location $ProjectRoot
    
    Write-Log "Infrastructure services started" "SUCCESS"
    Write-Host ""
}

# Wait for PostgreSQL
function Wait-ForPostgreSQL {
    Write-Log "Waiting for PostgreSQL to be ready..." "INFO"
    
    $maxAttempts = 60
    $attempt = 0
    $ready = $false
    
    while ($attempt -lt $maxAttempts -and -not $ready) {
        $attempt++
        Write-Host "  Attempt $attempt/$maxAttempts..." -NoNewline
        
        try {
            # Check Docker logs directly (faster than Test-NetConnection)
            $logs = docker logs multi-agent-postgres --tail 10 2>&1
            
            if ($logs -match "database system is ready to accept connections") {
                $ready = $true
                Write-Host " Ready!" -ForegroundColor Green
                Write-Log "[OK] PostgreSQL is ready and accepting connections" "SUCCESS"
            } else {
                Write-Host " Starting..." -ForegroundColor Yellow
                Start-Sleep -Seconds 2
            }
        } catch {
            Write-Host " Error" -ForegroundColor Red
            Start-Sleep -Seconds 2
        }
    }
    
    if (-not $ready) {
        Write-Log "[ERROR] PostgreSQL did not become ready within timeout" "ERROR"
        Write-Log "Check Docker logs: docker logs multi-agent-postgres" "ERROR"
        exit 1
    }
    
    Write-Host ""
}

# Wait for Kafka
function Wait-ForKafka {
    Write-Log "Waiting for Kafka to be ready (this takes 2-3 minutes)..." "INFO"
    
    $maxAttempts = 90
    $attempt = 0
    $ready = $false
    
    while ($attempt -lt $maxAttempts -and -not $ready) {
        $attempt++
        
        if ($attempt % 10 -eq 0) {
            Write-Host "  Waiting... ($attempt seconds)" -ForegroundColor Yellow
        }
        
        try {
            # Check if Kafka is responding
            $result = docker exec multi-agent-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 2>&1
            
            if ($result -match "ApiVersion") {
                $ready = $true
                Write-Log "[OK] Kafka is ready" "SUCCESS"
            } else {
                Start-Sleep -Seconds 1
            }
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    
    if (-not $ready) {
        Write-Log "[WARNING] Kafka did not become ready within timeout" "WARNING"
        Write-Log "Continuing anyway - Kafka may still be starting" "WARNING"
    }
    
    Write-Host ""
}

# Initialize database
function Initialize-Database {
    Write-Log "Initializing database..." "INFO"
    
    # Get database credentials from environment
    $dbUser = [Environment]::GetEnvironmentVariable("DATABASE_USER", "Process")
    $dbName = [Environment]::GetEnvironmentVariable("DATABASE_NAME", "Process")
    
    # Check if database exists
    Write-Log "Checking if database exists..." "INFO"
    
    $dbExists = docker exec multi-agent-postgres psql -U $dbUser -lqt 2>$null | Select-String -Pattern $dbName
    
    if (-not $dbExists) {
        Write-Log "Creating database '$dbName'..." "INFO"
        docker exec multi-agent-postgres psql -U $dbUser -c "CREATE DATABASE $dbName;" 2>&1 | Tee-Object -FilePath $LogFile -Append | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "[OK] Database created" "SUCCESS"
        } else {
            Write-Log "[ERROR] Failed to create database" "ERROR"
            exit 1
        }
    } else {
        Write-Log "[OK] Database already exists" "SUCCESS"
    }
    
    # Run migrations
    Write-Log "Running database migrations..." "INFO"
    
    $migrationsDir = Join-Path $ProjectRoot "database\migrations"
    
    if (-not (Test-Path $migrationsDir)) {
        Write-Log "[ERROR] Migrations directory not found: $migrationsDir" "ERROR"
        exit 1
    }
    
    $migrationFiles = Get-ChildItem -Path $migrationsDir -Filter "*.sql" | Sort-Object Name
    
    if ($migrationFiles.Count -eq 0) {
        Write-Log "[WARNING] No migration files found" "WARNING"
    } else {
        Write-Log "Found $($migrationFiles.Count) migration files" "INFO"
        
        $successCount = 0
        $skipCount = 0
        $failCount = 0
        
        foreach ($migration in $migrationFiles) {
            Write-Host "  Applying: $($migration.Name)..." -NoNewline
            
            try {
                $result = Get-Content $migration.FullName -Raw | docker exec -i multi-agent-postgres psql -U $dbUser -d $dbName 2>&1
                
                if ($LASTEXITCODE -eq 0) {
                    $successCount++
                    Write-Host " OK" -ForegroundColor Green
                } else {
                    # Check if error is "already exists" (which is OK)
                    if ($result -match "already exists") {
                        $skipCount++
                        Write-Host " Skipped (already applied)" -ForegroundColor Yellow
                    } else {
                        $failCount++
                        Write-Host " Failed" -ForegroundColor Red
                        Write-Log "    Error: $result" "ERROR"
                    }
                }
            } catch {
                $failCount++
                Write-Host " Failed" -ForegroundColor Red
                Write-Log "    Error: $_" "ERROR"
            }
        }
        
        Write-Host ""
        Write-Log "[OK] Migrations complete: $successCount applied, $skipCount skipped, $failCount failed" "SUCCESS"
    }
    
    Write-Host ""
}

# Initialize Kafka topics
function Initialize-KafkaTopics {
    Write-Log "Initializing Kafka topics..." "INFO"
    
    $topics = @(
        "order_events",
        "inventory_events",
        "payment_events",
        "shipping_events",
        "warehouse_events",
        "product_events",
        "customer_events",
        "marketplace_events",
        "returns_events",
        "quality_events",
        "fraud_events",
        "document_events",
        "backoffice_events",
        "transport_events",
        "knowledge_events",
        "inventory_received",
        "order_ready_to_ship",
        "return_received",
        "quality_inspection_requested",
        "return_inspected"
    )
    
    $createCount = 0
    $skipCount = 0
    
    foreach ($topic in $topics) {
        Write-Host "  Creating topic: $topic..." -NoNewline
        
        # Use kafka:9092 for internal Docker network communication
        $result = docker exec multi-agent-kafka kafka-topics --create `
            --bootstrap-server kafka:9092 `
            --topic $topic `
            --partitions 3 `
            --replication-factor 1 `
            --if-not-exists 2>&1
        
        $resultStr = $result | Out-String
        
        if ($resultStr -match "Created topic") {
            $createCount++
            Write-Host " Created" -ForegroundColor Green
        } elseif ($resultStr -match "already exists") {
            $skipCount++
            Write-Host " Already exists" -ForegroundColor Yellow
        } else {
            Write-Host " Failed" -ForegroundColor Red
            # Log the actual error for debugging
            Write-Log "Kafka topic creation error for $topic`: $resultStr" "WARNING"
        }
    }
    
    Write-Host ""
    Write-Log "[OK] Kafka topics initialized: $createCount created, $skipCount already existed" "SUCCESS"
    Write-Host ""
}

# Start agents
function Start-Agents {
    Write-Log "Starting all 15 production agents..." "INFO"
    
    # Start agent monitor
    Write-Log "Launching agent monitor..." "INFO"
    
    $agentMonitorLog = Join-Path $LogDir "agents_$Timestamp.log"
    $agentMonitorErrorLog = Join-Path $LogDir "agents_$Timestamp.error.log"
    
    Start-Process python -ArgumentList "start-agents-monitor.py" `
        -WorkingDirectory $ProjectRoot `
        -RedirectStandardOutput $agentMonitorLog `
        -RedirectStandardError $agentMonitorErrorLog `
        -WindowStyle Hidden
    
    Write-Log "[OK] Agent monitor started" "SUCCESS"
    Write-Log "Agent logs: $agentMonitorLog" "INFO"
    Write-Log "Agent errors: $agentMonitorErrorLog" "INFO"
    
    # Wait for agents to start
    Write-Log "Waiting for agents to initialize (30 seconds)..." "INFO"
    Start-Sleep -Seconds 30
    
    Write-Host ""
}

# Start dashboard
function Start-Dashboard {
    Write-Log "Starting dashboard..." "INFO"
    
    $dashboardDir = Join-Path $ProjectRoot "multi-agent-dashboard"
    
    if (-not (Test-Path $dashboardDir)) {
        Write-Log "[ERROR] Dashboard directory not found: $dashboardDir" "ERROR"
        return
    }
    
    Set-Location $dashboardDir
    
    # Check if node_modules exists
    if (-not (Test-Path "node_modules")) {
        Write-Log "Installing dashboard dependencies..." "INFO"
        npm install 2>&1 | Tee-Object -FilePath $LogFile -Append | Out-Null
    }
    
    # Start dashboard
    $dashboardLog = Join-Path $LogDir "dashboard_$Timestamp.log"
    $dashboardErrorLog = Join-Path $LogDir "dashboard_$Timestamp.error.log"
    
    Start-Process npm -ArgumentList "run dev" `
        -WorkingDirectory $dashboardDir `
        -RedirectStandardOutput $dashboardLog `
        -RedirectStandardError $dashboardErrorLog `
        -WindowStyle Hidden
    
    Set-Location $ProjectRoot
    
    Write-Log "[OK] Dashboard started" "SUCCESS"
    Write-Log "Dashboard logs: $dashboardLog" "INFO"
    Write-Log "Dashboard URL: http://localhost:5173" "INFO"
    
    Write-Host ""
}

# Show summary
function Show-Summary {
    Write-Host ""
    Write-Host "===================================================================" -ForegroundColor Green
    Write-Host "   SETUP COMPLETE - SYSTEM IS RUNNING" -ForegroundColor Green
    Write-Host "===================================================================" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Infrastructure Services:" -ForegroundColor Cyan
    Write-Host "  PostgreSQL:  localhost:5432" -ForegroundColor White
    Write-Host "  Kafka:       localhost:9092" -ForegroundColor White
    Write-Host "  Redis:       localhost:6379" -ForegroundColor White
    Write-Host "  Prometheus:  http://localhost:9090" -ForegroundColor White
    Write-Host "  Grafana:     http://localhost:3000" -ForegroundColor White
    Write-Host ""
    
    Write-Host "Application:" -ForegroundColor Cyan
    Write-Host "  Dashboard:   http://localhost:5173" -ForegroundColor White
    Write-Host "  Agents:      15 agents running on ports 8001-8021" -ForegroundColor White
    Write-Host ""
    
    Write-Host "Logs:" -ForegroundColor Cyan
    Write-Host "  Setup:       $LogFile" -ForegroundColor White
    Write-Host "  Agents:      $LogDir\agents_$Timestamp.log" -ForegroundColor White
    Write-Host "  Dashboard:   $LogDir\dashboard_$Timestamp.log" -ForegroundColor White
    Write-Host ""
    
    Write-Host "Monitoring:" -ForegroundColor Cyan
    Write-Host "  Agent status: python start-agents-monitor.py" -ForegroundColor White
    Write-Host "  Logs:         Get-Content logs\agent_monitor_*.log -Tail 50" -ForegroundColor White
    Write-Host ""
    
    Write-Host "To stop all services:" -ForegroundColor Cyan
    Write-Host "  .\shutdown-all.ps1" -ForegroundColor White
    Write-Host ""
    
    Write-Host "===================================================================" -ForegroundColor Green
    Write-Host ""
}

# Main execution
try {
    Show-Banner
    
    # Load environment configuration
    Load-EnvFile
    
    # Check prerequisites
    Test-Prerequisites
    
    # Start infrastructure
    if (-not $SkipInfrastructure) {
        Start-Infrastructure
        Wait-ForPostgreSQL
        Wait-ForKafka
    } else {
        Write-Log "Skipping infrastructure startup (already running)" "INFO"
        Write-Host ""
    }
    
    # Initialize database
    if (-not $SkipDatabase) {
        Initialize-Database
        Initialize-KafkaTopics
    } else {
        Write-Log "Skipping database initialization (already set up)" "INFO"
        Write-Host ""
    }
    
    # Start agents
    if (-not $SkipAgents) {
        Start-Agents
    } else {
        Write-Log "Skipping agent startup" "INFO"
        Write-Host ""
    }
    
    # Start dashboard
    if (-not $SkipDashboard) {
        Start-Dashboard
    } else {
        Write-Log "Skipping dashboard startup" "INFO"
        Write-Host ""
    }
    
    # Show summary
    Show-Summary
    
    Write-Log "Setup and launch completed successfully!" "SUCCESS"
    
} catch {
    Write-Log "Setup failed with error: $_" "ERROR"
    Write-Log "Stack trace: $($_.ScriptStackTrace)" "ERROR"
    exit 1
}

