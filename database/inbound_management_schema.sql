-- Inbound Management Schema
-- Handles receiving, quality control, and putaway operations

-- Inbound Shipments (ASNs - Advanced Shipping Notices)
CREATE TABLE IF NOT EXISTS inbound_shipments (
    id SERIAL PRIMARY KEY,
    shipment_number VARCHAR(50) UNIQUE NOT NULL,
    po_id INTEGER,
    vendor_id INTEGER NOT NULL,
    expected_arrival_date TIMESTAMP,
    actual_arrival_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'expected', -- expected, in_transit, arrived, receiving, completed, cancelled
    carrier VARCHAR(100),
    tracking_number VARCHAR(100),
    total_items INTEGER DEFAULT 0,
    received_items INTEGER DEFAULT 0,
    warehouse_id INTEGER,
    dock_door VARCHAR(20),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inbound Shipment Items
CREATE TABLE IF NOT EXISTS inbound_shipment_items (
    id SERIAL PRIMARY KEY,
    shipment_id INTEGER REFERENCES inbound_shipments(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL,
    sku VARCHAR(100) NOT NULL,
    expected_quantity INTEGER NOT NULL,
    received_quantity INTEGER DEFAULT 0,
    accepted_quantity INTEGER DEFAULT 0,
    rejected_quantity INTEGER DEFAULT 0,
    unit_cost DECIMAL(10, 2),
    status VARCHAR(50) DEFAULT 'pending', -- pending, receiving, completed, discrepancy
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Receiving Tasks
CREATE TABLE IF NOT EXISTS receiving_tasks (
    id SERIAL PRIMARY KEY,
    shipment_id INTEGER REFERENCES inbound_shipments(id),
    task_number VARCHAR(50) UNIQUE NOT NULL,
    assigned_to VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, completed, on_hold
    priority VARCHAR(20) DEFAULT 'medium', -- low, medium, high, urgent
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quality Control Inspections
CREATE TABLE IF NOT EXISTS quality_inspections (
    id SERIAL PRIMARY KEY,
    shipment_item_id INTEGER REFERENCES inbound_shipment_items(id),
    inspection_number VARCHAR(50) UNIQUE NOT NULL,
    inspector_id VARCHAR(100),
    inspection_type VARCHAR(50), -- random, full, sample
    sample_size INTEGER,
    passed_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, passed, failed, partial
    defect_types JSONB, -- Array of defect types found
    photos JSONB, -- Array of photo URLs
    notes TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quality Defects
CREATE TABLE IF NOT EXISTS quality_defects (
    id SERIAL PRIMARY KEY,
    inspection_id INTEGER REFERENCES quality_inspections(id),
    defect_type VARCHAR(100), -- damaged, wrong_item, expired, missing_parts, etc.
    severity VARCHAR(20), -- minor, major, critical
    quantity INTEGER,
    description TEXT,
    action_taken VARCHAR(100), -- reject, accept_with_discount, return_to_vendor
    photos JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Putaway Tasks
CREATE TABLE IF NOT EXISTS putaway_tasks (
    id SERIAL PRIMARY KEY,
    shipment_item_id INTEGER REFERENCES inbound_shipment_items(id),
    task_number VARCHAR(50) UNIQUE NOT NULL,
    product_id INTEGER NOT NULL,
    sku VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    from_location VARCHAR(100), -- Receiving dock/staging area
    to_location VARCHAR(100), -- Final storage location
    assigned_to VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, completed, cancelled
    priority VARCHAR(20) DEFAULT 'medium',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Receiving Discrepancies
CREATE TABLE IF NOT EXISTS receiving_discrepancies (
    id SERIAL PRIMARY KEY,
    shipment_id INTEGER REFERENCES inbound_shipments(id),
    shipment_item_id INTEGER REFERENCES inbound_shipment_items(id),
    discrepancy_type VARCHAR(50), -- quantity_mismatch, damaged, wrong_item, missing, extra
    expected_quantity INTEGER,
    actual_quantity INTEGER,
    variance INTEGER,
    resolution_status VARCHAR(50) DEFAULT 'open', -- open, investigating, resolved, closed
    resolution_notes TEXT,
    reported_by VARCHAR(100),
    resolved_by VARCHAR(100),
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inbound Performance Metrics
CREATE TABLE IF NOT EXISTS inbound_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    warehouse_id INTEGER,
    shipments_received INTEGER DEFAULT 0,
    items_received INTEGER DEFAULT 0,
    items_accepted INTEGER DEFAULT 0,
    items_rejected INTEGER DEFAULT 0,
    average_receiving_time DECIMAL(10, 2), -- in minutes
    average_putaway_time DECIMAL(10, 2), -- in minutes
    discrepancy_rate DECIMAL(5, 2), -- percentage
    quality_pass_rate DECIMAL(5, 2), -- percentage
    on_time_arrival_rate DECIMAL(5, 2), -- percentage
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, warehouse_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_inbound_shipments_status ON inbound_shipments(status);
CREATE INDEX IF NOT EXISTS idx_inbound_shipments_arrival ON inbound_shipments(expected_arrival_date);
CREATE INDEX IF NOT EXISTS idx_inbound_shipments_po ON inbound_shipments(po_id);
CREATE INDEX IF NOT EXISTS idx_receiving_tasks_status ON receiving_tasks(status);
CREATE INDEX IF NOT EXISTS idx_receiving_tasks_assigned ON receiving_tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_quality_inspections_status ON quality_inspections(status);
CREATE INDEX IF NOT EXISTS idx_putaway_tasks_status ON putaway_tasks(status);
CREATE INDEX IF NOT EXISTS idx_putaway_tasks_assigned ON putaway_tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_discrepancies_status ON receiving_discrepancies(resolution_status);
