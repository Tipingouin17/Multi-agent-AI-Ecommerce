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

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID
from enum import Enum

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field
import structlog
import sys
import os

current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.database import DatabaseManager, get_database_manager

logger = structlog.get_logger(__name__)

# ENUMS
class MarketplaceName(str, Enum):
    CDISCOUNT = "cdiscount"
    AMAZON = "amazon"
    BACKMARKET = "backmarket"
    REFURBED = "refurbed"
    EBAY = "ebay"
    MIRAKL = "mirakl"

class SyncStatus(str, Enum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"

# MODELS
class MarketplaceConnection(BaseModel):
    connection_id: UUID
    marketplace_name: MarketplaceName
    merchant_id: str
    is_active: bool
    last_sync_at: Optional[datetime]

    class Config:
        from_attributes = True

class MarketplaceOrder(BaseModel):
    marketplace_order_id: UUID
    connection_id: UUID
    marketplace_order_number: str
    internal_order_id: Optional[str]
    order_data: Dict[str, Any]
    sync_status: SyncStatus
    created_at: datetime

    class Config:
        from_attributes = True

class InventorySyncRequest(BaseModel):
    connection_id: UUID
    product_id: str
    marketplace_sku: str
    quantity: int
    price: Decimal

class MessageCreate(BaseModel):
    connection_id: UUID
    customer_id: str
    order_id: Optional[str]
    subject: str
    message_body: str

class OfferCreate(BaseModel):
    connection_id: UUID
    product_id: str
    price: Decimal
    quantity: int

class SyncResult(BaseModel):
    success: bool
    synced_count: int
    failed_count: int
    errors: List[str] = []

# REPOSITORY
class MarketplaceRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def get_connections(self, active_only: bool = True) -> List[MarketplaceConnection]:
        query = "SELECT * FROM marketplace_connections"
        if active_only:
            query += " WHERE is_active = true"
        results = await self.db.fetch_all(query)
        return [MarketplaceConnection(**r) for r in results]
    
    async def get_connection(self, connection_id: UUID) -> Optional[MarketplaceConnection]:
        query = "SELECT * FROM marketplace_connections WHERE connection_id = $1"
        result = await self.db.fetch_one(query, connection_id)
        return MarketplaceConnection(**result) if result else None
    
    async def sync_order(self, order_data: Dict[str, Any]) -> UUID:
        query = """
            INSERT INTO marketplace_orders (connection_id, marketplace_order_number, order_data, sync_status)
            VALUES ($1, $2, $3, $4)
            RETURNING marketplace_order_id
        """
        result = await self.db.fetch_one(
            query, order_data['connection_id'], order_data['marketplace_order_number'],
            str(order_data['order_data']), 'synced'
        )
        return result['marketplace_order_id']
    
    async def get_marketplace_orders(
        self, connection_id: UUID, sync_status: Optional[SyncStatus] = None
    ) -> List[MarketplaceOrder]:
        query = "SELECT * FROM marketplace_orders WHERE connection_id = $1"
        params = [connection_id]
        
        if sync_status:
            query += " AND sync_status = $2"
            params.append(sync_status.value)
        
        query += " ORDER BY created_at DESC"
        results = await self.db.fetch_all(query, *params)
        return [MarketplaceOrder(**r) for r in results]
    
    async def sync_inventory(self, inventory_data: InventorySyncRequest) -> UUID:
        query = """
            INSERT INTO marketplace_inventory (connection_id, product_id, marketplace_sku, quantity, price)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (connection_id, product_id) DO UPDATE
            SET quantity = EXCLUDED.quantity, price = EXCLUDED.price, last_synced_at = CURRENT_TIMESTAMP
            RETURNING inventory_id
        """
        result = await self.db.fetch_one(
            query, inventory_data.connection_id, inventory_data.product_id,
            inventory_data.marketplace_sku, inventory_data.quantity, inventory_data.price
        )
        return result['inventory_id']
    
    async def create_message(self, message_data: MessageCreate) -> UUID:
        query = """
            INSERT INTO marketplace_messages (connection_id, customer_id, order_id, subject, message_body, direction)
            VALUES ($1, $2, $3, $4, $5, 'outbound')
            RETURNING message_id
        """
        result = await self.db.fetch_one(
            query, message_data.connection_id, message_data.customer_id,
            message_data.order_id, message_data.subject, message_data.message_body
        )
        return result['message_id']
    
    async def get_unread_messages(self, connection_id: UUID) -> List[Dict[str, Any]]:
        query = """
            SELECT * FROM marketplace_messages
            WHERE connection_id = $1 AND status = 'unread' AND direction = 'inbound'
            ORDER BY received_at DESC
        """
        results = await self.db.fetch_all(query, connection_id)
        return [dict(r) for r in results]
    
    async def create_offer(self, offer_data: OfferCreate) -> UUID:
        query = """
            INSERT INTO marketplace_offers (connection_id, product_id, price, quantity)
            VALUES ($1, $2, $3, $4)
            RETURNING offer_id
        """
        result = await self.db.fetch_one(
            query, offer_data.connection_id, offer_data.product_id,
            offer_data.price, offer_data.quantity
        )
        return result['offer_id']
    
    async def get_offers(self, connection_id: UUID, status: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM marketplace_offers WHERE connection_id = $1"
        params = [connection_id]
        
        if status:
            query += " AND status = $2"
            params.append(status)
        
        results = await self.db.fetch_all(query, *params)
        return [dict(r) for r in results]

# SERVICE
class MarketplaceService:
    def __init__(self, repo: MarketplaceRepository):
        self.repo = repo
    
    async def sync_orders_from_marketplace(self, connection_id: UUID) -> SyncResult:
        """Sync orders from marketplace to internal system."""
        connection = await self.repo.get_connection(connection_id)
        if not connection:
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
                'order_data': {'items': [], 'total': 100.00}
            }
        ]
        
        for order in simulated_orders:
            try:
                await self.repo.sync_order(order)
                synced_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(str(e))
        
        logger.info("orders_synced", connection_id=str(connection_id),
                   synced=synced_count, failed=failed_count)
        
        return SyncResult(
            success=failed_count == 0,
            synced_count=synced_count,
            failed_count=failed_count,
            errors=errors
        )
    
    async def sync_inventory_to_marketplace(self, inventory_data: InventorySyncRequest) -> UUID:
        """Sync inventory to marketplace."""
        connection = await self.repo.get_connection(inventory_data.connection_id)
        if not connection:
            raise ValueError("Connection not found")
        
        # In production, call marketplace API to update inventory
        inventory_id = await self.repo.sync_inventory(inventory_data)
        
        logger.info("inventory_synced", connection_id=str(inventory_data.connection_id),
                   product_id=inventory_data.product_id, quantity=inventory_data.quantity)
        
        return inventory_id
    
    async def send_message(self, message_data: MessageCreate) -> UUID:
        """Send message to marketplace customer."""
        connection = await self.repo.get_connection(message_data.connection_id)
        if not connection:
            raise ValueError("Connection not found")
        
        # In production, call marketplace API to send message
        message_id = await self.repo.create_message(message_data)
        
        logger.info("message_sent", connection_id=str(message_data.connection_id),
                   customer_id=message_data.customer_id)
        
        return message_id

