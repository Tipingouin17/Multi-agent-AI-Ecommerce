-- Workflow Configuration Migration
-- Supports visual workflow builder and automation

-- Workflows Table
CREATE TABLE IF NOT EXISTS workflows (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL, -- orders, inventory, returns, shipping, customer, marketing
    trigger_type VARCHAR(100) NOT NULL, -- order_placed, inventory_low, etc.
    enabled BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 5, -- 1=highest, 10=lowest
    nodes JSONB NOT NULL, -- Workflow nodes configuration
    connections JSONB, -- Node connections
    version INTEGER DEFAULT 1,
    execution_count BIGINT DEFAULT 0,
    last_executed_at TIMESTAMP,
    avg_execution_time_ms INTEGER,
    success_rate DECIMAL(5, 2),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- Workflow Versions (for version control)
CREATE TABLE IF NOT EXISTS workflow_versions (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES workflows(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    nodes JSONB NOT NULL,
    connections JSONB,
    change_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    UNIQUE(workflow_id, version)
);

-- Workflow Executions (execution history)
CREATE TABLE IF NOT EXISTS workflow_executions (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES workflows(id) ON DELETE CASCADE,
    trigger_data JSONB, -- Data that triggered the workflow
    status VARCHAR(50) DEFAULT 'running', -- running, completed, failed, cancelled
    current_node_id VARCHAR(255),
    execution_path JSONB, -- Sequence of nodes executed
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    duration_ms INTEGER,
    error_message TEXT,
    output_data JSONB,
    metadata JSONB
);

-- Workflow Node Executions (individual node execution logs)
CREATE TABLE IF NOT EXISTS workflow_node_executions (
    id SERIAL PRIMARY KEY,
    execution_id INTEGER REFERENCES workflow_executions(id) ON DELETE CASCADE,
    node_id VARCHAR(255) NOT NULL,
    node_type VARCHAR(50) NOT NULL,
    node_subtype VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'running', -- running, completed, failed, skipped
    input_data JSONB,
    output_data JSONB,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    duration_ms INTEGER,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0
);

-- Workflow Triggers (scheduled or event-based triggers)
CREATE TABLE IF NOT EXISTS workflow_triggers (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES workflows(id) ON DELETE CASCADE,
    trigger_type VARCHAR(100) NOT NULL, -- event, schedule, manual, api
    event_type VARCHAR(100), -- For event-based triggers
    schedule_cron VARCHAR(100), -- For scheduled triggers
    enabled BOOLEAN DEFAULT true,
    last_triggered_at TIMESTAMP,
    trigger_count BIGINT DEFAULT 0,
    conditions JSONB, -- Trigger conditions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workflow Templates (predefined workflow templates)
CREATE TABLE IF NOT EXISTS workflow_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    nodes JSONB NOT NULL,
    connections JSONB,
    tags TEXT[],
    usage_count INTEGER DEFAULT 0,
    is_public BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

-- Workflow Analytics (aggregated performance metrics)
CREATE TABLE IF NOT EXISTS workflow_analytics (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES workflows(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    avg_duration_ms INTEGER,
    min_duration_ms INTEGER,
    max_duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workflow_id, date)
);

-- Workflow Alerts (monitoring and alerting)
CREATE TABLE IF NOT EXISTS workflow_alerts (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES workflows(id) ON DELETE CASCADE,
    alert_type VARCHAR(100) NOT NULL, -- execution_failure, high_duration, low_success_rate
    severity VARCHAR(50) NOT NULL, -- info, warning, critical
    message TEXT NOT NULL,
    execution_id INTEGER REFERENCES workflow_executions(id),
    acknowledged BOOLEAN DEFAULT false,
    acknowledged_by INTEGER REFERENCES users(id),
    acknowledged_at TIMESTAMP,
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workflow Dependencies (workflow relationships)
CREATE TABLE IF NOT EXISTS workflow_dependencies (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES workflows(id) ON DELETE CASCADE,
    depends_on_workflow_id INTEGER REFERENCES workflows(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) NOT NULL, -- sequential, parallel, conditional
    condition JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workflow_id, depends_on_workflow_id)
);

-- Indexes for performance
CREATE INDEX idx_workflows_category ON workflows(category);
CREATE INDEX idx_workflows_enabled ON workflows(enabled);
CREATE INDEX idx_workflows_trigger_type ON workflows(trigger_type);
CREATE INDEX idx_workflow_executions_workflow ON workflow_executions(workflow_id);
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX idx_workflow_executions_start_time ON workflow_executions(start_time);
CREATE INDEX idx_workflow_node_executions_execution ON workflow_node_executions(execution_id);
CREATE INDEX idx_workflow_triggers_workflow ON workflow_triggers(workflow_id);
CREATE INDEX idx_workflow_triggers_enabled ON workflow_triggers(enabled);
CREATE INDEX idx_workflow_analytics_workflow_date ON workflow_analytics(workflow_id, date);
CREATE INDEX idx_workflow_alerts_workflow ON workflow_alerts(workflow_id);
CREATE INDEX idx_workflow_alerts_acknowledged ON workflow_alerts(acknowledged);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_workflow_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER workflows_updated_at
    BEFORE UPDATE ON workflows
    FOR EACH ROW
    EXECUTE FUNCTION update_workflow_timestamp();

CREATE TRIGGER workflow_triggers_updated_at
    BEFORE UPDATE ON workflow_triggers
    FOR EACH ROW
    EXECUTE FUNCTION update_workflow_timestamp();

-- Function to increment workflow execution count
CREATE OR REPLACE FUNCTION increment_workflow_execution_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE workflows
    SET execution_count = execution_count + 1,
        last_executed_at = NEW.start_time
    WHERE id = NEW.workflow_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER workflow_execution_counter
    AFTER INSERT ON workflow_executions
    FOR EACH ROW
    EXECUTE FUNCTION increment_workflow_execution_count();

-- Insert sample workflows
INSERT INTO workflows (
    name, description, category, trigger_type, enabled, priority, nodes, connections
) VALUES
(
    'Order Fulfillment Workflow',
    'Automated order processing from payment confirmation to shipment',
    'orders',
    'order_paid',
    true,
    1,
    '[
        {"id": "node_1", "type": "trigger", "subtype": "order_paid", "x": 100, "y": 100, "config": {}},
        {"id": "node_2", "type": "action", "subtype": "update_order_status", "x": 300, "y": 100, "config": {"status": "processing"}},
        {"id": "node_3", "type": "condition", "subtype": "check_inventory", "x": 500, "y": 100, "config": {"threshold": 1}},
        {"id": "node_4", "type": "action", "subtype": "create_shipment", "x": 700, "y": 100, "config": {}},
        {"id": "node_5", "type": "action", "subtype": "send_email", "x": 900, "y": 100, "config": {"template": "order_shipped"}}
    ]'::jsonb,
    '[
        {"from": "node_1", "to": "node_2"},
        {"from": "node_2", "to": "node_3"},
        {"from": "node_3", "to": "node_4", "condition": "in_stock"},
        {"from": "node_4", "to": "node_5"}
    ]'::jsonb
),
(
    'Low Inventory Alert',
    'Notify when product stock falls below reorder point',
    'inventory',
    'inventory_low',
    true,
    3,
    '[
        {"id": "node_1", "type": "trigger", "subtype": "inventory_low", "x": 100, "y": 100, "config": {}},
        {"id": "node_2", "type": "data", "subtype": "get_data", "x": 300, "y": 100, "config": {"entity": "product"}},
        {"id": "node_3", "type": "action", "subtype": "send_email", "x": 500, "y": 100, "config": {"template": "low_stock_alert"}},
        {"id": "node_4", "type": "action", "subtype": "call_api", "x": 700, "y": 100, "config": {"endpoint": "supplier_reorder"}}
    ]'::jsonb,
    '[
        {"from": "node_1", "to": "node_2"},
        {"from": "node_2", "to": "node_3"},
        {"from": "node_3", "to": "node_4"}
    ]'::jsonb
),
(
    'Return Processing Workflow',
    'Automated return request processing and approval',
    'returns',
    'return_requested',
    true,
    2,
    '[
        {"id": "node_1", "type": "trigger", "subtype": "return_requested", "x": 100, "y": 100, "config": {}},
        {"id": "node_2", "type": "action", "subtype": "send_email", "x": 300, "y": 100, "config": {"template": "return_received"}},
        {"id": "node_3", "type": "delay", "subtype": "wait", "x": 500, "y": 100, "config": {"duration": "24h"}},
        {"id": "node_4", "type": "condition", "subtype": "validate_data", "x": 700, "y": 100, "config": {"field": "return_reason"}},
        {"id": "node_5", "type": "action", "subtype": "update_order_status", "x": 900, "y": 50, "config": {"status": "return_approved"}},
        {"id": "node_6", "type": "action", "subtype": "send_email", "x": 900, "y": 150, "config": {"template": "return_rejected"}}
    ]'::jsonb,
    '[
        {"from": "node_1", "to": "node_2"},
        {"from": "node_2", "to": "node_3"},
        {"from": "node_3", "to": "node_4"},
        {"from": "node_4", "to": "node_5", "condition": "valid"},
        {"from": "node_4", "to": "node_6", "condition": "invalid"}
    ]'::jsonb
),
(
    'Abandoned Cart Recovery',
    'Send reminder emails for abandoned shopping carts',
    'marketing',
    'scheduled',
    true,
    5,
    '[
        {"id": "node_1", "type": "trigger", "subtype": "scheduled", "x": 100, "y": 100, "config": {"schedule": "0 */6 * * *"}},
        {"id": "node_2", "type": "data", "subtype": "get_data", "x": 300, "y": 100, "config": {"entity": "abandoned_carts"}},
        {"id": "node_3", "type": "data", "subtype": "filter_data", "x": 500, "y": 100, "config": {"age": "24h"}},
        {"id": "node_4", "type": "action", "subtype": "send_email", "x": 700, "y": 100, "config": {"template": "abandoned_cart"}}
    ]'::jsonb,
    '[
        {"from": "node_1", "to": "node_2"},
        {"from": "node_2", "to": "node_3"},
        {"from": "node_3", "to": "node_4"}
    ]'::jsonb
);

