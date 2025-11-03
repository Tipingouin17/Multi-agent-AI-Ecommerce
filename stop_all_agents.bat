@echo off
REM ============================================================================
REM Stop All Agents - Windows Version
REM ============================================================================

echo ================================================================================
echo Multi-Agent E-commerce Platform - Stopping All Agents (Windows)
echo ================================================================================
echo.

echo Stopping all Python agent processes...
echo.

REM Kill all Python processes running agents
taskkill /F /FI "WINDOWTITLE eq Order Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Product Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Inventory Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Marketplace Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Payment Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Dynamic Pricing Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Carrier Selection Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Customer Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Customer Communication Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Returns Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Fraud Detection Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Recommendation Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Promotion Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Risk Anomaly Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Knowledge Management Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Transport Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Warehouse Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Document Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Support Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq D2C Ecommerce Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq After Sales Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Backoffice Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Infrastructure Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq AI Monitoring Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Monitoring Agent*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq Quality Control Agent*" >nul 2>nul

REM Also kill any Python processes running on agent ports
for /L %%p in (8000,1,8025) do (
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%%p ^| findstr LISTENING') do (
        taskkill /F /PID %%a >nul 2>nul
    )
)

echo.
echo ================================================================================
echo All agents stopped!
echo ================================================================================
echo.

