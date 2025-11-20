"""
Advertising Campaign Management Models
SQLAlchemy models for advertising campaigns, ad groups, creatives, and analytics
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Numeric, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any
from shared.db_models import Base


class AdvertisingCampaign(Base):
    """Advertising campaigns across platforms"""
    __tablename__ = "advertising_campaigns"
    
    id = Column(Integer, primary_key=True)
    
    # Basic Information
    name = Column(String(255), nullable=False)
    description = Column(Text)
    campaign_type = Column(String(50), nullable=False)
    status = Column(String(50), default='draft', index=True)
    
    # Platform & Targeting
    platform = Column(String(50), index=True)
    platform_campaign_id = Column(String(255))
    target_audience = Column(JSON)
    target_locations = Column(JSON)
    target_devices = Column(JSON)
    
    # Budget & Bidding
    budget_type = Column(String(50))
    daily_budget = Column(Numeric(15, 2))
    total_budget = Column(Numeric(15, 2))
    bid_strategy = Column(String(50))
    max_bid = Column(Numeric(10, 2))
    
    # Schedule
    start_date = Column(DateTime, index=True)
    end_date = Column(DateTime, index=True)
    schedule_config = Column(JSON)
    
    # Performance Targets
    target_impressions = Column(Integer)
    target_clicks = Column(Integer)
    target_conversions = Column(Integer)
    target_roas = Column(Numeric(5, 2))
    
    # Current Performance
    total_impressions = Column(Integer, default=0)
    total_clicks = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)
    total_spend = Column(Numeric(15, 2), default=0.00)
    total_revenue = Column(Numeric(15, 2), default=0.00)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    extra_data = Column(JSON)
    
    # Relationships
    ad_groups = relationship("AdGroup", back_populates="campaign", cascade="all, delete-orphan")
    ad_creatives = relationship("AdCreative", back_populates="campaign")
    products = relationship("CampaignProduct", back_populates="campaign")
    analytics = relationship("CampaignAnalytics", back_populates="campaign")
    events = relationship("CampaignEvent", back_populates="campaign")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "campaign_type": self.campaign_type,
            "status": self.status,
            "platform": self.platform,
            "platform_campaign_id": self.platform_campaign_id,
            "target_audience": self.target_audience or {},
            "target_locations": self.target_locations or [],
            "target_devices": self.target_devices or [],
            "budget_type": self.budget_type,
            "daily_budget": float(self.daily_budget) if self.daily_budget else None,
            "total_budget": float(self.total_budget) if self.total_budget else None,
            "bid_strategy": self.bid_strategy,
            "max_bid": float(self.max_bid) if self.max_bid else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "schedule_config": self.schedule_config or {},
            "target_impressions": self.target_impressions,
            "target_clicks": self.target_clicks,
            "target_conversions": self.target_conversions,
            "target_roas": float(self.target_roas) if self.target_roas else None,
            "total_impressions": self.total_impressions,
            "total_clicks": self.total_clicks,
            "total_conversions": self.total_conversions,
            "total_spend": float(self.total_spend) if self.total_spend else 0.0,
            "total_revenue": float(self.total_revenue) if self.total_revenue else 0.0,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "extra_data": self.extra_data or {}
        }


class AdGroup(Base):
    """Ad groups within campaigns"""
    __tablename__ = "ad_groups"
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("advertising_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic Information
    name = Column(String(255), nullable=False)
    status = Column(String(50), default='active')
    
    # Bidding
    bid_amount = Column(Numeric(10, 2))
    
    # Targeting
    keywords = Column(JSON)
    negative_keywords = Column(JSON)
    placements = Column(JSON)
    
    # Performance
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    spend = Column(Numeric(15, 2), default=0.00)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    campaign = relationship("AdvertisingCampaign", back_populates="ad_groups")
    ad_creatives = relationship("AdCreative", back_populates="ad_group")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "name": self.name,
            "status": self.status,
            "bid_amount": float(self.bid_amount) if self.bid_amount else None,
            "keywords": self.keywords or [],
            "negative_keywords": self.negative_keywords or [],
            "placements": self.placements or [],
            "impressions": self.impressions,
            "clicks": self.clicks,
            "conversions": self.conversions,
            "spend": float(self.spend) if self.spend else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class AdCreative(Base):
    """Individual ad creatives"""
    __tablename__ = "ad_creatives"
    
    id = Column(Integer, primary_key=True)
    ad_group_id = Column(Integer, ForeignKey("ad_groups.id", ondelete="CASCADE"), index=True)
    campaign_id = Column(Integer, ForeignKey("advertising_campaigns.id"), index=True)
    
    # Basic Information
    name = Column(String(255), nullable=False)
    ad_type = Column(String(50), nullable=False)
    status = Column(String(50), default='active')
    
    # Creative Content
    headline = Column(String(255))
    description = Column(Text)
    call_to_action = Column(String(100))
    
    # Media Assets
    image_url = Column(Text)
    video_url = Column(Text)
    thumbnail_url = Column(Text)
    media_assets = Column(JSON)
    
    # Destination
    landing_page_url = Column(Text)
    tracking_template = Column(Text)
    utm_parameters = Column(JSON)
    
    # Performance
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    ctr = Column(Numeric(5, 2))
    conversion_rate = Column(Numeric(5, 2))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ad_group = relationship("AdGroup", back_populates="ad_creatives")
    campaign = relationship("AdvertisingCampaign", back_populates="ad_creatives")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "ad_group_id": self.ad_group_id,
            "campaign_id": self.campaign_id,
            "name": self.name,
            "ad_type": self.ad_type,
            "status": self.status,
            "headline": self.headline,
            "description": self.description,
            "call_to_action": self.call_to_action,
            "image_url": self.image_url,
            "video_url": self.video_url,
            "thumbnail_url": self.thumbnail_url,
            "media_assets": self.media_assets or [],
            "landing_page_url": self.landing_page_url,
            "tracking_template": self.tracking_template,
            "utm_parameters": self.utm_parameters or {},
            "impressions": self.impressions,
            "clicks": self.clicks,
            "conversions": self.conversions,
            "ctr": float(self.ctr) if self.ctr else None,
            "conversion_rate": float(self.conversion_rate) if self.conversion_rate else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class CampaignProduct(Base):
    """Products being advertised in campaigns"""
    __tablename__ = "campaign_products"
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("advertising_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Product-specific settings
    custom_bid = Column(Numeric(10, 2))
    priority = Column(Integer, default=0)
    
    # Performance
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Numeric(15, 2), default=0.00)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    campaign = relationship("AdvertisingCampaign", back_populates="products")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "product_id": self.product_id,
            "custom_bid": float(self.custom_bid) if self.custom_bid else None,
            "priority": self.priority,
            "impressions": self.impressions,
            "clicks": self.clicks,
            "conversions": self.conversions,
            "revenue": float(self.revenue) if self.revenue else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class CampaignAnalytics(Base):
    """Daily performance analytics for campaigns"""
    __tablename__ = "campaign_analytics"
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("advertising_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # Traffic Metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    ctr = Column(Numeric(5, 2))
    
    # Cost Metrics
    spend = Column(Numeric(15, 2), default=0.00)
    cpc = Column(Numeric(10, 2))
    cpm = Column(Numeric(10, 2))
    
    # Conversion Metrics
    conversions = Column(Integer, default=0)
    conversion_rate = Column(Numeric(5, 2))
    cpa = Column(Numeric(10, 2))
    
    # Revenue Metrics
    revenue = Column(Numeric(15, 2), default=0.00)
    roas = Column(Numeric(5, 2))
    profit = Column(Numeric(15, 2))
    
    # Engagement Metrics
    video_views = Column(Integer, default=0)
    video_completion_rate = Column(Numeric(5, 2))
    engagement_rate = Column(Numeric(5, 2))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    campaign = relationship("AdvertisingCampaign", back_populates="analytics")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "date": self.date.isoformat() if self.date else None,
            "impressions": self.impressions,
            "clicks": self.clicks,
            "ctr": float(self.ctr) if self.ctr else None,
            "spend": float(self.spend) if self.spend else 0.0,
            "cpc": float(self.cpc) if self.cpc else None,
            "cpm": float(self.cpm) if self.cpm else None,
            "conversions": self.conversions,
            "conversion_rate": float(self.conversion_rate) if self.conversion_rate else None,
            "cpa": float(self.cpa) if self.cpa else None,
            "revenue": float(self.revenue) if self.revenue else 0.0,
            "roas": float(self.roas) if self.roas else None,
            "profit": float(self.profit) if self.profit else None,
            "video_views": self.video_views,
            "video_completion_rate": float(self.video_completion_rate) if self.video_completion_rate else None,
            "engagement_rate": float(self.engagement_rate) if self.engagement_rate else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class CampaignEvent(Base):
    """Event log for campaign activities"""
    __tablename__ = "campaign_events"
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("advertising_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Event Details
    event_type = Column(String(50), nullable=False)
    event_data = Column(JSON)
    event_message = Column(Text)
    
    # User
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    campaign = relationship("AdvertisingCampaign", back_populates="events")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "event_type": self.event_type,
            "event_data": self.event_data or {},
            "event_message": self.event_message,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
