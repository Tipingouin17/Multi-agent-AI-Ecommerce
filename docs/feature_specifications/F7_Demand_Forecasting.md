# Feature 7: ML-Based Demand Forecasting

## Overview
Machine learning-powered demand forecasting system that predicts future product demand using historical sales data, seasonal patterns, promotional impacts, and external factors to optimize inventory planning and reduce stockouts.

## Business Requirements

### 1. Time Series Forecasting
- Historical sales analysis
- Trend detection and extrapolation
- Multiple forecasting horizons (7, 14, 30, 90 days)
- Confidence intervals for predictions
- Forecast accuracy tracking
- Model performance monitoring

### 2. Seasonal Pattern Detection
- Automatic seasonality detection
- Weekly, monthly, quarterly patterns
- Holiday and event impact
- Day-of-week effects
- Month-of-year effects
- Custom seasonal periods

### 3. Promotional Impact Analysis
- Promotion effectiveness measurement
- Price elasticity modeling
- Discount impact on demand
- Cross-promotion effects
- Cannibalization detection
- Promotional lift calculation

### 4. Multi-Product Forecasting
- Individual product forecasts
- Product category aggregation
- SKU-level predictions
- New product forecasting
- Product lifecycle modeling
- Substitute product relationships

### 5. External Factors Integration
- Weather impact (for relevant products)
- Economic indicators
- Competitor pricing
- Market trends
- Social media sentiment
- Search trend correlation

### 6. Forecast Accuracy Tracking
- Mean Absolute Error (MAE)
- Mean Absolute Percentage Error (MAPE)
- Root Mean Square Error (RMSE)
- Forecast bias detection
- Model performance comparison
- Continuous model improvement

## Technical Requirements

### Database Schema

#### demand_forecasts
- Forecast predictions by product and date
- Forecast values and confidence intervals
- Model version and parameters
- Accuracy metrics

#### forecast_models
- Model definitions and configurations
- Training data specifications
- Hyperparameters
- Performance metrics
- Version control

#### historical_demand
- Historical sales data
- Aggregated by product and time period
- Includes promotions and events
- External factor data

#### forecast_accuracy
- Actual vs predicted comparisons
- Accuracy metrics by product
- Model performance tracking
- Error analysis

#### seasonal_patterns
- Detected seasonal patterns
- Pattern strength and significance
- Seasonal indices
- Pattern metadata

#### promotional_impacts
- Promotion history
- Measured impact on demand
- Lift calculations
- ROI analysis

### API Endpoints

#### Forecasting
1. `POST /api/forecasting/generate` - Generate forecast for product(s)
2. `GET /api/forecasting/products/{product_id}` - Get product forecast
3. `GET /api/forecasting/products/{product_id}/history` - Get forecast history
4. `POST /api/forecasting/bulk` - Bulk forecast generation
5. `GET /api/forecasting/confidence-intervals` - Get confidence intervals

#### Model Management
6. `POST /api/forecasting/models/train` - Train new model
7. `GET /api/forecasting/models` - List models
8. `GET /api/forecasting/models/{model_id}` - Get model details
9. `PUT /api/forecasting/models/{model_id}/activate` - Activate model
10. `DELETE /api/forecasting/models/{model_id}` - Delete model

#### Accuracy & Performance
11. `GET /api/forecasting/accuracy` - Get accuracy metrics
12. `GET /api/forecasting/accuracy/products/{product_id}` - Product accuracy
13. `POST /api/forecasting/accuracy/calculate` - Calculate accuracy
14. `GET /api/forecasting/performance` - Model performance dashboard

#### Seasonal Analysis
15. `GET /api/forecasting/seasonality/{product_id}` - Get seasonal patterns
16. `POST /api/forecasting/seasonality/detect` - Detect seasonality
17. `GET /api/forecasting/seasonality/calendar` - Seasonal calendar

#### Promotional Analysis
18. `POST /api/forecasting/promotions/analyze` - Analyze promotion impact
19. `GET /api/forecasting/promotions/history` - Promotion history
20. `GET /api/forecasting/promotions/effectiveness` - Effectiveness metrics

### Machine Learning Models

