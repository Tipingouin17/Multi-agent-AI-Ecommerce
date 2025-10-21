"""
Unit Tests for Order Cancellation Service
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

import sys
sys.path.insert(0, '/home/ubuntu/Multi-agent-AI-Ecommerce')

from agents.order_cancellation_service import (
    OrderCancellationService,
    CreateCancellationRequest,
    CancellationRequest,
    CancellationReason,
    CancellationStatus,
    ReviewCancellationRequest,
    CancellationResult
)


class TestOrderCancellationService:
    """Test suite for OrderCancellationService."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager."""
        db_manager = Mock()
        db_manager.get_async_session = AsyncMock()
        return db_manager
    
    @pytest.fixture
    def service(self, mock_db_manager):
        """Create an OrderCancellationService instance."""
        return OrderCancellationService(mock_db_manager)
    
    def test_service_initialization(self, service, mock_db_manager):
        """Test that service initializes correctly."""
        assert service.db_manager == mock_db_manager
        assert service.logger is not None
    
    def test_cancellation_reason_enum(self):
        """Test CancellationReason enum values."""
        assert CancellationReason.CUSTOMER_REQUEST.value == "customer_request"
        assert CancellationReason.OUT_OF_STOCK.value == "out_of_stock"
        assert CancellationReason.PAYMENT_FAILED.value == "payment_failed"
        assert CancellationReason.FRAUD_DETECTED.value == "fraud_detected"
    
    def test_cancellation_status_enum(self):
        """Test CancellationStatus enum values."""
        assert CancellationStatus.PENDING.value == "pending"
        assert CancellationStatus.APPROVED.value == "approved"
        assert CancellationStatus.REJECTED.value == "rejected"
        assert CancellationStatus.COMPLETED.value == "completed"
    
    def test_create_cancellation_request_validation(self):
        """Test CreateCancellationRequest validation."""
        # Valid request
        valid_request = CreateCancellationRequest(
            order_id="order-001",
            reason=CancellationReason.CUSTOMER_REQUEST,
            reason_details="Customer changed mind",
            requested_by="customer-123"
        )
        assert valid_request.order_id == "order-001"
        assert valid_request.reason == CancellationReason.CUSTOMER_REQUEST
        
        # Test with invalid reason
        with pytest.raises(Exception):
            CreateCancellationRequest(
                order_id="order-001",
                reason="invalid_reason",  # Should fail
                requested_by="customer-123"
            )
    
    @pytest.mark.asyncio
    async def test_create_cancellation_request_success(self, service, mock_db_manager):
        """Test successful cancellation request creation."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_manager.get_async_session.return_value.__aenter__.return_value = mock_session
        
        # Mock order query
        order_result = Mock()
        order_result.fetchone.return_value = ("order-001", "processing", 199.99, "customer-123")
        
        # Mock insert query
        insert_result = Mock()
        insert_result.fetchone.return_value = ("req-001", datetime.utcnow())
        
        mock_session.execute = AsyncMock(side_effect=[order_result, insert_result])
        
        # Create request
        request = CreateCancellationRequest(
            order_id="order-001",
            reason=CancellationReason.CUSTOMER_REQUEST,
            reason_details="Changed mind",
            requested_by="customer-123"
        )
        
        # Execute
        result = await service.create_cancellation_request(request)
        
        # Verify
        assert result is not None
        assert isinstance(result, CancellationRequest)
        assert result.order_id == "order-001"
        assert result.status == CancellationStatus.PENDING
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_cancellation_order_not_found(self, service, mock_db_manager):
        """Test cancellation request for non-existent order."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_manager.get_async_session.return_value.__aenter__.return_value = mock_session
        
        # Mock order query returning None
        order_result = Mock()
        order_result.fetchone.return_value = None
        mock_session.execute = AsyncMock(return_value=order_result)
        
        # Create request
        request = CreateCancellationRequest(
            order_id="non-existent",
            reason=CancellationReason.CUSTOMER_REQUEST,
            requested_by="customer-123"
        )
        
        # Execute and verify exception
        with pytest.raises(ValueError) as exc_info:
            await service.create_cancellation_request(request)
        
        assert "not found" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_cancellation_non_cancellable_status(self, service, mock_db_manager):
        """Test cancellation request for order in non-cancellable status."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_manager.get_async_session.return_value.__aenter__.return_value = mock_session
        
        # Mock order query with delivered status
        order_result = Mock()
        order_result.fetchone.return_value = ("order-001", "delivered", 199.99, "customer-123")
        mock_session.execute = AsyncMock(return_value=order_result)
        
        # Create request
        request = CreateCancellationRequest(
            order_id="order-001",
            reason=CancellationReason.CUSTOMER_REQUEST,
            requested_by="customer-123"
        )
        
        # Execute and verify exception
        with pytest.raises(ValueError) as exc_info:
            await service.create_cancellation_request(request)
        
        assert "cannot be cancelled" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_review_cancellation_approve(self, service, mock_db_manager):
        """Test approving a cancellation request."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_manager.get_async_session.return_value.__aenter__.return_value = mock_session
        
        # Mock cancellation query
        cancel_result = Mock()
        cancel_result.fetchone.return_value = (
            "req-001", "order-001", "customer_request", None,
            "customer-123", datetime.utcnow(), "pending", 199.99
        )
        
        # Mock update query
        update_result = Mock()
        update_result.fetchone.return_value = (datetime.utcnow(),)
        
        mock_session.execute = AsyncMock(side_effect=[cancel_result, update_result])
        
        # Create review request
        review = ReviewCancellationRequest(
            request_id="req-001",
            approved=True,
            reviewed_by="admin-001",
            review_notes="Approved by customer service"
        )
        
        # Execute
        result = await service.review_cancellation_request(review)
        
        # Verify
        assert result is not None
        assert isinstance(result, CancellationResult)
        assert result.success is True
        mock_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_review_cancellation_reject(self, service, mock_db_manager):
        """Test rejecting a cancellation request."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_manager.get_async_session.return_value.__aenter__.return_value = mock_session
        
        # Mock cancellation query
        cancel_result = Mock()
        cancel_result.fetchone.return_value = (
            "req-001", "order-001", "customer_request", None,
            "customer-123", datetime.utcnow(), "pending", 199.99
        )
        
        # Mock update query
        update_result = Mock()
        update_result.fetchone.return_value = (datetime.utcnow(),)
        
        mock_session.execute = AsyncMock(side_effect=[cancel_result, update_result])
        
        # Create review request
        review = ReviewCancellationRequest(
            request_id="req-001",
            approved=False,
            reviewed_by="admin-001",
            review_notes="Order already shipped"
        )
        
        # Execute
        result = await service.review_cancellation_request(review)
        
        # Verify
        assert result is not None
        assert result.success is True
        mock_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_cancellation_request(self, service, mock_db_manager):
        """Test retrieving a cancellation request."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_manager.get_async_session.return_value.__aenter__.return_value = mock_session
        
        mock_result = Mock()
        mock_result.fetchone.return_value = (
            "req-001", "order-001", "customer_request", "Changed mind",
            "customer-123", datetime.utcnow(), "pending", 199.99,
            None, None, None, None
        )
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await service.get_cancellation_request("req-001")
        
        # Verify
        assert result is not None
        assert result.request_id == "req-001"
        assert result.order_id == "order-001"
        assert result.status == CancellationStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_get_order_cancellations(self, service, mock_db_manager):
        """Test retrieving all cancellations for an order."""
        # Setup mock
        mock_session = AsyncMock()
        mock_db_manager.get_async_session.return_value.__aenter__.return_value = mock_session
        
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            ("req-001", "order-001", "customer_request", "Changed mind",
             "customer-123", datetime.utcnow(), "approved", 199.99,
             datetime.utcnow(), "admin-001", "Approved", None),
            ("req-002", "order-001", "customer_request", "Duplicate order",
             "customer-123", datetime.utcnow(), "rejected", 199.99,
             datetime.utcnow(), "admin-001", "Already processed", None)
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Execute
        result = await service.get_order_cancellations("order-001")
        
        # Verify
        assert len(result) == 2
        assert result[0].status == CancellationStatus.APPROVED
        assert result[1].status == CancellationStatus.REJECTED
    
    def test_cancellation_result_model(self):
        """Test CancellationResult model."""
        result = CancellationResult(
            success=True,
            request_id="req-001",
            order_id="order-001",
            status=CancellationStatus.APPROVED,
            refund_amount=Decimal("199.99"),
            message="Cancellation approved"
        )
        
        assert result.success is True
        assert result.request_id == "req-001"
        assert result.status == CancellationStatus.APPROVED
        assert result.refund_amount == Decimal("199.99")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

