-- ============================================================================
-- OFFERS MANAGEMENT SCHEMA
-- ============================================================================
-- This migration adds tables for managing special offers, promotions, and deals
-- Based on Market Master Tool competitive analysis
-- ============================================================================

-- Offers table
CREATE TABLE IF NOT EXISTS offers (
    id SERIAL PRIMARY KEY,
    
    -- Basic Information
    name VARCHAR(255) NOT NULL,
    description TEXT,
    offer_type VARCHAR(50) NOT NULL, -- percentage, fixed_amount, buy_x_get_y, bundle
    status VARCHAR(50) DEFAULT 'draft', -- draft, active, paused, expired, cancelled
    
    -- Pricing & Discount
    discount_type VARCHAR(50), -- percentage, fixed
    discount_value NUMERIC(10, 2),
    min_purchase_amount NUMERIC(15, 2),
    max_discount_amount NUMERIC(15, 2),
    
    -- Scheduling
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    is_scheduled BOOLEAN DEFAULT false,
    
    -- Targeting
    target_customer_groups JSONB, -- Array of customer group IDs
    target_marketplaces JSONB, -- Array of marketplace IDs
    target_products JSONB, -- Array of product IDs
    target_categories JSONB, -- Array of category names
    
    -- Usage Limits
    usage_limit_per_customer INTEGER,
    total_usage_limit INTEGER,
    current_usage_count INTEGER DEFAULT 0,
    
    -- Conditions
    conditions JSONB, -- Complex conditions (min quantity, specific SKUs, etc.)
    stackable BOOLEAN DEFAULT false, -- Can be combined with other offers
    
    -- Priority & Display
    priority INTEGER DEFAULT 0, -- Higher priority offers shown first
    display_badge VARCHAR(100), -- "Limited Time", "Flash Sale", etc.
    display_banner_url TEXT,
    
    -- Metadata
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Offer Products (Many-to-Many relationship)
CREATE TABLE IF NOT EXISTS offer_products (
    id SERIAL PRIMARY KEY,
    offer_id INTEGER REFERENCES offers(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    
    -- Product-specific discount override
    custom_discount_value NUMERIC(10, 2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(offer_id, product_id)
);

-- Offer Marketplaces (Many-to-Many relationship)
CREATE TABLE IF NOT EXISTS offer_marketplaces (
    id SERIAL PRIMARY KEY,
    offer_id INTEGER REFERENCES offers(id) ON DELETE CASCADE,
    marketplace_id INTEGER REFERENCES marketplaces(id) ON DELETE CASCADE,
    
    -- Marketplace-specific configuration
    marketplace_offer_id VARCHAR(255), -- External offer ID on marketplace
    sync_status VARCHAR(50) DEFAULT 'pending', -- pending, synced, failed
    last_synced_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(offer_id, marketplace_id)
);

-- Offer Usage Tracking
CREATE TABLE IF NOT EXISTS offer_usage (
    id SERIAL PRIMARY KEY,
    offer_id INTEGER REFERENCES offers(id) ON DELETE CASCADE,
    customer_id INTEGER REFERENCES customers(id),
    order_id INTEGER REFERENCES orders(id),
    
    -- Usage details
    discount_applied NUMERIC(15, 2),
    original_amount NUMERIC(15, 2),
    final_amount NUMERIC(15, 2),
    
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_offer_usage_offer (offer_id),
    INDEX idx_offer_usage_customer (customer_id),
    INDEX idx_offer_usage_order (order_id)
);

-- Offer Performance Analytics
CREATE TABLE IF NOT EXISTS offer_analytics (
    id SERIAL PRIMARY KEY,
    offer_id INTEGER REFERENCES offers(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    
    -- Performance metrics
    views_count INTEGER DEFAULT 0,
    clicks_count INTEGER DEFAULT 0,
    usage_count INTEGER DEFAULT 0,
    revenue_generated NUMERIC(15, 2) DEFAULT 0.00,
    discount_given NUMERIC(15, 2) DEFAULT 0.00,
    orders_count INTEGER DEFAULT 0,
    
    -- Conversion metrics
    conversion_rate NUMERIC(5, 2), -- Percentage
    average_order_value NUMERIC(15, 2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(offer_id, date)
);

-- Indexes for performance
CREATE INDEX idx_offers_status ON offers(status);
CREATE INDEX idx_offers_dates ON offers(start_date, end_date);
CREATE INDEX idx_offers_type ON offers(offer_type);
CREATE INDEX idx_offer_products_product ON offer_products(product_id);
CREATE INDEX idx_offer_marketplaces_marketplace ON offer_marketplaces(marketplace_id);

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_offers_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER offers_updated_at_trigger
    BEFORE UPDATE ON offers
    FOR EACH ROW
    EXECUTE FUNCTION update_offers_updated_at();

CREATE TRIGGER offer_analytics_updated_at_trigger
    BEFORE UPDATE ON offer_analytics
    FOR EACH ROW
    EXECUTE FUNCTION update_offers_updated_at();

-- Comments
COMMENT ON TABLE offers IS 'Special offers, promotions, and deals';
COMMENT ON TABLE offer_products IS 'Products included in offers';
COMMENT ON TABLE offer_marketplaces IS 'Marketplaces where offers are active';
COMMENT ON TABLE offer_usage IS 'Tracking of offer usage by customers';
COMMENT ON TABLE offer_analytics IS 'Daily analytics for offer performance';
