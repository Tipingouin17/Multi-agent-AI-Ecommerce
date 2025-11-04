#!/bin/bash

echo "=========================================="
echo "   COMPREHENSIVE ADMIN API TESTING"
echo "=========================================="
echo ""

BASE_URL="http://localhost:8100"
PASS=0
FAIL=0

test_endpoint() {
    local name="$1"
    local endpoint="$2"
    
    response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    status_code=$(echo "$response" | tail -n1)
    
    if [ "$status_code" = "200" ]; then
        echo "✅ $name"
        ((PASS++))
    else
        echo "❌ $name (HTTP $status_code)"
        ((FAIL++))
    fi
}

echo "Testing System Endpoints..."
test_endpoint "System Overview" "/api/system/overview"
test_endpoint "System Config" "/api/system/config"
test_endpoint "System Metrics" "/api/system/metrics"
test_endpoint "System Health" "/health"

echo ""
echo "Testing Agent Endpoints..."
test_endpoint "List Agents" "/api/agents"
test_endpoint "Agent Stats" "/api/agents/stats"

echo ""
echo "Testing Alert Endpoints..."
test_endpoint "List Alerts" "/api/alerts"
test_endpoint "Alert Stats" "/api/alerts/stats"

echo ""
echo "Testing Order Endpoints..."
test_endpoint "List Orders" "/api/orders?limit=10"
test_endpoint "Order Stats" "/api/orders/stats"
test_endpoint "Recent Orders" "/api/orders/recent"

echo ""
echo "Testing Product Endpoints..."
test_endpoint "List Products" "/api/products?limit=10"
test_endpoint "Product Stats" "/api/products/stats"
test_endpoint "Categories" "/api/categories"

echo ""
echo "Testing Inventory Endpoints..."
test_endpoint "List Inventory" "/api/inventory?limit=10"
test_endpoint "Low Stock" "/api/inventory/low-stock"

echo ""
echo "Testing Customer Endpoints..."
test_endpoint "List Customers" "/api/customers?limit=10"

echo ""
echo "Testing Carrier/Warehouse Endpoints..."
test_endpoint "List Carriers" "/api/carriers"
test_endpoint "List Warehouses" "/api/warehouses"

echo ""
echo "Testing User Management..."
test_endpoint "List Users" "/api/users?limit=10"

echo ""
echo "Testing Analytics..."
test_endpoint "Agent Analytics" "/api/analytics/agents"
test_endpoint "Customer Analytics" "/api/analytics/customers"
test_endpoint "Inventory Analytics" "/api/analytics/inventory"
test_endpoint "Performance Analytics" "/api/analytics/performance"
test_endpoint "Sales Analytics" "/api/analytics/sales"

echo ""
echo "Testing Configuration..."
test_endpoint "Marketplace Integrations" "/api/marketplace/integrations"
test_endpoint "Payment Gateways" "/api/payment/gateways"
test_endpoint "Shipping Zones" "/api/shipping/zones"
test_endpoint "Tax Config" "/api/tax/config"
test_endpoint "Notification Templates" "/api/notifications/templates"
test_endpoint "Document Templates" "/api/documents/templates"
test_endpoint "Workflows" "/api/workflows"

echo ""
echo "Testing Performance Metrics..."
test_endpoint "Performance Metrics" "/metrics/performance?time_range=24h"

echo ""
echo "=========================================="
echo "RESULTS: $PASS passed, $FAIL failed"
echo "Coverage: $(echo "scale=1; $PASS * 100 / ($PASS + $FAIL)" | bc)%"
echo "=========================================="
