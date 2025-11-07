# Windows Setup Guide

## Quick Start for Windows Users

This guide provides Windows-specific instructions for running the Multi-Agent E-commerce Platform.

---

## Prerequisites

### Required Software

1. **Python 3.11+**
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"

2. **PostgreSQL 14+**
   - Download from: https://www.postgresql.org/download/windows/
   - Remember your postgres user password

3. **Git** (for cloning the repository)
   - Download from: https://git-scm.com/download/win

### Optional Software

4. **Apache Kafka** (recommended for full functionality)
   - Download from: https://kafka.apache.org/downloads
   - Or use Docker: `docker run -p 9092:9092 apache/kafka`

5. **Node.js 18+** (for the dashboard)
   - Download from: https://nodejs.org/
   - Required if you want to run the UI dashboard

---

## Installation Steps

### 1. Clone the Repository

```powershell
git clone https://github.com/Tipingouin17/Multi-agent-AI-Ecommerce.git
cd Multi-agent-AI-Ecommerce
```

### 2. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=multi_agent_ecommerce
DATABASE_USER=postgres
DATABASE_PASSWORD=your_postgres_password

# Kafka Configuration (optional)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# OpenAI API Key (for AI monitoring)
OPENAI_API_KEY=your_openai_api_key
```

### 4. Initialize the Database

```powershell
python init_database.py
```

---

## Running the System

### Option 1: Complete Setup and Testing (Recommended)

**Using Batch File (Double-click):**
```
setup_and_test.bat
```

**Using PowerShell:**
```powershell
.\setup_and_test.ps1
```

This will:
- Check prerequisites
- Initialize database
- Start all 16 agents
- Run comprehensive tests
- Generate production readiness report

### Option 2: Manual Steps

**Start All Agents:**
```powershell
.\start_all_agents.ps1
```

**Check Agent Status:**
```powershell
.\check_agents_status.ps1
```

**Stop All Agents:**
```powershell
.\stop_all_agents.ps1
```

**Run Tests:**
```powershell
# Workflow tests
python testing/comprehensive_workflow_tests.py

# UI tests (requires dashboard running)
python testing/ui_automation_tests.py

# Production validation
python testing/production_validation_suite.py
```

---

## Running the Dashboard (Optional)

The dashboard is a React application that provides a UI for the system.

### Start the Dashboard

```powershell
cd multi-agent-dashboard
npm install
npm run dev
```

The dashboard will be available at: http://localhost:5173

---

## Troubleshooting

### PowerShell Execution Policy Error

If you get an error about execution policy:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Or run scripts with:
```powershell
powershell -ExecutionPolicy Bypass -File .\setup_and_test.ps1
```

### PostgreSQL Connection Error

1. Verify PostgreSQL is running:
   ```powershell
   # Check if PostgreSQL service is running
   Get-Service -Name postgresql*
   
   # Start if not running
   Start-Service postgresql-x64-14  # Adjust version number
   ```

2. Test connection:
   ```powershell
   psql -U postgres -h localhost
   ```

3. Verify `.env` file has correct credentials

### Port Already in Use

If you get "port already in use" errors:

```powershell
# Find process using port (e.g., 8000)
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
Get-Process -Id <PID>

