# Testing Guide for New Agents - Inventory & Customer

This guide provides step-by-step instructions for testing the newly implemented Inventory Agent and Customer Agent on your Windows machine with PostgreSQL 18.

---

## Prerequisites

Before testing, ensure you have:

- ✅ PostgreSQL 18 installed and running
- ✅ Python 3.11 installed
- ✅ Git repository cloned and up to date
- ✅ Virtual environment activated
- ✅ All dependencies installed

---

## Step 1: Pull Latest Code

Open PowerShell and navigate to your project directory:

```powershell
cd Multi-agent-AI-Ecommerce
git pull origin main
```

**Expected Output:**
```
Already up to date.
```
or
```
Updating <commit>...<commit>
Fast-forward
 <files changed>
```

---

## Step 2: Run Database Migrations

### Inventory Agent Migration

```powershell
psql -U postgres -d multi_agent_ecommerce -f database/migrations/004_inventory_agent.sql
```

**Expected Output:**
```
CREATE TABLE
CREATE TABLE
...
CREATE INDEX
CREATE MATERIALIZED VIEW
```

**Verify Tables Created:**
```powershell
psql -U postgres -d multi_agent_ecommerce -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'inventory%' OR table_name LIKE 'warehouse%' ORDER BY table_name;"
```

**Expected Tables:**
- inventory_batches
- inventory_cycle_counts
- inventory_replenishment_orders
- inventory_reservations
- inventory_transactions
- inventory_valuation
- product_inventory
- stock_alerts
- stock_movements
- warehouse_locations

### Customer Agent Migration

```powershell
psql -U postgres -d multi_agent_ecommerce -f database/migrations/005_customer_agent.sql
```

**Expected Output:**
```
CREATE TABLE
CREATE TABLE
...
CREATE INDEX
CREATE MATERIALIZED VIEW
```

**Verify Tables Created:**
```powershell
psql -U postgres -d multi_agent_ecommerce -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'customer%' OR table_name LIKE 'loyalty%' OR table_name LIKE 'wishlist%' ORDER BY table_name;"
```

**Expected Tables:**
- customer_addresses
- customer_interactions
- customer_loyalty
- customer_preferences
- customer_profiles
- customer_segment_membership
- customer_segments
- customer_wishlists
- loyalty_transactions
- wishlist_items

---

## Step 3: Verify Database Schema

### Check Total Table Count

```powershell
psql -U postgres -d multi_agent_ecommerce -c "SELECT COUNT(*) as total_tables FROM information_schema.tables WHERE table_schema = 'public';"
```

**Expected Result:** 69 tables (or more)

### Check Materialized Views

```powershell
psql -U postgres -d multi_agent_ecommerce -c "SELECT matviewname FROM pg_matviews WHERE schemaname = 'public' ORDER BY matviewname;"
```

**Expected Views:**
- customer_summary
- inventory_movement_summary
- inventory_summary
- order_fulfillment_summary
- order_summary
- order_timeline_summary
- product_inventory_summary
- product_pricing_summary
- product_rating_summary

### Check Indexes

```powershell
psql -U postgres -d multi_agent_ecommerce -c "SELECT COUNT(*) as total_indexes FROM pg_indexes WHERE schemaname = 'public';"
```

**Expected Result:** 100+ indexes

---

## Step 4: Test Inventory Agent API

### Start Inventory Agent

```powershell
cd agents
python inventory_agent_enhanced.py
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8002
```

### Test API Endpoints

Open a new PowerShell window and test the endpoints:

**1. Health Check:**
```powershell
curl http://localhost:8002/health
```

**Expected Response:**
```json
{"status":"healthy","agent":"inventory_agent_enhanced","version":"1.0.0"}
```

**2. Create Stock Level:**
```powershell
$body = @{
    product_id = "PROD-001"
    location_id = "WH-001"
    quantity_on_hand = 100
    quantity_available = 100
    reorder_point = 20
    reorder_quantity = 50
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8002/api/v1/inventory/stock" -Method Post -Body $body -ContentType "application/json"
```

**Expected Response:**
```json
{
  "stock_id": "<uuid>",
  "product_id": "PROD-001",
  "location_id": "WH-001",
  "quantity_on_hand": 100,
  "quantity_available": 100,
  ...
}
```

