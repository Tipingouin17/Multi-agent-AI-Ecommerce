# Database Update Instructions

## Overview

This guide will help you update your database to support the new 8-step product wizard.

---

## What Will Be Added

### Products Table (35+ new fields)
- **Basic Information:** display_name, brand, model_number, product_type, key_features
- **Specifications:** dimensions (length/width/height), weight, material, color, warranty
- **Pricing:** currency, profit_margin
- **Publishing:** is_draft, published_at, scheduled_publish_at
- **Logistics:** shipping dimensions, handling_time_days, requires_shipping
- **Flags:** is_fragile, is_perishable, has_age_restriction, is_hazmat
- **Compliance:** export_restriction_countries, safety_warnings

### New Tables (10 tables)
1. **product_specifications** - Custom product specs (Step 2)
2. **product_media** - Images, videos, 360° views (Step 3)
3. **product_pricing_tiers** - Bulk pricing (Step 4)
4. **product_tax_config** - Tax configuration (Step 4)
5. **product_warehouse_inventory** - Multi-warehouse stock (Step 5)
6. **product_bundles** - Bundle configuration (Step 6)
7. **bundle_components** - Bundle items (Step 6)
8. **product_marketplace_listings** - Marketplace integration (Step 7)
9. **product_identifiers** - GTIN, UPC, EAN, ISBN, ASIN (Step 7)
10. **product_compliance** - Certifications (Step 7)
11. **product_lifecycle_events** - Audit trail (Step 8)

### Triggers (2 triggers)
1. **Auto-calculate profit margin** - When cost or price changes
2. **Log lifecycle events** - When product status changes

### Views (2 views)
1. **vw_products_complete** - Products with all related data
2. **vw_products_low_stock** - Products below reorder point

### Indexes (20+ indexes)
- Performance indexes on all foreign keys
- Search indexes on brand, model_number, display_name
- Filter indexes on is_draft, product_type

---

## Prerequisites

Before running the migration:

1. ✅ **Backup your database**
   ```bash
   pg_dump -U postgres -d ecommerce > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. ✅ **Ensure PostgreSQL is running**
   ```bash
   sudo systemctl status postgresql
   # or
   pg_isready
   ```

3. ✅ **Have database credentials ready**
   - Host (usually `localhost`)
   - Port (usually `5432`)
   - Database name (usually `ecommerce`)
   - Username (usually `postgres`)
   - Password

---

## Method 1: Using the Update Script (Recommended)

### Step 1: Set Environment Variables

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=ecommerce
export DB_USER=postgres
export DB_PASSWORD=your_password_here
```

### Step 2: Run the Script

```bash
cd /path/to/Multi-agent-AI-Ecommerce
./UPDATE_DATABASE.sh
```

### Step 3: Verify Success

You should see:
```
✅ Migration completed successfully!
```

---

## Method 2: Manual Execution

### Step 1: Navigate to Project Directory

```bash
cd /path/to/Multi-agent-AI-Ecommerce
```

### Step 2: Run Migration File

```bash
psql -h localhost -p 5432 -U postgres -d ecommerce -f database/migrations/024_product_wizard_fields_corrected.sql
```

Enter your password when prompted.

### Step 3: Check for Errors

If successful, you'll see:
```
ALTER TABLE
CREATE TABLE
CREATE INDEX
CREATE TRIGGER
CREATE VIEW
...
```

If you see errors, check:
- Database credentials are correct
- Database is running
- You have sufficient permissions
- Migration file exists

---

## Method 3: Using pgAdmin or DBeaver

### Step 1: Open Database Tool

Open pgAdmin or DBeaver and connect to your database.

### Step 2: Open SQL Editor

Create a new SQL query window.

### Step 3: Copy Migration SQL

Open `database/migrations/024_product_wizard_fields_corrected.sql` and copy the entire content.

### Step 4: Execute

Paste the SQL into the query window and execute.

### Step 5: Verify

Check that all tables, indexes, triggers, and views were created.

---

## Verification

After running the migration, verify it worked:

### Check New Columns

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'products' 
AND column_name IN ('display_name', 'brand', 'model_number', 'product_type');
```

Expected result: 4 rows showing the new columns.

### Check New Tables

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'product_%';
```

Expected result: Multiple tables including product_specifications, product_media, etc.

### Check Triggers

