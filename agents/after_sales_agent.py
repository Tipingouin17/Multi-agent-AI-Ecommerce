"""
After-Sales Agent
Handles RMA requests, returns, refunds, customer satisfaction, and warranty claims
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
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os


from shared.db_helpers import DatabaseHelper

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from shared.base_agent import BaseAgent
from shared.kafka_config import KafkaProducer, KafkaConsumer

logger = structlog.get_logger(__name__)


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


class ReturnRequest(BaseModel):
    """Return request model"""
    order_id: str
    customer_id: str
    items: List[Dict[str, Any]]
    return_reason: ReturnReason
    return_description: str
    return_type: ReturnType = ReturnType.REFUND
    requested_at: datetime = Field(default_factory=datetime.utcnow)


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
    filed_at: datetime = Field(default_factory=datetime.utcnow)


class AfterSalesAgent(BaseAgent):
    """
    After-Sales Agent
    
    Responsibilities:
    - Process return requests
    - Authorize RMA (Return Merchandise Authorization)
    - Handle refunds and exchanges
    - Manage customer satisfaction surveys
    - Process warranty claims
    - Track return shipments
    - Handle customer complaints
    """
    
    def __init__(self):
        super().__init__(agent_id="AfterSalesAgent")
        self.kafka_producer = None
        self.kafka_consumer = None
        self.return_window_days = 30  # Standard return window
        self.defect_return_window_days = 90  # Extended for defects
        
    async def initialize(self):
        """Initialize agent"""
        await super().initialize()
        self.kafka_producer = KafkaProducer()
        self.kafka_consumer = KafkaConsumer(*[
                "order_delivered",
                "return_request_submitted",
                "return_shipped",
                "return_received"
            ],
            group_id="after_sales_agent"
        )
        logger.info("After-Sales Agent initialized")
    
    async def process_return_request(self, request: ReturnRequest) -> Dict[str, Any]:
        """
        Process a return request from customer
        
        Args:
            request: Return request details
            
        Returns:
            RMA authorization or rejection
        """
        try:
            logger.info("Processing return request",
                       order_id=request.order_id,
                       reason=request.return_reason)
            
            # Retrieve order details
            order = await self._get_order_details(request.order_id)
            if not order:
                return {
                    "success": False,
                    "error": "Order not found"
                }
            
            # Check return eligibility
            eligibility = await self._check_return_eligibility(order, request)
            
            if not eligibility["eligible"]:
                logger.warning("Return request rejected",
                             order_id=request.order_id,
                             reason=eligibility["reason"])
                
                # Send rejection notification
                await self._send_rejection_notification(
                    request.customer_id,
                    request.order_id,
                    eligibility["reason"]
                )
                
                return {
                    "success": False,
                    "eligible": False,
                    "reason": eligibility["reason"]
                }
            
            # Generate RMA authorization
            rma = await self._generate_rma_authorization(order, request)
            
            # Save RMA to database
            await self._save_rma_authorization(rma)
            
            # Publish RMA authorized event
            await self.kafka_producer.send(
                "return_authorized",
                {
                    "rma_number": rma.rma_number,
                    "order_id": rma.order_id,
                    "customer_id": rma.customer_id,
                    "return_reason": rma.return_reason.value,
                    "return_type": rma.return_type.value,
                    "refund_amount": float(rma.refund_amount) if rma.refund_amount else 0,
                    "return_shipping_cost": float(rma.return_shipping_cost),
                    "authorized_at": rma.authorized_at.isoformat()
                }
            )
            
            # Request return label generation
            await self.kafka_producer.send(
                "generate_return_label",
                {
                    "rma_number": rma.rma_number,
                    "order_id": rma.order_id,
                    "customer_id": rma.customer_id
                }
            )
            
            logger.info("RMA authorized",
                       rma_number=rma.rma_number,
                       order_id=request.order_id)
            
            return {
                "success": True,
                "eligible": True,
                "rma_number": rma.rma_number,
                "return_type": rma.return_type.value,
                "refund_amount": float(rma.refund_amount) if rma.refund_amount else 0,
                "return_shipping_cost": float(rma.return_shipping_cost),
                "expires_at": rma.expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to process return request",
                        error=str(e),
                        order_id=request.order_id)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _check_return_eligibility(
        self,
        order: Dict[str, Any],
        request: ReturnRequest
    ) -> Dict[str, Any]:
        """
        Check if return is eligible based on policy
        
        Args:
            order: Order details
            request: Return request
            
        Returns:
            Eligibility result with reason
        """
        # Check order status
        if order["status"] not in ["delivered", "completed"]:
            return {
                "eligible": False,
                "reason": "Order must be delivered before return can be processed"
            }
        
        # Check return window
        order_date = datetime.fromisoformat(order["created_at"])
        days_since_order = (datetime.utcnow() - order_date).days
        
        # Extended window for defects
        if request.return_reason in [ReturnReason.PRODUCT_DEFECT, ReturnReason.DAMAGED_IN_SHIPPING]:
            max_days = self.defect_return_window_days
        else:
            max_days = self.return_window_days
        
        if days_since_order > max_days:
            return {
                "eligible": False,
                "reason": f"Return window expired ({max_days} days)"
            }
        
        # Check if already returned
        existing_rma = await self._check_existing_rma(order["order_id"])
        if existing_rma:
            return {
                "eligible": False,
                "reason": "Return already processed for this order"
            }
        
        # All checks passed
        return {
            "eligible": True,
            "reason": "Return eligible"
        }
    
    async def _generate_rma_authorization(
        self,
        order: Dict[str, Any],
        request: ReturnRequest
    ) -> RMAAuthorization:
        """Generate RMA authorization"""
        # Generate RMA number
        rma_number = f"RMA-{datetime.utcnow().strftime('%Y%m%d')}-{order['order_id'][-6:]}"
        
        # Calculate refund amount
        refund_amount = Decimal(str(order["total_amount"]))
        
        # Determine return shipping cost
        if request.return_reason in [
            ReturnReason.PRODUCT_DEFECT,
            ReturnReason.DAMAGED_IN_SHIPPING,
            ReturnReason.WRONG_ITEM,
            ReturnReason.NOT_AS_DESCRIBED
        ]:
            # Free return shipping for our errors
            return_shipping_cost = Decimal("0.00")
        else:
            # Customer pays return shipping
            return_shipping_cost = Decimal("5.00")  # Standard return shipping
        
        # Set expiration (30 days to return)
        expires_at = datetime.utcnow() + timedelta(days=30)
        
        return RMAAuthorization(
            rma_number=rma_number,
            order_id=request.order_id,
            customer_id=request.customer_id,
            return_reason=request.return_reason,
            return_type=request.return_type,
            refund_amount=refund_amount,
            return_shipping_cost=return_shipping_cost,
            status=RMAStatus.APPROVED,
            expires_at=expires_at
        )
    
    async def process_return_received(
        self,
        rma_number: str,
        condition: str,
        inspection_notes: str
    ) -> Dict[str, Any]:
        """
        Process return when received at warehouse
        
        Args:
            rma_number: RMA number
            condition: Product condition
            inspection_notes: Notes from inspection
            
        Returns:
            Processing result
        """
        try:
            logger.info("Processing received return",
                       rma_number=rma_number,
                       condition=condition)
            
            # Get RMA details
            rma = await self._get_rma_details(rma_number)
            if not rma:
                return {
                    "success": False,
                    "error": "RMA not found"
                }
            
            # Update RMA status
            await self._update_rma_status(rma_number, RMAStatus.RECEIVED)
            
            # Determine disposition based on condition and reason
            disposition = await self._determine_disposition(
                rma,
                condition,
                inspection_notes
            )
            
            # Process refund if approved
            if disposition["refund_approved"]:
                await self._process_refund(rma)
            
            # Publish return received event
            await self.kafka_producer.send(
                "return_received",
                {
                    "rma_number": rma_number,
                    "order_id": rma["order_id"],
                    "condition": condition,
                    "disposition": disposition["action"],
                    "refund_approved": disposition["refund_approved"],
                    "received_at": datetime.utcnow().isoformat()
                }
            )
            
            logger.info("Return processed",
                       rma_number=rma_number,
                       disposition=disposition["action"])
            
            return {
                "success": True,
                "disposition": disposition["action"],
                "refund_approved": disposition["refund_approved"]
            }
            
        except Exception as e:
            logger.error("Failed to process return",
                        error=str(e),
                        rma_number=rma_number)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _determine_disposition(
        self,
        rma: Dict[str, Any],
        condition: str,
        inspection_notes: str
    ) -> Dict[str, Any]:
        """Determine what to do with returned product"""
        if condition == "defective":
            return {
                "action": "return_to_manufacturer",
                "refund_approved": True,
                "restock": False
            }
        elif condition == "damaged":
            return {
                "action": "dispose",
                "refund_approved": True,
                "restock": False
            }
        elif condition == "like_new":
            return {
                "action": "restock",
                "refund_approved": True,
                "restock": True
            }
        elif condition == "used":
            return {
                "action": "restock_as_refurbished",
                "refund_approved": True,
                "restock": True
            }
        else:
            return {
                "action": "manual_review",
                "refund_approved": False,
                "restock": False
            }
    
    async def _process_refund(self, rma: Dict[str, Any]) -> bool:
        """Process refund for approved return"""
        try:
            # Publish refund request
            await self.kafka_producer.send(
                "refund_requested",
                {
                    "rma_number": rma["rma_number"],
                    "order_id": rma["order_id"],
                    "customer_id": rma["customer_id"],
                    "refund_amount": float(rma["refund_amount"]),
                    "refund_method": "original_payment",
                    "requested_at": datetime.utcnow().isoformat()
                }
            )
            
            logger.info("Refund requested",
                       rma_number=rma["rma_number"],
                       amount=rma["refund_amount"])
            
            return True
            
        except Exception as e:
            logger.error("Failed to process refund",
                        error=str(e),
                        rma_number=rma["rma_number"])
            return False
    
    async def send_satisfaction_survey(
        self,
        order_id: str,
        customer_id: str
    ) -> bool:
        """
        Send customer satisfaction survey after delivery
        
        Args:
            order_id: Order ID
            customer_id: Customer ID
            
        Returns:
            Success status
        """
        try:
            # Wait 24 hours after delivery before sending survey
            await asyncio.sleep(86400)  # In production, use scheduled task
            
            # Publish survey request
            await self.kafka_producer.send(
                "send_satisfaction_survey",
                {
                    "order_id": order_id,
                    "customer_id": customer_id,
                    "survey_type": "post_delivery",
                    "sent_at": datetime.utcnow().isoformat()
                }
            )
            
            logger.info("Satisfaction survey sent",
                       order_id=order_id,
                       customer_id=customer_id)
            
            return True
            
        except Exception as e:
            logger.error("Failed to send survey",
                        error=str(e),
                        order_id=order_id)
            return False
    
    async def process_warranty_claim(
        self,
        claim: WarrantyClaim
    ) -> Dict[str, Any]:
        """
        Process warranty claim
        
        Args:
            claim: Warranty claim details
            
        Returns:
            Claim processing result
        """
        try:
            logger.info("Processing warranty claim",
                       claim_id=claim.claim_id,
                       order_id=claim.order_id)
            
            # Verify warranty coverage
            warranty_valid = await self._verify_warranty(
                claim.order_id,
                claim.product_id,
                claim.warranty_type
            )
            
            if not warranty_valid:
                return {
                    "success": False,
                    "claim_status": "rejected",
                    "reason": "Warranty expired or not applicable"
                }
            
            # Save claim to database
            await self._save_warranty_claim(claim)
            
            # Publish warranty claim event
            await self.kafka_producer.send(
                "warranty_claim_filed",
                {
                    "claim_id": claim.claim_id,
                    "order_id": claim.order_id,
                    "product_id": claim.product_id,
                    "customer_id": claim.customer_id,
                    "warranty_type": claim.warranty_type,
                    "filed_at": claim.filed_at.isoformat()
                }
            )
            
            logger.info("Warranty claim filed",
                       claim_id=claim.claim_id)
            
            return {
                "success": True,
                "claim_id": claim.claim_id,
                "claim_status": "pending_review",
                "estimated_resolution_days": 5
            }
            
        except Exception as e:
            logger.error("Failed to process warranty claim",
                        error=str(e),
                        claim_id=claim.claim_id)
            return {
                "success": False,
                "error": str(e)
            }
    
    # Database helper methods
    async def _get_order_details(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order details from database"""
        # Implementation would query database
        # For now, return mock data
        return {
            "order_id": order_id,
            "customer_id": "CUST123",
            "status": "delivered",
            "total_amount": 99.99,
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def _check_existing_rma(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Check if RMA already exists for order"""
        # Implementation would query database
        return None
    
    async def _save_rma_authorization(self, rma: RMAAuthorization) -> bool:
        """Save RMA authorization to database"""
        # Implementation would save to database
        return True
    
    async def _get_rma_details(self, rma_number: str) -> Optional[Dict[str, Any]]:
        """Get RMA details from database"""
        # Implementation would query database
        return {
            "rma_number": rma_number,
            "order_id": "ORD123",
            "customer_id": "CUST123",
            "refund_amount": 99.99
        }
    
    async def _update_rma_status(self, rma_number: str, status: RMAStatus) -> bool:
        """Update RMA status in database"""
        # Implementation would update database
        return True
    
    async def _verify_warranty(
        self,
        order_id: str,
        product_id: str,
        warranty_type: str
    ) -> bool:
        """Verify warranty is still valid"""
        # Implementation would check warranty expiration
        return True
    
    async def _save_warranty_claim(self, claim: WarrantyClaim) -> bool:
        """Save warranty claim to database"""
        # Implementation would save to database
        return True
    
    async def _send_rejection_notification(
        self,
        customer_id: str,
        order_id: str,
        reason: str
    ) -> bool:
        """Send return rejection notification to customer"""
        await self.kafka_producer.send(
            "send_notification",
            {
                "customer_id": customer_id,
                "notification_type": "return_rejected",
                "order_id": order_id,
                "reason": reason,
                "sent_at": datetime.utcnow().isoformat()
            }
        )
        return True
    
    async def run(self):
        """Main agent loop"""
        logger.info("After-Sales Agent starting...")
        await self.initialize()
        
        try:
            async for message in self.kafka_consumer:
                topic = message.topic
                data = message.value
                
                if topic == "order_delivered":
                    # Schedule satisfaction survey
                    asyncio.create_task(
                        self.send_satisfaction_survey(
                            data["order_id"],
                            data["customer_id"]
                        )
                    )
                
                elif topic == "return_request_submitted":
                    # Process return request
                    request = ReturnRequest(**data)
                    await self.process_return_request(request)
                
                elif topic == "return_received":
                    # Process received return
                    await self.process_return_received(
                        data["rma_number"],
                        data["condition"],
                        data.get("inspection_notes", "")
                    )
                
        except Exception as e:
            logger.error("Error in agent loop", error=str(e))
        finally:
            await self.shutdown()
    
    async def cleanup(self):
        """Cleanup agent resources"""
        try:
            if self.kafka_producer:
                await self.kafka_producer.stop()
            if self.kafka_consumer:
                await self.kafka_consumer.stop()
            if self.db_manager:
                await self.db_manager.close()
            await super().cleanup()
            logger.info(f"{self.agent_name} cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process after-sales business logic
        
        Args:
            data: Dictionary containing operation type and parameters
            
        Returns:
            Dictionary with processing results
        """
        try:
            operation = data.get("operation", "create_return")
            
            if operation == "create_return":
                # Create return request
                return_request = ReturnRequest(**data.get("return_request", {}))
                rma_number = await self.create_return_request(return_request)
                return {"status": "success", "rma_number": rma_number}
            
            elif operation == "approve_return":
                # Approve return
                rma_number = data.get("rma_number")
                approved_by = data.get("approved_by")
                result = await self.approve_return(rma_number, approved_by)
                return {"status": "success", "result": result}
            
            elif operation == "process_refund":
                # Process refund
                rma_number = data.get("rma_number")
                refund_amount = data.get("refund_amount")
                result = await self.process_refund(rma_number, refund_amount)
                return {"status": "success", "result": result}
            
            elif operation == "warranty_claim":
                # Process warranty claim
                claim = WarrantyClaim(**data.get("claim", {}))
                claim_id = await self.process_warranty_claim(claim)
                return {"status": "success", "claim_id": claim_id}
            
            else:
                return {"status": "error", "message": f"Unknown operation: {operation}"}
                
        except Exception as e:
            logger.error(f"Error in process_business_logic: {e}")
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    agent = AfterSalesAgent()
    asyncio.run(agent.run())



# FastAPI Server Setup
app = FastAPI(
    title="After Sales Agent",
    description="After Sales Agent - Multi-Agent E-commerce Platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent": "after_sales_agent"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "agent": "after_sales_agent",
        "status": "running",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8011))
    uvicorn.run(app, host="0.0.0.0", port=port)
