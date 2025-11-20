# Docker PostgreSQL Database Migration Guide

## Quick Migration for Docker PostgreSQL

This guide shows you how to run the database migrations for the new world-class features when your PostgreSQL database is running in Docker.

---

## Method 1: Using Docker Exec (Recommended)

### Step 1: Find Your PostgreSQL Container

```bash
docker ps | grep postgres
```

You should see something like:
```
CONTAINER ID   IMAGE         COMMAND                  CREATED        STATUS        PORTS                    NAMES
abc123def456   postgres:15   "docker-entrypoint.s…"   2 days ago     Up 2 days     0.0.0.0:5432->5432/tcp   postgres_container
```

Note the **CONTAINER ID** or **NAMES** (e.g., `postgres_container`)

### Step 2: Copy Migration Files to Container

```bash
# Copy offers migration
docker cp database/migrations/add_offers_management.sql postgres_container:/tmp/

# Copy supplier migration
docker cp database/migrations/add_supplier_management.sql postgres_container:/tmp/
```

Replace `postgres_container` with your actual container name.

### Step 3: Execute Migrations

```bash
# Run offers migration
docker exec -i postgres_container psql -U your_username -d your_database_name -f /tmp/add_offers_management.sql

# Run supplier migration
docker exec -i postgres_container psql -U your_username -d your_database_name -f /tmp/add_supplier_management.sql
```

**Replace:**
- `postgres_container` with your container name
- `your_username` with your PostgreSQL username (often `postgres`)
- `your_database_name` with your database name

### Step 4: Verify Tables Created

```bash
docker exec -it postgres_container psql -U your_username -d your_database_name -c "\dt offers*"
docker exec -it postgres_container psql -U your_username -d your_database_name -c "\dt supplier*"
```

---

## Method 2: Using Docker Compose (If Using docker-compose.yml)

### Step 1: Find Your Service Name

Check your `docker-compose.yml` file for the PostgreSQL service name:

```yaml
services:
  postgres:  # <-- This is your service name
    image: postgres:15
    ...
```

### Step 2: Run Migrations via Docker Compose

```bash
# Copy files to container
docker-compose cp database/migrations/add_offers_management.sql postgres:/tmp/
docker-compose cp database/migrations/add_supplier_management.sql postgres:/tmp/

# Execute migrations
docker-compose exec postgres psql -U your_username -d your_database_name -f /tmp/add_offers_management.sql
docker-compose exec postgres psql -U your_username -d your_database_name -f /tmp/add_supplier_management.sql
```

---

## Method 3: Using Interactive Shell

### Step 1: Enter PostgreSQL Container

```bash
docker exec -it postgres_container bash
```

### Step 2: Connect to PostgreSQL

```bash
psql -U your_username -d your_database_name
```

### Step 3: Copy-Paste SQL

Open the migration files on your host machine and copy-paste the SQL commands directly into the psql prompt.

1. Open `database/migrations/add_offers_management.sql`
2. Copy all content (Ctrl+A, Ctrl+C)
3. Paste into psql prompt (Ctrl+V or right-click paste)
4. Press Enter
5. Repeat for `add_supplier_management.sql`

### Step 4: Exit

```bash
\q  # Exit psql
exit  # Exit container
```

---

## Method 4: Using Python Script (Automated)

I can create a Python migration script that automatically runs the migrations.

### Step 1: Create Migration Script

```python
# run_migrations.py
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Get database connection from environment
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'ecommerce_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

def run_migration(sql_file):
    """Run a SQL migration file"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Read and execute SQL file
        with open(sql_file, 'r') as f:
            sql = f.read()
            cursor.execute(sql)
        
        print(f"✅ Successfully executed: {sql_file}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error executing {sql_file}: {e}")
        raise

if __name__ == "__main__":
    print("Running database migrations...")
    
    # Run migrations
    run_migration('database/migrations/add_offers_management.sql')
    run_migration('database/migrations/add_supplier_management.sql')
    
    print("\n✅ All migrations completed successfully!")
```

### Step 2: Run the Script

```bash
python run_migrations.py
```

---

## Common Docker PostgreSQL Configurations

### Configuration 1: Default PostgreSQL Container

