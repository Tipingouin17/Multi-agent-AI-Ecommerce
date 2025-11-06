-- Carrier Selection Schema
-- Handles intelligent carrier selection, rate shopping, and shipping label generation

-- Carriers Configuration
CREATE TABLE IF NOT EXISTS carriers (
    id SERIAL PRIMARY KEY,
    carrier_code VARCHAR(50) UNIQUE NOT NULL, -- FEDEX, UPS, USPS, DHL
    carrier_name VARCHAR(100) NOT NULL,
    api_endpoint VARCHAR(255),
    api_key_encrypted TEXT,
    account_number VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    supports_tracking BOOLEAN DEFAULT true,
    supports_labels BOOLEAN DEFAULT true,
    supports_international BOOLEAN DEFAULT false,
    dim_weight_divisor INTEGER DEFAULT 139, -- For dimensional weight calculation
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

-- Carrier Services (e.g., Ground, Express, Overnight)
CREATE TABLE IF NOT EXISTS carrier_services (
    id SERIAL PRIMARY KEY,
    carrier_id INTEGER REFERENCES carriers(id) ON DELETE CASCADE,
    service_code VARCHAR(50) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    service_type VARCHAR(50), -- ground, express, overnight, international
    estimated_days INTEGER, -- Typical delivery time
    is_active BOOLEAN DEFAULT true,
    supports_saturday BOOLEAN DEFAULT false,
    supports_sunday BOOLEAN DEFAULT false,
    max_weight_lbs DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(carrier_id, service_code)
);

-- Shipping Rates (cached rate quotes)
CREATE TABLE IF NOT EXISTS shipping_rates (
    id SERIAL PRIMARY KEY,
    carrier_id INTEGER REFERENCES carriers(id),
    service_id INTEGER REFERENCES carrier_services(id),
    origin_zip VARCHAR(20) NOT NULL,
    destination_zip VARCHAR(20) NOT NULL,
    weight_lbs DECIMAL(10,2) NOT NULL,
    length_inches DECIMAL(10,2),
    width_inches DECIMAL(10,2),
    height_inches DECIMAL(10,2),
    dim_weight_lbs DECIMAL(10,2), -- Calculated dimensional weight
    billable_weight_lbs DECIMAL(10,2), -- MAX(actual, dim weight)
    base_rate DECIMAL(10,2) NOT NULL,
    fuel_surcharge DECIMAL(10,2) DEFAULT 0,
    additional_fees DECIMAL(10,2) DEFAULT 0,
    total_rate DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    estimated_delivery_date DATE,
    estimated_days INTEGER,
    zone VARCHAR(10), -- Shipping zone
    rate_valid_until TIMESTAMP, -- Cache expiration
    created_at TIMESTAMP DEFAULT NOW()
);

-- Shipping Labels
CREATE TABLE IF NOT EXISTS shipping_labels (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    shipment_id INTEGER,
    carrier_id INTEGER REFERENCES carriers(id),
    service_id INTEGER REFERENCES carrier_services(id),
    tracking_number VARCHAR(100) UNIQUE NOT NULL,
    label_format VARCHAR(20) DEFAULT 'PDF', -- PDF, PNG, ZPL
    label_url TEXT, -- S3 or file path
    label_data TEXT, -- Base64 encoded label
    status VARCHAR(50) DEFAULT 'active', -- active, voided, expired
    ship_date DATE DEFAULT CURRENT_DATE,
    origin_address JSONB,
    destination_address JSONB,
    package_weight_lbs DECIMAL(10,2),
    package_dimensions JSONB, -- {length, width, height}
    insured_value DECIMAL(10,2),
    signature_required BOOLEAN DEFAULT false,
    is_return_label BOOLEAN DEFAULT false,
    cost DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW(),
    voided_at TIMESTAMP,
    notes TEXT
);

-- Carrier Selection Rules
CREATE TABLE IF NOT EXISTS carrier_rules (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- cost_optimization, speed_optimization, balanced, zone_based
    priority INTEGER DEFAULT 0,
    conditions JSONB, -- Flexible rule conditions (weight range, destination, order value)
    preferred_carriers JSONB, -- Array of carrier IDs in preference order
    excluded_carriers JSONB, -- Array of carrier IDs to exclude
    max_cost DECIMAL(10,2), -- Maximum acceptable cost
    max_days INTEGER, -- Maximum acceptable delivery days
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tracking Events
CREATE TABLE IF NOT EXISTS tracking_events (
    id SERIAL PRIMARY KEY,
    tracking_number VARCHAR(100) NOT NULL,
    label_id INTEGER REFERENCES shipping_labels(id),
    event_type VARCHAR(50) NOT NULL, -- picked_up, in_transit, out_for_delivery, delivered, exception
    event_description TEXT,
    event_location VARCHAR(255),
    event_city VARCHAR(100),
    event_state VARCHAR(50),
    event_zip VARCHAR(20),
    event_country VARCHAR(50),
    event_timestamp TIMESTAMP NOT NULL,
    carrier_id INTEGER REFERENCES carriers(id),
    is_delivered BOOLEAN DEFAULT false,
    signature_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Shipment History (for analytics)
CREATE TABLE IF NOT EXISTS shipment_history (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    label_id INTEGER REFERENCES shipping_labels(id),
    carrier_id INTEGER REFERENCES carriers(id),
    service_id INTEGER REFERENCES carrier_services(id),
    tracking_number VARCHAR(100),
    ship_date DATE,
    estimated_delivery_date DATE,
    actual_delivery_date DATE,
    shipping_cost DECIMAL(10,2),
    delivery_days INTEGER, -- Actual days to deliver
    on_time BOOLEAN, -- Was it delivered on time?
    status VARCHAR(50), -- pending, shipped, in_transit, delivered, exception, returned
    created_at TIMESTAMP DEFAULT NOW(),
    delivered_at TIMESTAMP
);

-- Rate Card Uploads (AI-powered rate extraction)
CREATE TABLE IF NOT EXISTS rate_card_uploads (
    id SERIAL PRIMARY KEY,
    carrier_id INTEGER REFERENCES carriers(id),
    upload_filename VARCHAR(255) NOT NULL,
    upload_file_path TEXT,
    file_type VARCHAR(50), -- pdf, excel, image
    upload_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    extraction_status VARCHAR(50) DEFAULT 'pending', -- pending, extracted, validated, imported
    extracted_data JSONB, -- AI-extracted rate data
    validation_errors JSONB, -- Any validation issues
    rates_imported_count INTEGER DEFAULT 0,
    effective_date DATE,
    expiration_date DATE,
    uploaded_by VARCHAR(100),
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

-- Carrier Performance Metrics (daily aggregated)
CREATE TABLE IF NOT EXISTS carrier_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    carrier_id INTEGER REFERENCES carriers(id),
    total_shipments INTEGER DEFAULT 0,
    on_time_deliveries INTEGER DEFAULT 0,
    late_deliveries INTEGER DEFAULT 0,
    exceptions INTEGER DEFAULT 0,
    average_cost DECIMAL(10,2),
    average_delivery_days DECIMAL(5,2),
    on_time_percentage DECIMAL(5,2),
    total_cost DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date, carrier_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_rates_origin_dest ON shipping_rates(origin_zip, destination_zip);
CREATE INDEX IF NOT EXISTS idx_rates_carrier_service ON shipping_rates(carrier_id, service_id);
CREATE INDEX IF NOT EXISTS idx_rates_valid_until ON shipping_rates(rate_valid_until);
CREATE INDEX IF NOT EXISTS idx_rates_weight ON shipping_rates(weight_lbs);

CREATE INDEX IF NOT EXISTS idx_labels_order ON shipping_labels(order_id);
CREATE INDEX IF NOT EXISTS idx_labels_tracking ON shipping_labels(tracking_number);
CREATE INDEX IF NOT EXISTS idx_labels_carrier ON shipping_labels(carrier_id);
CREATE INDEX IF NOT EXISTS idx_labels_status ON shipping_labels(status);

CREATE INDEX IF NOT EXISTS idx_tracking_number ON tracking_events(tracking_number);
CREATE INDEX IF NOT EXISTS idx_tracking_label ON tracking_events(label_id);
CREATE INDEX IF NOT EXISTS idx_tracking_timestamp ON tracking_events(event_timestamp);

CREATE INDEX IF NOT EXISTS idx_history_order ON shipment_history(order_id);
CREATE INDEX IF NOT EXISTS idx_history_carrier ON shipment_history(carrier_id);
CREATE INDEX IF NOT EXISTS idx_history_date ON shipment_history(ship_date);

CREATE INDEX IF NOT EXISTS idx_metrics_date_carrier ON carrier_metrics(date, carrier_id);

CREATE INDEX IF NOT EXISTS idx_rate_uploads_carrier ON rate_card_uploads(carrier_id);
CREATE INDEX IF NOT EXISTS idx_rate_uploads_status ON rate_card_uploads(upload_status, extraction_status);
