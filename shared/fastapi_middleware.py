"""
FastAPI Middleware for Multi-Agent E-commerce Platform

Provides automatic metrics collection, error handling, and monitoring
for all FastAPI-based agents.
"""

import time
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic metrics collection on all HTTP requests.
    
    Tracks:
    - Request count
    - Request duration
    - Error count
    - Active connections
    """
    
    def __init__(self, app: FastAPI, metrics_collector=None):
        super().__init__(app)
        self.metrics_collector = metrics_collector
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics"""
        
        # Skip metrics for /metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Increment active connections
        if self.metrics_collector:
            self.metrics_collector.set_gauge("active_connections", 
                self.metrics_collector.get_metric("active_connections").value + 1)
        
        # Track request start time
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Record metrics
            if self.metrics_collector:
                self.metrics_collector.increment_counter("requests_total")
                self.metrics_collector.observe_histogram("request_duration_ms", duration_ms)
                
                # Track by status code
                status_metric = f"requests_status_{response.status_code}"
                metric = self.metrics_collector.get_metric(status_metric)
                if not metric:
                    self.metrics_collector.register_counter(status_metric)
                self.metrics_collector.increment_counter(status_metric)
            
            return response
            
        except Exception as e:
            # Record error
            if self.metrics_collector:
                self.metrics_collector.increment_counter("errors_total")
            
            logger.error(
                "Request processing error",
                path=request.url.path,
                method=request.method,
                error=str(e)
            )
            
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )
        
        finally:
            # Decrement active connections
            if self.metrics_collector:
                self.metrics_collector.set_gauge("active_connections",
                    self.metrics_collector.get_metric("active_connections").value - 1)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for centralized error handling and logging.
    """
    
    def __init__(self, app: FastAPI, alert_manager=None):
        super().__init__(app)
        self.alert_manager = alert_manager
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with error handling"""
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(
                "Unhandled exception in request",
                path=request.url.path,
                method=request.method,
                error=str(e),
                exc_info=True
            )
            
            # Trigger alert for critical errors
            if self.alert_manager:
                from .monitoring import AlertSeverity
                await self.alert_manager.trigger_alert(
                    name="unhandled_exception",
                    severity=AlertSeverity.ERROR,
                    message=f"Unhandled exception in {request.method} {request.url.path}: {str(e)}",
                    metadata={
                        "path": request.url.path,
                        "method": request.method,
                        "error_type": type(e).__name__
                    }
                )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": str(e)
                }
            )


def setup_agent_endpoints(app: FastAPI, agent):
    """
    Setup standard endpoints for an agent.
    
    Args:
        app: FastAPI application
        agent: Agent instance (should have metrics_collector and alert_manager)
    
    Endpoints added:
        GET /metrics - Prometheus-format metrics
        GET /metrics/json - JSON-format metrics
        GET /alerts - Active alerts
        GET /status - Agent status
    """
    
    @app.get("/metrics", response_class=PlainTextResponse, tags=["Monitoring"])
    async def get_metrics():
        """
        Get metrics in Prometheus text format.
        
        This endpoint can be scraped by Prometheus for monitoring.
        """
        if not hasattr(agent, 'metrics_collector') or agent.metrics_collector is None:
            return "# Metrics not available\n"
        
        return agent.metrics_collector.get_prometheus_format()
    
    @app.get("/metrics/json", tags=["Monitoring"])
    async def get_metrics_json():
        """Get metrics in JSON format"""
        if not hasattr(agent, 'metrics_collector') or agent.metrics_collector is None:
            return {"error": "Metrics not available"}
        
        return agent.metrics_collector.get_all_metrics()
    
    @app.get("/alerts", tags=["Monitoring"])
    async def get_alerts():
        """Get active alerts"""
        if not hasattr(agent, 'alert_manager') or agent.alert_manager is None:
            return {"error": "Alert manager not available"}
        
        active_alerts = agent.alert_manager.get_active_alerts()
        return {
            "active_count": len(active_alerts),
            "alerts": [alert.to_dict() for alert in active_alerts]
        }
    
    @app.get("/alerts/history", tags=["Monitoring"])
    async def get_alert_history(limit: int = 100):
        """Get alert history"""
        if not hasattr(agent, 'alert_manager') or agent.alert_manager is None:
            return {"error": "Alert manager not available"}
        
        history = agent.alert_manager.get_alert_history(limit)
        return {
            "count": len(history),
            "alerts": [alert.to_dict() for alert in history]
        }
    
    @app.get("/status", tags=["Monitoring"])
    async def get_agent_status():
        """Get comprehensive agent status"""
        status = {
            "agent_id": agent.agent_id if hasattr(agent, 'agent_id') else "unknown",
            "status": agent.status.value if hasattr(agent, 'status') else "unknown",
            "uptime_seconds": 0
        }
        
        if hasattr(agent, 'start_time') and agent.start_time:
            from datetime import datetime
            status["uptime_seconds"] = (datetime.utcnow() - agent.start_time).total_seconds()
        
        if hasattr(agent, 'degradation_level') and agent.degradation_level:
            status["degradation_level"] = agent.degradation_level.value
        
        if hasattr(agent, 'db_status') and agent.db_status:
            status["database_status"] = agent.db_status.value
        
        if hasattr(agent, 'kafka_status') and agent.kafka_status:
            status["kafka_status"] = agent.kafka_status.value
        
        if hasattr(agent, 'metrics_collector') and agent.metrics_collector:
            status["metrics"] = agent.metrics_collector.get_all_metrics()
        
        if hasattr(agent, 'alert_manager') and agent.alert_manager:
            active_alerts = agent.alert_manager.get_active_alerts()
            status["active_alerts"] = len(active_alerts)
        
        return status


def setup_monitoring_middleware(app: FastAPI, agent):
    """
    Setup monitoring middleware for an agent's FastAPI app.
    
    Args:
        app: FastAPI application
        agent: Agent instance
    """
    # Add metrics middleware
    if hasattr(agent, 'metrics_collector') and agent.metrics_collector:
        app.add_middleware(MetricsMiddleware, metrics_collector=agent.metrics_collector)
        logger.info("Metrics middleware enabled", agent_id=agent.agent_id)
    
    # Add error handling middleware
    if hasattr(agent, 'alert_manager') and agent.alert_manager:
        app.add_middleware(ErrorHandlingMiddleware, alert_manager=agent.alert_manager)
        logger.info("Error handling middleware enabled", agent_id=agent.agent_id)
    
    # Setup standard endpoints
    setup_agent_endpoints(app, agent)
    logger.info("Standard monitoring endpoints enabled", agent_id=agent.agent_id)


# Decorator for automatic performance monitoring
def monitor_performance(operation_name: str = None):
    """
    Decorator to automatically monitor function performance.
    
    Args:
        operation_name: Name of the operation (defaults to function name)
    
    Example:
        @monitor_performance("process_order")
        async def process_order(order_id: str):
            # Your code here
            pass
    """
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            if not hasattr(self, 'performance_monitor') or self.performance_monitor is None:
                return await func(self, *args, **kwargs)
            
            op_name = operation_name or func.__name__
            return await self.performance_monitor.monitor_async_operation(
                op_name, func, self, *args, **kwargs
            )
        
        return wrapper
    return decorator

