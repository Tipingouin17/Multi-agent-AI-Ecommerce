"""
Unit tests for database operations.
"""

import pytest
from datetime import datetime
from decimal import Decimal

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.database import DatabaseManager
from shared.models import (
    DatabaseConfig, ProductBase, OrderStatus, ProductCondition,
    ChannelType
)


@pytest.fixture
def db_config():
    """Create test database configuration."""
    return DatabaseConfig(
        host="localhost",
        port=5432,
        database="test_multi_agent_ecommerce",
        username="postgres",
        password="test_password",
        pool_size=5,
        max_overflow=10,
        echo=False
    )


@pytest.fixture
def db_manager(db_config):
    """Create database manager instance."""
    return DatabaseManager(db_config)


class TestDatabaseConfig:
    """Test cases for DatabaseConfig."""
    
    def test_database_config_creation(self, db_config):
        """Test database configuration creation."""
        assert db_config.host == "localhost"
        assert db_config.port == 5432
        assert db_config.database == "test_multi_agent_ecommerce"
        assert db_config.username == "postgres"
        assert db_config.pool_size == 5
    
    def test_database_url_generation(self, db_config):
        """Test database URL generation."""
        expected_url = "postgresql://postgres:test_password@localhost:5432/test_multi_agent_ecommerce"
        assert db_config.url == expected_url


class TestDatabaseManager:
    """Test cases for DatabaseManager."""
    
    def test_database_manager_initialization(self, db_manager):
        """Test database manager initialization."""
        assert db_manager.config is not None
        assert db_manager.sync_engine is None
        assert db_manager.async_engine is None
        assert not db_manager._initialized
    
    def test_sync_engine_initialization(self, db_manager):
        """Test synchronous engine initialization."""
        db_manager.initialize_sync()
        
        assert db_manager.sync_engine is not None
        assert db_manager.sync_session_factory is not None


class TestModels:
    """Test cases for data models."""
    
    def test_product_base_model(self):
        """Test ProductBase model creation."""
        product = ProductBase(
            name="Test Product",
            description="A test product",
            category="Electronics",
            brand="TestBrand",
            sku="TEST-001",
            price=Decimal("99.99"),
            cost=Decimal("50.00"),
            weight=Decimal("1.5"),
            dimensions={"length": 10.0, "width": 5.0, "height": 3.0},
            condition=ProductCondition.NEW
        )
        
        assert product.name == "Test Product"
        assert product.sku == "TEST-001"
        assert product.price == Decimal("99.99")
        assert product.condition == ProductCondition.NEW
    
    def test_product_price_validation(self):
        """Test product price validation."""
        with pytest.raises(ValueError, match="Price and cost must be positive"):
            ProductBase(
                name="Test Product",
                category="Electronics",
                brand="TestBrand",
                sku="TEST-001",
                price=Decimal("-10.00"),  # Invalid negative price
                cost=Decimal("50.00"),
                weight=Decimal("1.5"),
                dimensions={"length": 10.0, "width": 5.0, "height": 3.0},
                condition=ProductCondition.NEW
            )
    
    def test_product_weight_validation(self):
        """Test product weight validation."""
        with pytest.raises(ValueError, match="Weight must be positive"):
            ProductBase(
                name="Test Product",
                category="Electronics",
                brand="TestBrand",
                sku="TEST-001",
                price=Decimal("99.99"),
                cost=Decimal("50.00"),
                weight=Decimal("0"),  # Invalid zero weight
                dimensions={"length": 10.0, "width": 5.0, "height": 3.0},
                condition=ProductCondition.NEW
            )
    
    def test_order_status_enum(self):
        """Test OrderStatus enum values."""
        assert OrderStatus.PENDING.value == "pending"
        assert OrderStatus.CONFIRMED.value == "confirmed"
        assert OrderStatus.PROCESSING.value == "processing"
        assert OrderStatus.SHIPPED.value == "shipped"
        assert OrderStatus.DELIVERED.value == "delivered"
        assert OrderStatus.CANCELLED.value == "cancelled"
    
    def test_channel_type_enum(self):
        """Test ChannelType enum values."""
        assert ChannelType.SHOPIFY.value == "shopify"
        assert ChannelType.AMAZON.value == "amazon"
        assert ChannelType.DIRECT.value == "direct"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

