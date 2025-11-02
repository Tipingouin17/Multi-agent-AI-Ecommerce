from fastapi.middleware.cors import CORSMiddleware

"""
Marketplace Connector Agent - Multi-Agent E-Commerce System

This agent manages multi-marketplace integrations including CDiscount, Amazon, BackMarket,
Refurbed, eBay, and Mirakl. It handles order synchronization, inventory sync, message handling,
and offer management across all connected marketplaces.

DATABASE SCHEMA (migration 016_marketplace_connector_agent.sql):

CREATE TABLE marketplace_connections (
    connection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    marketplace_name VARCHAR(100) NOT NULL, -- 'cdiscount', 'amazon', 'backmarket', 'refurbed', 'ebay', 'mirakl'
    merchant_id VARCHAR(200) NOT NULL,
    api_credentials JSONB NOT NULL, -- Encrypted credentials
    is_active BOOLEAN DEFAULT true,
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE marketplace_orders (
    marketplace_order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID REFERENCES marketplace_connections(connection_id),
    marketplace_order_number VARCHAR(200) NOT NULL,
    internal_order_id VARCHAR(100), -- Link to internal order system
    order_data JSONB NOT NULL,
    sync_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'synced', 'failed'
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE marketplace_inventory (
    inventory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID REFERENCES marketplace_connections(connection_id),
    product_id VARCHAR(100) NOT NULL,
    marketplace_sku VARCHAR(200),
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2),
    last_synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE marketplace_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID REFERENCES marketplace_connections(connection_id),
    marketplace_message_id VARCHAR(200),
    customer_id VARCHAR(100),
    order_id VARCHAR(100),
    subject TEXT,
    message_body TEXT,
    direction VARCHAR(20), -- 'inbound', 'outbound'
    status VARCHAR(50) DEFAULT 'unread',
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE marketplace_offers (
    offer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID REFERENCES marketplace_connections(connection_id),
    product_id VARCHAR(100) NOT NULL,
    marketplace_offer_id VARCHAR(200),
    price DECIMAL(10, 2) NOT NULL,
    quantity INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'paused', 'out_of_stock', 'ended'
    last_synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

import os
import sys
import uvicorn
import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID
from enum import Enum

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field
import structlog

# Add project root to sys.path for shared modules
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.base_agent_v2 import BaseAgentV2, MessageType, AgentMessage
from shared.database import DatabaseManager
from contextlib import asynccontextmanager, get_database_manager
from shared.db_helpers import DatabaseHelper

logger = structlog.get_logger(__name__)

# ENUMS
class MarketplaceName(str, Enum):
    """Enum for supported marketplace names."""
    CDISCOUNT = "cdiscount"
    AMAZON = "amazon"
    BACKMARKET = "backmarket"
    REFURBED = "refurbed"
    EBAY = "ebay"
    MIRAKL = "mirakl"
    async def initialize(self):
        """Initialize agent."""
        await super().initialize()
        
    async def cleanup(self):
        """Cleanup agent."""
        await super().cleanup()
        
    async def process_business_logic(self, data):
        """Process business logic."""
        return {"status": "success"}


class SyncStatus(str, Enum):
    """Enum for order synchronization statuses."""
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"

# MODELS
class MarketplaceConnection(BaseModel):
    """Pydantic model for a marketplace connection."""
    connection_id: UUID
    marketplace_name: MarketplaceName
    merchant_id: str
    api_credentials: Dict[str, Any] # Credentials will be stored as JSONB
    is_active: bool
    last_sync_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class MarketplaceOrder(BaseModel):
    """Pydantic model for a marketplace order."""
    marketplace_order_id: UUID
    connection_id: UUID
    marketplace_order_number: str
    internal_order_id: Optional[str]
    order_data: Dict[str, Any]
    sync_status: SyncStatus
    last_synced_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class MarketplaceInventory(BaseModel):
    """Pydantic model for marketplace inventory."""
    inventory_id: UUID
    connection_id: UUID
    product_id: str
    marketplace_sku: Optional[str]
    quantity: int
    price: Decimal
    last_synced_at: datetime

    class Config:
        from_attributes = True

class MarketplaceMessage(BaseModel):
    """Pydantic model for a marketplace message."""
    message_id: UUID
    connection_id: UUID
    marketplace_message_id: Optional[str]
    customer_id: Optional[str]
    order_id: Optional[str]
    subject: Optional[str]
    message_body: str
    direction: str # 'inbound', 'outbound'
    status: str # 'unread', 'read', etc.
    received_at: datetime

    class Config:
        from_attributes = True

class MarketplaceOffer(BaseModel):
    """Pydantic model for a marketplace offer."""
    offer_id: UUID
    connection_id: UUID
    product_id: str
    marketplace_offer_id: Optional[str]
    price: Decimal
    quantity: int
    status: str # 'active', 'paused', 'out_of_stock', 'ended'
    last_synced_at: datetime

    class Config:
        from_attributes = True

class InventorySyncRequest(BaseModel):
    """Request model for syncing inventory."""
    connection_id: UUID
    product_id: str
    marketplace_sku: Optional[str] = None
    quantity: int
    price: Decimal

class MessageCreate(BaseModel):
    """Request model for creating a message."""
    connection_id: UUID
    customer_id: str
    order_id: Optional[str] = None
    subject: str
    message_body: str

class OfferCreate(BaseModel):
    """Request model for creating an offer."""
    connection_id: UUID
    product_id: str
    price: Decimal
    quantity: int

class SyncResult(BaseModel):
    """Result model for synchronization operations."""
    success: bool
    synced_count: int
    failed_count: int
    errors: List[str] = []

# REPOSITORY
class MarketplaceRepository:
    """Handles database operations for marketplace entities."""
    def __init__(self, db_manager: DatabaseManager):
        # FastAPI app for REST API
        
        
        # Add CORS middleware for dashboard integration
        
        """Initializes the repository with a database manager."""
        self.db_manager = db_manager
        self.db_helper = DatabaseHelper(db_manager)

    async def create_connection(self, connection_data: Dict[str, Any]) -> MarketplaceConnection:
        """Creates a new marketplace connection."""
        async with self.db_manager.get_session() as session:
            new_connection = await self.db_helper.create(
                session, "marketplace_connections", connection_data
            )
            return MarketplaceConnection(**new_connection)

    async def get_connections(self, active_only: bool = True) -> List[MarketplaceConnection]:
        """Retrieves marketplace connections, optionally filtered by active status."""
        async with self.db_manager.get_session() as session:
            if active_only:
                connections = await self.db_helper.get_all(session, "marketplace_connections", {"is_active": True})
            else:
                connections = await self.db_helper.get_all(session, "marketplace_connections")
            return [MarketplaceConnection(**c) for c in connections]

    async def get_connection(self, connection_id: UUID) -> Optional[MarketplaceConnection]:
        """Retrieves a single marketplace connection by its ID."""
        async with self.db_manager.get_session() as session:
            connection = await self.db_helper.get_by_id(session, "marketplace_connections", connection_id)
            return MarketplaceConnection(**connection) if connection else None

    async def update_connection(self, connection_id: UUID, update_data: Dict[str, Any]) -> Optional[MarketplaceConnection]:
        """Updates an existing marketplace connection."""
        async with self.db_manager.get_session() as session:
            updated_connection = await self.db_helper.update(
                session, "marketplace_connections", connection_id, update_data
            )
            return MarketplaceConnection(**updated_connection) if updated_connection else None

    async def delete_connection(self, connection_id: UUID) -> bool:
        """Deletes a marketplace connection by its ID."""
        async with self.db_manager.get_session() as session:
            return await self.db_helper.delete(session, "marketplace_connections", connection_id)

    async def sync_order(self, order_data: Dict[str, Any]) -> MarketplaceOrder:
        """Synchronizes an order into the database."""
        async with self.db_manager.get_session() as session:
            # Ensure order_data is a dictionary for JSONB storage
            if 'order_data' in order_data and not isinstance(order_data['order_data'], dict):
                order_data['order_data'] = json.loads(order_data['order_data'])
            
            new_order = await self.db_helper.create(
                session, "marketplace_orders", order_data
            )
            return MarketplaceOrder(**new_order)

    async def get_marketplace_orders(
        self, connection_id: UUID, sync_status: Optional[SyncStatus] = None
    ) -> List[MarketplaceOrder]:
        """Retrieves marketplace orders, optionally filtered by connection ID and sync status."""
        async with self.db_manager.get_session() as session:
            filters = {"connection_id": connection_id}
            if sync_status:
                filters["sync_status"] = sync_status.value
            orders = await self.db_helper.get_all(session, "marketplace_orders", filters)
            return [MarketplaceOrder(**o) for o in orders]

    async def sync_inventory(self, inventory_data: InventorySyncRequest) -> MarketplaceInventory:
        """Synchronizes inventory data, updating if product already exists for connection."""
        async with self.db_manager.get_session() as session:
            # Check if inventory already exists for this connection_id and product_id
            existing_inventory = await self.db_helper.get_all(
                session, "marketplace_inventory", 
                {"connection_id": inventory_data.connection_id, "product_id": inventory_data.product_id}
            )
            
            data_to_save = inventory_data.model_dump()
            data_to_save['last_synced_at'] = datetime.utcnow()

            if existing_inventory:
                # Update existing inventory
                updated_inventory = await self.db_helper.update(
                    session, 
                    "marketplace_inventory", 
                    existing_inventory[0]['inventory_id'], # Assuming product_id and connection_id form a unique key
                    data_to_save
                )
                return MarketplaceInventory(**updated_inventory)
            else:
                # Create new inventory entry
                new_inventory = await self.db_helper.create(
                    session, "marketplace_inventory", data_to_save
                )
                return MarketplaceInventory(**new_inventory)

    async def create_message(self, message_data: MessageCreate, direction: str = 'outbound', status: str = 'unread') -> MarketplaceMessage:
        """Creates a new marketplace message."""
        async with self.db_manager.get_session() as session:
            data_to_save = message_data.model_dump()
            data_to_save['direction'] = direction
            data_to_save['status'] = status
            data_to_save['received_at'] = datetime.utcnow() # For outbound, this is when it's sent
            new_message = await self.db_helper.create(
                session, "marketplace_messages", data_to_save
            )
            return MarketplaceMessage(**new_message)

    async def get_unread_messages(self, connection_id: UUID) -> List[MarketplaceMessage]:
        """Retrieves unread inbound messages for a given connection."""
        async with self.db_manager.get_session() as session:
            messages = await self.db_helper.get_all(
                session, "marketplace_messages", 
                {"connection_id": connection_id, "status": "unread", "direction": "inbound"}
            )
            return [MarketplaceMessage(**m) for m in messages]

    async def create_offer(self, offer_data: OfferCreate) -> MarketplaceOffer:
        """Creates a new marketplace offer."""
        async with self.db_manager.get_session() as session:
            data_to_save = offer_data.model_dump()
            data_to_save['status'] = 'active'
            data_to_save['last_synced_at'] = datetime.utcnow()
            new_offer = await self.db_helper.create(
                session, "marketplace_offers", data_to_save
            )
            return MarketplaceOffer(**new_offer)

    async def get_offers(self, connection_id: UUID, status: Optional[str] = None) -> List[MarketplaceOffer]:
        """Retrieves marketplace offers, optionally filtered by connection ID and status."""
        async with self.db_manager.get_session() as session:
            filters = {"connection_id": connection_id}
            if status:
                filters["status"] = status
            offers = await self.db_helper.get_all(session, "marketplace_offers", filters)
            return [MarketplaceOffer(**o) for o in offers]


# SERVICE
class MarketplaceService:
    """Business logic for marketplace operations."""
    def __init__(self, repo: MarketplaceRepository):
        """Initializes the service with a marketplace repository."""
        self.repo = repo

    async def sync_orders_from_marketplace(self, connection_id: UUID) -> SyncResult:
        """Sync orders from marketplace to internal system."""
        try:
            connection = await self.repo.get_connection(connection_id)
            if not connection:
                logger.warning("sync_orders_failed", reason="Connection not found", connection_id=str(connection_id))
                raise ValueError("Connection not found")
            
            # In production, call marketplace API to fetch orders
            # For now, simulate sync
            synced_count = 0
            failed_count = 0
            errors = []
            
            # Simulated orders
            simulated_orders = [
                {
                    'connection_id': connection_id,
                    'marketplace_order_number': f"MKT-{uuid4().hex[:8].upper()}",
                    'order_data': {'items': [], 'total': str(Decimal('100.00'))}, # Convert Decimal to str for JSONB compatibility
                    'sync_status': SyncStatus.SYNCED.value,
                    'created_at': datetime.utcnow()
                }
            ]
            
            for order in simulated_orders:
                try:
                    await self.repo.sync_order(order)
                    synced_count += 1
                except Exception as e:
                    failed_count += 1
                    errors.append(f"Failed to sync order {order.get('marketplace_order_number')}: {str(e)}")
                    logger.error("sync_single_order_failed", order_data=order, error=str(e))
            
            logger.info("orders_synced", connection_id=str(connection_id),
                       synced=synced_count, failed=failed_count)
            
            return SyncResult(
                success=failed_count == 0,
                synced_count=synced_count,
                failed_count=failed_count,
                errors=errors
            )
        except Exception as e:
            logger.error("sync_orders_from_marketplace_error", connection_id=str(connection_id), error=str(e))
            raise

    async def sync_inventory_to_marketplace(self, inventory_data: InventorySyncRequest) -> MarketplaceInventory:
        """Sync inventory to marketplace."""
        try:
            connection = await self.repo.get_connection(inventory_data.connection_id)
            if not connection:
                logger.warning("sync_inventory_failed", reason="Connection not found", connection_id=str(inventory_data.connection_id))
                raise ValueError("Connection not found")
            
            # In production, call marketplace API to update inventory
            inventory = await self.repo.sync_inventory(inventory_data)
            
            logger.info("inventory_synced", connection_id=str(inventory_data.connection_id),
                       product_id=inventory_data.product_id, quantity=inventory_data.quantity)
            
            return inventory
        except Exception as e:
            logger.error("sync_inventory_to_marketplace_error", inventory_data=inventory_data.model_dump(), error=str(e))
            raise

    async def send_message(self, message_data: MessageCreate) -> MarketplaceMessage:
        """Send message to marketplace customer."""
        try:
            connection = await self.repo.get_connection(message_data.connection_id)
            if not connection:
                logger.warning("send_message_failed", reason="Connection not found", connection_id=str(message_data.connection_id))
                raise ValueError("Connection not found")
            
            # In production, call marketplace API to send message
            message = await self.repo.create_message(message_data)
            
            logger.info("message_sent", connection_id=str(message_data.connection_id),
                       customer_id=message_data.customer_id, message_id=str(message.message_id))
            
            return message
        except Exception as e:
            logger.error("send_message_error", message_data=message_data.model_dump(), error=str(e))
            raise

    async def create_offer(self, offer_data: OfferCreate) -> MarketplaceOffer:
        """Creates a new offer on the marketplace."""
        try:
            connection = await self.repo.get_connection(offer_data.connection_id)
            if not connection:
                logger.warning("create_offer_failed", reason="Connection not found", connection_id=str(offer_data.connection_id))
                raise ValueError("Connection not found")

            offer = await self.repo.create_offer(offer_data)
            logger.info("offer_created", connection_id=str(offer_data.connection_id), product_id=offer_data.product_id, offer_id=str(offer.offer_id))
            return offer
        except Exception as e:
            logger.error("create_offer_error", offer_data=offer_data.model_dump(), error=str(e))
            raise


# AGENT CLASS
app = FastAPI()


    """Marketplace Connector Agent for managing multi-marketplace integrations."""
    def __init__(self, agent_id: str, agent_type: str):
        """Initializes the MarketplaceConnectorAgent."""
        super().__init__(agent_id)
        self.db_manager = None
        self.repo = None
        self.service = None
        self.fastapi_app = self._create_fastapi_app()
        self.logger = logger # Use the global structlog logger
        self._db_initialized = False # Flag for database initialization check

    async def _initialize_db(self):
        """Initializes the database manager connection."""
        if not self._db_initialized:
            # Try to get global database manager first
            try:
                self.db_manager = get_database_manager()
                self.logger.info("Using global database manager")
            except (RuntimeError, ImportError):
                # Create new database manager with config
                from shared.models import DatabaseConfig
                from shared.database_manager import EnhancedDatabaseManager
                db_config = DatabaseConfig()
                self.db_manager = EnhancedDatabaseManager(db_config)
                await self.db_manager.initialize(max_retries=5)
                self.logger.info("Created new enhanced database manager")
            
            self.repo = MarketplaceRepository(self.db_manager)
            self.service = MarketplaceService(self.repo)
            self._db_initialized = True
            self.logger.info("Database connection established for agent.")

    def _create_fastapi_app(self) -> FastAPI:
        """Creates and configures the FastAPI application for the agent."""
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            await self._initialize_db()
            self.logger.info("FastAPI Lifespan Startup: Database Initialized.")
            
            yield
            
            # Shutdown
            if self._db_initialized:
                await self.db_manager.close()
                self.logger.info("FastAPI Lifespan Shutdown: Database disconnected.")

        app = FastAPI(title="Marketplace Connector Agent API", version="1.0.0",
                      description="API for managing multi-marketplace integrations.",
                      lifespan=lifespan)

        @app.get("/health", tags=["Monitoring"])
        async def health_check():
            """Returns the health status of the agent."""
            self.logger.info("Health check requested.")
            return {"status": "healthy", "agent": self.agent_id, "version": "1.0.0"}

        @app.get("/", tags=["Root"])
        async def root():
            """Root endpoint providing basic agent information."""
            self.logger.info("Root endpoint requested.")
            return {"message": f"Welcome to {self.agent_type} {self.agent_id} API!"}

        @app.post("/api/v1/marketplaces/connections", response_model=MarketplaceConnection, tags=["Connections"])
        async def create_connection(
            connection_data: Dict[str, Any] = Body(...)):
            """Creates a new marketplace connection."""
            try:
                if not self._db_initialized: await self._initialize_db()
                connection = await self.repo.create_connection(connection_data)
                self.logger.info("Connection created", connection_id=str(connection.connection_id))
                return connection
            except Exception as e:
                self.logger.error("create_connection_failed", error=str(e), data=connection_data)
                raise HTTPException(status_code=500, detail=f"Failed to create connection: {e}")

        @app.get("/api/v1/marketplaces/connections", response_model=List[MarketplaceConnection], tags=["Connections"])
        async def get_connections(
            active_only: bool = Query(True)):
            """Retrieves marketplace connections, optionally filtered by active status."""
            try:
                if not self._db_initialized: await self._initialize_db()
                connections = await self.repo.get_connections(active_only)
                self.logger.info("Connections retrieved", count=len(connections), active_only=active_only)
                return connections
            except Exception as e:
                self.logger.error("get_connections_failed", error=str(e), active_only=active_only)
                raise HTTPException(status_code=500, detail=f"Failed to retrieve connections: {e}")

        @app.get("/api/v1/marketplaces/connections/{connection_id}", response_model=MarketplaceConnection, tags=["Connections"])
        async def get_connection_by_id(
            connection_id: UUID = Path(..., description="The ID of the marketplace connection")):
            """Retrieves a single marketplace connection by its ID."""
            try:
                if not self._db_initialized: await self._initialize_db()
                connection = await self.repo.get_connection(connection_id)
                if not connection:
                    raise HTTPException(status_code=404, detail="Connection not found")
                self.logger.info("Connection retrieved by ID", connection_id=str(connection_id))
                return connection
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("get_connection_by_id_failed", error=str(e), connection_id=str(connection_id))
                raise HTTPException(status_code=500, detail=f"Failed to retrieve connection: {e}")

        @app.put("/api/v1/marketplaces/connections/{connection_id}", response_model=MarketplaceConnection, tags=["Connections"])
        async def update_connection(
            connection_id: UUID = Path(..., description="The ID of the marketplace connection to update"),
            update_data: Dict[str, Any] = Body(..., description="Data to update the connection with")
        ):
            """Updates an existing marketplace connection."""
            try:
                if not self._db_initialized: await self._initialize_db()
                updated_connection = await self.repo.update_connection(connection_id, update_data)
                if not updated_connection:
                    raise HTTPException(status_code=404, detail="Connection not found")
                self.logger.info("Connection updated", connection_id=str(connection_id), update_data=update_data)
                return updated_connection
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("update_connection_failed", error=str(e), connection_id=str(connection_id), update_data=update_data)
                raise HTTPException(status_code=500, detail=f"Failed to update connection: {e}")

        @app.delete("/api/v1/marketplaces/connections/{connection_id}", status_code=204, tags=["Connections"])
        async def delete_connection(
            connection_id: UUID = Path(..., description="The ID of the marketplace connection to delete")):
            """Deletes a marketplace connection."""
            try:
                if not self._db_initialized: await self._initialize_db()
                deleted = await self.repo.delete_connection(connection_id)
                if not deleted:
                    raise HTTPException(status_code=404, detail="Connection not found")
                self.logger.info("Connection deleted", connection_id=str(connection_id))
                return
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("delete_connection_failed", error=str(e), connection_id=str(connection_id))
                raise HTTPException(status_code=500, detail=f"Failed to delete connection: {e}")

        @app.post("/api/v1/marketplaces/{connection_id}/sync-orders", response_model=SyncResult, tags=["Orders"])
        async def sync_orders(
            connection_id: UUID = Path(..., description="The ID of the marketplace connection")):
            """Triggers order synchronization for a specific marketplace connection."""
            try:
                if not self._db_initialized: await self._initialize_db()
                result = await self.service.sync_orders_from_marketplace(connection_id)
                self.logger.info("Orders sync initiated", connection_id=str(connection_id), result=result.model_dump())
                return result
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                self.logger.error("sync_orders_failed", error=str(e), connection_id=str(connection_id))
                raise HTTPException(status_code=500, detail=f"Failed to sync orders: {e}")

        @app.get("/api/v1/marketplaces/{connection_id}/orders", response_model=List[MarketplaceOrder], tags=["Orders"])
        async def get_marketplace_orders(
            connection_id: UUID = Path(..., description="The ID of the marketplace connection"),
            sync_status: Optional[SyncStatus] = Query(None, description="Filter orders by sync status")):
            """Retrieves marketplace orders for a specific connection, optionally filtered by sync status."""
            try:
                if not self._db_initialized: await self._initialize_db()
                orders = await self.repo.get_marketplace_orders(connection_id, sync_status)
                self.logger.info("Marketplace orders retrieved", connection_id=str(connection_id), count=len(orders))
                return orders
            except Exception as e:
                self.logger.error("get_marketplace_orders_failed", error=str(e), connection_id=str(connection_id))
                raise HTTPException(status_code=500, detail=f"Failed to retrieve marketplace orders: {e}")

        @app.post("/api/v1/marketplaces/sync-inventory", response_model=MarketplaceInventory, tags=["Inventory"])
        async def sync_inventory_endpoint(
            inventory_data: InventorySyncRequest = Body(..., description="Inventory data to sync")):
            """Synchronizes inventory data to a marketplace."""
            try:
                if not self._db_initialized: await self._initialize_db()
                inventory = await self.service.sync_inventory_to_marketplace(inventory_data)
                self.logger.info("Inventory sync initiated", connection_id=str(inventory_data.connection_id), product_id=inventory_data.product_id)
                return inventory
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                self.logger.error("sync_inventory_failed", error=str(e), inventory_data=inventory_data.model_dump())
                raise HTTPException(status_code=500, detail=f"Failed to sync inventory: {e}")

        @app.post("/api/v1/marketplaces/messages", response_model=MarketplaceMessage, tags=["Messages"])
        async def send_message_endpoint(
            message_data: MessageCreate = Body(..., description="Message data to send")):
            """Sends a message to a marketplace customer."""
            try:
                if not self._db_initialized: await self._initialize_db()
                message = await self.service.send_message(message_data)
                self.logger.info("Message sent", connection_id=str(message_data.connection_id), customer_id=message_data.customer_id)
                return message
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                self.logger.error("send_message_failed", error=str(e), message_data=message_data.model_dump())
                raise HTTPException(status_code=500, detail=f"Failed to send message: {e}")

        @app.get("/api/v1/marketplaces/{connection_id}/messages/unread", response_model=List[MarketplaceMessage], tags=["Messages"])
        async def get_unread_messages_endpoint(
            connection_id: UUID = Path(..., description="The ID of the marketplace connection")):
            """Retrieves unread messages for a specific marketplace connection."""
            try:
                if not self._db_initialized: await self._initialize_db()
                messages = await self.repo.get_unread_messages(connection_id)
                self.logger.info("Unread messages retrieved", connection_id=str(connection_id), count=len(messages))
                return messages
            except Exception as e:
                self.logger.error("get_unread_messages_failed", error=str(e), connection_id=str(connection_id))
                raise HTTPException(status_code=500, detail=f"Failed to retrieve unread messages: {e}")

        @app.post("/api/v1/marketplaces/offers", response_model=MarketplaceOffer, tags=["Offers"])
        async def create_offer_endpoint(
            offer_data: OfferCreate = Body(..., description="Offer data to create")):
            """Creates a new offer on a marketplace."""
            try:
                if not self._db_initialized: await self._initialize_db()
                offer = await self.service.create_offer(offer_data)
                self.logger.info("Offer created", connection_id=str(offer_data.connection_id), product_id=offer_data.product_id)
                return offer
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                self.logger.error("create_offer_failed", error=str(e), offer_data=offer_data.model_dump())
                raise HTTPException(status_code=500, detail=f"Failed to create offer: {e}")

        @app.get("/api/v1/marketplaces/{connection_id}/offers", response_model=List[MarketplaceOffer], tags=["Offers"])
        async def get_offers_endpoint(
            connection_id: UUID = Path(..., description="The ID of the marketplace connection"),
            status: Optional[str] = Query(None, description="Filter offers by status (e.g., 'active', 'paused')")):
            """Retrieves offers for a specific marketplace connection, optionally filtered by status."""
            try:
                if not self._db_initialized: await self._initialize_db()
                offers = await self.repo.get_offers(connection_id, status)
                self.logger.info("Offers retrieved", connection_id=str(connection_id), count=len(offers))
                return offers
            except Exception as e:
                self.logger.error("get_offers_failed", error=str(e), connection_id=str(connection_id))
                raise HTTPException(status_code=500, detail=f"Failed to retrieve offers: {e}")

        return app

    async def process_message(self, message: AgentMessage):
        """Processes incoming messages for the agent."""
        self.logger.info("Processing message", message_type=message.message_type, sender=message.sender_id)
        try:
            if not self._db_initialized: await self._initialize_db()
            if message.message_type == MessageType.ORDER_NEW:
                # Example: A new order from another agent needs to be synced to a marketplace
                order_data = message.payload
                connection_id = UUID(order_data.get("connection_id"))
                self.logger.info("Received new order message", order_data=order_data)
                sync_result = await self.service.sync_orders_from_marketplace(connection_id)
                await self.send_message(
                    recipient_id=message.sender_id,
                    payload=sync_result.model_dump(),
                    message_type=MessageType.ORDER_UPDATE
                )
            elif message.message_type == MessageType.INVENTORY_UPDATE:
                # Example: Inventory update from another agent needs to be pushed to a marketplace
                inventory_data = InventorySyncRequest(**message.payload)
                self.logger.info("Received inventory update message", inventory_data=inventory_data.model_dump())
                updated_inventory = await self.service.sync_inventory_to_marketplace(inventory_data)
                await self.send_message(
                    recipient_id=message.sender_id,
                    payload=updated_inventory.model_dump(),
                    message_type=MessageType.INVENTORY_UPDATE_CONFIRMATION
                )
            elif message.message_type == MessageType.MESSAGE_CREATE:
                # Example: Create an outbound message to a customer on a marketplace
                message_create_data = MessageCreate(**message.payload)
                self.logger.info("Received message create request", message_data=message_create_data.model_dump())
                new_message = await self.service.send_message(message_create_data)
                await self.send_message(
                    recipient_id=message.sender_id,
                    payload=new_message.model_dump(),
                    message_type=MessageType.MESSAGE_CONFIRMATION
                )
            elif message.message_type == MessageType.OFFER_CREATE:
                # Example: Create a new offer on a marketplace
                offer_create_data = OfferCreate(**message.payload)
                self.logger.info("Received offer create request", offer_data=offer_create_data.model_dump())
                new_offer = await self.service.create_offer(offer_create_data)
                await self.send_message(
                    recipient_id=message.sender_id,
                    payload=new_offer.model_dump(),
                    message_type=MessageType.OFFER_CONFIRMATION
                )
            else:
                self.logger.warning("Unhandled message type", message_type=message.message_type, sender=message.sender_id)
        except Exception as e:
            self.logger.error("Error processing message", message=message.model_dump(), error=str(e))
            # Optionally send an error message back to the sender
            await self.send_message(
                recipient_id=message.sender_id,
                payload={"error": str(e), "original_message": message.model_dump()},
                message_type=MessageType.ERROR
            )


    async def initialize(self):
        """Initialize agent-specific components."""
        await self._initialize_db()
        self.logger.info("MarketplaceConnectorAgent initialized")
    
    async def cleanup(self):
        """Cleanup agent-specific resources."""
        if self._db_initialized:
            await self.db_manager.close()
            self.logger.info("MarketplaceConnectorAgent cleaned up")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process agent-specific business logic."""
        # This agent primarily operates via REST API, not message processing
        # But we need to implement this for BaseAgentV2
        self.logger.info("Processing business logic", data=data)
        return {"status": "processed", "data": data}


