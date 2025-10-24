# CORS Configuration Guide for Dashboard Integration

## Overview

To enable the dashboard to communicate with the backend agents, each agent needs CORS (Cross-Origin Resource Sharing) middleware configured.

## Quick Fix

Add these lines to each agent's FastAPI app initialization:

```python
from fastapi.middleware.cors import CORSMiddleware

# After creating the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Agent-by-Agent Instructions

### For agents with `self.app = FastAPI(...)`:

1. Find the line: `self.app = FastAPI(...)`
2. Add CORS middleware right after it:

```python
self.app = FastAPI(title="Agent Name API")

# Add CORS middleware
self.app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### For agents with module-level `app = FastAPI(...)`:

1. Find the line: `app = FastAPI(...)`
2. Add CORS middleware right after it (same code as above, but use `app` instead of `self.app`)

## Testing CORS

After adding CORS, test it with:

```bash
curl -H "Origin: http://localhost:5173" -I http://localhost:8001/health
```

You should see:
```
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Credentials: true
```

## Dashboard API Methods

The following API methods have been added to the dashboard (`multi-agent-dashboard/src/lib/api.js`):

### Warehouse Agent
- `getWarehouses()` - Get all warehouses
- `getWarehouse(id)` - Get specific warehouse

### Marketplace Agent
- `getMarketplaces()` - Get all marketplaces
- `getConnectedMarketplaces()` - Alias for getMarketplaces
- `getAvailableMarketplaces()` - Get available marketplaces for integration
- `getMarketplace(id)` - Get specific marketplace

All methods include mock data fallbacks for graceful degradation when agents are unavailable.

## Current Status

✅ **Dashboard API**: Complete with all required methods  
⚠️ **Agent CORS**: Needs to be added manually to each agent  
✅ **Mock Data**: All methods have realistic fallback data  

## Next Steps

1. Add CORS to each of the 16 agents manually
2. Test each agent's health endpoint with CORS headers
3. Verify dashboard can load without errors
4. Test full workflows end-to-end

## Notes

- **Do not use automated scripts** to add CORS - each agent has a unique structure
- Add CORS carefully to avoid breaking existing code
- Test each agent individually after adding CORS
- The dashboard will work with mock data even if agents don't have CORS yet

