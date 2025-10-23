# Complete Setup and Testing Script for Windows
# 
# This script performs a complete system setup and validation:
# 1. Initializes the database
# 2. Starts all 16 agents
# 3. Runs comprehensive validation tests
# 4. Generates production readiness report

$ErrorActionPreference = "Stop"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Multi-Agent E-commerce System - Complete Setup and Testing" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Get project root
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

# Step 1: Check prerequisites
Write-Host "Step 1: Checking prerequisites..." -ForegroundColor Yellow
Write-Host ""

# Check if PostgreSQL is running
$pgRunning = $false
try {
    $pgTest = Test-NetConnection -ComputerName localhost -Port 5432 -InformationLevel Quiet -WarningAction SilentlyContinue
    if ($pgTest) {
        $pgRunning = $true
        Write-Host "✅ PostgreSQL is running" -ForegroundColor Green
    }
} catch {
    # Ignore error
}

if (-not $pgRunning) {
    Write-Host "❌ PostgreSQL is not running on localhost:5432" -ForegroundColor Red
    Write-Host "Please start PostgreSQL and try again." -ForegroundColor Red
    exit 1
}

# Check if Kafka is running (optional)
$kafkaRunning = $false
try {
    $kafkaTest = Test-NetConnection -ComputerName localhost -Port 9092 -InformationLevel Quiet -WarningAction SilentlyContinue
    if ($kafkaTest) {
        $kafkaRunning = $true
        Write-Host "✅ Kafka is running" -ForegroundColor Green
    }
} catch {
    # Ignore error
}

if (-not $kafkaRunning) {
    Write-Host "⚠️  Kafka is not running on localhost:9092" -ForegroundColor Yellow
    Write-Host "Some features may not work without Kafka." -ForegroundColor Yellow
}

Write-Host ""

# Step 2: Initialize database
Write-Host "Step 2: Initializing database..." -ForegroundColor Yellow
Write-Host ""

python init_database.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Database initialization failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Database initialized" -ForegroundColor Green
Write-Host ""

# Step 3: Stop any running agents
Write-Host "Step 3: Stopping any running agents..." -ForegroundColor Yellow
Write-Host ""

if (Test-Path ".\stop_all_agents.ps1") {
    & .\stop_all_agents.ps1 2>$null
}

Write-Host "✅ Cleanup complete" -ForegroundColor Green
Write-Host ""

# Step 4: Start all agents
Write-Host "Step 4: Starting all 16 agents..." -ForegroundColor Yellow
Write-Host ""

# Start agents in background
$agentJob = Start-Job -ScriptBlock {
    param($root)
    Set-Location $root
    python start_production_system.py
} -ArgumentList $ProjectRoot

# Wait for agents to start
Write-Host "Waiting 15 seconds for agents to initialize..."
Start-Sleep -Seconds 15

# Check if job is still running
$jobState = Get-Job -Id $agentJob.Id | Select-Object -ExpandProperty State
if ($jobState -ne "Running") {
    Write-Host "❌ Agent startup failed" -ForegroundColor Red
    Get-Job -Id $agentJob.Id | Receive-Job
    exit 1
}

Write-Host "✅ Agents started (running in background job)" -ForegroundColor Green
Write-Host ""

# Step 5: Check agent health
Write-Host "Step 5: Checking agent health..." -ForegroundColor Yellow
Write-Host ""

if (Test-Path ".\check_agents_status.ps1") {
    & .\check_agents_status.ps1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Some agents are not healthy" -ForegroundColor Yellow
    } else {
        Write-Host "✅ All agents healthy" -ForegroundColor Green
    }
}

Write-Host ""

# Step 6: Run tests
Write-Host "Step 6: Running comprehensive validation tests..." -ForegroundColor Yellow
Write-Host ""

# Run workflow tests
Write-Host "Running workflow tests..."
python testing/comprehensive_workflow_tests.py

# Run UI tests (if dashboard is running)
$dashboardRunning = $false
try {
    $dashTest = Test-NetConnection -ComputerName localhost -Port 5173 -InformationLevel Quiet -WarningAction SilentlyContinue
    if ($dashTest) {
        $dashboardRunning = $true
    }
} catch {
    # Ignore error
}

if ($dashboardRunning) {
    Write-Host "Running UI tests..."
    python testing/ui_automation_tests.py
} else {
    Write-Host "⚠️  Dashboard not running on port 5173, skipping UI tests" -ForegroundColor Yellow
}

# Run production validation suite
Write-Host "Running production validation suite..."
python testing/production_validation_suite.py

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Setup and Testing Complete!" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test results are available in the test_logs/ directory"
Write-Host ""
Write-Host "To stop all agents:"
Write-Host "  .\stop_all_agents.ps1"
Write-Host ""
Write-Host "To check agent status:"
Write-Host "  .\check_agents_status.ps1"
Write-Host ""
Write-Host "Background agent job ID: $($agentJob.Id)"
Write-Host "To stop the agent job: Stop-Job -Id $($agentJob.Id)"
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan

