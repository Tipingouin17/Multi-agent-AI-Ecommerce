-- =====================================================
-- Product Wizard Fields - Corrected Migration
-- Migration: 024_product_wizard_fields_corrected.sql
-- Description: Add wizard fields matching existing schema structure
-- =====================================================

-- =====================================================
-- 1. EXTEND PRODUCTS TABLE
-- =====================================================

-- Add new wizard fields to products table
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS display_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS brand VARCHAR(255),
ADD COLUMN IF NOT EXISTS model_number VARCHAR(255),
ADD COLUMN IF NOT EXISTS product_type VARCHAR(50) DEFAULT 'simple',
ADD COLUMN IF NOT EXISTS key_features TEXT[],
ADD COLUMN IF NOT EXISTS profit_margin DECIMAL(5,2),
ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'USD',
ADD COLUMN IF NOT EXISTS is_draft BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS published_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS scheduled_publish_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS dimensions_length DECIMAL(8,2),
ADD COLUMN IF NOT EXISTS dimensions_width DECIMAL(8,2),
ADD COLUMN IF NOT EXISTS dimensions_height DECIMAL(8,2),
ADD COLUMN IF NOT EXISTS dimensions_unit VARCHAR(10) DEFAULT 'cm',
ADD COLUMN IF NOT EXISTS weight_unit VARCHAR(10) DEFAULT 'kg',
ADD COLUMN IF NOT EXISTS material VARCHAR(255),
ADD COLUMN IF NOT EXISTS color VARCHAR(100),
ADD COLUMN IF NOT EXISTS warranty_period INTEGER,
ADD COLUMN IF NOT EXISTS country_of_origin VARCHAR(100),
ADD COLUMN IF NOT EXISTS shipping_weight DECIMAL(8,3),
ADD COLUMN IF NOT EXISTS shipping_length DECIMAL(8,2),
ADD COLUMN IF NOT EXISTS shipping_width DECIMAL(8,2),
ADD COLUMN IF NOT EXISTS shipping_height DECIMAL(8,2),
ADD COLUMN IF NOT EXISTS handling_time_days INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS requires_shipping BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS is_fragile BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS is_perishable BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS has_age_restriction BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS min_age INTEGER,
ADD COLUMN IF NOT EXISTS is_hazmat BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS hazmat_class VARCHAR(50),
ADD COLUMN IF NOT EXISTS requires_signature BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS has_export_restrictions BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS export_restriction_countries TEXT[],
ADD COLUMN IF NOT EXISTS safety_warnings TEXT[];

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_products_display_name ON products(display_name);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_model_number ON products(model_number);
CREATE INDEX IF NOT EXISTS idx_products_product_type ON products(product_type);
CREATE INDEX IF NOT EXISTS idx_products_is_draft ON products(is_draft);

-- =====================================================
-- 2. PRODUCT SPECIFICATIONS (Step 2)
-- =====================================================

