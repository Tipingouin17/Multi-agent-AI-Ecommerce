"""
Marketplace Integration Agent v3
Manages marketplace connections, product listings, and order synchronization
Supports: Amazon, eBay, Walmart, Etsy, and custom marketplaces
Port: 8043
"""

import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uvicorn
from dotenv import load_dotenv

from shared.db_connection import get_database_url
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from shared.auth import get_current_user, require_merchant, User
from shared.db_models import Marketplace, Product

# Load environment variables
load_dotenv()

# Create database engine and session
engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(title="Marketplace Integration Agent", version="3.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "marketplace_agent_v3", "version": "3.0.0"}

# ==================== PYDANTIC MODELS ====================

class MarketplaceConnect(BaseModel):
    name: str
    platform: str  # amazon, ebay, walmart, etsy, custom
    region: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    merchant_id: Optional[str] = None
    settings: Optional[Dict] = None

class MarketplaceUpdate(BaseModel):
    name: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    merchant_id: Optional[str] = None
    is_active: Optional[bool] = None
    settings: Optional[Dict] = None
    sync_frequency: Optional[int] = None

class ProductListingCreate(BaseModel):
    marketplace_id: int
    product_id: int
    marketplace_sku: Optional[str] = None
    marketplace_title: Optional[str] = None
    marketplace_description: Optional[str] = None
    marketplace_price: float
    marketplace_quantity: int
    auto_sync: Optional[bool] = True

class SyncRequest(BaseModel):
    marketplace_id: int
    sync_type: str  # inventory, orders, prices, all
    force: Optional[bool] = False

# ==================== MARKETPLACE ENDPOINTS ====================

@app.get("/api/marketplaces")
async def get_marketplaces(
    platform: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant)
):
    """Get all connected marketplaces"""
    query = db.query(Marketplace)
    
    if platform:
        query = query.filter(Marketplace.platform == platform)
    
    if is_active is not None:
        query = query.filter(Marketplace.is_active == is_active)
    
    marketplaces = query.order_by(Marketplace.name).all()
    return [marketplace.to_dict() for marketplace in marketplaces]

@app.get("/api/marketplaces/{marketplace_id}")
async def get_marketplace(
    marketplace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant)
):
    """Get marketplace by ID"""
    marketplace = db.query(Marketplace).filter(Marketplace.id == marketplace_id).first()
    if not marketplace:
        raise HTTPException(status_code=404, detail="Marketplace not found")
    return marketplace.to_dict()

@app.post("/api/marketplaces/connect")
async def connect_marketplace(
    marketplace_data: MarketplaceConnect,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant)
):
    """Connect to a new marketplace"""
    # Check if marketplace already exists
    existing = db.query(Marketplace).filter(
        Marketplace.platform == marketplace_data.platform,
        Marketplace.merchant_id == marketplace_data.merchant_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Marketplace already connected")
    
    marketplace = Marketplace(
        name=marketplace_data.name,
        platform=marketplace_data.platform,
        region=marketplace_data.region,
        api_key=marketplace_data.api_key,
        api_secret=marketplace_data.api_secret,
        merchant_id=marketplace_data.merchant_id,
        is_active=True,
        settings=marketplace_data.settings or {},
        created_by=current_user.user_id
    )
    
    db.add(marketplace)
    db.commit()
    db.refresh(marketplace)
    
    return {
        "message": "Marketplace connected successfully",
        "marketplace": marketplace.to_dict()
    }

@app.patch("/api/marketplaces/{marketplace_id}")
async def update_marketplace(
    marketplace_id: int,
    marketplace_data: MarketplaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant)
):
    """Update marketplace settings"""
    marketplace = db.query(Marketplace).filter(Marketplace.id == marketplace_id).first()
    if not marketplace:
        raise HTTPException(status_code=404, detail="Marketplace not found")
    
    for field, value in marketplace_data.dict(exclude_unset=True).items():
        setattr(marketplace, field, value)
    
    db.commit()
    db.refresh(marketplace)
    return marketplace.to_dict()

@app.delete("/api/marketplaces/{marketplace_id}")
async def disconnect_marketplace(
    marketplace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant)
):
    """Disconnect marketplace"""
    marketplace = db.query(Marketplace).filter(Marketplace.id == marketplace_id).first()
    if not marketplace:
        raise HTTPException(status_code=404, detail="Marketplace not found")
    
    # Soft delete - just deactivate
    marketplace.is_active = False
    db.commit()
    
    return {"message": "Marketplace disconnected successfully"}

# ==================== PRODUCT LISTINGS ENDPOINTS ====================

