-- Market Master Warehouse Enhancements Migration
-- Adds capacity tracking, staff management, utilization metrics, and automation levels

-- Add new columns to warehouses table
ALTER TABLE warehouses ADD COLUMN IF NOT EXISTS total_items INTEGER DEFAULT 0;
ALTER TABLE warehouses ADD COLUMN IF NOT EXISTS unique_skus INTEGER DEFAULT 0;
ALTER TABLE warehouses ADD COLUMN IF NOT EXISTS daily_orders_fulfilled INTEGER DEFAULT 0;
ALTER TABLE warehouses ADD COLUMN IF NOT EXISTS automation_level VARCHAR(50) DEFAULT 'manual';
ALTER TABLE warehouses ADD COLUMN IF NOT EXISTS target_utilization_min INTEGER DEFAULT 70;
ALTER TABLE warehouses ADD COLUMN IF NOT EXISTS target_utilization_max INTEGER DEFAULT 85;

-- Add column comments
COMMENT ON COLUMN warehouses.total_items IS 'Total items stored in warehouse';
COMMENT ON COLUMN warehouses.unique_skus IS 'Number of unique SKUs in warehouse';
COMMENT ON COLUMN warehouses.daily_orders_fulfilled IS 'Orders fulfilled today';
COMMENT ON COLUMN warehouses.automation_level IS 'Automation level: manual, semi-automated, automated';
COMMENT ON COLUMN warehouses.target_utilization_min IS 'Target minimum utilization percentage';
COMMENT ON COLUMN warehouses.target_utilization_max IS 'Target maximum utilization percentage';

-- Update existing warehouses with sample Market Master data
UPDATE warehouses SET 
  total_items = 3404,
  unique_skus = 10,
  daily_orders_fulfilled = 283,
  automation_level = 'automated'
WHERE name = 'Main Distribution Center';

UPDATE warehouses SET 
  total_items = 2916,
  unique_skus = 10,
  daily_orders_fulfilled = 243,
  automation_level = 'automated'
WHERE name = 'West Coast Fulfillment';

UPDATE warehouses SET 
  total_items = 3892,
  unique_skus = 10,
  daily_orders_fulfilled = 323,
  automation_level = 'automated'
WHERE name = 'European Center';

-- Create view for warehouse analytics
CREATE OR REPLACE VIEW vw_warehouse_analytics AS
SELECT 
  w.id,
  w.name,
  w.location,
  w.status,
  w.total_capacity_sqft,
  w.available_capacity_sqft,
  w.total_items,
  w.unique_skus,
  w.current_employees,
  w.max_employees,
  w.daily_orders_fulfilled,
  w.automation_level,
  -- Calculate utilization percentage
  ROUND(((w.total_capacity_sqft - w.available_capacity_sqft)::NUMERIC / w.total_capacity_sqft * 100), 1) as utilization_percentage,
  -- Calculate capacity level
  CASE 
    WHEN ((w.total_capacity_sqft - w.available_capacity_sqft)::NUMERIC / w.total_capacity_sqft * 100) >= 85 THEN 'Low'
    WHEN ((w.total_capacity_sqft - w.available_capacity_sqft)::NUMERIC / w.total_capacity_sqft * 100) >= 60 THEN 'Medium'
    ELSE 'High'
  END as capacity_level,
  -- Calculate workforce percentage
  ROUND((w.current_employees::NUMERIC / w.max_employees * 100), 1) as workforce_percentage,
  w.created_at,
  w.updated_at
FROM warehouses w;

COMMENT ON VIEW vw_warehouse_analytics IS 'Warehouse analytics with calculated metrics';

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_warehouses_automation_level ON warehouses(automation_level);
CREATE INDEX IF NOT EXISTS idx_warehouses_status_active ON warehouses(status) WHERE status = 'active';

-- Success message
DO $$
BEGIN
  RAISE NOTICE '✅ Warehouse enhancements migration completed successfully!';
  RAISE NOTICE '   - Added 6 new columns to warehouses table';
  RAISE NOTICE '   - Updated existing warehouses with sample data';
  RAISE NOTICE '   - Created vw_warehouse_analytics view';
  RAISE NOTICE '   - Created performance indexes';
END $$;
