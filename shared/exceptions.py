"""
Custom exceptions for the multi-agent system.

This module defines a hierarchy of custom exceptions to provide
better error handling and debugging capabilities.
"""

from typing import Optional, Dict, Any


class MultiAgentException(Exception):
    """Base exception for all multi-agent system errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize exception.
        
        Args:
            message: Error message
            error_code: Optional error code for categorization
            details: Optional additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


# Agent-related exceptions
class AgentException(MultiAgentException):
    """Base exception for agent-related errors."""
    pass


class AgentInitializationError(AgentException):
    """Raised when agent fails to initialize."""
    pass


class AgentCommunicationError(AgentException):
    """Raised when agent communication fails."""
    pass


class AgentTimeoutError(AgentException):
    """Raised when agent operation times out."""
    pass


# Database-related exceptions
class DatabaseException(MultiAgentException):
    """Base exception for database-related errors."""
    pass


class DatabaseConnectionError(DatabaseException):
    """Raised when database connection fails."""
    pass


class DatabaseQueryError(DatabaseException):
    """Raised when database query fails."""
    pass


class RecordNotFoundError(DatabaseException):
    """Raised when a database record is not found."""
    pass


class DuplicateRecordError(DatabaseException):
    """Raised when attempting to create a duplicate record."""
    pass


# Validation exceptions
class ValidationException(MultiAgentException):
    """Base exception for validation errors."""
    pass


class InvalidInputError(ValidationException):
    """Raised when input validation fails."""
    pass


class SchemaValidationError(ValidationException):
    """Raised when schema validation fails."""
    pass


class ConfigurationError(ValidationException):
    """Raised when configuration is invalid."""
    pass


# Business logic exceptions
class BusinessLogicException(MultiAgentException):
    """Base exception for business logic errors."""
    pass


class InsufficientInventoryError(BusinessLogicException):
    """Raised when inventory is insufficient for an operation."""
    pass


class OrderProcessingError(BusinessLogicException):
    """Raised when order processing fails."""
    pass


class PaymentError(BusinessLogicException):
    """Raised when payment processing fails."""
    pass


class ShippingError(BusinessLogicException):
    """Raised when shipping operation fails."""
    pass


# External service exceptions
class ExternalServiceException(MultiAgentException):
    """Base exception for external service errors."""
    pass


class APIError(ExternalServiceException):
    """Raised when external API call fails."""
    pass


class RateLimitError(ExternalServiceException):
    """Raised when rate limit is exceeded."""
    pass


class AuthenticationError(ExternalServiceException):
    """Raised when authentication fails."""
    pass


class AuthorizationError(ExternalServiceException):
    """Raised when authorization fails."""
    pass


# Messaging exceptions
class MessagingException(MultiAgentException):
    """Base exception for messaging errors."""
    pass


class MessageValidationError(MessagingException):
    """Raised when message validation fails."""
    pass


class MessageDeliveryError(MessagingException):
    """Raised when message delivery fails."""
    pass


class MessageSerializationError(MessagingException):
    """Raised when message serialization fails."""
    pass


# Retry decorator
import functools
import time
from typing import Callable, Type, Tuple


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator to retry a function on failure.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch and retry
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator to retry an async function on failure.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch and retry
    
    Returns:
        Decorated async function
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            import asyncio
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator

