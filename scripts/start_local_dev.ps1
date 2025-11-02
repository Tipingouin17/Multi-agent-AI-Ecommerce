# Corrected script to start all multi-agent system components for local development on Windows (PowerShell)

# --- Configuration ---
$AgentModules = @(
    "monitoring_agent",
    "order_agent_production_v2",
    "product_agent_production",
    "inventory_agent",
    "warehouse_agent_production",
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
    "recommendation_agent"
)
$StartPort = 8000
$LogDir = ".\logs\agents"
$PIDsFile = ".\logs\agent_pids.txt"

# --- Functions ---

function Cleanup {
    Write-Host "`n--- Cleaning up running agents ---" -ForegroundColor Yellow
    
    if (Test-Path $PIDsFile) {
        $PIDs = Get-Content $PIDsFile
        foreach ($PID in $PIDs) {
            try {
                Stop-Process -Id $PID -Force -ErrorAction Stop
                Write-Host "Stopped process with PID: $PID" -ForegroundColor Green
            }
            catch {
                Write-Host "Process with PID $PID was not running or could not be stopped." -ForegroundColor DarkYellow
            }
        }
        Remove-Item $PIDsFile
    }
    else {
        Write-Host "No PID file found. Searching for processes on ports $StartPort-$(($StartPort + $AgentModules.Count - 1))..." -ForegroundColor DarkYellow
        # Fallback: Find processes listening on the ports and kill them
        for ($i = 0; $i -lt $AgentModules.Count; $i++) {
            $Port = $StartPort + $i
            $Process = Get-NetTCPConnection -LocalPort $Port -State Listen | Select-Object -ExpandProperty OwningProcess -Unique
            if ($Process) {
                try {
                    Stop-Process -Id $Process -Force -ErrorAction Stop
                    Write-Host "Stopped process on port $Port (PID: $Process)" -ForegroundColor Green
                }
                catch {
                    Write-Host "Could not stop process on port $Port." -ForegroundColor Red
                }
            }
        }
    }
    Write-Host "Cleanup complete." -ForegroundColor Yellow
}

# Check for cleanup argument
if ($args[0] -eq "cleanup") {
    Cleanup
    exit 0
}

# --- Main Execution ---

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "STARTING MULTI-AGENT E-COMMERCE LOCAL ENVIRONMENT (Windows/PowerShell)" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

# 1. Cleanup previous runs
Cleanup

# 2. Set PYTHONPATH
$ProjectRoot = Get-Location
$env:PYTHONPATH = "$env:PYTHONPATH;$ProjectRoot"
Write-Host "PYTHONPATH set to include project root: $ProjectRoot" -ForegroundColor Green

# 3. Infrastructure Startup (Docker Compose)
Write-Host "`n--- Infrastructure Startup (Docker Compose) ---" -ForegroundColor Yellow

# Check if Docker Compose is available
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: 'docker-compose' command not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

Write-Host "Starting PostgreSQL, Kafka, and Redis via Docker Compose..." -ForegroundColor White
try {
    # Use 'up -d' to start services in detached mode
    docker-compose up -d postgres kafka redis
    Write-Host "Infrastructure services started successfully." -ForegroundColor Green
}
catch {
    Write-Host "ERROR: Failed to start infrastructure services with Docker Compose." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host "Waiting 15 seconds for infrastructure to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# 4. Agent Startup
Write-Host "`n--- Starting Agents (Ports $StartPort to $(($StartPort + $AgentModules.Count - 1))) ---" -ForegroundColor Yellow
if (-not (Test-Path $LogDir)) {
    New-Item -Path $LogDir -ItemType Directory | Out-Null
}

# Clear PIDs file
Clear-Content $PIDsFile

for ($i = 0; $i -lt $AgentModules.Count; $i++) {
    $Module = $AgentModules[$i]
    $Port = $StartPort + $i
    $AgentName = $Module -replace "_agent.*"
    $ModulePath = "agents.$Module`:app"
    $LogFile = Join-Path $LogDir "$AgentName.log"
    
    Write-Host "Starting $AgentName Agent on port $Port..." -ForegroundColor White
    
    # Start uvicorn in a new process, redirecting output to a log file
    # -NoNewWindow is used to keep the process in the background
    # Start-Process is used to run the command asynchronously
    $StartCommand = "python -m uvicorn $ModulePath --host 0.0.0.0 --port $Port --log-level debug"
    
    $Process = Start-Process -FilePath "powershell.exe" -ArgumentList "-Command `"$StartCommand > '$LogFile' 2>&1`"" -PassThru -NoNewWindow
    
    $Process.Id | Out-File -Append $PIDsFile
    Write-Host "  -> PID: $($Process.Id). Log: $LogFile" -ForegroundColor DarkGreen
}

Write-Host "`n--- Agent Startup Complete ---" -ForegroundColor Yellow
Write-Host "All agents are running in the background. Check logs in $LogDir" -ForegroundColor Yellow
Write-Host "Waiting 10 seconds for agents to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 5. UI Startup (Placeholder)
Write-Host "`n--- UI Startup (Placeholder) ---" -ForegroundColor Yellow
Write-Host "INFO: Assuming UI is started via 'npm run dev' or similar on port 5173." -ForegroundColor Yellow
Write-Host "INFO: Skipping UI startup as it is external to this script." -ForegroundColor Yellow

Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "PLATFORM STARTUP FINISHED. Agents are running in the background." -ForegroundColor Cyan
Write-Host "To stop all agents, run: $ProjectRoot\scripts\start_local_dev.ps1 cleanup" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

# The script exits here, but the background processes continue to run.
# The user must manually run the cleanup command to stop them.
