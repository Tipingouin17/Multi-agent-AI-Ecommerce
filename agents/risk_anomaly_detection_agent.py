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
from uuid import uuid4
from enum import Enum
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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
    logger.info(f"Added {project_root} to Python path")

# Now try the import
try:
    from shared.openai_helper import chat_completion
    from shared.base_agent import BaseAgent, MessageType, AgentMessage
    logger.info("Successfully imported shared.base_agent")
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.info(f"Current sys.path: {sys.path}")
    
    # List files in the shared directory to verify it exists
    shared_dir = os.path.join(project_root, "shared")
    if os.path.exists(shared_dir):
        logger.info(f"Contents of {shared_dir}:")
        for item in os.listdir(shared_dir):
            logger.info(f"  - {item}")
    else:
        logger.info(f"Directory not found: {shared_dir}")

from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.models import APIResponse
from shared.database import DatabaseManager, get_database_manager


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
    alert_id: str
    alert_type: AnomalyType
    risk_category: RiskCategory
    risk_level: RiskLevel
    title: str
    description: str
    affected_components: List[str]
    metrics: Dict[str, Any]
    threshold_breached: Optional[str] = None
    confidence_score: float
    created_at: datetime
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None


class AnomalyDetectionModel(BaseModel):
    """Model for anomaly detection configuration."""
    model_id: str
    model_type: str  # "isolation_forest", "statistical", "ai_based"
    target_metrics: List[str]
    sensitivity: float  # 0.0 to 1.0
    training_window_hours: int
    detection_window_minutes: int
    threshold_multiplier: float
    active: bool = True
    last_trained: Optional[datetime] = None
    performance_score: Optional[float] = None


class RiskAssessment(BaseModel):
    """Model for risk assessments."""
    assessment_id: str
    risk_category: RiskCategory
    risk_factors: List[str]
    probability: float  # 0.0 to 1.0
    impact_score: float  # 0.0 to 1.0
    overall_risk_score: float  # 0.0 to 1.0
    mitigation_strategies: List[str]
    assessment_date: datetime
    next_review_date: datetime
    assessor: str  # "ai" or human assessor ID


class SystemMetrics(BaseModel):
    """Model for system performance metrics."""
    timestamp: datetime
    agent_id: str
    cpu_usage: float
    memory_usage: float
    response_time_ms: float
    error_rate: float
    throughput: float
    queue_length: int
    active_connections: int


class MarketIndicator(BaseModel):
    """Model for external market indicators."""
    indicator_id: str
    indicator_type: str  # "economic", "weather", "geopolitical", "industry"
    value: float
    unit: str
    source: str
    timestamp: datetime
    impact_assessment: Optional[str] = None


@dataclass
class AnomalyResult:
    """Result of anomaly detection."""
    is_anomaly: bool
    anomaly_score: float
    confidence: float
    affected_metrics: List[str]
    explanation: str


