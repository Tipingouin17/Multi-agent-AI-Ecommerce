# Infrastructure Setup Guide

## Current Issues

Your agents are failing to connect to:
1. **Kafka** - `localhost:9092` (Connection closed)
2. **PostgreSQL** - Database connection error (WinError 64)

## Root Cause

The agents are trying to connect to infrastructure services that either:
- Are not running
- Are not accessible at the configured addresses
- Have incorrect configuration in your `.env` file

---

## Quick Fix: Start Infrastructure Services

### Option 1: Using Docker Compose (Recommended)

**Step 1: Ensure Docker is Running**

```powershell
# Check if Docker Desktop is running
docker --version
docker ps
```

**Step 2: Start Infrastructure Services**

```powershell
cd Multi-agent-AI-Ecommerce
docker-compose -f infrastructure/docker-compose.yml up -d
```

This will start:
- Kafka (port 9092)
- Zookeeper (for Kafka)
- PostgreSQL (port 5432)
- Redis (port 6379)
- Prometheus, Grafana, Loki (monitoring)

**Step 3: Verify Services Are Running**

```powershell
docker ps
```

You should see containers for:
- `kafka`
- `zookeeper`
- `postgres`
- `redis`

**Step 4: Wait for Services to Be Ready**

```powershell
# Wait 30-60 seconds for services to fully start
Start-Sleep -Seconds 30
```

**Step 5: Start Agents**

```powershell
.\start-system.ps1
```

---

### Option 2: Check Your .env Configuration

If you're using external services (not Docker), verify your `.env` file:

**Step 1: Create .env File**

```powershell
# Copy example if .env doesn't exist
Copy-Item .env.example .env
```

**Step 2: Edit .env File**

Open `.env` and configure:

```env
# Database Configuration
DATABASE_HOST=localhost          # Or your database server IP
DATABASE_PORT=5432
DATABASE_NAME=multi_agent_ecommerce
DATABASE_USER=postgres
DATABASE_PASSWORD=your_actual_password

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092  # Or your Kafka server

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# OpenAI API (for AI features)
OPENAI_API_KEY=sk-your_actual_openai_key
```

**Step 3: Verify Services Are Accessible**

```powershell
# Test PostgreSQL connection
Test-NetConnection -ComputerName localhost -Port 5432

# Test Kafka connection
Test-NetConnection -ComputerName localhost -Port 9092

# Test Redis connection
Test-NetConnection -ComputerName localhost -Port 6379
```

---

## Detailed Troubleshooting

### Issue 1: Kafka Connection Error

**Error**:
```
KafkaConnectionError: Connection at localhost:9092 closed
Topic customer_communication_agent_topic is not available
```

**Solutions**:

#### A. Start Kafka via Docker

```powershell
cd Multi-agent-AI-Ecommerce
docker-compose -f infrastructure/docker-compose.yml up -d kafka zookeeper
```

#### B. Verify Kafka is Running

```powershell
docker ps | Select-String kafka
```

Expected output:
```
kafka           Up      9092/tcp
zookeeper       Up      2181/tcp
```

#### C. Check Kafka Logs

```powershell
docker logs kafka
```

Look for:
```
[KafkaServer id=1] started
```

#### D. Test Kafka Connection

```powershell
# From inside the Kafka container
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092
```

---

### Issue 2: PostgreSQL Connection Error

**Error**:
```
[WinError 64] The specified network name is no longer available
Database session error
```

**Solutions**:

#### A. Start PostgreSQL via Docker

```powershell
cd Multi-agent-AI-Ecommerce
docker-compose -f infrastructure/docker-compose.yml up -d postgres
```

#### B. Verify PostgreSQL is Running

```powershell
docker ps | Select-String postgres
```

Expected output:
```
postgres        Up      5432/tcp
```

#### C. Check PostgreSQL Logs

```powershell
docker logs postgres
```

Look for:
```
database system is ready to accept connections
```

#### D. Test Database Connection

```powershell
# Using psql (if installed)
psql -h localhost -p 5432 -U postgres -d multi_agent_ecommerce

# Or using Docker
docker exec -it postgres psql -U postgres -d multi_agent_ecommerce
```

---

## Complete Startup Sequence

Follow this order for best results:

### 1. Start Infrastructure (Docker)

```powershell
cd Multi-agent-AI-Ecommerce

# Start all infrastructure services
docker-compose -f infrastructure/docker-compose.yml up -d

# Wait for services to be ready
Start-Sleep -Seconds 30

# Verify all services are running
docker ps
```

### 2. Initialize Database (First Time Only)

```powershell
# Run database migrations
python shared/database.py
```

### 3. Verify .env Configuration

```powershell
# Check .env file exists
Test-Path .env

# If not, copy from example
if (!(Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "⚠ Please edit .env file with your configuration"
}
```

### 4. Start Agents

```powershell
.\start-system.ps1
```

---

## Environment Variables Check

The agents read configuration from `.env` file. Verify these are set:

