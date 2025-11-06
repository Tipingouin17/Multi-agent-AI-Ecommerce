"""
Shared Database Models for Multi-Agent E-commerce Platform
All agents use these models to ensure consistency
"""

from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, ForeignKey, JSON
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
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"))
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
    order_number = Column(String(100), unique=True, nullable=False)
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
