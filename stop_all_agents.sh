#!/bin/bash

#
# Multi-Agent E-commerce Platform - Stop All Agents
#
# This script stops all running agents
#

echo "================================================================================"
echo "Multi-Agent E-commerce Platform - Stopping All Agents"
echo "================================================================================"
echo ""

# Find and kill all Python processes running agent files
echo "Finding running agents..."

# Kill by port (more reliable)
declare -A PORTS
PORTS[8000]="monitoring"
PORTS[8001]="order"
PORTS[8002]="product"
PORTS[8003]="marketplace"
PORTS[8004]="customer"
PORTS[8005]="inventory"
PORTS[8006]="transport"
PORTS[8007]="payment"
PORTS[8008]="warehouse"
PORTS[8009]="document"
PORTS[8010]="fraud"
PORTS[8011]="risk"
PORTS[8012]="knowledge"
PORTS[8020]="aftersales"
PORTS[8021]="backoffice"
PORTS[8022]="quality"

stopped=0

for port in "${!PORTS[@]}"; do
    agent=${PORTS[$port]}
    
    # Find process listening on this port
    pid=$(lsof -ti:$port 2>/dev/null)
    
    if [ -n "$pid" ]; then
        echo "Stopping $agent (port $port, PID $pid)..."
        kill $pid 2>/dev/null
        stopped=$((stopped + 1))
    fi
done

echo ""
echo "================================================================================"
echo "Stopped $stopped agents"
echo "================================================================================"

# Also kill any remaining Python agent processes
pkill -f "python.*agent.*\.py" 2>/dev/null

echo ""
echo "All agents stopped."
echo ""

