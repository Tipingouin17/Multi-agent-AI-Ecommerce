-- Advanced Analytics & Reporting Schema
-- Comprehensive analytics and reporting system

-- Reports (report definitions)
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    report_type VARCHAR(50) NOT NULL, -- sales, inventory, fulfillment, customer, financial, operational
    data_sources JSONB, -- Array of table names and joins
    fields JSONB, -- Array of field selections
    filters JSONB, -- Filter conditions
    grouping JSONB, -- Group by fields
    sorting JSONB, -- Sort configuration
    aggregations JSONB, -- Aggregation functions
    visualization_type VARCHAR(50), -- line, bar, pie, table, etc.
    visualization_config JSONB, -- Chart configuration
    is_template BOOLEAN DEFAULT false,
    is_public BOOLEAN DEFAULT false,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Report Schedules (automated report generation)
CREATE TABLE IF NOT EXISTS report_schedules (
    id SERIAL PRIMARY KEY,
    report_id INTEGER REFERENCES reports(id) ON DELETE CASCADE,
    schedule_name VARCHAR(255) NOT NULL,
    frequency VARCHAR(50) NOT NULL, -- daily, weekly, monthly, custom
    cron_expression VARCHAR(100), -- For custom schedules
    delivery_method VARCHAR(50) NOT NULL, -- email, dashboard, api
    recipients JSONB, -- Array of email addresses or user IDs
    export_format VARCHAR(20) DEFAULT 'pdf', -- csv, excel, pdf, json
    is_active BOOLEAN DEFAULT true,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    last_status VARCHAR(50), -- success, failed, running
    last_error TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Report Executions (execution history)
CREATE TABLE IF NOT EXISTS report_executions (
    id SERIAL PRIMARY KEY,
    report_id INTEGER REFERENCES reports(id) ON DELETE CASCADE,
    schedule_id INTEGER REFERENCES report_schedules(id) ON DELETE SET NULL,
    executed_by VARCHAR(100),
    execution_time TIMESTAMP DEFAULT NOW(),
    duration_seconds DECIMAL(10,2),
    row_count INTEGER,
    data_size_bytes BIGINT,
    status VARCHAR(50) NOT NULL, -- success, failed, cancelled, running
    error_message TEXT,
    result_file_path TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Report Exports (export files)
CREATE TABLE IF NOT EXISTS report_exports (
    id SERIAL PRIMARY KEY,
    report_id INTEGER REFERENCES reports(id) ON DELETE CASCADE,
    execution_id INTEGER REFERENCES report_executions(id) ON DELETE CASCADE,
    export_format VARCHAR(20) NOT NULL,
    file_path TEXT NOT NULL,
    file_size_bytes BIGINT,
    download_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Dashboards (dashboard definitions)
CREATE TABLE IF NOT EXISTS dashboards (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    layout_config JSONB, -- Grid layout configuration
    refresh_interval INTEGER DEFAULT 60, -- Seconds
    is_public BOOLEAN DEFAULT false,
    is_default BOOLEAN DEFAULT false,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Dashboard Widgets (widgets in dashboards)
CREATE TABLE IF NOT EXISTS dashboard_widgets (
    id SERIAL PRIMARY KEY,
    dashboard_id INTEGER REFERENCES dashboards(id) ON DELETE CASCADE,
    widget_type VARCHAR(50) NOT NULL, -- chart, metric, table, text
    widget_title VARCHAR(255),
    report_id INTEGER REFERENCES reports(id) ON DELETE SET NULL,
    data_source JSONB, -- Custom data source config
    visualization_config JSONB,
    position_x INTEGER NOT NULL,
    position_y INTEGER NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    refresh_interval INTEGER, -- Override dashboard refresh
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Analytics Cache (cached results for performance)
CREATE TABLE IF NOT EXISTS analytics_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    cache_data JSONB NOT NULL,
    ttl_seconds INTEGER DEFAULT 300,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

-- Report Templates (pre-built report templates)
CREATE TABLE IF NOT EXISTS report_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(255) NOT NULL,
    template_category VARCHAR(100), -- sales, inventory, etc.
    description TEXT,
    report_config JSONB NOT NULL, -- Complete report configuration
    preview_image TEXT,
    is_active BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Analytics Metrics (pre-calculated metrics)
CREATE TABLE IF NOT EXISTS analytics_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_category VARCHAR(50), -- sales, inventory, fulfillment, etc.
    metric_value DECIMAL(15,2),
    metric_unit VARCHAR(50), -- dollars, units, percentage, etc.
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    dimensions JSONB, -- Additional dimensions (product_id, warehouse_id, etc.)
    calculated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(metric_name, period_start, period_end, dimensions)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(report_type);
CREATE INDEX IF NOT EXISTS idx_reports_created_by ON reports(created_by);
CREATE INDEX IF NOT EXISTS idx_reports_is_template ON reports(is_template);

CREATE INDEX IF NOT EXISTS idx_report_schedules_report ON report_schedules(report_id);
CREATE INDEX IF NOT EXISTS idx_report_schedules_next_run ON report_schedules(next_run_at);
CREATE INDEX IF NOT EXISTS idx_report_schedules_active ON report_schedules(is_active);

CREATE INDEX IF NOT EXISTS idx_report_executions_report ON report_executions(report_id);
CREATE INDEX IF NOT EXISTS idx_report_executions_schedule ON report_executions(schedule_id);
CREATE INDEX IF NOT EXISTS idx_report_executions_time ON report_executions(execution_time);
CREATE INDEX IF NOT EXISTS idx_report_executions_status ON report_executions(status);

CREATE INDEX IF NOT EXISTS idx_report_exports_report ON report_exports(report_id);
CREATE INDEX IF NOT EXISTS idx_report_exports_execution ON report_exports(execution_id);
CREATE INDEX IF NOT EXISTS idx_report_exports_expires ON report_exports(expires_at);

CREATE INDEX IF NOT EXISTS idx_dashboards_created_by ON dashboards(created_by);
CREATE INDEX IF NOT EXISTS idx_dashboards_is_default ON dashboards(is_default);

CREATE INDEX IF NOT EXISTS idx_dashboard_widgets_dashboard ON dashboard_widgets(dashboard_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_widgets_report ON dashboard_widgets(report_id);

CREATE INDEX IF NOT EXISTS idx_analytics_cache_key ON analytics_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_analytics_cache_expires ON analytics_cache(expires_at);

CREATE INDEX IF NOT EXISTS idx_report_templates_category ON report_templates(template_category);
CREATE INDEX IF NOT EXISTS idx_report_templates_active ON report_templates(is_active);

CREATE INDEX IF NOT EXISTS idx_analytics_metrics_name ON analytics_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_analytics_metrics_category ON analytics_metrics(metric_category);
CREATE INDEX IF NOT EXISTS idx_analytics_metrics_period ON analytics_metrics(period_start, period_end);
