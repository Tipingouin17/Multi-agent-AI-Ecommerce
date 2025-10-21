-- Migration 030: Carrier Contracts and Rate Cards Management
-- This migration creates tables for managing carrier contracts, rate cards, postal zones, and surcharges

-- ============================================================================
-- Carrier Contracts Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS carrier_contracts (
    id SERIAL PRIMARY KEY,
    carrier_id INTEGER NOT NULL REFERENCES carriers(id) ON DELETE CASCADE,
    contract_number VARCHAR(100) NOT NULL,
    effective_date DATE NOT NULL,
    expiry_date DATE,
    file_path TEXT NOT NULL,
    file_type VARCHAR(20),
    file_size INTEGER,
    parsed_data JSONB,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'expired', 'pending', 'archived')),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by INTEGER REFERENCES users(id),
    parsed_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(carrier_id, contract_number)
);

CREATE INDEX idx_carrier_contracts_carrier ON carrier_contracts(carrier_id);
CREATE INDEX idx_carrier_contracts_status ON carrier_contracts(status);
CREATE INDEX idx_carrier_contracts_effective_date ON carrier_contracts(effective_date);
CREATE INDEX idx_carrier_contracts_expiry_date ON carrier_contracts(expiry_date);

COMMENT ON TABLE carrier_contracts IS 'Stores carrier contract documents and parsed data';
COMMENT ON COLUMN carrier_contracts.parsed_data IS 'JSON data extracted from contract by AI parsing';

-- ============================================================================
-- Carrier Rate Cards Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS carrier_rate_cards (
    id SERIAL PRIMARY KEY,
    carrier_id INTEGER NOT NULL REFERENCES carriers(id) ON DELETE CASCADE,
    contract_id INTEGER REFERENCES carrier_contracts(id) ON DELETE SET NULL,
    weight_min DECIMAL(10, 2) NOT NULL,
    weight_max DECIMAL(10, 2) NOT NULL,
    zone VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    service_level VARCHAR(50),
    effective_date DATE NOT NULL DEFAULT CURRENT_DATE,
    expiry_date DATE,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(carrier_id, weight_min, weight_max, zone, service_level, effective_date)
);

CREATE INDEX idx_rate_cards_carrier ON carrier_rate_cards(carrier_id);
CREATE INDEX idx_rate_cards_zone ON carrier_rate_cards(zone);
CREATE INDEX idx_rate_cards_weight ON carrier_rate_cards(weight_min, weight_max);
CREATE INDEX idx_rate_cards_active ON carrier_rate_cards(is_active);
CREATE INDEX idx_rate_cards_effective_date ON carrier_rate_cards(effective_date);

COMMENT ON TABLE carrier_rate_cards IS 'Stores carrier pricing rates by weight and zone';
COMMENT ON COLUMN carrier_rate_cards.version IS 'Version number for rate card history tracking';

-- ============================================================================
-- Carrier Postal Zones Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS carrier_postal_zones (
    id SERIAL PRIMARY KEY,
    carrier_id INTEGER NOT NULL REFERENCES carriers(id) ON DELETE CASCADE,
    zone_id VARCHAR(50) NOT NULL,
    country_code VARCHAR(2),
    postal_codes TEXT[], -- Array of postal codes
    postal_code_ranges JSONB, -- For ranges like "75000-75999"
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(carrier_id, zone_id)
);

CREATE INDEX idx_postal_zones_carrier ON carrier_postal_zones(carrier_id);
CREATE INDEX idx_postal_zones_country ON carrier_postal_zones(country_code);
CREATE INDEX idx_postal_zones_active ON carrier_postal_zones(is_active);
CREATE INDEX idx_postal_zones_codes ON carrier_postal_zones USING GIN (postal_codes);

COMMENT ON TABLE carrier_postal_zones IS 'Defines postal code zones for carrier pricing';
COMMENT ON COLUMN carrier_postal_zones.postal_codes IS 'Array of individual postal codes in this zone';
COMMENT ON COLUMN carrier_postal_zones.postal_code_ranges IS 'JSON array of postal code ranges';

