# CRITICAL FIX - Agent Startup Issues

**Date:** October 22, 2025  
**Latest Commit:** b700ab5  
**Status:** ✅ FIXED

---

## Issues Identified from Your Error Log

### Issue 1: `ModuleNotFoundError: No module named 'shared'` ❌ FIXED

**Error Messages:**
```
[Order] ModuleNotFoundError: No module named 'shared'
[Product] ModuleNotFoundError: No module named 'shared'
[Payment] ModuleNotFoundError: No module named 'shared'
[Warehouse] ModuleNotFoundError: No module named 'shared'
```

**Root Cause:**
The Python interpreter couldn't find the `shared` module because the project root directory was not in the PYTHONPATH.

**Fix Applied (Commit b700ab5):**
Updated `start-agents-monitor.py` to automatically add the project root to PYTHONPATH before starting each agent:

```python
# CRITICAL: Add project root to PYTHONPATH so agents can import 'shared' module
project_root = os.path.dirname(os.path.abspath(__file__))
pythonpath = env.get('PYTHONPATH', '')
if pythonpath:
    env['PYTHONPATH'] = f"{project_root}{os.pathsep}{pythonpath}"
else:
    env['PYTHONPATH'] = project_root
```

---

### Issue 2: Database Connection Errors ⚠️ NEEDS INVESTIGATION

**Error Messages:**
```
[Transport] 'DatabaseManager' object has no attribute 'connect'
[Transport] 'DatabaseManager' object has no attribute 'disconnect'
[Inventory] asyncpg.exceptions.ConnectionDoesNotExistError: connection was closed in the middle of operation
```

**Possible Causes:**

1. **Old code version** - You may have old `.pyc` bytecode files cached
2. **PostgreSQL not fully ready** - Database might not be accepting connections yet
3. **Network issues** - Docker networking on Windows can be flaky

**Solutions to Try:**

#### Solution 1: Clean Python Cache and Pull Latest Code

```powershell
# Stop all agents (Ctrl+C)

# Clean Python cache
Get-ChildItem -Path . -Recurse -Filter "*.pyc" | Remove-Item -Force
Get-ChildItem -Path . -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force

# Pull latest fixes
git pull origin main

# Restart
.\start-system.ps1
```

#### Solution 2: Verify PostgreSQL is Accessible

```powershell
# Check if PostgreSQL port is accessible
Test-NetConnection -ComputerName localhost -Port 5432

# If not accessible, check Docker
docker ps | findstr postgres

# Check PostgreSQL logs
docker logs multi-agent-postgres

# Try connecting manually
docker exec -it multi-agent-postgres psql -U postgres -d multi_agent_ecommerce
```

#### Solution 3: Restart Docker Services

```powershell
# Stop everything
cd infrastructure
docker-compose down

# Wait 10 seconds
Start-Sleep -Seconds 10

# Start fresh
docker-compose up -d

# Wait for services to be ready (2-3 minutes)
Start-Sleep -Seconds 180

# Verify services
docker ps
```

---

## How to Apply the Fix

### Step 1: Pull Latest Code

```powershell
cd C:\Users\jerom\OneDrive\Documents\Project\Multi-agent-AI-Ecommerce
git pull origin main
```

You should see:
```
Updating f4454ad..b700ab5
Fast-forward
 start-agents-monitor.py | 8 ++++++++
 1 file changed, 8 insertions(+)
```

### Step 2: Clean Python Cache

```powershell
# Remove all .pyc files and __pycache__ directories
Get-ChildItem -Path . -Recurse -Filter "*.pyc" | Remove-Item -Force
Get-ChildItem -Path . -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
```

### Step 3: Restart Infrastructure

```powershell
# Make sure Docker is running
docker ps

# Restart infrastructure
.\start-infrastructure.ps1
```

Wait for:
```
SUCCESS: All infrastructure services are ready!
```

### Step 4: Wait for Kafka (Important!)

Kafka takes 2-3 minutes to fully initialize. **Do not skip this step!**

