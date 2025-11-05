# Agent Port Reference

**Complete Port Assignment for All 27 Agents**

---

## Port Assignment Table

| Port | Agent File | Agent Name | Category | Status |
|------|-----------|------------|----------|--------|
| 8000 | order_agent_v3.py | Order Agent | Core Business | ✅ Active |
| 8001 | product_agent_v3.py | Product Agent | Core Business | ✅ Active |
| 8002 | inventory_agent_v3.py | Inventory Agent | Core Business | ✅ Active |
| 8003 | marketplace_connector_v3.py | Marketplace Connector | Marketplace & Integration | ✅ Active |
| 8004 | payment_agent_v3.py | Payment Agent | Core Business | ✅ Active |
| 8005 | dynamic_pricing_v3.py | Dynamic Pricing | Marketplace & Integration | ✅ Active |
| 8006 | carrier_agent_v3.py | Carrier Agent | Core Business | ✅ Active |
| 8007 | customer_agent_v3.py | Customer Agent | Core Business | ✅ Active |
| 8008 | warehouse_agent_v3.py | Warehouse Agent | Operations & Support | ✅ Active |
| 8009 | returns_agent_v3.py | Returns Agent | Core Business | ✅ Active |
| 8010 | fraud_detection_agent_v3.py | Fraud Detection | Core Business | ✅ Active |
| 8011 | risk_anomaly_detection_v3.py | Risk Anomaly Detection | Infrastructure & Monitoring | ✅ Active |
| 8012 | knowledge_management_agent_v3.py | Knowledge Management | Infrastructure & Monitoring | ✅ Active |
| 8014 | recommendation_agent_v3.py | Recommendation Agent | Marketplace & Integration | ✅ Active |
| 8015 | transport_management_v3.py | Transport Management | Operations & Support | ✅ Active |
| 8016 | document_generation_agent_v3.py | Document Generation | Operations & Support | ✅ Active |
| 8018 | support_agent_v3.py | Support Agent | Operations & Support | ✅ Active |
| 8019 | customer_communication_v3.py | Customer Communication | Operations & Support | ✅ Active |
| 8020 | promotion_agent_v3.py | Promotion Agent | Marketplace & Integration | ✅ Active |
| 8021 | after_sales_agent_v3.py | After Sales Agent | Operations & Support | ✅ Active |
| 8022 | infrastructure_v3.py | Infrastructure | Infrastructure & Monitoring | ✅ Active |
| 8023 | monitoring_agent_v3.py | Monitoring Agent | Infrastructure & Monitoring | ✅ Active |
| 8024 | ai_monitoring_agent_v3.py | AI Monitoring | Infrastructure & Monitoring | ✅ Active |
| 8026 | d2c_ecommerce_agent_v3.py | D2C Ecommerce | Marketplace & Integration | ✅ Active |
| 8027 | backoffice_agent_v3.py | Backoffice Agent | Operations & Support | ✅ Active |
| 8028 | quality_control_agent_v3.py | Quality Control | Operations & Support | ✅ Active |
| 8100 | system_api_gateway_v3.py | System API Gateway | Infrastructure & Monitoring | ✅ Active |

**Total Agents:** 27  
**Port Range:** 8000-8100  
**Reserved Ports:** 8013, 8017, 8025, 8029-8099 (available for future agents)

---

## Category Breakdown

### Core Business Agents (8 agents)

Critical agents that handle core business operations:

- **8000** - Order Agent: Order management and processing
- **8001** - Product Agent: Product catalog and management
- **8002** - Inventory Agent: Stock and inventory management
- **8004** - Payment Agent: Payment processing and transactions
- **8006** - Carrier Agent: Shipping carrier selection and management
- **8007** - Customer Agent: Customer data and management
- **8009** - Returns Agent: Returns and refunds processing
- **8010** - Fraud Detection: Security and fraud monitoring

### Marketplace & Integration Agents (5 agents)

Agents handling multi-channel and marketplace integrations:

- **8003** - Marketplace Connector: Multi-channel marketplace sync
- **8005** - Dynamic Pricing: Pricing optimization and strategies
- **8014** - Recommendation Agent: Product recommendations and AI
- **8020** - Promotion Agent: Marketing campaigns and promotions
- **8026** - D2C Ecommerce: Direct-to-consumer operations

### Operations & Support Agents (8 agents)

Agents managing operations and customer support:

- **8008** - Warehouse Agent: Warehouse operations and management
- **8015** - Transport Management: Logistics and transportation
- **8016** - Document Generation: Invoices, receipts, and documents
- **8018** - Support Agent: Customer support and tickets
- **8019** - Customer Communication: Messaging and notifications
- **8021** - After Sales Agent: Post-purchase support
- **8027** - Backoffice Agent: Administrative operations
- **8028** - Quality Control: Quality assurance and testing

### Infrastructure & Monitoring Agents (6 agents)

Agents handling system infrastructure and monitoring:

- **8011** - Risk Anomaly Detection: Risk analysis and detection
- **8012** - Knowledge Management: Knowledge base and documentation
- **8022** - Infrastructure: Infrastructure management
- **8023** - Monitoring Agent: System health monitoring
- **8024** - AI Monitoring: AI-powered monitoring and alerts
- **8100** - System API Gateway: Central API gateway and routing

---

## Health Check Endpoints

All agents expose a standard health check endpoint:

```
GET http://localhost:{PORT}/health
```

**Example Response:**

