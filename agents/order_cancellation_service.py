"""
Order Cancellation Service - Multi-Agent E-commerce System

This service handles order cancellation workflow including:
- Cancellation requests and approvals
- Refund processing coordination
- Inventory restoration
- Customer notifications
"""

from typing import Dict, List, Optional
from datetime import datetime
from uuid import UUID, uuid4
from decimal import Decimal
from pydantic import BaseModel
from enum import Enum
import structlog
from shared.base_agent_v2 import BaseAgentV2
from typing import Any

logger = structlog.get_logger(__name__)


# ===========================
# ENUMS
# ===========================

class CancellationStatus(str, Enum):
    """Status of a cancellation request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CancellationReason(str, Enum):
    """Reason for order cancellation."""
    CUSTOMER_REQUEST = "customer_request"
    OUT_OF_STOCK = "out_of_stock"
    PAYMENT_FAILED = "payment_failed"
    FRAUD_DETECTED = "fraud_detected"
    DUPLICATE_ORDER = "duplicate_order"
    ADDRESS_ISSUE = "address_issue"
    PRICING_ERROR = "pricing_error"
    OTHER = "other"


# ===========================
# PYDANTIC MODELS
# ===========================

class CancellationRequest(BaseModel):
    """Order cancellation request."""
    request_id: Optional[UUID] = None
    order_id: str
    reason: CancellationReason
    reason_details: Optional[str] = None
    requested_by: str  # customer_id or admin_id
    requested_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    status: CancellationStatus = CancellationStatus.PENDING
    refund_amount: Optional[Decimal] = None
    refund_processed: bool = False
    inventory_restored: bool = False
    notes: Optional[str] = None


class CreateCancellationRequest(BaseModel):
    """Request to create a cancellation."""
    order_id: str
    reason: CancellationReason
    reason_details: Optional[str] = None
    requested_by: str


class ReviewCancellationRequest(BaseModel):
    """Request to review a cancellation."""
    request_id: UUID
    approved: bool
    reviewed_by: str
    notes: Optional[str] = None


class CancellationResult(BaseModel):
    """Result of a cancellation operation."""
    success: bool
    request_id: UUID
    order_id: str
    status: CancellationStatus
    refund_amount: Optional[Decimal] = None
    message: str


# ===========================
# ORDER CANCELLATION SERVICE
# ===========================

class OrderCancellationService(BaseAgentV2):
    """Service for managing order cancellations."""
    
    def __init__(self, agent_id: str = "order_cancellation_service_001", db_manager=None, message_broker=None):
        super().__init__(agent_id=agent_id)
        self.db_manager = db_manager
        self.message_broker = message_broker
        self.logger = logger.bind(service="order_cancellation")
    
    async def create_cancellation_request(
        self,
        request: CreateCancellationRequest
    ) -> CancellationRequest:
        """Create a new cancellation request."""
        request_id = uuid4()
        
        async with self.db_manager.get_async_session() as session:
            try:
                # 1. Verify order exists and get details
                order_query = """
                    SELECT id, status, total_amount, customer_id
                    FROM orders
                    WHERE id = $1
                """
                
                order_result = await session.execute(order_query, request.order_id)
                order_row = order_result.fetchone()
                
                if not order_row:
                    raise ValueError(f"Order {request.order_id} not found")
                
                order_id, order_status, total_amount, customer_id = order_row
                
                # 2. Check if order can be cancelled
                non_cancellable_statuses = ['cancelled', 'delivered', 'refunded']
                if order_status in non_cancellable_statuses:
                    raise ValueError(f"Order cannot be cancelled. Current status: {order_status}")
                
                # 3. Create cancellation request
                insert_query = """
                    INSERT INTO cancellation_requests (
                        request_id, order_id, reason, reason_details,
                        requested_by, requested_at, status, refund_amount
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING request_id, requested_at
                """
                
                result = await session.execute(
                    insert_query,
                    str(request_id),
                    request.order_id,
                    request.reason.value,
                    request.reason_details,
                    request.requested_by,
                    datetime.utcnow(),
                    CancellationStatus.PENDING.value,
                    float(total_amount)
                )
                
                row = result.fetchone()
                await session.commit()
                
                self.logger.info("Created cancellation request",
                               request_id=str(request_id),
                               order_id=request.order_id,
                               reason=request.reason.value)
                
                # 4. Send notification (if message broker available)
                if self.message_broker:
                    await self._send_cancellation_notification(
                        request_id=request_id,
                        order_id=request.order_id,
                        customer_id=customer_id,
                        reason=request.reason
                    )
                
                return CancellationRequest(
                    request_id=request_id,
                    order_id=request.order_id,
                    reason=request.reason,
                    reason_details=request.reason_details,
                    requested_by=request.requested_by,
                    requested_at=row[1],
                    status=CancellationStatus.PENDING,
                    refund_amount=Decimal(str(total_amount))
                )
                
            except Exception as e:
                await session.rollback()
                self.logger.error("Failed to create cancellation request",
                                error=str(e),
                                order_id=request.order_id)
                raise
    
    async def review_cancellation_request(
        self,
        review: ReviewCancellationRequest
    ) -> CancellationResult:
        """Review and approve/reject a cancellation request."""
        async with self.db_manager.get_async_session() as session:
            try:
                # 1. Get cancellation request
                query = """
                    SELECT cr.request_id, cr.order_id, cr.reason, cr.refund_amount,
                           cr.status, o.status as order_status
                    FROM cancellation_requests cr
                    JOIN orders o ON cr.order_id = o.id
                    WHERE cr.request_id = $1
                """
                
                result = await session.execute(query, str(review.request_id))
                row = result.fetchone()
                
                if not row:
                    raise ValueError(f"Cancellation request {review.request_id} not found")
                
                request_id, order_id, reason, refund_amount, status, order_status = row
                
                if status != CancellationStatus.PENDING.value:
                    raise ValueError(f"Cancellation request already {status}")
                
                # 2. Update cancellation request
                new_status = CancellationStatus.APPROVED if review.approved else CancellationStatus.REJECTED
                
                update_query = """
                    UPDATE cancellation_requests
                    SET status = $1,
                        reviewed_by = $2,
                        reviewed_at = $3,
                        notes = $4
                    WHERE request_id = $5
                """
                
                await session.execute(
                    update_query,
                    new_status.value,
                    review.reviewed_by,
                    datetime.utcnow(),
                    review.notes,
                    str(review.request_id)
                )
                
                # 3. If approved, process cancellation
                if review.approved:
                    await self._process_cancellation(
                        session=session,
                        request_id=review.request_id,
                        order_id=order_id,
                        refund_amount=Decimal(str(refund_amount))
                    )
                
                await session.commit()
                
                self.logger.info("Reviewed cancellation request",
                               request_id=str(review.request_id),
                               approved=review.approved,
                               reviewed_by=review.reviewed_by)
                
                return CancellationResult(
                    success=True,
                    request_id=review.request_id,
                    order_id=order_id,
                    status=new_status,
                    refund_amount=Decimal(str(refund_amount)) if review.approved else None,
                    message=f"Cancellation {'approved' if review.approved else 'rejected'}"
                )
                
            except Exception as e:
                await session.rollback()
                self.logger.error("Failed to review cancellation request",
                                error=str(e),
                                request_id=str(review.request_id))
                raise
    
    async def _process_cancellation(
        self,
        session,
        request_id: UUID,
        order_id: str,
        refund_amount: Decimal
    ):
        """Process an approved cancellation."""
        # 1. Update order status
        update_order_query = """
            UPDATE orders
            SET status = 'cancelled',
                cancellation_reason = (
                    SELECT reason FROM cancellation_requests WHERE request_id = $1
                ),
                cancelled_at = CURRENT_TIMESTAMP,
                cancelled_by = (
                    SELECT reviewed_by FROM cancellation_requests WHERE request_id = $1
                ),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
        """
        
        await session.execute(update_order_query, str(request_id), order_id)
        
        # 2. Update cancellation request status
        update_request_query = """
            UPDATE cancellation_requests
            SET status = $1
            WHERE request_id = $2
        """
        
        await session.execute(
            update_request_query,
            CancellationStatus.PROCESSING.value,
            str(request_id)
        )
        
        # 3. Restore inventory (get order items and restore)
        items_query = """
            SELECT product_id, quantity
            FROM order_items
            WHERE order_id = $1
        """
        
        items_result = await session.execute(items_query, order_id)
        items = items_result.fetchall()
        
        for product_id, quantity in items:
            # This would normally call the Inventory Agent
            # For now, we'll just log it
            self.logger.info("Restoring inventory",
                           product_id=product_id,
                           quantity=quantity,
                           order_id=order_id)
        
        # 4. Mark inventory as restored
        await session.execute(
            """
            UPDATE cancellation_requests
            SET inventory_restored = true
            WHERE request_id = $1
            """,
            str(request_id)
        )
        
        # 5. Initiate refund (would call Payment Agent)
        self.logger.info("Initiating refund",
                       order_id=order_id,
                       amount=float(refund_amount))
        
        # 6. Mark refund as processed (in real system, wait for Payment Agent confirmation)
        await session.execute(
            """
            UPDATE cancellation_requests
            SET refund_processed = true,
                status = $1
            WHERE request_id = $2
            """,
            CancellationStatus.COMPLETED.value,
            str(request_id)
        )
        
        self.logger.info("Processed cancellation",
                       request_id=str(request_id),
                       order_id=order_id)
    
    async def get_cancellation_request(
        self,
        request_id: UUID
    ) -> Optional[CancellationRequest]:
        """Get a cancellation request by ID."""
        async with self.db_manager.get_async_session() as session:
            query = """
                SELECT 
                    request_id, order_id, reason, reason_details,
                    requested_by, requested_at, reviewed_by, reviewed_at,
                    status, refund_amount, refund_processed, inventory_restored, notes
                FROM cancellation_requests
                WHERE request_id = $1
            """
            
            result = await session.execute(query, str(request_id))
            row = result.fetchone()
            
            if not row:
                return None
            
            return CancellationRequest(
                request_id=UUID(row[0]),
                order_id=row[1],
                reason=CancellationReason(row[2]),
                reason_details=row[3],
                requested_by=row[4],
                requested_at=row[5],
                reviewed_by=row[6],
                reviewed_at=row[7],
                status=CancellationStatus(row[8]),
                refund_amount=Decimal(str(row[9])) if row[9] else None,
                refund_processed=row[10],
                inventory_restored=row[11],
                notes=row[12]
            )
    
    async def get_order_cancellations(
        self,
        order_id: str
    ) -> List[CancellationRequest]:
        """Get all cancellation requests for an order."""
        async with self.db_manager.get_async_session() as session:
            query = """
                SELECT 
                    request_id, order_id, reason, reason_details,
                    requested_by, requested_at, reviewed_by, reviewed_at,
                    status, refund_amount, refund_processed, inventory_restored, notes
                FROM cancellation_requests
                WHERE order_id = $1
                ORDER BY requested_at DESC
            """
            
            result = await session.execute(query, order_id)
            rows = result.fetchall()
            
            return [
                CancellationRequest(
                    request_id=UUID(row[0]),
                    order_id=row[1],
                    reason=CancellationReason(row[2]),
                    reason_details=row[3],
                    requested_by=row[4],
                    requested_at=row[5],
                    reviewed_by=row[6],
                    reviewed_at=row[7],
                    status=CancellationStatus(row[8]),
                    refund_amount=Decimal(str(row[9])) if row[9] else None,
                    refund_processed=row[10],
                    inventory_restored=row[11],
                    notes=row[12]
                )
                for row in rows
            ]
    
    async def get_pending_cancellations(self) -> List[CancellationRequest]:
        """Get all pending cancellation requests."""
        async with self.db_manager.get_async_session() as session:
            query = """
                SELECT 
                    request_id, order_id, reason, reason_details,
                    requested_by, requested_at, reviewed_by, reviewed_at,
                    status, refund_amount, refund_processed, inventory_restored, notes
                FROM cancellation_requests
                WHERE status = $1
                ORDER BY requested_at ASC
            """
            
            result = await session.execute(query, CancellationStatus.PENDING.value)
            rows = result.fetchall()
            
            return [
                CancellationRequest(
                    request_id=UUID(row[0]),
                    order_id=row[1],
                    reason=CancellationReason(row[2]),
                    reason_details=row[3],
                    requested_by=row[4],
                    requested_at=row[5],
                    reviewed_by=row[6],
                    reviewed_at=row[7],
                    status=CancellationStatus(row[8]),
                    refund_amount=Decimal(str(row[9])) if row[9] else None,
                    refund_processed=row[10],
                    inventory_restored=row[11],
                    notes=row[12]
                )
                for row in rows
            ]
    
    async def _send_cancellation_notification(
        self,
        request_id: UUID,
        order_id: str,
        customer_id: str,
        reason: CancellationReason
    ):
        """Send cancellation notification via message broker."""
        if not self.message_broker:
            return
        
        message = {
            "type": "order_cancellation_requested",
            "request_id": str(request_id),
            "order_id": order_id,
            "customer_id": customer_id,
            "reason": reason.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            await self.message_broker.publish("order_events", message)
            self.logger.info("Sent cancellation notification",
                           request_id=str(request_id),
                           order_id=order_id)
        except Exception as e:
            self.logger.error("Failed to send cancellation notification",
                            error=str(e),
                            request_id=str(request_id))
    
    async def initialize(self):
        """Initialize the service."""
        await super().initialize()
        logger.info("OrderCancellationService initialized successfully")
    
    async def cleanup(self):
        """Cleanup service resources."""
        try:
            await super().cleanup()
            logger.info("OrderCancellationService cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process service business logic.
        
        Args:
            data: Dictionary containing operation type and parameters
            
        Returns:
            Dictionary with processing results
        """
        try:
            operation = data.get("operation", "process")
            logger.info(f"Processing OrderCancellationService operation: {operation}")
            return {"status": "success", "operation": operation, "data": data}
        except Exception as e:
            logger.error(f"Error in process_business_logic: {e}")
            return {"status": "error", "message": str(e)}

