-- ============================================================================
-- SUPPLIER MANAGEMENT SCHEMA
-- ============================================================================
-- This migration adds tables for managing suppliers and their products
-- Based on Market Master Tool competitive analysis
-- ============================================================================

-- Suppliers table
CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    
    -- Basic Information
    name VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),
    supplier_code VARCHAR(100) UNIQUE,
    status VARCHAR(50) DEFAULT 'active', -- active, inactive, suspended
    
    -- Contact Information
    contact_person VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    website VARCHAR(255),
    
    -- Address
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    
    -- Business Details
    tax_id VARCHAR(100),
    payment_terms VARCHAR(100), -- Net 30, Net 60, etc.
    currency VARCHAR(10) DEFAULT 'USD',
    minimum_order_value NUMERIC(15, 2),
    
    -- Performance Metrics
    rating NUMERIC(3, 2), -- 0.00 to 5.00
    total_orders INTEGER DEFAULT 0,
    total_spend NUMERIC(15, 2) DEFAULT 0.00,
    on_time_delivery_rate NUMERIC(5, 2), -- Percentage
    quality_score NUMERIC(5, 2), -- Percentage
    
    -- Metadata
    notes TEXT,
    tags JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    metadata JSONB
);

-- Supplier Products (Products sourced from suppliers)
CREATE TABLE IF NOT EXISTS supplier_products (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER REFERENCES suppliers(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    
    -- Supplier-specific product info
    supplier_sku VARCHAR(255),
    supplier_product_name VARCHAR(255),
    cost_price NUMERIC(15, 2),
    minimum_order_quantity INTEGER DEFAULT 1,
    lead_time_days INTEGER, -- Days to deliver
    
    -- Status
    is_primary_supplier BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(supplier_id, product_id)
);

-- Purchase Orders
CREATE TABLE IF NOT EXISTS purchase_orders (
    id SERIAL PRIMARY KEY,
    
    -- Order Information
    po_number VARCHAR(100) UNIQUE NOT NULL,
    supplier_id INTEGER REFERENCES suppliers(id),
    status VARCHAR(50) DEFAULT 'draft', -- draft, sent, confirmed, shipped, received, cancelled
    
    -- Dates
    order_date DATE,
    expected_delivery_date DATE,
    actual_delivery_date DATE,
    
    -- Financial
    subtotal NUMERIC(15, 2) DEFAULT 0.00,
    tax_amount NUMERIC(15, 2) DEFAULT 0.00,
    shipping_cost NUMERIC(15, 2) DEFAULT 0.00,
    total_amount NUMERIC(15, 2) DEFAULT 0.00,
    currency VARCHAR(10) DEFAULT 'USD',
    
    -- Delivery
    shipping_address JSONB,
    tracking_number VARCHAR(255),
    
    -- Metadata
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Purchase Order Items
CREATE TABLE IF NOT EXISTS purchase_order_items (
    id SERIAL PRIMARY KEY,
    purchase_order_id INTEGER REFERENCES purchase_orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    supplier_product_id INTEGER REFERENCES supplier_products(id),
    
    -- Item Details
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(15, 2) NOT NULL,
    tax_rate NUMERIC(5, 2) DEFAULT 0.00,
    line_total NUMERIC(15, 2) NOT NULL,
    
    -- Receiving
    quantity_received INTEGER DEFAULT 0,
    quantity_pending INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Supplier Payments
CREATE TABLE IF NOT EXISTS supplier_payments (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER REFERENCES suppliers(id),
    purchase_order_id INTEGER REFERENCES purchase_orders(id),
    
    -- Payment Details
    payment_date DATE NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    payment_method VARCHAR(50), -- bank_transfer, check, credit_card, etc.
    reference_number VARCHAR(255),
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- pending, completed, failed
    
    -- Metadata
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Indexes for performance
CREATE INDEX idx_suppliers_status ON suppliers(status);
CREATE INDEX idx_suppliers_name ON suppliers(name);
CREATE INDEX idx_supplier_products_supplier ON supplier_products(supplier_id);
CREATE INDEX idx_supplier_products_product ON supplier_products(product_id);
CREATE INDEX idx_purchase_orders_supplier ON purchase_orders(supplier_id);
CREATE INDEX idx_purchase_orders_status ON purchase_orders(status);
CREATE INDEX idx_purchase_orders_dates ON purchase_orders(order_date, expected_delivery_date);
CREATE INDEX idx_purchase_order_items_po ON purchase_order_items(purchase_order_id);
CREATE INDEX idx_supplier_payments_supplier ON supplier_payments(supplier_id);

-- Update timestamp triggers
CREATE TRIGGER suppliers_updated_at_trigger
    BEFORE UPDATE ON suppliers
    FOR EACH ROW
    EXECUTE FUNCTION update_offers_updated_at();

CREATE TRIGGER supplier_products_updated_at_trigger
    BEFORE UPDATE ON supplier_products
    FOR EACH ROW
    EXECUTE FUNCTION update_offers_updated_at();

CREATE TRIGGER purchase_orders_updated_at_trigger
    BEFORE UPDATE ON purchase_orders
    FOR EACH ROW
    EXECUTE FUNCTION update_offers_updated_at();

-- Comments
COMMENT ON TABLE suppliers IS 'Supplier and vendor management';
COMMENT ON TABLE supplier_products IS 'Products sourced from suppliers';
COMMENT ON TABLE purchase_orders IS 'Purchase orders to suppliers';
COMMENT ON TABLE purchase_order_items IS 'Line items in purchase orders';
COMMENT ON TABLE supplier_payments IS 'Payments made to suppliers';
