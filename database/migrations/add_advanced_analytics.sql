-- ============================================================================
-- ADVANCED ANALYTICS & REPORTING SCHEMA
-- ============================================================================
-- This migration adds comprehensive analytics and business intelligence
-- ============================================================================

-- Customer Analytics
CREATE TABLE IF NOT EXISTS customer_analytics (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    
    -- Purchase Behavior
    orders_count INTEGER DEFAULT 0,
    items_purchased INTEGER DEFAULT 0,
    total_spent NUMERIC(15, 2) DEFAULT 0.00,
    average_order_value NUMERIC(15, 2),
    
    -- Engagement
    site_visits INTEGER DEFAULT 0,
    pages_viewed INTEGER DEFAULT 0,
    time_on_site_minutes INTEGER DEFAULT 0,
    
    -- Product Interactions
    products_viewed INTEGER DEFAULT 0,
    products_added_to_cart INTEGER DEFAULT 0,
    products_wishlisted INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(customer_id, date)
);

-- Product Performance Analytics
CREATE TABLE IF NOT EXISTS product_performance (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    
    -- Sales Metrics
    units_sold INTEGER DEFAULT 0,
    revenue NUMERIC(15, 2) DEFAULT 0.00,
    profit NUMERIC(15, 2) DEFAULT 0.00,
    
    -- Engagement Metrics
    views INTEGER DEFAULT 0,
    add_to_cart_count INTEGER DEFAULT 0,
    wishlist_count INTEGER DEFAULT 0,
    
    -- Conversion Metrics
    conversion_rate NUMERIC(5, 2),
    cart_abandonment_rate NUMERIC(5, 2),
    
    -- Inventory Metrics
    stock_level INTEGER,
    days_of_inventory INTEGER,
    stockout_occurrences INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(product_id, date)
);

-- Sales Analytics (Daily aggregates)
CREATE TABLE IF NOT EXISTS sales_analytics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    
    -- Order Metrics
    total_orders INTEGER DEFAULT 0,
    completed_orders INTEGER DEFAULT 0,
    cancelled_orders INTEGER DEFAULT 0,
    pending_orders INTEGER DEFAULT 0,
    
    -- Revenue Metrics
    gross_revenue NUMERIC(15, 2) DEFAULT 0.00,
    net_revenue NUMERIC(15, 2) DEFAULT 0.00,
    discounts_given NUMERIC(15, 2) DEFAULT 0.00,
    refunds_issued NUMERIC(15, 2) DEFAULT 0.00,
    
    -- Customer Metrics
    new_customers INTEGER DEFAULT 0,
    returning_customers INTEGER DEFAULT 0,
    average_order_value NUMERIC(15, 2),
    
    -- Product Metrics
    units_sold INTEGER DEFAULT 0,
    unique_products_sold INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Category Performance
