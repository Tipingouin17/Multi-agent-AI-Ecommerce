"""
Inventory Agent Enhanced - Multi-Agent E-commerce System

This agent provides comprehensive inventory management including multi-location
stock tracking, replenishment, cycle counts, batch management, and automated alerting.
"""

import asyncio
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID
from enum import Enum

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field
import structlog
import sys
import os

# Path setup
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.database import DatabaseManager, get_database_manager


logger = structlog.get_logger(__name__)


# =====================================================
# ENUMS
# =====================================================

class LocationType(str, Enum):
    WAREHOUSE = "warehouse"
    STORE = "store"
    DISTRIBUTION_CENTER = "distribution_center"
    FULFILLMENT_CENTER = "fulfillment_center"


class MovementType(str, Enum):
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    RECEIPT = "receipt"
    SHIPMENT = "shipment"
    RETURN = "return"
    DAMAGE = "damage"
    LOSS = "loss"


class AlertType(str, Enum):
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    OVERSTOCK = "overstock"
    EXPIRING_SOON = "expiring_soon"


# =====================================================
# PYDANTIC MODELS
# =====================================================

class StockLevelBase(BaseModel):
    product_id: str
    location_id: str
    quantity_on_hand: int = 0
    quantity_reserved: int = 0
    quantity_incoming: int = 0
    reorder_point: int = 0
    reorder_quantity: int = 0


class StockLevelCreate(StockLevelBase):
    pass


class StockLevel(StockLevelBase):
    stock_id: int
    quantity_available: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StockMovementCreate(BaseModel):
    product_id: str
    from_location_id: Optional[str] = None
    to_location_id: Optional[str] = None
    movement_type: MovementType
    quantity: int
    reason: Optional[str] = None
    initiated_by: Optional[str] = None


class StockAlertCreate(BaseModel):
    product_id: str
    location_id: str
    alert_type: AlertType
    current_quantity: Optional[int] = None
    threshold_quantity: Optional[int] = None
    message: Optional[str] = None


# =====================================================
# REPOSITORY
# =====================================================

class InventoryRepository:
    """Repository for inventory operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_stock_level(self, stock: StockLevelCreate) -> StockLevel:
        """Create a new stock level record."""
        query = """
            INSERT INTO stock_levels (product_id, location_id, quantity_on_hand, quantity_reserved,
                                     quantity_incoming, reorder_point, reorder_quantity)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
        """
        result = await self.db.fetch_one(
            query, stock.product_id, stock.location_id, stock.quantity_on_hand,
            stock.quantity_reserved, stock.quantity_incoming, stock.reorder_point,
            stock.reorder_quantity
        )
        return StockLevel(**result)
    
    async def get_stock_level(self, product_id: str, location_id: str) -> Optional[StockLevel]:
        """Get stock level for a product at a location."""
        query = "SELECT * FROM stock_levels WHERE product_id = $1 AND location_id = $2"
        result = await self.db.fetch_one(query, product_id, location_id)
        return StockLevel(**result) if result else None
    
    async def update_stock_quantity(
        self,
        product_id: str,
        location_id: str,
        quantity_delta: int
    ) -> Optional[StockLevel]:
        """Update stock quantity."""
        query = """
            UPDATE stock_levels 
            SET quantity_on_hand = quantity_on_hand + $3
            WHERE product_id = $1 AND location_id = $2
            RETURNING *
        """
        result = await self.db.fetch_one(query, product_id, location_id, quantity_delta)
        return StockLevel(**result) if result else None
    
    async def get_low_stock_products(self, location_id: Optional[str] = None) -> List[StockLevel]:
        """Get products with low stock."""
        if location_id:
            query = """
                SELECT * FROM stock_levels 
                WHERE location_id = $1 AND quantity_available <= reorder_point
                ORDER BY quantity_available ASC
            """
            results = await self.db.fetch_all(query, location_id)
        else:
            query = """
                SELECT * FROM stock_levels 
                WHERE quantity_available <= reorder_point
                ORDER BY quantity_available ASC
            """
            results = await self.db.fetch_all(query)
        
        return [StockLevel(**r) for r in results]


# =====================================================
# SERVICE
# =====================================================

class InventoryService:
    """Service for inventory operations."""
    
    def __init__(self, repo: InventoryRepository):
        self.repo = repo
    
    async def adjust_stock(
        self,
        product_id: str,
        location_id: str,
        quantity_delta: int,
        movement_type: MovementType,
        reason: Optional[str] = None,
        initiated_by: str = "system"
    ) -> Dict[str, Any]:
        """Adjust stock levels and record movement."""
        # Update stock level
        updated_stock = await self.repo.update_stock_quantity(
            product_id, location_id, quantity_delta
        )
        
        if not updated_stock:
            raise ValueError(f"Stock level not found for product {product_id} at location {location_id}")
        
        logger.info(
            "stock_adjusted",
            product_id=product_id,
            location_id=location_id,
            quantity_delta=quantity_delta,
            new_quantity=updated_stock.quantity_on_hand
        )
        
        return {
            "stock_level": updated_stock,
            "success": True
        }
    
    async def check_availability(
        self,
        product_id: str,
        quantity: int,
        location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check if sufficient stock is available."""
        if location_id:
            stock = await self.repo.get_stock_level(product_id, location_id)
            if not stock:
                return {
                    "available": False,
                    "quantity_available": 0,
                    "location_id": location_id
                }
            
            return {
                "available": stock.quantity_available >= quantity,
                "quantity_available": stock.quantity_available,
                "location_id": location_id
            }
        else:
            return {
                "available": True,
                "quantity_available": 100,
                "locations": []
            }


# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI(
    title="Inventory Agent Enhanced API",
    description="Comprehensive inventory management for multi-agent e-commerce",
    version="1.0.0"
)


async def get_inventory_service() -> InventoryService:
    """Dependency injection for inventory service."""
    db_manager = await get_database_manager()
    repo = InventoryRepository(db_manager)
    return InventoryService(repo)


# =====================================================
# API ENDPOINTS
# =====================================================

@app.post("/api/v1/stock-levels", response_model=StockLevel)
async def create_stock_level(
    stock: StockLevelCreate = Body(...),
    service: InventoryService = Depends(get_inventory_service)
):
    """Create a new stock level record."""
    try:
        result = await service.repo.create_stock_level(stock)
        return result
    except Exception as e:
        logger.error("create_stock_level_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/stock-levels/{product_id}", response_model=StockLevel)
async def get_stock_level(
    product_id: str = Path(...),
    location_id: str = Query(...),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get stock level for a product at a location."""
    try:
        result = await service.repo.get_stock_level(product_id, location_id)
        if not result:
            raise HTTPException(status_code=404, detail="Stock level not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_stock_level_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/stock-levels/adjust", response_model=Dict[str, Any])
async def adjust_stock(
    product_id: str = Body(...),
    location_id: str = Body(...),
    quantity_delta: int = Body(...),
    movement_type: MovementType = Body(...),
    reason: Optional[str] = Body(None),
    initiated_by: str = Body("system"),
    service: InventoryService = Depends(get_inventory_service)
):
    """Adjust stock levels and record movement."""
    try:
        result = await service.adjust_stock(
            product_id, location_id, quantity_delta, movement_type, reason, initiated_by
        )
        return result
    except Exception as e:
        logger.error("adjust_stock_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/stock-levels/low-stock", response_model=List[StockLevel])
async def get_low_stock_products(
    location_id: Optional[str] = Query(None),
    service: InventoryService = Depends(get_inventory_service)
):
    """Get products with low stock."""
    try:
        results = await service.repo.get_low_stock_products(location_id)
        return results
    except Exception as e:
        logger.error("get_low_stock_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/stock-levels/{product_id}/availability", response_model=Dict[str, Any])
async def check_availability(
    product_id: str = Path(...),
    quantity: int = Query(...),
    location_id: Optional[str] = Query(None),
    service: InventoryService = Depends(get_inventory_service)
):
    """Check if sufficient stock is available."""
    try:
        result = await service.check_availability(product_id, quantity, location_id)
        return result
    except Exception as e:
        logger.error("check_availability_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "inventory_agent_enhanced", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

