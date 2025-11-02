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
from contextlib import asynccontextmanager # ADDED: Required for lifespan context

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import structlog
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import sys
import os

# --- Project Root Setup (Keep for shared imports) ---
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now try the import
from shared.base_agent_v2 import BaseAgentV2, MessageType, AgentMessage
from shared.models import APIResponse
from shared.database import DatabaseManager, get_database_manager
from shared.db_helpers import DatabaseHelper
from shared.openai_helper import chat_completion # Assuming this is needed

logger = structlog.get_logger(__name__)

# --- Data Models (Keep as is) ---
class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AnomalyType(str, Enum):
    PERFORMANCE = "performance"
    FRAUD = "fraud"
    SUPPLY_CHAIN = "supply_chain"
    SYSTEM = "system"
    MARKET = "market"
    OPERATIONAL = "operational"

class RiskCategory(str, Enum):
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    TECHNICAL = "technical"
    EXTERNAL = "external"
    COMPLIANCE = "compliance"
    SECURITY = "security"

class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

class RiskAlert(BaseModel):
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
    is_anomaly: bool = Field(..., description="True if an anomaly was detected, False otherwise.")
    anomaly_score: float = Field(..., ge=0.0, le=1.0, description="Normalized score indicating the severity of the anomaly.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level in the anomaly detection (0.0 to 1.0).")
    affected_metrics: List[str] = Field(..., description="List of metrics identified as anomalous.")
    explanation: str = Field(..., description="Detailed explanation of the anomaly and its potential causes.")


