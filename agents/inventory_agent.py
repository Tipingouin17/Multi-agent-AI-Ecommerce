"""
Inventory Agent - Multi-Agent E-commerce System

This agent manages inventory levels across all warehouses, tracks stock movements,
handles reservations, and provides real-time inventory information to other agents.
"""

import asyncio
from datetime import datetime, timedelta
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
    logger.info(f"Added {project_root} to Python path")

# Now try the import
try:
    from shared.base_agent import BaseAgent, MessageType, AgentMessage
    logger.info("Successfully imported shared.base_agent")
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.info(f"Current sys.path: {sys.path}")
    
    # List files in the shared directory to verify it exists
    shared_dir = os.path.join(project_root, "shared")
    if os.path.exists(shared_dir):
        logger.info(f"Contents of {shared_dir}:")
        for item in os.listdir(shared_dir):
            logger.info(f"  - {item}")
    else:
        logger.info(f"Directory not found: {shared_dir}")

from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.models import (
    Inventory, InventoryBase, APIResponse, PaginatedResponse
)
from shared.database import DatabaseManager, BaseRepository, get_database_manager


logger = structlog.get_logger(__name__)


class InventoryUpdateRequest(BaseModel):
    """Request model for updating inventory."""
    quantity: Optional[int] = None
    reserved_quantity: Optional[int] = None
    reorder_point: Optional[int] = None
    max_stock: Optional[int] = None


class StockMovementRequest(BaseModel):
    """Request model for stock movements."""
    product_id: str
    warehouse_id: str
    quantity_change: int  # Positive for inbound, negative for outbound
    movement_type: str  # "inbound", "outbound", "transfer", "adjustment"
    reference_id: Optional[str] = None  # Order ID, transfer ID, etc.
    notes: Optional[str] = None


class StockReservationRequest(BaseModel):
    """Request model for stock reservations."""
    product_id: str
    warehouse_id: str
    quantity: int
    order_id: str
    expires_at: Optional[datetime] = None


class LowStockAlert(BaseModel):
    """Model for low stock alerts."""
    product_id: str
    warehouse_id: str
    current_quantity: int
    reorder_point: int
    suggested_reorder_quantity: int
    alert_level: str  # "warning", "critical"


