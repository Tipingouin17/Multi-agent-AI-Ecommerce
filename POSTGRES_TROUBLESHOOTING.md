# PostgreSQL Connection Troubleshooting Guide

## Quick Fix (Most Common Issues)

### Option 1: Run the Fix Script
```powershell
.\scripts\fix_postgres_connection.ps1
```

This will automatically:
1. Restart PostgreSQL container
2. Wait for it to be ready
3. Ensure database exists
4. Test the connection

### Option 2: Manual Steps
```powershell
# 1. Restart PostgreSQL
docker restart multi-agent-postgres

# 2. Wait 10 seconds
Start-Sleep -Seconds 10

# 3. Check if it's ready
docker logs multi-agent-postgres --tail 20

# 4. Test connection
docker exec multi-agent-postgres psql -U postgres -d multi_agent_ecommerce -c "SELECT 1;"
```

---

## Common Issues and Solutions

### Issue 1: Container Not Running

**Symptoms:**
- Error: "Cannot connect to PostgreSQL"
- Container shows as "Exited" in Docker Desktop

**Solution:**
```powershell
# Check container status
docker ps -a | Select-String "postgres"

# Start the container
docker start multi-agent-postgres

# Check logs for errors
docker logs multi-agent-postgres
```

### Issue 2: Port 5432 Already in Use

**Symptoms:**
- Error: "port is already allocated"
- Container fails to start

**Solution:**
```powershell
# Find what's using port 5432
netstat -ano | Select-String "5432"

# Option A: Stop the other PostgreSQL instance
# (if you have PostgreSQL installed locally)

# Option B: Change the port in docker-compose.yml
# Edit infrastructure/docker-compose.yml:
#   ports:
#     - "5433:5432"  # Use 5433 instead
# Then update .env:
#   DATABASE_URL=postgresql://postgres:postgres@localhost:5433/multi_agent_ecommerce
```

### Issue 3: Database Doesn't Exist

**Symptoms:**
- Error: "database 'multi_agent_ecommerce' does not exist"

**Solution:**
```powershell
# Create the database
docker exec multi-agent-postgres psql -U postgres -c "CREATE DATABASE multi_agent_ecommerce;"

# Verify it was created
docker exec multi-agent-postgres psql -U postgres -c "\l"
```

### Issue 4: Container Exists But Won't Start

**Symptoms:**
- Container shows in `docker ps -a` but not in `docker ps`
- Logs show errors

**Solution:**
```powershell
# Remove and recreate the container
cd infrastructure
docker-compose down
docker-compose up -d postgres

# Wait for it to start
Start-Sleep -Seconds 15

# Check logs
docker logs multi-agent-postgres
```

### Issue 5: Permission Denied

**Symptoms:**
- Error: "permission denied for database"
- Error: "role 'postgres' does not exist"

**Solution:**
```powershell
# Recreate container with fresh data
docker-compose down -v  # WARNING: This deletes all data!
docker-compose up -d postgres
```

### Issue 6: Connection Timeout

**Symptoms:**
- Error: "could not connect to server: Connection timed out"
- Takes a long time then fails

**Solution:**
```powershell
# 1. Check if PostgreSQL is actually running
docker exec multi-agent-postgres pg_isready -U postgres

# 2. Check if it's listening on the right port
docker exec multi-agent-postgres netstat -tlnp | Select-String "5432"

# 3. Restart with fresh logs
docker restart multi-agent-postgres
docker logs -f multi-agent-postgres  # Watch the logs
```

### Issue 7: Windows Firewall Blocking

**Symptoms:**
- Connection works from Docker but not from host
- Error: "Connection refused"

**Solution:**
```powershell
# Allow Docker through Windows Firewall
# 1. Open Windows Defender Firewall
# 2. Click "Allow an app through firewall"
# 3. Find "Docker Desktop" and ensure both Private and Public are checked
```

---

## Diagnostic Commands

### Check Container Status
```powershell
docker ps -a --filter "name=multi-agent-postgres"
```

### View Logs
```powershell
# Last 50 lines
docker logs multi-agent-postgres --tail 50

# Follow logs in real-time
docker logs -f multi-agent-postgres

# Search for errors
docker logs multi-agent-postgres 2>&1 | Select-String "ERROR"
```

### Test Connection from Inside Container
```powershell
docker exec multi-agent-postgres psql -U postgres -d multi_agent_ecommerce -c "SELECT version();"
```

