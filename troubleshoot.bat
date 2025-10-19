@echo off
REM Multi-Agent E-commerce System - Troubleshooting Script
REM This script helps diagnose and fix common issues

echo ========================================
echo Multi-Agent System Troubleshooting
echo ========================================
echo.

REM Check Python installation
echo 1. Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH
    echo Please install Python 3.9+ from https://python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    goto :end
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo [OK] Python %%i found
)

REM Check virtual environment
echo.
echo 2. Checking virtual environment...
if exist venv (
    echo [OK] Virtual environment exists
    call venv\Scripts\activate.bat
    if errorlevel 1 (
        echo [ERROR] Failed to activate virtual environment
        echo Recreating virtual environment...
        rmdir /s /q venv
        python -m venv venv
        call venv\Scripts\activate.bat
    ) else (
        echo [OK] Virtual environment activated
    )
) else (
    echo [WARNING] Virtual environment not found
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
)

REM Check pip
echo.
echo 3. Checking pip...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip not available
    echo Installing pip...
    python -m ensurepip --upgrade
) else (
    echo [OK] pip is available
)

REM Check core dependencies
echo.
echo 4. Checking core dependencies...
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo [WARNING] FastAPI not found, installing core dependencies...
    python -m pip install fastapi uvicorn pydantic sqlalchemy asyncpg psycopg2-binary
) else (
    echo [OK] Core dependencies found
)

REM Check database dependencies
echo.
echo 5. Checking database dependencies...
python -c "import asyncpg" 2>nul
if errorlevel 1 (
    echo [WARNING] asyncpg not found, installing...
    python -m pip install asyncpg
) else (
    echo [OK] asyncpg found
)

python -c "import psycopg2" 2>nul
if errorlevel 1 (
    echo [WARNING] psycopg2 not found, installing...
    python -m pip install psycopg2-binary
) else (
    echo [OK] psycopg2 found
)

REM Check CLI dependencies
echo.
echo 6. Checking CLI dependencies...
python -c "import click, structlog" 2>nul
if errorlevel 1 (
    echo [WARNING] CLI dependencies not found, installing...
    python -m pip install click structlog rich typer python-dotenv
) else (
    echo [OK] CLI dependencies found
)

REM Test package import
echo.
echo 7. Testing package import...
python -c "import multi_agent_ecommerce; print('Package import successful')" 2>nul
if errorlevel 1 (
    echo [WARNING] Package import failed
    echo Installing package in development mode...
    python -m pip install -e .
    
    REM Test again
    python -c "import multi_agent_ecommerce; print('Package import successful')" 2>nul
    if errorlevel 1 (
        echo [WARNING] Package still not importable, using fallback method
        echo You can use run_cli.py as a fallback
    ) else (
        echo [OK] Package import successful after installation
    )
) else (
    echo [OK] Package import successful
)

REM Test CLI
echo.
echo 8. Testing CLI...
python -m multi_agent_ecommerce.cli --help >nul 2>&1
if errorlevel 1 (
    echo [WARNING] CLI test failed, trying fallback...
    python run_cli.py --help >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Both CLI methods failed
        echo Please check the error messages above
    ) else (
        echo [OK] Fallback CLI works - use run_cli.py instead of the normal CLI
    )
) else (
    echo [OK] CLI test successful
)

REM Check configuration
echo.
echo 9. Checking configuration...
if exist .env (
    echo [OK] .env file exists
) else (
    echo [WARNING] .env file not found
    if exist .env.example (
        copy .env.example .env
        echo [OK] Created .env from template
    ) else (
        echo [ERROR] No .env.example found
    )
)

REM Check PostgreSQL
echo.
echo 10. Checking PostgreSQL...
psql --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] PostgreSQL not found in PATH
    echo Please install PostgreSQL 12+ from https://www.postgresql.org/download/windows/
) else (
    for /f "tokens=3" %%i in ('psql --version 2^>^&1') do echo [OK] PostgreSQL %%i found
)

echo.
echo ========================================
echo Troubleshooting completed
echo ========================================
echo.
echo If you still have issues:
echo 1. Check the error messages above
echo 2. Try using run_cli.py instead of the normal CLI
echo 3. Ensure PostgreSQL is installed and running
echo 4. Edit .env with correct database credentials
echo.
echo Available commands after fixing issues:
echo   python run_cli.py status
echo   python run_cli.py health
echo   python run_cli.py init-db
echo   python run_cli.py start
echo.
pause

:end