# Kill the process
Stop-Process -Id <PID> -Force
```

Or use the stop script:
```powershell
.\stop_all_agents.ps1
```

### Python Not Found

If you get "python is not recognized":

1. Verify Python is installed:
   ```powershell
   python --version
   ```

2. If not found, add Python to PATH:
   - Search "Environment Variables" in Windows
   - Edit "Path" variable
   - Add Python installation directory (e.g., `C:\Python311\`)

### Kafka Not Running

Kafka is optional. If you don't have Kafka:

1. **Skip Kafka** - The system will work without it (some features limited)

2. **Use Docker** (easiest):
   ```powershell
   docker run -d -p 9092:9092 --name kafka apache/kafka
   ```

3. **Install Kafka** - Follow: https://kafka.apache.org/quickstart

---

## File Locations

### Scripts (Windows-specific)

- `setup_and_test.bat` - Batch file for easy double-click execution
- `setup_and_test.ps1` - PowerShell script for complete setup
- `start_all_agents.ps1` - Start all agents
- `check_agents_status.ps1` - Check agent health
- `stop_all_agents.ps1` - Stop all agents

### Logs

- `logs/` - Agent log files
- `test_logs/` - Test result logs
- `screenshots/` - UI test failure screenshots

### Test Results

- `test_results_*.log` - Workflow test results
- `ui_test_results_*.log` - UI test results
- `test_report_*.json` - JSON test reports

---

## Agent Ports

All agents run on localhost with these ports:

| Agent | Port |
|-------|------|
| Monitoring | 8000 |
| Order | 8001 |
| Product | 8002 |
| Marketplace | 8003 |
| Customer | 8004 |
| Inventory | 8005 |
| Payment | 8006 |
| Transport | 8007 |
| Warehouse | 8008 |
| Document | 8009 |
| Fraud | 8010 |
| Risk | 8011 |
| Knowledge | 8012 |
| After-Sales | 8013 |
| Backoffice | 8014 |
| Quality | 8015 |

---

## Testing the System

### Quick Health Check

```powershell
.\check_agents_status.ps1
```

Expected output: All 16 agents showing "✅ RUNNING & HEALTHY"

### Run Comprehensive Tests

```powershell
.\setup_and_test.ps1
```

This runs 170+ test scenarios and generates a production readiness score.

### View Test Results

```powershell
# View latest test log
Get-Content test_logs\production_validation_*.log -Tail 50

# View test report
Get-Content test_logs\production_readiness_report_*.json | ConvertFrom-Json
```

---

## Common Commands

### Start Everything

```powershell
# Initialize database
python init_database.py

# Start all agents
.\start_all_agents.ps1

# Start dashboard (in another terminal)
cd multi-agent-dashboard
npm run dev
```

### Check Status

```powershell
# Check all agents
.\check_agents_status.ps1

# Check specific agent logs
Get-Content logs\monitoring.log -Tail 20 -Wait
```

### Stop Everything

```powershell
# Stop all agents
.\stop_all_agents.ps1

# Stop dashboard (Ctrl+C in the terminal)
```

---

## Production Deployment

For production deployment on Windows Server:

1. **Use Windows Services** to run agents as services
2. **Use IIS** as reverse proxy
3. **Use SQL Server** instead of PostgreSQL (optional)
4. **Configure SSL/TLS** certificates
5. **Set up monitoring** (Prometheus, Grafana)

See `PRODUCTION_READINESS_FINAL_REPORT.md` for complete deployment guide.

---

## Getting Help

### Check Logs

All logs are in the `logs/` directory:

```powershell
# View all recent logs
Get-ChildItem logs\*.log | ForEach-Object { 
    Write-Host "`n=== $($_.Name) ===" -ForegroundColor Cyan
    Get-Content $_.FullName -Tail 10 
}
```

### Common Issues

1. **"Access Denied"** - Run PowerShell as Administrator
2. **"Port in use"** - Run `.\stop_all_agents.ps1`
3. **"Database connection failed"** - Check PostgreSQL is running
4. **"Module not found"** - Run `pip install -r requirements.txt`

### Documentation

- `PRODUCTION_READINESS_FINAL_REPORT.md` - Complete system overview
- `TEST_FIXES_SUMMARY.md` - Test fixes and improvements
- `100_PERCENT_PRODUCTION_READY_CERTIFICATION.md` - Production certification

---

## Summary

**To get started quickly:**

1. Install Python, PostgreSQL, Git
2. Clone repository
3. Create `.env` file with database credentials
4. Double-click `setup_and_test.bat`

**That's it!** The system will set up and validate everything automatically.

---

## Support

For issues or questions:
- Check the logs in `logs/` directory
- Review documentation in the project root
- Check GitHub issues: https://github.com/Tipingouin17/Multi-agent-AI-Ecommerce/issues

