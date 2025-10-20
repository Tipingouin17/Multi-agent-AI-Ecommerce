# System Startup Guide

## Quick Start

### Windows (Batch File)
```cmd
start-system.bat
```

### Windows (PowerShell)
```powershell
.\start-system.ps1
```

### Linux/Mac
```bash
python start-agents-monitor.py
```

## What Happens

The startup script performs these steps automatically:

### 1. ✅ Virtual Environment
- Activates Python virtual environment
- Ensures all dependencies are available

### 2. ✅ Docker Infrastructure
- Checks Docker is running
- Starts all services:
  - PostgreSQL (database)
  - Kafka (message broker)
  - Redis (cache)
  - Zookeeper (Kafka dependency)
  - Prometheus (metrics)
  - Grafana (dashboards)
  - Loki (log aggregation)
  - Promtail (log shipper)
  - Nginx (reverse proxy)
- Waits 15 seconds for initialization

### 3. ✅ Database Verification
- Tests PostgreSQL connection
- Creates database if needed
- Verifies database is ready

### 4. ✅ Agent Startup (Unified Monitor)
- Starts all 14 agents in one console
- **Color-coded output** for each agent
- **Real-time monitoring** of all agent logs
- **Error detection** and highlighting
- **Status tracking** for each agent

## Unified Monitor Features

### Color-Coded Output

Each agent has its own color for easy identification:

- 🔵 **Blue** - Order Agent
- 🟢 **Green** - Inventory Agent  
- 🔷 **Cyan** - Product Agent
- 🟣 **Magenta** - Carrier Selection Agent
- 🟡 **Yellow** - Warehouse Selection Agent
- 🔴 **Red** - Customer Communication Agent
- And more...

### Message Types

Messages are automatically categorized:

- ✓ **Green** - Success messages (started, ready, success)
- ✗ **Red** - Error messages (error, exception, failed)
- ⚠ **Yellow** - Warning messages (warning, warn)
- • **White** - Info messages (everything else)

### Output Format

```
[HH:MM:SS] [AgentName    ] • Message
[10:30:45] [Order        ] ✓ Agent started successfully
[10:30:46] [Inventory    ] • Processing inventory update
[10:30:47] [Carrier      ] ✗ API connection failed
```

### Real-Time Monitoring

- **Live output** from all agents in one window
- **Error counting** per agent
- **Uptime tracking** for each agent
- **Crash detection** with automatic alerts
- **Status summary** on exit

## Available Scripts

### Main Scripts

| Script | Purpose | Use When |
|--------|---------|----------|
| `start-system.bat` | Complete startup (Windows) | Starting everything |
| `start-system.ps1` | Complete startup (PowerShell) | Starting everything |
| `start-agents-monitor.py` | Agents only with monitoring | Docker already running |
| `agents/start_agents.py` | Agents only (separate windows) | Need individual windows |

### Utility Scripts

| Script | Purpose |
|--------|---------|
| `verify-system.ps1` | Verify all components working |
| `shutdown-all.ps1` | Stop everything cleanly |
| `setup-database.bat` | Initialize database |

### Removed Scripts (Outdated)

These scripts have been removed and replaced:

- ~~`start-demo.bat`~~ → Use `start-system.bat`
- ~~`start-simple.bat`~~ → Use `start-system.bat`
- ~~`start-system-fixed.bat`~~ → Use `start-system.bat`

## Usage Examples

### Basic Startup

```powershell
# Start everything
.\start-system.ps1

# Wait for "All agents started! Monitoring output..."
# Watch the color-coded logs
# Press Ctrl+C when done
```

### Skip Docker (Already Running)

```powershell
# If Docker services already running
python start-agents-monitor.py
```

### PowerShell Options

```powershell
# Skip Docker startup
.\start-system.ps1 -SkipDocker

# Skip waiting period
.\start-system.ps1 -SkipWait

# Both
.\start-system.ps1 -SkipDocker -SkipWait
```

