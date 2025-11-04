-- Multi-Agent E-commerce Platform - Comprehensive Database Schema
-- Created: November 4, 2025
-- Purpose: Production-ready schema for all agents and personas

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Users table (for all personas: admin, merchant, customer)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'merchant', 'customer')),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Create indexes for users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ============================================================================
-- MERCHANT TABLES
-- ============================================================================

-- Merchants (extended profile for merchant users)
CREATE TABLE IF NOT EXISTS merchants (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    business_name VARCHAR(255) NOT NULL,
    business_type VARCHAR(100),
    tax_id VARCHAR(100),
    website VARCHAR(255),
    description TEXT,
    logo_url VARCHAR(500),
    rating DECIMAL(3,2) DEFAULT 0.00,
    total_sales DECIMAL(15,2) DEFAULT 0.00,
    total_orders INTEGER DEFAULT 0,
    commission_rate DECIMAL(5,2) DEFAULT 10.00,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'pending')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_merchants_user_id ON merchants(user_id);
CREATE INDEX IF NOT EXISTS idx_merchants_status ON merchants(status);

-- ============================================================================
-- PRODUCT TABLES
-- ============================================================================

-- Categories
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    parent_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    image_url VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_categories_parent_id ON categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_categories_slug ON categories(slug);

-- Products
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    merchant_id INTEGER REFERENCES merchants(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    sku VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    short_description TEXT,
    price DECIMAL(10,2) NOT NULL,
    cost DECIMAL(10,2),
    compare_at_price DECIMAL(10,2),
    weight DECIMAL(10,2),
    dimensions JSONB,
    images JSONB,
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'inactive', 'out_of_stock')),
    is_featured BOOLEAN DEFAULT false,
    rating DECIMAL(3,2) DEFAULT 0.00,
    review_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    sales_count INTEGER DEFAULT 0,
    tags JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_merchant_id ON products(merchant_id);
CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);
CREATE INDEX IF NOT EXISTS idx_products_slug ON products(slug);

-- Product Variants
CREATE TABLE IF NOT EXISTS product_variants (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    sku VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10,2),
    cost DECIMAL(10,2),
    compare_at_price DECIMAL(10,2),
    weight DECIMAL(10,2),
    image_url VARCHAR(500),
    attributes JSONB,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_product_variants_product_id ON product_variants(product_id);
CREATE INDEX IF NOT EXISTS idx_product_variants_sku ON product_variants(sku);

-- ============================================================================
-- INVENTORY TABLES
-- ============================================================================

-- Warehouses
CREATE TABLE IF NOT EXISTS warehouses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    phone VARCHAR(50),
    email VARCHAR(255),
    manager_name VARCHAR(255),
    capacity INTEGER,
    current_utilization INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_warehouses_code ON warehouses(code);
CREATE INDEX IF NOT EXISTS idx_warehouses_is_active ON warehouses(is_active);

-- Inventory
CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    variant_id INTEGER REFERENCES product_variants(id) ON DELETE CASCADE,
    warehouse_id INTEGER REFERENCES warehouses(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0,
    available_quantity INTEGER GENERATED ALWAYS AS (quantity - reserved_quantity) STORED,
    reorder_point INTEGER DEFAULT 10,
    reorder_quantity INTEGER DEFAULT 50,
    last_restock_date TIMESTAMP,
    last_count_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, variant_id, warehouse_id)
);

