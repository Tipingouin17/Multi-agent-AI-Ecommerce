# Launch Scripts Documentation

This document provides comprehensive information about the launch scripts created for the Multi-Agent AI E-commerce Platform.

## Overview

Two unified launch scripts have been created to simplify the startup process across different operating systems:

- **`launch.sh`** - For Linux and macOS systems
- **`launch.ps1`** - For Windows systems with PowerShell

These scripts automate the entire setup and launch process, including:
- Dependency installation
- Environment configuration
- Infrastructure service startup (PostgreSQL, Kafka, Redis, monitoring tools)
- Database initialization
- Kafka topic creation

## Quick Start

### Linux / macOS

```bash
# Make the script executable (first time only)
chmod +x launch.sh

# Launch the system
./launch.sh

# Launch with development tools (pgAdmin, Kafka UI)
./launch.sh --dev

# Check system status
./launch.sh --status

# Stop all services
./launch.sh --stop
```

### Windows

```powershell
# Launch the system
.\launch.ps1

# Launch with development tools (pgAdmin, Kafka UI)
.\launch.ps1 -Dev

# Check system status
.\launch.ps1 -Status

# Stop all services
.\launch.ps1 -Stop
```

## Script Options

### Linux/macOS (`launch.sh`)

| Option | Description |
|--------|-------------|
| `--skip-deps` | Skip Python dependency installation (faster restarts) |
| `--skip-db` | Skip database initialization (if already initialized) |
| `--dev` | Start with development tools (pgAdmin, Kafka UI) |
| `--stop` | Stop all running services |
| `--status` | Check the status of all services |
| `--help` | Display help information |

### Windows (`launch.ps1`)

| Option | Description |
|--------|-------------|
| `-SkipDeps` | Skip Python dependency installation (faster restarts) |
| `-SkipDb` | Skip database initialization (if already initialized) |
| `-Dev` | Start with development tools (pgAdmin, Kafka UI) |
| `-Stop` | Stop all running services |
| `-Status` | Check the status of all services |

## What the Scripts Do

### 1. Prerequisites Check

The scripts verify that all required software is installed:
- Python 3.9+
- Docker and Docker Compose
- Git

If any prerequisites are missing, the script will exit with an error message.

### 2. Python Environment Setup

- Creates a virtual environment (if it doesn't exist)
- Activates the virtual environment
- Installs all Python dependencies from `requirements.txt`
- Installs the project in editable mode

### 3. Environment Configuration

- Checks for the existence of a `.env` file
- Creates a `.env` file from a template if it doesn't exist
- Reminds you to add your OpenAI API key if needed

### 4. Infrastructure Services

Starts all required infrastructure services using Docker Compose:
- **PostgreSQL** - Database (port 5432)
- **Redis** - Cache (port 6379)
- **Kafka** - Message broker (port 9092)
- **Zookeeper** - Kafka coordination (port 2181)
- **Prometheus** - Metrics collection (port 9090)
- **Grafana** - Monitoring dashboard (port 3000)
- **Loki** - Log aggregation (port 3100)
- **Promtail** - Log shipper
- **Nginx** - Reverse proxy (ports 80, 443)

With `--dev` or `-Dev` flag, additional development tools are started:
- **Kafka UI** - Kafka management interface (port 8080)
- **pgAdmin** - PostgreSQL management (port 5050)

### 5. Database Initialization

- Runs `init_database.py` to create all database tables
- Runs `init_kafka_topics.py` to create all Kafka topics

### 6. Completion Summary

Displays all access points and next steps for using the system.

## Access Points

After successful launch, you can access:

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana Dashboard | http://localhost:3000 | admin / admin123 |
| Prometheus | http://localhost:9090 | - |
| PostgreSQL | localhost:5432 | postgres / postgres123 |
| Redis | localhost:6379 | password: redis123 |
| Kafka | localhost:9092 | - |

### Development Tools (with `--dev` or `-Dev`)

| Service | URL | Credentials |
|---------|-----|-------------|
| Kafka UI | http://localhost:8080 | - |
| pgAdmin | http://localhost:5050 | admin@multiagent.com / admin123 |

## Next Steps After Launch

1. **Start the agents:**
   ```bash
   python3 agents/start_agents.py
   ```

2. **View service logs:**
   ```bash
   cd infrastructure
   docker-compose logs -f [service-name]
   ```

3. **Access API documentation:**
   - Each agent exposes FastAPI documentation at `http://localhost:[port]/docs`
   - Order Agent: http://localhost:8000/docs
   - Product Agent: http://localhost:8001/docs

## Troubleshooting

### Docker Not Running

**Error:** `Cannot connect to the Docker daemon`

**Solution:** Start Docker Desktop and wait for it to fully initialize.

### Port Already in Use

**Error:** `Port 5432 is already allocated`

**Solution:** Stop any existing PostgreSQL, Kafka, or Redis services running on your system, or modify the ports in `infrastructure/docker-compose.yml`.

### Permission Denied (Linux/macOS)

**Error:** `Permission denied: './launch.sh'`

**Solution:** Make the script executable:
```bash
chmod +x launch.sh
```

### Execution Policy Error (Windows)

**Error:** `cannot be loaded because running scripts is disabled`

**Solution:** Run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Services Not Healthy

If services show as "unhealthy" after launch, wait a few more minutes. Some services (especially Kafka) take time to fully initialize. You can check logs:

```bash
cd infrastructure
docker-compose logs [service-name]
```

## Faster Restarts

If you've already set up the system once and want to restart it quickly:

```bash
# Linux/macOS
./launch.sh --skip-deps --skip-db

# Windows
.\launch.ps1 -SkipDeps -SkipDb
```

This skips dependency installation and database initialization, significantly reducing startup time.

## Stopping the System

To cleanly stop all services:

```bash
# Linux/macOS
./launch.sh --stop

# Windows
.\launch.ps1 -Stop
```

This stops and removes all Docker containers while preserving data in volumes.

## Repository Organization

A separate script `organize_repository.sh` has been created to clean up the repository by moving historical documentation files to an `old/` folder. This keeps the root directory clean and focused on essential documentation.

### Files Kept in Root

- `README.md` - Main project documentation
- `COMPLETE_STARTUP_GUIDE.md` - Detailed startup guide
- `DEPLOYMENT_GUIDE.md` - Deployment instructions
- `TESTING_GUIDE.md` - Testing guidelines
- `CHANGELOG.md` - Version history
- `launch.sh` - Linux/macOS launch script
- `launch.ps1` - Windows launch script

### Files Moved to `old/`

All progress reports, fix guides, implementation summaries, and historical documentation have been moved to the `old/` directory for reference.

## Support

For more detailed information, refer to:
- `README.md` - Project overview
- `COMPLETE_STARTUP_GUIDE.md` - Step-by-step manual setup
- `DEPLOYMENT_GUIDE.md` - Production deployment
- `TESTING_GUIDE.md` - Testing procedures

---

**Happy launching!** 🚀

