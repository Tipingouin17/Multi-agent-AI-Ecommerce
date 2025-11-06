-- RMA (Return Merchandise Authorization) Workflow Schema
-- Handles complete return management from request to refund

-- RMA Requests (main return tracking)
CREATE TABLE IF NOT EXISTS rma_requests (
    id SERIAL PRIMARY KEY,
    rma_number VARCHAR(50) UNIQUE NOT NULL,
    order_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'requested', -- requested, approved, rejected, label_sent, in_transit, received, inspecting, inspected, refund_pending, refund_processed, completed, closed
    return_reason VARCHAR(100) NOT NULL, -- defective, wrong_item, not_as_described, changed_mind, damaged_in_shipping, other
    return_reason_details TEXT,
    requested_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP,
    approved_by VARCHAR(100),
    rejected_at TIMESTAMP,
    rejection_reason TEXT,
    received_at TIMESTAMP,
    inspected_at TIMESTAMP,
    completed_at TIMESTAMP,
    is_eligible BOOLEAN DEFAULT true,
    eligibility_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- RMA Items (individual items in return)
CREATE TABLE IF NOT EXISTS rma_items (
    id SERIAL PRIMARY KEY,
    rma_id INTEGER REFERENCES rma_requests(id) ON DELETE CASCADE,
    order_item_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    product_sku VARCHAR(100),
    product_name VARCHAR(255),
    quantity_requested INTEGER NOT NULL,
    quantity_received INTEGER DEFAULT 0,
    unit_price DECIMAL(10,2) NOT NULL,
    condition_requested VARCHAR(50), -- unopened, opened, defective, damaged
    condition_actual VARCHAR(50), -- new, like_new, good, fair, poor, defective, unsellable
    disposition VARCHAR(50), -- restock, liquidate, warranty_claim, dispose, pending
    restocking_fee_percent DECIMAL(5,2) DEFAULT 0,
    restocking_fee_amount DECIMAL(10,2) DEFAULT 0,
    refund_amount DECIMAL(10,2) DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- RMA Inspections (inspection records)
CREATE TABLE IF NOT EXISTS rma_inspections (
    id SERIAL PRIMARY KEY,
    rma_id INTEGER REFERENCES rma_requests(id) ON DELETE CASCADE,
    rma_item_id INTEGER REFERENCES rma_items(id) ON DELETE CASCADE,
    inspector_name VARCHAR(100),
    inspection_date TIMESTAMP DEFAULT NOW(),
    condition_assessment VARCHAR(50) NOT NULL,
    packaging_condition VARCHAR(50), -- original, damaged, missing
    completeness_check BOOLEAN DEFAULT true, -- all parts/accessories included
    functionality_check BOOLEAN DEFAULT true,
    cosmetic_condition VARCHAR(50), -- excellent, good, fair, poor
    inspection_notes TEXT,
    photos JSONB, -- Array of photo URLs
    passed_inspection BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- RMA Refunds (refund processing)
CREATE TABLE IF NOT EXISTS rma_refunds (
    id SERIAL PRIMARY KEY,
    rma_id INTEGER REFERENCES rma_requests(id) ON DELETE CASCADE,
    refund_method VARCHAR(50) NOT NULL, -- original_payment, store_credit, exchange, check
    subtotal DECIMAL(10,2) NOT NULL,
    restocking_fees DECIMAL(10,2) DEFAULT 0,
    return_shipping_cost DECIMAL(10,2) DEFAULT 0,
    original_shipping_refund DECIMAL(10,2) DEFAULT 0,
    total_refund_amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    refund_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    payment_transaction_id VARCHAR(100),
    processed_at TIMESTAMP,
    failed_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- RMA Shipping (return shipping labels)
CREATE TABLE IF NOT EXISTS rma_shipping (
    id SERIAL PRIMARY KEY,
    rma_id INTEGER REFERENCES rma_requests(id) ON DELETE CASCADE,
    carrier_id INTEGER,
    tracking_number VARCHAR(100),
    label_url TEXT,
    label_cost DECIMAL(10,2),
    ship_from_address JSONB,
    ship_to_address JSONB, -- warehouse/return center
    label_created_at TIMESTAMP DEFAULT NOW(),
    shipped_at TIMESTAMP,
    estimated_arrival DATE,
    actual_arrival TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- RMA Communications (customer communication log)
CREATE TABLE IF NOT EXISTS rma_communications (
    id SERIAL PRIMARY KEY,
    rma_id INTEGER REFERENCES rma_requests(id) ON DELETE CASCADE,
    communication_type VARCHAR(50) NOT NULL, -- email, sms, phone, chat
    direction VARCHAR(20) NOT NULL, -- inbound, outbound
    subject VARCHAR(255),
    message TEXT,
    sent_at TIMESTAMP DEFAULT NOW(),
    sent_by VARCHAR(100),
    status VARCHAR(50) DEFAULT 'sent', -- sent, delivered, failed, read
    created_at TIMESTAMP DEFAULT NOW()
);

-- RMA Photos (inspection photos)
CREATE TABLE IF NOT EXISTS rma_photos (
    id SERIAL PRIMARY KEY,
    rma_id INTEGER REFERENCES rma_requests(id) ON DELETE CASCADE,
    rma_item_id INTEGER REFERENCES rma_items(id) ON DELETE CASCADE,
    inspection_id INTEGER REFERENCES rma_inspections(id) ON DELETE CASCADE,
    photo_url TEXT NOT NULL,
    photo_type VARCHAR(50), -- packaging, product, defect, label, other
    description TEXT,
    uploaded_by VARCHAR(100),
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- RMA Metrics (daily aggregated)
CREATE TABLE IF NOT EXISTS rma_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    total_requests INTEGER DEFAULT 0,
    approved_requests INTEGER DEFAULT 0,
    rejected_requests INTEGER DEFAULT 0,
    completed_returns INTEGER DEFAULT 0,
    total_refund_amount DECIMAL(10,2) DEFAULT 0,
    total_restocking_fees DECIMAL(10,2) DEFAULT 0,
    average_processing_days DECIMAL(5,2),
    restocked_items INTEGER DEFAULT 0,
    disposed_items INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date)
);

-- Return Policies (configurable return policies)
CREATE TABLE IF NOT EXISTS return_policies (
    id SERIAL PRIMARY KEY,
    policy_name VARCHAR(100) NOT NULL,
    return_window_days INTEGER DEFAULT 30,
    restocking_fee_percent DECIMAL(5,2) DEFAULT 0,
    free_return_shipping BOOLEAN DEFAULT false,
    conditions TEXT, -- JSON or text describing conditions
    excluded_categories JSONB, -- Array of category IDs
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_rma_requests_order ON rma_requests(order_id);
CREATE INDEX IF NOT EXISTS idx_rma_requests_customer ON rma_requests(customer_id);
CREATE INDEX IF NOT EXISTS idx_rma_requests_status ON rma_requests(status);
CREATE INDEX IF NOT EXISTS idx_rma_requests_rma_number ON rma_requests(rma_number);
CREATE INDEX IF NOT EXISTS idx_rma_requests_requested_at ON rma_requests(requested_at);

CREATE INDEX IF NOT EXISTS idx_rma_items_rma ON rma_items(rma_id);
CREATE INDEX IF NOT EXISTS idx_rma_items_product ON rma_items(product_id);
CREATE INDEX IF NOT EXISTS idx_rma_items_disposition ON rma_items(disposition);

CREATE INDEX IF NOT EXISTS idx_rma_inspections_rma ON rma_inspections(rma_id);
CREATE INDEX IF NOT EXISTS idx_rma_inspections_item ON rma_inspections(rma_item_id);
CREATE INDEX IF NOT EXISTS idx_rma_inspections_date ON rma_inspections(inspection_date);

CREATE INDEX IF NOT EXISTS idx_rma_refunds_rma ON rma_refunds(rma_id);
CREATE INDEX IF NOT EXISTS idx_rma_refunds_status ON rma_refunds(refund_status);

CREATE INDEX IF NOT EXISTS idx_rma_shipping_rma ON rma_shipping(rma_id);
CREATE INDEX IF NOT EXISTS idx_rma_shipping_tracking ON rma_shipping(tracking_number);

CREATE INDEX IF NOT EXISTS idx_rma_communications_rma ON rma_communications(rma_id);
CREATE INDEX IF NOT EXISTS idx_rma_communications_sent_at ON rma_communications(sent_at);

CREATE INDEX IF NOT EXISTS idx_rma_photos_rma ON rma_photos(rma_id);
CREATE INDEX IF NOT EXISTS idx_rma_photos_item ON rma_photos(rma_item_id);

CREATE INDEX IF NOT EXISTS idx_rma_metrics_date ON rma_metrics(date);
