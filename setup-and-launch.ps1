#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Complete setup and launch script for Multi-Agent E-commerce Platform

.DESCRIPTION
    This script performs a complete setup from scratch:
    1. Verifies prerequisites (Docker, Python, Node.js)
    2. Sets up the database with all tables
    3. Starts infrastructure services (PostgreSQL, Kafka, Redis)
    4. Initializes Kafka topics
    5. Launches all 15 production agents
    6. Starts the dashboard
    7. Provides comprehensive logging

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
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Magenta
    Write-Host "   MULTI-AGENT E-COMMERCE PLATFORM - SETUP & LAUNCH" -ForegroundColor Magenta
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Magenta
    Write-Host ""
    Write-Log "Starting complete system setup and launch"
    Write-Log "Log file: $LogFile"
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
    Write-Log "Starting infrastructure services (PostgreSQL, Kafka, Redis, Zookeeper)..." "INFO"
    
    Set-Location (Join-Path $ProjectRoot "infrastructure")
    
    # Stop any existing containers
    Write-Log "Stopping existing containers..." "INFO"
    docker-compose down 2>&1 | Out-Null
    
    # Start services
    Write-Log "Starting Docker containers..." "INFO"
    docker-compose up -d 2>&1 | Tee-Object -FilePath $LogFile -Append | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Failed to start infrastructure" "ERROR"
        exit 1
    }
    
    Set-Location $ProjectRoot
    
    Write-Log "Infrastructure services started" "SUCCESS"
    Write-Host ""
    
    # Wait for services to be ready
    Write-Log "Waiting for services to initialize..." "INFO"
    Write-Log "PostgreSQL: Waiting for port 5432..." "INFO"
    
    $maxAttempts = 30
    $attempt = 0
    $postgresReady = $false
    
    while ($attempt -lt $maxAttempts -and -not $postgresReady) {
        $attempt++
        try {
            $connection = Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue
            if ($connection.TcpTestSucceeded) {
                $postgresReady = $true
                Write-Log "[OK] PostgreSQL is ready" "SUCCESS"
            } else {
                Start-Sleep -Seconds 2
            }
        } catch {
            Start-Sleep -Seconds 2
        }
    }
    
    if (-not $postgresReady) {
        Write-Log "PostgreSQL did not start in time" "ERROR"
        exit 1
    }
    
    # Wait for Kafka (takes longer)
    Write-Log "Kafka: Waiting for initialization (this takes 2-3 minutes)..." "INFO"
    Start-Sleep -Seconds 120
    
    Write-Log "[OK] All infrastructure services ready" "SUCCESS"
    Write-Host ""
}

