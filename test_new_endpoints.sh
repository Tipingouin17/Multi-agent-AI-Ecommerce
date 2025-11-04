#!/bin/bash

echo "=========================================="
echo "TESTING NEW ENDPOINTS"
echo "=========================================="
echo ""

# Test Auth Endpoints
echo "1. Testing Authentication Endpoints (Port 8026)"
echo "-------------------------------------------"

# Test login
echo "  Testing POST /api/auth/login..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8026/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}')

if echo "$LOGIN_RESPONSE" | jq -e '.access_token' > /dev/null 2>&1; then
    echo "  ✅ Login successful"
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
else
    echo "  ❌ Login failed"
    ACCESS_TOKEN=""
fi

# Test /me endpoint
if [ -n "$ACCESS_TOKEN" ]; then
    echo "  Testing GET /api/auth/me..."
    ME_RESPONSE=$(curl -s http://localhost:8026/api/auth/me \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    if echo "$ME_RESPONSE" | jq -e '.email' > /dev/null 2>&1; then
        echo "  ✅ Get current user successful"
    else
        echo "  ❌ Get current user failed"
    fi
fi

echo ""

# Test Carrier Endpoints
echo "2. Testing Carrier Endpoints (Port 8006)"
echo "-------------------------------------------"
echo "  Testing POST /api/carriers/rates..."
RATES_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8006/api/carriers/rates \
  -H "Content-Type: application/json" \
  -d '{"order_id":"test-order","warehouse_id":"wh-001"}' 2>/dev/null)
HTTP_CODE=$(echo "$RATES_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
    echo "  ✅ Carrier rates endpoint accessible"
else
    echo "  ⚠️  Carrier rates endpoint returned HTTP $HTTP_CODE (may need valid data)"
fi

echo ""

# Test Inventory Endpoints
echo "3. Testing Inventory Endpoints (Port 8002)"
echo "-------------------------------------------"
echo "  Testing POST /api/inventory/adjust..."
ADJUST_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8002/api/inventory/adjust \
  -H "Content-Type: application/json" \
  -d '{"product_id":"test-prod","warehouse_id":"wh-001","quantity":10,"movement_type":"inbound"}' 2>/dev/null)
HTTP_CODE=$(echo "$ADJUST_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
    echo "  ✅ Inventory adjust endpoint accessible"
else
    echo "  ⚠️  Inventory adjust endpoint returned HTTP $HTTP_CODE (may need valid data)"
fi

echo ""

# Test System Config Endpoints
echo "4. Testing System Config Endpoints (Port 8022)"
echo "-------------------------------------------"
echo "  Testing GET /api/system/config..."
CONFIG_RESPONSE=$(curl -s http://localhost:8022/api/system/config)

if echo "$CONFIG_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    echo "  ✅ Get system config successful"
else
    echo "  ❌ Get system config failed"
fi

echo ""
echo "=========================================="
echo "ENDPOINT TEST COMPLETE"
echo "=========================================="

