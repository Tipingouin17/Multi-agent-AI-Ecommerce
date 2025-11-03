# Agent Port Assignment Plan

## Current Status

**Total Agents:** 26  
**Port Conflicts:** 7 conflicts affecting 15 agents  
**Missing Ports:** 2 agents (product, quality_control)

---

## Proposed Port Assignment (8000-8025)

| Port | Agent | Current Port | Status |
|------|-------|--------------|--------|
| 8000 | order_agent_production_v2 | 8000 | ✅ OK |
| 8001 | product_agent_production | NONE | ⚠️ NEEDS PORT |
| 8002 | inventory_agent | 8003 | 🔧 CHANGE |
| 8003 | marketplace_connector_agent | 8015 | 🔧 CHANGE |
| 8004 | payment_agent_enhanced | 8004 | ✅ OK |
| 8005 | dynamic_pricing_agent | 8005 | ✅ OK (conflict with carrier) |
| 8006 | carrier_selection_agent | 8005 | 🔧 CHANGE |
| 8007 | customer_agent_enhanced | 8008 | 🔧 CHANGE |
| 8008 | customer_communication_agent | 8008 | ✅ OK (conflict with customer) |
| 8009 | returns_agent | 8009 | ✅ OK |
| 8010 | fraud_detection_agent | 8011 | 🔧 CHANGE |
| 8011 | recommendation_agent | 8011 | ✅ OK (conflict with fraud) |
| 8012 | promotion_agent | 8012 | ✅ OK (conflict with risk) |
| 8013 | risk_anomaly_detection_agent | 8012 | 🔧 CHANGE |
| 8014 | knowledge_management_agent | 8014 | ✅ OK (conflict with transport) |
| 8015 | transport_management_agent_enhanced | 8014 | 🔧 CHANGE |
| 8016 | warehouse_agent | 8013 | 🔧 CHANGE |
| 8017 | document_generation_agent | 8013 | 🔧 CHANGE |
| 8018 | support_agent | 8018 | ✅ OK |
| 8019 | d2c_ecommerce_agent | 8013 | 🔧 CHANGE |
| 8020 | after_sales_agent_production | 8020 | ✅ OK |
| 8021 | backoffice_agent_production | 8021 | ✅ OK |
| 8022 | infrastructure_agents | 8022 | ✅ OK |
| 8023 | ai_monitoring_agent_self_healing | 8023 | ✅ OK |
| 8024 | monitoring_agent | 8015 | 🔧 CHANGE |
| 8025 | quality_control_agent_production | NONE | ⚠️ NEEDS PORT |

---

## Changes Required

### 1. Agents Needing Port Changes (10 agents)

1. **inventory_agent**: 8003 → 8002
2. **marketplace_connector_agent**: 8015 → 8003
3. **carrier_selection_agent**: 8005 → 8006
4. **customer_agent_enhanced**: 8008 → 8007
5. **fraud_detection_agent**: 8011 → 8010
6. **risk_anomaly_detection_agent**: 8012 → 8013
7. **transport_management_agent_enhanced**: 8014 → 8015
8. **warehouse_agent**: 8013 → 8016
9. **document_generation_agent**: 8013 → 8017
10. **d2c_ecommerce_agent**: 8013 → 8019
11. **monitoring_agent**: 8015 → 8024

### 2. Agents Needing Port Added (2 agents)

1. **product_agent_production**: Add port 8001
2. **quality_control_agent_production**: Add port 8025

---

## Implementation Strategy

### Option 1: Environment Variable Override (Recommended)
Set `API_PORT` environment variable when starting each agent. This doesn't require code changes.

```bash
API_PORT=8002 python3.11 agents/inventory_agent.py &
API_PORT=8003 python3.11 agents/marketplace_connector_agent.py &
# etc...
```

### Option 2: Code Changes
Modify each agent file to use the new port. More permanent but requires more changes.

---

## Startup Script

Create `start_all_26_agents.sh` that:
1. Exports DATABASE_URL
2. Starts each agent with correct API_PORT
3. Waits between starts to avoid resource conflicts
4. Reports status

---

## Testing Plan

1. ✅ Test all agents import successfully (DONE - 26/26 pass)
2. 🔄 Assign unique ports to all agents
3. 🔄 Create comprehensive startup script
4. 🔄 Start all 26 agents
5. 🔄 Verify health endpoints on all ports
6. 🔄 Test functional endpoints
7. 🔄 Document any remaining issues

---

## Notes

- Ports 8000-8025 are reserved for these 26 agents
- All agents should check `API_PORT` environment variable first
- Database port (5432) should never be used by agents
- Kafka port (9092) should never be used by agents


