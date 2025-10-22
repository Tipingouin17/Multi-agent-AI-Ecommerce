# Multi-Agent E-commerce System - Startup Troubleshooting Guide

**Date:** October 22, 2025  
**Version:** 1.0  
**Latest Commit:** 30e532e

---

## Overview

This guide helps troubleshoot common issues when starting the Multi-Agent E-commerce platform using the PowerShell startup scripts.

---

## Startup Scripts Overview

### 1. `start-infrastructure.ps1`

**Purpose:** Starts Docker infrastructure services (PostgreSQL, Kafka, Redis)

**What it does:**
- Checks if Docker is running
- Starts `docker-compose` services from `infrastructure/docker-compose.yml`
- Waits 30 seconds for services to initialize
- Verifies PostgreSQL (port 5432), Kafka (port 9092), and Redis (port 6379)

**Expected output:**
```
SUCCESS: Docker is running
SUCCESS: Infrastructure services started
SUCCESS: Kafka is accessible on port 9092
SUCCESS: PostgreSQL is accessible on port 5432
SUCCESS: All infrastructure services are ready!
```

---

### 2. `start-system.ps1`

**Purpose:** Complete system startup - infrastructure + all 15 agents

**What it does:**
- Activates Python virtual environment
- Checks dependencies
- Starts Docker infrastructure (unless `--SkipDocker` flag is used)
- Waits for Kafka to be fully ready (up to 90 seconds)
- Verifies database connection
- Starts all 15 agents via `start-agents-monitor.py`

**Expected output:**
```
[OK] Virtual environment activated
[OK] Dependencies OK
[OK] Docker is running
[OK] Docker services started
[OK] Kafka is ready and accepting connections!
[OK] Database connection successful
Starting all 15 production agents...
```

---

### 3. `start-dashboard.ps1`

**Purpose:** Starts the React/Vite dashboard UI

**What it does:**
- Checks Node.js version (requires v18+)
- Installs npm dependencies if needed
- Verifies critical dashboard files
- Checks if backend agents are running (all 15 ports)
- Starts Vite dev server on `http://localhost:5173`

**Expected output:**
```
SUCCESS: Node.js version: v22.x.x
SUCCESS: Dependencies installed
SUCCESS: Detected 15/15 agents running
Starting dashboard on http://localhost:5173
```

---

## Common Issues & Solutions

### Issue 1: "Agents cannot detect Kafka and Postgres"

**Symptoms:**
- Agents fail to start
- Error messages about connection timeouts
- "Cannot connect to localhost:9092" or "Cannot connect to localhost:5432"

**Root Cause:**
Agents are trying to connect to `localhost` but Docker services are running in containers with different hostnames.

**Solution:**

The updated `start-agents-monitor.py` script now sets environment variables correctly:

```python
env['DATABASE_HOST'] = 'localhost'
env['KAFKA_BOOTSTRAP_SERVERS'] = 'localhost:9092'
```

However, if you're running agents **inside Docker**, you need to use Docker service names:

```bash
# For agents running OUTSIDE Docker (on Windows/Mac host)
DATABASE_HOST=localhost
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# For agents running INSIDE Docker containers
DATABASE_HOST=postgres
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

**Fix for your setup:**

Since you're running infrastructure in Docker but agents on Windows, ensure:

1. Docker Desktop is configured to expose ports to `localhost`
2. Check Docker Compose port mappings:

```yaml
# infrastructure/docker-compose.yml
postgres:
  ports:
    - "5432:5432"  # Maps container port to localhost

kafka:
  ports:
    - "9092:9092"  # Maps container port to localhost
