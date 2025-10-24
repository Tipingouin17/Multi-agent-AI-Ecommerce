# Infrastructure Setup Guide

This guide explains how to set up the infrastructure for the Multi-Agent E-commerce Platform.

## Prerequisites

1. **PostgreSQL** must be running
   ```bash
   # Start PostgreSQL via Docker
   docker-compose -f infrastructure/docker-compose.yml up -d postgres
   ```

2. **Kafka** must be running (optional, but recommended)
   ```bash
   # Start Kafka via Docker
   docker-compose -f infrastructure/docker-compose.yml up -d kafka zookeeper
   ```

3. **Python dependencies** must be installed
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### Option 1: Fresh Setup (Recommended for first time)

```bash
# Drop existing tables and create fresh database
python setup_infrastructure.py --drop-existing
```

### Option 2: Create Tables Only

```bash
# Create tables without dropping existing ones
python setup_infrastructure.py
```

### Option 3: Full Setup with Test Data

```bash
# Drop existing, create tables, and seed test data
python setup_infrastructure.py --drop-existing --seed-data
```

## What Does the Setup Script Do?

### 1. Database Setup
- Creates PostgreSQL database tables for all agents
- Tables include:
  - `orders`, `order_items`
  - `customers`
  - `products`, `inventory`
  - `payments`
  - `shipments`
  - `return_requests`, `warranty_claims`
  - `quality_checks`
  - `fraud_alerts`
  - `notifications`
  - And more...

### 2. Kafka Topics Setup
- Creates all required Kafka topics with 3 partitions each
- Topics include:
  - Order lifecycle: `order_created`, `order_confirmed`, `order_shipped`, etc.
  - Inventory: `inventory_reserved`, `inventory_released`, etc.
  - Payment: `payment_initiated`, `payment_completed`, etc.
  - Returns: `return_request_submitted`, `return_approved`, etc.
  - Monitoring: `agent_heartbeat`, `system_alert`
  - And more...

## Troubleshooting

### Database Connection Failed

**Error:** `Failed to connect to database`

**Solution:**
1. Check if PostgreSQL is running:
   ```bash
   docker ps | grep postgres
   ```

2. Verify database credentials in `.env` or environment variables:
   ```bash
   export DB_HOST=localhost
   export DB_PORT=5432
   export DB_NAME=multi_agent_ecommerce
   export DB_USER=postgres
   export DB_PASSWORD=postgres
   ```

3. Test connection manually:
   ```bash
   psql -h localhost -U postgres -d multi_agent_ecommerce
   ```

### Kafka Connection Failed

**Error:** `Failed to setup Kafka`

**Solution:**
1. Check if Kafka is running:
   ```bash
   docker ps | grep kafka
   ```

2. Verify Kafka broker address:
   ```bash
   export KAFKA_BROKERS=localhost:9092
   ```

3. If Kafka is not available, the system will still work but without event streaming

### Permission Denied

**Error:** `Permission denied when creating tables`

**Solution:**
1. Ensure the database user has CREATE TABLE permissions:
   ```sql
   GRANT ALL PRIVILEGES ON DATABASE multi_agent_ecommerce TO postgres;
   ```

### Tables Already Exist

**Error:** `Table already exists`

**Solution:**
1. Use `--drop-existing` flag to drop and recreate tables:
   ```bash
   python setup_infrastructure.py --drop-existing
   ```

2. Or manually drop tables:
   ```sql
   DROP SCHEMA public CASCADE;
   CREATE SCHEMA public;
   ```

## Next Steps

After successful setup:

1. **Start all agents:**
   ```bash
   python start-agents-monitor.py
   ```

2. **Start the dashboard:**
   ```bash
   cd multi-agent-dashboard
   npm run dev
   ```

3. **Access the system:**
   - Dashboard: http://localhost:5173
   - API docs: http://localhost:8001/docs (Order Agent)
   - Monitoring: http://localhost:8015/docs

## Configuration

### Database Configuration

Edit `shared/models.py` to change database settings:

```python
class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    database: str = "multi_agent_ecommerce"
    username: str = "postgres"
    password: str = "postgres"
```

### Kafka Configuration

Set environment variable:

```bash
export KAFKA_BROKERS=localhost:9092
```

For multiple brokers:

```bash
export KAFKA_BROKERS=broker1:9092,broker2:9092,broker3:9092
```

## Manual Setup (Alternative)

If you prefer to set up manually:

### 1. Create Database

```sql
CREATE DATABASE multi_agent_ecommerce;
```

### 2. Run Migrations

```bash
# Using Alembic (if migrations exist)
alembic upgrade head
```

### 3. Create Kafka Topics

```bash
# Using kafka-topics.sh
kafka-topics.sh --create --topic order_created --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
# Repeat for all topics...
```

## Support

For issues or questions:
1. Check the logs in `logs/` directory
2. Review agent-specific documentation
3. Open an issue on GitHub

