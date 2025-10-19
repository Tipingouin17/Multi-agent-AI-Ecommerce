-- =====================================================
-- Product Agent Enhancements - Database Migration
-- Migration: 003_product_agent_enhancements.sql
-- Description: Comprehensive product management enhancements
-- Features: Variants, Bundles, Media, Categories, Attributes,
--           Pricing Rules, Reviews, Inventory, Relationships, Lifecycle
-- =====================================================

-- =====================================================
-- 1. PRODUCT VARIANTS
-- =====================================================

-- Variant attributes (size, color, material, etc.)
CREATE TABLE IF NOT EXISTS variant_attributes (
    attribute_id SERIAL PRIMARY KEY,
    attribute_name VARCHAR(100) NOT NULL UNIQUE,
    attribute_type VARCHAR(50) NOT NULL, -- text, color, size, number
    display_order INTEGER DEFAULT 0,
    is_required BOOLEAN DEFAULT false,
    is_visible BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product variants (parent-child relationship)
CREATE TABLE IF NOT EXISTS product_variants (
    variant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_product_id VARCHAR(255) NOT NULL,
    variant_sku VARCHAR(255) NOT NULL UNIQUE,
    variant_name VARCHAR(255),
    is_master BOOLEAN DEFAULT false, -- Is this the master/default variant?
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Variant attribute values (specific values for each variant)
CREATE TABLE IF NOT EXISTS variant_attribute_values (
    value_id SERIAL PRIMARY KEY,
    variant_id UUID NOT NULL,
    attribute_id INTEGER NOT NULL,
    attribute_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (variant_id) REFERENCES product_variants(variant_id) ON DELETE CASCADE,
    FOREIGN KEY (attribute_id) REFERENCES variant_attributes(attribute_id) ON DELETE CASCADE,
    UNIQUE(variant_id, attribute_id)
);

-- Variant-specific pricing
CREATE TABLE IF NOT EXISTS variant_pricing (
    pricing_id SERIAL PRIMARY KEY,
    variant_id UUID NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    compare_at_price DECIMAL(10, 2), -- Original price for showing discounts
    cost DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (variant_id) REFERENCES product_variants(variant_id) ON DELETE CASCADE
);

-- =====================================================
-- 2. PRODUCT BUNDLES & KITS
-- =====================================================

-- Bundle definitions
CREATE TABLE IF NOT EXISTS product_bundles (
    bundle_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bundle_name VARCHAR(255) NOT NULL,
    bundle_description TEXT,
    bundle_sku VARCHAR(255) NOT NULL UNIQUE,
    bundle_type VARCHAR(50) NOT NULL, -- fixed, flexible, custom
    pricing_strategy VARCHAR(50) NOT NULL, -- fixed_price, percentage_discount, component_sum
    bundle_price DECIMAL(10, 2),
    discount_percentage DECIMAL(5, 2),
    is_active BOOLEAN DEFAULT true,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP,
    max_quantity INTEGER, -- Max quantity that can be purchased
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Components in each bundle
CREATE TABLE IF NOT EXISTS bundle_components (
    component_id SERIAL PRIMARY KEY,
    bundle_id UUID NOT NULL,
    product_id VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    is_required BOOLEAN DEFAULT true,
    can_substitute BOOLEAN DEFAULT false,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bundle_id) REFERENCES product_bundles(bundle_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Bundle pricing rules
CREATE TABLE IF NOT EXISTS bundle_pricing_rules (
    rule_id SERIAL PRIMARY KEY,
    bundle_id UUID NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- quantity_discount, customer_segment, time_based
    rule_condition JSONB NOT NULL, -- Flexible conditions
    discount_type VARCHAR(50) NOT NULL, -- percentage, fixed_amount
    discount_value DECIMAL(10, 2) NOT NULL,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bundle_id) REFERENCES product_bundles(bundle_id) ON DELETE CASCADE
);

-- =====================================================
-- 3. PRODUCT IMAGES & MEDIA
-- =====================================================

-- Product images
CREATE TABLE IF NOT EXISTS product_images (
    image_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(255) NOT NULL,
    image_url TEXT NOT NULL,
    image_alt_text VARCHAR(255),
    image_caption TEXT,
    is_primary BOOLEAN DEFAULT false,
    display_order INTEGER DEFAULT 0,
    width INTEGER,
    height INTEGER,
    file_size INTEGER, -- in bytes
    mime_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Product media (videos, 360 views, etc.)
CREATE TABLE IF NOT EXISTS product_media (
    media_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(255) NOT NULL,
    media_type VARCHAR(50) NOT NULL, -- video, 360_view, pdf, document
    media_url TEXT NOT NULL,
    thumbnail_url TEXT,
    media_title VARCHAR(255),
    media_description TEXT,
    duration INTEGER, -- for videos, in seconds
    file_size INTEGER,
    mime_type VARCHAR(50),
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Image variants (thumbnail, full-size, zoom)
CREATE TABLE IF NOT EXISTS image_variants (
    variant_id SERIAL PRIMARY KEY,
    image_id UUID NOT NULL,
    variant_type VARCHAR(50) NOT NULL, -- thumbnail, medium, large, zoom
    image_url TEXT NOT NULL,
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (image_id) REFERENCES product_images(image_id) ON DELETE CASCADE,
    UNIQUE(image_id, variant_type)
);

-- =====================================================
-- 4. PRODUCT CATEGORIES & TAXONOMY
-- =====================================================

-- Hierarchical category structure
CREATE TABLE IF NOT EXISTS product_categories (
    category_id SERIAL PRIMARY KEY,
    parent_id INTEGER,
    category_name VARCHAR(255) NOT NULL,
    category_slug VARCHAR(255) NOT NULL UNIQUE,
    category_description TEXT,
    category_image_url TEXT,
    level INTEGER DEFAULT 0, -- Depth in hierarchy
    path TEXT, -- Materialized path for efficient queries
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    seo_title VARCHAR(255),
    seo_description TEXT,
    seo_keywords TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES product_categories(category_id) ON DELETE CASCADE
);

-- Category-specific attributes
CREATE TABLE IF NOT EXISTS category_attributes (
    attribute_id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL,
    attribute_name VARCHAR(100) NOT NULL,
    attribute_type VARCHAR(50) NOT NULL, -- text, number, boolean, date, select
    is_required BOOLEAN DEFAULT false,
    is_filterable BOOLEAN DEFAULT true,
    is_searchable BOOLEAN DEFAULT true,
    default_value TEXT,
    validation_rules JSONB,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES product_categories(category_id) ON DELETE CASCADE
);

-- Product-category mapping (many-to-many)
CREATE TABLE IF NOT EXISTS product_category_mapping (
    mapping_id SERIAL PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    category_id INTEGER NOT NULL,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES product_categories(category_id) ON DELETE CASCADE,
    UNIQUE(product_id, category_id)
);

-- =====================================================
-- 5. PRODUCT ATTRIBUTES & SPECIFICATIONS
-- =====================================================

-- Attribute groups (Technical Specs, Dimensions, etc.)
CREATE TABLE IF NOT EXISTS attribute_groups (
    group_id SERIAL PRIMARY KEY,
    group_name VARCHAR(100) NOT NULL UNIQUE,
    group_description TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product attribute definitions
CREATE TABLE IF NOT EXISTS product_attributes (
    attribute_id SERIAL PRIMARY KEY,
    group_id INTEGER,
    attribute_name VARCHAR(100) NOT NULL,
    attribute_code VARCHAR(100) NOT NULL UNIQUE,
    attribute_type VARCHAR(50) NOT NULL, -- text, number, boolean, date, select, multiselect
    unit VARCHAR(50), -- kg, cm, watts, etc.
    is_required BOOLEAN DEFAULT false,
    is_filterable BOOLEAN DEFAULT true,
    is_searchable BOOLEAN DEFAULT true,
    is_comparable BOOLEAN DEFAULT true,
    validation_rules JSONB,
    possible_values JSONB, -- For select/multiselect types
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES attribute_groups(group_id) ON DELETE SET NULL
);

-- Product attribute values
CREATE TABLE IF NOT EXISTS product_attribute_values (
    value_id SERIAL PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    attribute_id INTEGER NOT NULL,
    attribute_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (attribute_id) REFERENCES product_attributes(attribute_id) ON DELETE CASCADE,
    UNIQUE(product_id, attribute_id)
);

-- =====================================================
-- 6. PRICING RULES & STRATEGIES
-- =====================================================

-- Pricing rule definitions
CREATE TABLE IF NOT EXISTS pricing_rules (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(255) NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- tiered, segment, geographic, time_based, cost_plus
    rule_config JSONB NOT NULL, -- Flexible configuration
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Quantity-based pricing tiers
CREATE TABLE IF NOT EXISTS pricing_tiers (
    tier_id SERIAL PRIMARY KEY,
    rule_id UUID NOT NULL,
    min_quantity INTEGER NOT NULL,
    max_quantity INTEGER,
    price DECIMAL(10, 2) NOT NULL,
    discount_percentage DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rule_id) REFERENCES pricing_rules(rule_id) ON DELETE CASCADE
);

-- Price history and audit trail
CREATE TABLE IF NOT EXISTS price_history (
    history_id SERIAL PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    old_price DECIMAL(10, 2),
    new_price DECIMAL(10, 2) NOT NULL,
    change_reason TEXT,
    changed_by VARCHAR(255),
    change_type VARCHAR(50), -- manual, rule_based, automated, competitor_match
    effective_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Competitor price tracking
CREATE TABLE IF NOT EXISTS competitor_prices (
    tracking_id SERIAL PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    competitor_name VARCHAR(255) NOT NULL,
    competitor_url TEXT,
    competitor_price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    is_available BOOLEAN DEFAULT true,
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- =====================================================
-- 7. PRODUCT REVIEWS & RATINGS
-- =====================================================

-- Product reviews
CREATE TABLE IF NOT EXISTS product_reviews (
    review_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(255) NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    order_id VARCHAR(255), -- Link to verified purchase
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_title VARCHAR(255),
    review_text TEXT,
    is_verified_purchase BOOLEAN DEFAULT false,
    is_approved BOOLEAN DEFAULT false,
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Review images
CREATE TABLE IF NOT EXISTS review_images (
    image_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL,
    image_url TEXT NOT NULL,
    image_caption TEXT,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES product_reviews(review_id) ON DELETE CASCADE
);

-- Review votes (helpful/not helpful)
CREATE TABLE IF NOT EXISTS review_votes (
    vote_id SERIAL PRIMARY KEY,
    review_id UUID NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    vote_type VARCHAR(20) NOT NULL, -- helpful, not_helpful
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES product_reviews(review_id) ON DELETE CASCADE,
    UNIQUE(review_id, customer_id)
);

-- Seller responses to reviews
CREATE TABLE IF NOT EXISTS review_responses (
    response_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL,
    response_text TEXT NOT NULL,
    responded_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES product_reviews(review_id) ON DELETE CASCADE
);

-- =====================================================
-- 8. PRODUCT INVENTORY TRACKING
-- =====================================================

-- Multi-location inventory
CREATE TABLE IF NOT EXISTS product_inventory (
    inventory_id SERIAL PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    location_id VARCHAR(255) NOT NULL,
    quantity_available INTEGER NOT NULL DEFAULT 0,
    quantity_reserved INTEGER NOT NULL DEFAULT 0,
    quantity_on_order INTEGER NOT NULL DEFAULT 0,
    reorder_point INTEGER DEFAULT 0,
    reorder_quantity INTEGER DEFAULT 0,
    last_counted TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE(product_id, location_id)
);

-- Inventory transactions (movements)
CREATE TABLE IF NOT EXISTS inventory_transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(255) NOT NULL,
    location_id VARCHAR(255) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL, -- received, sold, adjusted, transferred, returned
    quantity INTEGER NOT NULL, -- Positive for additions, negative for reductions
    reference_id VARCHAR(255), -- Order ID, PO ID, etc.
    reference_type VARCHAR(50), -- order, purchase_order, adjustment, transfer
    notes TEXT,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Inventory reservations
CREATE TABLE IF NOT EXISTS inventory_reservations (
    reservation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(255) NOT NULL,
    location_id VARCHAR(255) NOT NULL,
    order_id VARCHAR(255) NOT NULL,
    quantity_reserved INTEGER NOT NULL,
    reserved_until TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    released_at TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Batch/lot tracking
CREATE TABLE IF NOT EXISTS inventory_batches (
    batch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(255) NOT NULL,
    location_id VARCHAR(255) NOT NULL,
    batch_number VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL,
    manufacture_date DATE,
    expiration_date DATE,
    received_date DATE DEFAULT CURRENT_DATE,
    supplier_id VARCHAR(255),
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE(product_id, batch_number)
);

-- =====================================================
-- 9. PRODUCT RELATIONSHIPS
-- =====================================================

-- Product relationships (related, cross-sell, up-sell, etc.)
CREATE TABLE IF NOT EXISTS product_relationships (
    relationship_id SERIAL PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    related_product_id VARCHAR(255) NOT NULL,
    relationship_type VARCHAR(50) NOT NULL, -- related, cross_sell, up_sell, alternative, accessory, frequently_bought_together
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (related_product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE(product_id, related_product_id, relationship_type)
);

-- AI-generated product recommendations
CREATE TABLE IF NOT EXISTS product_recommendations (
    recommendation_id SERIAL PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL,
    recommended_product_id VARCHAR(255) NOT NULL,
    recommendation_type VARCHAR(50) NOT NULL, -- ai_similar, ai_complementary, ai_trending
    confidence_score DECIMAL(5, 4), -- 0.0000 to 1.0000
    recommendation_reason TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (recommended_product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- =====================================================
-- 10. PRODUCT LIFECYCLE MANAGEMENT
-- =====================================================

-- Product lifecycle status tracking
CREATE TABLE IF NOT EXISTS product_lifecycle (
    lifecycle_id SERIAL PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL, -- draft, pending_approval, active, discontinued, archived
    launch_date DATE,
    discontinue_date DATE,
    end_of_life_date DATE,
    status_reason TEXT,
    changed_by VARCHAR(255),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Product version history
CREATE TABLE IF NOT EXISTS product_versions (
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(255) NOT NULL,
    version_number INTEGER NOT NULL,
    version_data JSONB NOT NULL, -- Complete product data snapshot
    change_summary TEXT,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Product change audit trail
CREATE TABLE IF NOT EXISTS product_changes (
    change_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(255) NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    change_type VARCHAR(50), -- created, updated, deleted
    changed_by VARCHAR(255),
    change_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Product approval workflow
CREATE TABLE IF NOT EXISTS product_approvals (
    approval_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(255) NOT NULL,
    approval_type VARCHAR(50) NOT NULL, -- new_product, price_change, major_update
    requested_by VARCHAR(255) NOT NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, approved, rejected
    review_notes TEXT,
    approval_data JSONB, -- Data being approved
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Product Variants Indexes
CREATE INDEX IF NOT EXISTS idx_product_variants_parent ON product_variants(parent_product_id, is_active);
CREATE INDEX IF NOT EXISTS idx_product_variants_sku ON product_variants(variant_sku);
CREATE INDEX IF NOT EXISTS idx_variant_attribute_values_variant ON variant_attribute_values(variant_id);
CREATE INDEX IF NOT EXISTS idx_variant_pricing_variant ON variant_pricing(variant_id, is_active);

-- Product Bundles Indexes
CREATE INDEX IF NOT EXISTS idx_product_bundles_active ON product_bundles(is_active, valid_from, valid_to);
CREATE INDEX IF NOT EXISTS idx_product_bundles_sku ON product_bundles(bundle_sku);
CREATE INDEX IF NOT EXISTS idx_bundle_components_bundle ON bundle_components(bundle_id);
CREATE INDEX IF NOT EXISTS idx_bundle_components_product ON bundle_components(product_id);

-- Product Media Indexes
CREATE INDEX IF NOT EXISTS idx_product_images_product ON product_images(product_id, display_order);
CREATE INDEX IF NOT EXISTS idx_product_images_primary ON product_images(product_id, is_primary);
CREATE INDEX IF NOT EXISTS idx_product_media_product ON product_media(product_id, media_type);
CREATE INDEX IF NOT EXISTS idx_image_variants_image ON image_variants(image_id, variant_type);

-- Product Categories Indexes
CREATE INDEX IF NOT EXISTS idx_product_categories_parent ON product_categories(parent_id, is_active);
CREATE INDEX IF NOT EXISTS idx_product_categories_slug ON product_categories(category_slug);
CREATE INDEX IF NOT EXISTS idx_product_categories_path ON product_categories(path);
CREATE INDEX IF NOT EXISTS idx_category_attributes_category ON category_attributes(category_id);
CREATE INDEX IF NOT EXISTS idx_product_category_mapping_product ON product_category_mapping(product_id);
CREATE INDEX IF NOT EXISTS idx_product_category_mapping_category ON product_category_mapping(category_id);

-- Product Attributes Indexes
CREATE INDEX IF NOT EXISTS idx_product_attributes_code ON product_attributes(attribute_code);
CREATE INDEX IF NOT EXISTS idx_product_attributes_group ON product_attributes(group_id);
CREATE INDEX IF NOT EXISTS idx_product_attribute_values_product ON product_attribute_values(product_id);
CREATE INDEX IF NOT EXISTS idx_product_attribute_values_attribute ON product_attribute_values(attribute_id);

-- Pricing Rules Indexes
CREATE INDEX IF NOT EXISTS idx_pricing_rules_product ON pricing_rules(product_id, is_active);
CREATE INDEX IF NOT EXISTS idx_pricing_rules_valid ON pricing_rules(valid_from, valid_to, is_active);
CREATE INDEX IF NOT EXISTS idx_pricing_tiers_rule ON pricing_tiers(rule_id, min_quantity);
CREATE INDEX IF NOT EXISTS idx_price_history_product ON price_history(product_id, effective_date DESC);
CREATE INDEX IF NOT EXISTS idx_competitor_prices_product ON competitor_prices(product_id, last_checked DESC);

-- Product Reviews Indexes
CREATE INDEX IF NOT EXISTS idx_product_reviews_product ON product_reviews(product_id, is_approved, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_product_reviews_customer ON product_reviews(customer_id);
CREATE INDEX IF NOT EXISTS idx_product_reviews_rating ON product_reviews(product_id, rating);
CREATE INDEX IF NOT EXISTS idx_review_images_review ON review_images(review_id);
CREATE INDEX IF NOT EXISTS idx_review_votes_review ON review_votes(review_id);

-- Product Inventory Indexes
CREATE INDEX IF NOT EXISTS idx_product_inventory_product ON product_inventory(product_id);
CREATE INDEX IF NOT EXISTS idx_product_inventory_location ON product_inventory(location_id);
CREATE INDEX IF NOT EXISTS idx_product_inventory_low_stock ON product_inventory(product_id) WHERE quantity_available <= reorder_point;
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_product ON inventory_transactions(product_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_inventory_reservations_product ON inventory_reservations(product_id, is_active);
CREATE INDEX IF NOT EXISTS idx_inventory_reservations_order ON inventory_reservations(order_id);
CREATE INDEX IF NOT EXISTS idx_inventory_batches_product ON inventory_batches(product_id, is_active);

-- Product Relationships Indexes
CREATE INDEX IF NOT EXISTS idx_product_relationships_product ON product_relationships(product_id, relationship_type);
CREATE INDEX IF NOT EXISTS idx_product_relationships_related ON product_relationships(related_product_id);
CREATE INDEX IF NOT EXISTS idx_product_recommendations_product ON product_recommendations(product_id, is_active);

-- Product Lifecycle Indexes
CREATE INDEX IF NOT EXISTS idx_product_lifecycle_status ON product_lifecycle(status, changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_product_versions_product ON product_versions(product_id, version_number DESC);
CREATE INDEX IF NOT EXISTS idx_product_changes_product ON product_changes(product_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_product_approvals_status ON product_approvals(status, requested_at DESC);

-- =====================================================
-- MATERIALIZED VIEWS FOR ANALYTICS
-- =====================================================

-- Product inventory summary
CREATE MATERIALIZED VIEW IF NOT EXISTS product_inventory_summary AS
SELECT 
    pi.product_id,
    SUM(pi.quantity_available) as total_available,
    SUM(pi.quantity_reserved) as total_reserved,
    SUM(pi.quantity_on_order) as total_on_order,
    SUM(pi.quantity_available) - SUM(pi.quantity_reserved) as sellable_quantity,
    COUNT(DISTINCT pi.location_id) as location_count,
    MIN(pi.quantity_available) as min_location_stock,
    MAX(pi.quantity_available) as max_location_stock,
    MAX(pi.last_updated) as last_inventory_update
FROM product_inventory pi
GROUP BY pi.product_id;

CREATE UNIQUE INDEX IF NOT EXISTS idx_product_inventory_summary_product ON product_inventory_summary(product_id);

-- Product rating summary
CREATE MATERIALIZED VIEW IF NOT EXISTS product_rating_summary AS
SELECT 
    pr.product_id,
    COUNT(*) as total_reviews,
    COUNT(CASE WHEN pr.is_verified_purchase THEN 1 END) as verified_reviews,
    AVG(pr.rating) as average_rating,
    COUNT(CASE WHEN pr.rating = 5 THEN 1 END) as five_star_count,
    COUNT(CASE WHEN pr.rating = 4 THEN 1 END) as four_star_count,
    COUNT(CASE WHEN pr.rating = 3 THEN 1 END) as three_star_count,
    COUNT(CASE WHEN pr.rating = 2 THEN 1 END) as two_star_count,
    COUNT(CASE WHEN pr.rating = 1 THEN 1 END) as one_star_count,
    SUM(pr.helpful_count) as total_helpful_votes,
    MAX(pr.created_at) as latest_review_date
FROM product_reviews pr
WHERE pr.is_approved = true
GROUP BY pr.product_id;

CREATE UNIQUE INDEX IF NOT EXISTS idx_product_rating_summary_product ON product_rating_summary(product_id);

-- Product pricing summary
CREATE MATERIALIZED VIEW IF NOT EXISTS product_pricing_summary AS
SELECT 
    p.id as product_id,
    p.price as base_price,
    p.cost as base_cost,
    COALESCE(MIN(pt.price), p.price) as min_tiered_price,
    COALESCE(MAX(pt.price), p.price) as max_tiered_price,
    COUNT(DISTINCT pr.rule_id) as active_pricing_rules,
    MAX(ph.effective_date) as last_price_change,
    COALESCE(AVG(cp.competitor_price), 0) as avg_competitor_price,
    COALESCE(MIN(cp.competitor_price), 0) as min_competitor_price
FROM products p
LEFT JOIN pricing_rules pr ON p.id = pr.product_id 
    AND pr.is_active = true 
    AND CURRENT_TIMESTAMP BETWEEN pr.valid_from AND COALESCE(pr.valid_to, CURRENT_TIMESTAMP + INTERVAL '100 years')
LEFT JOIN pricing_tiers pt ON pr.rule_id = pt.rule_id
LEFT JOIN price_history ph ON p.id = ph.product_id
LEFT JOIN competitor_prices cp ON p.id = cp.product_id 
    AND cp.last_checked > CURRENT_TIMESTAMP - INTERVAL '7 days'
GROUP BY p.id, p.price, p.cost;

CREATE UNIQUE INDEX IF NOT EXISTS idx_product_pricing_summary_product ON product_pricing_summary(product_id);

-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to relevant tables
CREATE TRIGGER update_variant_attributes_updated_at BEFORE UPDATE ON variant_attributes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_product_variants_updated_at BEFORE UPDATE ON product_variants FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_variant_pricing_updated_at BEFORE UPDATE ON variant_pricing FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_product_bundles_updated_at BEFORE UPDATE ON product_bundles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_product_images_updated_at BEFORE UPDATE ON product_images FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_product_media_updated_at BEFORE UPDATE ON product_media FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_product_categories_updated_at BEFORE UPDATE ON product_categories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_attribute_groups_updated_at BEFORE UPDATE ON attribute_groups FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_product_attributes_updated_at BEFORE UPDATE ON product_attributes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_product_attribute_values_updated_at BEFORE UPDATE ON product_attribute_values FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pricing_rules_updated_at BEFORE UPDATE ON pricing_rules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_product_reviews_updated_at BEFORE UPDATE ON product_reviews FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_review_responses_updated_at BEFORE UPDATE ON review_responses FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON TABLE product_variants IS 'Stores product variants with parent-child relationships for managing size, color, and other variations';
COMMENT ON TABLE product_bundles IS 'Defines product bundles and kits for promotional offerings';
COMMENT ON TABLE product_images IS 'Manages multiple images per product with ordering and primary image designation';
COMMENT ON TABLE product_categories IS 'Hierarchical category structure with materialized path for efficient queries';
COMMENT ON TABLE product_attributes IS 'Flexible custom attributes system for product specifications';
COMMENT ON TABLE pricing_rules IS 'Advanced pricing rules including tiered, segment-based, and time-based pricing';
COMMENT ON TABLE product_reviews IS 'Customer reviews and ratings with verification and moderation workflow';
COMMENT ON TABLE product_inventory IS 'Multi-location inventory tracking with reservations and reorder points';
COMMENT ON TABLE product_relationships IS 'Product relationships for cross-selling, up-selling, and recommendations';
COMMENT ON TABLE product_lifecycle IS 'Tracks product status through its lifecycle from draft to archived';

-- =====================================================
-- END OF MIGRATION
-- =====================================================

-- Refresh materialized views
REFRESH MATERIALIZED VIEW CONCURRENTLY product_inventory_summary;
REFRESH MATERIALIZED VIEW CONCURRENTLY product_rating_summary;
REFRESH MATERIALIZED VIEW CONCURRENTLY product_pricing_summary;