#### Model 1: ARIMA (AutoRegressive Integrated Moving Average)
**Use Case:** Univariate time series forecasting  
**Strengths:** Simple, interpretable, good for stable patterns  
**Parameters:** p (AR order), d (differencing), q (MA order)

```python
from statsmodels.tsa.arima.model import ARIMA

def train_arima_model(historical_data, order=(5,1,0)):
    model = ARIMA(historical_data, order=order)
    fitted_model = model.fit()
    return fitted_model

def forecast_arima(model, periods=30):
    forecast = model.forecast(steps=periods)
    conf_int = model.get_forecast(steps=periods).conf_int()
    return forecast, conf_int
```

#### Model 2: Prophet (Facebook's Time Series Model)
**Use Case:** Seasonal patterns, holidays, multiple seasonality  
**Strengths:** Handles missing data, robust to outliers  
**Parameters:** Growth, seasonality, holidays

```python
from prophet import Prophet

def train_prophet_model(historical_data):
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False
    )
    model.fit(historical_data)
    return model

def forecast_prophet(model, periods=30):
    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)
    return forecast
```

#### Model 3: LSTM (Long Short-Term Memory Neural Network)
**Use Case:** Complex patterns, long-term dependencies  
**Strengths:** Captures non-linear patterns, handles multiple features  
**Parameters:** Hidden layers, sequence length, epochs

```python
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

def build_lstm_model(input_shape):
    model = Sequential([
        LSTM(50, activation='relu', input_shape=input_shape, return_sequences=True),
        LSTM(50, activation='relu'),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    return model

def train_lstm_model(model, X_train, y_train, epochs=50):
    model.fit(X_train, y_train, epochs=epochs, batch_size=32, verbose=0)
    return model
```

#### Model 4: Ensemble Model
**Use Case:** Combining multiple models for better accuracy  
**Strengths:** Reduces individual model weaknesses  
**Approach:** Weighted average of ARIMA, Prophet, and LSTM

```python
def ensemble_forecast(arima_forecast, prophet_forecast, lstm_forecast, weights=[0.3, 0.4, 0.3]):
    ensemble = (
        weights[0] * arima_forecast +
        weights[1] * prophet_forecast +
        weights[2] * lstm_forecast
    )
    return ensemble
```

### Business Logic

#### Forecast Generation Pipeline
```python
def generate_demand_forecast(product_id, horizon_days=30):
    # 1. Load historical data
    historical_data = load_historical_demand(product_id, lookback_days=365)
    
    # 2. Preprocess data
    processed_data = preprocess_data(historical_data)
    
    # 3. Detect seasonality
    seasonality = detect_seasonality(processed_data)
    
    # 4. Load active model
    model = load_active_model(product_id)
    
    # 5. Generate forecast
    forecast = model.predict(processed_data, horizon=horizon_days)
    
    # 6. Apply promotional adjustments
    if has_upcoming_promotions(product_id):
        forecast = adjust_for_promotions(forecast, product_id)
    
    # 7. Calculate confidence intervals
    confidence_intervals = calculate_confidence_intervals(forecast, model)
    
    # 8. Save forecast
    save_forecast(product_id, forecast, confidence_intervals, model.version)
    
    # 9. Generate recommendations
    recommendations = generate_inventory_recommendations(forecast, product_id)
    
    return {
        "product_id": product_id,
        "forecast": forecast,
        "confidence_intervals": confidence_intervals,
        "seasonality": seasonality,
        "recommendations": recommendations,
        "model_version": model.version,
        "generated_at": datetime.now()
    }
```

#### Accuracy Calculation
```python
def calculate_forecast_accuracy(product_id, evaluation_period_days=30):
    # Get forecasts from evaluation period
    forecasts = get_forecasts(product_id, days=evaluation_period_days)
    
    # Get actual demand
    actuals = get_actual_demand(product_id, days=evaluation_period_days)
    
    # Calculate metrics
    mae = mean_absolute_error(actuals, forecasts)
    mape = mean_absolute_percentage_error(actuals, forecasts)
    rmse = root_mean_square_error(actuals, forecasts)
    bias = calculate_bias(actuals, forecasts)
    
    # Save accuracy metrics
    save_accuracy_metrics(product_id, mae, mape, rmse, bias)
    
    return {
        "product_id": product_id,
        "mae": mae,
        "mape": mape,
        "rmse": rmse,
        "bias": bias,
        "evaluation_period": evaluation_period_days
    }
```

