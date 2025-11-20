-- ============================================================================
-- MARKETPLACE INTEGRATION SCHEMA
-- ============================================================================
-- This migration adds comprehensive marketplace integration capabilities
-- Supports Amazon, eBay, Walmart, Etsy, and custom marketplaces
-- ============================================================================

-- Marketplace Connections (already created in offers migration, but add more fields)
DO $$ 
BEGIN
    -- Add new columns if they don't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='marketplaces' AND column_name='marketplace_type') THEN
        ALTER TABLE marketplaces ADD COLUMN marketplace_type VARCHAR(50);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='marketplaces' AND column_name='account_id') THEN
        ALTER TABLE marketplaces ADD COLUMN account_id VARCHAR(255);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='marketplaces' AND column_name='seller_id') THEN
        ALTER TABLE marketplaces ADD COLUMN seller_id VARCHAR(255);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='marketplaces' AND column_name='region') THEN
        ALTER TABLE marketplaces ADD COLUMN region VARCHAR(50);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='marketplaces' AND column_name='currency') THEN
        ALTER TABLE marketplaces ADD COLUMN currency VARCHAR(10) DEFAULT 'USD';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='marketplaces' AND column_name='commission_rate') THEN
        ALTER TABLE marketplaces ADD COLUMN commission_rate NUMERIC(5, 2);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='marketplaces' AND column_name='last_sync_at') THEN
        ALTER TABLE marketplaces ADD COLUMN last_sync_at TIMESTAMP;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='marketplaces' AND column_name='sync_frequency') THEN
        ALTER TABLE marketplaces ADD COLUMN sync_frequency INTEGER DEFAULT 3600;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='marketplaces' AND column_name='auto_sync_enabled') THEN
        ALTER TABLE marketplaces ADD COLUMN auto_sync_enabled BOOLEAN DEFAULT true;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='marketplaces' AND column_name='settings') THEN
        ALTER TABLE marketplaces ADD COLUMN settings JSONB;
    END IF;
END $$;