CREATE TABLE IF NOT EXISTS category_analytics (
    id SERIAL PRIMARY KEY,
    category_name VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    
    -- Sales Metrics
    orders_count INTEGER DEFAULT 0,
    units_sold INTEGER DEFAULT 0,
    revenue NUMERIC(15, 2) DEFAULT 0.00,
    
    -- Engagement
    views INTEGER DEFAULT 0,
    conversion_rate NUMERIC(5, 2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(category_name, date)
);

-- Customer Cohorts
CREATE TABLE IF NOT EXISTS customer_cohorts (
    id SERIAL PRIMARY KEY,
    cohort_month DATE NOT NULL, -- First purchase month
    months_since_first_purchase INTEGER NOT NULL,
    
    -- Cohort Metrics
    customers_count INTEGER DEFAULT 0,
    active_customers INTEGER DEFAULT 0,
    retention_rate NUMERIC(5, 2),
    
    -- Revenue Metrics
    total_revenue NUMERIC(15, 2) DEFAULT 0.00,
    average_revenue_per_customer NUMERIC(15, 2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(cohort_month, months_since_first_purchase)
);

-- Customer Segments
CREATE TABLE IF NOT EXISTS customer_segments (
    id SERIAL PRIMARY KEY,
    
    -- Segment Definition
    segment_name VARCHAR(255) NOT NULL UNIQUE,
    segment_type VARCHAR(50), -- rfm, behavioral, demographic, custom
    description TEXT,
    
    -- Segment Criteria
    criteria JSONB NOT NULL,
    
    -- Segment Stats
    customer_count INTEGER DEFAULT 0,
    total_revenue NUMERIC(15, 2) DEFAULT 0.00,
    average_order_value NUMERIC(15, 2),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer Segment Membership
CREATE TABLE IF NOT EXISTS customer_segment_members (
    id SERIAL PRIMARY KEY,
    segment_id INTEGER REFERENCES customer_segments(id) ON DELETE CASCADE,
    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    
    -- Membership Details
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    score NUMERIC(10, 2), -- Relevance score for this segment
    
    UNIQUE(segment_id, customer_id)
);

-- Business Reports
CREATE TABLE IF NOT EXISTS business_reports (
    id SERIAL PRIMARY KEY,
    
    -- Report Details
    report_name VARCHAR(255) NOT NULL,
    report_type VARCHAR(50) NOT NULL, -- sales, inventory, customer, financial, custom
    description TEXT,
    
    -- Schedule
    schedule_type VARCHAR(50), -- daily, weekly, monthly, custom
    schedule_config JSONB,
    
    -- Recipients
    recipients JSONB, -- Array of email addresses
    
    -- Report Configuration
    filters JSONB,
    metrics JSONB,
    visualization_config JSONB,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    last_generated_at TIMESTAMP,
    
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Report Execution Log
CREATE TABLE IF NOT EXISTS report_executions (
    id SERIAL PRIMARY KEY,
    report_id INTEGER REFERENCES business_reports(id) ON DELETE CASCADE,
    
    -- Execution Details
    execution_status VARCHAR(50), -- pending, running, completed, failed
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Results
    file_path TEXT,
    file_size_bytes INTEGER,
    rows_generated INTEGER,
    
    -- Error tracking
    error_message TEXT,
    
    triggered_by VARCHAR(50) -- scheduled, manual, api
);

-- Custom Metrics
CREATE TABLE IF NOT EXISTS custom_metrics (
    id SERIAL PRIMARY KEY,
    
    -- Metric Definition
    metric_name VARCHAR(255) NOT NULL UNIQUE,
    metric_type VARCHAR(50), -- sum, average, count, ratio, custom
    description TEXT,
    
    -- Calculation
    calculation_formula TEXT, -- SQL or expression
    data_source VARCHAR(100), -- orders, customers, products, custom
    
    -- Display
    unit VARCHAR(50), -- currency, percentage, count, etc.
    format_string VARCHAR(100),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Metric Values (Time series data for custom metrics)
CREATE TABLE IF NOT EXISTS metric_values (
    id SERIAL PRIMARY KEY,
    metric_id INTEGER REFERENCES custom_metrics(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    
    value NUMERIC(20, 4),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(metric_id, date)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_customer_analytics_customer ON customer_analytics(customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_analytics_date ON customer_analytics(date);
CREATE INDEX IF NOT EXISTS idx_product_performance_product ON product_performance(product_id);
CREATE INDEX IF NOT EXISTS idx_product_performance_date ON product_performance(date);
CREATE INDEX IF NOT EXISTS idx_sales_analytics_date ON sales_analytics(date);
CREATE INDEX IF NOT EXISTS idx_category_analytics_category ON category_analytics(category_name);
CREATE INDEX IF NOT EXISTS idx_category_analytics_date ON category_analytics(date);
CREATE INDEX IF NOT EXISTS idx_customer_cohorts_cohort_month ON customer_cohorts(cohort_month);
CREATE INDEX IF NOT EXISTS idx_customer_segment_members_segment ON customer_segment_members(segment_id);
CREATE INDEX IF NOT EXISTS idx_customer_segment_members_customer ON customer_segment_members(customer_id);
CREATE INDEX IF NOT EXISTS idx_report_executions_report ON report_executions(report_id);
CREATE INDEX IF NOT EXISTS idx_metric_values_metric ON metric_values(metric_id);
CREATE INDEX IF NOT EXISTS idx_metric_values_date ON metric_values(date);

-- Update timestamp triggers
DROP TRIGGER IF EXISTS customer_segments_updated_at_trigger ON customer_segments;
CREATE TRIGGER customer_segments_updated_at_trigger
    BEFORE UPDATE ON customer_segments
    FOR EACH ROW
    EXECUTE FUNCTION update_offers_updated_at();

DROP TRIGGER IF EXISTS business_reports_updated_at_trigger ON business_reports;
CREATE TRIGGER business_reports_updated_at_trigger
    BEFORE UPDATE ON business_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_offers_updated_at();

DROP TRIGGER IF EXISTS custom_metrics_updated_at_trigger ON custom_metrics;
CREATE TRIGGER custom_metrics_updated_at_trigger
    BEFORE UPDATE ON custom_metrics
    FOR EACH ROW
    EXECUTE FUNCTION update_offers_updated_at();

-- Comments
COMMENT ON TABLE customer_analytics IS 'Daily customer behavior and purchase analytics';
COMMENT ON TABLE product_performance IS 'Daily product performance metrics';
COMMENT ON TABLE sales_analytics IS 'Daily aggregated sales metrics';
COMMENT ON TABLE category_analytics IS 'Category-level performance analytics';
COMMENT ON TABLE customer_cohorts IS 'Cohort analysis for customer retention';
COMMENT ON TABLE customer_segments IS 'Customer segmentation definitions';
COMMENT ON TABLE customer_segment_members IS 'Customer assignments to segments';
COMMENT ON TABLE business_reports IS 'Scheduled business reports configuration';
COMMENT ON TABLE report_executions IS 'Report generation execution log';
COMMENT ON TABLE custom_metrics IS 'Custom business metrics definitions';
COMMENT ON TABLE metric_values IS 'Time series data for custom metrics';
