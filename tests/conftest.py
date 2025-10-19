"""
Pytest configuration and shared fixtures.
"""

import pytest
import asyncio
import os
from typing import Generator
from dotenv import load_dotenv

from shared.database import DatabaseManager
from shared.models import DatabaseConfig


# Load environment variables from .env.test if it exists, otherwise from .env
if os.path.exists(".env.test"):
    load_dotenv(".env.test")
else:
    load_dotenv()


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def db_config() -> DatabaseConfig:
    """Create database configuration from environment variables."""
    return DatabaseConfig(
        host=os.getenv("DATABASE_HOST", "localhost"),
        port=int(os.getenv("DATABASE_PORT", "5432")),
        database=os.getenv("DATABASE_NAME", "multi_agent_ecommerce"),
        username=os.getenv("DATABASE_USER", "postgres"),
        password=os.getenv("DATABASE_PASSWORD", ""),
        pool_size=5,  # Smaller pool for testing
        max_overflow=10,
        echo=False  # Set to True for SQL debugging
    )


@pytest.fixture(scope="session")
async def db_manager(db_config: DatabaseConfig) -> DatabaseManager:
    """Create database manager for tests."""
    manager = DatabaseManager(db_config)
    await manager.initialize_async()
    
    # Test connection
    try:
        await manager.test_connection()
    except Exception as e:
        pytest.skip(f"Database connection failed: {e}")
    
    yield manager
    
    # Cleanup
    if manager.async_engine:
        await manager.async_engine.dispose()


@pytest.fixture
def sample_order_data():
    """Sample order data for testing."""
    return {
        "customer_id": "cust-123",
        "channel": "shopify",
        "channel_order_id": "order-456",
        "items": [
            {
                "product_id": "prod-789",
                "quantity": 2,
                "unit_price": 29.99,
                "total_price": 59.98
            }
        ],
        "shipping_address": {
            "street": "123 Test St",
            "city": "Test City",
            "postal_code": "12345",
            "country": "US"
        },
        "billing_address": {
            "street": "123 Test St",
            "city": "Test City",
            "postal_code": "12345",
            "country": "US"
        }
    }


@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return {
        "name": "Test Product",
        "description": "A test product description",
        "category": "Electronics",
        "brand": "TestBrand",
        "sku": "TEST-SKU-001",
        "price": 99.99,
        "cost": 50.00,
        "weight": 1.5,
        "dimensions": {
            "length": 10.0,
            "width": 5.0,
            "height": 3.0
        },
        "condition": "new"
    }

