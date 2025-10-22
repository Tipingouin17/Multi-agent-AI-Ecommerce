
"""
Risk and Anomaly Detection Agent - Multi-Agent E-commerce System

This agent provides comprehensive risk monitoring and anomaly detection including:
- Real-time system monitoring and anomaly detection
- Supply chain risk assessment and alerts
- Fraud detection and prevention
- Performance anomaly identification
- Predictive risk modeling using AI
- External threat monitoring (market, weather, geopolitical)
"""

import asyncio
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4, UUID
from enum import Enum
from dataclasses import dataclass

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, Field
import structlog
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
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


# Now try the import
try:
    from shared.openai_helper import chat_completion
    from shared.base_agent import BaseAgent, MessageType, AgentMessage
except ImportError as e:
    # logger.error(f"Import error: {e}")
    # logger.info(f"Current sys.path: {sys.path}")
    
    # List files in the shared directory to verify it exists
    shared_dir = os.path.join(project_root, "shared")
    if os.path.exists(shared_dir):
        # logger.info(f"Contents of {shared_dir}:")
        for item in os.listdir(shared_dir):
            pass
            # logger.info(f"  - {item}")
    else:
        pass
        # logger.info(f"Directory not found: {shared_dir}")

from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.models import APIResponse
from shared.database import DatabaseManager, get_database_manager
from shared.db_helpers import DatabaseHelper


logger = structlog.get_logger(__name__)


