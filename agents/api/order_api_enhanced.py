"""
Enhanced API Endpoints for Order Agent

This module provides comprehensive REST API endpoints for all enhanced order features
including modifications, splits, partial shipments, fulfillment, and cancellations.
"""

from datetime import datetime

import structlog

logger = structlog.get_logger(__name__)
from decimal import Decimal
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel

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
from agents.services.order_service import EnhancedOrderService


# Create router
router = APIRouter(prefix="/api/orders", tags=["orders"])


# Dependency to get service instance
def get_order_service() -> EnhancedOrderService:
    """Dependency to get EnhancedOrderService instance."""
    db_manager = DatabaseManager()  # This should be injected properly
    return EnhancedOrderService(db_manager)


# ============================================================================
# Order Modification Endpoints
# ============================================================================

@router.post("/{order_id}/modifications", response_model=OrderModification)
async def modify_order_field(
    order_id: str = Path(..., description="Order ID"),
    modification: OrderModificationCreate = Body(...),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Modify a field in an order with audit trail.
    
    This endpoint allows modifying any order field while maintaining
    a complete audit trail of all changes.
    """
    try:
        return await service.modifications.modify_order_field(
            order_id=order_id,
            field_name=modification.field_name,
            old_value=modification.old_value,
            new_value=modification.new_value,
            reason=modification.reason,
            modified_by=modification.modified_by,
            metadata=modification.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}/modifications", response_model=List[OrderModification])
async def get_order_modifications(
    order_id: str = Path(..., description="Order ID"),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Get complete modification history for an order.
    
    Returns all modifications made to the order in chronological order.
    """
    try:
        return await service.modifications.get_modification_history(order_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Order Split Endpoints
# ============================================================================

@router.post("/splits", response_model=List[OrderSplit])
async def split_order(
    split_request: OrderSplitRequest = Body(...),
    split_by: Optional[str] = Query(None, description="User performing the split"),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Split an order into multiple child orders.
    
    This is used for multi-warehouse fulfillment where different items
    are shipped from different locations.
    """
    try:
        return await service.splits.split_order(split_request, split_by)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}/child-orders", response_model=List[OrderSplit])
async def get_child_orders(
    order_id: str = Path(..., description="Parent order ID"),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Get all child orders for a parent order.
    
    Returns the list of orders that were created when splitting the parent order.
    """
    try:
        return await service.splits.get_child_orders(order_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Partial Shipment Endpoints
# ============================================================================

@router.post("/{order_id}/shipments", response_model=PartialShipment)
async def create_partial_shipment(
    order_id: str = Path(..., description="Order ID"),
    shipment: PartialShipmentCreate = Body(...),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Create a new partial shipment for an order.
    
    Used when an order is fulfilled in multiple shipments.
    """
    try:
        return await service.shipments.create_partial_shipment(shipment)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}/shipments", response_model=List[PartialShipment])
async def get_order_shipments(
    order_id: str = Path(..., description="Order ID"),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Get all shipments for an order.
    
    Returns both complete and partial shipments.
    """
    try:
        return await service.shipments.get_order_shipments(order_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/shipments/{shipment_id}/tracking", response_model=PartialShipment)
async def update_shipment_tracking(
    shipment_id: str = Path(..., description="Shipment ID"),
    tracking_number: str = Body(..., embed=True),
    carrier: Optional[str] = Body(None, embed=True),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Update tracking information for a shipment.
    
    Adds tracking number and carrier information to a shipment.
    """
    try:
        return await service.shipments.update_shipment_tracking(
            shipment_id, tracking_number, carrier
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/shipments/{shipment_id}/delivered", response_model=PartialShipment)
async def mark_shipment_delivered(
    shipment_id: str = Path(..., description="Shipment ID"),
    delivery_date: Optional[datetime] = Body(None, embed=True),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Mark a shipment as delivered.
    
    Records the delivery date and updates shipment status.
    """
    try:
        return await service.shipments.mark_shipment_delivered(
            shipment_id, delivery_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Fulfillment Planning Endpoints
# ============================================================================

@router.post("/{order_id}/fulfillment-plan", response_model=FulfillmentPlan)
async def create_fulfillment_plan(
    order_id: str = Path(..., description="Order ID"),
    plan: FulfillmentPlanCreate = Body(...),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Create a fulfillment plan for an order.
    
    Defines how the order will be fulfilled including warehouse allocation
    and processing strategy.
    """
    try:
        return await service.fulfillment.create_fulfillment_plan(plan)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}/fulfillment-plan", response_model=Optional[FulfillmentPlan])
async def get_fulfillment_plan(
    order_id: str = Path(..., description="Order ID"),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Get the fulfillment plan for an order.
    
    Returns the current fulfillment plan or None if not yet created.
    """
    try:
        return await service.fulfillment.get_order_fulfillment_plan(order_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/fulfillment-plans/{plan_id}/status", response_model=FulfillmentPlan)
async def update_fulfillment_status(
    plan_id: str = Path(..., description="Fulfillment plan ID"),
    status: FulfillmentStatus = Body(..., embed=True),
    actual_processing_time: Optional[int] = Body(None, embed=True),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Update the status of a fulfillment plan.
    
    Updates the fulfillment status and optionally records actual processing time.
    """
    try:
        return await service.fulfillment.update_fulfillment_status(
            plan_id, status, actual_processing_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Delivery Tracking Endpoints
# ============================================================================

@router.post("/{order_id}/delivery-attempts", response_model=DeliveryAttempt)
async def record_delivery_attempt(
    order_id: str = Path(..., description="Order ID"),
    attempt: DeliveryAttemptCreate = Body(...),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Record a delivery attempt.
    
    Logs each delivery attempt including success/failure and reasons.
    """
    try:
        return await service.delivery.record_delivery_attempt(attempt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}/delivery-attempts", response_model=List[DeliveryAttempt])
async def get_delivery_attempts(
    order_id: str = Path(..., description="Order ID"),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Get all delivery attempts for an order.
    
    Returns the complete delivery history including all attempts.
    """
    try:
        return await service.delivery.get_delivery_history(order_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Cancellation Endpoints
# ============================================================================

@router.post("/{order_id}/cancellation-requests", response_model=CancellationRequest)
async def request_cancellation(
    order_id: str = Path(..., description="Order ID"),
    request: CancellationRequestCreate = Body(...),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Request order cancellation.
    
    Creates a cancellation request that needs to be reviewed and approved.
    """
    try:
        return await service.cancellations.request_cancellation(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}/cancellation-requests", response_model=List[CancellationRequest])
async def get_order_cancellations(
    order_id: str = Path(..., description="Order ID"),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Get all cancellation requests for an order.
    
    Returns the history of cancellation requests.
    """
    try:
        return await service.cancellations.get_order_cancellations(order_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancellation-requests/{request_id}/review", response_model=CancellationRequest)
async def review_cancellation(
    request_id: str = Path(..., description="Cancellation request ID"),
    review: CancellationRequestReview = Body(...),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Review a cancellation request.
    
    Approve or reject a cancellation request with notes.
    """
    try:
        return await service.cancellations.review_cancellation(request_id, review)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cancellation-requests/pending", response_model=List[CancellationRequest])
async def get_pending_cancellations(
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Get all pending cancellation requests.
    
    Returns cancellation requests awaiting review.
    """
    try:
        return await service.cancellations.get_pending_cancellations()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Order Notes Endpoints
# ============================================================================

@router.post("/{order_id}/notes", response_model=OrderNote)
async def add_order_note(
    order_id: str = Path(..., description="Order ID"),
    note: OrderNoteCreate = Body(...),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Add a note to an order.
    
    Notes can be internal-only or visible to customers.
    """
    try:
        return await service.notes.add_note(note)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}/notes", response_model=List[OrderNote])
async def get_order_notes(
    order_id: str = Path(..., description="Order ID"),
    visible_to_customer: Optional[bool] = Query(None, description="Filter by visibility"),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Get notes for an order.
    
    Can filter by customer visibility.
    """
    try:
        return await service.notes.get_order_notes(order_id, visible_to_customer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/notes/{note_id}", response_model=OrderNote)
async def update_order_note(
    note_id: str = Path(..., description="Note ID"),
    updates: OrderNoteUpdate = Body(...),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Update an order note.
    
    Can update content and visibility.
    """
    try:
        return await service.notes.update_note(note_id, updates)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notes/{note_id}")
async def delete_order_note(
    note_id: str = Path(..., description="Note ID"),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Delete an order note.
    
    Soft deletes the note (marks as deleted).
    """
    try:
        success = await service.notes.delete_note(note_id)
        if success:
            return {"message": "Note deleted successfully"}
        raise HTTPException(status_code=404, detail="Note not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Order Tags Endpoints
# ============================================================================

@router.post("/{order_id}/tags", response_model=OrderTag)
async def add_order_tag(
    order_id: str = Path(..., description="Order ID"),
    tag: OrderTagCreate = Body(...),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Add a tag to an order.
    
    Tags are used for categorization and filtering.
    """
    try:
        return await service.tags.add_tag(tag)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}/tags", response_model=List[OrderTag])
async def get_order_tags(
    order_id: str = Path(..., description="Order ID"),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Get all tags for an order.
    """
    try:
        return await service.tags.get_order_tags(order_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{order_id}/tags/{tag}")
async def remove_order_tag(
    order_id: str = Path(..., description="Order ID"),
    tag: str = Path(..., description="Tag to remove"),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Remove a tag from an order.
    """
    try:
        success = await service.tags.remove_tag(order_id, tag)
        if success:
            return {"message": "Tag removed successfully"}
        raise HTTPException(status_code=404, detail="Tag not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags/{tag}/orders", response_model=List[str])
async def find_orders_by_tag(
    tag: str = Path(..., description="Tag to search for"),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Find all orders with a specific tag.
    
    Returns list of order IDs.
    """
    try:
        return await service.tags.find_orders_by_tag(tag)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Order Timeline Endpoints
# ============================================================================

@router.get("/{order_id}/timeline", response_model=List[OrderTimelineEvent])
async def get_order_timeline(
    order_id: str = Path(..., description="Order ID"),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Get complete timeline for an order.
    
    Returns all events in chronological order.
    """
    try:
        return await service.timeline.get_timeline(order_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{order_id}/timeline", response_model=OrderTimelineEvent)
async def add_timeline_event(
    order_id: str = Path(..., description="Order ID"),
    event: OrderTimelineEventCreate = Body(...),
    service: EnhancedOrderService = Depends(get_order_service)
):
    """
    Add a custom event to order timeline.
    
    Used for manual event logging.
    """
    try:
        return await service.timeline.add_event(event)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

