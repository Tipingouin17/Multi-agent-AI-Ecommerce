"""
Returns Agent - Multi-Agent E-Commerce System

This agent manages product returns, RMA (Return Merchandise Authorization),
refund processing, and return analytics.

DATABASE SCHEMA (migration 010_returns_agent.sql):

CREATE TABLE return_reasons (
    reason_id SERIAL PRIMARY KEY,
    reason_code VARCHAR(50) UNIQUE NOT NULL,
    reason_name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'defective', 'wrong_item', 'not_as_described', 'changed_mind', 'damaged', 'other'
    requires_images BOOLEAN DEFAULT false,
    auto_approve BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE return_requests (
    return_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id VARCHAR(100) NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    return_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'received', 'inspected', 'refunded', 'cancelled'
    reason_id INTEGER REFERENCES return_reasons(reason_id),
    reason_details TEXT,
    requested_items JSONB NOT NULL, -- [{order_item_id, quantity, reason}]
    return_method VARCHAR(50), -- 'pickup', 'dropoff', 'mail'
    tracking_number VARCHAR(200),
    images JSONB DEFAULT '[]',
    refund_amount DECIMAL(10, 2),
    refund_method VARCHAR(50), -- 'original', 'store_credit', 'exchange'
    approved_by VARCHAR(100),
    approved_at TIMESTAMP,
    received_at TIMESTAMP,
    inspected_at TIMESTAMP,
    refunded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE return_items (
    return_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    return_id UUID REFERENCES return_requests(return_id),
    order_item_id VARCHAR(100) NOT NULL,
    product_id VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    condition VARCHAR(50), -- 'unopened', 'opened', 'used', 'damaged'
    inspection_notes TEXT,
    approved_quantity INTEGER,
    refund_amount DECIMAL(10, 2),
    restock BOOLEAN DEFAULT true
);

CREATE TABLE return_shipments (
    shipment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    return_id UUID REFERENCES return_requests(return_id),
    carrier VARCHAR(100),
    tracking_number VARCHAR(200),
    label_url VARCHAR(500),
    shipment_status VARCHAR(50) DEFAULT 'pending',
    shipped_at TIMESTAMP,
    delivered_at TIMESTAMP
);

CREATE TABLE return_refunds (
    refund_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    return_id UUID REFERENCES return_requests(return_id),
    payment_id VARCHAR(100),
    refund_amount DECIMAL(10, 2) NOT NULL,
    refund_method VARCHAR(50) NOT NULL,
    refund_status VARCHAR(50) DEFAULT 'pending',
    processed_at TIMESTAMP,
    completed_at TIMESTAMP
);
"""

from datetime import datetime, date
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
class ReturnStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    RECEIVED = "received"
    INSPECTED = "inspected"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class RefundMethod(str, Enum):
    ORIGINAL = "original"
    STORE_CREDIT = "store_credit"
    EXCHANGE = "exchange"

# MODELS
class ReturnReason(BaseModel):
    reason_id: int
    reason_code: str
    reason_name: str
    category: str
    requires_images: bool = False
    auto_approve: bool = False

class ReturnItemRequest(BaseModel):
    order_item_id: str
    product_id: str
    quantity: int
    reason: str

class ReturnRequestCreate(BaseModel):
    order_id: str
    customer_id: str
    reason_id: int
    reason_details: Optional[str] = None
    requested_items: List[ReturnItemRequest]
    return_method: str = "mail"
    refund_method: RefundMethod = RefundMethod.ORIGINAL
    images: List[str] = []

class ReturnRequest(BaseModel):
    return_id: UUID
    order_id: str
    customer_id: str
    return_status: ReturnStatus
    reason_id: int
    reason_details: Optional[str]
    refund_amount: Optional[Decimal]
    refund_method: str
    tracking_number: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# REPOSITORY
class ReturnsRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def get_return_reasons(self) -> List[ReturnReason]:
        query = "SELECT * FROM return_reasons WHERE is_active = true"
        results = await self.db.fetch_all(query)
        return [ReturnReason(**r) for r in results]
    
    async def create_return_request(self, return_data: ReturnRequestCreate) -> ReturnRequest:
        query = """
            INSERT INTO return_requests (order_id, customer_id, reason_id, reason_details,
                                        requested_items, return_method, refund_method, images)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING *
        """
        result = await self.db.fetch_one(
            query, return_data.order_id, return_data.customer_id, return_data.reason_id,
            return_data.reason_details, str([item.dict() for item in return_data.requested_items]),
            return_data.return_method, return_data.refund_method.value, str(return_data.images)
        )
        return ReturnRequest(**result)
    
    async def get_return_request(self, return_id: UUID) -> Optional[ReturnRequest]:
        query = "SELECT * FROM return_requests WHERE return_id = $1"
        result = await self.db.fetch_one(query, return_id)
        return ReturnRequest(**result) if result else None
    
    async def update_return_status(self, return_id: UUID, status: ReturnStatus) -> Optional[ReturnRequest]:
        query = """
            UPDATE return_requests 
            SET return_status = $2,
                approved_at = CASE WHEN $2 = 'approved' THEN CURRENT_TIMESTAMP ELSE approved_at END,
                received_at = CASE WHEN $2 = 'received' THEN CURRENT_TIMESTAMP ELSE received_at END,
                inspected_at = CASE WHEN $2 = 'inspected' THEN CURRENT_TIMESTAMP ELSE inspected_at END,
                refunded_at = CASE WHEN $2 = 'refunded' THEN CURRENT_TIMESTAMP ELSE refunded_at END
            WHERE return_id = $1
            RETURNING *
        """
        result = await self.db.fetch_one(query, return_id, status.value)
        return ReturnRequest(**result) if result else None
    
    async def get_customer_returns(self, customer_id: str, limit: int = 50) -> List[ReturnRequest]:
        query = """
            SELECT * FROM return_requests 
            WHERE customer_id = $1 
            ORDER BY created_at DESC 
            LIMIT $2
        """
        results = await self.db.fetch_all(query, customer_id, limit)
        return [ReturnRequest(**r) for r in results]

