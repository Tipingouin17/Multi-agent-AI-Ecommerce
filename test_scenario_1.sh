#!/bin/bash
echo "=== SCENARIO 1: ORDER CREATION AND PROCESSING ==="
echo ""

# Step 1: Customer browses products
echo "Step 1: Customer browses products"
PRODUCTS=$(curl -s "http://localhost:8001/api/products?limit=3")
echo "$PRODUCTS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"  ✅ Found {len(data.get('products', []))} products\")
for p in data.get('products', [])[:2]:
    print(f\"    - {p['name']}: \${p['price']}\")
"
echo ""

# Step 2: Check inventory availability
echo "Step 2: Check inventory for Product 5"
INV=$(curl -s "http://localhost:8002/api/inventory?product_id=5")
echo "$INV" | python3 -c "
import sys, json
data = json.load(sys.stdin)
total = sum(inv['available_quantity'] for inv in data['inventory'])
print(f\"  ✅ Available: {total} units\")
"
echo ""

# Step 3: Create order
echo "Step 3: Create order (triggers inventory deduction)"
ORDER=$(curl -s -X POST "http://localhost:8000/api/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "merchant_id": 3,
    "items": [{"product_id": 5, "quantity": 2, "unit_price": 49.99}],
    "shipping_address_id": 2,
    "billing_address_id": 2
  }')
echo "$ORDER" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'order_number' in data:
    print(f\"  ✅ Order created: {data['order_number']}\")
    print(f\"     Total: \${data['total']}\")
else:
    print(f\"  ❌ Error: {data.get('detail', 'Unknown')}\")
"
echo ""

# Step 4: Verify inventory was deducted
echo "Step 4: Verify inventory deduction"
INV2=$(curl -s "http://localhost:8002/api/inventory?product_id=5")
echo "$INV2" | python3 -c "
import sys, json
data = json.load(sys.stdin)
total = sum(inv['available_quantity'] for inv in data['inventory'])
reserved = sum(inv['reserved_quantity'] for inv in data['inventory'])
print(f\"  ✅ Available: {total} units (Reserved: {reserved})\")
"
echo ""
echo "=== SCENARIO 1 COMPLETE ===" 