# FASTAPI APP
app = FastAPI(title="Marketplace Connector Agent API", version="1.0.0")

async def get_marketplace_service() -> MarketplaceService:
    db_manager = await get_database_manager()
    repo = MarketplaceRepository(db_manager)
    return MarketplaceService(repo)

# ENDPOINTS
@app.get("/api/v1/marketplaces/connections", response_model=List[MarketplaceConnection])
async def get_connections(
    active_only: bool = Query(True),
    service: MarketplaceService = Depends(get_marketplace_service)
):
    try:
        connections = await service.repo.get_connections(active_only)
        return connections
    except Exception as e:
        logger.error("get_connections_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/marketplaces/{connection_id}/sync-orders", response_model=SyncResult)
async def sync_orders(
    connection_id: UUID = Path(...),
    service: MarketplaceService = Depends(get_marketplace_service)
):
    try:
        result = await service.sync_orders_from_marketplace(connection_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("sync_orders_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/marketplaces/{connection_id}/orders", response_model=List[MarketplaceOrder])
async def get_marketplace_orders(
    connection_id: UUID = Path(...),
    sync_status: Optional[SyncStatus] = Query(None),
    service: MarketplaceService = Depends(get_marketplace_service)
):
    try:
        orders = await service.repo.get_marketplace_orders(connection_id, sync_status)
        return orders
    except Exception as e:
        logger.error("get_marketplace_orders_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/marketplaces/sync-inventory")
async def sync_inventory(
    inventory_data: InventorySyncRequest = Body(...),
    service: MarketplaceService = Depends(get_marketplace_service)
):
    try:
        inventory_id = await service.sync_inventory_to_marketplace(inventory_data)
        return {"inventory_id": inventory_id, "message": "Inventory synced successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("sync_inventory_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/marketplaces/messages")
async def send_message(
    message_data: MessageCreate = Body(...),
    service: MarketplaceService = Depends(get_marketplace_service)
):
    try:
        message_id = await service.send_message(message_data)
        return {"message_id": message_id, "message": "Message sent successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("send_message_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/marketplaces/{connection_id}/messages/unread")
async def get_unread_messages(
    connection_id: UUID = Path(...),
    service: MarketplaceService = Depends(get_marketplace_service)
):
    try:
        messages = await service.repo.get_unread_messages(connection_id)
        return {"messages": messages}
    except Exception as e:
        logger.error("get_unread_messages_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/marketplaces/offers")
async def create_offer(
    offer_data: OfferCreate = Body(...),
    service: MarketplaceService = Depends(get_marketplace_service)
):
    try:
        offer_id = await service.repo.create_offer(offer_data)
        return {"offer_id": offer_id, "message": "Offer created successfully"}
    except Exception as e:
        logger.error("create_offer_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/marketplaces/{connection_id}/offers")
async def get_offers(
    connection_id: UUID = Path(...),
    status: Optional[str] = Query(None),
    service: MarketplaceService = Depends(get_marketplace_service)
):
    try:
        offers = await service.repo.get_offers(connection_id, status)
        return {"offers": offers}
    except Exception as e:
        logger.error("get_offers_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "marketplace_connector_agent", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8015)