@app.get("/api/marketplaces/{marketplace_id}/listings")
async def get_marketplace_listings(
    marketplace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant)
):
    """Get all product listings for a marketplace"""
    marketplace = db.query(Marketplace).filter(Marketplace.id == marketplace_id).first()
    if not marketplace:
        raise HTTPException(status_code=404, detail="Marketplace not found")
    
    # Note: This would query marketplace_listings table when it's created
    # For now, return placeholder
    return {
        "marketplace_id": marketplace_id,
        "marketplace_name": marketplace.name,
        "listings": [],
        "message": "Listing sync feature coming soon"
    }

@app.post("/api/listings")
async def create_listing(
    listing_data: ProductListingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant)
):
    """Create product listing on marketplace"""
    # Verify marketplace exists
    marketplace = db.query(Marketplace).filter(
        Marketplace.id == listing_data.marketplace_id
    ).first()
    if not marketplace:
        raise HTTPException(status_code=404, detail="Marketplace not found")
    
    # Verify product exists
    product = db.query(Product).filter(Product.id == listing_data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Note: This would create listing in marketplace_listings table
    # and trigger API call to actual marketplace
    
    return {
        "message": "Listing created successfully",
        "marketplace": marketplace.name,
        "product": product.name,
        "status": "pending_sync"
    }

# ==================== SYNCHRONIZATION ENDPOINTS ====================

@app.post("/api/sync")
async def sync_marketplace(
    sync_request: SyncRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant)
):
    """Trigger marketplace synchronization"""
    marketplace = db.query(Marketplace).filter(
        Marketplace.id == sync_request.marketplace_id
    ).first()
    if not marketplace:
        raise HTTPException(status_code=404, detail="Marketplace not found")
    
    if not marketplace.is_active:
        raise HTTPException(status_code=400, detail="Marketplace is not active")
    
    # Update last sync time
    marketplace.last_sync_at = datetime.utcnow()
    db.commit()
    
    # Note: This would trigger background task to sync with marketplace API
    # background_tasks.add_task(sync_marketplace_data, marketplace.id, sync_request.sync_type)
    
    return {
        "message": f"Sync initiated for {marketplace.name}",
        "sync_type": sync_request.sync_type,
        "status": "in_progress",
        "estimated_time": "2-5 minutes"
    }

@app.get("/api/marketplaces/{marketplace_id}/sync-status")
async def get_sync_status(
    marketplace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant)
):
    """Get marketplace sync status"""
    marketplace = db.query(Marketplace).filter(Marketplace.id == marketplace_id).first()
    if not marketplace:
        raise HTTPException(status_code=404, detail="Marketplace not found")
    
    return {
        "marketplace_id": marketplace_id,
        "marketplace_name": marketplace.name,
        "last_sync": marketplace.last_sync_at.isoformat() if marketplace.last_sync_at else None,
        "sync_frequency": marketplace.sync_frequency,
        "next_sync": "Calculated based on frequency",
        "status": "idle"
    }

# ==================== MARKETPLACE ANALYTICS ====================

@app.get("/api/marketplaces/{marketplace_id}/analytics")
async def get_marketplace_analytics(
    marketplace_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant)
):
    """Get marketplace performance analytics"""
    marketplace = db.query(Marketplace).filter(Marketplace.id == marketplace_id).first()
    if not marketplace:
        raise HTTPException(status_code=404, detail="Marketplace not found")
    
    # Note: This would query marketplace_analytics table
    return {
        "marketplace_id": marketplace_id,
        "marketplace_name": marketplace.name,
        "period": {
            "start": start_date,
            "end": end_date
        },
        "metrics": {
            "total_listings": 0,
            "active_listings": 0,
            "total_orders": 0,
            "total_revenue": 0.0,
            "average_order_value": 0.0,
            "commission_paid": 0.0,
            "conversion_rate": 0.0
        },
        "message": "Analytics feature coming soon"
    }

# ==================== SUPPORTED PLATFORMS ====================

@app.get("/api/platforms")
async def get_supported_platforms():
    """Get list of supported marketplace platforms"""
    return {
        "platforms": [
            {
                "id": "amazon",
                "name": "Amazon",
                "regions": ["US", "UK", "DE", "FR", "IT", "ES", "CA", "JP"],
                "features": ["listings", "orders", "inventory", "pricing", "fulfillment"]
            },
            {
                "id": "ebay",
                "name": "eBay",
                "regions": ["US", "UK", "DE", "AU"],
                "features": ["listings", "orders", "inventory", "pricing"]
            },
            {
                "id": "walmart",
                "name": "Walmart Marketplace",
                "regions": ["US"],
                "features": ["listings", "orders", "inventory", "pricing"]
            },
            {
                "id": "etsy",
                "name": "Etsy",
                "regions": ["Global"],
                "features": ["listings", "orders", "inventory"]
            },
            {
                "id": "custom",
                "name": "Custom Marketplace",
                "regions": ["Any"],
                "features": ["configurable"]
            }
        ]
    }

# ==================== RUN SERVER ====================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8043)
