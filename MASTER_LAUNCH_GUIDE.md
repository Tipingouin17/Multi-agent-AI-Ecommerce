# Multi-Agent E-Commerce Platform - Master Launch Guide

## Overview

This guide provides comprehensive documentation for the **master launch script**, the ultimate one-command solution for launching, monitoring, and managing the entire multi-agent e-commerce platform.

**Last Updated:** November 3, 2025  
**Platform Status:** ✅ 100% Operational & Cross-Platform  

---

## The Master Launch Script

### One Command to Rule Them All

**Linux/macOS:**
```bash
./master_launch.sh
```

**Windows:**
```batch
master_launch.bat
```

### Key Features

1.  **Comprehensive Logging**
    -   **Master Log:** Tracks the entire startup sequence (`logs/master/startup_...log`)
    -   **Agent Logs:** Every agent gets its own dedicated log file (`logs/agents/`)
    -   **Infrastructure Logs:** Logs for PostgreSQL, Kafka, Node.js, etc. (`logs/infrastructure/`)

2.  **Infrastructure Tracking**
    -   Verifies all prerequisites (PostgreSQL, Kafka, Node.js, Python)
    -   Checks disk space and memory
    -   Ensures a healthy environment before startup

3.  **Process Monitoring**
    -   Tracks the PID of every agent and the dashboard
    -   Saves process information to `logs/master/process_tracking.json`

4.  **Intelligent Startup Sequence**
    -   Starts agents in a controlled sequence with delays
    -   Waits for agents to initialize before running health checks

5.  **Automated Health Checks**
    -   Performs health checks on all 26 agents after startup
    -   Provides a detailed summary of healthy, unhealthy, and non-running agents

6.  **Real-Time Status Dashboard**
    -   Color-coded console output for at-a-glance status
    -   Detailed final report summarizing the state of the entire system

7.  **Cross-Platform Compatibility**
    -   Works seamlessly on both **Linux/macOS** (`.sh`) and **Windows** (`.bat`)

---

## Verbose Mode

For even more detailed output, you can run the master launch script in **verbose mode**.

### Linux/macOS

```bash
VERBOSE=1 ./master_launch.sh
```

### Windows

```batch
set VERBOSE=1
master_launch.bat
```

Verbose mode will:
- Print every command as it is executed (`set -x`)
- Show detailed error messages in the console
- Provide real-time feedback on every step of the startup process

---

## How It Works

### Startup Sequence

1.  **Initialization:**
    -   Creates all necessary log directories (`logs/master`, `logs/agents`, `logs/infrastructure`)
    -   Initializes the master log file and process tracking file

2.  **Infrastructure Check:**
    -   Verifies all required software is installed and running
    -   Checks system resources (disk space, memory)

3.  **Agent Startup:**
    -   Starts all 26 agents sequentially with a 2-second delay
    -   Assigns a unique port (8000-8025) to each agent
    -   Redirects each agent's output to its own log file
    -   Records the PID of each agent

4.  **Health Monitoring:**
    -   Waits 30 seconds for agents to initialize
    -   Performs a health check on every agent's `/health` endpoint
    -   Provides a detailed summary of agent status

5.  **Dashboard Startup:**
    -   Launches the dashboard UI in the background
    -   Waits for the dashboard to be ready on port 5173

6.  **Final Report:**
    -   Generates a comprehensive status report with details on:
        -   Infrastructure status
        -   Agent health
        -   Dashboard status
        -   Log file locations
        -   Process tracking information

### Log Files

-   **Master Log:** `logs/master/startup_YYYYMMDD_HHMMSS.log`
    -   A complete, timestamped log of the entire startup process.

-   **Agent Logs:** `logs/agents/`
    -   `order.log`, `product.log`, `inventory.log`, etc.
    -   One log file for each of the 26 agents.

-   **Infrastructure Logs:** `logs/infrastructure/`
    -   `postgresql.log`, `kafka.log`, `nodejs.log`, etc.
    -   Logs for each infrastructure component check.

-   **Process Tracking:** `logs/master/process_tracking.json`
    -   A JSON file containing the PIDs, ports, and log file locations for all running processes.

---

## Usage

### Prerequisites

-   **Python 3.11**
-   **Node.js 18+**
-   **PostgreSQL** (running on port 5432)
-   **Git**
-   **Dependencies:** `pip install -r requirements.txt`

### Launching the System

**Linux/macOS:**
```bash
./master_launch.sh
```

**Windows:**
```batch
master_launch.bat
```

### Output

The script will provide a real-time, color-coded status update in the console, followed by a final summary:

```
================================================================================
MASTER LAUNCH COMPLETE!
================================================================================

Access Points:
  Dashboard:    http://localhost:5173
  Primary API:  http://localhost:8000
  API Docs:     http://localhost:8000/docs

Logs:
  Master Log:   logs/master/startup_...
  Agent Logs:   logs/agents/
  Tracking:     logs/master/process_tracking.json

Management:
  Stop agents:  ./stop_all_agents.sh (or .bat)
  Check health: python check_all_26_agents_health.py
```

### Stopping the System

**Linux/macOS:**
```bash
./stop_all_agents.sh
```

**Windows:**
```batch
stop_all_agents.bat
```

---

## Conclusion

The **master launch script** is the definitive way to start and monitor the multi-agent e-commerce platform. It provides complete visibility, robust logging, and a seamless, one-command experience on both Linux/macOS and Windows.

**Repository:** https://github.com/Tipingouin17/Multi-agent-AI-Ecommerce  
**Status:** ✅ 100% Operational & Cross-Platform  
**Version:** 1.2.0

---

**Author:** Manus AI

