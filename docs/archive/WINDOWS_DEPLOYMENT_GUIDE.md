# Windows Deployment Guide

**Multi-Agent E-commerce Platform - Windows Installation & Deployment**

---

## Prerequisites

### Required Software

1. **Python 3.11**
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"
   - Verify: `python --version` should show 3.11.x

2. **Node.js 22.13.0 or later**
   - Download from: https://nodejs.org/
   - Verify: `node --version` should show v22.x.x

3. **PostgreSQL 14 or later**
   - Download from: https://www.postgresql.org/download/windows/
   - During installation, remember your postgres password
   - Default port: 5432

4. **Git for Windows**
   - Download from: https://git-scm.com/download/win
   - Use Git Bash for command-line operations

5. **curl (usually included with Windows 10/11)**
   - Verify: `curl --version`
   - If not available, download from: https://curl.se/windows/

---

## Installation Steps

### Step 1: Clone the Repository

```cmd
cd C:\
git clone https://github.com/Tipingouin17/Multi-agent-AI-Ecommerce.git
cd Multi-agent-AI-Ecommerce
```

### Step 2: Set Up PostgreSQL Database

1. **Open PostgreSQL Command Line (psql)**

```cmd
psql -U postgres
```

2. **Create Database and User**

```sql
CREATE DATABASE ecommerce_db;
CREATE USER ecommerce_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE ecommerce_db TO ecommerce_user;
\q
```

3. **Import Database Schema**

```cmd
psql -U ecommerce_user -d ecommerce_db -f database\schema.sql
```

### Step 3: Configure Environment Variables

1. **Create `.env` file in project root**

```cmd
copy .env.example .env
notepad .env
```

2. **Edit `.env` with your settings:**

```env
# Database Configuration
DATABASE_URL=postgresql://ecommerce_user:your_secure_password@localhost:5432/ecommerce_db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Environment
ENVIRONMENT=production
DEBUG=false

# Security (generate your own secret keys)
SECRET_KEY=your-secret-key-here-change-this
JWT_SECRET=your-jwt-secret-here-change-this

# CORS (adjust for your domain)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Step 4: Install Python Dependencies

```cmd
REM Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

REM Install dependencies
pip install -r requirements.txt
```

### Step 5: Install Frontend Dependencies

```cmd
cd multi-agent-dashboard
npm install
cd ..
```

---

## Running the Platform

### Option 1: Using Batch Scripts (Recommended)

**Start All 27 Agents:**

```cmd
start_all_agents.bat
```

**Check Agent Health:**

```cmd
check_all_agents.bat
```

**Stop All Agents:**

```cmd
stop_all_agents.bat
```

**Start Frontend:**

```cmd
cd multi-agent-dashboard
npm run dev
```

### Option 2: Manual Start

**Start Individual Agent:**

```cmd
set API_PORT=8000
python agents\order_agent_v3.py
```

**Start Frontend:**

```cmd
cd multi-agent-dashboard
npm run dev
```

---

## Verification

### 1. Check All Agents Are Running

```cmd
check_all_agents.bat
```

**Expected Output:**
```
==========================================
Checking All 27 V3 Agents Health
==========================================

[HEALTHY] order_agent (port 8000)
[HEALTHY] product_agent (port 8001)
[HEALTHY] inventory_agent (port 8002)
...
==========================================
Health Check Summary
==========================================
Total Agents: 27
Healthy: 27
Offline: 0
Health Rate: 100%

