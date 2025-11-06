#!/bin/bash

# Test script for Inbound Management Agent
# Tests all 15 API endpoints

BASE_URL="http://localhost:8032"
echo "======================================"
echo "Inbound Management Agent API Tests"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

test_count=0
pass_count=0

# Function to test endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    test_count=$((test_count + 1))
    echo -n "Test $test_count: $name... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    elif [ "$method" = "PUT" ]; then
        response=$(curl -s -w "\n%{http_code}" -X PUT "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo -e "${GREEN}PASS${NC} (HTTP $http_code)"
        pass_count=$((pass_count + 1))
        
        # Store IDs for later tests
        if echo "$body" | grep -q "shipment_id"; then
            SHIPMENT_ID=$(echo "$body" | python3.11 -c "import sys, json; print(json.load(sys.stdin).get('shipment_id', ''))" 2>/dev/null)
        fi
        if echo "$body" | grep -q "inspection_id"; then
            INSPECTION_ID=$(echo "$body" | python3.11 -c "import sys, json; print(json.load(sys.stdin).get('inspection_id', ''))" 2>/dev/null)
        fi
        if echo "$body" | grep -q "task_id"; then
            TASK_ID=$(echo "$body" | python3.11 -c "import sys, json; print(json.load(sys.stdin).get('task_id', ''))" 2>/dev/null)
        fi
        if echo "$body" | grep -q "shipment_item_id"; then
            ITEM_ID=$(echo "$body" | python3.11 -c "import sys, json; data=json.load(sys.stdin); items=data.get('shipment',{}).get('items',[]); print(items[0]['id'] if items else '')" 2>/dev/null)
        fi
    else
        echo -e "${RED}FAIL${NC} (HTTP $http_code)"
        echo "Response: $body"
    fi
    
    echo ""
}

# Test 1: Health Check
test_endpoint "Health Check" "GET" "/health"

# Test 2: Create Inbound Shipment
shipment_data='{
  "vendor_id": 1,
  "expected_arrival_date": "2025-11-10T10:00:00",
  "carrier": "FedEx",
  "tracking_number": "TRACK123456",
  "warehouse_id": 1,
  "dock_door": "DOCK-A1",
  "notes": "Test shipment",
  "items": [
    {
      "product_id": 1,
      "sku": "SKU001",
      "expected_quantity": 100,
      "unit_cost": 10.50
    },
    {
      "product_id": 2,
      "sku": "SKU002",
      "expected_quantity": 50,
      "unit_cost": 15.75
    }
  ]
}'
test_endpoint "Create Inbound Shipment" "POST" "/api/inbound/shipments" "$shipment_data"

# Test 3: Get All Shipments
test_endpoint "Get All Shipments" "GET" "/api/inbound/shipments?limit=10"

# Test 4: Get Shipment by ID
if [ ! -z "$SHIPMENT_ID" ]; then
    test_endpoint "Get Shipment Details" "GET" "/api/inbound/shipments/$SHIPMENT_ID"
fi

# Test 5: Update Shipment
if [ ! -z "$SHIPMENT_ID" ]; then
    update_data='{"status": "in_transit", "notes": "Shipment in transit"}'
    test_endpoint "Update Shipment Status" "PUT" "/api/inbound/shipments/$SHIPMENT_ID" "$update_data"
fi

# Test 6: Start Receiving
if [ ! -z "$SHIPMENT_ID" ]; then
    test_endpoint "Start Receiving" "POST" "/api/inbound/shipments/$SHIPMENT_ID/receive"
fi

# Test 7: Receive Item
if [ ! -z "$ITEM_ID" ]; then
    receive_data="{
      \"shipment_item_id\": $ITEM_ID,
      \"received_quantity\": 95,
      \"accepted_quantity\": 90,
      \"rejected_quantity\": 5,
      \"notes\": \"5 items damaged\"
    }"
    test_endpoint "Receive Item" "POST" "/api/inbound/receive-item" "$receive_data"
fi

