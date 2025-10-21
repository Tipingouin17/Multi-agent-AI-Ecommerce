-- Shipping Zones & Rates Migration
-- Supports geographic zone definition and flexible rate calculation

-- Shipping Zones Table
CREATE TABLE IF NOT EXISTS shipping_zones (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    enabled BOOLEAN DEFAULT true,
    countries TEXT[] DEFAULT ARRAY[]::TEXT[], -- ISO country codes
    regions TEXT[] DEFAULT ARRAY[]::TEXT[], -- State/province codes
    postal_codes TEXT[] DEFAULT ARRAY[]::TEXT[], -- Postal code ranges
    rate_method VARCHAR(50) DEFAULT 'flat', -- flat, weight_based, price_based, dimensional, table_rate
    base_rate DECIMAL(10, 2) DEFAULT 0,
    free_shipping_threshold DECIMAL(10, 2) DEFAULT 0,
    handling_fee DECIMAL(10, 2) DEFAULT 0,
    min_delivery_days INTEGER DEFAULT 3,
    max_delivery_days INTEGER DEFAULT 7,
    priority INTEGER DEFAULT 1, -- Lower number = higher priority
    rate_tiers JSONB, -- For weight/price-based calculations
    conditions JSONB, -- Additional conditions (min/max order value, weight, etc.)
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- Shipping Zone Carriers (many-to-many relationship)
CREATE TABLE IF NOT EXISTS shipping_zone_carriers (
    id SERIAL PRIMARY KEY,
    zone_id INTEGER REFERENCES shipping_zones(id) ON DELETE CASCADE,
    carrier_id INTEGER REFERENCES carriers(id) ON DELETE CASCADE,
    enabled BOOLEAN DEFAULT true,
    rate_adjustment_type VARCHAR(20) DEFAULT 'none', -- none, fixed, percentage
    rate_adjustment_value DECIMAL(10, 2) DEFAULT 0,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(zone_id, carrier_id)
);

-- Shipping Rate Cache (for performance optimization)
CREATE TABLE IF NOT EXISTS shipping_rate_cache (
    id SERIAL PRIMARY KEY,
    zone_id INTEGER REFERENCES shipping_zones(id) ON DELETE CASCADE,
    carrier_id INTEGER REFERENCES carriers(id),
    country_code VARCHAR(2),
    postal_code VARCHAR(20),
    weight DECIMAL(10, 2),
    order_value DECIMAL(10, 2),
    calculated_rate DECIMAL(10, 2),
    delivery_estimate_min INTEGER,
    delivery_estimate_max INTEGER,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    metadata JSONB
);

-- Shipping Zone Exclusions (products/categories that cannot ship to certain zones)
CREATE TABLE IF NOT EXISTS shipping_zone_exclusions (
    id SERIAL PRIMARY KEY,
    zone_id INTEGER REFERENCES shipping_zones(id) ON DELETE CASCADE,
    exclusion_type VARCHAR(50) NOT NULL, -- product, category, brand
    exclusion_id INTEGER NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shipping Surcharges (additional fees for specific conditions)
CREATE TABLE IF NOT EXISTS shipping_surcharges (
    id SERIAL PRIMARY KEY,
    zone_id INTEGER REFERENCES shipping_zones(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    enabled BOOLEAN DEFAULT true,
    surcharge_type VARCHAR(50) NOT NULL, -- fuel, remote_area, oversized, hazmat, residential
    calculation_method VARCHAR(50) DEFAULT 'fixed', -- fixed, percentage
    amount DECIMAL(10, 2) NOT NULL,
    conditions JSONB, -- When to apply this surcharge
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shipping Holidays (dates when shipping is not available)
CREATE TABLE IF NOT EXISTS shipping_holidays (
    id SERIAL PRIMARY KEY,
    zone_id INTEGER REFERENCES shipping_zones(id) ON DELETE CASCADE,
    holiday_name VARCHAR(255) NOT NULL,
    holiday_date DATE NOT NULL,
    affects_pickup BOOLEAN DEFAULT true,
    affects_delivery BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shipping Rate History (for auditing and analysis)
CREATE TABLE IF NOT EXISTS shipping_rate_history (
    id SERIAL PRIMARY KEY,
    zone_id INTEGER REFERENCES shipping_zones(id),
    order_id INTEGER REFERENCES orders(id),
    carrier_id INTEGER REFERENCES carriers(id),
    country_code VARCHAR(2),
    postal_code VARCHAR(20),
    weight DECIMAL(10, 2),
    dimensions JSONB, -- length, width, height
    order_value DECIMAL(10, 2),
    base_rate DECIMAL(10, 2),
    surcharges JSONB,
    discounts JSONB,
    final_rate DECIMAL(10, 2),
    calculation_method VARCHAR(50),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_shipping_zones_enabled ON shipping_zones(enabled);
CREATE INDEX idx_shipping_zones_priority ON shipping_zones(priority);
CREATE INDEX idx_shipping_zones_countries ON shipping_zones USING GIN(countries);
CREATE INDEX idx_shipping_zone_carriers_zone ON shipping_zone_carriers(zone_id);
CREATE INDEX idx_shipping_zone_carriers_carrier ON shipping_zone_carriers(carrier_id);
CREATE INDEX idx_shipping_rate_cache_zone ON shipping_rate_cache(zone_id);
CREATE INDEX idx_shipping_rate_cache_country ON shipping_rate_cache(country_code);
CREATE INDEX idx_shipping_rate_cache_expires ON shipping_rate_cache(expires_at);
CREATE INDEX idx_shipping_zone_exclusions_zone ON shipping_zone_exclusions(zone_id);
CREATE INDEX idx_shipping_surcharges_zone ON shipping_surcharges(zone_id);
CREATE INDEX idx_shipping_holidays_zone_date ON shipping_holidays(zone_id, holiday_date);
CREATE INDEX idx_shipping_rate_history_zone ON shipping_rate_history(zone_id);
CREATE INDEX idx_shipping_rate_history_order ON shipping_rate_history(order_id);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_shipping_zone_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER shipping_zones_updated_at
    BEFORE UPDATE ON shipping_zones
    FOR EACH ROW
    EXECUTE FUNCTION update_shipping_zone_timestamp();

CREATE TRIGGER shipping_surcharges_updated_at
    BEFORE UPDATE ON shipping_surcharges
    FOR EACH ROW
    EXECUTE FUNCTION update_shipping_zone_timestamp();

-- Insert sample shipping zones
INSERT INTO shipping_zones (
    name, description, enabled, countries, rate_method,
    base_rate, free_shipping_threshold, handling_fee,
    min_delivery_days, max_delivery_days, priority,
    rate_tiers, conditions
) VALUES
(
    'Domestic USA - Standard',
    'Standard shipping for United States',
    true,
    ARRAY['US'],
    'weight_based',
    5.99,
    75.00,
    2.00,
    3,
    7,
    1,
    '[
        {"min": 0, "max": 5, "rate": 5.99},
        {"min": 5, "max": 10, "rate": 8.99},
        {"min": 10, "max": 20, "rate": 12.99},
        {"min": 20, "max": 999999, "rate": 19.99}
    ]'::jsonb,
    '{
        "min_order_value": 0,
        "max_order_value": 999999,
        "min_weight": 0,
        "max_weight": 150
    }'::jsonb
),
(
    'Domestic USA - Express',
    'Express shipping for United States',
    true,
    ARRAY['US'],
    'weight_based',
    12.99,
    150.00,
    3.00,
    1,
    2,
    2,
    '[
        {"min": 0, "max": 5, "rate": 12.99},
        {"min": 5, "max": 10, "rate": 16.99},
        {"min": 10, "max": 20, "rate": 24.99},
        {"min": 20, "max": 999999, "rate": 34.99}
    ]'::jsonb,
    '{
        "min_order_value": 0,
        "max_order_value": 999999,
        "min_weight": 0,
        "max_weight": 70
    }'::jsonb
),
(
    'Canada',
    'Shipping to Canada',
    true,
    ARRAY['CA'],
    'weight_based',
    9.99,
    100.00,
    3.00,
    5,
    10,
    3,
    '[
        {"min": 0, "max": 5, "rate": 9.99},
        {"min": 5, "max": 10, "rate": 14.99},
        {"min": 10, "max": 20, "rate": 22.99},
        {"min": 20, "max": 999999, "rate": 34.99}
    ]'::jsonb,
    '{
        "min_order_value": 0,
        "max_order_value": 999999,
        "min_weight": 0,
        "max_weight": 150
    }'::jsonb
),
(
    'Europe',
    'Shipping to European countries',
    true,
    ARRAY['GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'SE', 'NO', 'DK'],
    'weight_based',
    15.99,
    150.00,
    5.00,
    7,
    14,
    4,
    '[
        {"min": 0, "max": 5, "rate": 15.99},
        {"min": 5, "max": 10, "rate": 24.99},
        {"min": 10, "max": 20, "rate": 39.99},
        {"min": 20, "max": 999999, "rate": 59.99}
    ]'::jsonb,
    '{
        "min_order_value": 0,
        "max_order_value": 999999,
        "min_weight": 0,
        "max_weight": 100
    }'::jsonb
),
(
    'Asia Pacific',
    'Shipping to Asia Pacific region',
    true,
    ARRAY['AU', 'JP', 'CN', 'SG', 'KR', 'NZ'],
    'weight_based',
    19.99,
    200.00,
    6.00,
    10,
    21,
    5,
    '[
        {"min": 0, "max": 5, "rate": 19.99},
        {"min": 5, "max": 10, "rate": 29.99},
        {"min": 10, "max": 20, "rate": 49.99},
        {"min": 20, "max": 999999, "rate": 79.99}
    ]'::jsonb,
    '{
        "min_order_value": 0,
        "max_order_value": 999999,
        "min_weight": 0,
        "max_weight": 100
    }'::jsonb
);

