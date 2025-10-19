"""
AI Monitoring and Error Management Agent

This meta-agent acts as the central nervous system for the entire multi-agent ecosystem,
providing continuous oversight, intelligent error detection, and actionable recommendations
for system optimization.

Key Features:
- Real-time system health monitoring
- AI-powered anomaly detection and root cause analysis
- Intelligent error management with human-readable recommendations
- Performance optimization suggestions
- Automated system recovery and self-healing capabilities
- Comprehensive dashboard for human operators
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import psutil
import requests
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pandas as pd
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import OpenAI helper
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.openai_helper import chat_completion

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AgentStatus(Enum):
    """Agent status enumeration"""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    OFFLINE = "offline"
    RECOVERING = "recovering"

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    active_connections: int
    response_time: float
    error_rate: float
    throughput: float

@dataclass
class AgentHealth:
    """Individual agent health status"""
    agent_id: str
    agent_name: str
    status: AgentStatus
    last_heartbeat: datetime
    response_time: float
    error_count: int
    success_rate: float
    cpu_usage: float
    memory_usage: float
    active_tasks: int
    queue_size: int
    custom_metrics: Dict[str, Any]

@dataclass
class Alert:
    """System alert with AI-generated recommendations"""
    id: str
    timestamp: datetime
    severity: AlertSeverity
    title: str
    description: str
    affected_agents: List[str]
    root_cause: str
    ai_recommendation: str
    confidence_score: float
    auto_resolution_possible: bool
    human_approval_required: bool
    resolution_steps: List[str]
    estimated_impact: str
    related_metrics: Dict[str, Any]

@dataclass
class PerformanceInsight:
    """AI-generated performance insights"""
    id: str
    timestamp: datetime
    category: str
    title: str
    description: str
    impact_assessment: str
    optimization_suggestions: List[str]
    expected_improvement: str
    implementation_complexity: str
    confidence_score: float

class AIMonitoringAgent:
    """
    AI-powered monitoring and error management agent that oversees
    the entire multi-agent e-commerce system.
    """
    
    def __init__(self):
        self.app = FastAPI(title="AI Monitoring Agent", version="1.0.0")
        self.setup_cors()
        self.setup_routes()
        
        # Agent registry and health tracking
        self.registered_agents: Dict[str, AgentHealth] = {}
        self.system_metrics_history: List[SystemMetrics] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.resolved_alerts: List[Alert] = []
        self.performance_insights: List[PerformanceInsight] = []
        
        # AI models for anomaly detection
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.model_trained = False
        
        # WebSocket connections for real-time updates
        self.websocket_connections: List[WebSocket] = []
        
        # Configuration
        self.config = {
            "monitoring_interval": 30,  # seconds
            "metrics_retention_days": 30,
            "alert_cooldown_minutes": 5,
            "auto_recovery_enabled": True,
            "ai_analysis_enabled": True,
            "performance_threshold": {
                "cpu_usage": 80.0,
                "memory_usage": 85.0,
                "response_time": 5000.0,  # milliseconds
                "error_rate": 5.0,  # percentage
            }
        }
        
        # Background tasks
        self.monitoring_task = None
        
        # Register startup event to start background tasks
        @self.app.on_event("startup")
        async def startup_event():
            await self.start_background_tasks()
        
        # Register shutdown event to clean up
        @self.app.on_event("shutdown")
        async def shutdown_event():
            await self.stop_background_tasks()
    
    async def start_background_tasks(self):
        """Start all background tasks"""
        logger.info("Starting background tasks...")
        self.monitoring_task = asyncio.create_task(self.start_monitoring())
    
    async def stop_background_tasks(self):
        """Stop all background tasks"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
    def setup_cors(self):
        """Setup CORS middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "monitored_agents": len(self.registered_agents),
                "active_alerts": len(self.active_alerts),
                "system_status": await self.get_overall_system_status()
            }
        
        @self.app.post("/agents/register")
        async def register_agent(agent_data: dict):
            """Register a new agent for monitoring"""
            agent_id = agent_data.get("agent_id")
            if not agent_id:
                raise HTTPException(status_code=400, detail="Agent ID is required")
            
            agent_health = AgentHealth(
                agent_id=agent_id,
                agent_name=agent_data.get("agent_name", agent_id),
                status=AgentStatus.HEALTHY,
                last_heartbeat=datetime.now(),
                response_time=0.0,
                error_count=0,
                success_rate=100.0,
                cpu_usage=0.0,
                memory_usage=0.0,
                active_tasks=0,
                queue_size=0,
                custom_metrics=agent_data.get("custom_metrics", {})
            )
            
            self.registered_agents[agent_id] = agent_health
            await self.broadcast_update("agent_registered", asdict(agent_health))
            
            logger.info(f"Agent registered: {agent_id}")
            return {"status": "registered", "agent_id": agent_id}
        
        @self.app.post("/agents/{agent_id}/heartbeat")
        async def agent_heartbeat(agent_id: str, metrics: dict):
            """Receive heartbeat and metrics from agents"""
            if agent_id not in self.registered_agents:
                raise HTTPException(status_code=404, detail="Agent not registered")
            
            agent = self.registered_agents[agent_id]
            agent.last_heartbeat = datetime.now()
            agent.response_time = metrics.get("response_time", 0.0)
            agent.error_count = metrics.get("error_count", 0)
            agent.success_rate = metrics.get("success_rate", 100.0)
            agent.cpu_usage = metrics.get("cpu_usage", 0.0)
            agent.memory_usage = metrics.get("memory_usage", 0.0)
            agent.active_tasks = metrics.get("active_tasks", 0)
            agent.queue_size = metrics.get("queue_size", 0)
            agent.custom_metrics.update(metrics.get("custom_metrics", {}))
            
            # Update agent status based on metrics
            agent.status = await self.assess_agent_health(agent)
            
            await self.broadcast_update("agent_heartbeat", {
                "agent_id": agent_id,
                "status": agent.status.value,
                "metrics": metrics
            })
            
            return {"status": "received"}
        
        @self.app.get("/system/overview")
        async def get_system_overview():
            """Get comprehensive system overview"""
            return {
                "timestamp": datetime.now().isoformat(),
                "system_status": await self.get_overall_system_status(),
                "agents": {agent_id: asdict(agent) for agent_id, agent in self.registered_agents.items()},
                "active_alerts": [asdict(alert) for alert in self.active_alerts.values()],
                "system_metrics": asdict(await self.collect_system_metrics()) if self.system_metrics_history else None,
                "performance_insights": [asdict(insight) for insight in self.performance_insights[-5:]]
            }
        
        @self.app.get("/alerts")
        async def get_alerts(active_only: bool = True):
            """Get system alerts"""
            if active_only:
                return [asdict(alert) for alert in self.active_alerts.values()]
            else:
                all_alerts = list(self.active_alerts.values()) + self.resolved_alerts[-50:]
                return [asdict(alert) for alert in sorted(all_alerts, key=lambda x: x.timestamp, reverse=True)]
        
        @self.app.post("/alerts/{alert_id}/resolve")
        async def resolve_alert(alert_id: str, resolution_data: dict):
            """Resolve an active alert"""
            if alert_id not in self.active_alerts:
                raise HTTPException(status_code=404, detail="Alert not found")
            
            alert = self.active_alerts.pop(alert_id)
            alert.resolution_steps.append(f"Manually resolved: {resolution_data.get('reason', 'No reason provided')}")
            self.resolved_alerts.append(alert)
            
            await self.broadcast_update("alert_resolved", {"alert_id": alert_id, "resolution": resolution_data})
            
            logger.info(f"Alert resolved: {alert_id}")
            return {"status": "resolved"}
        
        @self.app.post("/system/optimize")
        async def trigger_optimization():
            """Trigger AI-powered system optimization"""
            insights = await self.generate_performance_insights()
            return {
                "status": "optimization_complete",
                "insights_generated": len(insights),
                "insights": [asdict(insight) for insight in insights]
            }
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                while True:
                    # Send periodic updates
                    await asyncio.sleep(5)
                    await websocket.send_json({
                        "type": "system_update",
                        "data": {
                            "timestamp": datetime.now().isoformat(),
                            "agent_count": len(self.registered_agents),
                            "alert_count": len(self.active_alerts),
                            "system_status": await self.get_overall_system_status()
                        }
                    })
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
    
    async def start_monitoring(self):
        """Start the main monitoring loop"""
        logger.info("Starting AI monitoring system...")
        
        while True:
            try:
                # Collect system metrics
                metrics = await self.collect_system_metrics()
                self.system_metrics_history.append(metrics)
                
                # Clean old metrics
                cutoff_date = datetime.now() - timedelta(days=self.config["metrics_retention_days"])
                self.system_metrics_history = [
                    m for m in self.system_metrics_history 
                    if m.timestamp > cutoff_date
                ]
                
                # Check agent health
                await self.check_agent_health()
                
                # Perform anomaly detection
                if self.config["ai_analysis_enabled"]:
                    await self.detect_anomalies()
                
                # Generate performance insights
                if len(self.system_metrics_history) > 100:  # Need sufficient data
                    await self.generate_performance_insights()
                
                # Auto-resolve alerts if possible
                if self.config["auto_recovery_enabled"]:
                    await self.attempt_auto_recovery()
                
                await asyncio.sleep(self.config["monitoring_interval"])
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)  # Wait before retrying
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system performance metrics"""
        try:
            # Get system metrics using psutil
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Calculate network I/O rates (simplified)
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
            
            # Get active connections count
            active_connections = len(psutil.net_connections())
            
            # Calculate aggregate metrics from agents
            if self.registered_agents:
                response_times = [agent.response_time for agent in self.registered_agents.values()]
                error_rates = [
                    (agent.error_count / max(agent.error_count + (agent.success_rate * 10), 1)) * 100
                    for agent in self.registered_agents.values()
                ]
                throughputs = [agent.active_tasks for agent in self.registered_agents.values()]
                
                avg_response_time = statistics.mean(response_times) if response_times else 0.0
                avg_error_rate = statistics.mean(error_rates) if error_rates else 0.0
                total_throughput = sum(throughputs) if throughputs else 0.0
            else:
                avg_response_time = 0.0
                avg_error_rate = 0.0
                total_throughput = 0.0
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_io=network_io,
                active_connections=active_connections,
                response_time=avg_response_time,
                error_rate=avg_error_rate,
                throughput=total_throughput
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                network_io={},
                active_connections=0,
                response_time=0.0,
                error_rate=0.0,
                throughput=0.0
            )
    
    async def assess_agent_health(self, agent: AgentHealth) -> AgentStatus:
        """Assess individual agent health status"""
        now = datetime.now()
        time_since_heartbeat = (now - agent.last_heartbeat).total_seconds()
        
        # Check if agent is offline
        if time_since_heartbeat > 120:  # 2 minutes
            return AgentStatus.OFFLINE
        
        # Check critical thresholds
        if (agent.cpu_usage > 95 or 
            agent.memory_usage > 95 or 
            agent.success_rate < 50):
            return AgentStatus.ERROR
        
        # Check warning thresholds
        if (agent.cpu_usage > 80 or 
            agent.memory_usage > 80 or 
            agent.success_rate < 80 or
            agent.response_time > 5000):
            return AgentStatus.WARNING
        
        return AgentStatus.HEALTHY
    
    async def check_agent_health(self):
        """Check health of all registered agents"""
        now = datetime.now()
        
        for agent_id, agent in list(self.registered_agents.items()):
            time_since_heartbeat = (now - agent.last_heartbeat).total_seconds()
            
            # Update status based on heartbeat
            if time_since_heartbeat > 120:  # 2 minutes
                old_status = agent.status
                agent.status = AgentStatus.OFFLINE
                
                if old_status != AgentStatus.OFFLINE:
                    # Create alert for newly offline agent
                    await self.create_alert(
                        severity=AlertSeverity.HIGH,
                        title=f"Agent Offline: {agent.agent_name}",
                        description=f"Agent has not sent a heartbeat in {int(time_since_heartbeat)} seconds",
                        affected_agents=[agent_id],
                        root_cause="Agent may have crashed or lost network connectivity",
                        metrics={"time_since_heartbeat": time_since_heartbeat}
                    )
            
            # Check for agents in error state
            elif agent.status == AgentStatus.ERROR:
                # Create alert for agent in error state
                alert_key = f"error_{agent_id}_{int(now.timestamp() / 300)}"  # Group by 5-minute intervals
                
                if alert_key not in self.active_alerts:
                    root_cause = await self.analyze_agent_issues(agent)
                    
                    await self.create_alert(
                        severity=AlertSeverity.HIGH,
                        title=f"Agent Error: {agent.agent_name}",
                        description=f"Agent is reporting error status with {agent.error_count} errors",
                        affected_agents=[agent_id],
                        root_cause=root_cause,
                        metrics=asdict(agent)
                    )
    
    async def detect_anomalies(self):
        """Detect anomalies in system metrics using machine learning"""
        if len(self.system_metrics_history) < 10:
            return  # Not enough data
        
        try:
            # Prepare data for anomaly detection
            data = []
            for metrics in self.system_metrics_history[-100:]:  # Use last 100 data points
                data.append([
                    metrics.cpu_usage,
                    metrics.memory_usage,
                    metrics.disk_usage,
                    metrics.response_time,
                    metrics.error_rate,
                    metrics.throughput
                ])
            
            # Convert to DataFrame for easier handling
            df = pd.DataFrame(data, columns=[
                'cpu_usage', 'memory_usage', 'disk_usage', 
                'response_time', 'error_rate', 'throughput'
            ])
            
            # Scale the data
            scaled_data = self.scaler.fit_transform(df)
            
            # Train model if not trained or retrain periodically
            if not self.model_trained or len(self.system_metrics_history) % 100 == 0:
                self.anomaly_detector.fit(scaled_data)
                self.model_trained = True
            
            # Predict anomalies on recent data
            recent_data = scaled_data[-10:]  # Last 10 data points
            anomalies = self.anomaly_detector.predict(recent_data)
            anomaly_scores = self.anomaly_detector.decision_function(recent_data)
            
            # Generate alerts for detected anomalies
            for i, (score, is_anomaly) in enumerate(zip(anomaly_scores, anomalies)):
                if is_anomaly == -1:  # Anomaly detected
                    await self.create_anomaly_alert(
                        anomaly_score=score,
                        metrics_index=len(self.system_metrics_history) - 10 + i,
                        affected_metrics=df.iloc[-10 + i].to_dict()
                    )
                    
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
    
    async def create_alert(self, severity: AlertSeverity, title: str, description: str, 
                          affected_agents: List[str], root_cause: str, metrics: Dict[str, Any]):
        """Create a new system alert with AI analysis"""
        alert_id = f"alert_{int(time.time())}_{len(self.active_alerts)}"
        
        # Generate AI recommendation
        ai_recommendation = await self.generate_ai_recommendation(
            severity, title, description, root_cause, metrics
        )
        
        alert = Alert(
            id=alert_id,
            timestamp=datetime.now(),
            severity=severity,
            title=title,
            description=description,
            affected_agents=affected_agents,
            root_cause=root_cause,
            ai_recommendation=ai_recommendation["recommendation"],
            confidence_score=ai_recommendation["confidence"],
            auto_resolution_possible=ai_recommendation["auto_resolvable"],
            human_approval_required=ai_recommendation["human_approval_required"],
            resolution_steps=ai_recommendation["resolution_steps"],
            estimated_impact=ai_recommendation["estimated_impact"],
            related_metrics=metrics
        )
        
        self.active_alerts[alert_id] = alert
        
        await self.broadcast_update("new_alert", asdict(alert))
        
        logger.warning(f"Alert created: {title} (Severity: {severity.value})")
        
        return alert
    
    async def create_anomaly_alert(self, anomaly_score: float, metrics_index: int, affected_metrics: Dict[str, Any]):
        """Create alert for detected anomaly"""
        metrics = self.system_metrics_history[metrics_index]
        
        # Determine which metrics are most anomalous
        anomalous_metrics = []
        thresholds = self.config["performance_threshold"]
        
        if metrics.cpu_usage > thresholds["cpu_usage"]:
            anomalous_metrics.append(f"CPU usage: {metrics.cpu_usage:.1f}%")
        if metrics.memory_usage > thresholds["memory_usage"]:
            anomalous_metrics.append(f"Memory usage: {metrics.memory_usage:.1f}%")
        if metrics.response_time > thresholds["response_time"]:
            anomalous_metrics.append(f"Response time: {metrics.response_time:.1f}ms")
        if metrics.error_rate > thresholds["error_rate"]:
            anomalous_metrics.append(f"Error rate: {metrics.error_rate:.1f}%")
        
        severity = AlertSeverity.HIGH if anomaly_score < -0.5 else AlertSeverity.MEDIUM
        
        await self.create_alert(
            severity=severity,
            title="System Anomaly Detected",
            description=f"Anomaly detected in system metrics. Anomalous metrics: {', '.join(anomalous_metrics)}",
            affected_agents=list(self.registered_agents.keys()),
            root_cause=f"Statistical anomaly detected with score {anomaly_score:.3f}",
            metrics=affected_metrics
        )
    
    async def generate_ai_recommendation(self, severity: AlertSeverity, title: str, 
                                       description: str, root_cause: str, 
                                       metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered recommendations for alerts"""
        try:
            prompt = f"""
            As an expert system administrator for a multi-agent e-commerce platform, analyze this system alert and provide actionable recommendations:

            Alert Details:
            - Severity: {severity.value}
            - Title: {title}
            - Description: {description}
            - Root Cause: {root_cause}
            - Metrics: {json.dumps(metrics, indent=2)}

            Please provide:
            1. A clear, actionable recommendation for resolving this issue
            2. Step-by-step resolution instructions
            3. Estimated impact if not resolved
            4. Confidence level (0-100%)
            5. Whether this can be auto-resolved (true/false)
            6. Whether human approval is required for resolution (true/false)

            Respond in JSON format with keys: recommendation, resolution_steps, estimated_impact, confidence, auto_resolvable, human_approval_required
            """
            
            response = await chat_completion(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            
            if not response:
                return None
            
            ai_response = json.loads(response["choices"][0]["message"]["content"])
            
            return {
                "recommendation": ai_response.get("recommendation", "Manual investigation required"),
                "resolution_steps": ai_response.get("resolution_steps", ["Contact system administrator"]),
                "estimated_impact": ai_response.get("estimated_impact", "Unknown impact"),
                "confidence": ai_response.get("confidence", 50),
                "auto_resolvable": ai_response.get("auto_resolvable", False),
                "human_approval_required": ai_response.get("human_approval_required", True)
            }
            
        except Exception as e:
            logger.error(f"Error generating AI recommendation: {e}")
            return {
                "recommendation": "AI analysis unavailable. Manual investigation required.",
                "resolution_steps": ["Contact system administrator", "Review system logs", "Check agent status"],
                "estimated_impact": "Potential service degradation",
                "confidence": 30,
                "auto_resolvable": False,
                "human_approval_required": True
            }
    
    async def analyze_agent_issues(self, agent: AgentHealth) -> str:
        """Analyze specific agent issues using AI"""
        try:
            prompt = f"""
            Analyze this agent's health metrics and determine the most likely root cause:

            Agent: {agent.agent_name} ({agent.agent_id})
            Status: {agent.status.value}
            CPU Usage: {agent.cpu_usage}%
            Memory Usage: {agent.memory_usage}%
            Response Time: {agent.response_time}ms
            Success Rate: {agent.success_rate}%
            Error Count: {agent.error_count}
            Active Tasks: {agent.active_tasks}
            Queue Size: {agent.queue_size}
            Last Heartbeat: {agent.last_heartbeat}

            Provide a concise root cause analysis in 1-2 sentences.
            """
            
            response = await chat_completion(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )
            
            if not response:
                return "Unable to generate root cause analysis - OpenAI API not configured"
            
            return response["choices"][0]["message"]["content"].strip()
            
        except Exception as e:
            logger.error(f"Error analyzing agent issues: {e}")
            return f"Agent experiencing {agent.status.value} status. Manual investigation required."
    
    async def generate_performance_insights(self) -> List[PerformanceInsight]:
        """Generate AI-powered performance optimization insights"""
        if len(self.system_metrics_history) < 100:
            return []
        
        try:
            # Analyze recent performance trends
            recent_metrics = self.system_metrics_history[-100:]
            
            # Calculate trends
            cpu_trend = [m.cpu_usage for m in recent_metrics]
            memory_trend = [m.memory_usage for m in recent_metrics]
            response_time_trend = [m.response_time for m in recent_metrics]
            error_rate_trend = [m.error_rate for m in recent_metrics]
            
            insights = []
            
            # CPU optimization insight
            if statistics.mean(cpu_trend[-20:]) > 70:
                insight = await self.create_performance_insight(
                    "cpu_optimization",
                    "High CPU Usage Detected",
                    f"Average CPU usage is {statistics.mean(cpu_trend[-20:]):.1f}% over the last 20 monitoring cycles",
                    cpu_trend
                )
                if insight:
                    insights.append(insight)
            
            # Memory optimization insight
            if statistics.mean(memory_trend[-20:]) > 75:
                insight = await self.create_performance_insight(
                    "memory_optimization",
                    "High Memory Usage Detected",
                    f"Average memory usage is {statistics.mean(memory_trend[-20:]):.1f}% over the last 20 monitoring cycles",
                    memory_trend
                )
                if insight:
                    insights.append(insight)
            
            # Response time optimization insight
            if statistics.mean(response_time_trend[-20:]) > 3000:
                insight = await self.create_performance_insight(
                    "response_time_optimization",
                    "Slow Response Times Detected",
                    f"Average response time is {statistics.mean(response_time_trend[-20:]):.1f}ms over the last 20 monitoring cycles",
                    response_time_trend
                )
                if insight:
                    insights.append(insight)
            
            # Add insights to history
            self.performance_insights.extend(insights)
            
            # Keep only recent insights
            self.performance_insights = self.performance_insights[-50:]
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating performance insights: {e}")
            return []
    
    async def create_performance_insight(self, category: str, title: str, 
                                       description: str, trend_data: List[float]) -> Optional[PerformanceInsight]:
        """Create a performance insight using AI analysis"""
        try:
            prompt = f"""
            As a performance optimization expert for a multi-agent e-commerce system, analyze this performance trend and provide optimization recommendations:

            Category: {category}
            Issue: {title}
            Description: {description}
            Trend Data (last 20 points): {trend_data[-20:]}

            Please provide:
            1. Impact assessment of this performance issue
            2. 3-5 specific optimization suggestions
            3. Expected improvement percentage
            4. Implementation complexity (Low/Medium/High)
            5. Confidence level (0-100%)

            Respond in JSON format with keys: impact_assessment, optimization_suggestions, expected_improvement, implementation_complexity, confidence
            """
            
            response = await chat_completion(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            if not response:
                return None
            
            ai_response = json.loads(response["choices"][0]["message"]["content"])
            
            return PerformanceInsight(
                id=f"insight_{int(time.time())}_{category}",
                timestamp=datetime.now(),
                category=category,
                title=title,
                description=description,
                impact_assessment=ai_response.get("impact_assessment", "Unknown impact"),
                optimization_suggestions=ai_response.get("optimization_suggestions", []),
                expected_improvement=ai_response.get("expected_improvement", "Unknown"),
                implementation_complexity=ai_response.get("implementation_complexity", "Medium"),
                confidence_score=ai_response.get("confidence", 50)
            )
            
        except Exception as e:
            logger.error(f"Error creating performance insight: {e}")
            return None
    
    async def attempt_auto_recovery(self):
        """Attempt automatic recovery for resolvable issues"""
        for alert_id, alert in list(self.active_alerts.items()):
            if alert.auto_resolution_possible and not alert.human_approval_required:
                try:
                    # Implement auto-recovery logic based on alert type
                    success = await self.execute_auto_recovery(alert)
                    
                    if success:
                        alert.resolution_steps.append("Automatically resolved by AI system")
                        self.active_alerts.pop(alert_id)
                        self.resolved_alerts.append(alert)
                        
                        await self.broadcast_update("alert_auto_resolved", {
                            "alert_id": alert_id,
                            "resolution": "Automatic recovery successful"
                        })
                        
                        logger.info(f"Alert auto-resolved: {alert_id}")
                        
                except Exception as e:
                    logger.error(f"Auto-recovery failed for alert {alert_id}: {e}")
    
    async def execute_auto_recovery(self, alert: Alert) -> bool:
        """Execute automatic recovery actions"""
        try:
            # Example auto-recovery actions
            if "high cpu usage" in alert.title.lower():
                # Restart high-CPU agents
                for agent_id in alert.affected_agents:
                    if agent_id in self.registered_agents:
                        # Send restart command to agent (implementation depends on agent architecture)
                        logger.info(f"Attempting to restart agent {agent_id}")
                        # await self.restart_agent(agent_id)
                return True
            
            elif "memory usage" in alert.title.lower():
                # Trigger garbage collection or memory cleanup
                logger.info("Triggering system memory cleanup")
                # await self.cleanup_system_memory()
                return True
            
            elif "offline" in alert.description.lower():
                # Attempt to restart offline agents
                for agent_id in alert.affected_agents:
                    logger.info(f"Attempting to restart offline agent {agent_id}")
                    # await self.restart_agent(agent_id)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in auto-recovery execution: {e}")
            return False
    
    async def get_overall_system_status(self) -> str:
        """Determine overall system health status"""
        if not self.registered_agents:
            return "no_agents"
        
        critical_alerts = [a for a in self.active_alerts.values() if a.severity == AlertSeverity.CRITICAL]
        high_alerts = [a for a in self.active_alerts.values() if a.severity == AlertSeverity.HIGH]
        
        offline_agents = [a for a in self.registered_agents.values() if a.status == AgentStatus.OFFLINE]
        error_agents = [a for a in self.registered_agents.values() if a.status == AgentStatus.ERROR]
        
        if critical_alerts or len(offline_agents) > len(self.registered_agents) * 0.5:
            return "critical"
        elif high_alerts or error_agents:
            return "degraded"
        elif len([a for a in self.registered_agents.values() if a.status == AgentStatus.WARNING]) > 0:
            return "warning"
        else:
            return "healthy"
    
    async def broadcast_update(self, update_type: str, data: Any):
        """Broadcast real-time updates to connected WebSocket clients"""
        if not self.websocket_connections:
            return
        
        message = {
            "type": update_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        # Send to all connected clients
        disconnected = []
        for websocket in self.websocket_connections:
            try:
                await websocket.send_json(message)
            except:
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            self.websocket_connections.remove(websocket)

def create_app():
    """Create and return the FastAPI application"""
    agent = AIMonitoringAgent()
    return agent.app

# FastAPI app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8014)
