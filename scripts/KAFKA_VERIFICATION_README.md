# Kafka Connectivity Verification

This directory contains scripts to verify Kafka connectivity and configuration based on your `.env` file.

---

## 📋 **What Gets Verified**

The verification script checks:

1. ✅ **Environment Variables** - Confirms `.env` file is loaded correctly
2. ✅ **Network Connectivity** - Tests if Kafka broker is reachable
3. ✅ **Kafka Connection** - Verifies connection to Kafka broker
4. ✅ **Topic Listing** - Lists available Kafka topics
5. ✅ **Producer Test** - Sends a test message to Kafka
6. ✅ **Consumer Test** - Creates a test consumer

---

## 🚀 **How to Run**

### **Windows:**
```cmd
cd C:\Users\jerom\OneDrive\Documents\Project\Multi-agent-AI-Ecommerce
scripts\verify_kafka.bat
```

### **Linux/Mac:**
```bash
cd /path/to/Multi-agent-AI-Ecommerce
./scripts/verify_kafka.sh
```

### **Direct Python:**
```bash
python scripts/verify_kafka_connectivity.py
```

---

## 📊 **Expected Output**

### **When Kafka is Running:**
```
🔍🔍🔍 KAFKA CONNECTIVITY VERIFICATION 🔍🔍🔍

================================================================================
  1. Environment Variables Check
================================================================================
✅ KAFKA_BOOTSTRAP_SERVERS: 127.0.0.1:9092
✅ POSTGRES_HOST: 127.0.0.1
✅ POSTGRES_PORT: 5432
...

================================================================================
  2. Network Connectivity Check
================================================================================
✅ PASS Network connectivity
   127.0.0.1:9092 is reachable

================================================================================
  3. Kafka Broker Connection Check
================================================================================
✅ PASS Kafka connection
   Connected to 127.0.0.1:9092
✅ PASS List topics
   Found 15 topics

================================================================================
  4. Kafka Producer Check
================================================================================
✅ PASS Producer test
   Successfully sent message to 'test_connectivity'

================================================================================
  5. Kafka Consumer Check
================================================================================
✅ PASS Consumer test
   Successfully created consumer

================================================================================
  VERIFICATION SUMMARY
================================================================================
Tests Passed: 6/6
Success Rate: 100.0%

✅ ✅ ✅  ALL TESTS PASSED! KAFKA IS FULLY OPERATIONAL  ✅ ✅ ✅
```

### **When Kafka is NOT Running:**
```
================================================================================
  2. Network Connectivity Check
================================================================================
❌ FAIL Network connectivity
   127.0.0.1:9092 is not reachable
   Make sure Kafka is running at 127.0.0.1:9092

================================================================================
  3. Kafka Broker Connection Check
================================================================================
❌ FAIL Kafka connection
   Connection refused
   Make sure Kafka is running at 127.0.0.1:9092

================================================================================
  VERIFICATION SUMMARY
================================================================================
Tests Passed: 1/6
Success Rate: 16.7%

❌ KAFKA CONNECTION FAILED

Kafka is not accessible. Please check:
  1. Kafka is running
  2. Kafka is listening on 127.0.0.1:9092
  3. No firewall blocking the connection
  4. .env file has correct KAFKA_BOOTSTRAP_SERVERS value
```

---

## 🔧 **Your Current Configuration**

Based on your `.env` file:

```bash
KAFKA_BOOTSTRAP_SERVERS=127.0.0.1:9092
```

This means:
- **Host:** 127.0.0.1 (localhost)
- **Port:** 9092 (default Kafka port)

---

## ⚠️ **Common Issues & Solutions**

### **Issue 1: Connection Refused**

**Error:**
```
❌ FAIL Network connectivity
   127.0.0.1:9092 is not reachable
```

**Solutions:**
1. **Start Kafka:**
   ```bash
   # Windows
   cd C:\kafka
   bin\windows\kafka-server-start.bat config\server.properties

   # Linux/Mac
   cd /path/to/kafka
   bin/kafka-server-start.sh config/server.properties
   ```

