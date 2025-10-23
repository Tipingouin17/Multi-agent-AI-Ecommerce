# Start All Agents Script for Windows
# Starts all 16 production-ready agents

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Starting All 16 Production Agents" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Agent configurations: Name, File, Port
$agents = @(
    @{Name="Monitoring"; File="agents/monitoring_agent.py"; Port=8000},
    @{Name="Order"; File="agents/order_agent_production_v2.py"; Port=8001},
    @{Name="Product"; File="agents/product_agent_production.py"; Port=8002},
    @{Name="Marketplace"; File="agents/marketplace_connector_agent.py"; Port=8003},
    @{Name="Customer"; File="agents/customer_agent_enhanced.py"; Port=8004},
    @{Name="Inventory"; File="agents/inventory_agent.py"; Port=8005},
    @{Name="Payment"; File="agents/payment_agent_enhanced.py"; Port=8006},
    @{Name="Transport"; File="agents/transport_agent_production.py"; Port=8007},
    @{Name="Warehouse"; File="agents/warehouse_agent_production.py"; Port=8008},
    @{Name="Document"; File="agents/document_generation_agent.py"; Port=8009},
    @{Name="Fraud"; File="agents/fraud_detection_agent.py"; Port=8010},
    @{Name="Risk"; File="agents/risk_anomaly_detection_agent.py"; Port=8011},
    @{Name="Knowledge"; File="agents/knowledge_management_agent.py"; Port=8012},
    @{Name="After-Sales"; File="agents/after_sales_agent_production.py"; Port=8013},
    @{Name="Backoffice"; File="agents/backoffice_agent_production.py"; Port=8014},
    @{Name="Quality"; File="agents/quality_control_agent_production.py"; Port=8015}
)

# Create logs directory
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

# Start each agent
$jobs = @()
foreach ($agent in $agents) {
    Write-Host "Starting $($agent.Name) Agent on port $($agent.Port)..." -ForegroundColor Yellow
    
    $logFile = "logs/$($agent.Name.ToLower()).log"
    
    # Start agent as background job
    $job = Start-Job -ScriptBlock {
        param($file, $logFile)
        python $file 2>&1 | Tee-Object -FilePath $logFile
    } -ArgumentList $agent.File, $logFile
    
    $jobs += @{Name=$agent.Name; Job=$job; Port=$agent.Port}
    
    Write-Host "✅ $($agent.Name) Agent started (Job ID: $($job.Id))" -ForegroundColor Green
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "All agents started!" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Logs are being written to the logs/ directory"
Write-Host ""
Write-Host "To check agent status:"
Write-Host "  .\check_agents_status.ps1"
Write-Host ""
Write-Host "To stop all agents:"
Write-Host "  .\stop_all_agents.ps1"
Write-Host ""
Write-Host "Job IDs:"
foreach ($jobInfo in $jobs) {
    Write-Host "  $($jobInfo.Name): $($jobInfo.Job.Id)" -ForegroundColor Cyan
}
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan

