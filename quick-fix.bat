@echo off
REM Quick Fix Script for Multi-Agent E-commerce System
REM This script fixes common import and model issues

echo ========================================
echo Multi-Agent System Quick Fix
echo ========================================
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    echo Please run install.bat first
    pause
    exit /b 1
)

REM Install missing dependencies
echo.
echo Installing/updating dependencies...
python -m pip install --upgrade pip
python -m pip install asyncpg psycopg2-binary sqlalchemy pydantic fastapi
python -m pip install click structlog rich typer python-dotenv

REM Reinstall the package
echo.
echo Reinstalling package...
python -m pip uninstall -y multi-agent-ecommerce
python -m pip install -e .

REM Test the installation
echo.
echo Testing installation...
python -c "from multi_agent_ecommerce.shared.models import CustomerDB, ProductDB, OrderDB; print('Models import successful')" 2>nul
if errorlevel 1 (
    echo [WARNING] Model import test failed
    echo Trying alternative method...
    python -c "import multi_agent_ecommerce; print('Package import successful')" 2>nul
    if errorlevel 1 (
        echo [ERROR] Package import still failing
        echo Please check error messages above
    ) else (
        echo [OK] Package import successful
    )
) else (
    echo [OK] All models import successfully
)

REM Test CLI
echo.
echo Testing CLI...
python -m multi_agent_ecommerce.cli --help >nul 2>&1
if errorlevel 1 (
    echo [WARNING] CLI test failed, using fallback...
    python run_cli.py --help >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Both CLI methods failed
    ) else (
        echo [OK] Fallback CLI works
    )
) else (
    echo [OK] CLI test successful
)

echo.
echo ========================================
echo Quick fix completed
echo ========================================
echo.
echo You can now try:
echo   init-database.bat
echo   check-health.bat
echo   start-system.bat
echo.
echo Or use the fallback CLI:
echo   python run_cli.py init-db
echo   python run_cli.py health
echo   python run_cli.py start
echo.
pause
