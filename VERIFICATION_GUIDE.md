# System Verification Guide

## Overview

Before confirming the system is ready for demo, **all components must be verified** to ensure there are no errors in logs or runtime issues.

This guide provides comprehensive verification scripts and manual checks to ensure everything is working correctly.

## Automated Verification Scripts

Two verification scripts are provided:

### 1. PowerShell Script (Windows)
```powershell
.\verify-system.ps1

# With verbose output (shows error details)
.\verify-system.ps1 -Verbose
```

### 2. Python Script (Cross-platform)
```bash
python verify-system.py
```

## What Gets Checked

### ✅ Docker Services
- PostgreSQL (multi-agent-postgres)
- Redis (multi-agent-redis)
- Kafka (multi-agent-kafka)
- Zookeeper (multi-agent-zookeeper)
- Prometheus (multi-agent-prometheus)
- Grafana (multi-agent-grafana)
- Loki (multi-agent-loki)
- Promtail (multi-agent-promtail)
- Nginx (multi-agent-nginx)

**Checks:**
- Container is running
- Status is "Up"
- No restart loops

### ✅ Docker Container Logs
**Scans for error patterns:**
- ERROR
- FATAL
- panic
- failed
- cannot
- permission denied
- connection refused

**Containers checked:**
- PostgreSQL
- Kafka
- Redis
- Loki
- Promtail

### ✅ Database Connection
- PostgreSQL is accessible
- Database `multi_agent_ecommerce` exists
- Can execute queries
- No connection errors

### ✅ Required Ports
**Verifies these ports are listening:**
- 5432 - PostgreSQL
- 6379 - Redis
- 9092 - Kafka
- 2181 - Zookeeper
- 9090 - Prometheus
- 3000 - Grafana
- 3100 - Loki

### ✅ Agent Processes
**Checks if these agents are running:**
- order_agent
- inventory_agent
- product_agent
- carrier_selection_agent
- warehouse_selection_agent
- customer_communication_agent
- demand_forecasting_agent
- dynamic_pricing_agent
- reverse_logistics_agent
- risk_anomaly_detection_agent
- ai_monitoring_agent
- d2c_ecommerce_agent
- standard_marketplace_agent
- refurbished_marketplace_agent

### ✅ Agent Log Files
**Scans logs for error patterns:**
- ERROR
- CRITICAL
- FATAL
- Exception
- Traceback
- failed
- cannot import
- ModuleNotFoundError
- ImportError
- ConnectionError
- TimeoutError

**Checks last 100 lines** of each log file.

## Manual Verification Steps

If you prefer manual verification:

### 1. Check Docker Services

```powershell
# List all containers
docker ps

# Check specific service
docker logs multi-agent-postgres --tail 50
docker logs multi-agent-kafka --tail 50
docker logs multi-agent-redis --tail 50

# Look for errors
docker logs multi-agent-postgres 2>&1 | Select-String "ERROR"
```

### 2. Test Database Connection

```powershell
# Connect to PostgreSQL
docker exec -it multi-agent-postgres psql -U postgres -d multi_agent_ecommerce

# In psql:
\l                    # List databases
\dt                   # List tables
SELECT COUNT(*) FROM orders;
\q                    # Quit
```

### 3. Check Agent Logs

```powershell
# Navigate to logs directory
cd logs

# Check for errors in all logs
Get-ChildItem -Recurse -Filter *.log | ForEach-Object {
    Write-Host "Checking $($_.Name)..." -ForegroundColor Cyan
    Get-Content $_ -Tail 50 | Select-String "ERROR|Exception|FATAL"
}
```

### 4. Verify Ports

```powershell
# Check if ports are listening
Get-NetTCPConnection -LocalPort 5432,6379,9092,3000,9090,3100 | 
    Select-Object LocalPort, State

# Or use netstat
netstat -an | findstr "5432 6379 9092 3000 9090 3100"
```

