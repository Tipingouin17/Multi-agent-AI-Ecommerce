"""
Health Check Module for Multi-Agent E-commerce System

Provides standardized health check endpoints for all agents with three tiers:
1. Liveness - Is the agent running?
2. Readiness - Is the agent ready to handle requests?
3. Detailed - Full diagnostic information

Usage:
    from shared.health_checks import setup_health_endpoints
    
    # In your FastAPI app setup:
    setup_health_endpoints(app, agent)
"""

from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, Response, status
from pydantic import BaseModel

try:
    from .base_agent_v2 import BaseAgentV2, ServiceStatus, DegradationLevel, AgentStatus
    BASEV2_AVAILABLE = True
except ImportError:
    # Fallback for agents still using BaseAgent
    BASEV2_AVAILABLE = False
    BaseAgentV2 = None
    ServiceStatus = None
    DegradationLevel = None
    AgentStatus = None


class LivenessResponse(BaseModel):
    """Simple liveness check response."""
    status: str = "alive"
    timestamp: datetime


class ReadinessResponse(BaseModel):
    """Readiness check response with dependency status."""
    status: str
    ready: bool
    dependencies: Dict[str, str]
    degradation_level: Optional[int] = None
    timestamp: datetime


class DetailedHealthResponse(BaseModel):
    """Detailed health check response with full diagnostics."""
    agent_id: str
    status: str
    ready: bool
    uptime_seconds: float
    degradation_level: Optional[int] = None
    dependencies: Dict[str, str]
    metrics: Dict[str, Any]
    errors: Dict[str, Any]
    timestamp: datetime


def setup_health_endpoints(app: FastAPI, agent: Any):
    """
    Set up standardized health check endpoints for an agent.
    
    Args:
        app: FastAPI application instance
        agent: Agent instance (BaseAgent or BaseAgentV2)
    
    Endpoints created:
        GET /health - Liveness check (always returns 200 if agent is running)
        GET /health/ready - Readiness check (returns 503 if not ready)
        GET /health/detailed - Detailed health information
    """
    
    @app.get("/health", response_model=LivenessResponse, tags=["Health"])
    async def liveness_check():
        """
        Liveness check endpoint.
        
        Returns 200 OK if the agent process is running.
        This endpoint should never fail unless the agent is completely down.
        """
        return LivenessResponse(
            status="alive",
            timestamp=datetime.now()
        )
    
    @app.get("/health/ready", response_model=ReadinessResponse, tags=["Health"])
    async def readiness_check(response: Response):
        """
        Readiness check endpoint.
        
        Returns:
            200 OK if agent is ready to handle requests
            503 Service Unavailable if agent is not ready
        """
        # Check if agent has BaseAgentV2 features
        if BASEV2_AVAILABLE and isinstance(agent, BaseAgentV2):
            # Use BaseAgentV2 status
            is_ready = (
                agent.status in [AgentStatus.RUNNING, AgentStatus.DEGRADED] and
                agent.degradation_level.value < DegradationLevel.CRITICAL.value
            )
            
            dependencies = {
                "database": agent.db_status.value if agent.db_status else "unknown",
                "kafka": agent.kafka_status.value if agent.kafka_status else "unknown",
            }
            
            degradation_level = agent.degradation_level.value if agent.degradation_level else None
            
        else:
            # Fallback for BaseAgent
            is_ready = hasattr(agent, 'status') and agent.status == "running"
            dependencies = {}
            degradation_level = None
        
        if not is_ready:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
        return ReadinessResponse(
            status="ready" if is_ready else "not_ready",
            ready=is_ready,
            dependencies=dependencies,
            degradation_level=degradation_level,
            timestamp=datetime.now()
        )
    
    @app.get("/health/detailed", response_model=DetailedHealthResponse, tags=["Health"])
    async def detailed_health_check():
        """
        Detailed health check endpoint.
        
        Returns comprehensive diagnostic information about the agent.
        """
        # Calculate uptime
        uptime = 0.0
        if hasattr(agent, 'start_time') and agent.start_time:
            uptime = (datetime.now() - agent.start_time).total_seconds()
        
        # Get agent status
        if BASEV2_AVAILABLE and isinstance(agent, BaseAgentV2):
            agent_status = agent.status.value if agent.status else "unknown"
            is_ready = (
                agent.status in [AgentStatus.RUNNING, AgentStatus.DEGRADED] and
                agent.degradation_level.value < DegradationLevel.CRITICAL.value
            )
            
            dependencies = {
                "database": agent.db_status.value if agent.db_status else "unknown",
                "kafka": agent.kafka_status.value if agent.kafka_status else "unknown",
            }
            
            degradation_level = agent.degradation_level.value if agent.degradation_level else None
            
            metrics = agent.metrics if hasattr(agent, 'metrics') else {}
            
            errors = {
                "count": agent.error_count if hasattr(agent, 'error_count') else 0,
                "last_error": agent.last_error if hasattr(agent, 'last_error') else None
            }
            
        else:
            # Fallback for BaseAgent
            agent_status = getattr(agent, 'status', 'unknown')
            is_ready = agent_status == "running"
            dependencies = {}
            degradation_level = None
            metrics = {}
            errors = {
                "count": getattr(agent, 'error_count', 0),
                "last_error": getattr(agent, 'last_error', None)
            }
        
        return DetailedHealthResponse(
            agent_id=agent.agent_id if hasattr(agent, 'agent_id') else "unknown",
            status=agent_status,
            ready=is_ready,
            uptime_seconds=uptime,
            degradation_level=degradation_level,
            dependencies=dependencies,
            metrics=metrics,
            errors=errors,
            timestamp=datetime.now()
        )


