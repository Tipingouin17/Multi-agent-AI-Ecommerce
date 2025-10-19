"""
Product Agent - Multi-Agent E-commerce System

This agent manages the master product catalog, handles product information
synchronization across channels, and manages pricing and availability updates.
"""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import structlog
import sys
import os

# Get the absolute path of the current file
current_file_path = os.path.abspath(__file__)

# Get the directory containing the current file
current_dir = os.path.dirname(current_file_path)

# Get the parent directory (project root)
project_root = os.path.dirname(current_dir)

# Add the project root to the Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added {project_root} to Python path")

# Now try the import
try:
    from shared.base_agent import BaseAgent, MessageType, AgentMessage
    print("Successfully imported shared.base_agent")
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current sys.path: {sys.path}")
    
    # List files in the shared directory to verify it exists
    shared_dir = os.path.join(project_root, "shared")
    if os.path.exists(shared_dir):
        print(f"Contents of {shared_dir}:")
        for item in os.listdir(shared_dir):
            print(f"  - {item}")
    else:
        print(f"Directory not found: {shared_dir}")

from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.models import (
    Product, ProductBase, ProductCondition, RefurbishedGrade,
    APIResponse, PaginatedResponse
)
from shared.database import DatabaseManager, BaseRepository, get_database_manager


logger = structlog.get_logger(__name__)


class ProductCreateRequest(BaseModel):
    """Request model for creating a new product."""
    name: str
    description: str
    category: str
    brand: str
    sku: str
    price: Decimal
    cost: Decimal
    weight: float
    dimensions: Dict[str, float]
    condition: ProductCondition
    grade: Optional[RefurbishedGrade] = None


class ProductUpdateRequest(BaseModel):
    """Request model for updating a product."""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    weight: Optional[float] = None
    dimensions: Optional[Dict[str, float]] = None
    condition: Optional[ProductCondition] = None
    grade: Optional[RefurbishedGrade] = None


class PriceUpdateRequest(BaseModel):
    """Request model for updating product price."""
    price: Decimal
    reason: Optional[str] = None


class ProductSyncRequest(BaseModel):
    """Request model for syncing products to channels."""
    product_ids: Optional[List[str]] = None  # If None, sync all products
    channels: Optional[List[str]] = None  # If None, sync to all channels


