-- Monitoring Agent Tables
-- Created: 2025-10-23
-- Purpose: System monitoring, agent health tracking, alerts, and performance metrics

-- Agent Health Tracking
CREATE TABLE IF NOT EXISTS agent_health (
    id VARCHAR(255) PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('healthy', 'warning', 'critical', 'offline')),
    cpu_usage FLOAT DEFAULT 0.0,
    memory_usage FLOAT DEFAULT 0.0,
    response_time INTEGER DEFAULT 0,
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_count INTEGER DEFAULT 0,
    uptime_seconds INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_health_agent_id ON agent_health(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_health_status ON agent_health(status);

-- System Alerts
CREATE TABLE IF NOT EXISTS system_alerts (
    id VARCHAR(255) PRIMARY KEY,
    severity VARCHAR(50) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    affected_agents TEXT,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'acknowledged')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_system_alerts_status ON system_alerts(status);
CREATE INDEX IF NOT EXISTS idx_system_alerts_severity ON system_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_system_alerts_created_at ON system_alerts(created_at);

-- Performance Metrics
CREATE TABLE IF NOT EXISTS performance_metrics (
    id VARCHAR(255) PRIMARY KEY,
    metric_type VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    agent_id VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_performance_metrics_type ON performance_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_agent_id ON performance_metrics(agent_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);

-- Comments
COMMENT ON TABLE agent_health IS 'Tracks health status and metrics for all agents in the system';
COMMENT ON TABLE system_alerts IS 'System-wide alerts and notifications';
COMMENT ON TABLE performance_metrics IS 'Performance metrics for system and agent monitoring';
