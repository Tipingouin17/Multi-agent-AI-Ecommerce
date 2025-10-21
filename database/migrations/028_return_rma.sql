-- Return/RMA Configuration Migration
-- Supports comprehensive return and RMA management

-- Return Policies Table
CREATE TABLE IF NOT EXISTS return_policies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL, -- electronics, clothing, furniture, etc.
    return_window_days INTEGER NOT NULL DEFAULT 30,
    exchange_window_days INTEGER NOT NULL DEFAULT 30,
    refund_method VARCHAR(50) NOT NULL, -- original_payment, store_credit, exchange_only, both
    restocking_fee_percent DECIMAL(5, 2) DEFAULT 0,
    requires_original_packaging BOOLEAN DEFAULT false,
    requires_tags_attached BOOLEAN DEFAULT false,
    free_return_shipping BOOLEAN DEFAULT false,
    auto_approve_enabled BOOLEAN DEFAULT false,
    inspection_required BOOLEAN DEFAULT true,
    enabled BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

-- Return Reasons Table
CREATE TABLE IF NOT EXISTS return_reasons (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    label VARCHAR(255) NOT NULL,
    description TEXT,
    requires_photo BOOLEAN DEFAULT false,
    requires_explanation BOOLEAN DEFAULT false,
    auto_approve BOOLEAN DEFAULT false,
    restocking_fee_override DECIMAL(5, 2),
    enabled BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Return Requests Table
CREATE TABLE IF NOT EXISTS return_requests (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    customer_id INTEGER REFERENCES customers(id),
    policy_id INTEGER REFERENCES return_policies(id),
    reason_id INTEGER REFERENCES return_reasons(id),
    status VARCHAR(50) DEFAULT 'pending', -- pending, approved, rejected, received, inspected, completed, cancelled
    return_type VARCHAR(50) NOT NULL, -- refund, exchange, store_credit
    items JSONB NOT NULL, -- Array of items to return
    total_amount DECIMAL(10, 2),
    restocking_fee DECIMAL(10, 2) DEFAULT 0,
    refund_amount DECIMAL(10, 2),
    customer_notes TEXT,
    admin_notes TEXT,
    photos TEXT[], -- Array of photo URLs
    return_label_url VARCHAR(500),
    tracking_number VARCHAR(100),
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    approved_by INTEGER REFERENCES users(id),
    rejected_at TIMESTAMP,
    rejected_by INTEGER REFERENCES users(id),
    received_at TIMESTAMP,
    inspected_at TIMESTAMP,
    completed_at TIMESTAMP,
    metadata JSONB
);

-- Return Items Table
CREATE TABLE IF NOT EXISTS return_items (
    id SERIAL PRIMARY KEY,
    return_request_id INTEGER REFERENCES return_requests(id) ON DELETE CASCADE,
    order_item_id INTEGER,
    product_id INTEGER REFERENCES products(id),
    product_name VARCHAR(255),
    sku VARCHAR(100),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2),
    total_price DECIMAL(10, 2),
    condition VARCHAR(50), -- unopened, opened, used, damaged, defective
    disposition VARCHAR(50), -- restock, refurbish, liquidate, donate, recycle, dispose
    inspection_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Return Inspections Table
CREATE TABLE IF NOT EXISTS return_inspections (
    id SERIAL PRIMARY KEY,
    return_request_id INTEGER REFERENCES return_requests(id) ON DELETE CASCADE,
    inspector_id INTEGER REFERENCES users(id),
    inspection_status VARCHAR(50) NOT NULL, -- passed, failed, partial
    overall_condition VARCHAR(50), -- excellent, good, fair, poor, damaged
    packaging_intact BOOLEAN,
    tags_attached BOOLEAN,
    all_items_present BOOLEAN,
    items_functional BOOLEAN,
    notes TEXT,
    photos TEXT[],
    inspected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Return Disposition Rules Table
CREATE TABLE IF NOT EXISTS return_disposition_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    condition VARCHAR(50) NOT NULL, -- unopened, opened, used, damaged, defective
    category VARCHAR(50), -- Product category filter
    action VARCHAR(50) NOT NULL, -- restock, refurbish, liquidate, donate, recycle, dispose
    priority INTEGER DEFAULT 5,
    enabled BOOLEAN DEFAULT true,
    conditions JSONB, -- Additional rule conditions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Return Refunds Table
CREATE TABLE IF NOT EXISTS return_refunds (
    id SERIAL PRIMARY KEY,
    return_request_id INTEGER REFERENCES return_requests(id) ON DELETE CASCADE,
    refund_method VARCHAR(50) NOT NULL, -- original_payment, store_credit, exchange
    refund_amount DECIMAL(10, 2) NOT NULL,
    processing_fee DECIMAL(10, 2) DEFAULT 0,
    net_refund_amount DECIMAL(10, 2),
    payment_gateway VARCHAR(100),
    transaction_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    processed_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Return Shipping Labels Table
CREATE TABLE IF NOT EXISTS return_shipping_labels (
    id SERIAL PRIMARY KEY,
    return_request_id INTEGER REFERENCES return_requests(id) ON DELETE CASCADE,
    carrier VARCHAR(100) NOT NULL,
    service_level VARCHAR(100),
    tracking_number VARCHAR(100),
    label_url VARCHAR(500),
    label_format VARCHAR(20) DEFAULT 'PDF', -- PDF, PNG, ZPL
    cost DECIMAL(10, 2),
    customer_paid BOOLEAN DEFAULT false,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    used_at TIMESTAMP,
    metadata JSONB
);

-- Return Analytics Table
CREATE TABLE IF NOT EXISTS return_analytics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    category VARCHAR(50),
    return_count INTEGER DEFAULT 0,
    approved_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    total_refund_amount DECIMAL(10, 2) DEFAULT 0,
    avg_processing_time_hours INTEGER,
    return_rate DECIMAL(5, 4), -- Percentage of orders
    top_return_reasons JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, category)
);

-- Indexes for performance
CREATE INDEX idx_return_policies_category ON return_policies(category);
CREATE INDEX idx_return_policies_enabled ON return_policies(enabled);
CREATE INDEX idx_return_reasons_code ON return_reasons(code);
CREATE INDEX idx_return_requests_order ON return_requests(order_id);
CREATE INDEX idx_return_requests_customer ON return_requests(customer_id);
CREATE INDEX idx_return_requests_status ON return_requests(status);
CREATE INDEX idx_return_requests_requested_at ON return_requests(requested_at);
CREATE INDEX idx_return_items_return_request ON return_items(return_request_id);
CREATE INDEX idx_return_inspections_return_request ON return_inspections(return_request_id);
CREATE INDEX idx_return_refunds_return_request ON return_refunds(return_request_id);
CREATE INDEX idx_return_refunds_status ON return_refunds(status);
CREATE INDEX idx_return_shipping_labels_return_request ON return_shipping_labels(return_request_id);
CREATE INDEX idx_return_analytics_date ON return_analytics(date);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_return_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER return_policies_updated_at
    BEFORE UPDATE ON return_policies
    FOR EACH ROW
    EXECUTE FUNCTION update_return_timestamp();

CREATE TRIGGER return_disposition_rules_updated_at
    BEFORE UPDATE ON return_disposition_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_return_timestamp();

-- Insert sample return policies
INSERT INTO return_policies (
    name, category, return_window_days, exchange_window_days, refund_method,
    restocking_fee_percent, requires_original_packaging, free_return_shipping, enabled
) VALUES
(
    'Standard Electronics Return Policy',
    'electronics',
    30,
    30,
    'original_payment',
    15.0,
    true,
    false,
    true
),
(
    'Clothing & Apparel Return Policy',
    'clothing',
    60,
    60,
    'both',
    0,
    false,
    true,
    true
),
(
    'Furniture Return Policy',
    'furniture',
    14,
    14,
    'store_credit',
    20.0,
    true,
    false,
    true
),
(
    'General Merchandise Policy',
    'general',
    30,
    30,
    'original_payment',
    0,
    false,
    true,
    true
);

-- Insert sample return reasons
INSERT INTO return_reasons (code, label, description, requires_photo, auto_approve, enabled) VALUES
('defective', 'Defective or Damaged', 'Product arrived defective or damaged', true, false, true),
('wrong_item', 'Wrong Item Received', 'Received incorrect product', true, false, true),
('not_as_described', 'Not as Described', 'Product does not match description', true, false, true),
('size_fit', 'Size/Fit Issue', 'Product size or fit is not suitable', false, true, true),
('changed_mind', 'Changed Mind', 'Customer changed their mind', false, true, true),
('better_price', 'Found Better Price', 'Found the product at a better price elsewhere', false, true, true),
('late_delivery', 'Arrived Too Late', 'Product arrived after needed date', false, true, true),
('quality', 'Quality Not Satisfactory', 'Product quality does not meet expectations', true, false, true),
('other', 'Other', 'Other reason not listed', false, false, true);

-- Insert sample disposition rules
INSERT INTO return_disposition_rules (name, condition, action, priority, enabled) VALUES
('Restock Unopened Items', 'unopened', 'restock', 1, true),
('Refurbish Opened Electronics', 'opened', 'refurbish', 2, true),
('Liquidate Used Items', 'used', 'liquidate', 3, true),
('Dispose Damaged Items', 'damaged', 'dispose', 4, true),
('Recycle Defective Electronics', 'defective', 'recycle', 5, true);

-- Comments for documentation
COMMENT ON TABLE return_policies IS 'Return policy configurations by product category';
COMMENT ON TABLE return_reasons IS 'Predefined return reasons for customers';
COMMENT ON TABLE return_requests IS 'Customer return requests and RMA records';
COMMENT ON TABLE return_items IS 'Individual items in return requests';
COMMENT ON TABLE return_inspections IS 'Quality inspection records for returned items';
COMMENT ON TABLE return_disposition_rules IS 'Rules for handling returned items';
COMMENT ON TABLE return_refunds IS 'Refund processing records';
COMMENT ON TABLE return_shipping_labels IS 'Generated return shipping labels';
COMMENT ON TABLE return_analytics IS 'Aggregated return analytics and metrics';

