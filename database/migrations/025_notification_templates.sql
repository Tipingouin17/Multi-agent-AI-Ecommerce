-- Notification Templates Migration
-- Supports multi-channel notification management (Email, SMS, Push)

-- Notification Templates Table
CREATE TABLE IF NOT EXISTS notification_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- email, sms, push
    category VARCHAR(50) NOT NULL, -- order, shipping, account, marketing, system, payment
    trigger_event VARCHAR(100) NOT NULL, -- order_placed, order_shipped, etc.
    subject VARCHAR(500), -- For email and push notifications
    body TEXT NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    enabled BOOLEAN DEFAULT true,
    variables TEXT[], -- List of variables used in template
    metadata JSONB, -- Additional settings (from_email, reply_to, etc.)
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- Notification Template Versions (for version control)
CREATE TABLE IF NOT EXISTS notification_template_versions (
    id SERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES notification_templates(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    subject VARCHAR(500),
    body TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    UNIQUE(template_id, version)
);

-- Notification Queue (pending notifications to be sent)
CREATE TABLE IF NOT EXISTS notification_queue (
    id SERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES notification_templates(id),
    recipient_type VARCHAR(50) NOT NULL, -- customer, merchant, admin
    recipient_id INTEGER NOT NULL,
    recipient_email VARCHAR(255),
    recipient_phone VARCHAR(50),
    recipient_device_token VARCHAR(500), -- For push notifications
    subject VARCHAR(500),
    body TEXT NOT NULL,
    variables JSONB, -- Variable values for this notification
    priority INTEGER DEFAULT 5, -- 1=highest, 10=lowest
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, sent, failed, cancelled
    scheduled_at TIMESTAMP,
    sent_at TIMESTAMP,
    failed_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notification Delivery Log (history of sent notifications)
CREATE TABLE IF NOT EXISTS notification_delivery_log (
    id SERIAL PRIMARY KEY,
    queue_id INTEGER REFERENCES notification_queue(id),
    template_id INTEGER REFERENCES notification_templates(id),
    recipient_type VARCHAR(50) NOT NULL,
    recipient_id INTEGER NOT NULL,
    notification_type VARCHAR(50) NOT NULL, -- email, sms, push
    subject VARCHAR(500),
    body TEXT,
    status VARCHAR(50) NOT NULL, -- sent, delivered, opened, clicked, bounced, failed
    provider VARCHAR(100), -- sendgrid, twilio, firebase, etc.
    provider_message_id VARCHAR(255),
    delivery_time_ms INTEGER,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    bounced_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notification Preferences (user preferences for notifications)
CREATE TABLE IF NOT EXISTS notification_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL, -- email, sms, push
    category VARCHAR(50) NOT NULL, -- order, shipping, account, marketing, system
    enabled BOOLEAN DEFAULT true,
    frequency VARCHAR(50) DEFAULT 'immediate', -- immediate, daily_digest, weekly_digest
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, notification_type, category),
    UNIQUE(customer_id, notification_type, category)
);

-- Notification A/B Tests
CREATE TABLE IF NOT EXISTS notification_ab_tests (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_a_id INTEGER REFERENCES notification_templates(id),
    template_b_id INTEGER REFERENCES notification_templates(id),
    status VARCHAR(50) DEFAULT 'draft', -- draft, running, paused, completed
    traffic_split INTEGER DEFAULT 50, -- Percentage for template A (B gets 100-split)
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    winner_template_id INTEGER REFERENCES notification_templates(id),
    metrics JSONB, -- open_rate, click_rate, conversion_rate
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

-- Notification Analytics (aggregated statistics)
CREATE TABLE IF NOT EXISTS notification_analytics (
    id SERIAL PRIMARY KEY,
    template_id INTEGER REFERENCES notification_templates(id),
    date DATE NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    sent_count INTEGER DEFAULT 0,
    delivered_count INTEGER DEFAULT 0,
    opened_count INTEGER DEFAULT 0,
    clicked_count INTEGER DEFAULT 0,
    bounced_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    unsubscribed_count INTEGER DEFAULT 0,
    avg_delivery_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(template_id, date, notification_type)
);

-- Notification Unsubscribes
CREATE TABLE IF NOT EXISTS notification_unsubscribes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    customer_id INTEGER REFERENCES customers(id),
    email VARCHAR(255),
    notification_type VARCHAR(50), -- email, sms, push, all
    category VARCHAR(50), -- order, shipping, marketing, all
    reason TEXT,
    unsubscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_notification_templates_type ON notification_templates(type);
CREATE INDEX idx_notification_templates_category ON notification_templates(category);
CREATE INDEX idx_notification_templates_trigger ON notification_templates(trigger_event);
CREATE INDEX idx_notification_templates_enabled ON notification_templates(enabled);
CREATE INDEX idx_notification_queue_status ON notification_queue(status);
CREATE INDEX idx_notification_queue_scheduled ON notification_queue(scheduled_at);
CREATE INDEX idx_notification_queue_recipient ON notification_queue(recipient_type, recipient_id);
CREATE INDEX idx_notification_delivery_log_template ON notification_delivery_log(template_id);
CREATE INDEX idx_notification_delivery_log_recipient ON notification_delivery_log(recipient_type, recipient_id);
CREATE INDEX idx_notification_delivery_log_status ON notification_delivery_log(status);
CREATE INDEX idx_notification_delivery_log_sent_at ON notification_delivery_log(sent_at);
CREATE INDEX idx_notification_preferences_user ON notification_preferences(user_id);
CREATE INDEX idx_notification_preferences_customer ON notification_preferences(customer_id);
CREATE INDEX idx_notification_analytics_template_date ON notification_analytics(template_id, date);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_notification_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER notification_templates_updated_at
    BEFORE UPDATE ON notification_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_notification_timestamp();

CREATE TRIGGER notification_preferences_updated_at
    BEFORE UPDATE ON notification_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_notification_timestamp();

CREATE TRIGGER notification_ab_tests_updated_at
    BEFORE UPDATE ON notification_ab_tests
    FOR EACH ROW
    EXECUTE FUNCTION update_notification_timestamp();

-- Insert sample notification templates
INSERT INTO notification_templates (
    name, type, category, trigger_event, subject, body, language, enabled, variables, metadata
) VALUES
(
    'Order Confirmation Email',
    'email',
    'order',
    'order_placed',
    'Order Confirmation - Order #{{order_id}}',
    E'Hi {{customer_name}},\n\nThank you for your order! We''re excited to confirm that we''ve received your order #{{order_id}}.\n\nOrder Total: ${{order_total}}\n\nWe''ll send you another email when your order ships.\n\nBest regards,\n{{company_name}}',
    'en',
    true,
    ARRAY['customer_name', 'order_id', 'order_total', 'company_name'],
    '{"from_name": "Your Store", "from_email": "orders@example.com", "reply_to": "support@example.com"}'::jsonb
),
(
    'Order Shipped Email',
    'email',
    'shipping',
    'order_shipped',
    'Your Order Has Shipped! - Order #{{order_id}}',
    E'Hi {{customer_name}},\n\nGreat news! Your order #{{order_id}} has been shipped.\n\nTracking Number: {{tracking_number}}\n\nYou can track your package at: {{tracking_url}}\n\nEstimated Delivery: {{delivery_date}}\n\nBest regards,\n{{company_name}}',
    'en',
    true,
    ARRAY['customer_name', 'order_id', 'tracking_number', 'tracking_url', 'delivery_date', 'company_name'],
    '{"from_name": "Your Store", "from_email": "shipping@example.com", "reply_to": "support@example.com"}'::jsonb
),
(
    'Order Shipped SMS',
    'sms',
    'shipping',
    'order_shipped',
    NULL,
    'Hi {{customer_name}}, your order #{{order_id}} has shipped! Track it here: {{short_url}}',
    'en',
    true,
    ARRAY['customer_name', 'order_id', 'short_url'],
    '{}'::jsonb
),
(
    'Order Delivered Push',
    'push',
    'shipping',
    'order_delivered',
    'Your Order Has Been Delivered!',
    'Order #{{order_id}} has been delivered. We hope you love it!',
    'en',
    true,
    ARRAY['order_id'],
    '{"badge_count": 1, "sound": "default"}'::jsonb
),
(
    'Password Reset Email',
    'email',
    'account',
    'password_reset',
    'Reset Your Password',
    E'Hi {{customer_name}},\n\nWe received a request to reset your password. Click the link below to create a new password:\n\n{{reset_url}}\n\nThis link will expire in 24 hours.\n\nIf you didn''t request this, please ignore this email.\n\nBest regards,\n{{company_name}}',
    'en',
    true,
    ARRAY['customer_name', 'reset_url', 'company_name'],
    '{"from_name": "Your Store", "from_email": "noreply@example.com"}'::jsonb
),
(
    'Abandoned Cart Email',
    'email',
    'marketing',
    'abandoned_cart',
    'You Left Something Behind! 🛒',
    E'Hi {{customer_name}},\n\nWe noticed you left some items in your cart. Don''t miss out!\n\n{{cart_items}}\n\nTotal: ${{cart_total}}\n\nComplete your purchase now: {{cart_url}}\n\nBest regards,\n{{company_name}}',
    'en',
    true,
    ARRAY['customer_name', 'cart_items', 'cart_total', 'cart_url', 'company_name'],
    '{"from_name": "Your Store", "from_email": "marketing@example.com"}'::jsonb
),
(
    'Low Stock Alert Email',
    'email',
    'system',
    'low_stock_alert',
    'Low Stock Alert - {{product_name}}',
    E'Alert: {{product_name}} (SKU: {{sku}}) is running low.\n\nCurrent Stock: {{current_stock}} units\nReorder Point: {{reorder_point}} units\n\nAction Required: Please reorder inventory.\n\nView Product: {{product_url}}',
    'en',
    true,
    ARRAY['product_name', 'sku', 'current_stock', 'reorder_point', 'product_url'],
    '{"from_name": "Inventory System", "from_email": "alerts@example.com"}'::jsonb
);

-- Comments for documentation
COMMENT ON TABLE notification_templates IS 'Stores notification templates for email, SMS, and push notifications';
COMMENT ON TABLE notification_template_versions IS 'Version history of notification templates';
COMMENT ON TABLE notification_queue IS 'Queue of pending notifications to be sent';
COMMENT ON TABLE notification_delivery_log IS 'Historical log of all sent notifications';
COMMENT ON TABLE notification_preferences IS 'User preferences for receiving notifications';
COMMENT ON TABLE notification_ab_tests IS 'A/B testing configurations for notification templates';
COMMENT ON TABLE notification_analytics IS 'Aggregated analytics for notification performance';
COMMENT ON TABLE notification_unsubscribes IS 'Records of users who unsubscribed from notifications';

