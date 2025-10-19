"""
Order Service Layer for Enhanced Order Agent

This service layer encapsulates all business logic for order management including
modifications, splits, partial shipments, fulfillment planning, and cancellations.
"""

import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4

import structlog

from shared.database import DatabaseManager
from shared.order_models import (
    OrderModification, OrderModificationCreate,
    OrderSplit, OrderSplitRequest,
    PartialShipment, PartialShipmentCreate, PartialShipmentUpdate,
    OrderTimelineEvent, OrderTimelineEventCreate,
    OrderNote, OrderNoteCreate, OrderNoteUpdate,
    OrderTag, OrderTagCreate,
    FulfillmentPlan, FulfillmentPlanCreate, FulfillmentPlanUpdate,
    DeliveryAttempt, DeliveryAttemptCreate,
    CancellationRequest, CancellationRequestCreate, CancellationRequestReview,
    GiftOrder, OrderStatus, ShipmentStatus, FulfillmentStatus, CancellationStatus
)
from shared.order_repository_extended import OrderRepositoryFacade


logger = structlog.get_logger(__name__)


class OrderModificationService:
    """Service for handling order modifications."""
    
    def __init__(self, repos: OrderRepositoryFacade):
        self.repos = repos
    
    async def modify_order_field(
        self,
        order_id: str,
        field_name: str,
        old_value: Any,
        new_value: Any,
        reason: str,
        modified_by: str,
        metadata: Optional[Dict] = None
    ) -> OrderModification:
        """
        Modify a single order field with audit trail.
        
        Args:
            order_id: ID of the order to modify
            field_name: Name of the field being modified
            old_value: Previous value
            new_value: New value
            reason: Reason for modification
            modified_by: User/system making the modification
            metadata: Additional context
        
        Returns:
            OrderModification record
        """
        modification = OrderModificationCreate(
            order_id=order_id,
            modification_type="field_update",
            field_name=field_name,
            old_value=str(old_value),
            new_value=str(new_value),
            reason=reason,
            modified_by=modified_by,
            metadata=metadata or {}
        )
        
        result = await self.repos.modifications.create(modification)
        
        # Log timeline event
        await self.repos.timeline.create(OrderTimelineEventCreate(
            order_id=order_id,
            event_type="order_modified",
            event_description=f"Order field '{field_name}' modified: {old_value} -> {new_value}",
            event_data={"field": field_name, "reason": reason},
            triggered_by=modified_by
        ))
        
        logger.info(
            "order_field_modified",
            order_id=order_id,
            field=field_name,
            modified_by=modified_by
        )
        
        return result
    
    async def get_modification_history(self, order_id: str) -> List[OrderModification]:
        """Get complete modification history for an order."""
        return await self.repos.modifications.get_by_order(order_id)


class OrderSplitService:
    """Service for splitting orders across multiple warehouses."""
    
    def __init__(self, repos: OrderRepositoryFacade):
        self.repos = repos
    
    async def split_order(
        self,
        split_request: OrderSplitRequest,
        split_by: Optional[str] = None
    ) -> List[OrderSplit]:
        """
        Split an order into multiple child orders for multi-warehouse fulfillment.
        
        Args:
            split_request: Details of how to split the order
            split_by: User/system performing the split
        
        Returns:
            List of OrderSplit records
        """
        splits = []
        
        for child_order_id in split_request.child_order_ids:
            split = await self.repos.splits.create(
                parent_order_id=split_request.parent_order_id,
                child_order_id=child_order_id,
                split_reason=split_request.split_reason,
                split_by=split_by,
                metadata=split_request.metadata
            )
            splits.append(split)
        
        # Log timeline event
        await self.repos.timeline.create(OrderTimelineEventCreate(
            order_id=split_request.parent_order_id,
            event_type="order_split",
            event_description=f"Order split into {len(split_request.child_order_ids)} child orders",
            event_data={
                "child_orders": split_request.child_order_ids,
                "reason": split_request.split_reason
            },
            triggered_by=split_by
        ))
        
        logger.info(
            "order_split_created",
            parent_order=split_request.parent_order_id,
            child_count=len(split_request.child_order_ids),
            reason=split_request.split_reason
        )
        
        return splits
    
    async def get_child_orders(self, parent_order_id: str) -> List[OrderSplit]:
        """Get all child orders for a parent order."""
        return await self.repos.splits.get_child_orders(parent_order_id)


