-- =====================================================
-- INVENTORY AGENT DATABASE MIGRATION
-- =====================================================
-- This migration creates comprehensive inventory management tables
-- for multi-location inventory tracking, stock movements, replenishment,
-- and warehouse operations.

-- =====================================================
-- 1. WAREHOUSE LOCATIONS
-- =====================================================

CREATE TABLE IF NOT EXISTS warehouse_locations (
    location_id VARCHAR(50) PRIMARY KEY,
    location_name VARCHAR(200) NOT NULL,
    location_type VARCHAR(50) NOT NULL, -- 'warehouse', 'store', 'distribution_center', 'fulfillment_center'
    address JSONB NOT NULL,
    capacity_units INTEGER,
    is_active BOOLEAN DEFAULT true,
    priority_level INTEGER DEFAULT 0,
    operating_hours JSONB,
    contact_info JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_warehouse_locations_type ON warehouse_locations(location_type);
CREATE INDEX IF NOT EXISTS idx_warehouse_locations_active ON warehouse_locations(is_active);

COMMENT ON TABLE warehouse_locations IS 'Warehouse and storage location definitions';

-- =====================================================
-- 2. STOCK LEVELS (Enhanced from Product Agent)
-- =====================================================

CREATE TABLE IF NOT EXISTS stock_levels (
    stock_id SERIAL PRIMARY KEY,
    product_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL REFERENCES warehouse_locations(location_id),
    quantity_on_hand INTEGER NOT NULL DEFAULT 0,
    quantity_reserved INTEGER NOT NULL DEFAULT 0,
    quantity_available INTEGER GENERATED ALWAYS AS (quantity_on_hand - quantity_reserved) STORED,
    quantity_incoming INTEGER DEFAULT 0,
    reorder_point INTEGER DEFAULT 0,
    reorder_quantity INTEGER DEFAULT 0,
    max_stock_level INTEGER,
    min_stock_level INTEGER DEFAULT 0,
    last_counted_at TIMESTAMP,
    last_counted_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, location_id)
);

