#!/bin/bash
echo "========================================="
echo "AUTHENTICATION TESTING SUITE"
echo "========================================="
echo ""

# Test 1: Admin Login
echo "Test 1: Admin Login"
ADMIN_RESPONSE=$(curl -s -X POST http://localhost:8017/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ecommerce.com","password":"admin123"}')
ADMIN_TOKEN=$(echo $ADMIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', 'FAILED'))")
echo "Admin Token: ${ADMIN_TOKEN:0:50}..."
echo "Status: $([ "$ADMIN_TOKEN" != "FAILED" ] && echo "✅ PASS" || echo "❌ FAIL")"
echo ""

# Test 2: Merchant Login
echo "Test 2: Merchant Login"
MERCHANT_RESPONSE=$(curl -s -X POST http://localhost:8017/login \
  -H "Content-Type: application/json" \
  -d '{"email":"merchant1@example.com","password":"merchant123"}')
MERCHANT_TOKEN=$(echo $MERCHANT_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', 'FAILED'))")
echo "Merchant Token: ${MERCHANT_TOKEN:0:50}..."
echo "Status: $([ "$MERCHANT_TOKEN" != "FAILED" ] && echo "✅ PASS" || echo "❌ FAIL")"
echo ""

# Test 3: Customer Login
echo "Test 3: Customer Login"
CUSTOMER_RESPONSE=$(curl -s -X POST http://localhost:8017/login \
  -H "Content-Type: application/json" \
  -d '{"email":"customer1@example.com","password":"customer123"}')
CUSTOMER_TOKEN=$(echo $CUSTOMER_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', 'FAILED'))")
echo "Customer Token: ${CUSTOMER_TOKEN:0:50}..."
echo "Status: $([ "$CUSTOMER_TOKEN" != "FAILED" ] && echo "✅ PASS" || echo "❌ FAIL")"
echo ""

# Test 4: Invalid Credentials
echo "Test 4: Invalid Credentials (Should Fail)"
INVALID_RESPONSE=$(curl -s -X POST http://localhost:8017/login \
  -H "Content-Type: application/json" \
  -d '{"email":"invalid@example.com","password":"wrongpassword"}')
INVALID_TOKEN=$(echo $INVALID_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', 'FAILED'))")
echo "Status: $([ "$INVALID_TOKEN" == "FAILED" ] && echo "✅ PASS (Correctly rejected)" || echo "❌ FAIL (Should have rejected)")"
echo ""

# Test 5: Token Validation
echo "Test 5: Token Validation with Protected Endpoint"
PROFILE_RESPONSE=$(curl -s -X GET http://localhost:8017/api/auth/me \
  -H "Authorization: Bearer $CUSTOMER_TOKEN")
PROFILE_EMAIL=$(echo $PROFILE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('email', 'FAILED'))")
echo "Profile Email: $PROFILE_EMAIL"
echo "Status: $([ "$PROFILE_EMAIL" == "customer1@example.com" ] && echo "✅ PASS" || echo "❌ FAIL")"
echo ""

echo "========================================="
echo "AUTHENTICATION TESTS COMPLETE"
echo "========================================="
