-- =====================================================
-- PAYMENT AGENT DATABASE MIGRATION
-- =====================================================
-- This migration creates comprehensive payment management tables
-- for payment methods, transactions, gateways, refunds, and audit trails.

-- =====================================================
-- 1. PAYMENT GATEWAYS
-- =====================================================

CREATE TABLE IF NOT EXISTS payment_gateways (
    gateway_id SERIAL PRIMARY KEY,
    gateway_name VARCHAR(100) UNIQUE NOT NULL,
    gateway_type VARCHAR(50) NOT NULL, -- 'credit_card', 'paypal', 'stripe', 'bank_transfer', 'crypto', 'wallet'
    is_active BOOLEAN DEFAULT true,
    is_test_mode BOOLEAN DEFAULT false,
    configuration JSONB DEFAULT '{}',
    supported_currencies TEXT[] DEFAULT ARRAY['USD'],
    supported_countries TEXT[] DEFAULT ARRAY['US'],
    transaction_fee_percent DECIMAL(5, 2) DEFAULT 0.00,
    transaction_fee_fixed DECIMAL(10, 2) DEFAULT 0.00,
    min_transaction_amount DECIMAL(10, 2) DEFAULT 0.01,
    max_transaction_amount DECIMAL(10, 2),
    settlement_period_days INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_gateways_active ON payment_gateways(is_active);
CREATE INDEX IF NOT EXISTS idx_payment_gateways_type ON payment_gateways(gateway_type);

COMMENT ON TABLE payment_gateways IS 'Payment gateway configurations';

-- =====================================================
-- 2. PAYMENT METHODS
-- =====================================================

CREATE TABLE IF NOT EXISTS payment_methods (
    method_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(100) NOT NULL,
    gateway_id INTEGER NOT NULL REFERENCES payment_gateways(gateway_id),
    method_type VARCHAR(50) NOT NULL, -- 'credit_card', 'debit_card', 'paypal', 'bank_account', 'crypto_wallet'
    is_default BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,
    
    -- Card details (tokenized)
    card_last_four VARCHAR(4),
    card_brand VARCHAR(50), -- 'visa', 'mastercard', 'amex', 'discover'
    card_expiry_month INTEGER,
    card_expiry_year INTEGER,
    card_holder_name VARCHAR(200),
    
    -- Bank account details (tokenized)
    bank_name VARCHAR(200),
    account_last_four VARCHAR(4),
    account_type VARCHAR(50), -- 'checking', 'savings'
    
    -- PayPal/Wallet details
    email VARCHAR(255),
    wallet_address VARCHAR(500),
    
    -- Gateway-specific token
    gateway_token VARCHAR(500),
    gateway_customer_id VARCHAR(200),
    
    -- Billing address
    billing_address_id UUID,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_methods_customer ON payment_methods(customer_id);
CREATE INDEX IF NOT EXISTS idx_payment_methods_gateway ON payment_methods(gateway_id);
CREATE INDEX IF NOT EXISTS idx_payment_methods_default ON payment_methods(customer_id, is_default);
CREATE INDEX IF NOT EXISTS idx_payment_methods_type ON payment_methods(method_type);

COMMENT ON TABLE payment_methods IS 'Customer payment methods (tokenized)';

-- =====================================================
-- 3. PAYMENT TRANSACTIONS
-- =====================================================

CREATE TABLE IF NOT EXISTS payment_transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id VARCHAR(100),
    customer_id VARCHAR(100) NOT NULL,
    payment_method_id UUID REFERENCES payment_methods(method_id),
    gateway_id INTEGER NOT NULL REFERENCES payment_gateways(gateway_id),
    
    -- Transaction details
    transaction_type VARCHAR(50) NOT NULL, -- 'authorize', 'capture', 'sale', 'refund', 'void'
    transaction_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed', 'cancelled', 'refunded'
    
    -- Amounts
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    fee_amount DECIMAL(10, 2) DEFAULT 0.00,
    net_amount DECIMAL(10, 2),
    
    -- Gateway response
    gateway_transaction_id VARCHAR(200),
    gateway_response JSONB DEFAULT '{}',
    gateway_status VARCHAR(100),
    
    -- Authorization
    authorization_code VARCHAR(100),
    authorization_expires_at TIMESTAMP,
    
    -- Error handling
    error_code VARCHAR(100),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Fraud detection
    risk_score DECIMAL(5, 2),
    risk_level VARCHAR(20), -- 'low', 'medium', 'high', 'blocked'
    fraud_check_result JSONB DEFAULT '{}',
    
    -- Timestamps
    initiated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    failed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_transactions_order ON payment_transactions(order_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_customer ON payment_transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_method ON payment_transactions(payment_method_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_gateway ON payment_transactions(gateway_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_status ON payment_transactions(transaction_status);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_type ON payment_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_created ON payment_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_gateway_id ON payment_transactions(gateway_transaction_id);

COMMENT ON TABLE payment_transactions IS 'Payment transaction records';

-- =====================================================
-- 4. PAYMENT REFUNDS
-- =====================================================

CREATE TABLE IF NOT EXISTS payment_refunds (
    refund_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL REFERENCES payment_transactions(transaction_id),
    order_id VARCHAR(100),
    customer_id VARCHAR(100) NOT NULL,
    
    -- Refund details
    refund_type VARCHAR(50) NOT NULL, -- 'full', 'partial', 'chargeback'
    refund_reason VARCHAR(100), -- 'customer_request', 'order_cancelled', 'item_returned', 'damaged', 'fraud'
    refund_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed', 'cancelled'
    
    -- Amounts
    refund_amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    fee_refunded DECIMAL(10, 2) DEFAULT 0.00,
    
    -- Gateway response
    gateway_refund_id VARCHAR(200),
    gateway_response JSONB DEFAULT '{}',
    
    -- Error handling
    error_code VARCHAR(100),
    error_message TEXT,
    
    -- Metadata
    notes TEXT,
    requested_by VARCHAR(100),
    approved_by VARCHAR(100),
    
    -- Timestamps
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    completed_at TIMESTAMP,
    failed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_refunds_transaction ON payment_refunds(transaction_id);
CREATE INDEX IF NOT EXISTS idx_payment_refunds_order ON payment_refunds(order_id);
CREATE INDEX IF NOT EXISTS idx_payment_refunds_customer ON payment_refunds(customer_id);
CREATE INDEX IF NOT EXISTS idx_payment_refunds_status ON payment_refunds(refund_status);
CREATE INDEX IF NOT EXISTS idx_payment_refunds_created ON payment_refunds(created_at DESC);

COMMENT ON TABLE payment_refunds IS 'Payment refund records';

-- =====================================================
-- 5. PAYMENT AUTHORIZATIONS
-- =====================================================

CREATE TABLE IF NOT EXISTS payment_authorizations (
    authorization_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id VARCHAR(100) NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    payment_method_id UUID REFERENCES payment_methods(method_id),
    gateway_id INTEGER NOT NULL REFERENCES payment_gateways(gateway_id),
    
    -- Authorization details
    authorization_amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    authorization_code VARCHAR(100),
    authorization_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'authorized', 'captured', 'expired', 'cancelled'
    
    -- Capture details
    captured_amount DECIMAL(10, 2) DEFAULT 0.00,
    remaining_amount DECIMAL(10, 2),
    
    -- Gateway response
    gateway_authorization_id VARCHAR(200),
    gateway_response JSONB DEFAULT '{}',
    
    -- Expiry
    expires_at TIMESTAMP,
    
    -- Timestamps
    authorized_at TIMESTAMP,
    captured_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_authorizations_order ON payment_authorizations(order_id);
CREATE INDEX IF NOT EXISTS idx_payment_authorizations_customer ON payment_authorizations(customer_id);
CREATE INDEX IF NOT EXISTS idx_payment_authorizations_status ON payment_authorizations(authorization_status);
CREATE INDEX IF NOT EXISTS idx_payment_authorizations_expires ON payment_authorizations(expires_at);

COMMENT ON TABLE payment_authorizations IS 'Payment authorization holds';

-- =====================================================
-- 6. PAYMENT DISPUTES
-- =====================================================

CREATE TABLE IF NOT EXISTS payment_disputes (
    dispute_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL REFERENCES payment_transactions(transaction_id),
    order_id VARCHAR(100),
    customer_id VARCHAR(100) NOT NULL,
    
    -- Dispute details
    dispute_type VARCHAR(50) NOT NULL, -- 'chargeback', 'inquiry', 'retrieval_request'
    dispute_reason VARCHAR(100), -- 'fraud', 'unrecognized', 'duplicate', 'product_not_received', 'not_as_described'
    dispute_status VARCHAR(50) DEFAULT 'open', -- 'open', 'under_review', 'won', 'lost', 'accepted'
    
    -- Amounts
    disputed_amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Gateway details
    gateway_dispute_id VARCHAR(200),
    gateway_response JSONB DEFAULT '{}',
    
    -- Evidence
    evidence_submitted BOOLEAN DEFAULT false,
    evidence_due_date DATE,
    evidence_details JSONB DEFAULT '{}',
    
    -- Resolution
    resolution_notes TEXT,
    resolved_by VARCHAR(100),
    
    -- Timestamps
    disputed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    evidence_submitted_at TIMESTAMP,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_disputes_transaction ON payment_disputes(transaction_id);
CREATE INDEX IF NOT EXISTS idx_payment_disputes_order ON payment_disputes(order_id);
CREATE INDEX IF NOT EXISTS idx_payment_disputes_customer ON payment_disputes(customer_id);
CREATE INDEX IF NOT EXISTS idx_payment_disputes_status ON payment_disputes(dispute_status);
CREATE INDEX IF NOT EXISTS idx_payment_disputes_created ON payment_disputes(created_at DESC);

COMMENT ON TABLE payment_disputes IS 'Payment disputes and chargebacks';

-- =====================================================
-- 7. PAYMENT WEBHOOKS
-- =====================================================

CREATE TABLE IF NOT EXISTS payment_webhooks (
    webhook_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gateway_id INTEGER NOT NULL REFERENCES payment_gateways(gateway_id),
    
    -- Webhook details
    event_type VARCHAR(100) NOT NULL,
    event_id VARCHAR(200),
    payload JSONB NOT NULL,
    
    -- Processing
    processed BOOLEAN DEFAULT false,
    processed_at TIMESTAMP,
    processing_error TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Verification
    signature VARCHAR(500),
    signature_verified BOOLEAN DEFAULT false,
    
    -- Timestamps
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_webhooks_gateway ON payment_webhooks(gateway_id);
CREATE INDEX IF NOT EXISTS idx_payment_webhooks_processed ON payment_webhooks(processed);
CREATE INDEX IF NOT EXISTS idx_payment_webhooks_event ON payment_webhooks(event_type);
CREATE INDEX IF NOT EXISTS idx_payment_webhooks_received ON payment_webhooks(received_at DESC);

COMMENT ON TABLE payment_webhooks IS 'Payment gateway webhook events';

-- =====================================================
-- 8. PAYMENT AUDIT LOG
-- =====================================================

CREATE TABLE IF NOT EXISTS payment_audit_log (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID REFERENCES payment_transactions(transaction_id),
    refund_id UUID REFERENCES payment_refunds(refund_id),
    
    -- Audit details
    action VARCHAR(100) NOT NULL, -- 'created', 'updated', 'authorized', 'captured', 'refunded', 'cancelled'
    actor VARCHAR(100), -- 'system', 'customer', 'admin', 'gateway'
    actor_id VARCHAR(100),
    
    -- Changes
    old_values JSONB DEFAULT '{}',
    new_values JSONB DEFAULT '{}',
    
    -- Context
    ip_address VARCHAR(45),
    user_agent TEXT,
    metadata JSONB DEFAULT '{}',
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_audit_transaction ON payment_audit_log(transaction_id);
CREATE INDEX IF NOT EXISTS idx_payment_audit_refund ON payment_audit_log(refund_id);
CREATE INDEX IF NOT EXISTS idx_payment_audit_action ON payment_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_payment_audit_actor ON payment_audit_log(actor);
CREATE INDEX IF NOT EXISTS idx_payment_audit_created ON payment_audit_log(created_at DESC);

COMMENT ON TABLE payment_audit_log IS 'Complete audit trail for payment operations';

-- =====================================================
-- MATERIALIZED VIEWS
-- =====================================================

-- Payment Summary View
CREATE MATERIALIZED VIEW IF NOT EXISTS payment_summary AS
SELECT 
    pt.customer_id,
    COUNT(DISTINCT pt.transaction_id) as total_transactions,
    COUNT(DISTINCT CASE WHEN pt.transaction_status = 'completed' THEN pt.transaction_id END) as successful_transactions,
    COUNT(DISTINCT CASE WHEN pt.transaction_status = 'failed' THEN pt.transaction_id END) as failed_transactions,
    COALESCE(SUM(CASE WHEN pt.transaction_status = 'completed' THEN pt.amount ELSE 0 END), 0) as total_amount_paid,
    COALESCE(SUM(CASE WHEN pt.transaction_status = 'completed' THEN pt.fee_amount ELSE 0 END), 0) as total_fees,
    COALESCE(SUM(pr.refund_amount), 0) as total_refunded,
    COUNT(DISTINCT pr.refund_id) as total_refunds,
    MAX(pt.created_at) as last_payment_date,
    AVG(pt.risk_score) as average_risk_score
FROM payment_transactions pt
LEFT JOIN payment_refunds pr ON pt.transaction_id = pr.transaction_id AND pr.refund_status = 'completed'
GROUP BY pt.customer_id;

CREATE UNIQUE INDEX idx_payment_summary_customer ON payment_summary(customer_id);

COMMENT ON MATERIALIZED VIEW payment_summary IS 'Customer payment summary with transaction statistics';

-- Gateway Performance View
CREATE MATERIALIZED VIEW IF NOT EXISTS gateway_performance AS
SELECT 
    pg.gateway_id,
    pg.gateway_name,
    pg.gateway_type,
    COUNT(DISTINCT pt.transaction_id) as total_transactions,
    COUNT(DISTINCT CASE WHEN pt.transaction_status = 'completed' THEN pt.transaction_id END) as successful_transactions,
    COUNT(DISTINCT CASE WHEN pt.transaction_status = 'failed' THEN pt.transaction_id END) as failed_transactions,
    ROUND(COUNT(DISTINCT CASE WHEN pt.transaction_status = 'completed' THEN pt.transaction_id END)::numeric / 
          NULLIF(COUNT(DISTINCT pt.transaction_id), 0) * 100, 2) as success_rate,
    COALESCE(SUM(CASE WHEN pt.transaction_status = 'completed' THEN pt.amount ELSE 0 END), 0) as total_volume,
    COALESCE(SUM(CASE WHEN pt.transaction_status = 'completed' THEN pt.fee_amount ELSE 0 END), 0) as total_fees,
    AVG(CASE WHEN pt.transaction_status = 'completed' THEN pt.amount END) as average_transaction_amount,
    AVG(pt.risk_score) as average_risk_score
FROM payment_gateways pg
LEFT JOIN payment_transactions pt ON pg.gateway_id = pt.gateway_id
GROUP BY pg.gateway_id, pg.gateway_name, pg.gateway_type;

CREATE UNIQUE INDEX idx_gateway_performance_gateway ON gateway_performance(gateway_id);

COMMENT ON MATERIALIZED VIEW gateway_performance IS 'Payment gateway performance metrics';

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_payment_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
CREATE TRIGGER trigger_update_payment_gateways_timestamp
    BEFORE UPDATE ON payment_gateways
    FOR EACH ROW
    EXECUTE FUNCTION update_payment_timestamp();

CREATE TRIGGER trigger_update_payment_methods_timestamp
    BEFORE UPDATE ON payment_methods
    FOR EACH ROW
    EXECUTE FUNCTION update_payment_timestamp();

CREATE TRIGGER trigger_update_payment_transactions_timestamp
    BEFORE UPDATE ON payment_transactions
    FOR EACH ROW
    EXECUTE FUNCTION update_payment_timestamp();

CREATE TRIGGER trigger_update_payment_refunds_timestamp
    BEFORE UPDATE ON payment_refunds
    FOR EACH ROW
    EXECUTE FUNCTION update_payment_timestamp();

CREATE TRIGGER trigger_update_payment_authorizations_timestamp
    BEFORE UPDATE ON payment_authorizations
    FOR EACH ROW
    EXECUTE FUNCTION update_payment_timestamp();

CREATE TRIGGER trigger_update_payment_disputes_timestamp
    BEFORE UPDATE ON payment_disputes
    FOR EACH ROW
    EXECUTE FUNCTION update_payment_timestamp();

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to refresh payment summary
CREATE OR REPLACE FUNCTION refresh_payment_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY payment_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY gateway_performance;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_payment_summary() IS 'Refresh payment summary materialized views';

-- =====================================================
-- INITIAL DATA
-- =====================================================

-- Insert default payment gateways
INSERT INTO payment_gateways (gateway_name, gateway_type, is_active, is_test_mode, supported_currencies, transaction_fee_percent, transaction_fee_fixed)
VALUES 
    ('Stripe', 'credit_card', true, true, ARRAY['USD', 'EUR', 'GBP'], 2.9, 0.30),
    ('PayPal', 'paypal', true, true, ARRAY['USD', 'EUR', 'GBP'], 2.9, 0.30),
    ('Square', 'credit_card', true, true, ARRAY['USD'], 2.6, 0.10),
    ('Authorize.Net', 'credit_card', false, true, ARRAY['USD'], 2.9, 0.30),
    ('Bank Transfer', 'bank_transfer', true, false, ARRAY['USD'], 0.0, 0.00)
ON CONFLICT (gateway_name) DO NOTHING;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

COMMENT ON SCHEMA public IS 'Payment Agent migration 006 completed successfully';

