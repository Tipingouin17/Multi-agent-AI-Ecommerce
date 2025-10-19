"""
Pytest configuration and shared fixtures.
"""

import pytest
import asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


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

