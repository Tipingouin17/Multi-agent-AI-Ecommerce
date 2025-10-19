# Kafka Listener Configuration Fix

## The Real Problem

The issue wasn't just about connection addresses. Even when TCP connects successfully, **Kafka returns its `advertised.listeners` in metadata responses**. If those advertised addresses point to hostnames or IPs that your client can't reach (like container internal names or `localhost` from inside Docker), the client will fail with `NoBrokersAvailable` or connection errors.

## Root Cause Explained

### What Happens:

1. **Client connects** to `localhost:9092` ✅
2. **Kafka accepts** the connection ✅  
3. **Kafka sends metadata** with `advertised.listeners` ✅
4. **Client tries to connect** to the advertised address ❌
5. **Connection fails** because the advertised address is unreachable ❌

### Example Flow:

```
Client (Windows) → localhost:9092 → Kafka Container
                                     ↓
                    Metadata response: "Connect to kafka:29092"
                                     ↓
Client tries kafka:29092 → DNS fails → NoBrokersAvailable
```

## The Solution: Dual Listeners

Kafka needs **two separate listeners**:

1. **PLAINTEXT** (internal): For inter-broker communication and other Docker containers
   - Listens on: `0.0.0.0:29092`
   - Advertises: `kafka:29092` (container hostname)
   
2. **PLAINTEXT_HOST** (external): For clients on the Windows host
   - Listens on: `0.0.0.0:9092`
   - Advertises: `localhost:9092` (reachable from Windows)

## Fixed Configuration

### docker-compose.yml

```yaml
kafka:
  image: confluentinc/cp-kafka:7.4.0
  container_name: multi-agent-kafka
  depends_on:
    - zookeeper
  environment:
    KAFKA_BROKER_ID: 1
    KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    
    # Define two listeners with their security protocols
    KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
    
    # Bind both listeners to all interfaces
    KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:29092,PLAINTEXT_HOST://0.0.0.0:9092
    
    # Advertise different addresses for each listener
    # - PLAINTEXT: Use container name for internal Docker communication
    # - PLAINTEXT_HOST: Use localhost for Windows host access
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
    
    # Use internal listener for inter-broker communication
    KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
    
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
    KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
    KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'true'
    KAFKA_NUM_PARTITIONS: 3
    KAFKA_DEFAULT_REPLICATION_FACTOR: 1
  ports:
    - "9092:9092"  # External port for Windows host
    - "29092:29092"  # Internal port (optional, for debugging)
  networks:
    - multi-agent-network
```

### Key Configuration Explained

| Setting | Value | Purpose |
|---------|-------|---------|
| `KAFKA_LISTENERS` | `PLAINTEXT://0.0.0.0:29092,PLAINTEXT_HOST://0.0.0.0:9092` | Bind both listeners to all network interfaces |
| `KAFKA_ADVERTISED_LISTENERS` | `PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092` | Tell clients where to connect |
| `KAFKA_INTER_BROKER_LISTENER_NAME` | `PLAINTEXT` | Use internal listener for broker-to-broker |
| `KAFKA_LISTENER_SECURITY_PROTOCOL_MAP` | `PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT` | Map listener names to protocols |

## How to Apply the Fix

### Step 1: Pull Latest Changes

```powershell
cd C:\Users\jerom\OneDrive\Documents\Project\Multi-agent-AI-Ecommerce
git pull origin main
```

### Step 2: Restart Kafka with New Configuration

```powershell
cd infrastructure

# Stop everything
docker-compose down

# Remove old Kafka data (optional but recommended)
docker volume rm infrastructure_kafka_data

# Start with new configuration
docker-compose up -d

# Wait for Kafka to be ready (60 seconds)
Start-Sleep -Seconds 60
```

### Step 3: Verify Kafka is Ready

```powershell
# Check Kafka logs
docker logs multi-agent-kafka --tail 50

# Should see: "Kafka Server started"
```

### Step 4: Test Connection from Windows

```powershell
# Test with kafka-python
python -c "from kafka import KafkaAdminClient; admin = KafkaAdminClient(bootstrap_servers=['localhost:9092'], request_timeout_ms=10000); print(f'Connected! Topics: {admin.list_topics()}'); admin.close()"
```

### Step 5: Update .env (if needed)

Your `.env` should have:

