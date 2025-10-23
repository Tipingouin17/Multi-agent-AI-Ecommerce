"""
Comprehensive Error Handling Framework for Multi-Agent E-commerce System

This module provides production-ready error handling utilities including:
- Circuit breakers for external service calls
- Retry decorators with exponential backoff
- Graceful degradation helpers
- Error categorization and logging
- Health check utilities
"""

import asyncio
import functools
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from collections import defaultdict
import structlog

logger = structlog.get_logger(__name__)

T = TypeVar('T')


class ErrorSeverity(str, Enum):
    """Error severity levels for categorization"""
    LOW = "low"  # Non-critical, can continue
    MEDIUM = "medium"  # Important but recoverable
    HIGH = "high"  # Critical, affects functionality
    CRITICAL = "critical"  # System-wide failure


class ErrorCategory(str, Enum):
    """Error categories for better handling"""
    DATABASE = "database"
    NETWORK = "network"
    EXTERNAL_API = "external_api"
    KAFKA = "kafka"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for external service calls.
    
    Prevents cascading failures by temporarily blocking calls to failing services.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        name: str = "circuit_breaker"
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to catch
            name: Identifier for this circuit breaker
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        
        logger.info(
            "Circuit breaker initialized",
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout
        )
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result of func execution
            
        Raises:
            Exception: If circuit is open or func fails
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering half-open state", name=self.name)
            else:
                logger.warning(
                    "Circuit breaker is open, rejecting call",
                    name=self.name,
                    failure_count=self.failure_count
                )
                raise Exception(f"Circuit breaker {self.name} is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    async def call_async(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Async version of call method"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering half-open state", name=self.name)
            else:
                logger.warning(
                    "Circuit breaker is open, rejecting call",
                    name=self.name,
                    failure_count=self.failure_count
                )
                raise Exception(f"Circuit breaker {self.name} is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self.last_failure_time is None:
            return True
        return (datetime.utcnow() - self.last_failure_time).total_seconds() >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            logger.info("Circuit breaker recovered", name=self.name)
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(
                "Circuit breaker opened due to failures",
                name=self.name,
                failure_count=self.failure_count
            )


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback function called on each retry
        
    Example:
        @retry_with_backoff(max_attempts=5, base_delay=2.0)
        async def fetch_data():
            # Your code here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            "All retry attempts exhausted",
                            function=func.__name__,
                            attempts=max_attempts,
                            error=str(e)
                        )
                        raise
                    
                    delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
                    
                    logger.warning(
                        "Retry attempt",
                        function=func.__name__,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        delay=delay,
                        error=str(e)
                    )
                    
                    if on_retry:
                        on_retry(attempt, e)
                    
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            "All retry attempts exhausted",
                            function=func.__name__,
                            attempts=max_attempts,
                            error=str(e)
                        )
                        raise
                    
                    delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
                    
                    logger.warning(
                        "Retry attempt",
                        function=func.__name__,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        delay=delay,
                        error=str(e)
                    )
                    
                    if on_retry:
                        on_retry(attempt, e)
                    
                    time.sleep(delay)
            
            raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class GracefulDegradation:
    """
    Helper for implementing graceful degradation when services fail.
    
    Allows services to continue operating with reduced functionality
    instead of complete failure.
    """
    
    def __init__(self):
        self.degraded_features: Dict[str, Dict[str, Any]] = {}
        self.feature_status: Dict[str, bool] = defaultdict(lambda: True)
    
    def mark_degraded(
        self,
        feature: str,
        reason: str,
        fallback: Optional[Callable] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM
    ):
        """
        Mark a feature as degraded.
        
        Args:
            feature: Feature identifier
            reason: Reason for degradation
            fallback: Optional fallback function
            severity: Severity level
        """
        self.feature_status[feature] = False
        self.degraded_features[feature] = {
            "reason": reason,
            "fallback": fallback,
            "severity": severity,
            "timestamp": datetime.utcnow()
        }
        
        logger.warning(
            "Feature degraded",
            feature=feature,
            reason=reason,
            severity=severity
        )
    
    def mark_recovered(self, feature: str):
        """Mark a feature as recovered"""
        if feature in self.degraded_features:
            del self.degraded_features[feature]
        self.feature_status[feature] = True
        
        logger.info("Feature recovered", feature=feature)
    
    def is_available(self, feature: str) -> bool:
        """Check if a feature is available"""
        return self.feature_status.get(feature, True)
    
    def get_fallback(self, feature: str) -> Optional[Callable]:
        """Get fallback function for a degraded feature"""
        if feature in self.degraded_features:
            return self.degraded_features[feature].get("fallback")
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall degradation status"""
        return {
            "total_features": len(self.feature_status),
            "degraded_count": len(self.degraded_features),
            "degraded_features": self.degraded_features,
            "health_percentage": (
                (len(self.feature_status) - len(self.degraded_features)) /
                len(self.feature_status) * 100
                if self.feature_status else 100
            )
        }


def categorize_error(exception: Exception) -> tuple[ErrorCategory, ErrorSeverity]:
    """
    Categorize an exception for better handling.
    
    Args:
        exception: Exception to categorize
        
    Returns:
        Tuple of (category, severity)
    """
    error_str = str(exception).lower()
    exception_type = type(exception).__name__
    
    # Database errors
    if any(keyword in error_str for keyword in ["database", "sql", "connection", "postgres"]):
        return ErrorCategory.DATABASE, ErrorSeverity.HIGH
    
    # Network errors
    if any(keyword in error_str for keyword in ["network", "timeout", "connection refused", "unreachable"]):
        return ErrorCategory.NETWORK, ErrorSeverity.MEDIUM
    
    # Kafka errors
    if any(keyword in error_str for keyword in ["kafka", "broker", "consumer", "producer"]):
        return ErrorCategory.KAFKA, ErrorSeverity.HIGH
    
    # External API errors
    if any(keyword in error_str for keyword in ["api", "http", "request", "response"]):
        return ErrorCategory.EXTERNAL_API, ErrorSeverity.MEDIUM
    
    # Validation errors
    if "validation" in error_str or exception_type in ["ValidationError", "ValueError"]:
        return ErrorCategory.VALIDATION, ErrorSeverity.LOW
    
    # Configuration errors
    if any(keyword in error_str for keyword in ["config", "environment", "missing"]):
        return ErrorCategory.CONFIGURATION, ErrorSeverity.HIGH
    
    return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM


async def safe_execute(
    func: Callable,
    *args,
    fallback_value: Any = None,
    error_category: Optional[ErrorCategory] = None,
    **kwargs
) -> tuple[bool, Any]:
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Positional arguments
        fallback_value: Value to return on error
        error_category: Optional error category for logging
        **kwargs: Keyword arguments
        
    Returns:
        Tuple of (success: bool, result: Any)
    """
    try:
        if asyncio.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)
        return True, result
    except Exception as e:
        category, severity = categorize_error(e)
        
        logger.error(
            "Safe execution failed",
            function=func.__name__,
            category=error_category or category,
            severity=severity,
            error=str(e)
        )
        
        return False, fallback_value


# Global degradation manager
degradation_manager = GracefulDegradation()