# SERVICE
class ReturnsService:
    def __init__(self, repo: ReturnsRepository):
        self.repo = repo
    
    async def create_return(self, return_data: ReturnRequestCreate) -> Dict[str, Any]:
        # Create return request
        return_request = await self.repo.create_return_request(return_data)
        
        # Check if auto-approve
        reasons = await self.repo.get_return_reasons()
        reason = next((r for r in reasons if r.reason_id == return_data.reason_id), None)
        
        if reason and reason.auto_approve:
            return_request = await self.repo.update_return_status(
                return_request.return_id, ReturnStatus.APPROVED
            )
        
        logger.info("return_created", return_id=str(return_request.return_id), 
                   customer_id=return_data.customer_id)
        
        return {
            "return_request": return_request,
            "message": "Return request created successfully",
            "auto_approved": reason.auto_approve if reason else False
        }
    
    async def approve_return(self, return_id: UUID, approved_by: str) -> ReturnRequest:
        return_request = await self.repo.update_return_status(return_id, ReturnStatus.APPROVED)
        if not return_request:
            raise ValueError("Return request not found")
        
        logger.info("return_approved", return_id=str(return_id), approved_by=approved_by)
        return return_request
    
    async def process_refund(self, return_id: UUID, refund_amount: Decimal) -> Dict[str, Any]:
        # Update return with refund amount
        return_request = await self.repo.get_return_request(return_id)
        if not return_request:
            raise ValueError("Return request not found")
        
        # Update status to refunded
        return_request = await self.repo.update_return_status(return_id, ReturnStatus.REFUNDED)
        
        logger.info("refund_processed", return_id=str(return_id), amount=float(refund_amount))
        
        return {
            "return_request": return_request,
            "refund_amount": refund_amount,
            "message": "Refund processed successfully"
        }

# FASTAPI APP
app = FastAPI(title="Returns Agent API", version="1.0.0")

async def get_returns_service() -> ReturnsService:
    db_manager = await get_database_manager()
    repo = ReturnsRepository(db_manager)
    return ReturnsService(repo)

# ENDPOINTS
@app.get("/api/v1/returns/reasons", response_model=List[ReturnReason])
async def get_return_reasons(service: ReturnsService = Depends(get_returns_service)):
    try:
        reasons = await service.repo.get_return_reasons()
        return reasons
    except Exception as e:
        logger.error("get_return_reasons_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/returns", response_model=Dict[str, Any])
async def create_return(
    return_data: ReturnRequestCreate = Body(...),
    service: ReturnsService = Depends(get_returns_service)
):
    try:
        result = await service.create_return(return_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("create_return_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/returns/{return_id}", response_model=ReturnRequest)
async def get_return(
    return_id: UUID = Path(...),
    service: ReturnsService = Depends(get_returns_service)
):
    try:
        return_request = await service.repo.get_return_request(return_id)
        if not return_request:
            raise HTTPException(status_code=404, detail="Return not found")
        return return_request
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_return_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/returns/{return_id}/approve", response_model=ReturnRequest)
async def approve_return(
    return_id: UUID = Path(...),
    approved_by: str = Body(..., embed=True),
    service: ReturnsService = Depends(get_returns_service)
):
    try:
        return_request = await service.approve_return(return_id, approved_by)
        return return_request
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("approve_return_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/returns/{return_id}/refund", response_model=Dict[str, Any])
async def process_refund(
    return_id: UUID = Path(...),
    refund_amount: Decimal = Body(..., embed=True),
    service: ReturnsService = Depends(get_returns_service)
):
    try:
        result = await service.process_refund(return_id, refund_amount)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("process_refund_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/returns/customer/{customer_id}", response_model=List[ReturnRequest])
async def get_customer_returns(
    customer_id: str = Path(...),
    limit: int = Query(50, ge=1, le=100),
    service: ReturnsService = Depends(get_returns_service)
):
    try:
        returns = await service.repo.get_customer_returns(customer_id, limit)
        return returns
    except Exception as e:
        logger.error("get_customer_returns_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "returns_agent", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)

