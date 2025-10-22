# Multi-Agent AI E-commerce Platform - Deployment Guide

**Version:** 1.0  
**Date:** October 22, 2025  
**Latest Commit:** e344fad

---

## Quick Start

### Prerequisites
- Docker Desktop installed and running
- Git installed
- 8GB+ RAM available
- 20GB+ disk space

### One-Command Deployment

```bash
# Clone and deploy
git clone https://github.com/Tipingouin17/Multi-agent-AI-Ecommerce.git
cd Multi-agent-AI-Ecommerce/infrastructure
docker-compose up -d
```

That's it! The platform will start with all services.

---

## Detailed Deployment Steps

### Step 1: Clone Repository

```bash
git clone https://github.com/Tipingouin17/Multi-agent-AI-Ecommerce.git
cd Multi-agent-AI-Ecommerce
```

### Step 2: Configure Environment

The repository includes a `.env` file with default configurations. For production, review and update:

```bash
# Database credentials
DB_PASSWORD=your_secure_password

# API Keys (if using real services)
STRIPE_API_KEY=your_stripe_key
AMAZON_API_KEY=your_amazon_key
# ... etc
```

### Step 3: Build Docker Images

```bash
cd infrastructure
docker-compose build
```

This will build all agent images and download required base images.

### Step 4: Start Services

```bash
docker-compose up -d
```

Services will start in this order:
1. PostgreSQL database
2. Kafka broker
3. Redis cache
4. All 15 agent services
5. API gateway

### Step 5: Verify Deployment

```bash
# Check all services are running
docker-compose ps

# View logs
docker-compose logs -f

# Check specific agent
docker-compose logs -f document-generation-agent
```

### Step 6: Access Services

- **API Gateway:** http://localhost:8000
- **Health Check:** http://localhost:8000/health
- **PostgreSQL:** localhost:5432
- **Kafka:** localhost:9092
- **Redis:** localhost:6379

---

## Service Architecture

### Core Infrastructure
- **PostgreSQL** - Primary database for all agents
- **Kafka** - Message broker for inter-agent communication
- **Redis** - Caching and session management

### Agent Services (15 Total)

#### Critical Business Agents
1. **OrderAgent** (Port 8001) - Order processing
2. **InventoryAgent** (Port 8002) - Stock management
3. **ProductAgent** (Port 8003) - Product catalog
4. **PaymentAgent** (Port 8004) - Payment processing

#### Logistics & Fulfillment
5. **WarehouseAgent** (Port 8005) - Warehouse operations
6. **TransportAgent** (Port 8006) - Shipping coordination
7. **MarketplaceConnector** (Port 8007) - Multi-marketplace sync

#### Customer Service
8. **CustomerAgent** (Port 8008) - Customer management
9. **AfterSalesAgent** (Port 8009) - Returns & support
10. **DocumentGenerationAgent** (Port 8013) - Invoice/label generation

#### Quality & Compliance
11. **QualityControlAgent** (Port 8010) - Product quality
12. **BackofficeAgent** (Port 8011) - Admin operations
13. **KnowledgeManagementAgent** (Port 8020) - Knowledge base

#### Security & Monitoring
14. **FraudDetectionAgent** (Port 8012) - Fraud prevention
15. **RiskAnomalyDetectionAgent** (Port 8021) - Risk monitoring

---

## Testing Deployment

### 1. Health Check All Agents

```bash
# Test all agent health endpoints
for port in 8001 8002 8003 8004 8005 8006 8007 8008 8009 8010 8011 8012 8013 8020 8021; do
    echo "Testing port $port..."
    curl -s http://localhost:$port/health | jq
done
```

### 2. Database Verification

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d ecommerce

# Check tables
\dt

# Verify data
SELECT COUNT(*) FROM carriers;
SELECT COUNT(*) FROM marketplaces;
```

### 3. Kafka Verification

```bash
# List Kafka topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Monitor messages
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic order_events \
  --from-beginning
