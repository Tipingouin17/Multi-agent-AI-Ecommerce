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
