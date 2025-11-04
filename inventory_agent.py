from contextlib import asynccontextmanager
"""
Inventory Agent - Multi-Agent E-commerce System

This agent manages inventory levels across all warehouses, tracks stock movements,
and handles reservations, and provides real-time inventory information to other agents.
"""

import asyncio
import contextlib
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

        self.reservations: Dict[str, Dict[str, Any]] = {}
        self.app = FastAPI(
            title="Inventory Agent API",
            description="Manages product inventory, stock levels, and reservations.",
            version="1.0.0",
            lifespan=self.lifespan_context
        )
        
        # Add CORS middleware to allow dashboard access
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, specify exact origins
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self.setup_routes()

    @asynccontextmanager
    async def lifespan_context(self, app: FastAPI):
        """FastAPI Lifespan Context Manager for agent startup and shutdown.
        """
        self.logger.info("Inventory Agent API starting up...")
        await self.initialize()
        yield
        self.logger.info("Inventory Agent API shutting down...")
        await self.cleanup()

    async def initialize(self):
        """Initializes the agent, database, and Kafka connections.
        """
        await super().initialize()
        try:
            # Try to get the globally initialized database manager
            self.db_manager = get_database_manager()
        except RuntimeError:
            # If not initialized globally, initialize it locally
            from shared.database import DatabaseManager, DatabaseConfig
            self.db_manager = DatabaseManager(DatabaseConfig())
            await self.db_manager.initialize()
            self.logger.warning("Database manager was not initialized globally, initialized locally.")
            
        self.inventory_repo = InventoryRepository(self.db_manager)
        self.stock_movement_repo = StockMovementRepository(self.db_manager)
        self.logger.info("Inventory Agent initialized.")

    async def cleanup(self):
        """Cleans up resources upon agent shutdown.
        """
        await super().cleanup()
        await self.db_manager.disconnect()
        self.logger.info("Inventory Agent cleaned up.")

    async def process_message(self, message: AgentMessage):
        """Process incoming messages from other agents.

        Args:
            message (AgentMessage): The message to process.
        """
        self.logger.info(f"Received message: {message.message_type} from {message.sender_agent_id}")
        
        action = message.data.get("action")
        data = message.data.get("data")
        
        if not action or not data:
            self.logger.warning("Invalid message format received", message=message.dict())
            return

        try:
            result = await self.handle_action(action, data)
            self.logger.info(f"Action {action} completed successfully", result=result)
        except Exception as e:
            self.logger.error(f"Error handling action {action}", error=str(e), data=data)

    async def handle_action(self, action: str, data: Dict[str, Any]):
        """Handle a specific action requested by another agent.

        Args:
            action (str): The action to perform.
            data (Dict[str, Any]): The data associated with the action.

        Returns:
            Any: The result of the action.

        Raises:
            ValueError: If the action is unknown.
        """
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
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        The core business logic loop for the Inventory Agent.
        This is a placeholder implementation to satisfy the abstract method requirement.
        """
        self.logger.info("Running Inventory Agent core business logic loop (placeholder)")
        # In a real system, this would contain the main message processing loop
        # for non-API-triggered events (e.g., Kafka messages).
        await asyncio.sleep(1)
        return {"status": "ok", "message": "Business logic loop executed."}
    
    async def _get_inventory(
        self,
        product_id: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 100
    ) -> Dict[str, Any]:
        """Get inventory records with optional filtering and pagination.
        
        Args:
            product_id: Optional product ID filter
            warehouse_id: Optional warehouse ID filter
            page: Page number (1-indexed)
            per_page: Items per page
            
        Returns:
            Dictionary containing inventory items and pagination info
        """
        try:
            async with self.db_manager.get_session() as session:
                # Build query
                from shared.models import InventoryDB
                query = select(InventoryDB)
                
                # Apply filters
                if product_id:
                    query = query.where(InventoryDB.product_id == product_id)
                if warehouse_id:
                    query = query.where(InventoryDB.warehouse_id == warehouse_id)
                
                # Get total count
                from sqlalchemy import func
                count_query = select(func.count()).select_from(query.subquery())
                total_result = await session.execute(count_query)
                total = total_result.scalar() or 0
                
                # Apply pagination
                offset = (page - 1) * per_page
                query = query.limit(per_page).offset(offset)
                
                # Execute query
                result = await session.execute(query)
                items = result.scalars().all()
                
                return {
                    "items": [{
                        "id": item.id,
                        "product_id": item.product_id,
                        "warehouse_id": item.warehouse_id,
                        "quantity": item.quantity,
                        "reserved_quantity": item.reserved_quantity,
                        "available_quantity": item.quantity - item.reserved_quantity,
                        "reorder_point": item.reorder_point,
                        "max_stock": item.max_stock,
                        "last_updated": item.last_updated.isoformat() if item.last_updated else None
                    } for item in items],
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": (total + per_page - 1) // per_page
                }
        except Exception as e:
            self.logger.error("Error getting inventory", error=str(e))
            raise
    
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
                    message="Product availability checked",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to check product availability", error=str(e), product_id=product_id)
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/inventory/reserve", response_model=APIResponse)
        async def reserve_stock_api(request: StockReservationRequest):
            """Reserve stock for a product.

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

        @self.app.post("/inventory/release-reservation/{reservation_id}", response_model=APIResponse)
        async def release_reservation_api(reservation_id: str):
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

        @self.app.put("/api/inventory", response_model=APIResponse)
        async def update_inventory_bulk(updates: List[InventoryUpdateRequest]):
            """Bulk update inventory items.

            Args:
                updates (List[InventoryUpdateRequest]): List of inventory updates.

            Returns:
                APIResponse: A response containing the updated inventory items.
            """
            try:
                updated_items = []
                for update in updates:
                    if hasattr(update, 'product_id') and hasattr(update, 'warehouse_id'):
                        updated_item = await self._update_inventory_item(
                            update.product_id, 
                            update.warehouse_id, 
                            update
                        )
                        if updated_item:
                            updated_items.append(updated_item)
                
                return APIResponse(
                    success=True,
                    message=f"Updated {len(updated_items)} inventory items",
                    data={"updated_items": updated_items}
                )
            except Exception as e:
                self.logger.error("Failed to bulk update inventory", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/inventory/adjust", response_model=APIResponse)
        async def adjust_inventory(request: StockMovementRequest):
            """Adjust inventory quantity (add or subtract stock).

            Args:
                request (StockMovementRequest): The request containing adjustment details.

            Returns:
                APIResponse: A response containing the movement ID and updated quantity.
            """
            try:
                # Record the stock movement
                movement_id = await self._record_stock_movement(request)
                
                # Get updated inventory
                async with self.db_manager.get_session() as session:
                    from sqlalchemy import select
                    from shared.models import InventoryDB
                    
                    result = await session.execute(
                        select(InventoryDB).where(
                            InventoryDB.product_id == request.product_id,
                            InventoryDB.warehouse_id == request.warehouse_id
                        )
                    )
                    inventory = result.scalar_one_or_none()
                    
                    return APIResponse(
                        success=True,
                        message="Inventory adjusted successfully",
                        data={
                            "movement_id": movement_id,
                            "product_id": request.product_id,
                            "warehouse_id": request.warehouse_id,
                            "new_quantity": inventory.quantity if inventory else 0,
                            "movement_type": request.movement_type,
                            "quantity_changed": request.quantity
                        }
                    )
            except ValueError as e:
                self.logger.warning("Inventory adjustment failed", error=str(e), request=request.dict())
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                self.logger.error("Failed to adjust inventory", error=str(e), request=request.dict())
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
                        query.order_by(StockMovementDB.created_at.desc()).limit(100)
                    )
                    recent_movements = [
                        {
                            "movement_id": str(m.movement_id),
                            "product_id": str(m.product_id),
                            "warehouse_id": str(m.warehouse_id),
                            "quantity_change": m.quantity_change,
                            "movement_type": m.movement_type,
                            "reference_id": m.reference_id,
                            "created_at": m.created_at.isoformat()
                        }
                        for m in recent_result.scalars().all()
                    ]
                    
                    return APIResponse(
                        success=True,
                        message="Stock movement analytics retrieved successfully",
                        data={
                            "from_date": from_date.isoformat(),
                            "total_movements": total_movements,
                            "movements_by_type": movements_by_type,
                            "recent_movements": recent_movements
                        }
                    )
            except Exception as e:
                self.logger.error("Failed to get stock movement analytics", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))


# --- Agent Instantiation and Uvicorn Startup ---

# Create an instance of the agent
agent = InventoryAgent()

# Expose the FastAPI app for Uvicorn
app = agent.app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", "8002"))
    uvicorn.run(app, host="0.0.0.0", port=port)

