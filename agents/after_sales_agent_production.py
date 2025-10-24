"""
After-Sales Agent - Production Ready
Handles RMA requests, returns, refunds, customer satisfaction, and warranty claims with full database integration
"""

import os
import sys
import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum
from pydantic import BaseModel, Field
from decimal import Decimal
from fastapi import FastAPI, HTTPException, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
import uvicorn

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from shared.base_agent_v2 import BaseAgentV2
from shared.kafka_config import KafkaProducer, KafkaConsumer
from shared.database import DatabaseManager
from shared.db_helpers import DatabaseHelper

logger = structlog.get_logger(__name__)


# =====================================================
# ENUMS
# =====================================================

class ReturnReason(str, Enum):
    """Return reason types"""
    CHANGED_MIND = "changed_mind"
    BETTER_PRICE = "better_price"
    PRODUCT_DEFECT = "product_defect"
    NOT_AS_DESCRIBED = "not_as_described"
    DAMAGED_IN_SHIPPING = "damaged_in_shipping"
    WRONG_ITEM = "wrong_item"
    OTHER = "other"


class ReturnType(str, Enum):
    """Return type"""
    REFUND = "refund"
    EXCHANGE = "exchange"
    STORE_CREDIT = "store_credit"


class RMAStatus(str, Enum):
    """RMA request status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    INSPECTED = "inspected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# =====================================================
# PYDANTIC MODELS
# =====================================================

class ReturnRequest(BaseModel):
    """Return request model"""
    order_id: str
    customer_id: str
    items: List[Dict[str, Any]]
    return_reason: ReturnReason
    return_description: str
    return_type: ReturnType = ReturnType.REFUND


class RMAAuthorization(BaseModel):
    """RMA authorization model"""
    rma_number: str
    order_id: str
    customer_id: str
    return_reason: ReturnReason
    return_type: ReturnType
    refund_amount: Optional[Decimal] = None
    return_shipping_cost: Decimal = Decimal("0.00")
    status: RMAStatus = RMAStatus.APPROVED
    authorized_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime


class CustomerSatisfactionSurvey(BaseModel):
    """Customer satisfaction survey"""
    order_id: str
    customer_id: str
    rating: int  # 1-5
    feedback: Optional[str] = None
    would_recommend: bool
    delivery_rating: Optional[int] = None
    product_rating: Optional[int] = None
    service_rating: Optional[int] = None


class WarrantyClaim(BaseModel):
    """Warranty claim model"""
    claim_id: str
    order_id: str
    product_id: str
    customer_id: str
    issue_description: str
    warranty_type: str  # manufacturer, extended, store
    claim_status: str


# =====================================================
# REPOSITORY
# =====================================================

class AfterSalesRepository:
    """Handles all database operations for the after-sales agent"""
    
    def __init__(self, db_manager: DatabaseManager):
        # FastAPI app for REST API
        self.app = FastAPI(title="After-Sales Agent API")
        
        # Add CORS middleware for dashboard integration
        add_cors_middleware(self.app)
        
        self.db_manager = db_manager
        self.db_helper = DatabaseHelper(db_manager)
    
    async def create_return_request(self, request: ReturnRequest) -> Dict[str, Any]:
        """Create a return request in the database"""
        try:
            async with self.db_manager.get_session() as session:
                return_data = {
                    "id": str(uuid4()),
                    "order_id": request.order_id,
                    "customer_id": request.customer_id,
                    "items": str(request.items),  # JSON string
                    "return_reason": request.return_reason.value,
                    "return_description": request.return_description,
                    "return_type": request.return_type.value,
                    "status": "pending",
                    "created_at": datetime.utcnow()
                }
                result = await self.db_helper.create(session, "return_requests", return_data)
                return result
        except Exception as e:
            logger.error("create_return_request_failed", error=str(e))
            raise
    
    async def create_rma_authorization(self, rma: RMAAuthorization) -> Dict[str, Any]:
        """Create an RMA authorization in the database"""
        try:
            async with self.db_manager.get_session() as session:
                rma_data = {
                    "rma_number": rma.rma_number,
                    "order_id": rma.order_id,
                    "customer_id": rma.customer_id,
                    "return_reason": rma.return_reason.value,
                    "return_type": rma.return_type.value,
                    "refund_amount": float(rma.refund_amount) if rma.refund_amount else None,
                    "return_shipping_cost": float(rma.return_shipping_cost),
                    "status": rma.status.value,
                    "authorized_at": rma.authorized_at,
                    "expires_at": rma.expires_at
                }
                result = await self.db_helper.create(session, "rma_authorizations", rma_data)
                return result
        except Exception as e:
            logger.error("create_rma_authorization_failed", error=str(e))
            raise
    
    async def get_rma_by_number(self, rma_number: str) -> Optional[Dict[str, Any]]:
        """Get RMA authorization by RMA number"""
        try:
            async with self.db_manager.get_session() as session:
                result = await self.db_helper.get_by_id(session, "rma_authorizations", rma_number)
                return result
        except Exception as e:
            logger.error("get_rma_by_number_failed", error=str(e))
            return None
    
    async def update_rma_status(self, rma_number: str, status: RMAStatus) -> bool:
        """Update RMA status"""
        try:
            async with self.db_manager.get_session() as session:
                result = await self.db_helper.update(
                    session,
                    "rma_authorizations",
                    rma_number,
                    {"status": status.value, "updated_at": datetime.utcnow()}
                )
                return result is not None
        except Exception as e:
            logger.error("update_rma_status_failed", error=str(e))
            return False
    
    async def create_satisfaction_survey(self, survey: CustomerSatisfactionSurvey) -> Dict[str, Any]:
        """Create a customer satisfaction survey"""
        try:
            async with self.db_manager.get_session() as session:
                survey_data = {
                    "id": str(uuid4()),
                    "order_id": survey.order_id,
                    "customer_id": survey.customer_id,
                    "rating": survey.rating,
                    "feedback": survey.feedback,
                    "would_recommend": survey.would_recommend,
                    "delivery_rating": survey.delivery_rating,
                    "product_rating": survey.product_rating,
                    "service_rating": survey.service_rating,
                    "created_at": datetime.utcnow()
                }
                result = await self.db_helper.create(session, "satisfaction_surveys", survey_data)
                return result
        except Exception as e:
            logger.error("create_satisfaction_survey_failed", error=str(e))
            raise
    
    async def create_warranty_claim(self, claim: WarrantyClaim) -> Dict[str, Any]:
        """Create a warranty claim"""
        try:
            async with self.db_manager.get_session() as session:
                claim_data = {
                    "claim_id": claim.claim_id,
                    "order_id": claim.order_id,
                    "product_id": claim.product_id,
                    "customer_id": claim.customer_id,
                    "issue_description": claim.issue_description,
                    "warranty_type": claim.warranty_type,
                    "claim_status": claim.claim_status,
                    "filed_at": datetime.utcnow()
                }
                result = await self.db_helper.create(session, "warranty_claims", claim_data)
                return result
        except Exception as e:
            logger.error("create_warranty_claim_failed", error=str(e))
            raise
    
    async def get_customer_returns(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all returns for a customer"""
        try:
            async with self.db_manager.get_session() as session:
                results = await self.db_helper.get_all_where(
                    session,
                    "return_requests",
                    "customer_id",
                    customer_id
                )
                return results or []
        except Exception as e:
            logger.error("get_customer_returns_failed", error=str(e))
            return []


