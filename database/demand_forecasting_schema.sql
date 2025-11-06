-- ML-Based Demand Forecasting Schema
-- Machine learning-powered demand forecasting system

-- Demand Forecasts (forecast predictions)
CREATE TABLE IF NOT EXISTS demand_forecasts (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    forecast_date DATE NOT NULL,
    forecast_value DECIMAL(15,2) NOT NULL,
    lower_bound DECIMAL(15,2), -- Lower confidence interval
    upper_bound DECIMAL(15,2), -- Upper confidence interval
    confidence_level DECIMAL(5,2) DEFAULT 95.0, -- Confidence level percentage
    model_id INTEGER,
    model_version VARCHAR(50),
    horizon_days INTEGER, -- Forecast horizon
    generated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(product_id, forecast_date, model_version)
);

-- Forecast Models (model definitions)
CREATE TABLE IF NOT EXISTS forecast_models (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL, -- arima, prophet, lstm, ensemble
    model_config JSONB, -- Model hyperparameters
    training_data_config JSONB, -- Training data specifications
    performance_metrics JSONB, -- MAE, MAPE, RMSE, etc.
    is_active BOOLEAN DEFAULT false,
    trained_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Historical Demand (historical sales data)
CREATE TABLE IF NOT EXISTS historical_demand (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    demand_date DATE NOT NULL,
    quantity_sold INTEGER NOT NULL,
    revenue DECIMAL(15,2),
    promotion_active BOOLEAN DEFAULT false,
    promotion_id INTEGER,
    day_of_week INTEGER, -- 0-6
    week_of_year INTEGER, -- 1-52
    month INTEGER, -- 1-12
    quarter INTEGER, -- 1-4
    is_holiday BOOLEAN DEFAULT false,
    external_factors JSONB, -- Weather, events, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(product_id, demand_date)
);

-- Forecast Accuracy (actual vs predicted)
CREATE TABLE IF NOT EXISTS forecast_accuracy (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    forecast_date DATE NOT NULL,
    forecast_value DECIMAL(15,2) NOT NULL,
    actual_value DECIMAL(15,2) NOT NULL,
    absolute_error DECIMAL(15,2),
    percentage_error DECIMAL(10,2),
    model_id INTEGER,
    model_version VARCHAR(50),
    calculated_at TIMESTAMP DEFAULT NOW()
);

-- Seasonal Patterns (detected seasonal patterns)
CREATE TABLE IF NOT EXISTS seasonal_patterns (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    pattern_type VARCHAR(50) NOT NULL, -- weekly, monthly, quarterly, yearly
    pattern_strength DECIMAL(5,2), -- 0-100
    pattern_significance DECIMAL(5,4), -- p-value
    seasonal_indices JSONB, -- Seasonal index values
    detected_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- Promotional Impacts (promotion effectiveness)
CREATE TABLE IF NOT EXISTS promotional_impacts (
    id SERIAL PRIMARY KEY,
    promotion_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    promotion_start_date DATE NOT NULL,
    promotion_end_date DATE NOT NULL,
    baseline_demand DECIMAL(15,2), -- Expected demand without promotion
    actual_demand DECIMAL(15,2), -- Actual demand during promotion
    lift_percentage DECIMAL(10,2), -- Demand lift
    lift_units INTEGER, -- Additional units sold
    promotion_cost DECIMAL(15,2),
    additional_revenue DECIMAL(15,2),
    roi_percentage DECIMAL(10,2),
    analyzed_at TIMESTAMP DEFAULT NOW()
);

-- Forecast Recommendations (inventory recommendations)
CREATE TABLE IF NOT EXISTS forecast_recommendations (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    recommendation_date DATE NOT NULL,
    recommended_order_quantity INTEGER,
    recommended_safety_stock INTEGER,
    recommended_reorder_point INTEGER,
    reasoning TEXT,
    forecast_id INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Model Training History (training logs)
CREATE TABLE IF NOT EXISTS model_training_history (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES forecast_models(id) ON DELETE CASCADE,
    training_start_time TIMESTAMP NOT NULL,
    training_end_time TIMESTAMP,
    training_duration_seconds INTEGER,
    training_data_size INTEGER, -- Number of data points
    training_data_start_date DATE,
    training_data_end_date DATE,
    validation_mae DECIMAL(15,2),
    validation_mape DECIMAL(10,2),
    validation_rmse DECIMAL(15,2),
    status VARCHAR(50), -- training, completed, failed
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Forecast Adjustments (manual adjustments)
CREATE TABLE IF NOT EXISTS forecast_adjustments (
    id SERIAL PRIMARY KEY,
    forecast_id INTEGER REFERENCES demand_forecasts(id) ON DELETE CASCADE,
    original_value DECIMAL(15,2),
    adjusted_value DECIMAL(15,2),
    adjustment_reason TEXT,
    adjusted_by VARCHAR(100),
    adjusted_at TIMESTAMP DEFAULT NOW()
);

-- Demand Drivers (external factors)
CREATE TABLE IF NOT EXISTS demand_drivers (
    id SERIAL PRIMARY KEY,
    driver_name VARCHAR(100) NOT NULL,
    driver_type VARCHAR(50), -- weather, economic, competitor, event
    driver_date DATE NOT NULL,
    driver_value DECIMAL(15,2),
    driver_metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_demand_forecasts_product ON demand_forecasts(product_id);
CREATE INDEX IF NOT EXISTS idx_demand_forecasts_date ON demand_forecasts(forecast_date);
CREATE INDEX IF NOT EXISTS idx_demand_forecasts_model ON demand_forecasts(model_id);

CREATE INDEX IF NOT EXISTS idx_forecast_models_type ON forecast_models(model_type);
CREATE INDEX IF NOT EXISTS idx_forecast_models_active ON forecast_models(is_active);

CREATE INDEX IF NOT EXISTS idx_historical_demand_product ON historical_demand(product_id);
CREATE INDEX IF NOT EXISTS idx_historical_demand_date ON historical_demand(demand_date);
CREATE INDEX IF NOT EXISTS idx_historical_demand_promotion ON historical_demand(promotion_active);

CREATE INDEX IF NOT EXISTS idx_forecast_accuracy_product ON forecast_accuracy(product_id);
CREATE INDEX IF NOT EXISTS idx_forecast_accuracy_date ON forecast_accuracy(forecast_date);
CREATE INDEX IF NOT EXISTS idx_forecast_accuracy_model ON forecast_accuracy(model_id);

CREATE INDEX IF NOT EXISTS idx_seasonal_patterns_product ON seasonal_patterns(product_id);
CREATE INDEX IF NOT EXISTS idx_seasonal_patterns_type ON seasonal_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_seasonal_patterns_active ON seasonal_patterns(is_active);

CREATE INDEX IF NOT EXISTS idx_promotional_impacts_promotion ON promotional_impacts(promotion_id);
CREATE INDEX IF NOT EXISTS idx_promotional_impacts_product ON promotional_impacts(product_id);

CREATE INDEX IF NOT EXISTS idx_forecast_recommendations_product ON forecast_recommendations(product_id);
CREATE INDEX IF NOT EXISTS idx_forecast_recommendations_date ON forecast_recommendations(recommendation_date);

CREATE INDEX IF NOT EXISTS idx_model_training_history_model ON model_training_history(model_id);
CREATE INDEX IF NOT EXISTS idx_model_training_history_status ON model_training_history(status);

CREATE INDEX IF NOT EXISTS idx_forecast_adjustments_forecast ON forecast_adjustments(forecast_id);

CREATE INDEX IF NOT EXISTS idx_demand_drivers_type ON demand_drivers(driver_type);
CREATE INDEX IF NOT EXISTS idx_demand_drivers_date ON demand_drivers(driver_date);
