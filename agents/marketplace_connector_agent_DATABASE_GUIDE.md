
# Database Usage Examples for marketplace_connector_agent
# This agent now has access to database operations via self.db_helper

## Available Database Models
- MarketplaceOrderDB
- MarketplaceListingDB

## Common Operations

### 1. Create Record
```python
async def create_record(self, data: Dict[str, Any]):
    if not self._db_initialized:
        raise Exception("Database not initialized")
    
    async with self.db_manager.get_session() as session:
        record = await self.db_helper.create(session, MarketplaceOrderDB, data)
        await session.commit()
        return record
```

### 2. Get Record by ID
```python
async def get_by_id(self, record_id: str):
    if not self._db_initialized:
        return None
    
    async with self.db_manager.get_session() as session:
        record = await self.db_helper.get_by_id(session, MarketplaceOrderDB, record_id)
        return self.db_helper.to_dict(record) if record else None
```

### 3. Get All Records with Pagination
```python
async def get_all(self, skip: int = 0, limit: int = 100, filters: Optional[Dict] = None):
    if not self._db_initialized:
        return []
    
    async with self.db_manager.get_session() as session:
        records = await self.db_helper.get_all(
            session, MarketplaceOrderDB, skip=skip, limit=limit, filters=filters
        )
        return [self.db_helper.to_dict(r) for r in records]
```

### 4. Update Record
```python
async def update_record(self, record_id: str, data: Dict[str, Any]):
    if not self._db_initialized:
        return False
    
    async with self.db_manager.get_session() as session:
        record = await self.db_helper.update_by_id(session, MarketplaceOrderDB, record_id, data)
        if record:
            await session.commit()
            return True
        return False
```

### 5. Delete Record
```python
async def delete_record(self, record_id: str):
    if not self._db_initialized:
        return False
    
    async with self.db_manager.get_session() as session:
        deleted = await self.db_helper.delete_by_id(session, MarketplaceOrderDB, record_id)
        if deleted:
            await session.commit()
            return True
        return False
```

### 6. Count Records
```python
async def count_records(self, filters: Optional[Dict] = None):
    if not self._db_initialized:
        return 0
    
    async with self.db_manager.get_session() as session:
        count = await self.db_helper.count(session, MarketplaceOrderDB, filters=filters)
        return count
```

### 7. Search Records
```python
async def search_records(self, search_term: str, search_fields: List[str]):
    if not self._db_initialized:
        return []
    
    async with self.db_manager.get_session() as session:
        records = await self.db_helper.search(
            session, MarketplaceOrderDB, search_fields, search_term
        )
        return [self.db_helper.to_dict(r) for r in records]
```

### 8. Bulk Create
```python
async def bulk_create(self, data_list: List[Dict[str, Any]]):
    if not self._db_initialized:
        return []
    
    async with self.db_manager.get_session() as session:
        records = await self.db_helper.bulk_create(session, MarketplaceOrderDB, data_list)
        await session.commit()
        return records
```

## Important Notes

1. Always check `self._db_initialized` before database operations
2. Always use `async with self.db_manager.get_session()` for transactions
3. Always call `await session.commit()` after modifications
4. Use `self.db_helper.to_dict()` to convert models to dictionaries
5. All database operations are async and must be awaited
6. The database connection is automatically initialized when the agent starts
7. Database operations automatically handle UUIDs and timestamps

## Example: Complete CRUD Implementation

```python
class MarketplaceConnectorAgent(BaseAgent):
    
    async def create_marketplaceconnector(self, data: Dict[str, Any]) -> str:
        """Create new marketplaceconnector"""
        if not self._db_initialized:
            raise Exception("Database not initialized")
        
        async with self.db_manager.get_session() as session:
            marketplaceconnector = await self.db_helper.create(session, MarketplaceOrderDB, data)
            await session.commit()
            
            self.logger.info(f"Created marketplaceconnector with ID: {marketplaceconnector.id}")
            
            # Publish event
            await self.send_message(
                recipient_agent="monitoring_agent",
                message_type=MessageType.MARKETPLACECONNECTOR_CREATED,
                payload={"id": str(marketplaceconnector.id), **data}
            )
            
            return str(marketplaceconnector.id)
    
    async def get_marketplaceconnector(self, marketplaceconnector_id: str) -> Optional[Dict]:
        """Get marketplaceconnector by ID"""
        if not self._db_initialized:
            return None
        
        async with self.db_manager.get_session() as session:
            marketplaceconnector = await self.db_helper.get_by_id(session, MarketplaceOrderDB, marketplaceconnector_id)
            return self.db_helper.to_dict(marketplaceconnector) if marketplaceconnector else None
    
    async def update_marketplaceconnector(self, marketplaceconnector_id: str, data: Dict[str, Any]) -> bool:
        """Update marketplaceconnector"""
        if not self._db_initialized:
            return False
        
        async with self.db_manager.get_session() as session:
            marketplaceconnector = await self.db_helper.update_by_id(session, MarketplaceOrderDB, marketplaceconnector_id, data)
            if marketplaceconnector:
                await session.commit()
                self.logger.info(f"Updated marketplaceconnector {marketplaceconnector_id}")
                return True
            return False
    
    async def delete_marketplaceconnector(self, marketplaceconnector_id: str) -> bool:
        """Delete marketplaceconnector"""
        if not self._db_initialized:
            return False
        
        async with self.db_manager.get_session() as session:
            deleted = await self.db_helper.delete_by_id(session, MarketplaceOrderDB, marketplaceconnector_id)
            if deleted:
                await session.commit()
                self.logger.info(f"Deleted marketplaceconnector {marketplaceconnector_id}")
                return True
            return False
```

## Reference Implementation

See `agents/order_agent_production_v2.py` for a complete reference implementation
showing best practices for database integration.
