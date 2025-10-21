-- =====================================================
-- Saga Orchestration Tables
-- Migration: 020_saga_orchestration.sql
-- Description: Tables for Saga pattern implementation
-- =====================================================

-- Saga definitions table
CREATE TABLE IF NOT EXISTS saga_definitions (
    saga_id UUID PRIMARY KEY,
    saga_name VARCHAR(255) NOT NULL,
    description TEXT,
    steps JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_saga_definitions_name ON saga_definitions(saga_name);

-- Saga executions table
CREATE TABLE IF NOT EXISTS saga_executions (
    execution_id UUID PRIMARY KEY,
    saga_id UUID NOT NULL,
    saga_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    current_step INTEGER DEFAULT 0,
    steps JSONB NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    error TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (saga_id) REFERENCES saga_definitions(saga_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_saga_executions_saga ON saga_executions(saga_id);
CREATE INDEX IF NOT EXISTS idx_saga_executions_status ON saga_executions(status);
CREATE INDEX IF NOT EXISTS idx_saga_executions_started ON saga_executions(started_at DESC);

-- Saga execution log (detailed step-by-step log)
CREATE TABLE IF NOT EXISTS saga_execution_log (
    log_id SERIAL PRIMARY KEY,
    execution_id UUID NOT NULL,
    step_id VARCHAR(255) NOT NULL,
    step_name VARCHAR(255) NOT NULL,
    agent VARCHAR(100) NOT NULL,
    action VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    attempt INTEGER DEFAULT 1,
    params JSONB,
    result JSONB,
    error TEXT,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    FOREIGN KEY (execution_id) REFERENCES saga_executions(execution_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_saga_log_execution ON saga_execution_log(execution_id);
CREATE INDEX IF NOT EXISTS idx_saga_log_step ON saga_execution_log(step_id);
CREATE INDEX IF NOT EXISTS idx_saga_log_status ON saga_execution_log(status);

-- Saga compensation log
CREATE TABLE IF NOT EXISTS saga_compensation_log (
    compensation_id SERIAL PRIMARY KEY,
    execution_id UUID NOT NULL,
    step_id VARCHAR(255) NOT NULL,
    step_name VARCHAR(255) NOT NULL,
    agent VARCHAR(100) NOT NULL,
    compensation_action VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    params JSONB,
    result JSONB,
    error TEXT,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    FOREIGN KEY (execution_id) REFERENCES saga_executions(execution_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_saga_compensation_execution ON saga_compensation_log(execution_id);
CREATE INDEX IF NOT EXISTS idx_saga_compensation_status ON saga_compensation_log(status);

-- Saga metrics view
CREATE OR REPLACE VIEW saga_metrics AS
SELECT 
    saga_name,
    COUNT(*) as total_executions,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_executions,
    COUNT(CASE WHEN status = 'compensated' THEN 1 END) as compensated_executions,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_executions,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds,
    MAX(EXTRACT(EPOCH FROM (completed_at - started_at))) as max_duration_seconds,
    MIN(EXTRACT(EPOCH FROM (completed_at - started_at))) as min_duration_seconds
FROM saga_executions
WHERE completed_at IS NOT NULL
GROUP BY saga_name;

-- Comments
COMMENT ON TABLE saga_definitions IS 'Defines reusable saga workflows';
COMMENT ON TABLE saga_executions IS 'Tracks saga execution state and history';
COMMENT ON TABLE saga_execution_log IS 'Detailed log of each saga step execution';
COMMENT ON TABLE saga_compensation_log IS 'Log of compensation actions during saga rollback';
COMMENT ON VIEW saga_metrics IS 'Performance metrics for saga executions';

