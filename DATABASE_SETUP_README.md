# Database Setup Guide

## Overview

Complete guide to setting up your PostgreSQL database for the Multi-Agent E-commerce Platform.

---

## 📋 Prerequisites

1. **PostgreSQL Installed and Running**
   - PostgreSQL 12 or higher
   - Service must be running

2. **Database Created**
   ```sql
   CREATE DATABASE multi_agent_ecommerce;
   ```

3. **Python Dependencies**
   - SQLAlchemy
   - psycopg2
   - werkzeug

4. **Environment Variables (Optional)**
   - `POSTGRES_HOST` (default: localhost)
   - `POSTGRES_PORT` (default: 5432)
   - `POSTGRES_DB` (default: ecommerce_db)
   - `POSTGRES_USER` (default: postgres)
   - `POSTGRES_PASSWORD` (default: postgres)

---

## 🚀 Quick Start (2 Steps)

### **Step 1: Initialize Database (Create Tables)**

```batch
InitDatabase.bat
```

This creates all 28 required tables in your database.

### **Step 2: Seed Database (Populate Data)**

```batch
SeedDatabase.bat
```

This populates tables with realistic sample data.

---

## 📊 What Tables Are Created

The initialization script creates **28 tables**:

### **Core Tables:**
- `users` - User accounts (admin, merchant, customer)
- `merchants` - Merchant profiles
- `customers` - Customer profiles
- `addresses` - Shipping/billing addresses

### **Product Tables:**
- `categories` - Product categories
- `products` - Product catalog
- `warehouses` - Warehouse locations
- `inventory` - Stock levels by warehouse

### **Order Tables:**
- `orders` - Customer orders
- `order_items` - Line items in orders
- `shipments` - Shipping information
- `carriers` - Shipping carriers

### **Payment Tables:**
- `transactions` - Payment transactions
- `payment_methods` - Payment method configs

### **Supply Chain Tables:**
- `purchase_orders` - Purchase orders
- `purchase_order_items` - PO line items
- `inbound_shipments` - Incoming shipments
- `inbound_shipment_items` - Inbound items
- `receiving_tasks` - Receiving operations
- `receiving_discrepancies` - Receiving issues
- `putaway_tasks` - Warehouse putaway

### **Quality Tables:**
- `quality_inspections` - Quality checks
- `quality_defects` - Defect records

### **Analytics Tables:**
- `alerts` - System alerts
- `returns` - Product returns
- `replenishment_settings` - Reorder settings
- `replenishment_recommendations` - Reorder suggestions
- `demand_forecasts` - Demand predictions

---

## 🔧 Detailed Steps

### **1. Check PostgreSQL is Running**

**Windows:**
```batch
# Check service status
sc query postgresql-x64-14

# Start if not running
net start postgresql-x64-14
```

**Linux/Mac:**
```bash
# Check status
sudo systemctl status postgresql

# Start if not running
sudo systemctl start postgresql
```

### **2. Create Database (If Needed)**

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE multi_agent_ecommerce;

-- Verify
\l

-- Exit
\q
```

### **3. Set Environment Variables (Optional)**

**Windows (PowerShell):**
```powershell
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PORT = "5432"
$env:POSTGRES_DB = "multi_agent_ecommerce"
$env:POSTGRES_USER = "postgres"
$env:POSTGRES_PASSWORD = "your_password"
```

**Windows (Command Prompt):**
```batch
set POSTGRES_HOST=localhost
set POSTGRES_PORT=5432
set POSTGRES_DB=multi_agent_ecommerce
set POSTGRES_USER=postgres
set POSTGRES_PASSWORD=your_password
```

**Linux/Mac:**
```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=multi_agent_ecommerce
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=your_password
```

### **4. Initialize Database**

```batch
InitDatabase.bat
```

**Expected Output:**
```
============================================================
🗄️  DATABASE INITIALIZATION
============================================================

🔗 Connecting to database...
   URL: localhost:5432/multi_agent_ecommerce

✅ Database connection successful!

📋 Creating database tables...

📊 Found 0 existing tables:

📦 Models define 28 tables:
   ➕ will create: addresses
   ➕ will create: alerts
   ➕ will create: carriers
   ... (all 28 tables)

🔨 Creating 28 new tables...
✅ Tables created successfully!

📊 Final database state: 28 tables

