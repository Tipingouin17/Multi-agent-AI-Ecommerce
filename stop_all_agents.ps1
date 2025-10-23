# Stop All Agents Script for Windows
# Stops all running agent processes

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Stopping All Agents" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Stop all PowerShell jobs running Python agents
$jobs = Get-Job | Where-Object { $_.Command -like "*python*agent*" }

if ($jobs.Count -gt 0) {
    Write-Host "Found $($jobs.Count) agent job(s) running" -ForegroundColor Yellow
    
    foreach ($job in $jobs) {
        Write-Host "Stopping job $($job.Id): $($job.Name)..." -ForegroundColor Yellow
        Stop-Job -Id $job.Id
        Remove-Job -Id $job.Id
        Write-Host "✅ Job $($job.Id) stopped" -ForegroundColor Green
    }
} else {
    Write-Host "No agent jobs found" -ForegroundColor Yellow
}

Write-Host ""

# Kill Python processes on agent ports
$ports = 8000..8015

$processesKilled = 0

foreach ($port in $ports) {
    try {
        $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
        
        foreach ($conn in $connections) {
            $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            
            if ($process -and $process.ProcessName -like "*python*") {
                Write-Host "Stopping Python process on port $port (PID: $($process.Id))..." -ForegroundColor Yellow
                Stop-Process -Id $process.Id -Force
                Write-Host "✅ Process stopped" -ForegroundColor Green
                $processesKilled++
            }
        }
    } catch {
        # Port not in use, continue
    }
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
if ($processesKilled -gt 0) {
    Write-Host "Stopped $processesKilled agent process(es)" -ForegroundColor Green
} else {
    Write-Host "No agent processes were running" -ForegroundColor Yellow
}
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

