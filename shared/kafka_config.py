"""
Kafka Configuration Module
Provides Kafka producer and consumer configuration
"""

import os
from typing import Dict, Any
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import json
import logging

logger = logging.getLogger(__name__)


class KafkaConfig:
    """Kafka configuration and client management"""
    
    def __init__(self):
        self.bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.producer = None
        self.consumers = {}
    
    async def get_producer(self) -> AIOKafkaProducer:
        """Get or create Kafka producer"""
        if self.producer is None:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            await self.producer.start()
            logger.info(f"Kafka producer started: {self.bootstrap_servers}")
        return self.producer
    
    async def get_consumer(self, topic: str, group_id: str) -> AIOKafkaConsumer:
        """Get or create Kafka consumer for a topic"""
        key = f"{topic}:{group_id}"
        if key not in self.consumers:
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True
            )
            await consumer.start()
            self.consumers[key] = consumer
            logger.info(f"Kafka consumer started: topic={topic}, group={group_id}")
        return self.consumers[key]
    
    async def publish(self, topic: str, message: Dict[str, Any], key: str = None):
        """Publish message to Kafka topic"""
        producer = await self.get_producer()
        await producer.send(topic, value=message, key=key)
        logger.debug(f"Published to {topic}: {message}")
    
    async def close(self):
        """Close all Kafka connections"""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")
        
        for consumer in self.consumers.values():
            await consumer.stop()
        logger.info(f"Stopped {len(self.consumers)} Kafka consumers")
        
        self.consumers.clear()


# Global instance
kafka_config = KafkaConfig()

# Alias for backward compatibility
KafkaProducer = AIOKafkaProducer
KafkaConsumer = AIOKafkaConsumer