class PartialShipmentService:
    """Service for managing partial shipments."""
    
    def __init__(self, repos: OrderRepositoryFacade):
        self.repos = repos
    
    async def create_partial_shipment(
        self,
        shipment: PartialShipmentCreate
    ) -> PartialShipment:
        """
        Create a new partial shipment for an order.
        
        Args:
            shipment: Partial shipment details
        
        Returns:
            Created PartialShipment
        """
        result = await self.repos.shipments.create(shipment)
        
        # Log timeline event
        await self.repos.timeline.create(OrderTimelineEventCreate(
            order_id=shipment.order_id,
            event_type="partial_shipment_created",
            event_description=f"Partial shipment #{shipment.shipment_number} created",
            event_data={
                "shipment_id": result.shipment_id,
                "carrier": shipment.carrier,
                "items_count": len(shipment.items)
            },
            triggered_by="system"
        ))
        
        logger.info(
            "partial_shipment_created",
            order_id=shipment.order_id,
            shipment_id=result.shipment_id,
            shipment_number=shipment.shipment_number
        )
        
        return result
    
    async def update_shipment_tracking(
        self,
        shipment_id: str,
        tracking_number: str,
        carrier: Optional[str] = None
    ) -> PartialShipment:
        """Update tracking information for a shipment."""
        updates = PartialShipmentUpdate(
            tracking_number=tracking_number,
            carrier=carrier,
            shipped_at=datetime.utcnow()
        )
        
        result = await self.repos.shipments.update(shipment_id, updates)
        
        # Log timeline event
        await self.repos.timeline.create(OrderTimelineEventCreate(
            order_id=result.order_id,
            event_type="shipment_tracking_updated",
            event_description=f"Tracking number added: {tracking_number}",
            event_data={
                "shipment_id": shipment_id,
                "tracking_number": tracking_number,
                "carrier": carrier
            },
            triggered_by="system"
        ))
        
        return result
    
    async def mark_shipment_delivered(
        self,
        shipment_id: str,
        delivery_date: Optional[datetime] = None
    ) -> PartialShipment:
        """Mark a shipment as delivered."""
        updates = PartialShipmentUpdate(
            status=ShipmentStatus.DELIVERED,
            actual_delivery=delivery_date or datetime.utcnow()
        )
        
        result = await self.repos.shipments.update(shipment_id, updates)
        
        # Log timeline event
        await self.repos.timeline.create(OrderTimelineEventCreate(
            order_id=result.order_id,
            event_type="shipment_delivered",
            event_description=f"Shipment #{result.shipment_number} delivered",
            event_data={
                "shipment_id": shipment_id,
                "delivery_date": str(delivery_date or datetime.utcnow())
            },
            triggered_by="system"
        ))
        
        logger.info(
            "shipment_delivered",
            shipment_id=shipment_id,
            order_id=result.order_id
        )
        
        return result
    
    async def get_order_shipments(self, order_id: str) -> List[PartialShipment]:
        """Get all shipments for an order."""
        return await self.repos.shipments.get_by_order(order_id)


class FulfillmentPlanningService:
    """Service for order fulfillment planning."""
    
    def __init__(self, repos: OrderRepositoryFacade):
        self.repos = repos
    
    async def create_fulfillment_plan(
        self,
        plan: FulfillmentPlanCreate
    ) -> FulfillmentPlan:
        """
        Create a fulfillment plan for an order.
        
        Args:
            plan: Fulfillment plan details
        
        Returns:
            Created FulfillmentPlan
        """
        result = await self.repos.fulfillment.create(plan)
        
        # Log timeline event
        await self.repos.timeline.create(OrderTimelineEventCreate(
            order_id=plan.order_id,
            event_type="fulfillment_plan_created",
            event_description=f"Fulfillment plan created for warehouse {plan.warehouse_id}",
            event_data={
                "plan_id": result.plan_id,
                "strategy": plan.fulfillment_strategy,
                "priority": plan.priority_level
            },
            triggered_by="system"
        ))
        
        logger.info(
            "fulfillment_plan_created",
            order_id=plan.order_id,
            plan_id=result.plan_id,
            warehouse_id=plan.warehouse_id
        )
        
        return result
    
    async def update_fulfillment_status(
        self,
        plan_id: str,
        status: FulfillmentStatus,
        actual_processing_time: Optional[int] = None
    ) -> FulfillmentPlan:
        """Update fulfillment plan status."""
        updates = FulfillmentPlanUpdate(
            status=status,
            actual_processing_time=actual_processing_time
        )
        
        result = await self.repos.fulfillment.update(plan_id, updates)
        
        # Log timeline event
        await self.repos.timeline.create(OrderTimelineEventCreate(
            order_id=result.order_id,
            event_type="fulfillment_status_updated",
            event_description=f"Fulfillment status changed to {status.value}",
            event_data={
                "plan_id": plan_id,
                "status": status.value
            },
            triggered_by="system"
        ))
        
        return result
    
    async def get_order_fulfillment_plan(self, order_id: str) -> Optional[FulfillmentPlan]:
        """Get fulfillment plan for an order."""
        return await self.repos.fulfillment.get_by_order(order_id)


