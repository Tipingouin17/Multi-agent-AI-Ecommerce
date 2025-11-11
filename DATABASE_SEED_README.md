# Database Seed Script

## Overview

This script populates your PostgreSQL database with realistic sample data for testing the Multi-Agent E-commerce Platform.

## What Data is Created

### **Users & Authentication**
- ✅ 1 Admin user
- ✅ 3 Merchant users  
- ✅ 16 Customer users
- ✅ All with hashed passwords

### **Merchants**
- ✅ 3 Merchant profiles
- ✅ Different business types (Electronics, Fashion, Home & Garden)
- ✅ Realistic ratings and commission rates

### **Products & Categories**
- ✅ 10 Product categories (with parent-child relationships)
- ✅ 20 Products across different categories
- ✅ Realistic prices, costs, and stock quantities
- ✅ SKUs, descriptions, ratings

### **Warehouses & Inventory**
- ✅ 3 Warehouses (New York, Los Angeles, Chicago)
- ✅ Inventory records for products across warehouses
- ✅ Stock levels, reorder points, warehouse locations

### **Customers & Addresses**
- ✅ 16 Customer profiles
- ✅ 20-30 Addresses (shipping/billing)
- ✅ Realistic US addresses

### **Orders**
- ✅ 150 Orders spanning last 90 days
- ✅ Multiple items per order
- ✅ Various statuses (pending, confirmed, processing, shipped, delivered, cancelled)
- ✅ Realistic order progression based on age
- ✅ Calculated totals (subtotal, tax, shipping, total)

### **Carriers**
- ✅ 4 Shipping carriers (FedEx, UPS, USPS, DHL)
- ✅ Contact information and ratings

### **Alerts**
- ✅ Low stock alerts for items below reorder point
- ✅ Critical and high severity levels

---

## How to Use

### **Windows:**

```batch
# Simply double-click or run:
SeedDatabase.bat
```

### **Linux/Mac:**

```bash
python3 seed_database.py
```

---

## Prerequisites

1. **PostgreSQL Running**
   - Database must be running and accessible
   - Connection settings in environment variables or defaults

2. **Python Dependencies**
   - SQLAlchemy
   - psycopg2
   - werkzeug (for password hashing)

3. **Database Schema**
   - Tables must already exist (run migrations first if needed)

---

## What Happens

1. **Clears existing data** (⚠️ WARNING: This deletes all current data!)
2. **Creates data in order:**
   - Users → Merchants → Categories → Products
   - Warehouses → Inventory
   - Customers → Addresses
   - Carriers → Orders → Alerts
3. **Updates aggregated totals** (merchant sales, customer spending)
4. **Prints summary** of created records

---

## Login Credentials

After seeding, you can log in with:

| Role | Email | Password |
|------|-------|----------|
| **Admin** | admin@ecommerce.com | admin123 |
| **Merchant** | merchant1@example.com | merchant123 |
| **Merchant** | merchant2@example.com | merchant123 |
| **Merchant** | merchant3@example.com | merchant123 |
| **Customer** | customer1@example.com | customer123 |
| **Customer** | customer2@example.com | customer123 |
| ... | ... | ... |

---

## Expected Output

```
============================================================
🌱 DATABASE SEED SCRIPT
============================================================

🗑️  Clearing existing data...
✅ Database cleared
👥 Creating 20 users...
✅ Created 20 users
🏪 Creating merchants...
✅ Created 3 merchants
📁 Creating categories...
✅ Created 10 categories
📦 Creating products...
✅ Created 20 products
🏭 Creating warehouses...
✅ Created 3 warehouses
📊 Creating inventory records...
✅ Created 60 inventory records
👤 Creating customers...
✅ Created 16 customers
🏠 Creating addresses...
✅ Created 28 addresses
🚚 Creating carriers...
✅ Created 4 carriers
🛒 Creating orders...
✅ Created 150 orders with 375 items
⚠️  Creating alerts...
✅ Created 12 alerts
💰 Updating merchant totals...
✅ Updated merchant totals
💳 Updating customer totals...
✅ Updated customer totals

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

## After Seeding

1. **Restart the platform:**
   ```batch
   StopAllAgents.bat
   StartPlatform.bat
   ```

2. **Open the dashboard:**
   ```
   http://localhost:5173
   ```

3. **Check the Merchant Portal Dashboard:**
   - Should show real KPIs (sales, orders, AOV)
   - Recent orders table populated
   - Inventory alerts visible
   - Marketplace performance data

---

## Customization

You can modify the script to:

- **Change quantities:** Edit `num_orders = 150` to create more/fewer orders
- **Add more products:** Extend `PRODUCTS_DATA` array
- **Change date ranges:** Modify `days_ago = random.randint(0, 90)` for different time spans
- **Add more merchants:** Change `range(1, 4)` to create more merchant users

---

## Troubleshooting

### **Error: Database connection failed**
- Check PostgreSQL is running
- Verify connection settings in environment variables
- Check `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`

### **Error: Table does not exist**
- Run database migrations first to create tables
- Check that all models are defined in `shared/db_models.py`

### **Error: Column does not exist**
- Database schema may not match models
- Check for schema mismatches (like the `order_number` issue we fixed)

### **Script runs but no data appears**
- Check for errors in the output
- Verify database connection
- Check that agents are using the same database

---

## Safety

⚠️ **WARNING:** This script **deletes all existing data** before seeding!

- Only run on development/test databases
- **NEVER run on production databases**
- Back up your data before running if needed

---

## Next Steps

After seeding:

1. ✅ Test Merchant Portal Dashboard
2. ✅ Test Admin Portal
3. ✅ Test Customer Portal
4. ✅ Verify all agents can query data
5. ✅ Check analytics endpoints

---

## Support

If you encounter issues:

1. Check the error messages in console
2. Verify database connection
3. Check that all dependencies are installed
4. Review the script output for clues

---

**Happy Testing! 🎉**
