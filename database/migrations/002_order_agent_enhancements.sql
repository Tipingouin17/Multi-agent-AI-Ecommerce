-- Migration: 002_order_agent_enhancements
-- Description: Add comprehensive order management features including order splitting,
--              modifications, gift options, scheduled delivery, and partial shipments
-- Date: 2025-10-19
-- Database: PostgreSQL

-- Add new columns to orders table for enhanced features
ALTER TABLE orders ADD COLUMN IF NOT EXISTS is_gift BOOLEAN DEFAULT FALSE;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS gift_message TEXT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS gift_wrap_type VARCHAR(50);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS scheduled_delivery_date TIMESTAMP;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_instructions TEXT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS is_split_order BOOLEAN DEFAULT FALSE;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS parent_order_id VARCHAR(255);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS split_reason VARCHAR(255);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS priority_level VARCHAR(20) DEFAULT 'normal';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS estimated_delivery_date TIMESTAMP;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS actual_delivery_date TIMESTAMP;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS cancellation_reason TEXT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMP;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS cancelled_by VARCHAR(255);

-- Create order_modifications table for tracking all order changes
CREATE TABLE IF NOT EXISTS order_modifications (
    id SERIAL PRIMARY KEY,
    modification_id VARCHAR(255) UNIQUE NOT NULL,
    order_id VARCHAR(255) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    modification_type VARCHAR(50) NOT NULL,
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    reason TEXT,
    modified_by VARCHAR(255) NOT NULL,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_order_modifications_order_id ON order_modifications(order_id);
CREATE INDEX IF NOT EXISTS idx_order_modifications_type ON order_modifications(modification_type);
CREATE INDEX IF NOT EXISTS idx_order_modifications_date ON order_modifications(modified_at);

-- Create order_splits table for managing split orders
CREATE TABLE IF NOT EXISTS order_splits (
    id SERIAL PRIMARY KEY,
    split_id VARCHAR(255) UNIQUE NOT NULL,
    parent_order_id VARCHAR(255) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    child_order_id VARCHAR(255) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    split_reason VARCHAR(255) NOT NULL,
    split_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    split_by VARCHAR(255),
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_order_splits_parent ON order_splits(parent_order_id);
CREATE INDEX IF NOT EXISTS idx_order_splits_child ON order_splits(child_order_id);
CREATE INDEX IF NOT EXISTS idx_order_splits_date ON order_splits(split_date);

-- Create partial_shipments table for tracking multiple shipments per order
CREATE TABLE IF NOT EXISTS partial_shipments (
    id SERIAL PRIMARY KEY,
    shipment_id VARCHAR(255) UNIQUE NOT NULL,
    order_id VARCHAR(255) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    shipment_number INTEGER NOT NULL,
    items JSONB NOT NULL,
    warehouse_id VARCHAR(255),
    tracking_number VARCHAR(255),
    carrier VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    shipped_at TIMESTAMP,
    estimated_delivery_date TIMESTAMP,
    actual_delivery_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_partial_shipments_order ON partial_shipments(order_id);
CREATE INDEX IF NOT EXISTS idx_partial_shipments_status ON partial_shipments(status);
CREATE INDEX IF NOT EXISTS idx_partial_shipments_tracking ON partial_shipments(tracking_number);

-- Create fulfillment_plans table for warehouse execution planning
CREATE TABLE IF NOT EXISTS fulfillment_plans (
    id SERIAL PRIMARY KEY,
    plan_id VARCHAR(255) UNIQUE NOT NULL,
    order_id VARCHAR(255) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    warehouse_id VARCHAR(255) NOT NULL,
    items JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    assigned_to VARCHAR(255),
    estimated_processing_time_minutes INTEGER,
    actual_processing_time_minutes INTEGER,
    priority_level INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_fulfillment_plans_order ON fulfillment_plans(order_id);
CREATE INDEX IF NOT EXISTS idx_fulfillment_plans_warehouse ON fulfillment_plans(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_fulfillment_plans_status ON fulfillment_plans(status);
CREATE INDEX IF NOT EXISTS idx_fulfillment_plans_priority ON fulfillment_plans(priority_level);

-- Create delivery_attempts table for tracking delivery attempts
CREATE TABLE IF NOT EXISTS delivery_attempts (
    id SERIAL PRIMARY KEY,
    attempt_id VARCHAR(255) UNIQUE NOT NULL,
    order_id VARCHAR(255) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL,
    attempt_date TIMESTAMP NOT NULL,
    success BOOLEAN DEFAULT FALSE,
    failure_reason TEXT,
    driver_notes TEXT,
    recipient_name VARCHAR(255),
    signature_captured BOOLEAN DEFAULT FALSE,
    photo_proof_url VARCHAR(500),
    next_attempt_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_delivery_attempts_order ON delivery_attempts(order_id);
CREATE INDEX IF NOT EXISTS idx_delivery_attempts_date ON delivery_attempts(attempt_date);
CREATE INDEX IF NOT EXISTS idx_delivery_attempts_success ON delivery_attempts(success);

-- Create cancellation_requests table for managing order cancellations
CREATE TABLE IF NOT EXISTS cancellation_requests (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(255) UNIQUE NOT NULL,
    order_id VARCHAR(255) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    requested_by VARCHAR(255) NOT NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    refund_amount DECIMAL(10, 2),
    refund_processed BOOLEAN DEFAULT FALSE,
    refund_processed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cancellation_requests_order ON cancellation_requests(order_id);
CREATE INDEX IF NOT EXISTS idx_cancellation_requests_status ON cancellation_requests(status);
CREATE INDEX IF NOT EXISTS idx_cancellation_requests_date ON cancellation_requests(requested_at);

-- Create order_notes table for internal and customer-visible notes
CREATE TABLE IF NOT EXISTS order_notes (
    id SERIAL PRIMARY KEY,
    note_id VARCHAR(255) UNIQUE NOT NULL,
    order_id VARCHAR(255) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    note_text TEXT NOT NULL,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_visible_to_customer BOOLEAN DEFAULT FALSE,
    is_pinned BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_order_notes_order ON order_notes(order_id);
CREATE INDEX IF NOT EXISTS idx_order_notes_visibility ON order_notes(is_visible_to_customer);
CREATE INDEX IF NOT EXISTS idx_order_notes_date ON order_notes(created_at);

-- Create order_tags table for flexible categorization
CREATE TABLE IF NOT EXISTS order_tags (
    id SERIAL PRIMARY KEY,
    tag_id VARCHAR(255) UNIQUE NOT NULL,
    order_id VARCHAR(255) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    tag VARCHAR(100) NOT NULL,
    added_by VARCHAR(255) NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_order_tags_order ON order_tags(order_id);
CREATE INDEX IF NOT EXISTS idx_order_tags_tag ON order_tags(tag);
CREATE INDEX IF NOT EXISTS idx_order_tags_composite ON order_tags(order_id, tag);

-- Create order_timeline table for complete event history
CREATE TABLE IF NOT EXISTS order_timeline (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    order_id VARCHAR(255) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL,
    actor VARCHAR(255),
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_order_timeline_order ON order_timeline(order_id);
CREATE INDEX IF NOT EXISTS idx_order_timeline_type ON order_timeline(event_type);
CREATE INDEX IF NOT EXISTS idx_order_timeline_date ON order_timeline(event_timestamp);

-- Create gift_options table for gift-related features
CREATE TABLE IF NOT EXISTS gift_options (
    id SERIAL PRIMARY KEY,
    option_id VARCHAR(255) UNIQUE NOT NULL,
    order_id VARCHAR(255) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    is_gift BOOLEAN DEFAULT TRUE,
    gift_message TEXT,
    gift_wrap_type VARCHAR(50),
    gift_wrap_price DECIMAL(10, 2) DEFAULT 0.00,
    hide_prices BOOLEAN DEFAULT TRUE,
    recipient_name VARCHAR(255),
    recipient_email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_gift_options_order ON gift_options(order_id);

-- Create scheduled_deliveries table for delivery scheduling
CREATE TABLE IF NOT EXISTS scheduled_deliveries (
    id SERIAL PRIMARY KEY,
    schedule_id VARCHAR(255) UNIQUE NOT NULL,
    order_id VARCHAR(255) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    preferred_date TIMESTAMP NOT NULL,
    preferred_time_slot VARCHAR(50),
    delivery_instructions TEXT,
    requires_signature BOOLEAN DEFAULT FALSE,
    access_code VARCHAR(50),
    special_instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scheduled_deliveries_order ON scheduled_deliveries(order_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_deliveries_date ON scheduled_deliveries(preferred_date);

-- Create analytical views

-- View: Order Fulfillment Summary
CREATE OR REPLACE VIEW order_fulfillment_summary AS
SELECT 
    o.id AS order_id,
    o.status AS order_status,
    COUNT(DISTINCT ps.shipment_id) AS total_shipments,
    COUNT(DISTINCT CASE WHEN ps.status = 'delivered' THEN ps.shipment_id END) AS delivered_shipments,
    COUNT(DISTINCT fp.plan_id) AS fulfillment_plans,
    COUNT(DISTINCT CASE WHEN fp.status = 'completed' THEN fp.plan_id END) AS completed_plans,
    MIN(ps.estimated_delivery_date) AS earliest_delivery_date,
    MAX(ps.actual_delivery_date) AS latest_delivery_date
FROM orders o
LEFT JOIN partial_shipments ps ON o.id = ps.order_id
LEFT JOIN fulfillment_plans fp ON o.id = fp.order_id
GROUP BY o.id, o.status;

-- View: Order Cancellation Stats
CREATE OR REPLACE VIEW order_cancellation_stats AS
SELECT 
    DATE_TRUNC('day', cr.requested_at) AS request_date,
    cr.status,
    COUNT(*) AS total_requests,
    SUM(cr.refund_amount) AS total_refund_amount,
    AVG(EXTRACT(EPOCH FROM (cr.reviewed_at - cr.requested_at))/3600) AS avg_review_time_hours
FROM cancellation_requests cr
GROUP BY DATE_TRUNC('day', cr.requested_at), cr.status;

-- View: Order Modification Audit
CREATE OR REPLACE VIEW order_modification_audit AS
SELECT 
    om.order_id,
    om.modification_type,
    om.field_name,
    om.old_value,
    om.new_value,
    om.modified_by,
    om.modified_at,
    om.reason
FROM order_modifications om
ORDER BY om.modified_at DESC;

-- Add comments for documentation
COMMENT ON TABLE order_modifications IS 'Tracks all modifications made to orders for audit trail';
COMMENT ON TABLE order_splits IS 'Manages parent-child relationships for split orders';
COMMENT ON TABLE partial_shipments IS 'Tracks multiple shipments for a single order';
COMMENT ON TABLE fulfillment_plans IS 'Warehouse execution plans for order fulfillment';
COMMENT ON TABLE delivery_attempts IS 'Records all delivery attempts including failures';
COMMENT ON TABLE cancellation_requests IS 'Manages order cancellation workflow';
COMMENT ON TABLE order_notes IS 'Internal and customer-visible notes on orders';
COMMENT ON TABLE order_tags IS 'Flexible tagging system for order categorization';
COMMENT ON TABLE order_timeline IS 'Complete event history for each order';
COMMENT ON TABLE gift_options IS 'Gift-related features and preferences';
COMMENT ON TABLE scheduled_deliveries IS 'Delivery scheduling and preferences';