============================================================
✅ DATABASE INITIALIZATION COMPLETED!
============================================================

📊 Total tables: 28

🎉 Your database is ready for seeding!
```

### **5. Seed Database**

```batch
SeedDatabase.bat
```

**Expected Output:**
```
============================================================
🌱 DATABASE SEED SCRIPT
============================================================

🗑️  Clearing existing data...
   Cleared 0 records from order_items
   Cleared 0 records from orders
   ... (all tables)
✅ Database cleared

👥 Creating 20 users...
✅ Created 20 users

🏪 Creating merchants...
✅ Created 3 merchants

... (continues for all data types)

============================================================
✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!
============================================================

📊 Summary:
   - Users: 20
   - Merchants: 3
   - Customers: 16
   - Categories: 10
   - Products: 20
   - Warehouses: 3
   - Inventory Records: 60
   - Addresses: 28
   - Carriers: 4
   - Orders: 150
   - Alerts: 12

🎉 Your dashboard should now be populated with data!
```

---

## 🔍 Verification

### **Check Tables Exist:**

```sql
-- Connect to database
psql -U postgres -d multi_agent_ecommerce

-- List all tables
\dt

-- Check record counts
SELECT 'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'merchants', COUNT(*) FROM merchants
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'orders', COUNT(*) FROM orders;

-- Exit
\q
```

### **Expected Counts After Seeding:**
- users: 20
- merchants: 3
- customers: 16
- categories: 10
- products: 20
- warehouses: 3
- inventory: 60+
- addresses: 28
- carriers: 4
- orders: 150

---

## 🐛 Troubleshooting

### **Error: Cannot connect to database**

**Cause:** PostgreSQL not running or wrong credentials

**Solution:**
1. Check PostgreSQL service is running
2. Verify connection settings
3. Test connection: `psql -U postgres -d multi_agent_ecommerce`

### **Error: Database does not exist**

**Cause:** Database not created

**Solution:**
```sql
psql -U postgres
CREATE DATABASE multi_agent_ecommerce;
\q
```

### **Error: Permission denied**

**Cause:** User doesn't have permissions

**Solution:**
```sql
psql -U postgres
GRANT ALL PRIVILEGES ON DATABASE multi_agent_ecommerce TO postgres;
\q
```

### **Error: Table already exists**

**Cause:** Tables already created (not an error!)

**Solution:** This is normal. The script will skip existing tables.

### **Error: Missing required tables**

**Cause:** InitDatabase.bat not run

**Solution:**
1. Run `InitDatabase.bat` first
2. Then run `SeedDatabase.bat`

---

## 🔄 Reset Database

To completely reset and start fresh:

```batch
# 1. Drop and recreate database
psql -U postgres
DROP DATABASE multi_agent_ecommerce;
CREATE DATABASE multi_agent_ecommerce;
\q

# 2. Initialize tables
InitDatabase.bat

# 3. Seed data
SeedDatabase.bat
```

---

## 📝 Manual Approach (Without Scripts)

If you prefer manual setup:

### **Python:**

```python
# Initialize tables
python init_database.py

# Seed data
python seed_database.py
```

### **SQL:**

```sql
-- Connect
psql -U postgres -d multi_agent_ecommerce

-- Run schema file (if you have one)
\i schema.sql

-- Exit
\q
```

---

## 🎯 Next Steps

After successful setup:

1. **Start the platform:**
   ```batch
   StartPlatform.bat
   ```

2. **Open the dashboard:**
   ```
   http://localhost:5173
   ```

3. **Login with:**
   - Admin: admin@ecommerce.com / admin123
   - Merchant: merchant1@example.com / merchant123
   - Customer: customer1@example.com / customer123

4. **Verify data:**
   - Check Merchant Dashboard shows real KPIs
   - Check Recent Orders table is populated
   - Check Inventory Alerts appear
   - Check Marketplace Performance data

---

## 📚 Additional Resources

- **Database Models:** `shared/db_models.py`
- **Connection Config:** `shared/db_connection.py`
- **Init Script:** `init_database.py`
- **Seed Script:** `seed_database.py`

---

## 🆘 Support

If you encounter issues:

1. Check PostgreSQL is running
2. Verify database exists
3. Check connection credentials
4. Review error messages carefully
5. Check logs for details

---

**Happy Coding! 🚀**
