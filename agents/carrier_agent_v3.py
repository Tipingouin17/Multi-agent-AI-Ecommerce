"""
Carrier Agent V3 - Production Ready with New Schema
Manages shipping carriers and rate calculations
"""

import os
import sys
import logging
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Import shared modules
from shared.db_models import Carrier, Order, Shipment
from shared.db_connection import get_database_url
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create database engine
engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create FastAPI app
app = FastAPI(title="Carrier Agent V3", version="3.0.0")

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

class RateRequest(BaseModel):
    origin_postal_code: str
    destination_postal_code: str
    weight: float  # in kg
    dimensions: Optional[dict] = None  # length, width, height in cm
    service_type: Optional[str] = "standard"

class ShipmentCreate(BaseModel):
    order_id: int
    carrier_id: int
    service_type: str
    tracking_number: Optional[str] = None
    shipping_cost: float

# ============================================================================
# CARRIER ENDPOINTS
# ============================================================================

@app.get("/health")
def health_check():
    return {"status": "healthy", "agent": "carrier_agent_v3", "version": "3.0.0"}

@app.get("/api/carriers")
def get_carriers(db: Session = Depends(get_db)):
    """Get all active carriers"""
    try:
        carriers = db.query(Carrier).filter(Carrier.is_active == True).all()
        return {"carriers": [carrier.to_dict() for carrier in carriers]}
    except Exception as e:
        logger.error(f"Error getting carriers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/carriers/{carrier_id}")
def get_carrier(carrier_id: int, db: Session = Depends(get_db)):
    """Get a single carrier by ID"""
    try:
        carrier = db.query(Carrier).filter(Carrier.id == carrier_id).first()
        if not carrier:
            raise HTTPException(status_code=404, detail="Carrier not found")
        return carrier.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting carrier: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/carriers/rates")
def calculate_rates(rate_request: RateRequest, db: Session = Depends(get_db)):
    """Calculate shipping rates from all carriers"""
    try:
        carriers = db.query(Carrier).filter(Carrier.is_active == True).all()
        
        rates = []
        for carrier in carriers:
            # Simplified rate calculation
            # In production, this would call carrier APIs
            base_rate = Decimal('10.00')
            weight_rate = Decimal(str(rate_request.weight)) * Decimal('2.50')
            
            # Service type multipliers
            service_multipliers = {
                'standard': Decimal('1.0'),
                'express': Decimal('1.5'),
                'overnight': Decimal('2.0')
            }
            multiplier = service_multipliers.get(rate_request.service_type, Decimal('1.0'))
            
            total_rate = (base_rate + weight_rate) * multiplier
            
            # Estimated delivery days
            delivery_days = {
                'standard': '5-7',
                'express': '2-3',
                'overnight': '1'
            }.get(rate_request.service_type, '5-7')
            
            rates.append({
                'carrier_id': carrier.id,
                'carrier_name': carrier.name,
                'service_type': rate_request.service_type,
                'rate': float(total_rate),
                'currency': 'USD',
                'estimated_delivery_days': delivery_days,
                'available_services': carrier.supported_services or ['standard', 'express']
            })
        
        return {
            'rates': sorted(rates, key=lambda x: x['rate']),
            'request': rate_request.dict()
        }
    
    except Exception as e:
        logger.error(f"Error calculating rates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/carriers/shipments")
def create_shipment(shipment_data: ShipmentCreate, db: Session = Depends(get_db)):
    """Create a new shipment"""
    try:
        # Verify order exists
        order = db.query(Order).filter(Order.id == shipment_data.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Verify carrier exists
        carrier = db.query(Carrier).filter(Carrier.id == shipment_data.carrier_id).first()
        if not carrier:
            raise HTTPException(status_code=404, detail="Carrier not found")
        
        # Generate tracking number if not provided
        tracking_number = shipment_data.tracking_number
        if not tracking_number:
            # Simple tracking number generation
            tracking_number = f"{carrier.code}-{order.order_number}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Create shipment
        shipment = Shipment(
            order_id=shipment_data.order_id,
            carrier_id=shipment_data.carrier_id,
            tracking_number=tracking_number,
            status="pending",
            shipping_cost=Decimal(str(shipment_data.shipping_cost))
        )
        
        db.add(shipment)
        
        # Update order status
        order.fulfillment_status = "processing"
        order.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(shipment)
        
        result = shipment.to_dict()
        result['carrier'] = carrier.to_dict()
        result['order'] = {'id': order.id, 'order_number': order.order_number}
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating shipment: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/shipments")
def get_shipments(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    carrier_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all shipments with filtering"""
    try:
        query = db.query(Shipment)
        
        if status:
            query = query.filter(Shipment.status == status)
        if carrier_id:
            query = query.filter(Shipment.carrier_id == carrier_id)
        
        total = query.count()
        offset = (page - 1) * limit
        shipments = query.order_by(desc(Shipment.created_at)).offset(offset).limit(limit).all()
        
        result = []
        for shipment in shipments:
            shipment_dict = shipment.to_dict()
            if shipment.carrier:
                shipment_dict['carrier'] = {
                    'id': shipment.carrier.id,
                    'name': shipment.carrier.name,
                    'code': shipment.carrier.code
                }
            if shipment.order:
                shipment_dict['order'] = {
                    'id': shipment.order.id,
                    'order_number': shipment.order.order_number
                }
            result.append(shipment_dict)
        
        return {
            "shipments": result,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting shipments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/shipments/{tracking_number}")
def track_shipment(tracking_number: str, db: Session = Depends(get_db)):
    """Track a shipment by tracking number"""
    try:
        shipment = db.query(Shipment).filter(
            Shipment.tracking_number == tracking_number
        ).first()
        
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")
        
        result = shipment.to_dict()
        
        if shipment.carrier:
            result['carrier'] = shipment.carrier.to_dict()
            # Add tracking URL
            if shipment.carrier.tracking_url_template:
                result['tracking_url'] = shipment.carrier.tracking_url_template.replace(
                    '{tracking_number}', tracking_number
                )
        
        if shipment.order:
            result['order'] = shipment.order.to_dict()
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking shipment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/shipments/{shipment_id}/status")
def update_shipment_status(
    shipment_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """Update shipment status"""
    try:
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")
        
        shipment.status = status
        shipment.updated_at = datetime.utcnow()
        
        # Update order fulfillment status
        if shipment.order:
            if status == "in_transit":
                shipment.order.fulfillment_status = "shipped"
                shipment.order.shipped_at = datetime.utcnow()
            elif status == "delivered":
                shipment.order.fulfillment_status = "delivered"
                shipment.order.delivered_at = datetime.utcnow()
        
        db.commit()
        db.refresh(shipment)
        
        return shipment.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating shipment status: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/carriers/stats")
def get_carrier_stats(db: Session = Depends(get_db)):
    """Get carrier statistics"""
    try:
        total_carriers = db.query(func.count(Carrier.id)).scalar()
        active_carriers = db.query(func.count(Carrier.id)).filter(
            Carrier.is_active == True
        ).scalar()
        
        total_shipments = db.query(func.count(Shipment.id)).scalar()
        
        # Shipments by status
        shipment_stats = db.query(
            Shipment.status,
            func.count(Shipment.id)
        ).group_by(Shipment.status).all()
        
        status_distribution = {status: count for status, count in shipment_stats}
        
        return {
            "total_carriers": total_carriers,
            "active_carriers": active_carriers,
            "total_shipments": total_shipments,
            "status_distribution": status_distribution
        }
    
    except Exception as e:
        logger.error(f"Error getting carrier stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8006))
    uvicorn.run(app, host="0.0.0.0", port=port)
