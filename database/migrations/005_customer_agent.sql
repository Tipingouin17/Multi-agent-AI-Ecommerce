-- =====================================================
-- CUSTOMER AGENT DATABASE MIGRATION
-- =====================================================
-- This migration creates comprehensive customer management tables
-- for customer profiles, preferences, loyalty, segments, and interactions.

-- =====================================================
-- 1. CUSTOMER PROFILES (Enhanced)
-- =====================================================

CREATE TABLE IF NOT EXISTS customer_profiles (
    customer_id VARCHAR(100) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    date_of_birth DATE,
    gender VARCHAR(20),
    customer_type VARCHAR(50) DEFAULT 'individual', -- 'individual', 'business'
    account_status VARCHAR(50) DEFAULT 'active', -- 'active', 'inactive', 'suspended', 'blocked'
    email_verified BOOLEAN DEFAULT false,
    phone_verified BOOLEAN DEFAULT false,
    kyc_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'verified', 'failed'
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_customer_profiles_email ON customer_profiles(email);
CREATE INDEX idx_customer_profiles_phone ON customer_profiles(phone);
CREATE INDEX idx_customer_profiles_status ON customer_profiles(account_status);
CREATE INDEX idx_customer_profiles_type ON customer_profiles(customer_type);
CREATE INDEX idx_customer_profiles_registration ON customer_profiles(registration_date DESC);

COMMENT ON TABLE customer_profiles IS 'Comprehensive customer profile information';

-- =====================================================
-- 2. CUSTOMER ADDRESSES
-- =====================================================

CREATE TABLE IF NOT EXISTS customer_addresses (
    address_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(100) NOT NULL REFERENCES customer_profiles(customer_id) ON DELETE CASCADE,
    address_type VARCHAR(50) NOT NULL, -- 'shipping', 'billing', 'both'
    address_label VARCHAR(100), -- 'Home', 'Work', 'Office', etc.
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company_name VARCHAR(200),
    street_address_1 VARCHAR(500) NOT NULL,
    street_address_2 VARCHAR(500),
    city VARCHAR(100) NOT NULL,
    state_province VARCHAR(100),
    postal_code VARCHAR(20) NOT NULL,
    country_code VARCHAR(10) NOT NULL,
    phone VARCHAR(50),
    is_default BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    delivery_instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_customer_addresses_customer ON customer_addresses(customer_id);
CREATE INDEX idx_customer_addresses_type ON customer_addresses(address_type);
CREATE INDEX idx_customer_addresses_default ON customer_addresses(is_default);
CREATE INDEX idx_customer_addresses_country ON customer_addresses(country_code);

COMMENT ON TABLE customer_addresses IS 'Customer shipping and billing addresses';

-- =====================================================
-- 3. CUSTOMER PREFERENCES
-- =====================================================

CREATE TABLE IF NOT EXISTS customer_preferences (
    preference_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(100) NOT NULL REFERENCES customer_profiles(customer_id) ON DELETE CASCADE,
    preference_category VARCHAR(100) NOT NULL, -- 'communication', 'privacy', 'shopping', 'notifications'
    preference_key VARCHAR(100) NOT NULL,
    preference_value JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(customer_id, preference_category, preference_key)
);

CREATE INDEX idx_customer_preferences_customer ON customer_preferences(customer_id);
CREATE INDEX idx_customer_preferences_category ON customer_preferences(preference_category);

COMMENT ON TABLE customer_preferences IS 'Customer preferences and settings';

-- =====================================================
-- 4. CUSTOMER LOYALTY PROGRAM
-- =====================================================

CREATE TABLE IF NOT EXISTS customer_loyalty (
    loyalty_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(100) NOT NULL UNIQUE REFERENCES customer_profiles(customer_id) ON DELETE CASCADE,
    loyalty_tier VARCHAR(50) DEFAULT 'bronze', -- 'bronze', 'silver', 'gold', 'platinum', 'diamond'
    points_balance INTEGER DEFAULT 0,
    points_lifetime INTEGER DEFAULT 0,
    tier_start_date DATE DEFAULT CURRENT_DATE,
    tier_expiry_date DATE,
    next_tier VARCHAR(50),
    points_to_next_tier INTEGER,
    referral_code VARCHAR(50) UNIQUE,
    referrals_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_customer_loyalty_customer ON customer_loyalty(customer_id);
CREATE INDEX idx_customer_loyalty_tier ON customer_loyalty(loyalty_tier);
CREATE INDEX idx_customer_loyalty_referral ON customer_loyalty(referral_code);

COMMENT ON TABLE customer_loyalty IS 'Customer loyalty program membership';

-- =====================================================
-- 5. LOYALTY TRANSACTIONS
-- =====================================================

CREATE TABLE IF NOT EXISTS loyalty_transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(100) NOT NULL REFERENCES customer_profiles(customer_id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL, -- 'earn', 'redeem', 'expire', 'adjustment', 'bonus'
    points_amount INTEGER NOT NULL,
    points_balance_after INTEGER NOT NULL,
    reference_id VARCHAR(100),
    reference_type VARCHAR(50), -- 'order', 'review', 'referral', 'promotion'
    description TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_loyalty_transactions_customer ON loyalty_transactions(customer_id);
CREATE INDEX idx_loyalty_transactions_type ON loyalty_transactions(transaction_type);
CREATE INDEX idx_loyalty_transactions_reference ON loyalty_transactions(reference_id, reference_type);
CREATE INDEX idx_loyalty_transactions_created ON loyalty_transactions(created_at DESC);

COMMENT ON TABLE loyalty_transactions IS 'Loyalty points transaction history';

-- =====================================================
-- 6. CUSTOMER SEGMENTS
-- =====================================================

CREATE TABLE IF NOT EXISTS customer_segments (
    segment_id SERIAL PRIMARY KEY,
    segment_name VARCHAR(100) UNIQUE NOT NULL,
    segment_description TEXT,
    segment_criteria JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 0,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_customer_segments_active ON customer_segments(is_active);
CREATE INDEX idx_customer_segments_priority ON customer_segments(priority DESC);

COMMENT ON TABLE customer_segments IS 'Customer segmentation definitions';

-- =====================================================
-- 7. CUSTOMER SEGMENT MEMBERSHIP
-- =====================================================

CREATE TABLE IF NOT EXISTS customer_segment_membership (
    membership_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(100) NOT NULL REFERENCES customer_profiles(customer_id) ON DELETE CASCADE,
    segment_id INTEGER NOT NULL REFERENCES customer_segments(segment_id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(50) DEFAULT 'system',
    UNIQUE(customer_id, segment_id)
);

CREATE INDEX idx_customer_segment_membership_customer ON customer_segment_membership(customer_id);
CREATE INDEX idx_customer_segment_membership_segment ON customer_segment_membership(segment_id);

COMMENT ON TABLE customer_segment_membership IS 'Customer membership in segments';

-- =====================================================
-- 8. CUSTOMER INTERACTIONS
-- =====================================================

CREATE TABLE IF NOT EXISTS customer_interactions (
    interaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(100) NOT NULL REFERENCES customer_profiles(customer_id) ON DELETE CASCADE,
    interaction_type VARCHAR(50) NOT NULL, -- 'support_ticket', 'chat', 'email', 'phone', 'review', 'feedback'
    interaction_channel VARCHAR(50), -- 'web', 'mobile', 'email', 'phone', 'chat'
    subject VARCHAR(500),
    description TEXT,
    status VARCHAR(50) DEFAULT 'open', -- 'open', 'in_progress', 'resolved', 'closed'
    priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
    assigned_to VARCHAR(100),
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    satisfaction_rating INTEGER, -- 1-5 stars
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_customer_interactions_customer ON customer_interactions(customer_id);
CREATE INDEX idx_customer_interactions_type ON customer_interactions(interaction_type);
CREATE INDEX idx_customer_interactions_status ON customer_interactions(status);
CREATE INDEX idx_customer_interactions_assigned ON customer_interactions(assigned_to);
CREATE INDEX idx_customer_interactions_created ON customer_interactions(created_at DESC);

COMMENT ON TABLE customer_interactions IS 'Customer service interactions and support tickets';

-- =====================================================
-- 9. CUSTOMER WISHLISTS
-- =====================================================

CREATE TABLE IF NOT EXISTS customer_wishlists (
    wishlist_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(100) NOT NULL REFERENCES customer_profiles(customer_id) ON DELETE CASCADE,
    wishlist_name VARCHAR(200) DEFAULT 'My Wishlist',
    is_public BOOLEAN DEFAULT false,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_customer_wishlists_customer ON customer_wishlists(customer_id);
CREATE INDEX idx_customer_wishlists_public ON customer_wishlists(is_public);

COMMENT ON TABLE customer_wishlists IS 'Customer wishlists';

-- =====================================================
-- 10. WISHLIST ITEMS
-- =====================================================

CREATE TABLE IF NOT EXISTS wishlist_items (
    item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wishlist_id UUID NOT NULL REFERENCES customer_wishlists(wishlist_id) ON DELETE CASCADE,
    product_id VARCHAR(100) NOT NULL,
    variant_id UUID,
    quantity INTEGER DEFAULT 1,
    priority INTEGER DEFAULT 0,
    notes TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_wishlist_items_wishlist ON wishlist_items(wishlist_id);
CREATE INDEX idx_wishlist_items_product ON wishlist_items(product_id);
CREATE INDEX idx_wishlist_items_added ON wishlist_items(added_at DESC);

COMMENT ON TABLE wishlist_items IS 'Items in customer wishlists';

-- =====================================================
-- MATERIALIZED VIEWS
-- =====================================================

-- Customer Summary View
CREATE MATERIALIZED VIEW IF NOT EXISTS customer_summary AS
SELECT 
    cp.customer_id,
    cp.email,
    cp.first_name,
    cp.last_name,
    cp.customer_type,
    cp.account_status,
    cp.registration_date,
    cp.last_login_at,
    cl.loyalty_tier,
    cl.points_balance,
    COUNT(DISTINCT o.order_id) as total_orders,
    COALESCE(SUM(o.total_amount), 0) as lifetime_value,
    MAX(o.created_at) as last_order_date,
    COUNT(DISTINCT ci.interaction_id) as total_interactions
FROM customer_profiles cp
LEFT JOIN customer_loyalty cl ON cp.customer_id = cl.customer_id
LEFT JOIN orders o ON cp.customer_id = o.customer_id
LEFT JOIN customer_interactions ci ON cp.customer_id = ci.customer_id
GROUP BY cp.customer_id, cp.email, cp.first_name, cp.last_name, cp.customer_type,
         cp.account_status, cp.registration_date, cp.last_login_at, 
         cl.loyalty_tier, cl.points_balance;

CREATE UNIQUE INDEX idx_customer_summary_customer ON customer_summary(customer_id);
CREATE INDEX idx_customer_summary_tier ON customer_summary(loyalty_tier);
CREATE INDEX idx_customer_summary_ltv ON customer_summary(lifetime_value DESC);

COMMENT ON MATERIALIZED VIEW customer_summary IS 'Comprehensive customer summary with orders and loyalty';

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_customer_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
CREATE TRIGGER trigger_update_customer_profiles_timestamp
    BEFORE UPDATE ON customer_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_customer_timestamp();

CREATE TRIGGER trigger_update_customer_addresses_timestamp
    BEFORE UPDATE ON customer_addresses
    FOR EACH ROW
    EXECUTE FUNCTION update_customer_timestamp();

CREATE TRIGGER trigger_update_customer_preferences_timestamp
    BEFORE UPDATE ON customer_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_customer_timestamp();

CREATE TRIGGER trigger_update_customer_loyalty_timestamp
    BEFORE UPDATE ON customer_loyalty
    FOR EACH ROW
    EXECUTE FUNCTION update_customer_timestamp();

CREATE TRIGGER trigger_update_customer_segments_timestamp
    BEFORE UPDATE ON customer_segments
    FOR EACH ROW
    EXECUTE FUNCTION update_customer_timestamp();

CREATE TRIGGER trigger_update_customer_interactions_timestamp
    BEFORE UPDATE ON customer_interactions
    FOR EACH ROW
    EXECUTE FUNCTION update_customer_timestamp();

CREATE TRIGGER trigger_update_customer_wishlists_timestamp
    BEFORE UPDATE ON customer_wishlists
    FOR EACH ROW
    EXECUTE FUNCTION update_customer_timestamp();

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to refresh customer summary
CREATE OR REPLACE FUNCTION refresh_customer_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY customer_summary;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_customer_summary() IS 'Refresh customer summary materialized view';

-- =====================================================
-- INITIAL DATA
-- =====================================================

-- Insert default customer segments
INSERT INTO customer_segments (segment_name, segment_description, segment_criteria, is_active)
VALUES 
    ('VIP Customers', 'High value customers with lifetime value > $10,000', '{"lifetime_value": {"min": 10000}}', true),
    ('New Customers', 'Customers registered in the last 30 days', '{"registration_days": {"max": 30}}', true),
    ('At Risk', 'Customers who have not ordered in 90 days', '{"days_since_last_order": {"min": 90}}', true),
    ('Loyal Customers', 'Customers with 10+ orders', '{"order_count": {"min": 10}}', true)
ON CONFLICT (segment_name) DO NOTHING;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

COMMENT ON SCHEMA public IS 'Customer Agent migration 005 completed successfully';

