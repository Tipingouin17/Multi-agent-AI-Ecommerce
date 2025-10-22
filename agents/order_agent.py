
import asyncio
import json
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, Field
import structlog
import uvicorn

# Dynamically add project root to Python path for shared modules
import sys
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.base_agent import BaseAgent, MessageType, AgentMessage, AgentStatus, HealthStatus
from shared.models import (
    Order, OrderBase, OrderStatus, OrderItem, OrderItemBase,
    APIResponse, PaginatedResponse, DatabaseConfig, OrderDB
)
from shared.database import DatabaseManager, BaseRepository, get_database_manager, initialize_database_manager
from shared.db_helpers import DatabaseHelper, get_db_helper

logger = structlog.get_logger(__name__)

class OrderCreateRequest(BaseModel):
    """Request model for creating a new order."""
    customer_id: str = Field(..., description="ID of the customer placing the order")
    channel: str = Field(..., description="Sales channel (e.g., 'web', 'mobile', 'pos')")
    channel_order_id: str = Field(..., description="Unique order ID from the sales channel")
    items: List[OrderItemBase] = Field(..., description="List of items in the order")
    shipping_address: Dict[str, Any] = Field(..., description="Shipping address details")
    billing_address: Dict[str, Any] = Field(..., description="Billing address details")
    notes: Optional[str] = Field(None, description="Additional notes for the order")

class OrderUpdateRequest(BaseModel):
    """Request model for updating an order."""
    status: Optional[OrderStatus] = Field(None, description="New status for the order")
    notes: Optional[str] = Field(None, description="Updated notes for the order")

class OrderStatusUpdate(BaseModel):
    """Model for order status updates."""
    order_id: str = Field(..., description="ID of the order being updated")
    old_status: OrderStatus = Field(..., description="Previous status of the order")
    new_status: OrderStatus = Field(..., description="New status of the order")
    timestamp: datetime = Field(..., description="Timestamp of the status update")
    reason: Optional[str] = Field(None, description="Reason for the status change")

