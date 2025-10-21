"""
Unit Tests for Product Variants Service
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

import sys
sys.path.insert(0, '/home/ubuntu/Multi-agent-AI-Ecommerce')

from agents.product_variants_service import (
    ProductVariantsService,
    CreateVariantRequest,
    ProductVariant,
    VariantAttribute
)


class TestProductVariantsService:
    """Test suite for ProductVariantsService."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager."""
        db_manager = Mock()
        db_manager.get_async_session = AsyncMock()
        return db_manager
    
    @pytest.fixture
    def service(self, mock_db_manager):
        """Create a ProductVariantsService instance."""
        return ProductVariantsService(mock_db_manager)
    
    def test_service_initialization(self, service, mock_db_manager):
        """Test that service initializes correctly."""
        assert service.db_manager == mock_db_manager
        assert service.logger is not None
    
    def test_create_variant_request_validation(self):
        """Test CreateVariantRequest validation."""
        # Valid request
        valid_request = CreateVariantRequest(
            product_id="prod-001",
            variant_sku="TEST-SKU-001",
            attributes={"color": "red", "size": "L"},
            price_adjustment=Decimal("5.00"),
            stock_quantity=100
        )
        assert valid_request.product_id == "prod-001"
        assert valid_request.variant_sku == "TEST-SKU-001"
        assert valid_request.attributes["color"] == "red"
        
        # Test with missing required fields
        with pytest.raises(Exception):
            CreateVariantRequest(
                product_id="prod-001"
                # Missing required fields
            )
    
    def test_product_variant_model(self):
        """Test ProductVariant model."""
        variant = ProductVariant(
            variant_id="var-001",
            product_id="prod-001",
            variant_sku="TEST-SKU-001",
            attributes={"color": "red", "size": "L"},
            price_adjustment=Decimal("5.00"),
            stock_quantity=100,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        assert variant.variant_id == "var-001"
        assert variant.product_id == "prod-001"
        assert variant.is_active is True
        assert variant.stock_quantity == 100
    
    @pytest.mark.asyncio
    async def test_create_variant_success(self, service, mock_db_manager):
        """Test successful variant creation."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_manager.get_async_session.return_value.__aenter__.return_value = mock_session
        
        mock_result = Mock()
        mock_result.fetchone.return_value = ("var-001", datetime.utcnow())
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Create request
        request = CreateVariantRequest(
            product_id="prod-001",
            variant_sku="TEST-SKU-001",
            attributes={"color": "red"},
            price_adjustment=Decimal("5.00"),
            stock_quantity=100
        )
        
        # Execute
        result = await service.create_variant(request)
        
        # Verify
        assert result is not None
        assert isinstance(result, ProductVariant)
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_variant_database_error(self, service, mock_db_manager):
        """Test variant creation with database error."""
        # Setup mock to raise exception
        mock_session = AsyncMock()
        mock_db_manager.get_async_session.return_value.__aenter__.return_value = mock_session
        mock_session.execute = AsyncMock(side_effect=Exception("Database error"))
        
        # Create request
        request = CreateVariantRequest(
            product_id="prod-001",
            variant_sku="TEST-SKU-001",
            attributes={"color": "red"},
            price_adjustment=Decimal("5.00"),
            stock_quantity=100
        )
        
        # Execute and verify exception
        with pytest.raises(Exception) as exc_info:
            await service.create_variant(request)
        
        assert "Database error" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
    
    def test_variant_attribute_model(self):
        """Test VariantAttribute model."""
        attribute = VariantAttribute(
            attribute_name="color",
            attribute_value="red"
        )
        
        assert attribute.attribute_name == "color"
        assert attribute.attribute_value == "red"
    
    @pytest.mark.asyncio
    async def test_get_variant_by_id(self, service, mock_db_manager):
        """Test retrieving a variant by ID."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_manager.get_async_session.return_value.__aenter__.return_value = mock_session
        
        mock_result = Mock()
        mock_result.fetchone.return_value = (
            "var-001", "prod-001", "TEST-SKU-001",
            '{"color": "red"}', 5.00, 100, True, datetime.utcnow()
        )
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await service.get_variant("var-001")
        
        # Verify
        assert result is not None
        assert result.variant_id == "var-001"
        assert result.product_id == "prod-001"
    
    @pytest.mark.asyncio
    async def test_get_variant_not_found(self, service, mock_db_manager):
        """Test retrieving a non-existent variant."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_manager.get_async_session.return_value.__aenter__.return_value = mock_session
        
        mock_result = Mock()
        mock_result.fetchone.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await service.get_variant("non-existent")
        
        # Verify
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_product_variants(self, service, mock_db_manager):
        """Test listing all variants for a product."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_manager.get_async_session.return_value.__aenter__.return_value = mock_session
        
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            ("var-001", "prod-001", "SKU-001", '{"color": "red"}', 5.00, 100, True, datetime.utcnow()),
            ("var-002", "prod-001", "SKU-002", '{"color": "blue"}', 5.00, 50, True, datetime.utcnow())
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await service.list_product_variants("prod-001")
        
        # Verify
        assert len(result) == 2
        assert result[0].variant_id == "var-001"
        assert result[1].variant_id == "var-002"
    
    @pytest.mark.asyncio
    async def test_update_variant_stock(self, service, mock_db_manager):
        """Test updating variant stock quantity."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_manager.get_async_session.return_value.__aenter__.return_value = mock_session
        mock_session.execute = AsyncMock()
        
        # Execute
        await service.update_variant_stock("var-001", 150)
        
        # Verify
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
    
    def test_price_adjustment_calculation(self):
        """Test that price adjustments work correctly."""
        base_price = Decimal("100.00")
        adjustment = Decimal("10.00")
        
        final_price = base_price + adjustment
        assert final_price == Decimal("110.00")
        
        # Test negative adjustment (discount)
        adjustment = Decimal("-15.00")
        final_price = base_price + adjustment
        assert final_price == Decimal("85.00")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

