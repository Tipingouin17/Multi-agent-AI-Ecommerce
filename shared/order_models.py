"""
Enhanced Order Models for Multi-Agent E-commerce System

This module contains comprehensive Pydantic models for all order-related features
including order splitting, modifications, gift options, scheduled delivery, and partial shipments.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator


class PriorityLevel(str, Enum):
    """Order priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ModificationType(str, Enum):
    """Types of order modifications."""
    STATUS_CHANGE = "status_change"
    ITEM_ADDED = "item_added"
    ITEM_REMOVED = "item_removed"
    QUANTITY_CHANGED = "quantity_changed"
    ADDRESS_CHANGE = "address_change"
    DELIVERY_DATE_CHANGE = "delivery_date_change"
    PRIORITY_CHANGE = "priority_change"
    GIFT_OPTIONS_CHANGE = "gift_options_change"
    NOTES_CHANGE = "notes_change"


class SplitReason(str, Enum):
    """Reasons for order splitting."""
    MULTI_WAREHOUSE = "multi_warehouse"
    PARTIAL_AVAILABILITY = "partial_availability"
    DELIVERY_SPEED = "delivery_speed"
    CARRIER_LIMITATIONS = "carrier_limitations"
    CUSTOMER_REQUEST = "customer_request"
    COST_OPTIMIZATION = "cost_optimization"


class ShipmentStatus(str, Enum):
    """Status of partial shipments."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETURNED = "returned"


class FulfillmentStrategy(str, Enum):
    """Fulfillment strategies."""
    SINGLE_WAREHOUSE = "single_warehouse"
    SPLIT_SHIPMENT = "split_shipment"
    DROPSHIP = "dropship"
    STORE_PICKUP = "store_pickup"
    HYBRID = "hybrid"


class FulfillmentStatus(str, Enum):
    """Fulfillment plan status."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class DeliveryAttemptStatus(str, Enum):
    """Delivery attempt outcomes."""
    SUCCESSFUL = "successful"
    FAILED = "failed"
    CUSTOMER_NOT_HOME = "customer_not_home"
    ADDRESS_ISSUE = "address_issue"
    REFUSED_BY_CUSTOMER = "refused_by_customer"
    DAMAGED_PACKAGE = "damaged_package"
    WEATHER_DELAY = "weather_delay"
    RESCHEDULED = "rescheduled"


class CancellationStatus(str, Enum):
    """Cancellation request status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"


class RefundStatus(str, Enum):
    """Refund processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class NoteType(str, Enum):
    """Types of order notes."""
    INTERNAL = "internal"
    CUSTOMER = "customer"
    SYSTEM = "system"
    AGENT = "agent"


# ===== Gift Order Models =====

class GiftOptions(BaseModel):
    """Gift order options."""
    is_gift: bool = False
    gift_message: Optional[str] = None
    gift_wrap_type: Optional[str] = None  # 'standard', 'premium', 'custom'
    hide_prices: bool = True
    gift_receipt: bool = True


# ===== Order Modification Models =====

class OrderModification(BaseModel):
    """Model for order modifications."""
    modification_id: str
    order_id: str
    modification_type: ModificationType
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    reason: Optional[str] = None
    modified_by: str  # user_id or agent_id
    modified_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class OrderModificationCreate(BaseModel):
    """Request to create an order modification."""
    order_id: str
    modification_type: ModificationType
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    reason: Optional[str] = None
    modified_by: str
    metadata: Optional[Dict[str, Any]] = None


# ===== Order Split Models =====

class OrderSplit(BaseModel):
    """Model for order splits."""
    split_id: str
    parent_order_id: str
    child_order_id: str
    split_reason: SplitReason
    split_date: datetime
    split_by: Optional[str] = None  # agent_id
    metadata: Optional[Dict[str, Any]] = None


class OrderSplitRequest(BaseModel):
    """Request to split an order."""
    order_id: str
    split_reason: SplitReason
    item_splits: List[Dict[str, Any]]  # List of {item_id, quantity, warehouse_id}
    metadata: Optional[Dict[str, Any]] = None


# ===== Partial Shipment Models =====

class PartialShipmentItem(BaseModel):
    """Item in a partial shipment."""
    shipment_id: str
    order_item_id: int
    quantity: int = Field(gt=0)


class PartialShipment(BaseModel):
    """Model for partial shipments."""
    shipment_id: str
    order_id: str
    shipment_number: int
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    shipped_at: Optional[datetime] = None
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    status: ShipmentStatus = ShipmentStatus.PENDING
    items: List[PartialShipmentItem] = []
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class PartialShipmentCreate(BaseModel):
    """Request to create a partial shipment."""
    order_id: str
    shipment_number: int
    items: List[Dict[str, Any]]  # List of {order_item_id, quantity}
    carrier: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class PartialShipmentUpdate(BaseModel):
    """Request to update a partial shipment."""
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    shipped_at: Optional[datetime] = None
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    status: Optional[ShipmentStatus] = None
    metadata: Optional[Dict[str, Any]] = None


