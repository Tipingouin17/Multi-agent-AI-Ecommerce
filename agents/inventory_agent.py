"""
Inventory Agent - Multi-Agent E-commerce System

This agent manages inventory levels across all warehouses, tracks stock movements,
handles reservations, and provides real-time inventory information to other agents.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
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

from shared.base_agent_v2 import BaseAgentV2, MessageType, AgentMessage
from shared.models import (
    Inventory, InventoryBase, APIResponse, PaginatedResponse, StockMovementDB
)
from shared.database import DatabaseManager, BaseRepository, get_database_manager
from sqlalchemy import select

logger = structlog.get_logger(__name__)


class InventoryUpdateRequest(BaseModel):
    """Request model for updating inventory.

    Attributes:
        quantity (Optional[int]): The new quantity of the product in stock.
        reserved_quantity (Optional[int]): The new reserved quantity of the product.
        reorder_point (Optional[int]): The new reorder point for the product.
        max_stock (Optional[int]): The new maximum stock level for the product.
    """
    quantity: Optional[int] = None
    reserved_quantity: Optional[int] = None
    reorder_point: Optional[int] = None
    max_stock: Optional[int] = None


class StockMovementRequest(BaseModel):
    """Request model for stock movements.

    Attributes:
        product_id (str): The ID of the product.
        warehouse_id (str): The ID of the warehouse.
        quantity_change (int): The change in quantity (positive for inbound, negative for outbound).
        movement_type (str): The type of movement (e.g., "inbound", "outbound", "transfer", "adjustment").
        reference_id (Optional[str]): An optional reference ID (e.g., order ID, transfer ID).
        notes (Optional[str]): Optional notes for the movement.
    """
    product_id: str
    warehouse_id: str
    quantity_change: int  # Positive for inbound, negative for outbound
    movement_type: str  # "inbound", "outbound", "transfer", "adjustment"
    reference_id: Optional[str] = None  # Order ID, transfer ID, etc.
    notes: Optional[str] = None


class StockReservationRequest(BaseModel):
    """Request model for stock reservations.

    Attributes:
        product_id (str): The ID of the product to reserve.
        warehouse_id (str): The ID of the warehouse where the product is located.
        quantity (int): The quantity to reserve.
        order_id (str): The ID of the order associated with the reservation.
        expires_at (Optional[datetime]): The timestamp when the reservation expires.
    """
    product_id: str
    warehouse_id: str
    quantity: int
    order_id: str
    expires_at: Optional[datetime] = None


class LowStockAlert(BaseModel):
    """Model for low stock alerts.

    Attributes:
        product_id (str): The ID of the product that is low in stock.
        warehouse_id (str): The ID of the warehouse where the product is low.
        current_quantity (int): The current quantity of the product.
        reorder_point (int): The reorder point for the product.
        suggested_reorder_quantity (int): The suggested quantity to reorder.
        alert_level (str): The severity of the alert (e.g., "warning", "critical").
    """
    product_id: str
    warehouse_id: str
    current_quantity: int
    reorder_point: int
    suggested_reorder_quantity: int
    alert_level: str  # "warning", "critical"


class InventoryRepository(BaseRepository):
    """Repository for inventory data operations.

    Handles CRUD operations and specific queries for Inventory items.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """Initializes the InventoryRepository with a database manager.

        Args:
            db_manager (DatabaseManager): The database manager instance.
        """
        from shared.models import InventoryDB
        super().__init__(db_manager, InventoryDB)
        
        # FastAPI app for REST API
        self.app = FastAPI(title="Inventory Agent API")
        
        # Add CORS middleware for dashboard integration
        add_cors_middleware(self.app)
    
    async def find_by_product(self, product_id: str) -> List[Inventory]:
        """Find inventory records by product ID.

        Args:
            product_id (str): The ID of the product.

        Returns:
            List[Inventory]: A list of Inventory Pydantic models.
        """
        async with self.db_manager.get_session() as session:
            records = await super().find_by_criteria(session, product_id=product_id)
        return [self._to_pydantic(record) for record in records]
    
    async def find_by_warehouse(self, warehouse_id: str) -> List[Inventory]:
        """Find inventory records by warehouse ID.

        Args:
            warehouse_id (str): The ID of the warehouse.

        Returns:
            List[Inventory]: A list of Inventory Pydantic models.
        """
        async with self.db_manager.get_session() as session:
            records = await super().find_by_criteria(session, warehouse_id=warehouse_id)
        return [self._to_pydantic(record) for record in records]
    
    async def find_by_product_and_warehouse(self, product_id: str, warehouse_id: str) -> Optional[Inventory]:
        """Find inventory record by product and warehouse.

        Args:
            product_id (str): The ID of the product.
            warehouse_id (str): The ID of the warehouse.

        Returns:
            Optional[Inventory]: The Inventory Pydantic model if found, else None.
        """
        async with self.db_manager.get_session() as session:
            records = await super().find_by_criteria(session, product_id=product_id, warehouse_id=warehouse_id)
        return self._to_pydantic(records[0]) if records else None
    
    async def find_low_stock_items(self) -> List[Inventory]:
        """Find items with stock below reorder point.

        Returns:
            List[Inventory]: A list of Inventory Pydantic models for low stock items.
        """
        async with self.db_manager.get_session() as session:
            from shared.models import InventoryDB
            result = await session.execute(
                select(InventoryDB).filter(
                    InventoryDB.quantity <= InventoryDB.reorder_point
                )
            )
            records = result.scalars().all()
            return [self._to_pydantic(record) for record in records]
    
    async def get_total_available_quantity(self, product_id: str) -> int:
        """Get total available quantity across all warehouses for a given product.

        Args:
            product_id (str): The ID of the product.

        Returns:
            int: The total available quantity.
        """
        async with self.db_manager.get_session() as session:
            records = await super().find_by_criteria(session, product_id=product_id)
        return sum(record.quantity - record.reserved_quantity for record in records)
    
    def _to_pydantic(self, db_record) -> Inventory:
        """Convert database record to Pydantic model.

        Args:
            db_record: The SQLAlchemy database record.

        Returns:
            Inventory: The converted Inventory Pydantic model.
        """
        return Inventory(
            id=db_record.id,
            product_id=db_record.product_id,
            warehouse_id=db_record.warehouse_id,
            quantity=db_record.quantity,
            reserved_quantity=db_record.reserved_quantity,
            reorder_point=db_record.reorder_point,
            max_stock=db_record.max_stock,
            last_updated=db_record.last_updated
        )


