#!/bin/bash

# Comprehensive Startup Script for All 26 Agents
# Each agent gets a unique port from 8000-8025

export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/multi_agent_ecommerce"

cd /home/ubuntu/Multi-agent-AI-Ecommerce

# Kill any existing agents
echo "Stopping existing agents..."
pkill -f "python3.11 agents/" 2>/dev/null
sleep 3

# Create logs directory
mkdir -p logs/agents

echo "=" * 80
echo "Starting All 26 Agents with Unique Ports (8000-8025)"
echo "=" * 80
echo ""

# Port 8000: Order Agent
API_PORT=8000 nohup python3.11 agents/order_agent_production_v2.py > logs/agents/order.log 2>&1 &
echo "✓ [8000] order_agent"
sleep 1

# Port 8001: Product Agent
API_PORT=8001 nohup python3.11 agents/product_agent_production.py > logs/agents/product.log 2>&1 &
echo "✓ [8001] product_agent"
sleep 1

# Port 8002: Inventory Agent
API_PORT=8002 nohup python3.11 agents/inventory_agent.py > logs/agents/inventory.log 2>&1 &
echo "✓ [8002] inventory_agent"
sleep 1

# Port 8003: Marketplace Connector Agent
API_PORT=8003 nohup python3.11 agents/marketplace_connector_agent.py > logs/agents/marketplace.log 2>&1 &
echo "✓ [8003] marketplace_agent"
sleep 1

# Port 8004: Payment Agent
API_PORT=8004 nohup python3.11 agents/payment_agent_enhanced.py > logs/agents/payment.log 2>&1 &
echo "✓ [8004] payment_agent"
sleep 1

# Port 8005: Dynamic Pricing Agent
API_PORT=8005 nohup python3.11 agents/dynamic_pricing_agent.py > logs/agents/dynamic_pricing.log 2>&1 &
echo "✓ [8005] dynamic_pricing_agent"
sleep 1

# Port 8006: Carrier Selection Agent
API_PORT=8006 nohup python3.11 agents/carrier_selection_agent.py > logs/agents/carrier.log 2>&1 &
echo "✓ [8006] carrier_selection_agent"
sleep 1

# Port 8007: Customer Agent Enhanced
API_PORT=8007 nohup python3.11 agents/customer_agent_enhanced.py > logs/agents/customer.log 2>&1 &
echo "✓ [8007] customer_agent"
sleep 1

# Port 8008: Customer Communication Agent
API_PORT=8008 nohup python3.11 agents/customer_communication_agent.py > logs/agents/customer_comm.log 2>&1 &
echo "✓ [8008] customer_communication_agent"
sleep 1

# Port 8009: Returns Agent
API_PORT=8009 nohup python3.11 agents/returns_agent.py > logs/agents/returns.log 2>&1 &
echo "✓ [8009] returns_agent"
sleep 1

# Port 8010: Fraud Detection Agent
API_PORT=8010 nohup python3.11 agents/fraud_detection_agent.py > logs/agents/fraud.log 2>&1 &
echo "✓ [8010] fraud_detection_agent"
sleep 1

# Port 8011: Recommendation Agent
API_PORT=8011 nohup python3.11 agents/recommendation_agent.py > logs/agents/recommendation.log 2>&1 &
echo "✓ [8011] recommendation_agent"
sleep 1

# Port 8012: Promotion Agent
API_PORT=8012 nohup python3.11 agents/promotion_agent.py > logs/agents/promotion.log 2>&1 &
echo "✓ [8012] promotion_agent"
sleep 1

# Port 8013: Risk Anomaly Detection Agent
API_PORT=8013 nohup python3.11 agents/risk_anomaly_detection_agent.py > logs/agents/risk.log 2>&1 &
echo "✓ [8013] risk_anomaly_detection_agent"
sleep 1

# Port 8014: Knowledge Management Agent
API_PORT=8014 nohup python3.11 agents/knowledge_management_agent.py > logs/agents/knowledge.log 2>&1 &
echo "✓ [8014] knowledge_agent"
sleep 1

# Port 8015: Transport Management Agent (uses PORT not API_PORT)
PORT=8015 nohup python3.11 agents/transport_management_agent_enhanced.py > logs/agents/transport.log 2>&1 &
echo "✓ [8015] transport_agent"
sleep 1

# Port 8016: Warehouse Agent
API_PORT=8016 nohup python3.11 agents/warehouse_agent.py > logs/agents/warehouse.log 2>&1 &
echo "✓ [8016] warehouse_agent"
sleep 1

# Port 8017: Document Generation Agent
API_PORT=8017 nohup python3.11 agents/document_generation_agent.py > logs/agents/document.log 2>&1 &
echo "✓ [8017] document_agent"
sleep 1

# Port 8018: Support Agent
API_PORT=8018 nohup python3.11 agents/support_agent.py > logs/agents/support.log 2>&1 &
echo "✓ [8018] support_agent"
sleep 1

# Port 8019: D2C Ecommerce Agent
API_PORT=8019 nohup python3.11 agents/d2c_ecommerce_agent.py > logs/agents/d2c.log 2>&1 &
echo "✓ [8019] d2c_ecommerce_agent"
sleep 1

# Port 8020: After Sales Agent
API_PORT=8020 nohup python3.11 agents/after_sales_agent_production.py > logs/agents/aftersales.log 2>&1 &
echo "✓ [8020] after_sales_agent"
sleep 1

# Port 8021: Backoffice Agent
API_PORT=8021 nohup python3.11 agents/backoffice_agent_production.py > logs/agents/backoffice.log 2>&1 &
echo "✓ [8021] backoffice_agent"
sleep 1

# Port 8022: Infrastructure Agents
API_PORT=8022 nohup python3.11 agents/infrastructure_agents.py > logs/agents/infrastructure.log 2>&1 &
echo "✓ [8022] infrastructure_agents"
sleep 1

# Port 8023: AI Monitoring Agent
API_PORT=8023 nohup python3.11 agents/ai_monitoring_agent_self_healing.py > logs/agents/ai_monitoring.log 2>&1 &
echo "✓ [8023] ai_monitoring_agent"
sleep 1

# Port 8024: Monitoring Agent
API_PORT=8024 nohup python3.11 agents/monitoring_agent.py > logs/agents/monitoring.log 2>&1 &
echo "✓ [8024] monitoring_agent"
sleep 1

# Port 8025: Quality Control Agent
API_PORT=8025 nohup python3.11 agents/quality_control_agent_production.py > logs/agents/quality.log 2>&1 &
echo "✓ [8025] quality_control_agent"
sleep 1

echo ""
echo "All 26 agents started! Waiting 20 seconds for initialization..."
sleep 20

echo ""
echo "=" * 80
echo "AGENT STATUS"
echo "=" * 80

# Count running agents
RUNNING=$(ps aux | grep "python3.11 agents" | grep -v grep | wc -l)
echo "Running agents: $RUNNING / 26"

if [ $RUNNING -ge 20 ]; then
    echo "✅ Most agents started successfully!"
elif [ $RUNNING -ge 15 ]; then
    echo "⚠️  Some agents may have failed. Check logs in logs/agents/"
else
    echo "❌ Many agents failed to start. Check logs in logs/agents/"
fi

echo ""
echo "Check individual agent logs:"
echo "  tail -f logs/agents/<agent_name>.log"
echo ""
echo "Test health endpoints:"
echo "  curl http://localhost:8000/health  # order"
echo "  curl http://localhost:8001/health  # product"
echo "  # ... etc for ports 8000-8025"
echo ""

