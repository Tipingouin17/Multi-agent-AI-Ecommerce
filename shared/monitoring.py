"""
Monitoring and Metrics Collection System for Multi-Agent E-commerce Platform

Provides comprehensive monitoring, metrics collection, and alerting capabilities.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from collections import defaultdict, deque
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class MetricType(str, Enum):
    """Types of metrics"""
    COUNTER = "counter"  # Monotonically increasing
    GAUGE = "gauge"  # Can go up or down
    HISTOGRAM = "histogram"  # Distribution of values
    TIMER = "timer"  # Duration measurements


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Metric:
    """Base metric class"""
    
    def __init__(self, name: str, metric_type: MetricType, labels: Dict[str, str] = None):
        self.name = name
        self.metric_type = metric_type
        self.labels = labels or {}
        self.value = 0
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary"""
        return {
            "name": self.name,
            "type": self.metric_type.value,
            "value": self.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat()
        }


class Counter(Metric):
    """Counter metric - monotonically increasing"""
    
    def __init__(self, name: str, labels: Dict[str, str] = None):
        super().__init__(name, MetricType.COUNTER, labels)
    
    def inc(self, amount: float = 1.0):
        """Increment counter"""
        self.value += amount
        self.timestamp = datetime.utcnow()
    
    def reset(self):
        """Reset counter to zero"""
        self.value = 0
        self.timestamp = datetime.utcnow()


class Gauge(Metric):
    """Gauge metric - can go up or down"""
    
    def __init__(self, name: str, labels: Dict[str, str] = None):
        super().__init__(name, MetricType.GAUGE, labels)
    
    def set(self, value: float):
        """Set gauge value"""
        self.value = value
        self.timestamp = datetime.utcnow()
    
    def inc(self, amount: float = 1.0):
        """Increment gauge"""
        self.value += amount
        self.timestamp = datetime.utcnow()
    
    def dec(self, amount: float = 1.0):
        """Decrement gauge"""
        self.value -= amount
        self.timestamp = datetime.utcnow()


