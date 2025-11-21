-- =====================================================
-- Market Master Product Wizard - Database Migration
-- Migration: 023_market_master_product_wizard.sql
-- Description: Add all fields needed for 8-step product wizard
-- Based on: Market Master tool analysis
-- =====================================================

-- =====================================================
-- 1. EXTEND PRODUCTS TABLE
-- =====================================================

-- Add new fields to products table
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS display_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS model_number VARCHAR(255),
ADD COLUMN IF NOT EXISTS product_type VARCHAR(50) DEFAULT 'simple', -- simple, variable, grouped, external
ADD COLUMN IF NOT EXISTS key_features TEXT[], -- Array of key features
ADD COLUMN IF NOT EXISTS compare_price DECIMAL(10,2), -- MSRP/Compare at price
ADD COLUMN IF NOT EXISTS profit_margin DECIMAL(5,2), -- Calculated profit margin
ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'USD',
ADD COLUMN IF NOT EXISTS is_draft BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS published_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS scheduled_publish_at TIMESTAMP;

-- Add indexes for new fields
CREATE INDEX IF NOT EXISTS idx_products_display_name ON products(display_name);
CREATE INDEX IF NOT EXISTS idx_products_model_number ON products(model_number);
CREATE INDEX IF NOT EXISTS idx_products_product_type ON products(product_type);
CREATE INDEX IF NOT EXISTS idx_products_is_draft ON products(is_draft);

-- =====================================================
-- 2. PRODUCT SPECIFICATIONS (Step 2)
-- =====================================================

