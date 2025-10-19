"""
Message schema validation for inter-agent communication.

This module defines strict schemas for all message types to ensure
data integrity and facilitate debugging.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum


class MessagePriority(int, Enum):
    """Message priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class BaseMessagePayload(BaseModel):
    """Base class for all message payloads."""
    
    class Config:
        extra = "forbid"  # Forbid extra fields
        validate_assignment = True


class OrderCreatedPayload(BaseMessagePayload):
    """Payload for ORDER_CREATED message."""
    order_id: str = Field(..., min_length=1, description="Unique order identifier")
    customer_id: str = Field(..., min_length=1, description="Customer identifier")
    channel: str = Field(..., min_length=1, description="Sales channel")
    total_amount: Decimal = Field(..., gt=0, description="Total order amount")
    items_count: int = Field(..., ge=1, description="Number of items")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")


class OrderUpdatedPayload(BaseMessagePayload):
    """Payload for ORDER_UPDATED message."""
    order_id: str = Field(..., min_length=1, description="Order identifier")
    old_status: str = Field(..., min_length=1, description="Previous order status")
    new_status: str = Field(..., min_length=1, description="New order status")
    updated_at: datetime = Field(default_factory=datetime.now, description="Update timestamp")
    reason: Optional[str] = Field(None, description="Reason for status change")


class InventoryUpdatePayload(BaseMessagePayload):
    """Payload for INVENTORY_UPDATE message."""
    product_id: str = Field(..., min_length=1, description="Product identifier")
    warehouse_id: str = Field(..., min_length=1, description="Warehouse identifier")
    old_quantity: int = Field(..., ge=0, description="Previous quantity")
    new_quantity: int = Field(..., ge=0, description="New quantity")
    change_type: str = Field(..., description="Type of change (inbound, outbound, adjustment)")
    reference_id: Optional[str] = Field(None, description="Reference ID (order, transfer, etc.)")
    
    @validator('change_type')
    def validate_change_type(cls, v):
        """Validate change type."""
        valid_types = ['inbound', 'outbound', 'adjustment', 'transfer', 'return']
        if v not in valid_types:
            raise ValueError(f'Change type must be one of {valid_types}')
        return v


class PriceUpdatePayload(BaseMessagePayload):
    """Payload for PRICE_UPDATE message."""
    product_id: str = Field(..., min_length=1, description="Product identifier")
    old_price: Decimal = Field(..., gt=0, description="Previous price")
    new_price: Decimal = Field(..., gt=0, description="New price")
    reason: str = Field(..., min_length=1, description="Reason for price change")
    effective_date: datetime = Field(default_factory=datetime.now, description="Effective date")


class CarrierSelectedPayload(BaseMessagePayload):
    """Payload for CARRIER_SELECTED message."""
    order_id: str = Field(..., min_length=1, description="Order identifier")
    carrier_id: str = Field(..., min_length=1, description="Selected carrier identifier")
    carrier_name: str = Field(..., min_length=1, description="Carrier name")
    service_type: str = Field(..., min_length=1, description="Service type")
    estimated_cost: Decimal = Field(..., gt=0, description="Estimated shipping cost")
    estimated_delivery_date: datetime = Field(..., description="Estimated delivery date")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI confidence score")


class WarehouseSelectedPayload(BaseMessagePayload):
    """Payload for WAREHOUSE_SELECTED message."""
    order_id: str = Field(..., min_length=1, description="Order identifier")
    warehouse_id: str = Field(..., min_length=1, description="Selected warehouse identifier")
    warehouse_name: str = Field(..., min_length=1, description="Warehouse name")
    selection_score: float = Field(..., ge=0.0, le=100.0, description="Selection score")
    distance_km: Optional[float] = Field(None, ge=0, description="Distance to destination")
    estimated_processing_time: int = Field(..., ge=0, description="Estimated processing time in hours")


class ErrorDetectedPayload(BaseMessagePayload):
    """Payload for ERROR_DETECTED message."""
    error_id: str = Field(..., min_length=1, description="Error identifier")
    agent_id: str = Field(..., min_length=1, description="Agent that detected the error")
    error_type: str = Field(..., min_length=1, description="Type of error")
    error_message: str = Field(..., min_length=1, description="Error message")
    severity: str = Field(..., description="Error severity (low, medium, high, critical)")
    context: Dict[str, Any] = Field(default_factory=dict, description="Error context")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    
    @validator('severity')
    def validate_severity(cls, v):
        """Validate severity level."""
        valid_severities = ['low', 'medium', 'high', 'critical']
        if v.lower() not in valid_severities:
            raise ValueError(f'Severity must be one of {valid_severities}')
        return v.lower()


