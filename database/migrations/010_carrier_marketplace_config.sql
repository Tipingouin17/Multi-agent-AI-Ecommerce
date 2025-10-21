-- Migration: 010_carrier_marketplace_config
-- Description: Add carrier and marketplace configuration tables with pricing
-- Date: 2025-10-21
-- Database: PostgreSQL

-- ============================================================================
-- Carrier Configuration Tables
-- ============================================================================

-- Carriers master table
CREATE TABLE IF NOT EXISTS carriers (
    carrier_id SERIAL PRIMARY KEY,
    carrier_code VARCHAR(50) UNIQUE NOT NULL,
    carrier_name VARCHAR(255) NOT NULL,
    api_url VARCHAR(500),
    api_key_encrypted TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    supports_tracking BOOLEAN DEFAULT TRUE,
    supports_label_generation BOOLEAN DEFAULT TRUE,
    average_on_time_rate DECIMAL(5,4) DEFAULT 0.95,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_carriers_code ON carriers(carrier_code);
CREATE INDEX IF NOT EXISTS idx_carriers_active ON carriers(is_active);

-- Carrier service levels
CREATE TABLE IF NOT EXISTS carrier_services (
    service_id SERIAL PRIMARY KEY,
    carrier_id INTEGER NOT NULL REFERENCES carriers(carrier_id) ON DELETE CASCADE,
    service_code VARCHAR(50) NOT NULL,
    service_name VARCHAR(255) NOT NULL,
    service_level VARCHAR(50) NOT NULL, -- standard, express, overnight, economy
    estimated_transit_days INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(carrier_id, service_code)
);

CREATE INDEX IF NOT EXISTS idx_carrier_services_carrier ON carrier_services(carrier_id);
CREATE INDEX IF NOT EXISTS idx_carrier_services_level ON carrier_services(service_level);

-- Carrier pricing by destination
CREATE TABLE IF NOT EXISTS carrier_pricing (
    pricing_id SERIAL PRIMARY KEY,
    carrier_id INTEGER NOT NULL REFERENCES carriers(carrier_id) ON DELETE CASCADE,
    service_id INTEGER REFERENCES carrier_services(service_id) ON DELETE CASCADE,
    origin_country VARCHAR(2), -- ISO 2-letter code, NULL for any
    destination_country VARCHAR(2) NOT NULL, -- ISO 2-letter code
    destination_zone VARCHAR(50), -- EU, International, Domestic, etc.
    weight_min DECIMAL(10,3) DEFAULT 0, -- in kg
    weight_max DECIMAL(10,3), -- in kg, NULL for unlimited
    base_price DECIMAL(10,2) NOT NULL,
    price_per_kg DECIMAL(10,2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'EUR',
    valid_from DATE DEFAULT CURRENT_DATE,
    valid_until DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_carrier_pricing_carrier ON carrier_pricing(carrier_id);
CREATE INDEX IF NOT EXISTS idx_carrier_pricing_destination ON carrier_pricing(destination_country);
CREATE INDEX IF NOT EXISTS idx_carrier_pricing_active ON carrier_pricing(is_active);
CREATE INDEX IF NOT EXISTS idx_carrier_pricing_dates ON carrier_pricing(valid_from, valid_until);

-- Carrier surcharges (fuel, remote area, oversized, etc.)
CREATE TABLE IF NOT EXISTS carrier_surcharges (
    surcharge_id SERIAL PRIMARY KEY,
    carrier_id INTEGER NOT NULL REFERENCES carriers(carrier_id) ON DELETE CASCADE,
    surcharge_type VARCHAR(50) NOT NULL, -- fuel, remote_area, oversized, dangerous_goods
    surcharge_name VARCHAR(255) NOT NULL,
    surcharge_amount DECIMAL(10,2),
    surcharge_percentage DECIMAL(5,2), -- percentage of base price
    applies_to_countries VARCHAR(2)[], -- array of country codes, NULL for all
    applies_to_postal_codes TEXT[], -- array of postal code patterns
    is_active BOOLEAN DEFAULT TRUE,
    valid_from DATE DEFAULT CURRENT_DATE,
    valid_until DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_carrier_surcharges_carrier ON carrier_surcharges(carrier_id);
CREATE INDEX IF NOT EXISTS idx_carrier_surcharges_type ON carrier_surcharges(surcharge_type);

-- Carrier performance tracking
CREATE TABLE IF NOT EXISTS carrier_performance (
    performance_id SERIAL PRIMARY KEY,
    carrier_id INTEGER NOT NULL REFERENCES carriers(carrier_id) ON DELETE CASCADE,
    tracking_number VARCHAR(255),
    origin_country VARCHAR(2),
    destination_country VARCHAR(2),
    service_level VARCHAR(50),
    estimated_delivery_date DATE,
    actual_delivery_date DATE,
    was_on_time BOOLEAN,
    transit_days INTEGER,
    cost DECIMAL(10,2),
    customer_rating INTEGER, -- 1-5
    had_issues BOOLEAN DEFAULT FALSE,
    issue_description TEXT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_carrier_performance_carrier ON carrier_performance(carrier_id);
CREATE INDEX IF NOT EXISTS idx_carrier_performance_dates ON carrier_performance(actual_delivery_date);
CREATE INDEX IF NOT EXISTS idx_carrier_performance_on_time ON carrier_performance(was_on_time);

-- Carrier price list uploads (for tracking uploaded files)
CREATE TABLE IF NOT EXISTS carrier_price_uploads (
    upload_id SERIAL PRIMARY KEY,
    carrier_id INTEGER NOT NULL REFERENCES carriers(carrier_id) ON DELETE CASCADE,
    file_name VARCHAR(500) NOT NULL,
    file_url TEXT NOT NULL,
    file_type VARCHAR(50), -- csv, excel, pdf
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by VARCHAR(255),
    processing_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    records_imported INTEGER DEFAULT 0,
    error_message TEXT,
    processed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_carrier_uploads_carrier ON carrier_price_uploads(carrier_id);
CREATE INDEX IF NOT EXISTS idx_carrier_uploads_status ON carrier_price_uploads(processing_status);

-- ============================================================================
-- Marketplace Configuration Tables
-- ============================================================================

-- Marketplaces master table
CREATE TABLE IF NOT EXISTS marketplaces (
    marketplace_id SERIAL PRIMARY KEY,
    marketplace_code VARCHAR(50) UNIQUE NOT NULL,
    marketplace_name VARCHAR(255) NOT NULL,
    api_url VARCHAR(500),
    api_key_encrypted TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    supports_orders BOOLEAN DEFAULT TRUE,
    supports_listings BOOLEAN DEFAULT TRUE,
    supports_messages BOOLEAN DEFAULT TRUE,
    commission_rate DECIMAL(5,4) DEFAULT 0.15, -- 15% default
    currency VARCHAR(3) DEFAULT 'EUR',
    country VARCHAR(2), -- Primary country
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_marketplaces_code ON marketplaces(marketplace_code);
CREATE INDEX IF NOT EXISTS idx_marketplaces_active ON marketplaces(is_active);

-- Marketplace commission rates by category
CREATE TABLE IF NOT EXISTS marketplace_commissions (
    commission_id SERIAL PRIMARY KEY,
    marketplace_id INTEGER NOT NULL REFERENCES marketplaces(marketplace_id) ON DELETE CASCADE,
    category VARCHAR(255),
    subcategory VARCHAR(255),
    commission_rate DECIMAL(5,4) NOT NULL,
    minimum_commission DECIMAL(10,2),
    maximum_commission DECIMAL(10,2),
    valid_from DATE DEFAULT CURRENT_DATE,
    valid_until DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_marketplace_commissions_marketplace ON marketplace_commissions(marketplace_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_commissions_category ON marketplace_commissions(category);

-- Marketplace fee structure (listing fees, transaction fees, etc.)
CREATE TABLE IF NOT EXISTS marketplace_fees (
    fee_id SERIAL PRIMARY KEY,
    marketplace_id INTEGER NOT NULL REFERENCES marketplaces(marketplace_id) ON DELETE CASCADE,
    fee_type VARCHAR(50) NOT NULL, -- listing, transaction, subscription, storage
    fee_name VARCHAR(255) NOT NULL,
    fee_amount DECIMAL(10,2),
    fee_percentage DECIMAL(5,2),
    applies_to_category VARCHAR(255),
    currency VARCHAR(3) DEFAULT 'EUR',
    is_active BOOLEAN DEFAULT TRUE,
    valid_from DATE DEFAULT CURRENT_DATE,
    valid_until DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_marketplace_fees_marketplace ON marketplace_fees(marketplace_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_fees_type ON marketplace_fees(fee_type);

-- Marketplace product listings (synced from our platform)
CREATE TABLE IF NOT EXISTS marketplace_listings (
    listing_id SERIAL PRIMARY KEY,
    marketplace_id INTEGER NOT NULL REFERENCES marketplaces(marketplace_id) ON DELETE CASCADE,
    product_id UUID, -- References products table
    sku VARCHAR(255) NOT NULL,
    marketplace_listing_id VARCHAR(255), -- ID on the marketplace
    title VARCHAR(500),
    description TEXT,
    price DECIMAL(10,2),
    quantity INTEGER,
    status VARCHAR(50) DEFAULT 'active', -- active, inactive, out_of_stock, pending
    category VARCHAR(255),
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(marketplace_id, sku)
);

CREATE INDEX IF NOT EXISTS idx_marketplace_listings_marketplace ON marketplace_listings(marketplace_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_listings_sku ON marketplace_listings(sku);
CREATE INDEX IF NOT EXISTS idx_marketplace_listings_status ON marketplace_listings(status);

-- Marketplace orders (orders from marketplaces)
CREATE TABLE IF NOT EXISTS marketplace_orders (
    marketplace_order_id SERIAL PRIMARY KEY,
    marketplace_id INTEGER NOT NULL REFERENCES marketplaces(marketplace_id) ON DELETE CASCADE,
    external_order_id VARCHAR(255) NOT NULL, -- Order ID on marketplace
    internal_order_id VARCHAR(255), -- Our internal order ID
    order_date TIMESTAMP NOT NULL,
    customer_name VARCHAR(255),
    customer_email VARCHAR(255),
    shipping_address JSONB,
    items JSONB NOT NULL,
    subtotal DECIMAL(10,2),
    commission DECIMAL(10,2),
    fees DECIMAL(10,2),
    total_amount DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'EUR',
    status VARCHAR(50) DEFAULT 'pending',
    tracking_number VARCHAR(255),
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(marketplace_id, external_order_id)
);

CREATE INDEX IF NOT EXISTS idx_marketplace_orders_marketplace ON marketplace_orders(marketplace_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_orders_external ON marketplace_orders(external_order_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_orders_internal ON marketplace_orders(internal_order_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_orders_status ON marketplace_orders(status);
CREATE INDEX IF NOT EXISTS idx_marketplace_orders_date ON marketplace_orders(order_date);

-- Marketplace sync log
CREATE TABLE IF NOT EXISTS marketplace_sync_log (
    sync_id SERIAL PRIMARY KEY,
    marketplace_id INTEGER NOT NULL REFERENCES marketplaces(marketplace_id) ON DELETE CASCADE,
    sync_type VARCHAR(50) NOT NULL, -- orders, inventory, prices, listings
    sync_status VARCHAR(50) DEFAULT 'in_progress', -- in_progress, completed, failed
    records_processed INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_marketplace_sync_marketplace ON marketplace_sync_log(marketplace_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_sync_type ON marketplace_sync_log(sync_type);
CREATE INDEX IF NOT EXISTS idx_marketplace_sync_status ON marketplace_sync_log(sync_status);

-- ============================================================================
-- Seed Data - Initial Carriers
-- ============================================================================

INSERT INTO carriers (carrier_code, carrier_name, api_url, is_active, average_on_time_rate) VALUES
('colissimo', 'Colissimo', 'https://ws.colissimo.fr/sls-ws', TRUE, 0.95),
('chronopost', 'Chronopost', 'https://ws.chronopost.fr/shipping-cxf', TRUE, 0.98),
('dpd', 'DPD', 'https://api.dpd.com', TRUE, 0.93),
('colis_prive', 'Colis Privé', 'https://api.colisprive.com', TRUE, 0.88),
('ups', 'UPS', 'https://onlinetools.ups.com/api', TRUE, 0.92),
('fedex', 'FedEx', 'https://apis.fedex.com', TRUE, 0.91)
ON CONFLICT (carrier_code) DO NOTHING;

-- ============================================================================
-- Seed Data - Initial Marketplaces
-- ============================================================================

INSERT INTO marketplaces (marketplace_code, marketplace_name, api_url, is_active, commission_rate, country) VALUES
('cdiscount', 'CDiscount', 'https://api.cdiscount.com/v1', TRUE, 0.15, 'FR'),
('backmarket', 'BackMarket', 'https://api.backmarket.com/v1', TRUE, 0.15, 'FR'),
('refurbed', 'Refurbed', 'https://api.refurbed.com/v1', TRUE, 0.15, 'FR'),
('mirakl', 'Mirakl', 'https://api.mirakl.net/api', TRUE, 0.15, 'FR'),
('amazon', 'Amazon', 'https://sellingpartnerapi-eu.amazon.com', TRUE, 0.15, 'FR'),
('ebay', 'eBay', 'https://api.ebay.com/sell', TRUE, 0.12, 'FR')
ON CONFLICT (marketplace_code) DO NOTHING;

-- ============================================================================
-- Sample Carrier Pricing Data (Colissimo France)
-- ============================================================================

-- Get Colissimo carrier_id
DO $$
DECLARE
    colissimo_id INTEGER;
BEGIN
    SELECT carrier_id INTO colissimo_id FROM carriers WHERE carrier_code = 'colissimo';
    
    IF colissimo_id IS NOT NULL THEN
        -- Domestic France pricing
        INSERT INTO carrier_pricing (carrier_id, origin_country, destination_country, destination_zone, weight_min, weight_max, base_price, currency) VALUES
        (colissimo_id, 'FR', 'FR', 'Domestic', 0, 1, 5.50, 'EUR'),
        (colissimo_id, 'FR', 'FR', 'Domestic', 1, 5, 7.90, 'EUR'),
        (colissimo_id, 'FR', 'FR', 'Domestic', 5, 10, 12.50, 'EUR'),
        (colissimo_id, 'FR', 'FR', 'Domestic', 10, 30, 18.00, 'EUR')
        ON CONFLICT DO NOTHING;
        
        -- EU pricing
        INSERT INTO carrier_pricing (carrier_id, origin_country, destination_country, destination_zone, weight_min, weight_max, base_price, currency) VALUES
        (colissimo_id, 'FR', 'DE', 'EU', 0, 2, 15.00, 'EUR'),
        (colissimo_id, 'FR', 'DE', 'EU', 2, 5, 22.00, 'EUR'),
        (colissimo_id, 'FR', 'DE', 'EU', 5, 30, 35.00, 'EUR'),
        (colissimo_id, 'FR', 'BE', 'EU', 0, 2, 15.00, 'EUR'),
        (colissimo_id, 'FR', 'IT', 'EU', 0, 2, 15.00, 'EUR'),
        (colissimo_id, 'FR', 'ES', 'EU', 0, 2, 15.00, 'EUR')
        ON CONFLICT DO NOTHING;
    END IF;
END $$;

-- ============================================================================
-- Functions for rate calculation
-- ============================================================================

-- Function to get carrier rate
CREATE OR REPLACE FUNCTION get_carrier_rate(
    p_carrier_code VARCHAR(50),
    p_origin_country VARCHAR(2),
    p_destination_country VARCHAR(2),
    p_weight DECIMAL(10,3)
)
RETURNS TABLE (
    carrier_name VARCHAR(255),
    base_price DECIMAL(10,2),
    total_price DECIMAL(10,2),
    currency VARCHAR(3)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.carrier_name,
        cp.base_price,
        cp.base_price + (GREATEST(p_weight - cp.weight_min, 0) * cp.price_per_kg) as total_price,
        cp.currency
    FROM carriers c
    JOIN carrier_pricing cp ON c.carrier_id = cp.carrier_id
    WHERE c.carrier_code = p_carrier_code
        AND cp.is_active = TRUE
        AND (cp.origin_country IS NULL OR cp.origin_country = p_origin_country)
        AND cp.destination_country = p_destination_country
        AND p_weight >= cp.weight_min
        AND (cp.weight_max IS NULL OR p_weight <= cp.weight_max)
        AND (cp.valid_from IS NULL OR cp.valid_from <= CURRENT_DATE)
        AND (cp.valid_until IS NULL OR cp.valid_until >= CURRENT_DATE)
    ORDER BY total_price ASC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Triggers for updated_at timestamps
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_carriers_updated_at BEFORE UPDATE ON carriers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_carrier_pricing_updated_at BEFORE UPDATE ON carrier_pricing
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_marketplaces_updated_at BEFORE UPDATE ON marketplaces
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_marketplace_listings_updated_at BEFORE UPDATE ON marketplace_listings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_marketplace_orders_updated_at BEFORE UPDATE ON marketplace_orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

