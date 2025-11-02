from fastapi.middleware.cors import CORSMiddleware
"""
Promotion Agent - Multi-Agent E-Commerce System

This agent manages promotions, discounts, coupons, and marketing campaigns
with dynamic pricing and eligibility rules.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any, AsyncGenerator
from uuid import uuid4, UUID
from enum import Enum
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field
import structlog
import sys
import os
import uvicorn

# Add project root to path
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.base_agent_v2 import BaseAgentV2, MessageType, AgentMessage
from shared.database import DatabaseManager, get_database_manager
from shared.db_helpers import DatabaseHelper

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
        # Note: The original code used raw string conversions for JSONB fields. 
        # This is preserved but should ideally be handled by a proper ORM or driver.
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

# AGENT CLASS
app = FastAPI()


    """
    Promotion Agent with FastAPI for API exposure and database management via lifespan.
    """
    def __init__(self, agent_id: str = "promotion_agent"):
        super().__init__(agent_id=agent_id)
        self.agent_name = "Promotion Agent"
        self.db_manager: Optional[DatabaseManager] = None
        self.repo: Optional[PromotionRepository] = None
        self.service: Optional[PromotionService] = None
        
        # Initialize FastAPI app with lifespan
        
        self._setup_routes()

    @asynccontextmanager
    async def lifespan_context(self, app: FastAPI) -> AsyncGenerator[None, None]:
        """
        FastAPI Lifespan Context Manager for agent startup and shutdown.
        Initializes the database connection and the agent's services.
        """
        # Startup
        logger.info("FastAPI Lifespan Startup: Promotion Agent")
        
        # 1. Initialize Database Manager
        try:
            self.db_manager = get_database_manager()
        except RuntimeError:
            # Fallback to creating a new manager if global one is not set
            from shared.models import DatabaseConfig
            self.db_manager = DatabaseManager(DatabaseConfig().url)
        
        await self.db_manager.initialize_async()
        
        # 2. Initialize Repository and Service
        self.repo = PromotionRepository(self.db_manager)
        self.service = PromotionService(self.repo)
        
        # 3. Call BaseAgentV2 initialize (for Kafka, etc.)
        await self.initialize()
        
        yield
        
        # Shutdown
        logger.info("FastAPI Lifespan Shutdown: Promotion Agent")
        await self.cleanup()

    async def initialize(self):
        """Initialize agent-specific components"""
        await super().initialize()
        logger.info(f"{self.agent_name} initialized successfully")

    async def cleanup(self):
        """Cleanup agent resources"""
        if self.db_manager:
            await self.db_manager.close()
        await super().cleanup()
        logger.info(f"{self.agent_name} cleaned up successfully")

    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process promotion-specific business logic"""
        # This can be used for internal agent-to-agent communication
        logger.info("Processing promotion business logic", data=data)
        return {"status": "processed", "data": data}

    def _setup_routes(self):
        """Setup FastAPI routes for the Promotion Agent API."""
        
        # Dependency to get the initialized service
        def get_promotion_service_dependency() -> PromotionService:
            if not self.service:
                raise HTTPException(status_code=503, detail="Service not initialized")
            return self.service

        @app.post("/api/v1/promotions", response_model=Promotion)
        async def create_promotion(
            promo_data: PromotionCreate = Body(...),
            service: PromotionService = Depends(get_promotion_service_dependency)
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
            service: PromotionService = Depends(get_promotion_service_dependency)
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
            service: PromotionService = Depends(get_promotion_service_dependency)
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
            service: PromotionService = Depends(get_promotion_service_dependency)
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
            return {
                "status": "healthy", 
                "agent": "promotion_agent", 
                "version": "1.0.0",
                "db_connected": self.db_manager is not None and self.db_manager.is_initialized
            }

if __name__ == "__main__":
    agent = PromotionAgent()
    
    # Use environment variable for port, default to 8012
    port = int(os.getenv("PROMOTION_AGENT_PORT", 8012))
    host = os.getenv("PROMOTION_AGENT_HOST", "0.0.0.0")
    
    logger.info(f"Starting Promotion Agent API on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