-- ============================================================================
-- Carrier Surcharges Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS carrier_surcharges (
    id SERIAL PRIMARY KEY,
    carrier_id INTEGER NOT NULL REFERENCES carriers(id) ON DELETE CASCADE,
    surcharge_type VARCHAR(50) NOT NULL CHECK (surcharge_type IN (
        'fuel', 'residential', 'oversized', 'remote_area', 'dangerous_goods',
        'signature_required', 'saturday_delivery', 'peak_season', 'other'
    )),
    value_type VARCHAR(20) NOT NULL CHECK (value_type IN ('percentage', 'fixed', 'per_kg', 'per_package')),
    value DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    min_charge DECIMAL(10, 2),
    max_charge DECIMAL(10, 2),
    applies_to_zones TEXT[], -- Array of zone IDs
    effective_date DATE NOT NULL DEFAULT CURRENT_DATE,
    expiry_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(carrier_id, surcharge_type, effective_date)
);

CREATE INDEX idx_surcharges_carrier ON carrier_surcharges(carrier_id);
CREATE INDEX idx_surcharges_type ON carrier_surcharges(surcharge_type);
CREATE INDEX idx_surcharges_active ON carrier_surcharges(is_active);
CREATE INDEX idx_surcharges_effective_date ON carrier_surcharges(effective_date);

COMMENT ON TABLE carrier_surcharges IS 'Stores carrier surcharges and additional fees';
COMMENT ON COLUMN carrier_surcharges.value_type IS 'How the surcharge is calculated';

-- ============================================================================
-- Carrier Service Levels Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS carrier_service_levels (
    id SERIAL PRIMARY KEY,
    carrier_id INTEGER NOT NULL REFERENCES carriers(id) ON DELETE CASCADE,
    service_code VARCHAR(50) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    description TEXT,
    price_modifier DECIMAL(10, 2) DEFAULT 0, -- Additional cost or discount
    price_modifier_type VARCHAR(20) DEFAULT 'fixed' CHECK (price_modifier_type IN ('fixed', 'percentage')),
    estimated_transit_days INTEGER,
    guaranteed_delivery BOOLEAN DEFAULT FALSE,
    tracking_included BOOLEAN DEFAULT TRUE,
    signature_required BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(carrier_id, service_code)
);

CREATE INDEX idx_service_levels_carrier ON carrier_service_levels(carrier_id);
CREATE INDEX idx_service_levels_active ON carrier_service_levels(is_active);

COMMENT ON TABLE carrier_service_levels IS 'Defines available service levels for each carrier';
COMMENT ON COLUMN carrier_service_levels.price_modifier IS 'Additional cost or discount for this service level';

-- ============================================================================
-- Shipments Table (Enhanced)
-- ============================================================================
CREATE TABLE IF NOT EXISTS shipments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    carrier_id INTEGER REFERENCES carriers(id),
    tracking_number VARCHAR(100) UNIQUE,
    service_level VARCHAR(50),
    
    -- Origin and destination
    origin_address JSONB NOT NULL,
    destination_address JSONB NOT NULL,
    
    -- Package details
    weight DECIMAL(10, 2) NOT NULL,
    dimensions JSONB, -- {length, width, height, unit}
    dimensional_weight DECIMAL(10, 2),
    
    -- Pricing
    base_cost DECIMAL(10, 2),
    fuel_surcharge DECIMAL(10, 2),
    additional_surcharges JSONB,
    total_cost DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'EUR',
    
    -- Label information
    label_url TEXT,
    label_format VARCHAR(20),
    label_generated_at TIMESTAMP,
    
    -- Tracking
    status VARCHAR(50) DEFAULT 'pending',
    current_location TEXT,
    estimated_delivery DATE,
    actual_delivery_date TIMESTAMP,
    delivered_on_time BOOLEAN,
    actual_transit_days INTEGER,
    tracking_events JSONB,
    last_tracking_update TIMESTAMP,
    
    -- Performance
    customer_rating INTEGER CHECK (customer_rating BETWEEN 1 AND 5),
    customer_feedback TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shipments_order ON shipments(order_id);
CREATE INDEX idx_shipments_carrier ON shipments(carrier_id);
CREATE INDEX idx_shipments_tracking ON shipments(tracking_number);
CREATE INDEX idx_shipments_status ON shipments(status);
CREATE INDEX idx_shipments_created_at ON shipments(created_at);

COMMENT ON TABLE shipments IS 'Stores shipment information and tracking data';
COMMENT ON COLUMN shipments.dimensional_weight IS 'Calculated dimensional weight for pricing';
COMMENT ON COLUMN shipments.tracking_events IS 'Array of tracking events from carrier API';

