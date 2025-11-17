"""
Customer Agent V3 - Production Ready with New Schema
Manages customers and their data using the unified database schema
"""

import os
import sys
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_, desc

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Import shared modules
from shared.db_models import Customer, User, Address, Order
from shared.db_connection import get_database_url
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create database engine
engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create FastAPI app
app = FastAPI(title="Customer Agent V3", version="3.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class CustomerCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    
class CustomerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None

class AddressCreate(BaseModel):
    customer_id: int
    address_type: str  # shipping, billing, both
    street_address: str
    city: str
    state: str
    postal_code: str
    country: str
    is_default: bool = False

# ============================================================================
# CUSTOMER ENDPOINTS
# ============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent": "customer_agent_v3", "version": "3.0.0"}

@app.get("/api/customers")
def get_customers(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    segment: Optional[str] = None,
    sort_by: str = Query("created_at", regex="^(created_at|total_orders|lifetime_value)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """Get all customers with filtering and pagination"""
    try:
        query = db.query(Customer).join(User)
        
        # Search filter
        if search:
            query = query.filter(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.first_name.ilike(f"%{search}%"),
                    User.last_name.ilike(f"%{search}%")
                )
            )
        
        # Segment filter
        if segment:
            query = query.filter(Customer.segment == segment)
        
        # Get total count
        total = query.count()
        
        # Apply sorting
        sort_column = getattr(Customer, sort_by)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (page - 1) * limit
        customers = query.offset(offset).limit(limit).all()
        
        # Build response
        result = []
        for customer in customers:
            customer_dict = customer.to_dict()
            if customer.user:
                customer_dict['user'] = {
                    'id': customer.user.id,
                    'email': customer.user.email,
                    'first_name': customer.user.first_name,
                    'last_name': customer.user.last_name,
                    'phone': customer.user.phone
                }
            result.append(customer_dict)
        
        return {
            "customers": result,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/customers/{customer_id}")
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """Get a single customer by ID with full details"""
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        customer_dict = customer.to_dict()
        
        # Add user information
        if customer.user:
            customer_dict['user'] = customer.user.to_dict()
        
        # Add addresses
        addresses = db.query(Address).filter(Address.customer_id == customer_id).all()
        customer_dict['addresses'] = [addr.to_dict() for addr in addresses]
        
        # Add order statistics
        orders = db.query(Order).filter(Order.customer_id == customer_id).all()
        customer_dict['order_stats'] = {
            'total_orders': len(orders),
            'pending_orders': len([o for o in orders if o.status == 'pending']),
            'completed_orders': len([o for o in orders if o.status == 'delivered'])
        }
        
        return customer_dict
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/customers")
def create_customer(customer_data: CustomerCreate, db: Session = Depends(get_db)):
    """Create a new customer"""
    try:
        # Check if user with email exists
        existing_user = db.query(User).filter(User.email == customer_data.email).first()
        
        if existing_user:
            # Check if customer record exists
            existing_customer = db.query(Customer).filter(Customer.user_id == existing_user.id).first()
            if existing_customer:
                raise HTTPException(status_code=400, detail="Customer already exists")
            
            # Create customer for existing user
            customer = Customer(user_id=existing_user.id)
            db.add(customer)
            db.commit()
            db.refresh(customer)
            return customer.to_dict()
        
        # Create new user
        user = User(
            email=customer_data.email,
            username=customer_data.email.split('@')[0],
            first_name=customer_data.first_name,
            last_name=customer_data.last_name,
            phone=customer_data.phone,
            role="customer"
        )
        db.add(user)
        db.flush()
        
        # Create customer
        customer = Customer(user_id=user.id)
        db.add(customer)
        
        db.commit()
        db.refresh(customer)
        db.refresh(user)
        
        result = customer.to_dict()
        result['user'] = user.to_dict()
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/customers/{customer_id}")
def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db)
):
    """Update a customer"""
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Update customer fields
        update_data = customer_data.dict(exclude_unset=True)
        
        # Update user fields if provided
        if customer.user and (customer_data.first_name or customer_data.last_name or customer_data.phone):
            if customer_data.first_name:
                customer.user.first_name = customer_data.first_name
            if customer_data.last_name:
                customer.user.last_name = customer_data.last_name
            if customer_data.phone:
                customer.user.phone = customer_data.phone
        
        # Update customer-specific fields
        if customer_data.notes is not None:
            customer.notes = customer_data.notes
        if customer_data.tags is not None:
            customer.tags = customer_data.tags
        
        customer.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(customer)
        
        return customer.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customer: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/customers/{customer_id}/orders")
def get_customer_orders(
    customer_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get all orders for a customer"""
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        query = db.query(Order).filter(Order.customer_id == customer_id).order_by(desc(Order.created_at))
        
        total = query.count()
        offset = (page - 1) * limit
        orders = query.offset(offset).limit(limit).all()
        
        return {
            "orders": [order.to_dict() for order in orders],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/customers/stats")
def get_customer_stats(db: Session = Depends(get_db)):
    """Get customer statistics"""
    try:
        total_customers = db.query(func.count(Customer.id)).scalar()
        active_customers = db.query(func.count(Customer.id)).filter(
            Customer.status == "active"
        ).scalar()
        
        # Calculate average lifetime value
        avg_lifetime_value = db.query(func.avg(Customer.lifetime_value)).scalar() or 0
        
        # Get segment distribution
        segments = db.query(
            Customer.segment,
            func.count(Customer.id)
        ).group_by(Customer.segment).all()
        
        segment_distribution = {segment: count for segment, count in segments}
        
        return {
            "total_customers": total_customers,
            "active_customers": active_customers,
            "average_lifetime_value": float(avg_lifetime_value),
            "segment_distribution": segment_distribution
        }
    
    except Exception as e:
        logger.error(f"Error getting customer stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ADDRESS ENDPOINTS
# ============================================================================

@app.post("/api/customers/{customer_id}/addresses")
def create_address(
    customer_id: int,
    address_data: AddressCreate,
    db: Session = Depends(get_db)
):
    """Create a new address for a customer"""
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # If this is set as default, unset other defaults
        if address_data.is_default:
            db.query(Address).filter(
                and_(
                    Address.customer_id == customer_id,
                    Address.is_default == True
                )
            ).update({"is_default": False})
        
        address = Address(
            customer_id=customer_id,
            address_type=address_data.address_type,
            street_address=address_data.street_address,
            city=address_data.city,
            state=address_data.state,
            postal_code=address_data.postal_code,
            country=address_data.country,
            is_default=address_data.is_default
        )
        
        db.add(address)
        db.commit()
        db.refresh(address)
        
        return address.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating address: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/customers/{customer_id}/addresses")
def get_customer_addresses(customer_id: int, db: Session = Depends(get_db)):
    """Get all addresses for a customer"""
    try:
        addresses = db.query(Address).filter(Address.customer_id == customer_id).all()
        return {"addresses": [addr.to_dict() for addr in addresses]}
    except Exception as e:
        logger.error(f"Error getting customer addresses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# CUSTOMER PROFILE ENDPOINTS
# ============================================================================

@app.get("/profile")
def get_customer_profile(
    customer_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get customer profile"""
    try:
        if customer_id:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
        elif user_id:
            customer = db.query(Customer).filter(Customer.user_id == user_id).first()
        else:
            raise HTTPException(status_code=400, detail="customer_id or user_id required")
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return customer.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/profile")
def update_customer_profile(
    profileData: Dict[str, Any],
    customer_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Update customer profile"""
    try:
        if customer_id:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
        elif user_id:
            customer = db.query(Customer).filter(Customer.user_id == user_id).first()
        else:
            raise HTTPException(status_code=400, detail="customer_id or user_id required")
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Update allowed fields
        allowed_fields = ['phone', 'preferences']
        for field in allowed_fields:
            if field in profileData:
                setattr(customer, field, profileData[field])
        
        customer.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(customer)
        
        return customer.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customer profile: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/addresses")
def get_addresses(
    customer_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get customer addresses"""
    try:
        if user_id:
            addresses = db.query(Address).filter(Address.user_id == user_id).all()
        elif customer_id:
            # Get user_id from customer
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return {"addresses": []}
            addresses = db.query(Address).filter(Address.user_id == customer.user_id).all()
        else:
            return {"addresses": []}
        
        return {"addresses": [addr.to_dict() for addr in addresses]}
    except Exception as e:
        logger.error(f"Error getting addresses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/addresses/{address_id}")
def delete_address(
    address_id: int,
    db: Session = Depends(get_db)
):
    """Delete customer address"""
    try:
        address = db.query(Address).filter(Address.id == address_id).first()
        
        if not address:
            raise HTTPException(status_code=404, detail="Address not found")
        
        db.delete(address)
        db.commit()
        
        return {"success": True, "message": "Address deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting address: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8007))
    uvicorn.run(app, host="0.0.0.0", port=port)
