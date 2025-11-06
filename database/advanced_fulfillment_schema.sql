-- Advanced Fulfillment Schema
-- Handles intelligent order fulfillment, warehouse selection, and inventory allocation

-- Fulfillment Rules
CREATE TABLE IF NOT EXISTS fulfillment_rules (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- warehouse_selection, split_logic, allocation_priority
    priority INTEGER DEFAULT 0,
    conditions JSONB, -- Flexible rule conditions
    actions JSONB, -- Actions to take when rule matches
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Inventory Reservations
CREATE TABLE IF NOT EXISTS inventory_reservations (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    sku VARCHAR(100) NOT NULL,
    warehouse_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    reservation_type VARCHAR(50) DEFAULT 'soft', -- soft (unpaid), hard (paid), backorder
    status VARCHAR(50) DEFAULT 'active', -- active, released, expired, fulfilled
    expires_at TIMESTAMP,
    reserved_by VARCHAR(100), -- customer_id or system
    created_at TIMESTAMP DEFAULT NOW(),
    released_at TIMESTAMP,
    notes TEXT
);

-- Order Splits
CREATE TABLE IF NOT EXISTS order_splits (
    id SERIAL PRIMARY KEY,
    parent_order_id INTEGER NOT NULL,
    child_order_id INTEGER NOT NULL,
    split_reason VARCHAR(100), -- inventory_unavailable, cost_optimization, time_optimization
    warehouse_id INTEGER,
    split_number INTEGER, -- 1, 2, 3 for multi-way splits
    total_splits INTEGER, -- Total number of splits for this parent order
    items_count INTEGER,
    estimated_ship_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, shipped, delivered
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Backorders
CREATE TABLE IF NOT EXISTS backorders (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    order_item_id INTEGER,
    product_id INTEGER NOT NULL,
    sku VARCHAR(100) NOT NULL,
    customer_id INTEGER NOT NULL,
    quantity_backordered INTEGER NOT NULL,
    quantity_fulfilled INTEGER DEFAULT 0,
    priority_score INTEGER DEFAULT 0, -- Calculated based on customer tier, order value, wait time
    status VARCHAR(50) DEFAULT 'pending', -- pending, partially_fulfilled, fulfilled, cancelled
    estimated_fulfillment_date TIMESTAMP,
    customer_notified BOOLEAN DEFAULT false,
    notification_sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    fulfilled_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    notes TEXT
);

-- Fulfillment Waves (for batch picking optimization)
CREATE TABLE IF NOT EXISTS fulfillment_waves (
    id SERIAL PRIMARY KEY,
    wave_number VARCHAR(50) UNIQUE NOT NULL,
    warehouse_id INTEGER NOT NULL,
    wave_type VARCHAR(50) DEFAULT 'standard', -- standard, priority, same_day
    status VARCHAR(50) DEFAULT 'pending', -- pending, picking, packing, completed, cancelled
    orders_count INTEGER DEFAULT 0,
    items_count INTEGER DEFAULT 0,
    assigned_to VARCHAR(100), -- picker/packer user ID
    priority INTEGER DEFAULT 0,
    scheduled_start_time TIMESTAMP,
    actual_start_time TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

-- Wave Orders (many-to-many relationship)
CREATE TABLE IF NOT EXISTS wave_orders (
    id SERIAL PRIMARY KEY,
    wave_id INTEGER REFERENCES fulfillment_waves(id) ON DELETE CASCADE,
    order_id INTEGER NOT NULL,
    pick_sequence INTEGER, -- Optimized picking order
    status VARCHAR(50) DEFAULT 'pending',
    picked_at TIMESTAMP,
    packed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Warehouse Capacity Tracking
CREATE TABLE IF NOT EXISTS warehouse_capacity (
    id SERIAL PRIMARY KEY,
    warehouse_id INTEGER NOT NULL,
    date DATE NOT NULL,
    total_capacity INTEGER NOT NULL, -- Max orders per day
    current_load INTEGER DEFAULT 0, -- Current orders assigned
    available_capacity INTEGER, -- Calculated: total - current
    utilization_percentage DECIMAL(5,2), -- Calculated: (current/total) * 100
    status VARCHAR(50) DEFAULT 'normal', -- normal, high, critical, full
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(warehouse_id, date)
);

-- Fulfillment Plans (stores the analysis result for each order)
CREATE TABLE IF NOT EXISTS fulfillment_plans (
    id SERIAL PRIMARY KEY,
    order_id INTEGER UNIQUE NOT NULL,
    fulfillment_strategy VARCHAR(50), -- single_warehouse, split_order, backorder_partial
    primary_warehouse_id INTEGER,
    secondary_warehouse_id INTEGER,
    estimated_ship_date TIMESTAMP,
    estimated_delivery_date TIMESTAMP,
    total_shipping_cost DECIMAL(10,2),
    split_required BOOLEAN DEFAULT false,
    backorder_required BOOLEAN DEFAULT false,
    priority_level VARCHAR(50) DEFAULT 'standard', -- standard, priority, express
    analysis_score DECIMAL(5,2), -- Quality score of the fulfillment plan
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

-- Fulfillment Metrics (daily aggregated metrics)
CREATE TABLE IF NOT EXISTS fulfillment_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    warehouse_id INTEGER,
    orders_fulfilled INTEGER DEFAULT 0,
    orders_split INTEGER DEFAULT 0,
    orders_backordered INTEGER DEFAULT 0,
    average_fulfillment_time_hours DECIMAL(10,2),
    same_day_fulfillment_rate DECIMAL(5,2),
    order_accuracy_rate DECIMAL(5,2),
    average_shipping_cost DECIMAL(10,2),
    warehouse_utilization DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date, warehouse_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_reservations_order ON inventory_reservations(order_id);
CREATE INDEX IF NOT EXISTS idx_reservations_product ON inventory_reservations(product_id, warehouse_id);
CREATE INDEX IF NOT EXISTS idx_reservations_status ON inventory_reservations(status);
CREATE INDEX IF NOT EXISTS idx_reservations_expires ON inventory_reservations(expires_at);

CREATE INDEX IF NOT EXISTS idx_splits_parent ON order_splits(parent_order_id);
CREATE INDEX IF NOT EXISTS idx_splits_child ON order_splits(child_order_id);
CREATE INDEX IF NOT EXISTS idx_splits_warehouse ON order_splits(warehouse_id);

CREATE INDEX IF NOT EXISTS idx_backorders_order ON backorders(order_id);
CREATE INDEX IF NOT EXISTS idx_backorders_product ON backorders(product_id);
CREATE INDEX IF NOT EXISTS idx_backorders_customer ON backorders(customer_id);
CREATE INDEX IF NOT EXISTS idx_backorders_status ON backorders(status);
CREATE INDEX IF NOT EXISTS idx_backorders_priority ON backorders(priority_score DESC);

CREATE INDEX IF NOT EXISTS idx_waves_warehouse ON fulfillment_waves(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_waves_status ON fulfillment_waves(status);
CREATE INDEX IF NOT EXISTS idx_wave_orders_wave ON wave_orders(wave_id);
CREATE INDEX IF NOT EXISTS idx_wave_orders_order ON wave_orders(order_id);

CREATE INDEX IF NOT EXISTS idx_capacity_warehouse_date ON warehouse_capacity(warehouse_id, date);
CREATE INDEX IF NOT EXISTS idx_plans_order ON fulfillment_plans(order_id);
CREATE INDEX IF NOT EXISTS idx_metrics_date_warehouse ON fulfillment_metrics(date, warehouse_id);