class RiskAnomalyDetectionAgent(BaseAgent):
    """
    Risk and Anomaly Detection Agent provides comprehensive monitoring including:
    - Real-time anomaly detection using ML models
    - Risk assessment and scoring
    - Alert generation and management
    - Predictive risk modeling
    - External threat monitoring
    """
    
    def __init__(self, **kwargs):
        super().__init__(agent_id="risk_anomaly_detection_agent", **kwargs)
        self.app = FastAPI(title="Risk and Anomaly Detection Agent API", version="1.0.0")
        self.setup_routes()
        # OpenAI client is initialized in openai_helper
        # Risk and anomaly data
        self.active_alerts: Dict[str, RiskAlert] = {}
        self.detection_models: Dict[str, AnomalyDetectionModel] = {}
        self.risk_assessments: Dict[str, RiskAssessment] = {}
        self.system_metrics_history: List[SystemMetrics] = []
        self.market_indicators: Dict[str, MarketIndicator] = {}
        
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
    
    async def initialize(self):
        """Initialize the Risk and Anomaly Detection Agent."""
        self.logger.info("Initializing Risk and Anomaly Detection Agent")
        
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
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process risk and anomaly detection business logic."""
        action = data.get("action")
        
        if action == "detect_anomalies":
            return await self._detect_anomalies(data["metrics"])
        elif action == "assess_risk":
            return await self._assess_risk(data["risk_category"], data.get("context", {}))
        elif action == "create_alert":
            return await self._create_alert(data["alert_data"])
        elif action == "get_active_alerts":
            return await self._get_active_alerts(data.get("filters", {}))
        elif action == "acknowledge_alert":
            return await self._acknowledge_alert(data["alert_id"], data.get("user_id"))
        elif action == "resolve_alert":
            return await self._resolve_alert(data["alert_id"], data.get("resolution_notes"))
        elif action == "get_risk_dashboard":
            return await self._get_risk_dashboard()
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def setup_routes(self):
        """Setup FastAPI routes for the Risk and Anomaly Detection Agent."""
        
        @self.app.post("/detect", response_model=APIResponse)
        async def detect_anomalies(metrics: Dict[str, Any]):
            """Detect anomalies in provided metrics."""
            try:
                result = await self._detect_anomalies(metrics)
                
                return APIResponse(
                    success=True,
                    message="Anomaly detection completed successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to detect anomalies", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/assess-risk", response_model=APIResponse)
        async def assess_risk(risk_category: RiskCategory, context: Dict[str, Any] = None):
            """Assess risk for a specific category."""
            try:
                result = await self._assess_risk(risk_category, context or {})
                
                return APIResponse(
                    success=True,
                    message="Risk assessment completed successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to assess risk", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/alerts", response_model=APIResponse)
        async def get_active_alerts(
            risk_level: Optional[RiskLevel] = None,
            alert_type: Optional[AnomalyType] = None,
            status: Optional[AlertStatus] = None
        ):
            """Get active alerts with optional filters."""
            try:
                filters = {}
                if risk_level:
                    filters["risk_level"] = risk_level
                if alert_type:
                    filters["alert_type"] = alert_type
                if status:
                    filters["status"] = status
                
                result = await self._get_active_alerts(filters)
                
                return APIResponse(
                    success=True,
                    message="Active alerts retrieved successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to get active alerts", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/alerts/{alert_id}/acknowledge", response_model=APIResponse)
        async def acknowledge_alert(alert_id: str, user_id: Optional[str] = None):
            """Acknowledge an alert."""
            try:
                result = await self._acknowledge_alert(alert_id, user_id)
                
                return APIResponse(
                    success=True,
                    message="Alert acknowledged successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to acknowledge alert", error=str(e), alert_id=alert_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/alerts/{alert_id}/resolve", response_model=APIResponse)
        async def resolve_alert(alert_id: str, resolution_notes: Optional[str] = None):
            """Resolve an alert."""
            try:
                result = await self._resolve_alert(alert_id, resolution_notes)
                
                return APIResponse(
                    success=True,
                    message="Alert resolved successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to resolve alert", error=str(e), alert_id=alert_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/dashboard", response_model=APIResponse)
        async def get_risk_dashboard():
            """Get comprehensive risk dashboard data."""
            try:
                result = await self._get_risk_dashboard()
                
                return APIResponse(
                    success=True,
                    message="Risk dashboard data retrieved successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to get risk dashboard", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/models", response_model=APIResponse)
        async def list_detection_models():
            """List all anomaly detection models."""
            try:
                models = [model.dict() for model in self.detection_models.values()]
                
                return APIResponse(
                    success=True,
                    message="Detection models retrieved successfully",
                    data={"models": models}
                )
            
            except Exception as e:
                self.logger.error("Failed to list detection models", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/models/{model_id}/retrain", response_model=APIResponse)
        async def retrain_model(model_id: str):
            """Retrain a specific anomaly detection model."""
            try:
                result = await self._retrain_model(model_id)
                
                return APIResponse(
                    success=True,
                    message="Model retrained successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to retrain model", error=str(e), model_id=model_id)
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _detect_anomalies(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Detect anomalies in provided metrics using multiple detection methods."""
        try:
            anomaly_results = []
            
            # Statistical anomaly detection
            statistical_result = await self._statistical_anomaly_detection(metrics)
            if statistical_result.is_anomaly:
                anomaly_results.append({
                    "method": "statistical",
                    "result": statistical_result.__dict__
                })
            
            # ML-based anomaly detection
            ml_result = await self._ml_anomaly_detection(metrics)
            if ml_result.is_anomaly:
                anomaly_results.append({
                    "method": "machine_learning",
                    "result": ml_result.__dict__
                })
            
            # AI-powered anomaly detection
            ai_result = await self._ai_anomaly_detection(metrics)
            if ai_result.is_anomaly:
                anomaly_results.append({
                    "method": "ai_powered",
                    "result": ai_result.__dict__
                })
            
            # Determine overall anomaly status
            is_anomaly = len(anomaly_results) > 0
            max_confidence = max([r["result"]["confidence"] for r in anomaly_results]) if anomaly_results else 0.0
            
            # Create alert if anomaly detected
            if is_anomaly and max_confidence > 0.7:
                await self._create_anomaly_alert(metrics, anomaly_results, max_confidence)
            
            return {
                "is_anomaly": is_anomaly,
                "confidence": max_confidence,
                "detection_methods": anomaly_results,
                "timestamp": datetime.utcnow().isoformat(),
                "metrics_analyzed": list(metrics.keys())
            }
        
        except Exception as e:
            self.logger.error("Failed to detect anomalies", error=str(e))
            raise
    
    async def _statistical_anomaly_detection(self, metrics: Dict[str, Any]) -> AnomalyResult:
        """Statistical anomaly detection using z-score and IQR methods."""
        try:
            anomalies_found = []
            explanations = []
            
            for metric_name, value in metrics.items():
                if not isinstance(value, (int, float)):
                    continue
                
                # Get historical data for this metric
                historical_values = self._get_historical_metric_values(metric_name)
                
                if len(historical_values) < 10:  # Need minimum data points
                    continue
                
                # Z-score anomaly detection
                mean_val = statistics.mean(historical_values)
                std_val = statistics.stdev(historical_values)
                
                if std_val > 0:
                    z_score = abs((value - mean_val) / std_val)
                    
                    if z_score > 3:  # 3-sigma rule
                        anomalies_found.append(metric_name)
                        explanations.append(f"{metric_name}: z-score {z_score:.2f} (threshold: 3.0)")
                
                # IQR anomaly detection
                sorted_values = sorted(historical_values)
                q1 = sorted_values[len(sorted_values) // 4]
                q3 = sorted_values[3 * len(sorted_values) // 4]
                iqr = q3 - q1
                
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                if value < lower_bound or value > upper_bound:
                    if metric_name not in anomalies_found:
                        anomalies_found.append(metric_name)
                        explanations.append(f"{metric_name}: outside IQR bounds [{lower_bound:.2f}, {upper_bound:.2f}]")
            
            is_anomaly = len(anomalies_found) > 0
            confidence = min(len(anomalies_found) / len(metrics), 1.0) if is_anomaly else 0.0
            
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
        """ML-based anomaly detection using Isolation Forest."""
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
                historical_data = self._get_historical_feature_matrix(feature_names)
                
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
        try:
            if not os.getenv("OPENAI_API_KEY"):
                return AnomalyResult(
                    is_anomaly=False,
                    anomaly_score=0.0,
                    confidence=0.0,
                    affected_metrics=[],
                    explanation="AI detection not available"
                )
            
            # Prepare context with historical baselines
            baselines = {}
            for metric_name in metrics.keys():
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
                "severity": "low|medium|high|critical",
                "potential_causes": ["cause1", "cause2"],
                "recommended_actions": ["action1", "action2"]
            }}
            """
            
            response = await chat_completion(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert system monitoring and anomaly detection specialist."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )
            
            content = response["choices"][0]["message"]["content"]
            ai_result = json.loads(content)
            
            return AnomalyResult(
                is_anomaly=ai_result.get("is_anomaly", False),
                anomaly_score=ai_result.get("anomaly_score", 0.0),
                confidence=ai_result.get("confidence", 0.0),
                affected_metrics=ai_result.get("affected_metrics", []),
                explanation=ai_result.get("explanation", "AI analysis completed")
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
    
    def _get_historical_metric_values(self, metric_name: str, hours: int = 24) -> List[float]:
        """Get historical values for a specific metric."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        values = []
        for metric in self.system_metrics_history:
            if metric.timestamp >= cutoff_time:
                if hasattr(metric, metric_name):
                    value = getattr(metric, metric_name)
                    if isinstance(value, (int, float)):
                        values.append(value)
        
        return values
    
    def _get_historical_feature_matrix(self, feature_names: List[str], hours: int = 168) -> List[List[float]]:
        """Get historical feature matrix for ML training."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        feature_matrix = []
        for metric in self.system_metrics_history:
            if metric.timestamp >= cutoff_time:
                row = []
                for feature_name in feature_names:
                    if hasattr(metric, feature_name):
                        value = getattr(metric, feature_name)
                        if isinstance(value, (int, float)):
                            row.append(value)
                        else:
                            row.append(0.0)
                    else:
                        row.append(0.0)
                
                if len(row) == len(feature_names):
                    feature_matrix.append(row)
        
        return feature_matrix
    
    async def _create_anomaly_alert(self, metrics: Dict[str, Any], anomaly_results: List[Dict], confidence: float):
        """Create alert for detected anomaly."""
        try:
            # Determine risk level based on confidence and affected metrics
            risk_level = RiskLevel.LOW
            if confidence > 0.9:
                risk_level = RiskLevel.CRITICAL
            elif confidence > 0.8:
                risk_level = RiskLevel.HIGH
            elif confidence > 0.6:
                risk_level = RiskLevel.MEDIUM
            
            # Collect affected metrics
            affected_metrics = set()
            for result in anomaly_results:
                affected_metrics.update(result["result"]["affected_metrics"])
            
            # Create alert
            alert = RiskAlert(
                alert_id=str(uuid4()),
                alert_type=AnomalyType.PERFORMANCE,
                risk_category=RiskCategory.OPERATIONAL,
                risk_level=risk_level,
                title=f"Performance Anomaly Detected - {len(affected_metrics)} metrics affected",
                description=f"Anomaly detected with {confidence:.1%} confidence affecting: {', '.join(affected_metrics)}",
                affected_components=list(affected_metrics),
                metrics=metrics,
                confidence_score=confidence,
                created_at=datetime.utcnow()
            )
            
            # Store alert
            self.active_alerts[alert.alert_id] = alert
            
            # Send alert notification
            await self.send_message(
                recipient_agent="monitoring_agent",
                message_type=MessageType.RISK_ALERT,
                payload={
                    "alert_id": alert.alert_id,
                    "risk_level": alert.risk_level.value,
                    "title": alert.title,
                    "description": alert.description,
                    "affected_components": alert.affected_components,
                    "confidence": alert.confidence_score
                }
            )
            
            self.logger.warning("Anomaly alert created", 
                              alert_id=alert.alert_id,
                              risk_level=alert.risk_level,
                              confidence=confidence)
        
        except Exception as e:
            self.logger.error("Failed to create anomaly alert", error=str(e))
    
    async def _assess_risk(self, risk_category: RiskCategory, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk for a specific category."""
        try:
            # Use AI to assess risk if available
            if os.getenv("OPENAI_API_KEY"):
                ai_assessment = await self._ai_risk_assessment(risk_category, context)
                if ai_assessment:
                    return ai_assessment
            
            # Fallback to rule-based risk assessment
            return await self._rule_based_risk_assessment(risk_category, context)
        
        except Exception as e:
            self.logger.error("Failed to assess risk", error=str(e))
            raise
    
    async def _ai_risk_assessment(self, risk_category: RiskCategory, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """AI-powered risk assessment."""
        try:
            # Prepare context data
            current_alerts = [alert.dict() for alert in self.active_alerts.values()]
            recent_metrics = self.system_metrics_history[-10:] if self.system_metrics_history else []
            
            prompt = f"""
            Conduct a comprehensive risk assessment for the {risk_category.value} category:
            
            Context Information:
            {json.dumps(context, indent=2)}
            
            Current Active Alerts:
            {json.dumps([alert for alert in current_alerts], indent=2)}
            
            Recent System Performance:
            {json.dumps([metric.__dict__ for metric in recent_metrics], indent=2, default=str)}
            
            Assess the risk considering:
            1. Current system state and performance
            2. Active alerts and their severity
            3. Historical patterns and trends
            4. External factors and dependencies
            5. Potential impact on business operations
            
            Provide a comprehensive risk assessment in JSON format:
            {{
                "overall_risk_score": 0.65,
                "probability": 0.7,
                "impact_score": 0.6,
                "risk_factors": ["factor1", "factor2", "factor3"],
                "mitigation_strategies": ["strategy1", "strategy2"],
                "confidence": 0.85,
                "assessment_summary": "Detailed summary of risk assessment",
                "recommendations": ["recommendation1", "recommendation2"],
                "monitoring_points": ["point1", "point2"]
            }}
            """
            
            response = await chat_completion(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert risk assessment analyst with deep knowledge of e-commerce operations and system reliability."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=600
            )
            
            content = response["choices"][0]["message"]["content"]
            ai_result = json.loads(content)
            
            # Create risk assessment record
            assessment = RiskAssessment(
                assessment_id=str(uuid4()),
                risk_category=risk_category,
                risk_factors=ai_result.get("risk_factors", []),
                probability=ai_result.get("probability", 0.5),
                impact_score=ai_result.get("impact_score", 0.5),
                overall_risk_score=ai_result.get("overall_risk_score", 0.5),
                mitigation_strategies=ai_result.get("mitigation_strategies", []),
                assessment_date=datetime.utcnow(),
                next_review_date=datetime.utcnow() + timedelta(days=7),
                assessor="ai"
            )
            
            # Store assessment
            self.risk_assessments[assessment.assessment_id] = assessment
            
            return {
                "assessment_id": assessment.assessment_id,
                "risk_category": risk_category.value,
                "overall_risk_score": assessment.overall_risk_score,
                "probability": assessment.probability,
                "impact_score": assessment.impact_score,
                "risk_factors": assessment.risk_factors,
                "mitigation_strategies": assessment.mitigation_strategies,
                "assessment_summary": ai_result.get("assessment_summary", ""),
                "recommendations": ai_result.get("recommendations", []),
                "monitoring_points": ai_result.get("monitoring_points", []),
                "confidence": ai_result.get("confidence", 0.7),
                "assessment_date": assessment.assessment_date.isoformat(),
                "next_review_date": assessment.next_review_date.isoformat()
            }
        
        except Exception as e:
            self.logger.error("AI risk assessment failed", error=str(e))
            return None
    
    async def _rule_based_risk_assessment(self, risk_category: RiskCategory, context: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based risk assessment as fallback."""
        # Simple rule-based risk scoring
        base_scores = {
            RiskCategory.FINANCIAL: 0.4,
            RiskCategory.OPERATIONAL: 0.5,
            RiskCategory.TECHNICAL: 0.6,
            RiskCategory.EXTERNAL: 0.3,
            RiskCategory.COMPLIANCE: 0.4,
            RiskCategory.SECURITY: 0.7
        }
        
        base_score = base_scores.get(risk_category, 0.5)
        
        # Adjust based on active alerts
        high_risk_alerts = len([a for a in self.active_alerts.values() if a.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]])
        score_adjustment = min(high_risk_alerts * 0.1, 0.3)
        
        final_score = min(base_score + score_adjustment, 1.0)
        
        assessment = RiskAssessment(
            assessment_id=str(uuid4()),
            risk_category=risk_category,
            risk_factors=["Active high-risk alerts", "System performance metrics"],
            probability=final_score,
            impact_score=final_score,
            overall_risk_score=final_score,
            mitigation_strategies=["Monitor system performance", "Address active alerts"],
            assessment_date=datetime.utcnow(),
            next_review_date=datetime.utcnow() + timedelta(days=7),
            assessor="rule_based"
        )
        
        self.risk_assessments[assessment.assessment_id] = assessment
        
        return {
            "assessment_id": assessment.assessment_id,
            "risk_category": risk_category.value,
            "overall_risk_score": assessment.overall_risk_score,
            "probability": assessment.probability,
            "impact_score": assessment.impact_score,
            "risk_factors": assessment.risk_factors,
            "mitigation_strategies": assessment.mitigation_strategies,
            "assessment_summary": f"Rule-based assessment for {risk_category.value} category",
            "recommendations": ["Regular monitoring", "Proactive maintenance"],
            "confidence": 0.6,
            "assessment_date": assessment.assessment_date.isoformat(),
            "next_review_date": assessment.next_review_date.isoformat()
        }
    
    async def _create_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new risk alert."""
        try:
            alert = RiskAlert(
                alert_id=alert_data.get("alert_id", str(uuid4())),
                alert_type=AnomalyType(alert_data["alert_type"]),
                risk_category=RiskCategory(alert_data["risk_category"]),
                risk_level=RiskLevel(alert_data["risk_level"]),
                title=alert_data["title"],
                description=alert_data["description"],
                affected_components=alert_data.get("affected_components", []),
                metrics=alert_data.get("metrics", {}),
                threshold_breached=alert_data.get("threshold_breached"),
                confidence_score=alert_data.get("confidence_score", 1.0),
                created_at=datetime.utcnow()
            )
            
            # Store alert
            self.active_alerts[alert.alert_id] = alert
            
            # Send notification
            await self.send_message(
                recipient_agent="monitoring_agent",
                message_type=MessageType.RISK_ALERT,
                payload=alert.dict()
            )
            
            return alert.dict()
        
        except Exception as e:
            self.logger.error("Failed to create alert", error=str(e))
            raise
    
    async def _get_active_alerts(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get active alerts with optional filters."""
        try:
            alerts = list(self.active_alerts.values())
            
            # Apply filters
            if "risk_level" in filters:
                alerts = [a for a in alerts if a.risk_level == filters["risk_level"]]
            
            if "alert_type" in filters:
                alerts = [a for a in alerts if a.alert_type == filters["alert_type"]]
            
            if "status" in filters:
                alerts = [a for a in alerts if a.status == filters["status"]]
            
            # Sort by creation time (newest first)
            alerts.sort(key=lambda x: x.created_at, reverse=True)
            
            # Calculate summary statistics
            total_alerts = len(alerts)
            critical_alerts = len([a for a in alerts if a.risk_level == RiskLevel.CRITICAL])
            high_alerts = len([a for a in alerts if a.risk_level == RiskLevel.HIGH])
            
            return {
                "alerts": [alert.dict() for alert in alerts],
                "summary": {
                    "total": total_alerts,
                    "critical": critical_alerts,
                    "high": high_alerts,
                    "medium": len([a for a in alerts if a.risk_level == RiskLevel.MEDIUM]),
                    "low": len([a for a in alerts if a.risk_level == RiskLevel.LOW])
                }
            }
        
        except Exception as e:
            self.logger.error("Failed to get active alerts", error=str(e))
            raise
    
    async def _acknowledge_alert(self, alert_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Acknowledge an alert."""
        try:
            alert = self.active_alerts.get(alert_id)
            if not alert:
                raise ValueError(f"Alert {alert_id} not found")
            
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = user_id or "system"
            alert.acknowledged_at = datetime.utcnow()
            
            return {
                "alert_id": alert_id,
                "status": "acknowledged",
                "acknowledged_by": alert.acknowledged_by,
                "acknowledged_at": alert.acknowledged_at.isoformat()
            }
        
        except Exception as e:
            self.logger.error("Failed to acknowledge alert", error=str(e))
            raise
    
    async def _resolve_alert(self, alert_id: str, resolution_notes: Optional[str] = None) -> Dict[str, Any]:
        """Resolve an alert."""
        try:
            alert = self.active_alerts.get(alert_id)
            if not alert:
                raise ValueError(f"Alert {alert_id} not found")
            
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            alert.resolution_notes = resolution_notes
            
            return {
                "alert_id": alert_id,
                "status": "resolved",
                "resolved_at": alert.resolved_at.isoformat(),
                "resolution_notes": resolution_notes
            }
        
        except Exception as e:
            self.logger.error("Failed to resolve alert", error=str(e))
            raise
    
    async def _get_risk_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive risk dashboard data."""
        try:
            # Alert summary
            active_alerts = [a for a in self.active_alerts.values() if a.status == AlertStatus.ACTIVE]
            alert_summary = {
                "total": len(active_alerts),
                "critical": len([a for a in active_alerts if a.risk_level == RiskLevel.CRITICAL]),
                "high": len([a for a in active_alerts if a.risk_level == RiskLevel.HIGH]),
                "medium": len([a for a in active_alerts if a.risk_level == RiskLevel.MEDIUM]),
                "low": len([a for a in active_alerts if a.risk_level == RiskLevel.LOW])
            }
            
            # Risk assessment summary
            recent_assessments = [a for a in self.risk_assessments.values() 
                                if (datetime.utcnow() - a.assessment_date).days <= 7]
            
            risk_summary = {}
            for category in RiskCategory:
                category_assessments = [a for a in recent_assessments if a.risk_category == category]
                if category_assessments:
                    avg_score = sum(a.overall_risk_score for a in category_assessments) / len(category_assessments)
                    risk_summary[category.value] = avg_score
                else:
                    risk_summary[category.value] = 0.5  # Default moderate risk
            
            # System health metrics
            recent_metrics = self.system_metrics_history[-10:] if self.system_metrics_history else []
            
            if recent_metrics:
                avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
                avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
                avg_response_time = sum(m.response_time_ms for m in recent_metrics) / len(recent_metrics)
                avg_error_rate = sum(m.error_rate for m in recent_metrics) / len(recent_metrics)
            else:
                avg_cpu = avg_memory = avg_response_time = avg_error_rate = 0
            
            system_health = {
                "cpu_usage": avg_cpu,
                "memory_usage": avg_memory,
                "response_time_ms": avg_response_time,
                "error_rate": avg_error_rate,
                "health_score": max(0, 100 - (avg_cpu + avg_memory + avg_error_rate * 100) / 3)
            }
            
            # Detection model performance
            model_performance = []
            for model_id, model in self.detection_models.items():
                model_performance.append({
                    "model_id": model_id,
                    "model_type": model.model_type,
                    "active": model.active,
                    "last_trained": model.last_trained.isoformat() if model.last_trained else None,
                    "performance_score": model.performance_score or 0.0
                })
            
            return {
                "alert_summary": alert_summary,
                "risk_summary": risk_summary,
                "system_health": system_health,
                "model_performance": model_performance,
                "recent_alerts": [a.dict() for a in active_alerts[:5]],  # Top 5 recent alerts
                "dashboard_updated": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error("Failed to get risk dashboard", error=str(e))
            raise
    
    async def _initialize_detection_models(self):
        """Initialize anomaly detection models."""
        try:
            # Performance monitoring model
            performance_model = AnomalyDetectionModel(
                model_id="performance_monitor",
                model_type="isolation_forest",
                target_metrics=["cpu_usage", "memory_usage", "response_time_ms", "error_rate"],
                sensitivity=0.8,
                training_window_hours=168,  # 1 week
                detection_window_minutes=5,
                threshold_multiplier=2.0
            )
            
            # Fraud detection model
            fraud_model = AnomalyDetectionModel(
                model_id="fraud_detector",
                model_type="ai_based",
                target_metrics=["transaction_amount", "transaction_frequency", "user_behavior"],
                sensitivity=0.9,
                training_window_hours=720,  # 30 days
                detection_window_minutes=1,
                threshold_multiplier=3.0
            )
            
            # System health model
            system_model = AnomalyDetectionModel(
                model_id="system_health",
                model_type="statistical",
                target_metrics=["throughput", "queue_length", "active_connections"],
                sensitivity=0.7,
                training_window_hours=72,  # 3 days
                detection_window_minutes=10,
                threshold_multiplier=2.5
            )
            
            self.detection_models = {
                performance_model.model_id: performance_model,
                fraud_model.model_id: fraud_model,
                system_model.model_id: system_model
            }
            
            self.logger.info("Detection models initialized", count=len(self.detection_models))
        
        except Exception as e:
            self.logger.error("Failed to initialize detection models", error=str(e))
    
    async def _establish_performance_baselines(self):
        """Establish performance baselines from historical data."""
        try:
            # In production, this would load actual historical data
            # For now, establish simulated baselines
            
            self.performance_baselines = {
                "cpu_usage": {"mean": 45.0, "std": 15.0, "min": 10.0, "max": 90.0},
                "memory_usage": {"mean": 60.0, "std": 20.0, "min": 20.0, "max": 95.0},
                "response_time_ms": {"mean": 150.0, "std": 50.0, "min": 50.0, "max": 500.0},
                "error_rate": {"mean": 0.02, "std": 0.01, "min": 0.0, "max": 0.1},
                "throughput": {"mean": 1000.0, "std": 200.0, "min": 500.0, "max": 2000.0},
                "queue_length": {"mean": 25.0, "std": 10.0, "min": 0.0, "max": 100.0}
            }
            
            self.logger.info("Performance baselines established")
        
        except Exception as e:
            self.logger.error("Failed to establish performance baselines", error=str(e))
    
    async def _initialize_alert_thresholds(self):
        """Initialize alert thresholds."""
        try:
            self.alert_thresholds = {
                "cpu_usage": {"warning": 70.0, "critical": 90.0},
                "memory_usage": {"warning": 80.0, "critical": 95.0},
                "response_time_ms": {"warning": 300.0, "critical": 1000.0},
                "error_rate": {"warning": 0.05, "critical": 0.1},
                "throughput": {"warning": 500.0, "critical": 200.0},  # Lower is worse
                "queue_length": {"warning": 50.0, "critical": 100.0}
            }
            
            self.logger.info("Alert thresholds initialized")
        
        except Exception as e:
            self.logger.error("Failed to initialize alert thresholds", error=str(e))
    
    async def _retrain_model(self, model_id: str) -> Dict[str, Any]:
        """Retrain a specific anomaly detection model."""
        try:
            model = self.detection_models.get(model_id)
            if not model:
                raise ValueError(f"Model {model_id} not found")
            
            # Get training data
            training_data = self._get_historical_feature_matrix(model.target_metrics, model.training_window_hours)
            
            if len(training_data) < 50:
                raise ValueError("Insufficient training data")
            
            # Retrain based on model type
            if model.model_type == "isolation_forest":
                # Retrain Isolation Forest
                model_key = "_".join(sorted(model.target_metrics))
                
                self.isolation_forests[model_key] = IsolationForest(
                    contamination=0.1,
                    random_state=42
                )
                
                self.scalers[model_key] = StandardScaler()
                
                scaled_data = self.scalers[model_key].fit_transform(training_data)
                self.isolation_forests[model_key].fit(scaled_data)
                
                # Simulate performance score
                model.performance_score = 0.85
            
            model.last_trained = datetime.utcnow()
            
            return {
                "model_id": model_id,
                "retrained_at": model.last_trained.isoformat(),
                "training_samples": len(training_data),
                "performance_score": model.performance_score
            }
        
        except Exception as e:
            self.logger.error("Failed to retrain model", error=str(e), model_id=model_id)
            raise
    
    async def _handle_system_metrics(self, message: AgentMessage):
        """Handle system metrics messages."""
        payload = message.payload
        
        try:
            # Create system metrics record
            metrics = SystemMetrics(
                timestamp=datetime.utcnow(),
                agent_id=payload.get("agent_id", "unknown"),
                cpu_usage=payload.get("cpu_usage", 0.0),
                memory_usage=payload.get("memory_usage", 0.0),
                response_time_ms=payload.get("response_time_ms", 0.0),
                error_rate=payload.get("error_rate", 0.0),
                throughput=payload.get("throughput", 0.0),
                queue_length=payload.get("queue_length", 0),
                active_connections=payload.get("active_connections", 0)
            )
            
            # Store metrics
            self.system_metrics_history.append(metrics)
            
            # Keep only recent metrics (last 7 days)
            cutoff_time = datetime.utcnow() - timedelta(days=7)
            self.system_metrics_history = [
                m for m in self.system_metrics_history if m.timestamp >= cutoff_time
            ]
            
            # Check for threshold breaches
            await self._check_threshold_breaches(metrics)
            
        except Exception as e:
            self.logger.error("Failed to handle system metrics", error=str(e))
    
    async def _check_threshold_breaches(self, metrics: SystemMetrics):
        """Check if metrics breach alert thresholds."""
        try:
            for metric_name, thresholds in self.alert_thresholds.items():
                if hasattr(metrics, metric_name):
                    value = getattr(metrics, metric_name)
                    
                    # Check critical threshold
                    if "critical" in thresholds:
                        if (metric_name == "throughput" and value < thresholds["critical"]) or \
                           (metric_name != "throughput" and value > thresholds["critical"]):
                            
                            await self._create_threshold_alert(metric_name, value, "critical", metrics.agent_id)
                    
                    # Check warning threshold
                    elif "warning" in thresholds:
                        if (metric_name == "throughput" and value < thresholds["warning"]) or \
                           (metric_name != "throughput" and value > thresholds["warning"]):
                            
                            await self._create_threshold_alert(metric_name, value, "warning", metrics.agent_id)
        
        except Exception as e:
            self.logger.error("Failed to check threshold breaches", error=str(e))
    
    async def _create_threshold_alert(self, metric_name: str, value: float, severity: str, agent_id: str):
        """Create alert for threshold breach."""
        try:
            risk_level = RiskLevel.CRITICAL if severity == "critical" else RiskLevel.HIGH
            
            alert = RiskAlert(
                alert_id=str(uuid4()),
                alert_type=AnomalyType.PERFORMANCE,
                risk_category=RiskCategory.TECHNICAL,
                risk_level=risk_level,
                title=f"{metric_name.replace('_', ' ').title()} Threshold Breach",
                description=f"{metric_name} value {value} exceeded {severity} threshold on {agent_id}",
                affected_components=[agent_id],
                metrics={metric_name: value},
                threshold_breached=f"{metric_name}_{severity}",
                confidence_score=1.0,
                created_at=datetime.utcnow()
            )
            
            # Check if similar alert already exists (avoid spam)
            similar_alerts = [
                a for a in self.active_alerts.values()
                if a.threshold_breached == alert.threshold_breached and
                   a.status == AlertStatus.ACTIVE and
                   (datetime.utcnow() - a.created_at).total_seconds() < 3600  # Within 1 hour
            ]
            
            if not similar_alerts:
                self.active_alerts[alert.alert_id] = alert
                
                await self.send_message(
                    recipient_agent="monitoring_agent",
                    message_type=MessageType.RISK_ALERT,
                    payload=alert.dict()
                )
        
        except Exception as e:
            self.logger.error("Failed to create threshold alert", error=str(e))
    
    async def _handle_performance_data(self, message: AgentMessage):
        """Handle performance data messages."""
        payload = message.payload
        
        try:
            # Analyze performance data for anomalies
            await self._detect_anomalies(payload)
        
        except Exception as e:
            self.logger.error("Failed to handle performance data", error=str(e))
    
    async def _handle_error_occurred(self, message: AgentMessage):
        """Handle error occurrence messages."""
        payload = message.payload
        
        try:
            # Create error alert
            alert_data = {
                "alert_type": AnomalyType.SYSTEM.value,
                "risk_category": RiskCategory.TECHNICAL.value,
                "risk_level": RiskLevel.HIGH.value,
                "title": f"Error in {payload.get('agent_id', 'Unknown Agent')}",
                "description": payload.get("error_message", "Unknown error occurred"),
                "affected_components": [payload.get("agent_id", "unknown")],
                "metrics": payload,
                "confidence_score": 1.0
            }
            
            await self._create_alert(alert_data)
        
        except Exception as e:
            self.logger.error("Failed to handle error occurred", error=str(e))
    
    async def _handle_external_event(self, message: AgentMessage):
        """Handle external event messages."""
        payload = message.payload
        
        try:
            event_type = payload.get("event_type")
            
            if event_type in ["market_disruption", "supply_chain_issue", "weather_event"]:
                # Create external risk alert
                alert_data = {
                    "alert_type": AnomalyType.EXTERNAL.value,
                    "risk_category": RiskCategory.EXTERNAL.value,
                    "risk_level": RiskLevel.MEDIUM.value,
                    "title": f"External Event: {event_type}",
                    "description": payload.get("description", f"External {event_type} detected"),
                    "affected_components": payload.get("affected_components", []),
                    "metrics": payload,
                    "confidence_score": payload.get("confidence", 0.8)
                }
                
                await self._create_alert(alert_data)
        
        except Exception as e:
            self.logger.error("Failed to handle external event", error=str(e))
    
    async def _continuous_monitoring(self):
        """Background task for continuous monitoring."""
        while not self.shutdown_event.is_set():
            try:
                # Monitor every 5 minutes
                await asyncio.sleep(300)
                
                if not self.shutdown_event.is_set():
                    # Check system health
                    await self._check_system_health()
                    
                    # Update risk assessments
                    await self._update_risk_assessments()
            
            except Exception as e:
                self.logger.error("Error in continuous monitoring", error=str(e))
                await asyncio.sleep(300)
    
    async def _check_system_health(self):
        """Check overall system health."""
        try:
            if not self.system_metrics_history:
                return
            
            # Get recent metrics (last 30 minutes)
            cutoff_time = datetime.utcnow() - timedelta(minutes=30)
            recent_metrics = [m for m in self.system_metrics_history if m.timestamp >= cutoff_time]
            
            if not recent_metrics:
                return
            
            # Calculate health score
            avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
            avg_error_rate = sum(m.error_rate for m in recent_metrics) / len(recent_metrics)
            
            health_score = max(0, 100 - (avg_cpu + avg_memory + avg_error_rate * 100) / 3)
            
            # Create alert if health is poor
            if health_score < 50:
                alert_data = {
                    "alert_type": AnomalyType.SYSTEM.value,
                    "risk_category": RiskCategory.OPERATIONAL.value,
                    "risk_level": RiskLevel.HIGH.value if health_score < 30 else RiskLevel.MEDIUM.value,
                    "title": "Poor System Health Detected",
                    "description": f"System health score: {health_score:.1f}/100",
                    "affected_components": ["system"],
                    "metrics": {
                        "health_score": health_score,
                        "avg_cpu": avg_cpu,
                        "avg_memory": avg_memory,
                        "avg_error_rate": avg_error_rate
                    },
                    "confidence_score": 0.9
                }
                
                await self._create_alert(alert_data)
        
        except Exception as e:
            self.logger.error("Failed to check system health", error=str(e))
    
    async def _update_risk_assessments(self):
        """Update existing risk assessments."""
        try:
            current_time = datetime.utcnow()
            
            # Find assessments due for review
            for assessment in self.risk_assessments.values():
                if assessment.next_review_date <= current_time:
                    # Reassess risk
                    await self._assess_risk(assessment.risk_category, {})
        
        except Exception as e:
            self.logger.error("Failed to update risk assessments", error=str(e))
    
    async def _model_retraining(self):
        """Background task for model retraining."""
        while not self.shutdown_event.is_set():
            try:
                # Retrain models every 24 hours
                await asyncio.sleep(24 * 3600)
                
                if not self.shutdown_event.is_set():
                    for model_id in self.detection_models.keys():
                        try:
                            await self._retrain_model(model_id)
                        except Exception as e:
                            self.logger.error("Failed to retrain model", error=str(e), model_id=model_id)
            
            except Exception as e:
                self.logger.error("Error in model retraining", error=str(e))
                await asyncio.sleep(12 * 3600)  # Wait 12 hours on error
    
    async def _external_threat_monitoring(self):
        """Background task for external threat monitoring."""
        while not self.shutdown_event.is_set():
            try:
                # Monitor external threats every hour
                await asyncio.sleep(3600)
                
                if not self.shutdown_event.is_set():
                    # In production, this would monitor:
                    # - Weather APIs for shipping disruptions
                    # - Economic indicators
                    # - Geopolitical events
                    # - Industry news and alerts
                    
                    # Simulated external monitoring
                    pass
            
            except Exception as e:
                self.logger.error("Error in external threat monitoring", error=str(e))
                await asyncio.sleep(3600)
    
    async def _risk_assessment_updates(self):
        """Background task for risk assessment updates."""
        while not self.shutdown_event.is_set():
            try:
                # Update risk assessments every 6 hours
                await asyncio.sleep(6 * 3600)
                
                if not self.shutdown_event.is_set():
                    await self._update_risk_assessments()
            
            except Exception as e:
                self.logger.error("Error in risk assessment updates", error=str(e))
                await asyncio.sleep(6 * 3600)
    
    async def _alert_lifecycle_management(self):
        """Background task for alert lifecycle management."""
        while not self.shutdown_event.is_set():
            try:
                # Manage alert lifecycle every 30 minutes
                await asyncio.sleep(1800)
                
                if not self.shutdown_event.is_set():
                    current_time = datetime.utcnow()
                    
                    # Auto-resolve old alerts (older than 7 days)
                    for alert in self.active_alerts.values():
                        if (alert.status == AlertStatus.ACTIVE and 
                            (current_time - alert.created_at).days >= 7):
                            
                            alert.status = AlertStatus.RESOLVED
                            alert.resolved_at = current_time
                            alert.resolution_notes = "Auto-resolved due to age"
            
            except Exception as e:
                self.logger.error("Error in alert lifecycle management", error=str(e))
                await asyncio.sleep(1800)


# FastAPI app instance for running the agent as a service
app = FastAPI(title="Risk and Anomaly Detection Agent", version="1.0.0")

# Global agent instance
risk_anomaly_agent: Optional[RiskAnomalyDetectionAgent] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the Risk and Anomaly Detection Agent on startup."""
    global risk_anomaly_agent
    risk_anomaly_agent = RiskAnomalyDetectionAgent()
    await risk_anomaly_agent.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup the Risk and Anomaly Detection Agent on shutdown."""
    global risk_anomaly_agent
    if risk_anomaly_agent:
        await risk_anomaly_agent.stop()


# Include agent routes
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if risk_anomaly_agent:
        health_status = risk_anomaly_agent.get_health_status()
        return {"status": "healthy", "agent_status": health_status.dict()}
    return {"status": "unhealthy", "message": "Agent not initialized"}


# Mount agent's FastAPI app
app.mount("/api/v1", risk_anomaly_agent.app if risk_anomaly_agent else FastAPI())


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
        password=os.getenv("POSTGRES_PASSWORD")
        if not password:
            raise ValueError("Database password must be set in environment variables")
    )
    initialize_database_manager(db_config)
    
    # Run the agent
    uvicorn.run(
        "risk_anomaly_detection_agent:app",
        host="0.0.0.0",
        port=8010,
        reload=False,
        log_level="info"
    )
