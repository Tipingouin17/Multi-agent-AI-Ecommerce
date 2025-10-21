"""
Comprehensive tests for Marketplace Connector Agent
Tests marketplace integrations, order sync, inventory sync, and message handling
"""

import pytest
import asyncio
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock

# Import the agent (adjust path as needed)
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.marketplace_connector_agent import (
    MarketplaceConnectorAgent,
    MarketplaceName,
    SyncStatus,
    InventorySyncRequest,
    MessageCreate,
    OfferCreate
)


@pytest.fixture
def mock_db():
    """Mock database manager"""
    db = Mock()
    db.execute = AsyncMock()
    db.fetch_one = AsyncMock()
    db.fetch_all = AsyncMock()
    return db


@pytest.fixture
def agent(mock_db):
    """Create agent instance with mocked dependencies"""
    agent = MarketplaceConnectorAgent()
    agent.db = mock_db
    return agent


class TestMarketplaceConnections:
    """Test marketplace connection management"""
    
    @pytest.mark.asyncio
    async def test_create_connection_success(self, agent, mock_db):
        """Test successful marketplace connection creation"""
        connection_id = uuid4()
        mock_db.fetch_one.return_value = {
            'connection_id': connection_id,
            'marketplace_name': 'cdiscount',
            'merchant_id': 'MERCHANT123',
            'is_active': True
        }
        
        result = await agent.create_connection(
            marketplace_name=MarketplaceName.CDISCOUNT,
            merchant_id='MERCHANT123',
            api_credentials={'api_key': 'test_key'}
        )
        
        assert result['connection_id'] == connection_id
        assert result['marketplace_name'] == 'cdiscount'
        mock_db.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_connection_duplicate(self, agent, mock_db):
        """Test duplicate connection handling"""
        mock_db.execute.side_effect = Exception("Duplicate connection")
        
        with pytest.raises(Exception):
            await agent.create_connection(
                marketplace_name=MarketplaceName.CDISCOUNT,
                merchant_id='MERCHANT123',
                api_credentials={'api_key': 'test_key'}
            )
    
    @pytest.mark.asyncio
    async def test_list_connections(self, agent, mock_db):
        """Test listing all marketplace connections"""
        mock_db.fetch_all.return_value = [
            {
                'connection_id': uuid4(),
                'marketplace_name': 'cdiscount',
                'is_active': True
            },
            {
                'connection_id': uuid4(),
                'marketplace_name': 'amazon',
                'is_active': True
            }
        ]
        
        result = await agent.list_connections()
        
        assert len(result) == 2
        assert result[0]['marketplace_name'] == 'cdiscount'
        assert result[1]['marketplace_name'] == 'amazon'


