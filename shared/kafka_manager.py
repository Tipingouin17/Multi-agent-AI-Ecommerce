"""
Kafka Manager for Multi-Agent E-commerce System

This module provides Kafka connection management and message handling
for all agents.
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Callable, Any
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError
import structlog

logger = structlog.get_logger(__name__)


class KafkaManager:
    """
    Kafka manager for handling producer and consumer connections.
    Provides high-level interface for message publishing and consumption.
    """
    
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        group_id: Optional[str] = None,
        client_id: Optional[str] = None
    ):
        """
        Initialize Kafka manager.
        
        Args:
            bootstrap_servers: Kafka broker addresses
            group_id: Consumer group ID
            client_id: Client identifier
        """
        self.bootstrap_servers = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.group_id = group_id
        self.client_id = client_id
        
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._producer_started = False
        self._consumer_started = False
        
    async def start_producer(self):
        """Start Kafka producer."""
        if self._producer_started:
            logger.warning("Producer already started")
            return
        
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                client_id=self.client_id
            )
            
            await self.producer.start()
            self._producer_started = True
            logger.info("Kafka producer started", bootstrap_servers=self.bootstrap_servers)
            
        except Exception as e:
            logger.error("Failed to start Kafka producer", error=str(e))
            raise
    
    async def start_consumer(self, topics: List[str], **kwargs):
        """
        Start Kafka consumer.
        
        Args:
            topics: List of topics to subscribe to
            **kwargs: Additional consumer configuration
        """
        if self._consumer_started:
            logger.warning("Consumer already started")
            return
        
        try:
            self.consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                client_id=self.client_id,
                **kwargs
            )
            
            await self.consumer.start()
            self._consumer_started = True
            logger.info("Kafka consumer started", topics=topics, group_id=self.group_id)
            
        except Exception as e:
            logger.error("Failed to start Kafka consumer", error=str(e))
            raise
    
    async def send_message(self, topic: str, message: Dict[str, Any], key: Optional[str] = None):
        """
        Send a message to a Kafka topic.
        
        Args:
            topic: Topic name
            message: Message payload (will be JSON serialized)
            key: Optional message key
        """
        if not self._producer_started:
            await self.start_producer()
        
        try:
            key_bytes = key.encode('utf-8') if key else None
            await self.producer.send(topic, value=message, key=key_bytes)
            logger.debug("Message sent", topic=topic, key=key)
            
        except Exception as e:
            logger.error("Failed to send message", topic=topic, error=str(e))
            raise
    
    async def consume_messages(self, callback: Callable[[Dict[str, Any]], Any]):
        """
        Consume messages from subscribed topics.
        
        Args:
            callback: Async function to process each message
        """
        if not self._consumer_started:
            logger.error("Consumer not started")
            raise RuntimeError("Consumer not started. Call start_consumer() first.")
        
        try:
            async for message in self.consumer:
                try:
                    await callback(message.value)
                except Exception as e:
                    logger.error("Error processing message", error=str(e), topic=message.topic)
                    
        except Exception as e:
            logger.error("Error consuming messages", error=str(e))
            raise
    
    async def stop_producer(self):
        """Stop Kafka producer."""
        if self.producer and self._producer_started:
            try:
                await self.producer.stop()
                self._producer_started = False
                logger.info("Kafka producer stopped")
            except Exception as e:
                logger.error("Error stopping producer", error=str(e))
    
    async def stop_consumer(self):
        """Stop Kafka consumer."""
        if self.consumer and self._consumer_started:
            try:
                await self.consumer.stop()
                self._consumer_started = False
                logger.info("Kafka consumer stopped")
            except Exception as e:
                logger.error("Error stopping consumer", error=str(e))
    
    async def close(self):
        """Close all Kafka connections."""
        await self.stop_producer()
        await self.stop_consumer()
        logger.info("Kafka manager closed")
    
    async def health_check(self) -> bool:
        """Check Kafka connectivity."""
        try:
            if not self._producer_started:
                await self.start_producer()
            
            # Try to get cluster metadata
            metadata = await self.producer.client.fetch_all_metadata()
            return len(metadata.brokers) > 0
            
        except Exception as e:
            logger.error("Kafka health check failed", error=str(e))
            return False

