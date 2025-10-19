-- Migration: Order Agent Enhancements
-- Description: Add comprehensive order management features including order splitting,
--              modifications, gift options, scheduled delivery, and partial shipments
-- Date: 2025-10-19

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
    modification_type VARCHAR(50) NOT NULL, -- 'status_change', 'item_added', 'item_removed', 'address_change', etc.
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    reason TEXT,
    modified_by VARCHAR(255) NOT NULL, -- user_id or agent_id
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    
    INDEX idx_order_modifications_order_id (order_id),
    INDEX idx_order_modifications_type (modification_type),
    INDEX idx_order_modifications_date (modified_at)
);

-- Create order_splits table for managing split orders
CREATE TABLE IF NOT EXISTS order_splits (
    id SERIAL PRIMARY KEY,
    split_id VARCHAR(255) UNIQUE NOT NULL,
    parent_order_id VARCHAR(255) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    child_order_id VARCHAR(255) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    split_reason VARCHAR(255) NOT NULL, -- 'multi_warehouse', 'partial_availability', 'delivery_speed', etc.
    split_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    split_by VARCHAR(255), -- agent_id that initiated the split
    metadata JSONB,
    
    INDEX idx_order_splits_parent (parent_order_id),
    INDEX idx_order_splits_child (child_order_id),
    INDEX idx_order_splits_date (split_date)
);

-- Create partial_shipments table for tracking partial order fulfillment
CREATE TABLE IF NOT EXISTS partial_shipments (
    id SERIAL PRIMARY KEY,
    shipment_id VARCHAR(255) UNIQUE NOT NULL,
    order_id VARCHAR(255) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    shipment_number INTEGER NOT NULL, -- 1, 2, 3, etc. for multiple shipments
    tracking_number VARCHAR(255),
    carrier VARCHAR(100),
    shipped_at TIMESTAMP,
    estimated_delivery TIMESTAMP,
    actual_delivery TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'shipped', 'in_transit', 'delivered'
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_partial_shipments_order (order_id),
    INDEX idx_partial_shipments_tracking (tracking_number),
    INDEX idx_partial_shipments_status (status),
    UNIQUE (order_id, shipment_number)
);

