"""
Enhanced Base Agent Framework for Multi-Agent E-commerce System (V2)

This module provides production-grade agent infrastructure with:
- Unified initialization with retry logic
- Comprehensive error handling
- Graceful degradation
- Three-tier health monitoring
- Circuit breaker pattern
- Automatic recovery
"""

import asyncio
import json
import logging
import os
import random
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

import structlog
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError, GroupCoordinatorNotAvailableError
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database components
try:
    from .database import DatabaseManager
    from .db_helpers import DatabaseHelper, get_db_helper
    from .models import DatabaseConfig
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False


class MessageType(str, Enum):
    """Standard message types for inter-agent communication."""
    # Order Management
    ORDER_CREATED = "order_created"
    ORDER_UPDATED = "order_updated"
    ORDER_STATUS_UPDATED = "order_status_updated"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_FULFILLMENT_REQUIRED = "order_fulfillment_required"
    
    # Inventory Management
    INVENTORY_UPDATE = "inventory_update"
    INVENTORY_UPDATED = "inventory_updated"
    STOCK_ALERT = "stock_alert"
    
    # Pricing
    PRICE_UPDATE = "price_update"
    PRICE_UPDATED = "price_updated"
    COMPETITOR_PRICE_UPDATE = "competitor_price_update"
    
    # Logistics
    CARRIER_SELECTED = "carrier_selected"
    WAREHOUSE_SELECTED = "warehouse_selected"
    SHIPMENT_CREATED = "shipment_created"
    
    # Returns & Customer Service
    RETURN_REQUESTED = "return_requested"
    RETURN_APPROVED = "return_approved"
    RETURN_REJECTED = "return_rejected"
    ITEM_RECEIVED = "item_received"
    QUALITY_ASSESSMENT_COMPLETED = "quality_assessment_completed"
    REFURBISHMENT_COMPLETED = "refurbishment_completed"
    
    # Product Management
    PRODUCT_CREATED = "product_created"
    PRODUCT_UPDATED = "product_updated"
    PRODUCT_DELETED = "product_deleted"
    
    # System & Monitoring
    ERROR_DETECTED = "error_detected"
    ERROR_OCCURRED = "error_occurred"
    HEALTH_CHECK = "health_check"
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    SYSTEM_METRICS = "system_metrics"
    PERFORMANCE_DATA = "performance_data"
    EXTERNAL_EVENT = "external_event"
    
    # Analytics & Forecasting
    DEMAND_FORECAST = "demand_forecast"
    RISK_ALERT = "risk_alert"
    
    # Customer Communication
    CUSTOMER_NOTIFICATION = "customer_notification"
    CUSTOMER_MESSAGE = "customer_message"


class AgentStatus(str, Enum):
    """Agent operational status."""
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"  # Running with reduced functionality
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class ServiceStatus(str, Enum):
    """Status of individual services."""
    CONNECTED = "connected"
    DEGRADED = "degraded"
    DISCONNECTED = "disconnected"
    FAILED = "failed"
    INITIALIZING = "initializing"


class DegradationLevel(int, Enum):
    """Levels of service degradation."""
    FULL = 0          # All services operational
    DB_FALLBACK = 1   # Using SQLite fallback
    NO_KAFKA = 2      # Kafka unavailable
    MULTIPLE = 3      # Multiple services down
    CRITICAL = 4      # Cannot function


@dataclass
class AgentMessage:
    """Standard message format for inter-agent communication."""
    message_id: str
    sender_agent: str
    recipient_agent: str
    message_type: MessageType
    payload: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None
    priority: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['message_type'] = self.message_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['message_type'] = MessageType(data['message_type'])
        return cls(**data)


class HealthStatus(BaseModel):
    """Agent health status information."""
    agent_id: str
    status: AgentStatus
    degradation_level: DegradationLevel
    uptime_seconds: float
    last_heartbeat: datetime
    error_count: int = 0
    last_error: Optional[str] = None
    performance_metrics: Dict[str, float] = Field(default_factory=dict)
    dependencies: Dict[str, ServiceStatus] = Field(default_factory=dict)


