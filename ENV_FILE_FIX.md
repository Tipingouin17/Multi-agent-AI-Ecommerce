# .env File Fix Guide

## Issue Found

Your `.env` file is **missing the `DATABASE_URL`** variable, which is required by many agents.

## Quick Fix

Add this line to your `.env` file:

```env
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/multi_agent_ecommerce
```

## Complete .env File

Your `.env` file should have ALL of these variables:

```env
# ============================================================================
# Database Configuration
# ============================================================================

# Individual components (used by some agents)
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=multi_agent_ecommerce
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres123

# Alternative names (used by other agents)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=multi_agent_ecommerce
DB_USER=postgres
DB_PASSWORD=postgres123

# Full connection string (REQUIRED - used by most agents)
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/multi_agent_ecommerce

# ============================================================================
# Kafka Configuration
# ============================================================================

KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# ============================================================================
# Redis Configuration
# ============================================================================

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379

# ============================================================================
# OpenAI Configuration (Optional)
# ============================================================================

# Only needed if you want AI-powered features
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# ============================================================================
# Environment
# ============================================================================

ENVIRONMENT=development
DEBUG=true

# ============================================================================
# Agent Ports (Optional - agents have defaults)
# ============================================================================

ORDER_AGENT_PORT=8001
INVENTORY_AGENT_PORT=8002
PRODUCT_AGENT_PORT=8003
PAYMENT_AGENT_PORT=8004
WAREHOUSE_AGENT_PORT=8005
TRANSPORT_AGENT_PORT=8006
MARKETPLACE_AGENT_PORT=8007
CUSTOMER_AGENT_PORT=8008
AFTERSALES_AGENT_PORT=8009
QUALITY_AGENT_PORT=8010
BACKOFFICE_AGENT_PORT=8011
FRAUD_AGENT_PORT=8012
DOCUMENTS_AGENT_PORT=8013
KNOWLEDGE_AGENT_PORT=8020
RISK_AGENT_PORT=8021
```

## Step-by-Step Fix

### 1. Backup Your Current .env
```powershell
Copy-Item .env .env.backup
```

### 2. Add Missing Variables

Open your `.env` file and add these lines:

```env
# Add these if missing:
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/multi_agent_ecommerce
DB_HOST=localhost
DB_PORT=5432
DB_NAME=multi_agent_ecommerce
DB_USER=postgres
DB_PASSWORD=postgres123
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379
ENVIRONMENT=development
```

### 3. Verify Your .env File

Your `.env` should now have at minimum:

- ✅ `DATABASE_HOST`
- ✅ `DATABASE_PORT`
- ✅ `DATABASE_NAME`
- ✅ `DATABASE_USER`
- ✅ `DATABASE_PASSWORD`
- ✅ `DATABASE_URL` ← **This was missing!**
- ✅ `DB_HOST`
- ✅ `DB_PORT`
- ✅ `DB_NAME`
- ✅ `DB_USER`
- ✅ `DB_PASSWORD`
- ✅ `KAFKA_BOOTSTRAP_SERVERS`
- ✅ `REDIS_HOST`
- ✅ `REDIS_PORT`

### 4. Restart Everything

After updating `.env`:

```powershell
.\shutdown-all.ps1
.\setup-and-launch.ps1
```

## Why This Matters

Different agents use different variable names:

| Agent | Uses |
|-------|------|
| Order, Product, Payment | `DATABASE_URL` |
| Inventory, Warehouse | `DB_HOST`, `DB_PORT`, etc. |
| Fraud, Risk | `DATABASE_URL` |
| Quality, Knowledge | `DB_*` variables |

By having **both formats**, you ensure all agents can connect.

## Testing

After fixing, test the connection:

```powershell
# Test from Docker
docker exec multi-agent-postgres psql -U postgres -d multi_agent_ecommerce -c "SELECT 1;"

# Test from Python
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('DATABASE_URL'))"
```

## Common Mistakes

### ❌ Wrong: Missing DATABASE_URL
```env
DATABASE_HOST=localhost
DATABASE_PORT=5432
# Missing: DATABASE_URL
```

### ✅ Correct: Has both formats
```env
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/multi_agent_ecommerce
```

### ❌ Wrong: Password mismatch
```env
DATABASE_PASSWORD=postgres      # .env says postgres
# But docker-compose uses postgres123
```

### ✅ Correct: Passwords match
```env
DATABASE_PASSWORD=postgres123   # Matches docker-compose
DATABASE_URL=postgresql://postgres:postgres123@...
```

## Verification Checklist

After fixing your `.env` file:

- [ ] `.env` file has `DATABASE_URL`
- [ ] Password in `DATABASE_URL` matches `DATABASE_PASSWORD`
- [ ] Password matches docker-compose.yml
- [ ] All required variables present
- [ ] No typos in variable names
- [ ] Restarted all services
- [ ] Agents can connect to database

## Still Not Working?

If you still can't connect after fixing `.env`:

1. **Check Docker container:**
   ```powershell
   docker logs multi-agent-postgres --tail 20
   ```

2. **Test connection:**
   ```powershell
   .\scripts\fix_postgres_connection.ps1
   ```

3. **Verify password:**
   ```powershell
   docker exec multi-agent-postgres psql -U postgres -d multi_agent_ecommerce -c "SELECT 1;"
   # If this fails, password is wrong in docker-compose
   ```

---

**Summary:** Add `DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/multi_agent_ecommerce` to your `.env` file and restart!

