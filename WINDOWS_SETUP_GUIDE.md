# 🪟 Windows Setup Guide - Multi-Agent E-commerce System

## 🚀 Quick Start

### Step 1: Extract and Install
1. Extract `complete-multi-agent-ecommerce-system.zip` to your desired location
2. Open Command Prompt **as Administrator**
3. Navigate to the extracted folder:
   ```cmd
   cd C:\path\to\complete-multi-agent-system
   ```
4. Run the installer:
   ```cmd
   install.bat
   ```

### Step 2: Configure Database
1. Install PostgreSQL if not already installed:
   - Download from: https://www.postgresql.org/download/windows/
   - Use default settings during installation
   - Remember the password for the `postgres` user

2. Edit the `.env` file:
   ```cmd
   notepad .env
   ```
   
3. Update the database settings:
   ```env
   DATABASE_HOST=localhost
   DATABASE_PORT=5432
   DATABASE_NAME=multi_agent_ecommerce
   DATABASE_USER=postgres
   DATABASE_PASSWORD=your_postgres_password
   ```

### Step 3: Initialize and Start
1. Initialize the database:
   ```cmd
   init-database.bat
   ```

2. Start the system:
   ```cmd
   start-system.bat
   ```

## 🔧 Troubleshooting

### If Installation Fails

1. **Run the troubleshooter**:
   ```cmd
   troubleshoot.bat
   ```

2. **Manual dependency installation**:
   ```cmd
   # Activate virtual environment
   venv\Scripts\activate
   
   # Install core dependencies
   pip install fastapi uvicorn pydantic sqlalchemy
   pip install asyncpg psycopg2-binary
   pip install click structlog rich typer python-dotenv
   ```

3. **Use the fallback CLI**:
   ```cmd
   python run_cli.py --help
   python run_cli.py status
   python run_cli.py health
   ```

### Common Issues

#### "ModuleNotFoundError: No module named 'asyncpg'"
**Solution**:
```cmd
venv\Scripts\activate
pip install asyncpg psycopg2-binary
```

#### "ModuleNotFoundError: No module named 'multi_agent_ecommerce'"
**Solution**:
```cmd
venv\Scripts\activate
pip install -e .
```
Or use the fallback:
```cmd
python run_cli.py [command]
```

#### "Database connection failed"
**Solution**:
1. Ensure PostgreSQL is running
2. Check credentials in `.env` file
3. Test connection:
   ```cmd
   psql -h localhost -U postgres -d multi_agent_ecommerce
   ```

#### "Permission denied" errors
**Solution**:
1. Run Command Prompt as Administrator
2. Check antivirus isn't blocking the installation
3. Temporarily disable Windows Defender real-time protection

## 📋 Available Commands

### Batch Scripts (Recommended)
- `start-system.bat` - Start the multi-agent system
- `check-status.bat` - Check system status
- `check-health.bat` - Run health checks
- `init-database.bat` - Initialize database tables
- `view-config.bat` - View current configuration
- `troubleshoot.bat` - Run troubleshooting diagnostics

### Direct CLI Commands
```cmd
# Activate environment first
venv\Scripts\activate

# Then use CLI
python -m multi_agent_ecommerce.cli --help
python -m multi_agent_ecommerce.cli status
python -m multi_agent_ecommerce.cli health
python -m multi_agent_ecommerce.cli init-db
python -m multi_agent_ecommerce.cli start
```

### Fallback CLI (if package installation fails)
```cmd
python run_cli.py --help
python run_cli.py status
python run_cli.py health
python run_cli.py init-db
python run_cli.py start
```

## 🔍 System Verification

### Check Installation
```cmd
# Check Python
python --version

# Check virtual environment
venv\Scripts\activate
python -c "import multi_agent_ecommerce; print('OK')"

# Check database connection
python run_cli.py health
```

### Check Database
```cmd
# Connect to PostgreSQL
psql -h localhost -U postgres

# List databases
\l

# Connect to our database
\c multi_agent_ecommerce

# List tables
\dt
```

## 📊 System Requirements

### Minimum Requirements
- **OS**: Windows 10/11
- **Python**: 3.9 or higher
- **RAM**: 4GB
- **Disk**: 10GB free space
- **PostgreSQL**: 12 or higher

### Recommended Requirements
- **RAM**: 8GB or more
- **Disk**: 50GB free space
- **CPU**: 4 cores or more

## 🔒 Security Notes

- **Database**: All operations use real PostgreSQL - no mock data
- **Credentials**: Never commit `.env` file with real credentials
- **Firewall**: Configure Windows Firewall for PostgreSQL (port 5432)
- **Updates**: Keep PostgreSQL and Python updated

## 📞 Getting Help

### Self-Diagnosis
1. Run `troubleshoot.bat`
2. Check logs in the `logs/` directory
3. Use `python run_cli.py health` to test connections

### Manual Verification
```cmd
# Test Python
python --version

# Test dependencies
python -c "import fastapi, sqlalchemy, asyncpg; print('Dependencies OK')"

# Test database
python -c "import psycopg2; print('Database driver OK')"

# Test package
python -c "import multi_agent_ecommerce; print('Package OK')"
```

### Error Logs
Check these locations for error details:
- `logs/` directory (if created)
- Command prompt output
- Windows Event Viewer (for system-level issues)

## 🎯 Next Steps After Installation

1. **Configure APIs**: Add your API keys to `.env`
2. **Test System**: Run `check-health.bat`
3. **Start Agents**: Run `start-system.bat`
4. **Monitor**: Use `check-status.bat` regularly
5. **Scale**: Add more agents or database replicas as needed

---

**💡 Tip**: If you encounter any issues, always try `troubleshoot.bat` first - it can automatically fix most common problems!
