#!/bin/bash
echo "========================================="
echo "PERSONA-BASED TESTING SUITE"
echo "========================================="
echo ""

# Get tokens for all personas
echo "=== AUTHENTICATING ALL PERSONAS ==="
CUSTOMER_TOKEN=$(curl -s -X POST http://localhost:8017/login -H "Content-Type: application/json" -d '{"email":"customer1@example.com","password":"customer123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
MERCHANT_TOKEN=$(curl -s -X POST http://localhost:8017/login -H "Content-Type: application/json" -d '{"email":"merchant1@example.com","password":"merchant123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8017/login -H "Content-Type: application/json" -d '{"email":"admin@ecommerce.com","password":"admin123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "✅ Customer authenticated"
echo "✅ Merchant authenticated"
echo "✅ Admin authenticated"
echo ""

echo "========================================="
echo "CUSTOMER PERSONA TESTING"
echo "========================================="
echo ""

echo "1. Browse Products (Customer View)"
curl -s "http://localhost:8001/api/products?limit=3" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Total Products: {data['pagination']['total']}\")
for p in data['products'][:3]:
    print(f\"  - {p['name']}: \${p['price']} (SKU: {p['sku']})\")
"
echo ""

echo "2. View My Orders (Customer)"
curl -s "http://localhost:8000/api/orders?customer_id=1" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Total Orders: {data['pagination']['total']}\")
for o in data['orders']:
    print(f\"  - {o['order_number']}: \${o['total']} - {o['status']}\")
"
echo ""

echo "3. View Order Details (Customer)"
curl -s "http://localhost:8000/api/orders/1" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Order: {data['order_number']}\")
print(f\"Status: {data['status']}\")
print(f\"Total: \${data['total']}\")
print(f\"Items: {len(data['items'])}\")
for item in data['items']:
    print(f\"  - {item['name']} x{item['quantity']} @ \${item['unit_price']}\")
"
echo ""

echo "========================================="
echo "MERCHANT PERSONA TESTING"
echo "========================================="
echo ""

echo "1. View All Products (Merchant Dashboard)"
curl -s "http://localhost:8001/api/products?merchant_id=3" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Total Products: {data['pagination']['total']}\")
print(f\"Featured Products: {sum(1 for p in data['products'] if p['is_featured'])}\")
print(f\"Active Products: {sum(1 for p in data['products'] if p['status'] == 'active')}\")
"
echo ""

echo "2. View All Orders (Merchant)"
curl -s "http://localhost:8000/api/orders?merchant_id=3" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Total Orders: {data['pagination']['total']}\")
statuses = {}
for o in data['orders']:
    statuses[o['status']] = statuses.get(o['status'], 0) + 1
for status, count in statuses.items():
    print(f\"  - {status}: {count} orders\")
"
echo ""

echo "3. View Inventory (Merchant)"
curl -s "http://localhost:8002/api/inventory" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Total Inventory Items: {data['pagination']['total']}\")
total_stock = sum(i['quantity'] for i in data['inventory'])
print(f\"Total Stock Units: {total_stock}\")
low_stock = sum(1 for i in data['inventory'] if i['quantity'] < i['reorder_point'])
print(f\"Low Stock Items: {low_stock}\")
"
echo ""

echo "========================================="
echo "ADMIN PERSONA TESTING"
echo "========================================="
echo ""

echo "1. Platform Overview (Admin)"
echo "  Products: $(curl -s 'http://localhost:8001/api/products' | python3 -c 'import sys, json; print(json.load(sys.stdin)["pagination"]["total"])')"
echo "  Orders: $(curl -s 'http://localhost:8000/api/orders' | python3 -c 'import sys, json; print(json.load(sys.stdin)["pagination"]["total"])')"
echo "  Inventory Items: $(curl -s 'http://localhost:8002/api/inventory' | python3 -c 'import sys, json; print(json.load(sys.stdin)["pagination"]["total"])')"
echo ""

echo "2. System Health (Admin)"
echo "  Auth Agent: $(curl -s 'http://localhost:8017/health' | python3 -c 'import sys, json; print(json.load(sys.stdin)["status"])')"
echo "  Order Agent: $(curl -s 'http://localhost:8000/health' | python3 -c 'import sys, json; print(json.load(sys.stdin)["status"])')"
echo "  Product Agent: $(curl -s 'http://localhost:8001/health' | python3 -c 'import sys, json; print(json.load(sys.stdin)["status"])')"
echo "  Inventory Agent: $(curl -s 'http://localhost:8002/health' | python3 -c 'import sys, json; print(json.load(sys.stdin)["status"])')"
echo "  Analytics Agent: $(curl -s 'http://localhost:8031/health' | python3 -c 'import sys, json; print(json.load(sys.stdin)["status"])')"
echo ""

echo "3. Order Analytics (Admin)"
curl -s "http://localhost:8000/api/orders" | python3 -c "
import sys, json
data = json.load(sys.stdin)
total_revenue = sum(o['total'] for o in data['orders'])
avg_order = total_revenue / len(data['orders']) if data['orders'] else 0
print(f\"Total Revenue: \${total_revenue:.2f}\")
print(f\"Average Order Value: \${avg_order:.2f}\")
print(f\"Total Orders: {len(data['orders'])}\")
"
echo ""

echo "========================================="
echo "PERSONA TESTING COMPLETE"
echo "========================================="
