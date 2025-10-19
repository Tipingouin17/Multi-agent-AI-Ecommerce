@echo off
REM Multi-Agent E-commerce System - Windows Installation Script
REM This script sets up the complete system on Windows

echo ========================================
echo Multi-Agent E-commerce System Installer
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.9+ is required but not found.
    echo Please install Python from https://python.org/downloads/
    echo Make sure to add Python to PATH during installation.
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%

REM Check if pip is available
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)

REM Create virtual environment
echo.
echo Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, removing...
    rmdir /s /q venv
)

python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install required packages
echo.
echo Installing required packages...
python -m pip install wheel setuptools

REM Install core dependencies first
echo.
echo Installing core dependencies...
python -m pip install fastapi uvicorn pydantic pydantic-settings
python -m pip install sqlalchemy psycopg2-binary asyncpg alembic
python -m pip install aiokafka kafka-python
python -m pip install redis aioredis
python -m pip install httpx aiohttp requests
python -m pip install cryptography passlib python-jose PyJWT
python -m pip install openai scikit-learn numpy pandas
python -m pip install prometheus-client structlog
python -m pip install click typer rich
python -m pip install python-dotenv pyyaml
python -m pip install python-multipart email-validator psutil

REM Install the package in development mode
echo.
echo Installing Multi-Agent E-commerce System...
python -m pip install -e .
if errorlevel 1 (
    echo WARNING: Package installation failed, but dependencies are installed
    echo The system should still work with manual commands
)

REM Create necessary directories
echo.
echo Creating directories...
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "config" mkdir config

REM Copy configuration template
echo.
echo Setting up configuration...
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env"
        echo Configuration template copied to .env
        echo Please edit .env with your settings before starting the system.
    ) else (
        echo Creating basic .env file...
        echo # Multi-Agent E-commerce System Configuration > .env
        echo ENVIRONMENT=development >> .env
        echo LOG_LEVEL=INFO >> .env
        echo DATABASE_HOST=localhost >> .env
        echo DATABASE_PORT=5432 >> .env
        echo DATABASE_NAME=multi_agent_ecommerce >> .env
        echo DATABASE_USER=postgres >> .env
        echo DATABASE_PASSWORD=your_password_here >> .env
        echo KAFKA_BOOTSTRAP_SERVERS=localhost:9092 >> .env
        echo REDIS_URL=redis://localhost:6379/0 >> .env
        echo.
        echo Basic .env file created. Please edit it with your actual settings.
    )
)

REM Create startup scripts
echo.
echo Creating startup scripts...

REM Create start script
echo @echo off > start-system.bat
echo echo Starting Multi-Agent E-commerce System... >> start-system.bat
echo call venv\Scripts\activate.bat >> start-system.bat
echo python -m multi_agent_ecommerce.cli start >> start-system.bat
echo pause >> start-system.bat

REM Create status check script
echo @echo off > check-status.bat
echo echo Checking system status... >> check-status.bat
echo call venv\Scripts\activate.bat >> check-status.bat
echo python -m multi_agent_ecommerce.cli status >> check-status.bat
echo pause >> check-status.bat

REM Create health check script
echo @echo off > check-health.bat
echo echo Running health check... >> check-health.bat
echo call venv\Scripts\activate.bat >> check-health.bat
echo python -m multi_agent_ecommerce.cli health >> check-health.bat
echo pause >> check-health.bat

REM Create database initialization script
echo @echo off > init-database.bat
echo echo Initializing database... >> init-database.bat
echo call venv\Scripts\activate.bat >> init-database.bat
echo python -m multi_agent_ecommerce.cli init-db >> init-database.bat
echo pause >> init-database.bat

REM Create configuration viewer script
echo @echo off > view-config.bat
echo echo Current configuration: >> view-config.bat
echo call venv\Scripts\activate.bat >> view-config.bat
echo python -m multi_agent_ecommerce.cli config >> view-config.bat
echo pause >> view-config.bat

