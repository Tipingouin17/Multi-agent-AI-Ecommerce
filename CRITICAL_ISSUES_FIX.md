# Critical Issues Fix Guide

## Issues Identified

### 1. Kafka Version Compatibility Issue
**Error**: `aiokafka.errors.UnrecognizedBrokerVersion: UnrecognizedBrokerVersion`

**Root Cause**: The aiokafka library cannot recognize the Kafka broker version running in Docker. This happens when:
- Kafka broker version is too new for the aiokafka version
- API version negotiation fails
- Network/connection issues prevent proper version detection

**Solution**:
- Explicitly set `api_version` parameter in AIOKafkaProducer and AIOKafkaConsumer
- Use a stable Kafka API version (e.g., "2.8.0" or "auto")
- Add retry logic with exponential backoff

### 2. OpenAI API Deprecated Syntax
**Error**: `You tried to access openai.ChatCompletion, but this is no longer supported in openai>=1.0.0`

**Root Cause**: The code uses old OpenAI API syntax:
```python
response = openai.ChatCompletion.create(...)  # OLD
```

**Solution**: Update to new syntax:
```python
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.chat.completions.create(...)  # NEW
```

**Affected Agents**:
- AI Monitoring Agent
- Carrier Selection Agent
- Warehouse Selection Agent
- Demand Forecasting Agent
- Dynamic Pricing Agent
- Customer Communication Agent

### 3. Dashboard Import Errors
**Error**: `Failed to resolve import "@/lib/api" from "src/pages/..."`

**Root Cause**: 
- The `@/lib/api` file doesn't exist or is in wrong location
- Path alias `@` is not properly configured in vite.config.js

**Solution**:
- Create the missing `src/lib/api.js` file
- Ensure vite.config.js has proper path alias configuration
- Add API service with proper endpoints

## Fix Priority

1. **High Priority**: Kafka version compatibility (blocks all agents)
2. **High Priority**: OpenAI API syntax (blocks AI agents)
3. **Medium Priority**: Dashboard imports (blocks UI)

## Implementation Plan

### Phase 1: Fix Kafka Compatibility
- Update `shared/base_agent.py` to add `api_version` parameter
- Test with all 14 agents

### Phase 2: Fix OpenAI API Syntax
- Create helper function for OpenAI client initialization
- Update all 6 AI-powered agents
- Test AI functionality

### Phase 3: Fix Dashboard Imports
- Create `src/lib/api.js` with proper API service
- Verify vite.config.js path aliases
- Test dashboard startup

### Phase 4: Integration Testing
- Start all Docker services
- Start all 14 agents
- Start dashboard
- Verify end-to-end functionality

## Testing Checklist

- [ ] All Docker services running
- [ ] Kafka accessible on localhost:9092
- [ ] PostgreSQL accessible on localhost:5432
- [ ] All 14 agents start without errors
- [ ] Dashboard starts on http://localhost:5173
- [ ] No import errors in console
- [ ] API endpoints responding
- [ ] Real-time updates working

