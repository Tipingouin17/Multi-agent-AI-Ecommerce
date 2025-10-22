# Agent Testing Scripts

This directory contains scripts for testing and validating the Multi-Agent E-Commerce System in production/staging environments.

## Quick Start

### Windows
```cmd
cd Multi-agent-AI-Ecommerce
scripts\run_agent_tests.bat
```

### Linux/Mac
```bash
cd Multi-agent-AI-Ecommerce
./scripts/run_agent_tests.sh
```

## What the Test Does

The test script (`test_all_agents_with_logging.py`) performs the following checks on each agent:

1. **Import Test** - Verifies the agent module can be imported
2. **Instantiation Test** - Verifies the agent can be instantiated
3. **Method Check** - Verifies required abstract methods exist:
   - `initialize()`
   - `cleanup()`
   - `process_business_logic()`
4. **Initialization Test** - Attempts to initialize the agent (30s timeout)
5. **Cleanup Test** - Attempts to cleanup agent resources (10s timeout)

## Output Files

All logs are saved to the `logs/` directory:

### Main Log File
- **Location**: `logs/agent_startup_YYYYMMDD_HHMMSS.log`
- **Content**: Complete test execution log with all agents

### Individual Agent Logs
- **Location**: `logs/agents/AGENT_NAME_YYYYMMDD_HHMMSS.log`
- **Content**: Detailed logs for each specific agent

### Summary JSON
- **Location**: `logs/summary_YYYYMMDD_HHMMSS.json`
- **Content**: Machine-readable test results in JSON format

Example summary structure:
```json
{
  "timestamp": "20251022_120000",
  "total_agents": 15,
  "passed": 10,
  "failed": 3,
  "partial": 2,
  "critical_agents": {
    "total": 10,
    "passed": 8,
    "failed": 2
  },
  "agents": [
    {
      "name": "OrderAgent",
      "status": "✅ PASS",
      "import_success": true,
      "instantiate_success": true,
      "initialize_success": true,
      "cleanup_success": true,
      "errors": [],
      "warnings": [],
      "log_file": "logs/agents/OrderAgent_20251022_120000.log"
    }
  ]
}
```

## Exit Codes

- **0** - All tests passed
- **1** - Some tests failed
- **2** - Partial success (some warnings)
- **130** - Test interrupted by user (Ctrl+C)

## Prerequisites

### Required Services

The agents require the following services to be running:

1. **Apache Kafka**
   - Default: `localhost:9092`
   - Configure via `KAFKA_BOOTSTRAP_SERVERS` environment variable

2. **PostgreSQL**
   - Default: `localhost:5432`
   - Configure via `DATABASE_URL` environment variable

3. **Redis** (optional, for some agents)
   - Default: `localhost:6379`
   - Configure via `REDIS_URL` environment variable

### Environment Variables

Create a `.env` file in the project root with:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ecommerce

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Agent Configuration
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### Python Dependencies

Install all required dependencies:

```bash
pip install -r requirements.txt
```

## Common Issues and Solutions

### Issue: "Initialization timeout (30s)"

**Cause**: Agent is waiting for Kafka or PostgreSQL connection

**Solutions**:
1. Ensure Kafka is running: `docker ps | grep kafka`
2. Ensure PostgreSQL is running: `docker ps | grep postgres`
3. Check connection strings in `.env` file
4. Verify network connectivity to services

### Issue: "Import failed: ModuleNotFoundError"

**Cause**: Missing Python dependencies

**Solution**:
```bash
pip install -r requirements.txt
```

### Issue: "Missing cleanup() method"

**Cause**: Agent doesn't implement required abstract method

**Solution**: This should not happen after the fixes. If it does, the agent file may have been modified. Check git status:
```bash
git status
git diff agents/AGENT_NAME.py
```

## Docker Compose Setup (Recommended)

For testing with all required services, use Docker Compose:

```bash
# Start all services
docker-compose up -d

# Wait for services to be ready
sleep 10

# Run tests
./scripts/run_agent_tests.sh

# Stop services
docker-compose down
```

## Continuous Integration

To integrate with CI/CD pipelines:

```yaml
# .github/workflows/test-agents.yml
name: Test Agents

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      kafka:
        image: confluentinc/cp-kafka:latest
        env:
          KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run agent tests
        run: python scripts/test_all_agents_with_logging.py
      
      - name: Upload logs
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: agent-logs
          path: logs/
```

## Troubleshooting

### Enable Debug Logging

Edit `scripts/test_all_agents_with_logging.py` and change:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Already set to DEBUG
    ...
)
```

### Test Individual Agent

```python
import asyncio
from scripts.test_all_agents_with_logging import AgentTester

agent_config = {
    "name": "OrderAgent",
    "module": "agents.order_agent_production",
    "class": "OrderAgent",
    "priority": "critical",
    "init_kwargs": {}
}

tester = AgentTester(agent_config)
results = asyncio.run(tester.test_agent())
print(results)
```

### Check Service Connectivity

```bash
# Test PostgreSQL
psql -h localhost -U postgres -d ecommerce -c "SELECT 1"

# Test Kafka
kafka-console-producer.sh --broker-list localhost:9092 --topic test

# Test Redis
redis-cli ping
```

## Support

If you encounter issues:

1. Check the logs in `logs/` directory
2. Review the summary JSON for detailed error messages
3. Verify all prerequisites are met
4. Check environment variables in `.env`
5. Ensure all services (Kafka, PostgreSQL) are running

For additional help, create an issue in the GitHub repository with:
- The summary JSON file
- Relevant agent log files
- Your environment details (OS, Python version, etc.)

