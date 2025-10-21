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
import asyncio
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import json

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
    """Manages database operations for promotions and promotion usage."""

    def __init__(self, db_manager: DatabaseManager):
        """Initializes the PromotionRepository with a database manager."""
        self.db = db_manager
    
    async def create_promotion(self, promo_data: PromotionCreate) -> Promotion:
        """Creates a new promotion in the database."""
        try:
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
            if result:
                logger.info("promotion_created_db", promotion_id=str(result["promotion_id"]))
                return Promotion(**result)
            else:
                raise ValueError("Failed to create promotion in DB.")
        except Exception as e:
            logger.error("create_promotion_db_failed", error=str(e), promo_data=promo_data.dict())
            raise
    
    async def get_promotion_by_code(self, promotion_code: str) -> Optional[Dict[str, Any]]:
        """Retrieves a promotion by its code."""
        try:
            query = "SELECT * FROM promotions WHERE promotion_code = $1 AND is_active = true"
            result = await self.db.fetch_one(query, promotion_code)
            return dict(result) if result else None
        except Exception as e:
            logger.error("get_promotion_by_code_db_failed", error=str(e), promotion_code=promotion_code)
            raise
    
    async def get_active_promotions(self) -> List[Dict[str, Any]]:
        """Retrieves all active promotions."""
        try:
            query = """
                SELECT * FROM promotions
                WHERE is_active = true
                AND start_date <= CURRENT_TIMESTAMP
                AND end_date >= CURRENT_TIMESTAMP
                ORDER BY created_at DESC
            """
            results = await self.db.fetch_all(query)
            return [dict(r) for r in results]
        except Exception as e:
            logger.error("get_active_promotions_db_failed", error=str(e))
            raise
    
    async def get_promotion_usage_count(self, promotion_id: UUID) -> int:
        """Gets the total usage count for a given promotion."""
        try:
            query = "SELECT COUNT(*) as count FROM promotion_usage WHERE promotion_id = $1"
            result = await self.db.fetch_one(query, promotion_id)
            return result["count"]
        except Exception as e:
            logger.error("get_promotion_usage_count_db_failed", error=str(e), promotion_id=promotion_id)
            raise
    
    async def get_customer_usage_count(self, promotion_id: UUID, customer_id: str) -> int:
        """Gets the usage count for a promotion by a specific customer."""
        try:
            query = """
                SELECT COUNT(*) as count FROM promotion_usage
                WHERE promotion_id = $1 AND customer_id = $2
            """
            result = await self.db.fetch_one(query, promotion_id, customer_id)
            return result["count"]
        except Exception as e:
            logger.error("get_customer_usage_count_db_failed", error=str(e), promotion_id=promotion_id, customer_id=customer_id)
            raise
    
    async def record_promotion_usage(
        self, promotion_id: UUID, customer_id: str, order_id: str, discount_amount: Decimal
    ) -> UUID:
        """Records the usage of a promotion."""
        try:
            query = """
                INSERT INTO promotion_usage (promotion_id, customer_id, order_id, discount_amount)
                VALUES ($1, $2, $3, $4)
                RETURNING usage_id
            """
            result = await self.db.fetch_one(query, promotion_id, customer_id, order_id, discount_amount)
            if result:
                logger.info("promotion_usage_recorded_db", usage_id=str(result["usage_id"]))
                return result["usage_id"]
            else:
                raise ValueError("Failed to record promotion usage in DB.")
        except Exception as e:
            logger.error("record_promotion_usage_db_failed", error=str(e), promotion_id=promotion_id, customer_id=customer_id, order_id=order_id)
            raise

