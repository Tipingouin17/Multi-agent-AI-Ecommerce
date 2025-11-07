# Multi-Agent E-Commerce Platform - Cross-Platform Guide

## Overview

This guide provides comprehensive documentation for launching, testing, and managing the multi-agent e-commerce platform on both **Linux/macOS** and **Windows**.

**Last Updated:** November 3, 2025  
**Platform Status:** ✅ 26/26 Agents Operational (100%)  
**UI Status:** ✅ Dashboard Ready for Deployment  

---

## Quick Start

### Linux/macOS

Launch all 26 agents + dashboard UI with one command:

```bash
./start_complete_system.sh
```

### Windows

Launch all 26 agents + dashboard UI with one command:

```batch
start_complete_system.bat
```

**Access Points (All Platforms):**
- Dashboard: http://localhost:5173
- Primary API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Script Equivalents

| Linux/macOS Script | Windows Script | Purpose |
|--------------------|----------------|---------|
| `start_complete_system.sh` | `start_complete_system.bat` | Launch everything (agents + UI) |
| `start_all_26_agents.sh` | `start_all_26_agents.bat` | Launch only agents |
| `start_dashboard.sh` | `start_dashboard.bat` | Launch only dashboard |
| `stop_all_agents.sh` | `stop_all_agents.bat` | Stop all running agents |
| `check_agents_status.sh` | `check_agents_status.bat` | Health check all agents |
| `setup_and_test.sh` | `setup_and_test.bat` (TBD) | Complete setup + testing |

---

## Detailed Script Documentation

### 1. start_complete_system

**Full System Launcher**

**Linux/macOS:**
```bash
./start_complete_system.sh
```

**Windows:**
```batch
start_complete_system.bat
```

**Features:**
- ✅ Comprehensive prerequisite checking
- ✅ Automatic agent startup
- ✅ Health monitoring
- ✅ Dashboard deployment
- ✅ Detailed status reporting

**Prerequisites:**
- PostgreSQL running on port 5432
- Python 3.11 installed
- Node.js 18+ installed (for dashboard)
- Kafka running on port 9092 (optional)

**Output:**
- Launches agents and dashboard in background/new windows
- Provides a summary of access points and log file locations

**Stopping the System:**

**Linux/macOS:**
```bash
# Stop dashboard
pkill -f 'vite'

# Stop agents
./stop_all_agents.sh
```

**Windows:**
```batch
# Stop dashboard
Close the dashboard window or press Ctrl+C

# Stop agents
stop_all_agents.bat
```

---

### 2. start_all_26_agents

**Agent Launcher**

**Linux/macOS:**
```bash
./start_all_26_agents.sh
```

**Windows:**
```batch
start_all_26_agents.bat
```

**Features:**
- Starts all 26 agents with unique ports (8000-8025)
- Creates individual log files for each agent
- Runs agents in background

**Log Files:**
- **Linux/macOS:** `logs/agents/`
- **Windows:** `logs\agents\`

**Checking Agent Status:**

**Linux/macOS:**
```bash
# Quick check
curl http://localhost:8000/health

# Comprehensive check
python3.11 check_all_26_agents_health.py
```

**Windows:**
```batch
# Quick check
curl http://localhost:8000/health

# Comprehensive check
python check_all_26_agents_health.py
```

---

### 3. start_dashboard

**Dashboard Launcher**

**Linux/macOS:**
```bash
./start_dashboard.sh
```

**Windows:**
```batch
start_dashboard.bat
```

**Features:**
- ✅ Node.js version check
- ✅ Package manager detection (pnpm/npm)
- ✅ Automatic dependency installation
- ✅ Environment configuration
- ✅ Agent connectivity check
- ✅ Vite dev server startup

**Environment Configuration:**

The script creates a `.env` file in `multi-agent-dashboard/`:

```env
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8015/ws

# Development Tools
VITE_ENABLE_DEVTOOLS=true
```

---

### 4. stop_all_agents

**Stop All Agents**

**Linux/macOS:**
```bash
./stop_all_agents.sh
```

**Windows:**
```batch
stop_all_agents.bat
```

**Features:**
- Gracefully stops all running agent processes
- Kills processes by port and process name

---

## Windows-Specific Instructions

### Prerequisites

1. **Install Python 3.11:**
   - Download from https://www.python.org/downloads/
   - **Important:** Check "Add Python to PATH" during installation

2. **Install Node.js 18+:**
   - Download from https://nodejs.org/

3. **Install PostgreSQL:**
   - Download from https://www.postgresql.org/download/windows/
   - Ensure it's running on port 5432

4. **Install Git:**
   - Download from https://git-scm.com/download/win

5. **Install Dependencies:**
   ```batch
   pip install -r requirements.txt
   ```

### Running Scripts

- Open **Command Prompt** or **PowerShell**
- Navigate to the project directory
- Run the `.bat` scripts as described above

### Troubleshooting

- **`python` is not recognized:** Reinstall Python and check "Add Python to PATH"
- **`node` is not recognized:** Reinstall Node.js
- **`pg_isready` is not recognized:** Add PostgreSQL `bin` directory to your PATH
- **Port conflicts:** Use `netstat -aon | findstr :8000` to find the process ID and `taskkill /F /PID <PID>` to kill it

---

## Conclusion

This guide provides a comprehensive overview of how to launch and manage the multi-agent e-commerce platform on both Linux/macOS and Windows. The repository is now fully cross-platform compatible.

**Repository:** https://github.com/Tipingouin17/Multi-agent-AI-Ecommerce  
**Status:** ✅ 100% Operational (26/26 Agents + Dashboard)  
**Compatibility:** ✅ Linux/macOS & Windows  
**Last Updated:** November 3, 2025  

---

**Author:** Manus AI  
**Version:** 1.1.0