-- Marketplace Product Listings
CREATE TABLE IF NOT EXISTS marketplace_listings (
    id SERIAL PRIMARY KEY,
    marketplace_id INTEGER REFERENCES marketplaces(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    
    -- Listing Information
    marketplace_listing_id VARCHAR(255), -- External listing ID (ASIN, eBay item ID, etc.)
    marketplace_sku VARCHAR(255),
    title VARCHAR(500),
    description TEXT,
    
    -- Pricing
    price NUMERIC(15, 2),
    compare_at_price NUMERIC(15, 2),
    cost NUMERIC(15, 2),
    currency VARCHAR(10) DEFAULT 'USD',
    
    -- Inventory
    quantity INTEGER DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0,
    available_quantity INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(50) DEFAULT 'draft', -- draft, active, inactive, out_of_stock, error
    sync_status VARCHAR(50) DEFAULT 'pending', -- pending, synced, failed, syncing
    
    -- Marketplace-specific data
    category_id VARCHAR(255),
    category_path VARCHAR(500),
    attributes JSONB, -- Marketplace-specific attributes
    shipping_template_id VARCHAR(255),
    fulfillment_method VARCHAR(50), -- fbm, fba, sfs (seller fulfilled)
    
    -- Performance
    views INTEGER DEFAULT 0,
    orders INTEGER DEFAULT 0,
    revenue NUMERIC(15, 2) DEFAULT 0.00,
    
    -- Sync tracking
    last_synced_at TIMESTAMP,
    sync_error TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(marketplace_id, product_id)
);

-- Marketplace Orders
CREATE TABLE IF NOT EXISTS marketplace_orders (
    id SERIAL PRIMARY KEY,
    marketplace_id INTEGER REFERENCES marketplaces(id),
    order_id INTEGER REFERENCES orders(id),
    
    -- Marketplace Order Info
    marketplace_order_id VARCHAR(255) UNIQUE NOT NULL,
    marketplace_order_number VARCHAR(255),
    
    -- Order Details
    order_date TIMESTAMP,
    total_amount NUMERIC(15, 2),
    tax_amount NUMERIC(15, 2),
    shipping_amount NUMERIC(15, 2),
    commission_amount NUMERIC(15, 2),
    currency VARCHAR(10) DEFAULT 'USD',
    
    -- Status
    marketplace_status VARCHAR(100),
    payment_status VARCHAR(50),
    fulfillment_status VARCHAR(50),
    
    -- Customer (marketplace-side)
    buyer_email VARCHAR(255),
    buyer_name VARCHAR(255),
    shipping_address JSONB,
    
    -- Sync
    sync_status VARCHAR(50) DEFAULT 'pending',
    last_synced_at TIMESTAMP,
    
    -- Metadata
    raw_data JSONB, -- Full marketplace order data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Marketplace Order Items
CREATE TABLE IF NOT EXISTS marketplace_order_items (
    id SERIAL PRIMARY KEY,
    marketplace_order_id INTEGER REFERENCES marketplace_orders(id) ON DELETE CASCADE,
    marketplace_listing_id INTEGER REFERENCES marketplace_listings(id),
    product_id INTEGER REFERENCES products(id),
    
    -- Item Details
    marketplace_item_id VARCHAR(255),
    marketplace_sku VARCHAR(255),
    title VARCHAR(500),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(15, 2),
    total_price NUMERIC(15, 2),
    tax NUMERIC(15, 2),
    commission NUMERIC(15, 2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Marketplace Sync Log
CREATE TABLE IF NOT EXISTS marketplace_sync_log (
    id SERIAL PRIMARY KEY,
    marketplace_id INTEGER REFERENCES marketplaces(id) ON DELETE CASCADE,
    
    -- Sync Details
    sync_type VARCHAR(50) NOT NULL, -- products, orders, inventory, full
    sync_direction VARCHAR(20), -- push, pull, bidirectional
    status VARCHAR(50) NOT NULL, -- started, completed, failed, partial
    
    -- Results
    items_processed INTEGER DEFAULT 0,
    items_succeeded INTEGER DEFAULT 0,
    items_failed INTEGER DEFAULT 0,
    
    -- Timing
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    
    -- Error tracking
    error_message TEXT,
    error_details JSONB,
    
    -- Metadata
    triggered_by VARCHAR(50), -- manual, scheduled, webhook
    user_id INTEGER REFERENCES users(id)
);

-- Marketplace Inventory Sync
CREATE TABLE IF NOT EXISTS marketplace_inventory_sync (
    id SERIAL PRIMARY KEY,
    marketplace_listing_id INTEGER REFERENCES marketplace_listings(id) ON DELETE CASCADE,
    
    -- Inventory Change
    previous_quantity INTEGER,
    new_quantity INTEGER,
    change_reason VARCHAR(100), -- sale, restock, adjustment, sync
    
    -- Sync Status
    sync_status VARCHAR(50) DEFAULT 'pending',
    synced_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Marketplace Performance Analytics
CREATE TABLE IF NOT EXISTS marketplace_analytics (
    id SERIAL PRIMARY KEY,
    marketplace_id INTEGER REFERENCES marketplaces(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    
    -- Sales Metrics
    orders_count INTEGER DEFAULT 0,
    units_sold INTEGER DEFAULT 0,
    gross_revenue NUMERIC(15, 2) DEFAULT 0.00,
    net_revenue NUMERIC(15, 2) DEFAULT 0.00,
    commission_paid NUMERIC(15, 2) DEFAULT 0.00,
    
    -- Product Metrics
    active_listings INTEGER DEFAULT 0,
    out_of_stock_listings INTEGER DEFAULT 0,
    total_views INTEGER DEFAULT 0,
    conversion_rate NUMERIC(5, 2),
    
    -- Performance Metrics
    average_order_value NUMERIC(15, 2),
    return_rate NUMERIC(5, 2),
    cancellation_rate NUMERIC(5, 2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(marketplace_id, date)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_marketplace_listings_marketplace ON marketplace_listings(marketplace_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_listings_product ON marketplace_listings(product_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_listings_status ON marketplace_listings(status);
CREATE INDEX IF NOT EXISTS idx_marketplace_listings_sync_status ON marketplace_listings(sync_status);
CREATE INDEX IF NOT EXISTS idx_marketplace_orders_marketplace ON marketplace_orders(marketplace_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_orders_order ON marketplace_orders(order_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_orders_marketplace_order_id ON marketplace_orders(marketplace_order_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_order_items_marketplace_order ON marketplace_order_items(marketplace_order_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_sync_log_marketplace ON marketplace_sync_log(marketplace_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_sync_log_status ON marketplace_sync_log(status);
CREATE INDEX IF NOT EXISTS idx_marketplace_analytics_marketplace ON marketplace_analytics(marketplace_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_analytics_date ON marketplace_analytics(date);

-- Update timestamp triggers
DROP TRIGGER IF EXISTS marketplace_listings_updated_at_trigger ON marketplace_listings;
CREATE TRIGGER marketplace_listings_updated_at_trigger
    BEFORE UPDATE ON marketplace_listings
    FOR EACH ROW
    EXECUTE FUNCTION update_offers_updated_at();

DROP TRIGGER IF EXISTS marketplace_orders_updated_at_trigger ON marketplace_orders;
CREATE TRIGGER marketplace_orders_updated_at_trigger
    BEFORE UPDATE ON marketplace_orders
    FOR EACH ROW
    EXECUTE FUNCTION update_offers_updated_at();

-- Comments
COMMENT ON TABLE marketplace_listings IS 'Product listings on external marketplaces';
COMMENT ON TABLE marketplace_orders IS 'Orders from external marketplaces';
COMMENT ON TABLE marketplace_order_items IS 'Line items in marketplace orders';
COMMENT ON TABLE marketplace_sync_log IS 'Log of sync operations with marketplaces';
COMMENT ON TABLE marketplace_inventory_sync IS 'Inventory synchronization tracking';
COMMENT ON TABLE marketplace_analytics IS 'Daily performance analytics per marketplace';