# ===== Order Timeline Models =====

class OrderTimelineEvent(BaseModel):
    """Model for order timeline events."""
    event_id: str
    order_id: str
    event_type: str
    event_description: str
    event_data: Optional[Dict[str, Any]] = None
    triggered_by: Optional[str] = None  # user_id or agent_id
    occurred_at: datetime


class OrderTimelineEventCreate(BaseModel):
    """Request to create a timeline event."""
    order_id: str
    event_type: str
    event_description: str
    event_data: Optional[Dict[str, Any]] = None
    triggered_by: Optional[str] = None


# ===== Order Notes Models =====

class OrderNote(BaseModel):
    """Model for order notes."""
    note_id: str
    order_id: str
    note_type: NoteType
    note_text: str
    is_visible_to_customer: bool = False
    created_by: str
    created_at: datetime
    updated_at: datetime


class OrderNoteCreate(BaseModel):
    """Request to create an order note."""
    order_id: str
    note_type: NoteType
    note_text: str
    is_visible_to_customer: bool = False
    created_by: str


class OrderNoteUpdate(BaseModel):
    """Request to update an order note."""
    note_text: Optional[str] = None
    is_visible_to_customer: Optional[bool] = None


# ===== Order Tags Models =====

class OrderTag(BaseModel):
    """Model for order tags."""
    order_id: str
    tag: str
    added_by: Optional[str] = None
    added_at: datetime


class OrderTagCreate(BaseModel):
    """Request to add a tag to an order."""
    order_id: str
    tag: str
    added_by: Optional[str] = None


# ===== Fulfillment Plan Models =====

class FulfillmentItem(BaseModel):
    """Item in a fulfillment plan."""
    plan_id: str
    order_item_id: int
    quantity: int = Field(gt=0)
    allocated_quantity: int = Field(ge=0, default=0)
    picked_quantity: int = Field(ge=0, default=0)
    packed_quantity: int = Field(ge=0, default=0)


class FulfillmentPlan(BaseModel):
    """Model for order fulfillment plans."""
    plan_id: str
    order_id: str
    warehouse_id: str
    fulfillment_strategy: FulfillmentStrategy
    estimated_ship_date: Optional[datetime] = None
    estimated_delivery_date: Optional[datetime] = None
    priority: int = 0
    status: FulfillmentStatus = FulfillmentStatus.PLANNED
    items: List[FulfillmentItem] = []
    created_at: datetime
    updated_at: datetime


class FulfillmentPlanCreate(BaseModel):
    """Request to create a fulfillment plan."""
    order_id: str
    warehouse_id: str
    fulfillment_strategy: FulfillmentStrategy
    items: List[Dict[str, Any]]  # List of {order_item_id, quantity}
    estimated_ship_date: Optional[datetime] = None
    estimated_delivery_date: Optional[datetime] = None
    priority: int = 0


class FulfillmentPlanUpdate(BaseModel):
    """Request to update a fulfillment plan."""
    estimated_ship_date: Optional[datetime] = None
    estimated_delivery_date: Optional[datetime] = None
    priority: Optional[int] = None
    status: Optional[FulfillmentStatus] = None


# ===== Delivery Attempt Models =====

class DeliveryAttempt(BaseModel):
    """Model for delivery attempts."""
    attempt_id: str
    order_id: str
    shipment_id: Optional[str] = None
    attempt_number: int
    attempted_at: datetime
    status: DeliveryAttemptStatus
    failure_reason: Optional[str] = None
    next_attempt_date: Optional[datetime] = None
    notes: Optional[str] = None


class DeliveryAttemptCreate(BaseModel):
    """Request to record a delivery attempt."""
    order_id: str
    shipment_id: Optional[str] = None
    attempt_number: int
    attempted_at: datetime
    status: DeliveryAttemptStatus
    failure_reason: Optional[str] = None
    next_attempt_date: Optional[datetime] = None
    notes: Optional[str] = None


# ===== Cancellation Request Models =====

class CancellationRequest(BaseModel):
    """Model for order cancellation requests."""
    request_id: str
    order_id: str
    requested_by: str  # customer_id or agent_id
    reason: str
    detailed_reason: Optional[str] = None
    status: CancellationStatus = CancellationStatus.PENDING
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    refund_amount: Optional[Decimal] = None
    refund_status: Optional[RefundStatus] = None
    requested_at: datetime
    completed_at: Optional[datetime] = None


class CancellationRequestCreate(BaseModel):
    """Request to cancel an order."""
    order_id: str
    requested_by: str
    reason: str
    detailed_reason: Optional[str] = None