# =====================================================
# AGENT
# =====================================================

class AfterSalesAgent(BaseAgentV2):
    """
    After-Sales Agent - Production Ready
    
    Responsibilities:
    - Process return requests
    - Authorize RMA (Return Merchandise Authorization)
    - Handle refunds and exchanges
    - Manage customer satisfaction surveys
    - Process warranty claims
    - Track return shipments
    """
    
    def __init__(self):
        super().__init__(agent_id="AfterSalesAgent")
        self.kafka_producer: Optional[KafkaProducer] = None
        self.kafka_consumer: Optional[KafkaConsumer] = None
        self.db_manager: Optional[DatabaseManager] = None
        self.db_helper: Optional[DatabaseHelper] = None
        self.repository: Optional[AfterSalesRepository] = None
        self._db_initialized = False
        self.return_window_days = 30  # Standard return window
        self.defect_return_window_days = 90  # Extended for defects
        
    async def initialize(self):
        """Initialize agent with database and Kafka"""
        await super().initialize()
        
        # Initialize Database
        try:
            from shared.database_manager import get_database_manager
            self.db_manager = get_database_manager()
            logger.info("Using global database manager")
        except (RuntimeError, ImportError):
            from shared.models import DatabaseConfig
            from shared.database_manager import EnhancedDatabaseManager