### Test Connection from Host
```powershell
# Using Python
python -c "import psycopg2; conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/multi_agent_ecommerce'); print('Connected!')"

# Using Docker exec
docker exec multi-agent-postgres psql -U postgres -d multi_agent_ecommerce -c "SELECT 1;"
```

### Check Port Mapping
```powershell
docker port multi-agent-postgres
```

### Inspect Container
```powershell
docker inspect multi-agent-postgres | ConvertFrom-Json | Select-Object -ExpandProperty NetworkSettings
```

---

## Advanced Troubleshooting

### Reset Everything (Nuclear Option)
```powershell
# WARNING: This deletes ALL data!

# 1. Stop all containers
docker-compose down

# 2. Remove volumes (deletes data)
docker-compose down -v

# 3. Remove images (optional)
docker rmi $(docker images -q multi-agent*)

# 4. Start fresh
docker-compose up -d

# 5. Wait for PostgreSQL
Start-Sleep -Seconds 20

# 6. Run migrations
python scripts/run_migrations.py
```

### Check PostgreSQL Configuration
```powershell
# View postgresql.conf
docker exec multi-agent-postgres cat /var/lib/postgresql/data/postgresql.conf

# View pg_hba.conf (authentication)
docker exec multi-agent-postgres cat /var/lib/postgresql/data/pg_hba.conf
```

### Manual Database Creation
```powershell
# Connect as postgres user
docker exec -it multi-agent-postgres psql -U postgres

# Inside psql:
CREATE DATABASE multi_agent_ecommerce;
\c multi_agent_ecommerce
\dt  # List tables
\q   # Quit
```

---

## Verification Checklist

After fixing, verify everything works:

- [ ] Container is running: `docker ps | Select-String "postgres"`
- [ ] Port 5432 is listening: `netstat -an | Select-String "5432"`
- [ ] Database exists: `docker exec multi-agent-postgres psql -U postgres -c "\l"`
- [ ] Can connect: `docker exec multi-agent-postgres psql -U postgres -d multi_agent_ecommerce -c "SELECT 1;"`
- [ ] Migrations run: `python scripts/run_migrations.py`
- [ ] Agents can connect: Check agent logs for database connection success

---

## Environment Variables

Ensure your `.env` file has correct PostgreSQL settings:

```env
# PostgreSQL Configuration
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=multi_agent_ecommerce
DB_USER=postgres
DB_PASSWORD=postgres

# Full connection string
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/multi_agent_ecommerce
```

---

## Still Having Issues?

### Check Docker Desktop
1. Open Docker Desktop
2. Go to Settings → Resources
3. Ensure enough memory allocated (at least 4GB)
4. Restart Docker Desktop

### Check Windows Services
```powershell
# Ensure Docker service is running
Get-Service | Select-String "docker"
```

### Check System Resources
```powershell
# Check if system has enough resources
docker stats --no-stream
```

### Get Help
If none of these solutions work:

1. **Check container logs:**
   ```powershell
   docker logs multi-agent-postgres > postgres_error.log
   ```

2. **Check Docker Compose logs:**
   ```powershell
   cd infrastructure
   docker-compose logs postgres > postgres_compose.log
   ```

3. **Provide these logs when asking for help**

---

## Prevention

To avoid PostgreSQL connection issues in the future:

1. **Always use the setup script:**
   ```powershell
   .\setup-and-launch.ps1
   ```

2. **Wait for services to be ready:**
   - The script waits 30 seconds for PostgreSQL
   - Don't interrupt this wait time

3. **Check Docker Desktop before starting:**
   - Ensure Docker Desktop is running
   - Check it has enough resources

4. **Regular maintenance:**
   ```powershell
   # Weekly cleanup
   docker system prune -f
   ```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `docker ps` | List running containers |
| `docker ps -a` | List all containers |
| `docker logs multi-agent-postgres` | View PostgreSQL logs |
| `docker restart multi-agent-postgres` | Restart PostgreSQL |
| `docker exec -it multi-agent-postgres psql -U postgres` | Connect to PostgreSQL |
| `.\scripts\fix_postgres_connection.ps1` | Auto-fix connection issues |
| `.\scripts\diagnose_postgres.ps1` | Diagnose connection problems |

---

**Last Updated:** October 23, 2025

