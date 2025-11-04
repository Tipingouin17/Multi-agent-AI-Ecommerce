#!/bin/bash

# Start All V3 Agents Script
# This script starts all 26 V3 agents in the background

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
AGENTS_DIR="$SCRIPT_DIR/agents"
LOGS_DIR="$SCRIPT_DIR/logs/agents"

# Create logs directory
mkdir -p "$LOGS_DIR"

echo "=========================================="
echo "Starting All V3 Agents"
echo "=========================================="
echo ""

# Function to start an agent
start_agent() {
    local agent_file=$1
    local port=$2
    local agent_name=$(basename "$agent_file" .py)
    
    echo "Starting $agent_name on port $port..."
    
    cd "$SCRIPT_DIR"
    API_PORT=$port python3.11 "$AGENTS_DIR/$agent_file" > "$LOGS_DIR/${agent_name}.log" 2>&1 &
    
    local pid=$!
    echo "  PID: $pid"
    
    # Wait a moment to check if it started
    sleep 0.5
    if ps -p $pid > /dev/null; then
        echo "  ✓ Started successfully"
    else
        echo "  ✗ Failed to start (check $LOGS_DIR/${agent_name}.log)"
    fi
    echo ""
}

# Start all agents
echo "Core Business Agents:"
start_agent "order_agent_v3.py" 8000
start_agent "product_agent_v3.py" 8001
start_agent "inventory_agent_v3.py" 8002
start_agent "payment_agent_v3.py" 8004
start_agent "carrier_agent_v3.py" 8006
start_agent "customer_agent_v3.py" 8008
start_agent "returns_agent_v3.py" 8009
start_agent "fraud_detection_agent_v3.py" 8010

echo "Support & Operations:"
start_agent "marketplace_connector_v3.py" 8003
start_agent "dynamic_pricing_v3.py" 8005
start_agent "recommendation_agent_v3.py" 8014
start_agent "transport_management_v3.py" 8015
start_agent "warehouse_agent_v3.py" 8016
start_agent "support_agent_v3.py" 8018
start_agent "customer_communication_v3.py" 8019
start_agent "infrastructure_v3.py" 8022

echo "Advanced Features:"
start_agent "promotion_agent_v3.py" 8020
start_agent "after_sales_agent_v3.py" 8021
start_agent "monitoring_agent_v3.py" 8023
start_agent "ai_monitoring_agent_v3.py" 8024
start_agent "risk_anomaly_detection_v3.py" 8025
start_agent "auth_agent.py" 8026
start_agent "backoffice_agent_v3.py" 8027
start_agent "quality_control_agent_v3.py" 8028
start_agent "document_generation_agent_v3.py" 8029
start_agent "knowledge_management_agent_v3.py" 8030

echo "System API Gateway:"
start_agent "system_api_gateway_v3.py" 8100

echo "=========================================="
echo "All agents started!"
echo "=========================================="
echo ""
echo "Logs available in: $LOGS_DIR"
echo ""
echo "To check agent status:"
echo "  curl http://localhost:8100/api/agents"
echo ""
echo "To stop all agents:"
echo "  ./stop_all_agents.sh"
echo ""
