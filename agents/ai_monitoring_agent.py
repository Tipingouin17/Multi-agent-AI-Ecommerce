from contextlib import asynccontextmanager
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

from shared.db_helpers import DatabaseHelper
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
        @app.on_event("startup")
        async def startup_event():
            await self.start_background_tasks()
        
        # Register shutdown event to clean up
        @app.on_event("shutdown")
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
        
