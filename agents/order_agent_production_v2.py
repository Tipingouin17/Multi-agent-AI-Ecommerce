
"""
Order Agent - Production Ready with Full Database Integration
Manages complete order lifecycle with PostgreSQL persistence
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

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

# Import base agent and models
from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.db_manager import DBManager
from shared.db_helpers import DatabaseHelper
from shared.models import OrderDB, OrderItemDB, OrderStatus, CustomerDB

# Pydantic Models for API
class OrderItemRequest(BaseModel):
    """Order item request model"""
    product_id: str
    quantity: int
    unit_price: Decimal

class OrderRequest(BaseModel):
    """Order creation request model"""
    customer_id: str
    items: List[OrderItemRequest]
    shipping_address: Dict[str, str]
    billing_address: Optional[Dict[str, str]] = None
    notes: Optional[str] = None

class OrderResponse(BaseModel):
    """Order response model"""
    id: UUID
    customer_id: str
    status: str
    total_amount: Decimal
    created_at: datetime
    items: List[Dict[str, Any]]

class OrderAgent(BaseAgent):
    """
    Production-ready Order Agent with full database integration
    Manages the complete order lifecycle, including creation, retrieval, updates, and cancellations,
    with robust database persistence using PostgreSQL and FastAPI for API exposure.
    """
    
    def __init__(self):
        """
        Initializes the OrderAgent, setting up agent ID, type, database connection,
        FastAPI application, and routes.
        """
        super().__init__(
            agent_id="order_agent",
            agent_type="order_management"
        )
        
        logger.info("Order Agent initialized")
        
        # Database setup
        self.DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/ecommerce")
        self.db_manager = DBManager(self.DATABASE_URL)
        self.db_helper = DatabaseHelper()
        self._db_initialized = False
        
        # FastAPI app
        self.app = FastAPI(title="Order Agent API")
        self._setup_routes()
        
        # Initialize database connection asynchronously
        asyncio.create_task(self._init_db_connection())

    async def _init_db_connection(self):
        """
        Initializes the database connection and sets the _db_initialized flag.
        """
        try:
            await self.db_manager.connect()
            self._db_initialized = True
            logger.info("Database connection established for Order Agent.")
        except Exception as e:
            logger.error(f"Failed to connect to database for Order Agent: {e}")
            self._db_initialized = False

    def _setup_routes(self):
        """Setup FastAPI routes for the Order Agent API."""
        
        @self.app.get("/health", summary="Health Check")
        async def health_check():
            """Returns the health status of the Order Agent and its database connection."""
            return {
                "status": "healthy",
                "agent_id": self.agent_id,
                "database_connected": self._db_initialized
            }
        
        @self.app.get("/", summary="Root Endpoint")
        async def root():
            """Root endpoint for the Order Agent API."""
            return {"message": "Order Agent API is running"}

        @self.app.post("/orders", response_model=OrderResponse, status_code=201, summary="Create New Order")
        async def create_order_endpoint(order: OrderRequest):
            """Creates a new order with full database persistence and publishes an ORDER_CREATED event."""
            if not self._db_initialized:
                logger.warning("Attempted to create order but database not initialized.")
                raise HTTPException(status_code=503, detail="Database not initialized. Please try again later.")
            try:
                order_id = await self.create_order(order)
                order_data = await self.get_order_by_id(order_id)
                if not order_data:
                    raise HTTPException(status_code=500, detail="Failed to retrieve created order.")
                return order_data
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error creating order via API: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
        
        @self.app.get("/orders", response_model=List[OrderResponse], summary="Get All Orders")
        async def get_orders_endpoint(skip: int = 0, limit: int = 100, status: Optional[str] = None):
            """Retrieves a list of orders with optional pagination and status filtering."""
            if not self._db_initialized:
                logger.warning("Attempted to get orders but database not initialized.")
                return []
            try:
                filters = {"status": status} if status else None
                orders = await self.get_orders(skip, limit, filters)
                return orders
            except Exception as e:
                logger.error(f"Error getting orders via API: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
        
        @self.app.get("/orders/{order_id}", response_model=OrderResponse, summary="Get Order by ID")
        async def get_order_endpoint(order_id: UUID):
            """Retrieves a single order by its unique ID."""
            if not self._db_initialized:
                logger.warning(f"Attempted to get order {order_id} but database not initialized.")
                raise HTTPException(status_code=503, detail="Database not initialized. Please try again later.")
            try:
                order = await self.get_order_by_id(order_id)
                if not order:
                    raise HTTPException(status_code=404, detail="Order not found")
                return order
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting order {order_id} via API: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
        
        @self.app.patch("/orders/{order_id}/status", response_model=OrderResponse, summary="Update Order Status")
        async def update_order_status_endpoint(order_id: UUID, status: OrderStatus):
            """Updates the status of an existing order and publishes an ORDER_STATUS_UPDATED event."""
            if not self._db_initialized:
                logger.warning(f"Attempted to update status for order {order_id} but database not initialized.")
                raise HTTPException(status_code=503, detail="Database not initialized. Please try again later.")
            try:
                # First, get the order to ensure it exists and to return its full data
                existing_order = await self.get_order_by_id(order_id)
                if not existing_order:
                    raise HTTPException(status_code=404, detail="Order not found")
                
                updated_order_data = await self.update_status(order_id, status)
                if not updated_order_data:
                    raise HTTPException(status_code=500, detail="Failed to update order status.")
                return updated_order_data
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error updating order status for {order_id} via API: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
        
        @self.app.delete("/orders/{order_id}", summary="Cancel Order")
        async def cancel_order_endpoint(order_id: UUID, reason: str):
            """Cancels an order by ID and publishes an ORDER_CANCELLED event."""
            if not self._db_initialized:
                logger.warning(f"Attempted to cancel order {order_id} but database not initialized.")
                raise HTTPException(status_code=503, detail="Database not initialized. Please try again later.")
            try:
                success = await self.cancel_order(order_id, reason)
                if not success:
                    raise HTTPException(status_code=404, detail="Order not found or already cancelled")
                return {"id": order_id, "status": OrderStatus.CANCELLED.value, "reason": reason}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error cancelling order {order_id} via API: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

    async def create_order(self, order_request: OrderRequest) -> UUID:
        """
        Creates a new order in the database, including its items, and publishes an ORDER_CREATED event.
        
        Args:
            order_request (OrderRequest): The request object containing order details.
        
        Returns:
            UUID: The ID of the newly created order.
        
        Raises:
            Exception: If the database is not initialized or any database operation fails.
        """
        if not self._db_initialized:
            logger.error("Database not initialized when calling create_order.")
            raise Exception("Database not initialized")
        
        try:
            async with self.db_manager.get_session() as session:
                # Calculate total amount
                total_amount = sum(item.quantity * item.unit_price for item in order_request.items)
                
                order_id = uuid4()
                # Create order
                order_data = {
                    "id": order_id,
                    "customer_id": order_request.customer_id,
                    "status": OrderStatus.PENDING.value,
                    "total_amount": total_amount,
                    "shipping_address": order_request.shipping_address,
                    "billing_address": order_request.billing_address or order_request.shipping_address,
                    "notes": order_request.notes,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                order = await self.db_helper.create(session, OrderDB, order_data)
                
                # Create order items
                for item in order_request.items:
                    item_data = {
                        "id": uuid4(),
                        "order_id": order.id,
                        "product_id": item.product_id,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "total_price": item.quantity * item.unit_price,
                        "created_at": datetime.utcnow()
                    }
                    await self.db_helper.create(session, OrderItemDB, item_data)
                
                await session.commit()
                
                logger.info(f"Created order {order.id} with {len(order_request.items)} items for customer {order_request.customer_id}")
                
                # Publish order created event
                await self.send_message(
                    recipient_agent="inventory_agent",
                    message_type=MessageType.ORDER_CREATED,
                    payload={
                        "order_id": str(order.id),
                        "customer_id": order_request.customer_id,
                        "items": [
                            {
                                "product_id": item.product_id,
                                "quantity": item.quantity,
                                "unit_price": float(item.unit_price)
                            }
                            for item in order_request.items
                        ],
                        "total_amount": float(total_amount)
                    }
                )
                
                return order.id
                
        except Exception as e:
            logger.error(f"Failed to create order for customer {order_request.customer_id}: {e}", exc_info=True)
            raise
    
    async def get_orders(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[OrderResponse]:
        """
        Retrieves a list of orders from the database with pagination and optional filtering.
        
        Args:
            skip (int): The number of records to skip.
            limit (int): The maximum number of records to return.
            filters (Optional[Dict[str, Any]]): Optional dictionary of filters to apply (e.g., {"status": "PENDING"}).
        
        Returns:
            List[OrderResponse]: A list of order data as OrderResponse objects.
        
        Raises:
            Exception: If the database is not initialized or any database operation fails.
        """
        if not self._db_initialized:
            logger.warning("Database not initialized when calling get_orders.")
            return []
        
        try:
            async with self.db_manager.get_session() as session:
                orders_db = await self.db_helper.get_all(
                    session,
                    OrderDB,
                    skip=skip,
                    limit=limit,
                    filters=filters
                )
                
                result_orders = []
                for order_db in orders_db:
                    order_items_db = await self.db_helper.get_all(session, OrderItemDB, filters={"order_id": order_db.id})
                    items_data = [
                        {
                            "product_id": item.product_id,
                            "quantity": item.quantity,
                            "unit_price": item.unit_price,
                            "total_price": item.total_price
                        }
                        for item in order_items_db
                    ]
                    result_orders.append(OrderResponse(
                        id=order_db.id,
                        customer_id=order_db.customer_id,
                        status=order_db.status,
                        total_amount=order_db.total_amount,
                        created_at=order_db.created_at,
                        items=items_data
                    ))
                return result_orders
                
        except Exception as e:
            logger.error(f"Failed to retrieve orders: {e}", exc_info=True)
            raise
    
    async def get_order_by_id(self, order_id: UUID) -> Optional[OrderResponse]:
        """
        Retrieves a single order by its ID from the database.
        
        Args:
            order_id (UUID): The unique ID of the order.
        
        Returns:
            Optional[OrderResponse]: The order data as an OrderResponse object if found, otherwise None.
        
        Raises:
            Exception: If the database is not initialized or any database operation fails.
        """
        if not self._db_initialized:
            logger.warning(f"Database not initialized when calling get_order_by_id for order {order_id}.")
            return None
        
        try:
            async with self.db_manager.get_session() as session:
                order_db = await self.db_helper.get_by_id(session, OrderDB, order_id)
                if not order_db:
                    return None
                
                order_items_db = await self.db_helper.get_all(session, OrderItemDB, filters={"order_id": order_db.id})
                items_data = [
                    {
                        "product_id": item.product_id,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "total_price": item.total_price
                    }
                    for item in order_items_db
                ]
                
                return OrderResponse(
                    id=order_db.id,
                    customer_id=order_db.customer_id,
                    status=order_db.status,
                    total_amount=order_db.total_amount,
                    created_at=order_db.created_at,
                    items=items_data
                )
                
        except Exception as e:
            logger.error(f"Failed to retrieve order {order_id}: {e}", exc_info=True)
            raise

    async def update_status(self, order_id: UUID, new_status: OrderStatus) -> Optional[OrderResponse]:
        """
        Updates the status of an order in the database and publishes an ORDER_STATUS_UPDATED event.
        
        Args:
            order_id (UUID): The ID of the order to update.
            new_status (OrderStatus): The new status for the order.
        
        Returns:
            Optional[OrderResponse]: The updated order data as an OrderResponse object if successful, otherwise None.
        
        Raises:
            Exception: If the database is not initialized or any database operation fails.
        """
        if not self._db_initialized:
            logger.warning(f"Database not initialized when calling update_status for order {order_id}.")
            return None
        
        try:
            async with self.db_manager.get_session() as session:
                order_db = await self.db_helper.get_by_id(session, OrderDB, order_id)
                if not order_db:
                    logger.warning(f"Order {order_id} not found for status update.")
                    return None
                
                # Prevent updating to the same status
                if order_db.status == new_status.value:
                    logger.info(f"Order {order_id} already has status {new_status.value}. No update needed.")
                    return await self.get_order_by_id(order_id)

                updated_data = {"status": new_status.value, "updated_at": datetime.utcnow()}
                updated_order_db = await self.db_helper.update(session, OrderDB, order_id, updated_data)
                await session.commit()
                
                if updated_order_db:
                    logger.info(f"Order {order_id} status updated to {new_status.value}.")
                    
                    # Publish order status updated event
                    await self.send_message(
                        recipient_agent="notification_agent", # Or other relevant agent
                        message_type=MessageType.ORDER_STATUS_UPDATED,
                        payload={
                            "order_id": str(order_id),
                            "old_status": order_db.status,
                            "new_status": new_status.value,
                            "customer_id": updated_order_db.customer_id
                        }
                    )
                    return await self.get_order_by_id(order_id)
                return None
                
        except Exception as e:
            logger.error(f"Failed to update status for order {order_id} to {new_status.value}: {e}", exc_info=True)
            raise

    async def cancel_order(self, order_id: UUID, reason: str) -> bool:
        """
        Cancels an order in the database by updating its status to CANCELLED and publishes an ORDER_CANCELLED event.
        
        Args:
            order_id (UUID): The ID of the order to cancel.
            reason (str): The reason for cancellation.
        
        Returns:
            bool: True if the order was successfully cancelled, False otherwise.
        
        Raises:
            Exception: If the database is not initialized or any database operation fails.
        """
        if not self._db_initialized:
            logger.warning(f"Database not initialized when calling cancel_order for order {order_id}.")
            return False
        
        try:
            async with self.db_manager.get_session() as session:
                order_db = await self.db_helper.get_by_id(session, OrderDB, order_id)
                if not order_db:
                    logger.warning(f"Order {order_id} not found for cancellation.")
                    return False
                
                if order_db.status == OrderStatus.CANCELLED.value:
                    logger.info(f"Order {order_id} is already cancelled.")
                    return True

                updated_data = {"status": OrderStatus.CANCELLED.value, "notes": f"Cancelled: {reason}", "updated_at": datetime.utcnow()}
                updated_order_db = await self.db_helper.update(session, OrderDB, order_id, updated_data)
                await session.commit()
                
                if updated_order_db:
                    logger.info(f"Order {order_id} cancelled due to: {reason}.")
                    
                    # Publish order cancelled event
                    await self.send_message(
                        recipient_agent="inventory_agent", # Or other relevant agent
                        message_type=MessageType.ORDER_CANCELLED,
                        payload={
                            "order_id": str(order_id),
                            "customer_id": updated_order_db.customer_id,
                            "reason": reason
                        }
                    )
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}", exc_info=True)
            raise

    async def process_message(self, message: AgentMessage):
        """
        Processes incoming messages from other agents or services.
        
        Args:
            message (AgentMessage): The incoming message to process.
        """
        logger.info(f"Order Agent received message: {message.message_type} from {message.sender_id}")
        
        try:
            if message.message_type == MessageType.ORDER_REQUEST:
                # Example: Another agent requests order creation
                order_request_payload = message.payload
                # Assuming payload directly maps to OrderRequest for simplicity
                order_request = OrderRequest(**order_request_payload)
                order_id = await self.create_order(order_request)
                logger.info(f"Processed ORDER_REQUEST, created order {order_id}")
                # Optionally send a confirmation message back
                await self.send_message(
                    recipient_agent=message.sender_id,
                    message_type=MessageType.ORDER_CONFIRMATION,
                    payload={"original_message_id": message.message_id, "order_id": str(order_id), "status": "created"}
                )
            
            elif message.message_type == MessageType.PAYMENT_SUCCESS:
                # Example: Payment agent confirms payment success, update order status
                order_id = UUID(message.payload.get("order_id"))
                payment_details = message.payload.get("payment_details")
                await self.update_status(order_id, OrderStatus.PAID)
                logger.info(f"Processed PAYMENT_SUCCESS for order {order_id}. Payment details: {payment_details}")
                
            elif message.message_type == MessageType.SHIPPING_UPDATE:
                # Example: Shipping agent provides update, log it or update order notes
                order_id = UUID(message.payload.get("order_id"))
                shipping_status = message.payload.get("shipping_status")
                tracking_number = message.payload.get("tracking_number")
                logger.info(f"Order {order_id} shipping update: {shipping_status}, Tracking: {tracking_number}")
                # Potentially update order status to SHIPPED or DELIVERED
                if shipping_status == "SHIPPED":
                    await self.update_status(order_id, OrderStatus.SHIPPED)
                elif shipping_status == "DELIVERED":
                    await self.update_status(order_id, OrderStatus.DELIVERED)

            else:
                logger.warning(f"Unhandled message type: {message.message_type} from {message.sender_id}")
        except Exception as e:
            logger.error(f"Error processing message {message.message_id} of type {message.message_type}: {e}", exc_info=True)
            # Optionally send an error message back to the sender
            await self.send_message(
                recipient_agent=message.sender_id,
                message_type=MessageType.ERROR,
                payload={
                    "original_message_id": message.message_id,
                    "error": str(e),
                    "description": f"Failed to process message of type {message.message_type}"
                }
            )
    
    async def initialize(self):
        """Initialize agent-specific components"""
        await super().initialize()
        logger.info(f"{self.agent_name} initialized successfully")
    
    async def cleanup(self):
        """Cleanup agent resources"""
        try:
            if hasattr(self, 'db_manager') and self.db_manager:
                await self.db_manager.disconnect()
            await super().cleanup()
            logger.info(f"{self.agent_name} cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process order-specific business logic
        
        Args:
            data: Dictionary containing operation type and parameters
            
        Returns:
            Dictionary with processing results
        """
        try:
            operation = data.get("operation", "create_order")
            
            if operation == "create_order":
                order_data = data.get("order_data")
                order = await self.create_order(order_data)
                return {"status": "success", "order": order}
            
            elif operation == "update_order":
                order_id = data.get("order_id")
                updates = data.get("updates")
                order = await self.update_order(order_id, updates)
                return {"status": "success", "order": order}
            
            elif operation == "cancel_order":
                order_id = data.get("order_id")
                reason = data.get("reason", "customer_request")
                result = await self.cancel_order(order_id, reason)
                return {"status": "success", "result": result}
            
            else:
                return {"status": "error", "message": f"Unknown operation: {operation}"}
                
        except Exception as e:
            logger.error(f"Error in process_business_logic: {e}")
            return {"status": "error", "message": str(e)}


# Uvicorn runner for FastAPI
if __name__ == "__main__":
    import uvicorn
    agent = OrderAgent()
    # Use environment variable for port, default to 8000
    port = int(os.getenv("ORDER_AGENT_PORT", 8000))
    logger.info(f"Starting Order Agent API on port {port}")
    uvicorn.run(agent.app, host="0.0.0.0", port=port)