class TestOrderSynchronization:
    """Test order synchronization functionality"""
    
    @pytest.mark.asyncio
    async def test_sync_orders_success(self, agent, mock_db):
        """Test successful order synchronization"""
        connection_id = uuid4()
        
        # Mock marketplace API response
        with patch.object(agent, '_fetch_marketplace_orders', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [
                {
                    'order_number': 'ORD001',
                    'customer_name': 'John Doe',
                    'total': 99.99,
                    'items': []
                }
            ]
            
            mock_db.fetch_one.return_value = {'count': 1}
            
            result = await agent.sync_orders(connection_id)
            
            assert result['success'] is True
            assert result['synced_count'] == 1
            assert result['failed_count'] == 0
    
    @pytest.mark.asyncio
    async def test_sync_orders_partial_failure(self, agent, mock_db):
        """Test order sync with some failures"""
        connection_id = uuid4()
        
        with patch.object(agent, '_fetch_marketplace_orders', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [
                {'order_number': 'ORD001', 'total': 99.99},
                {'order_number': 'ORD002', 'total': 149.99},
            ]
            
            # First insert succeeds, second fails
            mock_db.execute.side_effect = [None, Exception("Database error")]
            
            result = await agent.sync_orders(connection_id)
            
            assert result['synced_count'] == 1
            assert result['failed_count'] == 1
            assert len(result['errors']) > 0


class TestInventorySynchronization:
    """Test inventory synchronization"""
    
    @pytest.mark.asyncio
    async def test_sync_inventory_success(self, agent, mock_db):
        """Test successful inventory sync"""
        sync_request = InventorySyncRequest(
            connection_id=uuid4(),
            product_id='PROD123',
            marketplace_sku='SKU123',
            quantity=50,
            price=Decimal('29.99')
        )
        
        mock_db.fetch_one.return_value = {'inventory_id': uuid4()}
        
        result = await agent.sync_inventory(sync_request)
        
        assert result['success'] is True
        assert 'inventory_id' in result
        mock_db.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_sync_inventory_negative_quantity(self, agent, mock_db):
        """Test inventory sync with invalid quantity"""
        sync_request = InventorySyncRequest(
            connection_id=uuid4(),
            product_id='PROD123',
            marketplace_sku='SKU123',
            quantity=-10,  # Invalid
            price=Decimal('29.99')
        )
        
        with pytest.raises(ValueError):
            await agent.sync_inventory(sync_request)


class TestMessageHandling:
    """Test marketplace message handling"""
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, agent, mock_db):
        """Test sending message to marketplace"""
        message = MessageCreate(
            connection_id=uuid4(),
            customer_id='CUST123',
            order_id='ORD123',
            subject='Order inquiry',
            message_body='When will my order ship?'
        )
        
        with patch.object(agent, '_send_to_marketplace', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {'message_id': 'MSG123', 'status': 'sent'}
            mock_db.fetch_one.return_value = {'message_id': uuid4()}
            
            result = await agent.send_message(message)
            
            assert result['success'] is True
            assert 'message_id' in result
    
    @pytest.mark.asyncio
    async def test_receive_messages(self, agent, mock_db):
        """Test receiving messages from marketplace"""
        connection_id = uuid4()
        
        with patch.object(agent, '_fetch_marketplace_messages', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [
                {
                    'message_id': 'MSG001',
                    'customer_id': 'CUST123',
                    'subject': 'Question',
                    'body': 'Test message'
                }
            ]
            
            result = await agent.receive_messages(connection_id)
            
            assert len(result) == 1
            assert result[0]['message_id'] == 'MSG001'


class TestOfferManagement:
    """Test marketplace offer management"""
    
    @pytest.mark.asyncio
    async def test_create_offer_success(self, agent, mock_db):
        """Test creating marketplace offer"""
        offer = OfferCreate(
            connection_id=uuid4(),
            product_id='PROD123',
            price=Decimal('49.99'),
            quantity=100
        )
        
        with patch.object(agent, '_create_marketplace_offer', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {'offer_id': 'OFFER123', 'status': 'active'}
            mock_db.fetch_one.return_value = {'offer_id': uuid4()}
            
            result = await agent.create_offer(offer)
            
            assert result['success'] is True
            assert 'offer_id' in result
    
    @pytest.mark.asyncio
    async def test_update_offer_price(self, agent, mock_db):
        """Test updating offer price"""
        offer_id = uuid4()
        new_price = Decimal('39.99')
        
        with patch.object(agent, '_update_marketplace_offer', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = {'status': 'updated'}
            
            result = await agent.update_offer_price(offer_id, new_price)
            
            assert result['success'] is True
            mock_db.execute.assert_called()


class TestMarketplaceSpecific:
    """Test marketplace-specific implementations"""
    
    @pytest.mark.asyncio
    async def test_cdiscount_order_format(self, agent):
        """Test CDiscount order format parsing"""
        cdiscount_order = {
            'OrderNumber': 'CD123',
            'OrderState': 'Validated',
            'TotalAmount': '99.99',
            'OrderLines': []
        }
        
        parsed = agent._parse_cdiscount_order(cdiscount_order)
        
        assert parsed['order_number'] == 'CD123'
        assert parsed['status'] == 'validated'
        assert float(parsed['total_amount']) == 99.99
    
    @pytest.mark.asyncio
    async def test_amazon_order_format(self, agent):
        """Test Amazon order format parsing"""
        amazon_order = {
            'AmazonOrderId': 'AMZ123',
            'OrderStatus': 'Shipped',
            'OrderTotal': {'Amount': '149.99'},
            'OrderItems': []
        }
        
        parsed = agent._parse_amazon_order(amazon_order)
        
        assert parsed['order_number'] == 'AMZ123'
        assert parsed['status'] == 'shipped'
        assert float(parsed['total_amount']) == 149.99


class TestErrorHandling:
    """Test error handling and resilience"""
    
    @pytest.mark.asyncio
    async def test_connection_timeout(self, agent):
        """Test handling of connection timeout"""
        connection_id = uuid4()
        
        with patch.object(agent, '_fetch_marketplace_orders', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = asyncio.TimeoutError()
            
            result = await agent.sync_orders(connection_id)
            
            assert result['success'] is False
            assert 'timeout' in result['errors'][0].lower()
    
    @pytest.mark.asyncio
    async def test_invalid_credentials(self, agent):
        """Test handling of invalid API credentials"""
        with pytest.raises(Exception) as exc_info:
            await agent.create_connection(
                marketplace_name=MarketplaceName.CDISCOUNT,
                merchant_id='INVALID',
                api_credentials={}  # Empty credentials
            )
        
        assert 'credentials' in str(exc_info.value).lower()


class TestPerformance:
    """Test performance and optimization"""
    
    @pytest.mark.asyncio
    async def test_bulk_order_sync_performance(self, agent, mock_db):
        """Test performance of bulk order synchronization"""
        connection_id = uuid4()
        
        # Generate 1000 mock orders
        mock_orders = [
            {'order_number': f'ORD{i:04d}', 'total': 99.99}
            for i in range(1000)
        ]
        
        with patch.object(agent, '_fetch_marketplace_orders', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_orders
            
            import time
            start = time.time()
            result = await agent.sync_orders(connection_id)
            duration = time.time() - start
            
            # Should process 1000 orders in under 5 seconds
            assert duration < 5.0
            assert result['synced_count'] == 1000


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