CREATE INDEX IF NOT EXISTS idx_inventory_product_id ON inventory(product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_warehouse_id ON inventory(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_inventory_available_quantity ON inventory(available_quantity);

-- Inventory Adjustments
CREATE TABLE IF NOT EXISTS inventory_adjustments (
    id SERIAL PRIMARY KEY,
    inventory_id INTEGER REFERENCES inventory(id) ON DELETE CASCADE,
    adjustment_type VARCHAR(50) NOT NULL CHECK (adjustment_type IN ('restock', 'sale', 'damage', 'return', 'correction')),
    quantity_change INTEGER NOT NULL,
    reason TEXT,
    reference_id VARCHAR(100),
    performed_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inventory_adjustments_inventory_id ON inventory_adjustments(inventory_id);
CREATE INDEX IF NOT EXISTS idx_inventory_adjustments_created_at ON inventory_adjustments(created_at);

-- ============================================================================
-- ORDER TABLES
-- ============================================================================

-- Customers (extended profile for customer users)
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    customer_group VARCHAR(100),
    total_orders INTEGER DEFAULT 0,
    total_spent DECIMAL(15,2) DEFAULT 0.00,
    average_order_value DECIMAL(10,2) DEFAULT 0.00,
    lifetime_value DECIMAL(15,2) DEFAULT 0.00,
    last_order_date TIMESTAMP,
    notes TEXT,
    tags JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_customers_user_id ON customers(user_id);

-- Addresses
CREATE TABLE IF NOT EXISTS addresses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    address_type VARCHAR(50) CHECK (address_type IN ('shipping', 'billing', 'both')),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company VARCHAR(255),
    address_line1 TEXT NOT NULL,
    address_line2 TEXT,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100),
    country VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    phone VARCHAR(50),
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_addresses_user_id ON addresses(user_id);

-- Orders
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(100) UNIQUE NOT NULL,
    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    merchant_id INTEGER REFERENCES merchants(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded')),
    payment_status VARCHAR(50) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'failed', 'refunded', 'partially_refunded')),
    fulfillment_status VARCHAR(50) DEFAULT 'unfulfilled' CHECK (fulfillment_status IN ('unfulfilled', 'partially_fulfilled', 'fulfilled', 'returned')),
    subtotal DECIMAL(10,2) NOT NULL,
    tax DECIMAL(10,2) DEFAULT 0.00,
    shipping_cost DECIMAL(10,2) DEFAULT 0.00,
    discount DECIMAL(10,2) DEFAULT 0.00,
    total DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    shipping_address_id INTEGER REFERENCES addresses(id),
    billing_address_id INTEGER REFERENCES addresses(id),
    notes TEXT,
    customer_notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP,
    shipped_at TIMESTAMP,
    delivered_at TIMESTAMP,
    cancelled_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_merchant_id ON orders(merchant_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);

-- Order Items
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    variant_id INTEGER REFERENCES product_variants(id) ON DELETE SET NULL,
    sku VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    tax DECIMAL(10,2) DEFAULT 0.00,
    discount DECIMAL(10,2) DEFAULT 0.00,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);

-- ============================================================================
-- SHIPPING & LOGISTICS TABLES
-- ============================================================================

-- Carriers
CREATE TABLE IF NOT EXISTS carriers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    tracking_url_template VARCHAR(500),
    api_endpoint VARCHAR(500),
    api_key_encrypted TEXT,
    is_active BOOLEAN DEFAULT true,
    supported_services JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_carriers_code ON carriers(code);
CREATE INDEX IF NOT EXISTS idx_carriers_is_active ON carriers(is_active);

-- Shipments
CREATE TABLE IF NOT EXISTS shipments (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    carrier_id INTEGER REFERENCES carriers(id) ON DELETE SET NULL,
    tracking_number VARCHAR(255),
    service_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'in_transit', 'delivered', 'failed', 'returned')),
    estimated_delivery_date DATE,
    actual_delivery_date TIMESTAMP,
    shipping_cost DECIMAL(10,2),
    weight DECIMAL(10,2),
    dimensions JSONB,
    from_address JSONB,
    to_address JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_shipments_order_id ON shipments(order_id);
CREATE INDEX IF NOT EXISTS idx_shipments_tracking_number ON shipments(tracking_number);
CREATE INDEX IF NOT EXISTS idx_shipments_status ON shipments(status);

-- ============================================================================
-- PAYMENT TABLES
-- ============================================================================

-- Payment Methods
CREATE TABLE IF NOT EXISTS payment_methods (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) CHECK (type IN ('credit_card', 'debit_card', 'paypal', 'bank_transfer', 'wallet')),
    provider VARCHAR(100),
    last_four VARCHAR(4),
    expiry_month INTEGER,
    expiry_year INTEGER,
    is_default BOOLEAN DEFAULT false,
    token_encrypted TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_methods_user_id ON payment_methods(user_id);

-- Transactions
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    payment_method_id INTEGER REFERENCES payment_methods(id) ON DELETE SET NULL,
    transaction_type VARCHAR(50) CHECK (transaction_type IN ('charge', 'refund', 'authorization', 'capture')),
    status VARCHAR(50) CHECK (status IN ('pending', 'success', 'failed', 'cancelled')),
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    gateway VARCHAR(100),
    gateway_transaction_id VARCHAR(255),
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transactions_order_id ON transactions(order_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);

-- ============================================================================
-- MARKETPLACE TABLES
-- ============================================================================

