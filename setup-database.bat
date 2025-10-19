@echo off
REM Database Setup Helper for Multi-Agent E-commerce System
REM This script helps set up PostgreSQL database

echo ========================================
echo Database Setup Helper
echo ========================================
echo.

REM Check if PostgreSQL is installed
echo 1. Checking PostgreSQL installation...
psql --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PostgreSQL not found in PATH
    echo.
    echo Please install PostgreSQL first:
    echo 1. Download from: https://www.postgresql.org/download/windows/
    echo 2. Install with default settings
    echo 3. Remember the postgres user password
    echo 4. Add PostgreSQL bin directory to PATH
    echo.
    echo Common PostgreSQL bin locations:
    echo   C:\Program Files\PostgreSQL\15\bin
    echo   C:\Program Files\PostgreSQL\16\bin
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=3" %%i in ('psql --version 2^>^&1') do echo [OK] PostgreSQL %%i found
)

REM Check if PostgreSQL service is running
echo.
echo 2. Checking PostgreSQL service...
sc query postgresql-x64-15 >nul 2>&1
if errorlevel 1 (
    sc query postgresql-x64-16 >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] PostgreSQL service not found
        echo Trying to start common service names...
        net start postgresql >nul 2>&1
        if errorlevel 1 (
            echo [ERROR] Could not start PostgreSQL service
            echo Please start PostgreSQL manually:
            echo 1. Open Services (services.msc)
            echo 2. Find PostgreSQL service
            echo 3. Right-click and Start
            pause
            exit /b 1
        )
    ) else (
        net start postgresql-x64-16 >nul 2>&1
    )
) else (
    net start postgresql-x64-15 >nul 2>&1
)
echo [OK] PostgreSQL service is running

REM Test basic connection
echo.
echo 3. Testing PostgreSQL connection...
set /p DB_PASSWORD="Enter postgres user password: "
echo Testing connection...
echo SELECT 1; | psql -h localhost -U postgres -d postgres -q >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Cannot connect to PostgreSQL
    echo Please check:
    echo 1. PostgreSQL service is running
    echo 2. Password is correct
    echo 3. Firewall allows connections on port 5432
    pause
    exit /b 1
) else (
    echo [OK] PostgreSQL connection successful
)

REM Check if database exists
echo.
echo 4. Checking if database exists...
echo SELECT 1 FROM pg_database WHERE datname='multi_agent_ecommerce'; | psql -h localhost -U postgres -d postgres -t -q 2>nul | findstr "1" >nul
if errorlevel 1 (
    echo [INFO] Database does not exist, creating...
    echo CREATE DATABASE multi_agent_ecommerce; | psql -h localhost -U postgres -d postgres -q
    if errorlevel 1 (
        echo [ERROR] Failed to create database
        pause
        exit /b 1
    ) else (
        echo [OK] Database created successfully
    )
) else (
    echo [OK] Database already exists
)

REM Update .env file
echo.
echo 5. Updating configuration...
if exist .env (
    echo [INFO] Updating .env file with database settings...
    
    REM Create temporary file with updated settings
    echo # Multi-Agent E-commerce System Configuration > .env.tmp
    echo ENVIRONMENT=development >> .env.tmp
    echo LOG_LEVEL=INFO >> .env.tmp
    echo DATABASE_HOST=localhost >> .env.tmp
    echo DATABASE_PORT=5432 >> .env.tmp
    echo DATABASE_NAME=multi_agent_ecommerce >> .env.tmp
    echo DATABASE_USER=postgres >> .env.tmp
    echo DATABASE_PASSWORD=%DB_PASSWORD% >> .env.tmp
    echo KAFKA_BOOTSTRAP_SERVERS=localhost:9092 >> .env.tmp
    echo REDIS_URL=redis://localhost:6379/0 >> .env.tmp
    echo MULTI_AGENT_MASTER_KEY=change_this_in_production >> .env.tmp
    
    REM Replace old .env with new one
    move .env.tmp .env >nul
    echo [OK] Configuration updated
) else (
    echo [ERROR] .env file not found
    echo Please run install.bat first
    pause
    exit /b 1
)

REM Test database connection with new settings
echo.
echo 6. Testing database connection with new settings...
call venv\Scripts\activate.bat >nul 2>&1
python run_cli.py health >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Health check failed, but database setup is complete
    echo You may need to run: quick-fix.bat
) else (
    echo [OK] Health check passed
)

REM Initialize database tables
echo.
echo 7. Initializing database tables...
python run_cli.py init-db
if errorlevel 1 (
    echo [ERROR] Database initialization failed
    echo Please check the error messages above
    pause
    exit /b 1
) else (
    echo [OK] Database tables created successfully
)

REM Verify tables were created
echo.
echo 8. Verifying database setup...
echo \dt | psql -h localhost -U postgres -d multi_agent_ecommerce -q 2>nul | findstr "customers\|products\|orders" >nul
if errorlevel 1 (
    echo [WARNING] Could not verify tables, but initialization completed
) else (
    echo [OK] Database tables verified
)

echo.
echo ========================================
echo Database setup completed successfully!
echo ========================================
echo.
echo Database Details:
echo   Host: localhost
echo   Port: 5432
echo   Database: multi_agent_ecommerce
echo   User: postgres
echo.
echo You can now:
echo   1. Run: check-health.bat
echo   2. Run: start-system.bat
echo   3. Use pgAdmin to manage the database
echo.
echo Database connection string:
echo   postgresql://postgres:%DB_PASSWORD%@localhost:5432/multi_agent_ecommerce
echo.
pause