class CircuitBreaker:
    """Circuit breaker for external service calls."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60, name: str = "default"):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.name = name
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        self.logger = structlog.get_logger().bind(circuit_breaker=name)
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
                self.logger.info("Circuit breaker entering half-open state")
            else:
                raise Exception(f"Circuit breaker '{self.name}' is open")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
                self.logger.info("Circuit breaker closed")
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                self.logger.error("Circuit breaker opened", failures=self.failure_count)
            raise


class BaseAgentV2(ABC):
    """
    Enhanced base class for all agents with production-grade features.
    
    Features:
    - Unified initialization with retry logic
    - Comprehensive error handling
    - Graceful degradation
    - Three-tier health monitoring
    - Circuit breaker pattern
    - Automatic recovery
    """
    
    def __init__(
        self,
        agent_id: str,
        kafka_bootstrap_servers: str = None,
        log_level: str = "INFO",
        allow_sqlite_fallback: bool = False,
        max_db_retries: int = 5,
        max_kafka_retries: int = 10
    ):
        self.agent_id = agent_id
        self.agent_name = agent_id
        
        # Configuration
        self.kafka_bootstrap_servers = (
            os.getenv("KAFKA_BOOTSTRAP_SERVERS") or 
            kafka_bootstrap_servers or 
            "localhost:9092"
        )
        self.allow_sqlite_fallback = allow_sqlite_fallback
        self.max_db_retries = max_db_retries
        self.max_kafka_retries = max_kafka_retries
        
        # Status tracking
        self.status = AgentStatus.STOPPED
        self.degradation_level = DegradationLevel.FULL
        self.start_time = None
        self.error_count = 0
        self.last_error = None
        
        # Service status
        self.db_status = ServiceStatus.DISCONNECTED
        self.kafka_status = ServiceStatus.DISCONNECTED
        self.redis_status = ServiceStatus.DISCONNECTED
        
        # Setup structured logging
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        self.logger = structlog.get_logger().bind(agent_id=self.agent_id)
        
        # Kafka components
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumer: Optional[AIOKafkaConsumer] = None
        
        # Message handlers
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.register_default_handlers()
        
        # Performance metrics
        self.metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "errors_handled": 0,
            "avg_response_time": 0.0,
            "db_queries": 0,
            "kafka_reconnects": 0
        }
        
        # Database components
        self.db_manager: Optional[DatabaseManager] = None
        self.db_helper: Optional[DatabaseHelper] = None
        self._db_initialized = False
        self.db_type = "none"  # "postgresql", "sqlite", "none"
        
        # Circuit breakers
        self.db_circuit_breaker = CircuitBreaker(name="database")
        self.kafka_circuit_breaker = CircuitBreaker(name="kafka")
        
        # Shutdown event
        self.shutdown_event = asyncio.Event()
    
    def register_default_handlers(self):
        """Register default message handlers."""
        self.message_handlers[MessageType.HEALTH_CHECK] = self._handle_health_check
    
    async def initialize_database(self, max_retries: int = None, retry_delay: int = 2) -> bool:
        """
        Initialize database with retry logic and fallback.
        
        Args:
            max_retries: Maximum number of retry attempts (default: self.max_db_retries)
            retry_delay: Base delay between retries in seconds
            
        Returns:
            True if initialization successful, False otherwise
        """
        if not DATABASE_AVAILABLE:
            self.logger.warning("Database components not available")
            self.db_status = ServiceStatus.DISCONNECTED
            return False
        
        max_retries = max_retries or self.max_db_retries
        self.db_status = ServiceStatus.INITIALIZING
        
        for attempt in range(max_retries):
            try:
                self.logger.info(
                    "Initializing database",
                    attempt=attempt + 1,
                    max_retries=max_retries
                )
                
                # Create database configuration from environment
                db_config = DatabaseConfig(
                    host=os.getenv("DATABASE_HOST", "localhost"),
                    port=int(os.getenv("DATABASE_PORT", "5432")),
                    database=os.getenv("DATABASE_NAME", "multi_agent_ecommerce"),
                    username=os.getenv("DATABASE_USER", "postgres"),
                    password=os.getenv("DATABASE_PASSWORD", "postgres"),
                    pool_size=int(os.getenv("DATABASE_POOL_SIZE", "10")),
                    max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
                )
                
                # Initialize database manager
                self.db_manager = DatabaseManager(db_config)
                await self.db_manager.initialize_async()
                
                # Initialize database helper
                self.db_helper = get_db_helper(self.db_manager)
                
                self._db_initialized = True
                self.db_type = "postgresql"
                self.db_status = ServiceStatus.CONNECTED
                
                self.logger.info("Database initialized successfully", db_type="postgresql")
                return True
                
            except Exception as e:
                self.logger.warning(
                    "Database initialization attempt failed",
                    attempt=attempt + 1,
                    error=str(e)
                )
                
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    wait_time = retry_delay * (2 ** attempt) * (0.5 + random.random() * 0.5)
                    self.logger.info("Retrying database initialization", wait_seconds=wait_time)
                    await asyncio.sleep(wait_time)
                else:
                    # All retries exhausted
                    if self.allow_sqlite_fallback:
                        self.logger.warning("Falling back to SQLite")
                        return await self._initialize_sqlite_fallback()
                    else:
                        self.db_status = ServiceStatus.FAILED
                        self.logger.error("Database initialization failed after all retries")
                        # Don't raise - allow agent to continue in degraded mode
                        return False
        
        return False
    
    async def _initialize_sqlite_fallback(self) -> bool:
        """Initialize SQLite fallback database."""
        try:
            # TODO: Implement SQLite fallback
            self.logger.warning("SQLite fallback not yet implemented")
            self.db_status = ServiceStatus.DEGRADED
            self.db_type = "sqlite"
            self.degradation_level = DegradationLevel.DB_FALLBACK
            return True
        except Exception as e:
            self.logger.error("SQLite fallback failed", error=str(e))
            self.db_status = ServiceStatus.FAILED
            return False
    
    async def _wait_for_kafka_ready(self, timeout: int = 60) -> bool:
        """
        Wait for Kafka to be ready (GroupCoordinator available).
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if Kafka is ready, False if timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Try to create a temporary consumer to check if Kafka is ready
                test_consumer = AIOKafkaConsumer(
                    bootstrap_servers=self.kafka_bootstrap_servers,
                    group_id=f"{self.agent_id}_test",
                    api_version='auto'
                )
                await test_consumer.start()
                await test_consumer.stop()
                self.logger.info("Kafka is ready")
                return True
            except GroupCoordinatorNotAvailableError:
                self.logger.debug("Kafka GroupCoordinator not available yet, waiting...")
                await asyncio.sleep(2)
            except Exception as e:
                self.logger.debug("Kafka not ready", error=str(e))
                await asyncio.sleep(2)
        
        self.logger.warning("Kafka readiness check timed out", timeout=timeout)
        return False
    
    async def initialize_kafka(self, max_retries: int = None, retry_delay: int = 3) -> bool:
        """
        Initialize Kafka with retry logic and graceful degradation.
        
        Args:
            max_retries: Maximum number of retry attempts (default: self.max_kafka_retries)
            retry_delay: Base delay between retries in seconds
            
        Returns:
            True if initialization successful, False otherwise
        """
        max_retries = max_retries or self.max_kafka_retries
        self.kafka_status = ServiceStatus.INITIALIZING
        
        # First, wait for Kafka to be ready
        kafka_ready = await self._wait_for_kafka_ready(timeout=30)
        if not kafka_ready:
            self.logger.warning("Kafka not ready, will retry initialization")
        
        for attempt in range(max_retries):
            try:
                self.logger.info(
                    "Initializing Kafka",
                    attempt=attempt + 1,
                    max_retries=max_retries
                )
                
                # Initialize Kafka producer
                self.producer = AIOKafkaProducer(
                    bootstrap_servers=self.kafka_bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    api_version='auto',
                    request_timeout_ms=30000,
                    retry_backoff_ms=100
                )
                await self.producer.start()
                
                # Initialize Kafka consumer
                self.consumer = AIOKafkaConsumer(
                    f"{self.agent_id}_topic",
                    "broadcast_topic",
                    bootstrap_servers=self.kafka_bootstrap_servers,
                    group_id=f"{self.agent_id}_group",
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    auto_offset_reset='latest',
                    api_version='auto',
                    request_timeout_ms=30000
                )
                await self.consumer.start()
                
                self.kafka_status = ServiceStatus.CONNECTED
                self.logger.info("Kafka initialized successfully")
                return True
                
            except Exception as e:
                self.logger.warning(
                    "Kafka initialization attempt failed",
                    attempt=attempt + 1,
                    error=str(e)
                )
                
                # Clean up partial initialization
                if self.producer:
                    try:
                        await self.producer.stop()
                    except:
                        pass
                    self.producer = None
                
                if self.consumer:
                    try:
                        await self.consumer.stop()
                    except:
                        pass
                    self.consumer = None
                
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    wait_time = retry_delay * (2 ** attempt) * (0.5 + random.random() * 0.5)
                    self.logger.info("Retrying Kafka initialization", wait_seconds=wait_time)
                    await asyncio.sleep(wait_time)
                else:
                    # All retries exhausted - graceful degradation
                    self.kafka_status = ServiceStatus.DEGRADED
                    self.degradation_level = max(self.degradation_level, DegradationLevel.NO_KAFKA)
                    self.logger.error(
                        "Kafka initialization failed, continuing in degraded mode (API-only)"
                    )
                    return False
        
        return False
    
    async def start(self):
        """Start the agent and initialize all components."""
        try:
            self.status = AgentStatus.STARTING
            self.start_time = datetime.now()
            
            self.logger.info("Starting agent", agent_id=self.agent_id)
            
            # Initialize database
            db_success = await self.initialize_database()
            if not db_success:
                self.logger.warning("Agent starting without database connection")
            
            # Initialize Kafka
            kafka_success = await self.initialize_kafka()
            if not kafka_success:
                self.logger.warning("Agent starting without Kafka connection")
            
            # Start agent-specific initialization
            await self.initialize()
            
            # Determine overall status
            if self.degradation_level == DegradationLevel.FULL:
                self.status = AgentStatus.RUNNING
            else:
                self.status = AgentStatus.DEGRADED
            
            # Send agent started notification (if Kafka available)
            if self.producer:
                try:
                    await self.send_message(
                        recipient_agent="monitoring_agent",
                        message_type=MessageType.AGENT_STARTED,
                        payload={
                            "agent_id": self.agent_id,
                            "start_time": self.start_time.isoformat(),
                            "degradation_level": self.degradation_level.value
                        }
                    )
                except:
                    pass  # Don't fail if notification fails
            
            self.logger.info(
                "Agent started",
                status=self.status.value,
                degradation_level=self.degradation_level.value
            )
            
            # Start message processing loop (if Kafka available)
            if self.consumer:
                await self._message_loop()
            else:
                # Keep agent running without message loop
                while not self.shutdown_event.is_set():
                    await asyncio.sleep(1)
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.last_error = str(e)
            self.error_count += 1
            self.logger.error("Failed to start agent", error=str(e))
            raise
    
    async def stop(self):
        """Stop the agent gracefully."""
        try:
            self.status = AgentStatus.STOPPING
            self.logger.info("Stopping agent")
            
            # Signal shutdown
            self.shutdown_event.set()
            
            # Send agent stopped notification (if Kafka available)
            if self.producer:
                try:
                    await self.send_message(
                        recipient_agent="monitoring_agent",
                        message_type=MessageType.AGENT_STOPPED,
                        payload={
                            "agent_id": self.agent_id,
                            "stop_time": datetime.now().isoformat()
                        }
                    )
                except:
                    pass  # Don't fail if notification fails
            
            # Cleanup agent-specific resources
            await self.cleanup()
            
            # Stop Kafka components
            if self.consumer:
                await self.consumer.stop()
            if self.producer:
                await self.producer.stop()
            
            # Close database connection
            if self.db_manager:
                await self.db_manager.close()
            
            self.status = AgentStatus.STOPPED
            self.logger.info("Agent stopped successfully")
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.last_error = str(e)
            self.logger.error("Error stopping agent", error=str(e))
    
    async def send_message(
        self,
        recipient_agent: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
        priority: int = 0
    ):
        """Send a message to another agent."""
        if not self.producer:
            raise RuntimeError("Kafka producer not available - agent in degraded mode")
        
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            sender_agent=self.agent_id,
            recipient_agent=recipient_agent,
            message_type=message_type,
            payload=payload,
            timestamp=datetime.now(),
            correlation_id=correlation_id,
            priority=priority
        )
        
        try:
            topic = f"{recipient_agent}_topic" if recipient_agent != "broadcast" else "broadcast_topic"
            
            await self.producer.send_and_wait(
                topic,
                value=message.to_dict(),
                key=message.message_id
            )
            
            self.metrics["messages_sent"] += 1
            
            self.logger.debug(
                "Message sent",
                message_id=message.message_id,
                recipient=recipient_agent,
                message_type=message_type.value
            )
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            self.logger.error(
                "Failed to send message",
                error=str(e),
                recipient=recipient_agent,
                message_type=message_type.value
            )
            raise
    
    async def _message_loop(self):
        """Main message processing loop."""
        self.logger.info("Starting message processing loop")
        
        try:
            async for message_data in self.consumer:
                if self.shutdown_event.is_set():
                    break
                
                try:
                    message = AgentMessage.from_dict(message_data.value)
                    self.metrics["messages_received"] += 1
                    
                    # Process message if it's for this agent or broadcast
                    if message.recipient_agent in [self.agent_id, "broadcast"]:
                        await self._handle_message(message)
                    
                except Exception as e:
                    self.error_count += 1
                    self.last_error = str(e)
                    self.logger.error("Error processing message", error=str(e))
        
        except Exception as e:
            self.logger.error("Message loop error", error=str(e))
            # Try to reconnect to Kafka
            self.metrics["kafka_reconnects"] += 1
            await self.initialize_kafka()
    
    async def _handle_message(self, message: AgentMessage):
        """Handle a received message."""
        handler = self.message_handlers.get(message.message_type)
        
        if handler:
            start_time = datetime.now()
            await handler(message)
            
            # Update response time metric
            response_time = (datetime.now() - start_time).total_seconds()
            self.metrics["avg_response_time"] = (
                (self.metrics["avg_response_time"] * (self.metrics["messages_received"] - 1) + response_time) /
                self.metrics["messages_received"]
            )
        else:
            self.logger.warning(
                "No handler for message type",
                message_type=message.message_type.value,
                message_id=message.message_id
            )
    
    async def _handle_health_check(self, message: AgentMessage):
        """Handle health check requests."""
        health_status = self.get_health_status()
        
        if self.producer:
            await self.send_message(
                recipient_agent=message.sender_agent,
                message_type=MessageType.HEALTH_CHECK,
                payload=health_status.dict(),
                correlation_id=message.correlation_id
            )
    
    def get_health_status(self) -> HealthStatus:
        """Get current health status of the agent."""
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        return HealthStatus(
            agent_id=self.agent_id,
            status=self.status,
            degradation_level=self.degradation_level,
            uptime_seconds=uptime,
            last_heartbeat=datetime.now(),
            error_count=self.error_count,
            last_error=self.last_error,
            performance_metrics=self.metrics,
            dependencies={
                "database": self.db_status,
                "kafka": self.kafka_status,
                "redis": self.redis_status
            }
        )
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        """Register a message handler for a specific message type."""
        self.message_handlers[message_type] = handler
        self.logger.debug("Handler registered", message_type=message_type.value)
    
    @abstractmethod
    async def initialize(self):
        """Initialize agent-specific components. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Cleanup agent-specific resources. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process agent-specific business logic. Must be implemented by subclasses."""
        pass


@asynccontextmanager
async def agent_lifecycle(agent: BaseAgentV2):
    """Context manager for agent lifecycle management."""
    try:
        await agent.start()
        yield agent
    finally:
        await agent.stop()

