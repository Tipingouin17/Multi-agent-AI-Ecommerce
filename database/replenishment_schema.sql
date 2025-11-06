-- ============================================================================
-- Inventory Replenishment Schema
-- ============================================================================
-- This schema adds purchase order and replenishment functionality
-- to enable automated inventory replenishment

-- Purchase Orders Table
CREATE TABLE IF NOT EXISTS purchase_orders (
    id SERIAL PRIMARY KEY,
    po_number VARCHAR(50) UNIQUE NOT NULL,
    vendor_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    -- Status: draft, pending_approval, approved, sent, confirmed, shipped, received, cancelled
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expected_delivery_date DATE,
    actual_delivery_date DATE,
    total_amount DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    shipping_cost DECIMAL(10, 2) DEFAULT 0.00,
    tax_amount DECIMAL(10, 2) DEFAULT 0.00,
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Purchase Order Items Table
CREATE TABLE IF NOT EXISTS purchase_order_items (
    id SERIAL PRIMARY KEY,
    po_id INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_cost DECIMAL(10, 2) NOT NULL,
    total_cost DECIMAL(12, 2) NOT NULL,
    received_quantity INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- Status: pending, partial, received, cancelled
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Replenishment Settings Table
CREATE TABLE IF NOT EXISTS replenishment_settings (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) UNIQUE,
    enabled BOOLEAN NOT NULL DEFAULT true,
    reorder_point INTEGER NOT NULL DEFAULT 0,
    safety_stock INTEGER NOT NULL DEFAULT 0,
    economic_order_quantity INTEGER NOT NULL DEFAULT 0,
    lead_time_days INTEGER NOT NULL DEFAULT 7,
    ordering_cost DECIMAL(10, 2) NOT NULL DEFAULT 50.00,
    holding_cost_per_unit DECIMAL(10, 2) NOT NULL DEFAULT 2.00,
    avg_daily_sales DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    max_daily_sales DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    last_calculated_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Replenishment Recommendations Table
CREATE TABLE IF NOT EXISTS replenishment_recommendations (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    current_stock INTEGER NOT NULL,
    reorder_point INTEGER NOT NULL,
    recommended_quantity INTEGER NOT NULL,
    reason VARCHAR(100) NOT NULL,
    -- Reason: below_reorder_point, stockout_risk, demand_spike, seasonal
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    -- Priority: low, medium, high, critical
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- Status: pending, approved, rejected, po_created
    po_id INTEGER REFERENCES purchase_orders(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Demand Forecast Table
CREATE TABLE IF NOT EXISTS demand_forecasts (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    forecast_date DATE NOT NULL,
    forecast_quantity DECIMAL(10, 2) NOT NULL,
    confidence_level DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    -- Confidence: 0.00 to 1.00 (0% to 100%)
    model_version VARCHAR(50) NOT NULL DEFAULT 'v1.0',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, forecast_date)
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_po_vendor ON purchase_orders(vendor_id);
CREATE INDEX IF NOT EXISTS idx_po_status ON purchase_orders(status);
CREATE INDEX IF NOT EXISTS idx_po_order_date ON purchase_orders(order_date);
CREATE INDEX IF NOT EXISTS idx_poi_po ON purchase_order_items(po_id);
CREATE INDEX IF NOT EXISTS idx_poi_product ON purchase_order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_rs_product ON replenishment_settings(product_id);
CREATE INDEX IF NOT EXISTS idx_rr_product ON replenishment_recommendations(product_id);
CREATE INDEX IF NOT EXISTS idx_rr_status ON replenishment_recommendations(status);
CREATE INDEX IF NOT EXISTS idx_df_product ON demand_forecasts(product_id);
CREATE INDEX IF NOT EXISTS idx_df_date ON demand_forecasts(forecast_date);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_po_updated_at BEFORE UPDATE ON purchase_orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_poi_updated_at BEFORE UPDATE ON purchase_order_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rs_updated_at BEFORE UPDATE ON replenishment_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rr_updated_at BEFORE UPDATE ON replenishment_recommendations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
