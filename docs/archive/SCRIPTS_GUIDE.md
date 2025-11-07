# Scripts Guide - Multi-Agent E-commerce Platform

**Last Updated:** October 22, 2025

This document explains all scripts in the repository and identifies which ones to use for production.

---

## 🚀 PRODUCTION SCRIPTS (USE THESE)

### 1. **`setup-and-launch.ps1`** ⭐ RECOMMENDED
**Purpose:** Complete setup and launch from scratch

**What it does:**
- Checks prerequisites (Docker, Python, Node.js)
- Sets up database with all tables
- Starts infrastructure (PostgreSQL, Kafka, Redis)
- Initializes Kafka topics
- Launches all 15 agents with logging
- Starts the dashboard

**Usage:**
```powershell
# Complete setup from scratch
.\setup-and-launch.ps1

# Skip infrastructure (if already running)
.\setup-and-launch.ps1 -SkipInfrastructure

# Skip database setup (if already initialized)
.\setup-and-launch.ps1 -SkipDatabase
```

**Logs:** All logs are saved to `logs/setup_YYYYMMDD_HHMMSS.log`

---

### 2. **`shutdown-all.ps1`**
**Purpose:** Stop all system components

**What it does:**
- Stops all agent processes
- Stops dashboard
- Stops Docker infrastructure

**Usage:**
```powershell
# Complete shutdown
.\shutdown-all.ps1

# Keep infrastructure running (stop agents only)
.\shutdown-all.ps1 -KeepInfrastructure
```

---

### 3. **`start-agents-monitor.py`**
**Purpose:** Start all 15 production agents with monitoring

**What it does:**
- Launches all production agents
- Monitors agent health
- Provides automatic logging
- Sets correct environment variables

**Usage:**
```powershell
python start-agents-monitor.py
```

**Note:** This is called automatically by `setup-and-launch.ps1`

---

## 📋 SUPPORTING SCRIPTS (OPTIONAL)

### **`start-infrastructure.ps1`**
**Purpose:** Start only Docker infrastructure

**Usage:**
```powershell
.\start-infrastructure.ps1
```

**When to use:** If you want to start infrastructure separately

---

### **`start-dashboard.ps1`**
**Purpose:** Start only the dashboard

**Usage:**
```powershell
.\start-dashboard.ps1
```

**When to use:** If you want to start dashboard separately

---

### **`init_database.py`**
**Purpose:** Initialize database with migrations

**Usage:**
```powershell
python init_database.py
```

**Note:** This is called automatically by `setup-and-launch.ps1`

---

### **`init_kafka_topics.py`**
**Purpose:** Create all Kafka topics

**Usage:**
```powershell
python init_kafka_topics.py
```

**Note:** This is called automatically by `setup-and-launch.ps1`

---

## 🗑️ OBSOLETE SCRIPTS (CAN BE DELETED)

The following scripts are obsolete and can be safely deleted:

### Diagnostic/Testing Scripts (No longer needed)
- ❌ `diagnose-kafka.ps1` - Old Kafka diagnostic tool
- ❌ `fix-kafka-connection.ps1` - Old Kafka fix script
- ❌ `test-fixes.ps1` - Old test script
- ❌ `test-kafka-addresses.ps1` - Old Kafka test
- ❌ `verify-system.ps1` - Old verification script
- ❌ `verify-system.py` - Old Python verification

### Old Launch Scripts (Replaced by `setup-and-launch.ps1`)
- ❌ `launch-all.ps1` - Old launch script
- ❌ `launch.ps1` - Old launch script
- ❌ `launch.sh` - Old bash launch script
- ❌ `start-system.ps1` - Old system starter
- ❌ `start_all_agents.sh` - Old bash agent starter
- ❌ `stop_all_agents.sh` - Old bash agent stopper

### Old Setup Scripts (Replaced by `setup-and-launch.ps1`)
- ❌ `setup_complete_system.py` - Old setup script
- ❌ `setup_incremental_migration.py` - Old migration script
- ❌ `check-and-install-dependencies.ps1` - Old dependency checker

### Old Migration Scripts (Migrations now automated)
- ❌ `fix_all_migrations.sh` - Old migration fixer
- ❌ `run_order_migration.py` - Old order migration
- ❌ `organize_repository.sh` - Old repository organizer

