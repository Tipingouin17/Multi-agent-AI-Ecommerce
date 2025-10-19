@echo off
REM Start Multi-Agent E-commerce System

echo Starting Multi-Agent E-commerce System...
call venv\Scripts\activate.bat

REM Check if PostgreSQL is available
python -c "import psycopg2; psycopg2.connect('host=localhost port=5432 user=postgres dbname=postgres')" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠️  PostgreSQL not available or not configured
    echo 🎯 Starting in DEMO mode instead...
    echo 💡 This will show the system working without requiring database setup
    echo.
    python -m multi_agent_ecommerce.cli start --agents demo
) else (
    echo.
    echo ✅ PostgreSQL detected, starting full system...
    python -m multi_agent_ecommerce.cli start
)

pause