-- Create partial_shipment_items table for items in each partial shipment
CREATE TABLE IF NOT EXISTS partial_shipment_items (
    id SERIAL PRIMARY KEY,
    shipment_id VARCHAR(255) NOT NULL REFERENCES partial_shipments(shipment_id) ON DELETE CASCADE,
    order_item_id INTEGER NOT NULL REFERENCES order_items(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    
    INDEX idx_partial_shipment_items_shipment (shipment_id),
    INDEX idx_partial_shipment_items_order_item (order_item_id),
    UNIQUE (shipment_id, order_item_id)
);

-- Create order_timeline table for detailed order event tracking
CREATE TABLE IF NOT EXISTS order_timeline (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    order_id VARCHAR(255) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL, -- 'created', 'paid', 'shipped', 'delivered', 'modified', etc.
    event_description TEXT NOT NULL,
    event_data JSONB,
    triggered_by VARCHAR(255), -- user_id or agent_id
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_order_timeline_order (order_id),
    INDEX idx_order_timeline_type (event_type),
    INDEX idx_order_timeline_date (occurred_at)
);

-- Create order_notes table for internal and customer-facing notes
CREATE TABLE IF NOT EXISTS order_notes (
    id SERIAL PRIMARY KEY,
    note_id VARCHAR(255) UNIQUE NOT NULL,
    order_id VARCHAR(255) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    note_type VARCHAR(50) NOT NULL, -- 'internal', 'customer', 'system'
    note_text TEXT NOT NULL,
    is_visible_to_customer BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(255) NOT NULL, -- user_id or agent_id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_order_notes_order (order_id),
    INDEX idx_order_notes_type (note_type),
    INDEX idx_order_notes_visibility (is_visible_to_customer)
);

-- Create order_tags table for flexible order categorization
CREATE TABLE IF NOT EXISTS order_tags (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(255) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    tag VARCHAR(100) NOT NULL, -- 'urgent', 'vip', 'fragile', 'gift', 'international', etc.
    added_by VARCHAR(255),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_order_tags_order (order_id),
    INDEX idx_order_tags_tag (tag),
    UNIQUE (order_id, tag)
);

-- Create order_fulfillment_plan table for multi-warehouse fulfillment
CREATE TABLE IF NOT EXISTS order_fulfillment_plan (
    id SERIAL PRIMARY KEY,
    plan_id VARCHAR(255) UNIQUE NOT NULL,
    order_id VARCHAR(255) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    warehouse_id VARCHAR(255) NOT NULL,
    fulfillment_strategy VARCHAR(50) NOT NULL, -- 'single_warehouse', 'split_shipment', 'dropship', etc.
    estimated_ship_date TIMESTAMP,
    estimated_delivery_date TIMESTAMP,
    priority INTEGER DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'planned', -- 'planned', 'in_progress', 'completed', 'cancelled'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_fulfillment_plan_order (order_id),
    INDEX idx_fulfillment_plan_warehouse (warehouse_id),
    INDEX idx_fulfillment_plan_status (status)
);

-- Create order_fulfillment_items table for items in each fulfillment plan
CREATE TABLE IF NOT EXISTS order_fulfillment_items (
    id SERIAL PRIMARY KEY,
    plan_id VARCHAR(255) NOT NULL REFERENCES order_fulfillment_plan(plan_id) ON DELETE CASCADE,
    order_item_id INTEGER NOT NULL REFERENCES order_items(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    allocated_quantity INTEGER DEFAULT 0 CHECK (allocated_quantity >= 0),
    picked_quantity INTEGER DEFAULT 0 CHECK (picked_quantity >= 0),
    packed_quantity INTEGER DEFAULT 0 CHECK (packed_quantity >= 0),
    
    INDEX idx_fulfillment_items_plan (plan_id),
    INDEX idx_fulfillment_items_order_item (order_item_id),
    UNIQUE (plan_id, order_item_id)
);

-- Create order_delivery_attempts table for tracking delivery attempts
CREATE TABLE IF NOT EXISTS order_delivery_attempts (
    id SERIAL PRIMARY KEY,
    attempt_id VARCHAR(255) UNIQUE NOT NULL,
    order_id VARCHAR(255) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    shipment_id VARCHAR(255) REFERENCES partial_shipments(shipment_id),
    attempt_number INTEGER NOT NULL,
    attempted_at TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'successful', 'failed', 'customer_not_home', 'address_issue', etc.
    failure_reason TEXT,
    next_attempt_date TIMESTAMP,
    notes TEXT,
    
    INDEX idx_delivery_attempts_order (order_id),
    INDEX idx_delivery_attempts_shipment (shipment_id),
    INDEX idx_delivery_attempts_status (status)
);

-- Create order_cancellation_requests table for managing cancellation workflow
CREATE TABLE IF NOT EXISTS order_cancellation_requests (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(255) UNIQUE NOT NULL,
    order_id VARCHAR(255) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    requested_by VARCHAR(255) NOT NULL, -- customer_id or agent_id
    reason VARCHAR(255) NOT NULL,
    detailed_reason TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'completed'
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    refund_amount DECIMAL(10, 2),
    refund_status VARCHAR(50), -- 'pending', 'processing', 'completed', 'failed'
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    INDEX idx_cancellation_requests_order (order_id),
    INDEX idx_cancellation_requests_status (status),
    INDEX idx_cancellation_requests_requested_by (requested_by)
);

-- Add indexes for improved query performance
CREATE INDEX IF NOT EXISTS idx_orders_is_gift ON orders(is_gift);
CREATE INDEX IF NOT EXISTS idx_orders_scheduled_delivery ON orders(scheduled_delivery_date);
CREATE INDEX IF NOT EXISTS idx_orders_is_split ON orders(is_split_order);
CREATE INDEX IF NOT EXISTS idx_orders_parent_order ON orders(parent_order_id);
CREATE INDEX IF NOT EXISTS idx_orders_priority ON orders(priority_level);
CREATE INDEX IF NOT EXISTS idx_orders_estimated_delivery ON orders(estimated_delivery_date);
CREATE INDEX IF NOT EXISTS idx_orders_cancelled_at ON orders(cancelled_at);

-- Add foreign key constraint for parent_order_id (self-referencing)
ALTER TABLE orders 
ADD CONSTRAINT fk_orders_parent 
FOREIGN KEY (parent_order_id) REFERENCES orders(id) ON DELETE SET NULL;

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_partial_shipments_updated_at BEFORE UPDATE ON partial_shipments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_order_notes_updated_at BEFORE UPDATE ON order_notes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_fulfillment_plan_updated_at BEFORE UPDATE ON order_fulfillment_plan
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries

-- View for order summary with split information
CREATE OR REPLACE VIEW order_summary_view AS
SELECT 
    o.id,
    o.customer_id,
    o.channel,
    o.status,
    o.total_amount,
    o.is_gift,
    o.is_split_order,
    o.parent_order_id,
    o.scheduled_delivery_date,
    o.estimated_delivery_date,
    o.priority_level,
    o.created_at,
    COUNT(DISTINCT os.child_order_id) as split_count,
    COUNT(DISTINCT ps.shipment_id) as shipment_count,
    COUNT(DISTINCT ot.event_id) as event_count
FROM orders o
LEFT JOIN order_splits os ON o.id = os.parent_order_id
LEFT JOIN partial_shipments ps ON o.id = ps.order_id
LEFT JOIN order_timeline ot ON o.id = ot.order_id
GROUP BY o.id;

-- View for pending fulfillment
CREATE OR REPLACE VIEW pending_fulfillment_view AS
SELECT 
    ofp.plan_id,
    ofp.order_id,
    o.customer_id,
    ofp.warehouse_id,
    ofp.fulfillment_strategy,
    ofp.estimated_ship_date,
    ofp.priority,
    COUNT(ofi.id) as item_count,
    SUM(ofi.quantity) as total_quantity,
    SUM(ofi.picked_quantity) as picked_quantity
FROM order_fulfillment_plan ofp
JOIN orders o ON ofp.order_id = o.id
LEFT JOIN order_fulfillment_items ofi ON ofp.plan_id = ofi.plan_id
WHERE ofp.status IN ('planned', 'in_progress')
GROUP BY ofp.plan_id, ofp.order_id, o.customer_id, ofp.warehouse_id, 
         ofp.fulfillment_strategy, ofp.estimated_ship_date, ofp.priority;

-- Insert sample data for testing (optional - comment out for production)
-- This data helps with initial testing of the enhanced features

COMMENT ON TABLE order_modifications IS 'Tracks all modifications made to orders including status changes, item updates, and address changes';
COMMENT ON TABLE order_splits IS 'Manages relationships between parent orders and their split child orders';
COMMENT ON TABLE partial_shipments IS 'Tracks multiple shipments for a single order when items are fulfilled separately';
COMMENT ON TABLE partial_shipment_items IS 'Links order items to their respective partial shipments';
COMMENT ON TABLE order_timeline IS 'Comprehensive event log for order lifecycle tracking';
COMMENT ON TABLE order_notes IS 'Internal and customer-facing notes attached to orders';
COMMENT ON TABLE order_tags IS 'Flexible tagging system for order categorization';
COMMENT ON TABLE order_fulfillment_plan IS 'Defines how orders will be fulfilled across warehouses';
COMMENT ON TABLE order_fulfillment_items IS 'Tracks fulfillment progress for each order item';
COMMENT ON TABLE order_delivery_attempts IS 'Records all delivery attempts and their outcomes';
COMMENT ON TABLE order_cancellation_requests IS 'Manages the order cancellation workflow and approval process';

-- Migration complete
-- This schema supports:
-- 1. Order splitting for multi-warehouse fulfillment
-- 2. Partial shipments with tracking
-- 3. Gift orders with messages and wrapping
-- 4. Scheduled delivery dates
-- 5. Order modifications with full audit trail
-- 6. Comprehensive order timeline
-- 7. Flexible order tagging
-- 8. Fulfillment planning and tracking
-- 9. Delivery attempt tracking
-- 10. Cancellation request workflow

