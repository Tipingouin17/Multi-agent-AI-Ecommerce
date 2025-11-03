"""
Warehouse Agent - Multi-Agent E-Commerce System

This agent manages multi-warehouse operations including bin locations,
pick/pack/ship workflows, inventory allocation, and warehouse capacity planning.

DATABASE SCHEMA (migration 014_warehouse_agent.sql):

CREATE TABLE warehouses (
    warehouse_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_code VARCHAR(50) UNIQUE NOT NULL,
    warehouse_name VARCHAR(200) NOT NULL,
    address JSONB NOT NULL,
    capacity INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE warehouse_zones (
    zone_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID REFERENCES warehouses(warehouse_id),
    zone_code VARCHAR(50) NOT NULL,
    zone_type VARCHAR(50), -- 'receiving', 'storage', 'picking', 'packing', 'shipping'
    capacity INTEGER
);

CREATE TABLE warehouse_bins (
    bin_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone_id UUID REFERENCES warehouse_zones(zone_id),
    bin_code VARCHAR(50) NOT NULL,
    bin_type VARCHAR(50), -- 'shelf', 'pallet', 'floor'
    max_capacity INTEGER,
    current_capacity INTEGER DEFAULT 0,
    is_available BOOLEAN DEFAULT true
);

CREATE TABLE warehouse_inventory (
    inventory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID REFERENCES warehouses(warehouse_id),
    bin_id UUID REFERENCES warehouse_bins(bin_id),
    product_id VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0,
    available_quantity INTEGER GENERATED ALWAYS AS (quantity - reserved_quantity) STORED,
    last_counted_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pick_lists (
    pick_list_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID REFERENCES warehouses(warehouse_id),
    order_id VARCHAR(100) NOT NULL,
    picker_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'assigned', 'picking', 'completed', 'cancelled'
    items JSONB NOT NULL,
    priority INTEGER DEFAULT 0,
    assigned_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE packing_slips (
    packing_slip_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pick_list_id UUID REFERENCES pick_lists(pick_list_id),
    order_id VARCHAR(100) NOT NULL,
    packer_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    packed_items JSONB,
    box_dimensions JSONB,
    weight DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID
from enum import Enum

from shared.db_helpers import DatabaseHelper

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

from shared.database import DatabaseManager, get_database_manager, initialize_database_manager
from shared.base_agent_v2 import BaseAgentV2
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

logger = structlog.get_logger(__name__)

# AGENT INSTANCE (for dependency injection)
warehouse_service: Optional['WarehouseService'] = None

# ENUMS
class PickListStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    PICKING = "picking"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# MODELS
class Warehouse(BaseModel):
    warehouse_id: UUID
    warehouse_code: str
    warehouse_name: str
    address: Dict[str, Any]
    capacity: Optional[int]
    is_active: bool

    class Config:
        from_attributes = True

class WarehouseInventory(BaseModel):
    inventory_id: UUID
    warehouse_id: UUID
    product_id: str
    quantity: int
    reserved_quantity: int
    available_quantity: int

    class Config:
        from_attributes = True

class PickListItem(BaseModel):
    product_id: str
    quantity: int
    bin_location: Optional[str] = None

class PickListCreate(BaseModel):
    warehouse_id: UUID
    order_id: str
    items: List[PickListItem]
    priority: int = 0

class PickList(BaseModel):
    pick_list_id: UUID
    warehouse_id: UUID
    order_id: str
    status: PickListStatus
    items: List[Dict[str, Any]]
    priority: int
    created_at: datetime

    class Config:
        from_attributes = True

class InventoryAllocationRequest(BaseModel):
    product_id: str
    quantity: int
    preferred_warehouse: Optional[UUID] = None

class InventoryAllocationResponse(BaseModel):
    allocated: bool
    warehouse_id: Optional[UUID]
    bin_id: Optional[UUID]
    available_quantity: int
    message: str

# REPOSITORY
class WarehouseRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def get_warehouses(self, active_only: bool = True) -> List[Warehouse]:
        query = "SELECT * FROM warehouses"
        if active_only:
            query += " WHERE is_active = true"
        results = await self.db.fetch_all(query)
        return [Warehouse(**r) for r in results]
    
    async def get_warehouse_inventory(
        self, warehouse_id: UUID, product_id: Optional[str] = None
    ) -> List[WarehouseInventory]:
        query = "SELECT * FROM warehouse_inventory WHERE warehouse_id = $1"
        params = [warehouse_id]
        
        if product_id:
            query += " AND product_id = $2"
            params.append(product_id)
        
        results = await self.db.fetch_all(query, *params)
        return [WarehouseInventory(**r) for r in results]
    
    async def create_pick_list(self, pick_data: PickListCreate) -> PickList:
        query = """
            INSERT INTO pick_lists (warehouse_id, order_id, items, priority)
            VALUES ($1, $2, $3, $4)
            RETURNING *
        """
        result = await self.db.fetch_one(
            query, pick_data.warehouse_id, pick_data.order_id,
            str([item.dict() for item in pick_data.items]), pick_data.priority
        )
        return PickList(**result)
    
    async def get_pick_list(self, pick_list_id: UUID) -> Optional[PickList]:
        query = "SELECT * FROM pick_lists WHERE pick_list_id = $1"
        result = await self.db.fetch_one(query, pick_list_id)
        return PickList(**result) if result else None
    
    async def update_pick_list_status(
        self, pick_list_id: UUID, status: PickListStatus
    ) -> Optional[PickList]:
        query = """
            UPDATE pick_lists 
            SET status = $2,
                started_at = CASE WHEN $2 = 'picking' THEN CURRENT_TIMESTAMP ELSE started_at END,
                completed_at = CASE WHEN $2 = 'completed' THEN CURRENT_TIMESTAMP ELSE completed_at END
            WHERE pick_list_id = $1
            RETURNING *
        """
        result = await self.db.fetch_one(query, pick_list_id, status.value)
        return PickList(**result) if result else None
    
    async def get_pending_pick_lists(self, warehouse_id: UUID) -> List[PickList]:
        query = """
            SELECT * FROM pick_lists
            WHERE warehouse_id = $1 AND status IN ('pending', 'assigned')
            ORDER BY priority DESC, created_at ASC
        """
        results = await self.db.fetch_all(query, warehouse_id)
        return [PickList(**r) for r in results]
    
    async def find_inventory_location(
        self, product_id: str, quantity: int, warehouse_id: Optional[UUID] = None
    ) -> Optional[Dict[str, Any]]:
        """Find warehouse and bin with sufficient inventory."""
        query = """
            SELECT warehouse_id, bin_id, available_quantity
            FROM warehouse_inventory
            WHERE product_id = $1 AND available_quantity >= $2
        """
        params = [product_id, quantity]
        
        if warehouse_id:
            query += " AND warehouse_id = $3"
            params.append(warehouse_id)
        
        query += " ORDER BY available_quantity DESC LIMIT 1"
        
        result = await self.db.fetch_one(query, *params)
        return dict(result) if result else None

# SERVICE
class WarehouseService:
    def __init__(self, repo: WarehouseRepository):
        self.repo = repo
    
    async def allocate_inventory(
        self, request: InventoryAllocationRequest
    ) -> InventoryAllocationResponse:
        """Allocate inventory from warehouse."""
        location = await self.repo.find_inventory_location(
            request.product_id, request.quantity, request.preferred_warehouse
        )
        
        if not location:
            return InventoryAllocationResponse(
                allocated=False,
                warehouse_id=None,
                bin_id=None,
                available_quantity=0,
                message="Insufficient inventory available"
            )
        
        logger.info("inventory_allocated", product_id=request.product_id,
                   quantity=request.quantity, warehouse_id=str(location['warehouse_id']))
        
        return InventoryAllocationResponse(
            allocated=True,
            warehouse_id=location['warehouse_id'],
            bin_id=location['bin_id'],
            available_quantity=location['available_quantity'],
            message="Inventory allocated successfully"
        )
    
    async def create_pick_list(self, pick_data: PickListCreate) -> PickList:
        """Create pick list for order fulfillment."""
        pick_list = await self.repo.create_pick_list(pick_data)
        
        logger.info("pick_list_created", pick_list_id=str(pick_list.pick_list_id),
                   order_id=pick_data.order_id, items_count=len(pick_data.items))
        
        return pick_list
    
    async def start_picking(self, pick_list_id: UUID, picker_id: str) -> PickList:
        """Start picking process."""
        pick_list = await self.repo.update_pick_list_status(
            pick_list_id, PickListStatus.PICKING
        )
        
        if not pick_list:
            raise ValueError("Pick list not found")
        
        logger.info("picking_started", pick_list_id=str(pick_list_id), picker_id=picker_id)
        return pick_list
    
    async def complete_picking(self, pick_list_id: UUID) -> PickList:
        """Complete picking process."""
        pick_list = await self.repo.update_pick_list_status(
            pick_list_id, PickListStatus.COMPLETED
        )
        
        if not pick_list:
            raise ValueError("Pick list not found")
        
        logger.info("picking_completed", pick_list_id=str(pick_list_id))
        return pick_list

# --- FastAPI Lifespan ---
# WAREHOUSE AGENT CLASS
class WarehouseAgent(BaseAgentV2):
    """Warehouse Agent for managing multi-warehouse operations."""
    
    def __init__(self, agent_id: str = "warehouse_agent"):
        super().__init__(agent_id=agent_id)
        self.agent_name = "Warehouse Agent"
        self.db_manager: Optional[DatabaseManager] = None
        self.service: Optional[WarehouseService] = None
    
    async def initialize(self):
        """Initialize the Warehouse Agent with database connections."""
        await super().initialize()
        logger.info("WarehouseAgent initialize initiated.")
        
        try:
            # Initialize database manager
            try:
                self.db_manager = get_database_manager()
                logger.info("Using global database manager")
            except RuntimeError:
                from shared.models import DatabaseConfig
                db_config = DatabaseConfig()
                self.db_manager = DatabaseManager(db_config)
                await self.db_manager.initialize()
                logger.info("Created new database manager")
            
            # Initialize repository and service
            db_helper = DatabaseHelper(self.db_manager)
            repo = WarehouseRepository(db_helper)
            self.service = WarehouseService(repo)
            
            logger.info("WarehouseAgent initialized successfully")
            
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup agent resources."""
        try:
            if self.db_manager:
                await self.db_manager.close()
            await super().cleanup()
            logger.info(f"{self.agent_name} cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process warehouse business logic.
        
        Args:
            data: Dictionary containing operation type and parameters
            
        Returns:
            Dictionary with processing results
        """
        try:
            operation = data.get("operation", "process")
            logger.info(f"Processing warehouse operation: {operation}")
            return {"status": "success", "operation": operation, "data": data}
        except Exception as e:
            logger.error(f"Error in process_business_logic: {e}")
            return {"status": "error", "message": str(e)}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes the database connection and service layer."""
    global warehouse_service
    logger.info("Warehouse Agent Startup: Initializing Database and Service")
    try:
        # Initialize database manager first
        from shared.models import DatabaseConfig
        import os
        db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/multi_agent_ecommerce")
        db_config = DatabaseConfig(url=db_url)
        db_manager = initialize_database_manager(db_config)
        await db_manager.initialize_async()
        repo = WarehouseRepository(db_manager)
        warehouse_service = WarehouseService(repo)
        logger.info("Warehouse Agent Startup: Initialization Complete")
        yield
    finally:
        logger.info("Warehouse Agent Shutdown: Cleaning up resources")
        # DatabaseManager handles connection pool cleanup on its own
        pass

# FASTAPI APP
app = FastAPI(title="Warehouse Agent API", version="1.0.0", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_warehouse_service() -> WarehouseService:
    """Dependency injector for the WarehouseService."""
    if not warehouse_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return warehouse_service

# ENDPOINTS
@app.get("/api/v1/warehouses", response_model=List[Warehouse])
async def get_warehouses(
    active_only: bool = Query(True),
    service: WarehouseService = Depends(get_warehouse_service)
):
    try:
        warehouses = await service.repo.get_warehouses(active_only)
        return warehouses
    except Exception as e:
        logger.error("get_warehouses_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/warehouses/{warehouse_id}/inventory", response_model=List[WarehouseInventory])
async def get_warehouse_inventory(
    warehouse_id: UUID = Path(...),
    product_id: Optional[str] = Query(None),
    service: WarehouseService = Depends(get_warehouse_service)
):
    try:
        inventory = await service.repo.get_warehouse_inventory(warehouse_id, product_id)
        return inventory
    except Exception as e:
        logger.error("get_warehouse_inventory_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/warehouses/allocate", response_model=InventoryAllocationResponse)
async def allocate_inventory(
    request: InventoryAllocationRequest = Body(...),
    service: WarehouseService = Depends(get_warehouse_service)
):
    try:
        response = await service.allocate_inventory(request)
        return response
    except Exception as e:
        logger.error("allocate_inventory_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/warehouses/pick-lists", response_model=PickList)
async def create_pick_list(
    pick_data: PickListCreate = Body(...),
    service: WarehouseService = Depends(get_warehouse_service)
):
    try:
        pick_list = await service.create_pick_list(pick_data)
        return pick_list
    except Exception as e:
        logger.error("create_pick_list_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/warehouses/pick-lists/{pick_list_id}/start", response_model=PickList)
async def start_picking(
    pick_list_id: UUID = Path(...),
    picker_id: str = Body(..., embed=True),
    service: WarehouseService = Depends(get_warehouse_service)
):
    try:
        pick_list = await service.start_picking(pick_list_id, picker_id)
        return pick_list
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("start_picking_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/warehouses/pick-lists/{pick_list_id}/complete", response_model=PickList)
async def complete_picking(
    pick_list_id: UUID = Path(...),
    service: WarehouseService = Depends(get_warehouse_service)
):
    try:
        pick_list = await service.complete_picking(pick_list_id)
        return pick_list
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("complete_picking_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/warehouses/{warehouse_id}/pick-lists/pending", response_model=List[PickList])
async def get_pending_pick_lists(
    warehouse_id: UUID = Path(...),
    service: WarehouseService = Depends(get_warehouse_service)
):
    try:
        pick_lists = await service.repo.get_pending_pick_lists(warehouse_id)
        return pick_lists
    except Exception as e:
        logger.error("get_pending_pick_lists_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "warehouse_agent", "version": "1.0.0"}

# Create agent instance at module level
agent = WarehouseAgent()

if __name__ == "__main__":
    import uvicorn
    
    # Setup logging
    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    
    port = int(os.getenv("PORT", 8013))
    logger.info(f"Starting Warehouse Agent on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

