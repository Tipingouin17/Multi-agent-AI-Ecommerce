# Multi-Agent E-Commerce System - Full Production Startup Script
# This script starts ALL 26 production-ready agents

param(
    [string]$Action = ""
)

# --- Configuration ---
$AgentModules = @(
    "monitoring_agent",
    "order_agent_production_v2",
    "product_agent_production",
    "inventory_agent",
    "warehouse_agent",
    "payment_agent_enhanced",
    "transport_management_agent_enhanced",
    "marketplace_connector_agent",
    "customer_agent_enhanced",
    "fraud_detection_agent",
    "risk_anomaly_detection_agent",
    "backoffice_agent_production",
    "knowledge_management_agent",
    "quality_control_agent_production",
    "promotion_agent",
    "recommendation_agent",
    "after_sales_agent_production",
    "support_agent",
    "returns_agent",
    "document_generation_agent",
    "customer_communication_agent",
    "carrier_selection_agent",
    "dynamic_pricing_agent",
    "d2c_ecommerce_agent",
    "ai_monitoring_agent_self_healing",
    "infrastructure_agents"
)
$StartPort = 8000
$LogDir = ".\logs\agents"
$PIDsFile = ".\logs\agent_pids.txt"

# --- Cleanup Function ---

if ($Action -eq "cleanup") {
    Write-Host "`n--- Cleanup Mode ---" -ForegroundColor Yellow
    
    # Kill all agent processes
    if (Test-Path $PIDsFile) {
        Write-Host "Stopping all agents..." -ForegroundColor White
        Get-Content $PIDsFile | ForEach-Object {
            try {
                Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
                Write-Host "  Stopped PID: $_" -ForegroundColor DarkGreen
            } catch {
                Write-Host "  Could not stop PID: $_" -ForegroundColor DarkRed
            }
        }
        Remove-Item $PIDsFile
    }
    
    # Clean log files
    if (Test-Path $LogDir) {
        Write-Host "Cleaning log files..." -ForegroundColor White
        Remove-Item "$LogDir\*.log" -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host "`nCleanup complete!" -ForegroundColor Green
    exit 0
}

# --- Startup ---
Write-Host "`n=== Multi-Agent E-Commerce System - Full Production Startup ===" -ForegroundColor Cyan
Write-Host "Starting $($AgentModules.Count) agents..." -ForegroundColor White
Write-Host ""

# Create log directory if it doesn't exist
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

# Clear PID file
if (Test-Path $PIDsFile) {
    Remove-Item $PIDsFile
}

# --- Docker Infrastructure ---
Write-Host "--- Infrastructure (Docker Compose) ---" -ForegroundColor Yellow
Write-Host "Starting PostgreSQL, Kafka, Redis, Zookeeper..." -ForegroundColor White

$DockerComposeFile = ".\infrastructure\docker-compose.yml"
if (Test-Path $DockerComposeFile) {
    docker compose -f $DockerComposeFile up -d
    Write-Host "  -> Infrastructure started. Waiting 10 seconds for services to be ready..." -ForegroundColor DarkGreen
    Start-Sleep -Seconds 10
} else {
    Write-Host "  -> WARNING: Docker Compose file not found. Skipping infrastructure startup." -ForegroundColor DarkYellow
}

Write-Host ""

# --- Agent Startup ---
Write-Host "--- Agent Startup ---" -ForegroundColor Yellow

for ($i = 0; $i -lt $AgentModules.Count; $i++) {
    $Module = $AgentModules[$i]
    $Port = $StartPort + $i
    $AgentName = $Module -replace "_agent.*"
    $ModulePath = "agents.$Module`:app"
    $LogFile = Join-Path $LogDir "$AgentName.log"
    
    Write-Host "Starting $AgentName Agent on port $Port..." -ForegroundColor White
    
    # Start uvicorn in a new process, redirecting output to a log file
    $StartCommand = "python -m uvicorn $ModulePath --host 0.0.0.0 --port $Port --log-level debug"
    
    $Process = Start-Process -FilePath "powershell.exe" -ArgumentList "-Command `"$StartCommand > '$LogFile' 2>&1`"" -PassThru -NoNewWindow
    
    $Process.Id | Out-File -Append $PIDsFile
    Write-Host "  -> PID: $($Process.Id). Log: $LogFile" -ForegroundColor DarkGreen
}

Write-Host "`n--- Agent Startup Complete ---" -ForegroundColor Yellow
Write-Host "All $($AgentModules.Count) agents are starting up. Check logs in $LogDir for details." -ForegroundColor White
Write-Host "`nWaiting 15 seconds for agents to initialize..." -ForegroundColor White
Start-Sleep -Seconds 15

# --- UI Startup (Vite/npm) ---
Write-Host "`n--- UI Startup (Vite/npm) ---" -ForegroundColor Yellow
Write-Host "Starting UI application (npm run dev) on port 5173..." -ForegroundColor White

$UIDir = ".\ui"
$UILogFile = Join-Path $LogDir "ui_startup.log"

if (Test-Path $UIDir) {
    $UICommand = "Set-Location '$UIDir'; npm run dev"
    $UIProcess = Start-Process -FilePath "powershell.exe" -ArgumentList "-Command `"$UICommand > '$UILogFile' 2>&1`"" -PassThru -NoNewWindow
    $UIProcess.Id | Out-File -Append $PIDsFile
    Write-Host "  -> PID: $($UIProcess.Id). Log: $UILogFile" -ForegroundColor DarkGreen
    Write-Host "Waiting 5 seconds for UI to start..." -ForegroundColor White
    Start-Sleep -Seconds 5
} else {
    Write-Host "  -> WARNING: UI directory not found. Skipping UI startup." -ForegroundColor DarkYellow
}

Write-Host "`n=== System Startup Complete ===" -ForegroundColor Green
Write-Host "Access the UI at: http://localhost:5173" -ForegroundColor Cyan
Write-Host "Agent APIs are available on ports $StartPort-$($StartPort + $AgentModules.Count - 1)" -ForegroundColor Cyan
Write-Host "`nTo stop all agents, run: .\scripts\start_local_dev_FULL.ps1 cleanup" -ForegroundColor White
Write-Host ""

