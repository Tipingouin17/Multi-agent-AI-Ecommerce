"""
Comprehensive Test Suite for Enhanced Order Agent

Tests all enhanced features including:
- Order modifications
- Order splitting
- Partial shipments
- Fulfillment planning
- Delivery tracking
- Cancellations
- Notes and tags
- Timeline
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock

from shared.database import DatabaseManager
from shared.order_models import (
    OrderModificationCreate,
    OrderSplitRequest, OrderSplitItem,
    PartialShipmentCreate, PartialShipmentItem,
    FulfillmentPlanCreate, FulfillmentPlanItem,
    DeliveryAttemptCreate,
    CancellationRequestCreate, CancellationRequestReview,
    OrderNoteCreate, OrderNoteUpdate,
    OrderTagCreate,
    OrderTimelineEventCreate,
    OrderStatus, ShipmentStatus, FulfillmentStatus, CancellationStatus
)
from agents.services.order_service import EnhancedOrderService


# Fixtures

@pytest.fixture
async def db_manager():
    """Create database manager for tests."""
    manager = DatabaseManager()
    yield manager
    # Cleanup would go here

@pytest.fixture
async def order_service(db_manager):
    """Create order service instance."""
    return EnhancedOrderService(db_manager)

@pytest.fixture
def sample_order_id():
    """Sample order ID for tests."""
    return "test-order-123"

@pytest.fixture
def sample_modification_data():
    """Sample modification data."""
    return OrderModificationCreate(
        order_id="test-order-123",
        field_name="status",
        old_value="pending",
        new_value="processing",
        reason="Payment confirmed",
        modified_by="admin"
    )

@pytest.fixture
def sample_split_request():
    """Sample order split request."""
    return OrderSplitRequest(
        parent_order_id="test-order-123",
        split_reason="multi_warehouse",
        splits=[
            OrderSplitItem(
                child_order_id="test-order-123-1",
                items=[{"product_id": "prod-1", "quantity": 2}],
                warehouse_id="warehouse-1",
                estimated_ship_date=datetime.now() + timedelta(days=1)
            ),
            OrderSplitItem(
                child_order_id="test-order-123-2",
                items=[{"product_id": "prod-2", "quantity": 1}],
                warehouse_id="warehouse-2",
                estimated_ship_date=datetime.now() + timedelta(days=2)
            )
        ]
    )


# Order Modifications Tests

@pytest.mark.asyncio
async def test_modify_order_field(order_service, sample_order_id, sample_modification_data):
    """Test modifying an order field."""
    with patch.object(order_service.modifications.repository, 'create_modification', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {
            'modification_id': 'mod-1',
            **sample_modification_data.dict(),
            'modified_at': datetime.now()
        }
        
        result = await order_service.modifications.modify_order_field(
            order_id=sample_modification_data.order_id,
            field_name=sample_modification_data.field_name,
            old_value=sample_modification_data.old_value,
            new_value=sample_modification_data.new_value,
            reason=sample_modification_data.reason,
            modified_by=sample_modification_data.modified_by
        )
        
        assert result is not None
        assert result['field_name'] == 'status'
        assert result['new_value'] == 'processing'
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_get_modification_history(order_service, sample_order_id):
    """Test retrieving modification history."""
    with patch.object(order_service.modifications.repository, 'get_order_modifications', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [
            {
                'modification_id': 'mod-1',
                'field_name': 'status',
                'old_value': 'pending',
                'new_value': 'processing',
                'modified_at': datetime.now()
            }
        ]
        
        result = await order_service.modifications.get_modification_history(sample_order_id)
        
        assert len(result) == 1
        assert result[0]['field_name'] == 'status'
        mock_get.assert_called_once_with(sample_order_id)


# Order Split Tests

@pytest.mark.asyncio
async def test_split_order(order_service, sample_split_request):
    """Test splitting an order."""
    with patch.object(order_service.splits.repository, 'create_split', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {
            'split_id': 'split-1',
            'parent_order_id': sample_split_request.parent_order_id,
            'child_order_id': sample_split_request.splits[0].child_order_id,
            'created_at': datetime.now()
        }
        
        result = await order_service.splits.split_order(sample_split_request, 'admin')
        
        assert result is not None
        mock_create.assert_called()


@pytest.mark.asyncio
async def test_get_child_orders(order_service, sample_order_id):
    """Test retrieving child orders."""
    with patch.object(order_service.splits.repository, 'get_child_orders', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [
            {
                'split_id': 'split-1',
                'child_order_id': 'test-order-123-1',
                'warehouse_id': 'warehouse-1'
            }
        ]
        
        result = await order_service.splits.get_child_orders(sample_order_id)
        
        assert len(result) == 1
        assert result[0]['child_order_id'] == 'test-order-123-1'
        mock_get.assert_called_once_with(sample_order_id)


# Partial Shipment Tests

@pytest.mark.asyncio
async def test_create_partial_shipment(order_service):
    """Test creating a partial shipment."""
    shipment_data = PartialShipmentCreate(
        order_id="test-order-123",
        shipment_number=1,
        items=[
            PartialShipmentItem(
                product_id="prod-1",
                quantity=2
            )
        ],
        warehouse_id="warehouse-1",
        estimated_delivery_date=datetime.now() + timedelta(days=3)
    )
    
    with patch.object(order_service.shipments.repository, 'create_shipment', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {
            'shipment_id': 'ship-1',
            **shipment_data.dict(),
            'status': ShipmentStatus.PENDING,
            'created_at': datetime.now()
        }
        
        result = await order_service.shipments.create_partial_shipment(shipment_data)
        
        assert result is not None
        assert result['shipment_number'] == 1
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_update_shipment_tracking(order_service):
    """Test updating shipment tracking."""
    shipment_id = "ship-1"
    tracking_number = "TRACK123456"
    carrier = "UPS"
    
    with patch.object(order_service.shipments.repository, 'update_shipment', new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {
            'shipment_id': shipment_id,
            'tracking_number': tracking_number,
            'carrier': carrier,
            'status': ShipmentStatus.SHIPPED
        }
        
        result = await order_service.shipments.update_shipment_tracking(
            shipment_id, tracking_number, carrier
        )
        
        assert result['tracking_number'] == tracking_number
        assert result['carrier'] == carrier
        mock_update.assert_called_once()


# Fulfillment Planning Tests

@pytest.mark.asyncio
async def test_create_fulfillment_plan(order_service):
    """Test creating a fulfillment plan."""
    plan_data = FulfillmentPlanCreate(
        order_id="test-order-123",
        warehouse_id="warehouse-1",
        items=[
            FulfillmentPlanItem(
                product_id="prod-1",
                quantity=2,
                location="A1-B2"
            )
        ],
        estimated_processing_time_minutes=60,
        priority_level=1
    )
    
    with patch.object(order_service.fulfillment.repository, 'create_plan', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {
            'plan_id': 'plan-1',
            **plan_data.dict(),
            'status': FulfillmentStatus.PENDING,
            'created_at': datetime.now()
        }
        
        result = await order_service.fulfillment.create_fulfillment_plan(plan_data)
        
        assert result is not None
        assert result['warehouse_id'] == 'warehouse-1'
        mock_create.assert_called_once()


# Delivery Tracking Tests

@pytest.mark.asyncio
async def test_record_delivery_attempt(order_service):
    """Test recording a delivery attempt."""
    attempt_data = DeliveryAttemptCreate(
        order_id="test-order-123",
        attempt_number=1,
        attempt_date=datetime.now(),
        success=False,
        failure_reason="Customer not home",
        next_attempt_date=datetime.now() + timedelta(days=1)
    )
    
    with patch.object(order_service.delivery.repository, 'create_attempt', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {
            'attempt_id': 'attempt-1',
            **attempt_data.dict()
        }
        
        result = await order_service.delivery.record_delivery_attempt(attempt_data)
        
        assert result is not None
        assert result['success'] == False
        assert result['failure_reason'] == "Customer not home"
        mock_create.assert_called_once()


# Cancellation Tests

@pytest.mark.asyncio
async def test_request_cancellation(order_service):
    """Test requesting order cancellation."""
    request_data = CancellationRequestCreate(
        order_id="test-order-123",
        requested_by="customer",
        reason="Changed mind",
        refund_amount=Decimal("99.99")
    )
    
    with patch.object(order_service.cancellations.repository, 'create_request', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {
            'request_id': 'cancel-1',
            **request_data.dict(),
            'status': CancellationStatus.PENDING,
            'requested_at': datetime.now()
        }
        
        result = await order_service.cancellations.request_cancellation(request_data)
        
        assert result is not None
        assert result['reason'] == "Changed mind"
        assert result['status'] == CancellationStatus.PENDING
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_review_cancellation(order_service):
    """Test reviewing a cancellation request."""
    request_id = "cancel-1"
    review_data = CancellationRequestReview(
        approved=True,
        reviewed_by="admin",
        review_notes="Approved - within return window"
    )
    
    with patch.object(order_service.cancellations.repository, 'update_request', new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {
            'request_id': request_id,
            'status': CancellationStatus.APPROVED,
            'reviewed_by': review_data.reviewed_by,
            'reviewed_at': datetime.now()
        }
        
        result = await order_service.cancellations.review_cancellation(request_id, review_data)
        
        assert result['status'] == CancellationStatus.APPROVED
        mock_update.assert_called_once()


# Order Notes Tests

@pytest.mark.asyncio
async def test_add_order_note(order_service):
    """Test adding a note to an order."""
    note_data = OrderNoteCreate(
        order_id="test-order-123",
        note_text="Customer requested gift wrapping",
        created_by="admin",
        is_visible_to_customer=False
    )
    
    with patch.object(order_service.notes.repository, 'create_note', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {
            'note_id': 'note-1',
            **note_data.dict(),
            'created_at': datetime.now()
        }
        
        result = await order_service.notes.add_note(note_data)
        
        assert result is not None
        assert result['note_text'] == "Customer requested gift wrapping"
        assert result['is_visible_to_customer'] == False
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_update_order_note(order_service):
    """Test updating an order note."""
    note_id = "note-1"
    update_data = OrderNoteUpdate(
        note_text="Updated note text",
        is_visible_to_customer=True
    )
    
    with patch.object(order_service.notes.repository, 'update_note', new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {
            'note_id': note_id,
            **update_data.dict(),
            'updated_at': datetime.now()
        }
        
        result = await order_service.notes.update_note(note_id, update_data)
        
        assert result['note_text'] == "Updated note text"
        assert result['is_visible_to_customer'] == True
        mock_update.assert_called_once()


# Order Tags Tests

@pytest.mark.asyncio
async def test_add_order_tag(order_service):
    """Test adding a tag to an order."""
    tag_data = OrderTagCreate(
        order_id="test-order-123",
        tag="priority",
        added_by="admin"
    )
    
    with patch.object(order_service.tags.repository, 'add_tag', new_callable=AsyncMock) as mock_add:
        mock_add.return_value = {
            'tag_id': 'tag-1',
            **tag_data.dict(),
            'added_at': datetime.now()
        }
        
        result = await order_service.tags.add_tag(tag_data)
        
        assert result is not None
        assert result['tag'] == "priority"
        mock_add.assert_called_once()


@pytest.mark.asyncio
async def test_find_orders_by_tag(order_service):
    """Test finding orders by tag."""
    tag = "priority"
    
    with patch.object(order_service.tags.repository, 'find_by_tag', new_callable=AsyncMock) as mock_find:
        mock_find.return_value = ["order-1", "order-2", "order-3"]
        
        result = await order_service.tags.find_orders_by_tag(tag)
        
        assert len(result) == 3
        assert "order-1" in result
        mock_find.assert_called_once_with(tag)


# Order Timeline Tests

@pytest.mark.asyncio
async def test_get_order_timeline(order_service, sample_order_id):
    """Test retrieving order timeline."""
    with patch.object(order_service.timeline.repository, 'get_timeline', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [
            {
                'event_id': 'event-1',
                'event_type': 'order_created',
                'description': 'Order created',
                'event_timestamp': datetime.now()
            },
            {
                'event_id': 'event-2',
                'event_type': 'payment_confirmed',
                'description': 'Payment confirmed',
                'event_timestamp': datetime.now()
            }
        ]
        
        result = await order_service.timeline.get_timeline(sample_order_id)
        
        assert len(result) == 2
        assert result[0]['event_type'] == 'order_created'
        mock_get.assert_called_once_with(sample_order_id)


@pytest.mark.asyncio
async def test_add_timeline_event(order_service):
    """Test adding a custom timeline event."""
    event_data = OrderTimelineEventCreate(
        order_id="test-order-123",
        event_type="custom_event",
        description="Custom event occurred",
        metadata={"key": "value"}
    )
    
    with patch.object(order_service.timeline.repository, 'add_event', new_callable=AsyncMock) as mock_add:
        mock_add.return_value = {
            'event_id': 'event-1',
            **event_data.dict(),
            'event_timestamp': datetime.now()
        }
        
        result = await order_service.timeline.add_event(event_data)
        
        assert result is not None
        assert result['event_type'] == "custom_event"
        mock_add.assert_called_once()


# Integration Tests

@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_order_lifecycle(order_service):
    """Test complete order lifecycle with all enhanced features."""
    order_id = "test-order-integration"
    
    # 1. Create modification
    mod_result = await order_service.modifications.modify_order_field(
        order_id=order_id,
        field_name="status",
        old_value="pending",
        new_value="processing",
        reason="Payment confirmed",
        modified_by="system"
    )
    assert mod_result is not None
    
    # 2. Add note
    note_result = await order_service.notes.add_note(
        OrderNoteCreate(
            order_id=order_id,
            note_text="Order processing started",
            created_by="system",
            is_visible_to_customer=False
        )
    )
    assert note_result is not None
    
    # 3. Add tag
    tag_result = await order_service.tags.add_tag(
        OrderTagCreate(
            order_id=order_id,
            tag="processing",
            added_by="system"
        )
    )
    assert tag_result is not None
    
    # 4. Get timeline
    timeline = await order_service.timeline.get_timeline(order_id)
    assert len(timeline) > 0


# Performance Tests

@pytest.mark.asyncio
@pytest.mark.performance
async def test_bulk_modifications_performance(order_service):
    """Test performance of bulk modifications."""
    import time
    
    order_id = "test-order-perf"
    start_time = time.time()
    
    # Create 100 modifications
    tasks = []
    for i in range(100):
        task = order_service.modifications.modify_order_field(
            order_id=order_id,
            field_name=f"field_{i}",
            old_value=f"old_{i}",
            new_value=f"new_{i}",
            reason="Bulk test",
            modified_by="test"
        )
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Should complete in reasonable time (adjust threshold as needed)
    assert duration < 10.0, f"Bulk modifications took too long: {duration}s"


# Error Handling Tests

@pytest.mark.asyncio
async def test_modify_nonexistent_order(order_service):
    """Test modifying a non-existent order."""
    with pytest.raises(Exception):
        await order_service.modifications.modify_order_field(
            order_id="nonexistent-order",
            field_name="status",
            old_value="pending",
            new_value="processing",
            reason="Test",
            modified_by="test"
        )


@pytest.mark.asyncio
async def test_invalid_split_request(order_service):
    """Test invalid order split request."""
    invalid_request = OrderSplitRequest(
        parent_order_id="test-order",
        split_reason="invalid",
        splits=[]  # Empty splits should be invalid
    )
    
    with pytest.raises(Exception):
        await order_service.splits.split_order(invalid_request, "test")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])

