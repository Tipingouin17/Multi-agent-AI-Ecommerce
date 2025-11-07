# Testing Guide for Multi-Agent E-commerce System

## Overview

This guide explains how to run the comprehensive test suite for the Multi-Agent E-commerce System, with special focus on the Order Agent enhancements.

## Prerequisites

### Required Services

Before running tests, ensure the following services are running:

1. **PostgreSQL 18** - Database must be running on `localhost:5432`
2. **Kafka** (optional for unit tests) - Required for integration tests
3. **Redis** (optional for unit tests) - Required for integration tests

### Environment Configuration

The test suite uses environment variables for configuration. You have two options:

#### Option 1: Use .env.test (Recommended for Testing)

The repository includes a `.env.test` file with test-specific configuration:

```bash
# Database Configuration (Test Database)
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=multi_agent_ecommerce
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
```

**Note:** The test suite automatically loads `.env.test` if it exists, otherwise falls back to `.env`.

#### Option 2: Use .env (Production Configuration)

Copy `.env.example` to `.env` and configure with your actual database credentials:

```bash
cp .env.example .env
# Edit .env with your database password
```

## Running Tests

### Install Dependencies

First, ensure all Python dependencies are installed:

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run Order Agent Tests Only

```bash
pytest tests/test_order_agent_enhanced.py -v
```

### Run Specific Test

```bash
pytest tests/test_order_agent_enhanced.py::test_modify_order_field -v
```

### Run Tests by Marker

The test suite includes custom markers for different test categories:

```bash
# Run only unit tests (fast, isolated)
pytest -m unit

# Run only integration tests (require services)
pytest -m integration

# Run only async tests
pytest -m asyncio

# Skip slow tests
pytest -m "not slow"
```

### Run Tests with Coverage

```bash
pytest --cov=agents --cov=shared --cov-report=html --cov-report=term-missing
```

This generates an HTML coverage report in `htmlcov/index.html`.

## Test Structure

### Order Agent Test Suite

The Order Agent test suite (`tests/test_order_agent_enhanced.py`) covers:

1. **Order Modifications** - Track field-level changes
2. **Order Splitting** - Split orders across warehouses
3. **Partial Shipments** - Handle multi-shipment orders
4. **Fulfillment Planning** - Optimize fulfillment strategies
5. **Delivery Tracking** - Track delivery attempts and status
6. **Cancellations** - Process cancellation requests and reviews
7. **Notes and Tags** - Manage order annotations
8. **Timeline Events** - Track order history

### Fixtures

The test suite uses pytest fixtures defined in `tests/conftest.py`:

- `db_config` - Database configuration from environment variables
- `db_manager` - Initialized DatabaseManager instance
- `order_service` - EnhancedOrderService instance for testing
- `sample_order_data` - Sample order data for testing
- `sample_product_data` - Sample product data for testing

## Troubleshooting

### Database Connection Failed

If tests are skipped with "Database connection failed" message:

1. Verify PostgreSQL is running:
   ```bash
   # Windows
   Get-Service postgresql*
   
   # Linux
   sudo systemctl status postgresql
   ```

2. Check database credentials in `.env.test` or `.env`

3. Verify database exists:
   ```sql
   psql -U postgres -c "\l"
   ```

4. Run database initialization if needed:
   ```bash
   python init_database.py
   ```

### Import Errors

If you encounter import errors:

1. Ensure you're in the project root directory
2. Verify all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

3. Check Python path includes the project directory:
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

### Async Test Issues

If async tests fail or hang:

1. Verify `pytest-asyncio` is installed:
   ```bash
   pip install pytest-asyncio
   ```

2. Check `pytest.ini` has `asyncio_mode = auto`

3. Ensure fixtures use proper async/await syntax

## Test Database Setup

For isolated testing, you may want to use a separate test database:

```sql
-- Create test database
CREATE DATABASE multi_agent_ecommerce_test;

-- Run migrations
psql -U postgres -d multi_agent_ecommerce_test -f database/migrations/001_initial_schema.sql
psql -U postgres -d multi_agent_ecommerce_test -f database/migrations/002_order_agent_enhancements.sql
```

Then update `.env.test`:

```bash
DATABASE_NAME=multi_agent_ecommerce_test
```

## Continuous Integration

The test suite is designed to work in CI/CD pipelines. Example GitHub Actions workflow:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:18
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: multi_agent_ecommerce_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## Best Practices

1. **Run tests frequently** during development
2. **Use markers** to categorize tests appropriately
3. **Mock external services** in unit tests
4. **Use fixtures** to avoid code duplication
5. **Write descriptive test names** that explain what is being tested
6. **Add docstrings** to test functions explaining the test scenario
7. **Clean up test data** in fixture teardown
8. **Use parametrize** for testing multiple scenarios

## Next Steps

After Order Agent tests pass:

1. Review test coverage report
2. Add additional test cases for edge cases
3. Move to Phase 2: Product Agent enhancement
4. Follow the same testing pattern for all agents

## Support

For issues or questions about testing:

1. Check the test output for detailed error messages
2. Review the test file comments and docstrings
3. Consult the main README.md for system architecture
4. Check AGENT_IMPLEMENTATION_MASTER_PLAN.md for implementation details

