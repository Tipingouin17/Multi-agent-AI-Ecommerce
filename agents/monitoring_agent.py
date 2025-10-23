"""
Monitoring Agent - Multi-Agent E-commerce System

This agent provides real-time system monitoring with:
- System health overview from database
- Agent health status tracking
- System alerts management
- Performance metrics collection

All data comes from the database - NO MOCK DATA.
"""

import asyncio
import logging
import os
import sys
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime, Integer, Float, Boolean, Text, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import base agent
try:
    from shared.base_agent_v2 import BaseAgentV2, MessageType, AgentMessage
    from shared.db_helpers import DatabaseHelper
    from shared.models import DatabaseConfig
    logger.info("Successfully imported shared modules")
except ImportError as e:
    logger.error(f"Import error: {e}")
    raise

# SQLAlchemy Base
Base = declarative_base()

# Database Models
class AgentHealthDB(Base):
    """Agent health status tracking"""
    __tablename__ = "agent_health"
    
    id = Column(String, primary_key=True)
    agent_id = Column(String, nullable=False, index=True)
    agent_name = Column(String, nullable=False)
    status = Column(String, nullable=False)  # healthy, warning, critical, offline
    cpu_usage = Column(Float, default=0.0)
    memory_usage = Column(Float, default=0.0)
    response_time = Column(Integer, default=0)  # milliseconds
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    error_count = Column(Integer, default=0)
    uptime_seconds = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SystemAlertDB(Base):
    """System alerts and notifications"""
    __tablename__ = "system_alerts"
    
    id = Column(String, primary_key=True)
    severity = Column(String, nullable=False)  # low, medium, high, critical
    title = Column(String, nullable=False)
    description = Column(Text)
    affected_agents = Column(Text)  # JSON array as string
    status = Column(String, default="active")  # active, resolved, acknowledged
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String, nullable=True)

