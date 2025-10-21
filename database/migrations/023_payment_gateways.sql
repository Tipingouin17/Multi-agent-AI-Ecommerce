-- Payment Gateway Configuration Migration
-- Supports multiple payment providers with secure credential storage

-- Payment Gateways Table
CREATE TABLE IF NOT EXISTS payment_gateways (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(50) NOT NULL, -- stripe, paypal, square, authorize_net, custom
    name VARCHAR(255) NOT NULL,
    enabled BOOLEAN DEFAULT true,
    test_mode BOOLEAN DEFAULT true,
    credentials JSONB NOT NULL, -- Encrypted credentials storage
    webhook_url TEXT,
    webhook_secret VARCHAR(255),
    supported_currencies TEXT[] DEFAULT ARRAY['USD'],
    supported_payment_methods TEXT[] DEFAULT ARRAY['card'],
    transaction_fee_fixed DECIMAL(10, 2) DEFAULT 0.30,
    transaction_fee_percentage DECIMAL(5, 2) DEFAULT 2.9,
    priority INTEGER DEFAULT 1, -- Lower number = higher priority
    regions TEXT[] DEFAULT ARRAY['US'],
    min_amount DECIMAL(10, 2) DEFAULT 0.50,
    max_amount DECIMAL(12, 2) DEFAULT 999999.99,
    auto_capture BOOLEAN DEFAULT true,
    three_d_secure BOOLEAN DEFAULT false,
    status VARCHAR(50) DEFAULT 'active', -- active, error, disabled
    last_health_check TIMESTAMP,
    health_check_status VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- Payment Transactions Table
CREATE TABLE IF NOT EXISTS payment_transactions (
    id SERIAL PRIMARY KEY,
    gateway_id INTEGER REFERENCES payment_gateways(id),
    order_id INTEGER REFERENCES orders(id),
    external_transaction_id VARCHAR(255), -- Provider's transaction ID
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    payment_method VARCHAR(50), -- card, paypal, apple_pay, etc.
    status VARCHAR(50) NOT NULL, -- pending, authorized, captured, failed, refunded, cancelled
    payment_intent_id VARCHAR(255),
    customer_id VARCHAR(255),
    card_last4 VARCHAR(4),
    card_brand VARCHAR(50),
    card_exp_month INTEGER,
    card_exp_year INTEGER,
    billing_address JSONB,
    shipping_address JSONB,
    metadata JSONB,
    error_code VARCHAR(50),
    error_message TEXT,
    authorized_at TIMESTAMP,
    captured_at TIMESTAMP,
    refunded_at TIMESTAMP,
    refund_amount DECIMAL(10, 2),
    refund_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payment Webhooks Log Table
CREATE TABLE IF NOT EXISTS payment_webhook_logs (
    id SERIAL PRIMARY KEY,
    gateway_id INTEGER REFERENCES payment_gateways(id),
    event_type VARCHAR(100) NOT NULL,
    event_id VARCHAR(255),
    payload JSONB NOT NULL,
    signature VARCHAR(500),
    signature_verified BOOLEAN DEFAULT false,
    processed BOOLEAN DEFAULT false,
    processing_error TEXT,
    transaction_id INTEGER REFERENCES payment_transactions(id),
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- Payment Gateway Health Checks Table
CREATE TABLE IF NOT EXISTS payment_gateway_health_checks (
    id SERIAL PRIMARY KEY,
    gateway_id INTEGER REFERENCES payment_gateways(id),
    check_type VARCHAR(50) NOT NULL, -- connection, api_key, webhook
    status VARCHAR(50) NOT NULL, -- success, failed, warning
    response_time_ms INTEGER,
    error_message TEXT,
    details JSONB,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payment Refunds Table
CREATE TABLE IF NOT EXISTS payment_refunds (
    id SERIAL PRIMARY KEY,
    transaction_id INTEGER REFERENCES payment_transactions(id),
    gateway_id INTEGER REFERENCES payment_gateways(id),
    external_refund_id VARCHAR(255),
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    reason TEXT,
    status VARCHAR(50) NOT NULL, -- pending, succeeded, failed, cancelled
    error_message TEXT,
    metadata JSONB,
    requested_by INTEGER REFERENCES users(id),
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payment Gateway Fees Table (for tracking actual fees charged)
CREATE TABLE IF NOT EXISTS payment_gateway_fees (
    id SERIAL PRIMARY KEY,
    transaction_id INTEGER REFERENCES payment_transactions(id),
    gateway_id INTEGER REFERENCES payment_gateways(id),
    fixed_fee DECIMAL(10, 2),
    percentage_fee DECIMAL(5, 2),
    calculated_fee DECIMAL(10, 2),
    actual_fee DECIMAL(10, 2), -- From provider's statement
    currency VARCHAR(3) DEFAULT 'USD',
    fee_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payment Methods Saved (for recurring payments)
CREATE TABLE IF NOT EXISTS saved_payment_methods (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    gateway_id INTEGER REFERENCES payment_gateways(id),
    external_payment_method_id VARCHAR(255) NOT NULL,
    payment_method_type VARCHAR(50), -- card, bank_account, paypal
    is_default BOOLEAN DEFAULT false,
    card_last4 VARCHAR(4),
    card_brand VARCHAR(50),
    card_exp_month INTEGER,
    card_exp_year INTEGER,
    billing_address JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_payment_gateways_provider ON payment_gateways(provider);
CREATE INDEX idx_payment_gateways_enabled ON payment_gateways(enabled);
CREATE INDEX idx_payment_gateways_priority ON payment_gateways(priority);
CREATE INDEX idx_payment_transactions_gateway ON payment_transactions(gateway_id);
CREATE INDEX idx_payment_transactions_order ON payment_transactions(order_id);
CREATE INDEX idx_payment_transactions_status ON payment_transactions(status);
CREATE INDEX idx_payment_transactions_external_id ON payment_transactions(external_transaction_id);
CREATE INDEX idx_payment_webhook_logs_gateway ON payment_webhook_logs(gateway_id);
CREATE INDEX idx_payment_webhook_logs_processed ON payment_webhook_logs(processed);
CREATE INDEX idx_payment_webhook_logs_event_id ON payment_webhook_logs(event_id);
CREATE INDEX idx_payment_refunds_transaction ON payment_refunds(transaction_id);
CREATE INDEX idx_payment_refunds_status ON payment_refunds(status);
CREATE INDEX idx_saved_payment_methods_customer ON saved_payment_methods(customer_id);
CREATE INDEX idx_saved_payment_methods_gateway ON saved_payment_methods(gateway_id);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_payment_gateway_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER payment_gateways_updated_at
    BEFORE UPDATE ON payment_gateways
    FOR EACH ROW
    EXECUTE FUNCTION update_payment_gateway_timestamp();

CREATE TRIGGER payment_transactions_updated_at
    BEFORE UPDATE ON payment_transactions
    FOR EACH ROW
    EXECUTE FUNCTION update_payment_gateway_timestamp();

CREATE TRIGGER payment_refunds_updated_at
    BEFORE UPDATE ON payment_refunds
    FOR EACH ROW
    EXECUTE FUNCTION update_payment_gateway_timestamp();

-- Insert sample payment gateways for testing
INSERT INTO payment_gateways (
    provider, name, enabled, test_mode, credentials,
    webhook_url, supported_currencies, supported_payment_methods,
    transaction_fee_fixed, transaction_fee_percentage, priority, status
) VALUES
(
    'stripe',
    'Stripe Test Gateway',
    true,
    true,
    '{"publishable_key": "pk_test_xxxxx", "secret_key": "sk_test_xxxxx", "webhook_secret": "whsec_xxxxx"}'::jsonb,
    'https://api.example.com/webhooks/stripe',
    ARRAY['USD', 'EUR', 'GBP'],
    ARRAY['card', 'apple_pay', 'google_pay'],
    0.30,
    2.9,
    1,
    'active'
),
(
    'paypal',
    'PayPal Test Gateway',
    true,
    true,
    '{"client_id": "xxxxx", "client_secret": "xxxxx"}'::jsonb,
    'https://api.example.com/webhooks/paypal',
    ARRAY['USD', 'EUR'],
    ARRAY['paypal', 'card'],
    0.30,
    2.9,
    2,
    'active'
);

-- Comments for documentation
COMMENT ON TABLE payment_gateways IS 'Stores payment gateway configurations and credentials';
COMMENT ON TABLE payment_transactions IS 'Records all payment transactions processed through gateways';
COMMENT ON TABLE payment_webhook_logs IS 'Logs all webhook events received from payment providers';
COMMENT ON TABLE payment_gateway_health_checks IS 'Tracks health check results for payment gateways';
COMMENT ON TABLE payment_refunds IS 'Manages refund requests and their status';
COMMENT ON TABLE payment_gateway_fees IS 'Tracks payment processing fees for accounting';
COMMENT ON TABLE saved_payment_methods IS 'Stores customer payment methods for recurring payments';