-- Insert sample workflow templates
INSERT INTO workflow_templates (
    name, description, category, nodes, connections, tags
) VALUES
(
    'Basic Order Processing',
    'Simple order processing workflow template',
    'orders',
    '[
        {"type": "trigger", "subtype": "order_placed", "x": 100, "y": 100},
        {"type": "action", "subtype": "send_email", "x": 300, "y": 100},
        {"type": "action", "subtype": "update_order_status", "x": 500, "y": 100}
    ]'::jsonb,
    '[]'::jsonb,
    ARRAY['order', 'basic', 'email']
),
(
    'Inventory Reorder',
    'Automatic inventory reordering workflow template',
    'inventory',
    '[
        {"type": "trigger", "subtype": "inventory_low", "x": 100, "y": 100},
        {"type": "data", "subtype": "get_data", "x": 300, "y": 100},
        {"type": "action", "subtype": "call_api", "x": 500, "y": 100}
    ]'::jsonb,
    '[]'::jsonb,
    ARRAY['inventory', 'reorder', 'automation']
);

-- Comments for documentation
COMMENT ON TABLE workflows IS 'Automated workflow configurations';
COMMENT ON TABLE workflow_versions IS 'Version history of workflows';
COMMENT ON TABLE workflow_executions IS 'Execution history of workflows';
COMMENT ON TABLE workflow_node_executions IS 'Individual node execution logs';
COMMENT ON TABLE workflow_triggers IS 'Workflow trigger configurations';
COMMENT ON TABLE workflow_templates IS 'Predefined workflow templates';
COMMENT ON TABLE workflow_analytics IS 'Aggregated workflow performance metrics';
COMMENT ON TABLE workflow_alerts IS 'Workflow monitoring alerts';
COMMENT ON TABLE workflow_dependencies IS 'Workflow dependency relationships';

