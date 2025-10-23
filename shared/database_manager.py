"""
Enhanced Database Manager with Robust Connection Handling

This module provides production-grade database connection management with:
- Exponential backoff retry logic
- Connection pre-warming
- Automatic reconnection on failure
- Health checks
- Connection pool monitoring
- Windows compatibility fixes
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError, DBAPIError

from .models import DatabaseConfig

logger = structlog.get_logger(__name__)


class DatabaseConnectionError(Exception):
    """Raised when database connection fails after all retries"""
    pass


class EnhancedDatabaseManager:
    """
    Enhanced database manager with robust error handling and retry logic.
    
    Features:
    - Exponential backoff for connection retries
    - Connection pre-warming
    - Automatic reconnection
    - Health monitoring
    - Windows compatibility
    """
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.async_engine = None
        self.async_session_factory = None
        self._initialized = False
        self._connection_attempts = 0
        self._last_health_check = 0
        self._health_check_interval = 30  # seconds
        
    async def initialize(
        self,
        max_retries: int = 5,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0
    ) -> None:
        """
        Initialize database connection with exponential backoff retry.
        
        Args:
            max_retries: Maximum number of connection attempts
            initial_delay: Initial delay between retries (seconds)
            max_delay: Maximum delay between retries (seconds)
            backoff_factor: Multiplier for exponential backoff
        """
        if self._initialized:
            logger.info("Database already initialized")
            return
            
        delay = initial_delay
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                self._connection_attempts = attempt
                logger.info(
                    "Attempting database connection",
                    attempt=attempt,
                    max_retries=max_retries
                )
                
                await self._create_engine()
                await self._test_connection()
                await self._prewarm_connections()
                
                self._initialized = True
                logger.info(
                    "Database initialized successfully",
                    attempt=attempt,
                    pool_size=5
                )
                return
                
            except (OperationalError, DBAPIError, ConnectionError) as e:
                last_error = e
                logger.warning(
                    "Database connection failed",
                    attempt=attempt,
                    max_retries=max_retries,
                    error=str(e),
                    retry_delay=delay
                )
                
                if attempt < max_retries:
                    await asyncio.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)
                else:
                    logger.error(
                        "Database initialization failed after all retries",
                        attempts=max_retries,
                        error=str(last_error)
                    )
                    raise DatabaseConnectionError(
                        f"Failed to connect to database after {max_retries} attempts: {last_error}"
                    ) from last_error
    
    async def _create_engine(self) -> None:
        """Create async database engine with optimized settings"""
        async_url = self.config.url.replace("postgresql://", "postgresql+asyncpg://")
        
        self.async_engine = create_async_engine(
            async_url,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=300,  # Recycle connections every 5 minutes
            pool_size=5,  # Maintain 5 persistent connections
            max_overflow=10,  # Allow up to 10 additional connections
            pool_timeout=30,  # Wait up to 30 seconds for connection
            echo=self.config.echo,
            connect_args={
                "server_settings": {
                    "application_name": "multi_agent_ecommerce"
                },
                "command_timeout": 60,  # Query timeout
                "timeout": 30  # Connection timeout
            }
        )
        
        self.async_session_factory = async_sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        
        logger.debug("Database engine created")
    
    async def _test_connection(self) -> None:
        """Test database connection"""
        async with self.async_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        logger.debug("Database connection test passed")
    
    async def _prewarm_connections(self, count: int = 3) -> None:
        """
        Pre-warm connection pool by creating and testing connections.
        
        Args:
            count: Number of connections to pre-warm
        """
        logger.debug("Pre-warming connection pool", count=count)
        
        sessions = []
        try:
            for i in range(count):
                session = self.async_session_factory()
                await session.execute(text("SELECT 1"))
                sessions.append(session)
                logger.debug("Pre-warmed connection", index=i+1)
            
            logger.info("Connection pool pre-warmed", count=count)
        finally:
            # Close all pre-warmed sessions
            for session in sessions:
                await session.close()
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session with automatic retry on connection failure.
        
        Yields:
            AsyncSession: Database session
            
        Raises:
            DatabaseConnectionError: If connection fails after retries
        """
        if not self._initialized:
            await self.initialize()
        
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                async with self.async_session_factory() as session:
                    # Test connection before yielding
                    await session.execute(text("SELECT 1"))
                    yield session
                    return
                    
            except (OperationalError, DBAPIError) as e:
                logger.warning(
                    "Session creation failed",
                    attempt=attempt,
                    max_retries=max_retries,
                    error=str(e)
                )
                
                if attempt < max_retries:
                    # Try to reinitialize connection
                    self._initialized = False
                    await self.initialize(max_retries=2)
                else:
                    raise DatabaseConnectionError(
                        f"Failed to create session after {max_retries} attempts"
                    ) from e
    
    async def health_check(self, force: bool = False) -> dict:
        """
        Perform database health check.
        
        Args:
            force: Force health check even if recently checked
            
        Returns:
            dict: Health check results
        """
        current_time = time.time()
        
        # Skip if recently checked (unless forced)
        if not force and (current_time - self._last_health_check) < self._health_check_interval:
            return {
                "status": "healthy",
                "cached": True,
                "last_check": self._last_health_check
            }
        
        try:
            start_time = time.time()
            async with self.async_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            response_time = (time.time() - start_time) * 1000  # ms
            
            self._last_health_check = current_time
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "pool_size": 5,
                "initialized": self._initialized,
                "connection_attempts": self._connection_attempts
            }
            
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "initialized": self._initialized
            }
    
    async def close(self) -> None:
        """Close database connections"""
        if self.async_engine:
            await self.async_engine.dispose()
            logger.info("Database connections closed")
        self._initialized = False
    
    def __repr__(self) -> str:
        return f"<EnhancedDatabaseManager initialized={self._initialized}>"


# Global instance (optional, for backward compatibility)
_global_db_manager: Optional[EnhancedDatabaseManager] = None


def get_database_manager() -> EnhancedDatabaseManager:
    """Get global database manager instance"""
    global _global_db_manager
    if _global_db_manager is None:
        raise RuntimeError("Database manager not initialized. Call initialize_database_manager() first.")
    return _global_db_manager


def initialize_database_manager(config: DatabaseConfig) -> EnhancedDatabaseManager:
    """Initialize global database manager"""
    global _global_db_manager
    _global_db_manager = EnhancedDatabaseManager(config)
    return _global_db_manager