#### Promotional Impact Analysis
```python
def analyze_promotional_impact(promotion_id):
    # Get promotion details
    promotion = get_promotion(promotion_id)
    
    # Get demand during promotion
    promotion_demand = get_demand_during_period(
        promotion.product_id,
        promotion.start_date,
        promotion.end_date
    )
    
    # Get baseline demand (without promotion)
    baseline_demand = get_baseline_demand(
        promotion.product_id,
        promotion.start_date,
        promotion.end_date
    )
    
    # Calculate lift
    lift = (promotion_demand - baseline_demand) / baseline_demand * 100
    
    # Calculate ROI
    additional_revenue = (promotion_demand - baseline_demand) * promotion.price
    promotion_cost = promotion.discount_amount * promotion_demand
    roi = (additional_revenue - promotion_cost) / promotion_cost * 100
    
    return {
        "promotion_id": promotion_id,
        "lift_percentage": lift,
        "roi_percentage": roi,
        "additional_units_sold": promotion_demand - baseline_demand,
        "additional_revenue": additional_revenue
    }
```

### Performance Targets

- **Forecast Generation**: < 5 seconds per product
- **Bulk Forecasting**: < 60 seconds for 100 products
- **Model Training**: < 10 minutes for standard model
- **Forecast Accuracy (MAPE)**: < 20% for established products
- **API Response Time**: < 2 seconds for forecast retrieval

### Integration Points

- **Inventory Management**: Use forecasts for replenishment
- **Purchase Orders**: Optimize order quantities
- **Pricing Engine**: Dynamic pricing based on demand
- **Marketing**: Plan promotions around demand patterns
- **Analytics**: Forecast accuracy dashboards

## Success Metrics

### Operational KPIs
- Forecast accuracy (MAPE): < 20%
- Stockout reduction: > 30%
- Overstock reduction: > 25%
- Forecast generation time: < 5 seconds
- Model training frequency: Weekly

### Business KPIs
- Inventory carrying cost reduction: > 15%
- Lost sales reduction: > 25%
- Purchase order optimization: > 20% fewer orders
- Promotional ROI improvement: > 10%

### User Experience KPIs
- Forecast confidence: > 80%
- Dashboard load time: < 3 seconds
- Forecast visualization clarity: > 4.0/5.0

## Implementation Priority

**Phase 1 (MVP):**
1. Basic ARIMA model implementation
2. Historical demand data collection
3. Simple forecast generation
4. Accuracy tracking
5. Basic dashboard

**Phase 2 (Enhanced):**
6. Prophet model integration
7. Seasonal pattern detection
8. Promotional impact analysis
9. Confidence intervals
10. Bulk forecasting

**Phase 3 (Advanced):**
11. LSTM neural network model
12. Ensemble modeling
13. External factors integration
14. Real-time forecast updates
15. Advanced analytics and insights

## Testing Requirements

### Unit Tests
- Model training functions
- Forecast generation logic
- Accuracy calculation
- Data preprocessing

### Integration Tests
- End-to-end forecast generation
- Model switching and versioning
- Accuracy tracking workflow
- Dashboard data flow

### Performance Tests
- Bulk forecast generation (1000+ products)
- Model training time
- API response times
- Concurrent forecast requests

## Dependencies

- Python libraries: statsmodels, prophet, tensorflow, scikit-learn, pandas, numpy
- Historical sales data (minimum 6 months)
- Promotional calendar
- Product catalog

## Risks & Mitigation

### Risk 1: Insufficient Historical Data
**Mitigation**: Use category-level forecasts, similar product patterns, external benchmarks

### Risk 2: Model Accuracy Issues
**Mitigation**: Ensemble modeling, continuous retraining, human-in-the-loop validation

### Risk 3: Computational Resources
**Mitigation**: Batch processing, model caching, incremental updates

### Risk 4: Data Quality Issues
**Mitigation**: Data validation, outlier detection, imputation strategies

## Future Enhancements

- Real-time demand sensing
- Causal impact analysis
- Multi-location forecasting
- Supply chain optimization
- Demand shaping recommendations
- AI-powered anomaly detection
- Automated model selection
- Transfer learning for new products
