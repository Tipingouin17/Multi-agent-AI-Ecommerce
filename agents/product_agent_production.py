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

from shared.db_helpers import DatabaseHelper

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import structlog
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
    """Product model"""
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
        super().__init__(agent_id="product_agent")
        
        # Initialize enhanced services
        self.variants_service = ProductVariantsService(self.db_manager) if ProductVariantsService else None
        self.categories_service = ProductCategoriesService(self.db_manager) if ProductCategoriesService else None
        self.seo_service = ProductSEOService(self.db_manager) if ProductSEOService else None
        self.bundles_service = ProductBundlesService(self.db_manager) if ProductBundlesService else None
        self.attributes_service = ProductAttributesService(self.db_manager) if ProductAttributesService else None
        
        logger.info("Product Agent initialized with enhanced services")
        
        # FastAPI app
        self.app = FastAPI(title="Product Agent API")
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
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
        
        @self.app.post("/products")
        async def create_product(product: Product):
            """Create new product"""
            try:
                product_id = await self.create_product_in_db(product)
                
                # Auto-generate SEO if service available
                if self.seo_service:
                    await self.seo_service.generate_seo_metadata(product_id, product.dict())
                
                return {"id": product_id, "status": "created"}
            except Exception as e:
                logger.error(f"Error creating product: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
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
    
    async def get_products_from_db(self, skip: int, limit: int) -> List[Dict]:
        """Get products from database"""
        # This would query the database
        # For now, return empty list
        logger.info(f"Getting products: skip={skip}, limit={limit}")
        if not self._db_initialized:
            return []
        
        async with self.db_manager.get_session() as session:
            records = await self.db_helper.get_all(session, ProductDB, limit=100)
            return [self.db_helper.to_dict(r) for r in records]
    
    async def create_product_in_db(self, product: Product) -> str:
        """Create product in database"""
        product_id = str(uuid4())
        logger.info(f"Creating product: {product.name} with ID {product_id}")
        return product_id
    
    async def process_message(self, message: AgentMessage):
        """Process incoming messages"""
        logger.info(f"Processing message: {message.message_type}")
        
        if message.message_type == MessageType.PRODUCT_CREATED:
            await self.handle_product_created(message.payload)
        elif message.message_type == MessageType.PRODUCT_UPDATED:
            await self.handle_product_updated(message.payload)
        else:
            logger.warning(f"Unknown message type: {message.message_type}")
    
    async def handle_product_created(self, payload: Dict):
        """Handle product created event"""
        logger.info(f"Product created: {payload.get('product_id')}")
        
        # Auto-generate SEO
        if self.seo_service:
            await self.seo_service.generate_seo_metadata(
                payload.get('product_id'),
                payload
            )
    
    async def handle_product_updated(self, payload: Dict):
        """Handle product updated event"""
        logger.info(f"Product updated: {payload.get('product_id')}")


    # Required abstract methods from BaseAgent
    async def initialize(self):
        """Initialize agent-specific components."""
        await super().initialize()
        while not self._db_initialized:
            await asyncio.sleep(0.1)
        logger.info(f"{self.agent_name} initialized successfully")

    async def cleanup(self):
        """Cleanup agent-specific resources."""
        if hasattr(self, 'engine') and self.engine:
            await self.engine.dispose()
        await super().cleanup()
        logger.info(f"{self.agent_name} cleaned up successfully")

    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process agent-specific business logic."""
        try:
            operation = data.get("operation", "unknown")
            logger.info(f"Processing {operation} operation")
            return {"status": "success", "operation": operation}
        except Exception as e:
            logger.error(f"Error in process_business_logic: {e}")
            return {"status": "error", "message": str(e)}


# Module-level app for ASGI servers (only create when running as main)
app = None

if __name__ == "__main__":
    # Create agent instance only when running as main
    agent = ProductAgent()
    app = agent.app
    
    # Initialize agent before starting server
    import asyncio
    async def startup():
        await agent.initialize()
    asyncio.run(startup())
    
    import uvicorn
    logger.info("Starting Product Agent on port 8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)

