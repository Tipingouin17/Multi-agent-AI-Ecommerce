#!/bin/bash

# Test All Agents Script
# Tests health endpoints and key functionality of all critical agents

echo "=========================================="
echo "MULTI-AGENT E-COMMERCE PLATFORM TEST"
echo "=========================================="
echo ""

# Define critical agents with their ports
declare -A AGENTS=(
    ["order_agent"]="8000"
    ["product_agent"]="8001"
    ["inventory_agent"]="8002"
    ["marketplace_connector"]="8003"
    ["payment_agent"]="8004"
    ["dynamic_pricing"]="8005"
    ["carrier_selection"]="8006"
    ["customer_agent"]="8007"
    ["customer_communication"]="8008"
    ["returns_agent"]="8009"
    ["fraud_detection"]="8010"
    ["recommendation"]="8014"
    ["transport_management"]="8015"
    ["warehouse"]="8016"
    ["support"]="8018"
    ["infrastructure"]="8022"
    ["auth_agent"]="8026"
)

PASSED=0
FAILED=0
RESULTS_FILE="/tmp/agent_test_results.json"

echo "[" > $RESULTS_FILE

for agent in "${!AGENTS[@]}"; do
    port="${AGENTS[$agent]}"
    echo "Testing $agent on port $port..."
    
    # Test health endpoint
    response=$(curl -s -w "\n%{http_code}" "http://localhost:$port/health" 2>/dev/null)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        echo "  ✅ $agent is healthy"
        PASSED=$((PASSED + 1))
        status="PASS"
    else
        echo "  ❌ $agent is not responding (HTTP $http_code)"
        FAILED=$((FAILED + 1))
        status="FAIL"
    fi
    
    # Write to JSON
    echo "  {" >> $RESULTS_FILE
    echo "    \"agent\": \"$agent\"," >> $RESULTS_FILE
    echo "    \"port\": $port," >> $RESULTS_FILE
    echo "    \"status\": \"$status\"," >> $RESULTS_FILE
    echo "    \"http_code\": \"$http_code\"," >> $RESULTS_FILE
    echo "    \"response\": $(echo "$body" | jq -c '.' 2>/dev/null || echo "null")" >> $RESULTS_FILE
    echo "  }," >> $RESULTS_FILE
done

# Remove trailing comma and close JSON
sed -i '$ s/,$//' $RESULTS_FILE
echo "]" >> $RESULTS_FILE

echo ""
echo "=========================================="
echo "TEST SUMMARY"
echo "=========================================="
echo "Total Agents Tested: $((PASSED + FAILED))"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""
echo "Results saved to: $RESULTS_FILE"

