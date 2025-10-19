"""
Demand Forecasting Agent - Multi-Agent E-commerce System

This agent uses machine learning to predict future product demand based on:
- Historical sales data
- Seasonal trends and patterns
- Market conditions and external factors
- Inventory levels and stock movements
- Customer behavior analytics
"""

import asyncio
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import structlog
import sys
import os

# Get the absolute path of the current file
current_file_path = os.path.abspath(__file__)

# Get the directory containing the current file
current_dir = os.path.dirname(current_file_path)

# Get the parent directory (project root)
project_root = os.path.dirname(current_dir)

# Add the project root to the Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added {project_root} to Python path")

# Now try the import
try:
    from shared.base_agent import BaseAgent, MessageType, AgentMessage
    print("Successfully imported shared.base_agent")
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current sys.path: {sys.path}")
    
    # List files in the shared directory to verify it exists
    shared_dir = os.path.join(project_root, "shared")
    if os.path.exists(shared_dir):
        print(f"Contents of {shared_dir}:")
        for item in os.listdir(shared_dir):
            print(f"  - {item}")
    else:
        print(f"Directory not found: {shared_dir}")

from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.models import APIResponse
from shared.database import DatabaseManager, get_database_manager


logger = structlog.get_logger(__name__)


class DemandForecastRequest(BaseModel):
    """Request model for demand forecasting."""
    product_id: str
    warehouse_id: Optional[str] = None
    forecast_days: int = 30
    include_confidence_interval: bool = True


class DemandForecast(BaseModel):
    """Model for demand forecast result."""
    product_id: str
    warehouse_id: Optional[str]
    forecast_period_days: int
    predicted_demand: float
    confidence_score: float
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None
    trend: str  # "increasing", "decreasing", "stable"
    seasonality_detected: bool
    factors_considered: List[str]
    generated_at: datetime


class ReorderRecommendation(BaseModel):
    """Model for reorder recommendation."""
    product_id: str
    warehouse_id: str
    current_stock: int
    predicted_demand: float
    recommended_order_quantity: int
    reorder_urgency: str  # "low", "medium", "high", "critical"
    estimated_stockout_date: Optional[datetime]
    cost_impact: float
    reasons: List[str]


class SeasonalPattern(BaseModel):
    """Model for seasonal pattern analysis."""
    product_id: str
    pattern_type: str  # "weekly", "monthly", "yearly"
    peak_periods: List[str]
    low_periods: List[str]
    seasonal_factor: float
    confidence: float