### 5. Check Agent Processes

```powershell
# List Python processes
Get-Process python* | Select-Object Id, ProcessName, StartTime

# Check specific agent
Get-Process | Where-Object {$_.CommandLine -like "*order_agent*"}
```

## Verification Checklist

Use this checklist before confirming system is ready:

- [ ] All 9 Docker services are running
- [ ] No errors in Docker container logs
- [ ] PostgreSQL connection successful
- [ ] All required ports are listening
- [ ] At least 6+ agents are running
- [ ] No errors in agent log files
- [ ] Grafana dashboard accessible (http://localhost:3000)
- [ ] Prometheus metrics accessible (http://localhost:9090)
- [ ] No import errors in any agent
- [ ] No connection errors in any agent
- [ ] No database errors in any agent

## Common Issues and Solutions

### Issue: Docker service shows "Restarting"

```powershell
# Check logs for the issue
docker logs <container_name> --tail 100

# Common fixes:
docker-compose down
docker-compose up -d
```

### Issue: Agent shows import errors

```powershell
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### Issue: Database connection fails

```powershell
# Check PostgreSQL is running
docker ps | findstr postgres

# Check PostgreSQL logs
docker logs multi-agent-postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Issue: Kafka connection errors

```powershell
# Check Kafka and Zookeeper
docker logs multi-agent-kafka --tail 50
docker logs multi-agent-zookeeper --tail 50

# Restart Kafka
docker-compose restart kafka zookeeper
```

## Success Criteria

The system is **ONLY** ready for demo when:

1. ✅ **All Docker services** show "Up" status
2. ✅ **No ERROR/FATAL** messages in Docker logs
3. ✅ **Database connection** works
4. ✅ **All ports** are listening
5. ✅ **All agents** are running (or at least core agents)
6. ✅ **No errors** in agent log files (last 100 lines)
7. ✅ **Dashboards** are accessible
8. ✅ **No import errors**
9. ✅ **No connection timeouts**
10. ✅ **No database errors**

## Running the Verification

### Quick Verification (PowerShell)

```powershell
# Run verification script
.\verify-system.ps1

# Expected output if everything is OK:
# ============================================================
# ✓ SYSTEM VERIFICATION PASSED
# All components are running without errors!
# ============================================================
```

### Detailed Verification (with verbose output)

```powershell
.\verify-system.ps1 -Verbose
```

### Python Verification

```bash
python verify-system.py
```

## Exit Codes

- **0** - All checks passed, system is ready
- **1** - One or more checks failed, system needs fixes

## Continuous Monitoring

For ongoing monitoring during demo:

```powershell
# Watch Docker services
while ($true) {
    Clear-Host
    docker ps --format "table {{.Names}}\t{{.Status}}"
    Start-Sleep -Seconds 5
}

# Watch agent logs
Get-Content logs\agents\order_agent.log -Wait -Tail 20
```

## Before Demo Checklist

Final checklist before starting demo:

1. [ ] Run `.\verify-system.ps1` - All checks pass
2. [ ] Open Grafana (http://localhost:3000) - Dashboard loads
3. [ ] Check agent logs - No recent errors
4. [ ] Test order creation - Works successfully
5. [ ] Check database - Tables populated
6. [ ] Monitor for 5 minutes - No crashes or errors

## Support

If verification fails:

1. Check the specific error messages
2. Review the relevant log files
3. Consult the troubleshooting guides:
   - `DOCKER_FIX_GUIDE.md`
   - `POSTGRES_PERMISSION_FIX.md`
   - `IMPORT_FIX_SUMMARY.md`
   - `DEPLOYMENT_GUIDE.md`

## Summary

**DO NOT** confirm system is ready for demo until:
- ✅ Verification script shows "PASSED"
- ✅ No errors in any log files
- ✅ All services are running stably
- ✅ Manual spot checks confirm functionality

This ensures a smooth demo experience without unexpected errors.

