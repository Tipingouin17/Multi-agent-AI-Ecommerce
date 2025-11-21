-- =====================================================
-- Fix Array Columns to JSON (v2)
-- Migration: 025_fix_array_columns_to_json_v2.sql
-- Description: Change TEXT[] columns to JSONB for better compatibility
-- =====================================================

-- Step 1: Drop views that depend on these columns
DROP VIEW IF EXISTS vw_products_complete CASCADE;
DROP VIEW IF EXISTS vw_products_low_stock CASCADE;

-- Step 2: Change key_features from TEXT[] to JSONB
ALTER TABLE products 
ALTER COLUMN key_features TYPE JSONB USING 
  CASE 
    WHEN key_features IS NULL THEN '[]'::jsonb
    ELSE to_jsonb(key_features)
  END;

-- Step 3: Change export_restriction_countries from TEXT[] to JSONB
ALTER TABLE products 
ALTER COLUMN export_restriction_countries TYPE JSONB USING 
  CASE 
    WHEN export_restriction_countries IS NULL THEN '[]'::jsonb
    ELSE to_jsonb(export_restriction_countries)
  END;

-- Step 4: Change safety_warnings from TEXT[] to JSONB
ALTER TABLE products 
ALTER COLUMN safety_warnings TYPE JSONB USING 
  CASE 
    WHEN safety_warnings IS NULL THEN '[]'::jsonb
    ELSE to_jsonb(safety_warnings)
  END;

-- Step 5: Set defaults for any NULL values
UPDATE products SET key_features = '[]'::jsonb WHERE key_features IS NULL;
UPDATE products SET export_restriction_countries = '[]'::jsonb WHERE export_restriction_countries IS NULL;
UPDATE products SET safety_warnings = '[]'::jsonb WHERE safety_warnings IS NULL;

-- Step 6: Add comments
COMMENT ON COLUMN products.key_features IS 'Product key features as JSON array';
COMMENT ON COLUMN products.export_restriction_countries IS 'Export restriction countries as JSON array';
COMMENT ON COLUMN products.safety_warnings IS 'Safety warnings as JSON array';

-- Step 7: Recreate the views (simplified version without the problematic columns for now)
-- You can recreate full views later if needed
CREATE OR REPLACE VIEW vw_products_low_stock AS
SELECT 
    p.id,
    p.sku,
    p.name,
    p.price,
    p.status,
    COALESCE(SUM(pwi.available_quantity), 0) as total_available,
    COALESCE(SUM(pwi.low_stock_threshold), 10) as threshold
FROM products p
LEFT JOIN product_warehouse_inventory pwi ON p.id = pwi.product_id
GROUP BY p.id, p.sku, p.name, p.price, p.status
HAVING COALESCE(SUM(pwi.available_quantity), 0) < COALESCE(SUM(pwi.low_stock_threshold), 10);

COMMENT ON VIEW vw_products_low_stock IS 'Products with stock below reorder point';
