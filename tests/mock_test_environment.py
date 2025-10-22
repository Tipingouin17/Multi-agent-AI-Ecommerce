#!/usr/bin/env python3
"""
Mock Test Environment for Agent Verification

This provides a lightweight mock environment for testing agents without
requiring actual Kafka/PostgreSQL connections.
"""
import asyncio
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MockDatabaseManager:
    """Mock database manager for testing"""
    
    def __init__(self, db_url: str = "mock://"):
        self.db_url = db_url
        self.connected = False
        
    async def connect(self):
        """Mock connect"""
        self.connected = True
        
    async def disconnect(self):
        """Mock disconnect"""
        self.connected = False
        
    async def create_all(self):
        """Mock create tables"""
        pass
        
    def get_session(self):
        """Mock session"""
        return MockSession()


class MockSession:
    """Mock database session"""
    
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    async def execute(self, query, params=None):
        """Mock execute"""
        return MockResult()
        
    async def commit(self):
        """Mock commit"""
        pass
        
    async def rollback(self):
        """Mock rollback"""
        pass


class MockResult:
    """Mock query result"""
    
    def __init__(self, rows=None):
        self.rows = rows or []
        
    def fetchall(self):
        return self.rows
        
    def fetchone(self):
        return self.rows[0] if self.rows else None
        
    def scalar(self):
        return self.rows[0][0] if self.rows and self.rows[0] else None


class MockKafkaProducer:
    """Mock Kafka producer for testing"""
    
    def __init__(self):
        self.messages = []
        
    async def send(self, topic: str, message: Dict[str, Any]):
        """Mock send message"""
        self.messages.append({"topic": topic, "message": message})
        return True
        
    async def stop(self):
        """Mock stop"""
        pass


class MockKafkaConsumer:
    """Mock Kafka consumer for testing"""
    
    def __init__(self, topics: List[str], group_id: str = "test"):
        self.topics = topics
        self.group_id = group_id
        self.messages = []
        
    async def start_consumer(self, callback):
        """Mock start consumer"""
        # Process any queued messages
        for msg in self.messages:
            await callback(msg)
            
    async def stop(self):
        """Mock stop"""
        pass
        
    def add_message(self, topic: str, message: Dict[str, Any]):
        """Add a message to the queue for testing"""
        self.messages.append({"topic": topic, "message": message})


class MockDatabaseHelper:
    """Mock database helper for testing"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager or MockDatabaseManager()
        self.data = {}  # In-memory storage
        
    async def create(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock create"""
        if table not in self.data:
            self.data[table] = []
        record_id = len(self.data[table]) + 1
        record = {"id": record_id, **data}
        self.data[table].append(record)
        return record
        
    async def get_by_id(self, table: str, record_id: int) -> Optional[Dict[str, Any]]:
        """Mock get by ID"""
        if table not in self.data:
            return None
        for record in self.data[table]:
            if record.get("id") == record_id:
                return record
        return None
        
    async def update(self, table: str, record_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mock update"""
        if table not in self.data:
            return None
        for record in self.data[table]:
            if record.get("id") == record_id:
                record.update(updates)
                return record
        return None
        
    async def delete(self, table: str, record_id: int) -> bool:
        """Mock delete"""
        if table not in self.data:
            return False
        for i, record in enumerate(self.data[table]):
            if record.get("id") == record_id:
                del self.data[table][i]
                return True
        return False
        
    async def query(self, table: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Mock query"""
        if table not in self.data:
            return []
        if not filters:
            return self.data[table]
        results = []
        for record in self.data[table]:
            match = all(record.get(k) == v for k, v in filters.items())
            if match:
                results.append(record)
        return results


def create_mock_agent_environment():
    """Create a complete mock environment for agent testing"""
    return {
        "db_manager": MockDatabaseManager(),
        "db_helper": MockDatabaseHelper(),
        "kafka_producer": MockKafkaProducer(),
        "kafka_consumer": MockKafkaConsumer(topics=["test_topic"]),
    }


async def test_agent_lifecycle(agent_class, **init_kwargs):
    """Test agent lifecycle (initialize, process, cleanup)
    
    Args:
        agent_class: The agent class to test
        **init_kwargs: Keyword arguments to pass to agent constructor
        
    Returns:
        dict: Test results
    """
    results = {
        "instantiate": False,
        "initialize": False,
        "process_business_logic": False,
        "cleanup": False,
        "errors": []
    }
    
    try:
        # Create mock environment
        env = create_mock_agent_environment()
        
        # Instantiate agent
        agent = agent_class(**init_kwargs)
        results["instantiate"] = True
        
        # Mock the database and Kafka components
        if hasattr(agent, 'db_manager'):
            agent.db_manager = env["db_manager"]
        if hasattr(agent, 'db_helper'):
            agent.db_helper = env["db_helper"]
        if hasattr(agent, 'kafka_producer'):
            agent.kafka_producer = env["kafka_producer"]
        if hasattr(agent, 'kafka_consumer'):
            agent.kafka_consumer = env["kafka_consumer"]
        
        # Test initialize
        try:
            await agent.initialize()
            results["initialize"] = True
        except Exception as e:
            results["errors"].append(f"Initialize failed: {str(e)}")
        
        # Test process_business_logic
        try:
            test_data = {"operation": "test", "data": {"test": "value"}}
            result = await agent.process_business_logic(test_data)
            if result and isinstance(result, dict):
                results["process_business_logic"] = True
            else:
                results["errors"].append("process_business_logic returned invalid result")
        except Exception as e:
            results["errors"].append(f"process_business_logic failed: {str(e)}")
        
        # Test cleanup
        try:
            await agent.cleanup()
            results["cleanup"] = True
        except Exception as e:
            results["errors"].append(f"Cleanup failed: {str(e)}")
            
    except Exception as e:
        results["errors"].append(f"Test failed: {str(e)}")
    
    return results


if __name__ == "__main__":
    print("Mock Test Environment Ready")
    print("Use create_mock_agent_environment() to create mock components")
    print("Use test_agent_lifecycle(AgentClass) to test an agent")
