# Complete Startup Guide - Multi-Agent E-commerce System

## Prerequisites

- ✅ Docker Desktop installed and running
- ✅ Python 3.11+ installed
- ✅ Git installed
- ✅ PowerShell (Windows) or Bash (Linux/Mac)

---

## Step-by-Step Startup Process

### Step 1: Get Latest Code

```powershell
cd Multi-agent-AI-Ecommerce
git pull origin main
```

**What this does**: Gets all the latest fixes including Kafka compatibility, database initialization, and topic creation scripts.

---

### Step 2: Install Python Dependencies

```powershell
# Activate your virtual environment
.\venv\Scripts\Activate.ps1

# Install/upgrade dependencies
pip install -r requirements.txt
pip install kafka-python  # For Kafka topic management
```

---

### Step 3: Configure Environment Variables

Update your `.env` file with correct values:

```env
# Database Configuration (must match docker-compose.yml)
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=multi_agent_ecommerce
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres123

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=127.0.0.1:9092

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis123

# OpenAI API Key (required for AI agents)
OPENAI_API_KEY=your_openai_api_key_here
```

**Important**: The database password must be `postgres123` to match docker-compose.yml, or update docker-compose.yml to match your password.

---

### Step 4: Start Infrastructure Services

```powershell
.\start-infrastructure.ps1
```

**What this does**:
- Starts PostgreSQL database
- Starts Kafka message broker
- Starts Redis cache
- Starts monitoring stack (Prometheus, Grafana, Loki)

**Expected output**:
```
SUCCESS: Docker is running
SUCCESS: Infrastructure services started
SUCCESS: All infrastructure services are ready!
```

**Verify services are running**:
```powershell
docker ps
```

You should see 9 containers running (all with "healthy" status):
- multi-agent-postgres
- multi-agent-kafka
- multi-agent-zookeeper
- multi-agent-redis
- multi-agent-prometheus
- multi-agent-grafana
- multi-agent-loki
- multi-agent-promtail
- multi-agent-nginx

---

### Step 5: Initialize Database Tables

```powershell
python init_database.py
```

**What this does**: Creates all required database tables (orders, products, inventory, warehouses, carriers, etc.)

**Expected output**:
```
======================================================================
Multi-Agent E-commerce System - Database Initialization
======================================================================

Database Configuration:
  Host: localhost
  Port: 5432
  Database: multi_agent_ecommerce
  User: postgres

SUCCESS: Database connection established
SUCCESS: All tables created successfully!
```

**If it fails**:
- Check PostgreSQL is running: `docker ps | findstr postgres`
- Check password matches: `.env` should have `DATABASE_PASSWORD=postgres123`
- Check database exists: `docker exec -it multi-agent-postgres psql -U postgres -l`

---

### Step 6: Create Kafka Topics

```powershell
python init_kafka_topics.py
```

**What this does**: Creates all Kafka topics needed for inter-agent communication.

**Expected output**:
```
======================================================================
Multi-Agent E-commerce System - Kafka Topics Initialization
======================================================================

Kafka Configuration:
  Bootstrap Servers: localhost:9092

SUCCESS: Connected to Kafka

Creating 18 topics...

  SUCCESS: Created topic 'order_agent_topic'
  SUCCESS: Created topic 'product_agent_topic'
  ...

Topic initialization complete!
  Created: 18 topics
```

**If it fails**:
- Check Kafka is running: `docker ps | findstr kafka`
- Check Kafka logs: `docker logs multi-agent-kafka`
- Wait 30 seconds after starting infrastructure, then try again

---

### Step 7: Start All Agents

```powershell
.\start-system.ps1
```

**What this does**: Starts all 14 agents in the correct order.

**Expected output**:
```
======================================================================
Multi-Agent E-commerce System - Unified Monitor
======================================================================

Starting all agents... Press Ctrl+C to stop

[20:00:00] [AI Monitor  ] ✓ Started (PID: 12345)
Progress: 1/14 agents started

[20:00:02] [Product     ] ✓ Started (PID: 12346)
Progress: 2/14 agents started

...

Progress: 14/14 agents started

All agents started successfully!
```

**You may see deprecation warnings** - these are normal and don't affect functionality:
- `on_event is deprecated` - FastAPI warning (agents still work)
- `Field "model_id" has conflict` - Pydantic warning (harmless)

---

### Step 8: Start Dashboard (Optional)

```powershell
.\start-dashboard.ps1
```

**What this does**: Starts the React dashboard for monitoring agents.

**Expected output**:
```
============================================================
   Multi-Agent E-commerce Dashboard Launcher
============================================================

SUCCESS: Node.js version: v21.7.1
SUCCESS: Changed to dashboard directory
SUCCESS: Found: src/lib/api.js
SUCCESS: Found: src/App.jsx
SUCCESS: Found: vite.config.js
SUCCESS: Found: package.json
SUCCESS: Detected 14/14 agents running

============================================================
SUCCESS: Starting dashboard on http://localhost:5173
============================================================
```

