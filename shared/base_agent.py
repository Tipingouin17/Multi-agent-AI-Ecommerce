"""
Base Agent Framework for Multi-Agent E-commerce System

This module provides the foundational classes and interfaces for all agents
in the multi-agent e-commerce system. It includes communication protocols,
health monitoring, and standardized message handling.
"""

import asyncio
import json
import logging
import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

import structlog
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Standard message types for inter-agent communication."""
    # Order Management
    ORDER_CREATED = "order_created"
    ORDER_UPDATED = "order_updated"
    ORDER_CANCELLED = "order_cancelled"
    
    # Inventory Management
    INVENTORY_UPDATE = "inventory_update"
    STOCK_ALERT = "stock_alert"
    
    # Pricing
    PRICE_UPDATE = "price_update"
    COMPETITOR_PRICE_UPDATE = "competitor_price_update"
    
    # Logistics
    CARRIER_SELECTED = "carrier_selected"
    WAREHOUSE_SELECTED = "warehouse_selected"
    SHIPMENT_CREATED = "shipment_created"
    
    # Returns & Customer Service
    RETURN_REQUESTED = "return_requested"
    RETURN_APPROVED = "return_approved"
    RETURN_REJECTED = "return_rejected"
    
    # Product Management
    PRODUCT_CREATED = "product_created"
    PRODUCT_UPDATED = "product_updated"
    PRODUCT_DELETED = "product_deleted"
    
    # System & Monitoring
    ERROR_DETECTED = "error_detected"
    HEALTH_CHECK = "health_check"
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    SYSTEM_METRICS = "system_metrics"
    
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
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"


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
    priority: int = 0  # 0=normal, 1=high, 2=critical
    
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
    uptime_seconds: float
    last_heartbeat: datetime
    error_count: int = 0
    last_error: Optional[str] = None
    performance_metrics: Dict[str, float] = Field(default_factory=dict)


class BaseAgent(ABC):
    """
    Base class for all agents in the multi-agent system.
    
    Provides common functionality including:
    - Kafka-based messaging
    - Health monitoring
    - Logging
    - Error handling
    - Graceful shutdown
    """
    
    def __init__(
        self,
        agent_id: str,
        kafka_bootstrap_servers: str = None,
        log_level: str = "INFO"
    ):
        self.agent_id = agent_id
        # Read from environment variable first, then use parameter, finally fall back to default
        self.kafka_bootstrap_servers = (
            os.getenv("KAFKA_BOOTSTRAP_SERVERS") or 
            kafka_bootstrap_servers or 
            "localhost:9092"
        )
        self.status = AgentStatus.STOPPED
        self.start_time = None
        self.error_count = 0
        self.last_error = None
        
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
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
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
            "avg_response_time": 0.0
        }
        
        # Shutdown event
        self.shutdown_event = asyncio.Event()
    
    def register_default_handlers(self):
        """Register default message handlers."""
        self.message_handlers[MessageType.HEALTH_CHECK] = self._handle_health_check
    
    async def start(self):
        """Start the agent and initialize all components."""
        try:
            self.status = AgentStatus.STARTING
            self.start_time = datetime.now()
            
            self.logger.info("Starting agent", agent_id=self.agent_id)
            
            # Initialize Kafka producer
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            await self.producer.start()
            
            # Initialize Kafka consumer
            self.consumer = AIOKafkaConsumer(
                f"{self.agent_id}_topic",
                "broadcast_topic",  # All agents listen to broadcast messages
                bootstrap_servers=self.kafka_bootstrap_servers,
                group_id=f"{self.agent_id}_group",
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest'
            )
            await self.consumer.start()
            
            # Start agent-specific initialization
            await self.initialize()
            
            self.status = AgentStatus.RUNNING
            
            # Send agent started notification
            await self.send_message(
                recipient_agent="monitoring_agent",
                message_type=MessageType.AGENT_STARTED,
                payload={"agent_id": self.agent_id, "start_time": self.start_time.isoformat()}
            )
            
            self.logger.info("Agent started successfully", agent_id=self.agent_id)
            
            # Start message processing loop
            await self._message_loop()
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.last_error = str(e)
            self.error_count += 1
            self.logger.error("Failed to start agent", error=str(e), agent_id=self.agent_id)
            raise
    
    async def stop(self):
        """Stop the agent gracefully."""
        try:
            self.status = AgentStatus.STOPPING
            self.logger.info("Stopping agent", agent_id=self.agent_id)
            
            # Signal shutdown
            self.shutdown_event.set()
            
            # Send agent stopped notification
            if self.producer:
                await self.send_message(
                    recipient_agent="monitoring_agent",
                    message_type=MessageType.AGENT_STOPPED,
                    payload={"agent_id": self.agent_id, "stop_time": datetime.now().isoformat()}
                )
            
            # Cleanup agent-specific resources
            await self.cleanup()
            
            # Stop Kafka components
            if self.consumer:
                await self.consumer.stop()
            if self.producer:
                await self.producer.stop()
            
            self.status = AgentStatus.STOPPED
            self.logger.info("Agent stopped successfully", agent_id=self.agent_id)
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.last_error = str(e)
            self.logger.error("Error stopping agent", error=str(e), agent_id=self.agent_id)
    
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
            raise RuntimeError("Agent not started - producer not available")
        
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
            # Determine topic based on recipient
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
        try:
            async for message in self.consumer:
                if self.shutdown_event.is_set():
                    break
                
                try:
                    # Parse message
                    agent_message = AgentMessage.from_dict(message.value)
                    
                    # Check if message is for this agent or broadcast
                    if (agent_message.recipient_agent != self.agent_id and 
                        agent_message.recipient_agent != "broadcast"):
                        continue
                    
                    self.metrics["messages_received"] += 1
                    
                    self.logger.debug(
                        "Message received",
                        message_id=agent_message.message_id,
                        sender=agent_message.sender_agent,
                        message_type=agent_message.message_type.value
                    )
                    
                    # Handle message
                    await self._handle_message(agent_message)
                    
                except Exception as e:
                    self.error_count += 1
                    self.last_error = str(e)
                    self.metrics["errors_handled"] += 1
                    self.logger.error("Error processing message", error=str(e))
                    
                    # Send error notification to monitoring agent
                    await self.send_message(
                        recipient_agent="monitoring_agent",
                        message_type=MessageType.ERROR_DETECTED,
                        payload={
                            "agent_id": self.agent_id,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }
                    )
        
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.last_error = str(e)
            self.logger.error("Message loop error", error=str(e))
    
    async def _handle_message(self, message: AgentMessage):
        """Route message to appropriate handler."""
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
            uptime_seconds=uptime,
            last_heartbeat=datetime.now(),
            error_count=self.error_count,
            last_error=self.last_error,
            performance_metrics=self.metrics
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
async def agent_lifecycle(agent: BaseAgent):
    """Context manager for agent lifecycle management."""
    try:
        await agent.start()
        yield agent
    finally:
        await agent.stop()


# Utility functions for agent management
async def create_and_run_agent(agent_class, **kwargs):
    """Create and run an agent with proper lifecycle management."""
    agent = agent_class(**kwargs)
    
    async with agent_lifecycle(agent):
        # Keep agent running until interrupted
        try:
            while not agent.shutdown_event.is_set():
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            agent.logger.info("Received shutdown signal")
            agent.shutdown_event.set()


def setup_agent_logging(agent_id: str, log_level: str = "INFO") -> structlog.BoundLogger:
    """Setup structured logging for an agent."""
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
    
    logger = structlog.get_logger().bind(agent_id=agent_id)
    logger.setLevel(getattr(logging, log_level.upper()))
    return logger
