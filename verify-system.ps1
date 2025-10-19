# Multi-Agent E-commerce System Verification Script (PowerShell)
# Comprehensive check of all system components

param(
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"
$script:ErrorCount = 0
$script:WarningCount = 0
$script:SuccessCount = 0

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param([string]$Text)
    Write-Host "✓ " -ForegroundColor Green -NoNewline
    Write-Host $Text
    $script:SuccessCount++
}

function Write-Failure {
    param([string]$Text)
    Write-Host "✗ " -ForegroundColor Red -NoNewline
    Write-Host $Text
    $script:ErrorCount++
}

function Write-Warn {
    param([string]$Text)
    Write-Host "⚠ " -ForegroundColor Yellow -NoNewline
    Write-Host $Text
    $script:WarningCount++
}

function Test-DockerServices {
    Write-Header "Checking Docker Services"
    
    $requiredServices = @(
        "multi-agent-postgres",
        "multi-agent-redis",
        "multi-agent-kafka",
        "multi-agent-zookeeper",
        "multi-agent-prometheus",
        "multi-agent-grafana",
        "multi-agent-loki",
        "multi-agent-promtail",
        "multi-agent-nginx"
    )
    
    try {
        $containers = docker ps --format "{{.Names}}`t{{.Status}}" 2>$null
        
        if ($LASTEXITCODE -ne 0) {
            Write-Failure "Docker is not running or not accessible"
            return $false
        }
        
        $runningContainers = @{}
        foreach ($line in $containers) {
            if ($line -match "^(.+?)`t(.+)$") {
                $runningContainers[$matches[1]] = $matches[2]
            }
        }
        
        $allRunning = $true
        foreach ($service in $requiredServices) {
            if ($runningContainers.ContainsKey($service)) {
                $status = $runningContainers[$service]
                if ($status -match "Up") {
                    Write-Success "$service : $status"
                } else {
                    Write-Failure "$service : $status"
                    $allRunning = $false
                }
            } else {
                Write-Failure "$service : Not running"
                $allRunning = $false
            }
        }
        
        return $allRunning
    } catch {
        Write-Failure "Error checking Docker services: $_"
        return $false
    }
}

function Test-DockerLogs {
    Write-Header "Checking Docker Container Logs for Errors"
    
    $containers = @(
        "multi-agent-postgres",
        "multi-agent-kafka",
        "multi-agent-redis",
        "multi-agent-loki"
    )
    
    $errorPatterns = @("ERROR", "FATAL", "panic", "failed", "cannot", "permission denied")
    
    $allClean = $true
    foreach ($container in $containers) {
        try {
            $logs = docker logs --tail 50 $container 2>&1
            
            $errorsFound = @()
            foreach ($pattern in $errorPatterns) {
                $matches = $logs | Select-String -Pattern $pattern -SimpleMatch
                if ($matches) {
                    $errorsFound += $matches
                }
            }
            
            if ($errorsFound.Count -gt 0) {
                Write-Failure "$container : Found $($errorsFound.Count) error(s) in logs"
                if ($Verbose) {
                    $errorsFound | Select-Object -First 3 | ForEach-Object {
                        Write-Host "  - $_" -ForegroundColor Gray
                    }
                }
                $allClean = $false
            } else {
                Write-Success "$container : No errors in recent logs"
            }
        } catch {
            Write-Warn "$container : Could not retrieve logs"
        }
    }
    
    return $allClean
}

function Test-DatabaseConnection {
    Write-Header "Checking Database Connection"
    
    try {
        $result = docker exec multi-agent-postgres psql -U postgres -d multi_agent_ecommerce -c "SELECT 1;" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "PostgreSQL connection successful"
            return $true
        } else {
            Write-Failure "PostgreSQL connection failed: $result"
            return $false
        }
    } catch {
        Write-Failure "PostgreSQL connection error: $_"
        return $false
    }
}

function Test-RequiredPorts {
    Write-Header "Checking Required Ports"
    
    $requiredPorts = @{
        5432 = "PostgreSQL"
        6379 = "Redis"
        9092 = "Kafka"
        2181 = "Zookeeper"
        9090 = "Prometheus"
        3000 = "Grafana"
        3100 = "Loki"
    }
    
    $allListening = $true
    foreach ($port in $requiredPorts.Keys) {
        $service = $requiredPorts[$port]
        $listening = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        
        if ($listening) {
            Write-Success "Port $port ($service) : Listening"
        } else {
            Write-Failure "Port $port ($service) : Not listening"
            $allListening = $false
        }
    }
    
    return $allListening
}

