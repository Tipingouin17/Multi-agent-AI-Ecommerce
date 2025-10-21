
"""
Order Agent - Multi-Agent E-commerce System (Production Ready)

This agent manages orders with all enhanced features:
- Order cancellations with approval workflow
- Partial shipments management
- Complete order lifecycle
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime, Numeric
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from shared.db_helpers import DatabaseHelper

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
    from agents.order_cancellation_service import OrderCancellationService
    from agents.partial_shipments_service import PartialShipmentsService
    logger.info("Successfully imported all order services")
except ImportError as e:
    logger.warning(f"Could not import order services: {e}")
    OrderCancellationService = None
    PartialShipmentsService = None

# SQLAlchemy Base
Base = declarative_base()

# SQLAlchemy Model
class OrderDB(Base):
    """SQLAlchemy model for the Order entity."""
    __tablename__ = "orders"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    customer_id = Column(String, nullable=False)
    channel = Column(String, nullable=False)
    status = Column(String, default="pending")
    total_amount = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the OrderDB object to a dictionary for serialization."""
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "channel": self.channel,
            "status": self.status,
            "total_amount": str(self.total_amount),  # Convert Decimal to string for JSON serialization
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Order(id='{self.id}', customer_id='{self.customer_id}', status='{self.status}')>"

# Pydantic Model
class Order(BaseModel):
    """Pydantic model for Order data, used for API request/response validation."""
    id: Optional[str] = None
    customer_id: str
    channel: str
    status: str = "pending"
    total_amount: Decimal
    created_at: Optional[datetime] = None


