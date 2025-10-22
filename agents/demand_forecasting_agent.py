
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
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import structlog
import sys
import os
import uvicorn

# Get the absolute path of the current file
current_file_path = os.path.abspath(__file__)

# Get the directory containing the current file
current_dir = os.path.dirname(current_file_path)

# Get the parent directory (project root)
project_root = os.path.dirname(current_dir)

# Add the project root to the Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now try the import
try:
    from shared.base_agent import BaseAgent, MessageType, AgentMessage
    from shared.models import APIResponse, Product, SalesData, InventoryData
    from shared.database import DatabaseManager, get_database_manager
    from shared.db_helpers import DatabaseHelper
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current sys.path: {sys.path}")
    shared_dir = os.path.join(project_root, "shared")
    if os.path.exists(shared_dir):
        print(f"Contents of {shared_dir}:")
        for item in os.listdir(shared_dir):
            print(f"  - {item}")
    else:
        print(f"Directory not found: {shared_dir}")
    sys.exit(1)

logger = structlog.get_logger(__name__)


class DemandForecastRequest(BaseModel):
    """Request model for demand forecasting.

    Attributes:
        product_id (str): The ID of the product to forecast.
        warehouse_id (Optional[str]): The ID of the warehouse (optional).
        forecast_days (int): Number of days to forecast (default: 30).
        include_confidence_interval (bool): Whether to include confidence intervals (default: True).
    """
    product_id: str = Field(..., description="The ID of the product to forecast")
    warehouse_id: Optional[str] = Field(None, description="The ID of the warehouse, if forecasting for a specific warehouse")
    forecast_days: int = Field(30, gt=0, description="Number of days into the future to forecast demand")
    include_confidence_interval: bool = Field(True, description="Whether to include confidence interval in the forecast result")