class CancellationRequestReview(BaseModel):
    """Request to review a cancellation request."""
    request_id: str
    status: CancellationStatus  # 'approved' or 'rejected'
    reviewed_by: str
    review_notes: Optional[str] = None
    refund_amount: Optional[Decimal] = None


# ===== Enhanced Order Models =====

class EnhancedOrderCreate(BaseModel):
    """Enhanced request model for creating a new order."""
    customer_id: str
    channel: str
    channel_order_id: str
    items: List[Dict[str, Any]]
    shipping_address: Dict[str, Any]
    billing_address: Dict[str, Any]
    
    # Gift options
    gift_options: Optional[GiftOptions] = None
    
    # Delivery options
    scheduled_delivery_date: Optional[datetime] = None
    delivery_instructions: Optional[str] = None
    priority_level: PriorityLevel = PriorityLevel.NORMAL
    
    # Additional options
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class EnhancedOrder(BaseModel):
    """Enhanced order model with all features."""
    id: str
    customer_id: str
    channel: str
    channel_order_id: str
    status: str
    items: List[Dict[str, Any]]
    shipping_address: Dict[str, Any]
    billing_address: Dict[str, Any]
    
    # Financial
    subtotal: Decimal
    shipping_cost: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    
    # Gift options
    is_gift: bool = False
    gift_message: Optional[str] = None
    gift_wrap_type: Optional[str] = None
    
    # Delivery
    scheduled_delivery_date: Optional[datetime] = None
    delivery_instructions: Optional[str] = None
    estimated_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    
    # Split order info
    is_split_order: bool = False
    parent_order_id: Optional[str] = None
    split_reason: Optional[str] = None
    
    # Priority and status
    priority_level: PriorityLevel = PriorityLevel.NORMAL
    
    # Cancellation
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    
    # Metadata
    notes: Optional[str] = None
    tags: List[str] = []
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Related data (loaded separately)
    modifications: List[OrderModification] = []
    timeline: List[OrderTimelineEvent] = []
    notes_list: List[OrderNote] = []
    shipments: List[PartialShipment] = []
    fulfillment_plans: List[FulfillmentPlan] = []


class OrderSummary(BaseModel):
    """Summary view of an order."""
    id: str
    customer_id: str
    channel: str
    status: str
    total_amount: Decimal
    is_gift: bool
    is_split_order: bool
    priority_level: PriorityLevel
    scheduled_delivery_date: Optional[datetime] = None
    estimated_delivery_date: Optional[datetime] = None
    created_at: datetime
    split_count: int = 0
    shipment_count: int = 0
    event_count: int = 0


# ===== Bulk Operations Models =====

class BulkOrderUpdate(BaseModel):
    """Request for bulk order updates."""
    order_ids: List[str]
    updates: Dict[str, Any]
    reason: str
    updated_by: str


class BulkTagOperation(BaseModel):
    """Request for bulk tag operations."""
    order_ids: List[str]
    tags: List[str]
    operation: str  # 'add' or 'remove'
    added_by: str


# ===== Analytics Models =====

class OrderAnalytics(BaseModel):
    """Order analytics data."""
    total_orders: int
    pending_orders: int
    processing_orders: int
    shipped_orders: int
    delivered_orders: int
    cancelled_orders: int
    split_orders: int
    gift_orders: int
    total_revenue: Decimal
    average_order_value: Decimal
    orders_by_priority: Dict[str, int]
    orders_by_channel: Dict[str, int]
    fulfillment_rate: float
    on_time_delivery_rate: float


# ===== Search and Filter Models =====

class OrderSearchFilters(BaseModel):
    """Filters for order search."""
    customer_id: Optional[str] = None
    channel: Optional[str] = None
    status: Optional[List[str]] = None
    priority_level: Optional[List[PriorityLevel]] = None
    is_gift: Optional[bool] = None
    is_split_order: Optional[bool] = None
    tags: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    search_query: Optional[str] = None  # Search in order_id, customer_id, notes
    page: int = 1
    per_page: int = 20
    sort_by: str = "created_at"
    sort_order: str = "desc"  # 'asc' or 'desc'


# ===== Response Models =====

class OrderOperationResponse(BaseModel):
    """Response for order operations."""
    success: bool
    message: str
    order_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None


class BulkOperationResponse(BaseModel):
    """Response for bulk operations."""
    success: bool
    message: str
    total_processed: int
    successful: int
    failed: int
    errors: Optional[List[Dict[str, str]]] = None


# Validators

@validator('gift_message')
def validate_gift_message_length(cls, v):
    """Validate gift message length."""
    if v and len(v) > 500:
        raise ValueError('Gift message must not exceed 500 characters')
    return v


@validator('delivery_instructions')
def validate_delivery_instructions_length(cls, v):
    """Validate delivery instructions length."""
    if v and len(v) > 1000:
        raise ValueError('Delivery instructions must not exceed 1000 characters')
    return v