```

3. Verify ports are accessible:

```powershell
Test-NetConnection -ComputerName localhost -Port 5432
Test-NetConnection -ComputerName localhost -Port 9092
```

---

### Issue 2: "Kafka takes too long to start"

**Symptoms:**
- Agents timeout waiting for Kafka
- "Kafka is not ready" warnings
- Agents crash on startup

**Solution:**

Kafka can take 60-90 seconds to fully initialize after a fresh start.

**Option 1: Wait longer**

The `start-system.ps1` script already waits up to 90 seconds. If Kafka still isn't ready:

```powershell
# Manually check Kafka status
docker exec multi-agent-kafka kafka-broker-api-versions --bootstrap-server localhost:9092
```

**Option 2: Start infrastructure separately**

```powershell
# Step 1: Start infrastructure and wait
.\start-infrastructure.ps1

# Step 2: Wait 2-3 minutes for Kafka to fully initialize

# Step 3: Start agents
.\start-system.ps1 --SkipDocker
```

---

### Issue 3: "Agent files not found"

**Symptoms:**
```
[ERROR] [AgentName] File not found: agents/old_agent_name.py
```

**Root Cause:**
The startup script was using old agent filenames.

**Solution:**

This has been fixed in commit `30e532e`. Pull the latest changes:

```powershell
git pull origin main
```

The script now uses correct production filenames:
- `order_agent_production.py`
- `product_agent_production.py`
- `warehouse_agent_production.py`
- `transport_agent_production.py`
- `marketplace_connector_agent_production.py`
- etc.

---

### Issue 4: "Database connection failed"

**Symptoms:**
```
[WARNING] Database connection failed
```

**Solution:**

1. **Check if PostgreSQL is running:**

```powershell
docker ps | findstr postgres
```

2. **Check database exists:**

```powershell
docker exec multi-agent-postgres psql -U postgres -l
```

3. **Create database if missing:**

```powershell
docker exec multi-agent-postgres psql -U postgres -c "CREATE DATABASE multi_agent_ecommerce;"
```

4. **Run migrations:**

```powershell
docker exec multi-agent-postgres psql -U postgres -d multi_agent_ecommerce -f /path/to/migrations/000_complete_system_schema.sql
```

---

### Issue 5: "Dashboard shows no data"

**Symptoms:**
- Dashboard loads but shows empty tables
- "No backend agents detected running" warning

**Root Cause:**
Agents are not running or not accessible on expected ports.

**Solution:**

1. **Check if agents are running:**

```powershell
# Check all 15 agent ports
8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009, 8010, 8011, 8012, 8013, 8020, 8021 | ForEach-Object {
    $port = $_
    $result = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue -InformationLevel Quiet
    if ($result.TcpTestSucceeded) {
        Write-Host "Port $port : OPEN" -ForegroundColor Green
    } else {
        Write-Host "Port $port : CLOSED" -ForegroundColor Red
    }
}
```

2. **Start agents if not running:**

```powershell
.\start-system.ps1
```

3. **Check agent logs:**

```powershell
# Logs are saved in logs/agent_monitor_YYYYMMDD_HHMMSS.log
Get-Content -Path "logs\agent_monitor_*.log" -Tail 50
```

---

### Issue 6: "Virtual environment not found"

**Symptoms:**
```
[ERROR] Virtual environment not found!
Please run: python -m venv venv
```

**Solution:**

1. **Create virtual environment:**

```powershell
python -m venv venv
```

2. **Activate it:**

```powershell
.\venv\Scripts\Activate.ps1
```

3. **Install dependencies:**

```powershell
pip install -r requirements.txt
```

---

### Issue 7: "Port already in use"

**Symptoms:**
```
Error: Port 8001 is already in use
```

**Solution:**

1. **Find process using the port:**

```powershell
netstat -ano | findstr :8001
```

2. **Kill the process:**

```powershell
# Replace PID with the actual process ID from netstat
Stop-Process -Id PID -Force
```

3. **Or stop all Python processes:**

```powershell
Get-Process python | Stop-Process -Force
```

---

## Environment Variables

### Required Environment Variables

The agents need these environment variables to connect to infrastructure:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_HOST` | `localhost` | PostgreSQL hostname |
| `DATABASE_PORT` | `5432` | PostgreSQL port |
| `DATABASE_NAME` | `multi_agent_ecommerce` | Database name |
| `DATABASE_USER` | `postgres` | Database username |
| `DATABASE_PASSWORD` | `postgres` | Database password |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker address |
| `REDIS_HOST` | `localhost` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |

### Setting Environment Variables (PowerShell)

**Temporary (current session only):**

```powershell
$env:DATABASE_HOST = "localhost"
$env:KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
$env:DATABASE_PASSWORD = "your_password"
```

**Permanent (system-wide):**

```powershell
[System.Environment]::SetEnvironmentVariable("DATABASE_HOST", "localhost", "User")
[System.Environment]::SetEnvironmentVariable("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092", "User")
```

**Using .env file:**

Create a `.env` file in the project root:

```env
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=multi_agent_ecommerce
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
REDIS_HOST=localhost
REDIS_PORT=6379
```

Then load it before starting agents:

```powershell
# Load .env file
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}
```

---

## Logging & Debugging

### Agent Logs

All agent output is logged to:

```
logs/agent_monitor_YYYYMMDD_HHMMSS.log
```

**View latest log:**

```powershell
Get-Content -Path (Get-ChildItem logs\agent_monitor_*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName -Tail 100
```

**Search for errors:**

```powershell
Select-String -Path "logs\agent_monitor_*.log" -Pattern "error|exception|failed" -CaseSensitive:$false
```

### Docker Logs

**View all infrastructure logs:**

```powershell
cd infrastructure
docker-compose logs -f
```

**View specific service:**

```powershell
docker-compose logs -f postgres
docker-compose logs -f kafka
```

### Agent Health Checks

Each agent exposes a `/health` endpoint:

```powershell
# Check all agents
8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009, 8010, 8011, 8012, 8013, 8020, 8021 | ForEach-Object {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$_/health" -TimeoutSec 2
        Write-Host "Port $_ : $($response.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "Port $_ : Failed" -ForegroundColor Red
    }
}
```

---

## Complete Startup Sequence

### Recommended Startup Order

1. **Start Infrastructure:**

```powershell
.\start-infrastructure.ps1
```

Wait for output:
```
SUCCESS: All infrastructure services are ready!
```

2. **Wait 2-3 minutes** for Kafka to fully initialize

3. **Verify Kafka is ready:**

```powershell
docker exec multi-agent-kafka kafka-broker-api-versions --bootstrap-server localhost:9092
```

4. **Start Agents:**

```powershell
.\start-system.ps1 --SkipDocker
```

Wait for output:
```
All 15 agents started! Monitoring output...
```

5. **Start Dashboard:**

```powershell
.\start-dashboard.ps1
```

Wait for output:
```
Starting dashboard on http://localhost:5173
```

6. **Access Dashboard:**

Open browser: `http://localhost:5173`

---

## Quick Reference

### Stop Everything

```powershell
# Stop agents (Ctrl+C in the start-system.ps1 window)

# Stop infrastructure
cd infrastructure
docker-compose down
```

### Restart Everything

```powershell
# Stop infrastructure
cd infrastructure
docker-compose down

# Start fresh
cd ..
.\start-infrastructure.ps1
# Wait 2-3 minutes
.\start-system.ps1 --SkipDocker
.\start-dashboard.ps1
```

### Check Status

```powershell
# Docker services
docker ps

# Agent processes
Get-Process python

# Ports
netstat -an | findstr "5432 9092 6379 8001 8002 8003"
```

---

## Getting Help

If you encounter issues not covered in this guide:

1. **Check logs** in `logs/agent_monitor_*.log`
2. **Check Docker logs** with `docker-compose logs`
3. **Review GitHub issues**: https://github.com/Tipingouin17/Multi-agent-AI-Ecommerce/issues
4. **Check commit history** for recent fixes

---

**Last Updated:** October 22, 2025  
**Maintainer:** Multi-Agent AI E-commerce Team  
**Latest Commit:** 30e532e

