@echo off
REM Check All V3 Agents Health - Windows Version

setlocal enabledelayedexpansion

echo ==========================================
echo Checking All 27 V3 Agents Health
echo ==========================================
echo.

set total=0
set healthy=0
set offline=0

call :check_agent "order_agent" 8000
call :check_agent "product_agent" 8001
call :check_agent "inventory_agent" 8002
call :check_agent "marketplace_connector" 8003
call :check_agent "payment_agent" 8004
call :check_agent "dynamic_pricing" 8005
call :check_agent "carrier_agent" 8006
call :check_agent "customer_agent" 8007
call :check_agent "warehouse_agent" 8008
call :check_agent "returns_agent" 8009
call :check_agent "fraud_detection" 8010
call :check_agent "risk_anomaly_detection" 8011
call :check_agent "knowledge_management" 8012
call :check_agent "recommendation_agent" 8014
call :check_agent "transport_management" 8015
call :check_agent "document_generation" 8016
call :check_agent "support_agent" 8018
call :check_agent "customer_communication" 8019
call :check_agent "promotion_agent" 8020
call :check_agent "after_sales_agent" 8021
call :check_agent "infrastructure" 8022
call :check_agent "monitoring_agent" 8023
call :check_agent "ai_monitoring" 8024
call :check_agent "d2c_ecommerce" 8026
call :check_agent "backoffice_agent" 8027
call :check_agent "quality_control" 8028
call :check_agent "system_api_gateway" 8100

echo.
echo ==========================================
echo Health Check Summary
echo ==========================================
echo Total Agents: %total%
echo Healthy: %healthy%
echo Offline: %offline%

set /a health_percent=healthy*100/total
echo Health Rate: %health_percent%%%
echo.

if %offline% equ 0 (
    echo Status: ALL AGENTS HEALTHY
) else (
    echo Status: SOME AGENTS OFFLINE - REVIEW REQUIRED
)
echo.

goto :eof

:check_agent
set agent_name=%~1
set port=%~2
set /a total+=1

curl -s --max-time 2 http://localhost:%port%/health >nul 2>&1

if %errorlevel% equ 0 (
    echo [HEALTHY] %agent_name% ^(port %port%^)
    set /a healthy+=1
) else (
    echo [OFFLINE] %agent_name% ^(port %port%^)
    set /a offline+=1
)

goto :eof
