#!/bin/bash
echo "========================================="
echo "BACKEND API TESTING SUITE"
echo "========================================="
echo ""

# Test Auth Agent (8017)
echo "=== AUTH AGENT (8017) ==="
echo "Health Check:"
curl -s http://localhost:8017/health | python3 -m json.tool | head -5
echo ""

# Test Order Agent (8000)
echo "=== ORDER AGENT (8000) ==="
echo "Health Check:"
curl -s http://localhost:8000/health | python3 -m json.tool
echo ""
echo "Get Orders:"
curl -s "http://localhost:8000/api/orders?limit=2" | python3 -m json.tool | head -20
echo ""
echo "Get Single Order:"
curl -s "http://localhost:8000/api/orders/1" | python3 -m json.tool | head -30
echo ""

# Test Product Agent (8001)
echo "=== PRODUCT AGENT (8001) ==="
echo "Health Check:"
curl -s http://localhost:8001/health | python3 -m json.tool
echo ""
echo "Get Products:"
curl -s "http://localhost:8001/api/products?limit=2" | python3 -m json.tool | head -30
echo ""

# Test Inventory Agent (8002)
echo "=== INVENTORY AGENT (8002) ==="
echo "Health Check:"
curl -s http://localhost:8002/health | python3 -m json.tool
echo ""
echo "Get Inventory:"
curl -s "http://localhost:8002/api/inventory?limit=2" | python3 -m json.tool | head -20
echo ""

# Test Analytics Agent (8031)
echo "=== ANALYTICS AGENT (8031) ==="
echo "Health Check:"
curl -s http://localhost:8031/health | python3 -m json.tool
echo ""

echo "========================================="
echo "API TESTS COMPLETE"
echo "========================================="
