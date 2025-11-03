#!/bin/bash

# Fixed script to start all agents in background with correct filenames
cd /home/ubuntu/Multi-agent-AI-Ecommerce

# Kill any existing agents first
pkill -f "python3.11 agents/" 2>/dev/null

# Create logs directory
mkdir -p logs/agents

echo "Starting all agents with correct filenames..."

# Core agents
nohup python3.11 agents/monitoring_agent.py > logs/agents/monitoring.log 2>&1 &
echo "Started monitoring_agent (port 8000)"
sleep 1

nohup python3.11 agents/order_agent_production_v2.py > logs/agents/order.log 2>&1 &
echo "Started order_agent (port 8001)"
sleep 1

nohup python3.11 agents/product_agent_production.py > logs/agents/product.log 2>&1 &
echo "Started product_agent (port 8002)"
sleep 1

nohup python3.11 agents/marketplace_connector_agent.py > logs/agents/marketplace.log 2>&1 &
echo "Started marketplace_agent (port 8003)"
sleep 1

nohup python3.11 agents/customer_agent_enhanced.py > logs/agents/customer.log 2>&1 &
echo "Started customer_agent (port 8004)"
sleep 1

nohup python3.11 agents/inventory_agent.py > logs/agents/inventory.log 2>&1 &
echo "Started inventory_agent (port 8005)"
sleep 1

nohup python3.11 agents/transport_management_agent_enhanced.py > logs/agents/transport.log 2>&1 &
echo "Started transport_agent (port 8006)"
sleep 1

nohup python3.11 agents/payment_agent_enhanced.py > logs/agents/payment.log 2>&1 &
echo "Started payment_agent (port 8007)"
sleep 1

nohup python3.11 agents/warehouse_agent.py > logs/agents/warehouse.log 2>&1 &
echo "Started warehouse_agent (port 8008)"
sleep 1

nohup python3.11 agents/document_generation_agent.py > logs/agents/document.log 2>&1 &
echo "Started document_agent (port 8009)"
sleep 1

nohup python3.11 agents/fraud_detection_agent.py > logs/agents/fraud.log 2>&1 &
echo "Started fraud_detection_agent (port 8010)"
sleep 1

nohup python3.11 agents/risk_anomaly_detection_agent.py > logs/agents/risk.log 2>&1 &
echo "Started risk_agent (port 8011)"
sleep 1

nohup python3.11 agents/knowledge_management_agent.py > logs/agents/knowledge.log 2>&1 &
echo "Started knowledge_agent (port 8012)"
sleep 1

nohup python3.11 agents/after_sales_agent_production.py > logs/agents/aftersales.log 2>&1 &
echo "Started aftersales_agent (port 8020)"
sleep 1

nohup python3.11 agents/backoffice_agent_production.py > logs/agents/backoffice.log 2>&1 &
echo "Started backoffice_agent (port 8021)"
sleep 1

nohup python3.11 agents/quality_control_agent_production.py > logs/agents/quality.log 2>&1 &
echo "Started quality_agent (port 8022)"
sleep 1

echo ""
echo "All agents started! Waiting 20 seconds for initialization..."
sleep 20

echo ""
echo "Checking running agents..."
ps aux | grep "python3.11 agents" | grep -v grep | wc -l
echo "agents are running"

