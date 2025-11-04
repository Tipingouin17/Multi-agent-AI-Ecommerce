#!/bin/bash
cd /home/ubuntu/Multi-agent-AI-Ecommerce

echo "Starting critical agents..."

# Start agents in background
python3.11 agents/order_agent_production_v2.py > logs/agents/order_agent.log 2>&1 &
echo "Started order_agent (PID: $!)"
sleep 2

python3.11 agents/product_agent_production.py > logs/agents/product_agent.log 2>&1 &
echo "Started product_agent (PID: $!)"
sleep 2

python3.11 agents/inventory_agent.py > logs/agents/inventory_agent.log 2>&1 &
echo "Started inventory_agent (PID: $!)"
sleep 2

python3.11 agents/auth_agent.py > logs/agents/auth_agent.log 2>&1 &
echo "Started auth_agent (PID: $!)"
sleep 2

python3.11 agents/carrier_selection_agent.py > logs/agents/carrier_agent.log 2>&1 &
echo "Started carrier_agent (PID: $!)"
sleep 2

python3.11 agents/infrastructure_agents.py > logs/agents/infrastructure.log 2>&1 &
echo "Started infrastructure_agent (PID: $!)"

sleep 5
echo ""
echo "Checking running agents..."
ps aux | grep "python3.11 agents/" | grep -v grep | wc -l
