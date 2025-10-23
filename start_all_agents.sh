#!/bin/bash

#
# Multi-Agent E-commerce Platform - Startup Script
#
# This script starts all 16 agents in the background
# Each agent runs on its designated port
#

echo "================================================================================"
echo "Multi-Agent E-commerce Platform - Starting All Agents"
echo "================================================================================"

# Set project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS_DIR="$PROJECT_ROOT/agents"
LOGS_DIR="$PROJECT_ROOT/logs"

# Create logs directory
mkdir -p "$LOGS_DIR"

# Function to start an agent
start_agent() {
    local agent_name=$1
    local agent_file=$2
    local port=$3
    
    echo "Starting $agent_name on port $port..."
    
    cd "$AGENTS_DIR"
    nohup python3 "$agent_file" > "$LOGS_DIR/${agent_name}.log" 2>&1 &
    local pid=$!
    
    echo "  PID: $pid"
    echo "  Log: $LOGS_DIR/${agent_name}.log"
    
    # Wait a moment to check if it started successfully
    sleep 1
    
    if ps -p $pid > /dev/null; then
        echo "  ✅ Started successfully"
    else
        echo "  ❌ Failed to start (check log file)"
    fi
    
    echo ""
}

echo ""
echo "Starting agents..."
echo ""

# Start all 16 agents
start_agent "monitoring" "monitoring_agent.py" 8000
start_agent "order" "order_agent_production_v2.py" 8001
start_agent "product" "product_agent_production.py" 8002
start_agent "marketplace" "marketplace_connector_agent.py" 8003
start_agent "customer" "customer_agent_enhanced.py" 8004
start_agent "inventory" "inventory_agent.py" 8005
start_agent "transport" "transport_agent_production.py" 8006
start_agent "payment" "payment_agent_enhanced.py" 8007
start_agent "warehouse" "warehouse_agent_production.py" 8008
start_agent "document" "document_generation_agent.py" 8009
start_agent "fraud" "fraud_detection_agent.py" 8010
start_agent "risk" "risk_anomaly_detection_agent.py" 8011
start_agent "knowledge" "knowledge_management_agent.py" 8012
start_agent "aftersales" "after_sales_agent_production.py" 8020
start_agent "backoffice" "backoffice_agent_production.py" 8021
start_agent "quality" "quality_control_agent_production.py" 8022

echo "================================================================================"
echo "All agents started!"
echo "================================================================================"
echo ""
echo "To check agent status:"
echo "  ./check_agents_status.sh"
echo ""
echo "To stop all agents:"
echo "  ./stop_all_agents.sh"
echo ""
echo "To view logs:"
echo "  tail -f logs/<agent_name>.log"
echo ""
echo "================================================================================"

