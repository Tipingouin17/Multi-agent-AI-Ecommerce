# Order Agent Integration Guide

## Overview

This guide explains how to integrate the enhanced Order Agent features into the existing `order_agent.py`.

## Components Created

### 1. Database Layer
- **File**: `database/migrations/002_order_agent_enhancements.sql`
- **Tables**: 11 new tables for enhanced features
- **Views**: 3 views for analytics

### 2. Models Layer
- **File**: `shared/order_models.py`
- **Models**: 40+ Pydantic models for all enhanced features

### 3. Repository Layer
- **Files**: 
  - `shared/order_repository.py` - Core repositories
  - `shared/order_repository_extended.py` - Extended repositories
- **Repositories**: 9 specialized repositories
- **Facade**: `OrderRepositoryFacade` for unified access

### 4. Service Layer
- **File**: `agents/services/order_service.py`
- **Services**: 9 specialized service classes
- **Facade**: `EnhancedOrderService` for unified access

### 5. API Layer
- **File**: `agents/api/order_api_enhanced.py`
- **Endpoints**: 30+ REST API endpoints
- **Router**: FastAPI router ready for integration

## Integration Steps

### Step 1: Run Database Migration

```bash
# Connect to PostgreSQL
docker exec -it multi-agent-postgres psql -U postgres -d multi_agent_ecommerce

# Run the migration
\i /path/to/database/migrations/002_order_agent_enhancements.sql
```

Or use Python:

```python
import asyncpg
import asyncio

async def run_migration():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres123',
        database='multi_agent_ecommerce'
    )
    
    with open('database/migrations/002_order_agent_enhancements.sql', 'r') as f:
        migration_sql = f.read()
    
    await conn.execute(migration_sql)
    await conn.close()

asyncio.run(run_migration())
```

### Step 2: Update Order Agent Imports

Add these imports to `agents/order_agent.py`:

```python
# Enhanced features
from agents.services.order_service import EnhancedOrderService
from agents.api.order_api_enhanced import router as enhanced_router
```

### Step 3: Initialize Enhanced Service

In the `OrderAgent` class `__init__` method, add:

```python
def __init__(self, ...):
    # ... existing initialization ...
    
    # Initialize enhanced service
    self.enhanced_service = EnhancedOrderService(self.db_manager)
```

### Step 4: Include Enhanced API Router

In the FastAPI app setup, add:

```python
# Include enhanced API endpoints
app.include_router(enhanced_router)
```

### Step 5: Add Kafka Event Handlers

Add these methods to handle new events:

```python
async def handle_order_modification_event(self, event: Dict):
    """Handle order modification events."""
    order_id = event.get('order_id')
    field_name = event.get('field_name')
    new_value = event.get('new_value')
    
    # Process modification
    await self.enhanced_service.modifications.modify_order_field(
        order_id=order_id,
        field_name=field_name,
        old_value=event.get('old_value'),
        new_value=new_value,
        reason=event.get('reason', 'System update'),
        modified_by=event.get('modified_by', 'system')
    )

async def handle_order_split_event(self, event: Dict):
    """Handle order split events."""
    from shared.order_models import OrderSplitRequest
    
    split_request = OrderSplitRequest(**event)
    await self.enhanced_service.splits.split_order(
        split_request,
        split_by=event.get('split_by', 'system')
    )

async def handle_partial_shipment_event(self, event: Dict):
    """Handle partial shipment creation events."""
    from shared.order_models import PartialShipmentCreate
    
    shipment = PartialShipmentCreate(**event)
    await self.enhanced_service.shipments.create_partial_shipment(shipment)

async def handle_cancellation_request_event(self, event: Dict):
    """Handle cancellation request events."""
    from shared.order_models import CancellationRequestCreate
    
    request = CancellationRequestCreate(**event)
    await self.enhanced_service.cancellations.request_cancellation(request)
```

### Step 6: Register Event Handlers

In the Kafka consumer setup, register the new handlers:

```python
self.event_handlers = {
    # ... existing handlers ...
    'order_modification': self.handle_order_modification_event,
    'order_split': self.handle_order_split_event,
    'partial_shipment': self.handle_partial_shipment_event,
    'cancellation_request': self.handle_cancellation_request_event,
}
```

## Testing

### Test Database Migration