class StockMovementRepository(BaseRepository):
    """Repository for stock movement tracking.

    Handles CRUD operations for StockMovement items.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """Initializes the StockMovementRepository with a database manager.

        Args:
            db_manager (DatabaseManager): The database manager instance.
        """
        super().__init__(db_manager, StockMovementDB)
    
    async def create_movement(self, movement_data: Dict[str, Any]) -> str:
        """Create a stock movement record.

        Args:
            movement_data (Dict[str, Any]): The data for the stock movement.

        Returns:
            str: The ID of the created stock movement record.

        Raises:
            Exception: If the stock movement record fails to be created.
        """
        movement_id = str(uuid4())
        movement_data["id"] = movement_id
        movement_data["timestamp"] = datetime.utcnow()
        
        try:
            movement = await self.create(movement_data)
            logger.info("Stock movement recorded in DB", movement_id=movement.id, **movement_data)
            return movement.id
        except Exception as e:
            logger.error("Failed to record stock movement", error=str(e), **movement_data)
            raise


class InventoryAgent(BaseAgentV2):
    """
    Inventory Agent handles all inventory-related operations including:
    - Stock level monitoring
    - Inventory reservations
    - Stock movements tracking
    - Low stock alerts
    - Reorder recommendations
    """
    
    def __init__(self, **kwargs):
        """Initializes the InventoryAgent.

        Args:
            **kwargs: Arbitrary keyword arguments passed to the BaseAgent constructor.
        """
        super().__init__(agent_id="inventory_agent")
        self.repository: Optional[InventoryRepository] = None
        self.movement_repository: Optional[StockMovementRepository] = None
        self.app = FastAPI(title="Inventory Agent API", version="1.0.0")
        
        # Add CORS middleware for dashboard integration
        add_cors_middleware(self.app)
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, specify exact origins
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.setup_routes()
        
        # In-memory reservations (in production, this would be in Redis or database)
        self.reservations: Dict[str, Dict[str, Any]] = {}
        
        # Register message handlers
        self.register_handler(MessageType.ORDER_CREATED, self._handle_order_created)
        self.register_handler(MessageType.ORDER_UPDATED, self._handle_order_updated)
        self.register_handler(MessageType.WAREHOUSE_SELECTED, self._handle_warehouse_selected)
    
    async def initialize(self):
        """Initialize the Inventory Agent with robust error handling.

        This includes initializing database repositories, creating database tables,
        and starting background tasks for monitoring and cleanup.
        """
        await super().initialize()
        
        self.logger.info("Initializing Inventory Agent")
        
        # Initialize database repositories with retry logic
        max_retries = 5
        for attempt in range(1, max_retries + 1):
            try:
                # Try to get global database manager
                try:
                    from shared.database_manager import get_database_manager
                    db_manager = get_database_manager()
                    self.logger.info("Using global database manager")
                except (RuntimeError, ImportError):
                    # Create enhanced database manager with retry logic
                    from shared.models import DatabaseConfig
                    from shared.database_manager import EnhancedDatabaseManager
                    db_config = DatabaseConfig()
                    db_manager = EnhancedDatabaseManager(db_config)
                    await db_manager.initialize(max_retries=5)
                    self.logger.info("Created new enhanced database manager")
                
                # Tables are created by migrations, not by agents
                # Initialize repositories
                self.repository = InventoryRepository(db_manager)
                self.movement_repository = StockMovementRepository(db_manager)
                
                self.logger.info("Database initialization successful", attempt=attempt)
                break
                
            except Exception as e:
                self.logger.warning(
                    "Database initialization failed",
                    attempt=attempt,
                    max_retries=max_retries,
                    error=str(e)
                )
                
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("Failed to initialize database after all retries")
                    raise
        
        # Start background tasks
        asyncio.create_task(self._monitor_low_stock())
        asyncio.create_task(self._cleanup_expired_reservations())
        asyncio.create_task(self._sync_inventory_levels())
        
        self.logger.info("Inventory Agent initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources used by the Inventory Agent.
        """
        self.logger.info("Cleaning up Inventory Agent")
        await super().cleanup()

    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process inventory-specific business logic based on the action in the data.

        Args:
            data (Dict[str, Any]): A dictionary containing the action and relevant data.

        Returns:
            Dict[str, Any]: The result of the business logic operation.

        Raises:
            ValueError: If an unknown action is provided.
        """
        action = data.get("action")
        
        if action == "check_availability":
            return await self._check_availability(data["product_id"], data["quantity"])
        elif action == "reserve_stock":
            return await self._reserve_stock(data["product_id"], data["warehouse_id"], data["quantity"], data["order_id"])
        elif action == "release_reservation":
            return await self._release_reservation(data["reservation_id"])
        elif action == "update_stock":
            return await self._update_stock(data["product_id"], data["warehouse_id"], data["quantity_change"])
        elif action == "get_inventory":
            return await self._get_inventory(data.get("product_id"), data.get("warehouse_id"))
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def setup_routes(self):
        """Setup FastAPI routes for the Inventory Agent API.
        """
        
        @self.app.get("/inventory", response_model=APIResponse)
        async def get_inventory(
            product_id: Optional[str] = None,
            warehouse_id: Optional[str] = None,
            page: int = 1,
            per_page: int = 20
        ):
            """Get inventory information.

            Args:
                product_id (Optional[str]): Filter by product ID.
                warehouse_id (Optional[str]): Filter by warehouse ID.
                page (int): Page number for pagination.
                per_page (int): Number of items per page.

            Returns:
                APIResponse: A response containing paginated inventory data.
            """
            try:
                result = await self._get_inventory(product_id, warehouse_id, page, per_page)
                
                return APIResponse(
                    success=True,
                    message="Inventory retrieved successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to get inventory", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/inventory/{product_id}/availability", response_model=APIResponse)
        async def check_product_availability(product_id: str, quantity: int = 1):
            """Check product availability across all warehouses.

            Args:
                product_id (str): The ID of the product.
                quantity (int): The quantity to check availability for.

            Returns:
                APIResponse: A response containing the available quantity.
            """
            try:
                result = await self._check_availability(product_id, quantity)
                
                return APIResponse(
                    success=True,
                    message="Product availability checked successfully",
                    data={"product_id": product_id, "available_quantity": result}
                )
            except Exception as e:
                self.logger.error(f"Failed to check availability for product {product_id}", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/inventory/reserve", response_model=APIResponse)
        async def reserve_stock_api(request: StockReservationRequest):
            """Reserve stock for an order.

            Args:
                request (StockReservationRequest): The request containing reservation details.

            Returns:
                APIResponse: A response containing the reservation ID.
            """
            try:
                reservation_id = await self._reserve_stock(
                    request.product_id, request.warehouse_id, request.quantity, request.order_id, request.expires_at
                )
                return APIResponse(
                    success=True,
                    message="Stock reserved successfully",
                    data={"reservation_id": reservation_id}
                )
            except ValueError as e:
                self.logger.warning("Stock reservation failed", error=str(e), request=request.dict())
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                self.logger.error("Failed to reserve stock", error=str(e), request=request.dict())
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/inventory/release/{reservation_id}", response_model=APIResponse)
        async def release_stock_api(reservation_id: str):
            """Release a stock reservation.

            Args:
                reservation_id (str): The ID of the reservation to release.

            Returns:
                APIResponse: A success message.
            """
            try:
                await self._release_reservation(reservation_id)
                return APIResponse(
                    success=True,
                    message="Stock reservation released successfully"
                )
            except ValueError as e:
                self.logger.warning("Stock reservation release failed", error=str(e), reservation_id=reservation_id)
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                self.logger.error("Failed to release stock reservation", error=str(e), reservation_id=reservation_id)
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/inventory/move", response_model=APIResponse)
        async def record_stock_movement_api(request: StockMovementRequest):
            """Record a stock movement (inbound/outbound/transfer).

            Args:
                request (StockMovementRequest): The request containing movement details.

            Returns:
                APIResponse: A response containing the movement ID.
            """
            try:
                movement_id = await self._record_stock_movement(request)
                return APIResponse(
                    success=True,
                    message="Stock movement recorded successfully",
                    data={"movement_id": movement_id}
                )
            except ValueError as e:
                self.logger.warning("Stock movement recording failed", error=str(e), request=request.dict())
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                self.logger.error("Failed to record stock movement", error=str(e), request=request.dict())
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.put("/inventory/{product_id}/{warehouse_id}", response_model=APIResponse)
        async def update_inventory_item_api(
            product_id: str,
            warehouse_id: str,
            request: InventoryUpdateRequest
        ):
            """Update an existing inventory item's details.

            Args:
                product_id (str): The ID of the product.
                warehouse_id (str): The ID of the warehouse.
                request (InventoryUpdateRequest): The request with fields to update.

            Returns:
                APIResponse: A response containing the updated inventory item.
            
            Raises:
                HTTPException: If the inventory item is not found or an error occurs.
            """
            try:
                updated_item = await self._update_inventory_item(product_id, warehouse_id, request)
                if not updated_item:
                    raise HTTPException(status_code=404, detail="Inventory item not found")
                return APIResponse(
                    success=True,
                    message="Inventory item updated successfully",
                    data=updated_item
                )
            except Exception as e:
                self.logger.error(f"Failed to update inventory item {product_id}/{warehouse_id}", error=str(e), request=request.dict())
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health", response_model=Dict[str, str])
        async def health_check():
            """Health check endpoint.

            Returns:
                Dict[str, str]: A dictionary with the status of the agent.
            """
            return {"status": "ok", "agent_id": self.agent_id}

        # =====================================================
        # ANALYTICS ENDPOINTS
        # =====================================================

        @self.app.get("/analytics/low-stock", response_model=APIResponse)
        async def get_low_stock_alerts():
            """Get products that are below reorder point.
            
            Returns:
                APIResponse: List of products with low stock levels.
            """
            try:
                async with self.db_manager.get_session() as session:
                    from sqlalchemy import select
                    from shared.models import InventoryDB
                    
                    # Query products where quantity <= reorder_point
                    result = await session.execute(
                        select(InventoryDB)
                        .where(InventoryDB.quantity <= InventoryDB.reorder_point)
                        .order_by(InventoryDB.quantity.asc())
                    )
                    low_stock_items = result.scalars().all()
                    
                    alerts = [
                        {
                            "product_id": str(item.product_id),
                            "warehouse_id": str(item.warehouse_id),
                            "current_quantity": item.quantity,
                            "reorder_point": item.reorder_point,
                            "shortage": item.reorder_point - item.quantity,
                            "last_updated": item.last_updated.isoformat() if item.last_updated else None
                        }
                        for item in low_stock_items
                    ]
                    
                    return APIResponse(
                        success=True,
                        message=f"Found {len(alerts)} low stock alerts",
                        data={"alerts": alerts, "count": len(alerts)}
                    )
            except Exception as e:
                self.logger.error("Failed to get low stock alerts", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/analytics/inventory-value", response_model=APIResponse)
        async def get_inventory_value():
            """Calculate total inventory value across all warehouses.
            
            Returns:
                APIResponse: Inventory value analytics by warehouse and product.
            """
            try:
                async with self.db_manager.get_session() as session:
                    from sqlalchemy import select, func
                    from shared.models import InventoryDB
                    
                    # Total units across all warehouses
                    total_units_result = await session.execute(
                        select(func.sum(InventoryDB.quantity))
                    )
                    total_units = total_units_result.scalar() or 0
                    
                    # Total reserved units
                    reserved_units_result = await session.execute(
                        select(func.sum(InventoryDB.reserved_quantity))
                    )
                    reserved_units = reserved_units_result.scalar() or 0
                    
                    # Available units
                    available_units = total_units - reserved_units
                    
                    # Units by warehouse
                    warehouse_result = await session.execute(
                        select(
                            InventoryDB.warehouse_id,
                            func.sum(InventoryDB.quantity),
                            func.sum(InventoryDB.reserved_quantity),
                            func.count(InventoryDB.product_id)
                        )
                        .group_by(InventoryDB.warehouse_id)
                    )
                    warehouses = [
                        {
                            "warehouse_id": str(row[0]),
                            "total_units": row[1] or 0,
                            "reserved_units": row[2] or 0,
                            "available_units": (row[1] or 0) - (row[2] or 0),
                            "unique_products": row[3]
                        }
                        for row in warehouse_result.all()
                    ]
                    
                    return APIResponse(
                        success=True,
                        message="Inventory value calculated successfully",
                        data={
                            "total_units": total_units,
                            "reserved_units": reserved_units,
                            "available_units": available_units,
                            "warehouses": warehouses,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
            except Exception as e:
                self.logger.error("Failed to calculate inventory value", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/analytics/stock-movements", response_model=APIResponse)
        async def get_stock_movement_analytics(
            days: int = 30,
            movement_type: Optional[str] = None
        ):
            """Get stock movement analytics for the specified period.
            
            Args:
                days: Number of days to analyze (default 30)
                movement_type: Filter by movement type (inbound, outbound, transfer, adjustment)
            
            Returns:
                APIResponse: Stock movement analytics.
            """
            try:
                from_date = datetime.utcnow() - timedelta(days=days)
                
                async with self.db_manager.get_session() as session:
                    from sqlalchemy import select, func
                    
                    # Build base query
                    query = select(StockMovementDB).where(
                        StockMovementDB.created_at >= from_date
                    )
                    
                    if movement_type:
                        query = query.where(StockMovementDB.movement_type == movement_type)
                    
                    # Total movements
                    total_result = await session.execute(
                        select(func.count(StockMovementDB.movement_id))
                        .where(StockMovementDB.created_at >= from_date)
                    )
                    total_movements = total_result.scalar() or 0
                    
                    # Movements by type
                    type_result = await session.execute(
                        select(
                            StockMovementDB.movement_type,
                            func.count(StockMovementDB.movement_id),
                            func.sum(StockMovementDB.quantity_change)
                        )
                        .where(StockMovementDB.created_at >= from_date)
                        .group_by(StockMovementDB.movement_type)
                    )
                    movements_by_type = {
                        row[0]: {
                            "count": row[1],
                            "total_quantity": row[2] or 0
                        }
                        for row in type_result.all()
                    }
                    
                    # Recent movements
                    recent_result = await session.execute(
                        query.order_by(StockMovementDB.created_at.desc()).limit(10)
                    )
                    recent_movements = [
                        {
                            "movement_id": str(item.movement_id),
                            "product_id": str(item.product_id),
                            "warehouse_id": str(item.warehouse_id),
                            "movement_type": item.movement_type,
                            "quantity_change": item.quantity_change,
                            "created_at": item.created_at.isoformat()
                        }
                        for item in recent_result.scalars().all()
                    ]
                    
                    return APIResponse(
                        success=True,
                        message="Stock movement analytics retrieved successfully",
                        data={
                            "period_days": days,
                            "from_date": from_date.isoformat(),
                            "total_movements": total_movements,
                            "movements_by_type": movements_by_type,
                            "recent_movements": recent_movements,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
            except Exception as e:
                self.logger.error("Failed to get stock movement analytics", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/", response_model=APIResponse)
        async def root():
            """Root endpoint providing basic agent information.

            Returns:
                APIResponse: A welcome message and agent details.
            """
            return APIResponse(
                success=True,
                message="Welcome to the Inventory Agent API",
                data={
                    "agent_id": self.agent_id,
                    "agent_type": self.agent_type,
                    "version": self.app.version
                }
            )

    async def _check_availability(self, product_id: str, quantity: int) -> int:
        """Check total available quantity for a product across all warehouses.

        Args:
            product_id (str): The ID of the product.
            quantity (int): The quantity to check availability for.

        Returns:
            int: The total available quantity.

        Raises:
            Exception: If an error occurs during availability check.
        """
        try:
            total_available = await self.repository.get_total_available_quantity(product_id)
            self.logger.info("Product availability checked", product_id=product_id, requested_quantity=quantity, total_available=total_available)
            return total_available
        except Exception as e:
            self.logger.error("Error checking product availability", product_id=product_id, error=str(e))
            raise

    async def _reserve_stock(self, product_id: str, warehouse_id: str, quantity: int, order_id: str, expires_at: Optional[datetime] = None) -> str:
        """Reserve stock for a given product in a specific warehouse.

        Args:
            product_id (str): The ID of the product.
            warehouse_id (str): The ID of the warehouse.
            quantity (int): The quantity to reserve.
            order_id (str): The ID of the order making the reservation.
            expires_at (Optional[datetime]): The expiration time for the reservation.

        Returns:
            str: The ID of the created reservation.

        Raises:
            ValueError: If there is not enough stock available.
            Exception: If an error occurs during stock reservation.
        """
        try:
            inventory_item = await self.repository.find_by_product_and_warehouse(product_id, warehouse_id)
            if not inventory_item or inventory_item.quantity - inventory_item.reserved_quantity < quantity:
                raise ValueError("Not enough stock available for reservation")

            reservation_id = str(uuid4())
            self.reservations[reservation_id] = {
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "quantity": quantity,
                "order_id": order_id,
                "expires_at": expires_at or (datetime.utcnow() + timedelta(minutes=30)),
                "created_at": datetime.utcnow()
            }
            
            # Update reserved quantity in DB
            await self.repository.update(
                inventory_item.id,
                {"reserved_quantity": inventory_item.reserved_quantity + quantity}
            )
            self.logger.info("Stock reserved", reservation_id=reservation_id, product_id=product_id, quantity=quantity, order_id=order_id)
            return reservation_id
        except Exception as e:
            self.logger.error("Error reserving stock", product_id=product_id, warehouse_id=warehouse_id, quantity=quantity, order_id=order_id, error=str(e))
            raise

    async def _release_reservation(self, reservation_id: str):
        """Release a previously made stock reservation.

        Args:
            reservation_id (str): The ID of the reservation to release.

        Raises:
            ValueError: If the reservation is not found or already released.
            Exception: If an error occurs during reservation release.
        """
        try:
            reservation = self.reservations.pop(reservation_id, None)
            if not reservation:
                raise ValueError("Reservation not found or already released")

            product_id = reservation["product_id"]
            warehouse_id = reservation["warehouse_id"]
            quantity = reservation["quantity"]
            
            inventory_item = await self.repository.find_by_product_and_warehouse(product_id, warehouse_id)
            if inventory_item:
                await self.repository.update(
                    inventory_item.id,
                    {"reserved_quantity": inventory_item.reserved_quantity - quantity}
                )
            self.logger.info("Stock reservation released", reservation_id=reservation_id, product_id=product_id, quantity=quantity)
        except Exception as e:
            self.logger.error("Error releasing reservation", reservation_id=reservation_id, error=str(e))
            raise

    async def _update_stock(self, product_id: str, warehouse_id: str, quantity_change: int):
        """Update the physical stock quantity for an item.

        Args:
            product_id (str): The ID of the product.
            warehouse_id (str): The ID of the warehouse.
            quantity_change (int): The amount to change the stock by (positive for increase, negative for decrease).

        Raises:
            ValueError: If the new stock quantity would be negative.
            Exception: If an error occurs during stock update.
        """
        try:
            inventory_item = await self.repository.find_by_product_and_warehouse(product_id, warehouse_id)
            if not inventory_item:
                # Create new inventory item if it doesn't exist
                new_inventory = InventoryBase(
                    product_id=product_id,
                    warehouse_id=warehouse_id,
                    quantity=quantity_change if quantity_change > 0 else 0,
                    reserved_quantity=0,
                    reorder_point=int(os.getenv("DEFAULT_REORDER_POINT", 10)),
                    max_stock=int(os.getenv("DEFAULT_MAX_STOCK", 100))
                )
                await self.repository.create(new_inventory.dict())
                self.logger.info("New inventory item created", product_id=product_id, warehouse_id=warehouse_id, quantity=quantity_change)
                return

            new_quantity = inventory_item.quantity + quantity_change
            if new_quantity < 0:
                raise ValueError("Attempted to set negative stock quantity")

            await self.repository.update(
                inventory_item.id,
                {"quantity": new_quantity}
            )
            self.logger.info("Stock updated", product_id=product_id, warehouse_id=warehouse_id, quantity_change=quantity_change, new_quantity=new_quantity)
        except Exception as e:
            self.logger.error("Error updating stock", product_id=product_id, warehouse_id=warehouse_id, quantity_change=quantity_change, error=str(e))
            raise

    async def _record_stock_movement(self, request: StockMovementRequest) -> str:
        """Record a stock movement and update inventory.

        Args:
            request (StockMovementRequest): The request containing details of the stock movement.

        Returns:
            str: The ID of the recorded stock movement.

        Raises:
            Exception: If an error occurs during recording or updating stock.
        """
        try:
            movement_id = await self.movement_repository.create_movement(request.dict())
            await self._update_stock(request.product_id, request.warehouse_id, request.quantity_change)
            self.logger.info("Stock movement and inventory updated", movement_id=movement_id, product_id=request.product_id, quantity_change=request.quantity_change)
            return movement_id
        except Exception as e:
            self.logger.error("Error recording stock movement", request=request.dict(), error=str(e))
            raise

    async def _get_inventory(self, product_id: Optional[str] = None, warehouse_id: Optional[str] = None, page: int = 1, per_page: int = 20) -> PaginatedResponse:
        """Retrieve inventory information, optionally filtered by product_id or warehouse_id.

        Args:
            product_id (Optional[str]): The ID of the product to filter by.
            warehouse_id (Optional[str]): The ID of the warehouse to filter by.
            page (int): The page number for pagination.
            per_page (int): The number of items per page for pagination.

        Returns:
            PaginatedResponse: A paginated response containing inventory items.

        Raises:
            Exception: If an error occurs during inventory retrieval.
        """
        try:
            filters = {}
            if product_id: filters["product_id"] = product_id
            if warehouse_id: filters["warehouse_id"] = warehouse_id

            total_items = await self.repository.count(**filters)
            items_db = await self.repository.get_all(skip=(page - 1) * per_page, limit=per_page, **filters)
            items = [self.repository._to_pydantic(item) for item in items_db]
            
            return PaginatedResponse(
                items=items,
                total=total_items,
                page=page,
                per_page=per_page
            )
        except Exception as e:
            self.logger.error("Error retrieving inventory", product_id=product_id, warehouse_id=warehouse_id, error=str(e))
            raise

    async def _update_inventory_item(self, product_id: str, warehouse_id: str, request: InventoryUpdateRequest) -> Optional[Inventory]:
        """Update specific fields of an inventory item.

        Args:
            product_id (str): The ID of the product.
            warehouse_id (str): The ID of the warehouse.
            request (InventoryUpdateRequest): The request containing the fields to update.

        Returns:
            Optional[Inventory]: The updated Inventory Pydantic model if found, else None.

        Raises:
            Exception: If an error occurs during the update.
        """
        try:
            inventory_item = await self.repository.find_by_product_and_warehouse(product_id, warehouse_id)
            if not inventory_item:
                return None
            
            update_data = request.dict(exclude_unset=True)
            updated_item_db = await self.repository.update(inventory_item.id, update_data)
            self.logger.info("Inventory item updated", product_id=product_id, warehouse_id=warehouse_id, update_data=update_data)
            return self.repository._to_pydantic(updated_item_db)
        except Exception as e:
            self.logger.error("Error updating inventory item", product_id=product_id, warehouse_id=warehouse_id, request=request.dict(), error=str(e))
            raise

    async def _monitor_low_stock(self):
        """Periodically check for low stock items and send alerts.
        This runs as a background task.
        """
        while True:
            try:
                low_stock_items = await self.repository.find_low_stock_items()
                for item in low_stock_items:
                    suggested_reorder_quantity = item.max_stock - item.quantity
                    alert = LowStockAlert(
                        product_id=item.product_id,
                        warehouse_id=item.warehouse_id,
                        current_quantity=item.quantity,
                        reorder_point=item.reorder_point,
                        suggested_reorder_quantity=suggested_reorder_quantity,
                        alert_level="critical" if item.quantity <= item.reorder_point / 2 else "warning"
                    )
                    self.logger.warning("Low stock alert", alert=alert.dict())
                    await self.send_message("warehouse_agent", MessageType.LOW_STOCK_ALERT, alert.dict())
                    await self.send_message("backoffice_agent", MessageType.REORDER_RECOMMENDATION, {"product_id": item.product_id, "warehouse_id": item.warehouse_id, "quantity": suggested_reorder_quantity})
            except Exception as e:
                self.logger.error("Error monitoring low stock", error=str(e))
            await asyncio.sleep(int(os.getenv("LOW_STOCK_MONITOR_INTERVAL", 300))) # Check every 5 minutes

    async def _cleanup_expired_reservations(self):
        """Periodically clean up expired stock reservations.
        This runs as a background task.
        """
        while True:
            try:
                now = datetime.utcnow()
                expired_reservation_ids = [
                    res_id for res_id, res_data in self.reservations.items()
                    if res_data["expires_at"] < now
                ]
                for res_id in expired_reservation_ids:
                    self.logger.info("Cleaning up expired reservation", reservation_id=res_id)
                    await self._release_reservation(res_id)
            except Exception as e:
                self.logger.error("Error cleaning up expired reservations", error=str(e))
            await asyncio.sleep(int(os.getenv("RESERVATION_CLEANUP_INTERVAL", 600))) # Check every 10 minutes

    async def _sync_inventory_levels(self):
        """Simulates periodic synchronization of inventory levels with an external system.
        This runs as a background task.
        """
        while True:
            try:
                self.logger.info("Simulating inventory synchronization...")
                # In a real scenario, this would involve calling an external API or reading from a data source
                # For demonstration, we'll just log a message
                self.logger.info("Inventory synchronization complete.")
            except Exception as e:
                self.logger.error("Error during inventory synchronization", error=str(e))
            await asyncio.sleep(int(os.getenv("INVENTORY_SYNC_INTERVAL", 3600))) # Sync every hour

    async def _handle_order_created(self, message: AgentMessage):
        """Handle ORDER_CREATED message to reserve stock.

        Args:
            message (AgentMessage): The incoming ORDER_CREATED message.
        """
        self.logger.info("Handling ORDER_CREATED message", payload=message.payload)
        order_id = message.payload["order_id"]
        product_id = message.payload["product_id"]
        quantity = message.payload["quantity"]
        # In a real scenario, warehouse selection would be more complex
        warehouse_id = os.getenv("DEFAULT_WAREHOUSE_ID", "warehouse_1") # Use environment variable for default warehouse

        try:
            reservation_id = await self._reserve_stock(product_id, warehouse_id, quantity, order_id)
            await self.send_message(
                message.sender, 
                MessageType.INVENTORY_RESERVE_RESPONSE, 
                {"order_id": order_id, "product_id": product_id, "quantity": quantity, "reservation_id": reservation_id, "success": True}
            )
        except Exception as e:
            self.logger.error("Failed to reserve stock for order", order_id=order_id, product_id=product_id, quantity=quantity, error=str(e))
            await self.send_message(
                message.sender, 
                MessageType.INVENTORY_RESERVE_RESPONSE, 
                {"order_id": order_id, "product_id": product_id, "quantity": quantity, "success": False, "error": str(e)}
            )

    async def _handle_order_updated(self, message: AgentMessage):
        """Handle ORDER_UPDATED message (e.g., for reservation changes or cancellations).

        Args:
            message (AgentMessage): The incoming ORDER_UPDATED message.
        """
        self.logger.info("Handling ORDER_UPDATED message", payload=message.payload)
        order_id = message.payload["order_id"]
        status = message.payload.get("status")
        # Example: if order is cancelled, release reservation
        if status == "cancelled":
            # Find reservation associated with this order_id and release it
            for res_id, res_data in list(self.reservations.items()): # Use list to allow modification during iteration
                if res_data["order_id"] == order_id:
                    try:
                        await self._release_reservation(res_id)
                        self.logger.info("Released reservation for cancelled order", order_id=order_id, reservation_id=res_id)
                    except Exception as e:
                        self.logger.error("Error releasing reservation for cancelled order", order_id=order_id, reservation_id=res_id, error=str(e))

    async def _handle_warehouse_selected(self, message: AgentMessage):
        """Handle WAREHOUSE_SELECTED message to confirm stock or transfer.

        Args:
            message (AgentMessage): The incoming WAREHOUSE_SELECTED message.
        """
        self.logger.info("Handling WAREHOUSE_SELECTED message", payload=message.payload)
        product_id = message.payload["product_id"]
        warehouse_id = message.payload["warehouse_id"]
        quantity = message.payload["quantity"]
        order_id = message.payload["order_id"]

        # In a real system, this might trigger a stock transfer or final allocation
        self.logger.info("Warehouse selected and stock confirmed", product_id=product_id, warehouse_id=warehouse_id, quantity=quantity, order_id=order_id)
        # Acknowledge the warehouse selection
        await self.send_message(
            message.sender,
            MessageType.INFO,
            {"message": "Stock confirmed for selected warehouse", "order_id": order_id, "product_id": product_id, "warehouse_id": warehouse_id}
        )

    async def process_message(self, message: AgentMessage):
        """Process incoming agent messages.

        Args:
            message (AgentMessage): The incoming message to process.
        """
        self.logger.info("Processing message", sender=message.sender, type=message.message_type.value, payload=message.payload)
        handler = self.message_handlers.get(message.message_type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                self.logger.error("Error handling message", message_type=message.message_type.value, error=str(e), payload=message.payload)
        else:
            self.logger.warning("No handler for message type", message_type=message.message_type.value)


if __name__ == "__main__":
    import uvicorn
    
    # Setup logging
    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    
    # Initialize agent
    agent = InventoryAgent()
    
    # Initialize agent before starting server
    async def startup():
        await agent.initialize()
    
    asyncio.run(startup())
    
    port = int(os.getenv("INVENTORY_AGENT_PORT", 8002))
    logger.info(f"Starting Inventory Agent on port {port}")
    uvicorn.run(agent.app, host="0.0.0.0", port=port)

