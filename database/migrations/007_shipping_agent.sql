-- =====================================================
-- SHIPPING AGENT DATABASE MIGRATION
-- =====================================================
-- This migration creates comprehensive shipping management tables
-- for carriers, rates, shipments, tracking, and AI-powered carrier selection.

-- =====================================================
-- 1. CARRIERS
-- =====================================================

CREATE TABLE IF NOT EXISTS carriers (
    carrier_id SERIAL PRIMARY KEY,
    carrier_name VARCHAR(100) UNIQUE NOT NULL,
    carrier_code VARCHAR(50) UNIQUE NOT NULL,
    carrier_type VARCHAR(50) NOT NULL, -- 'standard', 'express', 'freight', 'local'
    is_active BOOLEAN DEFAULT true,
    
    -- Service coverage
    service_areas TEXT[] DEFAULT ARRAY['local'], -- 'local', 'national', 'international', 'europe'
    supported_countries TEXT[] DEFAULT ARRAY['FR'],
    
    -- Capabilities
    supports_tracking BOOLEAN DEFAULT true,
    supports_insurance BOOLEAN DEFAULT false,
    supports_signature BOOLEAN DEFAULT false,
    supports_dangerous_goods BOOLEAN DEFAULT false,
    
    -- Performance metrics (updated by AI)
    on_time_delivery_rate DECIMAL(5, 2) DEFAULT 95.00, -- percentage
    average_delivery_days DECIMAL(5, 2),
    customer_satisfaction_score DECIMAL(3, 2) DEFAULT 4.00, -- out of 5
    
    -- Contact information
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    api_endpoint VARCHAR(500),
    api_key_encrypted VARCHAR(500),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_carriers_active ON carriers(is_active);
CREATE INDEX idx_carriers_code ON carriers(carrier_code);
CREATE INDEX idx_carriers_type ON carriers(carrier_type);

COMMENT ON TABLE carriers IS 'Shipping carrier configurations';

-- =====================================================
-- 2. CARRIER SERVICES
-- =====================================================

CREATE TABLE IF NOT EXISTS carrier_services (
    service_id SERIAL PRIMARY KEY,
    carrier_id INTEGER NOT NULL REFERENCES carriers(carrier_id),
    service_name VARCHAR(100) NOT NULL,
    service_code VARCHAR(50) NOT NULL,
    service_type VARCHAR(50) NOT NULL, -- 'standard', 'express', 'overnight', 'economy'
    
    -- Service characteristics
    estimated_delivery_days_min INTEGER,
    estimated_delivery_days_max INTEGER,
    cutoff_time TIME, -- order cutoff time for same-day processing
    
    -- Package constraints
    max_weight_kg DECIMAL(10, 2),
    max_length_cm DECIMAL(10, 2),
    max_width_cm DECIMAL(10, 2),
    max_height_cm DECIMAL(10, 2),
    max_value_amount DECIMAL(10, 2),
    
    -- Service features
    includes_tracking BOOLEAN DEFAULT true,
    includes_insurance BOOLEAN DEFAULT false,
    requires_signature BOOLEAN DEFAULT false,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(carrier_id, service_code)
);

CREATE INDEX idx_carrier_services_carrier ON carrier_services(carrier_id);
CREATE INDEX idx_carrier_services_active ON carrier_services(is_active);
CREATE INDEX idx_carrier_services_type ON carrier_services(service_type);

COMMENT ON TABLE carrier_services IS 'Carrier service offerings';

-- =====================================================
-- 3. SHIPPING RATES
-- =====================================================

CREATE TABLE IF NOT EXISTS shipping_rates (
    rate_id SERIAL PRIMARY KEY,
    carrier_id INTEGER NOT NULL REFERENCES carriers(carrier_id),
    service_id INTEGER REFERENCES carrier_services(service_id),
    
    -- Geographic scope
    origin_country VARCHAR(2),
    origin_postal_code VARCHAR(20),
    destination_country VARCHAR(2) NOT NULL,
    destination_postal_code VARCHAR(20),
    destination_zone VARCHAR(50), -- carrier-specific zone
    
    -- Package constraints
    weight_min_kg DECIMAL(10, 2) DEFAULT 0.00,
    weight_max_kg DECIMAL(10, 2),
    
    -- Pricing
    base_rate DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    rate_per_kg DECIMAL(10, 2) DEFAULT 0.00,
    fuel_surcharge_percent DECIMAL(5, 2) DEFAULT 0.00,
    
    -- Additional fees
    residential_surcharge DECIMAL(10, 2) DEFAULT 0.00,
    remote_area_surcharge DECIMAL(10, 2) DEFAULT 0.00,
    dangerous_goods_surcharge DECIMAL(10, 2) DEFAULT 0.00,
    insurance_rate_percent DECIMAL(5, 2) DEFAULT 0.00,
    
    -- Validity
    effective_date DATE NOT NULL,
    expiry_date DATE,
    
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shipping_rates_carrier ON shipping_rates(carrier_id);
CREATE INDEX idx_shipping_rates_service ON shipping_rates(service_id);
CREATE INDEX idx_shipping_rates_destination ON shipping_rates(destination_country, destination_postal_code);
CREATE INDEX idx_shipping_rates_active ON shipping_rates(is_active);
CREATE INDEX idx_shipping_rates_effective ON shipping_rates(effective_date, expiry_date);

COMMENT ON TABLE shipping_rates IS 'Carrier shipping rates and pricing';

-- =====================================================
-- 4. SHIPMENTS
-- =====================================================

CREATE TABLE IF NOT EXISTS shipments (
    shipment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id VARCHAR(100) NOT NULL,
    carrier_id INTEGER NOT NULL REFERENCES carriers(carrier_id),
    service_id INTEGER REFERENCES carrier_services(service_id),
    
    -- Shipment details
    tracking_number VARCHAR(200) UNIQUE,
    shipment_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'label_created', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered', 'failed', 'returned'
    
    -- Package information
    package_weight_kg DECIMAL(10, 2) NOT NULL,
    package_length_cm DECIMAL(10, 2),
    package_width_cm DECIMAL(10, 2),
    package_height_cm DECIMAL(10, 2),
    package_value_amount DECIMAL(10, 2),
    is_fragile BOOLEAN DEFAULT false,
    is_dangerous_goods BOOLEAN DEFAULT false,
    
    -- Addresses
    origin_address JSONB NOT NULL,
    destination_address JSONB NOT NULL,
    
    -- Shipping costs
    shipping_cost DECIMAL(10, 2) NOT NULL,
    insurance_cost DECIMAL(10, 2) DEFAULT 0.00,
    total_cost DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    
    -- Delivery information
    estimated_delivery_date DATE,
    actual_delivery_date DATE,
    delivery_signature VARCHAR(200),
    delivery_notes TEXT,
    
    -- Label information
    label_url VARCHAR(500),
    label_format VARCHAR(20), -- 'PDF', 'PNG', 'ZPL'
    
    -- AI selection metadata
    ai_selection_score DECIMAL(5, 2), -- confidence score of AI selection
    ai_selection_reason TEXT,
    alternative_carriers JSONB DEFAULT '[]', -- other carriers considered
    
    -- Timestamps
    label_created_at TIMESTAMP,
    picked_up_at TIMESTAMP,
    delivered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shipments_order ON shipments(order_id);
CREATE INDEX idx_shipments_carrier ON shipments(carrier_id);
CREATE INDEX idx_shipments_tracking ON shipments(tracking_number);
CREATE INDEX idx_shipments_status ON shipments(shipment_status);
CREATE INDEX idx_shipments_created ON shipments(created_at DESC);
CREATE INDEX idx_shipments_delivery_date ON shipments(estimated_delivery_date);

COMMENT ON TABLE shipments IS 'Shipment records with AI carrier selection';

-- =====================================================
-- 5. TRACKING EVENTS
-- =====================================================

CREATE TABLE IF NOT EXISTS tracking_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_id UUID NOT NULL REFERENCES shipments(shipment_id),
    
    -- Event details
    event_type VARCHAR(50) NOT NULL, -- 'label_created', 'picked_up', 'in_transit', 'customs', 'out_for_delivery', 'delivered', 'exception'
    event_status VARCHAR(50) NOT NULL,
    event_description TEXT,
    
    -- Location
    location_city VARCHAR(100),
    location_state VARCHAR(100),
    location_country VARCHAR(2),
    location_postal_code VARCHAR(20),
    location_coordinates JSONB, -- {lat, lon}
    
    -- Carrier data
    carrier_event_code VARCHAR(50),
    carrier_event_data JSONB DEFAULT '{}',
    
    -- Timestamp
    event_timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tracking_events_shipment ON tracking_events(shipment_id);
CREATE INDEX idx_tracking_events_type ON tracking_events(event_type);
CREATE INDEX idx_tracking_events_timestamp ON tracking_events(event_timestamp DESC);

COMMENT ON TABLE tracking_events IS 'Shipment tracking events';

-- =====================================================
-- 6. CARRIER PERFORMANCE HISTORY
-- =====================================================

CREATE TABLE IF NOT EXISTS carrier_performance_history (
    performance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    carrier_id INTEGER NOT NULL REFERENCES carriers(carrier_id),
    service_id INTEGER REFERENCES carrier_services(service_id),
    
    -- Time period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Performance metrics
    total_shipments INTEGER DEFAULT 0,
    on_time_deliveries INTEGER DEFAULT 0,
    late_deliveries INTEGER DEFAULT 0,
    failed_deliveries INTEGER DEFAULT 0,
    
    -- Calculated metrics
    on_time_rate DECIMAL(5, 2),
    average_delivery_days DECIMAL(5, 2),
    average_cost DECIMAL(10, 2),
    
    -- Customer feedback
    total_ratings INTEGER DEFAULT 0,
    average_rating DECIMAL(3, 2),
    
    -- AI learning data
    ai_recommendation_count INTEGER DEFAULT 0,
    ai_recommendation_success_rate DECIMAL(5, 2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_carrier_performance_carrier ON carrier_performance_history(carrier_id);
CREATE INDEX idx_carrier_performance_period ON carrier_performance_history(period_start, period_end);

COMMENT ON TABLE carrier_performance_history IS 'Historical carrier performance for AI learning';

-- =====================================================
-- 7. AI CARRIER SELECTION LOG
-- =====================================================

CREATE TABLE IF NOT EXISTS ai_carrier_selection_log (
    selection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id VARCHAR(100) NOT NULL,
    shipment_id UUID REFERENCES shipments(shipment_id),
    
    -- Input parameters
    package_characteristics JSONB NOT NULL, -- weight, dimensions, fragility, dangerous_goods
    origin_location JSONB NOT NULL,
    destination_location JSONB NOT NULL,
    required_delivery_date DATE,
    
    -- AI decision
    selected_carrier_id INTEGER REFERENCES carriers(carrier_id),
    selected_service_id INTEGER REFERENCES carrier_services(service_id),
    selection_confidence DECIMAL(5, 2), -- 0-100
    selection_reasoning TEXT,
    
    -- Alternative options considered
    alternatives_evaluated JSONB DEFAULT '[]', -- [{carrier_id, score, reason}]
    
    -- Decision factors
    on_time_weight DECIMAL(5, 2) DEFAULT 70.00, -- importance of on-time delivery
    cost_weight DECIMAL(5, 2) DEFAULT 30.00, -- importance of cost
    
    -- Outcome (updated after delivery)
    actual_on_time BOOLEAN,
    actual_delivery_days INTEGER,
    actual_cost DECIMAL(10, 2),
    customer_satisfaction INTEGER, -- 1-5
    
    -- AI learning
    feedback_incorporated BOOLEAN DEFAULT false,
    model_version VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ai_selection_order ON ai_carrier_selection_log(order_id);
CREATE INDEX idx_ai_selection_shipment ON ai_carrier_selection_log(shipment_id);
CREATE INDEX idx_ai_selection_carrier ON ai_carrier_selection_log(selected_carrier_id);
CREATE INDEX idx_ai_selection_created ON ai_carrier_selection_log(created_at DESC);

COMMENT ON TABLE ai_carrier_selection_log IS 'AI carrier selection decisions and outcomes for learning';

-- =====================================================
-- MATERIALIZED VIEWS
-- =====================================================

-- Carrier Performance Summary
CREATE MATERIALIZED VIEW IF NOT EXISTS carrier_performance_summary AS
SELECT 
    c.carrier_id,
    c.carrier_name,
    c.carrier_code,
    COUNT(DISTINCT s.shipment_id) as total_shipments,
    COUNT(DISTINCT CASE WHEN s.shipment_status = 'delivered' THEN s.shipment_id END) as delivered_shipments,
    COUNT(DISTINCT CASE WHEN s.actual_delivery_date <= s.estimated_delivery_date THEN s.shipment_id END) as on_time_deliveries,
    ROUND(COUNT(DISTINCT CASE WHEN s.actual_delivery_date <= s.estimated_delivery_date THEN s.shipment_id END)::numeric / 
          NULLIF(COUNT(DISTINCT CASE WHEN s.shipment_status = 'delivered' THEN s.shipment_id END), 0) * 100, 2) as on_time_rate,
    AVG(CASE WHEN s.delivered_at IS NOT NULL THEN 
        EXTRACT(EPOCH FROM (s.delivered_at - s.created_at))/86400 END) as avg_delivery_days,
    AVG(s.total_cost) as avg_cost,
    c.on_time_delivery_rate as target_on_time_rate,
    c.customer_satisfaction_score
FROM carriers c
LEFT JOIN shipments s ON c.carrier_id = s.carrier_id
GROUP BY c.carrier_id, c.carrier_name, c.carrier_code, c.on_time_delivery_rate, c.customer_satisfaction_score;

CREATE UNIQUE INDEX idx_carrier_performance_summary_carrier ON carrier_performance_summary(carrier_id);

COMMENT ON MATERIALIZED VIEW carrier_performance_summary IS 'Real-time carrier performance metrics';

-- AI Selection Performance
CREATE MATERIALIZED VIEW IF NOT EXISTS ai_selection_performance AS
SELECT 
    DATE_TRUNC('week', created_at) as week,
    COUNT(*) as total_selections,
    AVG(selection_confidence) as avg_confidence,
    COUNT(CASE WHEN actual_on_time = true THEN 1 END) as successful_predictions,
    ROUND(COUNT(CASE WHEN actual_on_time = true THEN 1 END)::numeric / 
          NULLIF(COUNT(CASE WHEN actual_on_time IS NOT NULL THEN 1 END), 0) * 100, 2) as prediction_accuracy,
    AVG(CASE WHEN actual_on_time IS NOT NULL THEN selection_confidence END) as avg_confidence_with_outcome
FROM ai_carrier_selection_log
GROUP BY DATE_TRUNC('week', created_at)
ORDER BY week DESC;

CREATE UNIQUE INDEX idx_ai_selection_performance_week ON ai_selection_performance(week);

COMMENT ON MATERIALIZED VIEW ai_selection_performance IS 'AI carrier selection accuracy over time';

-- =====================================================
-- TRIGGERS
-- =====================================================

CREATE OR REPLACE FUNCTION update_shipping_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_carriers_timestamp
    BEFORE UPDATE ON carriers
    FOR EACH ROW
    EXECUTE FUNCTION update_shipping_timestamp();

CREATE TRIGGER trigger_update_carrier_services_timestamp
    BEFORE UPDATE ON carrier_services
    FOR EACH ROW
    EXECUTE FUNCTION update_shipping_timestamp();

CREATE TRIGGER trigger_update_shipping_rates_timestamp
    BEFORE UPDATE ON shipping_rates
    FOR EACH ROW
    EXECUTE FUNCTION update_shipping_timestamp();

CREATE TRIGGER trigger_update_shipments_timestamp
    BEFORE UPDATE ON shipments
    FOR EACH ROW
    EXECUTE FUNCTION update_shipping_timestamp();

CREATE TRIGGER trigger_update_ai_selection_timestamp
    BEFORE UPDATE ON ai_carrier_selection_log
    FOR EACH ROW
    EXECUTE FUNCTION update_shipping_timestamp();

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to refresh shipping views
CREATE OR REPLACE FUNCTION refresh_shipping_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY carrier_performance_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY ai_selection_performance;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_shipping_views() IS 'Refresh shipping materialized views';

-- =====================================================
-- INITIAL DATA
-- =====================================================

-- Insert default carriers
INSERT INTO carriers (carrier_name, carrier_code, carrier_type, service_areas, supported_countries, on_time_delivery_rate, average_delivery_days)
VALUES 
    ('Colis Privé', 'COLISPRIVE', 'standard', ARRAY['local', 'national'], ARRAY['FR'], 92.5, 2.5),
    ('UPS', 'UPS', 'express', ARRAY['local', 'national', 'international', 'europe'], ARRAY['FR', 'DE', 'ES', 'IT', 'GB'], 95.0, 2.0),
    ('Chronopost', 'CHRONOPOST', 'express', ARRAY['local', 'national', 'europe'], ARRAY['FR', 'BE', 'LU', 'CH'], 96.0, 1.5),
    ('Colissimo', 'COLISSIMO', 'standard', ARRAY['local', 'national', 'international'], ARRAY['FR'], 93.0, 3.0)
ON CONFLICT (carrier_code) DO NOTHING;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

COMMENT ON SCHEMA public IS 'Shipping Agent migration 007 completed successfully';