class PerformanceMetricDB(Base):
    """System performance metrics"""
    __tablename__ = "performance_metrics"
    
    id = Column(String, primary_key=True)
    metric_type = Column(String, nullable=False, index=True)  # cpu, memory, disk, network, response_time
    metric_value = Column(Float, nullable=False)
    agent_id = Column(String, nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metadata = Column(Text, nullable=True)  # JSON metadata

# Pydantic Models
class AgentHealth(BaseModel):
    agent_id: str
    agent_name: str
    status: str
    cpu_usage: float
    memory_usage: float
    response_time: int
    last_heartbeat: str
    error_count: int
    uptime_seconds: int

class SystemAlert(BaseModel):
    id: str
    severity: str
    title: str
    description: Optional[str]
    affected_agents: List[str]
    status: str
    created_at: str
    resolved_at: Optional[str] = None

class SystemOverview(BaseModel):
    timestamp: str
    system_status: str
    total_agents: int
    healthy_agents: int
    warning_agents: int
    critical_agents: int
    offline_agents: int
    active_alerts: int
    critical_alerts: int
    system_metrics: Dict[str, float]

class MonitoringAgent(BaseAgentV2):
    """Monitoring Agent for system health and performance tracking"""
    
    def __init__(self, agent_id: str = "monitoring_agent"):
        super().__init__(agent_id=agent_id)
        
        self.agent_name = "Monitoring Agent"
        self.db_helper = None
        
        logger.info("Monitoring Agent constructor completed")
        
        # FastAPI app
        self.app = FastAPI(title="Monitoring Agent API")
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._setup_routes()
    
    async def initialize(self):
        """Initialize the monitoring agent"""
        try:
            logger.info("Initializing Monitoring Agent...")
            
            # Initialize database
            db_config = DatabaseConfig()
            self.db_helper = DatabaseHelper(
                db_config.get_database_url(),
                model=AgentHealthDB
            )
            
            # Create tables
            await self.db_helper.create_tables()
            
            # Initialize agent health records for all known agents
            await self._initialize_agent_health()
            
            logger.info("Monitoring Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Monitoring Agent: {e}")
            raise
    
    async def _initialize_agent_health(self):
        """Initialize health records for all known agents"""
        known_agents = [
            ("order_agent", "Order Management"),
            ("product_agent", "Product Management"),
            ("inventory_agent", "Inventory Management"),
            ("warehouse_agent", "Warehouse Management"),
            ("payment_agent", "Payment Processing"),
            ("transport_agent", "Transport Management"),
            ("marketplace_agent", "Marketplace Connector"),
            ("customer_agent", "Customer Service"),
            ("fraud_agent", "Fraud Detection"),
            ("risk_agent", "Risk Analysis"),
            ("backoffice_agent", "Backoffice Operations"),
            ("knowledge_agent", "Knowledge Management"),
            ("quality_agent", "Quality Control"),
            ("document_agent", "Document Generation"),
            ("monitoring_agent", "System Monitoring"),
        ]
        
        async with self.db_helper.get_session() as session:
            for agent_id, agent_name in known_agents:
                # Check if agent health record exists
                result = await session.execute(
                    select(AgentHealthDB).where(AgentHealthDB.agent_id == agent_id)
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    # Create initial health record
                    health_record = AgentHealthDB(
                        id=f"{agent_id}_health",
                        agent_id=agent_id,
                        agent_name=agent_name,
                        status="offline",
                        cpu_usage=0.0,
                        memory_usage=0.0,
                        response_time=0,
                        last_heartbeat=datetime.utcnow(),
                        error_count=0,
                        uptime_seconds=0
                    )
                    session.add(health_record)
            
            await session.commit()
            logger.info(f"Initialized health records for {len(known_agents)} agents")
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "agent": self.agent_name}
        
        @self.app.get("/system/overview", response_model=SystemOverview)
        async def get_system_overview():
            """Get system overview with real data from database"""
            try:
                async with self.db_helper.get_session() as session:
                    # Get agent health statistics
                    result = await session.execute(select(AgentHealthDB))
                    agents = result.scalars().all()
                    
                    total_agents = len(agents)
                    healthy_agents = sum(1 for a in agents if a.status == "healthy")
                    warning_agents = sum(1 for a in agents if a.status == "warning")
                    critical_agents = sum(1 for a in agents if a.status == "critical")
                    offline_agents = sum(1 for a in agents if a.status == "offline")
                    
                    # Get active alerts
                    alerts_result = await session.execute(
                        select(SystemAlertDB).where(SystemAlertDB.status == "active")
                    )
                    active_alerts_list = alerts_result.scalars().all()
                    active_alerts = len(active_alerts_list)
                    critical_alerts = sum(1 for a in active_alerts_list if a.severity == "critical")
                    
                    # Calculate system metrics
                    avg_cpu = sum(a.cpu_usage for a in agents) / total_agents if total_agents > 0 else 0
                    avg_memory = sum(a.memory_usage for a in agents) / total_agents if total_agents > 0 else 0
                    avg_response_time = sum(a.response_time for a in agents) / total_agents if total_agents > 0 else 0
                    total_errors = sum(a.error_count for a in agents)
                    
                    # Get system-wide metrics from performance_metrics table
                    perf_result = await session.execute(
                        select(PerformanceMetricDB)
                        .where(PerformanceMetricDB.timestamp >= datetime.utcnow() - timedelta(minutes=5))
                        .order_by(PerformanceMetricDB.timestamp.desc())
                        .limit(100)
                    )
                    perf_metrics = perf_result.scalars().all()
                    
                    # Determine overall system status
                    if critical_agents > 0 or critical_alerts > 0:
                        system_status = "critical"
                    elif warning_agents > 0 or active_alerts > 0:
                        system_status = "warning"
                    elif offline_agents > total_agents * 0.3:  # More than 30% offline
                        system_status = "degraded"
                    else:
                        system_status = "healthy"
                    
                    return SystemOverview(
                        timestamp=datetime.utcnow().isoformat(),
                        system_status=system_status,
                        total_agents=total_agents,
                        healthy_agents=healthy_agents,
                        warning_agents=warning_agents,
                        critical_agents=critical_agents,
                        offline_agents=offline_agents,
                        active_alerts=active_alerts,
                        critical_alerts=critical_alerts,
                        system_metrics={
                            "cpu_usage": round(avg_cpu, 2),
                            "memory_usage": round(avg_memory, 2),
                            "response_time": round(avg_response_time, 2),
                            "error_rate": round(total_errors / total_agents if total_agents > 0 else 0, 2),
                            "throughput": len(perf_metrics)
                        }
                    )
                    
            except Exception as e:
                logger.error(f"Error getting system overview: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/agents", response_model=List[AgentHealth])
        async def get_agent_health():
            """Get health status of all agents from database"""
            try:
                async with self.db_helper.get_session() as session:
                    result = await session.execute(
                        select(AgentHealthDB).order_by(AgentHealthDB.agent_name)
                    )
                    agents = result.scalars().all()
                    
                    return [
                        AgentHealth(
                            agent_id=agent.agent_id,
                            agent_name=agent.agent_name,
                            status=agent.status,
                            cpu_usage=agent.cpu_usage,
                            memory_usage=agent.memory_usage,
                            response_time=agent.response_time,
                            last_heartbeat=agent.last_heartbeat.isoformat(),
                            error_count=agent.error_count,
                            uptime_seconds=agent.uptime_seconds
                        )
                        for agent in agents
                    ]
                    
            except Exception as e:
                logger.error(f"Error getting agent health: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/alerts", response_model=List[SystemAlert])
        async def get_system_alerts(
            active_only: bool = Query(True, description="Return only active alerts")
        ):
            """Get system alerts from database"""
            try:
                async with self.db_helper.get_session() as session:
                    query = select(SystemAlertDB).order_by(SystemAlertDB.created_at.desc())
                    
                    if active_only:
                        query = query.where(SystemAlertDB.status == "active")
                    
                    result = await session.execute(query)
                    alerts = result.scalars().all()
                    
                    return [
                        SystemAlert(
                            id=alert.id,
                            severity=alert.severity,
                            title=alert.title,
                            description=alert.description,
                            affected_agents=alert.affected_agents.split(",") if alert.affected_agents else [],
                            status=alert.status,
                            created_at=alert.created_at.isoformat(),
                            resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None
                        )
                        for alert in alerts
                    ]
                    
            except Exception as e:
                logger.error(f"Error getting system alerts: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/metrics/performance")
        async def get_performance_metrics(
            time_range: str = Query("24h", description="Time range: 1h, 24h, 7d, 30d")
        ):
            """Get performance metrics from database"""
            try:
                # Parse time range
                time_delta_map = {
                    "1h": timedelta(hours=1),
                    "24h": timedelta(hours=24),
                    "7d": timedelta(days=7),
                    "30d": timedelta(days=30)
                }
                time_delta = time_delta_map.get(time_range, timedelta(hours=24))
                since = datetime.utcnow() - time_delta
                
                async with self.db_helper.get_session() as session:
                    result = await session.execute(
                        select(PerformanceMetricDB)
                        .where(PerformanceMetricDB.timestamp >= since)
                        .order_by(PerformanceMetricDB.timestamp.desc())
                    )
                    metrics = result.scalars().all()
                    
                    # Group metrics by type
                    metrics_by_type = {}
                    for metric in metrics:
                        if metric.metric_type not in metrics_by_type:
                            metrics_by_type[metric.metric_type] = []
                        metrics_by_type[metric.metric_type].append({
                            "value": metric.metric_value,
                            "timestamp": metric.timestamp.isoformat(),
                            "agent_id": metric.agent_id
                        })
                    
                    return {
                        "time_range": time_range,
                        "metrics_count": len(metrics),
                        "metrics": metrics_by_type
                    }
                    
            except Exception as e:
                logger.error(f"Error getting performance metrics: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/agents/{agent_id}/heartbeat")
        async def update_agent_heartbeat(agent_id: str, health_data: Dict[str, Any]):
            """Update agent heartbeat and health data"""
            try:
                async with self.db_helper.get_session() as session:
                    result = await session.execute(
                        select(AgentHealthDB).where(AgentHealthDB.agent_id == agent_id)
                    )
                    agent = result.scalar_one_or_none()
                    
                    if agent:
                        # Update existing record
                        agent.status = health_data.get("status", "healthy")
                        agent.cpu_usage = health_data.get("cpu_usage", 0.0)
                        agent.memory_usage = health_data.get("memory_usage", 0.0)
                        agent.response_time = health_data.get("response_time", 0)
                        agent.last_heartbeat = datetime.utcnow()
                        agent.error_count = health_data.get("error_count", 0)
                        agent.uptime_seconds = health_data.get("uptime_seconds", 0)
                        agent.updated_at = datetime.utcnow()
                    
                    await session.commit()
                    return {"status": "updated"}
                    
            except Exception as e:
                logger.error(f"Error updating agent heartbeat: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/alerts")
        async def create_alert(alert_data: Dict[str, Any]):
            """Create a new system alert"""
            try:
                async with self.db_helper.get_session() as session:
                    alert = SystemAlertDB(
                        id=f"alert_{datetime.utcnow().timestamp()}",
                        severity=alert_data.get("severity", "medium"),
                        title=alert_data["title"],
                        description=alert_data.get("description"),
                        affected_agents=",".join(alert_data.get("affected_agents", [])),
                        status="active"
                    )
                    session.add(alert)
                    await session.commit()
                    
                    return {"status": "created", "alert_id": alert.id}
                    
            except Exception as e:
                logger.error(f"Error creating alert: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/alerts/{alert_id}/resolve")
        async def resolve_alert(alert_id: str, resolved_by: str = "system"):
            """Resolve a system alert"""
            try:
                async with self.db_helper.get_session() as session:
                    result = await session.execute(
                        select(SystemAlertDB).where(SystemAlertDB.id == alert_id)
                    )
                    alert = result.scalar_one_or_none()
                    
                    if not alert:
                        raise HTTPException(status_code=404, detail="Alert not found")
                    
                    alert.status = "resolved"
                    alert.resolved_at = datetime.utcnow()
                    alert.resolved_by = resolved_by
                    
                    await session.commit()
                    return {"status": "resolved"}
                    
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error resolving alert: {e}")
                raise HTTPException(status_code=500, detail=str(e))

async def run_agent():
    """Run the monitoring agent"""
    agent = MonitoringAgent()
    await agent.initialize()
    
    import uvicorn
    config = uvicorn.Config(
        agent.app,
        host="0.0.0.0",
        port=8015,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(run_agent())

