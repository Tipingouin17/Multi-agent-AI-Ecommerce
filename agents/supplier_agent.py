"""
Supplier Agent - Multi-Agent E-Commerce System

This agent manages supplier relationships, purchase orders, supplier performance tracking,
lead time management, and cost analysis.

DATABASE SCHEMA (migration 015_supplier_agent.sql):

CREATE TABLE suppliers (
    supplier_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_code VARCHAR(50) UNIQUE NOT NULL,
    supplier_name VARCHAR(200) NOT NULL,
    contact_info JSONB NOT NULL,
    payment_terms VARCHAR(100),
    lead_time_days INTEGER DEFAULT 7,
    minimum_order_quantity INTEGER DEFAULT 1,
    rating DECIMAL(3, 2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE supplier_products (
    supplier_product_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID REFERENCES suppliers(supplier_id),
    product_id VARCHAR(100) NOT NULL,
    supplier_sku VARCHAR(100),
    cost DECIMAL(10, 2) NOT NULL,
    moq INTEGER DEFAULT 1, -- Minimum Order Quantity
    lead_time_days INTEGER,
    is_preferred BOOLEAN DEFAULT false,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE purchase_orders (
    po_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_number VARCHAR(50) UNIQUE NOT NULL,
    supplier_id UUID REFERENCES suppliers(supplier_id),
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'sent', 'confirmed', 'partially_received', 'received', 'cancelled'
    items JSONB NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    expected_delivery_date DATE,
    actual_delivery_date DATE,
    notes TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE po_receipts (
    receipt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_id UUID REFERENCES purchase_orders(po_id),
    received_items JSONB NOT NULL,
    received_by VARCHAR(100),
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE TABLE supplier_performance (
    performance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_id UUID REFERENCES suppliers(supplier_id),
    metric_type VARCHAR(50) NOT NULL, -- 'on_time_delivery', 'quality', 'cost', 'responsiveness'
    metric_value DECIMAL(5, 2) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

from datetime import datetime, date, timedelta
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

from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.database import DatabaseManager, get_database_manager

logger = structlog.get_logger(__name__)

# ENUMS
class POStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    CONFIRMED = "confirmed"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"

# MODELS
class Supplier(BaseModel):
    supplier_id: UUID
    supplier_code: str
    supplier_name: str
    contact_info: Dict[str, Any]
    payment_terms: Optional[str]
    lead_time_days: int
    rating: Decimal
    is_active: bool

    class Config:
        from_attributes = True

class SupplierProduct(BaseModel):
    supplier_product_id: UUID
    supplier_id: UUID
    product_id: str
    supplier_sku: Optional[str]
    cost: Decimal
    moq: int
    lead_time_days: Optional[int]
    is_preferred: bool

    class Config:
        from_attributes = True

class POItem(BaseModel):
    product_id: str
    quantity: int
    unit_cost: Decimal

class PurchaseOrderCreate(BaseModel):
    supplier_id: UUID
    items: List[POItem]
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None
    created_by: str

class PurchaseOrder(BaseModel):
    po_id: UUID
    po_number: str
    supplier_id: UUID
    status: POStatus
    items: List[Dict[str, Any]]
    total_amount: Decimal
    expected_delivery_date: Optional[date]
    created_at: datetime

    class Config:
        from_attributes = True

class POReceiptCreate(BaseModel):
    po_id: UUID
    received_items: List[Dict[str, Any]]
    received_by: str
    notes: Optional[str] = None

class SupplierPerformanceMetrics(BaseModel):
    supplier_id: UUID
    on_time_delivery_rate: Decimal
    quality_score: Decimal
    cost_competitiveness: Decimal
    responsiveness_score: Decimal
    overall_rating: Decimal

# REPOSITORY
class SupplierRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def get_suppliers(self, active_only: bool = True) -> List[Supplier]:
        query = "SELECT * FROM suppliers"
        if active_only:
            query += " WHERE is_active = true"
        query += " ORDER BY rating DESC"
        results = await self.db.fetch_all(query)
        return [Supplier(**r) for r in results]
    
    async def get_supplier(self, supplier_id: UUID) -> Optional[Supplier]:
        query = "SELECT * FROM suppliers WHERE supplier_id = $1"
        result = await self.db.fetch_one(query, supplier_id)
        return Supplier(**result) if result else None
    
    async def get_supplier_products(
        self, supplier_id: UUID, product_id: Optional[str] = None
    ) -> List[SupplierProduct]:
        query = "SELECT * FROM supplier_products WHERE supplier_id = $1"
        params = [supplier_id]
        
        if product_id:
            query += " AND product_id = $2"
            params.append(product_id)
        
        results = await self.db.fetch_all(query, *params)
        return [SupplierProduct(**r) for r in results]
    
    async def create_purchase_order(self, po_data: PurchaseOrderCreate) -> PurchaseOrder:
        # Generate PO number
        po_number = f"PO-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
        
        # Calculate total
        total_amount = sum(item.quantity * item.unit_cost for item in po_data.items)
        
        query = """
            INSERT INTO purchase_orders (po_number, supplier_id, items, total_amount,
                                        expected_delivery_date, notes, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
        """
        result = await self.db.fetch_one(
            query, po_number, po_data.supplier_id,
            str([item.dict() for item in po_data.items]), total_amount,
            po_data.expected_delivery_date, po_data.notes, po_data.created_by
        )
        return PurchaseOrder(**result)
    
    async def get_purchase_order(self, po_id: UUID) -> Optional[PurchaseOrder]:
        query = "SELECT * FROM purchase_orders WHERE po_id = $1"
        result = await self.db.fetch_one(query, po_id)
        return PurchaseOrder(**result) if result else None
    
    async def update_po_status(self, po_id: UUID, status: POStatus) -> Optional[PurchaseOrder]:
        query = """
            UPDATE purchase_orders
            SET status = $2,
                actual_delivery_date = CASE WHEN $2 = 'received' THEN CURRENT_DATE ELSE actual_delivery_date END
            WHERE po_id = $1
            RETURNING *
        """
        result = await self.db.fetch_one(query, po_id, status.value)
        return PurchaseOrder(**result) if result else None
    
    async def create_po_receipt(self, receipt_data: POReceiptCreate) -> UUID:
        query = """
            INSERT INTO po_receipts (po_id, received_items, received_by, notes)
            VALUES ($1, $2, $3, $4)
            RETURNING receipt_id
        """
        result = await self.db.fetch_one(
            query, receipt_data.po_id, str(receipt_data.received_items),
            receipt_data.received_by, receipt_data.notes
        )
        return result['receipt_id']
    
    async def get_supplier_performance(self, supplier_id: UUID) -> Optional[SupplierPerformanceMetrics]:
        """Calculate supplier performance metrics."""
        # In production, query supplier_performance table
        # For now, return simulated metrics
        return SupplierPerformanceMetrics(
            supplier_id=supplier_id,
            on_time_delivery_rate=Decimal("92.5"),
            quality_score=Decimal("88.0"),
            cost_competitiveness=Decimal("85.0"),
            responsiveness_score=Decimal("90.0"),
            overall_rating=Decimal("88.9")
        )

# SERVICE
class SupplierService:
    def __init__(self, repo: SupplierRepository):
        self.repo = repo
    
    async def find_best_supplier(self, product_id: str, quantity: int) -> Optional[Dict[str, Any]]:
        """Find best supplier for a product based on cost, lead time, and rating."""
        suppliers = await self.repo.get_suppliers(active_only=True)
        
        best_supplier = None
        best_score = -1
        
        for supplier in suppliers:
            supplier_products = await self.repo.get_supplier_products(
                supplier.supplier_id, product_id
            )
            
            if not supplier_products:
                continue
            
            product = supplier_products[0]
            
            # Check MOQ
            if quantity < product.moq:
                continue
            
            # Calculate score (lower cost + shorter lead time + higher rating = better)
            cost_score = 100 - min(100, float(product.cost))
            lead_time_score = 100 - min(100, product.lead_time_days or supplier.lead_time_days)
            rating_score = float(supplier.rating) * 10
            
            total_score = (cost_score * 0.4) + (lead_time_score * 0.3) + (rating_score * 0.3)
            
            if total_score > best_score:
                best_score = total_score
                best_supplier = {
                    'supplier': supplier,
                    'product': product,
                    'score': total_score
                }
        
        return best_supplier
    
    async def create_purchase_order(self, po_data: PurchaseOrderCreate) -> PurchaseOrder:
        """Create purchase order."""
        po = await self.repo.create_purchase_order(po_data)
        
        logger.info("purchase_order_created", po_id=str(po.po_id),
                   po_number=po.po_number, supplier_id=str(po_data.supplier_id))
        
        return po
    
    async def receive_purchase_order(self, receipt_data: POReceiptCreate) -> Dict[str, Any]:
        """Receive purchase order items."""
        # Create receipt
        receipt_id = await self.repo.create_po_receipt(receipt_data)
        
        # Update PO status
        po = await self.repo.get_purchase_order(receipt_data.po_id)
        if not po:
            raise ValueError("Purchase order not found")
        
        # Check if fully received
        # In production, compare received_items with po.items
        new_status = POStatus.RECEIVED  # Simplified
        
        await self.repo.update_po_status(receipt_data.po_id, new_status)
        
        logger.info("purchase_order_received", po_id=str(receipt_data.po_id),
                   receipt_id=str(receipt_id))
        
        return {"receipt_id": receipt_id, "status": new_status.value}

# FASTAPI APP
app = FastAPI(title="Supplier Agent API", version="1.0.0")

async def get_supplier_service() -> SupplierService:
    db_manager = await get_database_manager()
    repo = SupplierRepository(db_manager)
    return SupplierService(repo)

# ENDPOINTS
@app.get("/api/v1/suppliers", response_model=List[Supplier])
async def get_suppliers(
    active_only: bool = Query(True),
    service: SupplierService = Depends(get_supplier_service)
):
    try:
        suppliers = await service.repo.get_suppliers(active_only)
        return suppliers
    except Exception as e:
        logger.error("get_suppliers_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/suppliers/{supplier_id}", response_model=Supplier)
async def get_supplier(
    supplier_id: UUID = Path(...),
    service: SupplierService = Depends(get_supplier_service)
):
    try:
        supplier = await service.repo.get_supplier(supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        return supplier
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_supplier_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/suppliers/{supplier_id}/products", response_model=List[SupplierProduct])
async def get_supplier_products(
    supplier_id: UUID = Path(...),
    product_id: Optional[str] = Query(None),
    service: SupplierService = Depends(get_supplier_service)
):
    try:
        products = await service.repo.get_supplier_products(supplier_id, product_id)
        return products
    except Exception as e:
        logger.error("get_supplier_products_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/suppliers/find-best/{product_id}")
async def find_best_supplier(
    product_id: str = Path(...),
    quantity: int = Query(..., ge=1),
    service: SupplierService = Depends(get_supplier_service)
):
    try:
        result = await service.find_best_supplier(product_id, quantity)
        if not result:
            raise HTTPException(status_code=404, detail="No suitable supplier found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("find_best_supplier_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/suppliers/purchase-orders", response_model=PurchaseOrder)
async def create_purchase_order(
    po_data: PurchaseOrderCreate = Body(...),
    service: SupplierService = Depends(get_supplier_service)
):
    try:
        po = await service.create_purchase_order(po_data)
        return po
    except Exception as e:
        logger.error("create_purchase_order_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/suppliers/purchase-orders/{po_id}", response_model=PurchaseOrder)
async def get_purchase_order(
    po_id: UUID = Path(...),
    service: SupplierService = Depends(get_supplier_service)
):
    try:
        po = await service.repo.get_purchase_order(po_id)
        if not po:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        return po
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_purchase_order_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/suppliers/purchase-orders/receive")
async def receive_purchase_order(
    receipt_data: POReceiptCreate = Body(...),
    service: SupplierService = Depends(get_supplier_service)
):
    try:
        result = await service.receive_purchase_order(receipt_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("receive_purchase_order_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/suppliers/{supplier_id}/performance", response_model=SupplierPerformanceMetrics)
async def get_supplier_performance(
    supplier_id: UUID = Path(...),
    service: SupplierService = Depends(get_supplier_service)
):
    try:
        metrics = await service.repo.get_supplier_performance(supplier_id)
        if not metrics:
            raise HTTPException(status_code=404, detail="Performance metrics not found")
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_supplier_performance_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "supplier_agent", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8014)

