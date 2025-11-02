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
    Write-Host "`n--- Cleaning up running agents and infrastructure ---" -ForegroundColor Yellow
    
    # 1. Stop Docker Compose services
    Write-Host "Stopping Docker Compose services..." -ForegroundColor White
    try {
        docker-compose down --remove-orphans
        Write-Host "Docker Compose services stopped." -ForegroundColor Green
    }
    catch {
        Write-Host "Warning: Could not run 'docker-compose down'. Ensure Docker is running." -ForegroundColor DarkYellow
    }

    # 2. Stop Agent Processes
    if (Test-Path $PIDsFile) {
        $PIDs = Get-Content $PIDsFile
        foreach ($AgentPID in $PIDs) {
            try {
                Stop-Process -Id $AgentPID -Force -ErrorAction Stop
                Write-Host "Stopped process with PID: $AgentPID" -ForegroundColor Green
            }
            catch {
                Write-Host "Process with PID $AgentPID was not running or could not be stopped." -ForegroundColor DarkYellow
            }
        }
        Remove-Item $PIDsFile
    }
    else {
        Write-Host "No PID file found. Searching for agent processes on ports $StartPort-$(($StartPort + $AgentModules.Count - 1))..." -ForegroundColor DarkYellow
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
    
    # 3. Stop UI Process (assuming it was started via Start-Process)
    $UIPIDFile = ".\logs\ui_pid.txt"
    if (Test-Path $UIPIDFile) {
        $UIPID = Get-Content $UIPIDFile
        try {
            Stop-Process -Id $UIPID -Force -ErrorAction Stop
            Write-Host "Stopped UI process with PID: $UIPID" -ForegroundColor Green
        }
        catch {
            Write-Host "UI process with PID $UIPID was not running or could not be stopped." -ForegroundColor DarkYellow
        }
        Remove-Item $UIPIDFile
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

# Use 'up -d' to start services in detached mode
docker-compose up -d postgres kafka redis
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker Compose failed to start services. Check Docker status and docker-compose.yml." -ForegroundColor Red
    exit 1
}

# Robust Check: Wait for containers to be healthy/running
$MaxRetries = 10
$RetryDelay = 5
Write-Host "Waiting for infrastructure containers to be running..." -ForegroundColor Yellow
for ($i = 1; $i -le $MaxRetries; $i++) {
    $RunningContainers = docker-compose ps -q | Measure-Object | Select-Object -ExpandProperty Count
    if ($RunningContainers -ge 3) { # Assuming 3 services: postgres, kafka, redis
        Write-Host "Infrastructure services are running after $($i * $RetryDelay) seconds." -ForegroundColor Green
        break
    }
    if ($i -eq $MaxRetries) {
        Write-Host "ERROR: Infrastructure services did not start within the timeout." -ForegroundColor Red
        docker-compose ps
        exit 1
    }
    Start-Sleep -Seconds $RetryDelay
}

Write-Host "Waiting 15 seconds for services to initialize (e.g., Kafka topics, DB tables)..." -ForegroundColor Yellow
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

# 5. UI Startup
Write-Host "`n--- UI Startup (Vite/npm) ---" -ForegroundColor Yellow
$UIPIDFile = ".\logs\ui_pid.txt"
$UILogFile = Join-Path $LogDir "ui_startup.log"

if (-not (Test-Path ".\ui\package.json")) {
    Write-Host "WARNING: UI directory not found or missing package.json. Skipping UI startup." -ForegroundColor DarkYellow
}
else {
    Write-Host "Starting UI application (npm run dev) on port 5173..." -ForegroundColor White
    
    # Start npm run dev in the background
    $StartCommand = "npm run dev --prefix .\ui"
    
    # Use cmd /c to run npm and redirect output to a log file
    $Process = Start-Process -FilePath "cmd.exe" -ArgumentList "/c $StartCommand > '$UILogFile' 2>&1" -PassThru -NoNewWindow
    
    $Process.Id | Out-File -Append $UIPIDFile
    Write-Host "  -> PID: $($Process.Id). Log: $UILogFile" -ForegroundColor DarkGreen
    
    Write-Host "Waiting 5 seconds for UI to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}

Write-Host "`n================================================================================" -ForegroundColor Cyan
Write-Host "PLATFORM STARTUP FINISHED. All components are running in the background." -ForegroundColor Cyan
Write-Host "To stop all components (Agents, UI, Docker), run: $ProjectRoot\scripts\start_local_dev.ps1 cleanup" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

# The script exits here, but the background processes continue to run.
# The user must manually run the cleanup command to stop them.
