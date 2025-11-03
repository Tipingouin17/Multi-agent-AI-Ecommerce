@echo off
REM ============================================================================
REM Start All 26 Agents - Windows Version
REM ============================================================================

echo ================================================================================
echo Multi-Agent E-commerce Platform - Starting All 26 Agents (Windows)
echo ================================================================================
echo.

REM Set database URL
set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/multi_agent_ecommerce

REM Create logs directory
if not exist logs\agents mkdir logs\agents

echo Starting all 26 agents...
echo.

REM Start each agent with unique port
start "Order Agent" /B python agents\order_agent_production_v2.py > logs\agents\order.log 2>&1
timeout /t 1 /nobreak > nul

start "Product Agent" /B python agents\product_agent_production.py > logs\agents\product.log 2>&1
timeout /t 1 /nobreak > nul

start "Inventory Agent" /B python agents\inventory_agent.py > logs\agents\inventory.log 2>&1
timeout /t 1 /nobreak > nul

start "Marketplace Agent" /B python agents\marketplace_connector_agent.py > logs\agents\marketplace.log 2>&1
timeout /t 1 /nobreak > nul

start "Payment Agent" /B python agents\payment_agent_enhanced.py > logs\agents\payment.log 2>&1
timeout /t 1 /nobreak > nul

start "Dynamic Pricing Agent" /B python agents\dynamic_pricing_agent.py > logs\agents\dynamic_pricing.log 2>&1
timeout /t 1 /nobreak > nul

start "Carrier Selection Agent" /B python agents\carrier_selection_agent.py > logs\agents\carrier_selection.log 2>&1
timeout /t 1 /nobreak > nul

start "Customer Agent" /B python agents\customer_agent_enhanced.py > logs\agents\customer.log 2>&1
timeout /t 1 /nobreak > nul

start "Customer Communication Agent" /B python agents\customer_communication_agent.py > logs\agents\customer_communication.log 2>&1
timeout /t 1 /nobreak > nul

start "Returns Agent" /B python agents\returns_agent.py > logs\agents\returns.log 2>&1
timeout /t 1 /nobreak > nul

start "Fraud Detection Agent" /B python agents\fraud_detection_agent.py > logs\agents\fraud_detection.log 2>&1
timeout /t 1 /nobreak > nul

start "Recommendation Agent" /B python agents\recommendation_agent.py > logs\agents\recommendation.log 2>&1
timeout /t 1 /nobreak > nul

start "Promotion Agent" /B python agents\promotion_agent.py > logs\agents\promotion.log 2>&1
timeout /t 1 /nobreak > nul

start "Risk Anomaly Agent" /B python agents\risk_anomaly_detection_agent.py > logs\agents\risk_anomaly.log 2>&1
timeout /t 1 /nobreak > nul

start "Knowledge Management Agent" /B python agents\knowledge_management_agent.py > logs\agents\knowledge_management.log 2>&1
timeout /t 1 /nobreak > nul

start "Transport Agent" /B python agents\transport_management_agent_enhanced.py > logs\agents\transport.log 2>&1
timeout /t 1 /nobreak > nul

start "Warehouse Agent" /B python agents\warehouse_agent.py > logs\agents\warehouse.log 2>&1
timeout /t 1 /nobreak > nul

start "Document Agent" /B python agents\document_generation_agent.py > logs\agents\document.log 2>&1
timeout /t 1 /nobreak > nul

start "Support Agent" /B python agents\support_agent.py > logs\agents\support.log 2>&1
timeout /t 1 /nobreak > nul

start "D2C Ecommerce Agent" /B python agents\d2c_ecommerce_agent.py > logs\agents\d2c_ecommerce.log 2>&1
timeout /t 1 /nobreak > nul

start "After Sales Agent" /B python agents\after_sales_agent_production.py > logs\agents\after_sales.log 2>&1
timeout /t 1 /nobreak > nul

start "Backoffice Agent" /B python agents\backoffice_agent_production.py > logs\agents\backoffice.log 2>&1
timeout /t 1 /nobreak > nul

start "Infrastructure Agent" /B python agents\infrastructure_agents.py > logs\agents\infrastructure.log 2>&1
timeout /t 1 /nobreak > nul

start "AI Monitoring Agent" /B python agents\ai_monitoring_agent_self_healing.py > logs\agents\ai_monitoring.log 2>&1
timeout /t 1 /nobreak > nul

start "Monitoring Agent" /B python agents\monitoring_agent.py > logs\agents\monitoring.log 2>&1
timeout /t 1 /nobreak > nul

start "Quality Control Agent" /B python agents\quality_control_agent_production.py > logs\agents\quality_control.log 2>&1

echo.
echo ================================================================================
echo All 26 agents started!
echo ================================================================================
echo.
echo Waiting 20 seconds for agents to initialize...
timeout /t 20 /nobreak > nul

echo.
echo Checking agent health...
python check_all_26_agents_health.py

echo.
echo ================================================================================
echo Agent logs are available in: logs\agents\
echo.
echo To stop all agents, run: stop_all_agents.bat
echo ================================================================================

