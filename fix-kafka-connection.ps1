# Kafka Connection Fix for Windows
# This script fixes the Kafka connection issue on Windows Docker

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Kafka Connection Fix for Windows Docker" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Step 1: Check if Kafka container is running
Write-Host "Step 1: Checking Kafka container status..." -ForegroundColor Yellow
$kafkaStatus = docker ps --filter "name=multi-agent-kafka" --format "{{.Status}}"

if ($kafkaStatus) {
    Write-Host "[OK] Kafka container is running: $kafkaStatus" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Kafka container is not running!" -ForegroundColor Red
    Write-Host "Please start Docker services first: cd infrastructure && docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

# Step 2: Wait for Kafka to be fully ready
Write-Host "`nStep 2: Waiting for Kafka to be fully ready..." -ForegroundColor Yellow
Write-Host "This may take 30-60 seconds..." -ForegroundColor Gray

$maxAttempts = 12
$attempt = 0
$kafkaReady = $false

while ($attempt -lt $maxAttempts -and -not $kafkaReady) {
    $attempt++
    Write-Host "  Attempt $attempt/$maxAttempts..." -ForegroundColor Gray
    
    $result = docker exec multi-agent-kafka kafka-topics.sh --list --bootstrap-server localhost:9092 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $kafkaReady = $true
        Write-Host "[OK] Kafka is ready and accepting connections!" -ForegroundColor Green
    } else {
        Start-Sleep -Seconds 5
    }
}

if (-not $kafkaReady) {
    Write-Host "[WARNING] Kafka may not be fully ready yet. Continuing anyway..." -ForegroundColor Yellow
}

# Step 3: Get Kafka IP address
Write-Host "`nStep 3: Getting Kafka network information..." -ForegroundColor Yellow

$kafkaIP = docker inspect multi-agent-kafka --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
Write-Host "  Kafka container IP: $kafkaIP" -ForegroundColor Gray

# Step 4: Update .env file
Write-Host "`nStep 4: Updating .env configuration..." -ForegroundColor Yellow

$envPath = ".env"

if (-not (Test-Path $envPath)) {
    Write-Host "[WARNING] .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" $envPath
    } else {
        Write-Host "[ERROR] .env.example not found!" -ForegroundColor Red
        exit 1
    }
}

# Read .env content
$envContent = Get-Content $envPath

# Update or add KAFKA_BOOTSTRAP_SERVERS
$kafkaLineFound = $false
$newEnvContent = @()

foreach ($line in $envContent) {
    if ($line -match '^KAFKA_BOOTSTRAP_SERVERS=') {
        $newEnvContent += "KAFKA_BOOTSTRAP_SERVERS=host.docker.internal:9092"
        $kafkaLineFound = $true
        Write-Host "  Updated existing KAFKA_BOOTSTRAP_SERVERS" -ForegroundColor Gray
    } else {
        $newEnvContent += $line
    }
}

if (-not $kafkaLineFound) {
    $newEnvContent += ""
    $newEnvContent += "# Kafka Configuration (Windows Docker fix)"
    $newEnvContent += "KAFKA_BOOTSTRAP_SERVERS=host.docker.internal:9092"
    Write-Host "  Added new KAFKA_BOOTSTRAP_SERVERS" -ForegroundColor Gray
}

# Write back to .env
$newEnvContent | Set-Content $envPath

Write-Host "[OK] .env file updated" -ForegroundColor Green

# Step 5: Verify the configuration
Write-Host "`nStep 5: Verifying configuration..." -ForegroundColor Yellow

$kafkaConfig = Select-String -Path $envPath -Pattern "KAFKA_BOOTSTRAP_SERVERS"
Write-Host "  Current setting: $kafkaConfig" -ForegroundColor Gray

# Step 6: Test connection from Python
Write-Host "`nStep 6: Testing Kafka connection from Python..." -ForegroundColor Yellow

$testScript = @"
import sys
import os
from kafka import KafkaAdminClient
from kafka.errors import KafkaError

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Try host.docker.internal first
    print('Testing connection to host.docker.internal:9092...')
    admin = KafkaAdminClient(
        bootstrap_servers=['host.docker.internal:9092'],
        client_id='connection-test',
        request_timeout_ms=5000
    )
    topics = admin.list_topics()
    print(f'SUCCESS! Connected to Kafka. Found {len(topics)} topics.')
    admin.close()
    sys.exit(0)
except Exception as e:
    print(f'FAILED: {str(e)}')
    
    # Try localhost as fallback
    try:
        print('Trying localhost:9092 as fallback...')
        admin = KafkaAdminClient(
            bootstrap_servers=['localhost:9092'],
            client_id='connection-test',
            request_timeout_ms=5000
        )
        topics = admin.list_topics()
        print(f'SUCCESS with localhost! Connected to Kafka. Found {len(topics)} topics.')
        print('NOTE: Update .env to use KAFKA_BOOTSTRAP_SERVERS=localhost:9092')
        admin.close()
        sys.exit(0)
    except Exception as e2:
        print(f'FAILED with localhost too: {str(e2)}')
        sys.exit(1)
"@

$testScript | Out-File -FilePath "test_kafka_connection.py" -Encoding UTF8

# Run the test
& ".\venv\Scripts\python.exe" test_kafka_connection.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[OK] Kafka connection test PASSED!" -ForegroundColor Green
} else {
    Write-Host "`n[ERROR] Kafka connection test FAILED!" -ForegroundColor Red
    Write-Host "`nTroubleshooting steps:" -ForegroundColor Yellow
    Write-Host "1. Restart Kafka: docker restart multi-agent-kafka" -ForegroundColor Gray
    Write-Host "2. Check Kafka logs: docker logs multi-agent-kafka" -ForegroundColor Gray
    Write-Host "3. Verify port mapping: docker port multi-agent-kafka" -ForegroundColor Gray
    Write-Host "4. Try manual connection: docker exec -it multi-agent-kafka kafka-topics.sh --list --bootstrap-server localhost:9092" -ForegroundColor Gray
}

# Cleanup
Remove-Item "test_kafka_connection.py" -ErrorAction SilentlyContinue

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Fix Complete!" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Restart your agents: .\start-system.ps1" -ForegroundColor White
Write-Host "2. Monitor the output for Kafka connection errors" -ForegroundColor White
Write-Host "3. If still failing, check Docker logs: docker logs multi-agent-kafka`n" -ForegroundColor White

