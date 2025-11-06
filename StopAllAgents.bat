@echo off
REM Stop All V3 Agents Script for Windows
REM This script stops all Python agent processes

echo ==========================================
echo Stopping All Agents
echo ==========================================
echo.

echo Stopping all Python agent processes...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM python3.exe /T >nul 2>&1
taskkill /F /IM python3.11.exe /T >nul 2>&1

echo.
echo All agent processes stopped!
echo.

pause