CREATE TABLE IF NOT EXISTS product_specifications (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    spec_name VARCHAR(255) NOT NULL,
    spec_value TEXT NOT NULL,
    spec_unit VARCHAR(50),
    spec_group VARCHAR(100),
    display_order INTEGER DEFAULT 0,
    is_visible BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_product_specifications_product_id ON product_specifications(product_id);

-- =====================================================
-- 3. PRODUCT MEDIA (Step 3)
-- =====================================================

CREATE TABLE IF NOT EXISTS product_media (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    media_type VARCHAR(50) NOT NULL DEFAULT 'image',
    media_url TEXT NOT NULL,
    thumbnail_url TEXT,
    alt_text VARCHAR(500),
    caption TEXT,
    display_order INTEGER DEFAULT 0,
    is_primary BOOLEAN DEFAULT false,
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    mime_type VARCHAR(100),
    duration INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_product_media_product_id ON product_media(product_id);
CREATE INDEX IF NOT EXISTS idx_product_media_type ON product_media(media_type);

-- =====================================================
-- 4. PRICING TIERS (Step 4)
-- =====================================================

CREATE TABLE IF NOT EXISTS product_pricing_tiers (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    min_quantity INTEGER NOT NULL,
    max_quantity INTEGER,
    price DECIMAL(10,2) NOT NULL,
    discount_percentage DECIMAL(5,2),
    is_active BOOLEAN DEFAULT true,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_product_pricing_tiers_product_id ON product_pricing_tiers(product_id);

-- Tax configuration
CREATE TABLE IF NOT EXISTS product_tax_config (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    tax_class VARCHAR(100) NOT NULL,
    tax_rate DECIMAL(5,2) NOT NULL,
    tax_region VARCHAR(100),
    is_tax_inclusive BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_product_tax_config_product_id ON product_tax_config(product_id);

-- =====================================================
-- 5. WAREHOUSE INVENTORY (Step 5)
-- =====================================================

CREATE TABLE IF NOT EXISTS product_warehouse_inventory (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    warehouse_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0,
    available_quantity INTEGER GENERATED ALWAYS AS (quantity - reserved_quantity) STORED,
    low_stock_threshold INTEGER DEFAULT 10,
    reorder_point INTEGER DEFAULT 20,
    reorder_quantity INTEGER DEFAULT 50,
    warehouse_sku VARCHAR(255),
    warehouse_location VARCHAR(255),
    last_counted_at TIMESTAMP,
    last_restocked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE(product_id, warehouse_id)
);

CREATE INDEX IF NOT EXISTS idx_product_warehouse_inventory_product_id ON product_warehouse_inventory(product_id);
CREATE INDEX IF NOT EXISTS idx_product_warehouse_inventory_warehouse_id ON product_warehouse_inventory(warehouse_id);

-- =====================================================
-- 6. BUNDLES (Step 6)
-- =====================================================

-- Check if product_bundles exists, if not create it
CREATE TABLE IF NOT EXISTS product_bundles (
    id SERIAL PRIMARY KEY,
    bundle_name VARCHAR(255) NOT NULL,
    bundle_description TEXT,
    bundle_sku VARCHAR(255) NOT NULL UNIQUE,
    bundle_type VARCHAR(50) NOT NULL,
    pricing_strategy VARCHAR(50) NOT NULL,
    bundle_price DECIMAL(10,2),
    discount_percentage DECIMAL(5,2),
    is_active BOOLEAN DEFAULT true,
    is_customizable BOOLEAN DEFAULT false,
    min_items INTEGER,
    max_items INTEGER,
    display_name VARCHAR(255),
    display_description TEXT,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bundle_components (
    id SERIAL PRIMARY KEY,
    bundle_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    is_required BOOLEAN DEFAULT true,
    can_substitute BOOLEAN DEFAULT false,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bundle_id) REFERENCES product_bundles(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_bundle_components_bundle_id ON bundle_components(bundle_id);

-- =====================================================
-- 7. MARKETPLACE & COMPLIANCE (Step 7)
-- =====================================================

CREATE TABLE IF NOT EXISTS product_marketplace_listings (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    marketplace_name VARCHAR(100) NOT NULL,
    marketplace_sku VARCHAR(255),
    marketplace_category VARCHAR(255),
    marketplace_price DECIMAL(10,2),
    marketplace_status VARCHAR(50) DEFAULT 'draft',
    is_published BOOLEAN DEFAULT false,
    published_at TIMESTAMP,
    last_synced_at TIMESTAMP,
    sync_status VARCHAR(50),
    sync_error_message TEXT,
    listing_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE(product_id, marketplace_name)
);

CREATE INDEX IF NOT EXISTS idx_product_marketplace_listings_product_id ON product_marketplace_listings(product_id);
CREATE INDEX IF NOT EXISTS idx_product_marketplace_listings_marketplace ON product_marketplace_listings(marketplace_name);

-- Product identifiers
CREATE TABLE IF NOT EXISTS product_identifiers (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    identifier_type VARCHAR(50) NOT NULL,
    identifier_value VARCHAR(255) NOT NULL,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE(product_id, identifier_type, identifier_value)
);

CREATE INDEX IF NOT EXISTS idx_product_identifiers_product_id ON product_identifiers(product_id);
CREATE INDEX IF NOT EXISTS idx_product_identifiers_value ON product_identifiers(identifier_value);

-- Compliance & certifications
CREATE TABLE IF NOT EXISTS product_compliance (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    certification_type VARCHAR(100) NOT NULL,
    certification_number VARCHAR(255),
    certification_authority VARCHAR(255),
    issue_date DATE,
    expiry_date DATE,
    document_url TEXT,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_product_compliance_product_id ON product_compliance(product_id);

-- =====================================================
-- 8. LIFECYCLE & AUDIT (Step 8)
-- =====================================================

CREATE TABLE IF NOT EXISTS product_lifecycle_events (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_description TEXT,
    previous_status VARCHAR(50),
    new_status VARCHAR(50),
    triggered_by VARCHAR(255),
    event_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_product_lifecycle_events_product_id ON product_lifecycle_events(product_id);
CREATE INDEX IF NOT EXISTS idx_product_lifecycle_events_type ON product_lifecycle_events(event_type);

-- Product versions
CREATE TABLE IF NOT EXISTS product_versions (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    product_data JSONB NOT NULL,
    changed_fields TEXT[],
    change_summary TEXT,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_product_versions_product_id ON product_versions(product_id);

-- =====================================================
-- 9. FUNCTIONS & TRIGGERS
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
        VALUES (NEW.id, 'created', NEW.status, CURRENT_USER);
    ELSIF TG_OP = 'UPDATE' AND OLD.status != NEW.status THEN
        INSERT INTO product_lifecycle_events (product_id, event_type, previous_status, new_status, triggered_by)
        VALUES (NEW.id, 'status_changed', OLD.status, NEW.status, CURRENT_USER);
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
-- 10. VIEWS
-- =====================================================

-- Complete product view
CREATE OR REPLACE VIEW vw_products_complete AS
SELECT 
    p.*,
    COUNT(DISTINCT pwi.warehouse_id) as warehouse_count,
    COALESCE(SUM(pwi.available_quantity), 0) as total_available_quantity,
    COUNT(DISTINCT pml.marketplace_name) as marketplace_count,
    COUNT(DISTINCT pm.id) FILTER (WHERE pm.media_type = 'image') as image_count,
    COUNT(DISTINCT pm.id) FILTER (WHERE pm.media_type = 'video') as video_count,
    COUNT(DISTINCT ps.id) as specification_count
FROM products p
LEFT JOIN product_warehouse_inventory pwi ON p.id = pwi.product_id
LEFT JOIN product_marketplace_listings pml ON p.id = pml.product_id AND pml.is_published = true
LEFT JOIN product_media pm ON p.id = pm.product_id AND pm.is_active = true
LEFT JOIN product_specifications ps ON p.id = ps.product_id
GROUP BY p.id;

-- Low stock products view
CREATE OR REPLACE VIEW vw_products_low_stock AS
SELECT 
    p.id,
    p.sku,
    p.name,
    pwi.warehouse_id,
    pwi.available_quantity,
    pwi.low_stock_threshold,
    pwi.reorder_point
FROM products p
JOIN product_warehouse_inventory pwi ON p.id = pwi.product_id
WHERE pwi.available_quantity < pwi.low_stock_threshold
AND p.status = 'active';

-- =====================================================
-- END OF MIGRATION
-- =====================================================