def create_custom_health_endpoint(
    app: FastAPI,
    path: str,
    check_function: callable,
    tags: list = None
):
    """
    Create a custom health check endpoint.
    
    Args:
        app: FastAPI application instance
        path: Endpoint path (e.g., "/health/database")
        check_function: Async function that returns health status dict
        tags: Optional list of tags for the endpoint
    
    Example:
        async def check_database():
            try:
                # Check database connection
                return {"status": "healthy", "latency_ms": 5}
            except Exception as e:
                return {"status": "unhealthy", "error": str(e)}
        
        create_custom_health_endpoint(
            app,
            "/health/database",
            check_database,
            tags=["Health", "Database"]
        )
    """
    tags = tags or ["Health"]
    
    @app.get(path, tags=tags)
    async def custom_health_check():
        """Custom health check endpoint."""
        return await check_function()


# Utility functions for common health checks

async def check_database_health(db_manager) -> Dict[str, Any]:
    """
    Check database health.
    
    Args:
        db_manager: DatabaseManager instance
        
    Returns:
        Dict with status and details
    """
    try:
        if not db_manager:
            return {
                "status": "unavailable",
                "message": "Database manager not initialized"
            }
        
        # Try a simple query
        start_time = datetime.now()
        async with db_manager.get_async_session() as session:
            await session.execute("SELECT 1")
        latency = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "status": "healthy",
            "latency_ms": round(latency, 2)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def check_kafka_health(producer, consumer) -> Dict[str, Any]:
    """
    Check Kafka health.
    
    Args:
        producer: AIOKafkaProducer instance
        consumer: AIOKafkaConsumer instance
        
    Returns:
        Dict with status and details
    """
    try:
        producer_ok = producer is not None and hasattr(producer, '_sender')
        consumer_ok = consumer is not None and hasattr(consumer, '_coordinator')
        
        if producer_ok and consumer_ok:
            return {
                "status": "healthy",
                "producer": "connected",
                "consumer": "connected"
            }
        elif producer_ok or consumer_ok:
            return {
                "status": "degraded",
                "producer": "connected" if producer_ok else "disconnected",
                "consumer": "connected" if consumer_ok else "disconnected"
            }
        else:
            return {
                "status": "unhealthy",
                "producer": "disconnected",
                "consumer": "disconnected"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


async def check_redis_health(redis_client) -> Dict[str, Any]:
    """
    Check Redis health.
    
    Args:
        redis_client: Redis client instance
        
    Returns:
        Dict with status and details
    """
    try:
        if not redis_client:
            return {
                "status": "unavailable",
                "message": "Redis client not initialized"
            }
        
        # Try a ping
        start_time = datetime.now()
        await redis_client.ping()
        latency = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "status": "healthy",
            "latency_ms": round(latency, 2)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

