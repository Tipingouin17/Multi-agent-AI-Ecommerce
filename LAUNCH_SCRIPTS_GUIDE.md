# 🚀 Launch Scripts Quick Reference Guide

## Overview

This guide explains how to use the platform launch scripts and what to expect.

---

## Windows Scripts

### StartPlatform.bat - Master Launcher

**Purpose:** One-command launcher for the entire platform

**What it does:**
1. ✅ Checks prerequisites (Python, Node.js, npm, Docker)
2. ✅ Starts Docker infrastructure (PostgreSQL, Redis, Kafka, Grafana)
3. ✅ Waits for services to be healthy
4. ✅ Launches all 42 agents via StartAllAgents.bat
5. ✅ Starts frontend UI (Vite dev server)
6. ✅ Starts ngrok for external access (optional)
7. ✅ Opens browser to http://localhost:5173

**Usage:**
```cmd
StartPlatform.bat
```

**Expected Behavior:**
1. Console window opens showing startup progress
2. Each step displays status messages
3. Browser opens automatically when ready
4. Console shows "Press any key to close this window..."
5. **Press any key** - Console closes, agents continue running in background
6. Platform is ready at http://localhost:5173

**Important Notes:**
- ✅ Agents run in background after console closes
- ✅ Console closing does NOT stop the agents
- ✅ Use `StopAllAgents.bat` to stop agents when done

---

### StartAllAgents.bat - Agent Launcher

**Purpose:** Launches all 42 backend agents

**What it does:**
1. ✅ Creates log directory
2. ✅ Starts all 42 agents in background
3. ✅ Assigns correct ports to each agent
4. ✅ Redirects logs to individual files
5. ✅ Displays port mapping
6. ✅ Exits cleanly

**Usage:**
```cmd
StartAllAgents.bat
```

**Expected Behavior:**
1. Shows "Starting All 42 V3 Agents..."
2. Lists each agent as it starts
3. Displays port mapping
4. Exits automatically (no pause)
5. Agents continue running in background

**Log Files Location:**
```
logs/agents/
  ├── auth_agent.log
  ├── order_agent.log
  ├── product_agent.log
  ├── offers_agent.log
  ├── advertising_agent.log
  └── ... (42 total)
```

---

### StopAllAgents.bat - Agent Stopper

**Purpose:** Cleanly stops all running agents

**What it does:**
1. ✅ Counts running Python processes
2. ✅ Stops all Python agent processes
3. ✅ Displays success message
4. ✅ Exits automatically

**Usage:**
```cmd
StopAllAgents.bat
```

**Expected Behavior:**
1. Shows "Stopping All 42 Agents..."
2. Counts running processes
3. Stops all Python processes
4. Shows "✓ All agent processes stopped successfully!"
5. Exits automatically

**When to use:**
- When you're done using the platform
- Before restarting the platform
- When troubleshooting agent issues
- Before system shutdown

---

### StopPlatform.bat - Complete Shutdown

**Purpose:** Stops everything (agents + Docker infrastructure)

**What it does:**
1. ✅ Stops all agents (calls StopAllAgents.bat)
2. ✅ Stops Docker Compose services
3. ✅ Stops frontend UI
4. ✅ Cleans up processes

**Usage:**
```cmd
StopPlatform.bat
```

---

## Linux/Mac Scripts

### master_launch.sh - Master Launcher

**Purpose:** Comprehensive launcher with monitoring

**What it does:**
1. ✅ Creates comprehensive logs
2. ✅ Checks infrastructure health
3. ✅ Starts 30 core agents
4. ✅ Provides real-time status updates
5. ✅ Tracks processes

**Usage:**
```bash
./master_launch.sh
# or with verbose output
./master_launch.sh --verbose
```

**Expected Behavior:**
1. Shows colored status messages
2. Logs everything to `logs/master/startup_*.log`
3. Starts agents one by one
4. Displays health checks
5. Exits when complete

---

## Common Issues & Solutions

### Issue 1: Console Hangs After Pressing Key ✅ FIXED

**Symptoms:**
- Press any key at end of script
- Console doesn't close
- Appears stuck

**Solution:**
- ✅ Fixed in latest version (commit 2503400)
- Pull latest code: `git pull origin main`
- Console now closes cleanly
- Agents continue running in background

---

### Issue 2: Agents Not Starting

**Symptoms:**
- Script completes but agents not responding
- Health checks fail

**Diagnosis:**
```cmd
REM Check if agents are running
tasklist | findstr python

REM Check agent logs
type logs\agents\offers_agent.log
```

**Solutions:**
1. Check Python is installed: `python --version`
2. Check dependencies: `pip install -r requirements.txt`
3. Check database is running: `docker ps`
4. Check ports are available: `netstat -ano | findstr "8040"`

---

### Issue 3: Port Already in Use

**Symptoms:**
- Agent fails to start
- Error: "Address already in use"

**Solution:**
```cmd
REM Find process using port 8040
netstat -ano | findstr "8040"

REM Kill process (replace PID with actual process ID)
taskkill /F /PID <PID>

REM Restart agent
StartAllAgents.bat
```

---

### Issue 4: Docker Not Running

**Symptoms:**
- "Docker is not running" error
- PostgreSQL connection fails