class DemandForecastingAgent(BaseAgent):
    """
    Demand Forecasting Agent provides AI-powered demand predictions including:
    - Machine learning-based demand forecasting
    - Seasonal pattern detection
    - Reorder recommendations
    - Inventory optimization suggestions
    - Market trend analysis
    """
    
    def __init__(self, **kwargs):
        super().__init__(agent_id="demand_forecasting_agent", **kwargs)
        self.app = FastAPI(title="Demand Forecasting Agent API", version="1.0.0")
        self.setup_routes()
        
        # ML models and data
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.historical_data: Dict[str, pd.DataFrame] = {}
        
        # Register message handlers
        self.register_handler(MessageType.ORDER_CREATED, self._handle_order_created)
        self.register_handler(MessageType.INVENTORY_UPDATE, self._handle_inventory_update)
    
    async def initialize(self):
        """Initialize the Demand Forecasting Agent."""
        self.logger.info("Initializing Demand Forecasting Agent")
        
        # Initialize ML models and load historical data
        await self._initialize_ml_models()
        await self._load_historical_data()
        
        # Start background tasks
        asyncio.create_task(self._retrain_models_periodically())
        asyncio.create_task(self._generate_daily_forecasts())
        asyncio.create_task(self._monitor_forecast_accuracy())
        
        self.logger.info("Demand Forecasting Agent initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up Demand Forecasting Agent")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process demand forecasting business logic."""
        action = data.get("action")
        
        if action == "forecast_demand":
            return await self._forecast_demand(data["request"])
        elif action == "get_reorder_recommendations":
            return await self._get_reorder_recommendations(data.get("warehouse_id"))
        elif action == "analyze_seasonality":
            return await self._analyze_seasonality(data["product_id"])
        elif action == "get_forecast_accuracy":
            return await self._get_forecast_accuracy()
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def setup_routes(self):
        """Setup FastAPI routes for the Demand Forecasting Agent."""
        
        @self.app.post("/forecast", response_model=APIResponse)
        async def forecast_demand(request: DemandForecastRequest):
            """Generate demand forecast for a product."""
            try:
                result = await self._forecast_demand(request.dict())
                
                return APIResponse(
                    success=True,
                    message="Demand forecast generated successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to generate demand forecast", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/reorder-recommendations", response_model=APIResponse)
        async def get_reorder_recommendations(warehouse_id: Optional[str] = None):
            """Get reorder recommendations."""
            try:
                result = await self._get_reorder_recommendations(warehouse_id)
                
                return APIResponse(
                    success=True,
                    message="Reorder recommendations retrieved successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to get reorder recommendations", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/seasonality/{product_id}", response_model=APIResponse)
        async def analyze_seasonality(product_id: str):
            """Analyze seasonal patterns for a product."""
            try:
                result = await self._analyze_seasonality(product_id)
                
                return APIResponse(
                    success=True,
                    message="Seasonality analysis completed successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to analyze seasonality", error=str(e), product_id=product_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/accuracy", response_model=APIResponse)
        async def get_forecast_accuracy():
            """Get forecast accuracy metrics."""
            try:
                result = await self._get_forecast_accuracy()
                
                return APIResponse(
                    success=True,
                    message="Forecast accuracy retrieved successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to get forecast accuracy", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/retrain", response_model=APIResponse)
        async def retrain_models():
            """Manually trigger model retraining."""
            try:
                result = await self._retrain_models()
                
                return APIResponse(
                    success=True,
                    message="Models retrained successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to retrain models", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _forecast_demand(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate demand forecast for a product."""
        try:
            product_id = request_data["product_id"]
            warehouse_id = request_data.get("warehouse_id")
            forecast_days = request_data.get("forecast_days", 30)
            include_confidence_interval = request_data.get("include_confidence_interval", True)
            
            # Get or create model for this product
            model_key = f"{product_id}_{warehouse_id or 'all'}"
            
            if model_key not in self.models:
                await self._train_product_model(product_id, warehouse_id)
            
            # Prepare features for prediction
            features = await self._prepare_forecast_features(product_id, warehouse_id, forecast_days)
            
            # Make prediction
            model = self.models.get(model_key)
            scaler = self.scalers.get(model_key)
            
            if not model or not scaler:
                # Fallback to simple moving average
                predicted_demand = await self._simple_forecast(product_id, warehouse_id, forecast_days)
                confidence_score = 0.6
                trend = "stable"
                seasonality_detected = False
            else:
                # Use ML model
                scaled_features = scaler.transform([features])
                predicted_demand = max(0, model.predict(scaled_features)[0])
                
                # Calculate confidence score based on model performance
                confidence_score = self._calculate_confidence_score(model_key)
                
                # Determine trend
                trend = self._determine_trend(product_id, warehouse_id)
                
                # Check for seasonality
                seasonality_detected = await self._detect_seasonality(product_id)
            
            # Calculate confidence interval if requested
            confidence_interval_lower = None
            confidence_interval_upper = None
            
            if include_confidence_interval:
                margin = predicted_demand * (1 - confidence_score) * 0.5
                confidence_interval_lower = max(0, predicted_demand - margin)
                confidence_interval_upper = predicted_demand + margin
            
            # Create forecast result
            forecast = DemandForecast(
                product_id=product_id,
                warehouse_id=warehouse_id,
                forecast_period_days=forecast_days,
                predicted_demand=round(predicted_demand, 2),
                confidence_score=round(confidence_score, 3),
                confidence_interval_lower=round(confidence_interval_lower, 2) if confidence_interval_lower else None,
                confidence_interval_upper=round(confidence_interval_upper, 2) if confidence_interval_upper else None,
                trend=trend,
                seasonality_detected=seasonality_detected,
                factors_considered=[
                    "Historical sales data",
                    "Seasonal patterns",
                    "Recent trends",
                    "Inventory levels"
                ],
                generated_at=datetime.utcnow()
            )
            
            # Send forecast to interested agents
            await self.send_message(
                recipient_agent="inventory_agent",
                message_type=MessageType.DEMAND_FORECAST,
                payload={
                    "product_id": product_id,
                    "warehouse_id": warehouse_id,
                    "predicted_demand": predicted_demand,
                    "forecast_days": forecast_days,
                    "confidence_score": confidence_score
                }
            )
            
            self.logger.info("Demand forecast generated", product_id=product_id, predicted_demand=predicted_demand, confidence=confidence_score)
            
            return forecast.dict()
        
        except Exception as e:
            self.logger.error("Failed to forecast demand", error=str(e), product_id=request_data.get("product_id"))
            raise
    
    async def _get_reorder_recommendations(self, warehouse_id: Optional[str] = None) -> Dict[str, Any]:
        """Get reorder recommendations for products."""
        try:
            recommendations = []
            
            # Get products that need reorder analysis
            products_to_analyze = await self._get_products_for_reorder_analysis(warehouse_id)
            
            for product_data in products_to_analyze:
                product_id = product_data["product_id"]
                warehouse_id = product_data["warehouse_id"]
                current_stock = product_data["current_stock"]
                reorder_point = product_data.get("reorder_point", 10)
                
                # Generate demand forecast
                forecast_request = {
                    "product_id": product_id,
                    "warehouse_id": warehouse_id,
                    "forecast_days": 30,
                    "include_confidence_interval": False
                }
                
                forecast_result = await self._forecast_demand(forecast_request)
                predicted_demand = forecast_result["predicted_demand"]
                
                # Calculate reorder recommendation
                recommendation = await self._calculate_reorder_recommendation(
                    product_id, warehouse_id, current_stock, predicted_demand, reorder_point
                )
                
                if recommendation:
                    recommendations.append(recommendation)
            
            # Sort by urgency
            urgency_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            recommendations.sort(key=lambda r: urgency_order.get(r["reorder_urgency"], 4))
            
            return {
                "recommendations": recommendations,
                "total_products_analyzed": len(products_to_analyze),
                "critical_recommendations": len([r for r in recommendations if r["reorder_urgency"] == "critical"]),
                "generated_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error("Failed to get reorder recommendations", error=str(e))
            raise
    
    async def _analyze_seasonality(self, product_id: str) -> Dict[str, Any]:
        """Analyze seasonal patterns for a product."""
        try:
            # Get historical sales data
            sales_data = await self._get_historical_sales_data(product_id)
            
            if len(sales_data) < 90:  # Need at least 3 months of data
                return {
                    "product_id": product_id,
                    "seasonality_detected": False,
                    "message": "Insufficient data for seasonality analysis"
                }
            
            # Convert to pandas DataFrame
            df = pd.DataFrame(sales_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            
            # Analyze different seasonal patterns
            patterns = []
            
            # Weekly seasonality
            weekly_pattern = self._analyze_weekly_seasonality(df)
            if weekly_pattern:
                patterns.append(weekly_pattern)
            
            # Monthly seasonality
            monthly_pattern = self._analyze_monthly_seasonality(df)
            if monthly_pattern:
                patterns.append(monthly_pattern)
            
            # Yearly seasonality (if enough data)
            if len(sales_data) >= 365:
                yearly_pattern = self._analyze_yearly_seasonality(df)
                if yearly_pattern:
                    patterns.append(yearly_pattern)
            
            return {
                "product_id": product_id,
                "seasonality_detected": len(patterns) > 0,
                "patterns": [pattern.dict() for pattern in patterns],
                "analysis_date": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error("Failed to analyze seasonality", error=str(e), product_id=product_id)
            raise
    
    async def _get_forecast_accuracy(self) -> Dict[str, Any]:
        """Get forecast accuracy metrics."""
        try:
            accuracy_metrics = {}
            
            for model_key, model in self.models.items():
                # Calculate accuracy metrics for each model
                if hasattr(model, 'score') and model_key in self.historical_data:
                    # Get recent predictions vs actual sales
                    recent_accuracy = await self._calculate_recent_accuracy(model_key)
                    accuracy_metrics[model_key] = recent_accuracy
            
            # Calculate overall accuracy
            if accuracy_metrics:
                overall_mae = np.mean([metrics.get("mae", 0) for metrics in accuracy_metrics.values()])
                overall_mape = np.mean([metrics.get("mape", 0) for metrics in accuracy_metrics.values()])
            else:
                overall_mae = 0
                overall_mape = 0
            
            return {
                "overall_metrics": {
                    "mean_absolute_error": round(overall_mae, 2),
                    "mean_absolute_percentage_error": round(overall_mape, 2),
                    "models_evaluated": len(accuracy_metrics)
                },
                "model_metrics": accuracy_metrics,
                "last_updated": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error("Failed to get forecast accuracy", error=str(e))
            raise
    
    async def _initialize_ml_models(self):
        """Initialize machine learning models."""
        try:
            # Initialize model storage
            self.models = {}
            self.scalers = {}
            
            # Load pre-trained models if they exist
            # In production, this would load from a model registry or file system
            
            self.logger.info("ML models initialized")
        
        except Exception as e:
            self.logger.error("Failed to initialize ML models", error=str(e))
    
    async def _load_historical_data(self):
        """Load historical sales and inventory data."""
        try:
            # In production, this would load from the database
            # For now, we'll simulate some historical data
            
            self.historical_data = {}
            
            # Generate sample historical data for demonstration
            sample_products = ["product_1", "product_2", "product_3"]
            
            for product_id in sample_products:
                # Generate 6 months of daily sales data
                dates = pd.date_range(start=datetime.now() - timedelta(days=180), end=datetime.now(), freq='D')
                
                # Simulate sales with trend and seasonality
                base_demand = 10 + np.random.normal(0, 2, len(dates))
                trend = np.linspace(0, 5, len(dates))  # Increasing trend
                seasonality = 3 * np.sin(2 * np.pi * np.arange(len(dates)) / 7)  # Weekly seasonality
                
                sales = np.maximum(0, base_demand + trend + seasonality + np.random.normal(0, 1, len(dates)))
                
                df = pd.DataFrame({
                    'date': dates,
                    'sales': sales,
                    'inventory': np.random.randint(50, 200, len(dates))
                })
                
                self.historical_data[product_id] = df
            
            self.logger.info("Historical data loaded", products=len(self.historical_data))
        
        except Exception as e:
            self.logger.error("Failed to load historical data", error=str(e))
    
    async def _train_product_model(self, product_id: str, warehouse_id: Optional[str] = None):
        """Train ML model for a specific product."""
        try:
            model_key = f"{product_id}_{warehouse_id or 'all'}"
            
            # Get historical data
            historical_data = await self._get_historical_sales_data(product_id, warehouse_id)
            
            if len(historical_data) < 30:  # Need at least 30 days of data
                self.logger.warning("Insufficient data for model training", product_id=product_id)
                return
            
            # Prepare features and target
            features, target = self._prepare_training_data(historical_data)
            
            if len(features) == 0:
                return
            
            # Scale features
            scaler = StandardScaler()
            scaled_features = scaler.fit_transform(features)
            
            # Train model
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(scaled_features, target)
            
            # Store model and scaler
            self.models[model_key] = model
            self.scalers[model_key] = scaler
            
            self.logger.info("Model trained successfully", model_key=model_key, samples=len(features))
        
        except Exception as e:
            self.logger.error("Failed to train product model", error=str(e), product_id=product_id)
    
    def _prepare_training_data(self, historical_data: List[Dict[str, Any]]) -> Tuple[List[List[float]], List[float]]:
        """Prepare training data from historical sales."""
        try:
            df = pd.DataFrame(historical_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            features = []
            target = []
            
            # Create features for each day
            for i in range(7, len(df)):  # Need at least 7 days of history
                # Features: last 7 days sales, day of week, month, trend
                last_7_days = df.iloc[i-7:i]['sales'].values
                day_of_week = df.iloc[i]['date'].dayofweek
                month = df.iloc[i]['date'].month
                day_of_year = df.iloc[i]['date'].dayofyear
                
                # Calculate trend (slope of last 7 days)
                x = np.arange(7)
                trend = np.polyfit(x, last_7_days, 1)[0]
                
                feature_vector = [
                    np.mean(last_7_days),  # Average sales last 7 days
                    np.std(last_7_days),   # Volatility
                    last_7_days[-1],       # Yesterday's sales
                    trend,                 # Trend
                    day_of_week,          # Day of week
                    month,                # Month
                    day_of_year / 365.0,  # Day of year (normalized)
                ]
                
                features.append(feature_vector)
                target.append(df.iloc[i]['sales'])
            
            return features, target
        
        except Exception as e:
            self.logger.error("Failed to prepare training data", error=str(e))
            return [], []
    
    async def _prepare_forecast_features(self, product_id: str, warehouse_id: Optional[str], forecast_days: int) -> List[float]:
        """Prepare features for demand forecasting."""
        try:
            # Get recent sales data
            recent_data = await self._get_recent_sales_data(product_id, warehouse_id, days=7)
            
            if len(recent_data) < 7:
                # Use default features if insufficient data
                return [5.0, 1.0, 5.0, 0.0, datetime.now().weekday(), datetime.now().month, datetime.now().timetuple().tm_yday / 365.0]
            
            # Calculate features similar to training
            sales_values = [d['sales'] for d in recent_data]
            
            # Calculate trend
            x = np.arange(len(sales_values))
            trend = np.polyfit(x, sales_values, 1)[0] if len(sales_values) > 1 else 0
            
            # Future date for prediction
            future_date = datetime.now() + timedelta(days=forecast_days // 2)
            
            features = [
                np.mean(sales_values),           # Average recent sales
                np.std(sales_values),            # Volatility
                sales_values[-1],                # Latest sales
                trend,                           # Trend
                future_date.weekday(),           # Day of week
                future_date.month,               # Month
                future_date.timetuple().tm_yday / 365.0,  # Day of year
            ]
            
            return features
        
        except Exception as e:
            self.logger.error("Failed to prepare forecast features", error=str(e))
            return [5.0, 1.0, 5.0, 0.0, datetime.now().weekday(), datetime.now().month, datetime.now().timetuple().tm_yday / 365.0]
    
    async def _simple_forecast(self, product_id: str, warehouse_id: Optional[str], forecast_days: int) -> float:
        """Simple moving average forecast as fallback."""
        try:
            recent_data = await self._get_recent_sales_data(product_id, warehouse_id, days=14)
            
            if not recent_data:
                return 5.0  # Default forecast
            
            # Calculate moving average
            sales_values = [d['sales'] for d in recent_data]
            return np.mean(sales_values) * forecast_days
        
        except Exception as e:
            self.logger.error("Failed to calculate simple forecast", error=str(e))
            return 5.0
    
    def _calculate_confidence_score(self, model_key: str) -> float:
        """Calculate confidence score for a model."""
        try:
            # In production, this would be based on model validation metrics
            # For now, return a simulated confidence score
            base_confidence = 0.75
            
            # Adjust based on data availability
            if model_key in self.historical_data:
                data_points = len(self.historical_data[model_key])
                data_factor = min(1.0, data_points / 100.0)  # More data = higher confidence
                return min(0.95, base_confidence + (data_factor * 0.2))
            
            return base_confidence
        
        except Exception as e:
            self.logger.error("Failed to calculate confidence score", error=str(e))
            return 0.6
    
    def _determine_trend(self, product_id: str, warehouse_id: Optional[str]) -> str:
        """Determine demand trend for a product."""
        try:
            # Get recent sales data
            if product_id in self.historical_data:
                df = self.historical_data[product_id]
                recent_data = df.tail(14)  # Last 2 weeks
                
                if len(recent_data) >= 7:
                    # Calculate trend using linear regression
                    x = np.arange(len(recent_data))
                    y = recent_data['sales'].values
                    slope = np.polyfit(x, y, 1)[0]
                    
                    if slope > 0.1:
                        return "increasing"
                    elif slope < -0.1:
                        return "decreasing"
                    else:
                        return "stable"
            
            return "stable"
        
        except Exception as e:
            self.logger.error("Failed to determine trend", error=str(e))
            return "stable"
    
    async def _detect_seasonality(self, product_id: str) -> bool:
        """Detect if product has seasonal patterns."""
        try:
            if product_id in self.historical_data:
                df = self.historical_data[product_id]
                
                if len(df) >= 28:  # Need at least 4 weeks of data
                    # Simple seasonality detection using autocorrelation
                    sales = df['sales'].values
                    
                    # Check for weekly seasonality (lag 7)
                    if len(sales) >= 14:
                        correlation_7 = np.corrcoef(sales[:-7], sales[7:])[0, 1]
                        if correlation_7 > 0.3:  # Threshold for seasonality
                            return True
            
            return False
        
        except Exception as e:
            self.logger.error("Failed to detect seasonality", error=str(e))
            return False
    
    def _analyze_weekly_seasonality(self, df: pd.DataFrame) -> Optional[SeasonalPattern]:
        """Analyze weekly seasonal patterns."""
        try:
            df['day_of_week'] = df.index.dayofweek
            weekly_avg = df.groupby('day_of_week')['sales'].mean()
            
            # Check if there's significant variation
            if weekly_avg.std() > weekly_avg.mean() * 0.2:  # 20% coefficient of variation
                peak_days = weekly_avg.nlargest(2).index.tolist()
                low_days = weekly_avg.nsmallest(2).index.tolist()
                
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                
                return SeasonalPattern(
                    product_id=df.index.name or "unknown",
                    pattern_type="weekly",
                    peak_periods=[day_names[day] for day in peak_days],
                    low_periods=[day_names[day] for day in low_days],
                    seasonal_factor=weekly_avg.std() / weekly_avg.mean(),
                    confidence=0.8
                )
            
            return None
        
        except Exception as e:
            self.logger.error("Failed to analyze weekly seasonality", error=str(e))
            return None
    
    def _analyze_monthly_seasonality(self, df: pd.DataFrame) -> Optional[SeasonalPattern]:
        """Analyze monthly seasonal patterns."""
        try:
            df['month'] = df.index.month
            monthly_avg = df.groupby('month')['sales'].mean()
            
            # Check if there's significant variation
            if monthly_avg.std() > monthly_avg.mean() * 0.15:  # 15% coefficient of variation
                peak_months = monthly_avg.nlargest(3).index.tolist()
                low_months = monthly_avg.nsmallest(3).index.tolist()
                
                month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                
                return SeasonalPattern(
                    product_id=df.index.name or "unknown",
                    pattern_type="monthly",
                    peak_periods=[month_names[month-1] for month in peak_months],
                    low_periods=[month_names[month-1] for month in low_months],
                    seasonal_factor=monthly_avg.std() / monthly_avg.mean(),
                    confidence=0.7
                )
            
            return None
        
        except Exception as e:
            self.logger.error("Failed to analyze monthly seasonality", error=str(e))
            return None
    
    def _analyze_yearly_seasonality(self, df: pd.DataFrame) -> Optional[SeasonalPattern]:
        """Analyze yearly seasonal patterns."""
        try:
            df['quarter'] = df.index.quarter
            quarterly_avg = df.groupby('quarter')['sales'].mean()
            
            # Check if there's significant variation
            if quarterly_avg.std() > quarterly_avg.mean() * 0.1:  # 10% coefficient of variation
                peak_quarters = quarterly_avg.nlargest(2).index.tolist()
                low_quarters = quarterly_avg.nsmallest(2).index.tolist()
                
                quarter_names = ['Q1', 'Q2', 'Q3', 'Q4']
                
                return SeasonalPattern(
                    product_id=df.index.name or "unknown",
                    pattern_type="yearly",
                    peak_periods=[quarter_names[quarter-1] for quarter in peak_quarters],
                    low_periods=[quarter_names[quarter-1] for quarter in low_quarters],
                    seasonal_factor=quarterly_avg.std() / quarterly_avg.mean(),
                    confidence=0.6
                )
            
            return None
        
        except Exception as e:
            self.logger.error("Failed to analyze yearly seasonality", error=str(e))
            return None
    
    async def _get_historical_sales_data(self, product_id: str, warehouse_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get historical sales data for a product."""
        try:
            # In production, this would query the database
            # For now, use simulated data
            
            if product_id in self.historical_data:
                df = self.historical_data[product_id]
                return [
                    {
                        "date": row['date'].isoformat(),
                        "sales": row['sales'],
                        "inventory": row.get('inventory', 100)
                    }
                    for _, row in df.iterrows()
                ]
            
            return []
        
        except Exception as e:
            self.logger.error("Failed to get historical sales data", error=str(e))
            return []
    
    async def _get_recent_sales_data(self, product_id: str, warehouse_id: Optional[str], days: int = 7) -> List[Dict[str, Any]]:
        """Get recent sales data for a product."""
        try:
            historical_data = await self._get_historical_sales_data(product_id, warehouse_id)
            
            # Return last N days
            return historical_data[-days:] if len(historical_data) >= days else historical_data
        
        except Exception as e:
            self.logger.error("Failed to get recent sales data", error=str(e))
            return []
    
    async def _get_products_for_reorder_analysis(self, warehouse_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get products that need reorder analysis."""
        try:
            # In production, this would query the inventory database
            # For now, return sample data
            
            sample_products = [
                {
                    "product_id": "product_1",
                    "warehouse_id": "warehouse_1",
                    "current_stock": 15,
                    "reorder_point": 20,
                    "max_stock": 100
                },
                {
                    "product_id": "product_2",
                    "warehouse_id": "warehouse_1",
                    "current_stock": 5,
                    "reorder_point": 10,
                    "max_stock": 80
                },
                {
                    "product_id": "product_3",
                    "warehouse_id": "warehouse_2",
                    "current_stock": 25,
                    "reorder_point": 15,
                    "max_stock": 120
                }
            ]
            
            if warehouse_id:
                return [p for p in sample_products if p["warehouse_id"] == warehouse_id]
            
            return sample_products
        
        except Exception as e:
            self.logger.error("Failed to get products for reorder analysis", error=str(e))
            return []
    
    async def _calculate_reorder_recommendation(
        self, 
        product_id: str, 
        warehouse_id: str, 
        current_stock: int, 
        predicted_demand: float, 
        reorder_point: int
    ) -> Optional[Dict[str, Any]]:
        """Calculate reorder recommendation for a product."""
        try:
            # Calculate days until stockout
            daily_demand = predicted_demand / 30  # Convert monthly to daily
            days_until_stockout = current_stock / daily_demand if daily_demand > 0 else float('inf')
            
            # Determine urgency
            if current_stock <= 0:
                urgency = "critical"
            elif current_stock <= reorder_point * 0.5:
                urgency = "high"
            elif current_stock <= reorder_point:
                urgency = "medium"
            elif days_until_stockout <= 7:
                urgency = "high"
            elif days_until_stockout <= 14:
                urgency = "medium"
            else:
                urgency = "low"
            
            # Only recommend if urgency is medium or higher
            if urgency in ["low"]:
                return None
            
            # Calculate recommended order quantity
            # Use Economic Order Quantity (EOQ) concept simplified
            safety_stock = reorder_point * 0.5
            recommended_quantity = int(predicted_demand + safety_stock - current_stock)
            recommended_quantity = max(0, recommended_quantity)
            
            # Estimate cost impact
            unit_cost = 10.0  # Simplified unit cost
            cost_impact = recommended_quantity * unit_cost
            
            # Generate reasons
            reasons = []
            if current_stock <= reorder_point:
                reasons.append(f"Current stock ({current_stock}) below reorder point ({reorder_point})")
            if days_until_stockout <= 14:
                reasons.append(f"Estimated stockout in {int(days_until_stockout)} days")
            if predicted_demand > current_stock:
                reasons.append(f"Predicted demand ({predicted_demand:.1f}) exceeds current stock")
            
            recommendation = ReorderRecommendation(
                product_id=product_id,
                warehouse_id=warehouse_id,
                current_stock=current_stock,
                predicted_demand=predicted_demand,
                recommended_order_quantity=recommended_quantity,
                reorder_urgency=urgency,
                estimated_stockout_date=datetime.now() + timedelta(days=int(days_until_stockout)) if days_until_stockout != float('inf') else None,
                cost_impact=cost_impact,
                reasons=reasons
            )
            
            return recommendation.dict()
        
        except Exception as e:
            self.logger.error("Failed to calculate reorder recommendation", error=str(e))
            return None
    
    async def _calculate_recent_accuracy(self, model_key: str) -> Dict[str, float]:
        """Calculate recent forecast accuracy for a model."""
        try:
            # In production, this would compare recent predictions with actual sales
            # For now, return simulated accuracy metrics
            
            import random
            
            mae = random.uniform(1.0, 5.0)  # Mean Absolute Error
            mape = random.uniform(10.0, 30.0)  # Mean Absolute Percentage Error
            
            return {
                "mae": round(mae, 2),
                "mape": round(mape, 2),
                "samples": random.randint(20, 100)
            }
        
        except Exception as e:
            self.logger.error("Failed to calculate recent accuracy", error=str(e))
            return {"mae": 0, "mape": 0, "samples": 0}
    
    async def _retrain_models(self) -> Dict[str, Any]:
        """Retrain all ML models with latest data."""
        try:
            retrained_models = []
            
            # Get all products that have models
            for model_key in list(self.models.keys()):
                product_id = model_key.split('_')[0]
                warehouse_id = model_key.split('_')[1] if '_' in model_key else None
                
                try:
                    await self._train_product_model(product_id, warehouse_id)
                    retrained_models.append(model_key)
                except Exception as e:
                    self.logger.error("Failed to retrain model", error=str(e), model_key=model_key)
            
            return {
                "retrained_models": retrained_models,
                "total_models": len(self.models),
                "retrain_timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error("Failed to retrain models", error=str(e))
            raise
    
    async def _handle_order_created(self, message: AgentMessage):
        """Handle order created messages to update demand data."""
        payload = message.payload
        items = payload.get("items", [])
        
        # Update demand data for each product
        for item in items:
            product_id = item.get("product_id")
            quantity = item.get("quantity", 0)
            
            if product_id and quantity > 0:
                # In production, this would update the historical sales data
                self.logger.debug("Demand data updated", product_id=product_id, quantity=quantity)
    
    async def _handle_inventory_update(self, message: AgentMessage):
        """Handle inventory updates for reorder recommendations."""
        payload = message.payload
        
        if payload.get("action") == "reorder_recommendation":
            product_id = payload.get("product_id")
            warehouse_id = payload.get("warehouse_id")
            suggested_quantity = payload.get("suggested_quantity")
            
            # Generate detailed reorder recommendation
            try:
                forecast_request = {
                    "product_id": product_id,
                    "warehouse_id": warehouse_id,
                    "forecast_days": 30
                }
                
                forecast_result = await self._forecast_demand(forecast_request)
                
                # Send recommendation to procurement or inventory management
                await self.send_message(
                    recipient_agent="inventory_agent",
                    message_type=MessageType.DEMAND_FORECAST,
                    payload={
                        "action": "reorder_recommendation",
                        "product_id": product_id,
                        "warehouse_id": warehouse_id,
                        "predicted_demand": forecast_result["predicted_demand"],
                        "suggested_quantity": suggested_quantity,
                        "confidence": forecast_result["confidence_score"]
                    }
                )
            
            except Exception as e:
                self.logger.error("Failed to handle reorder recommendation request", error=str(e))
    
    async def _retrain_models_periodically(self):
        """Background task to retrain models periodically."""
        while not self.shutdown_event.is_set():
            try:
                # Retrain models every 24 hours
                await asyncio.sleep(24 * 3600)
                
                if not self.shutdown_event.is_set():
                    self.logger.info("Starting periodic model retraining")
                    await self._retrain_models()
                    self.logger.info("Periodic model retraining completed")
            
            except Exception as e:
                self.logger.error("Error in periodic model retraining", error=str(e))
                await asyncio.sleep(3600)  # Wait 1 hour on error
    
    async def _generate_daily_forecasts(self):
        """Background task to generate daily forecasts for all products."""
        while not self.shutdown_event.is_set():
            try:
                # Generate forecasts every 6 hours
                await asyncio.sleep(6 * 3600)
                
                if not self.shutdown_event.is_set():
                    self.logger.info("Starting daily forecast generation")
                    
                    # Generate forecasts for all products
                    for product_id in self.historical_data.keys():
                        try:
                            forecast_request = {
                                "product_id": product_id,
                                "forecast_days": 7,
                                "include_confidence_interval": False
                            }
                            
                            await self._forecast_demand(forecast_request)
                        
                        except Exception as e:
                            self.logger.error("Failed to generate daily forecast", error=str(e), product_id=product_id)
                    
                    self.logger.info("Daily forecast generation completed")
            
            except Exception as e:
                self.logger.error("Error in daily forecast generation", error=str(e))
                await asyncio.sleep(3600)  # Wait 1 hour on error
    
    async def _monitor_forecast_accuracy(self):
        """Background task to monitor and report forecast accuracy."""
        while not self.shutdown_event.is_set():
            try:
                # Check accuracy every 12 hours
                await asyncio.sleep(12 * 3600)
                
                if not self.shutdown_event.is_set():
                    accuracy_metrics = await self._get_forecast_accuracy()
                    
                    # Send accuracy report to monitoring agent
                    await self.send_message(
                        recipient_agent="monitoring_agent",
                        message_type=MessageType.RISK_ALERT,
                        payload={
                            "alert_type": "forecast_accuracy_report",
                            "overall_mae": accuracy_metrics["overall_metrics"]["mean_absolute_error"],
                            "overall_mape": accuracy_metrics["overall_metrics"]["mean_absolute_percentage_error"],
                            "models_evaluated": accuracy_metrics["overall_metrics"]["models_evaluated"],
                            "severity": "info"
                        }
                    )
            
            except Exception as e:
                self.logger.error("Error monitoring forecast accuracy", error=str(e))
                await asyncio.sleep(6 * 3600)  # Wait 6 hours on error


# FastAPI app instance for running the agent as a service
app = FastAPI(title="Demand Forecasting Agent", version="1.0.0")

# Global agent instance
demand_forecasting_agent: Optional[DemandForecastingAgent] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the Demand Forecasting Agent on startup."""
    global demand_forecasting_agent
    demand_forecasting_agent = DemandForecastingAgent()
    await demand_forecasting_agent.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup the Demand Forecasting Agent on shutdown."""
    global demand_forecasting_agent
    if demand_forecasting_agent:
        await demand_forecasting_agent.stop()


# Include agent routes
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if demand_forecasting_agent:
        health_status = demand_forecasting_agent.get_health_status()
        return {"status": "healthy", "agent_status": health_status.dict()}
    return {"status": "unhealthy", "message": "Agent not initialized"}


# Mount agent's FastAPI app
app.mount("/api/v1", demand_forecasting_agent.app if demand_forecasting_agent else FastAPI())


if __name__ == "__main__":
    import uvicorn
    from shared.database import initialize_database_manager, DatabaseConfig
    import os
    
    # Initialize database
    db_config = DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "multi_agent_ecommerce"),
        username=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres123")
    )
    initialize_database_manager(db_config)
    
    # Run the agent
    uvicorn.run(
        "demand_forecasting_agent:app",
        host="0.0.0.0",
        port=8006,
        reload=False,
        log_level="info"
    )