function Test-AgentProcesses {
    Write-Header "Checking Agent Processes"
    
    $agents = @(
        "order_agent",
        "inventory_agent",
        "product_agent",
        "carrier_selection_agent",
        "warehouse_selection_agent",
        "customer_communication_agent"
    )
    
    $pythonProcesses = Get-Process python* -ErrorAction SilentlyContinue
    
    if (-not $pythonProcesses) {
        Write-Warn "No Python processes detected (agents may not be running)"
        return $false
    }
    
    $runningCount = 0
    foreach ($agent in $agents) {
        $found = $false
        foreach ($proc in $pythonProcesses) {
            if ($proc.CommandLine -like "*$agent*") {
                Write-Success "$agent : Running (PID: $($proc.Id))"
                $runningCount++
                $found = $true
                break
            }
        }
        
        if (-not $found) {
            Write-Warn "$agent : Not detected in process list"
        }
    }
    
    if ($runningCount -eq 0) {
        Write-Warn "No agents appear to be running"
        return $false
    }
    
    return $true
}

function Test-AgentLogs {
    Write-Header "Checking Agent Log Files for Errors"
    
    $logDir = Join-Path $PSScriptRoot "logs"
    
    if (-not (Test-Path $logDir)) {
        Write-Warn "Log directory not found: $logDir"
        return $false
    }
    
    $logFiles = Get-ChildItem -Path $logDir -Filter "*.log" -Recurse -ErrorAction SilentlyContinue
    
    if (-not $logFiles) {
        Write-Warn "No log files found in $logDir"
        return $false
    }
    
    $errorPatterns = @(
        "ERROR",
        "CRITICAL",
        "FATAL",
        "Exception",
        "Traceback",
        "failed",
        "cannot import",
        "ModuleNotFoundError",
        "ImportError",
        "ConnectionError"
    )
    
    $allClean = $true
    foreach ($logFile in $logFiles) {
        try {
            # Read last 100 lines
            $lines = Get-Content $logFile -Tail 100 -ErrorAction Stop
            
            $errorsFound = @()
            foreach ($pattern in $errorPatterns) {
                $matches = $lines | Select-String -Pattern $pattern -SimpleMatch
                if ($matches) {
                    $errorsFound += $matches | Select-Object -First 2
                }
            }
            
            if ($errorsFound.Count -gt 0) {
                Write-Failure "$($logFile.Name) : Found $($errorsFound.Count) error(s)"
                if ($Verbose) {
                    $errorsFound | Select-Object -First 3 | ForEach-Object {
                        $line = $_.Line.Substring(0, [Math]::Min(100, $_.Line.Length))
                        Write-Host "  - $line" -ForegroundColor Gray
                    }
                }
                $allClean = $false
            } else {
                Write-Success "$($logFile.Name) : No errors detected"
            }
        } catch {
            Write-Warn "$($logFile.Name) : Could not read ($_)"
        }
    }
    
    return $allClean
}

function Show-FinalReport {
    Write-Header "System Verification Report"
    
    $totalChecks = 6
    $passedChecks = $script:SuccessCount
    $failedChecks = $script:ErrorCount
    
    Write-Host "Total Checks  : $totalChecks" -ForegroundColor White
    Write-Host "Passed        : " -NoNewline
    Write-Host $passedChecks -ForegroundColor Green
    Write-Host "Failed        : " -NoNewline
    Write-Host $failedChecks -ForegroundColor Red
    Write-Host "Warnings      : " -NoNewline
    Write-Host $script:WarningCount -ForegroundColor Yellow
    
    Write-Host ""
    
    if ($script:ErrorCount -eq 0) {
        Write-Host "============================================================" -ForegroundColor Green
        Write-Host "✓ SYSTEM VERIFICATION PASSED" -ForegroundColor Green
        Write-Host "All components are running without errors!" -ForegroundColor Green
        Write-Host "============================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Your multi-agent e-commerce system is ready for demo!" -ForegroundColor Green
        return $true
    } else {
        Write-Host "============================================================" -ForegroundColor Red
        Write-Host "✗ SYSTEM VERIFICATION FAILED" -ForegroundColor Red
        Write-Host "Please fix the errors above before proceeding" -ForegroundColor Red
        Write-Host "============================================================" -ForegroundColor Red
        return $false
    }
}

# Main execution
Write-Host "Multi-Agent E-commerce System Verification" -ForegroundColor Cyan
Write-Host "Starting comprehensive system check...`n" -ForegroundColor Cyan

$dockerOk = Test-DockerServices
$dockerLogsOk = Test-DockerLogs
$dbOk = Test-DatabaseConnection
$portsOk = Test-RequiredPorts
$agentsOk = Test-AgentProcesses
$agentLogsOk = Test-AgentLogs

$success = Show-FinalReport

if ($success) {
    exit 0
} else {
    exit 1
}

