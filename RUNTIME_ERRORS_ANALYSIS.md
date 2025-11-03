# Runtime Errors Analysis

**Date:** November 3, 2025  
**Source:** Production validation test logs

---

## Summary

**8 agents are offline** due to runtime errors during startup:

1. ✅ warehouse - Database manager not initialized
2. ✅ fraud_detection - `asynccontextmanager` not defined
3. ✅ returns - Database manager not initialized  
4. ✅ customer_communication - Database manager not initialized
5. ✅ carrier_selection - Database manager not initialized
6. ⚠️  d2c_ecommerce - Kafka errors + datetime JSON serialization
7. ⚠️  ai_monitoring - OpenAI API key not set
8. ❌ infrastructure - No `app` attribute found

---

## Detailed Error Analysis

### 1. warehouse_agent ✅
**Error:** `RuntimeError: Database manager not initialized`

**Location:** `agents/warehouse_agent.py` line 396

**Root Cause:**
```python
db_manager = await get_database_manager()
# Raises RuntimeError because database manager was never initialized
```

**Fix Required:**
- Call `initialize_database_manager()` in the lifespan context before `get_database_manager()`

---

### 2. fraud_detection_agent ✅
**Error:** `NameError: name 'asynccontextmanager' is not defined`

**Root Cause:**
- Missing import: `from contextlib import asynccontextmanager`

**Fix Required:**
- Add the missing import statement

---

### 3. returns_agent ✅
**Error:** `RuntimeError: Database manager not initialized`

**Root Cause:**
- Same as warehouse_agent - calling `get_database_manager()` without initialization

**Fix Required:**
- Initialize database manager in lifespan context

---

### 4. customer_communication_agent ✅
**Error:** `RuntimeError: Database manager not initialized`

**Root Cause:**
- Same pattern - missing database manager initialization

**Fix Required:**
- Initialize database manager in lifespan context

---

### 5. carrier_selection_agent ✅
**Error:** `RuntimeError: Database manager not initialized`

**Root Cause:**
- Same pattern - missing database manager initialization

**Fix Required:**
- Initialize database manager in lifespan context

---

### 6. d2c_ecommerce_agent ⚠️
**Errors:**
1. Kafka GroupCoordinatorNotAvailableError (infrastructure issue - not code)
2. `TypeError: Object of type datetime is not JSON serializable`

**Root Cause:**
- Trying to send datetime objects in JSON messages without serialization

**Example:**
```python
{
    "order_id": "...",
    "created_at": datetime.now()  # ← Not JSON serializable
}
```

**Fix Required:**
- Convert datetime objects to ISO format strings before JSON serialization
- Add a JSON encoder that handles datetime objects

---

### 7. ai_monitoring_agent ⚠️
**Error:** `openai.OpenAIError: The api_key client option must be set`

**Root Cause:**
- OpenAI API key not configured in environment variables

**Fix Required:**
- Add environment variable check and graceful fallback
- Or make AI analyzer optional if API key is missing

---

### 8. infrastructure_agents ❌
**Error:** `Error loading ASGI app. Attribute "app" not found in module`

**Root Cause:**
- The infrastructure_agents.py file doesn't export an `app` variable at module level
- It has multiple agent classes but no unified FastAPI app

**Fix Required:**
- Create a module-level `app` variable
- Or update the startup script to use a different entry point

---

## Priority Fixes

### High Priority (Blocking Startup)
1. ✅ Database manager initialization (5 agents)
2. ✅ Missing asynccontextmanager import (1 agent)
3. ❌ Infrastructure app export (1 agent)

### Medium Priority (Runtime Errors)
4. ⚠️ Datetime JSON serialization (1 agent)
5. ⚠️ OpenAI API key handling (1 agent)

---

## Fix Strategy

### Phase 1: Database Manager Initialization
Fix all 5 agents with database manager errors by adding initialization in lifespan:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database manager
    await initialize_database_manager()
    db_manager = await get_database_manager()
    
    # Rest of initialization...
    yield
    
    # Cleanup...
```

### Phase 2: Import Fixes
Add missing imports:
```python
from contextlib import asynccontextmanager
```

### Phase 3: Infrastructure App
Create module-level app in infrastructure_agents.py:
```python
app = FastAPI(title="Infrastructure Agents")
```

### Phase 4: Datetime Serialization
Add custom JSON encoder or convert datetimes to ISO strings:
```python
from datetime import datetime

def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")
```

### Phase 5: API Key Handling
Add graceful fallback for missing API keys:
```python
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.warning("OpenAI API key not set, AI analysis disabled")
    self.ai_analyzer = None
else:
    self.ai_analyzer = AIErrorAnalyzer(api_key=api_key)
```

---

## Expected Outcome

After applying all fixes:
- **8 offline agents → 0 offline agents**
- **13/26 healthy → 26/26 healthy**
- **100% agent availability**