CREATE INDEX IF NOT EXISTS idx_stock_levels_product ON stock_levels(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_levels_location ON stock_levels(location_id);
CREATE INDEX IF NOT EXISTS idx_stock_levels_available ON stock_levels(quantity_available);
CREATE INDEX IF NOT EXISTS idx_stock_levels_reorder ON stock_levels(quantity_available, reorder_point) WHERE quantity_available <= reorder_point;

COMMENT ON TABLE stock_levels IS 'Real-time stock levels by product and location';

-- =====================================================
-- 3. STOCK MOVEMENTS
-- =====================================================

CREATE TABLE IF NOT EXISTS stock_movements (
    movement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(100) NOT NULL,
    from_location_id VARCHAR(50) REFERENCES warehouse_locations(location_id),
    to_location_id VARCHAR(50) REFERENCES warehouse_locations(location_id),
    movement_type VARCHAR(50) NOT NULL, -- 'transfer', 'adjustment', 'receipt', 'shipment', 'return', 'damage', 'loss'
    quantity INTEGER NOT NULL,
    unit_cost DECIMAL(12, 2),
    total_cost DECIMAL(12, 2),
    reference_id VARCHAR(100),
    reference_type VARCHAR(50), -- 'order', 'purchase_order', 'transfer_order', 'adjustment'
    reason VARCHAR(500),
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'in_transit', 'completed', 'cancelled'
    initiated_by VARCHAR(100),
    completed_by VARCHAR(100),
    completed_at TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_from ON stock_movements(from_location_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_to ON stock_movements(to_location_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_type ON stock_movements(movement_type);
CREATE INDEX IF NOT EXISTS idx_stock_movements_status ON stock_movements(status);
CREATE INDEX IF NOT EXISTS idx_stock_movements_reference ON stock_movements(reference_id, reference_type);
CREATE INDEX IF NOT EXISTS idx_stock_movements_created ON stock_movements(created_at DESC);

COMMENT ON TABLE stock_movements IS 'Complete audit trail of all stock movements';

-- =====================================================
-- 4. REPLENISHMENT ORDERS
-- =====================================================

CREATE TABLE IF NOT EXISTS replenishment_orders (
    replenishment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL REFERENCES warehouse_locations(location_id),
    supplier_id VARCHAR(100),
    quantity_ordered INTEGER NOT NULL,
    quantity_received INTEGER DEFAULT 0,
    unit_cost DECIMAL(12, 2),
    total_cost DECIMAL(12, 2),
    order_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'ordered', 'in_transit', 'received', 'cancelled'
    priority VARCHAR(20) DEFAULT 'normal', -- 'low', 'normal', 'high', 'urgent'
    expected_delivery_date DATE,
    actual_delivery_date DATE,
    purchase_order_number VARCHAR(100),
    notes TEXT,
    created_by VARCHAR(100),
    approved_by VARCHAR(100),
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_replenishment_product ON replenishment_orders(product_id);
CREATE INDEX IF NOT EXISTS idx_replenishment_location ON replenishment_orders(location_id);
CREATE INDEX IF NOT EXISTS idx_replenishment_status ON replenishment_orders(order_status);
CREATE INDEX IF NOT EXISTS idx_replenishment_supplier ON replenishment_orders(supplier_id);
CREATE INDEX IF NOT EXISTS idx_replenishment_expected ON replenishment_orders(expected_delivery_date);

COMMENT ON TABLE replenishment_orders IS 'Purchase orders for stock replenishment';

-- =====================================================
-- 5. STOCK ALERTS
-- =====================================================

CREATE TABLE IF NOT EXISTS stock_alerts (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL REFERENCES warehouse_locations(location_id),
    alert_type VARCHAR(50) NOT NULL, -- 'low_stock', 'out_of_stock', 'overstock', 'expiring_soon', 'damaged'
    severity VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    current_quantity INTEGER,
    threshold_quantity INTEGER,
    message TEXT,
    is_resolved BOOLEAN DEFAULT false,
    resolved_by VARCHAR(100),
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stock_alerts_product ON stock_alerts(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_alerts_location ON stock_alerts(location_id);
CREATE INDEX IF NOT EXISTS idx_stock_alerts_type ON stock_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_stock_alerts_severity ON stock_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_stock_alerts_resolved ON stock_alerts(is_resolved);
CREATE INDEX IF NOT EXISTS idx_stock_alerts_created ON stock_alerts(created_at DESC);

COMMENT ON TABLE stock_alerts IS 'Automated alerts for inventory issues';

-- =====================================================
-- 6. CYCLE COUNTS
-- =====================================================

CREATE TABLE IF NOT EXISTS cycle_counts (
    count_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id VARCHAR(50) NOT NULL REFERENCES warehouse_locations(location_id),
    count_type VARCHAR(50) DEFAULT 'cycle', -- 'cycle', 'full', 'spot', 'blind'
    count_status VARCHAR(50) DEFAULT 'scheduled', -- 'scheduled', 'in_progress', 'completed', 'cancelled'
    scheduled_date DATE NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    assigned_to VARCHAR(100),
    total_items INTEGER DEFAULT 0,
    items_counted INTEGER DEFAULT 0,
    discrepancies_found INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cycle_counts_location ON cycle_counts(location_id);
CREATE INDEX IF NOT EXISTS idx_cycle_counts_status ON cycle_counts(count_status);
CREATE INDEX IF NOT EXISTS idx_cycle_counts_scheduled ON cycle_counts(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_cycle_counts_assigned ON cycle_counts(assigned_to);

COMMENT ON TABLE cycle_counts IS 'Scheduled inventory cycle counts';

-- =====================================================
-- 7. CYCLE COUNT DETAILS
-- =====================================================

CREATE TABLE IF NOT EXISTS cycle_count_details (
    detail_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    count_id UUID NOT NULL REFERENCES cycle_counts(count_id) ON DELETE CASCADE,
    product_id VARCHAR(100) NOT NULL,
    expected_quantity INTEGER NOT NULL,
    counted_quantity INTEGER,
    variance INTEGER GENERATED ALWAYS AS (counted_quantity - expected_quantity) STORED,
    variance_reason VARCHAR(500),
    counted_by VARCHAR(100),
    counted_at TIMESTAMP,
    is_reconciled BOOLEAN DEFAULT false,
    reconciled_by VARCHAR(100),
    reconciled_at TIMESTAMP,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_cycle_count_details_count ON cycle_count_details(count_id);
CREATE INDEX IF NOT EXISTS idx_cycle_count_details_product ON cycle_count_details(product_id);
CREATE INDEX IF NOT EXISTS idx_cycle_count_details_variance ON cycle_count_details(variance) WHERE variance != 0;
CREATE INDEX IF NOT EXISTS idx_cycle_count_details_reconciled ON cycle_count_details(is_reconciled);

COMMENT ON TABLE cycle_count_details IS 'Individual product counts within cycle counts';

-- =====================================================
-- 8. BATCH TRACKING
-- =====================================================

CREATE TABLE IF NOT EXISTS inventory_batches (
    batch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL REFERENCES warehouse_locations(location_id),
    batch_number VARCHAR(100) NOT NULL,
    lot_number VARCHAR(100),
    quantity INTEGER NOT NULL,
    unit_cost DECIMAL(12, 2),
    manufacture_date DATE,
    expiry_date DATE,
    received_date DATE DEFAULT CURRENT_DATE,
    supplier_id VARCHAR(100),
    quality_status VARCHAR(50) DEFAULT 'approved', -- 'pending', 'approved', 'rejected', 'quarantine'
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inventory_batches_product ON inventory_batches(product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_batches_location ON inventory_batches(location_id);
CREATE INDEX IF NOT EXISTS idx_inventory_batches_number ON inventory_batches(batch_number);
CREATE INDEX IF NOT EXISTS idx_inventory_batches_expiry ON inventory_batches(expiry_date);
CREATE INDEX IF NOT EXISTS idx_inventory_batches_status ON inventory_batches(quality_status);
CREATE INDEX IF NOT EXISTS idx_inventory_batches_active ON inventory_batches(is_active);

COMMENT ON TABLE inventory_batches IS 'Batch and lot tracking for inventory';

-- =====================================================
-- 9. STOCK RESERVATIONS (Enhanced)
-- =====================================================

CREATE TABLE IF NOT EXISTS stock_reservations (
    reservation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL REFERENCES warehouse_locations(location_id),
    order_id VARCHAR(100) NOT NULL,
    quantity_reserved INTEGER NOT NULL,
    reservation_status VARCHAR(50) DEFAULT 'active', -- 'active', 'fulfilled', 'cancelled', 'expired'
    reserved_until TIMESTAMP NOT NULL,
    reserved_by VARCHAR(100),
    fulfilled_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    cancellation_reason VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stock_reservations_product ON stock_reservations(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_reservations_location ON stock_reservations(location_id);
CREATE INDEX IF NOT EXISTS idx_stock_reservations_order ON stock_reservations(order_id);
CREATE INDEX IF NOT EXISTS idx_stock_reservations_status ON stock_reservations(reservation_status);
CREATE INDEX IF NOT EXISTS idx_stock_reservations_expiry ON stock_reservations(reserved_until);

COMMENT ON TABLE stock_reservations IS 'Stock reservations for orders';

-- =====================================================
-- 10. INVENTORY VALUATION
-- =====================================================

CREATE TABLE IF NOT EXISTS inventory_valuation (
    valuation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(100) NOT NULL,
    location_id VARCHAR(50) NOT NULL REFERENCES warehouse_locations(location_id),
    valuation_date DATE NOT NULL,
    quantity INTEGER NOT NULL,
    unit_cost DECIMAL(12, 2) NOT NULL,
    total_value DECIMAL(15, 2) NOT NULL,
    valuation_method VARCHAR(50) DEFAULT 'weighted_average', -- 'fifo', 'lifo', 'weighted_average', 'specific_identification'
    calculated_by VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inventory_valuation_product ON inventory_valuation(product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_valuation_location ON inventory_valuation(location_id);
CREATE INDEX IF NOT EXISTS idx_inventory_valuation_date ON inventory_valuation(valuation_date DESC);

COMMENT ON TABLE inventory_valuation IS 'Historical inventory valuation records';

-- =====================================================
-- MATERIALIZED VIEWS
-- =====================================================

-- Inventory Summary View
CREATE MATERIALIZED VIEW IF NOT EXISTS inventory_summary AS
SELECT 
    sl.product_id,
    sl.location_id,
    wl.location_name,
    sl.quantity_on_hand,
    sl.quantity_reserved,
    sl.quantity_available,
    sl.quantity_incoming,
    sl.reorder_point,
    CASE 
        WHEN sl.quantity_available <= 0 THEN 'out_of_stock'
        WHEN sl.quantity_available <= sl.reorder_point THEN 'low_stock'
        WHEN sl.max_stock_level IS NOT NULL AND sl.quantity_on_hand >= sl.max_stock_level THEN 'overstock'
        ELSE 'normal'
    END as stock_status,
    sl.last_counted_at,
    sl.updated_at
FROM stock_levels sl
JOIN warehouse_locations wl ON sl.location_id = wl.location_id
WHERE wl.is_active = true;

CREATE UNIQUE INDEX idx_inventory_summary_product_location ON inventory_summary(product_id, location_id);
CREATE INDEX IF NOT EXISTS idx_inventory_summary_status ON inventory_summary(stock_status);

COMMENT ON MATERIALIZED VIEW inventory_summary IS 'Real-time inventory summary across all locations';

-- Stock Movement Summary View
CREATE MATERIALIZED VIEW IF NOT EXISTS stock_movement_summary AS
SELECT 
    product_id,
    movement_type,
    DATE_TRUNC('day', created_at) as movement_date,
    COUNT(*) as movement_count,
    SUM(quantity) as total_quantity,
    SUM(total_cost) as total_cost
FROM stock_movements
WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY product_id, movement_type, DATE_TRUNC('day', created_at);

CREATE INDEX IF NOT EXISTS idx_stock_movement_summary_product ON stock_movement_summary(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_movement_summary_date ON stock_movement_summary(movement_date DESC);

COMMENT ON MATERIALIZED VIEW stock_movement_summary IS 'Stock movement analytics for last 90 days';

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Update timestamp trigger for stock_levels
CREATE OR REPLACE FUNCTION update_stock_levels_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_stock_levels_timestamp
    BEFORE UPDATE ON stock_levels
    FOR EACH ROW
    EXECUTE FUNCTION update_stock_levels_timestamp();

-- Update timestamp trigger for warehouse_locations
CREATE TRIGGER trigger_update_warehouse_locations_timestamp
    BEFORE UPDATE ON warehouse_locations
    FOR EACH ROW
    EXECUTE FUNCTION update_stock_levels_timestamp();

-- Update timestamp trigger for replenishment_orders
CREATE TRIGGER trigger_update_replenishment_orders_timestamp
    BEFORE UPDATE ON replenishment_orders
    FOR EACH ROW
    EXECUTE FUNCTION update_stock_levels_timestamp();

-- Update timestamp trigger for cycle_counts
CREATE TRIGGER trigger_update_cycle_counts_timestamp
    BEFORE UPDATE ON cycle_counts
    FOR EACH ROW
    EXECUTE FUNCTION update_stock_levels_timestamp();

-- Update timestamp trigger for inventory_batches
CREATE TRIGGER trigger_update_inventory_batches_timestamp
    BEFORE UPDATE ON inventory_batches
    FOR EACH ROW
    EXECUTE FUNCTION update_stock_levels_timestamp();

-- Update timestamp trigger for stock_reservations
CREATE TRIGGER trigger_update_stock_reservations_timestamp
    BEFORE UPDATE ON stock_reservations
    FOR EACH ROW
    EXECUTE FUNCTION update_stock_levels_timestamp();

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to refresh inventory summary
CREATE OR REPLACE FUNCTION refresh_inventory_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY inventory_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY stock_movement_summary;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_inventory_summary() IS 'Refresh inventory materialized views';

-- =====================================================
-- INITIAL DATA
-- =====================================================

-- Insert default warehouse location
INSERT INTO warehouse_locations (location_id, location_name, location_type, address, capacity_units, is_active)
VALUES 
    ('WH001', 'Main Warehouse', 'warehouse', '{"street": "123 Main St", "city": "New York", "state": "NY", "zip": "10001"}', 100000, true),
    ('WH002', 'Distribution Center East', 'distribution_center', '{"street": "456 East Ave", "city": "Boston", "state": "MA", "zip": "02101"}', 50000, true),
    ('WH003', 'Fulfillment Center West', 'fulfillment_center', '{"street": "789 West Blvd", "city": "Los Angeles", "state": "CA", "zip": "90001"}', 75000, true)
ON CONFLICT (location_id) DO NOTHING;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

COMMENT ON SCHEMA public IS 'Inventory Agent migration 004 completed successfully';

