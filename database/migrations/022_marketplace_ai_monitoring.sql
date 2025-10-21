-- Marketplace AI Monitoring & Knowledge Management Schema
-- This migration adds tables for AI-powered marketplace monitoring,
-- self-learning knowledge management, and human-in-the-loop decision tracking

-- Marketplace Rules Table
CREATE TABLE IF NOT EXISTS marketplace_rules (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    marketplace_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- 'required_field', 'format_validation', 'business_rule'
    rule_description TEXT NOT NULL,
    validation_logic JSONB,
    auto_correction_logic JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_marketplace_rules_marketplace ON marketplace_rules(marketplace_name);
CREATE INDEX idx_marketplace_rules_type ON marketplace_rules(rule_type);

-- Issue Patterns Table
CREATE TABLE IF NOT EXISTS issue_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    marketplace_name VARCHAR(100) NOT NULL,
    issue_type VARCHAR(100) NOT NULL,
    issue_description TEXT NOT NULL,
    pattern_signature JSONB NOT NULL, -- Unique identifier for this issue type
    occurrence_count INTEGER DEFAULT 1,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_issue_patterns_marketplace ON issue_patterns(marketplace_name);
CREATE INDEX idx_issue_patterns_type ON issue_patterns(issue_type);
CREATE INDEX idx_issue_patterns_signature ON issue_patterns USING GIN(pattern_signature);

-- Correction Decisions Table
CREATE TABLE IF NOT EXISTS correction_decisions (
    decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id UUID REFERENCES issue_patterns(pattern_id) ON DELETE CASCADE,
    issue_data JSONB NOT NULL,
    ai_suggestion JSONB NOT NULL,
    human_decision VARCHAR(50) NOT NULL, -- 'approved', 'rejected', 'modified'
    final_solution JSONB NOT NULL,
    decided_by VARCHAR(100) NOT NULL, -- User ID
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence_score DECIMAL(5,2) NOT NULL,
    notes TEXT
);

CREATE INDEX idx_correction_decisions_pattern ON correction_decisions(pattern_id);
CREATE INDEX idx_correction_decisions_decision ON correction_decisions(human_decision);
CREATE INDEX idx_correction_decisions_user ON correction_decisions(decided_by);

-- Auto-Correction Rules Table
CREATE TABLE IF NOT EXISTS auto_correction_rules (
    auto_rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id UUID REFERENCES issue_patterns(pattern_id) ON DELETE CASCADE,
    correction_logic JSONB NOT NULL,
    confidence_threshold DECIMAL(5,2) NOT NULL DEFAULT 0.80,
    success_rate DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    application_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_auto_correction_rules_pattern ON auto_correction_rules(pattern_id);
CREATE INDEX idx_auto_correction_rules_active ON auto_correction_rules(is_active);

-- Marketplace Connections Table
CREATE TABLE IF NOT EXISTS marketplace_connections (
    connection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    marketplace_name VARCHAR(100) NOT NULL,
    marketplace_type VARCHAR(50) NOT NULL, -- 'marketplace' or 'ecommerce'
    store_name VARCHAR(200) NOT NULL,
    store_url VARCHAR(500),
    api_credentials JSONB NOT NULL, -- Encrypted credentials
    sync_frequency INTEGER DEFAULT 300, -- seconds
    is_active BOOLEAN DEFAULT true,
    last_sync_at TIMESTAMP,
    sync_status VARCHAR(50) DEFAULT 'pending', -- 'active', 'syncing', 'error', 'inactive'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_marketplace_connections_name ON marketplace_connections(marketplace_name);
CREATE INDEX idx_marketplace_connections_status ON marketplace_connections(sync_status);

-- Marketplace Sync History Table
CREATE TABLE IF NOT EXISTS marketplace_sync_history (
    sync_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID REFERENCES marketplace_connections(connection_id) ON DELETE CASCADE,
    sync_type VARCHAR(50) NOT NULL, -- 'products', 'orders', 'inventory'
    records_synced INTEGER DEFAULT 0,
    issues_detected INTEGER DEFAULT 0,
    auto_corrected INTEGER DEFAULT 0,
    requires_review INTEGER DEFAULT 0,
    sync_duration_ms INTEGER,
    sync_status VARCHAR(50) NOT NULL, -- 'success', 'partial', 'failed'
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_sync_history_connection ON marketplace_sync_history(connection_id);
CREATE INDEX idx_sync_history_status ON marketplace_sync_history(sync_status);
CREATE INDEX idx_sync_history_started ON marketplace_sync_history(started_at DESC);

-- Detected Issues Table
CREATE TABLE IF NOT EXISTS detected_issues (
    issue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID REFERENCES marketplace_connections(connection_id) ON DELETE CASCADE,
    pattern_id UUID REFERENCES issue_patterns(pattern_id),
    sync_id UUID REFERENCES marketplace_sync_history(sync_id),
    issue_type VARCHAR(100) NOT NULL,
    issue_description TEXT NOT NULL,
    affected_entity_type VARCHAR(50) NOT NULL, -- 'product', 'order', 'inventory'
    affected_entity_id VARCHAR(200) NOT NULL,
    affected_entity_data JSONB,
    ai_suggestion JSONB,
    ai_confidence DECIMAL(5,2),
    resolution_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'auto_corrected', 'approved', 'rejected'
    resolution_data JSONB,
    resolved_by VARCHAR(100),
    resolved_at TIMESTAMP,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_detected_issues_connection ON detected_issues(connection_id);
CREATE INDEX idx_detected_issues_pattern ON detected_issues(pattern_id);
CREATE INDEX idx_detected_issues_status ON detected_issues(resolution_status);
CREATE INDEX idx_detected_issues_entity ON detected_issues(affected_entity_type, affected_entity_id);

-- Knowledge Base Statistics View
CREATE OR REPLACE VIEW knowledge_base_stats AS
SELECT 
    ip.pattern_id,
    ip.marketplace_name,
    ip.issue_type,
    ip.issue_description,
    ip.occurrence_count,
    COUNT(cd.decision_id) as total_decisions,
    SUM(CASE WHEN cd.human_decision = 'approved' THEN 1 ELSE 0 END) as approved_count,
    SUM(CASE WHEN cd.human_decision = 'rejected' THEN 1 ELSE 0 END) as rejected_count,
    CASE 
        WHEN COUNT(cd.decision_id) > 0 THEN 
            ROUND(SUM(CASE WHEN cd.human_decision = 'approved' THEN 1 ELSE 0 END)::DECIMAL / COUNT(cd.decision_id), 2)
        ELSE 0
    END as success_rate,
    acr.confidence_threshold,
    acr.is_active as auto_correct_enabled
FROM issue_patterns ip
LEFT JOIN correction_decisions cd ON ip.pattern_id = cd.pattern_id
LEFT JOIN auto_correction_rules acr ON ip.pattern_id = acr.pattern_id
GROUP BY ip.pattern_id, ip.marketplace_name, ip.issue_type, ip.issue_description, 
         ip.occurrence_count, acr.confidence_threshold, acr.is_active;

-- Marketplace Performance View
CREATE OR REPLACE VIEW marketplace_performance AS
SELECT 
    mc.connection_id,
    mc.marketplace_name,
    mc.store_name,
    mc.sync_status,
    mc.last_sync_at,
    COUNT(DISTINCT msh.sync_id) as total_syncs,
    SUM(msh.records_synced) as total_records_synced,
    SUM(msh.issues_detected) as total_issues_detected,
    SUM(msh.auto_corrected) as total_auto_corrected,
    SUM(msh.requires_review) as total_requires_review,
    AVG(msh.sync_duration_ms) as avg_sync_duration_ms
FROM marketplace_connections mc
LEFT JOIN marketplace_sync_history msh ON mc.connection_id = msh.connection_id
WHERE msh.started_at > NOW() - INTERVAL '24 hours'
GROUP BY mc.connection_id, mc.marketplace_name, mc.store_name, mc.sync_status, mc.last_sync_at;

-- Insert sample marketplace rules
INSERT INTO marketplace_rules (marketplace_name, rule_type, rule_description, validation_logic) VALUES
('shopify', 'required_field', 'Product must have title', '{"field": "title", "required": true}'),
('shopify', 'required_field', 'Product must have price', '{"field": "price", "required": true}'),
('amazon', 'required_field', 'Product must have brand', '{"field": "brand", "required": true}'),
('amazon', 'required_field', 'Product must have description', '{"field": "description", "required": true}'),
('mirakl', 'required_field', 'Product must have leadtime', '{"field": "leadtime", "required": true}'),
('ebay', 'required_field', 'Product must have return_policy', '{"field": "return_policy", "required": true}');

COMMENT ON TABLE marketplace_rules IS 'Marketplace-specific validation rules';
COMMENT ON TABLE issue_patterns IS 'Detected issue patterns for learning';
COMMENT ON TABLE correction_decisions IS 'Human decisions on AI suggestions';
COMMENT ON TABLE auto_correction_rules IS 'Learned rules for auto-correction';
COMMENT ON TABLE marketplace_connections IS 'Active marketplace connections';
COMMENT ON TABLE marketplace_sync_history IS 'History of marketplace synchronizations';
COMMENT ON TABLE detected_issues IS 'Issues detected during sync';

