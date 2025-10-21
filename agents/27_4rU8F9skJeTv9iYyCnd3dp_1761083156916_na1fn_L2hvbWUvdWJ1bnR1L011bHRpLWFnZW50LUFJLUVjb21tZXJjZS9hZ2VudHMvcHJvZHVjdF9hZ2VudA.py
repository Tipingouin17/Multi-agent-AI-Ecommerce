
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

# Ensure the project root is in the Python path for shared modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.models import (
    Product, ProductBase, ProductCondition, RefurbishedGrade,
    APIResponse, PaginatedResponse, DatabaseConfig
)
from shared.database import DatabaseManager, BaseRepository, get_database_manager, initialize_database_manager


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
    dimensions: Optional[Dict[str, float>] = None
    condition: Optional[ProductCondition] = None
    grade: Optional[RefurbishedGrade] = None


class PriceUpdateRequest(BaseModel):
    """Request model for updating product price."""
    price: Decimal
    reason: Optional[str] = None


class ProductSyncRequest(BaseModel):
    """Request model for syncing products to channels."""
    product_ids: Optional[List[str]] = None  # If None, sync all products
    channels: Optional[List[str>] = None  # If None, sync to all channels


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
        # Pop Kafka-related parameters from kwargs as BaseAgent handles them
        kafka_bootstrap_servers = kwargs.pop("kafka_bootstrap_servers", None)
        super().__init__(
            agent_id="product_agent",
            kafka_bootstrap_servers=kafka_bootstrap_servers,
            **kwargs
        )
        self.repository: Optional[ProductRepository] = None
        self.app = FastAPI(title="Product Agent API", version="1.0.0")
        self.setup_routes()
        
        # Register message handlers
        self.register_handler(MessageType.PRICE_UPDATE, self._handle_price_update)
        self.register_handler(MessageType.ORDER_CREATED, self._handle_order_created)
        self.register_handler(MessageType.PRODUCT_SYNC_REQUEST, self._handle_product_sync_request)

    async def initialize(self):
        """Initialize the Product Agent."""
        self.logger.info("Initializing Product Agent")
        
        # BaseAgent handles database initialization, ensure it's available
        if self.db_manager is None:
            raise RuntimeError("DatabaseManager not initialized by BaseAgent.")
        self.repository = ProductRepository(self.db_manager)
        
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
        async def create_product_api(request: ProductCreateRequest):
            """Create a new product."""
            try:
                product_dict = request.dict()
                # Convert price, cost, weight to Decimal if they are not already
                if 'price' in product_dict: product_dict['price'] = Decimal(str(product_dict['price']))
                if 'cost' in product_dict: product_dict['cost'] = Decimal(str(product_dict['cost']))
                if 'weight' in product_dict: product_dict['weight'] = float(product_dict['weight'])

                result = await self._create_product(product_dict)
                
                return APIResponse(
                    success=True,
                    message="Product created successfully",
                    data=result.dict() # Convert Pydantic model to dict for APIResponse
                )
            
            except Exception as e:
                self.logger.error("Failed to create product", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/products/{product_id}", response_model=APIResponse)
        async def get_product_api(product_id: str):
            """Get product by ID."""
            try:
                product = await self._get_product(product_id)
                if not product:
                    raise HTTPException(status_code=404, detail="Product not found")
                
                return APIResponse(
                    success=True,
                    message="Product retrieved successfully",
                    data=product.dict() # Convert Pydantic model to dict for APIResponse
                )
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get product", error=str(e), product_id=product_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.put("/products/{product_id}", response_model=APIResponse)
        async def update_product_api(product_id: str, request: ProductUpdateRequest):
            """Update product information."""
            try:
                updates = request.dict(exclude_unset=True)
                if 'price' in updates: updates['price'] = Decimal(str(updates['price']))
                if 'cost' in updates: updates['cost'] = Decimal(str(updates['cost']))
                if 'weight' in updates: updates['weight'] = float(updates['weight'])

                result = await self._update_product(product_id, updates)
                
                return APIResponse(
                    success=True,
                    message="Product updated successfully",
                    data=result.dict() # Convert Pydantic model to dict for APIResponse
                )
            
            except Exception as e:
                self.logger.error("Failed to update product", error=str(e), product_id=product_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/products/{product_id}", response_model=APIResponse)
        async def delete_product_api(product_id: str):
            """Delete a product."""
            try:
                success = await self._delete_product(product_id)
                if not success:
                    raise HTTPException(status_code=404, detail="Product not found or could not be deleted")
                
                return APIResponse(
                    success=True,
                    message="Product deleted successfully"
                )
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to delete product", error=str(e), product_id=product_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/products", response_model=PaginatedResponse)
        async def list_products_api(limit: int = 10, offset: int = 0):
            """List all products with pagination."""
            try:
                products = await self._list_products(limit, offset)
                total_count = await self._count_products()
                
                return PaginatedResponse(
                    success=True,
                    message="Products retrieved successfully",
                    items=[p.dict() for p in products],
                    total_count=total_count,
                    page=offset // limit + 1,
                    page_size=limit
                )
            
            except Exception as e:
                self.logger.error("Failed to list products", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/products/search", response_model=APIResponse)
        async def search_products_api(query: str):
            """Search products by name or description."""
            try:
                products = await self._search_products(query)
                
                return APIResponse(
                    success=True,
                    message="Products found successfully",
                    data=[p.dict() for p in products]
                )
            
            except Exception as e:
                self.logger.error("Failed to search products", error=str(e), query=query)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/products/{product_id}/price", response_model=APIResponse)
        async def update_product_price_api(product_id: str, request: PriceUpdateRequest):
            """Update product price and notify other agents."""
            try:
                updated_product = await self._update_product_price(product_id, request.price, request.reason)
                
                return APIResponse(
                    success=True,
                    message="Product price updated successfully",
                    data=updated_product.dict()
                )
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update product price", error=str(e), product_id=product_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/products/sync", response_model=APIResponse)
        async def sync_products_to_channels_api(request: ProductSyncRequest):
            """Trigger synchronization of products to external channels."""
            try:
                await self._sync_to_channels(request.product_ids, request.channels)
                
                return APIResponse(
                    success=True,
                    message="Product synchronization initiated successfully"
                )
            
            except Exception as e:
                self.logger.error("Failed to initiate product sync", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health", response_model=APIResponse)
        async def health_check():
            """Health check endpoint."""
            try:
                # Check database connection
                if self.db_manager is None:
                    raise RuntimeError("DatabaseManager not initialized.")
                await self.db_manager.test_connection()
                
                # Check Kafka connection (if applicable)
                # For AIOKafkaProducer, there isn't a direct 'ping' method.
                # A simple way to check is to try sending a dummy message or
                # check if the producer is connected, but that's usually handled
                # by the producer's internal state and error handling on send.
                # For now, we'll assume if the agent started, Kafka is reachable.
                
                return APIResponse(
                    success=True,
                    message="Product Agent is healthy",
                    status_code=200
                )
            except Exception as e:
                self.logger.error("Health check failed", error=str(e))
                raise HTTPException(status_code=500, detail=f"Health check failed: {e}")

    
    async def _create_product(self, product_data: Dict[str, Any]) -> Product:
        """Internal method to create a product."""
        try:
            # Convert float weight/dimensions to Decimal if necessary
            if 'weight' in product_data: product_data['weight'] = Decimal(str(product_data['weight']))
            if 'price' in product_data: product_data['price'] = Decimal(str(product_data['price']))
            if 'cost' in product_data: product_data['cost'] = Decimal(str(product_data['cost']))

            # Ensure dimensions are stored as JSONB compatible
            if 'dimensions' in product_data and isinstance(product_data['dimensions'], dict):
                product_data['dimensions'] = {k: float(v) for k, v in product_data['dimensions'].items()}

            product_db = await self.repository.create(**product_data)
            product = self.repository._to_pydantic(product_db)
            self.logger.info("Product created", product_id=product.id)
            
            # Publish event to Kafka
            await self.send_message(
                recipient_agent="all", # Or a specific topic for product events
                message_type=MessageType.PRODUCT_CREATED,
                payload={"product_id": str(product.id), "sku": product.sku, "name": product.name, "price": str(product.price)}
            )
            
            return product
        except Exception as e:
            self.logger.error("Error creating product", error=str(e), product_data=product_data)
            raise

    
    async def _get_product(self, product_id: str) -> Optional[Product]:
        """Internal method to get a product by ID."""
        try:
            product_db = await self.repository.get_by_id(product_id)
            if product_db:
                return self.repository._to_pydantic(product_db)
            return None
        except Exception as e:
            self.logger.error("Failed to get product", error=str(e), product_id=product_id)
            raise

    
    async def _update_product(self, product_id: str, updates: Dict[str, Any]) -> Product:
        """Internal method to update product information."""
        try:
            # Convert Decimal fields if present
            if 'price' in updates: updates['price'] = Decimal(str(updates['price']))
            if 'cost' in updates: updates['cost'] = Decimal(str(updates['cost']))
            if 'weight' in updates: updates['weight'] = Decimal(str(updates['weight']))

            product_db = await self.repository.update(product_id, **updates)
            if not product_db:
                raise HTTPException(status_code=404, detail="Product not found")
            
            product = self.repository._to_pydantic(product_db)
            self.logger.info("Product updated", product_id=product.id, updates=updates)
            
            # Publish event to Kafka
            await self.send_message(
                recipient_agent="all", # Or a specific topic for product events
                message_type=MessageType.PRODUCT_UPDATED,
                payload={"product_id": str(product.id), "sku": product.sku, "name": product.name, "updates": updates}
            )
            
            return product
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error("Error updating product", error=str(e), product_id=product_id, updates=updates)
            raise

    
    async def _delete_product(self, product_id: str) -> bool:
        """Internal method to delete a product."""
        try:
            success = await self.repository.delete(product_id)
            if success:
                self.logger.info("Product deleted", product_id=product_id)
                # Publish event to Kafka
                await self.send_message(
                    recipient_agent="all", # Or a specific topic for product events
                    message_type=MessageType.PRODUCT_DELETED,
                    payload={"product_id": product_id}
                )
            return success
        except Exception as e:
            self.logger.error("Error deleting product", error=str(e), product_id=product_id)
            raise

    
    async def _list_products(self, limit: int, offset: int) -> List[Product]:
        """Internal method to list products with pagination."""
        try:
            product_dbs = await self.repository.get_all(limit=limit, offset=offset)
            return [self.repository._to_pydantic(p) for p in product_dbs]
        except Exception as e:
            self.logger.error("Error listing products", error=str(e), limit=limit, offset=offset)
            raise

    
    async def _count_products(self) -> int:
        """Internal method to count total products."""
        try:
            return await self.repository.count()
        except Exception as e:
            self.logger.error("Error counting products", error=str(e))
            raise

    
    async def _search_products(self, query: str) -> List[Product]:
        """Internal method to search products."""
        try:
            product_dbs = await self.repository.search_products(query)
            return product_dbs  # search_products already returns Pydantic models
        except Exception as e:
            self.logger.error("Error searching products", error=str(e), query=query)
            raise

    
    async def _update_product_price(self, product_id: str, new_price: Decimal, reason: Optional[str] = None) -> Product:
        """Internal method to update product price."""
        try:
            product_db = await self.repository.update(product_id, price=new_price)
            if not product_db:
                raise HTTPException(status_code=404, detail="Product not found")
            
            product = self.repository._to_pydantic(product_db)
            self.logger.info("Product price updated", product_id=product.id, new_price=new_price, reason=reason)
            
            # Publish event to Kafka
            await self.send_message(
                recipient_agent="all", # Or a specific topic for product events
                message_type=MessageType.PRICE_UPDATE,
                payload={"product_id": str(product.id), "sku": product.sku, "old_price": str(product_db.price), "new_price": str(new_price), "reason": reason}
            )
            
            return product
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error("Error updating product price", error=str(e), product_id=product_id, new_price=new_price)
            raise

    
    async def _sync_to_channels(self, product_ids: Optional[List[str]] = None, channels: Optional[List[str]] = None):
        """Internal method to synchronize products to external channels."""
        self.logger.info("Initiating product sync to channels", product_ids=product_ids, channels=channels)
        
        # In a real system, this would involve calling external APIs for each channel
        # For now, we'll just log the action and send a message.
        
        # Example: Fetch products to sync
        products_to_sync = []
        if product_ids:
            for p_id in product_ids:
                product = await self._get_product(p_id)
                if product: products_to_sync.append(product)
        else:
            # Fetch all products if no specific IDs are provided
            product_dbs = await self.repository.get_all(limit=1000) # Adjust limit as needed
            products_to_sync = [self.repository._to_pydantic(p) for p in product_dbs]

        for product in products_to_sync:
            self.logger.info("Simulating sync for product", product_id=product.id, product_name=product.name, channels=channels)
            # Publish event to Kafka for each product to be synced
            await self.send_message(
                recipient_agent="all", # Or a specific topic for product events
                message_type=MessageType.PRODUCT_SYNC_REQUEST,
                payload={"product_id": str(product.id), "sku": product.sku, "channels": channels}
            )
        
        self.logger.info("Product sync process completed for requested products/channels")

    
    async def _handle_price_update(self, message: AgentMessage):
        """Handle price update messages from other agents."""
        product_id = message.payload.get("product_id")
        new_price_str = message.payload.get("new_price")
        reason = message.payload.get("reason", "External system update")
        
        if not product_id or not new_price_str:
            self.logger.error("Invalid PRICE_UPDATE message payload", payload=message.payload)
            return
        
        try:
            new_price = Decimal(new_price_str)
            # Update product price in the database
            await self._update_product_price(product_id, new_price, reason)
            self.logger.info("Handled price update message", product_id=product_id, new_price=new_price)
        except Exception as e:
            self.logger.error("Failed to process PRICE_UPDATE message", error=str(e), payload=message.payload)

    
    async def _handle_order_created(self, message: AgentMessage):
        """Handle order created messages from other agents."""
        order_id = message.payload.get("order_id")
        customer_id = message.payload.get("customer_id")
        items = message.payload.get("items")
        
        self.logger.info("Received ORDER_CREATED message", order_id=order_id, customer_id=customer_id)
        
        if not order_id or not customer_id or not items:
            self.logger.error("Invalid ORDER_CREATED message payload", payload=message.payload)
            return
        
        # Example: Deduct inventory for ordered items (simplified)
        for item in items:
            product_id = item.get("product_id")
            quantity = item.get("quantity")
            if product_id and quantity:
                self.logger.info("Simulating inventory deduction for product", product_id=product_id, quantity=quantity)
                # In a real scenario, this would interact with an Inventory Agent
                # For now, just log and acknowledge.
                await self.send_message(
                    recipient_agent="inventory_agent",
                    message_type=MessageType.INVENTORY_UPDATE_REQUEST,
                    payload={"product_id": product_id, "quantity_change": -quantity, "reason": "Order placed"}
                )

    async def _handle_product_sync_request(self, message: AgentMessage):
        """Handle product sync request messages."""
        product_ids = message.payload.get("product_ids")
        channels = message.payload.get("channels")
        self.logger.info("Received PRODUCT_SYNC_REQUEST message", product_ids=product_ids, channels=channels)
        await self._sync_to_channels(product_ids, channels)

    
    async def _sync_products_periodically(self):
        """Background task to periodically sync products to channels."""
        while True:
            self.logger.info("Running periodic product sync")
            # Here, you might fetch products that need syncing based on some criteria
            # or just sync all active products.
            await self._sync_to_channels() # Sync all products to all channels
            await asyncio.sleep(3600)  # Sync every hour

    
    async def _monitor_price_changes(self):
        """Background task to monitor external price changes (e.g., from a pricing API)."""
        while True:
            self.logger.info("Monitoring for external price changes")
            # In a real system, this would involve calling an external pricing API
            # and updating product prices if changes are detected.
            # For demonstration, we'll just simulate a check.
            
            # Example: Simulate a price change for a random product
            # product_id = "some_product_id"
            # new_price = Decimal("105.00")
            # await self._update_product_price(product_id, new_price, "External market adjustment")
            
            await asyncio.sleep(1800)  # Check every 30 minutes


# Main execution block
if __name__ == "__main__":
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory()
    )
    
    # Set environment variables for testing (replace with actual values in production)
    os.environ["KAFKA_BOOTSTRAP_SERVERS"] = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    os.environ["API_PORT"] = os.getenv("API_PORT", "8001")
    os.environ["DB_HOST"] = os.getenv("DB_HOST", "localhost")
    os.environ["DB_PORT"] = os.getenv("DB_PORT", "5432")
    os.environ["DB_NAME"] = os.getenv("DB_NAME", "ecommerce")
    os.environ["DB_USER"] = os.getenv("DB_USER", "postgres")
    os.environ["DB_PASSWORD"] = os.getenv("DB_PASSWORD", "postgres")
    os.environ["DB_POOL_SIZE"] = os.getenv("DB_POOL_SIZE", "10")
    os.environ["DB_MAX_OVERFLOW"] = os.getenv("DB_MAX_OVERFLOW", "20")

    async def main():
        agent = ProductAgent(
            kafka_bootstrap_servers=os.environ["KAFKA_BOOTSTRAP_SERVERS"]
        )
        await agent.start()
        
        # Start the FastAPI server in a separate thread/process or using uvicorn.run
        import uvicorn
        config = uvicorn.Config(agent.app, host="0.0.0.0", port=int(os.environ["API_PORT"]))
        server = uvicorn.Server(config)
        
        # Run the server and agent tasks concurrently
        await asyncio.gather(
            server.serve(),
            agent.run()
        )

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Product Agent stopped by user")
    except Exception as e:
        logger.error("Product Agent encountered an error", error=str(e))

