#!/bin/bash

#
# Multi-Agent E-commerce Platform - Agent Status Checker
#
# This script checks the health status of all 16 agents
#

echo "================================================================================"
echo "Multi-Agent E-commerce Platform - Agent Status Check"
echo "================================================================================"
echo ""

# Define agents and their ports
declare -A AGENTS
AGENTS[monitoring]=8000
AGENTS[order]=8001
AGENTS[product]=8002
AGENTS[marketplace]=8003
AGENTS[customer]=8004
AGENTS[inventory]=8005
AGENTS[transport]=8006
AGENTS[payment]=8007
AGENTS[warehouse]=8008
AGENTS[document]=8009
AGENTS[fraud]=8010
AGENTS[risk]=8011
AGENTS[knowledge]=8012
AGENTS[aftersales]=8020
AGENTS[backoffice]=8021
AGENTS[quality]=8022

# Counters
total=0
healthy=0
unhealthy=0

# Check each agent
for agent in "${!AGENTS[@]}"; do
    port=${AGENTS[$agent]}
    total=$((total + 1))
    
    # Try to connect to health endpoint
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        echo "✅ $agent (port $port): HEALTHY"
        healthy=$((healthy + 1))
    else
        echo "❌ $agent (port $port): OFFLINE"
        unhealthy=$((unhealthy + 1))
    fi
done

echo ""
echo "================================================================================"
echo "Summary:"
echo "  Total Agents: $total"
echo "  Healthy: $healthy"
echo "  Offline: $unhealthy"
echo "  Health Rate: $(awk "BEGIN {printf \"%.1f\", ($healthy/$total)*100}")%"
echo "================================================================================"

# Exit with error if any agent is down
if [ $unhealthy -gt 0 ]; then
    exit 1
else
    exit 0
fi