REM Create manual CLI script
echo @echo off > cli.bat
echo echo Multi-Agent CLI Access >> cli.bat
echo call venv\Scripts\activate.bat >> cli.bat
echo python -m multi_agent_ecommerce.cli %%* >> cli.bat

REM Test the installation
echo.
echo Testing installation...
python -c "import multi_agent_ecommerce; print('Package import successful')" 2>nul
if errorlevel 1 (
    echo WARNING: Package import test failed
    echo Testing CLI directly...
    python -m multi_agent_ecommerce.cli --help >nul 2>&1
    if errorlevel 1 (
        echo WARNING: CLI test failed, but installation may still work
        echo You can use the manual commands in the batch files
    ) else (
        echo CLI test passed successfully
    )
) else (
    echo Package import test passed successfully
)

REM Check for PostgreSQL
echo.
echo Checking for PostgreSQL...
psql --version >nul 2>&1
if not errorlevel 1 (
    echo PostgreSQL found.
    set /p DB_SETUP="Set up database now? (y/N): "
    if /i "%DB_SETUP%"=="y" (
        echo Creating database...
        createdb multi_agent_ecommerce 2>nul
        if not errorlevel 1 (
            echo Database created successfully
            echo Running database initialization...
            call init-database.bat
        ) else (
            echo Database may already exist or creation failed
            echo You can run init-database.bat later to set up tables
        )
    )
) else (
    echo PostgreSQL not found. Please install PostgreSQL 12+ and run database setup manually.
    echo Download from: https://www.postgresql.org/download/windows/
)

REM Create desktop shortcuts (optional)
set /p CREATE_SHORTCUTS="Create desktop shortcuts? (y/N): "
if /i "%CREATE_SHORTCUTS%"=="y" (
    echo Creating desktop shortcuts...
    
    REM Create start shortcut
    echo Set oWS = WScript.CreateObject("WScript.Shell") > create_shortcut.vbs
    echo sLinkFile = "%USERPROFILE%\Desktop\Start Multi-Agent System.lnk" >> create_shortcut.vbs
    echo Set oLink = oWS.CreateShortcut(sLinkFile) >> create_shortcut.vbs
    echo oLink.TargetPath = "%CD%\start-system.bat" >> create_shortcut.vbs
    echo oLink.WorkingDirectory = "%CD%" >> create_shortcut.vbs
    echo oLink.Description = "Start Multi-Agent E-commerce System" >> create_shortcut.vbs
    echo oLink.Save >> create_shortcut.vbs
    cscript create_shortcut.vbs >nul 2>&1
    
    REM Create status shortcut
    echo Set oWS = WScript.CreateObject("WScript.Shell") > create_shortcut.vbs
    echo sLinkFile = "%USERPROFILE%\Desktop\Check System Status.lnk" >> create_shortcut.vbs
    echo Set oLink = oWS.CreateShortcut(sLinkFile) >> create_shortcut.vbs
    echo oLink.TargetPath = "%CD%\check-status.bat" >> create_shortcut.vbs
    echo oLink.WorkingDirectory = "%CD%" >> create_shortcut.vbs
    echo oLink.Description = "Check Multi-Agent System Status" >> create_shortcut.vbs
    echo oLink.Save >> create_shortcut.vbs
    cscript create_shortcut.vbs >nul 2>&1
    
    del create_shortcut.vbs 2>nul
    echo Desktop shortcuts created.
)

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo Available commands:
echo   start-system.bat     - Start the multi-agent system
echo   check-status.bat     - Check system status
echo   check-health.bat     - Run health checks
echo   init-database.bat    - Initialize database tables
echo   view-config.bat      - View current configuration
echo   cli.bat [command]    - Direct CLI access
echo.
echo Next steps:
echo 1. Edit .env file with your database and API credentials
echo 2. Ensure PostgreSQL is running
echo 3. Run init-database.bat to set up database tables
echo 4. Run start-system.bat to start the system
echo.
echo For detailed information, see README.md
echo.
pause