**Solution:**
1. Start Docker Desktop
2. Wait for Docker to be ready
3. Run `StartPlatform.bat` again

---

## Verification Commands

### Check All Agents Are Running

```cmd
REM Windows
curl http://localhost:8040/health
curl http://localhost:8041/health
curl http://localhost:8042/health
curl http://localhost:8043/health

REM Or check all at once
FOR /L %i IN (8040,1,8043) DO @curl -s http://localhost:%i/health
```

```bash
# Linux/Mac
for port in 8040 8041 8042 8043; do
  echo "=== Port $port ==="
  curl -s http://localhost:$port/health | python3 -m json.tool
done
```

### Check Agent Logs

```cmd
REM Windows - View specific agent log
type logs\agents\offers_agent.log

REM View last 20 lines
powershell Get-Content logs\agents\offers_agent.log -Tail 20
```

```bash
# Linux/Mac
tail -f logs/agents/offers_agent.log
```

### Check Process Count

```cmd
REM Windows
tasklist | findstr python | find /c /v ""
```

```bash
# Linux/Mac
ps aux | grep python | grep agent | wc -l
```

---

## Best Practices

### Starting the Platform

1. ✅ Always use `StartPlatform.bat` (not individual scripts)
2. ✅ Wait for "Platform is ready!" message
3. ✅ Check browser opens automatically
4. ✅ Press any key to close console
5. ✅ Verify agents at http://localhost:8100/api/agents

### Stopping the Platform

1. ✅ Use `StopAllAgents.bat` (not Ctrl+C)
2. ✅ Wait for confirmation message
3. ✅ Verify all processes stopped
4. ✅ Use `StopPlatform.bat` for complete shutdown

### Troubleshooting

1. ✅ Always check logs first: `logs/agents/*.log`
2. ✅ Verify Docker is running: `docker ps`
3. ✅ Check database connection: `psql -h localhost -U postgres`
4. ✅ Test individual agents: `curl http://localhost:8040/health`
5. ✅ Restart if needed: `StopAllAgents.bat` then `StartPlatform.bat`

---

## Port Reference

### World-Class Agents (8040-8043)
```
8040 - offers_agent_v3        (Offers Management)
8041 - advertising_agent_v3   (Advertising Campaigns)
8042 - supplier_agent_v3      (Supplier Management)
8043 - marketplace_agent_v3   (Marketplace Integration)
```

### Core Agents (8000-8029)
```
8000 - order_agent
8001 - product_agent
8002 - inventory_agent
8003 - marketplace_connector
8004 - payment_agent
8005 - dynamic_pricing
8006 - carrier_agent
8007 - customer_agent
8008 - warehouse_agent
8009 - returns_agent
8010 - fraud_detection
8011 - risk_anomaly_detection
8012 - knowledge_management
8013 - analytics_agent
8014 - recommendation_agent
8015 - transport_management
8016 - document_generation
8017 - auth_agent
8018 - support_agent
8019 - customer_communication
8020 - promotion_agent
8021 - after_sales_agent
8022 - infrastructure
8023 - monitoring_agent
8024 - ai_monitoring
8026 - d2c_ecommerce
8027 - backoffice_agent
8028 - quality_control
```

### Feature Agents (8031-8038)
```
8031 - replenishment_agent
8032 - inbound_management_agent
8033 - fulfillment_agent
8034 - carrier_agent_ai
8035 - rma_agent
8036 - advanced_analytics_agent
8037 - demand_forecasting_agent
8038 - international_shipping_agent
```

### Infrastructure (8100)
```
8100 - system_api_gateway
```

### Frontend (5173)
```
5173 - Vite Dev Server (Frontend UI)
```

---

## Quick Commands Cheat Sheet

```cmd
REM === WINDOWS ===

REM Start everything
StartPlatform.bat

REM Start only agents
StartAllAgents.bat

REM Stop agents
StopAllAgents.bat

REM Stop everything
StopPlatform.bat

REM Check agent health
curl http://localhost:8040/health

REM View logs
type logs\agents\offers_agent.log

REM Count running agents
tasklist | findstr python | find /c /v ""
```

```bash
# === LINUX/MAC ===

# Start everything
./master_launch.sh

# Start with verbose output
./master_launch.sh --verbose

# Check agent health
curl http://localhost:8040/health

# View logs
tail -f logs/agents/offers_agent.log

# Count running agents
ps aux | grep python | grep agent | wc -l
```

---

## Support

If you encounter issues:

1. **Check logs:** `logs/agents/*.log`
2. **Check documentation:** See other guides in repository
3. **Restart platform:** `StopAllAgents.bat` then `StartPlatform.bat`
4. **Verify prerequisites:** Python, Node.js, Docker all installed

---

## Summary

✅ **StartPlatform.bat** - Start everything (recommended)  
✅ **StartAllAgents.bat** - Start only agents  
✅ **StopAllAgents.bat** - Stop agents cleanly  
✅ **StopPlatform.bat** - Stop everything  

**Key Point:** Console closing does NOT stop agents - they run in background!

**To stop agents:** Use `StopAllAgents.bat`

---

**Last Updated:** November 20, 2025  
**Version:** 1.0  
**Status:** ✅ Console hanging issue fixed