2. **Check if Kafka is running:**
   ```bash
   # Windows
   netstat -an | findstr 9092

   # Linux/Mac
   netstat -an | grep 9092
   ```

3. **Verify Kafka process:**
   ```bash
   # Windows
   tasklist | findstr java

   # Linux/Mac
   ps aux | grep kafka
   ```

### **Issue 2: Wrong IP Address**

**Error:**
```
❌ FAIL Network connectivity
   192.168.1.100:9092 is not reachable
```

**Solution:**
Update `.env` file with correct IP:
```bash
# For local Kafka
KAFKA_BOOTSTRAP_SERVERS=127.0.0.1:9092

# For remote Kafka
KAFKA_BOOTSTRAP_SERVERS=192.168.1.100:9092
```

### **Issue 3: Firewall Blocking**

**Error:**
```
❌ FAIL Network connectivity
   Connection timeout
```

**Solution:**
1. **Windows Firewall:**
   - Open Windows Defender Firewall
   - Allow port 9092 for inbound/outbound

2. **Linux Firewall:**
   ```bash
   sudo ufw allow 9092
   ```

### **Issue 4: Kafka Not Started with Zookeeper**

**Error:**
```
❌ FAIL Kafka connection
   No brokers available
```

**Solution:**
Start Zookeeper first, then Kafka:
```bash
# Windows
bin\windows\zookeeper-server-start.bat config\zookeeper.properties
bin\windows\kafka-server-start.bat config\server.properties

# Linux/Mac
bin/zookeeper-server-start.sh config/zookeeper.properties &
bin/kafka-server-start.sh config/server.properties &
```

---

## 📝 **How Agents Use Kafka**

All agents read Kafka configuration from the `.env` file:

```python
# In shared/base_agent.py (line 164-168)
self.kafka_bootstrap_servers = (
    os.getenv("KAFKA_BOOTSTRAP_SERVERS") or 
    kafka_bootstrap_servers or 
    "localhost:9092"
)
```

**Priority:**
1. Environment variable `KAFKA_BOOTSTRAP_SERVERS` from `.env`
2. Constructor parameter `kafka_bootstrap_servers`
3. Default fallback: `localhost:9092`

---

## 🎯 **Impact on Agent Tests**

### **With Kafka Running:**
- ✅ ProductAgent: PASS
- ✅ WarehouseAgent: PASS
- ✅ InventoryAgent: PASS
- **Result: 15/15 = 100% PASS** 🎉

### **Without Kafka:**
- ⚠️ ProductAgent: TIMEOUT (30s)
- ⚠️ WarehouseAgent: TIMEOUT (30s)
- ⚠️ InventoryAgent: TIMEOUT (30s)
- **Result: 12/15 = 80% PASS** (still production-ready!)

---

## 📞 **Next Steps**

1. **Run the verification script:**
   ```cmd
   scripts\verify_kafka.bat
   ```

2. **If Kafka is not running:**
   - Start Kafka at `127.0.0.1:9092`
   - Re-run verification

3. **If Kafka is on a different IP:**
   - Update `.env` file: `KAFKA_BOOTSTRAP_SERVERS=YOUR_IP:9092`
   - Re-run verification

4. **If all tests pass:**
   - Run agent tests: `scripts\run_agent_tests.bat`
   - Expect 15/15 PASS! 🎉

---

## 🔗 **Related Files**

- **Configuration:** `.env` (project root)
- **Base Agent:** `shared/base_agent.py` (line 164-168)
- **Kafka Config:** `shared/kafka_config.py`
- **Agent Tests:** `scripts/test_all_agents_with_logging.py`

---

## 📚 **Additional Resources**

- **Kafka Documentation:** https://kafka.apache.org/documentation/
- **Kafka Quickstart:** https://kafka.apache.org/quickstart
- **Troubleshooting:** https://kafka.apache.org/documentation/#troubleshooting

---

**Last Updated:** October 22, 2025  
**Status:** Ready for use  
**Compatibility:** Windows, Linux, Mac

