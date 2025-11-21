-- =====================================================
-- Fix Array Columns to JSON
-- Migration: 025_fix_array_columns_to_json.sql
-- Description: Change TEXT[] columns to JSONB for better compatibility
-- =====================================================

-- Change key_features from TEXT[] to JSONB
ALTER TABLE products 
ALTER COLUMN key_features TYPE JSONB USING 
  CASE 
    WHEN key_features IS NULL THEN NULL
    ELSE to_jsonb(key_features)
  END;

-- Change export_restriction_countries from TEXT[] to JSONB
ALTER TABLE products 
ALTER COLUMN export_restriction_countries TYPE JSONB USING 
  CASE 
    WHEN export_restriction_countries IS NULL THEN NULL
    ELSE to_jsonb(export_restriction_countries)
  END;

-- Change safety_warnings from TEXT[] to JSONB
ALTER TABLE products 
ALTER COLUMN safety_warnings TYPE JSONB USING 
  CASE 
    WHEN safety_warnings IS NULL THEN NULL
    ELSE to_jsonb(safety_warnings)
  END;

-- Update any existing empty string arrays to empty JSON arrays
UPDATE products SET key_features = '[]'::jsonb WHERE key_features IS NULL;
UPDATE products SET export_restriction_countries = '[]'::jsonb WHERE export_restriction_countries IS NULL;
UPDATE products SET safety_warnings = '[]'::jsonb WHERE safety_warnings IS NULL;

-- Add comment
COMMENT ON COLUMN products.key_features IS 'Product key features as JSON array';
COMMENT ON COLUMN products.export_restriction_countries IS 'Export restriction countries as JSON array';
COMMENT ON COLUMN products.safety_warnings IS 'Safety warnings as JSON array';
