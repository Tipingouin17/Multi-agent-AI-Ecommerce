# Windows Database Update Guide

## Quick Start (3 Steps)

### Step 1: Install psycopg2

Open Command Prompt or PowerShell and run:

```bash
pip install psycopg2-binary
```

If that fails, try:
```bash
pip install psycopg2
```

### Step 2: Run Migration Script

```bash
cd path\to\Multi-agent-AI-Ecommerce
python migrate_database.py
```

### Step 3: Follow Prompts

The script will:
- ✅ Ask for your database credentials (or use environment variables)
- ✅ Test the connection
- ✅ Ask for confirmation
- ✅ Offer to create a backup
- ✅ Run the migration
- ✅ Verify success
- ✅ Show next steps

---

## What You Need

- ✅ Python 3.7+ (you already have this)
- ✅ pip (comes with Python)
- ✅ PostgreSQL database running
- ✅ Database credentials (host, port, database name, username, password)

---

## Environment Variables (Optional)

Instead of entering credentials each time, you can set environment variables:

### Windows Command Prompt:
```cmd
set DB_HOST=localhost
set DB_PORT=5432
set DB_NAME=ecommerce
set DB_USER=postgres
set DB_PASSWORD=your_password
python migrate_database.py
```

### Windows PowerShell:
```powershell
$env:DB_HOST="localhost"
$env:DB_PORT="5432"
$env:DB_NAME="ecommerce"
$env:DB_USER="postgres"
$env:DB_PASSWORD="your_password"
python migrate_database.py
```

---

## Troubleshooting

### Error: "psycopg2 library not found"

**Solution:**
```bash
pip install psycopg2-binary
```

If you get an error about Microsoft Visual C++, use `psycopg2-binary` instead of `psycopg2`.

### Error: "Database connection failed"

**Possible causes:**
1. PostgreSQL is not running
   - Start PostgreSQL service from Windows Services
   - Or start pgAdmin and check if server is running

2. Wrong credentials
   - Double-check username and password
   - Default username is usually `postgres`

3. Wrong host or port
   - Default host: `localhost`
   - Default port: `5432`

4. Database doesn't exist
   - Create the database first in pgAdmin
   - Or use: `createdb -U postgres ecommerce`

### Error: "Migration file not found"

**Solution:** Make sure you're in the project root directory:
```bash
cd path\to\Multi-agent-AI-Ecommerce
python migrate_database.py
```

### Error: "already exists"

**This is usually safe to ignore!** It means the migration was already run before. The script uses `IF NOT EXISTS` clauses to prevent errors on re-runs.

---

## What Gets Added

### Products Table
- 35+ new fields for wizard data
- Fields for: brand, model, dimensions, shipping, compliance, etc.

### New Tables (10 tables)
1. `product_specifications` - Custom product specs
2. `product_media` - Images and videos
3. `product_pricing_tiers` - Bulk pricing
4. `product_tax_config` - Tax settings
5. `product_warehouse_inventory` - Multi-warehouse stock
6. `product_bundles` - Bundle configuration
7. `bundle_components` - Bundle items
8. `product_marketplace_listings` - Marketplace integration
9. `product_identifiers` - GTIN, UPC, EAN, etc.
10. `product_compliance` - Certifications
11. `product_lifecycle_events` - Audit trail

### Triggers & Views
- 2 auto-calculation triggers
- 2 views for easy querying
- 20+ performance indexes

---

## After Migration

### 1. Restart Backend

```bash
cd agents
python product_agent_v3.py
```

### 2. Restart Frontend

```bash
cd multi-agent-dashboard
npm run dev
```

### 3. Test Product Creation

1. Open http://localhost:5173/merchant/products
2. Click "Add Product"
3. Fill in the 8-step wizard
4. Click "Create Product"
5. ✅ Product should be created successfully!

---

## Verification

To verify the migration worked, you can run these SQL queries in pgAdmin:

### Check new columns:
```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'products' 
AND column_name IN ('display_name', 'brand', 'model_number', 'product_type');
```

Expected: 4 rows

### Check new tables:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'product_%'
ORDER BY table_name;
```

Expected: Multiple tables including product_specifications, product_media, etc.

---

## Rollback (If Needed)

If something goes wrong, you can restore from backup:

1. If you created a backup with the script:
   - Open the backup file (backup_schema_*.txt)
   - Use it as reference to manually drop tables/columns

2. If you have a full database backup:
   - Restore using pgAdmin or pg_restore

---

## Need Help?

If you encounter issues:

1. Check the error message (usually self-explanatory)
2. Make sure PostgreSQL is running
3. Verify your credentials
4. Try running in pgAdmin (GUI) instead
5. Share the error message and I'll help!

---

## Summary

**To update your database on Windows:**

```bash
# 1. Install library
pip install psycopg2-binary

# 2. Run migration
python migrate_database.py

# 3. Follow prompts and enter your database password

# 4. Restart backend and frontend

# 5. Test the wizard!
```

**Time required:** 2-3 minutes

**Safe to run:** Yes, uses IF NOT EXISTS clauses

**Can re-run:** Yes, safe to run multiple times

---

**Ready? Run the script and let me know if you need help!** 🚀
