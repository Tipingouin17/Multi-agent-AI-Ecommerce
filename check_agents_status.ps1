# Check Agent Status Script for Windows
# Checks if all agents are running and healthy

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Checking Agent Status" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Agent configurations: Name, Port
$agents = @(
    @{Name="Monitoring"; Port=8000},
    @{Name="Order"; Port=8001},
    @{Name="Product"; Port=8002},
    @{Name="Marketplace"; Port=8003},
    @{Name="Customer"; Port=8004},
    @{Name="Inventory"; Port=8005},
    @{Name="Payment"; Port=8006},
    @{Name="Transport"; Port=8007},
    @{Name="Warehouse"; Port=8008},
    @{Name="Document"; Port=8009},
    @{Name="Fraud"; Port=8010},
    @{Name="Risk"; Port=8011},
    @{Name="Knowledge"; Port=8012},
    @{Name="After-Sales"; Port=8013},
    @{Name="Backoffice"; Port=8014},
    @{Name="Quality"; Port=8015}
)

$runningCount = 0
$totalCount = $agents.Count

foreach ($agent in $agents) {
    $status = "❌ NOT RUNNING"
    $color = "Red"
    
    try {
        $test = Test-NetConnection -ComputerName localhost -Port $agent.Port -InformationLevel Quiet -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
        if ($test) {
            # Try to hit health endpoint
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:$($agent.Port)/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
                if ($response.StatusCode -eq 200) {
                    $status = "✅ RUNNING & HEALTHY"
                    $color = "Green"
                    $runningCount++
                } else {
                    $status = "⚠️  RUNNING (health check failed)"
                    $color = "Yellow"
                    $runningCount++
                }
            } catch {
                $status = "⚠️  RUNNING (no health endpoint)"
                $color = "Yellow"
                $runningCount++
            }
        }
    } catch {
        # Port not open
    }
    
    Write-Host ("{0,-20} (Port {1}): {2}" -f $agent.Name, $agent.Port, $status) -ForegroundColor $color
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Summary: $runningCount / $totalCount agents running" -ForegroundColor $(if ($runningCount -eq $totalCount) { "Green" } elseif ($runningCount -gt 0) { "Yellow" } else { "Red" })
Write-Host "================================================================================" -ForegroundColor Cyan

if ($runningCount -lt $totalCount) {
    Write-Host ""
    Write-Host "To start all agents:" -ForegroundColor Yellow
    Write-Host "  .\start_all_agents.ps1" -ForegroundColor Yellow
    exit 1
}

exit 0