```python
import asyncio
from shared.database import DatabaseManager
from shared.order_repository_extended import OrderRepositoryFacade

async def test_repositories():
    db_manager = DatabaseManager()
    repos = OrderRepositoryFacade(db_manager)
    
    # Test that all repositories are accessible
    assert repos.modifications is not None
    assert repos.splits is not None
    assert repos.shipments is not None
    # ... test others ...
    
    print("✓ All repositories initialized successfully")

asyncio.run(test_repositories())
```

### Test Service Layer

```python
from agents.services.order_service import EnhancedOrderService
from shared.order_models import OrderNoteCreate

async def test_services():
    db_manager = DatabaseManager()
    service = EnhancedOrderService(db_manager)
    
    # Test adding a note
    note = OrderNoteCreate(
        order_id="test-order-123",
        note_text="Test note",
        created_by="system",
        is_visible_to_customer=False
    )
    
    result = await service.notes.add_note(note)
    print(f"✓ Note created: {result.note_id}")

asyncio.run(test_services())
```

### Test API Endpoints

```bash
# Start the Order Agent
python agents/order_agent.py

# Test modification endpoint
curl -X POST http://localhost:8001/api/orders/test-order-123/modifications \
  -H "Content-Type: application/json" \
  -d '{
    "field_name": "status",
    "old_value": "pending",
    "new_value": "processing",
    "reason": "Payment confirmed",
    "modified_by": "system"
  }'

# Test timeline endpoint
curl http://localhost:8001/api/orders/test-order-123/timeline
```

## API Documentation

Once integrated, the enhanced API documentation will be available at:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## Features Available After Integration

### 1. Order Modifications
- Track all changes to orders
- Complete audit trail
- Automatic timeline logging

### 2. Order Splitting
- Multi-warehouse fulfillment
- Parent-child order relationships
- Automatic inventory allocation

### 3. Partial Shipments
- Multiple shipments per order
- Individual tracking per shipment
- Delivery status tracking

### 4. Fulfillment Planning
- Warehouse-specific plans
- Processing time tracking
- Priority management

### 5. Delivery Tracking
- Multiple delivery attempts
- Failure reason tracking
- Next attempt scheduling

### 6. Cancellations
- Request/review workflow
- Approval process
- Refund tracking

### 7. Order Notes
- Internal and customer notes
- Visibility control
- Full CRUD operations

### 8. Order Tags
- Flexible categorization
- Tag-based search
- Bulk operations

### 9. Order Timeline
- Complete event history
- Chronological view
- Custom event support

## Kafka Topics

The enhanced Order Agent publishes to and consumes from these topics:

### Published Events
- `order.modified` - When order is modified
- `order.split` - When order is split
- `shipment.created` - When partial shipment is created
- `shipment.tracking_updated` - When tracking is updated
- `shipment.delivered` - When shipment is delivered
- `cancellation.requested` - When cancellation is requested
- `cancellation.reviewed` - When cancellation is reviewed

### Consumed Events
- `order.modification_request` - Request to modify order
- `order.split_request` - Request to split order
- `shipment.create_request` - Request to create shipment
- `cancellation.request` - Cancellation request from customer

## Windows Compatibility Notes

All code is Windows-compatible:
- Uses `os.path.join()` for paths
- No Linux-specific commands
- Pure Python implementation
- Async/await throughout
- No shell scripts in critical path

## Performance Considerations

### Database Indexes
The migration includes indexes on:
- Foreign keys (order_id, shipment_id, etc.)
- Status fields
- Timestamp fields
- Tag fields

### Connection Pooling
- Uses async connection pooling
- Configurable pool size
- Automatic connection recycling

### Caching
Consider adding Redis caching for:
- Frequently accessed orders
- Order timelines
- Tag lookups

## Monitoring

Add these metrics to track enhanced features:

```python
# In Order Agent
self.metrics = {
    'modifications_total': 0,
    'splits_total': 0,
    'partial_shipments_total': 0,
    'cancellation_requests_total': 0,
    'notes_added_total': 0,
    'tags_added_total': 0,
}
```

## Next Steps

After integration:

1. **Test thoroughly** on Windows environment
2. **Monitor performance** with real data
3. **Add UI components** for dashboard
4. **Create user documentation**
5. **Set up alerts** for critical events
6. **Implement caching** if needed
7. **Add more comprehensive tests**

## Support

For issues or questions:
1. Check the code comments in each file
2. Review the Pydantic models for data structures
3. Test endpoints using Swagger UI
4. Check logs for detailed error messages

