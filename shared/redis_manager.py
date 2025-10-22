"""
Redis Manager for Multi-Agent E-commerce System

This module provides Redis connection management and caching utilities
for all agents.
"""

import os
import json
from typing import Optional, Any, Dict
import redis.asyncio as redis
from redis.asyncio import Redis
import structlog

logger = structlog.get_logger(__name__)


class RedisManager:
    """
    Redis manager for handling cache operations and pub/sub.
    Provides high-level interface for caching and real-time messaging.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        decode_responses: bool = True
    ):
        """
        Initialize Redis manager.
        
        Args:
            host: Redis server host
            port: Redis server port
            db: Database number
            password: Optional password
            decode_responses: Whether to decode responses to strings
        """
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", "6379"))
        self.db = db
        self.password = password or os.getenv("REDIS_PASSWORD")
        self.decode_responses = decode_responses
        
        self.client: Optional[Redis] = None
        self._connected = False
    
    async def connect(self):
        """Establish connection to Redis."""
        if self._connected:
            logger.warning("Redis already connected")
            return
        
        try:
            self.client = await redis.from_url(
                f"redis://{self.host}:{self.port}/{self.db}",
                password=self.password,
                decode_responses=self.decode_responses
            )
            
            # Test connection
            await self.client.ping()
            self._connected = True
            logger.info("Redis connected", host=self.host, port=self.port, db=self.db)
            
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.client and self._connected:
            try:
                await self.client.close()
                self._connected = False
                logger.info("Redis disconnected")
            except Exception as e:
                logger.error("Error disconnecting from Redis", error=str(e))
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None):
        """
        Set a key-value pair in Redis.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized if dict/list)
            expire: Optional expiration time in seconds
        """
        if not self._connected:
            await self.connect()
        
        try:
            # Serialize complex types
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            await self.client.set(key, value, ex=expire)
            logger.debug("Redis SET", key=key, expire=expire)
            
        except Exception as e:
            logger.error("Redis SET failed", key=key, error=str(e))
            raise
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from Redis.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        if not self._connected:
            await self.connect()
        
        try:
            value = await self.client.get(key)
            
            if value is None:
                return default
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error("Redis GET failed", key=key, error=str(e))
            return default
    
    async def delete(self, *keys: str) -> int:
        """
        Delete one or more keys from Redis.
        
        Args:
            *keys: Keys to delete
            
        Returns:
            Number of keys deleted
        """
        if not self._connected:
            await self.connect()
        
        try:
            count = await self.client.delete(*keys)
            logger.debug("Redis DELETE", keys=keys, count=count)
            return count
            
        except Exception as e:
            logger.error("Redis DELETE failed", keys=keys, error=str(e))
            raise
    
    async def exists(self, *keys: str) -> int:
        """
        Check if keys exist in Redis.
        
        Args:
            *keys: Keys to check
            
        Returns:
            Number of existing keys
        """
        if not self._connected:
            await self.connect()
        
        try:
            return await self.client.exists(*keys)
        except Exception as e:
            logger.error("Redis EXISTS failed", keys=keys, error=str(e))
            return 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for a key.
        
        Args:
            key: Cache key
            seconds: Expiration time in seconds
            
        Returns:
            True if expiration was set
        """
        if not self._connected:
            await self.connect()
        
        try:
            return await self.client.expire(key, seconds)
        except Exception as e:
            logger.error("Redis EXPIRE failed", key=key, error=str(e))
            return False
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter.
        
        Args:
            key: Counter key
            amount: Amount to increment by
            
        Returns:
            New counter value
        """
        if not self._connected:
            await self.connect()
        
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error("Redis INCR failed", key=key, error=str(e))
            raise
    
    async def hset(self, name: str, mapping: Dict[str, Any]):
        """
        Set hash fields.
        
        Args:
            name: Hash name
            mapping: Field-value mapping
        """
        if not self._connected:
            await self.connect()
        
        try:
            # Serialize complex values
            serialized = {}
            for k, v in mapping.items():
                if isinstance(v, (dict, list)):
                    serialized[k] = json.dumps(v)
                else:
                    serialized[k] = v
            
            await self.client.hset(name, mapping=serialized)
            logger.debug("Redis HSET", name=name)
            
        except Exception as e:
            logger.error("Redis HSET failed", name=name, error=str(e))
            raise
    
    async def hget(self, name: str, key: str, default: Any = None) -> Any:
        """
        Get a hash field value.
        
        Args:
            name: Hash name
            key: Field key
            default: Default value if field not found
            
        Returns:
            Field value or default
        """
        if not self._connected:
            await self.connect()
        
        try:
            value = await self.client.hget(name, key)
            
            if value is None:
                return default
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error("Redis HGET failed", name=name, key=key, error=str(e))
            return default
    
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """
        Get all hash fields.
        
        Args:
            name: Hash name
            
        Returns:
            Dictionary of all fields
        """
        if not self._connected:
            await self.connect()
        
        try:
            data = await self.client.hgetall(name)
            
            # Try to deserialize JSON values
            result = {}
            for k, v in data.items():
                try:
                    result[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    result[k] = v
            
            return result
            
        except Exception as e:
            logger.error("Redis HGETALL failed", name=name, error=str(e))
            return {}
    
    async def health_check(self) -> bool:
        """Check Redis connectivity."""
        try:
            if not self._connected:
                await self.connect()
            
            await self.client.ping()
            return True
            
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
            return False

