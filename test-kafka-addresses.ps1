#!/usr/bin/env pwsh
# Test different Kafka connection addresses to find which one works

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Kafka Address Tester" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Test 1: localhost
Write-Host "Test 1: Testing localhost:9092..." -ForegroundColor Yellow
$result1 = docker exec multi-agent-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] localhost:9092 works from inside container" -ForegroundColor Green
} else {
    Write-Host "[FAIL] localhost:9092 failed" -ForegroundColor Red
}

# Test 2: host.docker.internal
Write-Host "`nTest 2: Testing host.docker.internal:9092..." -ForegroundColor Yellow
try {
    $resolved = [System.Net.Dns]::GetHostAddresses("host.docker.internal")
    Write-Host "[OK] host.docker.internal resolves to: $($resolved.IPAddressToString)" -ForegroundColor Green
    
    # Try to connect
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("host.docker.internal", 9092)
    Write-Host "[OK] Can connect to host.docker.internal:9092" -ForegroundColor Green
    $tcpClient.Close()
} catch {
    Write-Host "[FAIL] host.docker.internal:9092 - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: 127.0.0.1
Write-Host "`nTest 3: Testing 127.0.0.1:9092..." -ForegroundColor Yellow
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("127.0.0.1", 9092)
    Write-Host "[OK] Can connect to 127.0.0.1:9092" -ForegroundColor Green
    $tcpClient.Close()
} catch {
    Write-Host "[FAIL] 127.0.0.1:9092 - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Get Docker network IP
Write-Host "`nTest 4: Testing Docker container IP..." -ForegroundColor Yellow
$kafkaIP = docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' multi-agent-kafka
if ($kafkaIP) {
    Write-Host "Kafka container IP: $kafkaIP" -ForegroundColor Cyan
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.Connect($kafkaIP, 9092)
        Write-Host "[OK] Can connect to ${kafkaIP}:9092" -ForegroundColor Green
        $tcpClient.Close()
    } catch {
        Write-Host "[FAIL] ${kafkaIP}:9092 - $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Test 5: Check port mapping
Write-Host "`nTest 5: Checking Docker port mapping..." -ForegroundColor Yellow
$portMapping = docker port multi-agent-kafka 9092
if ($portMapping) {
    Write-Host "Port 9092 is mapped to: $portMapping" -ForegroundColor Cyan
} else {
    Write-Host "[FAIL] Port 9092 is not mapped!" -ForegroundColor Red
}

# Test 6: Check what's listening on port 9092
Write-Host "`nTest 6: Checking what's listening on port 9092..." -ForegroundColor Yellow
$listening = netstat -an | Select-String ":9092"
if ($listening) {
    Write-Host "Found:" -ForegroundColor Cyan
    $listening | ForEach-Object { Write-Host "  $_" -ForegroundColor White }
} else {
    Write-Host "[FAIL] Nothing listening on port 9092!" -ForegroundColor Red
}

# Recommendation
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Recommendation" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

if ($portMapping -match "0.0.0.0:9092") {
    Write-Host "Use: KAFKA_BOOTSTRAP_SERVERS=localhost:9092" -ForegroundColor Green
    Write-Host "or:  KAFKA_BOOTSTRAP_SERVERS=127.0.0.1:9092" -ForegroundColor Green
} elseif ($kafkaIP) {
    Write-Host "Use: KAFKA_BOOTSTRAP_SERVERS=${kafkaIP}:9092" -ForegroundColor Green
} else {
    Write-Host "Kafka is not accessible from Windows host!" -ForegroundColor Red
    Write-Host "Check docker-compose.yml port mapping." -ForegroundColor Yellow
}

Write-Host ""

