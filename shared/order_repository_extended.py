"""
Extended Order Repository Layer - Continuation

This module provides additional repository classes for fulfillment plans,
delivery attempts, and cancellation requests.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from shared.database import DatabaseManager
from shared.order_models import (
    FulfillmentPlan, FulfillmentPlanCreate, FulfillmentPlanUpdate,
    DeliveryAttempt, DeliveryAttemptCreate,
    CancellationRequest, CancellationRequestCreate, CancellationRequestReview,
    FulfillmentStatus, CancellationStatus, DeliveryAttemptStatus
)


logger = structlog.get_logger(__name__)


class FulfillmentPlanRepository:
    """Repository for order fulfillment plans."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create(self, plan: FulfillmentPlanCreate) -> FulfillmentPlan:
        """Create a new fulfillment plan."""
        async with self.db_manager.get_session() as session:
            plan_id = str(uuid4())
            
            query = """
                INSERT INTO order_fulfillment_plan 
                (plan_id, order_id, warehouse_id, fulfillment_strategy, 
                 estimated_processing_time, priority_level, special_instructions, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING *
            """
            
            result = await session.execute(
                query,
                plan_id,
                plan.order_id,
                plan.warehouse_id,
                plan.fulfillment_strategy,
                plan.estimated_processing_time,
                plan.priority_level,
                plan.special_instructions,
                plan.metadata
            )
            
            row = result.fetchone()
            
            # Insert plan items
            for item in plan.items:
                item_query = """
                    INSERT INTO fulfillment_plan_items 
                    (plan_id, order_item_id, warehouse_id, allocated_quantity)
                    VALUES ($1, $2, $3, $4)
                """
                await session.execute(
                    item_query,
                    plan_id,
                    item['order_item_id'],
                    item['warehouse_id'],
                    item['allocated_quantity']
                )
            
            await session.commit()
            
            # Get items
            items = await self._get_plan_items(session, plan_id)
            
            return FulfillmentPlan(
                plan_id=row['plan_id'],
                order_id=row['order_id'],
                warehouse_id=row['warehouse_id'],
                fulfillment_strategy=row['fulfillment_strategy'],
                status=FulfillmentStatus(row['status']),
                estimated_processing_time=row['estimated_processing_time'],
                actual_processing_time=row['actual_processing_time'],
                priority_level=row['priority_level'],
                special_instructions=row['special_instructions'],
                items=items,
                metadata=row['metadata'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
    async def update(self, plan_id: str, updates: FulfillmentPlanUpdate) -> FulfillmentPlan:
        """Update a fulfillment plan."""
        async with self.db_manager.get_session() as session:
            update_fields = []
            params = []
            param_count = 1
            
            if updates.status is not None:
                update_fields.append(f"status = ${param_count}")
                params.append(updates.status.value)
                param_count += 1
            
            if updates.actual_processing_time is not None:
                update_fields.append(f"actual_processing_time = ${param_count}")
                params.append(updates.actual_processing_time)
                param_count += 1
            
            if updates.priority_level is not None:
                update_fields.append(f"priority_level = ${param_count}")
                params.append(updates.priority_level)
                param_count += 1
            
            if updates.special_instructions is not None:
                update_fields.append(f"special_instructions = ${param_count}")
                params.append(updates.special_instructions)
                param_count += 1
            
            if updates.metadata is not None:
                update_fields.append(f"metadata = ${param_count}")
                params.append(updates.metadata)
                param_count += 1
            
            if not update_fields:
                return await self.get_by_id(plan_id)
            
            params.append(plan_id)
            
            query = f"""
                UPDATE order_fulfillment_plan 
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE plan_id = ${param_count}
                RETURNING *
            """
            
            result = await session.execute(query, *params)
            row = result.fetchone()
            await session.commit()
            
            items = await self._get_plan_items(session, plan_id)
            
            return FulfillmentPlan(
                plan_id=row['plan_id'],
                order_id=row['order_id'],
                warehouse_id=row['warehouse_id'],
                fulfillment_strategy=row['fulfillment_strategy'],
                status=FulfillmentStatus(row['status']),
                estimated_processing_time=row['estimated_processing_time'],
                actual_processing_time=row['actual_processing_time'],
                priority_level=row['priority_level'],
                special_instructions=row['special_instructions'],
                items=items,
                metadata=row['metadata'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
    async def get_by_id(self, plan_id: str) -> Optional[FulfillmentPlan]:
        """Get a fulfillment plan by ID."""
        async with self.db_manager.get_session() as session:
            query = "SELECT * FROM order_fulfillment_plan WHERE plan_id = $1"
            result = await session.execute(query, plan_id)
            row = result.fetchone()
            
            if not row:
                return None
            
            items = await self._get_plan_items(session, plan_id)
            
            return FulfillmentPlan(
                plan_id=row['plan_id'],
                order_id=row['order_id'],
                warehouse_id=row['warehouse_id'],
                fulfillment_strategy=row['fulfillment_strategy'],
                status=FulfillmentStatus(row['status']),
                estimated_processing_time=row['estimated_processing_time'],
                actual_processing_time=row['actual_processing_time'],
                priority_level=row['priority_level'],
                special_instructions=row['special_instructions'],
                items=items,
                metadata=row['metadata'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
    async def get_by_order(self, order_id: str) -> Optional[FulfillmentPlan]:
        """Get fulfillment plan for an order."""
        async with self.db_manager.get_session() as session:
            query = "SELECT * FROM order_fulfillment_plan WHERE order_id = $1"
            result = await session.execute(query, order_id)
            row = result.fetchone()
            
            if not row:
                return None
            
            items = await self._get_plan_items(session, row['plan_id'])
            
            return FulfillmentPlan(
                plan_id=row['plan_id'],
                order_id=row['order_id'],
                warehouse_id=row['warehouse_id'],
                fulfillment_strategy=row['fulfillment_strategy'],
                status=FulfillmentStatus(row['status']),
                estimated_processing_time=row['estimated_processing_time'],
                actual_processing_time=row['actual_processing_time'],
                priority_level=row['priority_level'],
                special_instructions=row['special_instructions'],
                items=items,
                metadata=row['metadata'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
    async def _get_plan_items(self, session: AsyncSession, plan_id: str) -> List[Dict]:
        """Get items for a fulfillment plan."""
        query = """
            SELECT * FROM fulfillment_plan_items 
            WHERE plan_id = $1
        """
        
        result = await session.execute(query, plan_id)
        rows = result.fetchall()
        
        return [
            {
                'plan_id': row['plan_id'],
                'order_item_id': row['order_item_id'],
                'warehouse_id': row['warehouse_id'],
                'allocated_quantity': row['allocated_quantity']
            }
            for row in rows
        ]


class DeliveryAttemptRepository:
    """Repository for delivery attempts."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create(self, attempt: DeliveryAttemptCreate) -> DeliveryAttempt:
        """Create a new delivery attempt record."""
        async with self.db_manager.get_session() as session:
            attempt_id = str(uuid4())
            
            query = """
                INSERT INTO order_delivery_attempts 
                (attempt_id, order_id, shipment_id, attempt_number, attempt_date, 
                 delivery_status, failure_reason, next_attempt_date, courier_notes, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING *
            """
            
            result = await session.execute(
                query,
                attempt_id,
                attempt.order_id,
                attempt.shipment_id,
                attempt.attempt_number,
                attempt.attempt_date,
                attempt.delivery_status.value,
                attempt.failure_reason,
                attempt.next_attempt_date,
                attempt.courier_notes,
                attempt.metadata
            )
            
            row = result.fetchone()
            await session.commit()
            
            return DeliveryAttempt(
                attempt_id=row['attempt_id'],
                order_id=row['order_id'],
                shipment_id=row['shipment_id'],
                attempt_number=row['attempt_number'],
                attempt_date=row['attempt_date'],
                delivery_status=DeliveryAttemptStatus(row['delivery_status']),
                failure_reason=row['failure_reason'],
                next_attempt_date=row['next_attempt_date'],
                courier_notes=row['courier_notes'],
                metadata=row['metadata'],
                created_at=row['created_at']
            )
    
    async def get_by_order(self, order_id: str) -> List[DeliveryAttempt]:
        """Get all delivery attempts for an order."""
        async with self.db_manager.get_session() as session:
            query = """
                SELECT * FROM order_delivery_attempts 
                WHERE order_id = $1 
                ORDER BY attempt_number ASC
            """
            
            result = await session.execute(query, order_id)
            rows = result.fetchall()
            
            return [
                DeliveryAttempt(
                    attempt_id=row['attempt_id'],
                    order_id=row['order_id'],
                    shipment_id=row['shipment_id'],
                    attempt_number=row['attempt_number'],
                    attempt_date=row['attempt_date'],
                    delivery_status=DeliveryAttemptStatus(row['delivery_status']),
                    failure_reason=row['failure_reason'],
                    next_attempt_date=row['next_attempt_date'],
                    courier_notes=row['courier_notes'],
                    metadata=row['metadata'],
                    created_at=row['created_at']
                )
                for row in rows
            ]
    
    async def get_by_shipment(self, shipment_id: str) -> List[DeliveryAttempt]:
        """Get all delivery attempts for a shipment."""
        async with self.db_manager.get_session() as session:
            query = """
                SELECT * FROM order_delivery_attempts 
                WHERE shipment_id = $1 
                ORDER BY attempt_number ASC
            """
            
            result = await session.execute(query, shipment_id)
            rows = result.fetchall()
            
            return [
                DeliveryAttempt(
                    attempt_id=row['attempt_id'],
                    order_id=row['order_id'],
                    shipment_id=row['shipment_id'],
                    attempt_number=row['attempt_number'],
                    attempt_date=row['attempt_date'],
                    delivery_status=DeliveryAttemptStatus(row['delivery_status']),
                    failure_reason=row['failure_reason'],
                    next_attempt_date=row['next_attempt_date'],
                    courier_notes=row['courier_notes'],
                    metadata=row['metadata'],
                    created_at=row['created_at']
                )
                for row in rows
            ]


class CancellationRequestRepository:
    """Repository for order cancellation requests."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create(self, request: CancellationRequestCreate) -> CancellationRequest:
        """Create a new cancellation request."""
        async with self.db_manager.get_session() as session:
            request_id = str(uuid4())
            
            query = """
                INSERT INTO order_cancellation_requests 
                (request_id, order_id, requested_by, cancellation_reason, 
                 additional_details, refund_amount, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
            """
            
            result = await session.execute(
                query,
                request_id,
                request.order_id,
                request.requested_by,
                request.cancellation_reason,
                request.additional_details,
                request.refund_amount,
                request.metadata
            )
            
            row = result.fetchone()
            await session.commit()
            
            return CancellationRequest(
                request_id=row['request_id'],
                order_id=row['order_id'],
                requested_by=row['requested_by'],
                cancellation_reason=row['cancellation_reason'],
                additional_details=row['additional_details'],
                status=CancellationStatus(row['status']),
                refund_amount=row['refund_amount'],
                reviewed_by=row['reviewed_by'],
                review_notes=row['review_notes'],
                metadata=row['metadata'],
                requested_at=row['requested_at'],
                reviewed_at=row['reviewed_at']
            )
    
    async def review(self, request_id: str, review: CancellationRequestReview) -> CancellationRequest:
        """Review a cancellation request."""
        async with self.db_manager.get_session() as session:
            query = """
                UPDATE order_cancellation_requests 
                SET status = $1, reviewed_by = $2, review_notes = $3, 
                    reviewed_at = CURRENT_TIMESTAMP
                WHERE request_id = $4
                RETURNING *
            """
            
            result = await session.execute(
                query,
                review.status.value,
                review.reviewed_by,
                review.review_notes,
                request_id
            )
            
            row = result.fetchone()
            await session.commit()
            
            return CancellationRequest(
                request_id=row['request_id'],
                order_id=row['order_id'],
                requested_by=row['requested_by'],
                cancellation_reason=row['cancellation_reason'],
                additional_details=row['additional_details'],
                status=CancellationStatus(row['status']),
                refund_amount=row['refund_amount'],
                reviewed_by=row['reviewed_by'],
                review_notes=row['review_notes'],
                metadata=row['metadata'],
                requested_at=row['requested_at'],
                reviewed_at=row['reviewed_at']
            )
    
    async def get_by_id(self, request_id: str) -> Optional[CancellationRequest]:
        """Get a cancellation request by ID."""
        async with self.db_manager.get_session() as session:
            query = "SELECT * FROM order_cancellation_requests WHERE request_id = $1"
            result = await session.execute(query, request_id)
            row = result.fetchone()
            
            if not row:
                return None
            
            return CancellationRequest(
                request_id=row['request_id'],
                order_id=row['order_id'],
                requested_by=row['requested_by'],
                cancellation_reason=row['cancellation_reason'],
                additional_details=row['additional_details'],
                status=CancellationStatus(row['status']),
                refund_amount=row['refund_amount'],
                reviewed_by=row['reviewed_by'],
                review_notes=row['review_notes'],
                metadata=row['metadata'],
                requested_at=row['requested_at'],
                reviewed_at=row['reviewed_at']
            )
    
    async def get_by_order(self, order_id: str) -> List[CancellationRequest]:
        """Get all cancellation requests for an order."""
        async with self.db_manager.get_session() as session:
            query = """
                SELECT * FROM order_cancellation_requests 
                WHERE order_id = $1 
                ORDER BY requested_at DESC
            """
            
            result = await session.execute(query, order_id)
            rows = result.fetchall()
            
            return [
                CancellationRequest(
                    request_id=row['request_id'],
                    order_id=row['order_id'],
                    requested_by=row['requested_by'],
                    cancellation_reason=row['cancellation_reason'],
                    additional_details=row['additional_details'],
                    status=CancellationStatus(row['status']),
                    refund_amount=row['refund_amount'],
                    reviewed_by=row['reviewed_by'],
                    review_notes=row['review_notes'],
                    metadata=row['metadata'],
                    requested_at=row['requested_at'],
                    reviewed_at=row['reviewed_at']
                )
                for row in rows
            ]
    
    async def get_pending_requests(self) -> List[CancellationRequest]:
        """Get all pending cancellation requests."""
        async with self.db_manager.get_session() as session:
            query = """
                SELECT * FROM order_cancellation_requests 
                WHERE status = 'pending' 
                ORDER BY requested_at ASC
            """
            
            result = await session.execute(query)
            rows = result.fetchall()
            
            return [
                CancellationRequest(
                    request_id=row['request_id'],
                    order_id=row['order_id'],
                    requested_by=row['requested_by'],
                    cancellation_reason=row['cancellation_reason'],
                    additional_details=row['additional_details'],
                    status=CancellationStatus(row['status']),
                    refund_amount=row['refund_amount'],
                    reviewed_by=row['reviewed_by'],
                    review_notes=row['review_notes'],
                    metadata=row['metadata'],
                    requested_at=row['requested_at'],
                    reviewed_at=row['reviewed_at']
                )
                for row in rows
            ]


class OrderRepositoryFacade:
    """
    Facade that provides unified access to all order-related repositories.
    This simplifies dependency injection and provides a single entry point.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.modifications = OrderModificationRepository(db_manager)
        self.splits = OrderSplitRepository(db_manager)
        self.shipments = PartialShipmentRepository(db_manager)
        self.timeline = OrderTimelineRepository(db_manager)
        self.notes = OrderNoteRepository(db_manager)
        self.tags = OrderTagRepository(db_manager)
        self.fulfillment = FulfillmentPlanRepository(db_manager)
        self.delivery_attempts = DeliveryAttemptRepository(db_manager)
        self.cancellations = CancellationRequestRepository(db_manager)