class OrderRepository(BaseRepository):
    """Repository for order data operations."

    Handles CRUD operations for Order objects in the database.
    """
    def __init__(self, db_manager: DatabaseManager, db_helper: DatabaseHelper):
        """Initializes the OrderRepository with a database manager and helper."

        Args:
            db_manager (DatabaseManager): The database manager instance.
            db_helper (DatabaseHelper): The database helper instance.
        """
        super().__init__(db_manager, db_helper, OrderDB)

    async def find_by_status(self, status: OrderStatus) -> List[Order]:
        """Finds orders by their status."

        Args:
            status (OrderStatus): The status to filter orders by.

        Returns:
            List[Order]: A list of orders matching the given status.
        """
        if not self._db_initialized: return []
        try:
            records = await self.find_by_criteria(status=status.value)
            return [self._to_pydantic(record) for record in records]
        except Exception as e:
            logger.error(f"Failed to find orders by status {status.value}", error=str(e))
            raise

    async def find_by_channel(self, channel: str) -> List[Order]:
        """Finds orders by their sales channel."

        Args:
            channel (str): The channel to filter orders by.

        Returns:
            List[Order]: A list of orders from the given channel.
        """
        if not self._db_initialized: return []
        try:
            records = await self.find_by_criteria(channel=channel)
            return [self._to_pydantic(record) for record in records]
        except Exception as e:
            logger.error(f"Failed to find orders by channel {channel}", error=str(e))
            raise

    async def find_by_customer(self, customer_id: str) -> List[Order]:
        """Finds orders by customer ID."

        Args:
            customer_id (str): The customer ID to filter orders by.

        Returns:
            List[Order]: A list of orders placed by the given customer.
        """
        if not self._db_initialized: return []
        try:
            records = await self.find_by_criteria(customer_id=customer_id)
            return [self._to_pydantic(record) for record in records]
        except Exception as e:
            logger.error(f"Failed to find orders by customer {customer_id}", error=str(e))
            raise

    def _to_pydantic(self, db_record: Any) -> Order:
        """Converts a database record to a Pydantic Order model."

        Args:
            db_record (Any): The database record object.

        Returns:
            Order: The Pydantic Order model.
        """
        return Order(
            id=db_record.id,
            customer_id=db_record.customer_id,
            channel=db_record.channel,
            channel_order_id=db_record.channel_order_id,
            status=OrderStatus(db_record.status),
            items=[],  # Items will be populated separately if needed
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
        """Initializes the OrderAgent."

        Args:
            **kwargs: Arbitrary keyword arguments passed to BaseAgent.
        """
        super().__init__(agent_id="order_agent", **kwargs)
        self.repository: Optional[OrderRepository] = None
        self.app = FastAPI(title="Order Agent API", version="1.0.0",
                           description="API for managing orders in the e-commerce system.")
        self.setup_routes()
        
        # Register message handlers
        self.register_handler(MessageType.ORDER_CREATED, self._handle_order_created)
        self.register_handler(MessageType.ORDER_UPDATED, self._handle_order_updated)
        self.register_handler(MessageType.WAREHOUSE_SELECTED, self._handle_warehouse_selected)
        self.register_handler(MessageType.CARRIER_SELECTED, self._handle_carrier_selected)
        self.register_handler(MessageType.ORDER_FULFILLMENT_REQUIRED, self._handle_order_fulfillment_required)

    async def initialize(self):
        """Initializes the Order Agent, including database and background tasks."

        This method is called by the BaseAgent during startup.
        """
        self.logger.info("Initializing Order Agent")
        try:
            # Initialize database repository
            db_manager = get_database_manager()
            db_helper = get_db_helper(db_manager)
            self.repository = OrderRepository(db_manager, db_helper)
            await self.repository.initialize()
            self._db_initialized = True

            # Start background tasks
            asyncio.create_task(self._process_pending_orders())
            asyncio.create_task(self._monitor_order_timeouts())
            
            self.logger.info("Order Agent initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Order Agent: {e}", error=str(e))
            self.status = AgentStatus.ERROR
            raise

    async def cleanup(self):
        """Cleans up resources used by the Order Agent."

        This method is called by the BaseAgent during shutdown.
        """
        self.logger.info("Cleaning up Order Agent")
        if self.repository:
            await self.repository.close()
        self.logger.info("Order Agent cleanup complete")

    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processes order-specific business logic based on received data."

        Args:
            data (Dict[str, Any]): A dictionary containing action and relevant data.

        Returns:
            Dict[str, Any]: The result of the business logic operation.

        Raises:
            ValueError: If an unknown action is provided.
        """
        action = data.get("action")
        try:
            if action == "create_order":
                return await self._create_order(OrderBase(**data["order_data"]))
            elif action == "update_order_status":
                return await self._update_order_status(data["order_id"], OrderStatus(data["status"]))
            elif action == "get_order":
                return await self._get_order(data["order_id"])
            elif action == "list_orders":
                return await self._list_orders(data.get("filters", {}))
            else:
                raise ValueError(f"Unknown action: {action}")
        except Exception as e:
            self.logger.error(f"Error processing business logic for action {action}: {e}", error=str(e))
            raise

    def setup_routes(self):
        """Sets up FastAPI routes for the Order Agent API."

        Includes endpoints for creating, retrieving, updating, and listing orders,
        along with health checks and a root endpoint.
        """
        @self.app.get("/", response_model=APIResponse)
        async def root():
            return APIResponse(success=True, message="Order Agent API is running", data={"agent_id": self.agent_id, "status": self.status.value})

        @self.app.get("/health", response_model=HealthStatus)
        async def health_check_endpoint():
            """Health check endpoint for the Order Agent."

            Returns:
                HealthStatus: Current health status of the agent.
            """
            return self.get_health_status()

        @self.app.post("/orders", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
        async def create_order_endpoint(request: OrderCreateRequest):
            """Creates a new order in the system."

            Args:
                request (OrderCreateRequest): The request body containing order details.

            Returns:
                APIResponse: A response indicating success or failure, with the created order data.
            """
            try:
                # Calculate totals
                subtotal = sum(item.total_price for item in request.items)
                tax_rate = Decimal(os.getenv("ORDER_TAX_RATE", "0.20")) # 20% tax rate
                shipping_cost = Decimal(os.getenv("ORDER_SHIPPING_COST", "5.99")) # Default shipping cost

                tax_amount = subtotal * tax_rate
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
                
                result = await self._create_order(order_data)
                
                return APIResponse(
                    success=True,
                    message="Order created successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to create order via API", error=str(e), request_data=request.dict())
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        
        @self.app.get("/orders/{order_id}", response_model=APIResponse)
        async def get_order_endpoint(order_id: str):
            """Retrieves an order by its ID."

            Args:
                order_id (str): The ID of the order to retrieve.

            Returns:
                APIResponse: A response indicating success or failure, with the order data.
            """
            try:
                order = await self._get_order(order_id)
                if not order:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
                
                return APIResponse(
                    success=True,
                    message="Order retrieved successfully",
                    data=order
                )
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to get order via API", error=str(e), order_id=order_id)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        
        @self.app.put("/orders/{order_id}/status", response_model=APIResponse)
        async def update_order_status_endpoint(order_id: str, request: OrderUpdateRequest):
            """Updates the status of an order."

            Args:
                order_id (str): The ID of the order to update.
                request (OrderUpdateRequest): The request body containing the new status.

            Returns:
                APIResponse: A response indicating success or failure, with the updated status information.
            """
            try:
                if not request.status:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status is required")
                
                result = await self._update_order_status(order_id, request.status)
                
                return APIResponse(
                    success=True,
                    message="Order status updated successfully",
                    data=result
                )
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("Failed to update order status via API", error=str(e), order_id=order_id, new_status=request.status.value if request.status else 'None')
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        
        @self.app.get("/orders", response_model=PaginatedResponse)
        async def list_orders_endpoint(
            status_filter: Optional[OrderStatus] = Depends(lambda s: OrderStatus(s) if s else None),
            channel: Optional[str] = None,
            customer_id: Optional[str] = None,
            page: int = Field(1, ge=1, description="Page number"),
            per_page: int = Field(20, ge=1, le=100, description="Items per page")
        ):
            """Lists orders with optional filters and pagination."

            Args:
                status_filter (Optional[OrderStatus]): Filter orders by status.
                channel (Optional[str]): Filter orders by sales channel.
                customer_id (Optional[str]): Filter orders by customer ID.
                page (int): The page number for pagination.
                per_page (int): The number of items per page for pagination.

            Returns:
                PaginatedResponse: A paginated list of orders.
            """
            try:
                filters = {}
                if status_filter:
                    filters["status"] = status_filter
                if channel:
                    filters["channel"] = channel
                if customer_id:
                    filters["customer_id"] = customer_id
                
                filters["page"] = page
                filters["per_page"] = per_page
                
                result = await self._list_orders(filters)
                
                return PaginatedResponse(
                    items=[r.dict() for r in result.items],
                    total=result.total,
                    page=result.page,
                    per_page=result.per_page,
                    pages=result.pages
                )
            
            except Exception as e:
                self.logger.error("Failed to list orders via API", error=str(e), filters=filters)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    async def _create_order(self, order_data: OrderBase) -> Order:
        """Creates a new order in the database and sends relevant messages."

        Args:
            order_data (OrderBase): The Pydantic model containing the new order's data.

        Returns:
            Order: The created order with its generated ID and timestamps.

        Raises:
            RuntimeError: If the database is not initialized.
            Exception: For any other database or messaging errors.
        """
        if not self._db_initialized: 
            self.logger.error("Database not initialized, cannot create order.")
            raise RuntimeError("Database not initialized.")
        try:
            order_id = str(uuid4())
            current_time = datetime.utcnow()
            
            order_dict = order_data.dict()
            order_dict["id"] = order_id
            order_dict["created_at"] = current_time
            order_dict["updated_at"] = current_time
            order_dict["status"] = OrderStatus.PENDING.value # Ensure status is enum value
            
            # Convert OrderItemBase list to dict list for storage
            order_dict["items"] = [item.dict() for item in order_data.items]

            created_record = await self.repository.create(order_dict)
            created_order = self.repository._to_pydantic(created_record)
            
            await self.send_message(
                recipient_agent="broadcast",
                message_type=MessageType.ORDER_CREATED,
                payload={
                    "order_id": created_order.id,
                    "customer_id": created_order.customer_id,
                    "channel": created_order.channel,
                    "total_amount": float(created_order.total_amount),
                    "items": [item.dict() for item in created_order.items] # Ensure items are dicts for payload
                }
            )
            
            await self.send_message(
                recipient_agent="warehouse_selection_agent",
                message_type=MessageType.ORDER_FULFILLMENT_REQUIRED,
                payload={
                    "order_id": created_order.id,
                    "shipping_address": created_order.shipping_address,
                    "items": [item.dict() for item in created_order.items]
                }
            )
            
            self.logger.info("Order created", order_id=created_order.id, customer_id=created_order.customer_id)
            
            return created_order
        
        except Exception as e:
            self.logger.error("Failed to create order", error=str(e), order_data=order_data.dict())
            raise

    async def _get_order(self, order_id: str) -> Optional[Order]:
        """Retrieves an order from the database by its ID."

        Args:
            order_id (str): The ID of the order to retrieve.

        Returns:
            Optional[Order]: The Order object if found, otherwise None.

        Raises:
            RuntimeError: If the database is not initialized.
            Exception: For any other database errors.
        """
        if not self._db_initialized: 
            self.logger.error("Database not initialized, cannot get order.")
            return None
        try:
            order_record = await self.repository.get_by_id(order_id)
            if order_record:
                return self.repository._to_pydantic(order_record)
            return None
        except Exception as e:
            self.logger.error("Failed to get order", error=str(e), order_id=order_id)
            raise

    async def _update_order_status(self, order_id: str, new_status: OrderStatus) -> OrderStatusUpdate:
        """Updates the status of an order and sends status update messages."

        Args:
            order_id (str): The ID of the order to update.
            new_status (OrderStatus): The new status to set for the order.

        Returns:
            OrderStatusUpdate: An object detailing the status change.

        Raises:
            ValueError: If the order is not found.
            RuntimeError: If the database is not initialized.
            Exception: For any other database or messaging errors.
        """
        if not self._db_initialized: 
            self.logger.error("Database not initialized, cannot update order status.")
            raise RuntimeError("Database not initialized.")
        try:
            order = await self._get_order(order_id)
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            old_status = order.status
            current_time = datetime.utcnow()

            updated_record = await self.repository.update(order_id, status=new_status.value, updated_at=current_time)
            updated_order = self.repository._to_pydantic(updated_record)
            
            status_update = OrderStatusUpdate(
                order_id=order_id,
                old_status=old_status,
                new_status=new_status,
                timestamp=current_time
            )
            
            await self.send_message(
                recipient_agent="broadcast",
                message_type=MessageType.ORDER_STATUS_UPDATED,
                payload=status_update.dict()
            )
            
            await self.send_message(
                recipient_agent="customer_communication_agent",
                message_type=MessageType.CUSTOMER_NOTIFICATION,
                payload={
                    "customer_id": order.customer_id,
                    "order_id": order_id,
                    "notification_type": "status_update",
                    "old_status": old_status.value,
                    "new_status": new_status.value,
                    "message": f"Your order {order_id} status changed from {old_status.value} to {new_status.value}."
                }
            )
            
            self.logger.info("Order status updated", order_id=order_id, old_status=old_status.value, new_status=new_status.value)
            
            return status_update
        
        except Exception as e:
            self.logger.error("Failed to update order status", error=str(e), order_id=order_id, new_status=new_status.value)
            raise

    async def _list_orders(self, filters: Dict[str, Any]) -> PaginatedResponse:
        """Lists orders from the database with filtering and pagination."

        Args:
            filters (Dict[str, Any]): A dictionary of filters including 'status', 'channel', 'customer_id', 'page', and 'per_page'.

        Returns:
            PaginatedResponse: A paginated response containing a list of orders and pagination metadata.

        Raises:
            RuntimeError: If the database is not initialized.
            Exception: For any other database errors.
        """
        if not self._db_initialized: 
            self.logger.error("Database not initialized, cannot list orders.")
            return PaginatedResponse(items=[], total=0, page=filters.get("page", 1), per_page=filters.get("per_page", 20), pages=0)
        try:
            page = filters.get("page", 1)
            per_page = min(filters.get("per_page", 20), 100)  # Max 100 per page
            offset = (page - 1) * per_page
            
            query_filters = {}
            if "status" in filters: # Use 'in' to check for key existence
                query_filters["status"] = filters["status"].value if isinstance(filters["status"], OrderStatus) else filters["status"]
            if "channel" in filters:
                query_filters["channel"] = filters["channel"]
            if "customer_id" in filters:
                query_filters["customer_id"] = filters["customer_id"]
            
            # Fetch records with filters and pagination
            order_records = await self.repository.find_by_criteria(limit=per_page, offset=offset, **query_filters)
            orders = [self.repository._to_pydantic(record) for record in order_records]
            
            # Get total count with filters
            total = await self.repository.count_by_criteria(**query_filters)
            pages = (total + per_page - 1) // per_page
            
            return PaginatedResponse(
                items=orders,
                total=total,
                page=page,
                per_page=per_page,
                pages=pages
            )
        
        except Exception as e:
            self.logger.error("Failed to list orders", error=str(e), filters=filters)
            raise

    async def process_message(self, message: AgentMessage):
        """Processes an incoming message, dispatching it to the appropriate handler."

        Args:
            message (AgentMessage): The incoming message to process.
        """
        self.logger.info("Processing incoming message", message_id=message.message_id, message_type=message.message_type.value, sender=message.sender_agent)
        try:
            if message.message_type in self.message_handlers:
                await self.message_handlers[message.message_type](message)
            else:
                self.logger.warning("No handler for message type", message_type=message.message_type.value)
        except Exception as e:
            self.logger.error("Error processing message", message_id=message.message_id, message_type=message.message_type.value, error=str(e))
            # Optionally send an error message back or to a monitoring agent
            await self.send_message(
                recipient_agent="monitoring_agent",
                message_type=MessageType.ERROR_DETECTED,
                payload={
                    "agent_id": self.agent_id,
                    "error_type": "message_processing_failed",
                    "message_id": message.message_id,
                    "details": str(e)
                }
            )

    async def _handle_order_created(self, message: AgentMessage):
        """Handles ORDER_CREATED messages. Primarily for logging and internal state updates."

        Args:
            message (AgentMessage): The incoming ORDER_CREATED message.
        """
        self.logger.debug("Received order created message (self-generated or from other agents)", message_id=message.message_id, payload=message.payload)
        # This agent is the source of order creation, so this is mainly for logging
        # In a distributed system, this could also handle orders created by other order agents

    async def _handle_order_updated(self, message: AgentMessage):
        """Handles ORDER_UPDATED messages. Primarily for logging and audit purposes."

        Args:
            message (AgentMessage): The incoming ORDER_UPDATED message.
        """
        self.logger.debug("Received generic order updated message", message_id=message.message_id, payload=message.payload)
        # Log the update for audit purposes or trigger other internal processes

    async def _handle_order_status_updated(self, message: AgentMessage):
        """Handles ORDER_STATUS_UPDATED messages. Updates internal state and logs."

        Args:
            message (AgentMessage): The incoming ORDER_STATUS_UPDATED message.
        """
        payload = message.payload
        order_id = payload.get("order_id")
        new_status = payload.get("new_status")
        self.logger.info("Received order status updated message", order_id=order_id, new_status=new_status)
        # Here, the agent could update its internal cache or trigger follow-up actions

    async def _handle_order_fulfillment_required(self, message: AgentMessage):
        """Handles ORDER_FULFILLMENT_REQUIRED messages."

        This message type is used to request warehouse selection.

        Args:
            message (AgentMessage): The incoming ORDER_FULFILLMENT_REQUIRED message.
        """
        payload = message.payload
        order_id = payload.get("order_id")
        shipping_address = payload.get("shipping_address")
        items = payload.get("items")

        self.logger.info("Received order fulfillment required message, requesting warehouse selection", order_id=order_id)

        await self.send_message(
            recipient_agent="warehouse_selection_agent",
            message_type=MessageType.WAREHOUSE_SELECTED, # Re-using WAREHOUSE_SELECTED as a request type
            payload={
                "order_id": order_id,
                "shipping_address": shipping_address,
                "items": items
            }
        )

    async def _handle_warehouse_selected(self, message: AgentMessage):
        """Handles WAREHOUSE_SELECTED messages, updating order status and requesting carrier selection."

        Args:
            message (AgentMessage): The incoming WAREHOUSE_SELECTED message.
        """
        payload = message.payload
        order_id = payload.get("order_id")
        warehouse_id = payload.get("warehouse_id")
        
        if not order_id or not warehouse_id:
            self.logger.error("Invalid WAREHOUSE_SELECTED message payload", payload=payload)
            return

        self.logger.info("Warehouse selected for order", order_id=order_id, warehouse_id=warehouse_id)
        
        try:
            await self._update_order_status(order_id, OrderStatus.PROCESSING)
            
            await self.send_message(
                recipient_agent="carrier_selection_agent",
                message_type=MessageType.CARRIER_SELECTED, # Re-using CARRIER_SELECTED as a request type
                payload={
                    "order_id": order_id,
                    "warehouse_id": warehouse_id,
                    "shipping_address": payload.get("shipping_address"),
                    "package_details": payload.get("package_details")
                }
            )
        except Exception as e:
            self.logger.error("Error handling warehouse selected message", error=str(e), order_id=order_id)

    async def _handle_carrier_selected(self, message: AgentMessage):
        """Handles CARRIER_SELECTED messages, updating order status and sending fulfillment request."

        Args:
            message (AgentMessage): The incoming CARRIER_SELECTED message.
        """
        payload = message.payload
        order_id = payload.get("order_id")
        carrier_id = payload.get("carrier_id")
        estimated_delivery = payload.get("estimated_delivery")

        if not order_id or not carrier_id:
            self.logger.error("Invalid CARRIER_SELECTED message payload", payload=payload)
            return
        
        self.logger.info("Carrier selected for order", order_id=order_id, carrier_id=carrier_id)
        
        try:
            await self._update_order_status(order_id, OrderStatus.CONFIRMED)
            
            await self.send_message(
                recipient_agent="warehouse_management_agent",
                message_type=MessageType.SHIPMENT_CREATED, # Changed to SHIPMENT_CREATED for clarity
                payload={
                    "order_id": order_id,
                    "carrier_id": carrier_id,
                    "estimated_delivery": estimated_delivery,
                    "fulfillment_required": True
                }
            )
        except Exception as e:
            self.logger.error("Error handling carrier selected message", error=str(e), order_id=order_id)

    async def _process_pending_orders(self):
        """Background task to periodically check and process pending orders."

        Monitors orders that have been in PENDING status for too long and sends alerts.
        """
        while not self.shutdown_event.is_set():
            try:
                if not self._db_initialized: 
                    self.logger.warning("Database not initialized, skipping pending order processing.")
                    await asyncio.sleep(int(os.getenv("ORDER_PENDING_CHECK_INTERVAL", "30"))) # Wait before retrying
                    continue

                pending_orders = await self.repository.find_by_status(OrderStatus.PENDING)
                
                for order in pending_orders:
                    pending_timeout_minutes = int(os.getenv("ORDER_PENDING_TIMEOUT_MINUTES", "5"))
                    if datetime.utcnow() - order.created_at > timedelta(minutes=pending_timeout_minutes):
                        self.logger.warning("Order pending too long", order_id=order.id, created_at=order.created_at)
                        
                        await self.send_message(
                            recipient_agent="monitoring_agent",
                            message_type=MessageType.ERROR_DETECTED,
                            payload={
                                "agent_id": self.agent_id,
                                "error_type": "order_pending_timeout",
                                "order_id": order.id,
                                "message": f"Order {order.id} has been pending for too long ({pending_timeout_minutes} minutes)"
                            }
                        )
                
                await asyncio.sleep(int(os.getenv("ORDER_PENDING_CHECK_INTERVAL", "30"))) # Sleep for 30 seconds before next check
            
            except Exception as e:
                self.logger.error("Error in pending orders processing background task", error=str(e))
                await asyncio.sleep(int(os.getenv("ORDER_PENDING_ERROR_RETRY_INTERVAL", "60")))  # Wait longer on error

    async def _monitor_order_timeouts(self):
        """Background task to monitor order processing timeouts."

        Monitors orders that have been in PROCESSING status for too long and sends alerts.
        """
        while not self.shutdown_event.is_set():
            try:
                if not self._db_initialized: 
                    self.logger.warning("Database not initialized, skipping order timeout monitoring.")
                    await asyncio.sleep(int(os.getenv("ORDER_TIMEOUT_CHECK_INTERVAL", "60"))) # Wait before retrying
                    continue

                processing_orders = await self.repository.find_by_status(OrderStatus.PROCESSING)
                
                for order in processing_orders:
                    processing_timeout_minutes = int(os.getenv("ORDER_PROCESSING_TIMEOUT_MINUTES", "30"))
                    if datetime.utcnow() - order.updated_at > timedelta(minutes=processing_timeout_minutes):
                        self.logger.warning("Order processing timeout", order_id=order.id, last_updated=order.updated_at)
                        
                        await self.send_message(
                            recipient_agent="monitoring_agent",
                            message_type=MessageType.ERROR_DETECTED,
                            payload={
                                "agent_id": self.agent_id,
                                "error_type": "order_processing_timeout",
                                "order_id": order.id,
                                "message": f"Order {order.id} processing timeout ({processing_timeout_minutes} minutes)"
                            }
                        )
                
                await asyncio.sleep(int(os.getenv("ORDER_TIMEOUT_CHECK_INTERVAL", "60"))) # Sleep for 60 seconds before next check
            
            except Exception as e:
                self.logger.error("Error in order timeout monitoring background task", error=str(e))
                await asyncio.sleep(int(os.getenv("ORDER_TIMEOUT_ERROR_RETRY_INTERVAL", "120")))  # Wait longer on error


# FastAPI app instance for running the agent as a service
app = FastAPI(title="Order Agent", version="1.0.0", description="Main FastAPI application for the Order Agent.")

# Global agent instance
order_agent: Optional[OrderAgent] = None

@app.on_event("startup")
async def startup_event():
    """Initializes the Order Agent on application startup."

    This function is called by FastAPI when the application starts up.
    It creates and starts the global OrderAgent instance.
    """
    global order_agent
    logger.info("FastAPI startup event triggered.")
    try:
        # Initialize database manager early for all components that might need it
        db_config = DatabaseConfig(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "multi_agent_ecommerce"),
            username=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        if not db_config.password:
            logger.error("Database password environment variable not set.")
            raise ValueError("POSTGRES_PASSWORD environment variable must be set.")
        initialize_database_manager(db_config)

        order_agent = OrderAgent(
            kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )
        await order_agent.start()
        app.mount("/api/v1", order_agent.app)
        logger.info("Order Agent and FastAPI app mounted successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Order Agent during startup: {e}", error=str(e))
        # Depending on desired behavior, could re-raise or set a global error state
        # For now, we'll let it log and potentially crash if critical.

@app.on_event("shutdown")
async def shutdown_event():
    """Cleans up the Order Agent on application shutdown."

    This function is called by FastAPI when the application is shutting down.
    It stops the global OrderAgent instance.
    """
    global order_agent
    logger.info("FastAPI shutdown event triggered.")
    if order_agent:
        await order_agent.stop()
        logger.info("Order Agent stopped successfully.")

if __name__ == "__main__":
    logger.info("Starting Order Agent standalone application.")
    try:
        uvicorn_port = int(os.getenv("ORDER_AGENT_PORT", "8001"))
        uvicorn.run(
            "order_agent:app",
            host="0.0.0.0",
            port=uvicorn_port,
            reload=False,
            log_level=os.getenv("LOG_LEVEL", "info").lower()
        )
    except Exception as e:
        logger.critical(f"Uvicorn failed to start: {e}", error=str(e))
        sys.exit(1)

