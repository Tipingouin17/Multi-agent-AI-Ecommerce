#!/bin/bash
echo "=== TESTING ORDER → INVENTORY WORKFLOW ==="

# Get address ID
ADDR_ID=$(PGPASSWORD=postgres psql -U postgres -h localhost -d multi_agent_ecommerce -t -c "SELECT id FROM addresses WHERE user_id=11 LIMIT 1;")
ADDR_ID=$(echo $ADDR_ID | xargs)

# Get customer ID
CUST_ID=$(PGPASSWORD=postgres psql -U postgres -h localhost -d multi_agent_ecommerce -t -c "SELECT id FROM customers WHERE user_id=11 LIMIT 1;")
CUST_ID=$(echo $CUST_ID | xargs)

echo "Using Customer ID: $CUST_ID, Address ID: $ADDR_ID"
echo ""

echo "Step 1: Current Inventory for Product 5"
curl -s "http://localhost:8002/api/inventory?product_id=5" | python3 -m json.tool | grep -A1 quantity | head -4
echo ""

echo "Step 2: Creating order for 3 units"
curl -s -X POST "http://localhost:8000/api/orders" \
  -H "Content-Type: application/json" \
  -d "{
    \"customer_id\": $CUST_ID,
    \"merchant_id\": 3,
    \"items\": [{\"product_id\": 5, \"quantity\": 3, \"unit_price\": 49.99}],
    \"shipping_address_id\": $ADDR_ID,
    \"billing_address_id\": $ADDR_ID
  }" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'order_number' in data:
    print(f\"  ✅ Order created: {data['order_number']}, Total: \${data['total']}\")
else:
    print(f\"  ❌ Error: {data.get('detail', 'Unknown error')}\")
"
echo ""

echo "Step 3: Inventory After Order"
curl -s "http://localhost:8002/api/inventory?product_id=5" | python3 -m json.tool | grep -A1 quantity | head -4
echo ""
echo "=== TEST COMPLETE ==="
