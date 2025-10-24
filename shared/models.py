"""
Shared Data Models for Multi-Agent E-commerce System

This module contains all the data models used across the multi-agent system.
These models ensure consistency and type safety across all agents.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, DateTime, Numeric, Integer, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


# Enums
class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"
    REFUNDED = "refunded"


class ProductCondition(str, Enum):
    """Product condition enumeration."""
    NEW = "new"
    REFURBISHED = "refurbished"
    USED = "used"
    DAMAGED = "damaged"


class RefurbishedGrade(str, Enum):
    """Refurbished product grade enumeration."""
    GRADE_A = "A"  # Excellent condition
    GRADE_B = "B"  # Good condition
    GRADE_C = "C"  # Fair condition


class ChannelType(str, Enum):
    """Sales channel enumeration."""
    SHOPIFY = "shopify"
    AMAZON = "amazon"
    EBAY = "ebay"
    DIRECT = "direct"
    WHOLESALE = "wholesale"


class CarrierType(str, Enum):
    """Carrier type enumeration."""
    UPS = "ups"
    FEDEX = "fedex"
    DHL = "dhl"
    USPS = "usps"
    COLIS_PRIVE = "colis_prive"
    CHRONOPOST = "chronopost"
    COLISSIMO = "colissimo"


class ShipmentStatus(str, Enum):
    """Shipment status enumeration."""
    PENDING = "pending"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED_DELIVERY = "failed_delivery"
    RETURNED = "returned"


# Pydantic Models (for API and validation)
class Address(BaseModel):
    """Address model."""
    street: str
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CustomerBase(BaseModel):
    """Base customer model."""
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    shipping_address: Address
    billing_address: Optional[Address] = None


class Customer(CustomerBase):
    """Complete customer model."""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    """Base product model."""
    name: str
    description: Optional[str] = None
    category: str
    brand: str
    sku: str
    price: Decimal
    cost: Decimal
    weight: Decimal  # in kg
    dimensions: Dict[str, float]  # length, width, height in cm
    condition: ProductCondition
    grade: Optional[RefurbishedGrade] = None
    
    @validator('price', 'cost')
    def validate_positive_amounts(cls, v):
        if v < 0:
            raise ValueError('Price and cost must be positive')
        return v
    
    @validator('weight')
    def validate_positive_weight(cls, v):
        if v <= 0:
            raise ValueError('Weight must be positive')
        return v


class Product(ProductBase):
    """Complete product model."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OrderItemBase(BaseModel):
    """Base order item model."""
    product_id: UUID
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    
    @validator('quantity')
    def validate_positive_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v


class OrderItem(OrderItemBase):
    """Complete order item model."""
    id: str
    order_id: str
    
    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    """Base order model."""
    customer_id: str
    channel: ChannelType
    channel_order_id: str  # Original order ID from the channel
    status: OrderStatus
    items: List[OrderItemBase]
    shipping_address: Address
    billing_address: Address
    subtotal: Decimal
    shipping_cost: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    notes: Optional[str] = None


class Order(OrderBase):
    """Complete order model."""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WarehouseBase(BaseModel):
    """Base warehouse model."""
    name: str
    address: Address
    capacity: int
    operational_hours: Dict[str, str]  # day -> "HH:MM-HH:MM"
    contact_email: str
    contact_phone: str


class Warehouse(WarehouseBase):
    """Complete warehouse model."""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class InventoryBase(BaseModel):
    """Base inventory model."""
    product_id: str
    warehouse_id: str
    quantity: int
    reserved_quantity: int = 0
    reorder_point: int
    max_stock: int
    
    @validator('quantity', 'reserved_quantity', 'reorder_point', 'max_stock')
    def validate_non_negative(cls, v):
        if v < 0:
            raise ValueError('Inventory quantities must be non-negative')
        return v


class Inventory(InventoryBase):
    """Complete inventory model."""
    id: str
    last_updated: datetime
    
    class Config:
        from_attributes = True


class CarrierBase(BaseModel):
    """Base carrier model."""
    name: str
    carrier_type: CarrierType
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    base_rate: Decimal
    per_kg_rate: Decimal
    max_weight: Decimal
    max_dimensions: Dict[str, float]
    delivery_time_days: int
    tracking_url_template: str