-- Marketplace Channels
CREATE TABLE IF NOT EXISTS marketplace_channels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    type VARCHAR(50) CHECK (type IN ('marketplace', 'social', 'website', 'pos')),
    api_endpoint VARCHAR(500),
    api_key_encrypted TEXT,
    is_active BOOLEAN DEFAULT true,
    sync_enabled BOOLEAN DEFAULT true,
    last_sync_at TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_marketplace_channels_code ON marketplace_channels(code);

-- Product Channel Listings
CREATE TABLE IF NOT EXISTS product_channel_listings (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    channel_id INTEGER REFERENCES marketplace_channels(id) ON DELETE CASCADE,
    external_id VARCHAR(255),
    price DECIMAL(10,2),
    quantity INTEGER,
    status VARCHAR(50),
    last_synced_at TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, channel_id)
);

CREATE INDEX IF NOT EXISTS idx_product_channel_listings_product_id ON product_channel_listings(product_id);
CREATE INDEX IF NOT EXISTS idx_product_channel_listings_channel_id ON product_channel_listings(channel_id);

-- ============================================================================
-- ANALYTICS & REPORTING TABLES
-- ============================================================================

-- Agent Metrics
CREATE TABLE IF NOT EXISTS agent_metrics (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    metric_type VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,2),
    metadata JSONB,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_metrics_agent_id ON agent_metrics(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_metrics_recorded_at ON agent_metrics(recorded_at);

-- System Alerts
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    title VARCHAR(255) NOT NULL,
    message TEXT,
    source VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'acknowledged', 'resolved')),
    acknowledged_by INTEGER REFERENCES users(id),
    acknowledged_at TIMESTAMP,
    resolved_by INTEGER REFERENCES users(id),
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);

-- ============================================================================
-- CONFIGURATION TABLES
-- ============================================================================

-- System Configuration
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value JSONB,
    description TEXT,
    is_encrypted BOOLEAN DEFAULT false,
    updated_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key);

-- Workflows
CREATE TABLE IF NOT EXISTS workflows (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    trigger_type VARCHAR(100),
    trigger_config JSONB,
    actions JSONB,
    is_active BOOLEAN DEFAULT true,
    execution_count INTEGER DEFAULT 0,
    last_executed_at TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_workflows_is_active ON workflows(is_active);

-- ============================================================================
-- AUDIT & LOGGING TABLES
-- ============================================================================

-- Audit Log
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity_type ON audit_log(entity_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all tables with updated_at column
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN
        SELECT table_name 
        FROM information_schema.columns 
        WHERE column_name = 'updated_at' 
        AND table_schema = 'public'
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS update_%I_updated_at ON %I', t, t);
        EXECUTE format('CREATE TRIGGER update_%I_updated_at 
                       BEFORE UPDATE ON %I 
                       FOR EACH ROW 
                       EXECUTE FUNCTION update_updated_at_column()', t, t);
    END LOOP;
END;
$$ language 'plpgsql';

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Product inventory view
CREATE OR REPLACE VIEW product_inventory_view AS
SELECT 
    p.id as product_id,
    p.name as product_name,
    p.sku,
    p.price,
    p.status,
    w.id as warehouse_id,
    w.name as warehouse_name,
    i.quantity,
    i.reserved_quantity,
    i.available_quantity,
    i.reorder_point
FROM products p
LEFT JOIN inventory i ON p.id = i.product_id
LEFT JOIN warehouses w ON i.warehouse_id = w.id;

-- Order summary view
CREATE OR REPLACE VIEW order_summary_view AS
SELECT 
    o.id,
    o.order_number,
    o.status,
    o.total,
    o.created_at,
    u.email as customer_email,
    u.first_name || ' ' || u.last_name as customer_name,
    COUNT(oi.id) as item_count
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN users u ON c.user_id = u.id
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id, o.order_number, o.status, o.total, o.created_at, u.email, u.first_name, u.last_name;

-- Merchant performance view
CREATE OR REPLACE VIEW merchant_performance_view AS
SELECT 
    m.id as merchant_id,
    m.business_name,
    m.status,
    m.total_orders,
    m.total_sales,
    COUNT(DISTINCT p.id) as product_count,
    COUNT(DISTINCT o.id) as order_count_current,
    COALESCE(SUM(o.total), 0) as revenue
FROM merchants m
LEFT JOIN products p ON m.id = p.merchant_id
LEFT JOIN orders o ON m.id = o.merchant_id AND o.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY m.id, m.business_name, m.status, m.total_orders, m.total_sales;

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

-- Grant all permissions to postgres user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO postgres;

-- ============================================================================
-- SCHEMA COMPLETE
-- ============================================================================
