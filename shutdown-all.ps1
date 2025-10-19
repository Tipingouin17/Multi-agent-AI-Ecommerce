# Multi-Agent E-commerce System - Complete Shutdown Script
# This script stops all components of the system

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Red
Write-Host "Multi-Agent E-commerce System Shutdown" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""

# Step 1: Stop Python processes (agents)
Write-Host "[1/4] Stopping agent processes..." -ForegroundColor Yellow
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    $pythonProcesses | Stop-Process -Force
    Write-Host "  ✓ Stopped $($pythonProcesses.Count) Python process(es)" -ForegroundColor Green
} else {
    Write-Host "  ℹ No Python processes running" -ForegroundColor Gray
}

# Step 2: Stop Node processes (dashboard)
Write-Host ""
Write-Host "[2/4] Stopping dashboard processes..." -ForegroundColor Yellow
$nodeProcesses = Get-Process node -ErrorAction SilentlyContinue
if ($nodeProcesses) {
    $nodeProcesses | Stop-Process -Force
    Write-Host "  ✓ Stopped $($nodeProcesses.Count) Node process(es)" -ForegroundColor Green
} else {
    Write-Host "  ℹ No Node processes running" -ForegroundColor Gray
}

# Step 3: Stop Docker services
Write-Host ""
Write-Host "[3/4] Stopping Docker services..." -ForegroundColor Yellow
if (Test-Path "infrastructure\docker-compose.yml") {
    Push-Location infrastructure
    docker-compose down
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Docker services stopped" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Failed to stop Docker services" -ForegroundColor Yellow
    }
    Pop-Location
} else {
    Write-Host "  ℹ docker-compose.yml not found" -ForegroundColor Gray
}

# Step 4: Clean up temporary files (optional)
Write-Host ""
Write-Host "[4/4] Cleanup..." -ForegroundColor Yellow
Write-Host "  ℹ Temporary files preserved" -ForegroundColor Gray
Write-Host "  To clean logs, run: Remove-Item -Recurse -Force logs\*" -ForegroundColor Gray

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Red
Write-Host "Shutdown Summary:" -ForegroundColor White
Write-Host "  • Python processes: Stopped" -ForegroundColor Green
Write-Host "  • Node processes: Stopped" -ForegroundColor Green
Write-Host "  • Docker services: Stopped" -ForegroundColor Green
Write-Host ""
Write-Host "PostgreSQL is still running (managed separately)" -ForegroundColor Yellow
Write-Host "To stop PostgreSQL:" -ForegroundColor Gray
Write-Host "  Stop-Service postgresql-x64-14" -ForegroundColor Gray
Write-Host ""
Write-Host "To restart, run: .\launch-all.ps1" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Red
Write-Host "System shutdown complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Red

