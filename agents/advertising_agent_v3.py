"""
Advertising Campaign Management Agent v3
Manages advertising campaigns, ad groups, creatives, and analytics
Port: 8041
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import uvicorn
from dotenv import load_dotenv

from shared.db_connection import get_db_session
from shared.auth import get_current_user, require_merchant, User
from shared.advertising_models import (
    AdvertisingCampaign, AdGroup, AdCreative, 
    CampaignProduct, CampaignAnalytics, CampaignEvent
)
from sqlalchemy.orm import Session, joinedload

# Load environment variables
load_dotenv()

app = FastAPI(title="Advertising Agent", version="3.0.0")

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
    return {"status": "healthy", "agent": "advertising_agent_v3", "version": "3.0.0"}

# ==================== PYDANTIC MODELS ====================

class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    campaign_type: str
    platform: Optional[str] = None
    budget_type: Optional[str] = None
    daily_budget: Optional[float] = None
    total_budget: Optional[float] = None
    bid_strategy: Optional[str] = None
    max_bid: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    target_audience: Optional[Dict] = None
    target_locations: Optional[List] = None
    target_devices: Optional[List] = None
    target_impressions: Optional[int] = None
    target_clicks: Optional[int] = None
    target_conversions: Optional[int] = None
    target_roas: Optional[float] = None

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    daily_budget: Optional[float] = None
    total_budget: Optional[float] = None
    bid_strategy: Optional[str] = None
    max_bid: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class AdGroupCreate(BaseModel):
    campaign_id: int
    name: str
    bid_amount: Optional[float] = None
    keywords: Optional[List] = None
    negative_keywords: Optional[List] = None
    placements: Optional[List] = None

class AdCreativeCreate(BaseModel):
    ad_group_id: int
    campaign_id: int
    name: str
    ad_type: str
    headline: Optional[str] = None
    description: Optional[str] = None
    call_to_action: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    landing_page_url: Optional[str] = None
    utm_parameters: Optional[Dict] = None

# ==================== CAMPAIGN ENDPOINTS ====================

@app.get("/api/campaigns")
async def get_campaigns(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    campaign_type: Optional[str] = None,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_merchant)
):
    """Get all campaigns with optional filters"""
    query = db.query(AdvertisingCampaign)
    
    if status:
        query = query.filter(AdvertisingCampaign.status == status)
    if platform:
        query = query.filter(AdvertisingCampaign.platform == platform)
    if campaign_type:
        query = query.filter(AdvertisingCampaign.campaign_type == campaign_type)
    
    campaigns = query.order_by(AdvertisingCampaign.created_at.desc()).all()
    
    return {
        "campaigns": [c.to_dict() for c in campaigns],
        "total": len(campaigns)
    }

@app.get("/api/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_merchant)
):
    """Get campaign by ID"""
    campaign = db.query(AdvertisingCampaign).filter(
        AdvertisingCampaign.id == campaign_id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return campaign.to_dict()

@app.post("/api/campaigns")
async def create_campaign(
    campaign_data: CampaignCreate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_merchant)
):
    """Create new campaign"""
    campaign = AdvertisingCampaign(
        **campaign_data.dict(),
        status='draft',
        created_by=int(current_user.user_id)
    )
    
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    # Log event
    event = CampaignEvent(
        campaign_id=campaign.id,
        event_type='created',
        event_message=f'Campaign "{campaign.name}" created',
        user_id=int(current_user.user_id)
    )
    db.add(event)
    db.commit()
    
    return campaign.to_dict()

@app.patch("/api/campaigns/{campaign_id}")
async def update_campaign(
    campaign_id: int,
    campaign_data: CampaignUpdate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_merchant)
):
    """Update campaign"""
    campaign = db.query(AdvertisingCampaign).filter(
        AdvertisingCampaign.id == campaign_id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Update fields
    for field, value in campaign_data.dict(exclude_unset=True).items():
        setattr(campaign, field, value)
    
    db.commit()
    db.refresh(campaign)
    
    # Log event
    event = CampaignEvent(
        campaign_id=campaign.id,
        event_type='updated',
        event_message=f'Campaign "{campaign.name}" updated',
        user_id=int(current_user.user_id)
    )
    db.add(event)
    db.commit()
    
    return campaign.to_dict()

@app.delete("/api/campaigns/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_merchant)
):
    """Delete campaign"""
    campaign = db.query(AdvertisingCampaign).filter(
        AdvertisingCampaign.id == campaign_id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    db.delete(campaign)
    db.commit()
    
    return {"message": "Campaign deleted successfully"}

# ==================== ANALYTICS ENDPOINTS ====================

@app.get("/api/campaigns/{campaign_id}/analytics")
async def get_campaign_analytics(
    campaign_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_merchant)
):
    """Get campaign analytics"""
    query = db.query(CampaignAnalytics).filter(
        CampaignAnalytics.campaign_id == campaign_id
    )
    
    if start_date:
        query = query.filter(CampaignAnalytics.date >= start_date)
    if end_date:
        query = query.filter(CampaignAnalytics.date <= end_date)
    
    analytics = query.order_by(CampaignAnalytics.date.desc()).all()
    
    return {
        "analytics": [a.to_dict() for a in analytics],
        "total_records": len(analytics)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8041)