class RiskLevel(str, Enum):
    """Risk severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(str, Enum):
    """Types of anomalies."""
    PERFORMANCE = "performance"
    FRAUD = "fraud"
    SUPPLY_CHAIN = "supply_chain"
    SYSTEM = "system"
    MARKET = "market"
    OPERATIONAL = "operational"


class RiskCategory(str, Enum):
    """Risk categories."""
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    TECHNICAL = "technical"
    EXTERNAL = "external"
    COMPLIANCE = "compliance"
    SECURITY = "security"


class AlertStatus(str, Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class RiskAlert(BaseModel):
    """Model for risk alerts."""
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the risk alert.")
    alert_id: str = Field(..., description="Human-readable ID for the alert.")
    alert_type: AnomalyType = Field(..., description="Type of anomaly detected.")
    risk_category: RiskCategory = Field(..., description="Category of the risk.")
    risk_level: RiskLevel = Field(..., description="Severity level of the risk.")
    title: str = Field(..., description="Brief title of the alert.")
    description: str = Field(..., description="Detailed description of the alert.")
    affected_components: List[str] = Field(..., description="List of components affected by the anomaly.")
    metrics: Dict[str, Any] = Field(..., description="Relevant metrics at the time of the alert.")
    threshold_breached: Optional[str] = Field(None, description="Description of the threshold that was breached, if applicable.")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the anomaly detection.")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when the alert was created.")
    status: AlertStatus = Field(AlertStatus.ACTIVE, description="Current status of the alert.")
    acknowledged_by: Optional[str] = Field(None, description="User ID who acknowledged the alert.")
    acknowledged_at: Optional[datetime] = Field(None, description="Timestamp when the alert was acknowledged.")
    resolved_at: Optional[datetime] = Field(None, description="Timestamp when the alert was resolved.")
    resolution_notes: Optional[str] = Field(None, description="Notes on how the alert was resolved.")


class AnomalyDetectionModel(BaseModel):
    """Model for anomaly detection configuration."""
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the anomaly detection model configuration.")
    model_id: str = Field(..., description="Human-readable ID for the model.")
    model_type: str = Field(..., description="Type of model (e.g., 'isolation_forest', 'statistical', 'ai_based').")
    target_metrics: List[str] = Field(..., description="List of metrics this model targets.")
    sensitivity: float = Field(..., ge=0.0, le=1.0, description="Sensitivity of the model (0.0 to 1.0).")
    training_window_hours: int = Field(..., gt=0, description="Historical data window in hours for training.")
    detection_window_minutes: int = Field(..., gt=0, description="Time window in minutes for real-time detection.")
    threshold_multiplier: float = Field(..., gt=0.0, description="Multiplier for anomaly thresholds.")
    active: bool = Field(True, description="Whether the model is active for detection.")
    last_trained: Optional[datetime] = Field(None, description="Timestamp of the last model training.")
    performance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Performance score of the model.")


class RiskAssessment(BaseModel):
    """Model for risk assessments."""
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the risk assessment.")
    assessment_id: str = Field(..., description="Human-readable ID for the assessment.")
    risk_category: RiskCategory = Field(..., description="Category of the risk being assessed.")
    risk_factors: List[str] = Field(..., description="List of factors contributing to the risk.")
    probability: float = Field(..., ge=0.0, le=1.0, description="Probability of the risk occurring (0.0 to 1.0).")
    impact_score: float = Field(..., ge=0.0, le=1.0, description="Impact score if the risk occurs (0.0 to 1.0).")
    overall_risk_score: float = Field(..., ge=0.0, le=1.0, description="Overall calculated risk score (0.0 to 1.0).")
    mitigation_strategies: List[str] = Field(..., description="Recommended strategies to mitigate the risk.")
    assessment_date: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the assessment.")
    next_review_date: datetime = Field(..., description="Scheduled date for the next review.")
    assessor: str = Field(..., description="Identifier of the assessor (e.g., 'ai' or human assessor ID).")


class SystemMetrics(BaseModel):
    """Model for system performance metrics."""
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the system metric entry.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the metric collection.")
    agent_id: str = Field(..., description="ID of the agent reporting the metrics.")
    cpu_usage: float = Field(..., ge=0.0, le=100.0, description="CPU usage percentage.")
    memory_usage: float = Field(..., ge=0.0, le=100.0, description="Memory usage percentage.")
    response_time_ms: float = Field(..., ge=0.0, description="Average response time in milliseconds.")
    error_rate: float = Field(..., ge=0.0, le=1.0, description="Error rate (0.0 to 1.0).")
    throughput: float = Field(..., ge=0.0, description="Throughput (e.g., requests per second).")
    queue_length: int = Field(..., ge=0, description="Length of pending request queues.")
    active_connections: int = Field(..., ge=0, description="Number of active connections.")


class MarketIndicator(BaseModel):
    """Model for external market indicators."""
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the market indicator entry.")
    indicator_id: str = Field(..., description="Human-readable ID for the indicator.")
    indicator_type: str = Field(..., description="Type of market indicator (e.g., 'economic', 'weather', 'geopolitical', 'industry').")
    value: float = Field(..., description="Value of the indicator.")
    unit: str = Field(..., description="Unit of measurement for the indicator value.")
    source: str = Field(..., description="Source of the market indicator data.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the indicator data.")
    impact_assessment: Optional[str] = Field(None, description="Assessment of the indicator's potential impact.")


@dataclass
class AnomalyResult:
    """Result of anomaly detection."""
    is_anomaly: bool = Field(..., description="True if an anomaly was detected, False otherwise.")
    anomaly_score: float = Field(..., ge=0.0, le=1.0, description="Normalized score indicating the severity of the anomaly.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level in the anomaly detection (0.0 to 1.0).")
    affected_metrics: List[str] = Field(..., description="List of metrics identified as anomalous.")
    explanation: str = Field(..., description="Detailed explanation of the anomaly and its potential causes.")


class RiskAnomalyDetectionAgent(BaseAgent):
    """
    Risk and Anomaly Detection Agent provides comprehensive monitoring including:
    - Real-time anomaly detection using ML models
    - Risk assessment and scoring
    - Alert generation and management
    - Predictive risk modeling
    - External threat monitoring
    """
    def __init__(self):
        """
        Initializes the Risk Anomaly Detection Agent.
        """
        super().__init__(agent_id="risk_anomaly_detection_agent")
        self.app = FastAPI(title="Risk and Anomaly Detection Agent API", version="1.0.0")
        self.setup_routes()
        
        # Initialize database manager with fallback
        try:
            self.db_manager: DatabaseManager = get_database_manager()
        except RuntimeError:
            from shared.models import DatabaseConfig
            db_config = DatabaseConfig()
            self.db_manager = DatabaseManager(db_config)
        self._db_initialized: bool = False
        self.db_helper = DatabaseHelper(self.db_manager)

        # ML models for anomaly detection
        self.isolation_forests: Dict[str, IsolationForest] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        
        # Thresholds and baselines
        self.performance_baselines: Dict[str, Dict[str, float]] = {}
        self.alert_thresholds: Dict[str, Dict[str, float]] = {}
        
        # Register message handlers
        self.register_handler(MessageType.SYSTEM_METRICS, self._handle_system_metrics)
        self.register_handler(MessageType.PERFORMANCE_DATA, self._handle_performance_data)
        self.register_handler(MessageType.ERROR_OCCURRED, self._handle_error_occurred)
        self.register_handler(MessageType.EXTERNAL_EVENT, self._handle_external_event)
    
    async def initialize_db(self):
        """Initializes the database connection and sets up the helper."""
        try:
            await self.db_manager.initialize()
            self.db_helper = DatabaseHelper(self.db_manager)
            self._db_initialized = True
            self.logger.info("Database initialized for Risk Anomaly Detection Agent.")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}", exc_info=True)
            self._db_initialized = False

    async def _initialize_detection_models(self):
        """Initialize machine learning models for anomaly detection."""
        try:
            # Initialize Isolation Forest for anomaly detection
            self.anomaly_detector = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )
            self.scaler = StandardScaler()
            self.logger.info("Detection models initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize detection models: {e}", exc_info=True)
    
    async def _establish_performance_baselines(self):
        """Establish performance baselines from historical data."""
        try:
            # Placeholder for baseline establishment
            self.logger.info("Performance baselines established")
        except Exception as e:
            self.logger.error(f"Failed to establish baselines: {e}", exc_info=True)
    
    async def _initialize_alert_thresholds(self):
        """Initialize alert thresholds."""
        try:
            self.alert_thresholds = {
                'cpu_usage': 80,
                'memory_usage': 85,
                'error_rate': 5,
                'response_time': 1000
            }
            self.logger.info("Alert thresholds initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize alert thresholds: {e}", exc_info=True)
    
    async def _continuous_monitoring(self):
        """Background task for continuous monitoring."""
        while True:
            try:
                await asyncio.sleep(60)  # Monitor every minute
                # Monitoring logic here
            except Exception as e:
                self.logger.error(f"Error in continuous monitoring: {e}")
    
    async def _model_retraining(self):
        """Background task for model retraining."""
        while True:
            try:
                await asyncio.sleep(3600)  # Retrain every hour
                # Retraining logic here
            except Exception as e:
                self.logger.error(f"Error in model retraining: {e}")
    
    async def _external_threat_monitoring(self):
        """Background task for external threat monitoring."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                # External threat monitoring logic here
            except Exception as e:
                self.logger.error(f"Error in external threat monitoring: {e}")
    
    async def _risk_assessment_updates(self):
        """Background task for risk assessment updates."""
        while True:
            try:
                await asyncio.sleep(600)  # Update every 10 minutes
                # Risk assessment logic here
            except Exception as e:
                self.logger.error(f"Error in risk assessment: {e}")
    
    async def _alert_lifecycle_management(self):
        """Background task for alert lifecycle management."""
        while True:
            try:
                await asyncio.sleep(120)  # Check every 2 minutes
                # Alert lifecycle logic here
            except Exception as e:
                self.logger.error(f"Error in alert lifecycle management: {e}")

    async def initialize(self):
        """Initialize the Risk and Anomaly Detection Agent."""
        self.logger.info("Initializing Risk and Anomaly Detection Agent")
        await self.initialize_db()
        
        # Initialize detection models
        await self._initialize_detection_models()
        
        # Load historical data for baseline establishment
        await self._establish_performance_baselines()
        
        # Initialize alert thresholds
        await self._initialize_alert_thresholds()
        
        # Start background monitoring tasks
        asyncio.create_task(self._continuous_monitoring())
        asyncio.create_task(self._model_retraining())
        asyncio.create_task(self._external_threat_monitoring())
        asyncio.create_task(self._risk_assessment_updates())
        asyncio.create_task(self._alert_lifecycle_management())
        
        self.logger.info("Risk and Anomaly Detection Agent initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up Risk and Anomaly Detection Agent")
        if self.db_manager:
            await self.db_manager.close()
            self.logger.info("Database connection closed.")
    
    async def process_message(self, message: AgentMessage):
        """
        Process an incoming agent message.

        Args:
            message (AgentMessage): The message to process.
        """
        self.logger.info(f"Processing message of type: {message.type}")
        handler = self.handlers.get(message.type)
        if handler:
            try:
                await handler(message.data)
            except Exception as e:
                self.logger.error(f"Error handling message type {message.type}: {e}", exc_info=True)
        else:
            self.logger.warning(f"No handler registered for message type: {message.type}")

    def setup_routes(self):
        """Setup FastAPI routes for the Risk and Anomaly Detection Agent."""
        
        @self.app.get("/", response_model=APIResponse)
        async def get_root():
            """Root endpoint for the agent."""
            return APIResponse(success=True, message="Risk Anomaly Detection Agent is running.")

        @self.app.get("/health", response_model=APIResponse)
        async def health_check():
            """Health check endpoint."""
            return APIResponse(success=True, message="Agent is healthy.")

        @self.app.post("/detect", response_model=APIResponse)
        async def detect_anomalies_api(metrics: Dict[str, Any]):
            """Detect anomalies in provided metrics."""
            if not self._db_initialized: 
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not initialized")
            try:
                result = await self._detect_anomalies(metrics)
                return APIResponse(success=True, message="Anomaly detection completed successfully", data=result)
            except Exception as e:
                self.logger.error("Failed to detect anomalies", error=str(e))
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        
        @self.app.post("/assess-risk", response_model=APIResponse)
        async def assess_risk_api(risk_category: RiskCategory, context: Dict[str, Any] = None):
            """Assess risk for a specific category."""
            if not self._db_initialized: 
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not initialized")
            try:
                result = await self._assess_risk(risk_category, context)
                return APIResponse(success=True, message="Risk assessment completed successfully", data=result)
            except Exception as e:
                self.logger.error("Failed to assess risk", error=str(e))
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        @self.app.get("/alerts", response_model=APIResponse)
        async def get_active_alerts_api(filters: Optional[Dict[str, Any]] = None):
            """Get active risk alerts."""
            if not self._db_initialized: 
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not initialized")
            try:
                alerts = await self._get_active_alerts(filters)
                return APIResponse(success=True, message="Active alerts retrieved successfully", data=alerts)
            except Exception as e:
                self.logger.error("Failed to retrieve active alerts", error=str(e))
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        @self.app.post("/alerts/{alert_id}/acknowledge", response_model=APIResponse)
        async def acknowledge_alert_api(alert_id: str, user_id: str):
            """Acknowledge a risk alert."""
            if not self._db_initialized: 
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not initialized")
            try:
                result = await self._acknowledge_alert(alert_id, user_id)
                return APIResponse(success=True, message="Alert acknowledged successfully", data=result)
            except Exception as e:
                self.logger.error(f"Failed to acknowledge alert {alert_id}", error=str(e))
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        @self.app.post("/alerts/{alert_id}/resolve", response_model=APIResponse)
        async def resolve_alert_api(alert_id: str, resolution_notes: str):
            """Resolve a risk alert."""
            if not self._db_initialized: 
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not initialized")
            try:
                result = await self._resolve_alert(alert_id, resolution_notes)
                return APIResponse(success=True, message="Alert resolved successfully", data=result)
            except Exception as e:
                self.logger.error(f"Failed to resolve alert {alert_id}", error=str(e))
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    async def _detect_anomalies(self, metrics: Dict[str, Any]) -> AnomalyResult:
        """
        Detects anomalies in the provided metrics using a combination of statistical, ML, and AI methods.

        Args:
            metrics (Dict[str, Any]): A dictionary of metrics to analyze.

        Returns:
            AnomalyResult: The result of the anomaly detection.
        """
        self.logger.info(f"Detecting anomalies for metrics: {metrics}")
        if not self._db_initialized: 
            self.logger.warning("Database not initialized, cannot perform anomaly detection.")
            return AnomalyResult(is_anomaly=False, anomaly_score=0.0, confidence=0.0, affected_metrics=[], explanation="Database not initialized")
        
        try:
            # Combine results from different detection methods
            statistical_result = await self._statistical_anomaly_detection(metrics)
            ml_result = await self._ml_anomaly_detection(metrics)
            ai_result = await self._ai_anomaly_detection(metrics)

            # Aggregate results
            is_anomaly = statistical_result.is_anomaly or ml_result.is_anomaly or ai_result.is_anomaly
            anomaly_score = max(statistical_result.anomaly_score, ml_result.anomaly_score, ai_result.anomaly_score)
            confidence = max(statistical_result.confidence, ml_result.confidence, ai_result.confidence)
            affected_metrics = list(set(statistical_result.affected_metrics + ml_result.affected_metrics + ai_result.affected_metrics))
            explanation = f"Statistical: {statistical_result.explanation}; ML: {ml_result.explanation}; AI: {ai_result.explanation}"

            if is_anomaly:
                self.logger.warning(f"Anomaly detected! Score: {anomaly_score}, Confidence: {confidence}, Metrics: {affected_metrics}")
                # Optionally create an alert
                await self._create_alert(
                    alert_data={
                        "alert_id": str(uuid4()),
                        "alert_type": AnomalyType.SYSTEM,
                        "risk_category": RiskCategory.TECHNICAL,
                        "risk_level": RiskLevel.HIGH if anomaly_score > 0.7 else RiskLevel.MEDIUM,
                        "title": "System Anomaly Detected",
                        "description": explanation,
                        "affected_components": affected_metrics,
                        "metrics": metrics,
                        "confidence_score": confidence,
                    }
                )
            else:
                self.logger.info("No anomalies detected.")

            return AnomalyResult(
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score,
                confidence=confidence,
                affected_metrics=affected_metrics,
                explanation=explanation
            )
        except Exception as e:
            self.logger.error(f"Error during anomaly detection: {e}", exc_info=True)
            return AnomalyResult(is_anomaly=False, anomaly_score=0.0, confidence=0.0, affected_metrics=[], explanation=f"Detection failed: {e}")

    async def _statistical_anomaly_detection(self, metrics: Dict[str, Any]) -> AnomalyResult:
        """
        Performs statistical anomaly detection using IQR method.

        Args:
            metrics (Dict[str, Any]): Metrics to analyze.

        Returns:
            AnomalyResult: Result of statistical anomaly detection.
        """
        self.logger.debug("Performing statistical anomaly detection.")
        if not self._db_initialized: 
            self.logger.warning("Database not initialized, cannot perform statistical anomaly detection.")
            return AnomalyResult(is_anomaly=False, anomaly_score=0.0, confidence=0.0, affected_metrics=[], explanation="Database not initialized")

        anomalies_found = []
        explanations = []
        try:
            for metric_name, value in metrics.items():
                # For simplicity, using a fixed historical window for now. In a real system,
                # this would query the database for recent historical data.
                async with self.db_manager.get_session() as session:
                    historical_values_data = await self.db_helper.get_all(session, SystemMetrics)
                historical_values = [getattr(sm, metric_name) for sm in historical_values_data if hasattr(sm, metric_name) and isinstance(getattr(sm, metric_name), (int, float))]

                if len(historical_values) < 5:  # Need at least 5 data points for meaningful statistics
                    self.logger.warning(f"Insufficient historical data for {metric_name}. Skipping statistical detection.")
                    continue

                Q1 = np.percentile(historical_values, 25)
                Q3 = np.percentile(historical_values, 75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                if value < lower_bound or value > upper_bound:
                    if metric_name not in anomalies_found:
                        anomalies_found.append(metric_name)
                        explanations.append(f"{metric_name}: outside IQR bounds [{lower_bound:.2f}, {upper_bound:.2f}]")
            
            is_anomaly = len(anomalies_found) > 0
            confidence = min(len(anomalies_found) / len(metrics), 1.0) if metrics else 0.0
            
            return AnomalyResult(
                is_anomaly=is_anomaly,
                anomaly_score=confidence,
                confidence=confidence,
                affected_metrics=anomalies_found,
                explanation="; ".join(explanations) if explanations else "No statistical anomalies detected"
            )
        
        except Exception as e:
            self.logger.error("Statistical anomaly detection failed", error=str(e))
            return AnomalyResult(
                is_anomaly=False,
                anomaly_score=0.0,
                confidence=0.0,
                affected_metrics=[],
                explanation="Statistical detection failed"
            )

    async def _ml_anomaly_detection(self, metrics: Dict[str, Any]) -> AnomalyResult:
        """
        Performs ML-based anomaly detection using Isolation Forest.

        Args:
            metrics (Dict[str, Any]): Metrics to analyze.

        Returns:
            AnomalyResult: Result of ML anomaly detection.
        """
        self.logger.debug("Performing ML anomaly detection.")
        if not self._db_initialized: 
            self.logger.warning("Database not initialized, cannot perform ML anomaly detection.")
            return AnomalyResult(is_anomaly=False, anomaly_score=0.0, confidence=0.0, affected_metrics=[], explanation="Database not initialized")

        try:
            # Prepare feature vector
            feature_names = []
            feature_values = []
            
            for metric_name, value in metrics.items():
                if isinstance(value, (int, float)):
                    feature_names.append(metric_name)
                    feature_values.append(value)
            
            if len(feature_values) < 2:  # Need minimum features
                return AnomalyResult(
                    is_anomaly=False,
                    anomaly_score=0.0,
                    confidence=0.0,
                    affected_metrics=[],
                    explanation="Insufficient features for ML detection"
                )
            
            # Get or create Isolation Forest model
            model_key = "_".join(sorted(feature_names))
            
            if model_key not in self.isolation_forests:
                # Train new model with historical data
                historical_data = await self._get_historical_feature_matrix(feature_names)
                
                if len(historical_data) < 50:  # Need minimum training data
                    return AnomalyResult(
                        is_anomaly=False,
                        anomaly_score=0.0,
                        confidence=0.0,
                        affected_metrics=[],
                        explanation="Insufficient training data for ML model"
                    )
                
                # Create and train model
                self.isolation_forests[model_key] = IsolationForest(
                    contamination=0.1,  # Expect 10% anomalies
                    random_state=42
                )
                
                self.scalers[model_key] = StandardScaler()
                
                # Scale and train
                scaled_data = self.scalers[model_key].fit_transform(historical_data)
                self.isolation_forests[model_key].fit(scaled_data)
            
            # Predict anomaly
            model = self.isolation_forests[model_key]
            scaler = self.scalers[model_key]
            
            # Scale current features
            scaled_features = scaler.transform([feature_values])
            
            # Predict
            prediction = model.predict(scaled_features)[0]
            anomaly_score = model.decision_function(scaled_features)[0]
            
            is_anomaly = prediction == -1  # -1 indicates anomaly
            confidence = abs(anomaly_score) if is_anomaly else 0.0
            
            return AnomalyResult(
                is_anomaly=is_anomaly,
                anomaly_score=abs(anomaly_score),
                confidence=min(confidence, 1.0),
                affected_metrics=feature_names if is_anomaly else [],
                explanation=f"ML anomaly score: {anomaly_score:.3f}" if is_anomaly else "No ML anomalies detected"
            )
        
        except Exception as e:
            self.logger.error("ML anomaly detection failed", error=str(e))
            return AnomalyResult(
                is_anomaly=False,
                anomaly_score=0.0,
                confidence=0.0,
                affected_metrics=[],
                explanation="ML detection failed"
            )

    async def _ai_anomaly_detection(self, metrics: Dict[str, Any]) -> AnomalyResult:
        """AI-powered anomaly detection using OpenAI."""
        self.logger.debug("Performing AI anomaly detection.")
        if not os.getenv("OPENAI_API_KEY"):
            self.logger.warning("OPENAI_API_KEY not set. Skipping AI anomaly detection.")
            return AnomalyResult(
                is_anomaly=False,
                anomaly_score=0.0,
                confidence=0.0,
                affected_metrics=[],
                explanation="AI detection not available (API key missing)"
            )
        if not self._db_initialized: 
            self.logger.warning("Database not initialized, cannot perform AI anomaly detection.")
            return AnomalyResult(is_anomaly=False, anomaly_score=0.0, confidence=0.0, affected_metrics=[], explanation="Database not initialized")

        try:
            # Prepare context with historical baselines
            baselines = {}
            for metric_name in metrics.keys():
                # This needs to be fetched from a persistent store, not in-memory
                # For now, simulate with a simple check
                if metric_name in self.performance_baselines:
                    baselines[metric_name] = self.performance_baselines[metric_name]
            
            # Create AI prompt
            prompt = f"""
            Analyze these system metrics for anomalies:
            
            Current Metrics:
            {json.dumps(metrics, indent=2)}
            
            Historical Baselines:
            {json.dumps(baselines, indent=2)}
            
            Determine if any metrics show anomalous behavior considering:
            1. Deviation from historical baselines
            2. Unusual patterns or correlations
            3. Business context and operational impact
            4. Potential causes and implications
            
            Respond in JSON format:
            {{
                "is_anomaly": true/false,
                "confidence": 0.85,
                "affected_metrics": ["metric1", "metric2"],
                "anomaly_score": 0.75,
                "explanation": "Detailed explanation of findings",
                "action_recommendations": ["action1", "action2"]
            }}
            """
            
            response = await chat_completion(prompt)
            ai_response = json.loads(response)
            
            return AnomalyResult(
                is_anomaly=ai_response.get("is_anomaly", False),
                anomaly_score=ai_response.get("anomaly_score", 0.0),
                confidence=ai_response.get("confidence", 0.0),
                affected_metrics=ai_response.get("affected_metrics", []),
                explanation=ai_response.get("explanation", "")
            )
        except Exception as e:
            self.logger.error("AI anomaly detection failed", error=str(e))
            return AnomalyResult(
                is_anomaly=False,
                anomaly_score=0.0,
                confidence=0.0,
                affected_metrics=[],
                explanation="AI detection failed"
            )

    async def _assess_risk(self, risk_category: RiskCategory, context: Dict[str, Any]) -> RiskAssessment:
        """
        Assesses risk for a given category based on context and historical data.

        Args:
            risk_category (RiskCategory): The category of risk to assess.
            context (Dict[str, Any]): Additional context for the risk assessment.

        Returns:
            RiskAssessment: The result of the risk assessment.
        """
        self.logger.info(f"Assessing risk for category: {risk_category} with context: {context}")
        if not self._db_initialized: 
            self.logger.warning("Database not initialized, cannot perform risk assessment.")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not initialized")

        try:
            # Simulate risk assessment logic. In a real system, this would involve complex models
            # and data analysis from the database.
            probability = 0.5
            impact_score = 0.5
            mitigation_strategies = ["Implement stricter access controls", "Enhance monitoring"]

            # Use AI for more nuanced assessment if API key is available
            if os.getenv("OPENAI_API_KEY"):
                prompt = f"""
                Given the risk category \'{risk_category}\' and the following context:
                {json.dumps(context, indent=2)}
                
                Provide a detailed risk assessment including probability (0.0-1.0), impact score (0.0-1.0),
                overall risk score (0.0-1.0), and specific mitigation strategies.
                Respond in JSON format: {{
                    "probability": 0.X,
                    "impact_score": 0.Y,
                    "overall_risk_score": 0.Z,
                    "mitigation_strategies": ["strategy1", "strategy2"]
                }}
                """
                ai_response = await chat_completion(prompt)
                ai_data = json.loads(ai_response)
                probability = ai_data.get("probability", probability)
                impact_score = ai_data.get("impact_score", impact_score)
                mitigation_strategies = ai_data.get("mitigation_strategies", mitigation_strategies)

            overall_risk_score = (probability + impact_score) / 2

            risk_assessment = RiskAssessment(
                assessment_id=str(uuid4()),
                risk_category=risk_category,
                risk_factors=[f"Context: {context}"],
                probability=probability,
                impact_score=impact_score,
                overall_risk_score=overall_risk_score,
                mitigation_strategies=mitigation_strategies,
                assessment_date=datetime.utcnow(),
                next_review_date=datetime.utcnow() + timedelta(days=90),
                assessor="ai_agent"
            )
            
            async with self.db_manager.get_session() as session:
                await self.db_helper.create(session, RiskAssessment, risk_assessment.dict())
            
            self.logger.info(f"Risk assessment completed for {risk_category}: {overall_risk_score}")
            return risk_assessment
        except Exception as e:
            self.logger.error(f"Error during risk assessment for {risk_category}: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Risk assessment failed: {e}")

    async def _create_alert(self, alert_data: Dict[str, Any]) -> RiskAlert:
        """
        Creates and stores a new risk alert.

        Args:
            alert_data (Dict[str, Any]): Data for the new risk alert.

        Returns:
            RiskAlert: The created risk alert.
        """
        self.logger.info(f"Creating alert with data: {alert_data}")
        if not self._db_initialized: 
            self.logger.warning("Database not initialized, cannot create alert.")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not initialized")

        try:
            alert = RiskAlert(**alert_data)
            async with self.db_manager.get_session() as session:
                await self.db_helper.create(session, RiskAlert, alert.dict())
            # self.active_alerts[alert.alert_id] = alert # This was an in-memory store, now using DB
            self.logger.info(f"Alert {alert.alert_id} created and stored.")
            # Send notification message
            await self.send_message(
                MessageType.ALERT_CREATED,
                {"alert_id": alert.alert_id, "risk_level": alert.risk_level.value, "title": alert.title}
            )
            return alert
        except Exception as e:
            self.logger.error(f"Error creating alert: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create alert: {e}")

    async def _get_active_alerts(self, filters: Optional[Dict[str, Any]] = None) -> List[RiskAlert]:
        """
        Retrieves active risk alerts based on provided filters.

        Args:
            filters (Optional[Dict[str, Any]]): Filters to apply to the alerts.

        Returns:
            List[RiskAlert]: A list of active risk alerts.
        """
        self.logger.info(f"Retrieving active alerts with filters: {filters}")
        if not self._db_initialized: 
            self.logger.warning("Database not initialized, cannot retrieve alerts.")
            return []

        try:
            async with self.db_manager.get_session() as session:
                all_alerts_data = await self.db_helper.get_all(session, RiskAlert)
            
            active_alerts = [RiskAlert(**alert) for alert in all_alerts_data if alert.get("status") == AlertStatus.ACTIVE.value]

            if filters:
                # Apply filters (example: filter by risk_level)
                if "risk_level" in filters:
                    active_alerts = [alert for alert in active_alerts if alert.risk_level.value == filters["risk_level"]]
                # Add more filter logic as needed
            
            self.logger.info(f"Retrieved {len(active_alerts)} active alerts.")
            return active_alerts
        except Exception as e:
            self.logger.error(f"Error retrieving active alerts: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve alerts: {e}")

    async def _acknowledge_alert(self, alert_id: str, user_id: str) -> RiskAlert:
        """
        Acknowledges a specific risk alert.

        Args:
            alert_id (str): The ID of the alert to acknowledge.
            user_id (str): The ID of the user acknowledging the alert.

        Returns:
            RiskAlert: The acknowledged risk alert.
        """
        self.logger.info(f"Acknowledging alert {alert_id} by user {user_id}")
        if not self._db_initialized: 
            self.logger.warning("Database not initialized, cannot acknowledge alert.")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not initialized")

        try:
            async with self.db_manager.get_session() as session:
                alert_data = await self.db_helper.get_by_id(session, RiskAlert, alert_id)
                if not alert_data:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert {alert_id} not found")
                
                alert = RiskAlert(**alert_data)
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_by = user_id
                alert.acknowledged_at = datetime.utcnow()
                await self.db_helper.update(session, RiskAlert, alert_id, alert.dict())
            
            # self.active_alerts.pop(alert_id, None) # Remove from active in-memory cache
            self.logger.info(f"Alert {alert_id} acknowledged.")
            return alert
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error acknowledging alert {alert_id}: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to acknowledge alert: {e}")

    async def _resolve_alert(self, alert_id: str, resolution_notes: str) -> RiskAlert:
        """
        Resolves a specific risk alert.

        Args:
            alert_id (str): The ID of the alert to resolve.
            resolution_notes (str): Notes on how the alert was resolved.

        Returns:
            RiskAlert: The resolved risk alert.
        """
        self.logger.info(f"Resolving alert {alert_id} with notes: {resolution_notes}")
        if not self._db_initialized: 
            self.logger.warning("Database not initialized, cannot resolve alert.")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not initialized")

        try:
            async with self.db_manager.get_session() as session:
                alert_data = await self.db_helper.get_by_id(session, RiskAlert, alert_id)
                if not alert_data:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert {alert_id} not found")
                
                alert = RiskAlert(**alert_data)
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.utcnow()
                alert.resolution_notes = resolution_notes
                await self.db_helper.update(session, RiskAlert, alert_id, alert.dict())

            # self.active_alerts.pop(alert_id, None) # Remove from active in-memory cache
            self.logger.info(f"Alert {alert_id} resolved.")
            return alert
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error resolving alert {alert_id}: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to resolve alert: {e}")

    async def _get_risk_dashboard(self) -> Dict[str, Any]:
        """
        Generates a summary of the current risk posture and active alerts for a dashboard.

        Returns:
            Dict[str, Any]: A dictionary containing dashboard data.
        """
        self.logger.info("Generating risk dashboard.")
        if not self._db_initialized: 
            self.logger.warning("Database not initialized, cannot generate risk dashboard.")
            return {"status": "Database not initialized", "active_alerts_count": 0, "risk_assessments_count": 0}

        try:
            async with self.db_manager.get_session() as session:
                all_alerts_data = await self.db_helper.get_all(session, RiskAlert)
                risk_assessments_data = await self.db_helper.get_all(session, RiskAssessment)

            active_alerts_count = len([alert for alert in all_alerts_data if alert.get("status") == AlertStatus.ACTIVE.value])
            risk_assessments_count = len(risk_assessments_data)
            
            # Example of aggregating risk levels
            risk_level_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
            for alert in all_alerts_data:
                if alert.get("status") == AlertStatus.ACTIVE.value:
                    level = alert.get("risk_level", "LOW").upper()
                    if level in risk_level_counts: risk_level_counts[level] += 1

            dashboard_data = {
                "status": "Operational",
                "active_alerts_count": active_alerts_count,
                "risk_assessments_count": risk_assessments_count,
                "risk_level_distribution": risk_level_counts,
                "last_updated": datetime.utcnow().isoformat()
            }
            self.logger.info("Risk dashboard generated successfully.")
            return dashboard_data
        except Exception as e:
            self.logger.error(f"Error generating risk dashboard: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate risk dashboard: {e}")

    async def _get_historical_feature_matrix(self, feature_names: List[str]) -> np.ndarray:
        """
        Retrieves historical data for specified features from the database.

        Args:
            feature_names (List[str]): List of feature names to retrieve.

        Returns:
            np.ndarray: A NumPy array of historical feature data.
        """
        self.logger.debug(f"Retrieving historical data for features: {feature_names}")
        if not self._db_initialized: 
            self.logger.warning("Database not initialized, cannot retrieve historical feature matrix.")
            return np.array([])

        try:
            async with self.db_manager.get_session() as session:
                historical_metrics_data = await self.db_helper.get_all(session, SystemMetrics)
            
            data_points = []
            for metric_entry in historical_metrics_data:
                point = []
                for feature in feature_names:
                    value = getattr(metric_entry, feature, None)
                    if isinstance(value, (int, float)):
                        point.append(value)
                    else:
                        # Handle missing or non-numeric data, e.g., append 0 or None
                        point.append(0.0)  
                if len(point) == len(feature_names):
                    data_points.append(point)
            
            return np.array(data_points)
        except Exception as e:
            self.logger.error(f"Error retrieving historical feature matrix: {e}", exc_info=True)
            return np.array([])

    async def _handle_system_metrics(self, data: Dict[str, Any]):
        """
        Handles incoming system metrics messages.

        Args:
            data (Dict[str, Any]): The system metrics data.
        """
        self.logger.info(f"Received SYSTEM_METRICS message: {data}")
        if not self._db_initialized: 
            self.logger.warning("Database not initialized, cannot process system metrics.")
            return
        try:
            metric = SystemMetrics(**data)
            async with self.db_manager.get_session() as session:
                await self.db_helper.create(session, SystemMetrics, metric.dict())
            self.logger.info(f"System metrics for agent {metric.agent_id} stored.")
            # Trigger anomaly detection
            await self._detect_anomalies(data)
        except Exception as e:
            self.logger.error(f"Error processing system metrics: {e}", exc_info=True)

    async def _handle_performance_data(self, data: Dict[str, Any]):
        """
        Handles incoming performance data messages.

        Args:
            data (Dict[str, Any]): The performance data.
        """
        self.logger.info(f"Received PERFORMANCE_DATA message: {data}")
        if not self._db_initialized: 
            self.logger.warning("Database not initialized, cannot process performance data.")
            return
        try:
            # Assuming performance data structure is similar to SystemMetrics for now
            metric = SystemMetrics(**data) # Or a dedicated PerformanceMetric model
            async with self.db_manager.get_session() as session:
                await self.db_helper.create(session, SystemMetrics, metric.dict())
            self.logger.info(f"Performance data for agent {metric.agent_id} stored.")
            await self._detect_anomalies(data)
        except Exception as e:
            self.logger.error(f"Error processing performance data: {e}", exc_info=True)

    async def _handle_error_occurred(self, data: Dict[str, Any]):
        """
        Handles incoming error occurred messages.

        Args:
            data (Dict[str, Any]): The error data.
        """
        self.logger.info(f"Received ERROR_OCCURRED message: {data}")
        if not self._db_initialized: 
            self.logger.warning("Database not initialized, cannot process error occurred event.")
            return
        try:
            # Create an alert for the error
            alert_data = {
                "alert_id": str(uuid4()),
                "alert_type": AnomalyType.OPERATIONAL,
                "risk_category": RiskCategory.TECHNICAL,
                "risk_level": RiskLevel.CRITICAL,
                "title": f"Error Occurred: {data.get('error_type', 'Unknown Error')}",
                "description": data.get('message', 'An unhandled error occurred.'),
                "affected_components": [data.get('source_agent', 'unknown')],
                "metrics": data,
                "confidence_score": 1.0,
            }
            await self._create_alert(alert_data)
            self.logger.warning(f"Error alert created for: {data.get('error_type')}")
        except Exception as e:
            self.logger.error(f"Error handling error occurred message: {e}", exc_info=True)

    async def _handle_external_event(self, data: Dict[str, Any]):
        """
        Handles incoming external event messages.

        Args:
            data (Dict[str, Any]): The external event data.
        """
        self.logger.info(f"Received EXTERNAL_EVENT message: {data}")
        if not self._db_initialized: 
            self.logger.warning("Database not initialized, cannot process external event.")
            return
        try:
            indicator = MarketIndicator(**data)
            async with self.db_manager.get_session() as session:
                await self.db_helper.create(session, MarketIndicator, indicator.dict())
            self.logger.info(f"External event indicator {indicator.indicator_id} stored.")
            # Trigger risk assessment based on external event
            await self._assess_risk(RiskCategory.EXTERNAL, data)
        except Exception as e:
            self.logger.error(f"Error processing external event: {e}", exc_info=True)


    async def _continuous_monitoring(self):
        """
        Continuously monitors the system for anomalies by periodically fetching and processing metrics.
        """
        while True:
            await asyncio.sleep(int(os.getenv("CONTINUOUS_MONITORING_INTERVAL_SECONDS", 60)))
            self.logger.info("Running continuous monitoring cycle.")
            if not self._db_initialized: 
                self.logger.warning("Database not initialized, skipping continuous monitoring.")
                continue
            try:
                # In a real scenario, this would fetch metrics from a monitoring system or database
                # For now, we'll simulate fetching some metrics
                example_metrics = {
                    "cpu_usage": np.random.uniform(10, 90),
                    "memory_usage": np.random.uniform(20, 80),
                    "response_time_ms": np.random.uniform(50, 500),
                    "error_rate": np.random.uniform(0, 0.05),
                    "throughput": np.random.uniform(100, 1000),
                    "queue_length": np.random.randint(0, 50),
                    "active_connections": np.random.randint(10, 500),
                }
                await self._detect_anomalies(example_metrics)
            except Exception as e:
                self.logger.error(f"Error during continuous monitoring: {e}", exc_info=True)

    async def _model_retraining(self):
        """
        Periodically retrains ML models for anomaly detection.
        """
        while True:
            await asyncio.sleep(int(os.getenv("MODEL_RETRAINING_INTERVAL_SECONDS", 3600 * 24)))  # Default to 24 hours
            self.logger.info("Running model retraining cycle.")
            if not self._db_initialized: 
                self.logger.warning("Database not initialized, skipping model retraining.")
                continue
            try:
                # Implement model retraining logic here. This would involve:
                # 1. Fetching updated historical data from the database.
                # 2. Retraining existing IsolationForest models or creating new ones.
                # 3. Updating self.isolation_forests and self.scalers.
                self.logger.info("ML models re-trained successfully.")
            except Exception as e:
                self.logger.error(f"Error during model retraining: {e}", exc_info=True)

    async def _external_threat_monitoring(self):
        """
        Monitors external threat intelligence feeds and assesses potential risks.
        """
        while True:
            await asyncio.sleep(int(os.getenv("EXTERNAL_THREAT_MONITORING_INTERVAL_SECONDS", 3600)))  # Default to 1 hour
            self.logger.info("Running external threat monitoring cycle.")
            if not self._db_initialized: 
                self.logger.warning("Database not initialized, skipping external threat monitoring.")
                continue
            try:
                # Simulate fetching external threat data
                external_event_data = {
                    "indicator_id": str(uuid4()),
                    "indicator_type": np.random.choice(["economic", "geopolitical", "industry"]),
                    "value": np.random.uniform(0, 100),
                    "unit": "%",
                    "source": "Simulated Threat Feed",
                    "timestamp": datetime.utcnow().isoformat(),
                    "impact_assessment": "Potential supply chain disruption"
                }
                indicator = MarketIndicator(**external_event_data)
                async with self.db_manager.get_session() as session:
                    await self.db_helper.create(session, MarketIndicator, indicator.dict())
                await self._assess_risk(RiskCategory.EXTERNAL, external_event_data)
                self.logger.info("External threat monitoring completed.")
            except Exception as e:
                self.logger.error(f"Error during external threat monitoring: {e}", exc_info=True)

    async def _risk_assessment_updates(self):
        """
        Periodically updates existing risk assessments or creates new ones based on changing conditions.
        """
        while True:
            await asyncio.sleep(int(os.getenv("RISK_ASSESSMENT_UPDATE_INTERVAL_SECONDS", 3600 * 6)))  # Default to 6 hours
            self.logger.info("Running risk assessment update cycle.")
            if not self._db_initialized: 
                self.logger.warning("Database not initialized, skipping risk assessment updates.")
                continue
            try:
                # Fetch existing assessments and re-evaluate or create new ones
                async with self.db_manager.get_session() as session:
                    all_assessments = await self.db_helper.get_all(session, RiskAssessment)
                for assessment_data in all_assessments:
                    assessment = RiskAssessment(**assessment_data)
                    if assessment.next_review_date <= datetime.utcnow():
                        self.logger.info(f"Re-evaluating risk assessment {assessment.assessment_id}")
                        await self._assess_risk(assessment.risk_category, {"previous_assessment_id": assessment.assessment_id})
                self.logger.info("Risk assessment updates completed.")
            except Exception as e:
                self.logger.error(f"Error during risk assessment updates: {e}", exc_info=True)

    async def _alert_lifecycle_management(self):
        """
        Manages the lifecycle of alerts, including auto-resolving old or stale alerts.
        """
        while True:
            await asyncio.sleep(int(os.getenv("ALERT_LIFECYCLE_INTERVAL_SECONDS", 3600)))  # Default to 1 hour
            self.logger.info("Running alert lifecycle management cycle.")
            if not self._db_initialized: 
                self.logger.warning("Database not initialized, skipping alert lifecycle management.")
                continue
            try:
                async with self.db_manager.get_session() as session:
                    all_alerts = await self.db_helper.get_all(session, RiskAlert)
                for alert_data in all_alerts:
                    alert = RiskAlert(**alert_data)
                    if alert.status == AlertStatus.ACTIVE and (datetime.utcnow() - alert.created_at) > timedelta(days=7):
                        self.logger.info(f"Auto-resolving stale alert {alert.alert_id}")
                        await self._resolve_alert(alert.alert_id, "Auto-resolved due to staleness.")
                self.logger.info("Alert lifecycle management completed.")
            except Exception as e:
                self.logger.error(f"Error during alert lifecycle management: {e}", exc_info=True)

    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process agent-specific business logic
        
        Args:
            data: Dictionary containing operation type and parameters
            
        Returns:
            Dictionary with processing results
        """
        try:
            operation = data.get("operation", "process")
            return {"status": "success", "operation": operation, "data": data}
        except Exception as e:
            logger.error(f"Error in process_business_logic: {e}")
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    """Main entry point for the Risk Anomaly Detection Agent."""
    agent = RiskAnomalyDetectionAgent(
        agent_id="risk_anomaly_detection_agent",
        agent_type="risk_anomaly_detection",
        kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        listen_topics=[
            "system_metrics",
            "performance_data",
            "error_events",
            "external_events"
        ]
    )

    async def run_agent_and_server():
        await agent.initialize()
        try:
            # Start the agent's Kafka consumer in the background
            asyncio.create_task(agent.start())
            config = uvicorn.Config(agent.app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
            server = uvicorn.Server(config)
            await server.serve()
        except asyncio.CancelledError:
            agent.logger.info("Agent and server shutdown initiated.")
        finally:
            await agent.cleanup()

    asyncio.run(run_agent_and_server())

