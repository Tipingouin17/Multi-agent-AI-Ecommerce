"""
Returns Agent V3 - Production Ready with New Schema
Manages product returns, refunds, and exchanges
"""

import os
import sys
import logging
from typing import Optional
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Import shared modules
from shared.db_models import Return, Order, OrderItem, Product, Customer
from shared.db_connection import get_database_url
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create database engine
engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create FastAPI app
app = FastAPI(title="Returns Agent V3", version="3.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ReturnCreate(BaseModel):
    order_id: int
    order_item_id: Optional[int] = None
    reason: str
    quantity: int = 1
    return_type: str = "refund"  # refund or exchange
    comments: Optional[str] = None

class ReturnUpdate(BaseModel):
    status: Optional[str] = None
    resolution: Optional[str] = None
    admin_notes: Optional[str] = None

# ============================================================================
# RETURNS ENDPOINTS
# ============================================================================

@app.get("/health")
def health_check():
    return {"status": "healthy", "agent": "returns_agent_v3", "version": "3.0.0"}

@app.get("/api/returns")
def get_returns(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    return_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all returns with filtering"""
    try:
        query = db.query(Return)
        
        if status:
            query = query.filter(Return.status == status)
        if return_type:
            query = query.filter(Return.return_type == return_type)
        
        total = query.count()
        offset = (page - 1) * limit
        returns = query.order_by(desc(Return.created_at)).offset(offset).limit(limit).all()
        
        result = []
        for ret in returns:
            ret_dict = ret.to_dict()
            if ret.order:
                ret_dict['order'] = {
                    'id': ret.order.id,
                    'order_number': ret.order.order_number
                }
            result.append(ret_dict)
        
        return {
            "returns": result,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting returns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/returns/{return_id}")
def get_return(return_id: int, db: Session = Depends(get_db)):
    """Get a single return by ID"""
    try:
        ret = db.query(Return).filter(Return.id == return_id).first()
        if not ret:
            raise HTTPException(status_code=404, detail="Return not found")
        
        ret_dict = ret.to_dict()
        if ret.order:
            ret_dict['order'] = ret.order.to_dict()
        
        return ret_dict
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting return: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/returns")
def create_return(return_data: ReturnCreate, db: Session = Depends(get_db)):
    """Create a new return request"""
    try:
        # Verify order exists
        order = db.query(Order).filter(Order.id == return_data.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Check if order is eligible for return (within 30 days)
        if order.delivered_at:
            days_since_delivery = (datetime.utcnow() - order.delivered_at).days
            if days_since_delivery > 30:
                raise HTTPException(
                    status_code=400,
                    detail="Return window has expired (30 days from delivery)"
                )
        
        # Generate return number
        return_count = db.query(func.count(Return.id)).scalar()
        return_number = f"RET-{return_count + 1:06d}"
        
        # Create return
        ret = Return(
            return_number=return_number,
            order_id=return_data.order_id,
            order_item_id=return_data.order_item_id,
            reason=return_data.reason,
            quantity=return_data.quantity,
            return_type=return_data.return_type,
            comments=return_data.comments,
            status="pending"
        )
        
        db.add(ret)
        db.commit()
        db.refresh(ret)
        
        return ret.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating return: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/returns/{return_id}")
def update_return(
    return_id: int,
    return_data: ReturnUpdate,
    db: Session = Depends(get_db)
):
    """Update a return"""
    try:
        ret = db.query(Return).filter(Return.id == return_id).first()
        if not ret:
            raise HTTPException(status_code=404, detail="Return not found")
        
        # Update fields
        update_data = return_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(ret, field, value)
        
        # Update timestamps based on status
        if return_data.status == "approved":
            ret.approved_at = datetime.utcnow()
        elif return_data.status == "completed":
            ret.completed_at = datetime.utcnow()
        
        ret.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(ret)
        
        return ret.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating return: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/returns/{return_id}/approve")
def approve_return(return_id: int, db: Session = Depends(get_db)):
    """Approve a return request"""
    try:
        ret = db.query(Return).filter(Return.id == return_id).first()
        if not ret:
            raise HTTPException(status_code=404, detail="Return not found")
        
        if ret.status != "pending":
            raise HTTPException(status_code=400, detail="Return is not in pending state")
        
        ret.status = "approved"
        ret.approved_at = datetime.utcnow()
        ret.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(ret)
        
        return ret.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving return: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/returns/{return_id}/reject")
def reject_return(
    return_id: int,
    reason: str,
    db: Session = Depends(get_db)
):
    """Reject a return request"""
    try:
        ret = db.query(Return).filter(Return.id == return_id).first()
        if not ret:
            raise HTTPException(status_code=404, detail="Return not found")
        
        if ret.status != "pending":
            raise HTTPException(status_code=400, detail="Return is not in pending state")
        
        ret.status = "rejected"
        ret.resolution = f"Rejected: {reason}"
        ret.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(ret)
        
        return ret.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting return: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/returns/{return_id}/complete")
def complete_return(return_id: int, db: Session = Depends(get_db)):
    """Mark a return as completed"""
    try:
        ret = db.query(Return).filter(Return.id == return_id).first()
        if not ret:
            raise HTTPException(status_code=404, detail="Return not found")
        
        if ret.status not in ["approved", "received"]:
            raise HTTPException(status_code=400, detail="Return must be approved or received")
        
        ret.status = "completed"
        ret.completed_at = datetime.utcnow()
        ret.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(ret)
        
        return ret.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing return: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/returns/stats")
def get_return_stats(db: Session = Depends(get_db)):
    """Get return statistics"""
    try:
        total_returns = db.query(func.count(Return.id)).scalar()
        
        # Status distribution
        status_stats = db.query(
            Return.status,
            func.count(Return.id)
        ).group_by(Return.status).all()
        
        status_distribution = {status: count for status, count in status_stats}
        
        # Return type distribution
        type_stats = db.query(
            Return.return_type,
            func.count(Return.id)
        ).group_by(Return.return_type).all()
        
        type_distribution = {rtype: count for rtype, count in type_stats}
        
        # Return rate (returns / total orders)
        total_orders = db.query(func.count(Order.id)).scalar()
        return_rate = (total_returns / total_orders * 100) if total_orders > 0 else 0
        
        return {
            "total_returns": total_returns,
            "status_distribution": status_distribution,
            "type_distribution": type_distribution,
            "return_rate": round(return_rate, 2)
        }
    
    except Exception as e:
        logger.error(f"Error getting return stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8009))
    uvicorn.run(app, host="0.0.0.0", port=port)