class ProductRepository(BaseRepository):
    """Repository for product data operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        from shared.models import ProductDB
        super().__init__(db_manager, ProductDB)
    
    async def find_by_sku(self, sku: str) -> Optional[Product]:
        """Find product by SKU."""
        records = await self.find_by_criteria(sku=sku)
        return self._to_pydantic(records[0]) if records else None
    
    async def find_by_category(self, category: str) -> List[Product]:
        """Find products by category."""
        records = await self.find_by_criteria(category=category)
        return [self._to_pydantic(record) for record in records]
    
    async def find_by_brand(self, brand: str) -> List[Product]:
        """Find products by brand."""
        records = await self.find_by_criteria(brand=brand)
        return [self._to_pydantic(record) for record in records]
    
    async def find_by_condition(self, condition: ProductCondition) -> List[Product]:
        """Find products by condition."""
        records = await self.find_by_criteria(condition=condition.value)
        return [self._to_pydantic(record) for record in records]
    
    async def search_products(self, query: str) -> List[Product]:
        """Search products by name or description."""
        # This would typically use full-text search in production
        async with self.db_manager.get_async_session() as session:
            from shared.models import ProductDB
            from sqlalchemy import or_, func
            
            result = await session.execute(
                session.query(ProductDB).filter(
                    or_(
                        func.lower(ProductDB.name).contains(query.lower()),
                        func.lower(ProductDB.description).contains(query.lower())
                    )
                )
            )
            records = result.scalars().all()
            return [self._to_pydantic(record) for record in records]
    
    def _to_pydantic(self, db_record) -> Product:
        """Convert database record to Pydantic model."""
        return Product(
            id=db_record.id,
            name=db_record.name,
            description=db_record.description,
            category=db_record.category,
            brand=db_record.brand,
            sku=db_record.sku,
            price=db_record.price,
            cost=db_record.cost,
            weight=db_record.weight,
            dimensions=db_record.dimensions,
            condition=ProductCondition(db_record.condition),
            grade=RefurbishedGrade(db_record.grade) if db_record.grade else None,
            created_at=db_record.created_at,
            updated_at=db_record.updated_at
        )


class ProductAgent(BaseAgent):
    """
    Product Agent handles all product-related operations including:
    - Product catalog management
    - Price updates and synchronization
    - Product information updates
    - Channel synchronization
    """
    
    def __init__(self, **kwargs):
        super().__init__(agent_id="product_agent", **kwargs)
        self.repository: Optional[ProductRepository] = None
        self.app = FastAPI(title="Product Agent API", version="1.0.0")
        self.setup_routes()
        
        # Register message handlers
        self.register_handler(MessageType.PRICE_UPDATE, self._handle_price_update)
        self.register_handler(MessageType.ORDER_CREATED, self._handle_order_created)
    
    async def initialize(self):
        """Initialize the Product Agent."""
        self.logger.info("Initializing Product Agent")
        
        # Initialize database repository
        db_manager = get_database_manager()
        self.repository = ProductRepository(db_manager)
        
        # Start background tasks
        asyncio.create_task(self._sync_products_periodically())
        asyncio.create_task(self._monitor_price_changes())
        
        self.logger.info("Product Agent initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up Product Agent")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process product-specific business logic."""
        action = data.get("action")
        
        if action == "create_product":
            return await self._create_product(data["product_data"])
        elif action == "update_product":
            return await self._update_product(data["product_id"], data["updates"])
        elif action == "get_product":
            return await self._get_product(data["product_id"])
        elif action == "search_products":
            return await self._search_products(data["query"])
        elif action == "sync_to_channels":
            return await self._sync_to_channels(data.get("product_ids"), data.get("channels"))
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def setup_routes(self):
        """Setup FastAPI routes for the Product Agent."""
        
        @self.app.post("/products", response_model=APIResponse)
        async def create_product(request: ProductCreateRequest):
            """Create a new product."""
            try:
                result = await self._create_product(request.dict())
                
                return APIResponse(
                    success=True,
                    message="Product created successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to create product", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/products/{product_id}", response_model=APIResponse)
        async def get_product(product_id: str):
            """Get product by ID."""
            try:
                product = await self._get_product(product_id)
                if not product:
                    raise HTTPException(status_code=404, detail="Product not found")
                
                return APIResponse(
                    success=True,
                    message="Product retrieved successfully",
                    data=product
                )
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get product", error=str(e), product_id=product_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.put("/products/{product_id}", response_model=APIResponse)
        async def update_product(product_id: str, request: ProductUpdateRequest):
            """Update product information."""
            try:
                updates = request.dict(exclude_unset=True)
                result = await self._update_product(product_id, updates)
                
                return APIResponse(
                    success=True,
                    message="Product updated successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to update product", error=str(e), product_id=product_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.put("/products/{product_id}/price", response_model=APIResponse)
        async def update_product_price(product_id: str, request: PriceUpdateRequest):
            """Update product price."""
            try:
                result = await self._update_product_price(product_id, request.price, request.reason)
                
                return APIResponse(
                    success=True,
                    message="Product price updated successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to update product price", error=str(e), product_id=product_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/products", response_model=APIResponse)
        async def list_products(
            category: Optional[str] = None,
            brand: Optional[str] = None,
            condition: Optional[str] = None,
            search: Optional[str] = None,
            page: int = 1,
            per_page: int = 20
        ):
            """List products with optional filters."""
            try:
                filters = {}
                if category:
                    filters["category"] = category
                if brand:
                    filters["brand"] = brand
                if condition:
                    filters["condition"] = condition
                if search:
                    filters["search"] = search
                
                filters["page"] = page
                filters["per_page"] = per_page
                
                result = await self._list_products(filters)
                
                return APIResponse(
                    success=True,
                    message="Products retrieved successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to list products", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/products/sync", response_model=APIResponse)
        async def sync_products(request: ProductSyncRequest):
            """Sync products to channels."""
            try:
                result = await self._sync_to_channels(request.product_ids, request.channels)
                
                return APIResponse(
                    success=True,
                    message="Product sync initiated successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to sync products", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/products/sku/{sku}", response_model=APIResponse)
        async def get_product_by_sku(sku: str):
            """Get product by SKU."""
            try:
                product = await self.repository.find_by_sku(sku)
                if not product:
                    raise HTTPException(status_code=404, detail="Product not found")
                
                return APIResponse(
                    success=True,
                    message="Product retrieved successfully",
                    data=product.dict()
                )
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get product by SKU", error=str(e), sku=sku)
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product."""
        try:
            # Check if SKU already exists
            existing_product = await self.repository.find_by_sku(product_data["sku"])
            if existing_product:
                raise ValueError(f"Product with SKU {product_data['sku']} already exists")
            
            # Generate product ID
            product_id = str(uuid4())
            product_data["id"] = product_id
            product_data["created_at"] = datetime.utcnow()
            product_data["updated_at"] = datetime.utcnow()
            
            # Create product in database
            await self.repository.create(**product_data)
            
            # Send product created notification
            await self.send_message(
                recipient_agent="broadcast",
                message_type=MessageType.ORDER_CREATED,  # Using ORDER_CREATED as generic notification
                payload={
                    "event_type": "product_created",
                    "product_id": product_id,
                    "sku": product_data["sku"],
                    "name": product_data["name"],
                    "category": product_data["category"]
                }
            )
            
            # Sync to all channels
            await self._sync_to_channels([product_id], None)
            
            self.logger.info("Product created", product_id=product_id, sku=product_data["sku"])
            
            return {"product_id": product_id, "status": "created"}
        
        except Exception as e:
            self.logger.error("Failed to create product", error=str(e))
            raise
    
    async def _get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product by ID."""
        try:
            product = await self.repository.get_by_id(product_id)
            if product:
                return product.__dict__
            return None
        
        except Exception as e:
            self.logger.error("Failed to get product", error=str(e), product_id=product_id)
            raise
    
    async def _update_product(self, product_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update product information."""
        try:
            # Get current product
            product = await self.repository.get_by_id(product_id)
            if not product:
                raise ValueError(f"Product {product_id} not found")
            
            # Add update timestamp
            updates["updated_at"] = datetime.utcnow()
            
            # Update product
            await self.repository.update(product_id, **updates)
            
            # Send product updated notification
            await self.send_message(
                recipient_agent="broadcast",
                message_type=MessageType.ORDER_UPDATED,  # Using ORDER_UPDATED as generic notification
                payload={
                    "event_type": "product_updated",
                    "product_id": product_id,
                    "updates": updates
                }
            )
            
            # Sync changes to channels
            await self._sync_to_channels([product_id], None)
            
            self.logger.info("Product updated", product_id=product_id, updates=list(updates.keys()))
            
            return {"product_id": product_id, "status": "updated", "updates": updates}
        
        except Exception as e:
            self.logger.error("Failed to update product", error=str(e), product_id=product_id)
            raise
    
    async def _update_product_price(self, product_id: str, new_price: Decimal, reason: Optional[str] = None) -> Dict[str, Any]:
        """Update product price."""
        try:
            # Get current product
            product = await self.repository.get_by_id(product_id)
            if not product:
                raise ValueError(f"Product {product_id} not found")
            
            old_price = product.price
            
            # Update price
            await self.repository.update(product_id, price=new_price, updated_at=datetime.utcnow())
            
            # Send price update notification
            await self.send_message(
                recipient_agent="broadcast",
                message_type=MessageType.PRICE_UPDATE,
                payload={
                    "product_id": product_id,
                    "sku": product.sku,
                    "old_price": float(old_price),
                    "new_price": float(new_price),
                    "reason": reason,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Sync price changes to channels
            await self._sync_to_channels([product_id], None)
            
            self.logger.info("Product price updated", product_id=product_id, old_price=float(old_price), new_price=float(new_price))
            
            return {
                "product_id": product_id,
                "old_price": float(old_price),
                "new_price": float(new_price),
                "status": "updated"
            }
        
        except Exception as e:
            self.logger.error("Failed to update product price", error=str(e), product_id=product_id)
            raise
    
    async def _list_products(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """List products with filters and pagination."""
        try:
            page = filters.get("page", 1)
            per_page = min(filters.get("per_page", 20), 100)  # Max 100 per page
            offset = (page - 1) * per_page
            
            # Apply filters
            if filters.get("search"):
                products = await self.repository.search_products(filters["search"])
            elif filters.get("category"):
                products = await self.repository.find_by_category(filters["category"])
            elif filters.get("brand"):
                products = await self.repository.find_by_brand(filters["brand"])
            elif filters.get("condition"):
                products = await self.repository.find_by_condition(ProductCondition(filters["condition"]))
            else:
                products = await self.repository.get_all(limit=per_page, offset=offset)
            
            # Apply pagination to filtered results
            total = len(products)
            start_idx = offset
            end_idx = start_idx + per_page
            paginated_products = products[start_idx:end_idx]
            
            pages = (total + per_page - 1) // per_page
            
            return PaginatedResponse(
                items=[product.dict() for product in paginated_products],
                total=total,
                page=page,
                per_page=per_page,
                pages=pages
            ).dict()
        
        except Exception as e:
            self.logger.error("Failed to list products", error=str(e))
            raise
    
    async def _sync_to_channels(self, product_ids: Optional[List[str]], channels: Optional[List[str]]) -> Dict[str, Any]:
        """Sync products to specified channels."""
        try:
            # Get products to sync
            if product_ids:
                products = []
                for product_id in product_ids:
                    product = await self.repository.get_by_id(product_id)
                    if product:
                        products.append(product)
            else:
                products = await self.repository.get_all(limit=1000)  # Sync up to 1000 products
            
            # Default channels if not specified
            if not channels:
                channels = ["mirakl", "shopify", "woocommerce", "prestashop", "back_market", "refurbed"]
            
            sync_results = {}
            
            for channel in channels:
                try:
                    # Send sync request to appropriate channel connector
                    if channel in ["mirakl"]:
                        recipient = "standard_marketplace_agent"
                    elif channel in ["back_market", "refurbed"]:
                        recipient = "refurbished_marketplace_agent"
                    elif channel in ["shopify", "woocommerce", "prestashop"]:
                        recipient = "ecommerce_platform_agent"
                    else:
                        continue
                    
                    await self.send_message(
                        recipient_agent=recipient,
                        message_type=MessageType.ORDER_UPDATED,  # Using as generic sync message
                        payload={
                            "action": "sync_products",
                            "channel": channel,
                            "products": [product.dict() for product in products]
                        }
                    )
                    
                    sync_results[channel] = "initiated"
                    
                except Exception as e:
                    self.logger.error("Failed to sync to channel", error=str(e), channel=channel)
                    sync_results[channel] = f"failed: {str(e)}"
            
            self.logger.info("Product sync initiated", channels=channels, product_count=len(products))
            
            return {
                "status": "sync_initiated",
                "channels": sync_results,
                "product_count": len(products)
            }
        
        except Exception as e:
            self.logger.error("Failed to sync products to channels", error=str(e))
            raise
    
    async def _search_products(self, query: str) -> List[Dict[str, Any]]:
        """Search products by query."""
        try:
            products = await self.repository.search_products(query)
            return [product.dict() for product in products]
        
        except Exception as e:
            self.logger.error("Failed to search products", error=str(e), query=query)
            raise
    
    async def _handle_price_update(self, message: AgentMessage):
        """Handle price update messages from other agents (e.g., dynamic pricing agent)."""
        payload = message.payload
        product_id = payload.get("product_id")
        new_price = payload.get("new_price")
        reason = payload.get("reason", "Automated price update")
        
        if product_id and new_price:
            try:
                await self._update_product_price(product_id, Decimal(str(new_price)), reason)
                self.logger.info("Price updated from external agent", product_id=product_id, new_price=new_price)
            except Exception as e:
                self.logger.error("Failed to update price from external agent", error=str(e), product_id=product_id)
    
    async def _handle_order_created(self, message: AgentMessage):
        """Handle order created messages to track product demand."""
        payload = message.payload
        items = payload.get("items", [])
        
        # Track product demand for analytics
        for item in items:
            product_id = item.get("product_id")
            quantity = item.get("quantity", 0)
            
            if product_id:
                # Send demand data to forecasting agent
                await self.send_message(
                    recipient_agent="demand_forecasting_agent",
                    message_type=MessageType.ORDER_CREATED,
                    payload={
                        "product_id": product_id,
                        "quantity_sold": quantity,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
    
    async def _sync_products_periodically(self):
        """Background task to sync products to channels periodically."""
        while not self.shutdown_event.is_set():
            try:
                # Sync all products every 6 hours
                await asyncio.sleep(6 * 3600)
                
                if not self.shutdown_event.is_set():
                    self.logger.info("Starting periodic product sync")
                    await self._sync_to_channels(None, None)
                    self.logger.info("Periodic product sync completed")
            
            except Exception as e:
                self.logger.error("Error in periodic product sync", error=str(e))
                await asyncio.sleep(3600)  # Wait 1 hour on error
    
    async def _monitor_price_changes(self):
        """Background task to monitor and validate price changes."""
        while not self.shutdown_event.is_set():
            try:
                # Check for products with recent price changes
                # This could include validation logic, competitor price checking, etc.
                await asyncio.sleep(1800)  # Check every 30 minutes
                
                # Placeholder for price monitoring logic
                self.logger.debug("Price monitoring check completed")
            
            except Exception as e:
                self.logger.error("Error in price monitoring", error=str(e))
                await asyncio.sleep(3600)  # Wait 1 hour on error


# FastAPI app instance for running the agent as a service
app = FastAPI(title="Product Agent", version="1.0.0")

# Global agent instance
product_agent: Optional[ProductAgent] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the Product Agent on startup."""
    global product_agent
    product_agent = ProductAgent()
    await product_agent.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup the Product Agent on shutdown."""
    global product_agent
    if product_agent:
        await product_agent.stop()


# Include agent routes
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if product_agent:
        health_status = product_agent.get_health_status()
        return {"status": "healthy", "agent_status": health_status.dict()}
    return {"status": "unhealthy", "message": "Agent not initialized"}


# Mount agent's FastAPI app
app.mount("/api/v1", product_agent.app if product_agent else FastAPI())


if __name__ == "__main__":
    import uvicorn
    from shared.database import initialize_database_manager, DatabaseConfig
    import os
    
    # Initialize database
    db_config = DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "multi_agent_ecommerce"),
        username=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres123")
    )
    initialize_database_manager(db_config)
    
    # Run the agent
    uvicorn.run(
        "product_agent:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
        log_level="info"
    )
