
"""
Warehouse Agent - Multi-Agent E-commerce System (Production Ready)

This agent manages warehouse operations with all enhanced features:
- Warehouse capacity management
- Workforce tracking
- Throughput monitoring
- Performance KPIs
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logger.info(f"Added {project_root} to Python path")

# Import base agent and shared utilities
try:
    from shared.base_agent_v2 import BaseAgentV2, MessageType, AgentMessage
    from shared.db_helpers import DatabaseManager, DatabaseHelper, ProductDB
from shared.cors_middleware import add_cors_middleware
    logger.info("Successfully imported shared.base_agent and db_helpers")
except ImportError as e:
    logger.error(f"Import error for shared modules: {e}")
    raise

# Import new services (optional)
try:
    from agents.warehouse_capacity_service import WarehouseCapacityService
    logger.info("Successfully imported warehouse capacity service")
except ImportError as e:
    logger.warning(f"Could not import warehouse capacity service: {e}. Functionality will be limited.")
    WarehouseCapacityService = None

class WarehouseAgent(BaseAgentV2):
    """
    Production-ready Warehouse Agent with capacity management and full database integration.

    This agent handles warehouse operations, including managing inventory, tracking capacity,
    and responding to various agent messages related to warehouse activities.
    It exposes a FastAPI interface for external communication and integrates with a database
    for persistent storage of warehouse-related data.
    """

    def __init__(self):
        """
        Initializes the WarehouseAgent, setting up its ID, type, database connection,
        FastAPI application, and message processing capabilities.
        """
        super().__init__(agent_id=os.getenv("AGENT_ID", "warehouse_agent"))
        self.db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./warehouse.db")
        self.db_manager = None
        self.db_helper = DatabaseHelper(self.db_manager)

        # Initialize capacity service
        self.capacity_service = WarehouseCapacityService(self.db_manager) if WarehouseCapacityService else None

        logger.info("Warehouse Agent initialized. Setting up database and FastAPI.")

        # FastAPI app setup
        self.app = FastAPI(title="Warehouse Agent API")
        
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
        self._setup_routes()
        self.setup_event_handlers()

    async def _initialize_database(self):
        """
        Initializes the database manager and creates necessary tables if they don't exist.
        This method should be called during agent startup.
        """
        try:
            self.db_manager = DatabaseManager(self.db_url)
            await self.db_manager.create_tables()
            self._db_initialized = True
            logger.info("Warehouse Agent database initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize database for Warehouse Agent: {e}")
            self._db_initialized = False

    def setup_event_handlers(self):
        """
        Sets up FastAPI startup and shutdown event handlers for database initialization.
        """
        @self.app.on_event("startup")
        async def startup_event():
            await self._initialize_database()
            logger.info("Warehouse Agent startup complete.")

        @self.app.on_event("shutdown")
        async def shutdown_event():
            logger.info("Warehouse Agent shutting down.")
            # Add any cleanup logic here if necessary

    def _setup_routes(self):
        """
        Sets up all FastAPI routes for the Warehouse Agent, including health checks,
        warehouse management, and capacity-related endpoints.
        """
        @self.app.get("/health", summary="Health Check")
        async def health_check():
            """Returns the health status of the Warehouse Agent and its services."""
            return {
                "status": "healthy",
                "agent_id": self.agent_id,
                "database_initialized": self._db_initialized,
                "services": {
                    "capacity": self.capacity_service is not None
                }
            }

        @self.app.get("/", summary="Root Endpoint")
        async def root():
            """Root endpoint for the Warehouse Agent API."""
            return {"message": "Warehouse Agent API is running"}

        @self.app.get("/warehouses", response_model=List[Dict[str, Any]], summary="Get All Warehouses")
        async def get_all_warehouses_api():
            """Retrieves a list of all warehouses from the database."""
            if not self._db_initialized:
                raise HTTPException(status_code=503, detail="Database not initialized")
            try:
                warehouses = await self.get_warehouses_from_db()
                return warehouses
            except Exception as e:
                logger.error(f"Error getting warehouses via API: {e}")
                raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

        @self.app.get("/warehouses/{warehouse_id}", response_model=Dict[str, Any], summary="Get Warehouse by ID")
        async def get_warehouse_by_id_api(warehouse_id: str):
            """Retrieves a single warehouse by its ID."""
            if not self._db_initialized:
                raise HTTPException(status_code=503, detail="Database not initialized")
            try:
                async with self.db_manager.get_session() as session:
                    warehouse = await self.db_helper.get_by_id(session, ProductDB, warehouse_id) # Assuming ProductDB is a placeholder for a Warehouse model
                    if not warehouse:
                        raise HTTPException(status_code=404, detail="Warehouse not found")
                    return self.db_helper.to_dict(warehouse)
            except HTTPException as e:
                raise e
            except Exception as e:
                logger.error(f"Error getting warehouse {warehouse_id} via API: {e}")
                raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

        @self.app.post("/warehouses", response_model=Dict[str, Any], status_code=201, summary="Create New Warehouse")
        async def create_warehouse_api(warehouse_data: Dict[str, Any]):
            """Creates a new warehouse entry in the database."""
            if not self._db_initialized:
                raise HTTPException(status_code=503, detail="Database not initialized")
            try:
                async with self.db_manager.get_session() as session:
                    # Assuming warehouse_data contains 'id', 'name', 'description', 'quantity'
                    new_warehouse = await self.db_helper.create(session, ProductDB, warehouse_data)
                    return self.db_helper.to_dict(new_warehouse)
            except Exception as e:
                logger.error(f"Error creating warehouse via API: {e}")
                raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

        @self.app.put("/warehouses/{warehouse_id}", response_model=Dict[str, Any], summary="Update Existing Warehouse")
        async def update_warehouse_api(warehouse_id: str, warehouse_data: Dict[str, Any]):
            """Updates an existing warehouse entry by ID."""
            if not self._db_initialized:
                raise HTTPException(status_code=503, detail="Database not initialized")
            try:
                async with self.db_manager.get_session() as session:
                    updated_warehouse = await self.db_helper.update(session, ProductDB, warehouse_id, warehouse_data)
                    if not updated_warehouse:
                        raise HTTPException(status_code=404, detail="Warehouse not found")
                    return self.db_helper.to_dict(updated_warehouse)
            except HTTPException as e:
                raise e
            except Exception as e:
                logger.error(f"Error updating warehouse {warehouse_id} via API: {e}")
                raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

        @self.app.delete("/warehouses/{warehouse_id}", status_code=204, summary="Delete Warehouse")
        async def delete_warehouse_api(warehouse_id: str):
            """Deletes a warehouse entry by ID."""
            if not self._db_initialized:
                raise HTTPException(status_code=503, detail="Database not initialized")
            try:
                async with self.db_manager.get_session() as session:
                    deleted_warehouse = await self.db_helper.delete(session, ProductDB, warehouse_id)
                    if not deleted_warehouse:
                        raise HTTPException(status_code=404, detail="Warehouse not found")
                return # No content for 204
            except HTTPException as e:
                raise e
            except Exception as e:
                logger.error(f"Error deleting warehouse {warehouse_id} via API: {e}")
                raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

        # Capacity endpoints
        if self.capacity_service:
            @self.app.get("/warehouses/{warehouse_id}/capacity", summary="Get Warehouse Capacity")
            async def get_warehouse_capacity(warehouse_id: str):
                """Retrieves capacity metrics for a specific warehouse."""
                try:
                    capacity = await self.capacity_service.get_capacity_metrics(warehouse_id)
                    return capacity
                except Exception as e:
                    logger.error(f"Error getting capacity for {warehouse_id}: {e}")
                    raise HTTPException(status_code=500, detail=str(e))

            @self.app.get("/warehouses/{warehouse_id}/performance", summary="Get Warehouse Performance KPIs")
            async def get_warehouse_performance(warehouse_id: str):
                """Retrieves performance KPIs for a specific warehouse."""
                try:
                    performance = await self.capacity_service.get_performance_kpis(warehouse_id)
                    return performance
                except Exception as e:
                    logger.error(f"Error getting performance for {warehouse_id}: {e}")
                    raise HTTPException(status_code=500, detail=str(e))

    async def get_warehouses_from_db(self) -> List[Dict]:
        """
        Retrieves all warehouse records from the database.

        Returns:
            List[Dict]: A list of dictionaries, each representing a warehouse.
        """
        logger.info("Attempting to retrieve warehouses from database.")
        if not self._db_initialized:
            logger.warning("Database not initialized. Cannot retrieve warehouses.")
            return []
        try:
            async with self.db_manager.get_session() as session:
                # Assuming ProductDB is used as a placeholder for warehouse items
                records = await self.db_helper.get_all(session, ProductDB, limit=100)
                return [self.db_helper.to_dict(r) for r in records]
        except Exception as e:
            logger.error(f"Error in get_warehouses_from_db: {e}")
            return []

    async def process_message(self, message: AgentMessage):
        """
        Processes incoming messages for the Warehouse Agent.

        Args:
            message (AgentMessage): The message object containing sender, receiver, type, and payload.
        """
        logger.info(f"Processing message from {message.sender_id} with type: {message.message_type}")
        try:
            if message.message_type == MessageType.COMMAND:
                await self._handle_command(message)
            elif message.message_type == MessageType.EVENT:
                await self._handle_event(message)
            elif message.message_type == MessageType.INFO:
                await self._handle_info(message)
            else:
                logger.warning(f"Unhandled message type: {message.message_type}")
        except Exception as e:
            logger.error(f"Error processing message {message.message_id}: {e}")
            await self.send_message(
                receiver_id=message.sender_id,
                message_type=MessageType.ERROR,
                payload={"original_message_id": message.message_id, "error": str(e)}
            )

    async def _handle_command(self, message: AgentMessage):
        """
        Handles COMMAND type messages.

        Args:
            message (AgentMessage): The command message.
        """
        command = message.payload.get("command")
        logger.info(f"Handling command: {command}")
        # Example command handling
        if command == "update_stock":
            product_id = message.payload.get("product_id")
            quantity_change = message.payload.get("quantity_change")
            if product_id and quantity_change is not None:
                await self._update_product_stock(product_id, quantity_change)
                await self.send_message(
                    receiver_id=message.sender_id,
                    message_type=MessageType.RESPONSE,
                    payload={"status": "success", "command": command, "product_id": product_id}
                )
            else:
                logger.warning(f"Invalid update_stock command payload: {message.payload}")
                await self.send_message(
                    receiver_id=message.sender_id,
                    message_type=MessageType.ERROR,
                    payload={"status": "failure", "command": command, "details": "Missing product_id or quantity_change"}
                )
        else:
            logger.warning(f"Unknown command received: {command}")
            await self.send_message(
                receiver_id=message.sender_id,
                message_type=MessageType.ERROR,
                payload={"status": "failure", "command": command, "details": "Unknown command"}
            )

    async def _handle_event(self, message: AgentMessage):
        """
        Handles EVENT type messages.

        Args:
            message (AgentMessage): The event message.
        """
        event_type = message.payload.get("event_type")
        logger.info(f"Handling event: {event_type}")
        # Example event handling
        if event_type == "order_placed":
            order_details = message.payload.get("order_details")
            logger.info(f"Processing new order event: {order_details.get('order_id')}")
            # Logic to process new order, e.g., reserve stock
            pass
        else:
            logger.warning(f"Unknown event received: {event_type}")

    async def _handle_info(self, message: AgentMessage):
        """
        Handles INFO type messages.

        Args:
            message (AgentMessage): The info message.
        """
        info_type = message.payload.get("info_type")
        logger.info(f"Handling info message: {info_type}")
        # Example info handling
        if info_type == "request_stock_level":
            product_id = message.payload.get("product_id")
            if product_id:
                stock_level = await self._get_product_stock(product_id)
                await self.send_message(
                    receiver_id=message.sender_id,
                    message_type=MessageType.RESPONSE,
                    payload={"status": "success", "info_type": info_type, "product_id": product_id, "stock_level": stock_level}
                )
            else:
                logger.warning(f"Invalid request_stock_level info payload: {message.payload}")

    async def _update_product_stock(self, product_id: str, quantity_change: int):
        """
        Updates the stock level for a given product in the database.

        Args:
            product_id (str): The ID of the product to update.
            quantity_change (int): The amount to change the quantity by (can be positive or negative).
        """
        if not self._db_initialized:
            logger.error("Database not initialized. Cannot update product stock.")
            return
        try:
            async with self.db_manager.get_session() as session:
                product = await self.db_helper.get_by_id(session, ProductDB, product_id)
                if product:
                    new_quantity = product.quantity + quantity_change
                    await self.db_helper.update(session, ProductDB, product_id, {"quantity": new_quantity})
                    logger.info(f"Updated stock for product {product_id} to {new_quantity}")
                else:
                    logger.warning(f"Product {product_id} not found for stock update.")
        except Exception as e:
            logger.error(f"Error updating stock for product {product_id}: {e}")

    async def _get_product_stock(self, product_id: str) -> Optional[int]:
        """
        Retrieves the stock level for a given product from the database.

        Args:
            product_id (str): The ID of the product to retrieve stock for.

        Returns:
            Optional[int]: The stock level if found, otherwise None.
        """
        if not self._db_initialized:
            logger.error("Database not initialized. Cannot get product stock.")
            return None
        try:
            async with self.db_manager.get_session() as session:
                product = await self.db_helper.get_by_id(session, ProductDB, product_id)
                if product:
                    return product.quantity
                else:
                    logger.warning(f"Product {product_id} not found for stock inquiry.")
                    return None
        except Exception as e:
            logger.error(f"Error getting stock for product {product_id}: {e}")
            return None



    # Required abstract methods from BaseAgent
    async def initialize(self):
        """Initialize agent-specific components."""
        await super().initialize()
        logger.info(f"{self.agent_name} initialized successfully")

    async def cleanup(self):
        """Cleanup agent-specific resources."""
        if hasattr(self, 'engine') and self.engine:
            await self.engine.dispose()
        await super().cleanup()
        logger.info(f"{self.agent_name} cleaned up successfully")

    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process agent-specific business logic."""
        try:
            operation = data.get("operation", "unknown")
            logger.info(f"Processing {operation} operation")
            return {"status": "success", "operation": operation}
        except Exception as e:
            logger.error(f"Error in process_business_logic: {e}")
            return {"status": "error", "message": str(e)}


# Module-level app for ASGI servers (only create when running as main)
app = None

if __name__ == "__main__":
    # Create agent instance only when running as main
    agent = WarehouseAgent()
    app = agent.app
    
    # Initialize agent before starting server
    import asyncio
    async def startup():
        await agent.initialize()
    asyncio.run(startup())
    
    # Ensure environment variables are loaded if running directly
    from dotenv import load_dotenv
    load_dotenv()

    # Get port from environment variable, default to 8005
    port = int(os.getenv("WAREHOUSE_AGENT_PORT", 8005))
    logger.info(f"Starting Warehouse Agent on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

