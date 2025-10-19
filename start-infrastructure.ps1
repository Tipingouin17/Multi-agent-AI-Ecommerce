#!/usr/bin/env pwsh
# Start Infrastructure Services for Multi-Agent E-commerce System

Write-Host "🚀 Starting Multi-Agent E-commerce Infrastructure..." -ForegroundColor Cyan

# Check Docker is running
Write-Host "`n1. Checking Docker..." -ForegroundColor Yellow
docker ps > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    Write-Host "`nTo fix:" -ForegroundColor Yellow
    Write-Host "  1. Open Docker Desktop" -ForegroundColor Gray
    Write-Host "  2. Wait for Docker to fully start" -ForegroundColor Gray
    Write-Host "  3. Run this script again" -ForegroundColor Gray
    exit 1
}
Write-Host "✓ Docker is running" -ForegroundColor Green

# Check if docker-compose.yml exists
if (!(Test-Path "infrastructure/docker-compose.yml")) {
    Write-Host "❌ infrastructure/docker-compose.yml not found" -ForegroundColor Red
    Write-Host "Please ensure you're in the project root directory" -ForegroundColor Yellow
    exit 1
}

# Start infrastructure services
Write-Host "`n2. Starting infrastructure services..." -ForegroundColor Yellow
docker-compose -f infrastructure/docker-compose.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start infrastructure services" -ForegroundColor Red
    Write-Host "`nCheck Docker logs:" -ForegroundColor Yellow
    Write-Host "  docker-compose -f infrastructure/docker-compose.yml logs" -ForegroundColor Gray
    exit 1
}
Write-Host "✓ Infrastructure services started" -ForegroundColor Green

# Wait for services to be ready
Write-Host "`n3. Waiting for services to be ready (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Verify services
Write-Host "`n4. Verifying services..." -ForegroundColor Yellow

$services = @(
    @{Name="Kafka"; Port=9092; Required=$true},
    @{Name="PostgreSQL"; Port=5432; Required=$true},
    @{Name="Redis"; Port=6379; Required=$false}
)

$allHealthy = $true
foreach ($service in $services) {
    $result = Test-NetConnection -ComputerName localhost -Port $service.Port -WarningAction SilentlyContinue -InformationLevel Quiet
    if ($result.TcpTestSucceeded) {
        Write-Host "✓ $($service.Name) is accessible on port $($service.Port)" -ForegroundColor Green
    } else {
        if ($service.Required) {
            Write-Host "❌ $($service.Name) is NOT accessible on port $($service.Port)" -ForegroundColor Red
            $allHealthy = $false
        } else {
            Write-Host "⚠ $($service.Name) is NOT accessible on port $($service.Port) (optional)" -ForegroundColor Yellow
        }
    }
}

# Final status
Write-Host "`n" + ("="*60) -ForegroundColor Cyan
if ($allHealthy) {
    Write-Host "✅ All infrastructure services are ready!" -ForegroundColor Green
    Write-Host "`nYou can now start the agents with:" -ForegroundColor Cyan
    Write-Host "  .\start-system.ps1" -ForegroundColor White
    Write-Host "`nOr start the dashboard with:" -ForegroundColor Cyan
    Write-Host "  .\start-dashboard.ps1" -ForegroundColor White
} else {
    Write-Host "⚠ Some services are not ready" -ForegroundColor Yellow
    Write-Host "`nTroubleshooting steps:" -ForegroundColor Cyan
    Write-Host "  1. Check Docker logs:" -ForegroundColor Gray
    Write-Host "     docker-compose -f infrastructure/docker-compose.yml logs" -ForegroundColor White
    Write-Host "  2. Restart services:" -ForegroundColor Gray
    Write-Host "     docker-compose -f infrastructure/docker-compose.yml restart" -ForegroundColor White
    Write-Host "  3. See INFRASTRUCTURE_SETUP_GUIDE.md for detailed help" -ForegroundColor Gray
}
Write-Host ("="*60) -ForegroundColor Cyan