-- ============================================================================
-- Shipment History Table (for analytics)
-- ============================================================================
CREATE TABLE IF NOT EXISTS shipment_history (
    id SERIAL PRIMARY KEY,
    shipment_id INTEGER REFERENCES shipments(id) ON DELETE CASCADE,
    carrier_code VARCHAR(50) NOT NULL,
    origin_country VARCHAR(2),
    destination_country VARCHAR(2),
    service_level VARCHAR(50),
    weight DECIMAL(10, 2),
    cost DECIMAL(10, 2),
    estimated_transit_days INTEGER,
    actual_transit_days INTEGER,
    delivered_on_time BOOLEAN,
    customer_rating INTEGER CHECK (customer_rating BETWEEN 1 AND 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shipment_history_carrier ON shipment_history(carrier_code);
CREATE INDEX idx_shipment_history_route ON shipment_history(origin_country, destination_country);
CREATE INDEX idx_shipment_history_created_at ON shipment_history(created_at);

COMMENT ON TABLE shipment_history IS 'Historical shipment data for carrier performance analysis';

-- ============================================================================
-- Rate Card Version History Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS rate_card_history (
    id SERIAL PRIMARY KEY,
    rate_card_id INTEGER REFERENCES carrier_rate_cards(id) ON DELETE CASCADE,
    carrier_id INTEGER NOT NULL,
    weight_min DECIMAL(10, 2) NOT NULL,
    weight_max DECIMAL(10, 2) NOT NULL,
    zone VARCHAR(50) NOT NULL,
    old_price DECIMAL(10, 2),
    new_price DECIMAL(10, 2) NOT NULL,
    change_percentage DECIMAL(5, 2),
    contract_id INTEGER REFERENCES carrier_contracts(id),
    changed_by INTEGER REFERENCES users(id),
    change_reason TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rate_history_rate_card ON rate_card_history(rate_card_id);
CREATE INDEX idx_rate_history_carrier ON rate_card_history(carrier_id);
CREATE INDEX idx_rate_history_changed_at ON rate_card_history(changed_at);

COMMENT ON TABLE rate_card_history IS 'Tracks changes to rate cards over time';
COMMENT ON COLUMN rate_card_history.change_percentage IS 'Percentage change from old to new price';

-- ============================================================================
-- Contract Parsing Jobs Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS contract_parsing_jobs (
    id SERIAL PRIMARY KEY,
    contract_id INTEGER REFERENCES carrier_contracts(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    parsed_items_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_parsing_jobs_contract ON contract_parsing_jobs(contract_id);
CREATE INDEX idx_parsing_jobs_status ON contract_parsing_jobs(status);

COMMENT ON TABLE contract_parsing_jobs IS 'Tracks AI parsing jobs for uploaded contracts';

-- ============================================================================
-- Functions and Triggers
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to all tables
CREATE TRIGGER update_carrier_contracts_updated_at
    BEFORE UPDATE ON carrier_contracts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_carrier_rate_cards_updated_at
    BEFORE UPDATE ON carrier_rate_cards
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_carrier_postal_zones_updated_at
    BEFORE UPDATE ON carrier_postal_zones
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_carrier_surcharges_updated_at
    BEFORE UPDATE ON carrier_surcharges
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_carrier_service_levels_updated_at
    BEFORE UPDATE ON carrier_service_levels
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shipments_updated_at
    BEFORE UPDATE ON shipments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to track rate card changes
CREATE OR REPLACE FUNCTION track_rate_card_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.price IS DISTINCT FROM NEW.price THEN
        INSERT INTO rate_card_history (
            rate_card_id, carrier_id, weight_min, weight_max, zone,
            old_price, new_price, change_percentage, contract_id
        ) VALUES (
            NEW.id, NEW.carrier_id, NEW.weight_min, NEW.weight_max, NEW.zone,
            OLD.price, NEW.price,
            CASE WHEN OLD.price > 0 THEN ((NEW.price - OLD.price) / OLD.price * 100) ELSE NULL END,
            NEW.contract_id
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER track_rate_card_changes_trigger
    AFTER UPDATE ON carrier_rate_cards
    FOR EACH ROW
    EXECUTE FUNCTION track_rate_card_changes();

-- Function to auto-expire contracts
CREATE OR REPLACE FUNCTION auto_expire_contracts()
RETURNS void AS $$
BEGIN
    UPDATE carrier_contracts
    SET status = 'expired'
    WHERE status = 'active'
    AND expiry_date IS NOT NULL
    AND expiry_date < CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate dimensional weight
CREATE OR REPLACE FUNCTION calculate_dimensional_weight(
    length_cm DECIMAL,
    width_cm DECIMAL,
    height_cm DECIMAL,
    divisor INTEGER DEFAULT 5000
)
RETURNS DECIMAL AS $$
BEGIN
    RETURN (length_cm * width_cm * height_cm) / divisor;
END;
$$ LANGUAGE plpgsql;

-- Function to get applicable rate for shipment
CREATE OR REPLACE FUNCTION get_applicable_rate(
    p_carrier_id INTEGER,
    p_weight DECIMAL,
    p_zone VARCHAR,
    p_service_level VARCHAR DEFAULT NULL
)
RETURNS DECIMAL AS $$
DECLARE
    v_rate DECIMAL;
BEGIN
    SELECT price INTO v_rate
    FROM carrier_rate_cards
    WHERE carrier_id = p_carrier_id
    AND p_weight >= weight_min
    AND p_weight <= weight_max
    AND zone = p_zone
    AND (service_level = p_service_level OR service_level IS NULL)
    AND is_active = TRUE
    AND effective_date <= CURRENT_DATE
    AND (expiry_date IS NULL OR expiry_date >= CURRENT_DATE)
    ORDER BY effective_date DESC
    LIMIT 1;
    
    RETURN v_rate;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Sample Data for Testing
-- ============================================================================

-- Insert sample carriers if not exists
INSERT INTO carriers (name, code, api_url, is_active) VALUES
('DPD', 'dpd', 'https://api.dpd.com/v1', TRUE),
('GLS', 'gls', 'https://api.gls-group.eu/v1', TRUE),
('Hermes', 'hermes', 'https://api.hermesworld.com/v1', TRUE),
('Colissimo', 'colissimo', 'https://ws.colissimo.fr/sls-ws', TRUE),
('Chronopost', 'chronopost', 'https://ws.chronopost.fr/shipping-cxf', TRUE),
('DHL Express', 'dhl', 'https://api-eu.dhl.com/parcel/de/shipping/v2', TRUE),
('UPS', 'ups', 'https://onlinetools.ups.com/api', TRUE),
('Colis Privé', 'colis_prive', 'https://api.colisprive.com/v1', TRUE)
ON CONFLICT (code) DO NOTHING;

-- ============================================================================
-- Views for Reporting
-- ============================================================================

-- View for active rate cards with carrier info
CREATE OR REPLACE VIEW v_active_rate_cards AS
SELECT 
    rc.id,
    c.name as carrier_name,
    c.code as carrier_code,
    rc.weight_min,
    rc.weight_max,
    rc.zone,
    rc.price,
    rc.currency,
    rc.service_level,
    rc.effective_date,
    rc.expiry_date,
    cc.contract_number
FROM carrier_rate_cards rc
JOIN carriers c ON rc.carrier_id = c.id
LEFT JOIN carrier_contracts cc ON rc.contract_id = cc.id
WHERE rc.is_active = TRUE
AND rc.effective_date <= CURRENT_DATE
AND (rc.expiry_date IS NULL OR rc.expiry_date >= CURRENT_DATE);

-- View for carrier performance metrics
CREATE OR REPLACE VIEW v_carrier_performance AS
SELECT 
    carrier_code,
    origin_country,
    destination_country,
    COUNT(*) as total_shipments,
    AVG(actual_transit_days) as avg_transit_days,
    AVG(CASE WHEN delivered_on_time THEN 1 ELSE 0 END) as on_time_rate,
    AVG(customer_rating) as avg_rating,
    AVG(cost) as avg_cost
FROM shipment_history
WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY carrier_code, origin_country, destination_country;

-- ============================================================================
-- Grants (adjust as needed for your security model)
-- ============================================================================

-- Grant permissions to application user
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO app_user;

-- ============================================================================
-- Migration Complete
-- ============================================================================

COMMENT ON SCHEMA public IS 'Migration 030: Carrier Contracts and Rate Cards Management - Completed';

