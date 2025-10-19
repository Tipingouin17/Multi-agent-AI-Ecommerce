# Kafka Diagnostic Script
# Checks Kafka configuration and connectivity

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Kafka Diagnostic Tool" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Check if Kafka container is running
Write-Host "1. Checking Kafka container status..." -ForegroundColor Yellow
$kafkaStatus = docker ps --filter "name=multi-agent-kafka" --format "{{.Status}}"
if ($kafkaStatus) {
    Write-Host "   [OK] Kafka container is running: $kafkaStatus`n" -ForegroundColor Green
} else {
    Write-Host "   [ERROR] Kafka container is not running!`n" -ForegroundColor Red
    exit 1
}

# Check Kafka environment variables
Write-Host "2. Checking Kafka listener configuration..." -ForegroundColor Yellow
$listeners = docker exec multi-agent-kafka env | Select-String "KAFKA_"
Write-Host "   Key Kafka settings:" -ForegroundColor Gray
$listeners | Select-String "LISTENER" | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
Write-Host ""

# Check Kafka logs for startup
Write-Host "3. Checking Kafka startup logs..." -ForegroundColor Yellow
$kafkaLogs = docker logs multi-agent-kafka 2>&1 | Select-String -Pattern "started|Startup|ERROR" | Select-Object -Last 10
if ($kafkaLogs) {
    $kafkaLogs | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
} else {
    Write-Host "   No relevant logs found" -ForegroundColor Gray
}
Write-Host ""

# Test connection from inside container
Write-Host "4. Testing Kafka from inside container..." -ForegroundColor Yellow
Write-Host "   Testing localhost:9092..." -ForegroundColor Gray
$testInternal = docker exec multi-agent-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   [OK] localhost:9092 works from inside container`n" -ForegroundColor Green
} else {
    Write-Host "   [ERROR] localhost:9092 failed from inside container" -ForegroundColor Red
    Write-Host "   Error: $testInternal`n" -ForegroundColor Gray
}

Write-Host "   Testing kafka:29092..." -ForegroundColor Gray
$testInternalBroker = docker exec multi-agent-kafka kafka-broker-api-versions --bootstrap-server kafka:29092 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   [OK] kafka:29092 works from inside container`n" -ForegroundColor Green
} else {
    Write-Host "   [ERROR] kafka:29092 failed from inside container" -ForegroundColor Red
    Write-Host "   Error: $testInternalBroker`n" -ForegroundColor Gray
}

# Test connection from Windows host
Write-Host "5. Testing Kafka from Windows host..." -ForegroundColor Yellow

$testScript = @"
import sys
from kafka import KafkaAdminClient
from kafka.errors import KafkaError

addresses = [
    'localhost:9092',
    'host.docker.internal:9092',
    '127.0.0.1:9092'
]

for addr in addresses:
    try:
        print(f'   Testing {addr}...', end=' ')
        admin = KafkaAdminClient(
            bootstrap_servers=[addr],
            client_id='diagnostic-test',
            request_timeout_ms=10000
        )
        topics = admin.list_topics()
        print(f'SUCCESS! Found {len(topics)} topics.')
        
        # Get cluster metadata
        metadata = admin._client.cluster
        print(f'   Cluster ID: {metadata.cluster_id()}')
        for broker in metadata.brokers():
            print(f'   Broker: {broker.host}:{broker.port}')
        
        admin.close()
        break
    except Exception as e:
        print(f'FAILED: {str(e)}')
"@

$testScript | Out-File -FilePath "test_kafka_diagnostic.py" -Encoding UTF8
& ".\venv\Scripts\python.exe" test_kafka_diagnostic.py
Remove-Item "test_kafka_diagnostic.py" -ErrorAction SilentlyContinue
Write-Host ""

# Check port mapping
Write-Host "6. Checking port mappings..." -ForegroundColor Yellow
$ports = docker port multi-agent-kafka
Write-Host "   $ports`n" -ForegroundColor Gray

# Check if anything else is using port 9092
Write-Host "7. Checking for port conflicts..." -ForegroundColor Yellow
$portCheck = netstat -ano | Select-String ":9092"
if ($portCheck) {
    Write-Host "   Processes using port 9092:" -ForegroundColor Gray
    $portCheck | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
} else {
    Write-Host "   No conflicts found on port 9092" -ForegroundColor Gray
}
Write-Host ""

# Check .env configuration
Write-Host "8. Checking .env configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    $kafkaConfig = Select-String -Path ".env" -Pattern "KAFKA"
    if ($kafkaConfig) {
        Write-Host "   Kafka settings in .env:" -ForegroundColor Gray
        $kafkaConfig | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
    } else {
        Write-Host "   [WARNING] No KAFKA settings found in .env" -ForegroundColor Yellow
    }
} else {
    Write-Host "   [WARNING] .env file not found" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Diagnostic Summary" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host "`nRecommendations:" -ForegroundColor Yellow
Write-Host "1. If connection from Windows host failed, check KAFKA_ADVERTISED_LISTENERS" -ForegroundColor White
Write-Host "2. Ensure .env has: KAFKA_BOOTSTRAP_SERVERS=localhost:9092" -ForegroundColor White
Write-Host "3. Try restarting Kafka: docker restart multi-agent-kafka" -ForegroundColor White
Write-Host "4. Check Kafka logs: docker logs multi-agent-kafka --tail 100`n" -ForegroundColor White