class Histogram(Metric):
    """Histogram metric - distribution of values"""
    
    def __init__(self, name: str, labels: Dict[str, str] = None, max_size: int = 1000):
        super().__init__(name, MetricType.HISTOGRAM, labels)
        self.values: deque = deque(maxlen=max_size)
        self.count = 0
        self.sum = 0.0
    
    def observe(self, value: float):
        """Record an observation"""
        self.values.append(value)
        self.count += 1
        self.sum += value
        self.timestamp = datetime.utcnow()
    
    def get_percentile(self, percentile: float) -> float:
        """Get percentile value"""
        if not self.values:
            return 0.0
        sorted_values = sorted(self.values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_stats(self) -> Dict[str, float]:
        """Get histogram statistics"""
        if not self.values:
            return {
                "count": 0,
                "sum": 0.0,
                "avg": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p50": 0.0,
                "p95": 0.0,
                "p99": 0.0
            }
        
        return {
            "count": self.count,
            "sum": self.sum,
            "avg": self.sum / self.count if self.count > 0 else 0.0,
            "min": min(self.values),
            "max": max(self.values),
            "p50": self.get_percentile(50),
            "p95": self.get_percentile(95),
            "p99": self.get_percentile(99)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with stats"""
        base = super().to_dict()
        base["stats"] = self.get_stats()
        return base


class MetricsCollector:
    """
    Centralized metrics collection system.
    
    Collects and manages metrics for monitoring agent performance.
    """
    
    def __init__(self, agent_id: str):
        """
        Initialize metrics collector.
        
        Args:
            agent_id: Unique identifier for the agent
        """
        self.agent_id = agent_id
        self.metrics: Dict[str, Metric] = {}
        self.start_time = datetime.utcnow()
        
        # Standard metrics
        self.register_counter("requests_total", {"agent_id": agent_id})
        self.register_counter("errors_total", {"agent_id": agent_id})
        self.register_gauge("active_connections", {"agent_id": agent_id})
        self.register_histogram("request_duration_ms", {"agent_id": agent_id})
        
        logger.info("Metrics collector initialized", agent_id=agent_id)
    
    def register_counter(self, name: str, labels: Dict[str, str] = None) -> Counter:
        """Register a new counter metric"""
        metric = Counter(name, labels)
        self.metrics[name] = metric
        return metric
    
    def register_gauge(self, name: str, labels: Dict[str, str] = None) -> Gauge:
        """Register a new gauge metric"""
        metric = Gauge(name, labels)
        self.metrics[name] = metric
        return metric
    
    def register_histogram(self, name: str, labels: Dict[str, str] = None) -> Histogram:
        """Register a new histogram metric"""
        metric = Histogram(name, labels)
        self.metrics[name] = metric
        return metric
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """Get a metric by name"""
        return self.metrics.get(name)
    
    def increment_counter(self, name: str, amount: float = 1.0):
        """Increment a counter metric"""
        metric = self.get_metric(name)
        if metric and isinstance(metric, Counter):
            metric.inc(amount)
    
    def set_gauge(self, name: str, value: float):
        """Set a gauge metric value"""
        metric = self.get_metric(name)
        if metric and isinstance(metric, Gauge):
            metric.set(value)
    
    def observe_histogram(self, name: str, value: float):
        """Record a histogram observation"""
        metric = self.get_metric(name)
        if metric and isinstance(metric, Histogram):
            metric.observe(value)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics as a dictionary"""
        return {
            "agent_id": self.agent_id,
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "metrics": {
                name: metric.to_dict()
                for name, metric in self.metrics.items()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_prometheus_format(self) -> str:
        """
        Export metrics in Prometheus text format.
        
        Returns:
            Metrics in Prometheus format
        """
        lines = []
        
        for name, metric in self.metrics.items():
            # Add metric type
            lines.append(f"# TYPE {name} {metric.metric_type.value}")
            
            # Add labels
            label_str = ",".join([f'{k}="{v}"' for k, v in metric.labels.items()])
            if label_str:
                label_str = "{" + label_str + "}"
            
            # Add value
            if isinstance(metric, Histogram):
                stats = metric.get_stats()
                for stat_name, stat_value in stats.items():
                    lines.append(f"{name}_{stat_name}{label_str} {stat_value}")
            else:
                lines.append(f"{name}{label_str} {metric.value}")
        
        return "\n".join(lines)


class Alert:
    """Alert model"""
    
    def __init__(
        self,
        name: str,
        severity: AlertSeverity,
        message: str,
        metadata: Dict[str, Any] = None
    ):
        self.name = name
        self.severity = severity
        self.message = message
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
        self.resolved = False
        self.resolved_at: Optional[datetime] = None
    
    def resolve(self):
        """Mark alert as resolved"""
        self.resolved = True
        self.resolved_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "severity": self.severity.value,
            "message": self.message,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


class AlertManager:
    """
    Alert management system.
    
    Manages alerts and notifications for agent monitoring.
    """
    
    def __init__(self, agent_id: str):
        """
        Initialize alert manager.
        
        Args:
            agent_id: Unique identifier for the agent
        """
        self.agent_id = agent_id
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.alert_handlers: List[Callable] = []
        
        logger.info("Alert manager initialized", agent_id=agent_id)
    
    def register_handler(self, handler: Callable[[Alert], None]):
        """
        Register an alert handler.
        
        Args:
            handler: Async function that handles alerts
        """
        self.alert_handlers.append(handler)
    
    async def trigger_alert(
        self,
        name: str,
        severity: AlertSeverity,
        message: str,
        metadata: Dict[str, Any] = None
    ) -> Alert:
        """
        Trigger a new alert.
        
        Args:
            name: Alert name/identifier
            severity: Alert severity
            message: Alert message
            metadata: Additional metadata
            
        Returns:
            Alert object
        """
        alert = Alert(name, severity, message, metadata)
        self.active_alerts[name] = alert
        self.alert_history.append(alert)
        
        logger.warning(
            "Alert triggered",
            agent_id=self.agent_id,
            alert_name=name,
            severity=severity.value,
            message=message
        )
        
        # Call alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(
                    "Alert handler failed",
                    handler=handler.__name__,
                    error=str(e)
                )
        
        return alert
    
    def resolve_alert(self, name: str):
        """
        Resolve an active alert.
        
        Args:
            name: Alert name
        """
        if name in self.active_alerts:
            alert = self.active_alerts[name]
            alert.resolve()
            del self.active_alerts[name]
            
            logger.info(
                "Alert resolved",
                agent_id=self.agent_id,
                alert_name=name
            )
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return list(self.alert_history)[-limit:]
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Get active alerts by severity"""
        return [
            alert for alert in self.active_alerts.values()
            if alert.severity == severity
        ]


class PerformanceMonitor:
    """
    Performance monitoring for agent operations.
    
    Tracks operation durations and identifies performance bottlenecks.
    """
    
    def __init__(self, metrics_collector: MetricsCollector):
        """
        Initialize performance monitor.
        
        Args:
            metrics_collector: MetricsCollector instance
        """
        self.metrics_collector = metrics_collector
        self.operation_timers: Dict[str, datetime] = {}
    
    def start_operation(self, operation_name: str):
        """Start timing an operation"""
        self.operation_timers[operation_name] = datetime.utcnow()
    
    def end_operation(self, operation_name: str) -> float:
        """
        End timing an operation and record duration.
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            Duration in milliseconds
        """
        if operation_name not in self.operation_timers:
            logger.warning(
                "Operation timer not found",
                operation=operation_name
            )
            return 0.0
        
        start_time = self.operation_timers[operation_name]
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Record in histogram
        histogram_name = f"{operation_name}_duration_ms"
        histogram = self.metrics_collector.get_metric(histogram_name)
        
        if not histogram:
            histogram = self.metrics_collector.register_histogram(
                histogram_name,
                {"operation": operation_name}
            )
        
        if isinstance(histogram, Histogram):
            histogram.observe(duration_ms)
        
        del self.operation_timers[operation_name]
        return duration_ms
    
    async def monitor_async_operation(self, operation_name: str, func: Callable, *args, **kwargs):
        """
        Monitor an async operation.
        
        Args:
            operation_name: Name of the operation
            func: Async function to monitor
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Result of the function
        """
        self.start_operation(operation_name)
        try:
            result = await func(*args, **kwargs)
            duration = self.end_operation(operation_name)
            
            logger.debug(
                "Operation completed",
                operation=operation_name,
                duration_ms=duration
            )
            
            return result
        except Exception as e:
            self.end_operation(operation_name)
            logger.error(
                "Operation failed",
                operation=operation_name,
                error=str(e)
            )
            raise


# Global instances (can be initialized per agent)
_metrics_collectors: Dict[str, MetricsCollector] = {}
_alert_managers: Dict[str, AlertManager] = {}


def get_metrics_collector(agent_id: str) -> MetricsCollector:
    """Get or create metrics collector for an agent"""
    if agent_id not in _metrics_collectors:
        _metrics_collectors[agent_id] = MetricsCollector(agent_id)
    return _metrics_collectors[agent_id]


def get_alert_manager(agent_id: str) -> AlertManager:
    """Get or create alert manager for an agent"""
    if agent_id not in _alert_managers:
        _alert_managers[agent_id] = AlertManager(agent_id)
    return _alert_managers[agent_id]

