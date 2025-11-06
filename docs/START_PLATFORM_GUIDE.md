# StartPlatform Scripts - Complete Guide

## Overview

The Multi-Agent E-commerce Platform includes comprehensive startup scripts for both **Linux/Mac** and **Windows** environments. These scripts launch all 37 agents (8 feature + 29 core) and the frontend dashboard with a single command.

---

## 📋 Available Scripts

### Linux / Mac

| Script | Purpose |
|--------|---------|
| `start_platform.sh` | Complete system launcher (Docker + DB + 37 Agents + Frontend) |
| `start_all_agents.sh` | Launch all 37 agents only |
| `launch_all_agents.sh` | Alternative launcher with detailed logging |
| `launch_all_features.sh` | Launch only the 8 feature agents |
| `stop_all_agents.sh` | Stop all agent processes |
| `stop_platform.sh` | Stop entire platform |

### Windows

| Script | Purpose |
|--------|---------|
| `StartPlatform.bat` | Complete system launcher (DB + 37 Agents + Frontend) |
| `StartAllAgents.bat` | Launch all 37 agents only |
| `StopAllAgents.bat` | Stop all agent processes |
| `StopPlatform.bat` | Stop entire platform |

---

## 🚀 Quick Start

### Linux / Mac

```bash
# Complete platform startup (recommended)
./start_platform.sh

# Or just agents + frontend (if Docker already running)
./start_platform.sh --skip-docker

# Or just the 37 agents
./start_all_agents.sh

# Or just the 8 feature agents
./launch_all_features.sh
```

### Windows

```batch
REM Complete platform startup (recommended)
StartPlatform.bat

REM Or skip database initialization (if already done)
StartPlatform.bat --skip-db-init

REM Or just the 37 agents
StartAllAgents.bat
```

---

## 📊 What Gets Started

### All 37 Agents

#### Core Business Agents (8)
- Port 8000: Order Agent
- Port 8001: Product Agent
- Port 8002: Inventory Agent
- Port 8004: Payment Agent
- Port 8006: Carrier Agent
- Port 8007: Customer Agent
- Port 8009: Returns Agent
- Port 8010: Fraud Detection Agent

#### Marketplace & Integration Agents (5)
- Port 8003: Marketplace Connector
- Port 8005: Dynamic Pricing
- Port 8014: Recommendation Agent
- Port 8020: Promotion Agent
- Port 8026: D2C E-commerce Agent

#### Operations & Support Agents (8)
- Port 8008: Warehouse Agent
- Port 8015: Transport Management
- Port 8016: Document Generation
- Port 8018: Support Agent
- Port 8019: Customer Communication
- Port 8021: After-Sales Agent
- Port 8027: Backoffice Agent
- Port 8028: Quality Control Agent

#### Analytics & Reporting Agents (2)
- Port 8013: Analytics Agent
- Port 8036: Advanced Analytics Agent

#### Infrastructure & Monitoring Agents (6)
- Port 8011: Risk & Anomaly Detection
- Port 8012: Knowledge Management
- Port 8022: Infrastructure Agent
- Port 8023: Monitoring Agent
- Port 8024: AI Monitoring Agent
- Port 8100: System API Gateway

#### Feature Agents - Priority 1 & 2 (8)
- Port 8031: **Inventory Replenishment** (Feature 1)
- Port 8032: **Inbound Management** (Feature 2)
- Port 8033: **Advanced Fulfillment** (Feature 3)
- Port 8034: **Intelligent Carrier Selection with AI** (Feature 4)
- Port 8035: **Complete RMA Workflow** (Feature 5)
- Port 8036: **Advanced Analytics & Reporting** (Feature 6)
- Port 8037: **ML-Based Demand Forecasting** (Feature 7)
- Port 8038: **International Shipping** (Feature 8)

### Frontend Dashboard
- Port 5173: React + Vite Development Server

### Infrastructure (Linux only with Docker)
- Port 5432: PostgreSQL
- Port 6379: Redis
- Port 9092: Kafka
- Port 9090: Prometheus
- Port 3000: Grafana

---

## 🔧 Script Options

### start_platform.sh (Linux/Mac)

```bash
./start_platform.sh [options]

Options:
  --skip-docker    Skip Docker infrastructure startup (if already running)
  --skip-db-init   Skip database initialization (if already done)
  --dev            Start with development tools (pgAdmin, Kafka UI)
  --full           Start with all optional services
```

**Examples:**

```bash
# First time startup (complete)
./start_platform.sh

# Subsequent startups (skip Docker if already running)
./start_platform.sh --skip-docker --skip-db-init

# Development mode with extra tools
./start_platform.sh --dev

# Full mode with all services
./start_platform.sh --full
```

### StartPlatform.bat (Windows)

```batch
StartPlatform.bat [options]

Options:
  --skip-db-init   Skip database initialization (if already done)
```

**Examples:**

```batch
REM First time startup
StartPlatform.bat

REM Subsequent startups (skip DB init)
StartPlatform.bat --skip-db-init
```

---

## ✅ Verification

### Check Agent Health

```bash
# Linux/Mac
curl http://localhost:8100/api/agents

# Windows (PowerShell)
Invoke-WebRequest http://localhost:8100/api/agents

# Or use browser
# Open: http://localhost:8100/api/agents
```

### Check Individual Agent

```bash
# Check specific agent health
curl http://localhost:8031/health  # Replenishment
curl http://localhost:8032/health  # Inbound Management
curl http://localhost:8033/health  # Fulfillment
curl http://localhost:8034/health  # Carrier AI
curl http://localhost:8035/health  # RMA
curl http://localhost:8036/health  # Advanced Analytics
curl http://localhost:8037/health  # Demand Forecasting
curl http://localhost:8038/health  # International Shipping
```

