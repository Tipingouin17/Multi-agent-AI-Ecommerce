# Kafka Connection Fix Guide

## Problem

All agents are crashing with:
```
KafkaConnectionError: Unable to bootstrap from [('localhost', 9092)]
```

## Root Cause

On **Windows with Docker Desktop**, containers run in a separate network namespace. When Python agents running on Windows try to connect to `localhost:9092`, they're trying to connect to Windows localhost, not the Docker container.

## Solution

### **Option 1: Automated Fix (Recommended)**

Run the fix script:

```powershell
.\fix-kafka-connection.ps1
```

This script will:
1. ✅ Check Kafka container status
2. ✅ Wait for Kafka to be fully ready
3. ✅ Update `.env` with correct Kafka address
4. ✅ Test the connection from Python
5. ✅ Provide next steps

### **Option 2: Manual Fix**

#### Step 1: Verify Kafka is Running

```powershell
docker ps | findstr kafka
```

You should see:
```
multi-agent-kafka   Running
multi-agent-zookeeper   Running
```

#### Step 2: Test Kafka Inside Container

```powershell
docker exec -it multi-agent-kafka kafka-topics.sh --list --bootstrap-server localhost:9092
```

If this works, Kafka is running correctly inside Docker.

#### Step 3: Update .env File

Edit `.env` and change:

```env
# FROM:
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# TO:
KAFKA_BOOTSTRAP_SERVERS=host.docker.internal:9092
```

**Why `host.docker.internal`?**
- This is a special DNS name that Docker Desktop provides
- It resolves to the host machine's IP from inside containers
- It also works from the host to reach Docker services

#### Step 4: Alternative Addresses

If `host.docker.internal` doesn't work, try these in order:

1. **Docker container IP** (find with `docker inspect multi-agent-kafka | findstr IPAddress`):
   ```env
   KAFKA_BOOTSTRAP_SERVERS=172.18.0.X:9092
   ```

2. **Windows host IP** (find with `ipconfig`):
   ```env
   KAFKA_BOOTSTRAP_SERVERS=192.168.X.X:9092
   ```

3. **Keep localhost** (works if Kafka port is properly mapped):
   ```env
   KAFKA_BOOTSTRAP_SERVERS=localhost:9092
   ```

#### Step 5: Verify Port Mapping

```powershell
docker port multi-agent-kafka
```

Should show:
```
9092/tcp -> 0.0.0.0:9092
```

#### Step 6: Test Connection

```powershell
# Install kafka-python if needed
pip install kafka-python

# Test connection
python -c "from kafka import KafkaAdminClient; admin = KafkaAdminClient(bootstrap_servers=['host.docker.internal:9092']); print('Connected!'); admin.close()"
```

#### Step 7: Restart Agents

```powershell
.\start-system.ps1
```

## Troubleshooting

### Kafka Still Not Connecting

**1. Restart Kafka Container**

```powershell
docker restart multi-agent-kafka
docker restart multi-agent-zookeeper

# Wait 30 seconds
Start-Sleep -Seconds 30

# Check logs
docker logs multi-agent-kafka --tail 50
```

**2. Check Kafka Logs for Errors**

```powershell
docker logs multi-agent-kafka
```

Look for:
- ✅ `[KafkaServer id=1] started` - Good!
- ❌ `Connection refused` - Zookeeper issue
- ❌ `Address already in use` - Port conflict

**3. Verify Zookeeper is Healthy**

```powershell
docker logs multi-agent-zookeeper --tail 20
```

Should see: `binding to port 0.0.0.0/0.0.0.0:2181`

**4. Check for Port Conflicts**

```powershell
netstat -ano | findstr :9092
```

If something else is using port 9092, you need to:
- Stop that service, OR
- Change Kafka port in `docker-compose.yml`

**5. Recreate Kafka Container**

```powershell
cd infrastructure
docker-compose down
docker volume rm infrastructure_kafka_data
docker-compose up -d
```

Wait 60 seconds for Kafka to fully start, then retry.

### Agents Start But Can't Communicate

**Check Kafka Topics**

```powershell
docker exec -it multi-agent-kafka kafka-topics.sh --list --bootstrap-server localhost:9092
```

Should show topics like:
- `orders`
- `products`
- `inventory`
- `agent-communication`

**Create Missing Topics**

```powershell
docker exec -it multi-agent-kafka kafka-topics.sh --create --topic orders --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
```

### Windows Firewall Blocking

If using Docker container IP directly:

```powershell
# Allow Docker network
New-NetFirewallRule -DisplayName "Docker Kafka" -Direction Inbound -LocalPort 9092 -Protocol TCP -Action Allow
```

## Long-Term Solution: Run Agents in Docker

For production, run agents in Docker too:

1. Create `Dockerfile` for agents
2. Add agents to `docker-compose.yml`
3. Use Docker network names (e.g., `multi-agent-kafka:9092`)

This eliminates networking issues entirely.

## Verification Checklist

Before starting agents, verify:

- [ ] Docker Desktop is running
- [ ] Kafka container is running (`docker ps`)
- [ ] Zookeeper container is running (`docker ps`)
- [ ] Kafka logs show "started" (`docker logs multi-agent-kafka`)
- [ ] Port 9092 is mapped (`docker port multi-agent-kafka`)
- [ ] `.env` has correct `KAFKA_BOOTSTRAP_SERVERS`
- [ ] Python can connect to Kafka (test script passes)

## Quick Reference

### Useful Commands

```powershell
# Check all containers
docker ps

# Restart Kafka
docker restart multi-agent-kafka

# View Kafka logs
docker logs multi-agent-kafka --tail 100 -f

# List topics
docker exec -it multi-agent-kafka kafka-topics.sh --list --bootstrap-server localhost:9092

# Test from Python
python -c "from kafka import KafkaAdminClient; admin = KafkaAdminClient(bootstrap_servers=['host.docker.internal:9092']); print(f'Topics: {admin.list_topics()}'); admin.close()"

# Check Kafka consumer groups
docker exec -it multi-agent-kafka kafka-consumer-groups.sh --list --bootstrap-server localhost:9092
```

### Environment Variables

Add to `.env`:

```env
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=host.docker.internal:9092
KAFKA_TOPIC_PREFIX=multi-agent
KAFKA_CONSUMER_GROUP=multi-agent-consumers

# Zookeeper (if needed)
ZOOKEEPER_CONNECT=localhost:2181
```

## Still Having Issues?

1. **Check Docker Desktop Settings**:
   - Resources → Advanced → Ensure enough memory (4GB+)
   - Network → Enable "Use kernel networking for UDP"

2. **Restart Docker Desktop**:
   - Right-click Docker Desktop icon
   - Select "Restart"
   - Wait for it to fully start

3. **Check System Resources**:
   ```powershell
   docker stats
   ```
   Ensure Kafka isn't out of memory

4. **Enable Debug Logging**:
   Add to `.env`:
   ```env
   KAFKA_LOG_LEVEL=DEBUG
   ```

---

**After fixing, run**: `.\start-system.ps1`

All agents should now connect successfully to Kafka! 🎉

