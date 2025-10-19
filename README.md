# Multi-Agent E-commerce System

A comprehensive AI-powered multi-agent system for warehouse and marketplace integration, designed for scalable e-commerce operations with advanced automation capabilities.

## 🚀 Features

### Core Capabilities
- **Multi-Agent Architecture**: Distributed system with specialized agents for different business functions
- **Real Database Operations**: PostgreSQL with SQLAlchemy ORM - **NO MOCK DATA** anywhere in the system
- **Real-time Communication**: Kafka-based messaging with encryption and circuit breaker patterns
- **Security First**: Encrypted secrets management, message signing, and secure API communications
- **Health Monitoring**: Comprehensive health checks, performance metrics, and automatic recovery
- **Scalable Design**: Containerized deployment with Kubernetes support

### Business Functions
- **Order Management**: Automated order processing, status tracking, and fulfillment coordination
- **Inventory Management**: Real-time stock tracking, automatic reordering, and multi-warehouse support
- **Product Management**: Catalog management, pricing optimization, and product lifecycle tracking
- **Logistics Optimization**: Intelligent carrier selection, warehouse routing, and shipping optimization
- **Customer Communication**: Automated notifications, status updates, and customer service integration
- **Risk Management**: Fraud detection, anomaly monitoring, and business intelligence

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Dashboard │    │   API Gateway   │    │  External APIs  │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
         ┌─────────────────────────────────────────────────┐
         │              Message Bus (Kafka)                │
         └─────────────────────┬───────────────────────────┘
                               │
    ┌──────────────────────────┼──────────────────────────┐
    │                          │                          │
┌───▼────┐  ┌────────┐  ┌──────▼──┐  ┌─────────┐  ┌──────▼──┐
│ Order  │  │Product │  │Inventory│  │Warehouse│  │Carrier  │
│ Agent  │  │ Agent  │  │  Agent  │  │  Agent  │  │ Agent   │
└───┬────┘  └────┬───┘  └──────┬──┘  └─────┬───┘  └──────┬──┘
    │            │             │           │             │
    └────────────┼─────────────┼───────────┼─────────────┘
                 │             │           │
         ┌───────▼─────────────▼───────────▼───────┐
         │           Database (PostgreSQL)         │
         │            NO MOCK DATA                 │
         └─────────────────────────────────────────┘
```

### Agent Responsibilities

| Agent | Purpose | Key Functions |
|-------|---------|---------------|
| **Order Agent** | Order lifecycle management | Order processing, status updates, fulfillment coordination |
| **Product Agent** | Product catalog management | Product CRUD, pricing, categorization |
| **Inventory Agent** | Stock management | Inventory tracking, reorder points, stock movements |
| **Warehouse Agent** | Warehouse operations | Location selection, capacity management, routing |
| **Carrier Agent** | Shipping optimization | Carrier selection, rate comparison, tracking |
| **Customer Agent** | Customer communication | Notifications, updates, service requests |
| **Monitoring Agent** | System health | Performance monitoring, alerting, diagnostics |

## 🛠️ Installation

### Prerequisites

- **Python 3.9+**
- **PostgreSQL 12+**
- **Apache Kafka 2.8+** (optional, for full messaging)
- **Redis 6.0+** (optional, for caching)

### Quick Start (Windows)

1. **Extract the system**
   ```cmd
   # Extract to desired location, e.g., C:\multi-agent-ecommerce\
   ```

2. **Run the installer**
   ```cmd
   cd C:\multi-agent-ecommerce
   install.bat
   ```

3. **Configure the system**
   ```cmd
   # Edit .env with your settings
   notepad .env
   ```

4. **Start the system**
   ```cmd
   start-system.bat
   ```

### Manual Installation

1. **Clone or extract the system**
   ```bash
   cd multi-agent-ecommerce
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e .
   ```

4. **Setup environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   # Create database
   createdb multi_agent_ecommerce
   
   # Initialize tables
   python -m multi_agent_ecommerce.cli init-db
   ```

6. **Start the system**
   ```bash
   python -m multi_agent_ecommerce.cli start
   ```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_HOST` | PostgreSQL host | `localhost` |
| `DATABASE_PORT` | PostgreSQL port | `5432` |
| `DATABASE_NAME` | Database name | `multi_agent_ecommerce` |
| `DATABASE_USER` | Database user | `postgres` |
| `DATABASE_PASSWORD` | Database password | *Required* |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka brokers | `localhost:9092` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Database Configuration

The system uses PostgreSQL with the following key features:
- **NO MOCK DATA**: All operations use real database queries
- **Proper Relationships**: Foreign keys and constraints ensure data integrity
- **Connection Pooling**: Optimized for high-concurrency operations
- **Migrations**: Schema versioning and updates

## 📊 CLI Commands

### Available Commands

```bash
# Check system status
python -m multi_agent_ecommerce.cli status

# Check system health
python -m multi_agent_ecommerce.cli health

# View configuration
python -m multi_agent_ecommerce.cli config

# Initialize database
python -m multi_agent_ecommerce.cli init-db

# Start the system
python -m multi_agent_ecommerce.cli start
```

### Windows Batch Scripts

After installation, these scripts are available:

- `start-system.bat` - Start the multi-agent system
- `check-status.bat` - Check system status
- `check-health.bat` - Run health checks
- `init-database.bat` - Initialize database tables
- `view-config.bat` - View current configuration

## 🔧 Development

### Database Operations

All database operations use real PostgreSQL - no mock data:

```python
from multi_agent_ecommerce.shared.database import get_database_manager
from multi_agent_ecommerce.shared.models import ProductDB

# Get database manager
db_manager = get_database_manager()

# Create product (real database operation)
async with db_manager.get_async_session() as session:
    product = ProductDB(
        name="New Product",
        sku="PROD-001",
        price=99.99,
        category="Electronics"
    )
    session.add(product)
    await session.commit()
```

## 🚀 Deployment

### Windows Deployment

The system includes Windows-specific deployment scripts:

1. **Run installer**: `install.bat`
2. **Start system**: `start-system.bat`
3. **Check status**: `check-status.bat`
4. **Check health**: `check-health.bat`
5. **Initialize database**: `init-database.bat`

## 🔒 Security

### Security Features

- **Real Database**: All operations use secure PostgreSQL connections
- **No Mock Data**: Production-ready data handling
- **Encrypted Secrets**: All secrets encrypted at rest
- **Message Signing**: HMAC signatures for message integrity
- **Secure Communication**: TLS for all external communications

## 🆘 Support

### Common Issues

#### Database Connection Issues
```bash
# Check database connectivity
python -m multi_agent_ecommerce.cli health

# Verify credentials
psql -h localhost -U postgres -d multi_agent_ecommerce
```

#### Agent Startup Issues
```bash
# Check agent logs
python -m multi_agent_ecommerce.cli status

# Verify dependencies
python -c "from multi_agent_ecommerce.shared.database import DatabaseManager; print('OK')"
```

### System Requirements

- **Minimum**: 4GB RAM, 2 CPU cores, 10GB disk
- **Recommended**: 8GB RAM, 4 CPU cores, 50GB disk
- **Production**: 16GB RAM, 8 CPU cores, 100GB disk

---

**🎉 Built with ❤️ for scalable e-commerce automation with real database operations and no mock data.**