class HealthCheckPayload(BaseMessagePayload):
    """Payload for HEALTH_CHECK message."""
    agent_id: str = Field(..., min_length=1, description="Agent identifier")
    status: str = Field(..., description="Agent status")
    uptime_seconds: float = Field(..., ge=0, description="Agent uptime in seconds")
    memory_usage_mb: Optional[float] = Field(None, ge=0, description="Memory usage in MB")
    cpu_usage_percent: Optional[float] = Field(None, ge=0, le=100, description="CPU usage percentage")
    error_count: int = Field(default=0, ge=0, description="Error count")
    last_error: Optional[str] = Field(None, description="Last error message")


class AgentStartedPayload(BaseMessagePayload):
    """Payload for AGENT_STARTED message."""
    agent_id: str = Field(..., min_length=1, description="Agent identifier")
    start_time: datetime = Field(..., description="Start timestamp")
    version: Optional[str] = Field(None, description="Agent version")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")


class AgentStoppedPayload(BaseMessagePayload):
    """Payload for AGENT_STOPPED message."""
    agent_id: str = Field(..., min_length=1, description="Agent identifier")
    stop_time: datetime = Field(..., description="Stop timestamp")
    reason: str = Field(..., min_length=1, description="Reason for stopping")
    graceful: bool = Field(default=True, description="Whether shutdown was graceful")


class DemandForecastPayload(BaseMessagePayload):
    """Payload for DEMAND_FORECAST message."""
    product_id: str = Field(..., min_length=1, description="Product identifier")
    forecast_period_days: int = Field(..., ge=1, le=365, description="Forecast period in days")
    predicted_demand: int = Field(..., ge=0, description="Predicted demand quantity")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Forecast confidence")
    trend: str = Field(..., description="Demand trend (increasing, stable, decreasing)")
    seasonality_detected: bool = Field(default=False, description="Whether seasonality was detected")


class RiskAlertPayload(BaseMessagePayload):
    """Payload for RISK_ALERT message."""
    alert_id: str = Field(..., min_length=1, description="Alert identifier")
    risk_type: str = Field(..., min_length=1, description="Type of risk")
    severity: str = Field(..., description="Risk severity")
    description: str = Field(..., min_length=1, description="Risk description")
    affected_entities: List[str] = Field(default_factory=list, description="Affected entity IDs")
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended actions")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    
    @validator('severity')
    def validate_severity(cls, v):
        """Validate severity level."""
        valid_severities = ['low', 'medium', 'high', 'critical']
        if v.lower() not in valid_severities:
            raise ValueError(f'Severity must be one of {valid_severities}')
        return v.lower()


class CustomerNotificationPayload(BaseMessagePayload):
    """Payload for CUSTOMER_NOTIFICATION message."""
    customer_id: str = Field(..., min_length=1, description="Customer identifier")
    notification_type: str = Field(..., min_length=1, description="Type of notification")
    channel: str = Field(..., description="Notification channel (email, sms, push)")
    subject: str = Field(..., min_length=1, description="Notification subject")
    message: str = Field(..., min_length=1, description="Notification message")
    reference_id: Optional[str] = Field(None, description="Reference ID (order, shipment, etc.)")
    
    @validator('channel')
    def validate_channel(cls, v):
        """Validate notification channel."""
        valid_channels = ['email', 'sms', 'push', 'webhook']
        if v.lower() not in valid_channels:
            raise ValueError(f'Channel must be one of {valid_channels}')
        return v.lower()


# Mapping of message types to their payload schemas
MESSAGE_PAYLOAD_SCHEMAS = {
    "order_created": OrderCreatedPayload,
    "order_updated": OrderUpdatedPayload,
    "inventory_update": InventoryUpdatePayload,
    "price_update": PriceUpdatePayload,
    "carrier_selected": CarrierSelectedPayload,
    "warehouse_selected": WarehouseSelectedPayload,
    "error_detected": ErrorDetectedPayload,
    "health_check": HealthCheckPayload,
    "agent_started": AgentStartedPayload,
    "agent_stopped": AgentStoppedPayload,
    "demand_forecast": DemandForecastPayload,
    "risk_alert": RiskAlertPayload,
    "customer_notification": CustomerNotificationPayload,
}


def validate_message_payload(message_type: str, payload: Dict[str, Any]) -> BaseMessagePayload:
    """
    Validate message payload against its schema.
    
    Args:
        message_type: Type of message
        payload: Payload data to validate
    
    Returns:
        Validated payload object
    
    Raises:
        ValueError: If message type is unknown or payload is invalid
    """
    schema_class = MESSAGE_PAYLOAD_SCHEMAS.get(message_type)
    
    if schema_class is None:
        raise ValueError(f"Unknown message type: {message_type}")
    
    try:
        return schema_class(**payload)
    except Exception as e:
        raise ValueError(f"Invalid payload for message type '{message_type}': {str(e)}")

