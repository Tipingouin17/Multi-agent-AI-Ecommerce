# PostgreSQL Permission Error Fix

## Problem

When starting the PostgreSQL Docker container, you encountered:
```
mkdir: cannot create directory '/var/lib/postgresql/data': Permission denied
```

This is a common issue on Windows with Docker Desktop when PostgreSQL tries to create its data directory.

## Root Cause

The issue occurs because:
1. Docker on Windows has different permission handling than Linux
2. The `PGDATA` environment variable was pointing to a subdirectory that couldn't be created
3. Volume mount permissions weren't properly set for the postgres user

## Solution Applied

### Changes to `docker-compose.yml`:

**Before:**
```yaml
postgres:
  image: postgres:18-alpine
  container_name: multi-agent-postgres
  environment:
    POSTGRES_DB: multi_agent_ecommerce
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres123}
    PGDATA: /var/lib/postgresql/data/pgdata  # ❌ Problematic
  volumes:
    - postgres_data:/var/lib/postgresql/data
```

**After:**
```yaml
postgres:
  image: postgres:18-alpine
  container_name: multi-agent-postgres
  user: postgres  # ✅ Run as postgres user
  environment:
    POSTGRES_DB: multi_agent_ecommerce
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres123}
    # ✅ Removed PGDATA - use default location
  volumes:
    - postgres_data:/var/lib/postgresql/data
```

### What Changed:

1. **Added `user: postgres`** - Ensures container runs as postgres user
2. **Removed `PGDATA` override** - Uses default PostgreSQL data directory
3. **Simplified volume mount** - Direct mapping without subdirectory issues

## How to Apply the Fix

### Step 1: Stop and Remove Existing Container

```powershell
cd infrastructure

# Stop all services
docker-compose down

# Remove the postgres volume (this will delete existing data!)
docker volume rm infrastructure_postgres_data

# Or if you want to keep data, just stop:
docker-compose stop postgres
docker rm multi-agent-postgres
```

### Step 2: Pull Latest Changes

```powershell
cd C:\Users\jerom\OneDrive\Documents\Project\Multi-agent-AI-Ecommerce
git pull origin main
```

### Step 3: Start PostgreSQL

```powershell
cd infrastructure

# Start only PostgreSQL first to verify it works
docker-compose up -d postgres

# Check logs
docker-compose logs postgres

# Should see: "database system is ready to accept connections"
```

### Step 4: Start All Services

```powershell
# Once PostgreSQL is working, start everything
docker-compose up -d

# Verify all services
docker-compose ps
```

## Verification

### Check PostgreSQL is Running

```powershell
# Check container status
docker ps | findstr postgres

# Check logs
docker logs multi-agent-postgres

# Connect to PostgreSQL
docker exec -it multi-agent-postgres psql -U postgres -d multi_agent_ecommerce

# In psql:
\l                    # List databases
\dt                   # List tables
\q                    # Quit
```

### Test Connection from Host

```powershell
# If you have psql installed locally
psql -h localhost -U postgres -d multi_agent_ecommerce

# Or use Python
python -c "import psycopg2; conn = psycopg2.connect('postgresql://postgres:postgres123@localhost:5432/multi_agent_ecommerce'); print('✓ Connected'); conn.close()"
```

## Alternative Solutions

If the above doesn't work, try these alternatives:

### Option 1: Use Named Volume with Explicit Permissions

```yaml
postgres:
  image: postgres:18-alpine
  container_name: multi-agent-postgres
  environment:
    POSTGRES_DB: multi_agent_ecommerce
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres123}
  ports:
    - "5432:5432"
  volumes:
    - type: volume
      source: postgres_data
      target: /var/lib/postgresql/data
      volume:
        nocopy: false
  tmpfs:
    - /tmp
```

### Option 2: Use Bind Mount (Windows-specific)

```yaml
postgres:
  image: postgres:18-alpine
  container_name: multi-agent-postgres
  environment:
    POSTGRES_DB: multi_agent_ecommerce
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres123}
  ports:
    - "5432:5432"
  volumes:
    - C:/docker-volumes/postgres:/var/lib/postgresql/data
```

Then create the directory first:
```powershell
mkdir C:\docker-volumes\postgres
```

### Option 3: Use Your Local PostgreSQL

If Docker continues to have issues, use your local PostgreSQL 18 installation:

1. **Skip PostgreSQL in Docker:**
   ```powershell
   # Start everything except postgres
   docker-compose up -d redis kafka zookeeper prometheus grafana loki
   ```

2. **Update `.env` to use local PostgreSQL:**
   ```ini
   DATABASE_HOST=localhost
   DATABASE_PORT=5432
   DATABASE_NAME=multi_agent_ecommerce
   DATABASE_USER=postgres
   DATABASE_PASSWORD=your_local_postgres_password
   ```

3. **Create database manually:**
   ```sql
   CREATE DATABASE multi_agent_ecommerce;
   ```

## Troubleshooting

### Issue: Volume still has permission errors

```powershell
# Remove volume completely
docker-compose down -v
docker volume prune -f

# Restart Docker Desktop
# Then try again
docker-compose up -d postgres
```

### Issue: Container starts but crashes immediately

```powershell
# Check detailed logs
docker logs multi-agent-postgres --tail 100

# Check if port is already in use
netstat -ano | findstr :5432

# If local PostgreSQL is running, stop it:
Stop-Service postgresql-x64-18
```

### Issue: "role postgres does not exist"

```powershell
# Recreate the container
docker-compose down
docker volume rm infrastructure_postgres_data
docker-compose up -d postgres
```

## Windows-Specific Notes

1. **Docker Desktop Settings:**
   - Ensure "Use WSL 2 based engine" is enabled
   - Allocate at least 4GB RAM to Docker
   - Enable file sharing for the drive where your project is located

2. **Antivirus/Firewall:**
   - Some antivirus software blocks Docker volume access
   - Add Docker Desktop to exclusions if needed

3. **WSL 2 Integration:**
   - If using WSL 2, ensure integration is enabled in Docker Desktop settings
   - Resources → WSL Integration → Enable for your distribution

## Summary

The fix simplifies the PostgreSQL configuration by:
- ✅ Running as the correct user (`postgres`)
- ✅ Using default data directory (no PGDATA override)
- ✅ Proper volume permissions

This should resolve the permission denied error on Windows.

## Next Steps

1. ✅ Pull latest changes from GitHub
2. ✅ Remove old PostgreSQL container and volume
3. ✅ Start PostgreSQL with new configuration
4. ✅ Verify connection works
5. 📝 Initialize database schema
6. 📝 Start remaining services
7. 📝 Start agents

All changes have been pushed to GitHub!