```env
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

**Not** `host.docker.internal:9092` - with the fixed listener configuration, `localhost:9092` will work correctly!

### Step 6: Start Agents

```powershell
cd ..
.\start-system.ps1
```

All agents should now connect successfully! ✅

## Verification

### Check Kafka Listeners

```powershell
docker exec -it multi-agent-kafka kafka-broker-api-versions --bootstrap-server localhost:9092
```

Should return broker information without errors.

### Check Topics

```powershell
docker exec -it multi-agent-kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Test Producer/Consumer

```powershell
# Create test topic
docker exec -it multi-agent-kafka kafka-topics --create --topic test --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

# Send message
docker exec -it multi-agent-kafka bash -c "echo 'test message' | kafka-console-producer --bootstrap-server localhost:9092 --topic test"

# Consume message
docker exec -it multi-agent-kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic test --from-beginning --max-messages 1
```

## Troubleshooting

### Still Getting Connection Errors?

**1. Check Kafka is fully started**

```powershell
docker logs multi-agent-kafka | Select-String "started"
```

Wait until you see: `[KafkaServer id=1] started`

**2. Verify listener configuration**

```powershell
docker exec -it multi-agent-kafka env | Select-String "KAFKA_"
```

Should show all the environment variables correctly set.

**3. Check from inside container**

```powershell
# Test internal listener
docker exec -it multi-agent-kafka kafka-broker-api-versions --bootstrap-server kafka:29092

# Test external listener
docker exec -it multi-agent-kafka kafka-broker-api-versions --bootstrap-server localhost:9092
```

Both should work.

**4. Check Windows firewall**

```powershell
# Allow Kafka port
New-NetFirewallRule -DisplayName "Kafka" -Direction Inbound -LocalPort 9092 -Protocol TCP -Action Allow
```

**5. Restart Docker Desktop**

Sometimes Docker Desktop needs a full restart:
- Right-click Docker Desktop icon
- Select "Restart"
- Wait for it to fully start
- Run `docker-compose up -d` again

### Agents Still Failing?

**Check agent logs for the exact error:**

```powershell
# Look at agent startup
python start-agents-monitor.py
```

**Common issues:**

| Error | Cause | Fix |
|-------|-------|-----|
| `NoBrokersAvailable` | Advertised listeners wrong | Check `KAFKA_ADVERTISED_LISTENERS` |
| `Connection refused` | Kafka not ready | Wait longer (60s+) |
| `DNS resolution failed` | Using container hostname | Use `localhost:9092` |
| `Timeout` | Firewall blocking | Check Windows Firewall |

## Advanced: Using host.docker.internal

If you want to use `host.docker.internal` instead of `localhost`:

```yaml
KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://host.docker.internal:9092
```

And in `.env`:
```env
KAFKA_BOOTSTRAP_SERVERS=host.docker.internal:9092
```

This works on Windows and Mac but not Linux.

## For Production

### Option 1: Run Agents in Docker

Add agents to `docker-compose.yml`:

```yaml
order-agent:
  build: ./agents
  environment:
    KAFKA_BOOTSTRAP_SERVERS: kafka:29092  # Use internal listener
  networks:
    - multi-agent-network
```

Benefits:
- ✅ No listener configuration needed
- ✅ Better isolation
- ✅ Easier deployment

### Option 2: Use External DNS

For production with external clients:

```yaml
KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://kafka.yourdomain.com:9092
```

## Quick Reference

### Working Configuration Summary

```yaml
# Listeners: Where Kafka binds
KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:29092,PLAINTEXT_HOST://0.0.0.0:9092

# Advertised: What Kafka tells clients
KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092

# Inter-broker: Which listener brokers use
KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
```

### Client Configuration

**From Windows host (your agents):**
```python
bootstrap_servers=['localhost:9092']
```

**From Docker containers:**
```python
bootstrap_servers=['kafka:29092']
```

**From other machines:**
```python
bootstrap_servers=['your-server-ip:9092']
```

---

## Summary

The fix involves properly configuring Kafka's dual listener setup:
- **Internal listener** (`kafka:29092`) for Docker network
- **External listener** (`localhost:9092`) for Windows host

This ensures clients receive advertised addresses they can actually reach, eliminating the `NoBrokersAvailable` and connection errors.

**After applying this fix, your agents will connect successfully!** 🎉