```bash
# Container name: postgres
# Username: postgres
# Database: postgres
# Port: 5432

docker exec -i postgres psql -U postgres -d postgres -f /tmp/add_offers_management.sql
```

### Configuration 2: Custom Named Container

```bash
# Container name: my_ecommerce_db
# Username: admin
# Database: ecommerce_db
# Port: 5432

docker exec -i my_ecommerce_db psql -U admin -d ecommerce_db -f /tmp/add_offers_management.sql
```

### Configuration 3: Docker Compose with Custom Names

```bash
# Service name: db
# Username: ecommerce_user
# Database: ecommerce_production
# Port: 5432

docker-compose exec db psql -U ecommerce_user -d ecommerce_production -f /tmp/add_offers_management.sql
```

---

## Troubleshooting

### Issue: "No such container"

**Solution:** Check your container name/ID:
```bash
docker ps -a | grep postgres
```

### Issue: "FATAL: password authentication failed"

**Solution:** Check your PostgreSQL password:
```bash
# If using environment variables
docker exec -it postgres_container env | grep POSTGRES

# Or check docker-compose.yml for credentials
```

### Issue: "database does not exist"

**Solution:** List available databases:
```bash
docker exec -it postgres_container psql -U postgres -c "\l"
```

### Issue: "permission denied"

**Solution:** Use the correct PostgreSQL user (usually `postgres`):
```bash
docker exec -it postgres_container psql -U postgres -d your_database_name
```

### Issue: "file not found"

**Solution:** Verify the file was copied:
```bash
docker exec -it postgres_container ls -la /tmp/
```

---

## Verification Commands

After running migrations, verify everything is set up correctly:

### Check Tables Exist

```bash
# Check offers tables
docker exec -it postgres_container psql -U your_username -d your_database_name -c "
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'offer%'
ORDER BY table_name;
"

# Check supplier tables
docker exec -it postgres_container psql -U your_username -d your_database_name -c "
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'supplier%'
ORDER BY table_name;
"
```

### Check Table Structures

```bash
# Check offers table structure
docker exec -it postgres_container psql -U your_username -d your_database_name -c "\d offers"

# Check suppliers table structure
docker exec -it postgres_container psql -U your_username -d your_database_name -c "\d suppliers"
```

### Count Rows (Should be 0 initially)

```bash
docker exec -it postgres_container psql -U your_username -d your_database_name -c "
SELECT 
  'offers' as table_name, COUNT(*) as row_count FROM offers
UNION ALL
SELECT 'suppliers', COUNT(*) FROM suppliers
UNION ALL
SELECT 'purchase_orders', COUNT(*) FROM purchase_orders;
"
```

---

## Quick Reference: One-Line Migration

If you know your exact configuration, use this one-liner:

```bash
# Replace with your values
CONTAINER_NAME="postgres_container"
DB_USER="postgres"
DB_NAME="ecommerce_db"

# Copy and execute both migrations
docker cp database/migrations/add_offers_management.sql $CONTAINER_NAME:/tmp/ && \
docker cp database/migrations/add_supplier_management.sql $CONTAINER_NAME:/tmp/ && \
docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -f /tmp/add_offers_management.sql && \
docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -f /tmp/add_supplier_management.sql && \
echo "✅ Migrations completed!"
```

---

## Environment Variables

Make sure your `.env` file has the correct Docker PostgreSQL connection:

```env
# Database Configuration (Docker)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ecommerce_db
DB_USER=postgres
DB_PASSWORD=your_password_here

# Or use connection URL
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/ecommerce_db
```

---

## Next Steps After Migration

1. ✅ Verify tables are created (see verification commands above)
2. ✅ Start the Offers Agent: `python agents/offers_agent_v3.py`
3. ✅ Test the API: `curl http://localhost:8040/health`
4. ✅ Access the UI: http://localhost:5173/merchant/offers

---

## Need Help?

If you encounter any issues:

1. Check Docker container is running: `docker ps`
2. Check PostgreSQL logs: `docker logs postgres_container`
3. Verify database credentials in `.env` file
4. Try the interactive shell method (Method 3)
5. Check the main implementation guide: `WORLD_CLASS_FEATURES_IMPLEMENTATION_GUIDE.md`

---

**Last Updated:** November 20, 2024  
**Compatible with:** PostgreSQL 12+, Docker 20+, Docker Compose 2+
