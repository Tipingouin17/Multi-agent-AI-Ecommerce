"""
Shared Database Models for Multi-Agent E-commerce Platform
All agents use these models to ensure consistency
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, Date, ForeignKey, JSON, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional

Base = declarative_base()

# ============================================================================
# USER & AUTHENTICATION MODELS
# ============================================================================

class User(Base):
    """User model for all personas (admin, merchant, customer)"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # admin, merchant, customer
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(50))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    merchant = relationship("Merchant", back_populates="user", uselist=False)
    customer = relationship("Customer", back_populates="user", uselist=False)
    addresses = relationship("Address", back_populates="user")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "role": self.role,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

# ============================================================================
# MERCHANT MODELS
# ============================================================================

class Merchant(Base):
    """Merchant profile"""
    __tablename__ = "merchants"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    business_name = Column(String(255), nullable=False)
    business_type = Column(String(100))
    tax_id = Column(String(100))
    website = Column(String(255))
    description = Column(Text)
    logo_url = Column(String(500))
    rating = Column(Numeric(3, 2), default=0.00)
    total_sales = Column(Numeric(15, 2), default=0.00)
    total_orders = Column(Integer, default=0)
    commission_rate = Column(Numeric(5, 2), default=10.00)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="merchant")
    products = relationship("Product", back_populates="merchant")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "business_name": self.business_name,
            "business_type": self.business_type,
            "tax_id": self.tax_id,
            "website": self.website,
            "description": self.description,
            "logo_url": self.logo_url,
            "rating": float(self.rating) if self.rating else 0.0,
            "total_sales": float(self.total_sales) if self.total_sales else 0.0,
            "total_orders": self.total_orders,
            "commission_rate": float(self.commission_rate) if self.commission_rate else 10.0,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

# ============================================================================
# PRODUCT MODELS
# ============================================================================

class Category(Base):
    """Product category"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"))
    image_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = relationship("Product", back_populates="category")
    parent = relationship("Category", remote_side=[id], backref="children")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "parent_id": self.parent_id,
            "image_url": self.image_url,
            "is_active": self.is_active,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class Product(Base):
    """Product model"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id", ondelete="CASCADE"))
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"))
    sku = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    short_description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    cost = Column(Numeric(10, 2))
    compare_at_price = Column(Numeric(10, 2))
    weight = Column(Numeric(10, 2))
    dimensions = Column(JSON)
    images = Column(JSON)
    status = Column(String(50), default="draft")
    is_featured = Column(Boolean, default=False)
    rating = Column(Numeric(3, 2), default=0.00)
    review_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    sales_count = Column(Integer, default=0)
    tags = Column(JSON)
    extra_data = Column('metadata', JSON)
    
    # Wizard Step 1 - Basic Information
    display_name = Column(String(255))
    brand = Column(String(255))
    model_number = Column(String(255))
    product_type = Column(String(50), default='simple')
    key_features = Column(JSON)
    
    # Wizard Step 2 - Specifications (dimensions moved from JSON to individual columns)
    dimensions_length = Column(Numeric(8, 2))
    dimensions_width = Column(Numeric(8, 2))
    dimensions_height = Column(Numeric(8, 2))
    dimensions_unit = Column(String(10), default='cm')
    weight_unit = Column(String(10), default='kg')
    material = Column(String(255))
    color = Column(String(100))
    warranty_period = Column(Integer)
    country_of_origin = Column(String(100))
    
    # Wizard Step 4 - Pricing & Costs
    profit_margin = Column(Numeric(5, 2))
    currency = Column(String(3), default='USD')
    
    # Wizard Step 5 - Inventory & Logistics
    shipping_weight = Column(Numeric(8, 3))
    shipping_length = Column(Numeric(8, 2))
    shipping_width = Column(Numeric(8, 2))
    shipping_height = Column(Numeric(8, 2))
    handling_time_days = Column(Integer, default=1)
    requires_shipping = Column(Boolean, default=True)
    is_fragile = Column(Boolean, default=False)
    is_perishable = Column(Boolean, default=False)
    
    # Wizard Step 7 - Compliance
    has_age_restriction = Column(Boolean, default=False)
    min_age = Column(Integer)
    is_hazmat = Column(Boolean, default=False)
    hazmat_class = Column(String(50))
    requires_signature = Column(Boolean, default=False)
    has_export_restrictions = Column(Boolean, default=False)
    export_restriction_countries = Column(JSON)
    safety_warnings = Column(JSON)
    
    # Wizard Step 8 - Publishing
    is_draft = Column(Boolean, default=True)
    published_at = Column(DateTime)
    scheduled_publish_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    merchant = relationship("Merchant", back_populates="products")
    category = relationship("Category", back_populates="products")
    inventory = relationship("Inventory", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "merchant_id": self.merchant_id,
            "category_id": self.category_id,
            "sku": self.sku,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "short_description": self.short_description,
            "price": float(self.price) if self.price else 0.0,
            "cost": float(self.cost) if self.cost else 0.0,
            "compare_at_price": float(self.compare_at_price) if self.compare_at_price else None,
            "weight": float(self.weight) if self.weight else 0.0,
            "dimensions": self.dimensions,
            "images": self.images or [],
            "status": self.status,
            "is_featured": self.is_featured,
            "rating": float(self.rating) if self.rating else 0.0,
            "review_count": self.review_count,
            "view_count": self.view_count,
            "sales_count": self.sales_count,
            "tags": self.tags or [],
            "metadata": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

# ============================================================================
# INVENTORY MODELS
# ============================================================================

class Warehouse(Base):
    """Warehouse model"""
    __tablename__ = "warehouses"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    phone = Column(String(50))
    email = Column(String(255))
    manager_name = Column(String(255))
    capacity = Column(Integer)
    current_utilization = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    extra_data = Column('metadata', JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    inventory = relationship("Inventory", back_populates="warehouse")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "postal_code": self.postal_code,
            "phone": self.phone,
            "email": self.email,
            "manager_name": self.manager_name,
            "capacity": self.capacity,
            "current_utilization": self.current_utilization,
            "is_active": self.is_active,
            "metadata": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class Inventory(Base):
    """Inventory model"""
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    variant_id = Column(Integer, nullable=True)  # Removed FK constraint - product_variants table not implemented yet
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="CASCADE"))
    quantity = Column(Integer, default=0)
    reserved_quantity = Column(Integer, default=0)
    # available_quantity is a generated column in the database
    reorder_point = Column(Integer, default=10)
    reorder_quantity = Column(Integer, default=50)
    last_restock_date = Column(DateTime)
    last_count_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="inventory")
    warehouse = relationship("Warehouse", back_populates="inventory")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "variant_id": self.variant_id,
            "warehouse_id": self.warehouse_id,
            "quantity": self.quantity,
            "reserved_quantity": self.reserved_quantity,
            "available_quantity": self.quantity - self.reserved_quantity,
            "reorder_point": self.reorder_point,
            "reorder_quantity": self.reorder_quantity,
            "last_restock_date": self.last_restock_date.isoformat() if self.last_restock_date else None,
            "last_count_date": self.last_count_date.isoformat() if self.last_count_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

