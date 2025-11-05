@echo off
REM Start All V3 Agents Script for Windows
REM This script starts all 27 V3 agents in the background with correct port assignments

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set AGENTS_DIR=%SCRIPT_DIR%agents
set LOGS_DIR=%SCRIPT_DIR%logs\agents

REM Create logs directory
if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"

echo ==========================================
echo Starting All 27 V3 Agents
echo ==========================================
echo.

echo Core Business Agents (8):
call :start_agent "order_agent_v3.py" 8000
call :start_agent "product_agent_v3.py" 8001
call :start_agent "inventory_agent_v3.py" 8002
call :start_agent "payment_agent_v3.py" 8004
call :start_agent "carrier_agent_v3.py" 8006
call :start_agent "customer_agent_v3.py" 8007
call :start_agent "returns_agent_v3.py" 8009
call :start_agent "fraud_detection_agent_v3.py" 8010

echo.
echo Marketplace ^& Integration Agents (5):
call :start_agent "marketplace_connector_v3.py" 8003
call :start_agent "dynamic_pricing_v3.py" 8005
call :start_agent "recommendation_agent_v3.py" 8014
call :start_agent "promotion_agent_v3.py" 8020
call :start_agent "d2c_ecommerce_agent_v3.py" 8026

echo.
echo Operations ^& Support Agents (8):
call :start_agent "warehouse_agent_v3.py" 8008
call :start_agent "transport_management_v3.py" 8015
call :start_agent "document_generation_agent_v3.py" 8016
call :start_agent "support_agent_v3.py" 8018
call :start_agent "customer_communication_v3.py" 8019
call :start_agent "after_sales_agent_v3.py" 8021
call :start_agent "backoffice_agent_v3.py" 8027
call :start_agent "quality_control_agent_v3.py" 8028

echo.
echo Infrastructure ^& Monitoring Agents (6):
call :start_agent "risk_anomaly_detection_v3.py" 8011
call :start_agent "knowledge_management_agent_v3.py" 8012
call :start_agent "infrastructure_v3.py" 8022
call :start_agent "monitoring_agent_v3.py" 8023
call :start_agent "ai_monitoring_agent_v3.py" 8024
call :start_agent "system_api_gateway_v3.py" 8100

echo.
echo ==========================================
echo All 27 agents started!
echo ==========================================
echo.
echo Logs available in: %LOGS_DIR%
echo.
echo To check agent status:
echo   curl http://localhost:8100/api/agents
echo.
echo To verify all agents are healthy:
echo   check_all_agents.bat
echo.
echo To stop all agents:
echo   stop_all_agents.bat
echo.
echo Agent Port Mapping:
echo   8000 - order_agent
echo   8001 - product_agent
echo   8002 - inventory_agent
echo   8003 - marketplace_connector
echo   8004 - payment_agent
echo   8005 - dynamic_pricing
echo   8006 - carrier_agent
echo   8007 - customer_agent
echo   8008 - warehouse_agent
echo   8009 - returns_agent
echo   8010 - fraud_detection
echo   8011 - risk_anomaly_detection
echo   8012 - knowledge_management
echo   8014 - recommendation_agent
echo   8015 - transport_management
echo   8016 - document_generation
echo   8018 - support_agent
echo   8019 - customer_communication
echo   8020 - promotion_agent
echo   8021 - after_sales_agent
echo   8022 - infrastructure
echo   8023 - monitoring_agent
echo   8024 - ai_monitoring
echo   8026 - d2c_ecommerce
echo   8027 - backoffice_agent
echo   8028 - quality_control
echo   8100 - system_api_gateway
echo.

goto :eof

:start_agent
set agent_file=%~1
set port=%~2
set agent_name=%agent_file:.py=%

echo Starting %agent_name% on port %port%...

cd /d "%SCRIPT_DIR%"
start /B cmd /c "set API_PORT=%port% && python %AGENTS_DIR%\%agent_file% > %LOGS_DIR%\%agent_name%.log 2>&1"

timeout /t 1 /nobreak >nul
echo   Started successfully
echo.

goto :eof
