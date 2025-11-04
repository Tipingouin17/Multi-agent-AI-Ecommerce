#!/bin/bash

# Test All Admin Page APIs
# This script tests all API endpoints used by the 28 admin pages

BASE_URL="http://localhost:8100"

echo "=========================================="
echo "Testing Admin Dashboard APIs"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0.32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

test_endpoint() {
    local name=$1
    local url=$2
    local method=${3:-GET}
    
    echo -n "Testing $name... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ OK${NC} ($http_code)"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} ($http_code)"
        echo "  Response: $(echo $body | head -c 100)"
        return 1
    fi
}

echo "=== Core System APIs ==="
test_endpoint "System Overview" "$BASE_URL/api/system/overview"
test_endpoint "System Health" "$BASE_URL/health"
test_endpoint "System Config" "$BASE_URL/api/system/config"
test_endpoint "System Metrics" "$BASE_URL/api/system/metrics"
echo ""

echo "=== Agent Management ==="
test_endpoint "List All Agents" "$BASE_URL/api/agents"
test_endpoint "Agent Statistics" "$BASE_URL/api/agents/stats"
echo ""

echo "=== Alert Management ==="
test_endpoint "List Alerts" "$BASE_URL/api/alerts"
test_endpoint "Alert Statistics" "$BASE_URL/api/alerts/stats"
echo ""

echo "=== Analytics ==="
test_endpoint "Agent Analytics" "$BASE_URL/api/analytics/agents"
test_endpoint "Customer Analytics" "$BASE_URL/api/analytics/customers"
test_endpoint "Inventory Analytics" "$BASE_URL/api/analytics/inventory"
test_endpoint "Performance Analytics" "$BASE_URL/api/analytics/performance"
test_endpoint "Sales Analytics" "$BASE_URL/api/analytics/sales"
echo ""

echo "=== Orders ==="
test_endpoint "List Orders" "$BASE_URL/api/orders"
test_endpoint "Order Statistics" "$BASE_URL/api/orders/stats"
test_endpoint "Recent Orders" "$BASE_URL/api/orders/recent"
echo ""

echo "=== Products ==="
test_endpoint "List Products" "$BASE_URL/api/products"
test_endpoint "Product Statistics" "$BASE_URL/api/products/stats"
test_endpoint "Product Categories" "$BASE_URL/api/categories"
echo ""

echo "=== Inventory ==="
test_endpoint "List Inventory" "$BASE_URL/api/inventory"
test_endpoint "Low Stock Items" "$BASE_URL/api/inventory/low-stock"
echo ""

echo "=== Customers ==="
test_endpoint "List Customers" "$BASE_URL/api/customers"
echo ""

echo "=== Carriers & Shipping ==="
test_endpoint "List Carriers" "$BASE_URL/api/carriers"
test_endpoint "List Warehouses" "$BASE_URL/api/warehouses"
echo ""

echo "=========================================="
echo "API Testing Complete"
echo "=========================================="
