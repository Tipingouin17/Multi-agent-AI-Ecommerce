#!/bin/bash

# Script to start all agents with DATABASE_URL environment variable
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/multi_agent_ecommerce"

cd /home/ubuntu/Multi-agent-AI-Ecommerce

# Kill any existing agents first
pkill -f "python3.11 agents/" 2>/dev/null
sleep 2

# Create logs directory
mkdir -p logs/agents

echo "Starting all agents with DATABASE_URL=$DATABASE_URL"
echo ""

# Core agents
nohup python3.11 agents/monitoring_agent.py > logs/agents/monitoring.log 2>&1 &
echo "✓ Started monitoring_agent (port 8000)"
sleep 2

nohup python3.11 agents/order_agent_production_v2.py > logs/agents/order.log 2>&1 &
echo "✓ Started order_agent (port 8001)"
sleep 2

nohup python3.11 agents/product_agent_production.py > logs/agents/product.log 2>&1 &
echo "✓ Started product_agent (port 8002)"
sleep 2

nohup python3.11 agents/marketplace_connector_agent.py > logs/agents/marketplace.log 2>&1 &
echo "✓ Started marketplace_agent (port 8003)"
sleep 2

nohup python3.11 agents/customer_agent_enhanced.py > logs/agents/customer.log 2>&1 &
echo "✓ Started customer_agent (port 8004)"
sleep 2

nohup python3.11 agents/inventory_agent.py > logs/agents/inventory.log 2>&1 &
echo "✓ Started inventory_agent (port 8005)"
sleep 2

nohup python3.11 agents/transport_management_agent_enhanced.py > logs/agents/transport.log 2>&1 &
echo "✓ Started transport_agent (port 8006)"
sleep 2

nohup python3.11 agents/payment_agent_enhanced.py > logs/agents/payment.log 2>&1 &
echo "✓ Started payment_agent (port 8007)"
sleep 2

nohup python3.11 agents/warehouse_agent.py > logs/agents/warehouse.log 2>&1 &
echo "✓ Started warehouse_agent (port 8008)"
sleep 2

nohup python3.11 agents/document_generation_agent.py > logs/agents/document.log 2>&1 &
echo "✓ Started document_agent (port 8009)"
sleep 2

nohup python3.11 agents/fraud_detection_agent.py > logs/agents/fraud.log 2>&1 &
echo "✓ Started fraud_detection_agent (port 8010)"
sleep 2

nohup python3.11 agents/risk_anomaly_detection_agent.py > logs/agents/risk.log 2>&1 &
echo "✓ Started risk_agent (port 8011)"
sleep 2

nohup python3.11 agents/knowledge_management_agent.py > logs/agents/knowledge.log 2>&1 &
echo "✓ Started knowledge_agent (port 8012)"
sleep 2

nohup python3.11 agents/after_sales_agent_production.py > logs/agents/aftersales.log 2>&1 &
echo "✓ Started aftersales_agent (port 8020)"
sleep 2

nohup python3.11 agents/backoffice_agent_production.py > logs/agents/backoffice.log 2>&1 &
echo "✓ Started backoffice_agent (port 8021)"
sleep 2

nohup python3.11 agents/quality_control_agent_production.py > logs/agents/quality.log 2>&1 &
echo "✓ Started quality_agent (port 8022)"
sleep 2

echo ""
echo "All agents started! Waiting 15 seconds for full initialization..."
sleep 15

echo ""
echo "=== Agent Status ==="
RUNNING=$(ps aux | grep "python3.11 agents" | grep -v grep | wc -l)
echo "Running agents: $RUNNING / 16"
echo ""

if [ $RUNNING -gt 10 ]; then
    echo "✅ Most agents started successfully!"
else
    echo "⚠️  Some agents may have failed to start. Check logs in logs/agents/"
fi