CREATE TABLE IF NOT EXISTS product_specifications (
    spec_id SERIAL PRIMARY KEY,
    product_id UUID NOT NULL,
    spec_name VARCHAR(255) NOT NULL,
    spec_value TEXT NOT NULL,
    spec_unit VARCHAR(50), -- cm, kg, watts, etc.
    spec_group VARCHAR(100), -- Dimensions, Technical, Materials, etc.
    display_order INTEGER DEFAULT 0,
    is_visible BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_product_specifications_product_id ON product_specifications(product_id);
CREATE INDEX IF NOT EXISTS idx_product_specifications_group ON product_specifications(spec_group);

-- Common specifications
ALTER TABLE products
ADD COLUMN IF NOT EXISTS dimensions_length DECIMAL(8,2),
ADD COLUMN IF NOT EXISTS dimensions_width DECIMAL(8,2),
ADD COLUMN IF NOT EXISTS dimensions_height DECIMAL(8,2),
ADD COLUMN IF NOT EXISTS dimensions_unit VARCHAR(10) DEFAULT 'cm',
ADD COLUMN IF NOT EXISTS weight_value DECIMAL(8,3),
ADD COLUMN IF NOT EXISTS weight_unit VARCHAR(10) DEFAULT 'kg',
ADD COLUMN IF NOT EXISTS material VARCHAR(255),
ADD COLUMN IF NOT EXISTS color VARCHAR(100),
ADD COLUMN IF NOT EXISTS warranty_period INTEGER, -- in months
ADD COLUMN IF NOT EXISTS country_of_origin VARCHAR(100);

-- =====================================================
-- 3. PRODUCT MEDIA (Step 3 - Enhanced)
-- =====================================================

-- Enhance existing product_media table if it exists, or create new one
CREATE TABLE IF NOT EXISTS product_media_enhanced (
    media_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL,
    media_type VARCHAR(50) NOT NULL, -- image, video, 360_view, document
    media_url TEXT NOT NULL,
    thumbnail_url TEXT,
    alt_text VARCHAR(500),
    caption TEXT,
    display_order INTEGER DEFAULT 0,
    is_primary BOOLEAN DEFAULT false,
    width INTEGER,
    height INTEGER,
    file_size INTEGER, -- bytes
    mime_type VARCHAR(100),
    duration INTEGER, -- for videos, in seconds
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_product_media_enhanced_product_id ON product_media_enhanced(product_id);
CREATE INDEX IF NOT EXISTS idx_product_media_enhanced_type ON product_media_enhanced(media_type);
CREATE INDEX IF NOT EXISTS idx_product_media_enhanced_primary ON product_media_enhanced(is_primary);

-- =====================================================
-- 4. PRICING & COSTS (Step 4 - Enhanced)
-- =====================================================

CREATE TABLE IF NOT EXISTS product_pricing_tiers (
    tier_id SERIAL PRIMARY KEY,
    product_id UUID NOT NULL,
    min_quantity INTEGER NOT NULL,
    max_quantity INTEGER,
    price DECIMAL(10,2) NOT NULL,
    discount_percentage DECIMAL(5,2),
    is_active BOOLEAN DEFAULT true,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_product_pricing_tiers_product_id ON product_pricing_tiers(product_id);

-- Tax configuration
CREATE TABLE IF NOT EXISTS product_tax_config (
    tax_id SERIAL PRIMARY KEY,
    product_id UUID NOT NULL,
    tax_class VARCHAR(100) NOT NULL, -- standard, reduced, zero, exempt
    tax_rate DECIMAL(5,2) NOT NULL,
    tax_region VARCHAR(100), -- US, EU, UK, etc.
    is_tax_inclusive BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_product_tax_config_product_id ON product_tax_config(product_id);

-- =====================================================
-- 5. INVENTORY & LOGISTICS (Step 5 - Enhanced)
-- =====================================================

CREATE TABLE IF NOT EXISTS product_warehouse_inventory (
    inventory_id SERIAL PRIMARY KEY,
    product_id UUID NOT NULL,
    warehouse_id UUID NOT NULL,
    quantity INTEGER DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0, -- Reserved for orders
    available_quantity INTEGER GENERATED ALWAYS AS (quantity - reserved_quantity) STORED,
    low_stock_threshold INTEGER DEFAULT 10,
    reorder_point INTEGER DEFAULT 20,
    reorder_quantity INTEGER DEFAULT 50,
    warehouse_sku VARCHAR(255), -- Warehouse-specific SKU
    warehouse_location VARCHAR(255), -- Bin/shelf location
    last_counted_at TIMESTAMP,
    last_restocked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    UNIQUE(product_id, warehouse_id)
);

CREATE INDEX IF NOT EXISTS idx_product_warehouse_inventory_product_id ON product_warehouse_inventory(product_id);
CREATE INDEX IF NOT EXISTS idx_product_warehouse_inventory_warehouse_id ON product_warehouse_inventory(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_product_warehouse_inventory_low_stock ON product_warehouse_inventory(available_quantity) WHERE available_quantity < low_stock_threshold;

-- Shipping configuration
ALTER TABLE products
ADD COLUMN IF NOT EXISTS shipping_weight DECIMAL(8,3),
ADD COLUMN IF NOT EXISTS shipping_weight_unit VARCHAR(10) DEFAULT 'kg',
ADD COLUMN IF NOT EXISTS shipping_length DECIMAL(8,2),
ADD COLUMN IF NOT EXISTS shipping_width DECIMAL(8,2),
ADD COLUMN IF NOT EXISTS shipping_height DECIMAL(8,2),
ADD COLUMN IF NOT EXISTS shipping_dimensions_unit VARCHAR(10) DEFAULT 'cm',
ADD COLUMN IF NOT EXISTS handling_time_days INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS requires_shipping BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS is_fragile BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS is_perishable BOOLEAN DEFAULT false;

-- =====================================================
-- 6. BUNDLES & KITS (Step 6 - Enhanced)
-- =====================================================

-- Note: product_bundles table already exists from 003_product_agent_enhancements.sql
-- Add additional fields if needed

ALTER TABLE product_bundles
ADD COLUMN IF NOT EXISTS is_customizable BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS min_items INTEGER,
ADD COLUMN IF NOT EXISTS max_items INTEGER,
ADD COLUMN IF NOT EXISTS display_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS display_description TEXT;

-- Bundle component options (for flexible bundles)
CREATE TABLE IF NOT EXISTS bundle_component_options (
    option_id SERIAL PRIMARY KEY,
    component_id INTEGER NOT NULL,
    product_id UUID NOT NULL,
    is_default BOOLEAN DEFAULT false,
    price_adjustment DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (component_id) REFERENCES bundle_components(component_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_bundle_component_options_component_id ON bundle_component_options(component_id);

-- =====================================================
-- 7. MARKETPLACE & COMPLIANCE (Step 7)
-- =====================================================

CREATE TABLE IF NOT EXISTS product_marketplace_listings (
    listing_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL,
    marketplace_name VARCHAR(100) NOT NULL, -- Amazon, eBay, Walmart, etc.
    marketplace_sku VARCHAR(255),
    marketplace_category VARCHAR(255),
    marketplace_price DECIMAL(10,2),
    marketplace_status VARCHAR(50) DEFAULT 'draft', -- draft, active, inactive, error
    is_published BOOLEAN DEFAULT false,
    published_at TIMESTAMP,
    last_synced_at TIMESTAMP,
    sync_status VARCHAR(50), -- pending, syncing, synced, error
    sync_error_message TEXT,
    listing_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    UNIQUE(product_id, marketplace_name)
);

CREATE INDEX IF NOT EXISTS idx_product_marketplace_listings_product_id ON product_marketplace_listings(product_id);
CREATE INDEX IF NOT EXISTS idx_product_marketplace_listings_marketplace ON product_marketplace_listings(marketplace_name);
CREATE INDEX IF NOT EXISTS idx_product_marketplace_listings_status ON product_marketplace_listings(marketplace_status);

-- Product identifiers (GTIN, UPC, EAN, ISBN, etc.)
CREATE TABLE IF NOT EXISTS product_identifiers (
    identifier_id SERIAL PRIMARY KEY,
    product_id UUID NOT NULL,
    identifier_type VARCHAR(50) NOT NULL, -- GTIN, UPC, EAN, ISBN, ASIN, MPN
    identifier_value VARCHAR(255) NOT NULL,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    UNIQUE(product_id, identifier_type, identifier_value)
);

CREATE INDEX IF NOT EXISTS idx_product_identifiers_product_id ON product_identifiers(product_id);
CREATE INDEX IF NOT EXISTS idx_product_identifiers_type ON product_identifiers(identifier_type);
CREATE INDEX IF NOT EXISTS idx_product_identifiers_value ON product_identifiers(identifier_value);

-- Compliance & certifications
CREATE TABLE IF NOT EXISTS product_compliance (
    compliance_id SERIAL PRIMARY KEY,
    product_id UUID NOT NULL,
    certification_type VARCHAR(100) NOT NULL, -- CE, FCC, RoHS, FDA, etc.
    certification_number VARCHAR(255),
    certification_authority VARCHAR(255),
    issue_date DATE,
    expiry_date DATE,
    document_url TEXT,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_product_compliance_product_id ON product_compliance(product_id);
CREATE INDEX IF NOT EXISTS idx_product_compliance_type ON product_compliance(certification_type);

-- Safety & restrictions
ALTER TABLE products
ADD COLUMN IF NOT EXISTS has_age_restriction BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS min_age INTEGER,
ADD COLUMN IF NOT EXISTS is_hazmat BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS hazmat_class VARCHAR(50),
ADD COLUMN IF NOT EXISTS requires_signature BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS has_export_restrictions BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS export_restriction_countries TEXT[],
ADD COLUMN IF NOT EXISTS safety_warnings TEXT[];

-- =====================================================
-- 8. PRODUCT LIFECYCLE & AUDIT (Step 8)
-- =====================================================

CREATE TABLE IF NOT EXISTS product_lifecycle_events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL, -- created, draft_saved, published, unpublished, archived, deleted
    event_description TEXT,
    previous_status VARCHAR(50),
    new_status VARCHAR(50),
    triggered_by VARCHAR(255), -- user_id or system
    event_data JSONB, -- Additional event metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_product_lifecycle_events_product_id ON product_lifecycle_events(product_id);
CREATE INDEX IF NOT EXISTS idx_product_lifecycle_events_type ON product_lifecycle_events(event_type);
CREATE INDEX IF NOT EXISTS idx_product_lifecycle_events_created_at ON product_lifecycle_events(created_at);

-- Product versions (for tracking changes)
CREATE TABLE IF NOT EXISTS product_versions (
    version_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL,
    version_number INTEGER NOT NULL,
    product_data JSONB NOT NULL, -- Full product snapshot
    changed_fields TEXT[], -- List of changed fields
    change_summary TEXT,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_product_versions_product_id ON product_versions(product_id);
CREATE INDEX IF NOT EXISTS idx_product_versions_version_number ON product_versions(version_number);

-- =====================================================
-- 9. VIEWS FOR EASY QUERYING
-- =====================================================

-- Complete product view with all related data
CREATE OR REPLACE VIEW vw_products_complete AS
SELECT 
    p.*,
    COUNT(DISTINCT pwi.warehouse_id) as warehouse_count,
    COALESCE(SUM(pwi.available_quantity), 0) as total_available_quantity,
    COUNT(DISTINCT pml.marketplace_name) as marketplace_count,
    COUNT(DISTINCT pm.media_id) FILTER (WHERE pm.media_type = 'image') as image_count,
    COUNT(DISTINCT pm.media_id) FILTER (WHERE pm.media_type = 'video') as video_count,
    COUNT(DISTINCT ps.spec_id) as specification_count
FROM products p
LEFT JOIN product_warehouse_inventory pwi ON p.product_id = pwi.product_id
LEFT JOIN product_marketplace_listings pml ON p.product_id = pml.product_id AND pml.is_published = true
LEFT JOIN product_media_enhanced pm ON p.product_id = pm.product_id AND pm.is_active = true
LEFT JOIN product_specifications ps ON p.product_id = ps.product_id
GROUP BY p.product_id;

-- Low stock products view
CREATE OR REPLACE VIEW vw_products_low_stock AS
SELECT 
    p.product_id,
    p.sku,
    p.name,
    pwi.warehouse_id,
    pwi.available_quantity,
    pwi.low_stock_threshold,
    pwi.reorder_point
FROM products p
JOIN product_warehouse_inventory pwi ON p.product_id = pwi.product_id
WHERE pwi.available_quantity < pwi.low_stock_threshold
AND p.status = 'active';

-- =====================================================
-- 10. FUNCTIONS & TRIGGERS
-- =====================================================

-- Function to calculate profit margin
CREATE OR REPLACE FUNCTION calculate_profit_margin()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.price IS NOT NULL AND NEW.cost IS NOT NULL AND NEW.cost > 0 THEN
        NEW.profit_margin := ((NEW.price - NEW.cost) / NEW.cost) * 100;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-calculate profit margin
DROP TRIGGER IF EXISTS trg_calculate_profit_margin ON products;
CREATE TRIGGER trg_calculate_profit_margin
    BEFORE INSERT OR UPDATE OF price, cost ON products
    FOR EACH ROW
    EXECUTE FUNCTION calculate_profit_margin();

-- Function to log product lifecycle events
CREATE OR REPLACE FUNCTION log_product_lifecycle_event()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO product_lifecycle_events (product_id, event_type, new_status, triggered_by)
        VALUES (NEW.product_id, 'created', NEW.status, CURRENT_USER);
    ELSIF TG_OP = 'UPDATE' AND OLD.status != NEW.status THEN
        INSERT INTO product_lifecycle_events (product_id, event_type, previous_status, new_status, triggered_by)
        VALUES (NEW.product_id, 'status_changed', OLD.status, NEW.status, CURRENT_USER);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to log lifecycle events
DROP TRIGGER IF EXISTS trg_log_product_lifecycle ON products;
CREATE TRIGGER trg_log_product_lifecycle
    AFTER INSERT OR UPDATE OF status ON products
    FOR EACH ROW
    EXECUTE FUNCTION log_product_lifecycle_event();

-- =====================================================
-- 11. SEED DATA FOR TESTING
-- =====================================================

-- Insert sample attribute groups
INSERT INTO attribute_groups (group_name, group_description, display_order) VALUES
('Dimensions', 'Physical dimensions and measurements', 1),
('Technical Specifications', 'Technical details and specifications', 2),
('Materials & Construction', 'Material composition and construction details', 3),
('Warranty & Support', 'Warranty and support information', 4)
ON CONFLICT DO NOTHING;

-- =====================================================
-- END OF MIGRATION
-- =====================================================

-- Add comments for documentation
COMMENT ON TABLE product_specifications IS 'Product technical specifications and attributes (Step 2 of wizard)';
COMMENT ON TABLE product_media_enhanced IS 'Product images, videos, and 360° views (Step 3 of wizard)';
COMMENT ON TABLE product_pricing_tiers IS 'Bulk pricing tiers (Step 4 of wizard)';
COMMENT ON TABLE product_warehouse_inventory IS 'Multi-warehouse inventory management (Step 5 of wizard)';
COMMENT ON TABLE product_marketplace_listings IS 'Marketplace integration and listings (Step 7 of wizard)';
COMMENT ON TABLE product_compliance IS 'Product certifications and compliance (Step 7 of wizard)';
COMMENT ON TABLE product_lifecycle_events IS 'Product lifecycle audit trail (Step 8 of wizard)';