**3. Get Stock Level:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8002/api/v1/inventory/stock/PROD-001/WH-001" -Method Get
```

**4. Adjust Stock:**
```powershell
$body = @{
    product_id = "PROD-001"
    location_id = "WH-001"
    quantity_change = -10
    movement_type = "sale"
    reference_id = "ORDER-001"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8002/api/v1/inventory/adjust" -Method Post -Body $body -ContentType "application/json"
```

**5. Check Low Stock:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8002/api/v1/inventory/low-stock" -Method Get
```

**6. Check Availability:**
```powershell
$body = @{
    product_id = "PROD-001"
    location_id = "WH-001"
    quantity_requested = 5
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8002/api/v1/inventory/availability" -Method Post -Body $body -ContentType "application/json"
```

### Stop Inventory Agent

Press `Ctrl+C` in the PowerShell window running the agent.

---

## Step 5: Test Customer Agent API

### Start Customer Agent

```powershell
cd agents
python customer_agent_enhanced.py
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8003
```

### Test API Endpoints

Open a new PowerShell window and test the endpoints:

**1. Health Check:**
```powershell
curl http://localhost:8003/health
```

**Expected Response:**
```json
{"status":"healthy","agent":"customer_agent_enhanced","version":"1.0.0"}
```

**2. Create Customer:**
```powershell
$body = @{
    customer_id = "CUST-001"
    email = "john.doe@example.com"
    phone = "+1234567890"
    first_name = "John"
    last_name = "Doe"
    customer_type = "individual"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8003/api/v1/customers" -Method Post -Body $body -ContentType "application/json"
```

**Expected Response:**
```json
{
  "customer_id": "CUST-001",
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "account_status": "active",
  ...
}
```

**3. Get Customer Details:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8003/api/v1/customers/CUST-001" -Method Get
```

**Expected Response:**
```json
{
  "customer": {...},
  "addresses": [],
  "loyalty": null
}
```

**4. Add Customer Address:**
```powershell
$body = @{
    address_type = "shipping"
    address_label = "Home"
    first_name = "John"
    last_name = "Doe"
    street_address_1 = "123 Main St"
    city = "New York"
    postal_code = "10001"
    country_code = "US"
    is_default = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8003/api/v1/customers/CUST-001/addresses" -Method Post -Body $body -ContentType "application/json"
```

**5. Get Customer Addresses:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8003/api/v1/customers/CUST-001/addresses" -Method Get
```

**6. Create Customer Interaction:**
```powershell
$body = @{
    customer_id = "CUST-001"
    interaction_type = "support_ticket"
    interaction_channel = "web"
    subject = "Product inquiry"
    description = "Question about product availability"
    priority = "medium"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8003/api/v1/customers/CUST-001/interactions" -Method Post -Body $body -ContentType "application/json"
```

### Stop Customer Agent

Press `Ctrl+C` in the PowerShell window running the agent.

---

## Step 6: Verify Data in Database

### Check Inventory Data

```powershell
psql -U postgres -d multi_agent_ecommerce -c "SELECT * FROM product_inventory;"
psql -U postgres -d multi_agent_ecommerce -c "SELECT * FROM stock_movements ORDER BY created_at DESC LIMIT 5;"
psql -U postgres -d multi_agent_ecommerce -c "SELECT * FROM inventory_transactions ORDER BY created_at DESC LIMIT 5;"
```

### Check Customer Data

```powershell
psql -U postgres -d multi_agent_ecommerce -c "SELECT * FROM customer_profiles;"
psql -U postgres -d multi_agent_ecommerce -c "SELECT * FROM customer_addresses;"
psql -U postgres -d multi_agent_ecommerce -c "SELECT * FROM customer_interactions ORDER BY created_at DESC LIMIT 5;"
```

### Refresh Materialized Views

```powershell
psql -U postgres -d multi_agent_ecommerce -c "REFRESH MATERIALIZED VIEW CONCURRENTLY inventory_summary;"
psql -U postgres -d multi_agent_ecommerce -c "REFRESH MATERIALIZED VIEW CONCURRENTLY customer_summary;"
```

### Check Materialized Views

```powershell
psql -U postgres -d multi_agent_ecommerce -c "SELECT * FROM inventory_summary;"
psql -U postgres -d multi_agent_ecommerce -c "SELECT * FROM customer_summary;"
```

---

## Step 7: API Documentation

Both agents provide interactive API documentation via Swagger UI:

**Inventory Agent:**
- Open browser: http://localhost:8002/docs
- Test all endpoints interactively

**Customer Agent:**
- Open browser: http://localhost:8003/docs
- Test all endpoints interactively

---

## Troubleshooting

### Issue: Database Connection Failed

**Error:**
```
asyncpg.exceptions.InvalidCatalogNameError: database "multi_agent_ecommerce" does not exist
```

**Solution:**
```powershell
psql -U postgres -c "CREATE DATABASE multi_agent_ecommerce;"
```

### Issue: Table Already Exists

**Error:**
```
ERROR: relation "product_inventory" already exists
```

**Solution:**
This is expected if you've run the migration before. The migrations use `CREATE TABLE IF NOT EXISTS` so they're idempotent.

### Issue: Port Already in Use

**Error:**
```
ERROR: [Errno 10048] Only one usage of each socket address is normally permitted
```

**Solution:**
Stop any existing agent processes:
```powershell
Get-Process python | Where-Object {$_.Path -like "*inventory*" -or $_.Path -like "*customer*"} | Stop-Process
```

### Issue: Module Not Found

**Error:**
```
ModuleNotFoundError: No module named 'asyncpg'
```

**Solution:**
Install dependencies:
```powershell
pip install -r requirements.txt
```

---

## Success Criteria

✅ **Database Migrations:**
- All 69 tables created successfully
- All 9 materialized views created
- All 100+ indexes created

✅ **Inventory Agent:**
- Health check returns healthy status
- Can create stock levels
- Can adjust stock quantities
- Can check availability
- Can get low stock alerts

✅ **Customer Agent:**
- Health check returns healthy status
- Can create customer profiles
- Can add customer addresses
- Can create customer interactions
- Can retrieve customer details

✅ **Data Integrity:**
- Data persists in database
- Foreign key relationships work
- Materialized views refresh successfully
- Triggers fire correctly

---

## Next Steps

Once testing is complete and all agents are working:

1. ✅ **Confirm Success** - Let me know all tests passed
2. 🔄 **Payment Agent** - I'll implement next
3. 🔄 **Integration Testing** - Test inter-agent communication
4. 🔄 **Shipping Agent** - Implement carrier integrations
5. 🔄 **Notification Agent** - Implement multi-channel notifications

---

## Support

If you encounter any issues during testing:

1. Check the error messages carefully
2. Verify PostgreSQL is running: `Get-Service postgresql*`
3. Check database connection: `psql -U postgres -d multi_agent_ecommerce -c "SELECT version();"`
4. Review agent logs for detailed error information
5. Share error messages with me for assistance

---

**Testing Guide Version:** 1.0  
**Last Updated:** [Current Date]  
**Agents Covered:** Inventory Agent, Customer Agent  
**Database Version:** PostgreSQL 18  
**Python Version:** 3.11

