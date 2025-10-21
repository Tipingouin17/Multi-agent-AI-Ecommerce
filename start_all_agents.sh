#!/bin/bash
# Master Script to Start All 38 Agents
# Multi-Agent AI E-commerce Platform

set -e

echo "================================"
echo "Starting All 38 Agents"
echo "================================"
echo ""

# Create logs directory
mkdir -p logs

# Function to start an agent
start_agent() {
    local agent_file=$1
    local agent_name=$2
    local port=$3
    
    echo "Starting $agent_name on port $port..."
    python3 agents/$agent_file > logs/$agent_name.log 2>&1 &
    echo "  PID: $!"
    sleep 0.5
}

echo "1. Starting Core E-commerce Agents (8)..."
echo "----------------------------------------"
start_agent "product_agent_production.py" "product_agent" 8002
start_agent "order_agent_production.py" "order_agent" 8001
start_agent "inventory_agent_enhanced.py" "inventory_agent" 8003
start_agent "warehouse_agent_production.py" "warehouse_agent" 8004
start_agent "payment_agent_enhanced.py" "payment_agent" 8005
start_agent "shipping_agent_ai.py" "shipping_agent" 8006
start_agent "customer_agent_enhanced.py" "customer_agent" 8007
start_agent "returns_agent.py" "returns_agent" 8008
echo ""

echo "2. Starting AI-Powered Intelligence Agents (12)..."
echo "---------------------------------------------------"
start_agent "recommendation_agent.py" "recommendation_agent" 8009
start_agent "demand_forecasting_agent.py" "demand_forecasting_agent" 8010
start_agent "dynamic_pricing_agent.py" "dynamic_pricing_agent" 8011
start_agent "fraud_detection_agent.py" "fraud_detection_agent" 8012
start_agent "risk_anomaly_detection_agent.py" "risk_anomaly_agent" 8013
start_agent "chatbot_agent.py" "chatbot_agent" 8014
start_agent "support_agent.py" "support_agent" 8015
start_agent "analytics_agent_complete.py" "analytics_agent" 8016
start_agent "ai_monitoring_agent.py" "ai_monitoring_agent" 8017
start_agent "knowledge_management_agent.py" "knowledge_agent" 8018
start_agent "promotion_agent.py" "promotion_agent" 8019
start_agent "carrier_selection_agent.py" "carrier_selection_agent" 8020
echo ""

echo "3. Starting Marketplace & Channel Agents (4)..."
echo "------------------------------------------------"
start_agent "marketplace_connector_agent.py" "marketplace_connector" 8021
start_agent "standard_marketplace_agent.py" "standard_marketplace" 8022
start_agent "refurbished_marketplace_agent.py" "refurbished_marketplace" 8023
start_agent "d2c_ecommerce_agent.py" "d2c_ecommerce" 8024
echo ""

echo "4. Starting Operations & Logistics Agents (6)..."
echo "-------------------------------------------------"
start_agent "warehouse_selection_agent.py" "warehouse_selection" 8025
start_agent "reverse_logistics_agent.py" "reverse_logistics" 8026
start_agent "supplier_agent.py" "supplier_agent" 8027
start_agent "tax_agent.py" "tax_agent" 8028
start_agent "compliance_agent.py" "compliance_agent" 8029
start_agent "notification_agent.py" "notification_agent" 8030
echo ""

echo "5. Starting Communication & Workflow Agents (5)..."
echo "---------------------------------------------------"
start_agent "workflow_orchestration_agent.py" "workflow_orchestration" 8031
start_agent "customer_communication_agent.py" "customer_communication" 8032
start_agent "infrastructure_agents.py" "infrastructure_agents" 8033
start_agent "product_agent_api.py" "product_api" 8034
echo ""

echo "================================"
echo "✅ All 38 Agents Started!"
echo "================================"
echo ""
echo "Agent Logs: ./logs/"
echo "Check Status: curl http://localhost:8000/api/agents"
echo ""
echo "To stop all agents: ./stop_all_agents.sh"
echo ""

# Save PIDs to file for easy stopping
ps aux | grep "python3 agents/" | grep -v grep | awk '{print $2}' > logs/agent_pids.txt

echo "Agent PIDs saved to logs/agent_pids.txt"
echo ""
echo "🚀 System Ready!"