# SERVICE
class PromotionService:
    """Handles business logic for promotions, including discount calculation and validation."""

    def __init__(self, repo: PromotionRepository):
        """Initializes the PromotionService with a PromotionRepository."""
        self.repo = repo
    
    def calculate_discount(
        self, promotion: Dict[str, Any], order_amount: Decimal
    ) -> Decimal:
        """Calculate discount amount based on promotion type.

        Args:
            promotion (Dict[str, Any]): The promotion details.
            order_amount (Decimal): The total amount of the order.

        Returns:
            Decimal: The calculated discount amount.
        """
        promo_type = promotion["promotion_type"]
        
        if promo_type == PromotionType.PERCENTAGE.value:
            discount = order_amount * (Decimal(str(promotion["discount_percentage"])) / 100)
            if promotion["max_discount_amount"]:
                discount = min(discount, Decimal(str(promotion["max_discount_amount"])))
            return discount
        
        elif promo_type == PromotionType.FIXED_AMOUNT.value:
            return Decimal(str(promotion["discount_value"]))
        
        elif promo_type == PromotionType.FREE_SHIPPING.value:
            # In production, get shipping cost from order
            return Decimal("10.00")  # Simulated shipping cost
        
        return Decimal("0.00")
    
    async def validate_promotion(
        self, request: PromotionValidationRequest
    ) -> PromotionValidationResponse:
        """Validates a promotion code against various rules and calculates the discount.

        Args:
            request (PromotionValidationRequest): The promotion validation request.

        Returns:
            PromotionValidationResponse: The response indicating validity and discount.
        """
        try:
            # Get promotion
            promotion = await self.repo.get_promotion_by_code(request.promotion_code)
            
            if not promotion:
                logger.warning("promotion_validation_failed", reason="code_not_found", promotion_code=request.promotion_code)
                return PromotionValidationResponse(
                    is_valid=False,
                    promotion=None,
                    final_amount=request.order_amount,
                    reason="Promotion code not found"
                )
            
            # Check if active and within date range
            now = datetime.utcnow()
            if not promotion["is_active"]:
                logger.warning("promotion_validation_failed", reason="not_active", promotion_id=str(promotion["promotion_id"]))
                return PromotionValidationResponse(
                    is_valid=False,
                    promotion=None,
                    final_amount=request.order_amount,
                    reason="Promotion is not active"
                )
            
            if now < promotion["start_date"] or now > promotion["end_date"]:
                logger.warning("promotion_validation_failed", reason="not_valid_time", promotion_id=str(promotion["promotion_id"]))
                return PromotionValidationResponse(
                    is_valid=False,
                    promotion=None,
                    final_amount=request.order_amount,
                    reason="Promotion is not valid at this time"
                )
            
            # Check minimum purchase amount
            if promotion["min_purchase_amount"]:
                if request.order_amount < Decimal(str(promotion["min_purchase_amount"])):
                    logger.warning("promotion_validation_failed", reason="min_purchase_not_met", promotion_id=str(promotion["promotion_id"]), required=promotion["min_purchase_amount"], actual=request.order_amount)
                    return PromotionValidationResponse(
                        is_valid=False,
                        promotion=None,
                        final_amount=request.order_amount,
                        reason=f"Minimum purchase amount of ${promotion["min_purchase_amount"]} required"
                    )
            
            # Check usage limits
            if promotion["usage_limit"]:
                total_usage = await self.repo.get_promotion_usage_count(promotion["promotion_id"])
                if total_usage >= promotion["usage_limit"]:
                    logger.warning("promotion_validation_failed", reason="usage_limit_reached", promotion_id=str(promotion["promotion_id"]), limit=promotion["usage_limit"], actual=total_usage)
                    return PromotionValidationResponse(
                        is_valid=False,
                        promotion=None,
                        final_amount=request.order_amount,
                        reason="Promotion usage limit reached"
                    )
            
            # Check per-customer usage
            customer_usage = await self.repo.get_customer_usage_count(
                promotion["promotion_id"], request.customer_id
            )
            if customer_usage >= promotion["usage_per_customer"]:
                logger.warning("promotion_validation_failed", reason="customer_usage_limit_reached", promotion_id=str(promotion["promotion_id"]), customer_id=request.customer_id, limit=promotion["usage_per_customer"], actual=customer_usage)
                return PromotionValidationResponse(
                    is_valid=False,
                    promotion=None,
                    final_amount=request.order_amount,
                    reason="You have already used this promotion"
                )
            
            # Check applicable products and categories (simplified)
            if promotion["applicable_products"] and not any(p in request.products for p in promotion["applicable_products"]):
                logger.warning("promotion_validation_failed", reason="no_applicable_products", promotion_id=str(promotion["promotion_id"]), products=request.products)
                return PromotionValidationResponse(
                    is_valid=False,
                    promotion=None,
                    final_amount=request.order_amount,
                    reason="No applicable products in order"
                )
            
            if promotion["applicable_categories"] and not any(c in request.categories for c in promotion["applicable_categories"]):
                logger.warning("promotion_validation_failed", reason="no_applicable_categories", promotion_id=str(promotion["promotion_id"]), categories=request.categories)
                return PromotionValidationResponse(
                    is_valid=False,
                    promotion=None,
                    final_amount=request.order_amount,
                    reason="No applicable categories in order"
                )
            
            # Check excluded products
            if promotion["excluded_products"] and any(p in request.products for p in promotion["excluded_products"]):
                logger.warning("promotion_validation_failed", reason="excluded_products_found", promotion_id=str(promotion["promotion_id"]), products=request.products)
                return PromotionValidationResponse(
                    is_valid=False,
                    promotion=None,
                    final_amount=request.order_amount,
                    reason="Order contains excluded products"
                )
            
            # Apply discount
            discount_amount = self.calculate_discount(promotion, request.order_amount)
            final_amount = max(Decimal("0.00"), request.order_amount - discount_amount)
            
            logger.info("promotion_validated", promotion_code=request.promotion_code,
                       discount_amount=float(discount_amount), final_amount=float(final_amount))
            
            return PromotionValidationResponse(
                is_valid=True,
                promotion=Promotion(**promotion),
                discount_amount=discount_amount,
                final_amount=final_amount,
                reason=None
            )
        except Exception as e:
            logger.error("validate_promotion_service_failed", error=str(e), request=request.dict())
            return PromotionValidationResponse(
                is_valid=False,
                promotion=None,
                discount_amount=Decimal("0.00"),
                final_amount=request.order_amount,
                reason=f"An unexpected error occurred: {e}"
            )

