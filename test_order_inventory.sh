#!/bin/bash
echo "=== TESTING ORDER → INVENTORY WORKFLOW ==="
echo ""

# Step 1: Check current inventory
echo "Step 1: Current Inventory for Product 5"
curl -s "http://localhost:8002/api/inventory?product_id=5" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for inv in data['inventory']:
    print(f\"  Warehouse {inv['warehouse_id']}: {inv['quantity']} units\")
total = sum(inv['quantity'] for inv in data['inventory'])
print(f\"  Total: {total} units\")
"
echo ""

# Step 2: Create an order for 5 units
echo "Step 2: Creating order for 5 units of Product 5"
ORDER_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "merchant_id": 3,
    "items": [{"product_id": 5, "quantity": 5, "unit_price": 49.99}],
    "shipping_address_id": 1,
    "billing_address_id": 1
  }')

echo "$ORDER_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'order_number' in data:
        print(f\"  ✅ Order created: {data['order_number']}\")
        print(f\"  Total: \${data['total']}\")
    elif 'detail' in data:
        print(f\"  ❌ Error: {data['detail']}\")
except:
    print('  ❌ Failed to parse response')
"
echo ""

# Step 3: Check inventory after order
echo "Step 3: Inventory After Order"
curl -s "http://localhost:8002/api/inventory?product_id=5" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for inv in data['inventory']:
    print(f\"  Warehouse {inv['warehouse_id']}: {inv['quantity']} units (Reserved: {inv.get('reserved_quantity', 0)})\")
total = sum(inv['quantity'] for inv in data['inventory'])
print(f\"  Total: {total} units\")
"
echo ""
echo "=== TEST COMPLETE ==="
