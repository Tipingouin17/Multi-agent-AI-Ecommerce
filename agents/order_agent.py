"""
Order Agent - Multi-Agent E-commerce System

This agent manages the complete order lifecycle from creation to fulfillment.
It coordinates with other agents to process orders efficiently and provides
real-time order status updates.
"""

import asyncio
from datetime import datetime, timedelta
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
    Order, OrderBase, OrderStatus, OrderItem, OrderItemBase,
    APIResponse, PaginatedResponse
)
from shared.database import DatabaseManager, BaseRepository, get_database_manager


logger = structlog.get_logger(__name__)


class OrderCreateRequest(BaseModel):
    """Request model for creating a new order."""
    customer_id: str
    channel: str
    channel_order_id: str
    items: List[OrderItemBase]
    shipping_address: Dict[str, Any]
    billing_address: Dict[str, Any]
    notes: Optional[str] = None


class OrderUpdateRequest(BaseModel):
    """Request model for updating an order."""
    status: Optional[OrderStatus] = None
    notes: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    """Model for order status updates."""
    order_id: str
    old_status: OrderStatus
    new_status: OrderStatus
    timestamp: datetime
    reason: Optional[str] = None


class OrderRepository(BaseRepository):
    """Repository for order data operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        from shared.models import OrderDB
        super().__init__(db_manager, OrderDB)
    
    async def find_by_status(self, status: OrderStatus) -> List[Order]:
        """Find orders by status."""
        records = await self.find_by_criteria(status=status.value)
        return [self._to_pydantic(record) for record in records]
    
    async def find_by_channel(self, channel: str) -> List[Order]:
        """Find orders by channel."""
        records = await self.find_by_criteria(channel=channel)
        return [self._to_pydantic(record) for record in records]
    
    async def find_by_customer(self, customer_id: str) -> List[Order]:
        """Find orders by customer."""
        records = await self.find_by_criteria(customer_id=customer_id)
        return [self._to_pydantic(record) for record in records]
    
    def _to_pydantic(self, db_record) -> Order:
        """Convert database record to Pydantic model."""
        return Order(
            id=db_record.id,
            customer_id=db_record.customer_id,
            channel=db_record.channel,
            channel_order_id=db_record.channel_order_id,
            status=OrderStatus(db_record.status),
            items=[],  # Will be populated separately
            shipping_address=db_record.shipping_address,
            billing_address=db_record.billing_address,
            subtotal=db_record.subtotal,
            shipping_cost=db_record.shipping_cost,
            tax_amount=db_record.tax_amount,
            total_amount=db_record.total_amount,
            notes=db_record.notes,
            created_at=db_record.created_at,
            updated_at=db_record.updated_at
        )


class OrderAgent(BaseAgent):
    """
    Order Agent handles all order-related operations including:
    - Order creation and validation
    - Order status management
    - Order fulfillment coordination
    - Customer notifications
    """
    
    def __init__(self, **kwargs):
        super().__init__(agent_id="order_agent", **kwargs)
        self.repository: Optional[OrderRepository] = None
        self.app = FastAPI(title="Order Agent API", version="1.0.0")
        self.setup_routes()
        
        # Register message handlers
        self.register_handler(MessageType.ORDER_CREATED, self._handle_order_created)
        self.register_handler(MessageType.ORDER_UPDATED, self._handle_order_updated)
        self.register_handler(MessageType.WAREHOUSE_SELECTED, self._handle_warehouse_selected)
        self.register_handler(MessageType.CARRIER_SELECTED, self._handle_carrier_selected)
    
    async def initialize(self):
        """Initialize the Order Agent."""
        self.logger.info("Initializing Order Agent")
        
        # Initialize database repository
        db_manager = get_database_manager()
        self.repository = OrderRepository(db_manager)
        
        # Start background tasks
        asyncio.create_task(self._process_pending_orders())
        asyncio.create_task(self._monitor_order_timeouts())
        
        self.logger.info("Order Agent initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up Order Agent")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process order-specific business logic."""
        action = data.get("action")
        
        if action == "create_order":
            return await self._create_order(data["order_data"])
        elif action == "update_order_status":
            return await self._update_order_status(data["order_id"], data["status"])
        elif action == "get_order":
            return await self._get_order(data["order_id"])
        elif action == "list_orders":
            return await self._list_orders(data.get("filters", {}))
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def setup_routes(self):
        """Setup FastAPI routes for the Order Agent."""
        
        @self.app.post("/orders", response_model=APIResponse)
        async def create_order(request: OrderCreateRequest):
            """Create a new order."""
            try:
                # Calculate totals
                subtotal = sum(item.total_price for item in request.items)
                tax_amount = subtotal * Decimal("0.20")  # 20% tax rate
                shipping_cost = Decimal("5.99")  # Default shipping cost
                total_amount = subtotal + tax_amount + shipping_cost
                
                order_data = OrderBase(
                    customer_id=request.customer_id,
                    channel=request.channel,
                    channel_order_id=request.channel_order_id,
                    status=OrderStatus.PENDING,
                    items=request.items,
                    shipping_address=request.shipping_address,
                    billing_address=request.billing_address,
                    subtotal=subtotal,
                    shipping_cost=shipping_cost,
                    tax_amount=tax_amount,
                    total_amount=total_amount,
                    notes=request.notes
                )
                
                result = await self._create_order(order_data.dict())
                
                return APIResponse(
                    success=True,
                    message="Order created successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to create order", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/orders/{order_id}", response_model=APIResponse)
        async def get_order(order_id: str):
            """Get order by ID."""
            try:
                order = await self._get_order(order_id)
                if not order:
                    raise HTTPException(status_code=404, detail="Order not found")
                
                return APIResponse(
                    success=True,
                    message="Order retrieved successfully",
                    data=order
                )
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get order", error=str(e), order_id=order_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.put("/orders/{order_id}/status", response_model=APIResponse)
        async def update_order_status(order_id: str, request: OrderUpdateRequest):
            """Update order status."""
            try:
                if request.status:
                    result = await self._update_order_status(order_id, request.status)
                    
                    return APIResponse(
                        success=True,
                        message="Order status updated successfully",
                        data=result
                    )
                else:
                    raise HTTPException(status_code=400, detail="Status is required")
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update order status", error=str(e), order_id=order_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/orders", response_model=APIResponse)
        async def list_orders(
            status: Optional[str] = None,
            channel: Optional[str] = None,
            customer_id: Optional[str] = None,
            page: int = 1,
            per_page: int = 20
        ):
            """List orders with optional filters."""
            try:
                filters = {}
                if status:
                    filters["status"] = status
                if channel:
                    filters["channel"] = channel
                if customer_id:
                    filters["customer_id"] = customer_id
                
                filters["page"] = page
                filters["per_page"] = per_page
                
                result = await self._list_orders(filters)
                
                return APIResponse(
                    success=True,
                    message="Orders retrieved successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to list orders", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new order."""
        try:
            # Generate order ID
            order_id = str(uuid4())
            order_data["id"] = order_id
            order_data["created_at"] = datetime.utcnow()
            order_data["updated_at"] = datetime.utcnow()
            
            # Create order in database
            await self.repository.create(**order_data)
            
            # Send order created notification
            await self.send_message(
                recipient_agent="broadcast",
                message_type=MessageType.ORDER_CREATED,
                payload={
                    "order_id": order_id,
                    "customer_id": order_data["customer_id"],
                    "channel": order_data["channel"],
                    "total_amount": float(order_data["total_amount"]),
                    "items": order_data["items"]
                }
            )
            
            # Request warehouse selection
            await self.send_message(
                recipient_agent="warehouse_selection_agent",
                message_type=MessageType.ORDER_CREATED,
                payload={
                    "order_id": order_id,
                    "shipping_address": order_data["shipping_address"],
                    "items": order_data["items"]
                }
            )
            
            self.logger.info("Order created", order_id=order_id)
            
            return {"order_id": order_id, "status": "created"}
        
        except Exception as e:
            self.logger.error("Failed to create order", error=str(e))
            raise
    
    async def _get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID."""
        try:
            order = await self.repository.get_by_id(order_id)
            if order:
                return order.__dict__
            return None
        
        except Exception as e:
            self.logger.error("Failed to get order", error=str(e), order_id=order_id)
            raise
    
    async def _update_order_status(self, order_id: str, new_status: OrderStatus) -> Dict[str, Any]:
        """Update order status."""
        try:
            # Get current order
            order = await self.repository.get_by_id(order_id)
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            old_status = OrderStatus(order.status)
            
            # Update status
            await self.repository.update(order_id, status=new_status.value, updated_at=datetime.utcnow())
            
            # Create status update record
            status_update = OrderStatusUpdate(
                order_id=order_id,
                old_status=old_status,
                new_status=new_status,
                timestamp=datetime.utcnow()
            )
            
            # Send status update notification
            await self.send_message(
                recipient_agent="broadcast",
                message_type=MessageType.ORDER_UPDATED,
                payload=status_update.dict()
            )
            
            # Send customer notification
            await self.send_message(
                recipient_agent="customer_communication_agent",
                message_type=MessageType.CUSTOMER_NOTIFICATION,
                payload={
                    "customer_id": order.customer_id,
                    "order_id": order_id,
                    "notification_type": "status_update",
                    "old_status": old_status.value,
                    "new_status": new_status.value
                }
            )
            
            self.logger.info("Order status updated", order_id=order_id, old_status=old_status.value, new_status=new_status.value)
            
            return status_update.dict()
        
        except Exception as e:
            self.logger.error("Failed to update order status", error=str(e), order_id=order_id)
            raise
    
    async def _list_orders(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """List orders with filters and pagination."""
        try:
            page = filters.get("page", 1)
            per_page = min(filters.get("per_page", 20), 100)  # Max 100 per page
            offset = (page - 1) * per_page
            
            # Apply filters
            if filters.get("status"):
                orders = await self.repository.find_by_status(OrderStatus(filters["status"]))
            elif filters.get("channel"):
                orders = await self.repository.find_by_channel(filters["channel"])
            elif filters.get("customer_id"):
                orders = await self.repository.find_by_customer(filters["customer_id"])
            else:
                orders = await self.repository.get_all(limit=per_page, offset=offset)
            
            # Get total count
            total = await self.repository.count()
            pages = (total + per_page - 1) // per_page
            
            return PaginatedResponse(
                items=[order.__dict__ for order in orders],
                total=total,
                page=page,
                per_page=per_page,
                pages=pages
            ).dict()
        
        except Exception as e:
            self.logger.error("Failed to list orders", error=str(e))
            raise
    
    async def _handle_order_created(self, message: AgentMessage):
        """Handle order created messages from other agents."""
        self.logger.debug("Received order created message", message_id=message.message_id)
        # This agent is the source of order creation, so this is mainly for logging
    
    async def _handle_order_updated(self, message: AgentMessage):
        """Handle order updated messages from other agents."""
        self.logger.debug("Received order updated message", message_id=message.message_id)
        # Log the update for audit purposes
    
    async def _handle_warehouse_selected(self, message: AgentMessage):
        """Handle warehouse selection completion."""
        payload = message.payload
        order_id = payload.get("order_id")
        warehouse_id = payload.get("warehouse_id")
        
        self.logger.info("Warehouse selected for order", order_id=order_id, warehouse_id=warehouse_id)
        
        # Update order status to processing
        await self._update_order_status(order_id, OrderStatus.PROCESSING)
        
        # Request carrier selection
        await self.send_message(
            recipient_agent="carrier_selection_agent",
            message_type=MessageType.WAREHOUSE_SELECTED,
            payload={
                "order_id": order_id,
                "warehouse_id": warehouse_id,
                "shipping_address": payload.get("shipping_address"),
                "package_details": payload.get("package_details")
            }
        )
    
    async def _handle_carrier_selected(self, message: AgentMessage):
        """Handle carrier selection completion."""
        payload = message.payload
        order_id = payload.get("order_id")
        carrier_id = payload.get("carrier_id")
        estimated_delivery = payload.get("estimated_delivery")
        
        self.logger.info("Carrier selected for order", order_id=order_id, carrier_id=carrier_id)
        
        # Update order status to confirmed
        await self._update_order_status(order_id, OrderStatus.CONFIRMED)
        
        # Send fulfillment request to warehouse
        await self.send_message(
            recipient_agent="warehouse_management_agent",
            message_type=MessageType.CARRIER_SELECTED,
            payload={
                "order_id": order_id,
                "carrier_id": carrier_id,
                "estimated_delivery": estimated_delivery,
                "fulfillment_required": True
            }
        )
    
    async def _process_pending_orders(self):
        """Background task to process pending orders."""
        while not self.shutdown_event.is_set():
            try:
                # Get pending orders
                pending_orders = await self.repository.find_by_status(OrderStatus.PENDING)
                
                for order in pending_orders:
                    # Check if order has been pending too long (> 5 minutes)
                    if datetime.utcnow() - order.created_at > timedelta(minutes=5):
                        self.logger.warning("Order pending too long", order_id=order.id)
                        
                        # Send alert to monitoring agent
                        await self.send_message(
                            recipient_agent="monitoring_agent",
                            message_type=MessageType.ERROR_DETECTED,
                            payload={
                                "agent_id": self.agent_id,
                                "error_type": "order_timeout",
                                "order_id": order.id,
                                "message": f"Order {order.id} has been pending for too long"
                            }
                        )
                
                # Sleep for 30 seconds before next check
                await asyncio.sleep(30)
            
            except Exception as e:
                self.logger.error("Error in pending orders processing", error=str(e))
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _monitor_order_timeouts(self):
        """Background task to monitor order processing timeouts."""
        while not self.shutdown_event.is_set():
            try:
                # Get processing orders
                processing_orders = await self.repository.find_by_status(OrderStatus.PROCESSING)
                
                for order in processing_orders:
                    # Check if order has been processing too long (> 30 minutes)
                    if datetime.utcnow() - order.updated_at > timedelta(minutes=30):
                        self.logger.warning("Order processing timeout", order_id=order.id)
                        
                        # Send alert to monitoring agent
                        await self.send_message(
                            recipient_agent="monitoring_agent",
                            message_type=MessageType.ERROR_DETECTED,
                            payload={
                                "agent_id": self.agent_id,
                                "error_type": "processing_timeout",
                                "order_id": order.id,
                                "message": f"Order {order.id} processing timeout"
                            }
                        )
                
                # Sleep for 60 seconds before next check
                await asyncio.sleep(60)
            
            except Exception as e:
                self.logger.error("Error in order timeout monitoring", error=str(e))
                await asyncio.sleep(120)  # Wait longer on error


# FastAPI app instance for running the agent as a service
app = FastAPI(title="Order Agent", version="1.0.0")

# Global agent instance
order_agent: Optional[OrderAgent] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the Order Agent on startup."""
    global order_agent
    order_agent = OrderAgent()
    await order_agent.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup the Order Agent on shutdown."""
    global order_agent
    if order_agent:
        await order_agent.stop()


# Include agent routes
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if order_agent:
        health_status = order_agent.get_health_status()
        return {"status": "healthy", "agent_status": health_status.dict()}
    return {"status": "unhealthy", "message": "Agent not initialized"}


# Mount agent's FastAPI app
app.mount("/api/v1", order_agent.app if order_agent else FastAPI())


if __name__ == "__main__":
    import uvicorn
    from shared.database import initialize_database_manager, DatabaseConfig
    from shared.models import DatabaseConfig
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
        "order_agent:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )
