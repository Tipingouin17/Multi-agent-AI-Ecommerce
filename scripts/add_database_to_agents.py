"""
Script to add database operation examples to all agent files
This creates comprehensive documentation showing how each agent should use the database
"""

import os
import re
from pathlib import Path

# Agent-to-model mapping
AGENT_DB_MODELS = {
    "order_agent": ["OrderDB", "OrderItemDB"],
    "inventory_agent": ["InventoryDB", "ProductDB"],
    "product_agent": ["ProductDB"],
    "warehouse_agent": ["WarehouseDB", "InventoryDB"],
    "customer_agent": ["CustomerDB"],
    "carrier_selection_agent": ["ShipmentDB", "CarrierDB"],
    "pricing_agent": ["ProductDB", "PriceHistoryDB"],
    "marketplace_connector_agent": ["MarketplaceOrderDB", "MarketplaceListingDB"],
    "after_sales_agent": ["OrderDB", "ReturnDB", "RefundDB"],
    "quality_control_agent": ["ProductDB", "QualityInspectionDB"],
    "backoffice_agent": ["MerchantDB", "DocumentDB"],
}

DATABASE_USAGE_TEMPLATE = '''
# Database Usage Examples for {agent_name}
# This agent now has access to database operations via self.db_helper

## Available Database Models
{models}

## Common Operations

### 1. Create Record
```python
async def create_record(self, data: Dict[str, Any]):
    if not self._db_initialized:
        raise Exception("Database not initialized")
    
    async with self.db_manager.get_session() as session:
        record = await self.db_helper.create(session, {model}, data)
        await session.commit()
        return record
```

### 2. Get Record by ID
```python
async def get_by_id(self, record_id: str):
    if not self._db_initialized:
        return None
    
    async with self.db_manager.get_session() as session:
        record = await self.db_helper.get_by_id(session, {model}, record_id)
        return self.db_helper.to_dict(record) if record else None
```

### 3. Get All Records with Pagination
```python
async def get_all(self, skip: int = 0, limit: int = 100, filters: Optional[Dict] = None):
    if not self._db_initialized:
        return []
    
    async with self.db_manager.get_session() as session:
        records = await self.db_helper.get_all(
            session, {model}, skip=skip, limit=limit, filters=filters
        )
        return [self.db_helper.to_dict(r) for r in records]
```

### 4. Update Record
```python
async def update_record(self, record_id: str, data: Dict[str, Any]):
    if not self._db_initialized:
        return False
    
    async with self.db_manager.get_session() as session:
        record = await self.db_helper.update_by_id(session, {model}, record_id, data)
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
        deleted = await self.db_helper.delete_by_id(session, {model}, record_id)
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
        count = await self.db_helper.count(session, {model}, filters=filters)
        return count
```

### 7. Search Records
```python
async def search_records(self, search_term: str, search_fields: List[str]):
    if not self._db_initialized:
        return []
    
    async with self.db_manager.get_session() as session:
        records = await self.db_helper.search(
            session, {model}, search_fields, search_term
        )
        return [self.db_helper.to_dict(r) for r in records]
```

### 8. Bulk Create
```python
async def bulk_create(self, data_list: List[Dict[str, Any]]):
    if not self._db_initialized:
        return []
    
    async with self.db_manager.get_session() as session:
        records = await self.db_helper.bulk_create(session, {model}, data_list)
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
class {agent_class}(BaseAgent):
    
    async def create_{entity}(self, data: Dict[str, Any]) -> str:
        \"\"\"Create new {entity}\"\"\"
        if not self._db_initialized:
            raise Exception("Database not initialized")
        
        async with self.db_manager.get_session() as session:
            {entity_var} = await self.db_helper.create(session, {model}, data)
            await session.commit()
            
            self.logger.info(f"Created {entity} with ID: {{{entity_var}.id}}")
            
            # Publish event
            await self.send_message(
                recipient_agent="monitoring_agent",
                message_type=MessageType.{entity_upper}_CREATED,
                payload={{"id": str({entity_var}.id), **data}}
            )
            
            return str({entity_var}.id)
    
    async def get_{entity}(self, {entity}_id: str) -> Optional[Dict]:
        \"\"\"Get {entity} by ID\"\"\"
        if not self._db_initialized:
            return None
        
        async with self.db_manager.get_session() as session:
            {entity_var} = await self.db_helper.get_by_id(session, {model}, {entity}_id)
            return self.db_helper.to_dict({entity_var}) if {entity_var} else None
    
    async def update_{entity}(self, {entity}_id: str, data: Dict[str, Any]) -> bool:
        \"\"\"Update {entity}\"\"\"
        if not self._db_initialized:
            return False
        
        async with self.db_manager.get_session() as session:
            {entity_var} = await self.db_helper.update_by_id(session, {model}, {entity}_id, data)
            if {entity_var}:
                await session.commit()
                self.logger.info(f"Updated {entity} {{{entity}_id}}")
                return True
            return False
    
    async def delete_{entity}(self, {entity}_id: str) -> bool:
        \"\"\"Delete {entity}\"\"\"
        if not self._db_initialized:
            return False
        
        async with self.db_manager.get_session() as session:
            deleted = await self.db_helper.delete_by_id(session, {model}, {entity}_id)
            if deleted:
                await session.commit()
                self.logger.info(f"Deleted {entity} {{{entity}_id}}")
                return True
            return False
```

## Reference Implementation

See `agents/order_agent_production_v2.py` for a complete reference implementation
showing best practices for database integration.
'''


