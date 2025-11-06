#!/bin/bash

# Start All V3 Agents Script
# This script starts all 37 V3 agents in the background with correct port assignments
# Updated to include all 8 feature agents + 29 core agents

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
AGENTS_DIR="$SCRIPT_DIR/agents"
LOGS_DIR="$SCRIPT_DIR/logs/agents"

# Create logs directory
mkdir -p "$LOGS_DIR"

echo "=========================================="
echo "Starting All 37 V3 Agents"
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

echo "Core Business Agents (8):"
start_agent "order_agent_v3.py" 8000
start_agent "product_agent_v3.py" 8001
start_agent "inventory_agent_v3.py" 8002
start_agent "payment_agent_v3.py" 8004
start_agent "carrier_agent_v3.py" 8006
start_agent "customer_agent_v3.py" 8007
start_agent "returns_agent_v3.py" 8009
start_agent "fraud_detection_agent_v3.py" 8010

echo "Marketplace & Integration Agents (5):"
start_agent "marketplace_connector_v3.py" 8003
start_agent "dynamic_pricing_v3.py" 8005
start_agent "recommendation_agent_v3.py" 8014
start_agent "promotion_agent_v3.py" 8020
start_agent "d2c_ecommerce_agent_v3.py" 8026

echo "Operations & Support Agents (8):"
start_agent "warehouse_agent_v3.py" 8008
start_agent "transport_management_v3.py" 8015
start_agent "document_generation_agent_v3.py" 8016
start_agent "support_agent_v3.py" 8018
start_agent "customer_communication_v3.py" 8019
start_agent "after_sales_agent_v3.py" 8021
start_agent "backoffice_agent_v3.py" 8027
start_agent "quality_control_agent_v3.py" 8028

echo "Analytics & Reporting Agents (2):"
start_agent "analytics_agent_v3.py" 8013
start_agent "advanced_analytics_agent_v3.py" 8036

echo "Infrastructure & Monitoring Agents (6):"
start_agent "risk_anomaly_detection_v3.py" 8011
start_agent "knowledge_management_agent_v3.py" 8012
start_agent "infrastructure_v3.py" 8022
start_agent "monitoring_agent_v3.py" 8023
start_agent "ai_monitoring_agent_v3.py" 8024
start_agent "system_api_gateway_v3.py" 8100

echo "=========================================="
echo "Feature Agents - Priority 1 & 2 (8):"
echo "=========================================="
echo ""

start_agent "replenishment_agent_v3.py" 8031
start_agent "inbound_management_agent_v3.py" 8032
start_agent "fulfillment_agent_v3.py" 8033
start_agent "carrier_agent_ai_v3.py" 8034
start_agent "rma_agent_v3.py" 8035
start_agent "demand_forecasting_agent_v3.py" 8037
start_agent "international_shipping_agent_v3.py" 8038

echo "=========================================="
echo "All 37 agents started!"
echo "=========================================="
echo ""
echo "Logs available in: $LOGS_DIR"
echo ""
echo "To check agent status:"
echo "  curl http://localhost:8100/api/agents"
echo ""
echo "To verify all agents are healthy:"
echo "  ./check_all_agents.sh"
echo ""
echo "To stop all agents:"
echo "  ./stop_all_agents.sh"
echo ""
echo "Agent Port Mapping:"
echo ""
echo "Core Business Agents:"
echo "  8000 - order_agent"
echo "  8001 - product_agent"
echo "  8002 - inventory_agent"
echo "  8003 - marketplace_connector"
echo "  8004 - payment_agent"
echo "  8005 - dynamic_pricing"
echo "  8006 - carrier_agent"
echo "  8007 - customer_agent"
echo "  8008 - warehouse_agent"
echo "  8009 - returns_agent"
echo "  8010 - fraud_detection"
echo "  8011 - risk_anomaly_detection"
echo "  8012 - knowledge_management"
echo "  8013 - analytics_agent"
echo "  8014 - recommendation_agent"
echo "  8015 - transport_management"
echo "  8016 - document_generation"
echo "  8018 - support_agent"
echo "  8019 - customer_communication"
echo "  8020 - promotion_agent"
echo "  8021 - after_sales_agent"
echo "  8022 - infrastructure"
echo "  8023 - monitoring_agent"
echo "  8024 - ai_monitoring"
echo "  8026 - d2c_ecommerce"
echo "  8027 - backoffice_agent"
echo "  8028 - quality_control"
echo ""
echo "Feature Agents (Priority 1 & 2):"
echo "  8031 - replenishment_agent (Inventory Replenishment)"
echo "  8032 - inbound_management_agent (Inbound Workflow)"
echo "  8033 - fulfillment_agent (Advanced Fulfillment)"
echo "  8034 - carrier_agent_ai (Intelligent Carrier Selection with AI)"
echo "  8035 - rma_agent (Complete RMA Workflow)"
echo "  8036 - advanced_analytics_agent (Advanced Analytics & Reporting)"
echo "  8037 - demand_forecasting_agent (ML-Based Demand Forecasting)"
echo "  8038 - international_shipping_agent (International Shipping)"
echo ""
echo "Infrastructure:"
echo "  8100 - system_api_gateway"
echo ""
