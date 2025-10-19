# 🐘 PostgreSQL Setup Guide for Windows

## 🎉 Good News!
The error `[WinError 1225] The remote computer refused the network connection` means your Multi-Agent system is working correctly - it's just that PostgreSQL isn't running or configured yet.

## 📥 Step 1: Install PostgreSQL

### Download and Install
1. **Download PostgreSQL 15 or 16** from: https://www.postgresql.org/download/windows/
2. **Run the installer** as Administrator
3. **During installation**:
   - ✅ Keep default port: `5432`
   - ✅ Set a **strong password** for the `postgres` user (remember this!)
   - ✅ Keep default locale settings
   - ✅ Install pgAdmin (recommended for database management)

### Installation Options
- **Components**: Install PostgreSQL Server, pgAdmin, Command Line Tools
- **Data Directory**: Use default location
- **Port**: 5432 (default)
- **Locale**: Default

## ⚙️ Step 2: Configure PostgreSQL

### Start PostgreSQL Service
1. **Open Services** (Windows + R, type `services.msc`)
2. **Find "postgresql-x64-15"** (or similar)
3. **Right-click** → **Start** (if not running)
4. **Set to "Automatic"** for auto-start

### Alternative: Start via Command Line
```cmd
# Open Command Prompt as Administrator
net start postgresql-x64-15
```

## 🔧 Step 3: Create Database

### Method 1: Using Command Line
```cmd
# Open Command Prompt
# Navigate to PostgreSQL bin directory (usually):
cd "C:\Program Files\PostgreSQL\15\bin"

# Connect to PostgreSQL
psql -U postgres -h localhost

# Enter your password when prompted
# Then create the database:
CREATE DATABASE multi_agent_ecommerce;

# Exit PostgreSQL
\q
```

### Method 2: Using pgAdmin
1. **Open pgAdmin** (installed with PostgreSQL)
2. **Connect to PostgreSQL Server**
   - Host: `localhost`
   - Port: `5432`
   - Username: `postgres`
   - Password: (your password)
3. **Right-click "Databases"** → **Create** → **Database**
4. **Name**: `multi_agent_ecommerce`
5. **Click "Save"**

## 📝 Step 4: Update Configuration

### Edit .env File
```cmd
# Open your .env file
notepad .env
```

### Update Database Settings
```env
# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=multi_agent_ecommerce
DATABASE_USER=postgres
DATABASE_PASSWORD=your_actual_password_here
```

**⚠️ Important**: Replace `your_actual_password_here` with the password you set during PostgreSQL installation.

## 🧪 Step 5: Test Connection

### Test Database Connection
```cmd
# Test connection using psql
psql -h localhost -U postgres -d multi_agent_ecommerce

# If successful, you'll see:
# multi_agent_ecommerce=#

# Exit with:
\q
```

### Test Multi-Agent System
```cmd
# Test the system health
python run_cli.py health

# Initialize database tables
init-database.bat

# Check system status
check-status.bat
```

## 🔍 Troubleshooting

### Issue: "psql: command not found"
**Solution**: Add PostgreSQL to PATH
1. **Open System Properties** → **Environment Variables**
2. **Edit PATH** variable
3. **Add**: `C:\Program Files\PostgreSQL\15\bin`
4. **Restart Command Prompt**

### Issue: "Connection refused"
**Solutions**:
1. **Check PostgreSQL is running**:
   ```cmd
   # Check service status
   sc query postgresql-x64-15
   
   # Start if stopped
   net start postgresql-x64-15
   ```

2. **Check firewall**:
   - Allow PostgreSQL through Windows Firewall
   - Port 5432 should be open

3. **Check configuration**:
   - Verify `.env` file has correct password
   - Ensure database name is correct

### Issue: "Authentication failed"
**Solutions**:
1. **Reset postgres password**:
   ```cmd
   # As Administrator
   psql -U postgres
   ALTER USER postgres PASSWORD 'new_password';
   ```

2. **Update .env file** with new password

### Issue: "Database does not exist"
**Solution**: Create the database
```sql
-- Connect as postgres user
psql -U postgres -h localhost

-- Create database
CREATE DATABASE multi_agent_ecommerce;

-- Verify creation
\l

-- Exit
\q
```

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] PostgreSQL service is running
- [ ] Can connect with `psql -U postgres -h localhost`
- [ ] Database `multi_agent_ecommerce` exists
- [ ] `.env` file has correct credentials
- [ ] `python run_cli.py health` shows database connection OK
- [ ] `init-database.bat` runs without errors

## 🚀 Next Steps

Once PostgreSQL is set up:

1. **Initialize database**:
   ```cmd
   init-database.bat
   ```

2. **Check system health**:
   ```cmd
   check-health.bat
   ```

3. **Start the system**:
   ```cmd
   start-system.bat
   ```

## 📊 Database Management

### Using pgAdmin (Recommended)
- **Connect**: localhost:5432, user: postgres
- **View tables**: Navigate to multi_agent_ecommerce → Schemas → public → Tables
- **Run queries**: Use Query Tool
- **Monitor**: Check server activity and logs

### Using Command Line
```cmd
# Connect to database
psql -U postgres -h localhost -d multi_agent_ecommerce

# List tables
\dt

# View table structure
\d customers

# Run queries
SELECT * FROM customers LIMIT 5;

# Exit
\q
```

## 🔒 Security Notes

- **Use strong passwords** for the postgres user
- **Don't use default passwords** in production
- **Configure firewall** to restrict database access
- **Regular backups** of your database
- **Keep PostgreSQL updated**

---

**💡 Once PostgreSQL is running, your Multi-Agent system will work perfectly with real database operations!**