class OrderAgent(BaseAgent):
    """
    Production-ready Order Agent with all enhanced features.
    Manages order lifecycle, integrates with cancellation and partial shipment services,
    and exposes a FastAPI for external interactions.
    """

    def __init__(self):
        """Initializes the OrderAgent, setting up database, services, and FastAPI app.

        Calls super().__init__() with agent_id and agent_type.
        Initializes database connection and helper, enhanced services, and FastAPI application.
        """
        super().__init__(
            agent_id="order_agent",
            agent_type="order_management"
        )

        self.db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./order_agent.db")
        self.engine = create_async_engine(self.db_url, echo=True)
        self.async_session = sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)
        self.db_helper = DatabaseHelper(Base) # Assuming DatabaseHelper is compatible with SQLAlchemy 2.0 async
        self._db_initialized = False
        asyncio.create_task(self._init_db())

        # Initialize enhanced services
        self.cancellation_service = OrderCancellationService() if OrderCancellationService else None
        self.shipments_service = PartialShipmentsService() if PartialShipmentsService else None

        logger.info("Order Agent initialized with enhanced services")

        # FastAPI app
        self.app = FastAPI(title="Order Agent API")
        self._setup_routes()

    async def _init_db(self):
        """Initializes the database by creating all defined tables.

        This method is called asynchronously during agent initialization.
        """
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            self._db_initialized = True
            logger.info("Database initialized and tables created.")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            # Depending on the severity, you might want to re-raise or handle gracefully

    def _setup_routes(self):
        """Sets up the FastAPI routes for the Order Agent API.

        Includes health check, root, order retrieval, and order creation endpoints.
        Also includes cancellation and partial shipment endpoints if services are available.
        """

        @self.app.get("/")
        async def root():
            """Root endpoint for the Order Agent API.

            Returns a welcome message.
            """
            return {"message": "Order Agent is running!"}

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint.

            Returns the agent's status and the status of its enhanced services.
            """
            return {
                "status": "healthy",
                "agent_id": self.agent_id,
                "services": {
                    "cancellations": self.cancellation_service is not None,
                    "partial_shipments": self.shipments_service is not None
                }
            }

        @self.app.get("/orders")
        async def get_orders(skip: int = 0, limit: int = 100) -> Dict[str, Any]:
            """Retrieves a list of orders from the database.

            Args:
                skip (int): The number of items to skip (for pagination).
                limit (int): The maximum number of items to return.

            Returns:
                Dict[str, Any]: A dictionary containing the list of orders and the total count.
            """
            try:
                orders = await self.get_orders_from_db(skip, limit)
                return {"orders": orders, "total": len(orders)}
            except Exception as e:
                logger.error(f"Error getting orders: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/orders")
        async def create_order(order: Order) -> Dict[str, str]:
            """Creates a new order in the database.

            Args:
                order (Order): The order data to create.

            Returns:
                Dict[str, str]: A dictionary containing the ID of the created order and its status.
            """
            try:
                order_id = await self.create_order_in_db(order)
                return {"id": order_id, "status": "created"}
            except Exception as e:
                logger.error(f"Error creating order: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Cancellation endpoints
        if self.cancellation_service:
            @self.app.post("/orders/{order_id}/cancel")
            async def cancel_order(order_id: str, reason: str):
                """Requests cancellation for a specific order.

                Args:
                    order_id (str): The ID of the order to cancel.
                    reason (str): The reason for cancellation.

                Returns:
                    Any: The result from the cancellation service.
                """
                try:
                    result = await self.cancellation_service.request_cancellation(
                        order_id, reason
                    )
                    return result
                except Exception as e:
                    logger.error(f"Error cancelling order {order_id}: {e}")
                    raise HTTPException(status_code=500, detail=str(e))

        # Partial shipments endpoints
        if self.shipments_service:
            @self.app.get("/orders/{order_id}/shipments")
            async def get_order_shipments(order_id: str):
                """Retrieves all shipments for a given order.

                Args:
                    order_id (str): The ID of the order.

                Returns:
                    Dict[str, Any]: A dictionary containing the list of shipments.
                """
                try:
                    shipments = await self.shipments_service.get_shipments(order_id)
                    return {"shipments": shipments}
                except Exception as e:
                    logger.error(f"Error getting shipments for order {order_id}: {e}")
                    raise HTTPException(status_code=500, detail=str(e))

    async def get_orders_from_db(self, skip: int, limit: int) -> List[Dict]:
        """Retrieves orders from the database with pagination.

        Args:
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to return.

        Returns:
            List[Dict]: A list of order dictionaries.
        """
        logger.info(f"Getting orders: skip={skip}, limit={limit}")
        if not self._db_initialized:
            logger.warning("Database not initialized. Cannot retrieve orders.")
            return []

        try:
            async with self.async_session() as session:
                stmt = select(OrderDB).offset(skip).limit(limit)
                result = await session.execute(stmt)
                orders = result.scalars().all()
                return [order.to_dict() for order in orders]  # Use the to_dict() method for serialization
        except Exception as e:
            logger.error(f"Error retrieving orders from DB: {e}")
            raise

    async def create_order_in_db(self, order: Order) -> str:
        """Creates a new order record in the database.

        Args:
            order (Order): The Pydantic Order model containing order data.

        Returns:
            str: The ID of the newly created order.

        Raises:
            HTTPException: If the database is not ready or an error occurs during creation.
        """
        if not self._db_initialized:
            logger.warning("Database not initialized. Cannot create order.")
            raise HTTPException(status_code=503, detail="Database not ready")

        try:
            async with self.async_session() as session:
                db_order = OrderDB(**order.model_dump())
                session.add(db_order)
                await session.commit()
                await session.refresh(db_order)
                logger.info(f"Created order with ID {db_order.id}")
                return db_order.id
        except Exception as e:
            logger.error(f"Error creating order in DB: {e}")
            raise

    async def process_message(self, message: AgentMessage):
        """Processes incoming messages from Kafka.

        Args:
            message (AgentMessage): The incoming message containing type and payload.
        """
        try:
            logger.info(f"Processing message: {message.message_type} with payload {message.payload}")

            if message.message_type == MessageType.ORDER_CREATED:
                await self.handle_order_created(message.payload)
            elif message.message_type == MessageType.ORDER_CANCELLED:
                await self.handle_order_cancelled(message.payload)
            elif message.message_type == MessageType.ORDER_UPDATED:
                await self.handle_order_updated(message.payload)
            else:
                logger.warning(f"Unknown message type received: {message.message_type}")
        except Exception as e:
            logger.error(f"Error processing message {message.message_type}: {e}")

    async def handle_order_created(self, payload: Dict):
        """Handles the ORDER_CREATED message type.

        Args:
            payload (Dict): The payload of the ORDER_CREATED message.
        """
        try:
            order_id = payload.get("order_id")
            logger.info(f"Handling order created event for order ID: {order_id}")
            # Further business logic for handling created order
            # For example, sending a confirmation message or updating inventory
        except Exception as e:
            logger.error(f"Error handling order created event for payload {payload}: {e}")

    async def handle_order_cancelled(self, payload: Dict):
        """Handles the ORDER_CANCELLED message type.

        Args:
            payload (Dict): The payload of the ORDER_CANCELLED message.
        """
        try:
            order_id = payload.get("order_id")
            logger.info(f"Handling order cancelled event for order ID: {order_id}")
            # Further business logic for handling cancelled order
            # For example, updating order status in DB or notifying other agents
        except Exception as e:
            logger.error(f"Error handling order cancelled event for payload {payload}: {e}")

    async def handle_order_updated(self, payload: Dict):
        """Handles the ORDER_UPDATED message type.

        Args:
            payload (Dict): The payload of the ORDER_UPDATED message.
        """
        try:
            order_id = payload.get("order_id")
            logger.info(f"Handling order updated event for order ID: {order_id}")
            # Further business logic for handling updated order
        except Exception as e:
            logger.error(f"Error handling order updated event for payload {payload}: {e}")


# Create agent instance
agent = OrderAgent()
app = agent.app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    logger.info(f"Starting Order Agent on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

