"""
Product Agent - Multi-Agent E-commerce System (Production Ready with Database)

This agent manages the master product catalog with REAL database integration:
- Product CRUD operations from PostgreSQL
- Product search and filtering
- Category management
- Product analytics
- NO MOCK DATA - All queries hit database
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime, Numeric, Float, Text, Integer, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logger.info(f"Added {project_root} to Python path")

# Import base agent
try:
    from shared.base_agent_v2 import BaseAgentV2, MessageType, AgentMessage
    from shared.database import DatabaseConfig
    logger.info("Successfully imported shared modules")
except ImportError as e:
    logger.error(f"Import error: {e}")
    raise

# SQLAlchemy Base
Base = declarative_base()

# Database Models
class ProductDB(Base):
    """SQLAlchemy model for Product"""
    __tablename__ = "products"
    
    id = Column(String, primary_key=True)
    sku = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    cost = Column(Numeric(10, 2), nullable=False)
    weight = Column(Float)
    condition = Column(String, default="new")
    grade = Column(String, default="A")
    stock_quantity = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "brand": self.brand,
            "price": str(self.price),
            "cost": str(self.cost),
            "weight": self.weight,
            "condition": self.condition,
            "grade": self.grade,
            "stock_quantity": self.stock_quantity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class ProductCategoryDB(Base):
    """SQLAlchemy model for Product Categories"""
    __tablename__ = "product_categories"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    parent_id = Column(String)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

# Pydantic Models
class Product(BaseModel):
    """Product model for API"""
    id: Optional[str] = None
    sku: str
    name: str
    description: Optional[str] = None
    category: str
    brand: str
    price: Decimal
    cost: Decimal
    weight: Optional[float] = 0.0
    condition: str = "new"
    grade: str = "A"
    stock_quantity: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ProductCategory(BaseModel):
    """Product Category model for API"""
    id: Optional[str] = None
    name: str
    parent_id: Optional[str] = None
    description: Optional[str] = None

class ProductAgent(BaseAgentV2):
    """
    Production-ready Product Agent with 100% database integration
    """
    
    def __init__(self):
        super().__init__(agent_id="product_agent")
        
        # Database setup
        db_config = DatabaseConfig()
        self.database_url = db_config.get_async_url()
        self.engine = create_async_engine(self.database_url, echo=False)
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        self._db_initialized = False
        
        logger.info("Product Agent initialized with database connection")
    
    async def initialize(self):
        """Initialize agent and database"""
        await super().initialize()
        
        # Create tables if they don't exist
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            self._db_initialized = True
            logger.info("Product Agent database tables created/verified")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def setup_routes(self):
        """Setup FastAPI routes - ALL query database"""
        
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "agent": "product_agent",
                "database": "connected" if self._db_initialized else "disconnected",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # ===== PRODUCT CRUD ENDPOINTS =====
        
        @self.app.get("/products")
        async def get_products(
            skip: int = 0,
            limit: int = 100,
            category: Optional[str] = None,
            brand: Optional[str] = None,
            min_price: Optional[float] = None,
            max_price: Optional[float] = None
        ):
            """Get products with optional filtering - queries database"""
            try:
                async with self.async_session() as session:
                    query = select(ProductDB)
                    
                    # Apply filters
                    if category:
                        query = query.where(ProductDB.category == category)
                    if brand:
                        query = query.where(ProductDB.brand == brand)
                    if min_price is not None:
                        query = query.where(ProductDB.price >= min_price)
                    if max_price is not None:
                        query = query.where(ProductDB.price <= max_price)
                    
                    # Pagination
                    query = query.offset(skip).limit(limit)
                    
                    result = await session.execute(query)
                    products = result.scalars().all()
                    
                    # Get total count
                    count_query = select(func.count(ProductDB.id))
                    if category:
                        count_query = count_query.where(ProductDB.category == category)
                    if brand:
                        count_query = count_query.where(ProductDB.brand == brand)
                    
                    count_result = await session.execute(count_query)
                    total = count_result.scalar()
                    
                    return {
                        "products": [p.to_dict() for p in products],
                        "total": total,
                        "skip": skip,
                        "limit": limit
                    }
            except Exception as e:
                logger.error(f"Error getting products: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/products/{product_id}")
        async def get_product(product_id: str):
            """Get single product by ID - queries database"""
            try:
                async with self.async_session() as session:
                    result = await session.execute(
                        select(ProductDB).where(ProductDB.id == product_id)
                    )
                    product = result.scalar_one_or_none()
                    
                    if not product:
                        raise HTTPException(status_code=404, detail="Product not found")
                    
                    return product.to_dict()
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting product {product_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/products")
        async def create_product(product: Product):
            """Create new product - saves to database"""
            try:
                product_id = str(uuid4())
                
                async with self.async_session() as session:
                    db_product = ProductDB(
                        id=product_id,
                        sku=product.sku,
                        name=product.name,
                        description=product.description,
                        category=product.category,
                        brand=product.brand,
                        price=product.price,
                        cost=product.cost,
                        weight=product.weight,
                        condition=product.condition,
                        grade=product.grade,
                        stock_quantity=product.stock_quantity
                    )
                    
                    session.add(db_product)
                    await session.commit()
                    
                    logger.info(f"Created product: {product_id}")
                    return {"id": product_id, "status": "created"}
            except Exception as e:
                logger.error(f"Error creating product: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.put("/products/{product_id}")
        async def update_product(product_id: str, product: Product):
            """Update product - updates database"""
            try:
                async with self.async_session() as session:
                    result = await session.execute(
                        select(ProductDB).where(ProductDB.id == product_id)
                    )
                    db_product = result.scalar_one_or_none()
                    
                    if not db_product:
                        raise HTTPException(status_code=404, detail="Product not found")
                    
                    # Update fields
                    db_product.sku = product.sku
                    db_product.name = product.name
                    db_product.description = product.description
                    db_product.category = product.category
                    db_product.brand = product.brand
                    db_product.price = product.price
                    db_product.cost = product.cost
                    db_product.weight = product.weight
                    db_product.condition = product.condition
                    db_product.grade = product.grade
                    db_product.stock_quantity = product.stock_quantity
                    db_product.updated_at = datetime.utcnow()
                    
                    await session.commit()
                    
                    logger.info(f"Updated product: {product_id}")
                    return {"id": product_id, "status": "updated"}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error updating product {product_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/products/{product_id}")
        async def delete_product(product_id: str):
            """Delete product - removes from database"""
            try:
                async with self.async_session() as session:
                    result = await session.execute(
                        select(ProductDB).where(ProductDB.id == product_id)
                    )
                    db_product = result.scalar_one_or_none()
                    
                    if not db_product:
                        raise HTTPException(status_code=404, detail="Product not found")
                    
                    await session.delete(db_product)
                    await session.commit()
                    
                    logger.info(f"Deleted product: {product_id}")
                    return {"id": product_id, "status": "deleted"}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error deleting product {product_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ===== SEARCH ENDPOINT =====
        
        @self.app.get("/products/search")
        async def search_products(
            q: str = Query(..., min_length=1),
            limit: int = 20
        ):
            """Search products by name, SKU, or description - queries database"""
            try:
                async with self.async_session() as session:
                    search_term = f"%{q}%"
                    query = select(ProductDB).where(
                        or_(
                            ProductDB.name.ilike(search_term),
                            ProductDB.sku.ilike(search_term),
                            ProductDB.description.ilike(search_term)
                        )
                    ).limit(limit)
                    
                    result = await session.execute(query)
                    products = result.scalars().all()
                    
                    return {
                        "products": [p.to_dict() for p in products],
                        "query": q,
                        "count": len(products)
                    }
            except Exception as e:
                logger.error(f"Error searching products: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ===== CATEGORY ENDPOINTS =====
        
        @self.app.get("/categories")
        async def get_categories():
            """Get all product categories - queries database"""
            try:
                async with self.async_session() as session:
                    result = await session.execute(select(ProductCategoryDB))
                    categories = result.scalars().all()
                    
                    return {
                        "categories": [c.to_dict() for c in categories],
                        "count": len(categories)
                    }
            except Exception as e:
                logger.error(f"Error getting categories: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/categories")
        async def create_category(category: ProductCategory):
            """Create new category - saves to database"""
            try:
                category_id = str(uuid4())
                
                async with self.async_session() as session:
                    db_category = ProductCategoryDB(
                        id=category_id,
                        name=category.name,
                        parent_id=category.parent_id,
                        description=category.description
                    )
                    
                    session.add(db_category)
                    await session.commit()
                    
                    logger.info(f"Created category: {category_id}")
                    return {"id": category_id, "status": "created"}
            except Exception as e:
                logger.error(f"Error creating category: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ===== ANALYTICS ENDPOINTS =====
        
        @self.app.get("/analytics/products")
        async def get_product_analytics():
            """Get product analytics - queries database"""
            try:
                async with self.async_session() as session:
                    # Total products
                    total_result = await session.execute(
                        select(func.count(ProductDB.id))
                    )
                    total_products = total_result.scalar()
                    
                    # Products by category
                    category_result = await session.execute(
                        select(ProductDB.category, func.count(ProductDB.id))
                        .group_by(ProductDB.category)
                    )
                    products_by_category = {
                        row[0]: row[1] for row in category_result.all()
                    }
                    
                    # Products by brand
                    brand_result = await session.execute(
                        select(ProductDB.brand, func.count(ProductDB.id))
                        .group_by(ProductDB.brand)
                    )
                    products_by_brand = {
                        row[0]: row[1] for row in brand_result.all()
                    }
                    
                    # Average price
                    avg_price_result = await session.execute(
                        select(func.avg(ProductDB.price))
                    )
                    avg_price = avg_price_result.scalar() or Decimal('0')
                    
                    # Low stock products (< 10)
                    low_stock_result = await session.execute(
                        select(func.count(ProductDB.id))
                        .where(ProductDB.stock_quantity < 10)
                    )
                    low_stock_count = low_stock_result.scalar()
                    
                    # Out of stock products
                    out_of_stock_result = await session.execute(
                        select(func.count(ProductDB.id))
                        .where(ProductDB.stock_quantity == 0)
                    )
                    out_of_stock_count = out_of_stock_result.scalar()
                    
                    return {
                        "total_products": total_products,
                        "products_by_category": products_by_category,
                        "products_by_brand": products_by_brand,
                        "average_price": str(avg_price),
                        "low_stock_count": low_stock_count,
                        "out_of_stock_count": out_of_stock_count,
                        "timestamp": datetime.utcnow().isoformat()
                    }
            except Exception as e:
                logger.error(f"Error getting product analytics: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/analytics/inventory")
        async def get_inventory_analytics():
            """Get inventory analytics - queries database"""
            try:
                async with self.async_session() as session:
                    # Total inventory value
                    value_result = await session.execute(
                        select(func.sum(ProductDB.price * ProductDB.stock_quantity))
                    )
                    total_value = value_result.scalar() or Decimal('0')
                    
                    # Total units
                    units_result = await session.execute(
                        select(func.sum(ProductDB.stock_quantity))
                    )
                    total_units = units_result.scalar() or 0
                    
                    # Inventory by category
                    category_result = await session.execute(
                        select(
                            ProductDB.category,
                            func.sum(ProductDB.stock_quantity),
                            func.sum(ProductDB.price * ProductDB.stock_quantity)
                        )
                        .group_by(ProductDB.category)
                    )
                    inventory_by_category = {
                        row[0]: {
                            "units": row[1],
                            "value": str(row[2] or Decimal('0'))
                        }
                        for row in category_result.all()
                    }
                    
                    return {
                        "total_inventory_value": str(total_value),
                        "total_units": total_units,
                        "inventory_by_category": inventory_by_category,
                        "timestamp": datetime.utcnow().isoformat()
                    }
            except Exception as e:
                logger.error(f"Error getting inventory analytics: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def process_message(self, message: AgentMessage):
        """Process incoming messages"""
        logger.info(f"Processing message: {message.message_type}")
        
        if message.message_type == MessageType.PRODUCT_CREATED:
            logger.info(f"Product created: {message.payload.get('product_id')}")
        elif message.message_type == MessageType.PRODUCT_UPDATED:
            logger.info(f"Product updated: {message.payload.get('product_id')}")
    
    async def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'engine') and self.engine:
            await self.engine.dispose()
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process product-specific business logic"""
        # This method is required by BaseAgentV2 but not actively used
        # Product operations are handled via REST API endpoints
        return {"status": "success", "message": "Product agent uses REST API for operations"}


async def run_agent():
    """Run the Product Agent"""
    agent = ProductAgent()
    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("Shutting down Product Agent...")
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(run_agent())