# Dependency to get the agent instance
# This is a placeholder for how the agent might be integrated into a larger system
# For standalone execution, the agent instance is created directly in __main__
# async def get_marketplace_connector_agent() -> MarketplaceConnectorAgent:
#     # In a real system, this would retrieve a singleton or manage agent lifecycle
#     # For now, we'll assume a global instance or create one if needed
#     global marketplace_agent_instance
#     if marketplace_agent_instance is None:
#         marketplace_agent_instance = MarketplaceConnectorAgent(
#             agent_id=os.getenv("AGENT_ID", "marketplace_connector_001"),
#             agent_type="marketplace_connector"
#         )
#         await marketplace_agent_instance._initialize_db()
#     return marketplace_agent_instance


if __name__ == "__main__":
    # Environment variables for agent configuration
    AGENT_ID = os.getenv("AGENT_ID", "marketplace_connector_001")
    AGENT_TYPE = os.getenv("AGENT_TYPE", "marketplace_connector")
    API_PORT = int(os.getenv("API_PORT", "8015"))
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/ecommerce")
    KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092").split(',')
    
    # DatabaseManager is initialized via get_database_manager() in the agent's __init__
    marketplace_agent = MarketplaceConnectorAgent(AGENT_ID, AGENT_TYPE)
    # The FastAPI app is already created within the agent's __init__
    app = marketplace_agent.fastapi_app

    # Run the FastAPI application using uvicorn
    logger.info(f"Starting Marketplace Connector Agent API on port {API_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=API_PORT)

