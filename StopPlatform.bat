@echo off
REM Stop Multi-Agent E-commerce Platform for Windows
REM This script stops all components: agents, frontend, and optionally database

echo ==========================================
echo Stopping Multi-Agent E-commerce Platform
echo ==========================================
echo.

echo Stopping Frontend UI...
taskkill /F /FI "WINDOWTITLE eq npm*" /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1

echo Stopping All Agents...
call StopAllAgents.bat

echo.
echo ==========================================
echo Platform Stopped!
echo ==========================================
echo.
echo Note: PostgreSQL is still running.
echo To stop PostgreSQL:
echo   - Windows Service: Stop "postgresql-x64-14" service
echo   - Or run: pg_ctl stop -D "C:\Program Files\PostgreSQL\14\data"
echo.

pause
