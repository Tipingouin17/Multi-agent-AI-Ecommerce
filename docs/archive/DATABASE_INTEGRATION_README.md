# Database Integration - Complete Implementation Guide

## Overview

All agents in the Multi-Agent AI E-commerce platform now have **full database integration** through the enhanced `BaseAgent` class. This document explains how the database system works and how to use it.

## Architecture

### Components

1. **`shared/database.py`** - Database connection manager with async support
2. **`shared/db_helpers.py`** - Universal CRUD operations helper
3. **`shared/models.py`** - SQLAlchemy ORM models
4. **`shared/base_agent.py`** - Enhanced with automatic database initialization

### How It Works

```
BaseAgent (enhanced)
    ↓
Automatic Database Initialization
    ↓
self.db_manager (connection pool)
self.db_helper (CRUD operations)
    ↓
All 57 agents inherit database capabilities
```

## For Developers

### 1. Database Access in Agents

Every agent that inherits from `BaseAgent` automatically gets:

```python
class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="my_agent", agent_type="my_type")
        # Database is automatically initialized
        # self.db_manager - Database connection manager
        # self.db_helper - CRUD operations helper
        # self._db_initialized - Boolean flag
```

### 2. Basic CRUD Operations

#### Create Record

```python
async def create_order(self, order_data: Dict[str, Any]) -> str:
    if not self._db_initialized:
        raise Exception("Database not initialized")
    
    async with self.db_manager.get_session() as session:
        order = await self.db_helper.create(session, OrderDB, order_data)
        await session.commit()
        return str(order.id)
```

#### Read Record

```python
async def get_order(self, order_id: str) -> Optional[Dict]:
    if not self._db_initialized:
        return None
    
    async with self.db_manager.get_session() as session:
        order = await self.db_helper.get_by_id(session, OrderDB, order_id)
        return self.db_helper.to_dict(order) if order else None
```

#### Update Record

```python
async def update_order(self, order_id: str, data: Dict[str, Any]) -> bool:
    if not self._db_initialized:
        return False
    
    async with self.db_manager.get_session() as session:
        order = await self.db_helper.update_by_id(session, OrderDB, order_id, data)
        if order:
            await session.commit()
            return True
        return False
```

#### Delete Record

```python
async def delete_order(self, order_id: str) -> bool:
    if not self._db_initialized:
        return False
    
    async with self.db_manager.get_session() as session:
        deleted = await self.db_helper.delete_by_id(session, OrderDB, order_id)
        if deleted:
            await session.commit()
            return True
        return False
```

### 3. Advanced Operations

#### Pagination and Filtering

```python
async def get_orders(self, skip: int = 0, limit: int = 100, status: Optional[str] = None):
    if not self._db_initialized:
        return []
    
    filters = {"status": status} if status else None
    
    async with self.db_manager.get_session() as session:
        orders = await self.db_helper.get_all(
            session, OrderDB,
            skip=skip,
            limit=limit,
            filters=filters
        )
        return [self.db_helper.to_dict(order) for order in orders]
```

#### Search

```python
async def search_products(self, search_term: str):
    if not self._db_initialized:
        return []
    
    async with self.db_manager.get_session() as session:
        products = await self.db_helper.search(
            session, ProductDB,
            search_fields=["name", "description", "sku"],
            search_term=search_term
        )
        return [self.db_helper.to_dict(p) for p in products]
```

#### Bulk Create

```python
async def create_multiple_items(self, items_data: List[Dict]):
    if not self._db_initialized:
        return []
    
    async with self.db_manager.get_session() as session:
        items = await self.db_helper.bulk_create(session, OrderItemDB, items_data)
        await session.commit()
        return items
```

#### Count

```python
async def count_orders(self, status: Optional[str] = None):
    if not self._db_initialized:
        return 0
    
    filters = {"status": status} if status else None
    
    async with self.db_manager.get_session() as session:
        count = await self.db_helper.count(session, OrderDB, filters=filters)
        return count
```

### 4. Transaction Management

```python
async def process_order_with_inventory(self, order_data: Dict, items: List[Dict]):
    if not self._db_initialized:
        raise Exception("Database not initialized")
    
    async with self.db_manager.get_session() as session:
        try:
            # Create order
            order = await self.db_helper.create(session, OrderDB, order_data)
            
            # Update inventory for each item
            for item in items:
                inventory = await self.db_helper.get_by_id(
                    session, InventoryDB, item['product_id']
                )
                if inventory:
                    new_quantity = inventory.quantity - item['quantity']
                    await self.db_helper.update_by_id(
                        session, InventoryDB, item['product_id'],
                        {"quantity": new_quantity}
                    )
            
            # Commit transaction
            await session.commit()
            return str(order.id)
            
        except Exception as e:
            # Rollback on error
            await session.rollback()
            self.logger.error(f"Transaction failed: {e}")
            raise
```

## Database Models

### Available Models

Located in `shared/models.py`:

- **OrderDB** - Orders
- **OrderItemDB** - Order line items
- **ProductDB** - Products
- **CustomerDB** - Customers
- **InventoryDB** - Inventory levels
- **WarehouseDB** - Warehouses
- **ShipmentDB** - Shipments
- **CarrierDB** - Carriers
- **MarketplaceOrderDB** - Marketplace orders
- **MarketplaceListingDB** - Marketplace listings
- **ReturnDB** - Returns
- **RefundDB** - Refunds
- **QualityInspectionDB** - Quality inspections
- **MerchantDB** - Merchants
- **DocumentDB** - Documents

### Model Structure