class DeliveryTrackingService:
    """Service for tracking delivery attempts."""
    
    def __init__(self, repos: OrderRepositoryFacade):
        self.repos = repos
    
    async def record_delivery_attempt(
        self,
        attempt: DeliveryAttemptCreate
    ) -> DeliveryAttempt:
        """
        Record a delivery attempt.
        
        Args:
            attempt: Delivery attempt details
        
        Returns:
            Created DeliveryAttempt
        """
        result = await self.repos.delivery_attempts.create(attempt)
        
        # Log timeline event
        event_desc = (
            f"Delivery attempt #{attempt.attempt_number} - {attempt.delivery_status.value}"
        )
        if attempt.failure_reason:
            event_desc += f": {attempt.failure_reason}"
        
        await self.repos.timeline.create(OrderTimelineEventCreate(
            order_id=attempt.order_id,
            event_type="delivery_attempt",
            event_description=event_desc,
            event_data={
                "attempt_id": result.attempt_id,
                "attempt_number": attempt.attempt_number,
                "status": attempt.delivery_status.value,
                "failure_reason": attempt.failure_reason
            },
            triggered_by="system"
        ))
        
        logger.info(
            "delivery_attempt_recorded",
            order_id=attempt.order_id,
            attempt_number=attempt.attempt_number,
            status=attempt.delivery_status.value
        )
        
        return result
    
    async def get_delivery_history(self, order_id: str) -> List[DeliveryAttempt]:
        """Get all delivery attempts for an order."""
        return await self.repos.delivery_attempts.get_by_order(order_id)


class CancellationService:
    """Service for order cancellation management."""
    
    def __init__(self, repos: OrderRepositoryFacade):
        self.repos = repos
    
    async def request_cancellation(
        self,
        request: CancellationRequestCreate
    ) -> CancellationRequest:
        """
        Create a cancellation request.
        
        Args:
            request: Cancellation request details
        
        Returns:
            Created CancellationRequest
        """
        result = await self.repos.cancellations.create(request)
        
        # Log timeline event
        await self.repos.timeline.create(OrderTimelineEventCreate(
            order_id=request.order_id,
            event_type="cancellation_requested",
            event_description=f"Cancellation requested: {request.cancellation_reason}",
            event_data={
                "request_id": result.request_id,
                "reason": request.cancellation_reason,
                "refund_amount": str(request.refund_amount) if request.refund_amount else None
            },
            triggered_by=request.requested_by
        ))
        
        logger.info(
            "cancellation_requested",
            order_id=request.order_id,
            request_id=result.request_id,
            requested_by=request.requested_by
        )
        
        return result
    
    async def review_cancellation(
        self,
        request_id: str,
        review: CancellationRequestReview
    ) -> CancellationRequest:
        """
        Review a cancellation request.
        
        Args:
            request_id: ID of the cancellation request
            review: Review details
        
        Returns:
            Updated CancellationRequest
        """
        result = await self.repos.cancellations.review(request_id, review)
        
        # Log timeline event
        await self.repos.timeline.create(OrderTimelineEventCreate(
            order_id=result.order_id,
            event_type="cancellation_reviewed",
            event_description=f"Cancellation {review.status.value}",
            event_data={
                "request_id": request_id,
                "status": review.status.value,
                "reviewed_by": review.reviewed_by,
                "notes": review.review_notes
            },
            triggered_by=review.reviewed_by
        ))
        
        logger.info(
            "cancellation_reviewed",
            request_id=request_id,
            order_id=result.order_id,
            status=review.status.value
        )
        
        return result
    
    async def get_pending_cancellations(self) -> List[CancellationRequest]:
        """Get all pending cancellation requests."""
        return await self.repos.cancellations.get_pending_requests()
    
    async def get_order_cancellations(self, order_id: str) -> List[CancellationRequest]:
        """Get all cancellation requests for an order."""
        return await self.repos.cancellations.get_by_order(order_id)


