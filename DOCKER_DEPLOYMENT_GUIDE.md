# Docker Deployment Guide

**Multi-Agent E-commerce Platform - Complete Docker Deployment**

---

## Overview

The platform uses Docker Compose for infrastructure services (PostgreSQL, Redis, Kafka, monitoring) while agents run as Python processes on the host. This hybrid approach provides:

- **Easy infrastructure management** via Docker
- **Fast agent development** without container rebuilds
- **Production-ready monitoring** with Prometheus + Grafana
- **Cross-platform compatibility** (Windows, Linux, macOS)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Host Machine                              │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  27 Python Agents (Ports 8000-8100)                  │  │
│  │  - order_agent, product_agent, payment_agent, etc.   │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓ ↑                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Docker Containers (infrastructure/)                  │  │
│  │                                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │ PostgreSQL  │  │   Redis     │  │   Kafka     │  │  │
│  │  │   :5432     │  │   :6379     │  │   :9092     │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  │                                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │ Prometheus  │  │   Grafana   │  │    Loki     │  │  │
│  │  │   :9090     │  │   :3000     │  │   :3100     │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  │                                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐                    │  │
│  │  │   Nginx     │  │  pgAdmin    │                    │  │
│  │  │  :80/:443   │  │   :5050     │                    │  │
│  │  └─────────────┘  └─────────────┘                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Frontend (Vite Dev Server - Port 5173)              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Required Software

**All Platforms:**
- Docker Desktop 20.10+ or Docker Engine + Docker Compose
- Python 3.11+
- Node.js 22.13.0+
- Git

**Platform-Specific:**

**Windows:**
- Docker Desktop for Windows
- WSL2 (Windows Subsystem for Linux)

**macOS:**
- Docker Desktop for Mac

**Linux:**
- Docker Engine
- Docker Compose plugin

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/Tipingouin17/Multi-agent-AI-Ecommerce.git
cd Multi-agent-AI-Ecommerce
```

### 2. Start Infrastructure (Docker)

```bash
# Start all infrastructure services
cd infrastructure
docker-compose up -d

# Verify all containers are running
docker-compose ps
```

**Expected Output:**
```
NAME                        STATUS              PORTS
multi-agent-postgres        Up (healthy)        0.0.0.0:5432->5432/tcp
multi-agent-redis           Up (healthy)        0.0.0.0:6379->6379/tcp
multi-agent-kafka           Up (healthy)        0.0.0.0:9092->9092/tcp
multi-agent-zookeeper       Up (healthy)        0.0.0.0:2181->2181/tcp
multi-agent-prometheus      Up (healthy)        0.0.0.0:9090->9090/tcp
multi-agent-grafana         Up (healthy)        0.0.0.0:3000->3000/tcp
multi-agent-loki            Up (healthy)        0.0.0.0:3100->3100/tcp
multi-agent-promtail        Up                  
multi-agent-nginx           Up (healthy)        0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

### 3. Initialize Database

```bash
# Return to project root
cd ..

# Import database schema
docker exec -i multi-agent-postgres psql -U postgres -d ecommerce_db < database/schema.sql

# (Optional) Import seed data
docker exec -i multi-agent-postgres psql -U postgres -d ecommerce_db < database/seed_data.sql
```

### 4. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3.11 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Install Frontend Dependencies

```bash
cd multi-agent-dashboard
npm install
cd ..
```

### 6. Start All 27 Agents

```bash
# Linux/macOS:
./start_all_agents.sh

# Windows:
start_all_agents.bat
```

### 7. Start Frontend

```bash
cd multi-agent-dashboard
npm run dev
```

### 8. Verify System

```bash
# Check all agents are healthy
# Linux/macOS:
./check_all_agents.sh

# Windows:
check_all_agents.bat
```

**Access the Platform:**
- **Frontend:** http://localhost:5173
- **Grafana:** http://localhost:3000 (admin/admin123)
- **Prometheus:** http://localhost:9090
- **pgAdmin:** http://localhost:5050 (admin@multiagent.com/pgadmin_default)
- **Kafka UI:** http://localhost:8080 (dev profile only)

---

## Docker Compose Services

### Core Infrastructure

| Service | Port | Description | Health Check |
|---------|------|-------------|--------------|
| **postgres** | 5432 | PostgreSQL 18 database | `pg_isready` |
| **redis** | 6379 | Redis cache | `redis-cli ping` |
| **kafka** | 9092 | Kafka message broker | API versions check |
| **zookeeper** | 2181 | Zookeeper (for Kafka) | Port check |