# FASTAPI APP
class PromotionAgent(BaseAgent):
    """PromotionAgent manages promotions, discounts, coupons, and marketing campaigns."""

    def __init__(self, agent_name: str):
        """Initializes the PromotionAgent with a name and sets up FastAPI app and routes."""
        super().__init__(agent_name)
        self.app = FastAPI(title=f"{agent_name} API", version="1.0.0")
        self.repo: Optional[PromotionRepository] = None
        self.service: Optional[PromotionService] = None
        self.db_manager: Optional[DatabaseManager] = None
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.KAFKA_PROMOTION_TOPIC = os.getenv("KAFKA_PROMOTION_TOPIC", "promotion_events")
        self.KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "promotion_agent_group")
        self.setup_routes()

    async def setup_db(self):
        """Sets up the database connection and initializes repository and service."""
        try:
            self.db_manager = await get_database_manager()
            self.repo = PromotionRepository(self.db_manager)
            self.service = PromotionService(self.repo)
            logger.info("database_setup_successful")
        except Exception as e:
            logger.error("database_setup_failed", error=str(e))
            raise

    async def setup_kafka(self):
        """Sets up Kafka producer and consumer."""
        try:
            self.producer = AIOKafkaProducer(bootstrap_servers=self.KAFKA_BOOTSTRAP_SERVERS)
            await self.producer.start()
            logger.info("kafka_producer_started")

            self.consumer = AIOKafkaConsumer(
                self.KAFKA_PROMOTION_TOPIC,
                bootstrap_servers=self.KAFKA_BOOTSTRAP_SERVERS,
                group_id=self.KAFKA_GROUP_ID,
                auto_offset_reset="earliest"
            )
            await self.consumer.start()
            asyncio.create_task(self.consume_messages())
            logger.info("kafka_consumer_started", topic=self.KAFKA_PROMOTION_TOPIC)

        except Exception as e:
            logger.error("kafka_setup_failed", error=str(e))
            raise

    async def consume_messages(self):
        """Consumes messages from Kafka topic and processes them."""
        try:
            async for msg in self.consumer:
                logger.info("received_kafka_message", topic=msg.topic, partition=msg.partition, offset=msg.offset, value=msg.value.decode())
                # Process message here (e.g., update promotion status, trigger campaign)
                message_data = json.loads(msg.value.decode())
                message_type = message_data.get("type")

                if message_type == "promotion_created":
                    logger.info("processing_promotion_created_event", promotion_id=message_data.get("promotion_id"))
                    # Example: Send a notification or log the event
                elif message_type == "promotion_updated":
                    logger.info("processing_promotion_updated_event", promotion_id=message_data.get("promotion_id"))
                else:
                    logger.warning("unknown_kafka_message_type", message_type=message_type)

        except Exception as e:
            logger.error("kafka_consume_failed", error=str(e))

    async def send_message(self, topic: str, message: Dict[str, Any]):
        """Sends a message to a Kafka topic."""
        try:
            await self.producer.send_and_wait(topic, json.dumps(message).encode())
            logger.info("kafka_message_sent", topic=topic, message=message)
        except Exception as e:
            logger.error("kafka_send_failed", error=str(e), topic=topic, message=message)
            raise

    def setup_routes(self):
        """Sets up FastAPI routes for promotion management."""
        @self.app.on_event("startup")
        async def startup_event():
            await self.setup_db()
            await self.setup_kafka()

        @self.app.on_event("shutdown")
        async def shutdown_event():
            if self.db_manager:
                await self.db_manager.disconnect()
                logger.info("database_disconnected")
            if self.producer:
                await self.producer.stop()
                logger.info("kafka_producer_stopped")
            if self.consumer:
                await self.consumer.stop()
                logger.info("kafka_consumer_stopped")

        @self.app.post("/api/v1/promotions", response_model=Promotion)
        async def create_promotion_endpoint(
            promo_data: PromotionCreate = Body(...),
        ):
            """Creates a new promotion. Args: promo_data (PromotionCreate): The data for the new promotion. Returns: Promotion: The created promotion. Raises: HTTPException: If the promotion creation fails."""
            try:
                promotion = await self.service.repo.create_promotion(promo_data)
                await self.send_message(self.KAFKA_PROMOTION_TOPIC, {"type": "promotion_created", "promotion_id": str(promotion.promotion_id), "promotion_code": promotion.promotion_code})
                logger.info("promotion_created", promotion_id=str(promotion.promotion_id))
                return promotion
            except Exception as e:
                logger.error("create_promotion_failed", error=str(e))
                raise HTTPException(status_code=500, detail=f"Failed to create promotion: {e}")

        @self.app.get("/api/v1/promotions/active")
        async def get_active_promotions_endpoint():
            """Retrieves all active promotions. Returns: Dict[str, List[Dict[str, Any]]]: A dictionary containing a list of active promotions. Raises: HTTPException: If retrieving active promotions fails."""
            try:
                promotions = await self.service.repo.get_active_promotions()
                return {"promotions": promotions}
            except Exception as e:
                logger.error("get_active_promotions_failed", error=str(e))
                raise HTTPException(status_code=500, detail=f"Failed to retrieve active promotions: {e}")

        @self.app.post("/api/v1/promotions/validate", response_model=PromotionValidationResponse)
        async def validate_promotion_endpoint(
            request: PromotionValidationRequest = Body(...),
        ):
            """Validates a promotion code and calculates discount. Args: request (PromotionValidationRequest): The request containing promotion code, customer ID, order amount, products, and categories. Returns: PromotionValidationResponse: The response indicating if the promotion is valid and the calculated discount. Raises: HTTPException: If promotion validation fails."""
            try:
                response = await self.service.validate_promotion(request)
                return response
            except Exception as e:
                logger.error("validate_promotion_failed", error=str(e))
                raise HTTPException(status_code=500, detail=f"Failed to validate promotion: {e}")

        @self.app.post("/api/v1/promotions/{promotion_id}/use")
        async def record_usage_endpoint(
            promotion_id: UUID = Path(...),
            customer_id: str = Body(..., embed=True),
            order_id: str = Body(..., embed=True),
            discount_amount: Decimal = Body(..., embed=True),
        ):
            """Records the usage of a promotion by a customer for a specific order. Args: promotion_id (UUID): The ID of the promotion. customer_id (str): The ID of the customer. order_id (str): The ID of the order. discount_amount (Decimal): The discount amount applied. Returns: Dict[str, Any]: A dictionary containing the usage ID and a confirmation message. Raises: HTTPException: If recording promotion usage fails."""
            try:
                usage_id = await self.service.repo.record_promotion_usage(
                    promotion_id, customer_id, order_id, discount_amount
                )
                await self.send_message(self.KAFKA_PROMOTION_TOPIC, {"type": "promotion_used", "promotion_id": str(promotion_id), "customer_id": customer_id, "order_id": order_id})
                return {"usage_id": usage_id, "message": "Promotion usage recorded"}
            except Exception as e:
                logger.error("record_usage_failed", error=str(e))
                raise HTTPException(status_code=500, detail=f"Failed to record usage: {e}")

        @self.app.get("/health")
        async def health_check_endpoint():
            """Health check endpoint. Returns: Dict[str, str]: A dictionary indicating the health status of the agent."""
            return {"status": "healthy", "agent": self.agent_name, "version": "1.0.0"}

    async def run(self):
        """Runs the FastAPI application using Uvicorn, listening on a configurable port."""
        import uvicorn
        port = int(os.getenv("PROMOTION_AGENT_PORT", 8012))
        logger.info("Promotion Agent starting", host="0.0.0.0", port=port)
        uvicorn.run(self.app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    agent = PromotionAgent(agent_name="PromotionAgent")
    asyncio.run(agent.run())

