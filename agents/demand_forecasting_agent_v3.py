"""
ML-Based Demand Forecasting Agent v3
Machine learning-powered demand forecasting with ARIMA and Prophet models
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, date
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

app = FastAPI(title="Demand Forecasting Agent", version="3.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "multi_agent_ecommerce"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres")
}

def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# ============================================================================
# Pydantic Models
# ============================================================================

class ForecastRequest(BaseModel):
    product_id: int
    horizon_days: int = 30
    model_type: str = "arima"  # arima, prophet, ensemble

class BulkForecastRequest(BaseModel):
    product_ids: List[int]
    horizon_days: int = 30
    model_type: str = "arima"

class ModelTrainRequest(BaseModel):
    product_id: int
    model_type: str
    lookback_days: int = 365

# ============================================================================
# Helper Functions - Data Processing
# ============================================================================

def load_historical_demand(product_id: int, lookback_days: int = 365) -> pd.DataFrame:
    """Load historical demand data for a product"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)
        
        cursor.execute("""
            SELECT demand_date, quantity_sold
            FROM historical_demand
            WHERE product_id = %s
            AND demand_date BETWEEN %s AND %s
            ORDER BY demand_date
        """, (product_id, start_date, end_date))
        
        data = cursor.fetchall()
        
        if not data:
            # Generate synthetic data for demo purposes
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            # Create realistic demand pattern with trend and seasonality
            base_demand = 100
            trend = np.linspace(0, 20, len(dates))
            seasonality = 20 * np.sin(2 * np.pi * np.arange(len(dates)) / 7)  # Weekly pattern
            noise = np.random.normal(0, 10, len(dates))
            quantities = np.maximum(0, base_demand + trend + seasonality + noise)
            
            df = pd.DataFrame({
                'demand_date': dates,
                'quantity_sold': quantities.astype(int)
            })
        else:
            df = pd.DataFrame(data)
            df['demand_date'] = pd.to_datetime(df['demand_date'])
        
        return df
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading historical data: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def save_forecast(product_id: int, forecast_df: pd.DataFrame, model_type: str, model_version: str):
    """Save forecast to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for _, row in forecast_df.iterrows():
            cursor.execute("""
                INSERT INTO demand_forecasts
                (product_id, forecast_date, forecast_value, lower_bound, upper_bound, 
                 model_version, horizon_days)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (product_id, forecast_date, model_version)
                DO UPDATE SET
                    forecast_value = EXCLUDED.forecast_value,
                    lower_bound = EXCLUDED.lower_bound,
                    upper_bound = EXCLUDED.upper_bound,
                    generated_at = NOW()
            """, (
                product_id,
                row['forecast_date'],
                float(row['forecast_value']),
                float(row.get('lower_bound', row['forecast_value'] * 0.8)),
                float(row.get('upper_bound', row['forecast_value'] * 1.2)),
                model_version,
                len(forecast_df)
            ))
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving forecast: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# ML Models
# ============================================================================

def train_arima_model(historical_data: pd.DataFrame, order=(5,1,0)):
    """Train ARIMA model"""
    try:
        # Prepare data
        ts_data = historical_data.set_index('demand_date')['quantity_sold']
        
        # Train model
        model = ARIMA(ts_data, order=order)
        fitted_model = model.fit()
        
        return fitted_model
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ARIMA training failed: {str(e)}")

def forecast_arima(model, historical_data: pd.DataFrame, horizon_days: int = 30) -> pd.DataFrame:
    """Generate forecast using ARIMA"""
    try:
        # Generate forecast
        forecast = model.forecast(steps=horizon_days)
        
        # Get confidence intervals
        forecast_obj = model.get_forecast(steps=horizon_days)
        conf_int = forecast_obj.conf_int()
        
        # Create forecast dataframe
        last_date = historical_data['demand_date'].max()
        forecast_dates = pd.date_range(start=last_date + timedelta(days=1), periods=horizon_days, freq='D')
        
        forecast_df = pd.DataFrame({
            'forecast_date': forecast_dates,
            'forecast_value': forecast.values,
            'lower_bound': conf_int.iloc[:, 0].values,
            'upper_bound': conf_int.iloc[:, 1].values
        })
        
        # Ensure non-negative forecasts
        forecast_df['forecast_value'] = forecast_df['forecast_value'].clip(lower=0)
        forecast_df['lower_bound'] = forecast_df['lower_bound'].clip(lower=0)
        forecast_df['upper_bound'] = forecast_df['upper_bound'].clip(lower=0)
        
        return forecast_df
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ARIMA forecasting failed: {str(e)}")

def train_prophet_model(historical_data: pd.DataFrame):
    """Train Prophet model"""
    try:
        # Prepare data for Prophet (requires 'ds' and 'y' columns)
        prophet_data = historical_data.rename(columns={
            'demand_date': 'ds',
            'quantity_sold': 'y'
        })
        
        # Train model
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode='multiplicative'
        )
        model.fit(prophet_data)
        
        return model
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prophet training failed: {str(e)}")

def forecast_prophet(model, historical_data: pd.DataFrame, horizon_days: int = 30) -> pd.DataFrame:
    """Generate forecast using Prophet"""
    try:
        # Create future dataframe
        last_date = historical_data['demand_date'].max()
        future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=horizon_days, freq='D')
        future = pd.DataFrame({'ds': future_dates})
        
        # Generate forecast
        forecast = model.predict(future)
        
        # Create forecast dataframe
        forecast_df = pd.DataFrame({
            'forecast_date': forecast['ds'],
            'forecast_value': forecast['yhat'],
            'lower_bound': forecast['yhat_lower'],
            'upper_bound': forecast['yhat_upper']
        })
        
        # Ensure non-negative forecasts
        forecast_df['forecast_value'] = forecast_df['forecast_value'].clip(lower=0)
        forecast_df['lower_bound'] = forecast_df['lower_bound'].clip(lower=0)
        forecast_df['upper_bound'] = forecast_df['upper_bound'].clip(lower=0)
        
        return forecast_df
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prophet forecasting failed: {str(e)}")

# ============================================================================
# API Endpoints - Health & Info
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "demand_forecasting_agent",
        "version": "3.0.0",
        "models": ["arima", "prophet", "ensemble"],
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# API Endpoints - Forecasting
# ============================================================================

@app.post("/api/forecasting/generate")
async def generate_forecast(request: ForecastRequest):
    """Generate demand forecast for a product"""
    
    try:
        # Load historical data
        historical_data = load_historical_demand(request.product_id, lookback_days=365)
        
        if len(historical_data) < 30:
            raise HTTPException(status_code=400, detail="Insufficient historical data (minimum 30 days required)")
        
        # Generate forecast based on model type
        if request.model_type == "arima":
            model = train_arima_model(historical_data)
            forecast_df = forecast_arima(model, historical_data, request.horizon_days)
            model_version = "arima_v1"
            
        elif request.model_type == "prophet":
            model = train_prophet_model(historical_data)
            forecast_df = forecast_prophet(model, historical_data, request.horizon_days)
            model_version = "prophet_v1"
            
        elif request.model_type == "ensemble":
            # Train both models
            arima_model = train_arima_model(historical_data)
            prophet_model = train_prophet_model(historical_data)
            
            # Generate forecasts
            arima_forecast = forecast_arima(arima_model, historical_data, request.horizon_days)
            prophet_forecast = forecast_prophet(prophet_model, historical_data, request.horizon_days)
            
            # Ensemble (weighted average)
            forecast_df = arima_forecast.copy()
            forecast_df['forecast_value'] = (
                0.4 * arima_forecast['forecast_value'] +
                0.6 * prophet_forecast['forecast_value']
            )
            forecast_df['lower_bound'] = (
                0.4 * arima_forecast['lower_bound'] +
                0.6 * prophet_forecast['lower_bound']
            )
            forecast_df['upper_bound'] = (
                0.4 * arima_forecast['upper_bound'] +
                0.6 * prophet_forecast['upper_bound']
            )
            model_version = "ensemble_v1"
        else:
            raise HTTPException(status_code=400, detail="Invalid model type")
        
        # Save forecast
        save_forecast(request.product_id, forecast_df, request.model_type, model_version)
        
        # Calculate summary statistics
        total_forecast = forecast_df['forecast_value'].sum()
        avg_daily_forecast = forecast_df['forecast_value'].mean()
        
        return {
            "success": True,
            "product_id": request.product_id,
            "model_type": request.model_type,
            "model_version": model_version,
            "horizon_days": request.horizon_days,
            "forecast": forecast_df.to_dict('records'),
            "summary": {
                "total_forecast": float(total_forecast),
                "avg_daily_forecast": float(avg_daily_forecast),
                "min_forecast": float(forecast_df['forecast_value'].min()),
                "max_forecast": float(forecast_df['forecast_value'].max())
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast generation failed: {str(e)}")

@app.get("/api/forecasting/products/{product_id}")
async def get_product_forecast(product_id: int, days: int = 30):
    """Get existing forecast for a product"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                forecast_date,
                forecast_value,
                lower_bound,
                upper_bound,
                model_version,
                generated_at
            FROM demand_forecasts
            WHERE product_id = %s
            AND forecast_date >= CURRENT_DATE
            ORDER BY forecast_date
            LIMIT %s
        """, (product_id, days))
        
        forecasts = cursor.fetchall()
        
        if not forecasts:
            return {
                "success": False,
                "message": "No forecast found. Generate a new forecast first.",
                "product_id": product_id
            }
        
        return {
            "success": True,
            "product_id": product_id,
            "forecast_count": len(forecasts),
            "forecasts": [dict(f) for f in forecasts]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/api/forecasting/bulk")
async def bulk_forecast(request: BulkForecastRequest):
    """Generate forecasts for multiple products"""
    
    results = []
    errors = []
    
    for product_id in request.product_ids:
        try:
            forecast_request = ForecastRequest(
                product_id=product_id,
                horizon_days=request.horizon_days,
                model_type=request.model_type
            )
            result = await generate_forecast(forecast_request)
            results.append({
                "product_id": product_id,
                "status": "success",
                "summary": result["summary"]
            })
        except Exception as e:
            errors.append({
                "product_id": product_id,
                "status": "failed",
                "error": str(e)
            })
    
    return {
        "success": True,
        "total_products": len(request.product_ids),
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }

# ============================================================================
# API Endpoints - Accuracy & Performance
# ============================================================================

@app.get("/api/forecasting/accuracy")
async def get_accuracy_metrics(days: int = 30):
    """Get forecast accuracy metrics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                COUNT(*) as total_forecasts,
                AVG(ABS(percentage_error)) as mape,
                AVG(absolute_error) as mae,
                SQRT(AVG(POWER(absolute_error, 2))) as rmse
            FROM forecast_accuracy
            WHERE calculated_at >= CURRENT_DATE - INTERVAL '%s days'
        """, (days,))
        
        metrics = cursor.fetchone()
        
        return {
            "success": True,
            "period_days": days,
            "metrics": dict(metrics) if metrics else {}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/forecasting/accuracy/products/{product_id}")
async def get_product_accuracy(product_id: int, days: int = 30):
    """Get accuracy metrics for specific product"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                COUNT(*) as total_forecasts,
                AVG(ABS(percentage_error)) as mape,
                AVG(absolute_error) as mae,
                SQRT(AVG(POWER(absolute_error, 2))) as rmse
            FROM forecast_accuracy
            WHERE product_id = %s
            AND calculated_at >= CURRENT_DATE - INTERVAL '%s days'
        """, (product_id, days))
        
        metrics = cursor.fetchone()
        
        return {
            "success": True,
            "product_id": product_id,
            "period_days": days,
            "metrics": dict(metrics) if metrics else {}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# API Endpoints - Dashboard
# ============================================================================

@app.get("/api/forecasting/dashboard")
async def get_forecasting_dashboard():
    """Get comprehensive forecasting dashboard"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get forecast summary
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT product_id) as products_with_forecasts,
                COUNT(*) as total_forecasts,
                AVG(forecast_value) as avg_forecast_value
            FROM demand_forecasts
            WHERE forecast_date >= CURRENT_DATE
        """)
        
        summary = cursor.fetchone()
        
        # Get model usage
        cursor.execute("""
            SELECT 
                model_version,
                COUNT(DISTINCT product_id) as product_count
            FROM demand_forecasts
            WHERE forecast_date >= CURRENT_DATE
            GROUP BY model_version
        """)
        
        models = cursor.fetchall()
        
        return {
            "success": True,
            "summary": dict(summary) if summary else {},
            "models": [dict(m) for m in models],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8037)