### Monitoring Stack

| Service | Port | Description | Credentials |
|---------|------|-------------|-------------|
| **prometheus** | 9090 | Metrics collection | None |
| **grafana** | 3000 | Monitoring dashboards | admin/admin123 |
| **loki** | 3100 | Log aggregation | None |
| **promtail** | - | Log shipper | None |

### Management Tools

| Service | Port | Description | Credentials | Profile |
|---------|------|-------------|-------------|---------|
| **nginx** | 80, 443 | Reverse proxy | None | default |
| **pgadmin** | 5050 | Database management | admin@multiagent.com/pgadmin_default | dev |
| **kafka-ui** | 8080 | Kafka management | None | dev |

---

## Docker Compose Profiles

The docker-compose.yml supports different profiles for different environments:

### Default Profile (Production)

```bash
docker-compose up -d
```

**Includes:**
- postgres
- redis
- kafka + zookeeper
- prometheus
- grafana
- loki + promtail
- nginx

### Dev Profile (Development)

```bash
docker-compose --profile dev up -d
```

**Adds:**
- pgAdmin (database management)
- Kafka UI (Kafka management)

### Full Profile (All Services)

```bash
docker-compose --profile full up -d
```

**Includes everything** from default + dev profiles

---

## Environment Configuration

### Using .env File

The docker-compose.yml reads from `../.env` (project root):

```env
# Database
DATABASE_NAME=ecommerce_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your_secure_password

# Grafana
GRAFANA_PASSWORD=your_grafana_password

# pgAdmin
PGADMIN_PASSWORD=your_pgadmin_password
```

### Environment Variables

All services support environment variable overrides:

```bash
# Override database password
DATABASE_PASSWORD=newpass docker-compose up -d postgres

# Override multiple variables
DATABASE_PASSWORD=pass1 GRAFANA_PASSWORD=pass2 docker-compose up -d
```

---

## Docker Commands Reference

### Start Services

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d postgres

# Start with dev tools
docker-compose --profile dev up -d

# Start and view logs
docker-compose up
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data!)
docker-compose down -v

# Stop specific service
docker-compose stop postgres
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100 postgres
```

### Check Status

```bash
# List all containers
docker-compose ps

# Check health
docker-compose ps | grep healthy
```

### Execute Commands

```bash
# PostgreSQL shell
docker exec -it multi-agent-postgres psql -U postgres -d ecommerce_db

# Redis CLI
docker exec -it multi-agent-redis redis-cli

# View container logs
docker logs multi-agent-postgres
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart postgres
```

---

## Data Persistence

### Docker Volumes

All data is persisted in Docker volumes:

```bash
# List volumes
docker volume ls | grep multi-agent

# Inspect volume
docker volume inspect infrastructure_postgres_data

# Backup volume
docker run --rm -v infrastructure_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# Restore volume
docker run --rm -v infrastructure_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

### Volume List

- `postgres_data` - PostgreSQL database files
- `redis_data` - Redis persistence
- `kafka_data` - Kafka message logs
- `zookeeper_data` - Zookeeper data
- `prometheus_data` - Prometheus metrics
- `grafana_data` - Grafana dashboards
- `loki_data` - Loki logs
- `pgadmin_data` - pgAdmin configuration

---

## Networking

### Docker Network

All services are on the `multi-agent-network` bridge network (172.20.0.0/16).

**From Host to Container:**
```bash
# Access PostgreSQL from host
psql -h localhost -p 5432 -U postgres -d ecommerce_db
```

**From Container to Container:**
```bash
# Agents connect to PostgreSQL using 'postgres' hostname
DATABASE_HOST=postgres
DATABASE_PORT=5432
```

**From Agent (Host) to Container:**
```python
# In agent code, use localhost
DATABASE_HOST=localhost  # or postgres if agent is also containerized
DATABASE_PORT=5432
```

---

## Monitoring & Observability

### Prometheus Metrics

**Access:** http://localhost:9090

**Key Metrics:**
- Agent health endpoints
- Database connections
- Kafka message rates
- System resource usage

### Grafana Dashboards

**Access:** http://localhost:3000  
**Login:** admin / admin123

**Pre-configured Dashboards:**
- System Overview
- Agent Performance
- Database Metrics
- Kafka Metrics

### Loki Logs

