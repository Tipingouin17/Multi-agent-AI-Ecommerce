@echo off
REM Start Multi-Agent E-commerce System - FIXED VERSION

echo Starting Multi-Agent E-commerce System...
call venv\Scripts\activate.bat

REM Test if the CLI start command works
python -m multi_agent_ecommerce.cli start --help >nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠️  CLI start command not working, using fallback method...
    echo 🔧 Starting agents directly...
    echo.
    
    REM Use the fallback CLI runner
    python run_cli.py start
    
    if errorlevel 1 (
        echo.
        echo ⚠️  Fallback also failed, starting demo mode...
        python run_cli.py start --agents demo
    )
) else (
    echo.
    echo ✅ CLI working, checking PostgreSQL...
    
    REM Check if PostgreSQL is available
    python -c "import psycopg2; psycopg2.connect('host=localhost port=5432 user=postgres dbname=multi_agent_ecommerce password=%DATABASE_PASSWORD%')" >nul 2>&1
    if errorlevel 1 (
        echo.
        echo ⚠️  PostgreSQL connection failed, starting in DEMO mode...
        echo 💡 This will show the system working without requiring database
        echo.
        python -m multi_agent_ecommerce.cli start --agents demo
    ) else (
        echo.
        echo ✅ PostgreSQL connected, starting full system...
        python -m multi_agent_ecommerce.cli start
    )
)

pause