Status: ALL AGENTS HEALTHY
```

### 2. Check Frontend

Open browser and navigate to:
```
http://localhost:5173
```

You should see the interface selector with 3 options:
- Admin Dashboard
- Merchant Portal
- Customer Portal

### 3. Check System API Gateway

```cmd
curl http://localhost:8100/api/system/overview
```

**Expected Response:**
```json
{
  "status": "healthy",
  "agents": {
    "total": 27,
    "online": 27,
    "offline": 0
  },
  ...
}
```

---

## Port Configuration

### Agent Ports (27 agents)

| Port | Agent | Description |
|------|-------|-------------|
| 8000 | order_agent | Order management |
| 8001 | product_agent | Product catalog |
| 8002 | inventory_agent | Stock management |
| 8003 | marketplace_connector | Multi-channel sync |
| 8004 | payment_agent | Payment processing |
| 8005 | dynamic_pricing | Pricing optimization |
| 8006 | carrier_agent | Shipping carriers |
| 8007 | customer_agent | Customer management |
| 8008 | warehouse_agent | Warehouse operations |
| 8009 | returns_agent | Returns/refunds |
| 8010 | fraud_detection | Security monitoring |
| 8011 | risk_anomaly_detection | Risk analysis |
| 8012 | knowledge_management | Knowledge base |
| 8014 | recommendation_agent | Product recommendations |
| 8015 | transport_management | Logistics |
| 8016 | document_generation | Documents/invoices |
| 8018 | support_agent | Customer support |
| 8019 | customer_communication | Messaging |
| 8020 | promotion_agent | Marketing/promotions |
| 8021 | after_sales_agent | Post-purchase |
| 8022 | infrastructure | Infrastructure management |
| 8023 | monitoring_agent | System monitoring |
| 8024 | ai_monitoring | AI monitoring |
| 8026 | d2c_ecommerce | Direct-to-consumer |
| 8027 | backoffice_agent | Admin operations |
| 8028 | quality_control | Quality assurance |
| 8100 | system_api_gateway | API gateway |

### Frontend Port

| Port | Service | Description |
|------|---------|-------------|
| 5173 | Vite Dev Server | Frontend development server |

**Note:** Make sure these ports are not blocked by Windows Firewall.

---

## Windows Firewall Configuration

### Allow Ports Through Firewall

1. **Open Windows Defender Firewall**
   - Press `Win + R`
   - Type `wf.msc` and press Enter

2. **Create Inbound Rules**
   - Click "Inbound Rules" → "New Rule"
   - Select "Port" → Next
   - Select "TCP" → Specific local ports: `8000-8100, 5173`
   - Allow the connection
   - Apply to all profiles (Domain, Private, Public)
   - Name: "Multi-Agent Ecommerce Platform"

---

## Troubleshooting

### Issue 1: Python Not Found

**Error:** `'python' is not recognized as an internal or external command`

**Solution:**
1. Reinstall Python and check "Add Python to PATH"
2. Or add Python manually to PATH:
   - Right-click "This PC" → Properties
   - Advanced system settings → Environment Variables
   - Edit "Path" → Add Python installation directory

### Issue 2: Port Already in Use

**Error:** `Address already in use` or `Port 8000 is already allocated`

**Solution:**
```cmd
REM Find process using the port
netstat -ano | findstr :8000

REM Kill the process (replace PID with actual process ID)
taskkill /F /PID <PID>
```

### Issue 3: Database Connection Failed

**Error:** `could not connect to server: Connection refused`

**Solution:**
1. Verify PostgreSQL is running:
   ```cmd
   sc query postgresql-x64-14
   ```

2. Start PostgreSQL if stopped:
   ```cmd
   net start postgresql-x64-14
   ```

3. Check DATABASE_URL in `.env` file

### Issue 4: Module Not Found

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```cmd
REM Activate virtual environment
venv\Scripts\activate

REM Install dependencies
pip install -r requirements.txt
```

### Issue 5: Agents Not Starting

**Error:** Agents fail to start or crash immediately

**Solution:**
1. Check logs in `logs\agents\` directory
2. Verify database connection
3. Ensure all dependencies are installed
4. Check if ports are available

---

## Production Deployment on Windows Server

### Using Windows Service

1. **Install NSSM (Non-Sucking Service Manager)**
   - Download from: https://nssm.cc/download
   - Extract to `C:\nssm`

2. **Create Service for Each Agent**

```cmd
REM Example: Create service for order agent
nssm install OrderAgent "C:\Python311\python.exe"
nssm set OrderAgent AppParameters "C:\Multi-agent-AI-Ecommerce\agents\order_agent_v3.py"
nssm set OrderAgent AppDirectory "C:\Multi-agent-AI-Ecommerce"
nssm set OrderAgent AppEnvironmentExtra API_PORT=8000
nssm set OrderAgent DisplayName "Order Agent V3"
nssm set OrderAgent Description "Multi-Agent Ecommerce - Order Agent"
nssm set OrderAgent Start SERVICE_AUTO_START

