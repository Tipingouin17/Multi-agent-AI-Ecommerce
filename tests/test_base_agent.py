"""
Unit tests for the BaseAgent class.
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.base_agent import (
    BaseAgent, MessageType, AgentMessage, AgentStatus, HealthStatus
)


class TestAgent(BaseAgent):
    """Test implementation of BaseAgent."""
    
    async def initialize(self):
        """Initialize test agent."""
        self.initialized = True
    
    async def cleanup(self):
        """Cleanup test agent."""
        self.cleaned_up = True
    
    async def process_business_logic(self, data):
        """Process test business logic."""
        return {"result": "success", "data": data}


@pytest.fixture
def test_agent():
    """Create a test agent instance."""
    agent = TestAgent(
        agent_id="test_agent",
        kafka_bootstrap_servers="localhost:9092"
    )
    return agent


@pytest.mark.asyncio
class TestBaseAgent:
    """Test cases for BaseAgent."""
    
    async def test_agent_initialization(self, test_agent):
        """Test agent initialization."""
        assert test_agent.agent_id == "test_agent"
        assert test_agent.status == AgentStatus.STOPPED
        assert test_agent.error_count == 0
        assert test_agent.producer is None
        assert test_agent.consumer is None
    
    async def test_message_creation(self):
        """Test AgentMessage creation and serialization."""
        message = AgentMessage(
            message_id="test-123",
            sender_agent="agent_a",
            recipient_agent="agent_b",
            message_type=MessageType.ORDER_CREATED,
            payload={"order_id": "order-123"},
            timestamp=datetime.now(),
            correlation_id="corr-123",
            priority=1
        )
        
        # Test to_dict
        message_dict = message.to_dict()
        assert message_dict["message_id"] == "test-123"
        assert message_dict["sender_agent"] == "agent_a"
        assert message_dict["message_type"] == "order_created"
        
        # Test from_dict
        restored_message = AgentMessage.from_dict(message_dict)
        assert restored_message.message_id == message.message_id
        assert restored_message.sender_agent == message.sender_agent
        assert restored_message.message_type == message.message_type
    
    async def test_health_status(self, test_agent):
        """Test health status reporting."""
        test_agent.status = AgentStatus.RUNNING
        test_agent.start_time = datetime.now()
        
        health = HealthStatus(
            agent_id=test_agent.agent_id,
            status=test_agent.status,
            uptime_seconds=10.5,
            last_heartbeat=datetime.now(),
            error_count=test_agent.error_count
        )
        
        assert health.agent_id == "test_agent"
        assert health.status == AgentStatus.RUNNING
        assert health.uptime_seconds == 10.5
        assert health.error_count == 0
    
    async def test_message_handler_registration(self, test_agent):
        """Test message handler registration."""
        handler_called = False
        
        async def test_handler(message):
            nonlocal handler_called
            handler_called = True
        
        test_agent.register_handler(MessageType.ORDER_CREATED, test_handler)
        
        assert MessageType.ORDER_CREATED in test_agent.message_handlers
        
        # Simulate message handling
        test_message = AgentMessage(
            message_id="test-123",
            sender_agent="test_sender",
            recipient_agent="test_agent",
            message_type=MessageType.ORDER_CREATED,
            payload={},
            timestamp=datetime.now()
        )
        
        await test_agent.message_handlers[MessageType.ORDER_CREATED](test_message)
        assert handler_called
    
    async def test_business_logic_processing(self, test_agent):
        """Test business logic processing."""
        result = await test_agent.process_business_logic({"test": "data"})
        
        assert result["result"] == "success"
        assert result["data"]["test"] == "data"
    
    def test_agent_status_enum(self):
        """Test AgentStatus enum values."""
        assert AgentStatus.STARTING.value == "starting"
        assert AgentStatus.RUNNING.value == "running"
        assert AgentStatus.STOPPING.value == "stopping"
        assert AgentStatus.STOPPED.value == "stopped"
        assert AgentStatus.ERROR.value == "error"
        assert AgentStatus.MAINTENANCE.value == "maintenance"
    
    def test_message_type_enum(self):
        """Test MessageType enum values."""
        assert MessageType.ORDER_CREATED.value == "order_created"
        assert MessageType.ORDER_UPDATED.value == "order_updated"
        assert MessageType.INVENTORY_UPDATE.value == "inventory_update"
        assert MessageType.PRICE_UPDATE.value == "price_update"
        assert MessageType.HEALTH_CHECK.value == "health_check"


@pytest.mark.asyncio
class TestAgentMessaging:
    """Test cases for agent messaging functionality."""
    
    async def test_send_message_without_producer(self, test_agent):
        """Test sending message without initialized producer."""
        with pytest.raises(RuntimeError, match="Agent not started"):
            await test_agent.send_message(
                recipient_agent="other_agent",
                message_type=MessageType.ORDER_CREATED,
                payload={"test": "data"}
            )
    
    @patch('shared.base_agent.AIOKafkaProducer')
    async def test_send_message_with_producer(self, mock_producer_class, test_agent):
        """Test sending message with initialized producer."""
        # Create mock producer
        mock_producer = AsyncMock()
        mock_producer.send_and_wait = AsyncMock()
        mock_producer_class.return_value = mock_producer
        test_agent.producer = mock_producer
        
        # Send message
        await test_agent.send_message(
            recipient_agent="other_agent",
            message_type=MessageType.ORDER_CREATED,
            payload={"order_id": "123"}
        )
        
        # Verify send was called
        assert mock_producer.send_and_wait.called
        assert test_agent.metrics["messages_sent"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

