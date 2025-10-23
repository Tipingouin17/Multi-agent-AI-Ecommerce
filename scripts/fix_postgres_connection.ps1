# Quick Fix for PostgreSQL Connection Issues
# Restarts PostgreSQL and ensures it's ready

param(
    [switch]$Force
)

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "PostgreSQL Connection Fix" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if container exists
Write-Host "[1/5] Checking PostgreSQL container..." -ForegroundColor Yellow
$containerExists = docker ps -a --filter "name=multi-agent-postgres" --format "{{.Names}}"

if (-not $containerExists) {
    Write-Host "  [ERROR] PostgreSQL container not found!" -ForegroundColor Red
    Write-Host "  Starting infrastructure..." -ForegroundColor Yellow
    cd infrastructure
    docker-compose up -d postgres
    cd ..
    Start-Sleep -Seconds 10
}

# Step 2: Restart container
Write-Host ""
Write-Host "[2/5] Restarting PostgreSQL container..." -ForegroundColor Yellow
docker restart multi-agent-postgres
Write-Host "  Waiting for PostgreSQL to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Step 3: Wait for PostgreSQL to be ready
Write-Host ""
Write-Host "[3/5] Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$ready = $false

while ($attempt -lt $maxAttempts -and -not $ready) {
    $attempt++
    Write-Host "  Attempt $attempt/$maxAttempts..." -ForegroundColor Gray
    
    $logs = docker logs multi-agent-postgres --tail 5 2>&1
    if ($logs -match "database system is ready to accept connections") {
        $ready = $true
        Write-Host "  [OK] PostgreSQL is ready!" -ForegroundColor Green
    } else {
        Start-Sleep -Seconds 2
    }
}

if (-not $ready) {
    Write-Host "  [WARNING] PostgreSQL did not become ready within timeout" -ForegroundColor Yellow
    Write-Host "  Continuing anyway..." -ForegroundColor Yellow
}

# Step 4: Ensure database exists
Write-Host ""
Write-Host "[4/5] Ensuring database exists..." -ForegroundColor Yellow
$dbExists = docker exec multi-agent-postgres psql -U postgres -lqt 2>&1 | Select-String "multi_agent_ecommerce" -Quiet

if ($dbExists) {
    Write-Host "  [OK] Database 'multi_agent_ecommerce' exists" -ForegroundColor Green
} else {
    Write-Host "  Creating database..." -ForegroundColor Yellow
    docker exec multi-agent-postgres psql -U postgres -c "CREATE DATABASE multi_agent_ecommerce;" 2>&1 | Out-Null
    Write-Host "  [OK] Database created" -ForegroundColor Green
}

# Step 5: Test connection
Write-Host ""
Write-Host "[5/5] Testing connection..." -ForegroundColor Yellow
$testResult = docker exec multi-agent-postgres psql -U postgres -d multi_agent_ecommerce -c "SELECT 1 AS test;" 2>&1

if ($testResult -match "1 row") {
    Write-Host "  [OK] Connection test successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "=" * 80 -ForegroundColor Green
    Write-Host "PostgreSQL is ready and accepting connections!" -ForegroundColor Green
    Write-Host "=" * 80 -ForegroundColor Green
    Write-Host ""
    Write-Host "Connection details:" -ForegroundColor White
    Write-Host "  Host: localhost (or 127.0.0.1)" -ForegroundColor White
    Write-Host "  Port: 5432" -ForegroundColor White
    Write-Host "  Database: multi_agent_ecommerce" -ForegroundColor White
    Write-Host "  User: postgres" -ForegroundColor White
    Write-Host "  Password: postgres" -ForegroundColor White
    Write-Host ""
    Write-Host "You can now run migrations:" -ForegroundColor Yellow
    Write-Host "  python scripts/run_migrations.py" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "  [ERROR] Connection test failed!" -ForegroundColor Red
    Write-Host "  Error: $testResult" -ForegroundColor Red
    Write-Host ""
    Write-Host "Try these steps:" -ForegroundColor Yellow
    Write-Host "  1. Check Docker Desktop is running" -ForegroundColor White
    Write-Host "  2. Check container logs: docker logs multi-agent-postgres" -ForegroundColor White
    Write-Host "  3. Recreate container: docker-compose down && docker-compose up -d" -ForegroundColor White
    exit 1
}