```json
{
  "status": "healthy",
  "agent": "order_agent_v3",
  "version": "3.0.0",
  "timestamp": "2025-11-05T12:00:00Z"
}
```

### Quick Health Check Commands

**Linux/Mac:**
```bash
curl http://localhost:8000/health
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/health
```

**Windows (cmd with curl):**
```cmd
curl http://localhost:8000/health
```

---

## Starting Agents

### Individual Agent Start

**Linux/Mac:**
```bash
API_PORT=8000 python3.11 agents/order_agent_v3.py &
```

**Windows:**
```cmd
set API_PORT=8000
python agents\order_agent_v3.py
```

### All Agents Start

**Linux/Mac:**
```bash
./start_all_agents.sh
```

**Windows:**
```cmd
start_all_agents.bat
```

---

## Port Conflict Resolution

If you encounter port conflicts, you can change agent ports by:

### Method 1: Environment Variable (Recommended)

```bash
# Linux/Mac
API_PORT=9000 python3.11 agents/order_agent_v3.py

# Windows
set API_PORT=9000
python agents\order_agent_v3.py
```

### Method 2: Modify Agent Code

Edit the agent file and change the default port:

```python
# In agent file (e.g., order_agent_v3.py)
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 9000))  # Change default from 8000 to 9000
    uvicorn.run(app, host="0.0.0.0", port=port)
```

---

## Firewall Configuration

### Linux (ufw)

```bash
# Allow all agent ports
sudo ufw allow 8000:8100/tcp

# Or allow specific ports
sudo ufw allow 8000/tcp
sudo ufw allow 8001/tcp
# ... etc
```

### Windows Firewall

```powershell
# PowerShell (Run as Administrator)
New-NetFirewallRule -DisplayName "Multi-Agent Ecommerce" -Direction Inbound -Protocol TCP -LocalPort 8000-8100 -Action Allow
```

### macOS

```bash
# macOS doesn't block localhost by default
# For external access, configure in System Preferences > Security & Privacy > Firewall
```

---

## Monitoring Ports

### Check Which Ports Are Listening

**Linux:**
```bash
netstat -tlnp | grep -E ":(80[0-9]{2}|8100)"
```

**macOS:**
```bash
lsof -i -P | grep LISTEN | grep -E ":(80[0-9]{2}|8100)"
```

**Windows:**
```cmd
netstat -ano | findstr /R ":80[0-9][0-9] .*LISTENING"
```

### Check Specific Port

**Linux/macOS:**
```bash
lsof -i :8000
```

**Windows:**
```cmd
netstat -ano | findstr :8000
```

---

## API Endpoint Examples

### Order Agent (8000)

```
GET  http://localhost:8000/api/orders
POST http://localhost:8000/api/orders
GET  http://localhost:8000/api/orders/{order_id}
GET  http://localhost:8000/api/orders/stats
```

### Product Agent (8001)

```
GET  http://localhost:8001/api/products
POST http://localhost:8001/api/products
GET  http://localhost:8001/api/products/{product_id}
GET  http://localhost:8001/featured
```

### Payment Agent (8004)

```
GET  http://localhost:8004/api/payments
POST http://localhost:8004/api/payments
GET  http://localhost:8004/api/payments/methods
GET  http://localhost:8004/api/payments/stats
```

### System API Gateway (8100)

```
GET  http://localhost:8100/api/system/overview
GET  http://localhost:8100/api/agents
GET  http://localhost:8100/api/system/config
GET  http://localhost:8100/health
```

---

## Troubleshooting

### Port Already in Use

**Error:** `Address already in use` or `OSError: [Errno 98] Address already in use`

**Solution:**

**Linux/macOS:**
```bash
# Find process using the port
lsof -i :8000

# Kill the process
kill -9 <PID>
```

**Windows:**
```cmd
# Find process using the port
netstat -ano | findstr :8000

# Kill the process (replace <PID> with actual process ID)
taskkill /F /PID <PID>
```

### Agent Not Responding

**Check if agent is running:**

```bash
# Linux/macOS
ps aux | grep agent_v3.py

# Windows
tasklist | findstr python
```

**Check agent logs:**

```bash
# Linux/macOS
tail -f logs/agents/order_agent_v3.log

# Windows
type logs\agents\order_agent_v3.log
```

### Connection Refused

**Possible causes:**
1. Agent not started
2. Firewall blocking port
3. Wrong port number
4. Agent crashed (check logs)

**Solution:**
1. Verify agent is running: `curl http://localhost:8000/health`
2. Check firewall settings
3. Review agent logs for errors
4. Restart the agent

---

## Best Practices

1. **Use Standard Ports**
   - Keep the default port assignments for consistency
   - Only change if absolutely necessary

2. **Monitor Health**
   - Regularly check agent health endpoints
   - Set up automated monitoring

3. **Log Management**
   - Rotate logs regularly to prevent disk space issues
   - Monitor logs for errors and warnings

4. **Security**
   - Don't expose agent ports to the internet directly
   - Use API Gateway (8100) as the only public endpoint
   - Implement authentication and authorization

5. **Load Balancing**
   - For production, run multiple instances of critical agents
   - Use different ports for each instance
   - Configure load balancer to distribute traffic

---

## Future Expansion

**Available Ports for New Agents:**

- 8013 (reserved)
- 8017 (reserved)
- 8025 (reserved)
- 8029-8099 (available)

When adding new agents, follow the naming convention and update this document.

---

**Last Updated:** November 5, 2025  
**Platform Version:** 3.0.0  
**Total Agents:** 27
