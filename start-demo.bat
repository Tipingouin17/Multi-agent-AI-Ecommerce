@echo off
REM Start Multi-Agent E-commerce System in Demo Mode
REM This demonstrates the system working without requiring PostgreSQL, Kafka, or Redis

echo ========================================
echo Multi-Agent E-commerce System - DEMO
echo ========================================
echo.
echo 🎯 Starting in DEMO mode...
echo 📝 This shows the system working without external services
echo 🔧 No PostgreSQL, Kafka, or Redis required
echo.

call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Virtual environment not found
    echo Please run install.bat first
    pause
    exit /b 1
)

python -m multi_agent_ecommerce.cli start --agents demo

echo.
echo ========================================
echo Demo completed!
echo ========================================
echo.
echo To start the full system with real database:
echo 1. Set up PostgreSQL (see POSTGRESQL_SETUP_WINDOWS.md)
echo 2. Run: setup-database.bat
echo 3. Run: start-system.bat
echo.
pause