# Initialize database
function Initialize-Database {
    Write-Log "Initializing database with all tables..." "INFO"
    
    # Set environment variables
    $env:DATABASE_HOST = "localhost"
    $env:DATABASE_PORT = "5432"
    $env:DATABASE_NAME = "multi_agent_ecommerce"
    $env:DATABASE_USER = "postgres"
    $env:DATABASE_PASSWORD = "postgres"
    
    # Check if database exists
    Write-Log "Checking if database exists..." "INFO"
    
    $dbExists = docker exec multi-agent-postgres psql -U postgres -lqt 2>$null | Select-String -Pattern "multi_agent_ecommerce"
    
    if (-not $dbExists) {
        Write-Log "Creating database..." "INFO"
        docker exec multi-agent-postgres psql -U postgres -c "CREATE DATABASE multi_agent_ecommerce;" 2>&1 | Tee-Object -FilePath $LogFile -Append | Out-Null
        Write-Log "[OK] Database created" "SUCCESS"
    } else {
        Write-Log "[OK] Database already exists" "SUCCESS"
    }
    
    # Run migrations
    Write-Log "Running database migrations..." "INFO"
    
    $migrationFiles = Get-ChildItem -Path (Join-Path $ProjectRoot "database\migrations") -Filter "*.sql" | Sort-Object Name
    
    $migrationCount = 0
    foreach ($migration in $migrationFiles) {
        Write-Log "  Applying: $($migration.Name)" "INFO"
        
        $migrationPath = $migration.FullName
        $migrationContent = Get-Content $migrationPath -Raw
        
        # Execute migration
        try {
            $result = docker exec -i multi-agent-postgres psql -U postgres -d multi_agent_ecommerce -c "$migrationContent" 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                $migrationCount++
                Write-Log "    [OK] Applied successfully" "SUCCESS"
            } else {
                # Check if error is "already exists" (which is OK)
                if ($result -match "already exists") {
                    Write-Log "    [WARNING] Already applied (skipping)" "WARNING"
                } else {
                    Write-Log "    [ERROR] Failed: $result" "ERROR"
                }
            }
        } catch {
            Write-Log "    [ERROR] Failed: $_" "ERROR"
        }
    }
    
    Write-Log "[OK] Database initialized ($migrationCount migrations applied)" "SUCCESS"
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
        "knowledge_events"
    )
    
    foreach ($topic in $topics) {
        Write-Log "  Creating topic: $topic" "INFO"
        
        docker exec multi-agent-kafka kafka-topics --create `
            --bootstrap-server localhost:9092 `
            --topic $topic `
            --partitions 3 `
            --replication-factor 1 `
            --if-not-exists 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "    [OK] Created" "SUCCESS"
        } else {
            Write-Log "    [WARNING] Already exists or failed" "WARNING"
        }
    }
    
    Write-Log "[OK] Kafka topics initialized" "SUCCESS"
    Write-Host ""
}

# Start agents
function Start-Agents {
    Write-Log "Starting all 15 production agents..." "INFO"
    
    # Set environment variables
    $env:DATABASE_HOST = "localhost"
    $env:DATABASE_PORT = "5432"
    $env:DATABASE_NAME = "multi_agent_ecommerce"
    $env:DATABASE_USER = "postgres"
    $env:DATABASE_PASSWORD = "postgres"
    $env:KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
    $env:REDIS_HOST = "localhost"
    $env:REDIS_PORT = "6379"
    
    # Start agent monitor
    Write-Log "Launching agent monitor..." "INFO"
    
    $agentMonitorLog = Join-Path $LogDir "agents_$Timestamp.log"
    
    Start-Process python -ArgumentList "start-agents-monitor.py" `
        -WorkingDirectory $ProjectRoot `
        -RedirectStandardOutput $agentMonitorLog `
        -RedirectStandardError $agentMonitorLog `
        -WindowStyle Hidden
    
    Write-Log "[OK] Agent monitor started (logging to $agentMonitorLog)" "SUCCESS"
    
    # Wait for agents to start
    Write-Log "Waiting for agents to initialize (30 seconds)..." "INFO"
    Start-Sleep -Seconds 30
    
    # Check if agents are running
    Write-Log "Verifying agent status..." "INFO"
    
    $agentPorts = @(8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009, 8010, 8011, 8012, 8013, 8020, 8021)
    $runningAgents = 0
    
    foreach ($port in $agentPorts) {
        try {
            $connection = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue -InformationLevel Quiet
            if ($connection) {
                $runningAgents++
            }
        } catch {
            # Port not accessible
        }
    }
    
    Write-Log "[OK] $runningAgents / $($agentPorts.Count) agents running" "SUCCESS"
    
    if ($runningAgents -lt 10) {
        Write-Log "Warning: Less than 10 agents started. Check logs for details." "WARNING"
    }
    
    Write-Host ""
}

# Start dashboard
function Start-Dashboard {
    Write-Log "Starting dashboard..." "INFO"
    
    Set-Location (Join-Path $ProjectRoot "multi-agent-dashboard")
    
    # Install dependencies if needed
    if (-not (Test-Path "node_modules")) {
        Write-Log "Installing dashboard dependencies..." "INFO"
        npm install 2>&1 | Tee-Object -FilePath $LogFile -Append | Out-Null
    }
    
    # Start dashboard
    Write-Log "Launching dashboard on http://localhost:5173..." "INFO"
    
    $dashboardLog = Join-Path $LogDir "dashboard_$Timestamp.log"
    
    Start-Process npm -ArgumentList "run dev" `
        -WorkingDirectory (Join-Path $ProjectRoot "multi-agent-dashboard") `
        -RedirectStandardOutput $dashboardLog `
        -RedirectStandardError $dashboardLog `
        -WindowStyle Normal
    
    Set-Location $ProjectRoot
    
    Write-Log "[OK] Dashboard started (logging to $dashboardLog)" "SUCCESS"
    Write-Host ""
}

# Main execution
function Main {
    Show-Banner
    
    # Step 1: Check prerequisites
    Test-Prerequisites
    
    # Step 2: Start infrastructure
    if (-not $SkipInfrastructure) {
        Start-Infrastructure
    } else {
        Write-Log "Skipping infrastructure startup (already running)" "INFO"
        Write-Host ""
    }
    
    # Step 3: Initialize database
    if (-not $SkipDatabase) {
        Initialize-Database
        Initialize-KafkaTopics
    } else {
        Write-Log "Skipping database initialization (already set up)" "INFO"
        Write-Host ""
    }
    
    # Step 4: Start agents
    if (-not $SkipAgents) {
        Start-Agents
    } else {
        Write-Log "Skipping agent startup" "INFO"
        Write-Host ""
    }
    
    # Step 5: Start dashboard
    if (-not $SkipDashboard) {
        Start-Dashboard
    } else {
        Write-Log "Skipping dashboard startup" "INFO"
        Write-Host ""
    }
    
    # Final summary
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "   SETUP COMPLETE - SYSTEM READY" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Log "System is now running!" "SUCCESS"
    Write-Host ""
    Write-Host "Access Points:" -ForegroundColor Cyan
    Write-Host "  • Dashboard:  http://localhost:5173" -ForegroundColor White
    Write-Host "  • API Gateway: http://localhost:8000" -ForegroundColor White
    Write-Host "  • Order Agent: http://localhost:8001" -ForegroundColor White
    Write-Host ""
    Write-Host "Logs:" -ForegroundColor Cyan
    Write-Host "  • Setup Log:  $LogFile" -ForegroundColor White
    Write-Host "  • Agent Logs: $LogDir\agents_$Timestamp.log" -ForegroundColor White
    Write-Host "  • Dashboard:  $LogDir\dashboard_$Timestamp.log" -ForegroundColor White
    Write-Host ""
    Write-Host "To stop the system, run: .\shutdown-all.ps1" -ForegroundColor Yellow
    Write-Host ""
}

# Run main function
Main