### Required Variables

```env
# Database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=multi_agent_ecommerce
DATABASE_USER=postgres
DATABASE_PASSWORD=<your_password>

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Redis (optional but recommended)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Optional but Recommended

```env
# OpenAI (for AI features)
OPENAI_API_KEY=sk-<your_key>

# Logging
LOG_LEVEL=INFO
```

---

## Docker Compose Configuration

If `infrastructure/docker-compose.yml` doesn't exist or needs updating:

### Check Docker Compose File

```powershell
Test-Path infrastructure/docker-compose.yml
```

### View Docker Compose Services

```powershell
docker-compose -f infrastructure/docker-compose.yml config --services
```

Expected services:
- kafka
- zookeeper
- postgres
- redis
- prometheus
- grafana
- loki
- promtail

---

## Common Issues and Solutions

### Issue: "Docker is not running"

**Solution**:
1. Start Docker Desktop
2. Wait for Docker to fully start (whale icon in system tray)
3. Verify: `docker ps`

### Issue: "Port already in use"

**Error**: `Bind for 0.0.0.0:9092 failed: port is already allocated`

**Solution**:
```powershell
# Find what's using the port
netstat -ano | findstr :9092

# Stop the conflicting service or change port in docker-compose.yml
```

### Issue: "Container keeps restarting"

**Solution**:
```powershell
# Check container logs
docker logs <container_name>

# Restart with fresh data
docker-compose -f infrastructure/docker-compose.yml down -v
docker-compose -f infrastructure/docker-compose.yml up -d
```

### Issue: ".env file not loaded"

**Solution**:
```powershell
# Verify .env file exists in project root
Get-Content .env

# Ensure no spaces around = in .env
# WRONG: DATABASE_HOST = localhost
# RIGHT: DATABASE_HOST=localhost
```

---

## Verification Checklist

Before starting agents, verify:

- [ ] Docker Desktop is running
- [ ] Infrastructure services are up: `docker ps`
- [ ] Kafka is accessible: `Test-NetConnection localhost -Port 9092`
- [ ] PostgreSQL is accessible: `Test-NetConnection localhost -Port 5432`
- [ ] Redis is accessible: `Test-NetConnection localhost -Port 6379`
- [ ] `.env` file exists and is configured
- [ ] Database is initialized

---

## Quick Start Script

Create `start-infrastructure.ps1`:

```powershell
#!/usr/bin/env pwsh
# Start Infrastructure Services

Write-Host "🚀 Starting Multi-Agent E-commerce Infrastructure..." -ForegroundColor Cyan

# Check Docker is running
Write-Host "`n1. Checking Docker..." -ForegroundColor Yellow
docker ps > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Docker is running" -ForegroundColor Green

# Start infrastructure services
Write-Host "`n2. Starting infrastructure services..." -ForegroundColor Yellow
docker-compose -f infrastructure/docker-compose.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start infrastructure services" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Infrastructure services started" -ForegroundColor Green

# Wait for services to be ready
Write-Host "`n3. Waiting for services to be ready (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Verify services
Write-Host "`n4. Verifying services..." -ForegroundColor Yellow

$services = @(
    @{Name="Kafka"; Port=9092},
    @{Name="PostgreSQL"; Port=5432},
    @{Name="Redis"; Port=6379}
)

$allHealthy = $true
foreach ($service in $services) {
    $result = Test-NetConnection -ComputerName localhost -Port $service.Port -WarningAction SilentlyContinue
    if ($result.TcpTestSucceeded) {
        Write-Host "✓ $($service.Name) is accessible on port $($service.Port)" -ForegroundColor Green
    } else {
        Write-Host "❌ $($service.Name) is NOT accessible on port $($service.Port)" -ForegroundColor Red
        $allHealthy = $false
    }
}

if ($allHealthy) {
    Write-Host "`n✅ All infrastructure services are ready!" -ForegroundColor Green
    Write-Host "You can now start the agents with: .\start-system.ps1" -ForegroundColor Cyan
} else {
    Write-Host "`n⚠ Some services are not ready. Check Docker logs:" -ForegroundColor Yellow
    Write-Host "docker-compose -f infrastructure/docker-compose.yml logs" -ForegroundColor Gray
}
```

**Usage**:
```powershell
.\start-infrastructure.ps1
```

---

## Summary

**Your agents need these services running**:

1. **Kafka** (localhost:9092) - For inter-agent communication
2. **PostgreSQL** (localhost:5432) - For data storage
3. **Redis** (localhost:6379) - For caching (optional)

**Quick fix**:
```powershell
# Start everything
docker-compose -f infrastructure/docker-compose.yml up -d

# Wait 30 seconds
Start-Sleep -Seconds 30

# Start agents
.\start-system.ps1
```

**If you don't have Docker**, you need to:
1. Install and configure Kafka locally
2. Install and configure PostgreSQL locally
3. Update `.env` with correct connection details

**Recommended**: Use Docker - it's much easier! 🐳

