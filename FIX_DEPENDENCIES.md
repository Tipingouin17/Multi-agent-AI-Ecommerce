# Fix: Dependency Installation Issues

## Problem

All agents are failing with errors like:
```
ModuleNotFoundError: No module named 'fastapi'
ModuleNotFoundError: No module named 'openai'
ModuleNotFoundError: No module named 'numpy'
```

This means Python packages are not installed in your virtual environment.

## Quick Fix

### Option 1: Automated Fix (Recommended)

```powershell
# Run the dependency checker and installer
.\check-and-install-dependencies.ps1

# Or batch version
check-and-install-dependencies.bat
```

This will:
1. Check if virtual environment exists (create if missing)
2. Activate virtual environment
3. Check all critical packages
4. Install missing packages from requirements.txt
5. Verify installation

### Option 2: Manual Fix

```powershell
# 1. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 2. Install all dependencies
pip install -r requirements.txt

# 3. Verify installation
python -c "import fastapi, uvicorn, pydantic, sqlalchemy, openai, numpy"

# If successful (no errors), you're ready!
```

### Option 3: Fresh Start

```powershell
# 1. Remove old virtual environment
Remove-Item -Recurse -Force venv

# 2. Create new virtual environment
python -m venv venv

# 3. Activate it
.\venv\Scripts\Activate.ps1

# 4. Upgrade pip
python -m pip install --upgrade pip

# 5. Install dependencies
pip install -r requirements.txt

# 6. Verify
python -c "import fastapi, uvicorn, pydantic"
```

## Specific Errors Fixed

### 1. ✅ MIMEMultipart Import Error

**Error:**
```
ImportError: cannot import name 'MimeMultipart' from 'email.mime.multipart'
```

**Fix:** Changed `MimeMultipart` to `MIMEMultipart` (correct capitalization) in `customer_communication_agent.py`

### 2. ✅ Missing fastapi

**Error:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Fix:** Install with `pip install fastapi uvicorn`

### 3. ✅ Missing openai

**Error:**
```
ModuleNotFoundError: No module named 'openai'
```

**Fix:** Install with `pip install openai`

### 4. ✅ Missing numpy

**Error:**
```
ModuleNotFoundError: No module named 'numpy'
```

**Fix:** Install with `pip install numpy pandas`

## Verification

After fixing, verify all packages are installed:

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Test imports
python -c "import fastapi; print('✓ fastapi')"
python -c "import uvicorn; print('✓ uvicorn')"
python -c "import pydantic; print('✓ pydantic')"
python -c "import sqlalchemy; print('✓ sqlalchemy')"
python -c "import psycopg2; print('✓ psycopg2')"
python -c "import aiokafka; print('✓ aiokafka')"
python -c "import redis; print('✓ redis')"
python -c "import structlog; print('✓ structlog')"
python -c "import openai; print('✓ openai')"
python -c "import numpy; print('✓ numpy')"
python -c "import pandas; print('✓ pandas')"
```

All should print ✓ with no errors.

## Updated Startup Process

The startup scripts now **automatically check** dependencies:

### start-system.ps1 / start-system.bat

Now includes:
1. ✅ Virtual environment check
2. ✅ **Dependency verification**
3. ✅ **Auto-install if missing**
4. ✅ Docker startup
5. ✅ Agent monitoring

So you can just run:
```powershell
.\start-system.ps1
```

And it will:
- Detect missing dependencies
- Automatically install them
- Then start everything

## Common Issues

### Issue: pip not found

```powershell
# Ensure pip is installed
python -m ensurepip --upgrade
python -m pip install --upgrade pip
```

### Issue: Permission denied

```powershell
# Run PowerShell as Administrator
# Or use --user flag
pip install --user -r requirements.txt
```

### Issue: SSL certificate errors

```powershell
# Use trusted host
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### Issue: Slow installation

```powershell
# Use a mirror
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

### Issue: Conflicting packages

```powershell
# Force reinstall
pip install -r requirements.txt --force-reinstall --no-cache-dir
```

## Requirements.txt Contents

The file includes all necessary packages:

```
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1

# Message Broker
aiokafka==0.8.1
kafka-python==2.0.2

# Cache
redis==5.0.1

# AI/ML
openai==1.3.5
numpy==1.26.2
pandas==2.1.3
scikit-learn==1.3.2

# Logging
structlog==23.2.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0

# Utilities
python-dotenv==1.0.0
requests==2.31.0
aiohttp==3.9.1
```

## After Installing

Once dependencies are installed:

1. ✅ Run verification: `.\verify-system.ps1`
2. ✅ Start system: `.\start-system.ps1`
3. ✅ Watch for green ✓ messages (not red ✗)
4. ✅ All 14 agents should start successfully

## Prevention

To avoid this in the future:

1. **Always activate venv** before running agents
2. **Check dependencies** before starting system
3. **Use the startup scripts** (they auto-check now)
4. **Keep requirements.txt** updated

## Summary

**Problem:** Missing Python packages
**Solution:** Run `.\check-and-install-dependencies.ps1`
**Result:** All dependencies installed and verified

The startup scripts now handle this automatically!