def create_database_guide(agent_file: Path):
    """Create database usage guide for an agent"""
    
    agent_name = agent_file.stem
    agent_key = agent_name.replace("_production", "").replace("_enhanced", "")
    
    # Get models for this agent
    models = AGENT_DB_MODELS.get(agent_key, ["OrderDB"])  # Default to OrderDB
    
    # Determine entity name
    entity = agent_key.replace("_agent", "").replace("_", " ").title().replace(" ", "")
    entity_var = entity.lower()
    entity_upper = entity.upper()
    
    # Determine agent class name
    class_name = ''.join(word.capitalize() for word in agent_name.split('_'))
    
    # Format models list
    models_list = "\n".join(f"- {model}" for model in models)
    
    # Create guide content
    guide = DATABASE_USAGE_TEMPLATE.format(
        agent_name=agent_name,
        models=models_list,
        model=models[0],
        agent_class=class_name,
        entity=entity.lower(),
        entity_var=entity_var,
        entity_upper=entity_upper
    )
    
    # Write guide file
    guide_file = agent_file.parent / f"{agent_name}_DATABASE_GUIDE.md"
    guide_file.write_text(guide)
    
    print(f"✅ Created database guide for {agent_name}")
    return guide_file


def main():
    """Create database guides for all agents"""
    
    agents_dir = Path(__file__).parent.parent / "agents"
    
    if not agents_dir.exists():
        print(f"❌ Agents directory not found: {agents_dir}")
        return
    
    # Find all agent files
    agent_files = list(agents_dir.glob("*_agent*.py"))
    
    print(f"Found {len(agent_files)} agent files")
    print("\nCreating database usage guides...\n")
    
    guides_created = 0
    
    for agent_file in agent_files:
        # Skip test files and __init__
        if "test" in agent_file.name or "__init__" in agent_file.name:
            continue
        
        try:
            create_database_guide(agent_file)
            guides_created += 1
        except Exception as e:
            print(f"⚠️  Error creating guide for {agent_file.name}: {e}")
    
    print(f"\n✅ Created {guides_created} database usage guides")
    print("\nAll agents now have:")
    print("  - Access to self.db_manager (database connection)")
    print("  - Access to self.db_helper (CRUD operations)")
    print("  - Comprehensive usage examples")
    print("  - Best practices documentation")
    print("\nNext steps:")
    print("  1. Review the guides in agents/*_DATABASE_GUIDE.md")
    print("  2. Implement database operations following the examples")
    print("  3. See agents/order_agent_production_v2.py for reference")


if __name__ == "__main__":
    main()