```sql
SELECT trigger_name, event_object_table 
FROM information_schema.triggers 
WHERE trigger_name LIKE '%product%';
```

Expected result: At least 2 triggers (profit margin, lifecycle events).

### Check Views

```sql
SELECT table_name 
FROM information_schema.views 
WHERE table_schema = 'public' 
AND table_name LIKE 'vw_products%';
```

Expected result: 2 views (vw_products_complete, vw_products_low_stock).

---

## Troubleshooting

### Error: "relation 'products' does not exist"

**Cause:** Products table doesn't exist yet.

**Solution:** Run the base schema migrations first:
```bash
psql -h localhost -U postgres -d ecommerce -f database/migrations/001_initial_schema.sql
```

### Error: "column 'display_name' already exists"

**Cause:** Migration was already run.

**Solution:** This is safe to ignore. The migration uses `ADD COLUMN IF NOT EXISTS`.

### Error: "permission denied"

**Cause:** User doesn't have sufficient permissions.

**Solution:** Grant permissions:
```sql
GRANT ALL PRIVILEGES ON DATABASE ecommerce TO your_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
```

### Error: "password authentication failed"

**Cause:** Wrong password or authentication method.

**Solution:** 
1. Check password is correct
2. Check `pg_hba.conf` for authentication settings
3. Try using `trust` authentication temporarily (not for production!)

---

## After Migration

### 1. Restart Backend

The product agent needs to be restarted to recognize the new fields:

```bash
# If using systemd
sudo systemctl restart product-agent

# If running manually
# Stop the current process (Ctrl+C) and restart
cd agents
python product_agent_v3.py
```

### 2. Restart Frontend

```bash
cd multi-agent-dashboard
npm run dev
```

### 3. Test Product Creation

1. Navigate to http://localhost:5173/merchant/products
2. Click "Add Product"
3. Fill in the 8-step wizard
4. Click "Create Product"
5. Verify product appears in list
6. Check database to see all data was saved

### 4. Check Logs

Monitor backend logs for any errors:
```bash
tail -f /path/to/logs/product-agent.log
```

---

## Rollback (If Needed)

If something goes wrong, you can rollback:

### Option 1: Restore from Backup

```bash
psql -U postgres -d ecommerce < backup_YYYYMMDD_HHMMSS.sql
```

### Option 2: Drop New Tables

```sql
DROP TABLE IF EXISTS product_lifecycle_events CASCADE;
DROP TABLE IF EXISTS product_compliance CASCADE;
DROP TABLE IF EXISTS product_identifiers CASCADE;
DROP TABLE IF EXISTS product_marketplace_listings CASCADE;
DROP TABLE IF EXISTS bundle_components CASCADE;
DROP TABLE IF EXISTS product_bundles CASCADE;
DROP TABLE IF EXISTS product_warehouse_inventory CASCADE;
DROP TABLE IF EXISTS product_tax_config CASCADE;
DROP TABLE IF EXISTS product_pricing_tiers CASCADE;
DROP TABLE IF EXISTS product_media CASCADE;
DROP TABLE IF EXISTS product_specifications CASCADE;

-- Drop new columns from products table
ALTER TABLE products 
DROP COLUMN IF EXISTS display_name,
DROP COLUMN IF EXISTS brand,
DROP COLUMN IF EXISTS model_number,
DROP COLUMN IF EXISTS product_type,
DROP COLUMN IF EXISTS key_features,
-- ... (continue for all new columns)
```

---

## Support

If you encounter issues:

1. **Check the error message** - Most errors are self-explanatory
2. **Review prerequisites** - Ensure all requirements are met
3. **Check database logs** - Look for detailed error messages
4. **Verify credentials** - Double-check username, password, database name
5. **Test connection** - Use `psql` to verify you can connect

---

## Summary

**What you need:**
- ✅ Database backup
- ✅ PostgreSQL running
- ✅ Database credentials
- ✅ Migration file (024_product_wizard_fields_corrected.sql)

**What to run:**
```bash
./UPDATE_DATABASE.sh
```

**What you get:**
- ✅ 35+ new product fields
- ✅ 10 new tables
- ✅ 2 triggers
- ✅ 2 views
- ✅ 20+ indexes

**Time required:** 1-2 minutes

**Risk level:** Low (uses IF NOT EXISTS, safe to re-run)

---

**Ready to proceed?** Run the update script and start using the 8-step product wizard! 🚀
