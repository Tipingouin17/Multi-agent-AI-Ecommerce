"""
Offers Management Agent V3
Manages special offers, promotions, and deals across products and marketplaces
"""

import os
import sys
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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
from shared.db_models import (
    Offer, OfferProduct, OfferMarketplace, OfferUsage, OfferAnalytics,
    Product, Marketplace, Customer, Order
)
from shared.db_connection import get_database_url
from shared.auth import get_current_user, require_merchant, User as AuthUser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create database engine
engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create FastAPI app
app = FastAPI(title="Offers Management Agent V3", version="3.0.0")

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

class OfferCreate(BaseModel):
    name: str
    description: Optional[str] = None
    offer_type: str  # percentage, fixed_amount, buy_x_get_y, bundle
    discount_type: Optional[str] = None  # percentage, fixed
    discount_value: Optional[float] = None
    min_purchase_amount: Optional[float] = None
    max_discount_amount: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_scheduled: bool = False
    target_customer_groups: Optional[List[int]] = []
    target_marketplaces: Optional[List[int]] = []
    target_products: Optional[List[int]] = []
    target_categories: Optional[List[str]] = []
    usage_limit_per_customer: Optional[int] = None
    total_usage_limit: Optional[int] = None
    conditions: Optional[Dict[str, Any]] = {}
    stackable: bool = False
    priority: int = 0
    display_badge: Optional[str] = None
    display_banner_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class OfferUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    discount_value: Optional[float] = None
    min_purchase_amount: Optional[float] = None
    max_discount_amount: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_scheduled: Optional[bool] = None
    target_customer_groups: Optional[List[int]] = None
    target_marketplaces: Optional[List[int]] = None
    target_products: Optional[List[int]] = None
    target_categories: Optional[List[str]] = None
    usage_limit_per_customer: Optional[int] = None
    total_usage_limit: Optional[int] = None
    conditions: Optional[Dict[str, Any]] = None
    stackable: Optional[bool] = None
    priority: Optional[int] = None
    display_badge: Optional[str] = None
    display_banner_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class OfferProductAdd(BaseModel):
    product_id: int
    custom_discount_value: Optional[float] = None

class OfferMarketplaceAdd(BaseModel):
    marketplace_id: int

# ============================================================================
# OFFER ENDPOINTS
# ============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent": "offers_agent_v3", "version": "3.0.0"}