Each model includes:
- **id** - UUID primary key (auto-generated)
- **created_at** - Timestamp (auto-generated)
- **updated_at** - Timestamp (auto-updated)
- Model-specific fields

## Configuration

### Environment Variables

Set in `.env` file:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ecommerce
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

### Connection Pool

The database manager uses connection pooling:
- **Pool Size**: 10 connections (configurable)
- **Max Overflow**: 20 additional connections (configurable)
- **Pool Recycle**: 300 seconds
- **Pool Pre-Ping**: Enabled (checks connection health)

## Best Practices

### 1. Always Check Initialization

```python
if not self._db_initialized:
    self.logger.warning("Database not initialized")
    return default_value
```

### 2. Use Context Managers

```python
async with self.db_manager.get_session() as session:
    # Your database operations
    await session.commit()
```

### 3. Handle Errors

```python
try:
    async with self.db_manager.get_session() as session:
        # Operations
        await session.commit()
except Exception as e:
    self.logger.error(f"Database error: {e}")
    raise
```

### 4. Commit After Modifications

```python
# Always commit after create, update, or delete
await session.commit()
```

### 5. Convert Models to Dicts

```python
# For API responses
order_dict = self.db_helper.to_dict(order)
orders_list = self.db_helper.to_dict_list(orders)
```

### 6. Use Filters for Queries

```python
# Instead of loading all and filtering in Python
filters = {
    "status": "pending",
    "customer_id": customer_id
}
orders = await self.db_helper.get_all(session, OrderDB, filters=filters)
```

## Agent-Specific Guides

Each agent has a detailed database guide:

- `agents/order_agent_DATABASE_GUIDE.md`
- `agents/inventory_agent_DATABASE_GUIDE.md`
- `agents/product_agent_DATABASE_GUIDE.md`
- ... (47 total guides)

These guides include:
- Agent-specific models
- Common operations
- Complete CRUD examples
- Best practices

## Reference Implementation

See `agents/order_agent_production_v2.py` for a complete reference implementation showing:
- Full CRUD operations
- Transaction management
- Error handling
- Kafka event publishing
- FastAPI integration
- Best practices

## Testing Database Operations

### 1. Test Connection

```python
async def test_connection(self):
    if self.db_manager:
        await self.db_manager.test_connection()
        self.logger.info("Database connection successful")
```

### 2. Test CRUD

```python
async def test_crud(self):
    # Create
    data = {"name": "Test Product", "price": 99.99}
    product = await self.create_product(data)
    
    # Read
    retrieved = await self.get_product(product.id)
    assert retrieved["name"] == "Test Product"
    
    # Update
    await self.update_product(product.id, {"price": 89.99})
    updated = await self.get_product(product.id)
    assert updated["price"] == 89.99
    
    # Delete
    await self.delete_product(product.id)
    deleted = await self.get_product(product.id)
    assert deleted is None
```

## Migration from Stub Methods

### Before (Stub)

```python
async def get_orders_from_db(self, skip: int, limit: int) -> List[Dict]:
    logger.info(f"Getting orders: skip={skip}, limit={limit}")
    return []  # ❌ Returns empty list
```

### After (Real Implementation)

```python
async def get_orders_from_db(self, skip: int, limit: int) -> List[Dict]:
    if not self._db_initialized:
        return []
    
    async with self.db_manager.get_session() as session:
        orders = await self.db_helper.get_all(
            session, OrderDB, skip=skip, limit=limit
        )
        return [self.db_helper.to_dict(order) for order in orders]
```

## Performance Considerations

### 1. Use Pagination

```python
# Don't load all records
orders = await self.db_helper.get_all(session, OrderDB, limit=100)
```

### 2. Use Filters

```python
# Filter in database, not in Python
filters = {"status": "pending"}
orders = await self.db_helper.get_all(session, OrderDB, filters=filters)
```

### 3. Bulk Operations

```python
# Use bulk_create for multiple records
items = await self.db_helper.bulk_create(session, OrderItemDB, items_data)
```

### 4. Connection Pooling

The database manager automatically handles connection pooling. No manual connection management needed.

## Troubleshooting

### Database Not Initialized

**Symptom**: `self._db_initialized` is False

**Solutions**:
1. Check environment variables in `.env`
2. Ensure PostgreSQL is running
3. Check database credentials
4. Review agent logs for initialization errors

### Connection Errors

**Symptom**: "Connection refused" or timeout errors

**Solutions**:
1. Verify PostgreSQL is running: `pg_isready`
2. Check host and port in `.env`
3. Verify firewall rules
4. Check PostgreSQL logs

### Transaction Errors

**Symptom**: "Transaction already committed" or rollback errors

**Solutions**:
1. Always use `async with` for sessions
2. Call `commit()` only once per transaction
3. Handle exceptions properly
4. Don't reuse sessions

## Summary

✅ **All 57 agents** have database access via `BaseAgent`  
✅ **Automatic initialization** on agent startup  
✅ **Comprehensive CRUD operations** via `db_helper`  
✅ **Transaction support** with rollback  
✅ **Connection pooling** for performance  
✅ **Type-safe** operations with SQLAlchemy  
✅ **47 agent-specific guides** with examples  
✅ **Reference implementation** in `order_agent_production_v2.py`

## Next Steps

1. Review your agent's specific guide: `agents/{your_agent}_DATABASE_GUIDE.md`
2. Study the reference implementation: `agents/order_agent_production_v2.py`
3. Replace stub methods with real database operations
4. Test your implementation
5. Deploy to production

---

**Questions?** See the agent-specific guides or reference implementation for detailed examples.