```

### 4. End-to-End Workflow Test

```bash
# Create a test order
curl -X POST http://localhost:8001/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "test-customer-001",
    "items": [
      {
        "product_id": "prod-001",
        "quantity": 2,
        "price": 29.99
      }
    ],
    "shipping_address": {
      "street": "123 Test St",
      "city": "Paris",
      "postal_code": "75001",
      "country": "FR"
    }
  }'
```

---

## Monitoring & Logs

### View All Logs
```bash
docker-compose logs -f
```

### View Specific Agent
```bash
docker-compose logs -f order-agent
docker-compose logs -f payment-agent
```

### Log Locations
Logs are stored in:
- Container: `/app/logs/`
- Host: `./logs/` (if volume mounted)

### Metrics
Each agent exposes metrics at `/metrics` endpoint:
```bash
curl http://localhost:8001/metrics
```

---

## Troubleshooting

### Agent Not Starting

1. Check logs:
```bash
docker-compose logs agent-name
```

2. Verify dependencies:
```bash
# Check if PostgreSQL is ready
docker-compose exec postgres pg_isready

# Check if Kafka is ready
docker-compose exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092
```

3. Restart specific agent:
```bash
docker-compose restart agent-name
```

### Database Connection Issues

```bash
# Check PostgreSQL status
docker-compose ps postgres

# Verify connection
docker-compose exec postgres psql -U postgres -c "SELECT version();"

# Check environment variables
docker-compose exec order-agent env | grep DB_
```

### Kafka Connection Issues

```bash
# Check Kafka status
docker-compose ps kafka

# Verify broker
docker-compose exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092

# Check topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Memory Issues

If agents are crashing due to memory:

1. Increase Docker memory limit (Docker Desktop > Settings > Resources)
2. Reduce number of concurrent agents
3. Adjust agent memory limits in docker-compose.yml

---

## Scaling

### Horizontal Scaling

Scale specific agents:
```bash
docker-compose up -d --scale order-agent=3
docker-compose up -d --scale inventory-agent=2
```

### Load Balancing

For production, add nginx or traefik:
```yaml
# Add to docker-compose.yml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
```

---

## Maintenance

### Update Agents

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Database Backup

```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres ecommerce > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres ecommerce < backup.sql
```

### Clean Up

```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

---

## Production Considerations

### Security

1. **Change default passwords** in `.env`
2. **Enable SSL/TLS** for all services
3. **Use secrets management** (Docker Secrets, Vault)
4. **Enable firewall** rules
5. **Regular security updates**

### Performance

1. **Database tuning** - Adjust PostgreSQL settings
2. **Kafka optimization** - Configure retention and partitions
3. **Redis configuration** - Set memory limits and eviction policies
4. **Agent resources** - Allocate appropriate CPU/memory

### Monitoring

1. **Prometheus** - Metrics collection
2. **Grafana** - Dashboards
3. **Loki** - Log aggregation
4. **Jaeger** - Distributed tracing
5. **Alertmanager** - Alert notifications

### Backup Strategy

1. **Database** - Daily automated backups
2. **Configuration** - Version control
3. **Logs** - Centralized storage
4. **Disaster recovery** - Tested restore procedures

---

## Support & Documentation

### Additional Resources
- **README.md** - Project overview
- **PRODUCTION_READINESS_STATUS.md** - Current status
- **API Documentation** - Available at `/docs` endpoint
- **GitHub Issues** - Bug reports and features

### Getting Help
1. Check logs: `docker-compose logs -f`
2. Review documentation
3. GitHub Issues: https://github.com/Tipingouin17/Multi-agent-AI-Ecommerce/issues

---

## Version History

### v1.0 (October 22, 2025)
- ✅ All 15 agents implemented
- ✅ Complete Docker deployment
- ✅ Security features (JWT, RBAC, rate limiting)
- ✅ 12 API integrations (carriers + marketplaces)
- ✅ Database-driven configuration
- ✅ Production-ready code

---

**Last Updated:** October 22, 2025  
**Maintainer:** Multi-Agent AI E-commerce Team  
**License:** Proprietary