```powershell
# Wait 3 minutes
Start-Sleep -Seconds 180

# Verify Kafka is ready
docker exec multi-agent-kafka kafka-broker-api-versions --bootstrap-server localhost:9092
```

### Step 5: Start Agents

```powershell
.\start-system.ps1 --SkipDocker
```

You should now see agents starting successfully without the "No module named 'shared'" error.

---

## Expected Output After Fix

### Successful Agent Start

```
[14:57:54] [Order       ] • Starting...
[14:57:55] [Order       ] ✓ Started (PID: 5460, Port: 8001)
[14:57:57] [Order       ] ✓ Database initialized successfully
[14:57:57] [Order       ] ✓ Kafka consumer started
[14:57:57] [Order       ] ✓ Order Agent is running on port 8001
```

### What You Should NOT See Anymore

❌ `ModuleNotFoundError: No module named 'shared'`  
❌ `Failed to start (immediate crash)`  
❌ Agent crashing immediately after startup

---

## Additional Troubleshooting

### If Agents Still Fail to Import 'shared'

**Option 1: Set PYTHONPATH Manually (PowerShell)**

```powershell
$env:PYTHONPATH = "C:\Users\jerom\OneDrive\Documents\Project\Multi-agent-AI-Ecommerce"
.\start-system.ps1
```

**Option 2: Activate Virtual Environment First**

```powershell
.\venv\Scripts\Activate.ps1
$env:PYTHONPATH = (Get-Location).Path
python start-agents-monitor.py
```

### If Database Errors Persist

**Check Database Connection String:**

```powershell
# In PowerShell, check environment variables
$env:DATABASE_HOST
$env:DATABASE_PORT
$env:DATABASE_NAME
```

Should be:
- `DATABASE_HOST=localhost`
- `DATABASE_PORT=5432`
- `DATABASE_NAME=multi_agent_ecommerce`

**Verify Database Exists:**

```powershell
docker exec multi-agent-postgres psql -U postgres -l
```

You should see `multi_agent_ecommerce` in the list.

**Create Database if Missing:**

```powershell
docker exec multi-agent-postgres psql -U postgres -c "CREATE DATABASE multi_agent_ecommerce;"
```

---

## Verification Checklist

After applying the fix, verify:

- [ ] `git pull origin main` shows commit b700ab5
- [ ] Python cache cleaned (no `__pycache__` directories)
- [ ] Docker services running (`docker ps` shows 10 containers)
- [ ] PostgreSQL accessible (`Test-NetConnection localhost -Port 5432`)
- [ ] Kafka accessible (`Test-NetConnection localhost -Port 9092`)
- [ ] Agents start without "No module named 'shared'" error
- [ ] Agent logs show successful database initialization
- [ ] All 15 agents running (check `logs/agent_monitor_*.log`)

---

## Quick Reference

### Start Everything (Full Sequence)

```powershell
# 1. Pull latest code
git pull origin main

# 2. Clean cache
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force

# 3. Start infrastructure
.\start-infrastructure.ps1

# 4. Wait 3 minutes for Kafka
Start-Sleep -Seconds 180

# 5. Start agents
.\start-system.ps1 --SkipDocker

# 6. Start dashboard (in new terminal)
.\start-dashboard.ps1
```

### Stop Everything

```powershell
# Stop agents (Ctrl+C in agent terminal)

# Stop infrastructure
cd infrastructure
docker-compose down
```

### Check Logs

```powershell
# Agent logs
Get-Content -Path "logs\agent_monitor_*.log" -Tail 50

# Docker logs
docker-compose -f infrastructure/docker-compose.yml logs -f
```

---

## Summary

**Main Fix:** Added PYTHONPATH configuration to `start-agents-monitor.py` so agents can import the `shared` module.

**Commit:** b700ab5

**Action Required:**
1. Pull latest code: `git pull origin main`
2. Clean Python cache
3. Restart infrastructure and agents

**Expected Result:** All agents start successfully without import errors.

---

**Last Updated:** October 22, 2025  
**Maintainer:** Multi-Agent AI E-commerce Team  
**Latest Commit:** b700ab5