@app.get("/api/offers")
async def get_offers(
    status: Optional[str] = None,
    offer_type: Optional[str] = None,
    active_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all offers with optional filtering"""
    try:
        query = db.query(Offer)
        
        # Apply filters
        if status:
            query = query.filter(Offer.status == status)
        
        if offer_type:
            query = query.filter(Offer.offer_type == offer_type)
        
        if active_only:
            now = datetime.utcnow()
            query = query.filter(
                and_(
                    Offer.status == 'active',
                    or_(
                        Offer.start_date.is_(None),
                        Offer.start_date <= now
                    ),
                    or_(
                        Offer.end_date.is_(None),
                        Offer.end_date >= now
                    )
                )
            )
        
        # Order by priority and creation date
        query = query.order_by(desc(Offer.priority), desc(Offer.created_at))
        
        # Pagination
        total = query.count()
        offers = query.offset(skip).limit(limit).all()
        
        return {
            "offers": [offer.to_dict() for offer in offers],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error getting offers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/offers/{offer_id}")
async def get_offer(
    offer_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get offer by ID with related data"""
    try:
        offer = db.query(Offer).options(
            joinedload(Offer.products),
            joinedload(Offer.marketplaces)
        ).filter(Offer.id == offer_id).first()
        
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")
        
        offer_dict = offer.to_dict()
        
        # Add related products
        offer_dict["products"] = [
            {
                **op.to_dict(),
                "product": op.product.to_dict() if op.product else None
            }
            for op in offer.products
        ]
        
        # Add related marketplaces
        offer_dict["marketplaces"] = [
            {
                **om.to_dict(),
                "marketplace": om.marketplace.to_dict() if om.marketplace else None
            }
            for om in offer.marketplaces
        ]
        
        return offer_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting offer {offer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/offers")
async def create_offer(
    offer_data: OfferCreate,
    current_user: AuthUser = Depends(require_merchant),
    db: Session = Depends(get_db)
):
    """Create a new offer"""
    try:
        # Create offer
        offer = Offer(
            name=offer_data.name,
            description=offer_data.description,
            offer_type=offer_data.offer_type,
            status='draft',
            discount_type=offer_data.discount_type,
            discount_value=offer_data.discount_value,
            min_purchase_amount=offer_data.min_purchase_amount,
            max_discount_amount=offer_data.max_discount_amount,
            start_date=offer_data.start_date,
            end_date=offer_data.end_date,
            is_scheduled=offer_data.is_scheduled,
            target_customer_groups=offer_data.target_customer_groups,
            target_marketplaces=offer_data.target_marketplaces,
            target_products=offer_data.target_products,
            target_categories=offer_data.target_categories,
            usage_limit_per_customer=offer_data.usage_limit_per_customer,
            total_usage_limit=offer_data.total_usage_limit,
            conditions=offer_data.conditions,
            stackable=offer_data.stackable,
            priority=offer_data.priority,
            display_badge=offer_data.display_badge,
            display_banner_url=offer_data.display_banner_url,
            created_by=int(current_user.user_id),
            metadata=offer_data.metadata
        )
        
        db.add(offer)
        db.commit()
        db.refresh(offer)
        
        logger.info(f"Created offer: {offer.id} - {offer.name}")
        
        return offer.to_dict()
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating offer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/offers/{offer_id}")
async def update_offer(
    offer_id: int,
    offer_data: OfferUpdate,
    current_user: AuthUser = Depends(require_merchant),
    db: Session = Depends(get_db)
):
    """Update an existing offer"""
    try:
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")
        
        # Update fields
        update_data = offer_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(offer, field, value)
        
        db.commit()
        db.refresh(offer)
        
        logger.info(f"Updated offer: {offer.id}")
        
        return offer.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating offer {offer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/offers/{offer_id}")
async def delete_offer(
    offer_id: int,
    current_user: AuthUser = Depends(require_merchant),
    db: Session = Depends(get_db)
):
    """Delete an offer"""
    try:
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")
        
        db.delete(offer)
        db.commit()
        
        logger.info(f"Deleted offer: {offer_id}")
        
        return {"message": "Offer deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting offer {offer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# OFFER PRODUCTS ENDPOINTS
# ============================================================================

@app.post("/api/offers/{offer_id}/products")
async def add_product_to_offer(
    offer_id: int,
    product_data: OfferProductAdd,
    current_user: AuthUser = Depends(require_merchant),
    db: Session = Depends(get_db)
):
    """Add a product to an offer"""
    try:
        # Check if offer exists
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")
        
        # Check if product exists
        product = db.query(Product).filter(Product.id == product_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Check if already added
        existing = db.query(OfferProduct).filter(
            and_(
                OfferProduct.offer_id == offer_id,
                OfferProduct.product_id == product_data.product_id
            )
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Product already added to this offer")
        
        # Add product to offer
        offer_product = OfferProduct(
            offer_id=offer_id,
            product_id=product_data.product_id,
            custom_discount_value=product_data.custom_discount_value
        )
        
        db.add(offer_product)
        db.commit()
        db.refresh(offer_product)
        
        logger.info(f"Added product {product_data.product_id} to offer {offer_id}")
        
        return offer_product.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding product to offer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/offers/{offer_id}/products/{product_id}")
async def remove_product_from_offer(
    offer_id: int,
    product_id: int,
    current_user: AuthUser = Depends(require_merchant),
    db: Session = Depends(get_db)
):
    """Remove a product from an offer"""
    try:
        offer_product = db.query(OfferProduct).filter(
            and_(
                OfferProduct.offer_id == offer_id,
                OfferProduct.product_id == product_id
            )
        ).first()
        
        if not offer_product:
            raise HTTPException(status_code=404, detail="Product not found in this offer")
        
        db.delete(offer_product)
        db.commit()
        
        logger.info(f"Removed product {product_id} from offer {offer_id}")
        
        return {"message": "Product removed from offer successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error removing product from offer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# OFFER ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/api/offers/{offer_id}/analytics")
async def get_offer_analytics(
    offer_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics for an offer"""
    try:
        query = db.query(OfferAnalytics).filter(OfferAnalytics.offer_id == offer_id)
        
        if start_date:
            query = query.filter(OfferAnalytics.date >= start_date)
        if end_date:
            query = query.filter(OfferAnalytics.date <= end_date)
        
        analytics = query.order_by(OfferAnalytics.date).all()
        
        # Calculate totals
        total_views = sum(a.views_count for a in analytics)
        total_clicks = sum(a.clicks_count for a in analytics)
        total_usage = sum(a.usage_count for a in analytics)
        total_revenue = sum(float(a.revenue_generated) for a in analytics)
        total_discount = sum(float(a.discount_given) for a in analytics)
        total_orders = sum(a.orders_count for a in analytics)
        
        return {
            "offer_id": offer_id,
            "analytics": [a.to_dict() for a in analytics],
            "summary": {
                "total_views": total_views,
                "total_clicks": total_clicks,
                "total_usage": total_usage,
                "total_revenue": total_revenue,
                "total_discount": total_discount,
                "total_orders": total_orders,
                "average_conversion_rate": (total_usage / total_views * 100) if total_views > 0 else 0,
                "average_order_value": total_revenue / total_orders if total_orders > 0 else 0
            }
        }
    except Exception as e:
        logger.error(f"Error getting offer analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8040))
    uvicorn.run(app, host="0.0.0.0", port=port)
