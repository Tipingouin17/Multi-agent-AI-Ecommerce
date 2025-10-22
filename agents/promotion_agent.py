"""
Promotion Agent - Multi-Agent E-Commerce System

This agent manages promotions, discounts, coupons, and marketing campaigns
with dynamic pricing and eligibility rules.

DATABASE SCHEMA (migration 013_promotion_agent.sql):

CREATE TABLE promotions (
    promotion_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    promotion_code VARCHAR(50) UNIQUE NOT NULL,
    promotion_name VARCHAR(200) NOT NULL,
    promotion_type VARCHAR(50) NOT NULL, -- 'percentage', 'fixed_amount', 'bogo', 'free_shipping', 'bundle'
    discount_value DECIMAL(10, 2),
    discount_percentage DECIMAL(5, 2),
    min_purchase_amount DECIMAL(10, 2),
    max_discount_amount DECIMAL(10, 2),
    applicable_products JSONB DEFAULT '[]',
    applicable_categories JSONB DEFAULT '[]',
    excluded_products JSONB DEFAULT '[]',
    customer_eligibility JSONB DEFAULT '{}', -- {min_orders, loyalty_tier, etc}
    usage_limit INTEGER,
    usage_per_customer INTEGER DEFAULT 1,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE promotion_usage (
    usage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    promotion_id UUID REFERENCES promotions(promotion_id),
    customer_id VARCHAR(100) NOT NULL,
    order_id VARCHAR(100) NOT NULL,
    discount_amount DECIMAL(10, 2) NOT NULL,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE campaigns (
    campaign_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_name VARCHAR(200) NOT NULL,
    campaign_type VARCHAR(50) NOT NULL, -- 'email', 'sms', 'push', 'banner'
    target_audience JSONB NOT NULL, -- Segmentation criteria
    promotion_id UUID REFERENCES promotions(promotion_id),
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    budget DECIMAL(10, 2),
    spent DECIMAL(10, 2) DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true
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

from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.database import DatabaseManager, get_database_manager

logger = structlog.get_logger(__name__)

# ENUMS
class PromotionType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    BOGO = "bogo"  # Buy One Get One
    FREE_SHIPPING = "free_shipping"
    BUNDLE = "bundle"

# MODELS
class PromotionCreate(BaseModel):
    promotion_code: str
    promotion_name: str
    promotion_type: PromotionType
    discount_value: Optional[Decimal] = None
    discount_percentage: Optional[Decimal] = None
    min_purchase_amount: Optional[Decimal] = None
    max_discount_amount: Optional[Decimal] = None
    applicable_products: List[str] = []
    applicable_categories: List[str] = []
    excluded_products: List[str] = []
    customer_eligibility: Dict[str, Any] = {}
    usage_limit: Optional[int] = None
    usage_per_customer: int = 1
    start_date: datetime
    end_date: datetime
    async def initialize(self):
        """Initialize agent."""
        await super().initialize()
        
    async def cleanup(self):
        """Cleanup agent."""
        await super().cleanup()
        
    async def process_business_logic(self, data):
        """Process business logic."""
        return {"status": "success"}


class Promotion(BaseModel):
    promotion_id: UUID
    promotion_code: str
    promotion_name: str
    promotion_type: PromotionType
    discount_value: Optional[Decimal]
    discount_percentage: Optional[Decimal]
    start_date: datetime
    end_date: datetime
    is_active: bool

    class Config:
        from_attributes = True

class PromotionValidationRequest(BaseModel):
    promotion_code: str
    customer_id: str
    order_amount: Decimal
    products: List[str] = []
    categories: List[str] = []

class PromotionValidationResponse(BaseModel):
    is_valid: bool
    promotion: Optional[Promotion]
    discount_amount: Decimal = Decimal("0.00")
    final_amount: Decimal
    reason: Optional[str] = None

# REPOSITORY
class PromotionRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_promotion(self, promo_data: PromotionCreate) -> Promotion:
        query = """
            INSERT INTO promotions (promotion_code, promotion_name, promotion_type,
                                   discount_value, discount_percentage, min_purchase_amount,
                                   max_discount_amount, applicable_products, applicable_categories,
                                   excluded_products, customer_eligibility, usage_limit,
                                   usage_per_customer, start_date, end_date)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            RETURNING *
        """
        result = await self.db.fetch_one(
            query, promo_data.promotion_code, promo_data.promotion_name,
            promo_data.promotion_type.value, promo_data.discount_value,
            promo_data.discount_percentage, promo_data.min_purchase_amount,
            promo_data.max_discount_amount, str(promo_data.applicable_products),
            str(promo_data.applicable_categories), str(promo_data.excluded_products),
            str(promo_data.customer_eligibility), promo_data.usage_limit,
            promo_data.usage_per_customer, promo_data.start_date, promo_data.end_date
        )
        return Promotion(**result)
    
    async def get_promotion_by_code(self, promotion_code: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM promotions WHERE promotion_code = $1 AND is_active = true"
        result = await self.db.fetch_one(query, promotion_code)
        return dict(result) if result else None
    
    async def get_active_promotions(self) -> List[Dict[str, Any]]:
        query = """
            SELECT * FROM promotions
            WHERE is_active = true
            AND start_date <= CURRENT_TIMESTAMP
            AND end_date >= CURRENT_TIMESTAMP
            ORDER BY created_at DESC
        """
        results = await self.db.fetch_all(query)
        return [dict(r) for r in results]
    
    async def get_promotion_usage_count(self, promotion_id: UUID) -> int:
        query = "SELECT COUNT(*) as count FROM promotion_usage WHERE promotion_id = $1"
        result = await self.db.fetch_one(query, promotion_id)
        return result['count']
    
    async def get_customer_usage_count(self, promotion_id: UUID, customer_id: str) -> int:
        query = """
            SELECT COUNT(*) as count FROM promotion_usage
            WHERE promotion_id = $1 AND customer_id = $2
        """
        result = await self.db.fetch_one(query, promotion_id, customer_id)
        return result['count']
    
    async def record_promotion_usage(
        self, promotion_id: UUID, customer_id: str, order_id: str, discount_amount: Decimal
    ) -> UUID:
        query = """
            INSERT INTO promotion_usage (promotion_id, customer_id, order_id, discount_amount)
            VALUES ($1, $2, $3, $4)
            RETURNING usage_id
        """
        result = await self.db.fetch_one(query, promotion_id, customer_id, order_id, discount_amount)
        return result['usage_id']

# SERVICE
class PromotionService:
    def __init__(self, repo: PromotionRepository):
        self.repo = repo
    
    def calculate_discount(
        self, promotion: Dict[str, Any], order_amount: Decimal
    ) -> Decimal:
        """Calculate discount amount based on promotion type."""
        promo_type = promotion['promotion_type']
        
        if promo_type == PromotionType.PERCENTAGE.value:
            discount = order_amount * (Decimal(str(promotion['discount_percentage'])) / 100)
            if promotion['max_discount_amount']:
                discount = min(discount, Decimal(str(promotion['max_discount_amount'])))
            return discount
        
        elif promo_type == PromotionType.FIXED_AMOUNT.value:
            return Decimal(str(promotion['discount_value']))
        
        elif promo_type == PromotionType.FREE_SHIPPING.value:
            # In production, get shipping cost from order
            return Decimal("10.00")  # Simulated shipping cost
        
        return Decimal("0.00")
    
    async def validate_promotion(
        self, request: PromotionValidationRequest
    ) -> PromotionValidationResponse:
        """Validate promotion code and calculate discount."""
        # Get promotion
        promotion = await self.repo.get_promotion_by_code(request.promotion_code)
        
        if not promotion:
            return PromotionValidationResponse(
                is_valid=False,
                promotion=None,
                final_amount=request.order_amount,
                reason="Promotion code not found"
            )
        
        # Check if active and within date range
        now = datetime.utcnow()
        if not promotion['is_active']:
            return PromotionValidationResponse(
                is_valid=False,
                promotion=None,
                final_amount=request.order_amount,
                reason="Promotion is not active"
            )
        
        if now < promotion['start_date'] or now > promotion['end_date']:
            return PromotionValidationResponse(
                is_valid=False,
                promotion=None,
                final_amount=request.order_amount,
                reason="Promotion is not valid at this time"
            )
        
        # Check minimum purchase amount
        if promotion['min_purchase_amount']:
            if request.order_amount < Decimal(str(promotion['min_purchase_amount'])):
                return PromotionValidationResponse(
                    is_valid=False,
                    promotion=None,
                    final_amount=request.order_amount,
                    reason=f"Minimum purchase amount of ${promotion['min_purchase_amount']} required"
                )
        
        # Check usage limits
        if promotion['usage_limit']:
            total_usage = await self.repo.get_promotion_usage_count(promotion['promotion_id'])
            if total_usage >= promotion['usage_limit']:
                return PromotionValidationResponse(
                    is_valid=False,
                    promotion=None,
                    final_amount=request.order_amount,
                    reason="Promotion usage limit reached"
                )
        
        # Check per-customer usage
        customer_usage = await self.repo.get_customer_usage_count(
            promotion['promotion_id'], request.customer_id
        )
        if customer_usage >= promotion['usage_per_customer']:
            return PromotionValidationResponse(
                is_valid=False,
                promotion=None,
                final_amount=request.order_amount,
                reason="You have already used this promotion"
            )
        
        # Calculate discount
        discount_amount = self.calculate_discount(promotion, request.order_amount)
        final_amount = max(Decimal("0.00"), request.order_amount - discount_amount)
        
        logger.info("promotion_validated", promotion_code=request.promotion_code,
                   discount_amount=float(discount_amount))
        
        return PromotionValidationResponse(
            is_valid=True,
            promotion=Promotion(**promotion),
            discount_amount=discount_amount,
            final_amount=final_amount,
            reason=None
        )

# FASTAPI APP
app = FastAPI(title="Promotion Agent API", version="1.0.0")

async def get_promotion_service() -> PromotionService:
    db_manager = await get_database_manager()
    repo = PromotionRepository(db_manager)
    return PromotionService(repo)

# ENDPOINTS
@app.post("/api/v1/promotions", response_model=Promotion)
async def create_promotion(
    promo_data: PromotionCreate = Body(...),
    service: PromotionService = Depends(get_promotion_service)
):
    try:
        promotion = await service.repo.create_promotion(promo_data)
        logger.info("promotion_created", promotion_id=str(promotion.promotion_id))
        return promotion
    except Exception as e:
        logger.error("create_promotion_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/promotions/active")
async def get_active_promotions(
    service: PromotionService = Depends(get_promotion_service)
):
    try:
        promotions = await service.repo.get_active_promotions()
        return {"promotions": promotions}
    except Exception as e:
        logger.error("get_active_promotions_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/promotions/validate", response_model=PromotionValidationResponse)
async def validate_promotion(
    request: PromotionValidationRequest = Body(...),
    service: PromotionService = Depends(get_promotion_service)
):
    try:
        response = await service.validate_promotion(request)
        return response
    except Exception as e:
        logger.error("validate_promotion_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/promotions/{promotion_id}/use")
async def record_usage(
    promotion_id: UUID = Path(...),
    customer_id: str = Body(..., embed=True),
    order_id: str = Body(..., embed=True),
    discount_amount: Decimal = Body(..., embed=True),
    service: PromotionService = Depends(get_promotion_service)
):
    try:
        usage_id = await service.repo.record_promotion_usage(
            promotion_id, customer_id, order_id, discount_amount
        )
        return {"usage_id": usage_id, "message": "Promotion usage recorded"}
    except Exception as e:
        logger.error("record_usage_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "promotion_agent", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8012)

