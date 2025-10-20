# Docker Configuration Fix Guide

## Problem Fixed

The Docker Compose configuration had **empty configuration files** for:
- ✅ Loki (log aggregation)
- ✅ Promtail (log shipper)
- ✅ Nginx (reverse proxy)
- ✅ Prometheus (metrics)
- ✅ Grafana (dashboards)

All configuration files have now been created with proper settings.

## What Was Fixed

### 1. Loki Configuration (`monitoring/loki.yml`)
- Configured log storage with filesystem backend
- Set up proper schema for log indexing
- Enabled embedded cache for query performance
- Configured ports: 3100 (HTTP), 9096 (gRPC)

### 2. Promtail Configuration (`monitoring/promtail.yml`)
- Configured to scrape Docker container logs
- Set up system log collection
- Configured agent log collection
- Sends logs to Loki at `http://loki:3100`

### 3. Prometheus Configuration (`monitoring/prometheus.yml`)
- Scrape interval: 15 seconds
- Configured to monitor:
  - PostgreSQL, Redis, Kafka
  - Grafana, Loki
  - Multi-agent services
  - Prometheus itself
- Alert rules integration

### 4. Alert Rules (`monitoring/alert_rules.yml`)
- Agent down alerts
- High error rate detection
- Database connection failures
- Kafka/Redis availability
- Memory and disk usage warnings

### 5. Nginx Configuration
**Main config (`nginx/nginx.conf`):**
- Optimized worker processes
- Gzip compression enabled
- Security headers added
- Client max body size: 20MB

**Site config (`nginx/conf.d/default.conf`):**
- Reverse proxy for Grafana (port 3000)
- Reverse proxy for Prometheus (port 9090)
- Reverse proxy for Loki (port 3100)
- Health check endpoint
- WebSocket support for Grafana

### 6. Grafana Configuration
**Datasources (`grafana/datasources/datasources.yml`):**
- Prometheus as default datasource
- Loki for log queries
- Auto-configured connections

**Dashboards (`grafana/dashboards/dashboards.yml`):**
- Dashboard provisioning enabled
- Auto-update every 10 seconds
- UI updates allowed

### 7. PostgreSQL Version Updated
- Changed from PostgreSQL 15 to **PostgreSQL 18** (matching your local installation)

## How to Use the Fixed Configuration

### Step 1: Pull Latest Changes

```powershell
cd C:\Users\jerom\OneDrive\Documents\Project\Multi-agent-AI-Ecommerce
git pull origin main
```

### Step 2: Stop Existing Containers (if any)

```powershell
cd infrastructure
docker-compose down
```

### Step 3: Start Services

```powershell
docker-compose up -d
```

### Step 4: Verify Services

```powershell
# Check all services are running
docker-compose ps

# Should show all services as "Up"
```

### Step 5: Check Logs

```powershell
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs loki
docker-compose logs promtail
docker-compose logs nginx
docker-compose logs prometheus
docker-compose logs grafana
```

## Service Access

Once all services are running:

| Service | URL | Purpose |
|---------|-----|---------|
| **Grafana** | http://localhost:3000 | Monitoring dashboards (admin/admin123) |
| **Prometheus** | http://localhost:9090 | Metrics and alerts |
| **Loki** | http://localhost:3100 | Log aggregation API |
| **Nginx** | http://localhost:80 | Reverse proxy |
| **PostgreSQL** | localhost:5432 | Database |
| **Redis** | localhost:6379 | Cache |
| **Kafka** | localhost:9092 | Message broker |
| **Kafka UI** | http://localhost:8080 | Kafka management (dev profile) |

## Troubleshooting

### Issue: Services still failing to start

```powershell
# Remove all containers and volumes
docker-compose down -v

# Rebuild and start
docker-compose up -d --build
```

### Issue: Port conflicts

```powershell
# Find process using port (e.g., 3000)
netstat -ano | findstr :3000

# Kill the process
taskkill /PID <PID> /F
```

### Issue: Permission errors (Windows)

```powershell
# Run PowerShell as Administrator
# Then navigate to project and run:
docker-compose up -d
```

### Issue: Loki not receiving logs

```powershell
# Check Promtail logs
docker-compose logs promtail

# Check Loki logs
docker-compose logs loki

# Restart Promtail
docker-compose restart promtail
```

### Issue: Nginx configuration errors

```powershell
# Test nginx configuration
docker-compose exec nginx nginx -t

# Reload nginx
docker-compose exec nginx nginx -s reload
```

## Verify Everything Works

### 1. Check Prometheus Targets

1. Open http://localhost:9090
2. Go to Status → Targets
3. All targets should show "UP"

### 2. Check Grafana Datasources

1. Open http://localhost:3000 (admin/admin123)
2. Go to Configuration → Data Sources
3. Prometheus and Loki should be configured

### 3. Check Loki Logs

1. In Grafana, go to Explore
2. Select "Loki" datasource
3. Query: `{compose_project="infrastructure"}`
4. You should see container logs

### 4. Test Nginx

```powershell
# Health check
curl http://localhost/health

# Should return: healthy
```

## Configuration File Locations

```
infrastructure/
├── docker-compose.yml          # Main Docker Compose file
├── monitoring/
│   ├── prometheus.yml          # Prometheus config
│   ├── alert_rules.yml         # Alert definitions
│   ├── loki.yml               # Loki config
│   ├── promtail.yml           # Promtail config
│   └── grafana/
│       ├── datasources/
│       │   └── datasources.yml # Grafana datasources
│       └── dashboards/
│           └── dashboards.yml  # Dashboard provisioning
└── nginx/
    ├── nginx.conf             # Main Nginx config
    └── conf.d/
        └── default.conf       # Site configuration
```

## Next Steps

1. ✅ All configuration files created
2. ✅ PostgreSQL version updated to 18
3. ✅ Services ready to start
4. 📝 Start Docker services: `docker-compose up -d`
5. 📝 Verify all services are healthy
6. 📝 Access Grafana and configure dashboards
7. 📝 Start your agents

## Common Docker Commands

```powershell
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Restart a service
docker-compose restart <service_name>

# Check service status
docker-compose ps

# Remove everything (including volumes)
docker-compose down -v

# Rebuild services
docker-compose up -d --build
```

## Support

If you encounter any issues:

1. Check service logs: `docker-compose logs <service_name>`
2. Verify configuration files exist and are not empty
3. Ensure Docker Desktop is running
4. Check for port conflicts
5. Try restarting Docker Desktop

All configuration files are now properly set up and pushed to your GitHub repository!