# ============================================================================
# CUSTOMER & ORDER MODELS
# ============================================================================

class Customer(Base):
    """Customer profile"""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    customer_group = Column(String(100))
    total_orders = Column(Integer, default=0)
    total_spent = Column(Numeric(15, 2), default=0.00)
    average_order_value = Column(Numeric(10, 2), default=0.00)
    lifetime_value = Column(Numeric(15, 2), default=0.00)
    last_order_date = Column(DateTime)
    notes = Column(Text)
    tags = Column(JSON)
    extra_data = Column('metadata', JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="customer")
    orders = relationship("Order", back_populates="customer")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "customer_group": self.customer_group,
            "total_orders": self.total_orders,
            "total_spent": float(self.total_spent) if self.total_spent else 0.0,
            "average_order_value": float(self.average_order_value) if self.average_order_value else 0.0,
            "lifetime_value": float(self.lifetime_value) if self.lifetime_value else 0.0,
            "last_order_date": self.last_order_date.isoformat() if self.last_order_date else None,
            "notes": self.notes,
            "tags": self.tags or [],
            "metadata": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class Address(Base):
    """Address model"""
    __tablename__ = "addresses"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    address_type = Column(String(50))  # shipping, billing, both
    first_name = Column(String(100))
    last_name = Column(String(100))
    company = Column(String(255))
    address_line1 = Column(Text, nullable=False)
    address_line2 = Column(Text)
    city = Column(String(100), nullable=False)
    state = Column(String(100))
    country = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    phone = Column(String(50))
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="addresses")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "address_type": self.address_type,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "company": self.company,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "postal_code": self.postal_code,
            "phone": self.phone,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class Order(Base):
    """Order model"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String(100), unique=True, nullable=True)  # Made nullable to match existing database
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"))
    merchant_id = Column(Integer, ForeignKey("merchants.id", ondelete="SET NULL"))
    status = Column(String(50), default="pending")
    payment_status = Column(String(50), default="pending")
    fulfillment_status = Column(String(50), default="unfulfilled")
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax = Column(Numeric(10, 2), default=0.00)
    shipping_cost = Column(Numeric(10, 2), default=0.00)
    discount = Column(Numeric(10, 2), default=0.00)
    total = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="USD")
    shipping_address_id = Column(Integer, ForeignKey("addresses.id"))
    billing_address_id = Column(Integer, ForeignKey("addresses.id"))
    notes = Column(Text)
    customer_notes = Column(Text)
    extra_data = Column('metadata', JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmed_at = Column(DateTime)
    shipped_at = Column(DateTime)
    delivered_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    
    # Relationships
    customer = relationship("Customer", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "order_number": self.order_number,
            "customer_id": self.customer_id,
            "merchant_id": self.merchant_id,
            "status": self.status,
            "payment_status": self.payment_status,
            "fulfillment_status": self.fulfillment_status,
            "subtotal": float(self.subtotal) if self.subtotal else 0.0,
            "tax": float(self.tax) if self.tax else 0.0,
            "shipping_cost": float(self.shipping_cost) if self.shipping_cost else 0.0,
            "discount": float(self.discount) if self.discount else 0.0,
            "total": float(self.total) if self.total else 0.0,
            "currency": self.currency,
            "shipping_address_id": self.shipping_address_id,
            "billing_address_id": self.billing_address_id,
            "notes": self.notes,
            "customer_notes": self.customer_notes,
            "metadata": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "shipped_at": self.shipped_at.isoformat() if self.shipped_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
        }

class OrderItem(Base):
    """Order item model"""
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"))
    variant_id = Column(Integer)
    sku = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    tax = Column(Numeric(10, 2), default=0.00)
    discount = Column(Numeric(10, 2), default=0.00)
    extra_data = Column('metadata', JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "variant_id": self.variant_id,
            "sku": self.sku,
            "name": self.name,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price) if self.unit_price else 0.0,
            "total_price": float(self.total_price) if self.total_price else 0.0,
            "tax": float(self.tax) if self.tax else 0.0,
            "discount": float(self.discount) if self.discount else 0.0,
            "metadata": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

# ============================================================================
# CARRIER MODELS
# ============================================================================

class Carrier(Base):
    """Carrier model"""
    __tablename__ = "carriers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    tracking_url_template = Column(String(500))
    api_endpoint = Column(String(500))
    api_key_encrypted = Column(Text)
    is_active = Column(Boolean, default=True)
    supported_services = Column(JSON)
    extra_data = Column('metadata', JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "tracking_url_template": self.tracking_url_template,
            "api_endpoint": self.api_endpoint,
            "is_active": self.is_active,
            "supported_services": self.supported_services or [],
            "metadata": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

# ============================================================================
# ALERT MODELS
# ============================================================================

class Alert(Base):
    """System alert model"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True)
    alert_type = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text)
    source = Column(String(100))
    status = Column(String(50), default="active")
    acknowledged_by = Column(Integer, ForeignKey("users.id"))
    acknowledged_at = Column(DateTime)
    resolved_by = Column(Integer, ForeignKey("users.id"))
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    extra_data = Column('metadata', JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "source": self.source,
            "status": self.status,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
            "metadata": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# RETURN MODELS
# ============================================================================

class Return(Base):
    """Return/RMA model"""
    __tablename__ = "returns"
    
    id = Column(Integer, primary_key=True)
    return_number = Column(String(50), unique=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    order_item_id = Column(Integer, ForeignKey("order_items.id", ondelete="SET NULL"))
    customer_id = Column(Integer)
    reason = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    return_type = Column(String(50), default="refund")  # refund, exchange, replacement
    status = Column(String(50), default="pending")  # pending, approved, rejected, received, completed, cancelled
    refund_amount = Column(Numeric(10, 2))
    resolution = Column(Text)
    comments = Column(Text)
    admin_notes = Column(Text)
    extra_data = Column('metadata', JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = Column(DateTime)
    received_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    order = relationship("Order", foreign_keys=[order_id])
    order_item = relationship("OrderItem", foreign_keys=[order_item_id])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "return_number": self.return_number,
            "order_id": self.order_id,
            "order_item_id": self.order_item_id,
            "customer_id": self.customer_id,
            "reason": self.reason,
            "quantity": self.quantity,
            "return_type": self.return_type,
            "status": self.status,
            "refund_amount": float(self.refund_amount) if self.refund_amount else None,
            "resolution": self.resolution,
            "comments": self.comments,
            "admin_notes": self.admin_notes,
            "metadata": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


# ============================================================================
# PAYMENT MODELS
# ============================================================================

class Payment(Base):
    """Payment/Transaction model (alias for transactions table)"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    payment_method_id = Column(Integer)
    transaction_type = Column(String(50))  # charge, refund, authorization, capture
    status = Column(String(50))  # pending, success, failed, cancelled
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="USD")
    gateway = Column(String(100))
    gateway_transaction_id = Column(String(255))
    error_message = Column(Text)
    extra_data = Column('metadata', JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order = relationship("Order", foreign_keys=[order_id])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "payment_method_id": self.payment_method_id,
            "transaction_type": self.transaction_type,
            "status": self.status,
            "amount": float(self.amount) if self.amount else None,
            "currency": self.currency,
            "gateway": self.gateway,
            "gateway_transaction_id": self.gateway_transaction_id,
            "error_message": self.error_message,
            "metadata": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PaymentMethod(Base):
    """Payment method configuration"""
    __tablename__ = "payment_methods"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    type = Column(String(50))  # credit_card, debit_card, paypal, stripe, etc.
    is_active = Column(Boolean, default=True)
    config = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "type": self.type,
            "is_active": self.is_active,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# SHIPPING MODELS
# ============================================================================

class Shipment(Base):
    """Shipment model for order deliveries"""
    __tablename__ = "shipments"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    carrier_id = Column(Integer, ForeignKey("carriers.id", ondelete="SET NULL"))
    tracking_number = Column(String(255))
    service_type = Column(String(100))
    status = Column(String(50), default="pending")  # pending, in_transit, delivered, failed, returned
    estimated_delivery_date = Column(DateTime)
    actual_delivery_date = Column(DateTime)
    shipping_cost = Column(Numeric(10, 2))
    weight = Column(Numeric(10, 2))
    dimensions = Column(JSON)
    from_address = Column(JSON)
    to_address = Column(JSON)
    extra_data = Column('metadata', JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order = relationship("Order", foreign_keys=[order_id])
    carrier = relationship("Carrier", foreign_keys=[carrier_id])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "carrier_id": self.carrier_id,
            "tracking_number": self.tracking_number,
            "service_type": self.service_type,
            "status": self.status,
            "estimated_delivery_date": self.estimated_delivery_date.isoformat() if self.estimated_delivery_date else None,
            "actual_delivery_date": self.actual_delivery_date.isoformat() if self.actual_delivery_date else None,
            "shipping_cost": float(self.shipping_cost) if self.shipping_cost else None,
            "weight": float(self.weight) if self.weight else None,
            "dimensions": self.dimensions,
            "from_address": self.from_address,
            "to_address": self.to_address,
            "metadata": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# REPLENISHMENT MODELS
# ============================================================================

class PurchaseOrder(Base):
    """Purchase Order model for inventory replenishment"""
    __tablename__ = 'purchase_orders'
    
    id = Column(Integer, primary_key=True)
    po_number = Column(String(50), unique=True, nullable=False)
    vendor_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String(20), nullable=False, default='draft')
    order_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    expected_delivery_date = Column(DateTime)
    actual_delivery_date = Column(DateTime)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    currency = Column(String(3), nullable=False, default='EUR')
    shipping_cost = Column(Numeric(10, 2), default=0.00)
    tax_amount = Column(Numeric(10, 2), default=0.00)
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey('users.id'))
    approved_by = Column(Integer, ForeignKey('users.id'))
    approved_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "po_number": self.po_number,
            "vendor_id": self.vendor_id,
            "status": self.status,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "expected_delivery_date": self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            "actual_delivery_date": self.actual_delivery_date.isoformat() if self.actual_delivery_date else None,
            "total_amount": float(self.total_amount) if self.total_amount else 0.0,
            "currency": self.currency,
            "shipping_cost": float(self.shipping_cost) if self.shipping_cost else 0.0,
            "tax_amount": float(self.tax_amount) if self.tax_amount else 0.0,
            "notes": self.notes,
            "created_by": self.created_by,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PurchaseOrderItem(Base):
    """Purchase Order Item model"""
    __tablename__ = 'purchase_order_items'
    
    id = Column(Integer, primary_key=True)
    po_id = Column(Integer, ForeignKey('purchase_orders.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    total_cost = Column(Numeric(12, 2), nullable=False)
    received_quantity = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default='pending')
    notes = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "po_id": self.po_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_cost": float(self.unit_cost) if self.unit_cost else 0.0,
            "total_cost": float(self.total_cost) if self.total_cost else 0.0,
            "received_quantity": self.received_quantity,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ReplenishmentSetting(Base):
    """Replenishment Settings model"""
    __tablename__ = 'replenishment_settings'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), unique=True, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    reorder_point = Column(Integer, nullable=False, default=0)
    safety_stock = Column(Integer, nullable=False, default=0)
    economic_order_quantity = Column(Integer, nullable=False, default=0)
    lead_time_days = Column(Integer, nullable=False, default=7)
    ordering_cost = Column(Numeric(10, 2), nullable=False, default=50.00)
    holding_cost_per_unit = Column(Numeric(10, 2), nullable=False, default=2.00)
    avg_daily_sales = Column(Numeric(10, 2), nullable=False, default=0.00)
    max_daily_sales = Column(Numeric(10, 2), nullable=False, default=0.00)
    last_calculated_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "enabled": self.enabled,
            "reorder_point": self.reorder_point,
            "safety_stock": self.safety_stock,
            "economic_order_quantity": self.economic_order_quantity,
            "lead_time_days": self.lead_time_days,
            "ordering_cost": float(self.ordering_cost) if self.ordering_cost else 50.0,
            "holding_cost_per_unit": float(self.holding_cost_per_unit) if self.holding_cost_per_unit else 2.0,
            "avg_daily_sales": float(self.avg_daily_sales) if self.avg_daily_sales else 0.0,
            "max_daily_sales": float(self.max_daily_sales) if self.max_daily_sales else 0.0,
            "last_calculated_at": self.last_calculated_at.isoformat() if self.last_calculated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ReplenishmentRecommendation(Base):
    """Replenishment Recommendation model"""
    __tablename__ = 'replenishment_recommendations'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    current_stock = Column(Integer, nullable=False)
    reorder_point = Column(Integer, nullable=False)
    recommended_quantity = Column(Integer, nullable=False)
    reason = Column(String(100), nullable=False)
    priority = Column(String(20), nullable=False, default='medium')
    status = Column(String(20), nullable=False, default='pending')
    po_id = Column(Integer, ForeignKey('purchase_orders.id'))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "current_stock": self.current_stock,
            "reorder_point": self.reorder_point,
            "recommended_quantity": self.recommended_quantity,
            "reason": self.reason,
            "priority": self.priority,
            "status": self.status,
            "po_id": self.po_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class DemandForecast(Base):
    """Demand Forecast model"""
    __tablename__ = 'demand_forecasts'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    forecast_date = Column(DateTime, nullable=False)
    forecast_quantity = Column(Numeric(10, 2), nullable=False)
    confidence_level = Column(Numeric(5, 2), nullable=False, default=0.00)
    model_version = Column(String(50), nullable=False, default='v1.0')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "forecast_date": self.forecast_date.isoformat() if self.forecast_date else None,
            "forecast_quantity": float(self.forecast_quantity) if self.forecast_quantity else 0.0,
            "confidence_level": float(self.confidence_level) if self.confidence_level else 0.0,
            "model_version": self.model_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================================
# INBOUND MANAGEMENT MODELS
# ============================================================================

class InboundShipment(Base):
    """Inbound shipment (ASN) model"""
    __tablename__ = 'inbound_shipments'
    
    id = Column(Integer, primary_key=True)
    shipment_number = Column(String(50), unique=True, nullable=False)
    po_id = Column(Integer, ForeignKey('purchase_orders.id'))
    vendor_id = Column(Integer, nullable=False)
    expected_arrival_date = Column(DateTime)
    actual_arrival_date = Column(DateTime)
    status = Column(String(50), default='expected')
    carrier = Column(String(100))
    tracking_number = Column(String(100))
    total_items = Column(Integer, default=0)
    received_items = Column(Integer, default=0)
    warehouse_id = Column(Integer)
    dock_door = Column(String(20))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "shipment_number": self.shipment_number,
            "po_id": self.po_id,
            "vendor_id": self.vendor_id,
            "expected_arrival_date": self.expected_arrival_date.isoformat() if self.expected_arrival_date else None,
            "actual_arrival_date": self.actual_arrival_date.isoformat() if self.actual_arrival_date else None,
            "status": self.status,
            "carrier": self.carrier,
            "tracking_number": self.tracking_number,
            "total_items": self.total_items,
            "received_items": self.received_items,
            "warehouse_id": self.warehouse_id,
            "dock_door": self.dock_door,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class InboundShipmentItem(Base):
    """Inbound shipment item model"""
    __tablename__ = 'inbound_shipment_items'
    
    id = Column(Integer, primary_key=True)
    shipment_id = Column(Integer, ForeignKey('inbound_shipments.id', ondelete='CASCADE'))
    product_id = Column(Integer, nullable=False)
    sku = Column(String(100), nullable=False)
    expected_quantity = Column(Integer, nullable=False)
    received_quantity = Column(Integer, default=0)
    accepted_quantity = Column(Integer, default=0)
    rejected_quantity = Column(Integer, default=0)
    unit_cost = Column(Numeric(10, 2))
    status = Column(String(50), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "shipment_id": self.shipment_id,
            "product_id": self.product_id,
            "sku": self.sku,
            "expected_quantity": self.expected_quantity,
            "received_quantity": self.received_quantity,
            "accepted_quantity": self.accepted_quantity,
            "rejected_quantity": self.rejected_quantity,
            "unit_cost": float(self.unit_cost) if self.unit_cost else 0.0,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class ReceivingTask(Base):
    """Receiving task model"""
    __tablename__ = 'receiving_tasks'
    
    id = Column(Integer, primary_key=True)
    shipment_id = Column(Integer, ForeignKey('inbound_shipments.id'))
    task_number = Column(String(50), unique=True, nullable=False)
    assigned_to = Column(String(100))
    status = Column(String(50), default='pending')
    priority = Column(String(20), default='medium')
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "shipment_id": self.shipment_id,
            "task_number": self.task_number,
            "assigned_to": self.assigned_to,
            "status": self.status,
            "priority": self.priority,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class QualityInspection(Base):
    """Quality inspection model"""
    __tablename__ = 'quality_inspections'
    
    id = Column(Integer, primary_key=True)
    shipment_item_id = Column(Integer, ForeignKey('inbound_shipment_items.id'))
    inspection_number = Column(String(50), unique=True, nullable=False)
    inspector_id = Column(String(100))
    inspection_type = Column(String(50))
    sample_size = Column(Integer)
    passed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    status = Column(String(50), default='pending')
    defect_types = Column(JSON)
    photos = Column(JSON)
    notes = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "shipment_item_id": self.shipment_item_id,
            "inspection_number": self.inspection_number,
            "inspector_id": self.inspector_id,
            "inspection_type": self.inspection_type,
            "sample_size": self.sample_size,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "status": self.status,
            "defect_types": self.defect_types,
            "photos": self.photos,
            "notes": self.notes,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class QualityDefect(Base):
    """Quality defect model"""
    __tablename__ = 'quality_defects'
    
    id = Column(Integer, primary_key=True)
    inspection_id = Column(Integer, ForeignKey('quality_inspections.id'))
    defect_type = Column(String(100))
    severity = Column(String(20))
    quantity = Column(Integer)
    description = Column(Text)
    action_taken = Column(String(100))
    photos = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "inspection_id": self.inspection_id,
            "defect_type": self.defect_type,
            "severity": self.severity,
            "quantity": self.quantity,
            "description": self.description,
            "action_taken": self.action_taken,
            "photos": self.photos,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class PutawayTask(Base):
    """Putaway task model"""
    __tablename__ = 'putaway_tasks'
    
    id = Column(Integer, primary_key=True)
    shipment_item_id = Column(Integer, ForeignKey('inbound_shipment_items.id'))
    task_number = Column(String(50), unique=True, nullable=False)
    product_id = Column(Integer, nullable=False)
    sku = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    from_location = Column(String(100))
    to_location = Column(String(100))
    assigned_to = Column(String(100))
    status = Column(String(50), default='pending')
    priority = Column(String(20), default='medium')
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "shipment_item_id": self.shipment_item_id,
            "task_number": self.task_number,
            "product_id": self.product_id,
            "sku": self.sku,
            "quantity": self.quantity,
            "from_location": self.from_location,
            "to_location": self.to_location,
            "assigned_to": self.assigned_to,
            "status": self.status,
            "priority": self.priority,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class ReceivingDiscrepancy(Base):
    """Receiving discrepancy model"""
    __tablename__ = 'receiving_discrepancies'
    
    id = Column(Integer, primary_key=True)
    shipment_id = Column(Integer, ForeignKey('inbound_shipments.id'))
    shipment_item_id = Column(Integer, ForeignKey('inbound_shipment_items.id'))
    discrepancy_type = Column(String(50))
    expected_quantity = Column(Integer)
    actual_quantity = Column(Integer)
    variance = Column(Integer)
    resolution_status = Column(String(50), default='open')
    resolution_notes = Column(Text)
    reported_by = Column(String(100))
    resolved_by = Column(String(100))
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "shipment_id": self.shipment_id,
            "shipment_item_id": self.shipment_item_id,
            "discrepancy_type": self.discrepancy_type,
            "expected_quantity": self.expected_quantity,
            "actual_quantity": self.actual_quantity,
            "variance": self.variance,
            "resolution_status": self.resolution_status,
            "resolution_notes": self.resolution_notes,
            "reported_by": self.reported_by,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================================
# SHOPPING CART MODELS
# ============================================================================

class Cart(Base):
    """Shopping cart for customers"""
    __tablename__ = "carts"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    session_id = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "session_id": self.session_id,
            "items": [item.to_dict() for item in self.items] if self.items else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CartItem(Base):
    """Items in shopping cart"""
    __tablename__ = "cart_items"
    
    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    price = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "cart_id": self.cart_id,
            "product_id": self.product_id,
            "product": self.product.to_dict() if self.product else None,
            "quantity": self.quantity,
            "price": float(self.price) if self.price else 0,
            "subtotal": float(self.price * self.quantity) if self.price else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================================
# REVIEWS MODEL
# ============================================================================

class Review(Base):
    """Product reviews"""
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    title = Column(String(255), nullable=True)
    comment = Column(Text, nullable=True)
    verified_purchase = Column(Boolean, default=False)
    helpful_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = relationship("Product")
    customer = relationship("Customer")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "customer_id": self.customer_id,
            "rating": self.rating,
            "title": self.title,
            "comment": self.comment,
            "verified_purchase": self.verified_purchase,
            "helpful_count": self.helpful_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# PROMOTIONS MODEL
# ============================================================================

class Promotion(Base):
    """Promotional campaigns"""
    __tablename__ = "promotions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    discount_type = Column(String(20), nullable=False)  # percentage, fixed
    discount_value = Column(DECIMAL(10, 2), nullable=False)
    min_order_value = Column(DECIMAL(10, 2), nullable=True)
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    max_uses = Column(Integer, nullable=True)
    uses_count = Column(Integer, default=0)
    status = Column(String(20), default='active')  # active, inactive, expired
    banner_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "code": self.code,
            "discount_type": self.discount_type,
            "discount_value": float(self.discount_value) if self.discount_value else 0,
            "min_order_value": float(self.min_order_value) if self.min_order_value else None,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "max_uses": self.max_uses,
            "uses_count": self.uses_count,
            "status": self.status,
            "banner_url": self.banner_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# CUSTOMER PAYMENT METHODS MODEL
# ============================================================================

class CustomerPaymentMethod(Base):
    """Saved customer payment methods"""
    __tablename__ = "customer_payment_methods"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    type = Column(String(50), nullable=False)  # card, paypal, etc
    provider = Column(String(50), nullable=True)  # visa, mastercard, etc
    last_four = Column(String(4), nullable=True)
    expiry_month = Column(Integer, nullable=True)
    expiry_year = Column(Integer, nullable=True)
    cardholder_name = Column(String(255), nullable=True)
    is_default = Column(Boolean, default=False)
    token = Column(String(255), nullable=True)  # Payment gateway token
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "type": self.type,
            "provider": self.provider,
            "last_four": self.last_four,
            "expiry_month": self.expiry_month,
            "expiry_year": self.expiry_year,
            "cardholder_name": self.cardholder_name,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# OFFERS MANAGEMENT MODELS
# ============================================================================

class Offer(Base):
    """Special offers and promotions"""
    __tablename__ = "offers"
    
    id = Column(Integer, primary_key=True)
    
    # Basic Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    offer_type = Column(String(50), nullable=False)  # percentage, fixed_amount, buy_x_get_y, bundle
    status = Column(String(50), default='draft')  # draft, active, paused, expired, cancelled
    
    # Pricing & Discount
    discount_type = Column(String(50))  # percentage, fixed
    discount_value = Column(Numeric(10, 2))
    min_purchase_amount = Column(Numeric(15, 2))
    max_discount_amount = Column(Numeric(15, 2))
    
    # Scheduling
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_scheduled = Column(Boolean, default=False)
    
    # Targeting
    target_customer_groups = Column(JSON)
    target_marketplaces = Column(JSON)
    target_products = Column(JSON)
    target_categories = Column(JSON)
    
    # Usage Limits
    usage_limit_per_customer = Column(Integer)
    total_usage_limit = Column(Integer)
    current_usage_count = Column(Integer, default=0)
    
    # Conditions
    conditions = Column(JSON)
    stackable = Column(Boolean, default=False)
    
    # Priority & Display
    priority = Column(Integer, default=0)
    display_badge = Column(String(100))
    display_banner_url = Column(Text)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    extra_data = Column(JSON)
    
    # Relationships
    products = relationship("OfferProduct", back_populates="offer", cascade="all, delete-orphan")
    marketplaces = relationship("OfferMarketplace", back_populates="offer", cascade="all, delete-orphan")
    usage_records = relationship("OfferUsage", back_populates="offer")
    analytics = relationship("OfferAnalytics", back_populates="offer")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "offer_type": self.offer_type,
            "status": self.status,
            "discount_type": self.discount_type,
            "discount_value": float(self.discount_value) if self.discount_value else None,
            "min_purchase_amount": float(self.min_purchase_amount) if self.min_purchase_amount else None,
            "max_discount_amount": float(self.max_discount_amount) if self.max_discount_amount else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_scheduled": self.is_scheduled,
            "target_customer_groups": self.target_customer_groups or [],
            "target_marketplaces": self.target_marketplaces or [],
            "target_products": self.target_products or [],
            "target_categories": self.target_categories or [],
            "usage_limit_per_customer": self.usage_limit_per_customer,
            "total_usage_limit": self.total_usage_limit,
            "current_usage_count": self.current_usage_count,
            "conditions": self.conditions or {},
            "stackable": self.stackable,
            "priority": self.priority,
            "display_badge": self.display_badge,
            "display_banner_url": self.display_banner_url,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "extra_data": self.extra_data or {}
        }


class OfferProduct(Base):
    """Products included in offers (Many-to-Many)"""
    __tablename__ = "offer_products"
    
    id = Column(Integer, primary_key=True)
    offer_id = Column(Integer, ForeignKey("offers.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    custom_discount_value = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    offer = relationship("Offer", back_populates="products")
    product = relationship("Product")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "offer_id": self.offer_id,
            "product_id": self.product_id,
            "custom_discount_value": float(self.custom_discount_value) if self.custom_discount_value else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class OfferMarketplace(Base):
    """Marketplaces where offers are active (Many-to-Many)"""
    __tablename__ = "offer_marketplaces"
    
    id = Column(Integer, primary_key=True)
    offer_id = Column(Integer, ForeignKey("offers.id", ondelete="CASCADE"), nullable=False)
    marketplace_id = Column(Integer, ForeignKey("marketplaces.id", ondelete="CASCADE"), nullable=False)
    marketplace_offer_id = Column(String(255))
    sync_status = Column(String(50), default='pending')
    last_synced_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    offer = relationship("Offer", back_populates="marketplaces")
    marketplace = relationship("Marketplace")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "offer_id": self.offer_id,
            "marketplace_id": self.marketplace_id,
            "marketplace_offer_id": self.marketplace_offer_id,
            "sync_status": self.sync_status,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class OfferUsage(Base):
    """Tracking of offer usage by customers"""
    __tablename__ = "offer_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("offers.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), index=True)
    discount_applied = Column(Numeric(15, 2))
    original_amount = Column(Numeric(15, 2))
    final_amount = Column(Numeric(15, 2))
    used_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    offer = relationship("Offer", back_populates="usage_records")
    customer = relationship("Customer")
    order = relationship("Order")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "offer_id": self.offer_id,
            "customer_id": self.customer_id,
            "order_id": self.order_id,
            "discount_applied": float(self.discount_applied) if self.discount_applied else 0.0,
            "original_amount": float(self.original_amount) if self.original_amount else 0.0,
            "final_amount": float(self.final_amount) if self.final_amount else 0.0,
            "used_at": self.used_at.isoformat() if self.used_at else None
        }


class OfferAnalytics(Base):
    """Daily analytics for offer performance"""
    __tablename__ = "offer_analytics"
    
    id = Column(Integer, primary_key=True)
    offer_id = Column(Integer, ForeignKey("offers.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    views_count = Column(Integer, default=0)
    clicks_count = Column(Integer, default=0)
    usage_count = Column(Integer, default=0)
    revenue_generated = Column(Numeric(15, 2), default=0.00)
    discount_given = Column(Numeric(15, 2), default=0.00)
    orders_count = Column(Integer, default=0)
    conversion_rate = Column(Numeric(5, 2))
    average_order_value = Column(Numeric(15, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    offer = relationship("Offer", back_populates="analytics")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "offer_id": self.offer_id,
            "date": self.date.isoformat() if self.date else None,
            "views_count": self.views_count,
            "clicks_count": self.clicks_count,
            "usage_count": self.usage_count,
            "revenue_generated": float(self.revenue_generated) if self.revenue_generated else 0.0,
            "discount_given": float(self.discount_given) if self.discount_given else 0.0,
            "orders_count": self.orders_count,
            "conversion_rate": float(self.conversion_rate) if self.conversion_rate else 0.0,
            "average_order_value": float(self.average_order_value) if self.average_order_value else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# ============================================================================
# SUPPLIER MANAGEMENT MODELS
# ============================================================================

class Supplier(Base):
    """Supplier and vendor management"""
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True)
    
    # Basic Information
    name = Column(String(255), nullable=False)
    company_name = Column(String(255))
    supplier_code = Column(String(100), unique=True)
    status = Column(String(50), default='active')
    
    # Contact Information
    contact_person = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    website = Column(String(255))
    
    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100))
    
    # Business Details
    tax_id = Column(String(100))
    payment_terms = Column(String(100))
    currency = Column(String(10), default='USD')
    minimum_order_value = Column(Numeric(15, 2))
    
    # Performance Metrics
    rating = Column(Numeric(3, 2))
    total_orders = Column(Integer, default=0)
    total_spend = Column(Numeric(15, 2), default=0.00)
    on_time_delivery_rate = Column(Numeric(5, 2))
    quality_score = Column(Numeric(5, 2))
    
    # Metadata
    notes = Column(Text)
    tags = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    extra_data = Column(JSON)
    
    # Relationships
    products = relationship("SupplierProduct", back_populates="supplier")
    # Note: PurchaseOrder uses vendor_id, not supplier_id, so no direct relationship
    # purchase_orders can be queried separately if needed
    payments = relationship("SupplierPayment", back_populates="supplier")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "company_name": self.company_name,
            "supplier_code": self.supplier_code,
            "status": self.status,
            "contact_person": self.contact_person,
            "email": self.email,
            "phone": self.phone,
            "website": self.website,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
            "tax_id": self.tax_id,
            "payment_terms": self.payment_terms,
            "currency": self.currency,
            "minimum_order_value": float(self.minimum_order_value) if self.minimum_order_value else None,
            "rating": float(self.rating) if self.rating else None,
            "total_orders": self.total_orders,
            "total_spend": float(self.total_spend) if self.total_spend else 0.0,
            "on_time_delivery_rate": float(self.on_time_delivery_rate) if self.on_time_delivery_rate else None,
            "quality_score": float(self.quality_score) if self.quality_score else None,
            "notes": self.notes,
            "tags": self.tags or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "extra_data": self.extra_data or {}
        }


class SupplierProduct(Base):
    """Products sourced from suppliers"""
    __tablename__ = "supplier_products"
    
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Supplier-specific product info
    supplier_sku = Column(String(255))
    supplier_product_name = Column(String(255))
    cost_price = Column(Numeric(15, 2))
    minimum_order_quantity = Column(Integer, default=1)
    lead_time_days = Column(Integer)
    
    # Status
    is_primary_supplier = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="products")
    product = relationship("Product")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "supplier_id": self.supplier_id,
            "product_id": self.product_id,
            "supplier_sku": self.supplier_sku,
            "supplier_product_name": self.supplier_product_name,
            "cost_price": float(self.cost_price) if self.cost_price else None,
            "minimum_order_quantity": self.minimum_order_quantity,
            "lead_time_days": self.lead_time_days,
            "is_primary_supplier": self.is_primary_supplier,
            "is_active": self.is_active,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class SupplierPayment(Base):
    """Payments made to suppliers"""
    __tablename__ = "supplier_payments"
    
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"))
    
    # Payment Details
    payment_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(10), default='USD')
    payment_method = Column(String(50))
    reference_number = Column(String(255))
    
    # Status
    status = Column(String(50), default='pending')
    
    # Metadata
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="payments")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "supplier_id": self.supplier_id,
            "purchase_order_id": self.purchase_order_id,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "amount": float(self.amount) if self.amount else 0.0,
            "currency": self.currency,
            "payment_method": self.payment_method,
            "reference_number": self.reference_number,
            "status": self.status,
            "notes": self.notes,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "extra_data": self.extra_data or {}
        }



# ============================================================================
# MARKETPLACE MODELS
# ============================================================================

class Marketplace(Base):
    """E-commerce marketplace integrations (Amazon, eBay, Walmart, etc.)"""
    __tablename__ = "marketplaces"
    
    id = Column(Integer, primary_key=True)
    
    # Marketplace Information
    name = Column(String(255), nullable=False)
    platform = Column(String(100), nullable=False, index=True)
    region = Column(String(50))
    
    # Connection
    api_key = Column(String(500))
    api_secret = Column(String(500))
    merchant_id = Column(String(255))
    is_active = Column(Boolean, default=True, index=True)
    
    # Configuration
    settings = Column(JSON)
    
    # Sync
    last_sync_at = Column(DateTime)
    sync_frequency = Column(Integer, default=3600)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "platform": self.platform,
            "region": self.region,
            "merchant_id": self.merchant_id,
            "is_active": self.is_active,
            "settings": self.settings or {},
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "sync_frequency": self.sync_frequency,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