**Access:** via Grafana (Data Sources → Loki)

**Log Sources:**
- All Docker containers
- System logs (/var/log)
- Agent logs (via Promtail)

---

## Troubleshooting

### PostgreSQL Connection Issues

**Problem:** Agents can't connect to PostgreSQL

**Solution:**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Verify connection from host
psql -h localhost -p 5432 -U postgres -d ecommerce_db

# Restart PostgreSQL
docker-compose restart postgres
```

### Port Conflicts

**Problem:** `Error: port is already allocated`

**Solution:**
```bash
# Find process using the port
# Linux/macOS:
lsof -i :5432

# Windows:
netstat -ano | findstr :5432

# Stop the conflicting service or change port in docker-compose.yml
```

### Container Health Issues

**Problem:** Container shows as unhealthy

**Solution:**
```bash
# Check health status
docker-compose ps

# View detailed health check logs
docker inspect multi-agent-postgres | grep -A 20 Health

# Restart unhealthy container
docker-compose restart postgres
```

### Volume Permission Issues

**Problem:** Permission denied errors

**Solution:**
```bash
# Linux: Fix volume permissions
docker-compose down
sudo chown -R $USER:$USER $(docker volume inspect infrastructure_postgres_data --format '{{ .Mountpoint }}')
docker-compose up -d
```

### Out of Disk Space

**Problem:** No space left on device

**Solution:**
```bash
# Clean up unused Docker resources
docker system prune -a --volumes

# Remove specific volumes
docker volume rm infrastructure_postgres_data  # WARNING: deletes data!
```

---

## Production Deployment

### Security Hardening

1. **Change Default Passwords**

```env
DATABASE_PASSWORD=strong_random_password_here
GRAFANA_PASSWORD=another_strong_password
PGADMIN_PASSWORD=yet_another_password
```

2. **Disable Dev Tools**

```bash
# Don't use --profile dev in production
docker-compose up -d
```

3. **Enable SSL/TLS**

Update `infrastructure/nginx/nginx.conf` with SSL certificates.

4. **Restrict Network Access**

```yaml
# In docker-compose.yml, bind to localhost only
ports:
  - "127.0.0.1:5432:5432"  # PostgreSQL only accessible from host
```

### Resource Limits

Add resource limits to prevent container resource exhaustion:

```yaml
services:
  postgres:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### Backup Strategy

```bash
# Daily database backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec multi-agent-postgres pg_dump -U postgres ecommerce_db | gzip > backup_$DATE.sql.gz

# Keep last 7 days
find . -name "backup_*.sql.gz" -mtime +7 -delete
```

---

## Windows-Specific Notes

### WSL2 Configuration

```powershell
# Enable WSL2
wsl --install

# Set WSL2 as default
wsl --set-default-version 2

# Configure Docker Desktop to use WSL2
```

### File Paths

Use forward slashes in docker-compose.yml even on Windows:

```yaml
volumes:
  - ./database/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
```

### Performance

For better performance on Windows:
1. Store project files in WSL2 filesystem (not /mnt/c/)
2. Allocate more resources to Docker Desktop (Settings → Resources)

---

## macOS-Specific Notes

### File Sharing

Ensure project directory is in Docker Desktop file sharing list:
- Docker Desktop → Preferences → Resources → File Sharing

### Performance

For better performance:
1. Use VirtioFS (Docker Desktop → Preferences → General → Use VirtioFS)
2. Allocate sufficient RAM (Settings → Resources → Memory: 8GB+)

---

## Complete System Startup

### Automated Script

```bash
# Start everything with one command
./start_complete_system.sh
```

This script:
1. Starts Docker infrastructure
2. Waits for services to be healthy
3. Initializes database
4. Starts all 27 agents
5. Starts frontend
6. Provides status summary

---

## Summary

**Infrastructure (Docker):**
- ✅ PostgreSQL, Redis, Kafka
- ✅ Prometheus, Grafana, Loki
- ✅ Nginx, pgAdmin, Kafka UI

**Agents (Host):**
- ✅ 27 Python agents on ports 8000-8100
- ✅ Fast development without container rebuilds

**Frontend (Host):**
- ✅ Vite dev server on port 5173

**Cross-Platform:**
- ✅ Works on Windows, Linux, macOS
- ✅ Consistent environment via Docker

---

**Last Updated:** November 5, 2025  
**Docker Compose Version:** 3.8  
**Platform Version:** 3.0.0