### Verify After Startup

```powershell
# In another terminal, verify everything is working
.\verify-system.ps1 -Verbose
```

## Stopping the System

### Stop Agents

Press `Ctrl+C` in the monitor window

This will:
1. Stop all agents gracefully
2. Show final status summary
3. Display error counts
4. Return to command prompt

### Stop Docker Services

```powershell
cd infrastructure
docker-compose down
```

Or use the shutdown script:

```powershell
.\shutdown-all.ps1
```

## Monitoring During Operation

### View Status Summary

Press `Ctrl+C` to stop agents and see status:

```
============================================================
Agent Status Summary
============================================================

Order                ✓ Running  PID: 12345  Uptime: 120s  No errors
Inventory            ✓ Running  PID: 12346  Uptime: 118s  No errors
Product              ✓ Running  PID: 12347  Uptime: 116s  No errors
Carrier              ✓ Running  PID: 12348  Uptime: 114s  2 errors
...

Total: 14  Running: 14  Stopped: 0
```

### Watch Specific Agent

All output is in one window, just look for the agent's color and name.

### Check for Errors

Errors are automatically highlighted in **red** with ✗ symbol.

## Troubleshooting

### Issue: Docker not running

```
[ERROR] Docker is not running!
```

**Solution**: Start Docker Desktop and try again.

### Issue: Port already in use

```
[WARNING] Port 5432 is already in use
```

**Solution**: 
```powershell
# Stop local PostgreSQL if running
Stop-Service postgresql-x64-18

# Or change port in docker-compose.yml
```

### Issue: Agent fails to start

Look for red error messages with the agent's color:

```
[10:30:45] [Order        ] ✗ ImportError: cannot import name 'APIResponse'
```

**Solution**: Check the error message and fix the issue, then restart.

### Issue: Database connection failed

```
[WARNING] Database connection failed
```

**Solution**: Script will automatically create database. If still failing:

```powershell
docker logs multi-agent-postgres
```

## Best Practices

### Before Starting

1. ✅ Ensure Docker Desktop is running
2. ✅ Close other applications using ports 5432, 9092, 6379, 3000
3. ✅ Have `.env` file configured
4. ✅ Virtual environment created and dependencies installed

### During Operation

1. 📊 Watch for red error messages
2. 📊 Monitor agent status
3. 📊 Check Grafana dashboard (http://localhost:3000)
4. 📊 Keep terminal window visible

### After Stopping

1. 🔍 Review error counts in status summary
2. 🔍 Check log files if errors occurred
3. 🔍 Run verification: `.\verify-system.ps1`
4. 🔍 Stop Docker if not needed: `docker-compose down`

## Advanced Usage

### Start Specific Agents Only

Edit `start-agents-monitor.py` and comment out agents you don't need:

```python
AGENTS = [
    {"name": "order_agent", "display": "Order", "file": "agents/order_agent.py"},
    {"name": "inventory_agent", "display": "Inventory", "file": "agents/inventory_agent.py"},
    # Comment out agents you don't need
    # {"name": "d2c_ecommerce_agent", "display": "D2C", "file": "agents/d2c_ecommerce_agent.py"},
]
```

### Custom Startup Delay

Edit the delay in `start-agents-monitor.py`:

```python
time.sleep(2)  # Change to desired seconds between agent starts
```

### Monitor Logs to File

```powershell
python start-agents-monitor.py | Tee-Object -FilePath startup-log.txt
```

## Summary

**One command starts everything:**

```powershell
.\start-system.ps1
```

**Features:**
- ✅ Automatic Docker infrastructure startup
- ✅ Database verification and creation
- ✅ All 14 agents in one console
- ✅ Color-coded real-time monitoring
- ✅ Error detection and highlighting
- ✅ Status tracking and reporting
- ✅ Graceful shutdown with Ctrl+C

**No more multiple windows or manual steps!**

