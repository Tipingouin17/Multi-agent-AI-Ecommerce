-- ============================================================================
-- ADVERTISING CAMPAIGN MANAGEMENT SCHEMA
-- ============================================================================
-- This migration adds tables for managing advertising campaigns across platforms
-- Based on Market Master Tool competitive analysis
-- ============================================================================

-- Advertising Campaigns table
CREATE TABLE IF NOT EXISTS advertising_campaigns (
    id SERIAL PRIMARY KEY,
    
    -- Basic Information
    name VARCHAR(255) NOT NULL,
    description TEXT,
    campaign_type VARCHAR(50) NOT NULL, -- ppc, display, social, email, retargeting
    status VARCHAR(50) DEFAULT 'draft', -- draft, active, paused, completed, cancelled
    
    -- Platform & Targeting
    platform VARCHAR(50), -- google_ads, facebook, instagram, amazon, custom
    platform_campaign_id VARCHAR(255), -- External campaign ID
    target_audience JSONB, -- Demographics, interests, behaviors
    target_locations JSONB, -- Geographic targeting
    target_devices JSONB, -- desktop, mobile, tablet
    
    -- Budget & Bidding
    budget_type VARCHAR(50), -- daily, lifetime, unlimited
    daily_budget NUMERIC(15, 2),
    total_budget NUMERIC(15, 2),
    bid_strategy VARCHAR(50), -- manual_cpc, auto_cpc, cpm, cpa
    max_bid NUMERIC(10, 2),
    
    -- Schedule
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    schedule_config JSONB, -- Day/time scheduling
    
    -- Performance Targets
    target_impressions INTEGER,
    target_clicks INTEGER,
    target_conversions INTEGER,
    target_roas NUMERIC(5, 2), -- Return on Ad Spend percentage
    
    -- Current Performance
    total_impressions INTEGER DEFAULT 0,
    total_clicks INTEGER DEFAULT 0,
    total_conversions INTEGER DEFAULT 0,
    total_spend NUMERIC(15, 2) DEFAULT 0.00,
    total_revenue NUMERIC(15, 2) DEFAULT 0.00,
    
    -- Metadata
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Ad Groups (within campaigns)
CREATE TABLE IF NOT EXISTS ad_groups (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES advertising_campaigns(id) ON DELETE CASCADE,
    
    -- Basic Information
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active', -- active, paused, archived
    
    -- Bidding
    bid_amount NUMERIC(10, 2),
    
    -- Targeting
    keywords JSONB, -- Array of keywords with match types
    negative_keywords JSONB,
    placements JSONB, -- Specific websites/apps
    
    -- Performance
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    spend NUMERIC(15, 2) DEFAULT 0.00,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ad Creatives
CREATE TABLE IF NOT EXISTS ad_creatives (
    id SERIAL PRIMARY KEY,
    ad_group_id INTEGER REFERENCES ad_groups(id) ON DELETE CASCADE,
    campaign_id INTEGER REFERENCES advertising_campaigns(id),
    
    -- Basic Information
    name VARCHAR(255) NOT NULL,
    ad_type VARCHAR(50) NOT NULL, -- text, image, video, carousel, dynamic
    status VARCHAR(50) DEFAULT 'active',
    
    -- Creative Content
    headline VARCHAR(255),
    description TEXT,
    call_to_action VARCHAR(100),
    
    -- Media Assets
    image_url TEXT,
    video_url TEXT,
    thumbnail_url TEXT,
    media_assets JSONB, -- Multiple images/videos for carousel
    
    -- Destination
    landing_page_url TEXT,
    tracking_template TEXT,
    utm_parameters JSONB,
    
    -- Performance
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    ctr NUMERIC(5, 2), -- Click-through rate
    conversion_rate NUMERIC(5, 2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Campaign Products (Products being advertised)
CREATE TABLE IF NOT EXISTS campaign_products (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES advertising_campaigns(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    
    -- Product-specific settings
    custom_bid NUMERIC(10, 2),
    priority INTEGER DEFAULT 0,
    
    -- Performance
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    revenue NUMERIC(15, 2) DEFAULT 0.00,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(campaign_id, product_id)
);

-- Campaign Performance Analytics (Daily)
CREATE TABLE IF NOT EXISTS campaign_analytics (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES advertising_campaigns(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    
    -- Traffic Metrics
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    ctr NUMERIC(5, 2), -- Click-through rate
    
    -- Cost Metrics
    spend NUMERIC(15, 2) DEFAULT 0.00,
    cpc NUMERIC(10, 2), -- Cost per click
    cpm NUMERIC(10, 2), -- Cost per thousand impressions
    
    -- Conversion Metrics
    conversions INTEGER DEFAULT 0,
    conversion_rate NUMERIC(5, 2),
    cpa NUMERIC(10, 2), -- Cost per acquisition
    
    -- Revenue Metrics
    revenue NUMERIC(15, 2) DEFAULT 0.00,
    roas NUMERIC(5, 2), -- Return on ad spend
    profit NUMERIC(15, 2),
    
    -- Engagement Metrics
    video_views INTEGER DEFAULT 0,
    video_completion_rate NUMERIC(5, 2),
    engagement_rate NUMERIC(5, 2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(campaign_id, date)
);

-- Campaign Budget Tracking
CREATE TABLE IF NOT EXISTS campaign_budget_history (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES advertising_campaigns(id) ON DELETE CASCADE,
    
    -- Budget Change
    previous_daily_budget NUMERIC(15, 2),
    new_daily_budget NUMERIC(15, 2),
    previous_total_budget NUMERIC(15, 2),
    new_total_budget NUMERIC(15, 2),
    
    -- Reason
    change_reason TEXT,
    changed_by INTEGER REFERENCES users(id),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Campaign Events Log
CREATE TABLE IF NOT EXISTS campaign_events (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES advertising_campaigns(id) ON DELETE CASCADE,
    
    -- Event Details
    event_type VARCHAR(50) NOT NULL, -- created, started, paused, resumed, completed, budget_changed, etc.
    event_data JSONB,
    event_message TEXT,
    
    -- User
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON advertising_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_platform ON advertising_campaigns(platform);
CREATE INDEX IF NOT EXISTS idx_campaigns_dates ON advertising_campaigns(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_ad_groups_campaign ON ad_groups(campaign_id);
CREATE INDEX IF NOT EXISTS idx_ad_creatives_ad_group ON ad_creatives(ad_group_id);
CREATE INDEX IF NOT EXISTS idx_ad_creatives_campaign ON ad_creatives(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_products_campaign ON campaign_products(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_products_product ON campaign_products(product_id);
CREATE INDEX IF NOT EXISTS idx_campaign_analytics_campaign ON campaign_analytics(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_analytics_date ON campaign_analytics(date);
CREATE INDEX IF NOT EXISTS idx_campaign_events_campaign ON campaign_events(campaign_id);

-- Update timestamp triggers
DROP TRIGGER IF EXISTS campaigns_updated_at_trigger ON advertising_campaigns;
CREATE TRIGGER campaigns_updated_at_trigger
    BEFORE UPDATE ON advertising_campaigns
    FOR EACH ROW
    EXECUTE FUNCTION update_offers_updated_at();

DROP TRIGGER IF EXISTS ad_groups_updated_at_trigger ON ad_groups;
CREATE TRIGGER ad_groups_updated_at_trigger
    BEFORE UPDATE ON ad_groups
    FOR EACH ROW
    EXECUTE FUNCTION update_offers_updated_at();

DROP TRIGGER IF EXISTS ad_creatives_updated_at_trigger ON ad_creatives;
CREATE TRIGGER ad_creatives_updated_at_trigger
    BEFORE UPDATE ON ad_creatives
    FOR EACH ROW
    EXECUTE FUNCTION update_offers_updated_at();

-- Comments
COMMENT ON TABLE advertising_campaigns IS 'Advertising campaigns across platforms';
COMMENT ON TABLE ad_groups IS 'Ad groups within campaigns for better organization';
COMMENT ON TABLE ad_creatives IS 'Individual ad creatives (text, image, video ads)';
COMMENT ON TABLE campaign_products IS 'Products being advertised in campaigns';
COMMENT ON TABLE campaign_analytics IS 'Daily performance analytics for campaigns';
COMMENT ON TABLE campaign_budget_history IS 'History of budget changes';
COMMENT ON TABLE campaign_events IS 'Event log for campaign activities';
