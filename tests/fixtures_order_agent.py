"""
Test Fixtures for Order Agent Enhanced Tests

Provides properly configured fixtures for testing Order Agent enhancements.
"""

import os
import pytest
from unittest.mock import Mock, AsyncMock

from shared.database import DatabaseManager
from shared.models import DatabaseConfig
from shared.order_repository_extended import OrderRepositoryFacade
from agents.services.order_service import EnhancedOrderService


@pytest.fixture
def db_config():
    """Create database configuration from environment variables."""
    return DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "multi_agent_ecommerce"),
        username=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres123"),
        pool_size=5,
        max_overflow=10,
        echo=False
    )


@pytest.fixture
async def db_manager(db_config):
    """Create and initialize database manager."""
    manager = DatabaseManager(db_config)
    manager.initialize_async()
    
    # Create tables if they don't exist
    async with manager.async_engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: None)  # Just verify connection
    
    yield manager
    
    # Cleanup
    if manager.async_engine:
        await manager.async_engine.dispose()


@pytest.fixture
def order_repos(db_manager):
    """Create order repository facade."""
    return OrderRepositoryFacade(db_manager)


@pytest.fixture
def order_service(order_repos):
    """Create enhanced order service."""
    return EnhancedOrderService(order_repos)


@pytest.fixture
def sample_order_id():
    """Provide a sample order ID for testing."""
    return "ORD-TEST-001"


@pytest.fixture
def sample_user_id():
    """Provide a sample user ID for testing."""
    return "USER-TEST-001"


@pytest.fixture
def sample_warehouse_id():
    """Provide a sample warehouse ID for testing."""
    return "WH-001"

