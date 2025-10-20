# FastAPI Deprecation Warning Guide

## Overview

FastAPI has deprecated the `@app.on_event()` decorator in favor of the `lifespan` context manager. While the old syntax still works, it generates deprecation warnings.

## Current Status

All 13 agents currently use the deprecated `@app.on_event("startup")` and `@app.on_event("shutdown")` decorators:

- carrier_selection_agent.py
- customer_communication_agent.py
- d2c_ecommerce_agent.py
- demand_forecasting_agent.py
- dynamic_pricing_agent.py
- inventory_agent.py
- order_agent.py
- product_agent.py
- refurbished_marketplace_agent.py
- reverse_logistics_agent.py
- risk_anomaly_detection_agent.py
- standard_marketplace_agent.py
- warehouse_selection_agent.py

## Why the Warning Appears

FastAPI recommends using the `lifespan` context manager for better control over startup and shutdown events. The old `@app.on_event()` decorator is still functional but will be removed in a future version.

## Migration Strategy

### Option 1: Suppress Warnings (Temporary Solution)

For immediate deployment, you can suppress the deprecation warnings:

```python
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="fastapi")
```

Add this at the top of each agent file after imports.

### Option 2: Migrate to Lifespan (Recommended)

Convert from the old syntax to the new lifespan context manager.

#### Old Syntax (Current)

```python
from fastapi import FastAPI

app = FastAPI(title="Order Agent", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup."""
    global order_agent
    order_agent = OrderAgent()
    await order_agent.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup the agent on shutdown."""
    global order_agent
    if order_agent:
        await order_agent.stop()
```

#### New Syntax (Recommended)

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    global order_agent
    order_agent = OrderAgent()
    await order_agent.start()
    
    yield  # Application runs here
    
    # Shutdown
    if order_agent:
        await order_agent.stop()

app = FastAPI(title="Order Agent", version="1.0.0", lifespan=lifespan)
```

## Step-by-Step Migration Guide

### 1. Add Import

Add the `asynccontextmanager` import:

```python
from contextlib import asynccontextmanager
```

### 2. Create Lifespan Function

Replace the `@app.on_event()` decorators with a single `lifespan` function:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup code (from @app.on_event("startup"))
    # ... your startup code here ...
    
    yield  # Application runs between startup and shutdown
    
    # Shutdown code (from @app.on_event("shutdown"))
    # ... your shutdown code here ...
```

### 3. Update FastAPI App Creation

Add the `lifespan` parameter to the FastAPI app:

```python
app = FastAPI(
    title="Order Agent",
    version="1.0.0",
    lifespan=lifespan  # Add this parameter
)
```

### 4. Remove Old Event Handlers

Delete the old `@app.on_event()` decorated functions.

## Example: Complete Migration

### Before (order_agent.py)

```python
from fastapi import FastAPI

app = FastAPI(title="Order Agent", version="1.0.0")
order_agent: Optional[OrderAgent] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the Order Agent on startup."""
    global order_agent
    order_agent = OrderAgent()
    await order_agent.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup the Order Agent on shutdown."""
    global order_agent
    if order_agent:
        await order_agent.stop()
```

### After (order_agent.py)

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

order_agent: Optional[OrderAgent] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    global order_agent
    order_agent = OrderAgent()
    await order_agent.start()
    
    yield
    
    # Shutdown
    if order_agent:
        await order_agent.stop()

app = FastAPI(title="Order Agent", version="1.0.0", lifespan=lifespan)
```

## Testing After Migration

After migrating an agent, test it:

```powershell
# Start the agent
python agents/order_agent.py

# Check for deprecation warnings in the output
# There should be no warnings about @app.on_event
```

## Benefits of Lifespan

1. **Better Error Handling**: Exceptions in lifespan are handled more gracefully
2. **Cleaner Code**: Single function instead of two decorators
3. **Future-Proof**: Recommended by FastAPI maintainers
4. **Context Management**: Natural Python context manager pattern

## Impact Assessment

**Current Impact**: Low
- Warnings appear in logs but don't affect functionality
- All agents work correctly with current implementation
- No performance impact

**Future Impact**: Medium
- FastAPI will eventually remove `@app.on_event()` support
- Migration will be required before upgrading to that version
- Estimated effort: 1-2 hours for all 13 agents

## Recommendation

**For Production Deployment Now**:
- Keep current implementation (warnings are acceptable)
- Add warning suppression if logs are cluttered
- Schedule migration for next maintenance window

**For Long-Term Maintenance**:
- Migrate to lifespan context manager
- Test each agent after migration
- Update documentation

## Automated Migration Script

A script has been created to automate the migration:

```bash
python3 /home/ubuntu/fix_fastapi_deprecation.py
```

**Note**: The automated script needs refinement to handle edge cases. Manual migration is recommended for production systems.

## References

- [FastAPI Lifespan Events Documentation](https://fastapi.tiangolo.com/advanced/events/)
- [FastAPI Release Notes](https://fastapi.tiangolo.com/release-notes/)
- [Python asynccontextmanager](https://docs.python.org/3/library/contextlib.html#contextlib.asynccontextmanager)

## Support

If you encounter issues during migration:

1. Check that `contextlib.asynccontextmanager` is imported
2. Verify the `yield` statement is present in the lifespan function
3. Ensure the lifespan parameter is passed to FastAPI()
4. Test startup and shutdown behavior thoroughly

## Status

- **Current Status**: All agents use deprecated syntax (functional with warnings)
- **Migration Status**: Not yet migrated (planned for future update)
- **Priority**: Low (warnings only, no functional impact)
- **Estimated Effort**: 1-2 hours for complete migration

