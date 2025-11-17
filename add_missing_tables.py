#!/usr/bin/env python3
"""
Database Migration: Add Missing Tables
Adds cart, reviews, promotions, and payment_methods tables
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, Column, Integer, String, Text, DECIMAL, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from shared.db_connection import get_database_url

Base = declarative_base()

# ============================================================================
# NEW TABLE MODELS
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


class PaymentMethod(Base):
    """Saved payment methods"""
    __tablename__ = "payment_methods"
    
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


# ============================================================================
# MIGRATION SCRIPT
# ============================================================================

def main():
    """Run the migration"""
    print("=" * 80)
    print("DATABASE MIGRATION: Adding Missing Tables")
    print("=" * 80)
    print()
    
    try:
        # Get database URL
        db_url = get_database_url()
        print(f"📊 Connecting to database...")
        
        # Create engine
        engine = create_engine(db_url, pool_pre_ping=True)
        
        print(f"✅ Connected successfully!")
        print()
        
        # Create tables
        print("🔨 Creating new tables...")
        print()
        
        tables_to_create = [
            ("carts", Cart),
            ("cart_items", CartItem),
            ("reviews", Review),
            ("promotions", Promotion),
            ("payment_methods", PaymentMethod)
        ]
        
        for table_name, model in tables_to_create:
            try:
                model.__table__.create(engine, checkfirst=True)
                print(f"  ✅ {table_name:20} - Created")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"  ⚠️  {table_name:20} - Already exists (skipped)")
                else:
                    print(f"  ❌ {table_name:20} - Error: {e}")
                    raise
        
        print()
        print("=" * 80)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print()
        print("📊 Summary:")
        print(f"   - Carts table: For shopping cart persistence")
        print(f"   - Cart Items table: For cart item storage")
        print(f"   - Reviews table: For product reviews")
        print(f"   - Promotions table: For promotional campaigns")
        print(f"   - Payment Methods table: For saved payment methods")
        print()
        print("🎉 Your database is now ready for full e-commerce functionality!")
        print()
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ MIGRATION FAILED!")
        print("=" * 80)
        print()
        print(f"Error: {e}")
        print()
        print("Please check:")
        print("  1. PostgreSQL is running")
        print("  2. Database exists")
        print("  3. Database credentials are correct")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