### Other Old Scripts
- ❌ `start-agents-direct.py` - Old direct agent starter (use `start-agents-monitor.py`)
- ❌ `run_cli.py` - Old CLI tool (not used)

---

## 🧹 CLEANUP INSTRUCTIONS

To remove all obsolete scripts:

```powershell
# Navigate to project root
cd C:\Users\jerom\OneDrive\Documents\Project\Multi-agent-AI-Ecommerce

# Remove obsolete scripts
Remove-Item diagnose-kafka.ps1
Remove-Item fix-kafka-connection.ps1
Remove-Item test-fixes.ps1
Remove-Item test-kafka-addresses.ps1
Remove-Item verify-system.ps1
Remove-Item verify-system.py
Remove-Item launch-all.ps1
Remove-Item launch.ps1
Remove-Item launch.sh
Remove-Item start-system.ps1
Remove-Item start_all_agents.sh
Remove-Item stop_all_agents.sh
Remove-Item setup_complete_system.py
Remove-Item setup_incremental_migration.py
Remove-Item check-and-install-dependencies.ps1
Remove-Item fix_all_migrations.sh
Remove-Item run_order_migration.py
Remove-Item organize_repository.sh
Remove-Item start-agents-direct.py
Remove-Item run_cli.py

# Commit the cleanup
git add -A
git commit -m "chore: Remove obsolete scripts"
git push origin main
```

---

## 📖 RECOMMENDED WORKFLOW

### First Time Setup (From Scratch)

```powershell
# 1. Clone the repository
git clone https://github.com/Tipingouin17/Multi-agent-AI-Ecommerce.git
cd Multi-agent-AI-Ecommerce

# 2. Run complete setup
.\setup-and-launch.ps1

# 3. Access the dashboard
# Open browser: http://localhost:5173
```

### Daily Development

```powershell
# Start (if infrastructure already running)
.\setup-and-launch.ps1 -SkipInfrastructure -SkipDatabase

# Stop
.\shutdown-all.ps1 -KeepInfrastructure
```

### Complete Restart

```powershell
# Stop everything
.\shutdown-all.ps1

# Start fresh
.\setup-and-launch.ps1
```

---

## 📂 FINAL SCRIPT STRUCTURE

After cleanup, you should have only these scripts:

```
Multi-agent-AI-Ecommerce/
├── setup-and-launch.ps1          ⭐ Main setup script
├── shutdown-all.ps1               ⭐ Main shutdown script
├── start-agents-monitor.py        ⭐ Agent launcher
├── start-infrastructure.ps1       (Optional - for infrastructure only)
├── start-dashboard.ps1            (Optional - for dashboard only)
├── init_database.py               (Called automatically)
└── init_kafka_topics.py           (Called automatically)
```

**Total:** 7 scripts (down from 25)

---

## ❓ TROUBLESHOOTING

### If agents don't start:

```powershell
# Check logs
Get-Content logs\agents_*.log -Tail 50

# Verify infrastructure is running
docker ps

# Restart infrastructure
.\shutdown-all.ps1
.\setup-and-launch.ps1
```

### If database is not initialized:

```powershell
# Run database setup manually
python init_database.py
```

### If Kafka topics are missing:

```powershell
# Create topics manually
python init_kafka_topics.py
```

---

## 📝 SUMMARY

**Use this for production:**
1. `setup-and-launch.ps1` - Start everything
2. `shutdown-all.ps1` - Stop everything

**Delete these (obsolete):**
- All diagnostic scripts (`diagnose-*`, `test-*`, `verify-*`, `fix-*`)
- Old launch scripts (`launch-*`, `start-system.ps1`, `start_all_agents.sh`)
- Old setup scripts (`setup_complete_system.py`, `check-and-install-dependencies.ps1`)
- Old migration scripts (`fix_all_migrations.sh`, `run_order_migration.py`)
- Other old scripts (`run_cli.py`, `start-agents-direct.py`, `organize_repository.sh`)

**Total reduction:** 25 scripts → 7 scripts (72% reduction)

---

**Last Updated:** October 22, 2025  
**Maintainer:** Multi-Agent AI E-commerce Team