-- Insert sample surcharges
INSERT INTO shipping_surcharges (
    zone_id, name, description, enabled, surcharge_type,
    calculation_method, amount, conditions
) VALUES
(
    1,
    'Fuel Surcharge',
    'Additional fee for fuel costs',
    true,
    'fuel',
    'percentage',
    3.5,
    '{"applies_to_all": true}'::jsonb
),
(
    1,
    'Remote Area Fee',
    'Additional fee for remote delivery locations',
    true,
    'remote_area',
    'fixed',
    5.00,
    '{"postal_code_patterns": ["99*", "96*"]}'::jsonb
),
(
    1,
    'Oversized Package Fee',
    'Additional fee for oversized packages',
    true,
    'oversized',
    'fixed',
    15.00,
    '{"min_dimension_sum": 96, "min_longest_side": 48}'::jsonb
);

-- Insert sample holidays
INSERT INTO shipping_holidays (
    zone_id, holiday_name, holiday_date, affects_pickup, affects_delivery
) VALUES
(1, 'New Year''s Day', '2025-01-01', true, true),
(1, 'Independence Day', '2025-07-04', true, true),
(1, 'Thanksgiving', '2025-11-27', true, true),
(1, 'Christmas Day', '2025-12-25', true, true);

-- Comments for documentation
COMMENT ON TABLE shipping_zones IS 'Defines geographic shipping zones with rate calculation methods';
COMMENT ON TABLE shipping_zone_carriers IS 'Links carriers to zones with specific configurations';
COMMENT ON TABLE shipping_rate_cache IS 'Caches calculated shipping rates for performance';
COMMENT ON TABLE shipping_zone_exclusions IS 'Products/categories that cannot ship to certain zones';
COMMENT ON TABLE shipping_surcharges IS 'Additional fees applied under specific conditions';
COMMENT ON TABLE shipping_holidays IS 'Dates when shipping services are not available';
COMMENT ON TABLE shipping_rate_history IS 'Historical record of shipping rate calculations';

