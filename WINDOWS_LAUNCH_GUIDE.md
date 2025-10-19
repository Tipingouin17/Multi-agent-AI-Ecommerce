# Windows Launch Guide - Multi-Agent E-commerce System

This guide will help you launch the entire multi-agent e-commerce system on Windows.

## Prerequisites Check

Before starting, ensure you have:

- [ ] Python 3.11+ installed
- [ ] PostgreSQL installed and running
- [ ] Docker Desktop installed (for Kafka, Redis, monitoring)
- [ ] Node.js 18+ installed (for dashboard)
- [ ] Git installed

## Step-by-Step Launch Process

### Step 1: Set Up Environment Variables

```powershell
# Navigate to project directory
cd C:\Users\jerom\OneDrive\Documents\Project\Multi-agent-AI-Ecommerce

# Copy environment template
copy .env.example .env

# Edit .env file with your settings
notepad .env
```

**Required settings in `.env`:**
```ini
DATABASE_PASSWORD=your_postgres_password
OPENAI_API_KEY=sk-your_openai_key_here  # Optional, for AI features
SECRET_KEY=generate_random_32_char_string
```

### Step 2: Install Python Dependencies

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Set Up Database

```powershell
# Option A: Use the batch file
.\setup-database.bat

# Option B: Manual setup
# Open psql command line
psql -U postgres

# In psql, run:
CREATE DATABASE multi_agent_ecommerce;
\q

# Initialize database schema
python -c "from shared.database import DatabaseManager; from shared.config import get_config; db = DatabaseManager(get_config().get_database_config()); db.initialize_sync(); print('Database ready')"
```

### Step 4: Start Infrastructure Services

#### Option A: Using Docker Desktop (Recommended)

```powershell
# Navigate to infrastructure directory
cd infrastructure

# Start all services (Kafka, Redis, PostgreSQL, Prometheus, Grafana, Loki)
docker-compose up -d

# Check services are running
docker-compose ps

# View logs
docker-compose logs -f
```

**Services started:**
- Kafka (localhost:9092)
- Zookeeper (localhost:2181)
- Redis (localhost:6379)
- Prometheus (localhost:9090)
- Grafana (localhost:3000)
- Loki (localhost:3100)

#### Option B: Manual Installation

If not using Docker, you'll need to install and start each service manually:

**Kafka:**
1. Download from https://kafka.apache.org/downloads
2. Extract and run:
   ```powershell
   .\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties
   .\bin\windows\kafka-server-start.bat .\config\server.properties
   ```

**Redis:**
1. Download from https://github.com/microsoftarchive/redis/releases
2. Run `redis-server.exe`

### Step 5: Verify Infrastructure

```powershell
# Test PostgreSQL connection
psql -U postgres -d multi_agent_ecommerce -c "SELECT version();"

# Test Redis (if installed locally)
redis-cli ping

# Test Kafka (if using Docker)
docker exec -it infrastructure_kafka_1 kafka-topics --list --bootstrap-server localhost:9092
```

### Step 6: Start the Agents

#### Option A: Start All Agents at Once

```powershell
# Make sure you're in the project root with venv activated
python agents/start_agents.py
```

#### Option B: Start Agents Individually (for testing)

Open separate PowerShell windows for each agent:

```powershell
# Terminal 1 - Order Agent
python -m agents.order_agent

# Terminal 2 - Inventory Agent
python -m agents.inventory_agent

# Terminal 3 - Product Agent
python -m agents.product_agent

# Terminal 4 - Carrier Selection Agent
python -m agents.carrier_selection_agent

# Terminal 5 - Warehouse Selection Agent
python -m agents.warehouse_selection_agent

# Terminal 6 - Customer Communication Agent
python -m agents.customer_communication_agent

# Terminal 7 - AI Monitoring Agent
python -m agents.ai_monitoring_agent

# ... and so on for other agents
```

#### Option C: Use the Batch File

```powershell
.\start-agents-direct.py
```

### Step 7: Start the Dashboard

```powershell
# Open a new PowerShell window
cd multi-agent-dashboard

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

**Dashboard URL:** http://localhost:5173

### Step 8: Verify Everything is Running

#### Check Agent Health

```powershell
# If you have curl installed
curl http://localhost:8000/health