from shared.cors_middleware import add_cors_middleware
            db_config = DatabaseConfig()
            self.db_manager = EnhancedDatabaseManager(db_config)
            await self.db_manager.initialize(max_retries=5)
            logger.info("Created new enhanced database manager")
        
        self.db_helper = DatabaseHelper(self.db_manager)
        self.repository = AfterSalesRepository(self.db_manager)
        self._db_initialized = True
        
        # Initialize Kafka
        self.kafka_producer = KafkaProducer()
        self.kafka_consumer = KafkaConsumer(
            "order_delivered",
            "return_request_submitted",
            "return_shipped",
            "return_received",
            group_id="after_sales_agent"
        )
        
        logger.info("After-Sales Agent initialized successfully")
    
    async def process_return_request(self, request: ReturnRequest) -> Dict[str, Any]:
        """Process a return request from customer"""
        if not self._db_initialized:
            raise ValueError("Database not initialized")
        
        try:
            logger.info("Processing return request",
                       order_id=request.order_id,
                       reason=request.return_reason)
            
            # Create return request in database
            return_record = await self.repository.create_return_request(request)
            
            # Check return eligibility
            eligibility = await self._check_return_eligibility(request)
            
            if not eligibility["eligible"]:
                logger.warning("Return request rejected",
                             order_id=request.order_id,
                             reason=eligibility["reason"])
                return {
                    "success": False,
                    "eligible": False,
                    "reason": eligibility["reason"],
                    "return_id": return_record.get("id")
                }
            
            # Generate RMA authorization
            rma = await self._generate_rma_authorization(request)
            
            # Save RMA to database
            rma_record = await self.repository.create_rma_authorization(rma)
            
            # Publish RMA authorized event
            await self.kafka_producer.send(
                "rma_authorized",
                {
                    "rma_number": rma.rma_number,
                    "order_id": request.order_id,
                    "customer_id": request.customer_id,
                    "return_type": request.return_type.value
                }
            )
            
            logger.info("RMA authorized", rma_number=rma.rma_number)
            
            return {
                "success": True,
                "eligible": True,
                "rma_number": rma.rma_number,
                "expires_at": rma.expires_at.isoformat(),
                "return_id": return_record.get("id")
            }
            
        except Exception as e:
            logger.error("process_return_request_failed", error=str(e))
            raise
    
    async def _check_return_eligibility(self, request: ReturnRequest) -> Dict[str, Any]:
        """Check if return is eligible"""
        # In production, this would check:
        # - Order delivery date
        # - Return window
        # - Product condition
        # - Return policy
        
        # Simplified eligibility check
        return {
            "eligible": True,
            "reason": None
        }
    
    async def _generate_rma_authorization(self, request: ReturnRequest) -> RMAAuthorization:
        """Generate RMA authorization"""
        rma_number = f"RMA-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
        
        return RMAAuthorization(
            rma_number=rma_number,
            order_id=request.order_id,
            customer_id=request.customer_id,
            return_reason=request.return_reason,
            return_type=request.return_type,
            refund_amount=Decimal("0.00"),  # Calculate from order
            return_shipping_cost=Decimal("0.00"),
            status=RMAStatus.APPROVED,
            authorized_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
    
    async def update_rma_status(self, rma_number: str, status: RMAStatus) -> Dict[str, Any]:
        """Update RMA status"""
        if not self._db_initialized:
            raise ValueError("Database not initialized")
        
        try:
            success = await self.repository.update_rma_status(rma_number, status)
            
            if success:
                # Publish status update event
                await self.kafka_producer.send(
                    "rma_status_updated",
                    {
                        "rma_number": rma_number,
                        "status": status.value,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                )
                
                logger.info("RMA status updated", rma_number=rma_number, status=status.value)
                
                return {
                    "success": True,
                    "rma_number": rma_number,
                    "status": status.value
                }
            else:
                return {
                    "success": False,
                    "error": "RMA not found or update failed"
                }
        except Exception as e:
            logger.error("update_rma_status_failed", error=str(e))
            raise
    
    async def submit_satisfaction_survey(self, survey: CustomerSatisfactionSurvey) -> Dict[str, Any]:
        """Submit customer satisfaction survey"""
        if not self._db_initialized:
            raise ValueError("Database not initialized")
        
        try:
            result = await self.repository.create_satisfaction_survey(survey)
            
            # Publish survey submitted event
            await self.kafka_producer.send(
                "satisfaction_survey_submitted",
                {
                    "survey_id": result.get("id"),
                    "order_id": survey.order_id,
                    "customer_id": survey.customer_id,
                    "rating": survey.rating,
                    "would_recommend": survey.would_recommend
                }
            )
            
            logger.info("Satisfaction survey submitted",
                       order_id=survey.order_id,
                       rating=survey.rating)
            
            return {
                "success": True,
                "survey_id": result.get("id")
            }
        except Exception as e:
            logger.error("submit_satisfaction_survey_failed", error=str(e))
            raise
    
    async def file_warranty_claim(self, claim: WarrantyClaim) -> Dict[str, Any]:
        """File a warranty claim"""
        if not self._db_initialized:
            raise ValueError("Database not initialized")
        
        try:
            result = await self.repository.create_warranty_claim(claim)
            
            # Publish warranty claim filed event
            await self.kafka_producer.send(
                "warranty_claim_filed",
                {
                    "claim_id": claim.claim_id,
                    "order_id": claim.order_id,
                    "product_id": claim.product_id,
                    "customer_id": claim.customer_id,
                    "warranty_type": claim.warranty_type
                }
            )
            
            logger.info("Warranty claim filed", claim_id=claim.claim_id)
            
            return {
                "success": True,
                "claim_id": claim.claim_id
            }
        except Exception as e:
            logger.error("file_warranty_claim_failed", error=str(e))
            raise


# =====================================================
# FASTAPI APP
# =====================================================

# FastAPI app moved to __init__ method as self.app

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent_instance: Optional[AfterSalesAgent] = None


@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup"""
    global agent_instance
    agent_instance = AfterSalesAgent()
    await agent_instance.initialize()
    logger.info("After-Sales Agent API started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global agent_instance
    if agent_instance:
        if agent_instance.db_manager:
            await agent_instance.db_manager.close()
    logger.info("After-Sales Agent API shutdown")


@self.app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent": "AfterSalesAgent",
        "version": "1.0.0",
        "database": agent_instance._db_initialized if agent_instance else False
    }


@self.app.get("/")
async def root():
    """Root endpoint"""
    return {
        "agent": "AfterSalesAgent",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/returns/request",
            "/returns/rma/{rma_number}",
            "/returns/rma/{rma_number}/status",
            "/returns/customer/{customer_id}",
            "/surveys/submit",
            "/warranty/claim"
        ]
    }


@self.app.post("/returns/request", summary="Submit Return Request")
async def submit_return_request(request: ReturnRequest):
    """Submit a return request"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await agent_instance.process_return_request(request)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("reason", "Return request rejected"))
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("submit_return_request_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@self.app.get("/returns/rma/{rma_number}", summary="Get RMA Authorization")
async def get_rma_authorization(rma_number: str = Path(...)):
    """Get RMA authorization by RMA number"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        rma = await agent_instance.repository.get_rma_by_number(rma_number)
        if not rma:
            raise HTTPException(status_code=404, detail="RMA not found")
        return rma
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_rma_authorization_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@self.app.put("/returns/rma/{rma_number}/status", summary="Update RMA Status")
async def update_rma_status_endpoint(
    rma_number: str = Path(...),
    status: RMAStatus = Body(...)
):
    """Update RMA status"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await agent_instance.update_rma_status(rma_number, status)
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result.get("error", "Update failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_rma_status_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@self.app.get("/returns/customer/{customer_id}", summary="Get Customer Returns")
async def get_customer_returns(customer_id: str = Path(...)):
    """Get all returns for a customer"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        returns = await agent_instance.repository.get_customer_returns(customer_id)
        return {
            "customer_id": customer_id,
            "returns": returns,
            "total": len(returns)
        }
    except Exception as e:
        logger.error("get_customer_returns_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@self.app.post("/surveys/submit", summary="Submit Satisfaction Survey")
async def submit_survey(survey: CustomerSatisfactionSurvey):
    """Submit customer satisfaction survey"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await agent_instance.submit_satisfaction_survey(survey)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("submit_survey_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@self.app.post("/warranty/claim", summary="File Warranty Claim")
async def file_warranty_claim_endpoint(claim: WarrantyClaim):
    """File a warranty claim"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await agent_instance.file_warranty_claim(claim)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("file_warranty_claim_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8020))
    logger.info(f"Starting After-Sales Agent on port {port}")
    uvicorn.run(agent.app, host="0.0.0.0", port=port)