**Access the dashboard**: Open http://localhost:5173 in your browser

---

## Troubleshooting

### Issue: "Docker is not running"

**Solution**:
1. Open Docker Desktop
2. Wait for it to fully start (whale icon steady in system tray)
3. Run `docker ps` to verify
4. Try again

### Issue: "Database connection failed"

**Causes**:
- Wrong password in `.env`
- PostgreSQL container not running
- Database doesn't exist

**Solutions**:
```powershell
# Check PostgreSQL is running
docker ps | findstr postgres

# Check if it's healthy
docker inspect multi-agent-postgres | findstr Health

# Check logs
docker logs multi-agent-postgres

# Connect manually to verify
docker exec -it multi-agent-postgres psql -U postgres -d multi_agent_ecommerce
```

### Issue: "Kafka connection errors"

**Causes**:
- Kafka not fully started
- Topics not created
- Wrong Kafka address

**Solutions**:
```powershell
# Check Kafka is running
docker ps | findstr kafka

# Check Kafka logs
docker logs multi-agent-kafka

# Wait 30 seconds after starting, then try:
python init_kafka_topics.py

# Verify topics exist
docker exec -it multi-agent-kafka kafka-topics --bootstrap-server localhost:9092 --list
```

### Issue: "UnrecognizedBrokerVersion"

**Cause**: Old code without Kafka compatibility fix

**Solution**:
```powershell
git pull origin main
```

The fix adds `api_version='auto'` to Kafka clients.

### Issue: "AI agents crashing"

**Causes**:
- Missing OpenAI API key
- Invalid API key
- Database tables not created

**Solutions**:
1. Add OpenAI API key to `.env`:
   ```env
   OPENAI_API_KEY=sk-...your-key-here...
   ```

2. Verify database tables exist:
   ```powershell
   python init_database.py
   ```

3. Check agent logs for specific errors

### Issue: "Agents keep restarting"

**Cause**: Startup errors causing crash loop

**Solution**:
1. Stop all agents: Press `Ctrl+C` in the terminal running start-system.ps1
2. Check what's failing:
   - Database initialized? `python init_database.py`
   - Kafka topics created? `python init_kafka_topics.py`
   - OpenAI key set? Check `.env`
3. Fix the issue
4. Start again: `.\start-system.ps1`

---

## Verification Checklist

After completing all steps, verify:

- [ ] Docker containers running: `docker ps` shows 9 healthy containers
- [ ] Database tables created: `python init_database.py` succeeds
- [ ] Kafka topics created: `python init_kafka_topics.py` succeeds
- [ ] All 14 agents started: `start-system.ps1` shows "14/14 agents started"
- [ ] No crash loops: Agents stay running without restarting
- [ ] Dashboard accessible: http://localhost:5173 loads

---

## Monitoring & Management

### View Agent Logs

Logs are displayed in the terminal running `start-system.ps1`.

### Stop All Agents

Press `Ctrl+C` in the terminal running `start-system.ps1`.

### Stop Infrastructure

```powershell
docker-compose -f infrastructure/docker-compose.yml down
```

### Restart Everything

```powershell
# Stop agents (Ctrl+C)

# Restart infrastructure
docker-compose -f infrastructure/docker-compose.yml restart

# Wait 30 seconds

# Start agents again
.\start-system.ps1
```

### Access Monitoring Tools

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100

---

## Quick Reference

### Complete Startup (First Time)

```powershell
# 1. Get code
git pull origin main

# 2. Install dependencies
pip install -r requirements.txt
pip install kafka-python

# 3. Start infrastructure
.\start-infrastructure.ps1

# 4. Initialize database
python init_database.py

# 5. Create Kafka topics
python init_kafka_topics.py

# 6. Start agents
.\start-system.ps1

# 7. Start dashboard (optional)
.\start-dashboard.ps1
```

### Subsequent Startups

```powershell
# 1. Start infrastructure (if not running)
.\start-infrastructure.ps1

# 2. Start agents
.\start-system.ps1

# 3. Start dashboard (optional)
.\start-dashboard.ps1
```

---

## Support

If you encounter issues not covered here:

1. Check the detailed guides:
   - `INFRASTRUCTURE_SETUP_GUIDE.md`
   - `FASTAPI_DEPRECATION_GUIDE.md`
   - `FIX_VERIFICATION_REPORT.md`

2. Check GitHub issues: https://github.com/Tipingouin17/Multi-agent-AI-Ecommerce/issues

3. Review commit history for recent fixes: `git log --oneline`

---

**Last Updated**: October 19, 2025  
**System Version**: All fixes applied (commit e7ee64b)  
**Status**: Production Ready ✅