# --- AGENT CLASS (Refactored for FastAPI integration) ---
class RiskAnomalyDetectionAgent(BaseAgentV2):
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
        # Removed self.app = FastAPI(...)
        
        # --- Anomaly Detection Model Setup ---
        self.anomaly_models: Dict[str, IsolationForest] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.model_configs: Dict[str, AnomalyDetectionModel] = {}
        self.metrics_history: Dict[str, List[float]] = {}
        self.last_training_time: Optional[datetime] = None
        
        # --- Initialization Flags ---
        self._db_initialized = False
        self._kafka_initialized = False
        self._models_loaded = False

    @asynccontextmanager
    async def lifespan_context(self, app: FastAPI):
        """
        FastAPI Lifespan Context Manager for agent startup and shutdown.
        """
        # Startup
        self.logger.info("FastAPI Lifespan Startup: Risk Anomaly Detection Agent")
        await self.initialize()
        
        yield
        
        # Shutdown
        self.logger.info("FastAPI Lifespan Shutdown: Risk Anomaly Detection Agent")
        await self.cleanup()
        self.logger.info("Risk Anomaly Detection Agent API shutdown complete")

    def setup_routes(self, app: FastAPI):
        """
        Sets up the FastAPI routes for the agent.
        """
        # --- Health Check ---
        @app.get("/health", summary="Health Check", tags=["Monitoring"])
        async def health_check():
            """Endpoint to check the health of the agent and its connections."""
            db_status = "connected" if self._db_initialized else "disconnected"
            return {"status": "healthy", "db_status": db_status, "agent": self.agent_id}

        # --- Alerts Endpoints ---
        @app.post("/api/v1/alerts", response_model=RiskAlert, summary="Create a new risk alert", tags=["Alerts"])
        async def create_alert_endpoint(alert: RiskAlert):
            """Endpoint to manually create a new risk alert."""
            try:
                await self.db_helper.insert_one("risk_alerts", alert.dict())
                self.logger.warning("Manual Alert Created", alert_id=alert.alert_id, title=alert.title)
                return alert
            except Exception as e:
                self.logger.error(f"Failed to create alert: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/api/v1/alerts", response_model=List[RiskAlert], summary="Get all active risk alerts", tags=["Alerts"])
        async def get_alerts_endpoint(status: AlertStatus = Query(AlertStatus.ACTIVE)):
            """Endpoint to retrieve risk alerts by status."""
            try:
                results = await self.db_helper.fetch_all("risk_alerts", {"status": status.value})
                return [RiskAlert(**r) for r in results]
            except Exception as e:
                self.logger.error(f"Failed to retrieve alerts: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        # --- Metrics Endpoints ---
        @app.post("/api/v1/metrics", response_model=SystemMetrics, summary="Submit system metrics", tags=["Metrics"])
        async def submit_metrics_endpoint(metrics: SystemMetrics):
            """Endpoint to submit system metrics for anomaly detection."""
            try:
                # This bypasses the message queue for direct API submission
                await self._handle_system_metrics(AgentMessage(
                    sender_agent_id=metrics.agent_id,
                    recipient_agent_id=self.agent_id,
                    message_type=MessageType.SYSTEM_METRICS,
                    data=metrics.dict()
                ))
                return metrics
            except Exception as e:
                self.logger.error(f"Failed to submit metrics: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        # --- Assessment Endpoints ---
        @app.post("/api/v1/assessments", response_model=RiskAssessment, summary="Submit a risk assessment", tags=["Assessment"])
        async def submit_assessment_endpoint(assessment: RiskAssessment):
            """Endpoint to submit a new risk assessment."""
            try:
                await self.db_helper.insert_one("risk_assessments", assessment.dict())
                self.logger.info("New Risk Assessment Submitted", assessment_id=assessment.assessment_id)
                return assessment
            except Exception as e:
                self.logger.error(f"Failed to submit assessment: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

    # --- Agent Core Logic (Keep as is) ---
    async def initialize(self):
        """Initializes database, Kafka, and loads models."""
        self.logger.info("Initializing Risk Anomaly Detection Agent...")
        await super().initialize()
        
        # Database Initialization
        try:
            self.db_manager = get_database_manager()
            self.db_helper = DatabaseHelper(self.db_manager)
            await self.db_manager.initialize()
            self._db_initialized = True
            self.logger.info("Database connection established.")
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}", exc_info=True)
            # Continue without DB, but flag it
            self._db_initialized = False

        # Kafka Initialization (Consumer)
        try:
            # Assuming self.kafka_consumer is set up in BaseAgentV2.initialize()
            # Start the message processing loop
            asyncio.create_task(self.process_messages())
            self._kafka_initialized = True
            self.logger.info("Kafka consumer started.")
        except Exception as e:
            self.logger.error(f"Failed to start Kafka consumer: {e}", exc_info=True)
            self._kafka_initialized = False

        # Load Anomaly Detection Models
        await self._load_anomaly_models()
        self.logger.info("Risk Anomaly Detection Agent initialized.")

    async def process_messages(self):
        """
        The main message processing loop for the Kafka consumer.
        This method is required by BaseAgentV2.
        """
        self.logger.info("Starting Kafka message processing loop...")
        # The message processing loop is started in the base class's 'start' method
        # This method should contain the agent-specific logic, but since the base class
        # handles the loop, we can leave this method empty or remove the super call.

    async def cleanup(self):
        """Performs cleanup tasks."""
        self.logger.info("Cleaning up Risk Anomaly Detection Agent...")
        await super().cleanup()
        if self._db_initialized:
            await self.db_manager.disconnect()
            self.logger.info("Database connection closed.")
        self.logger.info("Risk Anomaly Detection Agent cleanup complete.")

    async def process_business_logic(self, message: AgentMessage):
        """Processes incoming messages based on type."""
        self.logger.info("Processing message", message_type=message.message_type.value, sender=message.sender_agent_id)
        
        if message.message_type == MessageType.SYSTEM_METRICS:
            await self._handle_system_metrics(message)
        elif message.message_type == MessageType.MARKET_INDICATOR:
            await self._handle_market_indicator(message)
        elif message.message_type == MessageType.RISK_ASSESSMENT_REQUEST:
            await self._handle_risk_assessment_request(message)
        else:
            self.logger.warning("Received unhandled message type", message_type=message.message_type.value)

    async def _handle_system_metrics(self, message: AgentMessage):
        """Handles incoming system metrics for anomaly detection."""
        try:
            metrics = SystemMetrics(**message.data)
            self.logger.debug("Received system metrics", agent_id=metrics.agent_id, cpu=metrics.cpu_usage)
            
            # 1. Store metrics history
            await self._store_metrics(metrics)
            
            # 2. Check for anomalies
            anomaly_result = await self._detect_anomaly(metrics)
            
            if anomaly_result.is_anomaly:
                self.logger.warning("Anomaly Detected", agent_id=metrics.agent_id, score=anomaly_result.anomaly_score)
                await self._generate_alert(metrics, anomaly_result)
                
            # 3. Retrain models periodically
            await self._check_and_retrain_models()
            
        except Exception as e:
            self.logger.error(f"Error processing system metrics: {e}", exc_info=True)

    async def _handle_market_indicator(self, message: AgentMessage):
        """Handles incoming market indicators for external risk assessment."""
        try:
            indicator = MarketIndicator(**message.data)
            self.logger.info("Received market indicator", type=indicator.indicator_type, value=indicator.value)
            
            # 1. Store indicator
            if self._db_initialized:
                await self.db_helper.insert_one("market_indicators", indicator.dict())
            
            # 2. Assess impact using AI
            impact_assessment = await self._assess_market_impact_ai(indicator)
            
            # 3. Generate risk assessment message for Knowledge Management Agent
            risk_assessment = RiskAssessment(
                assessment_id=f"MKT-{uuid4().hex[:8]}",
                risk_category=RiskCategory.EXTERNAL,
                risk_factors=[indicator.indicator_type, indicator.source],
                probability=0.5, # Placeholder
                impact_score=0.7, # Placeholder
                overall_risk_score=0.35, # Placeholder
                mitigation_strategies=["Monitor closely", "Prepare contingency plan"],
                next_review_date=datetime.utcnow() + timedelta(days=7),
                assessor=self.agent_id
            )
            
            await self.send_message(
                recipient_agent_id="knowledge_management_agent",
                message_type=MessageType.RISK_ASSESSMENT_UPDATE,
                data=risk_assessment.dict()
            )
            
        except Exception as e:
            self.logger.error(f"Error processing market indicator: {e}", exc_info=True)

    async def _handle_risk_assessment_request(self, message: AgentMessage):
        """Handles requests for a specific risk assessment."""
        try:
            # Assuming message.data contains parameters for the assessment
            assessment_params = message.data
            
            # Perform the assessment (e.g., call a dedicated method)
            risk_assessment = await self._perform_detailed_assessment(assessment_params)
            
            # Send the result back
            await self.send_message(
                recipient_agent_id=message.sender_agent_id,
                message_type=MessageType.RISK_ASSESSMENT_RESPONSE,
                data=risk_assessment.dict()
            )
            
        except Exception as e:
            self.logger.error(f"Error handling risk assessment request: {e}", exc_info=True)

    # --- Anomaly Detection Methods ---
    async def _load_anomaly_models(self):
        """Loads or initializes anomaly detection models from DB or default config."""
        self.logger.info("Loading anomaly detection models...")
        
        # 1. Load configurations from DB (or use default if DB not initialized)
        if self._db_initialized:
            configs = await self.db_helper.fetch_all("anomaly_models")
            if not configs:
                self.logger.warning("No anomaly model configs found in DB. Using default.")
                configs = self._get_default_model_configs()
            else:
                self.logger.info(f"Loaded {len(configs)} model configurations from DB.")
        else:
            configs = self._get_default_model_configs()
            self.logger.warning("DB not initialized. Using default model configs.")

        for config_data in configs:
            config = AnomalyDetectionModel(**config_data)
            self.model_configs[config.model_id] = config
            
            # 2. Initialize Isolation Forest model and Scaler
            if config.model_type == 'isolation_forest':
                model = IsolationForest(contamination=config.sensitivity, random_state=42)
                scaler = StandardScaler()
                self.anomaly_models[config.model_id] = model
                self.scalers[config.model_id] = scaler
                self.metrics_history[config.model_id] = []
                self.logger.info(f"Initialized Isolation Forest model: {config.model_id}")
        
        self._models_loaded = True
        self.last_training_time = datetime.utcnow()

    def _get_default_model_configs(self) -> List[Dict[str, Any]]:
        """Returns a list of default model configurations."""
        return [
            {
                "model_id": "performance_if",
                "model_type": "isolation_forest",
                "target_metrics": ["cpu_usage", "memory_usage", "response_time_ms"],
                "sensitivity": 0.05,
                "training_window_hours": 24,
                "detection_window_minutes": 5,
                "threshold_multiplier": 1.5,
                "active": True
            },
            {
                "model_id": "fraud_if",
                "model_type": "isolation_forest",
                "target_metrics": ["error_rate", "throughput", "queue_length"],
                "sensitivity": 0.01,
                "training_window_hours": 72,
                "detection_window_minutes": 1,
                "threshold_multiplier": 2.0,
                "active": True
            }
        ]

    async def _store_metrics(self, metrics: SystemMetrics):
        """Stores metrics in the database and in memory for training."""
        if self._db_initialized:
            await self.db_helper.insert_one("system_metrics", metrics.dict())
        
        # Store in memory for active models
        for model_id, config in self.model_configs.items():
            if config.active and config.model_type == 'isolation_forest':
                # Create a feature vector from the targeted metrics
                feature_vector = [metrics.dict().get(m) for m in config.target_metrics if metrics.dict().get(m) is not None]
                if len(feature_vector) == len(config.target_metrics):
                    self.metrics_history[model_id].append(feature_vector)

    async def _check_and_retrain_models(self):
        """Checks if models need retraining and performs it."""
        if self.last_training_time and (datetime.utcnow() - self.last_training_time).total_seconds() > 3600: # Retrain every hour
            self.logger.info("Initiating periodic model retraining.")
            for model_id, config in self.model_configs.items():
                if config.active and config.model_type == 'isolation_forest':
                    await self._train_model(model_id, config)
            self.last_training_time = datetime.utcnow()

    async def _train_model(self, model_id: str, config: AnomalyDetectionModel):
        """Trains a specific anomaly detection model."""
        self.logger.info(f"Training model: {model_id}")
        
        history = self.metrics_history.get(model_id, [])
        if len(history) < 100: # Minimum data points
            self.logger.warning(f"Not enough data to train model {model_id}. Skipping.")
            return

        data = np.array(history)
        
        # 1. Scale data
        scaler = self.scalers[model_id]
        scaled_data = scaler.fit_transform(data)
        
        # 2. Train model
        model = self.anomaly_models[model_id]
        model.fit(scaled_data)
        
        # 3. Update config
        config.last_trained = datetime.utcnow()
        # In a real system, you would save the model and scaler to disk/DB here
        
        self.logger.info(f"Model {model_id} trained successfully.")

    async def _detect_anomaly(self, metrics: SystemMetrics) -> AnomalyResult:
        """Detects anomalies in the incoming metrics."""
        
        for model_id, config in self.model_configs.items():
            if config.active and config.model_type == 'isolation_forest':
                
                # 1. Prepare data
                feature_vector = [metrics.dict().get(m) for m in config.target_metrics if metrics.dict().get(m) is not None]
                if len(feature_vector) != len(config.target_metrics):
                    continue # Skip if metrics are incomplete

                data_point = np.array(feature_vector).reshape(1, -1)
                
                # 2. Scale data
                scaler = self.scalers[model_id]
                scaled_data_point = scaler.transform(data_point)
                
                # 3. Predict anomaly score
                model = self.anomaly_models[model_id]
                # decision_function returns the anomaly score (lower is more anomalous)
                anomaly_score = model.decision_function(scaled_data_point)[0]
                
                # 4. Determine threshold (based on model's internal threshold and multiplier)
                # The threshold is typically the score of the least anomalous point in the contamination fraction
                # For simplicity, we use a fixed threshold based on the training data's average score
                
                # A score < 0 indicates an anomaly. The further below 0, the more severe.
                if anomaly_score < -0.1: # Simple fixed threshold for demonstration
                    
                    # 5. Generate AnomalyResult
                    normalized_score = max(0.0, min(1.0, 1 - (anomaly_score / -0.5))) # Normalize score for severity
                    
                    return AnomalyResult(
                        is_anomaly=True,
                        anomaly_score=normalized_score,
                        confidence=0.8, # Placeholder
                        affected_metrics=config.target_metrics,
                        explanation=f"Isolation Forest detected an anomaly in {', '.join(config.target_metrics)} with score {anomaly_score:.2f}."
                    )
        
        return AnomalyResult(is_anomaly=False, anomaly_score=0.0, confidence=1.0, affected_metrics=[], explanation="No anomaly detected.")

    async def _generate_alert(self, metrics: SystemMetrics, anomaly_result: AnomalyResult):
        """Generates a risk alert and sends it to the Monitoring Agent."""
        alert_id = f"ANOMALY-{uuid4().hex[:8]}"
        
        alert = RiskAlert(
            alert_id=alert_id,
            alert_type=AnomalyType.SYSTEM,
            risk_category=RiskCategory.TECHNICAL,
            risk_level=RiskLevel.HIGH if anomaly_result.anomaly_score > 0.7 else RiskLevel.MEDIUM,
            title=f"System Anomaly Detected in {metrics.agent_id}",
            description=anomaly_result.explanation,
            affected_components=[metrics.agent_id],
            metrics=metrics.dict(),
            confidence_score=anomaly_result.confidence
        )
        
        if self._db_initialized:
            await self.db_helper.insert_one("risk_alerts", alert.dict())
        
        # Send alert message to Monitoring Agent
        await self.send_message(
            recipient_agent_id="monitoring_agent",
            message_type=MessageType.RISK_ALERT,
            data=alert.dict()
        )
        self.logger.warning("Generated and sent risk alert", alert_id=alert_id, agent=metrics.agent_id)

    async def _assess_market_impact_ai(self, indicator: MarketIndicator) -> str:
        """Uses AI to assess the impact of a market indicator."""
        prompt = (
            f"Analyze the following market indicator and provide a concise, 3-sentence assessment of its potential impact "
            f"on an e-commerce business. Indicator Type: {indicator.indicator_type}, Value: {indicator.value} {indicator.unit}, "
            f"Source: {indicator.source}. Focus on operational and financial risk."
        )
        
        try:
            response = await chat_completion(prompt=prompt, model="gpt-4.1-mini")
            return response.strip()
        except Exception as e:
            self.logger.error(f"AI assessment failed: {e}", exc_info=True)
            return "AI assessment failed due to an internal error."

    async def _perform_detailed_assessment(self, params: Dict[str, Any]) -> RiskAssessment:
        """Performs a detailed risk assessment based on request parameters."""
        # This is a placeholder for complex logic involving multiple data sources
        self.logger.info("Performing detailed risk assessment", params=params)
        
        # Example: Query DB for recent alerts and market indicators
        recent_alerts = []
        if self._db_initialized:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            # This query needs to be implemented in DatabaseHelper
            # recent_alerts = await self.db_helper.fetch_alerts_in_range(start_time, end_time)
        
        # Logic to combine data and calculate score
        
        return RiskAssessment(
            assessment_id=f"DETAILED-{uuid4().hex[:8]}",
            risk_category=RiskCategory.OPERATIONAL,
            risk_factors=["High recent error rate", "Supply chain disruption"],
            probability=0.8,
            impact_score=0.9,
            overall_risk_score=0.72,
            mitigation_strategies=["Increase inventory buffer", "Review error logs"],
            next_review_date=datetime.utcnow() + timedelta(days=1),
            assessor=self.agent_id
        )


# --- MODULE-LEVEL FASTAPI SETUP ---
# AGENT INSTANCE (for dependency injection)
risk_agent: Optional['RiskAnomalyDetectionAgent'] = None

# FastAPI app
app = FastAPI(
    title="Risk and Anomaly Detection Agent API", 
    version="1.0.0",
    # Set the lifespan context manager on the app
    lifespan=RiskAnomalyDetectionAgent().lifespan_context
)

# Apply CORS middleware to the module-level app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database manager globally (must be done before agent initialization)
from shared.database import initialize_database_manager
from shared.models import DatabaseConfig

# Initialize database manager globally (must be done before agent initialization)
db_config = DatabaseConfig()
initialize_database_manager(db_config)

# Initialize agent instance and setup routes
risk_agent = RiskAnomalyDetectionAgent()
risk_agent.setup_routes(app)


if __name__ == "__main__":
    # Setup logging
    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    
    port = int(os.getenv("PORT", 8012))
    logger.info(f"Starting Risk and Anomaly Detection Agent on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
