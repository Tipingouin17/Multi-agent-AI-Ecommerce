# PostgreSQL Connection Diagnostic Script
# Checks PostgreSQL Docker container and connection

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "PostgreSQL Connection Diagnostic" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "[1/7] Checking Docker status..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "  [OK] Docker is running: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Docker is not running!" -ForegroundColor Red
    Write-Host "  Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Check PostgreSQL container
Write-Host ""
Write-Host "[2/7] Checking PostgreSQL container..." -ForegroundColor Yellow
$pgContainer = docker ps -a --filter "name=multi-agent-postgres" --format "{{.Names}}\t{{.Status}}\t{{.Ports}}"

if ($pgContainer) {
    Write-Host "  Container found:" -ForegroundColor Green
    Write-Host "  $pgContainer" -ForegroundColor White
    
    # Check if container is running
    $isRunning = docker ps --filter "name=multi-agent-postgres" --format "{{.Names}}"
    if ($isRunning) {
        Write-Host "  [OK] Container is running" -ForegroundColor Green
    } else {
        Write-Host "  [WARNING] Container exists but is not running" -ForegroundColor Yellow
        Write-Host "  Attempting to start..." -ForegroundColor Yellow
        docker start multi-agent-postgres
        Start-Sleep -Seconds 5
    }
} else {
    Write-Host "  [ERROR] PostgreSQL container not found!" -ForegroundColor Red
    Write-Host "  Run: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

# Check container logs
Write-Host ""
Write-Host "[3/7] Checking PostgreSQL logs..." -ForegroundColor Yellow
$logs = docker logs multi-agent-postgres --tail 20 2>&1
if ($logs -match "database system is ready to accept connections") {
    Write-Host "  [OK] PostgreSQL is ready" -ForegroundColor Green
} elseif ($logs -match "starting") {
    Write-Host "  [WARNING] PostgreSQL is still starting up" -ForegroundColor Yellow
    Write-Host "  Waiting 10 seconds..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
} else {
    Write-Host "  [WARNING] Could not confirm PostgreSQL status from logs" -ForegroundColor Yellow
    Write-Host "  Last 5 log lines:" -ForegroundColor White
    $logs | Select-Object -Last 5 | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
}

# Check port 5432
Write-Host ""
Write-Host "[4/7] Checking port 5432..." -ForegroundColor Yellow
$portCheck = netstat -an | Select-String "0.0.0.0:5432" -Quiet
if ($portCheck) {
    Write-Host "  [OK] Port 5432 is listening" -ForegroundColor Green
} else {
    Write-Host "  [WARNING] Port 5432 is not listening" -ForegroundColor Yellow
    
    # Check if port is mapped correctly
    $portMapping = docker port multi-agent-postgres 5432 2>&1
    if ($portMapping) {
        Write-Host "  Port mapping: $portMapping" -ForegroundColor White
    } else {
        Write-Host "  [ERROR] Port 5432 is not mapped!" -ForegroundColor Red
    }
}

# Test connection with psql
Write-Host ""
Write-Host "[5/7] Testing PostgreSQL connection..." -ForegroundColor Yellow
$testConnection = docker exec multi-agent-postgres psql -U postgres -d multi_agent_ecommerce -c "SELECT 1;" 2>&1

if ($testConnection -match "1 row") {
    Write-Host "  [OK] Connection successful!" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Connection failed!" -ForegroundColor Red
    Write-Host "  Error: $testConnection" -ForegroundColor Red
}

# Check database exists
Write-Host ""
Write-Host "[6/7] Checking database..." -ForegroundColor Yellow
$dbCheck = docker exec multi-agent-postgres psql -U postgres -c "\l" 2>&1

if ($dbCheck -match "multi_agent_ecommerce") {
    Write-Host "  [OK] Database 'multi_agent_ecommerce' exists" -ForegroundColor Green
} else {
    Write-Host "  [WARNING] Database 'multi_agent_ecommerce' not found!" -ForegroundColor Yellow
    Write-Host "  Creating database..." -ForegroundColor Yellow
    docker exec multi-agent-postgres psql -U postgres -c "CREATE DATABASE multi_agent_ecommerce;" 2>&1
}

# Test connection from host
Write-Host ""
Write-Host "[7/7] Testing connection from host..." -ForegroundColor Yellow

# Check if .env file exists
if (Test-Path ".env") {
    Write-Host "  [OK] .env file found" -ForegroundColor Green
    
    # Read database URL from .env
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "DATABASE_URL=(.+)") {
        $dbUrl = $matches[1]
        Write-Host "  DATABASE_URL: $dbUrl" -ForegroundColor White
    }
} else {
    Write-Host "  [WARNING] .env file not found!" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "DIAGNOSTIC SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Recommendations
Write-Host "TROUBLESHOOTING STEPS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "If PostgreSQL is not connecting:" -ForegroundColor White
Write-Host "  1. Check Docker Desktop is running" -ForegroundColor White
Write-Host "  2. Restart PostgreSQL container:" -ForegroundColor White
Write-Host "     docker restart multi-agent-postgres" -ForegroundColor Gray
Write-Host "  3. Check container logs:" -ForegroundColor White
Write-Host "     docker logs multi-agent-postgres" -ForegroundColor Gray
Write-Host "  4. Recreate container if needed:" -ForegroundColor White
Write-Host "     docker-compose down" -ForegroundColor Gray
Write-Host "     docker-compose up -d" -ForegroundColor Gray
Write-Host "  5. Wait 30 seconds for PostgreSQL to fully start" -ForegroundColor White
Write-Host ""

Write-Host "If database doesn't exist:" -ForegroundColor White
Write-Host "  docker exec multi-agent-postgres psql -U postgres -c 'CREATE DATABASE multi_agent_ecommerce;'" -ForegroundColor Gray
Write-Host ""

Write-Host "To connect manually:" -ForegroundColor White
Write-Host "  docker exec -it multi-agent-postgres psql -U postgres -d multi_agent_ecommerce" -ForegroundColor Gray
Write-Host ""

Write-Host "=" * 80 -ForegroundColor Cyan

