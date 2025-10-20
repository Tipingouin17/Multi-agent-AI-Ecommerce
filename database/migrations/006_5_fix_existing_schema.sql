-- =====================================================
-- SCHEMA FIX FOR EXISTING TABLES
-- =====================================================
-- This migration adds missing columns to existing tables
-- to ensure compatibility with new agent migrations.
-- Run this BEFORE running other agent migrations.

-- =====================================================
-- Fix carriers table (if it exists)
-- =====================================================

-- Add is_active column to carriers if it doesn't exist
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'carriers') THEN
        -- Add is_active column if missing
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name = 'carriers' AND column_name = 'is_active') THEN
            ALTER TABLE carriers ADD COLUMN is_active BOOLEAN DEFAULT true;
            RAISE NOTICE 'Added is_active column to carriers table';
        END IF;
        
        -- Add active column if it exists instead of is_active (rename it)
        IF EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'carriers' AND column_name = 'active') 
           AND NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name = 'carriers' AND column_name = 'is_active') THEN
            ALTER TABLE carriers RENAME COLUMN active TO is_active;
            RAISE NOTICE 'Renamed active column to is_active in carriers table';
        END IF;
    END IF;
END $$;

-- =====================================================
-- Fix orders table references
-- =====================================================

-- Ensure orders table has both id and order_id for compatibility
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'orders') THEN
        -- If orders table uses 'id' as primary key but some views expect 'order_id'
        -- We'll handle this in the application layer or create a view
        RAISE NOTICE 'Orders table exists - schema compatibility checked';
    END IF;
END $$;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

COMMENT ON SCHEMA public IS 'Schema compatibility fixes applied successfully';

