"""
Order Agent - Production Ready with Full Database Integration
Manages complete order lifecycle with PostgreSQL persistence
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4

from shared.db_helpers import DatabaseHelper

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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

# Import base agent and models
from shared.base_agent import BaseAgent, MessageType, AgentMessage
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
    id: str
    customer_id: str
    status: str
    total_amount: Decimal
    created_at: datetime
    items: List[Dict[str, Any]]

class OrderAgent(BaseAgent):
    """
    Production-ready Order Agent with full database integration
    """
    
    def __init__(self):
        super().__init__(
            agent_id="order_agent",
            agent_type="order_management"
        )
        
        logger.info("Order Agent initialized")
        
        # FastAPI app
        self.app = FastAPI(title="Order Agent API")
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "agent_id": self.agent_id,
                "database_connected": self._db_initialized
            }
        
        @self.app.post("/orders", response_model=OrderResponse)
        async def create_order(order: OrderRequest):
            """Create new order with database persistence"""
            try:
                order_id = await self.create_order(order)
                order_data = await self.get_order_by_id(order_id)
                return order_data
            except Exception as e:
                logger.error(f"Error creating order: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/orders", response_model=List[OrderResponse])
        async def get_orders(skip: int = 0, limit: int = 100, status: Optional[str] = None):
            """Get orders with optional status filter"""
            try:
                filters = {"status": status} if status else None
                orders = await self.get_orders(skip, limit, filters)
                return orders
            except Exception as e:
                logger.error(f"Error getting orders: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/orders/{order_id}", response_model=OrderResponse)
        async def get_order(order_id: str):
            """Get order by ID"""
            try:
                order = await self.get_order_by_id(order_id)
                if not order:
                    raise HTTPException(status_code=404, detail="Order not found")
                return order
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting order: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.patch("/orders/{order_id}/status")
        async def update_order_status(order_id: str, status: str):
            """Update order status"""
            try:
                success = await self.update_status(order_id, status)
                if not success:
                    raise HTTPException(status_code=404, detail="Order not found")
                return {"id": order_id, "status": status}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error updating order status: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/orders/{order_id}")
        async def cancel_order(order_id: str, reason: str):
            """Cancel order"""
            try:
                success = await self.cancel_order(order_id, reason)
                if not success:
                    raise HTTPException(status_code=404, detail="Order not found")
                return {"id": order_id, "status": "cancelled", "reason": reason}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error cancelling order: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def create_order(self, order_request: OrderRequest) -> str:
        """
        Create new order with full database persistence
        
        Args:
            order_request: Order creation request
        
        Returns:
            Order ID
        """
        if not self._db_initialized:
            raise Exception("Database not initialized")
        
        try:
            async with self.db_manager.get_session() as session:
                # Calculate total amount
                total_amount = sum(item.quantity * item.unit_price for item in order_request.items)
                
                # Create order
                order_data = {
                    "id": uuid4(),
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
                
                logger.info(f"Created order {order.id} with {len(order_request.items)} items")
                
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
                                "quantity": item.quantity
                            }
                            for item in order_request.items
                        ],
                        "total_amount": float(total_amount)
                    }
                )
                
                return str(order.id)
                
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            raise
    
    async def get_orders(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get orders with pagination and filtering
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            filters: Optional filters
        
        Returns:
            List of orders
        """
        if not self._db_initialized:
            if not self._db_initialized:
            return []
        
        async with self.db_manager.get_session() as session:
            records = await self.db_helper.get_all(session, OrderDB, limit=100)
            return [self.db_helper.to_dict(r) for r in records]
        
        try:
            async with self.db_manager.get_session() as session:
                orders = await self.db_helper.get_all(
                    session,
                    OrderDB,
                    skip=skip,
                    limit=limit,
                    filters=filters
                )
                
                return [self.db_helper.to_dict(order) for order in orders]
                
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            if not self._db_initialized:
            return []
        
        async with self.db_manager.get_session() as session:
            records = await self.db_helper.get_all(session, OrderDB, limit=100)
            return [self.db_helper.to_dict(r) for r in records]
    
    async def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get order by ID
        
        Args:
            order_id: Order ID
        
        Returns:
            Order data or None
        """
        if not self._db_initialized:
            if not self._db_initialized:
            return None
        
        async with self.db_manager.get_session() as session:
            record = await self.db_helper.get_by_id(session, OrderDB, record_id)
            return self.db_helper.to_dict(record) if record else None
        
        try:
            async with self.db_manager.get_session() as session:
                order = await self.db_helper.get_by_id(session, OrderDB, order_id)
                
                if order:
                    return self.db_helper.to_dict(order)
                if not self._db_initialized:
            return None
        
        async with self.db_manager.get_session() as session:
            record = await self.db_helper.get_by_id(session, OrderDB, record_id)
            return self.db_helper.to_dict(record) if record else None
                
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            if not self._db_initialized:
            return None
        
        async with self.db_manager.get_session() as session:
            record = await self.db_helper.get_by_id(session, OrderDB, record_id)
            return self.db_helper.to_dict(record) if record else None
    
    async def update_status(self, order_id: str, status: str) -> bool:
        """
        Update order status
        
        Args:
            order_id: Order ID
            status: New status
        
        Returns:
            True if updated, False if not found
        """
        if not self._db_initialized:
            return False
        
        try:
            async with self.db_manager.get_session() as session:
                order = await self.db_helper.update_by_id(
                    session,
                    OrderDB,
                    order_id,
                    {"status": status}
                )
                
                if order:
                    await session.commit()
                    
                    logger.info(f"Updated order {order_id} status to {status}")
                    
                    # Publish status update event
                    await self.send_message(
                        recipient_agent="notification_agent",
                        message_type=MessageType.ORDER_STATUS_UPDATED,
                        payload={
                            "order_id": order_id,
                            "status": status,
                            "updated_at": datetime.utcnow().isoformat()
                        }
                    )
                    
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Error updating order {order_id} status: {e}")
            return False
    
    async def cancel_order(self, order_id: str, reason: str) -> bool:
        """
        Cancel order
        
        Args:
            order_id: Order ID
            reason: Cancellation reason
        
        Returns:
            True if cancelled, False if not found
        """
        if not self._db_initialized:
            return False
        
        try:
            async with self.db_manager.get_session() as session:
                order = await self.db_helper.update_by_id(
                    session,
                    OrderDB,
                    order_id,
                    {
                        "status": OrderStatus.CANCELLED.value,
                        "notes": f"Cancelled: {reason}"
                    }
                )
                
                if order:
                    await session.commit()
                    
                    logger.info(f"Cancelled order {order_id}: {reason}")
                    
                    # Publish cancellation event
                    await self.send_message(
                        recipient_agent="inventory_agent",
                        message_type=MessageType.ORDER_CANCELLED,
                        payload={
                            "order_id": order_id,
                            "reason": reason,
                            "cancelled_at": datetime.utcnow().isoformat()
                        }
                    )
                    
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    async def process_message(self, message: AgentMessage):
        """Process incoming Kafka messages"""
        logger.info(f"Processing message: {message.message_type}")
        
        if message.message_type == MessageType.INVENTORY_RESERVED:
            await self.handle_inventory_reserved(message.payload)
        elif message.message_type == MessageType.PAYMENT_CONFIRMED:
            await self.handle_payment_confirmed(message.payload)
        elif message.message_type == MessageType.SHIPMENT_CREATED:
            await self.handle_shipment_created(message.payload)
        else:
            logger.warning(f"Unknown message type: {message.message_type}")
    
    async def handle_inventory_reserved(self, payload: Dict):
        """Handle inventory reserved event"""
        order_id = payload.get("order_id")
        logger.info(f"Inventory reserved for order {order_id}")
        await self.update_status(order_id, OrderStatus.CONFIRMED.value)
    
    async def handle_payment_confirmed(self, payload: Dict):
        """Handle payment confirmed event"""
        order_id = payload.get("order_id")
        logger.info(f"Payment confirmed for order {order_id}")
        await self.update_status(order_id, OrderStatus.PROCESSING.value)
    
    async def handle_shipment_created(self, payload: Dict):
        """Handle shipment created event"""
        order_id = payload.get("order_id")
        logger.info(f"Shipment created for order {order_id}")
        await self.update_status(order_id, OrderStatus.SHIPPED.value)

# Create agent instance
agent = OrderAgent()
app = agent.app

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Order Agent on port 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)