class InventoryRepository(BaseRepository):
    """Repository for inventory data operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        from shared.models import InventoryDB
        super().__init__(db_manager, InventoryDB)
    
    async def find_by_product(self, product_id: str) -> List[Inventory]:
        """Find inventory records by product ID."""
        records = await self.find_by_criteria(product_id=product_id)
        return [self._to_pydantic(record) for record in records]
    
    async def find_by_warehouse(self, warehouse_id: str) -> List[Inventory]:
        """Find inventory records by warehouse ID."""
        records = await self.find_by_criteria(warehouse_id=warehouse_id)
        return [self._to_pydantic(record) for record in records]
    
    async def find_by_product_and_warehouse(self, product_id: str, warehouse_id: str) -> Optional[Inventory]:
        """Find inventory record by product and warehouse."""
        records = await self.find_by_criteria(product_id=product_id, warehouse_id=warehouse_id)
        return self._to_pydantic(records[0]) if records else None
    
    async def find_low_stock_items(self) -> List[Inventory]:
        """Find items with stock below reorder point."""
        async with self.db_manager.get_async_session() as session:
            from shared.models import InventoryDB
            
            result = await session.execute(
                session.query(InventoryDB).filter(
                    InventoryDB.quantity <= InventoryDB.reorder_point
                )
            )
            records = result.scalars().all()
            return [self._to_pydantic(record) for record in records]
    
    async def get_total_available_quantity(self, product_id: str) -> int:
        """Get total available quantity across all warehouses."""
        records = await self.find_by_product(product_id)
        return sum(record.quantity - record.reserved_quantity for record in records)
    
    def _to_pydantic(self, db_record) -> Inventory:
        """Convert database record to Pydantic model."""
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
    """Repository for stock movement tracking."""
    
    def __init__(self, db_manager: DatabaseManager):
        # We'll create a simple stock movement table
        super().__init__(db_manager, None)  # Will be implemented with raw SQL for now
    
    async def create_movement(self, movement_data: Dict[str, Any]) -> str:
        """Create a stock movement record."""
        movement_id = str(uuid4())
        movement_data["id"] = movement_id
        movement_data["timestamp"] = datetime.utcnow()
        
        # For now, we'll just log the movement
        # In production, this would be stored in a dedicated table
        logger.info("Stock movement recorded", **movement_data)
        
        return movement_id


class InventoryAgent(BaseAgent):
    """
    Inventory Agent handles all inventory-related operations including:
    - Stock level monitoring
    - Inventory reservations
    - Stock movements tracking
    - Low stock alerts
    - Reorder recommendations
    """
    
    def __init__(self, **kwargs):
        super().__init__(agent_id="inventory_agent", **kwargs)
        self.repository: Optional[InventoryRepository] = None
        self.movement_repository: Optional[StockMovementRepository] = None
        self.app = FastAPI(title="Inventory Agent API", version="1.0.0")
        self.setup_routes()
        
        # In-memory reservations (in production, this would be in Redis or database)
        self.reservations: Dict[str, Dict[str, Any]] = {}
        
        # Register message handlers
        self.register_handler(MessageType.ORDER_CREATED, self._handle_order_created)
        self.register_handler(MessageType.ORDER_UPDATED, self._handle_order_updated)
        self.register_handler(MessageType.WAREHOUSE_SELECTED, self._handle_warehouse_selected)
    
    async def initialize(self):
        """Initialize the Inventory Agent."""
        self.logger.info("Initializing Inventory Agent")
        
        # Initialize database repositories
        db_manager = get_database_manager()
        self.repository = InventoryRepository(db_manager)
        self.movement_repository = StockMovementRepository(db_manager)
        
        # Start background tasks
        asyncio.create_task(self._monitor_low_stock())
        asyncio.create_task(self._cleanup_expired_reservations())
        asyncio.create_task(self._sync_inventory_levels())
        
        self.logger.info("Inventory Agent initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up Inventory Agent")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process inventory-specific business logic."""
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
        """Setup FastAPI routes for the Inventory Agent."""
        
        @self.app.get("/inventory", response_model=APIResponse)
        async def get_inventory(
            product_id: Optional[str] = None,
            warehouse_id: Optional[str] = None,
            page: int = 1,
            per_page: int = 20
        ):
            """Get inventory information."""
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
            """Check product availability across all warehouses."""
            try:
                result = await self._check_availability(product_id, quantity)
                
                return APIResponse(
                    success=True,
                    message="Availability checked successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to check availability", error=str(e), product_id=product_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/inventory/reserve", response_model=APIResponse)
        async def reserve_stock(request: StockReservationRequest):
            """Reserve stock for an order."""
            try:
                result = await self._reserve_stock(
                    request.product_id,
                    request.warehouse_id,
                    request.quantity,
                    request.order_id,
                    request.expires_at
                )
                
                return APIResponse(
                    success=True,
                    message="Stock reserved successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to reserve stock", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/inventory/reservations/{reservation_id}", response_model=APIResponse)
        async def release_reservation(reservation_id: str):
            """Release a stock reservation."""
            try:
                result = await self._release_reservation(reservation_id)
                
                return APIResponse(
                    success=True,
                    message="Reservation released successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to release reservation", error=str(e), reservation_id=reservation_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/inventory/movements", response_model=APIResponse)
        async def record_stock_movement(request: StockMovementRequest):
            """Record a stock movement."""
            try:
                result = await self._record_stock_movement(request.dict())
                
                return APIResponse(
                    success=True,
                    message="Stock movement recorded successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to record stock movement", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/inventory/alerts/low-stock", response_model=APIResponse)
        async def get_low_stock_alerts():
            """Get low stock alerts."""
            try:
                result = await self._get_low_stock_alerts()
                
                return APIResponse(
                    success=True,
                    message="Low stock alerts retrieved successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to get low stock alerts", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.put("/inventory/{product_id}/{warehouse_id}", response_model=APIResponse)
        async def update_inventory(product_id: str, warehouse_id: str, request: InventoryUpdateRequest):
            """Update inventory information."""
            try:
                updates = request.dict(exclude_unset=True)
                result = await self._update_inventory(product_id, warehouse_id, updates)
                
                return APIResponse(
                    success=True,
                    message="Inventory updated successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to update inventory", error=str(e), product_id=product_id, warehouse_id=warehouse_id)
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _check_availability(self, product_id: str, quantity: int) -> Dict[str, Any]:
        """Check product availability across warehouses."""
        try:
            inventory_records = await self.repository.find_by_product(product_id)
            
            availability = []
            total_available = 0
            
            for record in inventory_records:
                available_qty = record.quantity - record.reserved_quantity
                total_available += available_qty
                
                availability.append({
                    "warehouse_id": record.warehouse_id,
                    "available_quantity": available_qty,
                    "total_quantity": record.quantity,
                    "reserved_quantity": record.reserved_quantity
                })
            
            return {
                "product_id": product_id,
                "requested_quantity": quantity,
                "total_available": total_available,
                "is_available": total_available >= quantity,
                "warehouses": availability
            }
        
        except Exception as e:
            self.logger.error("Failed to check availability", error=str(e), product_id=product_id)
            raise
    
    async def _reserve_stock(self, product_id: str, warehouse_id: str, quantity: int, order_id: str, expires_at: Optional[datetime] = None) -> Dict[str, Any]:
        """Reserve stock for an order."""
        try:
            # Check if enough stock is available
            inventory = await self.repository.find_by_product_and_warehouse(product_id, warehouse_id)
            if not inventory:
                raise ValueError(f"No inventory found for product {product_id} in warehouse {warehouse_id}")
            
            available_qty = inventory.quantity - inventory.reserved_quantity
            if available_qty < quantity:
                raise ValueError(f"Insufficient stock. Available: {available_qty}, Requested: {quantity}")
            
            # Create reservation
            reservation_id = str(uuid4())
            if not expires_at:
                expires_at = datetime.utcnow() + timedelta(hours=2)  # Default 2-hour expiration
            
            reservation = {
                "id": reservation_id,
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "quantity": quantity,
                "order_id": order_id,
                "created_at": datetime.utcnow(),
                "expires_at": expires_at
            }
            
            self.reservations[reservation_id] = reservation
            
            # Update reserved quantity in database
            new_reserved_qty = inventory.reserved_quantity + quantity
            await self.repository.update(inventory.id, reserved_quantity=new_reserved_qty, last_updated=datetime.utcnow())
            
            # Send inventory update notification
            await self.send_message(
                recipient_agent="broadcast",
                message_type=MessageType.INVENTORY_UPDATE,
                payload={
                    "product_id": product_id,
                    "warehouse_id": warehouse_id,
                    "reserved_quantity": quantity,
                    "order_id": order_id,
                    "reservation_id": reservation_id
                }
            )
            
            self.logger.info("Stock reserved", reservation_id=reservation_id, product_id=product_id, quantity=quantity)
            
            return reservation
        
        except Exception as e:
            self.logger.error("Failed to reserve stock", error=str(e), product_id=product_id, warehouse_id=warehouse_id)
            raise
    
    async def _release_reservation(self, reservation_id: str) -> Dict[str, Any]:
        """Release a stock reservation."""
        try:
            reservation = self.reservations.get(reservation_id)
            if not reservation:
                raise ValueError(f"Reservation {reservation_id} not found")
            
            # Update reserved quantity in database
            inventory = await self.repository.find_by_product_and_warehouse(
                reservation["product_id"], 
                reservation["warehouse_id"]
            )
            
            if inventory:
                new_reserved_qty = max(0, inventory.reserved_quantity - reservation["quantity"])
                await self.repository.update(inventory.id, reserved_quantity=new_reserved_qty, last_updated=datetime.utcnow())
            
            # Remove reservation
            del self.reservations[reservation_id]
            
            # Send inventory update notification
            await self.send_message(
                recipient_agent="broadcast",
                message_type=MessageType.INVENTORY_UPDATE,
                payload={
                    "product_id": reservation["product_id"],
                    "warehouse_id": reservation["warehouse_id"],
                    "released_quantity": reservation["quantity"],
                    "reservation_id": reservation_id
                }
            )
            
            self.logger.info("Reservation released", reservation_id=reservation_id)
            
            return {"reservation_id": reservation_id, "status": "released"}
        
        except Exception as e:
            self.logger.error("Failed to release reservation", error=str(e), reservation_id=reservation_id)
            raise
    
    async def _record_stock_movement(self, movement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record a stock movement."""
        try:
            # Record the movement
            movement_id = await self.movement_repository.create_movement(movement_data)
            
            # Update inventory quantity
            inventory = await self.repository.find_by_product_and_warehouse(
                movement_data["product_id"], 
                movement_data["warehouse_id"]
            )
            
            if inventory:
                new_quantity = inventory.quantity + movement_data["quantity_change"]
                if new_quantity < 0:
                    raise ValueError("Stock quantity cannot be negative")
                
                await self.repository.update(inventory.id, quantity=new_quantity, last_updated=datetime.utcnow())
            else:
                # Create new inventory record if it doesn't exist
                if movement_data["quantity_change"] > 0:
                    await self.repository.create(
                        product_id=movement_data["product_id"],
                        warehouse_id=movement_data["warehouse_id"],
                        quantity=movement_data["quantity_change"],
                        reserved_quantity=0,
                        reorder_point=10,  # Default reorder point
                        max_stock=1000,    # Default max stock
                        last_updated=datetime.utcnow()
                    )
            
            # Send inventory update notification
            await self.send_message(
                recipient_agent="broadcast",
                message_type=MessageType.INVENTORY_UPDATE,
                payload={
                    "product_id": movement_data["product_id"],
                    "warehouse_id": movement_data["warehouse_id"],
                    "quantity_change": movement_data["quantity_change"],
                    "movement_type": movement_data["movement_type"],
                    "movement_id": movement_id
                }
            )
            
            self.logger.info("Stock movement recorded", movement_id=movement_id, **movement_data)
            
            return {"movement_id": movement_id, "status": "recorded"}
        
        except Exception as e:
            self.logger.error("Failed to record stock movement", error=str(e))
            raise
    
    async def _get_inventory(self, product_id: Optional[str] = None, warehouse_id: Optional[str] = None, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Get inventory information with optional filters."""
        try:
            if product_id and warehouse_id:
                inventory = await self.repository.find_by_product_and_warehouse(product_id, warehouse_id)
                return {"inventory": inventory.dict() if inventory else None}
            elif product_id:
                inventory_records = await self.repository.find_by_product(product_id)
                return {"inventory": [record.dict() for record in inventory_records]}
            elif warehouse_id:
                inventory_records = await self.repository.find_by_warehouse(warehouse_id)
                return {"inventory": [record.dict() for record in inventory_records]}
            else:
                # Get all inventory with pagination
                offset = (page - 1) * per_page
                inventory_records = await self.repository.get_all(limit=per_page, offset=offset)
                total = await self.repository.count()
                pages = (total + per_page - 1) // per_page
                
                return PaginatedResponse(
                    items=[record.dict() for record in inventory_records],
                    total=total,
                    page=page,
                    per_page=per_page,
                    pages=pages
                ).dict()
        
        except Exception as e:
            self.logger.error("Failed to get inventory", error=str(e))
            raise
    
    async def _get_low_stock_alerts(self) -> List[Dict[str, Any]]:
        """Get low stock alerts."""
        try:
            low_stock_items = await self.repository.find_low_stock_items()
            
            alerts = []
            for item in low_stock_items:
                alert_level = "critical" if item.quantity == 0 else "warning"
                suggested_reorder = max(item.reorder_point * 2, item.max_stock - item.quantity)
                
                alert = LowStockAlert(
                    product_id=item.product_id,
                    warehouse_id=item.warehouse_id,
                    current_quantity=item.quantity,
                    reorder_point=item.reorder_point,
                    suggested_reorder_quantity=suggested_reorder,
                    alert_level=alert_level
                )
                
                alerts.append(alert.dict())
            
            return alerts
        
        except Exception as e:
            self.logger.error("Failed to get low stock alerts", error=str(e))
            raise
    
    async def _update_inventory(self, product_id: str, warehouse_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update inventory information."""
        try:
            inventory = await self.repository.find_by_product_and_warehouse(product_id, warehouse_id)
            if not inventory:
                raise ValueError(f"No inventory found for product {product_id} in warehouse {warehouse_id}")
            
            updates["last_updated"] = datetime.utcnow()
            await self.repository.update(inventory.id, **updates)
            
            # Send inventory update notification
            await self.send_message(
                recipient_agent="broadcast",
                message_type=MessageType.INVENTORY_UPDATE,
                payload={
                    "product_id": product_id,
                    "warehouse_id": warehouse_id,
                    "updates": updates
                }
            )
            
            self.logger.info("Inventory updated", product_id=product_id, warehouse_id=warehouse_id, updates=list(updates.keys()))
            
            return {"product_id": product_id, "warehouse_id": warehouse_id, "status": "updated"}
        
        except Exception as e:
            self.logger.error("Failed to update inventory", error=str(e), product_id=product_id, warehouse_id=warehouse_id)
            raise
    
    async def _handle_order_created(self, message: AgentMessage):
        """Handle order created messages to check inventory availability."""
        payload = message.payload
        order_id = payload.get("order_id")
        items = payload.get("items", [])
        
        # Check availability for all items
        availability_results = []
        
        for item in items:
            product_id = item.get("product_id")
            quantity = item.get("quantity", 0)
            
            if product_id and quantity > 0:
                try:
                    availability = await self._check_availability(product_id, quantity)
                    availability_results.append({
                        "product_id": product_id,
                        "requested_quantity": quantity,
                        "is_available": availability["is_available"],
                        "total_available": availability["total_available"]
                    })
                except Exception as e:
                    self.logger.error("Failed to check availability for order item", error=str(e), product_id=product_id, order_id=order_id)
        
        # Send availability results back to order agent
        await self.send_message(
            recipient_agent="order_agent",
            message_type=MessageType.INVENTORY_UPDATE,
            payload={
                "order_id": order_id,
                "availability_check": availability_results,
                "all_available": all(item["is_available"] for item in availability_results)
            }
        )
    
    async def _handle_order_updated(self, message: AgentMessage):
        """Handle order status updates."""
        payload = message.payload
        order_id = payload.get("order_id")
        new_status = payload.get("new_status")
        
        # If order is cancelled, release any reservations
        if new_status == "cancelled":
            # Find and release reservations for this order
            reservations_to_release = [
                res_id for res_id, res in self.reservations.items()
                if res.get("order_id") == order_id
            ]
            
            for reservation_id in reservations_to_release:
                try:
                    await self._release_reservation(reservation_id)
                except Exception as e:
                    self.logger.error("Failed to release reservation for cancelled order", error=str(e), reservation_id=reservation_id, order_id=order_id)
    
    async def _handle_warehouse_selected(self, message: AgentMessage):
        """Handle warehouse selection to reserve stock."""
        payload = message.payload
        order_id = payload.get("order_id")
        warehouse_id = payload.get("warehouse_id")
        items = payload.get("items", [])
        
        # Reserve stock for each item in the selected warehouse
        reservations = []
        
        for item in items:
            product_id = item.get("product_id")
            quantity = item.get("quantity", 0)
            
            if product_id and quantity > 0:
                try:
                    reservation = await self._reserve_stock(product_id, warehouse_id, quantity, order_id)
                    reservations.append(reservation)
                except Exception as e:
                    self.logger.error("Failed to reserve stock for order", error=str(e), product_id=product_id, order_id=order_id)
                    
                    # Send error notification
                    await self.send_message(
                        recipient_agent="monitoring_agent",
                        message_type=MessageType.ERROR_DETECTED,
                        payload={
                            "agent_id": self.agent_id,
                            "error_type": "stock_reservation_failed",
                            "order_id": order_id,
                            "product_id": product_id,
                            "warehouse_id": warehouse_id,
                            "message": f"Failed to reserve stock: {str(e)}"
                        }
                    )
        
        # Send reservation confirmation
        await self.send_message(
            recipient_agent="order_agent",
            message_type=MessageType.INVENTORY_UPDATE,
            payload={
                "order_id": order_id,
                "warehouse_id": warehouse_id,
                "reservations": reservations,
                "status": "reserved"
            }
        )
    
    async def _monitor_low_stock(self):
        """Background task to monitor low stock levels."""
        while not self.shutdown_event.is_set():
            try:
                # Check for low stock items
                alerts = await self._get_low_stock_alerts()
                
                for alert in alerts:
                    # Send alert to monitoring agent
                    await self.send_message(
                        recipient_agent="monitoring_agent",
                        message_type=MessageType.RISK_ALERT,
                        payload={
                            "alert_type": "low_stock",
                            "severity": alert["alert_level"],
                            "product_id": alert["product_id"],
                            "warehouse_id": alert["warehouse_id"],
                            "current_quantity": alert["current_quantity"],
                            "reorder_point": alert["reorder_point"]
                        }
                    )
                    
                    # Send reorder recommendation to demand forecasting agent
                    await self.send_message(
                        recipient_agent="demand_forecasting_agent",
                        message_type=MessageType.INVENTORY_UPDATE,
                        payload={
                            "action": "reorder_recommendation",
                            "product_id": alert["product_id"],
                            "warehouse_id": alert["warehouse_id"],
                            "suggested_quantity": alert["suggested_reorder_quantity"]
                        }
                    )
                
                # Sleep for 15 minutes before next check
                await asyncio.sleep(900)
            
            except Exception as e:
                self.logger.error("Error in low stock monitoring", error=str(e))
                await asyncio.sleep(1800)  # Wait 30 minutes on error
    
    async def _cleanup_expired_reservations(self):
        """Background task to cleanup expired reservations."""
        while not self.shutdown_event.is_set():
            try:
                current_time = datetime.utcnow()
                expired_reservations = [
                    res_id for res_id, res in self.reservations.items()
                    if res.get("expires_at", current_time) <= current_time
                ]
                
                for reservation_id in expired_reservations:
                    try:
                        await self._release_reservation(reservation_id)
                        self.logger.info("Expired reservation cleaned up", reservation_id=reservation_id)
                    except Exception as e:
                        self.logger.error("Failed to cleanup expired reservation", error=str(e), reservation_id=reservation_id)
                
                # Sleep for 5 minutes before next cleanup
                await asyncio.sleep(300)
            
            except Exception as e:
                self.logger.error("Error in reservation cleanup", error=str(e))
                await asyncio.sleep(600)  # Wait 10 minutes on error
    
    async def _sync_inventory_levels(self):
        """Background task to sync inventory levels with external systems."""
        while not self.shutdown_event.is_set():
            try:
                # This would sync with warehouse management systems, ERP, etc.
                # For now, we'll just log the sync operation
                self.logger.debug("Inventory sync check completed")
                
                # Sleep for 1 hour before next sync
                await asyncio.sleep(3600)
            
            except Exception as e:
                self.logger.error("Error in inventory sync", error=str(e))
                await asyncio.sleep(1800)  # Wait 30 minutes on error


# FastAPI app instance for running the agent as a service
app = FastAPI(title="Inventory Agent", version="1.0.0")

# Global agent instance
inventory_agent: Optional[InventoryAgent] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the Inventory Agent on startup."""
    global inventory_agent
    inventory_agent = InventoryAgent()
    await inventory_agent.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup the Inventory Agent on shutdown."""
    global inventory_agent
    if inventory_agent:
        await inventory_agent.stop()


# Include agent routes
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if inventory_agent:
        health_status = inventory_agent.get_health_status()
        return {"status": "healthy", "agent_status": health_status.dict()}
    return {"status": "unhealthy", "message": "Agent not initialized"}


# Mount agent's FastAPI app
app.mount("/api/v1", inventory_agent.app if inventory_agent else FastAPI())


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
        password=os.getenv("POSTGRES_PASSWORD")
        if not password:
            raise ValueError("Database password must be set in environment variables")
    )
    initialize_database_manager(db_config)
    
    # Run the agent
    uvicorn.run(
        "inventory_agent:app",
        host="0.0.0.0",
        port=8003,
        reload=False,
        log_level="info"
    )