class DemandForecast(BaseModel):
    """Model for demand forecast result.

    Attributes:
        product_id (str): The ID of the product.
        warehouse_id (Optional[str]): The ID of the warehouse.
        forecast_period_days (int): Number of days the forecast covers.
        predicted_demand (float): The predicted demand quantity.
        confidence_score (float): Confidence score of the forecast (0-1).
        confidence_interval_lower (Optional[float]): Lower bound of the confidence interval.
        confidence_interval_upper (Optional[float]): Upper bound of the confidence interval.
        trend (str): Detected demand trend ("increasing", "decreasing", "stable").
        seasonality_detected (bool): Whether seasonality was detected.
        factors_considered (List[str]): List of factors considered in the forecast.
        generated_at (datetime): Timestamp of when the forecast was generated.
    """
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
    """Model for reorder recommendation.

    Attributes:
        product_id (str): The ID of the product.
        warehouse_id (str): The ID of the warehouse.
        current_stock (int): Current stock level.
        predicted_demand (float): Predicted demand for the reorder period.
        recommended_order_quantity (int): Recommended quantity to reorder.
        reorder_urgency (str): Urgency level ("low", "medium", "high", "critical").
        estimated_stockout_date (Optional[datetime]): Estimated date of stockout.
        cost_impact (float): Estimated cost impact of the recommendation.
        reasons (List[str]): Reasons for the recommendation.
    """
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
    """Model for seasonal pattern analysis.

    Attributes:
        product_id (str): The ID of the product.
        pattern_type (str): Type of pattern ("weekly", "monthly", "yearly").
        peak_periods (List[str]): List of peak periods.
        low_periods (List[str]): List of low periods.
        seasonal_factor (float): Seasonal factor.
        confidence (float): Confidence of the detected pattern.
    """
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
        agent_id = os.getenv("AGENT_ID", "demand_forecasting_agent")
        agent_type = os.getenv("AGENT_TYPE", "demand_forecasting")  # Default agent_type
        super().__init__(agent_id=agent_id, **kwargs)
        self.app = FastAPI(title="Demand Forecasting Agent API", version="1.0.0")
        self.setup_routes()

        # ML models and data
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.historical_data: Dict[str, pd.DataFrame] = {}

        self.db_manager: DatabaseManager = get_database_manager()
        self.db_helper = DatabaseHelper(self.db_manager)
        self._db_initialized = False
        self.forecast_accuracy_metrics: Dict[str, Any] = {}

        # Register message handlers
        self.register_handler(MessageType.ORDER_CREATED, self._handle_order_created)
        self.register_handler(MessageType.INVENTORY_UPDATE, self._handle_inventory_update)

    async def initialize(self):
        """Initialize the Demand Forecasting Agent."""
        self.logger.info("Initializing Demand Forecasting Agent")
        await self._initialize_db()

        # Initialize ML models and load historical data
        await self._initialize_ml_models()
        await self._load_historical_data()

        # Start background tasks
        asyncio.create_task(self._retrain_models_periodically())
        asyncio.create_task(self._generate_daily_forecasts())
        asyncio.create_task(self._monitor_forecast_accuracy())

        self.logger.info("Demand Forecasting Agent initialized successfully")

    async def cleanup(self):
        """Cleanup resources.

        This method is called when the agent is shutting down.
        """
        self.logger.info("Cleaning up Demand Forecasting Agent")
        try:
            await self.db_manager.close()
            self.logger.info("Database disconnected.")
        except Exception as e:
            self.logger.error(f"Error disconnecting from database: {e}")

    async def _initialize_db(self):
        """Initialize the database connection.

        Ensures the database manager connects and sets the initialization flag.
        """
        try:
            await self.db_manager.initialize_async()
            self._db_initialized = True
            self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            self._db_initialized = False

    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process demand forecasting business logic.

        Args:
            data (Dict[str, Any]): Dictionary containing the action and relevant data.

        Returns:
            Dict[str, Any]: Result of the business logic execution.

        Raises:
            ValueError: If an unknown action is provided.
        """
        action = data.get("action")

        try:
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
        except Exception as e:
            self.logger.error(f"Error processing business logic for action {action}: {e}")
            raise

    def setup_routes(self):
        """Setup FastAPI routes for the Demand Forecasting Agent.

        This includes health check, root, and business logic endpoints.
        """

        @self.app.get("/health", status_code=status.HTTP_200_OK)
        async def health_check():
            """Health check endpoint to verify agent status."""
            self.logger.info("Health check requested.")
            return APIResponse(success=True, message="Demand Forecasting Agent is healthy.")

        @self.app.get("/", status_code=status.HTTP_200_OK)
        async def root():
            """Root endpoint providing basic agent information."""
            self.logger.info("Root endpoint requested.")
            return APIResponse(success=True, message="Welcome to the Demand Forecasting Agent API.", data={"agent_id": self.agent_id, "agent_type": self.agent_type})

        @self.app.post("/forecast", response_model=APIResponse)
        async def forecast_demand_endpoint(request: DemandForecastRequest):
            """Generate demand forecast for a product.

            Args:
                request (DemandForecastRequest): The request containing product_id, warehouse_id, forecast_days, and include_confidence_interval.

            Returns:
                APIResponse: The API response containing the demand forecast.
            """
            try:
                self.logger.info(f"Received forecast request for product: {request.product_id}")
                result = await self._forecast_demand(request.dict())
                return APIResponse(
                    success=True,
                    message="Demand forecast generated successfully",
                    data=result
                )
            except Exception as e:
                self.logger.error("Failed to generate demand forecast", error=str(e), product_id=request.product_id)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        @self.app.get("/reorder-recommendations", response_model=APIResponse)
        async def get_reorder_recommendations_endpoint(warehouse_id: Optional[str] = None):
            """Get reorder recommendations.

            Args:
                warehouse_id (Optional[str]): The ID of the warehouse (optional).

            Returns:
                APIResponse: The API response containing reorder recommendations.
            """
            try:
                self.logger.info(f"Received reorder recommendations request for warehouse: {warehouse_id}")
                result = await self._get_reorder_recommendations(warehouse_id)
                return APIResponse(
                    success=True,
                    message="Reorder recommendations retrieved successfully",
                    data=result
                )
            except Exception as e:
                self.logger.error("Failed to get reorder recommendations", error=str(e), warehouse_id=warehouse_id)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        @self.app.get("/seasonality/{product_id}", response_model=APIResponse)
        async def analyze_seasonality_endpoint(product_id: str):
            """Analyze seasonal patterns for a product.

            Args:
                product_id (str): The ID of the product.

            Returns:
                APIResponse: The API response containing seasonality analysis.
            """
            try:
                self.logger.info(f"Received seasonality analysis request for product: {product_id}")
                result = await self._analyze_seasonality(product_id)
                return APIResponse(
                    success=True,
                    message="Seasonality analysis completed successfully",
                    data=result
                )
            except Exception as e:
                self.logger.error("Failed to analyze seasonality", error=str(e), product_id=product_id)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        @self.app.get("/accuracy", response_model=APIResponse)
        async def get_forecast_accuracy_endpoint():
            """Get forecast accuracy metrics.

            Returns:
                APIResponse: The API response containing forecast accuracy metrics.
            """
            try:
                self.logger.info("Received forecast accuracy request.")
                result = await self._get_forecast_accuracy()
                return APIResponse(
                    success=True,
                    message="Forecast accuracy retrieved successfully",
                    data=result
                )
            except Exception as e:
                self.logger.error("Failed to get forecast accuracy", error=str(e))
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        @self.app.post("/retrain", response_model=APIResponse)
        async def retrain_models_endpoint():
            """Manually trigger model retraining.

            Returns:
                APIResponse: The API response indicating retraining status.
            """
            try:
                self.logger.info("Received model retraining request.")
                result = await self._retrain_models()
                return APIResponse(
                    success=True,
                    message="Models retrained successfully",
                    data=result
                )
            except Exception as e:
                self.logger.error("Failed to retrain models", error=str(e))
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    async def _forecast_demand(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate demand forecast for a product.

        Args:
            request_data (Dict[str, Any]): Dictionary containing product_id, warehouse_id, forecast_days, and include_confidence_interval.

        Returns:
            Dict[str, Any]: The demand forecast result.

        Raises:
            HTTPException: If forecasting fails due to insufficient data or other errors.
        """
        if not self._db_initialized:
            self.logger.error("Database not initialized. Cannot forecast demand.")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

        try:
            product_id = request_data["product_id"]
            warehouse_id = request_data.get("warehouse_id")
            forecast_days = request_data.get("forecast_days", 30)
            include_confidence_interval = request_data.get("include_confidence_interval", True)

            model_key = f"{product_id}_{warehouse_id or 'all'}"

            if model_key not in self.models:
                self.logger.info(f"No model found for {model_key}, training a new one.")
                await self._train_product_model(product_id, warehouse_id)

            if model_key not in self.models: # Check again after training attempt
                self.logger.warning(f"Model could not be trained for {model_key} due to insufficient data or error. Using simple forecast.")
                predicted_demand = await self._simple_forecast(product_id, warehouse_id, forecast_days)
                confidence_score = 0.5 # Lower confidence for simple forecast
                confidence_interval_lower = predicted_demand * 0.8
                confidence_interval_upper = predicted_demand * 1.2
                seasonality_detected = False
                trend = "stable"
                factors_considered = ["historical_average"]
            else:
                # Prepare features for prediction
                features = await self._prepare_forecast_features(product_id, warehouse_id, forecast_days)
                if not features:
                    self.logger.warning(f"Could not prepare features for {model_key}. Using simple forecast.")
                    predicted_demand = await self._simple_forecast(product_id, warehouse_id, forecast_days)
                    confidence_score = 0.5
                    confidence_interval_lower = predicted_demand * 0.8
                    confidence_interval_upper = predicted_demand * 1.2
                    seasonality_detected = False
                    trend = "stable"
                    factors_considered = ["historical_average"]
                else:
                    model = self.models[model_key]
                    scaler = self.scalers[model_key]
                    scaled_features = scaler.transform(np.array(features).reshape(1, -1))
                    predicted_demand = float(model.predict(scaled_features)[0])
                    predicted_demand = max(0, predicted_demand) # Demand cannot be negative

                    confidence_score = self._calculate_confidence_score(model_key)
                    trend = self._determine_trend(product_id, warehouse_id)
                    seasonality_detected = await self._detect_seasonality(product_id)
                    factors_considered = ["historical_sales", "seasonal_patterns", "recent_trends"]

                    if include_confidence_interval:
                        # Simple approximation for confidence interval
                        ci_range = (1 - confidence_score) * predicted_demand
                        confidence_interval_lower = max(0, predicted_demand - ci_range)
                        confidence_interval_upper = predicted_demand + ci_range
                    else:
                        confidence_interval_lower = None
                        confidence_interval_upper = None

            self.logger.info(f"Forecast generated for product {product_id}", predicted_demand=predicted_demand)
            return DemandForecast(
                product_id=product_id,
                warehouse_id=warehouse_id,
                forecast_period_days=forecast_days,
                predicted_demand=predicted_demand,
                confidence_score=confidence_score,
                confidence_interval_lower=confidence_interval_lower,
                confidence_interval_upper=confidence_interval_upper,
                trend=trend,
                seasonality_detected=seasonality_detected,
                factors_considered=factors_considered,
                generated_at=datetime.now()
            ).dict()

        except Exception as e:
            self.logger.error(f"Error in _forecast_demand for product {product_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate forecast: {e}")

    async def _get_reorder_recommendations(self, warehouse_id: Optional[str]) -> List[Dict[str, Any]]:
        """Generate reorder recommendations based on forecasts and current inventory.

        Args:
            warehouse_id (Optional[str]): The ID of the warehouse (optional).

        Returns:
            List[Dict[str, Any]]: A list of reorder recommendations.

        Raises:
            HTTPException: If recommendations cannot be generated.
        """
        if not self._db_initialized:
            self.logger.error("Database not initialized. Cannot get reorder recommendations.")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

        recommendations = []
        try:
            async with self.db_manager.get_session() as session:
                products = await self.db_helper.get_all(session, Product) # Assuming Product model exists
                for product in products:
                    product_id = product.id
                    current_stock = await self._get_current_stock(product_id, warehouse_id) # Needs implementation

                    # Forecast demand for the lead time + safety stock period
                    # Assume a lead time of 7 days for simplicity
                    forecast_request = {
                        "product_id": product_id,
                        "warehouse_id": warehouse_id,
                        "forecast_days": 7 # Lead time
                    }
                    forecast_result = await self._forecast_demand(forecast_request)
                    predicted_demand = forecast_result["predicted_demand"]

                    # Simple reorder logic: if current stock < predicted demand for lead time
                    if current_stock < predicted_demand:
                        recommended_order_quantity = int(predicted_demand * 1.5 - current_stock) # Order 1.5x lead time demand
                        reorder_urgency = "high"
                        estimated_stockout_date = datetime.now() + timedelta(days=int(current_stock / (predicted_demand / forecast_request["forecast_days"])) if predicted_demand > 0 else 999)
                        cost_impact = recommended_order_quantity * 10.0 # Placeholder cost
                        reasons = ["Low stock", "High predicted demand"]
                    else:
                        recommended_order_quantity = 0
                        reorder_urgency = "low"
                        estimated_stockout_date = None
                        cost_impact = 0.0
                        reasons = ["Sufficient stock"]

                    recommendations.append(ReorderRecommendation(
                        product_id=product_id,
                        warehouse_id=warehouse_id or "unknown",
                        current_stock=current_stock,
                        predicted_demand=predicted_demand,
                        recommended_order_quantity=recommended_order_quantity,
                        reorder_urgency=reorder_urgency,
                        estimated_stockout_date=estimated_stockout_date,
                        cost_impact=cost_impact,
                        reasons=reasons
                    ).dict())
            self.logger.info("Reorder recommendations generated.", count=len(recommendations))
            return recommendations
        except Exception as e:
            self.logger.error(f"Error generating reorder recommendations: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate reorder recommendations: {e}")

    async def _analyze_seasonality(self, product_id: str) -> Dict[str, Any]:
        """Analyze seasonal patterns for a given product.

        Args:
            product_id (str): The ID of the product.

        Returns:
            Dict[str, Any]: A dictionary containing seasonal pattern analysis.

        Raises:
            HTTPException: If seasonality analysis fails.
        """
        if not self._db_initialized:
            self.logger.error("Database not initialized. Cannot analyze seasonality.")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

        try:
            historical_data = await self._get_historical_sales_data(product_id)
            if not historical_data:
                self.logger.warning(f"No historical data for product {product_id} to analyze seasonality.")
                return {"product_id": product_id, "seasonality_detected": False, "patterns": []}

            df = pd.DataFrame(historical_data)
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)

            patterns = []
            # Example: Monthly seasonality
            monthly_pattern = self._analyze_monthly_seasonality(df.copy(deep=True))
            if monthly_pattern: patterns.append(monthly_pattern.dict())

            # Example: Yearly seasonality
            yearly_pattern = self._analyze_yearly_seasonality(df.copy(deep=True))
            if yearly_pattern: patterns.append(yearly_pattern.dict())

            seasonality_detected = len(patterns) > 0
            self.logger.info(f"Seasonality analysis completed for product {product_id}. Detected: {seasonality_detected}")
            return {"product_id": product_id, "seasonality_detected": seasonality_detected, "patterns": patterns}
        except Exception as e:
            self.logger.error(f"Error analyzing seasonality for product {product_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to analyze seasonality: {e}")

    async def _get_forecast_accuracy(self) -> Dict[str, Any]:
        """Retrieve current forecast accuracy metrics.

        Returns:
            Dict[str, Any]: A dictionary containing various accuracy metrics.
        """
        try:
            self.logger.info("Retrieving forecast accuracy metrics.")
            # In a real system, this would fetch metrics from a monitoring system or recalculate
            # For now, return the stored metrics.
            return self.forecast_accuracy_metrics
        except Exception as e:
            self.logger.error(f"Error retrieving forecast accuracy metrics: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve forecast accuracy: {e}")

    async def _retrain_models(self) -> Dict[str, Any]:
        """Trigger a retraining of all active ML models.

        Returns:
            Dict[str, Any]: Status of the retraining process.
        """
        if not self._db_initialized:
            self.logger.error("Database not initialized. Cannot retrain models.")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database service unavailable.")

        self.logger.info("Initiating model retraining for all products.")
        try:
            async with self.db_manager.get_session() as session:
                products = await self.db_helper.get_all(session, Product)
                retrained_count = 0
                for product in products:
                    product_id = product.id
                    try:
                        await self._train_product_model(product_id)
                        retrained_count += 1
                    except Exception as product_e:
                        self.logger.warning(f"Failed to retrain model for product {product_id}: {product_e}")
            self.logger.info(f"Retraining completed. {retrained_count} models retrained.")
            return {"status": "success", "retrained_models_count": retrained_count, "timestamp": datetime.now().isoformat()}
        except Exception as e:
            self.logger.error(f"Error during model retraining: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrain models: {e}")

    async def _initialize_ml_models(self):
        """Initialize machine learning models.

        This method can be used to load pre-trained models or initialize empty model structures.
        """
        try:
            self.logger.info("Initializing ML models")
            # In a real scenario, this might load models from storage
            # For now, models are trained on demand or during scheduled retraining
            self.models = {}
            self.scalers = {}
            self.logger.info("ML models initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize ML models: {e}")

    async def _load_historical_data(self):
        """Load historical sales data for model training from the database.

        If no data is found, sample data is generated and saved to the database.
        """
        if not self._db_initialized:
            self.logger.warning("Database not initialized, skipping historical data load.")
            return
        try:
            self.logger.info("Attempting to load historical data from database.")
            async with self.db_manager.get_session() as session:
                all_sales_data = await self.db_helper.get_all(session, SalesData) # Use actual SalesData model

                if not all_sales_data:
                    self.logger.info("No historical sales data found in the database. Generating and saving sample data.")
                    sample_products = ["product_1", "product_2", "product_3"]
                    for product_id in sample_products:
                        dates = pd.date_range(start=datetime.now() - timedelta(days=180), end=datetime.now(), freq='D')
                        base_demand = 10 + np.random.normal(0, 2, len(dates))
                        trend = np.linspace(0, 5, len(dates))
                        seasonality = 3 * np.sin(2 * np.pi * np.arange(len(dates)) / 7)
                        sales = np.maximum(0, base_demand + trend + seasonality + np.random.normal(0, 1, len(dates)))

                        for i, date in enumerate(dates):
                            sample_sales_data = SalesData(
                                product_id=product_id,
                                warehouse_id="warehouse_A", # Default warehouse
                                date=date.to_pydatetime(),
                                sales=float(sales[i]),
                                revenue=float(sales[i] * 10), # Placeholder revenue
                                quantity=int(sales[i]),
                                order_id=str(uuid4())
                            )
                            await self.db_helper.create(session, sample_sales_data)
                            # Add to in-memory for immediate use if needed, but primary source is DB
                            if product_id not in self.historical_data:
                                self.historical_data[product_id] = pd.DataFrame(columns=["date", "sales", "inventory"])
                            new_row = pd.DataFrame([{
                                "date": date.to_pydatetime(),
                                "sales": float(sales[i]),
                                "inventory": np.random.randint(50, 200)
                            }])
                            self.historical_data[product_id] = pd.concat([self.historical_data[product_id], new_row], ignore_index=True)
                    await session.commit()
                    self.logger.info("Sample historical data generated and saved to database.")
                else:
                    self.logger.info(f"Loaded {len(all_sales_data)} historical sales records from database.")
                    for record in all_sales_data:
                        product_id = record.product_id
                        if product_id not in self.historical_data:
                            self.historical_data[product_id] = pd.DataFrame(columns=["date", "sales", "inventory"])
                        new_row = pd.DataFrame([{
                            "date": record.date,
                            "sales": float(record.sales),
                            "inventory": np.random.randint(50, 200) # Assuming inventory is not directly in SalesData or needs to be fetched separately
                        }])
                        self.historical_data[product_id] = pd.concat([self.historical_data[product_id], new_row], ignore_index=True)
                    self.logger.info("Historical data loaded from database and processed into in-memory store.")

            self.logger.info("Historical data loading process completed.")
        except Exception as e:
            self.logger.error(f"Failed to load historical data from database: {e}")
            raise

    async def _train_product_model(self, product_id: str, warehouse_id: Optional[str] = None):
        """Train ML model for a specific product.

        Args:
            product_id (str): The ID of the product.
            warehouse_id (Optional[str]): The ID of the warehouse (optional).

        Raises:
            Exception: If model training fails.
        """
        if not self._db_initialized:
            self.logger.warning("Database not initialized, cannot train product model.")
            return
        try:
            model_key = f"{product_id}_{warehouse_id or 'all'}"
            self.logger.info(f"Attempting to train model for {model_key}")

            historical_data_records = await self._get_historical_sales_data(product_id, warehouse_id)
            if not historical_data_records:
                self.logger.warning(f"Insufficient data for model training for {model_key}. Skipping training.")
                return

            df = pd.DataFrame(historical_data_records)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')

            if len(df) < 30:  # Need at least 30 days of data for meaningful training
                self.logger.warning(f"Insufficient data for model training for {model_key} (less than 30 days). Skipping training.")
                return

            features, target = self._prepare_training_data(df)

            if not features or len(features) == 0:
                self.logger.warning(f"No features prepared for model training for {model_key}. Skipping training.")
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

            self.logger.info(f"Model trained successfully for {model_key}", samples=len(features))
        except Exception as e:
            self.logger.error(f"Failed to train product model for {product_id}: {e}")
            raise

    def _prepare_training_data(self, df: pd.DataFrame) -> Tuple[List[List[float]], List[float]]:
        """Prepare training data from historical sales DataFrame.

        Args:
            df (pd.DataFrame): DataFrame containing historical sales data.

        Returns:
            Tuple[List[List[float]], List[float]]: A tuple of features and target values.
        """
        try:
            features = []
            target = []

            # Create features for each day
            # Ensure enough historical data for feature creation (e.g., last 7 days)
            if len(df) < 7:
                self.logger.warning("Not enough data to create features for training.")
                return [], []

            for i in range(7, len(df)):  # Need at least 7 days of history
                # Features: last 7 days sales, day of week, month, trend
                last_7_days_sales = df.iloc[i-7:i]['sales'].values
                current_date = df.iloc[i]['date']

                if len(last_7_days_sales) != 7:
                    continue # Skip if not enough recent data

                day_of_week = current_date.dayofweek
                month = current_date.month
                day_of_year = current_date.dayofyear

                # Calculate trend (slope of last 7 days)
                x = np.arange(len(last_7_days_sales))
                trend = np.polyfit(x, last_7_days_sales, 1)[0] if len(last_7_days_sales) > 1 else 0.0

                feature_vector = [
                    np.mean(last_7_days_sales),  # Average sales last 7 days
                    np.std(last_7_days_sales),   # Volatility
                    last_7_days_sales[-1],       # Yesterday's sales
                    trend,                 # Trend
                    float(day_of_week),          # Day of week
                    float(month),                # Month
                    float(day_of_year / 365.0),  # Day of year (normalized)
                ]

                features.append(feature_vector)
                target.append(df.iloc[i]['sales'])

            return features, target
        except Exception as e:
            self.logger.error(f"Failed to prepare training data: {e}")
            return [], []

    async def _prepare_forecast_features(self, product_id: str, warehouse_id: Optional[str], forecast_days: int) -> Optional[List[float]]:
        """Prepare features for demand forecasting.

        Args:
            product_id (str): The ID of the product.
            warehouse_id (Optional[str]): The ID of the warehouse (optional).
            forecast_days (int): Number of days to forecast.

        Returns:
            Optional[List[float]]: A list of features for forecasting, or None if data is insufficient.
        """
        if not self._db_initialized:
            self.logger.warning("Database not initialized, cannot prepare forecast features.")
            return None
        try:
            # Get recent sales data
            recent_data_records = await self._get_recent_sales_data(product_id, warehouse_id, days=7)

            if len(recent_data_records) < 7:
                self.logger.warning(f"Insufficient recent data ({len(recent_data_records)} days) for product {product_id} to prepare forecast features. Need at least 7 days.")
                return None

            sales_values = [d['sales'] for d in recent_data_records]

            # Calculate trend
            x = np.arange(len(sales_values))
            trend = np.polyfit(x, sales_values, 1)[0] if len(sales_values) > 1 else 0.0

            # Future date for prediction (mid-point of forecast period)
            future_date = datetime.now() + timedelta(days=forecast_days // 2)

            features = [
                np.mean(sales_values),           # Average recent sales
                np.std(sales_values),            # Volatility
                sales_values[-1],                # Latest sales
                trend,                           # Trend
                float(future_date.weekday()),           # Day of week
                float(future_date.month),               # Month
                float(future_date.timetuple().tm_yday / 365.0),  # Day of year (normalized)
            ]

            return features
        except Exception as e:
            self.logger.error(f"Failed to prepare forecast features for product {product_id}: {e}")
            return None

    async def _simple_forecast(self, product_id: str, warehouse_id: Optional[str], forecast_days: int) -> float:
        """Simple moving average forecast as fallback.

        Args:
            product_id (str): The ID of the product.
            warehouse_id (Optional[str]): The ID of the warehouse (optional).
            forecast_days (int): Number of days to forecast.

        Returns:
            float: The simple moving average forecast.
        """
        if not self._db_initialized:
            self.logger.warning("Database not initialized, returning default simple forecast.")
            return 5.0
        try:
            recent_data_records = await self._get_recent_sales_data(product_id, warehouse_id, days=14)

            if not recent_data_records:
                self.logger.warning(f"No recent data for product {product_id} for simple forecast. Returning default.")
                return 5.0  # Default forecast

            sales_values = [d['sales'] for d in recent_data_records]
            return np.mean(sales_values) * forecast_days
        except Exception as e:
            self.logger.error(f"Failed to calculate simple forecast for product {product_id}: {e}")
            return 5.0

    def _calculate_confidence_score(self, model_key: str) -> float:
        """Calculate confidence score for a model.

        In a production environment, this would be based on model validation metrics (e.g., R-squared, MAE).

        Args:
            model_key (str): The key identifying the model.

        Returns:
            float: The confidence score (0-1).
        """
        try:
            base_confidence = 0.75
            # Adjust based on data availability and model performance metrics
            # For demonstration, a simple heuristic:
            if model_key in self.historical_data and not self.historical_data[model_key].empty:
                data_points = len(self.historical_data[model_key])
                data_factor = min(1.0, data_points / 100.0)  # More data = higher confidence
                return min(0.95, base_confidence + (data_factor * 0.2))
            return base_confidence
        except Exception as e:
            self.logger.error(f"Failed to calculate confidence score for {model_key}: {e}")
            return 0.6

    def _determine_trend(self, product_id: str, warehouse_id: Optional[str]) -> str:
        """Determine demand trend for a product based on recent sales data.

        Args:
            product_id (str): The ID of the product.
            warehouse_id (Optional[str]): The ID of the warehouse (optional).

        Returns:
            str: The trend ("increasing", "decreasing", "stable").
        """
        try:
            # Use in-memory historical data for trend analysis for now
            # In a real system, this would query recent sales from DB
            if product_id in self.historical_data and not self.historical_data[product_id].empty:
                df = self.historical_data[product_id]
                recent_data = df.tail(14)  # Last 2 weeks

                if len(recent_data) >= 7:
                    # Calculate trend using linear regression
                    x = np.arange(len(recent_data))
                    y = recent_data['sales'].values
                    # Handle potential division by zero if all x values are the same (unlikely for arange)
                    if len(x) > 1:
                        slope = np.polyfit(x, y, 1)[0]
                    else:
                        slope = 0.0

                    if slope > 0.1:
                        return "increasing"
                    elif slope < -0.1:
                        return "decreasing"
                    else:
                        return "stable"
            return "stable"
        except Exception as e:
            self.logger.error(f"Failed to determine trend for product {product_id}: {e}")
            return "stable"

    async def _detect_seasonality(self, product_id: str) -> bool:
        """Detect if product has seasonal patterns.

        Args:
            product_id (str): The ID of the product.

        Returns:
            bool: True if seasonality is detected, False otherwise.
        """
        if not self._db_initialized:
            self.logger.warning("Database not initialized, cannot detect seasonality.")
            return False
        try:
            historical_data = await self._get_historical_sales_data(product_id)
            if not historical_data or len(historical_data) < 90: # Need at least 3 months of data
                return False

            df = pd.DataFrame(historical_data)
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)

            # Check for monthly and yearly patterns
            monthly_pattern = self._analyze_monthly_seasonality(df.copy(deep=True))
            yearly_pattern = self._analyze_yearly_seasonality(df.copy(deep=True))

            return monthly_pattern is not None or yearly_pattern is not None
        except Exception as e:
            self.logger.error(f"Failed to detect seasonality for product {product_id}: {e}")
            return False

    def _analyze_monthly_seasonality(self, df: pd.DataFrame) -> Optional[SeasonalPattern]:
        """Analyze monthly seasonal patterns.

        Args:
            df (pd.DataFrame): DataFrame containing historical sales data with a datetime index.

        Returns:
            Optional[SeasonalPattern]: Detected monthly seasonal pattern, or None.
        """
        try:
            if len(df) < 120: # Need at least 4 months of data to detect monthly patterns reliably
                return None
            df['month'] = df.index.month
            monthly_avg = df.groupby('month')['sales'].mean()

            # Check if there's significant variation (e.g., > 15% coefficient of variation)
            if monthly_avg.std() > monthly_avg.mean() * 0.15:
                peak_months = monthly_avg.nlargest(2).index.tolist()
                low_months = monthly_avg.nsmallest(2).index.tolist()
                month_names = [datetime(2000, m, 1).strftime('%B') for m in range(1, 13)]

                return SeasonalPattern(
                    product_id=df.index.name if df.index.name else "unknown", # product_id might be in index name if set
                    pattern_type="monthly",
                    peak_periods=[month_names[month-1] for month in peak_months],
                    low_periods=[month_names[month-1] for month in low_months],
                    seasonal_factor=float(monthly_avg.std() / monthly_avg.mean()),
                    confidence=0.75
                )
            return None
        except Exception as e:
            self.logger.error(f"Failed to analyze monthly seasonality: {e}")
            return None

    def _analyze_yearly_seasonality(self, df: pd.DataFrame) -> Optional[SeasonalPattern]:
        """Analyze yearly seasonal patterns.

        Args:
            df (pd.DataFrame): DataFrame containing historical sales data with a datetime index.

        Returns:
            Optional[SeasonalPattern]: Detected yearly seasonal pattern, or None.
        """
        try:
            if len(df) < 365 * 2: # Need at least 2 years of data to detect yearly patterns reliably
                return None
            df['quarter'] = df.index.quarter
            quarterly_avg = df.groupby('quarter')['sales'].mean()

            # Check if there's significant variation (e.g., > 15% coefficient of variation)
            if quarterly_avg.std() > quarterly_avg.mean() * 0.15:
                peak_quarters = quarterly_avg.nlargest(2).index.tolist()
                low_quarters = quarterly_avg.nsmallest(2).index.tolist()
                quarter_names = ['Q1', 'Q2', 'Q3', 'Q4']

                return SeasonalPattern(
                    product_id=df.index.name if df.index.name else "unknown",
                    pattern_type="yearly",
                    peak_periods=[quarter_names[quarter-1] for quarter in peak_quarters],
                    low_periods=[quarter_names[quarter-1] for quarter in low_quarters],
                    seasonal_factor=float(quarterly_avg.std() / quarterly_avg.mean()),
                    confidence=0.8
                )
            return None
        except Exception as e:
            self.logger.error(f"Failed to analyze yearly seasonality: {e}")
            return None

    async def _get_recent_sales_data(self, product_id: str, warehouse_id: Optional[str], days: int) -> List[Dict[str, Any]]:
        """Retrieve recent sales data for a product from the database.

        Args:
            product_id (str): The ID of the product.
            warehouse_id (Optional[str]): The ID of the warehouse (optional).
            days (int): Number of recent days to retrieve data for.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a sales record.
        """
        if not self._db_initialized:
            self.logger.warning("Database not initialized, cannot retrieve recent sales data.")
            return []
        try:
            async with self.db_manager.get_session() as session:
                filters = {"product_id": product_id}
                if warehouse_id:
                    filters["warehouse_id"] = warehouse_id

                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)

                # Use db_helper to get filtered sales data
                # Assuming SalesData model has a 'date' field for filtering
                sales_data_records = await self.db_helper.get_all(session, SalesData, filters=filters)

                recent_data = []
                for record in sales_data_records:
                    if start_date <= record.date <= end_date:
                        recent_data.append(record.to_dict())
                self.logger.debug(f"Retrieved {len(recent_data)} recent sales records for product {product_id}.")
                return recent_data
        except Exception as e:
            self.logger.error(f"Error retrieving recent sales data for product {product_id}: {e}")
            return []

    async def _get_current_stock(self, product_id: str, warehouse_id: Optional[str]) -> int:
        """Retrieve current stock level for a product from the database.

        Args:
            product_id (str): The ID of the product.
            warehouse_id (Optional[str]): The ID of the warehouse (optional).

        Returns:
            int: The current stock level.
        """
        if not self._db_initialized:
            self.logger.warning("Database not initialized, returning 0 for current stock.")
            return 0
        try:
            async with self.db_manager.get_session() as session:
                filters = {"product_id": product_id}
                if warehouse_id:
                    filters["warehouse_id"] = warehouse_id

                # Assuming InventoryData model exists with product_id, warehouse_id, and stock_level
                inventory_record = await self.db_helper.get_all(session, InventoryData, filters=filters) # get_all to handle multiple warehouses
                if inventory_record:
                    # Sum stock from all relevant warehouses if warehouse_id is None, otherwise specific warehouse
                    current_stock = sum([rec.stock_level for rec in inventory_record])
                    self.logger.debug(f"Retrieved current stock for product {product_id}: {current_stock}")
                    return current_stock
                return 0
        except Exception as e:
            self.logger.error(f"Error retrieving current stock for product {product_id}: {e}")
            return 0

    async def _retrain_models_periodically(self, interval_hours: int = 24):
        """Periodically retrains ML models.

        Args:
            interval_hours (int): The interval in hours between retraining sessions.
        """
        while True:
            await asyncio.sleep(interval_hours * 3600)  # Convert hours to seconds
            self.logger.info(f"Initiating periodic model retraining (every {interval_hours} hours).")
            try:
                await self._retrain_models()
                self.logger.info("Periodic model retraining completed successfully.")
            except Exception as e:
                self.logger.error(f"Periodic model retraining failed: {e}")

    async def _generate_daily_forecasts(self):
        """Generates daily forecasts for all active products.

        This method runs once a day to update forecasts.
        """
        while True:
            # Schedule to run once every 24 hours, e.g., at midnight
            now = datetime.now()
            tomorrow = now + timedelta(days=1)
            midnight = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)
            time_to_wait = (midnight - now).total_seconds()
            self.logger.info(f"Next daily forecast generation scheduled in {time_to_wait / 3600:.2f} hours.")
            await asyncio.sleep(time_to_wait)

            self.logger.info("Initiating daily forecast generation.")
            if not self._db_initialized:
                self.logger.error("Database not initialized. Skipping daily forecast generation.")
                continue

            try:
                async with self.db_manager.get_session() as session:
                    products = await self.db_helper.get_all(session, Product)
                    for product in products:
                        try:
                            forecast_request = {
                                "product_id": product.id,
                                "forecast_days": 30 # Forecast for the next 30 days
                            }
                            forecast_result = await self._forecast_demand(forecast_request)
                            self.logger.info(f"Daily forecast generated for product {product.id}: {forecast_result['predicted_demand']}")
                            # Optionally, save this forecast to the database
                            # forecast_obj = DemandForecastModel(**forecast_result)
                            # await self.db_helper.create(session, forecast_obj)
                        except Exception as product_e:
                            self.logger.warning(f"Failed to generate daily forecast for product {product.id}: {product_e}")
                    await session.commit()
                self.logger.info("Daily forecast generation completed.")
            except Exception as e:
                self.logger.error(f"Daily forecast generation failed: {e}")

    async def _monitor_forecast_accuracy(self, interval_hours: int = 6):
        """Monitors forecast accuracy periodically.

        Args:
            interval_hours (int): The interval in hours between accuracy monitoring sessions.
        """
        while True:
            await asyncio.sleep(interval_hours * 3600)  # Convert hours to seconds
            self.logger.info(f"Initiating periodic forecast accuracy monitoring (every {interval_hours} hours).")
            if not self._db_initialized:
                self.logger.error("Database not initialized. Skipping forecast accuracy monitoring.")
                continue

            try:
                async with self.db_manager.get_session() as session:
                    # Fetch actual sales data for a recent period and compare with past forecasts
                    # This is a simplified example; a real system would store forecasts and actuals
                    products = await self.db_helper.get_all(session, Product)
                    total_mae = 0.0
                    total_mse = 0.0
                    product_count = 0

                    for product in products:
                        try:
                            # Get actual sales for the last 7 days
                            actual_sales_records = await self._get_recent_sales_data(product.id, warehouse_id=None, days=7)
                            if not actual_sales_records: continue

                            actual_sales = np.array([r['sales'] for r in actual_sales_records])

                            # Simulate past forecasts (in a real scenario, retrieve from DB)
                            # For simplicity, let's assume a naive forecast of previous day's sales
                            if len(actual_sales) > 1:
                                predicted_sales = np.roll(actual_sales, 1) # Shift by 1 to simulate previous day's forecast
                                predicted_sales[0] = predicted_sales[1] # Handle the first element

                                mae = mean_absolute_error(actual_sales, predicted_sales)
                                mse = mean_squared_error(actual_sales, predicted_sales)

                                total_mae += mae
                                total_mse += mse
                                product_count += 1
                                self.logger.debug(f"Accuracy for {product.id}: MAE={mae:.2f}, MSE={mse:.2f}")
                        except Exception as product_e:
                            self.logger.warning(f"Error monitoring accuracy for product {product.id}: {product_e}")

                    if product_count > 0:
                        avg_mae = total_mae / product_count
                        avg_mse = total_mse / product_count
                        self.forecast_accuracy_metrics = {
                            "average_mae": avg_mae,
                            "average_mse": avg_mse,
                            "last_monitored_at": datetime.now().isoformat()
                        }
                        self.logger.info(f"Forecast accuracy monitored. Avg MAE: {avg_mae:.2f}, Avg MSE: {avg_mse:.2f}")
                    else:
                        self.logger.info("No products to monitor forecast accuracy for.")
            except Exception as e:
                self.logger.error(f"Forecast accuracy monitoring failed: {e}")

    async def process_message(self, message: AgentMessage):
        """Process incoming messages from other agents or systems.

        Args:
            message (AgentMessage): The incoming message to process.
        """
        self.logger.info(f"Received message: {message.type} from {message.sender_id}")
        try:
            if message.type == MessageType.ORDER_CREATED:
                await self._handle_order_created(message)
            elif message.type == MessageType.INVENTORY_UPDATE:
                await self._handle_inventory_update(message)
            elif message.type == MessageType.PRODUCT_CATALOG_UPDATE:
                await self._handle_product_catalog_update(message)
            else:
                self.logger.warning(f"Unhandled message type: {message.type}")
        except Exception as e:
            self.logger.error(f"Error processing message {message.type} from {message.sender_id}: {e}")

    async def _handle_order_created(self, message: AgentMessage):
        """Handle ORDER_CREATED messages.

        This method processes new order creation events to update historical sales data
        and potentially trigger immediate forecast adjustments.

        Args:
            message (AgentMessage): The ORDER_CREATED message.
        """
        self.logger.info(f"Handling ORDER_CREATED message: {message.payload}")
        if not self._db_initialized:
            self.logger.warning("Database not initialized, cannot handle ORDER_CREATED.")
            return
        try:
            order_data = message.payload # Assuming payload contains order details
            product_id = order_data.get("product_id")
            quantity = order_data.get("quantity")
            warehouse_id = order_data.get("warehouse_id", "unknown")
            order_date = datetime.fromisoformat(order_data["order_date"]) if "order_date" in order_data else datetime.now()

            if product_id and quantity is not None:
                async with self.db_manager.get_session() as session:
                    # Create a new SalesData record
                    new_sales_record = SalesData(
                        product_id=product_id,
                        warehouse_id=warehouse_id,
                        date=order_date,
                        sales=float(quantity),
                        revenue=float(order_data.get("price", 0.0) * quantity), # Assuming price is in payload
                        quantity=quantity,
                        order_id=order_data.get("order_id", str(uuid4()))
                    )
                    await self.db_helper.create(session, new_sales_record)
                    await session.commit()
                    self.logger.info(f"Recorded new sale for product {product_id}, quantity {quantity}.")

                    # Optionally, trigger a micro-retraining or forecast update for this product
                    # await self._train_product_model(product_id, warehouse_id)
            else:
                self.logger.warning(f"ORDER_CREATED message missing product_id or quantity: {message.payload}")
        except Exception as e:
            self.logger.error(f"Error handling ORDER_CREATED message: {e}")

    async def _handle_inventory_update(self, message: AgentMessage):
        """Handle INVENTORY_UPDATE messages.

        This method processes inventory changes to update stock levels in the database.

        Args:
            message (AgentMessage): The INVENTORY_UPDATE message.
        """
        self.logger.info(f"Handling INVENTORY_UPDATE message: {message.payload}")
        if not self._db_initialized:
            self.logger.warning("Database not initialized, cannot handle INVENTORY_UPDATE.")
            return
        try:
            inventory_data = message.payload
            product_id = inventory_data.get("product_id")
            warehouse_id = inventory_data.get("warehouse_id")
            new_stock_level = inventory_data.get("stock_level")

            if product_id and warehouse_id and new_stock_level is not None:
                async with self.db_manager.get_session() as session:
                    # Check if inventory record exists, update or create
                    existing_inventory = await self.db_helper.get_all(session, InventoryData, filters={
                        "product_id": product_id,
                        "warehouse_id": warehouse_id
                    })
                    if existing_inventory:
                        inv_obj = existing_inventory[0]
                        inv_obj.stock_level = new_stock_level
                        inv_obj.last_updated = datetime.now()
                        await self.db_helper.update(session, inv_obj)
                        self.logger.info(f"Updated inventory for product {product_id} in {warehouse_id} to {new_stock_level}.")
                    else:
                        new_inv_record = InventoryData(
                            product_id=product_id,
                            warehouse_id=warehouse_id,
                            stock_level=new_stock_level,
                            last_updated=datetime.now()
                        )
                        await self.db_helper.create(session, new_inv_record)
                        self.logger.info(f"Created new inventory record for product {product_id} in {warehouse_id} with stock {new_stock_level}.")
                    await session.commit()
            else:
                self.logger.warning(f"INVENTORY_UPDATE message missing product_id, warehouse_id or stock_level: {message.payload}")
        except Exception as e:
            self.logger.error(f"Error handling INVENTORY_UPDATE message: {e}")

    async def _handle_product_catalog_update(self, message: AgentMessage):
        """Handle PRODUCT_CATALOG_UPDATE messages.

        This method processes product catalog changes to update product information in the database.

        Args:
            message (AgentMessage): The PRODUCT_CATALOG_UPDATE message.
        """
        self.logger.info(f"Handling PRODUCT_CATALOG_UPDATE message: {message.payload}")
        if not self._db_initialized:
            self.logger.warning("Database not initialized, cannot handle PRODUCT_CATALOG_UPDATE.")
            return
        try:
            product_data = message.payload
            product_id = product_data.get("product_id")

            if product_id:
                async with self.db_manager.get_session() as session:
                    existing_product = await self.db_helper.get_by_id(session, Product, product_id)
                    if existing_product:
                        # Update existing product details
                        for key, value in product_data.items():
                            setattr(existing_product, key, value)
                        await self.db_helper.update(session, existing_product)
                        self.logger.info(f"Updated product {product_id} in catalog.")
                    else:
                        # Create new product
                        new_product = Product(
                            id=product_id,
                            name=product_data.get("name", "Unknown Product"),
                            description=product_data.get("description", ""),
                            price=product_data.get("price", 0.0),
                            category=product_data.get("category", "Unknown"),
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        await self.db_helper.create(session, new_product)
                        self.logger.info(f"Created new product {product_id} in catalog.")
                    await session.commit()
            else:
                self.logger.warning(f"PRODUCT_CATALOG_UPDATE message missing product_id: {message.payload}")
        except Exception as e:
            self.logger.error(f"Error handling PRODUCT_CATALOG_UPDATE message: {e}")


# Main entry point for running the FastAPI app
if __name__ == "__main__":
    # Set up logging for uvicorn
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"

    agent = DemandForecastingAgent()

    # Run the agent's initialize method in an asyncio event loop
    # This is necessary for the agent to connect to the DB and set up models
    loop = asyncio.get_event_loop()
    loop.run_until_complete(agent.initialize())

    # Get port from environment variable, default to 8000
    port = int(os.getenv("AGENT_PORT", 8000))
    host = os.getenv("AGENT_HOST", "0.0.0.0")

    logger.info(f"Starting Demand Forecasting Agent API on {host}:{port}")
    uvicorn.run(agent.app, host=host, port=port, log_config=log_config)