class Carrier(CarrierBase):
    """Complete carrier model."""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ShipmentBase(BaseModel):
    """Base shipment model."""
    order_id: str
    carrier_id: str
    tracking_number: str
    status: ShipmentStatus
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    shipping_cost: Decimal
    weight: Decimal
    dimensions: Dict[str, float]


class Shipment(ShipmentBase):
    """Complete shipment model."""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# SQLAlchemy Models (for database)
class CustomerDB(Base):
    """Customer database model."""
    __tablename__ = "customers"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String)
    shipping_address = Column(JSONB, nullable=False)
    billing_address = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = relationship("OrderDB", back_populates="customer")


class ProductDB(Base):
    """Product database model."""
    __tablename__ = "products"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    sku = Column(String, unique=True, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    cost = Column(Numeric(10, 2), nullable=False)
    weight = Column(Numeric(8, 3), nullable=False)
    dimensions = Column(JSONB)
    condition = Column(String, nullable=False)
    grade = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    inventory_items = relationship("InventoryDB", back_populates="product")
    order_items = relationship("OrderItemDB", back_populates="product")


class WarehouseDB(Base):
    """Warehouse database model."""
    __tablename__ = "warehouses"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    address = Column(JSONB, nullable=False)
    capacity = Column(Integer, nullable=False)
    operational_hours = Column(JSONB, nullable=False)
    contact_email = Column(String, nullable=False)
    contact_phone = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    inventory_items = relationship("InventoryDB", back_populates="warehouse")


class InventoryDB(Base):
    """Inventory database model."""
    __tablename__ = "inventory"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    reserved_quantity = Column(Integer, nullable=False, default=0)
    reorder_point = Column(Integer, nullable=False)
    max_stock = Column(Integer, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = relationship("ProductDB", back_populates="inventory_items")
    warehouse = relationship("WarehouseDB", back_populates="inventory_items")


class OrderDB(Base):
    """Order database model."""
    __tablename__ = "orders"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    channel = Column(String, nullable=False)
    channel_order_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    shipping_address = Column(JSONB, nullable=False)
    billing_address = Column(JSONB, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    shipping_cost = Column(Numeric(10, 2), nullable=False)
    tax_amount = Column(Numeric(10, 2), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("CustomerDB", back_populates="orders")
    items = relationship("OrderItemDB", back_populates="order")
    shipments = relationship("ShipmentDB", back_populates="order")


class OrderItemDB(Base):
    """Order item database model."""
    __tablename__ = "order_items"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = Column(PGUUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    # Relationships
    order = relationship("OrderDB", back_populates="items")
    product = relationship("ProductDB", back_populates="order_items")


class CarrierDB(Base):
    """Carrier database model."""
    __tablename__ = "carriers"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    carrier_type = Column(String, nullable=False)
    api_endpoint = Column(String)
    api_key = Column(String)
    base_rate = Column(Numeric(8, 2), nullable=False)
    per_kg_rate = Column(Numeric(8, 2), nullable=False)
    max_weight = Column(Numeric(8, 3), nullable=False)
    max_dimensions = Column(JSONB, nullable=False)
    delivery_time_days = Column(Integer, nullable=False)
    tracking_url_template = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    shipments = relationship("ShipmentDB", back_populates="carrier")


class ShipmentDB(Base):
    """Shipment database model."""
    __tablename__ = "shipments"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = Column(PGUUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    carrier_id = Column(PGUUID(as_uuid=True), ForeignKey("carriers.id"), nullable=False)
    tracking_number = Column(String, unique=True, nullable=False)
    status = Column(String, nullable=False)
    estimated_delivery = Column(DateTime)
    actual_delivery = Column(DateTime)
    shipping_cost = Column(Numeric(10, 2), nullable=False)
    weight = Column(Numeric(8, 3), nullable=False)
    dimensions = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order = relationship("OrderDB", back_populates="shipments")
    carrier = relationship("CarrierDB", back_populates="shipments")


class AgentMetricsDB(Base):
    """Agent metrics database model."""
    __tablename__ = "agent_metrics"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_name = Column(String, nullable=False)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Numeric(15, 4), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class SystemEventDB(Base):
    """System event database model."""
    __tablename__ = "system_events"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type = Column(String, nullable=False)
    event_data = Column(JSONB, nullable=False)
    agent_name = Column(String)
    severity = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


# Message models
class AgentMessage(BaseModel):
    """Agent message model."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    sender: str
    recipient: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None


class AgentResponse(BaseModel):
    """Agent response model."""
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel):
    """Paginated response model."""
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int


# Configuration models
class DatabaseConfig(BaseModel):
    """Database configuration model."""
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(default="multi_agent_ecommerce")
    username: str = Field(default="postgres")
    password: str = Field(default="postgres")
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    echo: bool = False
    
    def __init__(self, **data):
        """Initialize DatabaseConfig from environment variables or provided data."""
        import os
        # Support both DATABASE_* and POSTGRES_* prefixes for compatibility
        if not data:
            # Read environment variables
            db_password = os.getenv('DATABASE_PASSWORD') or os.getenv('POSTGRES_PASSWORD') or 'postgres'
            print(f"[DatabaseConfig] DATABASE_PASSWORD from env: {os.getenv('DATABASE_PASSWORD')}")
            print(f"[DatabaseConfig] Using password: {db_password}")
            data = {
                'host': os.getenv('DATABASE_HOST') or os.getenv('POSTGRES_HOST') or 'localhost',
                'port': int(os.getenv('DATABASE_PORT') or os.getenv('POSTGRES_PORT') or '5432'),
                'database': os.getenv('DATABASE_NAME') or os.getenv('POSTGRES_NAME') or 'multi_agent_ecommerce',
                'username': os.getenv('DATABASE_USER') or os.getenv('POSTGRES_USER') or 'postgres',
                'password': db_password,
            }
        super().__init__(**data)
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class KafkaConfig(BaseModel):
    """Kafka configuration model."""
    bootstrap_servers: str = "localhost:9092"
    group_id: str = "multi_agent_group"
    auto_offset_reset: str = "latest"


class RedisConfig(BaseModel):
    """Redis configuration model."""
    host: str = "localhost"
    port: int = 6379
    database: int = 0
    password: Optional[str] = None
    
    @property
    def url(self) -> str:
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.database}"



# API Response Models
class APIResponse(BaseModel):
    """Standard API response model for external API calls."""
    success: bool
    status_code: int
    data: Optional[Any] = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        }



class StockMovementDB(Base):
    """Stock movement database model"""
    __tablename__ = 'stock_movements'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey('products.id'), nullable=False)
    warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey('warehouses.id'), nullable=False)
    movement_type = Column(String(50), nullable=False)  # 'IN', 'OUT', 'TRANSFER', 'ADJUSTMENT'
    quantity = Column(Integer, nullable=False)
    reference_id = Column(PGUUID(as_uuid=True))  # Order ID, Transfer ID, etc.
    reference_type = Column(String(50))  # 'ORDER', 'TRANSFER', 'ADJUSTMENT'
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255))
    
    # Relationships
    product = relationship("ProductDB")
    warehouse = relationship("WarehouseDB")


class QualityInspectionDB(Base):
    """Quality inspection database model"""
    __tablename__ = 'quality_inspections'
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey('products.id'), nullable=False)
    inspection_type = Column(String(50), nullable=False)  # 'INCOMING', 'OUTGOING', 'RETURN'
    status = Column(String(50), nullable=False)  # 'PASS', 'FAIL', 'CONDITIONAL'
    condition = Column(String(50))
    grade = Column(String(10))
    defects = Column(JSONB)
    notes = Column(Text)
    inspector_id = Column(String(255))
    inspected_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("ProductDB")

# Carrier Configuration Models
class CarrierConfig(BaseModel):
    """Carrier configuration model"""
    carrier_id: str
    carrier_name: str
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    enabled: bool = True
    
class CarrierRate(BaseModel):
    """Carrier rate model"""
    carrier_id: str
    service_level: str
    price: float
    transit_days: int
    

# Message Types for Kafka
class MessageType(str, Enum):
    """Kafka message types"""
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    ORDER_CANCELLED = "order.cancelled"
    INVENTORY_UPDATED = "inventory.updated"
    SHIPMENT_CREATED = "shipment.created"
    SHIPMENT_UPDATED = "shipment.updated"
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    
