-- AI Model Configuration Migration
-- Supports MLOps and model lifecycle management

-- AI Models Table
CREATE TABLE IF NOT EXISTS ai_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL, -- recommendation, pricing, demand_forecasting, fraud_detection, etc.
    algorithm VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'draft', -- draft, training, testing, deployed, failed, deprecated
    enabled BOOLEAN DEFAULT true,
    description TEXT,
    parameters JSONB, -- Model-specific parameters
    training_config JSONB, -- Training configuration (dataset_size, epochs, batch_size, etc.)
    inference_config JSONB, -- Inference configuration (batch_size, timeout, cache settings)
    auto_retrain JSONB, -- Auto-retraining configuration
    fallback JSONB, -- Fallback strategy configuration
    resources JSONB, -- Resource allocation (CPU, memory, GPU)
    accuracy DECIMAL(5, 4), -- Model accuracy (0-1)
    precision_score DECIMAL(5, 4),
    recall_score DECIMAL(5, 4),
    f1_score DECIMAL(5, 4),
    prediction_count BIGINT DEFAULT 0,
    last_trained_at TIMESTAMP,
    last_deployed_at TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    UNIQUE(name, version)
);

-- Model Versions (for version control and rollback)
CREATE TABLE IF NOT EXISTS ai_model_versions (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES ai_models(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    parameters JSONB,
    training_config JSONB,
    accuracy DECIMAL(5, 4),
    precision_score DECIMAL(5, 4),
    recall_score DECIMAL(5, 4),
    f1_score DECIMAL(5, 4),
    training_duration_seconds INTEGER,
    dataset_size INTEGER,
    model_size_mb DECIMAL(10, 2),
    deployed_at TIMESTAMP,
    deprecated_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    UNIQUE(model_id, version)
);

-- Model Training Jobs
CREATE TABLE IF NOT EXISTS ai_model_training_jobs (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES ai_models(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL, -- initial_training, retraining, fine_tuning
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed, cancelled
    dataset_id INTEGER,
    dataset_size INTEGER,
    training_config JSONB,
    progress INTEGER DEFAULT 0, -- 0-100
    current_epoch INTEGER,
    total_epochs INTEGER,
    current_loss DECIMAL(10, 6),
    validation_loss DECIMAL(10, 6),
    metrics JSONB, -- Training metrics per epoch
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

-- Model Predictions Log (for monitoring and analysis)
CREATE TABLE IF NOT EXISTS ai_model_predictions (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES ai_models(id),
    input_data JSONB NOT NULL,
    prediction JSONB NOT NULL,
    confidence_score DECIMAL(5, 4),
    inference_time_ms INTEGER,
    feedback VARCHAR(50), -- correct, incorrect, uncertain
    actual_outcome JSONB, -- Actual result for comparison
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model Performance Metrics (aggregated daily)
CREATE TABLE IF NOT EXISTS ai_model_performance (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES ai_models(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    prediction_count INTEGER DEFAULT 0,
    avg_inference_time_ms INTEGER,
    avg_confidence_score DECIMAL(5, 4),
    accuracy DECIMAL(5, 4),
    precision_score DECIMAL(5, 4),
    recall_score DECIMAL(5, 4),
    f1_score DECIMAL(5, 4),
    error_count INTEGER DEFAULT 0,
    timeout_count INTEGER DEFAULT 0,
    cache_hit_rate DECIMAL(5, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_id, date)
);

-- Model A/B Tests
CREATE TABLE IF NOT EXISTS ai_model_ab_tests (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    model_a_id INTEGER REFERENCES ai_models(id),
    model_b_id INTEGER REFERENCES ai_models(id),
    status VARCHAR(50) DEFAULT 'draft', -- draft, running, paused, completed
    traffic_split INTEGER DEFAULT 50, -- Percentage for model A
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    winner_model_id INTEGER REFERENCES ai_models(id),
    metrics JSONB, -- Comparison metrics
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id)
);

-- Model Deployment History
CREATE TABLE IF NOT EXISTS ai_model_deployments (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES ai_models(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    environment VARCHAR(50) NOT NULL, -- development, staging, production
    deployment_type VARCHAR(50) NOT NULL, -- initial, update, rollback
    status VARCHAR(50) DEFAULT 'pending', -- pending, deploying, deployed, failed, rolled_back
    replicas INTEGER DEFAULT 1,
    resource_allocation JSONB,
    health_check_url VARCHAR(500),
    error_message TEXT,
    deployed_at TIMESTAMP,
    rolled_back_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deployed_by INTEGER REFERENCES users(id)
);

-- Model Monitoring Alerts
CREATE TABLE IF NOT EXISTS ai_model_alerts (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES ai_models(id) ON DELETE CASCADE,
    alert_type VARCHAR(100) NOT NULL, -- accuracy_drop, high_latency, high_error_rate, data_drift
    severity VARCHAR(50) NOT NULL, -- info, warning, critical
    message TEXT NOT NULL,
    metrics JSONB,
    acknowledged BOOLEAN DEFAULT false,
    acknowledged_by INTEGER REFERENCES users(id),
    acknowledged_at TIMESTAMP,
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model Feature Importance (for interpretability)
CREATE TABLE IF NOT EXISTS ai_model_feature_importance (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES ai_models(id) ON DELETE CASCADE,
    version VARCHAR(50),
    feature_name VARCHAR(255) NOT NULL,
    importance_score DECIMAL(10, 6) NOT NULL,
    rank INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model Datasets
CREATE TABLE IF NOT EXISTS ai_model_datasets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    dataset_type VARCHAR(50) NOT NULL, -- training, validation, test
    source VARCHAR(255),
    size_records INTEGER,
    size_mb DECIMAL(10, 2),
    features TEXT[], -- List of feature names
    target_variable VARCHAR(255),
    date_range_start DATE,
    date_range_end DATE,
    quality_score DECIMAL(5, 4),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_ai_models_type ON ai_models(type);
CREATE INDEX idx_ai_models_status ON ai_models(status);
CREATE INDEX idx_ai_models_enabled ON ai_models(enabled);
CREATE INDEX idx_ai_model_versions_model ON ai_model_versions(model_id);
CREATE INDEX idx_ai_model_training_jobs_model ON ai_model_training_jobs(model_id);
CREATE INDEX idx_ai_model_training_jobs_status ON ai_model_training_jobs(status);
CREATE INDEX idx_ai_model_predictions_model ON ai_model_predictions(model_id);
CREATE INDEX idx_ai_model_predictions_created ON ai_model_predictions(created_at);
CREATE INDEX idx_ai_model_performance_model_date ON ai_model_performance(model_id, date);
CREATE INDEX idx_ai_model_ab_tests_status ON ai_model_ab_tests(status);
CREATE INDEX idx_ai_model_deployments_model ON ai_model_deployments(model_id);
CREATE INDEX idx_ai_model_alerts_model ON ai_model_alerts(model_id);
CREATE INDEX idx_ai_model_alerts_acknowledged ON ai_model_alerts(acknowledged);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_ai_model_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ai_models_updated_at
    BEFORE UPDATE ON ai_models
    FOR EACH ROW
    EXECUTE FUNCTION update_ai_model_timestamp();

CREATE TRIGGER ai_model_ab_tests_updated_at
    BEFORE UPDATE ON ai_model_ab_tests
    FOR EACH ROW
    EXECUTE FUNCTION update_ai_model_timestamp();

CREATE TRIGGER ai_model_datasets_updated_at
    BEFORE UPDATE ON ai_model_datasets
    FOR EACH ROW
    EXECUTE FUNCTION update_ai_model_timestamp();

-- Insert sample AI models
INSERT INTO ai_models (
    name, type, algorithm, version, status, enabled, description,
    parameters, training_config, inference_config, accuracy, prediction_count
) VALUES
(
    'Product Recommendation Engine v1',
    'recommendation',
    'Collaborative Filtering',
    '1.0.0',
    'deployed',
    true,
    'Recommends products based on user behavior and purchase history',
    '{"min_support": 0.01, "min_confidence": 0.5}'::jsonb,
    '{"dataset_size": 100000, "train_test_split": 0.8, "batch_size": 64, "epochs": 20}'::jsonb,
    '{"batch_size": 10, "timeout_ms": 500, "cache_enabled": true, "cache_ttl": 3600}'::jsonb,
    0.8750,
    1250000
),
(
    'Dynamic Pricing Model',
    'pricing',
    'XGBoost',
    '2.1.0',
    'deployed',
    true,
    'Optimizes product pricing based on demand, competition, and inventory',
    '{"max_depth": 6, "learning_rate": 0.1, "n_estimators": 100}'::jsonb,
    '{"dataset_size": 50000, "train_test_split": 0.8, "batch_size": 32, "epochs": 50}'::jsonb,
    '{"batch_size": 1, "timeout_ms": 200, "cache_enabled": true, "cache_ttl": 1800}'::jsonb,
    0.9200,
    850000
),
(
    'Demand Forecasting LSTM',
    'demand_forecasting',
    'LSTM',
    '1.5.0',
    'deployed',
    true,
    'Predicts future product demand using time series analysis',
    '{"hidden_units": 128, "dropout": 0.2, "sequence_length": 30}'::jsonb,
    '{"dataset_size": 75000, "train_test_split": 0.8, "batch_size": 32, "epochs": 100}'::jsonb,
    '{"batch_size": 1, "timeout_ms": 1000, "cache_enabled": true, "cache_ttl": 7200}'::jsonb,
    0.8900,
    320000
),
(
    'Fraud Detection System',
    'fraud_detection',
    'Isolation Forest',
    '1.0.0',
    'deployed',
    true,
    'Detects fraudulent transactions using anomaly detection',
    '{"contamination": 0.01, "n_estimators": 100}'::jsonb,
    '{"dataset_size": 200000, "train_test_split": 0.8, "batch_size": 128}'::jsonb,
    '{"batch_size": 1, "timeout_ms": 100, "cache_enabled": false}'::jsonb,
    0.9650,
    2100000
),
(
    'Customer Sentiment Analyzer',
    'sentiment_analysis',
    'BERT',
    '1.0.0',
    'testing',
    false,
    'Analyzes customer reviews and feedback sentiment',
    '{"model_name": "bert-base-uncased", "max_length": 512}'::jsonb,
    '{"dataset_size": 30000, "train_test_split": 0.8, "batch_size": 16, "epochs": 5}'::jsonb,
    '{"batch_size": 1, "timeout_ms": 2000, "cache_enabled": true, "cache_ttl": 3600}'::jsonb,
    0.9100,
    45000
);

-- Insert sample datasets
INSERT INTO ai_model_datasets (
    name, description, dataset_type, source, size_records, size_mb, features, target_variable
) VALUES
(
    'Customer Purchase History',
    'Historical customer purchase data for recommendation training',
    'training',
    'production_database',
    100000,
    250.5,
    ARRAY['customer_id', 'product_id', 'category', 'price', 'quantity', 'timestamp'],
    'purchased'
),
(
    'Product Pricing Data',
    'Historical pricing data with demand and competition metrics',
    'training',
    'pricing_analytics',
    50000,
    125.3,
    ARRAY['product_id', 'base_price', 'competitor_price', 'demand_score', 'inventory_level'],
    'optimal_price'
),
(
    'Transaction Fraud Labels',
    'Labeled transaction data for fraud detection',
    'training',
    'fraud_database',
    200000,
    450.8,
    ARRAY['transaction_id', 'amount', 'location', 'device_type', 'time_of_day', 'user_behavior'],
    'is_fraud'
);

-- Comments for documentation
COMMENT ON TABLE ai_models IS 'Registry of AI/ML models used across the platform';
COMMENT ON TABLE ai_model_versions IS 'Version history of AI models for rollback capability';
COMMENT ON TABLE ai_model_training_jobs IS 'Tracks model training and retraining jobs';
COMMENT ON TABLE ai_model_predictions IS 'Logs individual model predictions for monitoring';
COMMENT ON TABLE ai_model_performance IS 'Aggregated daily performance metrics for models';
COMMENT ON TABLE ai_model_ab_tests IS 'A/B testing configurations for model comparison';
COMMENT ON TABLE ai_model_deployments IS 'History of model deployments across environments';
COMMENT ON TABLE ai_model_alerts IS 'Monitoring alerts for model performance issues';
COMMENT ON TABLE ai_model_feature_importance IS 'Feature importance scores for model interpretability';
COMMENT ON TABLE ai_model_datasets IS 'Datasets used for model training and evaluation';