REM Start the service
nssm start OrderAgent
```

3. **Create Master Service Script**

Create `install_services.bat`:

```cmd
@echo off
REM Install all agents as Windows services

set PYTHON=C:\Python311\python.exe
set APP_DIR=C:\Multi-agent-AI-Ecommerce
set NSSM=C:\nssm\nssm.exe

%NSSM% install OrderAgent %PYTHON% "%APP_DIR%\agents\order_agent_v3.py"
%NSSM% set OrderAgent AppEnvironmentExtra API_PORT=8000

%NSSM% install ProductAgent %PYTHON% "%APP_DIR%\agents\product_agent_v3.py"
%NSSM% set ProductAgent AppEnvironmentExtra API_PORT=8001

REM ... repeat for all 27 agents ...

echo All services installed!
echo Use 'services.msc' to manage them.
```

### Using IIS as Reverse Proxy (Optional)

1. Install IIS with URL Rewrite and ARR modules
2. Configure reverse proxy rules for agents
3. Set up SSL certificates
4. Configure load balancing if needed

---

## Performance Optimization

### 1. Increase Process Limits

```cmd
REM Run as Administrator
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Executive" /v AdditionalCriticalWorkerThreads /t REG_DWORD /d 32 /f
```

### 2. Disable Windows Defender for Project Directory (Optional)

1. Open Windows Security
2. Virus & threat protection → Manage settings
3. Add exclusion → Folder
4. Select `C:\Multi-agent-AI-Ecommerce`

### 3. Use SSD for Database

Ensure PostgreSQL data directory is on SSD for better performance.

---

## Monitoring on Windows

### 1. Task Manager

- Press `Ctrl + Shift + Esc`
- Check CPU and Memory usage of Python processes

### 2. Resource Monitor

- Press `Win + R`, type `resmon`
- Monitor network activity on agent ports

### 3. Event Viewer

- Press `Win + R`, type `eventvwr.msc`
- Check Application logs for errors

---

## Backup and Recovery

### Database Backup

```cmd
REM Create backup
pg_dump -U ecommerce_user -d ecommerce_db -f backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.sql

REM Restore backup
psql -U ecommerce_user -d ecommerce_db -f backup_20251105.sql
```

### Application Backup

```cmd
REM Backup entire application
xcopy C:\Multi-agent-AI-Ecommerce C:\Backups\Multi-agent-AI-Ecommerce_%date:~-4,4%%date:~-10,2%%date:~-7,2% /E /I /H
```

---

## Security Recommendations

1. **Use Strong Passwords**
   - Database password
   - SECRET_KEY and JWT_SECRET

2. **Enable Windows Firewall**
   - Only allow necessary ports
   - Restrict access to localhost if not needed externally

3. **Keep Software Updated**
   - Windows Updates
   - Python packages: `pip list --outdated`
   - Node packages: `npm outdated`

4. **Use HTTPS in Production**
   - Install SSL certificate
   - Configure reverse proxy (IIS or nginx)

5. **Regular Backups**
   - Schedule daily database backups
   - Keep backups in separate location

---

## Support

For issues specific to Windows deployment:

1. Check logs in `logs\agents\` directory
2. Review this guide's Troubleshooting section
3. Consult main documentation in `DOCUMENTATION_INDEX.md`
4. Submit issues at: https://help.manus.im

---

## Quick Reference Commands

```cmd
REM Start all agents
start_all_agents.bat

REM Check agent health
check_all_agents.bat

REM Stop all agents
stop_all_agents.bat

REM Start frontend
cd multi-agent-dashboard && npm run dev

REM Check database connection
psql -U ecommerce_user -d ecommerce_db -c "SELECT version();"

REM View agent logs
type logs\agents\order_agent_v3.log

REM Check port usage
netstat -ano | findstr :8000
```

---

**Last Updated:** November 5, 2025  
**Platform Version:** 3.0.0  
**Compatibility:** Windows 10, Windows 11, Windows Server 2019+