class OrderNoteService:
    """Service for order notes management."""
    
    def __init__(self, repos: OrderRepositoryFacade):
        self.repos = repos
    
    async def add_note(self, note: OrderNoteCreate) -> OrderNote:
        """Add a note to an order."""
        result = await self.repos.notes.create(note)
        
        # Log timeline event if visible to customer
        if note.is_visible_to_customer:
            await self.repos.timeline.create(OrderTimelineEventCreate(
                order_id=note.order_id,
                event_type="customer_note_added",
                event_description="Note added for customer",
                event_data={"note_id": result.note_id},
                triggered_by=note.created_by
            ))
        
        logger.info(
            "order_note_added",
            order_id=note.order_id,
            note_id=result.note_id,
            visible_to_customer=note.is_visible_to_customer
        )
        
        return result
    
    async def update_note(self, note_id: str, updates: OrderNoteUpdate) -> OrderNote:
        """Update an order note."""
        return await self.repos.notes.update(note_id, updates)
    
    async def get_order_notes(
        self,
        order_id: str,
        visible_to_customer: Optional[bool] = None
    ) -> List[OrderNote]:
        """Get notes for an order."""
        return await self.repos.notes.get_by_order(order_id, visible_to_customer)
    
    async def delete_note(self, note_id: str) -> bool:
        """Delete a note."""
        return await self.repos.notes.delete(note_id)


class OrderTagService:
    """Service for order tagging."""
    
    def __init__(self, repos: OrderRepositoryFacade):
        self.repos = repos
    
    async def add_tag(self, tag: OrderTagCreate) -> OrderTag:
        """Add a tag to an order."""
        result = await self.repos.tags.add_tag(tag)
        
        logger.info(
            "order_tag_added",
            order_id=tag.order_id,
            tag=tag.tag,
            added_by=tag.added_by
        )
        
        return result
    
    async def remove_tag(self, order_id: str, tag: str) -> bool:
        """Remove a tag from an order."""
        result = await self.repos.tags.remove_tag(order_id, tag)
        
        if result:
            logger.info("order_tag_removed", order_id=order_id, tag=tag)
        
        return result
    
    async def get_order_tags(self, order_id: str) -> List[OrderTag]:
        """Get all tags for an order."""
        return await self.repos.tags.get_by_order(order_id)
    
    async def find_orders_by_tag(self, tag: str) -> List[str]:
        """Find all orders with a specific tag."""
        return await self.repos.tags.get_orders_by_tag(tag)


class OrderTimelineService:
    """Service for order timeline management."""
    
    def __init__(self, repos: OrderRepositoryFacade):
        self.repos = repos
    
    async def add_event(self, event: OrderTimelineEventCreate) -> OrderTimelineEvent:
        """Add an event to order timeline."""
        return await self.repos.timeline.create(event)
    
    async def get_timeline(self, order_id: str) -> List[OrderTimelineEvent]:
        """Get complete timeline for an order."""
        return await self.repos.timeline.get_by_order(order_id)


class EnhancedOrderService:
    """
    Unified service that provides access to all enhanced order features.
    This is the main entry point for the Order Agent.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.repos = OrderRepositoryFacade(db_manager)
        
        # Initialize all sub-services
        self.modifications = OrderModificationService(self.repos)
        self.splits = OrderSplitService(self.repos)
        self.shipments = PartialShipmentService(self.repos)
        self.fulfillment = FulfillmentPlanningService(self.repos)
        self.delivery = DeliveryTrackingService(self.repos)
        self.cancellations = CancellationService(self.repos)
        self.notes = OrderNoteService(self.repos)
        self.tags = OrderTagService(self.repos)
        self.timeline = OrderTimelineService(self.repos)

