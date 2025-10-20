-- =====================================================
-- NOTIFICATION AGENT DATABASE MIGRATION
-- =====================================================
-- This migration creates comprehensive notification management tables
-- for multi-channel notifications (email, SMS, push, in-app).

-- =====================================================
-- 1. NOTIFICATION TEMPLATES
-- =====================================================

CREATE TABLE IF NOT EXISTS notification_templates (
    template_id SERIAL PRIMARY KEY,
    template_name VARCHAR(100) UNIQUE NOT NULL,
    template_code VARCHAR(50) UNIQUE NOT NULL,
    channel VARCHAR(20) NOT NULL, -- 'email', 'sms', 'push', 'in_app'
    category VARCHAR(50) NOT NULL, -- 'order', 'shipping', 'payment', 'marketing', 'system'
    
    -- Content
    subject VARCHAR(500), -- for email
    body_text TEXT NOT NULL,
    body_html TEXT, -- for email
    
    -- Localization
    language VARCHAR(5) DEFAULT 'en',
    
    -- Variables
    variables JSONB DEFAULT '[]', -- [{name, type, required, default}]
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notification_templates_code ON notification_templates(template_code);
CREATE INDEX IF NOT EXISTS idx_notification_templates_channel ON notification_templates(channel);
CREATE INDEX IF NOT EXISTS idx_notification_templates_category ON notification_templates(category);

COMMENT ON TABLE notification_templates IS 'Notification templates for multi-channel messaging';

-- =====================================================
-- 2. NOTIFICATIONS
-- =====================================================

CREATE TABLE IF NOT EXISTS notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id INTEGER REFERENCES notification_templates(template_id),
    
    -- Recipient
    recipient_id VARCHAR(100) NOT NULL, -- customer_id, user_id, etc.
    recipient_email VARCHAR(255),
    recipient_phone VARCHAR(50),
    recipient_device_token VARCHAR(500),
    
    -- Channel
    channel VARCHAR(20) NOT NULL, -- 'email', 'sms', 'push', 'in_app'
    
    -- Content
    subject VARCHAR(500),
    body TEXT NOT NULL,
    
    -- Context
    context_type VARCHAR(50), -- 'order', 'shipment', 'payment', etc.
    context_id VARCHAR(100), -- order_id, shipment_id, etc.
    metadata JSONB DEFAULT '{}',
    
    -- Status
    notification_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'sent', 'delivered', 'failed', 'read'
    
    -- Delivery
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,
    failed_at TIMESTAMP,
    
    -- Error handling
    error_code VARCHAR(100),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Provider response
    provider VARCHAR(50), -- 'sendgrid', 'twilio', 'fcm', etc.
    provider_message_id VARCHAR(200),
    provider_response JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON notifications(recipient_id);
CREATE INDEX IF NOT EXISTS idx_notifications_channel ON notifications(channel);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(notification_status);
CREATE INDEX IF NOT EXISTS idx_notifications_context ON notifications(context_type, context_id);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_sent ON notifications(sent_at DESC);

COMMENT ON TABLE notifications IS 'Notification records across all channels';

-- =====================================================
-- 3. NOTIFICATION PREFERENCES
-- =====================================================

CREATE TABLE IF NOT EXISTS notification_preferences (
    preference_id SERIAL PRIMARY KEY,
    customer_id VARCHAR(100) NOT NULL,
    
    -- Channel preferences
    email_enabled BOOLEAN DEFAULT true,
    sms_enabled BOOLEAN DEFAULT false,
    push_enabled BOOLEAN DEFAULT true,
    in_app_enabled BOOLEAN DEFAULT true,
    
    -- Category preferences
    order_notifications BOOLEAN DEFAULT true,
    shipping_notifications BOOLEAN DEFAULT true,
    payment_notifications BOOLEAN DEFAULT true,
    marketing_notifications BOOLEAN DEFAULT false,
    system_notifications BOOLEAN DEFAULT true,
    
    -- Frequency
    digest_frequency VARCHAR(20) DEFAULT 'immediate', -- 'immediate', 'daily', 'weekly'
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    
    -- Contact info
    preferred_email VARCHAR(255),
    preferred_phone VARCHAR(50),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(customer_id)
);

CREATE INDEX IF NOT EXISTS idx_notification_preferences_customer ON notification_preferences(customer_id);

COMMENT ON TABLE notification_preferences IS 'Customer notification preferences';

-- =====================================================
-- 4. NOTIFICATION SCHEDULES
-- =====================================================

CREATE TABLE IF NOT EXISTS notification_schedules (
    schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id INTEGER REFERENCES notification_templates(template_id),
    
    -- Schedule details
    schedule_name VARCHAR(100) NOT NULL,
    schedule_type VARCHAR(50) NOT NULL, -- 'one_time', 'recurring', 'triggered'
    
    -- Timing
    scheduled_at TIMESTAMP,
    recurrence_rule VARCHAR(200), -- cron expression or rrule
    
    -- Recipient criteria
    recipient_filter JSONB DEFAULT '{}', -- criteria for selecting recipients
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notification_schedules_next_run ON notification_schedules(next_run_at);
CREATE INDEX IF NOT EXISTS idx_notification_schedules_active ON notification_schedules(is_active);

COMMENT ON TABLE notification_schedules IS 'Scheduled notification campaigns';

-- =====================================================
-- 5. NOTIFICATION LOGS
-- =====================================================

CREATE TABLE IF NOT EXISTS notification_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_id UUID REFERENCES notifications(notification_id),
    
    -- Event
    event_type VARCHAR(50) NOT NULL, -- 'queued', 'sent', 'delivered', 'opened', 'clicked', 'failed', 'bounced'
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Details
    event_data JSONB DEFAULT '{}',
    
    -- Provider
    provider VARCHAR(50),
    provider_event_id VARCHAR(200),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notification_logs_notification ON notification_logs(notification_id);
CREATE INDEX IF NOT EXISTS idx_notification_logs_event ON notification_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_notification_logs_timestamp ON notification_logs(event_timestamp DESC);

COMMENT ON TABLE notification_logs IS 'Notification delivery event logs';

-- =====================================================
-- MATERIALIZED VIEWS
-- =====================================================

-- Notification Summary by Channel
CREATE MATERIALIZED VIEW IF NOT EXISTS notification_summary_by_channel AS
SELECT 
    channel,
    DATE_TRUNC('day', created_at) as date,
    COUNT(*) as total_notifications,
    COUNT(CASE WHEN notification_status = 'sent' THEN 1 END) as sent_count,
    COUNT(CASE WHEN notification_status = 'delivered' THEN 1 END) as delivered_count,
    COUNT(CASE WHEN notification_status = 'failed' THEN 1 END) as failed_count,
    COUNT(CASE WHEN read_at IS NOT NULL THEN 1 END) as read_count,
    ROUND(COUNT(CASE WHEN notification_status = 'delivered' THEN 1 END)::numeric / 
          NULLIF(COUNT(CASE WHEN notification_status = 'sent' THEN 1 END), 0) * 100, 2) as delivery_rate,
    ROUND(COUNT(CASE WHEN read_at IS NOT NULL THEN 1 END)::numeric / 
          NULLIF(COUNT(CASE WHEN notification_status = 'delivered' THEN 1 END), 0) * 100, 2) as read_rate
FROM notifications
GROUP BY channel, DATE_TRUNC('day', created_at);

CREATE INDEX IF NOT EXISTS idx_notification_summary_channel_date ON notification_summary_by_channel(channel, date DESC);

COMMENT ON MATERIALIZED VIEW notification_summary_by_channel IS 'Daily notification metrics by channel';

-- =====================================================
-- TRIGGERS
-- =====================================================

CREATE OR REPLACE FUNCTION update_notification_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_notification_templates_timestamp
    BEFORE UPDATE ON notification_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_notification_timestamp();

CREATE TRIGGER trigger_update_notifications_timestamp
    BEFORE UPDATE ON notifications
    FOR EACH ROW
    EXECUTE FUNCTION update_notification_timestamp();

CREATE TRIGGER trigger_update_notification_preferences_timestamp
    BEFORE UPDATE ON notification_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_notification_timestamp();

CREATE TRIGGER trigger_update_notification_schedules_timestamp
    BEFORE UPDATE ON notification_schedules
    FOR EACH ROW
    EXECUTE FUNCTION update_notification_timestamp();

-- =====================================================
-- FUNCTIONS
-- =====================================================

-- Function to refresh notification views
CREATE OR REPLACE FUNCTION refresh_notification_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY notification_summary_by_channel;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_notification_views() IS 'Refresh notification materialized views';

-- =====================================================
-- INITIAL DATA
-- =====================================================

-- Insert default notification templates
INSERT INTO notification_templates (template_name, template_code, channel, category, subject, body_text, variables)
VALUES 
    ('Order Confirmation', 'ORDER_CONFIRMATION', 'email', 'order', 
     'Order Confirmation - {{order_id}}', 
     'Thank you for your order {{order_id}}. Total: {{total_amount}}.',
     '[{"name": "order_id", "type": "string", "required": true}, {"name": "total_amount", "type": "string", "required": true}]'::jsonb),
    ('Shipment Tracking', 'SHIPMENT_TRACKING', 'email', 'shipping',
     'Your order has shipped - Tracking: {{tracking_number}}',
     'Your order {{order_id}} has been shipped. Tracking number: {{tracking_number}}.',
     '[{"name": "order_id", "type": "string", "required": true}, {"name": "tracking_number", "type": "string", "required": true}]'::jsonb),
    ('Payment Successful', 'PAYMENT_SUCCESS', 'email', 'payment',
     'Payment Received - {{amount}}',
     'We have received your payment of {{amount}}. Transaction ID: {{transaction_id}}.',
     '[{"name": "amount", "type": "string", "required": true}, {"name": "transaction_id", "type": "string", "required": true}]'::jsonb)
ON CONFLICT (template_code) DO NOTHING;

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================

COMMENT ON SCHEMA public IS 'Notification Agent migration 008 completed successfully';