# Test 8: Create Quality Inspection
if [ ! -z "$ITEM_ID" ]; then
    inspection_data="{
      \"shipment_item_id\": $ITEM_ID,
      \"inspection_type\": \"sample\",
      \"sample_size\": 10,
      \"inspector_id\": \"inspector_001\",
      \"notes\": \"Random sample inspection\"
    }"
    test_endpoint "Create Quality Inspection" "POST" "/api/inbound/inspections" "$inspection_data"
fi

# Test 9: Update Quality Inspection
if [ ! -z "$INSPECTION_ID" ]; then
    inspection_update='{
      "passed_count": 8,
      "failed_count": 2,
      "status": "partial",
      "defect_types": ["scratches", "dents"],
      "notes": "Minor defects found"
    }'
    test_endpoint "Update Quality Inspection" "PUT" "/api/inbound/inspections/$INSPECTION_ID" "$inspection_update"
fi

# Test 10: Get Quality Inspections
test_endpoint "Get Quality Inspections" "GET" "/api/inbound/inspections?limit=10"

# Test 11: Create Quality Defect
if [ ! -z "$INSPECTION_ID" ]; then
    defect_data="{
      \"inspection_id\": $INSPECTION_ID,
      \"defect_type\": \"damaged\",
      \"severity\": \"minor\",
      \"quantity\": 2,
      \"description\": \"Minor scratches on surface\",
      \"action_taken\": \"accept_with_discount\"
    }"
    test_endpoint "Create Quality Defect" "POST" "/api/inbound/defects" "$defect_data"
fi

# Test 12: Get Putaway Tasks
test_endpoint "Get Putaway Tasks" "GET" "/api/inbound/putaway-tasks?status=pending&limit=10"

# Test 13: Update Putaway Task
# Get a putaway task ID first
PUTAWAY_TASK_ID=$(curl -s "$BASE_URL/api/inbound/putaway-tasks?limit=1" | python3.11 -c "import sys, json; data=json.load(sys.stdin); tasks=data.get('tasks',[]); print(tasks[0]['id'] if tasks else '')" 2>/dev/null)

if [ ! -z "$PUTAWAY_TASK_ID" ]; then
    putaway_update='{
      "status": "completed",
      "assigned_to": "worker_001",
      "to_location": "SHELF-A-01",
      "notes": "Putaway completed successfully"
    }'
    test_endpoint "Update Putaway Task" "PUT" "/api/inbound/putaway-tasks/$PUTAWAY_TASK_ID" "$putaway_update"
fi

# Test 14: Get Discrepancies
test_endpoint "Get Discrepancies" "GET" "/api/inbound/discrepancies?limit=10"

# Test 15: Resolve Discrepancy
# Get a discrepancy ID first
DISCREPANCY_ID=$(curl -s "$BASE_URL/api/inbound/discrepancies?limit=1" | python3.11 -c "import sys, json; data=json.load(sys.stdin); discs=data.get('discrepancies',[]); print(discs[0]['id'] if discs else '')" 2>/dev/null)

if [ ! -z "$DISCREPANCY_ID" ]; then
    resolve_data='{
      "resolution_status": "resolved",
      "resolution_notes": "Vendor credited for shortage",
      "resolved_by": "manager_001"
    }'
    test_endpoint "Resolve Discrepancy" "PUT" "/api/inbound/discrepancies/$DISCREPANCY_ID/resolve" "$resolve_data"
fi

# Test 16: Get Metrics
test_endpoint "Get Inbound Metrics" "GET" "/api/inbound/metrics?start_date=2025-11-01&end_date=2025-11-30"

# Test 17: Calculate Metrics
test_endpoint "Calculate Metrics" "POST" "/api/inbound/metrics/calculate"

# Summary
echo "======================================"
echo "Test Summary"
echo "======================================"
echo "Total Tests: $test_count"
echo -e "Passed: ${GREEN}$pass_count${NC}"
echo -e "Failed: ${RED}$((test_count - pass_count))${NC}"
echo ""

if [ $pass_count -eq $test_count ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
fi
