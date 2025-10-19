# Deployment and Testing Guide

This guide will help you deploy and test the improved Multi-Agent E-commerce System in your environment.

## Prerequisites

### Required Software
- Python 3.11 or higher
- PostgreSQL 12 or higher
- Apache Kafka 3.x
- Redis 6.x or higher
- Docker and Docker Compose (for containerized deployment)
- Node.js 18+ (for dashboard)

### System Requirements
- Minimum 4GB RAM
- 10GB free disk space
- Ubuntu 20.04+ / macOS / Windows with WSL2

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Tipingouin17/Multi-agent-AI-Ecommerce.git
cd Multi-agent-AI-Ecommerce
```

### 2. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

**Important:** Update these critical values in `.env`:
- `DATABASE_PASSWORD` - Your PostgreSQL password
- `OPENAI_API_KEY` - Your OpenAI API key (if using AI features)
- `SECRET_KEY` - Generate with: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
- `JWT_SECRET` - Generate with: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`

### 3. Install Python Dependencies

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Set Up Database

```bash
# Create database
createdb multi_agent_ecommerce

# Run migrations (if using Alembic)
alembic upgrade head

# Or use the setup script (Windows)
# setup-database.bat
```

### 5. Start Infrastructure Services

#### Option A: Using Docker Compose (Recommended)

```bash
cd infrastructure
docker-compose up -d
```

This starts:
- PostgreSQL
- Kafka + Zookeeper
- Redis
- Prometheus
- Grafana
- Loki

#### Option B: Manual Setup

Start each service individually:
```bash
# PostgreSQL (if not already running)
sudo systemctl start postgresql

# Kafka
bin/kafka-server-start.sh config/server.properties

# Redis
redis-server
```

### 6. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=shared --cov=agents --cov-report=html

# View coverage report
open htmlcov/index.html  # On macOS
# or
xdg-open htmlcov/index.html  # On Linux
```

### 7. Start the Agents

```bash
# Start all agents
python start-agents-direct.py

# Or start individual agents
python -m agents.order_agent
python -m agents.inventory_agent
python -m agents.carrier_selection_agent
```

### 8. Start the Dashboard

```bash
cd multi-agent-dashboard
npm install
npm run dev
```

Access the dashboard at: http://localhost:5173

## Testing in Your Environment

### 1. Verify Infrastructure

```bash
# Check PostgreSQL
psql -U postgres -d multi_agent_ecommerce -c "SELECT version();"

# Check Kafka
kafka-topics.sh --list --bootstrap-server localhost:9092

# Check Redis
redis-cli ping
```

### 2. Test Agent Communication

```bash
# Use the CLI to test agent interactions
python run_cli.py

# Or use the demo script
python start-demo.bat  # On Windows
```

### 3. Monitor System Health

- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Agent Health**: Check logs in `logs/` directory

### 4. Run Integration Tests

```bash
# Test order flow
pytest tests/integration/test_order_flow.py -v

# Test inventory management
pytest tests/integration/test_inventory.py -v
```

## Configuration Validation

### Test Configuration Loading

```python
from shared.config import get_config

config = get_config()
print(f"Database: {config.database_name}")
print(f"Kafka: {config.kafka_bootstrap_servers}")
print(f"Environment: {config.environment}")
```

### Test Security Features

```python
from shared.security import get_secret_manager, TokenGenerator

# Test encryption
secret_mgr = get_secret_manager()
encrypted = secret_mgr.encrypt("test_data")
decrypted = secret_mgr.decrypt(encrypted)
assert decrypted == "test_data"

# Test token generation
token = TokenGenerator.generate_token()
api_key = TokenGenerator.generate_api_key()
print(f"Generated API Key: {api_key}")
```

### Test Message Validation

```python
from shared.message_schemas import validate_message_payload
from datetime import datetime
from decimal import Decimal

# Test order creation message
payload = validate_message_payload("order_created", {
    "order_id": "test-123",
    "customer_id": "cust-456",
    "channel": "shopify",
    "total_amount": Decimal("99.99"),
    "items_count": 2,
    "created_at": datetime.now()
})

print(f"Validated payload: {payload}")
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Error
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -U postgres -c "SELECT 1;"

# Verify credentials in .env
cat .env | grep DATABASE
```

#### 2. Kafka Connection Error
```bash
# Check if Kafka is running
docker ps | grep kafka

# Test Kafka connectivity
kafka-broker-api-versions.sh --bootstrap-server localhost:9092
```

#### 3. Import Errors
```bash
# Ensure you're in the virtual environment
which python

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### 4. Test Failures
```bash
# Run tests with verbose output
pytest -vv

# Run specific test
pytest tests/test_base_agent.py::TestBaseAgent::test_agent_initialization -vv

# Clear pytest cache
pytest --cache-clear
```

### Logs Location

- Agent logs: `logs/agents/`
- System logs: `logs/system/`
- Error logs: `logs/errors/`

### Debug Mode

Enable debug mode in `.env`:
```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

## Performance Testing

### Load Testing

```bash
# Install locust
pip install locust

# Run load tests
locust -f tests/load/locustfile.py
```

### Benchmarking

```bash
# Benchmark message processing
python tests/benchmarks/message_throughput.py

# Benchmark database operations
python tests/benchmarks/database_performance.py
```

## Production Deployment

### Security Checklist

- [ ] All secrets in environment variables
- [ ] `.env` file not committed to git
- [ ] Strong passwords for all services
- [ ] HTTPS/TLS enabled
- [ ] Firewall configured
- [ ] Rate limiting enabled
- [ ] Monitoring and alerting configured
- [ ] Backup strategy in place
- [ ] Log rotation configured

### Docker Production Deployment

```bash
# Build production images
docker-compose -f infrastructure/docker-compose.prod.yml build

# Start production stack
docker-compose -f infrastructure/docker-compose.prod.yml up -d

# Check status
docker-compose -f infrastructure/docker-compose.prod.yml ps
```

### Kubernetes Deployment

```bash
# Apply configurations
kubectl apply -f infrastructure/k8s/

# Check deployments
kubectl get deployments
kubectl get services
kubectl get pods

# View logs
kubectl logs -f deployment/order-agent
```

## Monitoring and Maintenance

### Health Checks

```bash
# Check agent health
curl http://localhost:8000/health

# Check system metrics
curl http://localhost:9090/metrics
```

### Backup Database

```bash
# Backup
pg_dump -U postgres multi_agent_ecommerce > backup_$(date +%Y%m%d).sql

# Restore
psql -U postgres multi_agent_ecommerce < backup_20241019.sql
```

### Update System

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run migrations
alembic upgrade head

# Restart agents
./restart-agents.sh
```

## Support and Documentation

- **Architecture**: See `SYSTEM_ARCHITECTURE.md`
- **Improvements**: See `IMPROVEMENTS.md`
- **API Docs**: http://localhost:8000/docs (when running)
- **Issues**: https://github.com/Tipingouin17/Multi-agent-AI-Ecommerce/issues

## Next Steps

1. Review the `IMPROVEMENTS.md` for detailed information on new features
2. Check the `CHANGELOG.md` for all changes
3. Read the security best practices in `IMPROVEMENTS.md`
4. Set up monitoring dashboards in Grafana
5. Configure alerting rules in Prometheus
6. Implement CI/CD pipeline for automated testing and deployment

## Contact

For questions or support, please open an issue on GitHub or contact the development team.

