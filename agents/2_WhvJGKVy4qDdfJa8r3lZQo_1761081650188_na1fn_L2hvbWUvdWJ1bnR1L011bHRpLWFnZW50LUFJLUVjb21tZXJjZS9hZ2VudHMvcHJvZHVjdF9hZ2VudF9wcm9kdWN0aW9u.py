"""
Product Agent - Multi-Agent E-commerce System (Production Ready)

This agent manages the master product catalog with all enhanced features:
- Product variants management
- Category hierarchy
- SEO optimization
- Product bundles
- Advanced attributes and filtering
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4

from shared.db_helpers import DatabaseHelper, DBManager
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import json

# Define ProductDB for SQLAlchemy
Base = declarative_base()

class ProductDB(Base):
    __tablename__ = "products"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    sku = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    category = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    dimensions = Column(String) # Store as JSON string
    condition = Column(String, default="new")
    grade = Column(String, default="A")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Converts the ProductDB object to a dictionary, handling JSON deserialization for dimensions."""
        return {
            "id": str(self.id),
            "sku": self.sku,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "brand": self.brand,
            "price": float(self.price),
            "cost": float(self.cost),
            "weight": self.weight,
            "dimensions": json.loads(self.dimensions) if self.dimensions else None,
            "condition": self.condition,
            "grade": self.grade,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import structlog
import sys
import os

# Setup logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
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
    from shared.base_agent import BaseAgent, MessageType, AgentMessage
    logger.info("Successfully imported shared.base_agent")
except ImportError as e:
    logger.error(f"Import error: {e}")
    raise

# Import new services
try:
    from agents.product_variants_service import ProductVariantsService
    from agents.product_categories_service import ProductCategoriesService
    from agents.product_seo_service import ProductSEOService
    from agents.product_bundles_service import ProductBundlesService
    from agents.product_attributes_service import ProductAttributesService
    logger.info("Successfully imported all product services")
except ImportError as e:
    logger.warning(f"Could not import product services: {e}")
    # Services will be None if not available
    ProductVariantsService = None
    ProductCategoriesService = None
    ProductSEOService = None
    ProductBundlesService = None
    ProductAttributesService = None

# Pydantic Models
class Product(BaseModel):
    """Pydantic model for a product, used for request and response validation."""
    id: Optional[str] = None
    sku: str
    name: str
    description: Optional[str] = None
    category: str
    brand: str
    price: Decimal
    cost: Decimal
    weight: float
    dimensions: Optional[Dict[str, Any]] = None
    condition: str = "new"
    grade: Optional[str] = "A"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ProductAgent(BaseAgent):
    """
    Production-ready Product Agent with all enhanced features
    """
    
    def __init__(self):
        """Initializes the ProductAgent with agent_id and agent_type, and sets up enhanced services and FastAPI app."""
        super().__init__(
            agent_id="product_agent",
            agent_type="product_management"
        )
        self.db_url = os.getenv("DATABASE_URL", "sqlite:///./product_agent.db")
        self.db_manager = DBManager(self.db_url)
        self.db_helper = DatabaseHelper(Base)
        self._db_initialized = False
        asyncio.create_task(self._init_db())
        
        # Initialize enhanced services
        self.variants_service = ProductVariantsService() if ProductVariantsService else None
        self.categories_service = ProductCategoriesService() if ProductCategoriesService else None
        self.seo_service = ProductSEOService() if ProductSEOService else None
        self.bundles_service = ProductBundlesService() if ProductBundlesService else None
        self.attributes_service = ProductAttributesService() if ProductAttributesService else None
        
        logger.info("Product Agent initialized with enhanced services")

    async def _init_db(self):
        """Initializes the database connection and creates tables if they don't exist."""
        try:
            await self.db_manager.connect()
            async with self.db_manager.get_session() as session:
                await self.db_helper.create_all_tables(session)
            self._db_initialized = True
            logger.info("Database initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            self._db_initialized = False
        
        # FastAPI app
        self.app = FastAPI(title="Product Agent API")
        self._setup_routes()
    
    def _setup_routes(self):
        """Sets up the FastAPI routes for the Product Agent, including health check, product CRUD, and service-specific endpoints."""
        
        @self.app.get("/")
        async def root():
            return {"message": "Product Agent is running"}

        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "agent_id": self.agent_id,
                "services": {
                    "variants": self.variants_service is not None,
                    "categories": self.categories_service is not None,
                    "seo": self.seo_service is not None,
                    "bundles": self.bundles_service is not None,
                    "attributes": self.attributes_service is not None
                }
            }
        
        @self.app.get("/products")
        async def get_products(skip: int = 0, limit: int = 100):
            """Get all products"""
            try:
                products = await self.get_products_from_db(skip, limit)
                return {"products": products, "total": len(products)}
            except Exception as e:
                logger.error(f"Error getting products: {e}")
                raise HTTPException(status_code=500, detail=str(e))
            except HTTPException:
                raise
        
        @self.app.post("/products")
        async def create_product(product: Product):
            """Create new product"""
            try:
                product_id = await self.create_product_in_db(product)
                
                # Auto-generate SEO if service available
                if self.seo_service:
                    await self.seo_service.generate_seo_metadata(str(product_id), product.dict())
                
                # Send message to other agents about product creation
                await self.send_message(
                    MessageType.PRODUCT_CREATED,
                    {"product_id": str(product_id), "product_name": product.name, "sku": product.sku}
                )
                
                return {"id": str(product_id), "status": "created"}
            except Exception as e:
                logger.error(f"Error creating product: {e}")
                raise HTTPException(status_code=500, detail=str(e))
            except HTTPException:
                raise

        @self.app.get("/products/{product_id}")
        async def get_product_by_id(product_id: str):
            """Get a product by its ID."""
            try:
                product = await self.get_product_by_id_from_db(product_id)
                if not product:
                    raise HTTPException(status_code=404, detail="Product not found")
                return product
            except Exception as e:
                logger.error(f"Error getting product by ID: {e}")
                raise HTTPException(status_code=500, detail=str(e))
            except HTTPException:
                raise

        @self.app.put("/products/{product_id}")
        async def update_product(product_id: str, product: Product):
            """Update an existing product."""
            try:
                updated_id = await self.update_product_in_db(product_id, product)
                if not updated_id:
                    raise HTTPException(status_code=404, detail="Product not found or failed to update")
                # Send message to other agents about product update
                await self.send_message(
                    MessageType.PRODUCT_UPDATED,
                    {"product_id": updated_id, "product_name": product.name, "sku": product.sku}
                )
                return {"id": updated_id, "status": "updated"}
            except Exception as e:
                logger.error(f"Error updating product: {e}")
                raise HTTPException(status_code=500, detail=str(e))
            except HTTPException:
                raise

        @self.app.delete("/products/{product_id}")
        async def delete_product(product_id: str):
            """Delete a product by its ID."""
            try:
                deleted = await self.delete_product_from_db(product_id)
                if not deleted:
                    raise HTTPException(status_code=404, detail="Product not found or failed to delete")
                return {"id": product_id, "status": "deleted"}
            except Exception as e:
                logger.error(f"Error deleting product: {e}")
                raise HTTPException(status_code=500, detail=str(e))
            except HTTPException:
                raise
        
        # Variants endpoints
        if self.variants_service:
            @self.app.get("/products/{product_id}/variants")
            async def get_product_variants(product_id: str):
                """Get all variants for a product"""
                try:
                    variants = await self.variants_service.get_variants(product_id)
                    return {"variants": variants}
                except Exception as e:
                    logger.error(f"Error getting variants: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
            except HTTPException:
                raise
        
        # Categories endpoints
        if self.categories_service:
            @self.app.get("/categories")
            async def get_categories():
                """Get all categories"""
                try:
                    categories = await self.categories_service.get_all_categories()
                    return {"categories": categories}
                except Exception as e:
                    logger.error(f"Error getting categories: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
            except HTTPException:
                raise
        
        # Bundles endpoints
        if self.bundles_service:
            @self.app.get("/bundles")
            async def get_bundles():
                """Get all product bundles"""
                try:
                    bundles = await self.bundles_service.get_all_bundles()
                    return {"bundles": bundles}
                except Exception as e:
                    logger.error(f"Error getting bundles: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
            except HTTPException:
                raise
    
    async def get_products_from_db(self, skip: int, limit: int) -> List[Dict]:
        """Get products from database"""
        # This would query the database
        # For now, return empty list
        logger.info(f"Getting products: skip={skip}, limit={limit}")
        if not self._db_initialized:
            logger.warning("Database not initialized. Cannot get products.")
            return []
        try:
            async with self.db_manager.get_session() as session:
                records = await self.db_helper.get_all(session, ProductDB, skip=skip, limit=limit)
            return [r.to_dict() for r in records]
        except Exception as e:
            logger.error(f"Error retrieving products from DB: {e}")
            return []

    
    async def create_product_in_db(self, product: Product) -> str:
        """Create product in database"""
        if not self._db_initialized:
            logger.warning("Database not initialized. Cannot create product.")
            return None
        try:
            new_product = ProductDB(
                id=uuid4(),
                sku=product.sku,
                name=product.name,
                description=product.description,
                category=product.category,
                brand=product.brand,
                price=float(product.price),
                cost=float(product.cost),
                weight=product.weight,
                dimensions=json.dumps(product.dimensions) if product.dimensions else None,
                condition=product.condition,
                grade=product.grade
            )
            async with self.db_manager.get_session() as session:
                created_product = await self.db_helper.create(session, new_product)
                logger.info(f"Created product: {created_product.name} with ID {created_product.id}")
                return created_product.id
        except Exception as e:
            logger.error(f"Error creating product in DB: {e}")
            return None
    
    async def get_product_by_id_from_db(self, product_id: str) -> Optional[Dict]:
        """Get a product from the database by its ID."""
        if not self._db_initialized:
            logger.warning("Database not initialized. Cannot get product by ID.")
            return None
        try:
            async with self.db_manager.get_session() as session:
                product_db = await self.db_helper.get_by_id(session, ProductDB, product_id)
                return product_db.to_dict() if product_db else None
        except Exception as e:
            logger.error(f"Error retrieving product by ID from DB: {e}")
            return None

    async def update_product_in_db(self, product_id: str, product: Product) -> Optional[str]:
        """Update an existing product in the database."""
        if not self._db_initialized:
            logger.warning("Database not initialized. Cannot update product.")
            return None
        try:
            async with self.db_manager.get_session() as session:
                existing_product = await self.db_helper.get_by_id(session, ProductDB, product_id)
                if not existing_product:
                    return None

                update_data = product.dict(exclude_unset=True)
                for key, value in update_data.items():
                    if hasattr(existing_product, key):
                        if key == "dimensions": # Special handling for dimensions
                            setattr(existing_product, key, json.dumps(value) if value else None)
                        else:
                            setattr(existing_product, key, value)

                updated_product = await self.db_helper.update(session, existing_product)
                logger.info(f"Updated product: {updated_product.name} with ID {updated_product.id}")
                return str(updated_product.id)
        except Exception as e:
            logger.error(f"Error updating product in DB: {e}")
            return None

    async def delete_product_from_db(self, product_id: str) -> bool:
        """Delete a product from the database."""
        if not self._db_initialized:
            logger.warning("Database not initialized. Cannot delete product.")
            return False
        try:
            async with self.db_manager.get_session() as session:
                deleted = await self.db_helper.delete(session, ProductDB, product_id)
                if deleted:
                    logger.info(f"Deleted product with ID: {product_id}")
                else:
                    logger.warning(f"Product with ID {product_id} not found for deletion.")
                return deleted
        except Exception as e:
            logger.error(f"Error deleting product from DB: {e}")
            return False

    async def process_message(self, message: AgentMessage):
        """Processes incoming messages from other agents or services."""
        logger.info(f"Processing message: {message.message_type}")
        
        if message.message_type == MessageType.PRODUCT_CREATED:
            await self.handle_product_created(message.payload)
        elif message.message_type == MessageType.PRODUCT_UPDATED:
            await self.handle_product_updated(message.payload)
        else:
            logger.warning(f"Unknown message type: {message.message_type}")
    
    async def handle_product_created(self, payload: Dict):
        """Handles PRODUCT_CREATED messages by generating SEO metadata if the service is available."""
        logger.info(f"Product created: {payload.get('product_id')}")
        
        # Auto-generate SEO
        if self.seo_service:
            await self.seo_service.generate_seo_metadata(
                payload.get('product_id'),
                payload
            )
    
    async def handle_product_updated(self, payload: Dict):
        """Handles PRODUCT_UPDATED messages."""
        logger.info(f"Product updated: {payload.get('product_id')}")

# Create agent instance
agent = ProductAgent()
app = agent.app

if __name__ == "__main__":
    import uvicorn
    UVICORN_PORT = int(os.getenv("UVICORN_PORT", 8002))
    logger.info(f"Starting Product Agent on port {UVICORN_PORT}")
    try:
        uvicorn.run(app, host="0.0.0.0", port=UVICORN_PORT)
    except Exception as e:
        logger.error(f"Failed to start uvicorn server: {e}")