### Access Frontend

Open browser to: **http://localhost:5173**

---

## 🛑 Stopping the Platform

### Linux / Mac

```bash
# Stop entire platform
./stop_platform.sh

# Or just agents
./stop_all_agents.sh

# Or manually
pkill -f "python3.11.*agent"
```

### Windows

```batch
REM Stop entire platform
StopPlatform.bat

REM Or just agents
StopAllAgents.bat
```

---

## 📁 Log Files

### Linux / Mac

```
logs/agents/           - Individual agent logs
logs/all_agents/       - Comprehensive launch logs
logs/frontend.log      - Frontend development server log
```

### Windows

```
logs\agents\           - Individual agent logs
logs\frontend.log      - Frontend development server log
```

**View logs:**

```bash
# Linux/Mac
tail -f logs/agents/replenishment_agent_v3.log
tail -f logs/frontend.log

# Windows
type logs\agents\replenishment_agent_v3.log
type logs\frontend.log
```

---

## ⚠️ Troubleshooting

### Issue: Agents fail to start

**Solution:**
1. Check Python version: `python3.11 --version`
2. Check logs: `tail -f logs/agents/*.log`
3. Verify PostgreSQL is running
4. Check port availability: `netstat -tlnp | grep 80`

### Issue: Frontend fails to start

**Solution:**
1. Check Node.js version: `node --version` (should be 22+)
2. Install dependencies: `cd multi-agent-dashboard && npm install`
3. Check logs: `tail -f logs/frontend.log`
4. Verify port 5173 is available

### Issue: Database connection errors

**Solution:**
1. Check PostgreSQL status: `systemctl status postgresql` (Linux) or Services (Windows)
2. Verify database exists: `psql -U postgres -l | grep multi_agent_ecommerce`
3. Check connection: `psql -h localhost -U postgres -d multi_agent_ecommerce`
4. Review environment variables

### Issue: Port already in use

**Solution:**
1. Find process: `lsof -i :8031` (Linux) or `netstat -ano | findstr :8031` (Windows)
2. Kill process: `kill -9 <PID>` (Linux) or `taskkill /PID <PID> /F` (Windows)
3. Restart agent

---

## 🔍 Health Check Commands

### Quick Health Check

```bash
# Linux/Mac
for port in {8031..8038}; do
  echo "Port $port: $(curl -s http://localhost:$port/health | jq -r .status)"
done

# Windows (PowerShell)
8031..8038 | ForEach-Object {
  $port = $_
  $response = Invoke-WebRequest "http://localhost:$port/health" -UseBasicParsing
  Write-Host "Port $port: $($response.Content)"
}
```

### Comprehensive Check

```bash
# Linux/Mac
./check_agents_status.sh

# Or manually check all ports
for port in {8000..8100}; do
  if nc -z localhost $port 2>/dev/null; then
    echo "✓ Port $port is active"
  fi
done
```

---

## 📊 Expected Startup Time

| Component | Time |
|-----------|------|
| PostgreSQL | 5-10 seconds |
| All 37 Agents | 30-60 seconds |
| Frontend UI | 10-20 seconds |
| **Total** | **45-90 seconds** |

---

## 🎯 Best Practices

### First Time Setup

1. **Start with complete platform:**
   ```bash
   ./start_platform.sh  # Linux/Mac
   StartPlatform.bat    # Windows
   ```

2. **Wait for all services to be ready** (45-90 seconds)

3. **Verify health:**
   ```bash
   curl http://localhost:8100/api/agents
   ```

4. **Access frontend:**
   Open http://localhost:5173

### Daily Development

1. **Use skip options for faster startup:**
   ```bash
   ./start_platform.sh --skip-docker --skip-db-init
   ```

2. **Or start only what you need:**
   ```bash
   ./launch_all_features.sh  # Just the 8 feature agents
   ```

3. **Monitor logs during development:**
   ```bash
   tail -f logs/agents/carrier_agent_ai_v3.log
   ```

### Production Deployment

1. **Use systemd services** (Linux) or **Windows Services** for automatic startup
2. **Configure proper logging** with log rotation
3. **Set up monitoring** (Prometheus + Grafana)
4. **Use environment variables** for configuration
5. **Implement health checks** with automatic restart

---

## 🔗 Related Documentation

- **FINAL_HANDOFF_DOCUMENTATION.md** - Complete production guide
- **PRODUCTION_DEPLOYMENT_GUIDE.md** - Deployment instructions
- **PLATFORM_CAPABILITIES.md** - Feature overview
- **Feature Specifications (F1-F8)** - Detailed feature docs

---

## 💡 Tips

1. **Always check logs** if something doesn't work
2. **Use health endpoints** to verify agent status
3. **Start with complete platform** first time, then use skip options
4. **Monitor resource usage** (RAM, CPU) during development
5. **Use separate terminals** for logs and commands

---

## ✅ Success Indicators

After running the startup script, you should see:

- ✅ All 37 agents started (check logs)
- ✅ Frontend accessible at http://localhost:5173
- ✅ API Gateway responding at http://localhost:8100
- ✅ Health checks passing for all agents
- ✅ No errors in log files

---

## 🎉 Ready to Go!

Your Multi-Agent E-commerce Platform is now ready to use. Simply run:

```bash
# Linux/Mac
./start_platform.sh

# Windows
StartPlatform.bat
```

Then open **http://localhost:5173** and start exploring!

---

**Last Updated:** November 5, 2025  
**Version:** 3.0.0  
**Status:** Production Ready