# Or use PowerShell
Invoke-WebRequest -Uri http://localhost:8000/health
```

#### Check Monitoring Dashboards

- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Dashboard**: http://localhost:5173

#### Check Logs

```powershell
# View agent logs
Get-Content -Path "logs\agents\order_agent.log" -Tail 50 -Wait

# View all logs
Get-ChildItem -Path logs -Recurse -Filter *.log
```

## Quick Launch Script

Create a file `launch-all.ps1`:

```powershell
# Launch All Services Script

Write-Host "Starting Multi-Agent E-commerce System..." -ForegroundColor Green

# 1. Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# 2. Start Docker services
Write-Host "Starting Docker services..." -ForegroundColor Yellow
cd infrastructure
docker-compose up -d
cd ..

# Wait for services to be ready
Write-Host "Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 3. Start agents in background
Write-Host "Starting agents..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python agents/start_agents.py"

# 4. Start dashboard
Write-Host "Starting dashboard..." -ForegroundColor Yellow
cd multi-agent-dashboard
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev"
cd ..

Write-Host "System launched! Check the opened windows." -ForegroundColor Green
Write-Host "Dashboard: http://localhost:5173" -ForegroundColor Cyan
Write-Host "Grafana: http://localhost:3000" -ForegroundColor Cyan
```

**Run it:**
```powershell
.\launch-all.ps1
```

## Troubleshooting

### Issue: "Execution policy" error

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: Port already in use

```powershell
# Find process using port (e.g., 9092 for Kafka)
netstat -ano | findstr :9092

# Kill process by PID
taskkill /PID <PID> /F
```

### Issue: Docker services won't start

```powershell
# Restart Docker Desktop
# Or reset services
cd infrastructure
docker-compose down
docker-compose up -d
```

### Issue: Database connection failed

```powershell
# Check PostgreSQL is running
Get-Service -Name postgresql*

# Start if stopped
Start-Service postgresql-x64-14  # Adjust version number

# Test connection
psql -U postgres -c "SELECT 1;"
```

### Issue: Python module not found

```powershell
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Or install specific package
pip install aiokafka
```

### Issue: Kafka connection timeout

```powershell
# Check Kafka is running
docker ps | findstr kafka

# View Kafka logs
docker logs infrastructure_kafka_1

# Restart Kafka
cd infrastructure
docker-compose restart kafka
```

## Stopping Everything

### Stop Agents
Press `Ctrl+C` in each agent terminal window

### Stop Docker Services
```powershell
cd infrastructure
docker-compose down
```

### Stop Dashboard
Press `Ctrl+C` in the dashboard terminal

### Complete Shutdown Script

Create `shutdown-all.ps1`:
```powershell
Write-Host "Shutting down Multi-Agent E-commerce System..." -ForegroundColor Red

# Stop Docker services
cd infrastructure
docker-compose down
cd ..

# Kill Python processes
Get-Process python | Stop-Process -Force

# Kill Node processes
Get-Process node | Stop-Process -Force

Write-Host "System stopped." -ForegroundColor Green
```

## Testing the System

### Test Order Flow

```powershell
# Use the CLI
python run_cli.py

# Or send a test order
python -c "from agents.order_agent import OrderAgent; print('Test order creation')"
```

### Run Tests

```powershell
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_base_agent.py -v
```

## System URLs

Once everything is running:

| Service | URL | Credentials |
|---------|-----|-------------|
| Dashboard | http://localhost:5173 | - |
| Grafana | http://localhost:3000 | admin/admin123 |
| Prometheus | http://localhost:9090 | - |
| Agent API | http://localhost:8000 | - |

## Next Steps

1. ✅ Launch all services
2. ✅ Verify agents are running
3. ✅ Check dashboard
4. ✅ Monitor Grafana
5. 📝 Create test orders
6. 📝 Configure marketplace integrations
7. 📝 Set up production credentials

## Support

- Check logs in `logs/` directory
- Review `DEPLOYMENT_GUIDE.md` for detailed setup
- See `IMPROVEMENTS.md` for new features
- Open issues on GitHub

## Performance Tips

- Use Docker for infrastructure (easier management)
- Start only needed agents during development
- Monitor resource usage in Task Manager
- Use SSD for better database performance
- Allocate at least 4GB RAM to Docker Desktop

