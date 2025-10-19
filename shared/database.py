"""
Database utilities for Multi-Agent E-commerce System

This module provides database connection management, session handling,
and common database operations for all agents.
ALL OPERATIONS USE REAL DATABASE - NO MOCK DATA.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Type, List, Dict, Any

import asyncpg
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, NullPool
import structlog

from .models import Base, DatabaseConfig


logger = structlog.get_logger(__name__)


class DatabaseManager:
    """
    Database manager for handling connections and sessions.
    Supports both sync and async operations.
    ALL OPERATIONS USE REAL DATABASE - NO MOCK DATA.
    """
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.sync_engine = None
        self.async_engine = None
        self.sync_session_factory = None
        self.async_session_factory = None
        self._initialized = False
        
    def initialize_sync(self):
        """Initialize synchronous database engine and session factory."""
        self.sync_engine = create_engine(
            self.config.url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=self.config.echo,
            poolclass=QueuePool,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow
        )
        
        self.sync_session_factory = sessionmaker(
            bind=self.sync_engine,
            autocommit=False,
            autoflush=False
        )
        
        logger.info("Synchronous database engine initialized")
    
    async def initialize_async(self):
        """Initialize asynchronous database engine and session factory."""
        async_url = self.config.url.replace("postgresql://", "postgresql+asyncpg://")
        
        self.async_engine = create_async_engine(
            async_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=self.config.echo,
            poolclass=NullPool  # Use NullPool for async to avoid connection issues
        )
        
        self.async_session_factory = async_sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        
        self._initialized = True
        logger.info("Asynchronous database engine initialized")
    
    async def test_connection(self):
        """Test database connection."""
        if not self._initialized:
            await self.initialize_async()
        
        async with self.async_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        
        logger.info("Database connection test successful")
    
    async def create_tables(self):
        """Create all database tables."""
        if not self._initialized:
            await self.initialize_async()
        
        # Import all models to ensure they're registered
        from .models import (
            ProductDB, CustomerDB, OrderDB, OrderItemDB, 
            InventoryDB, WarehouseDB, ShipmentDB, CarrierDB
        )
        
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created")
    
    async def drop_tables(self):
        """Drop all database tables."""
        if not self._initialized:
            await self.initialize_async()
        
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.info("Database tables dropped")
    
    async def check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        if not self._initialized:
            await self.initialize_async()
        
        async with self.async_engine.begin() as conn:
            result = await conn.execute(
                text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)"),
                {"table_name": table_name}
            )
            return result.scalar()
    
    async def get_table_stats(self) -> Dict[str, int]:
        """Get row counts for all tables."""
        if not self._initialized:
            await self.initialize_async()
        
        stats = {}
        tables = ['products', 'customers', 'orders', 'order_items', 
                 'inventory', 'warehouses', 'shipments', 'carriers']
        
        async with self.get_async_session() as session:
            for table in tables:
                try:
                    result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    stats[table] = result.scalar()
                except Exception as e:
                    logger.warning(f"Could not get stats for table {table}", error=str(e))
                    stats[table] = 0
        
        return stats
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session with automatic cleanup."""
        if not self._initialized:
            await self.initialize_async()
        
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error("Database session error", error=str(e))
                raise
            finally:
                await session.close()
    
    @asynccontextmanager
    def get_sync_session(self) -> Session:
        """Get a sync database session with automatic cleanup."""
        if not self.sync_session_factory:
            self.initialize_sync()
        
        session = self.sync_session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            session.close()
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            if not self._initialized:
                await self.initialize_async()
            
            async with self.async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            
            return True
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False
    
    async def close(self):
        """Close database connections."""
        if self.async_engine:
            await self.async_engine.dispose()
        
        if self.sync_engine:
            self.sync_engine.dispose()
        
        self._initialized = False
        logger.info("Database connections closed")


class BaseRepository:
    """
    Base repository class providing common database operations.
    ALL OPERATIONS USE REAL DATABASE - NO MOCK DATA.
    """
    
    def __init__(self, db_manager: DatabaseManager, model_class: Type[Base]):
        self.db_manager = db_manager
        self.model_class = model_class
    
    async def create(self, **kwargs) -> Base:
        """Create a new record in the database."""
        async with self.db_manager.get_async_session() as session:
            instance = self.model_class(**kwargs)
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
            return instance
    
    async def get_by_id(self, record_id: str) -> Optional[Base]:
        """Get a record by ID from the database."""
        async with self.db_manager.get_async_session() as session:
            result = await session.get(self.model_class, record_id)
            return result
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Base]:
        """Get all records with pagination from the database."""
        async with self.db_manager.get_async_session() as session:
            result = await session.execute(
                text(f"SELECT * FROM {self.model_class.__tablename__} LIMIT :limit OFFSET :offset"),
                {"limit": limit, "offset": offset}
            )
            return result.fetchall()
    
    async def update(self, record_id: str, **kwargs) -> Optional[Base]:
        """Update a record by ID in the database."""
        async with self.db_manager.get_async_session() as session:
            instance = await session.get(self.model_class, record_id)
            if instance:
                for key, value in kwargs.items():
                    setattr(instance, key, value)
                await session.flush()
                await session.refresh(instance)
            return instance
    
    async def delete(self, record_id: str) -> bool:
        """Delete a record by ID from the database."""
        async with self.db_manager.get_async_session() as session:
            instance = await session.get(self.model_class, record_id)
            if instance:
                await session.delete(instance)
                return True
            return False
    
    async def count(self) -> int:
        """Count total records in the database."""
        async with self.db_manager.get_async_session() as session:
            result = await session.execute(
                text(f"SELECT COUNT(*) FROM {self.model_class.__tablename__}")
            )
            return result.scalar()
    
    async def find_by_criteria(self, **criteria) -> List[Base]:
        """Find records by criteria in the database."""
        async with self.db_manager.get_async_session() as session:
            where_clauses = []
            params = {}
            
            for key, value in criteria.items():
                if hasattr(self.model_class, key):
                    where_clauses.append(f"{key} = :{key}")
                    params[key] = value
            
            if where_clauses:
                query = f"SELECT * FROM {self.model_class.__tablename__} WHERE {' AND '.join(where_clauses)}"
            else:
                query = f"SELECT * FROM {self.model_class.__tablename__}"
            
            result = await session.execute(text(query), params)
            return result.fetchall()


class TransactionManager:
    """
    Transaction manager for handling complex database operations.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    @asynccontextmanager
    async def transaction(self):
        """Execute operations within a database transaction."""
        async with self.db_manager.get_async_session() as session:
            async with session.begin():
                yield session


class DatabaseInitializer:
    """
    Database initializer for setting up the database with initial data.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def initialize_database(self):
        """Initialize database with tables and seed data."""
        logger.info("Initializing database...")
        
        # Create tables
        await self.db_manager.create_tables()
        
        # Seed initial data
        await self._seed_carriers()
        await self._seed_warehouses()
        
        logger.info("Database initialization completed")
    
    async def _seed_carriers(self):
        """Seed initial carrier data."""
        from .models import CarrierDB, CarrierType
        
        carriers_data = [
            {
                "name": "UPS",
                "carrier_type": CarrierType.UPS,
                "base_rate": 5.99,
                "per_kg_rate": 2.50,
                "max_weight": 70.0,
                "max_dimensions": {"length": 120, "width": 80, "height": 80},
                "delivery_time_days": 2,
                "tracking_url_template": "https://www.ups.com/track?tracknum={tracking_number}"
            },
            {
                "name": "Colis Privé",
                "carrier_type": CarrierType.COLIS_PRIVE,
                "base_rate": 4.99,
                "per_kg_rate": 1.80,
                "max_weight": 30.0,
                "max_dimensions": {"length": 100, "width": 60, "height": 60},
                "delivery_time_days": 3,
                "tracking_url_template": "https://www.colisprive.com/moncolis/pages/detailColis.aspx?numColis={tracking_number}"
            },
            {
                "name": "Chronopost",
                "carrier_type": CarrierType.CHRONOPOST,
                "base_rate": 8.99,
                "per_kg_rate": 3.20,
                "max_weight": 30.0,
                "max_dimensions": {"length": 150, "width": 100, "height": 100},
                "delivery_time_days": 1,
                "tracking_url_template": "https://www.chronopost.fr/tracking-no-cms/suivi-page?listeNumerosLT={tracking_number}"
            },
            {
                "name": "Colissimo",
                "carrier_type": CarrierType.COLISSIMO,
                "base_rate": 6.99,
                "per_kg_rate": 2.10,
                "max_weight": 30.0,
                "max_dimensions": {"length": 150, "width": 100, "height": 100},
                "delivery_time_days": 2,
                "tracking_url_template": "https://www.laposte.fr/outils/suivre-vos-envois?code={tracking_number}"
            }
        ]
        
        async with self.db_manager.get_async_session() as session:
            for carrier_data in carriers_data:
                # Check if carrier already exists
                result = await session.execute(
                    text("SELECT id FROM carriers WHERE name = :name"),
                    {"name": carrier_data["name"]}
                )
                if not result.scalar():
                    carrier = CarrierDB(**carrier_data)
                    session.add(carrier)
        
        logger.info("Carrier data seeded")
    
    async def _seed_warehouses(self):
        """Seed initial warehouse data."""
        from .models import WarehouseDB
        
        warehouses_data = [
            {
                "name": "Paris Distribution Center",
                "address": {
                    "street": "123 Rue de la Logistique",
                    "city": "Paris",
                    "postal_code": "75001",
                    "country": "France",
                    "latitude": 48.8566,
                    "longitude": 2.3522
                },
                "capacity": 10000,
                "operational_hours": {
                    "monday": "08:00-18:00",
                    "tuesday": "08:00-18:00",
                    "wednesday": "08:00-18:00",
                    "thursday": "08:00-18:00",
                    "friday": "08:00-18:00",
                    "saturday": "09:00-15:00",
                    "sunday": "closed"
                },
                "contact_email": "paris@warehouse.com",
                "contact_phone": "+33 1 23 45 67 89"
            },
            {
                "name": "Lyon Regional Hub",
                "address": {
                    "street": "456 Avenue du Commerce",
                    "city": "Lyon",
                    "postal_code": "69001",
                    "country": "France",
                    "latitude": 45.7640,
                    "longitude": 4.8357
                },
                "capacity": 7500,
                "operational_hours": {
                    "monday": "08:00-17:00",
                    "tuesday": "08:00-17:00",
                    "wednesday": "08:00-17:00",
                    "thursday": "08:00-17:00",
                    "friday": "08:00-17:00",
                    "saturday": "closed",
                    "sunday": "closed"
                },
                "contact_email": "lyon@warehouse.com",
                "contact_phone": "+33 4 78 90 12 34"
            }
        ]
        
        async with self.db_manager.get_async_session() as session:
            for warehouse_data in warehouses_data:
                # Check if warehouse already exists
                result = await session.execute(
                    text("SELECT id FROM warehouses WHERE name = :name"),
                    {"name": warehouse_data["name"]}
                )
                if not result.scalar():
                    warehouse = WarehouseDB(**warehouse_data)
                    session.add(warehouse)
        
        logger.info("Warehouse data seeded")


# Global database manager instance
db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global db_manager
    if db_manager is None:
        raise RuntimeError("Database manager not initialized")
    return db_manager


def initialize_database_manager(config: DatabaseConfig) -> DatabaseManager:
    """Initialize the global database manager."""
    global db_manager
    db_manager = DatabaseManager(config)
    return db_manager


async def create_database_manager(config: DatabaseConfig) -> DatabaseManager:
    """Create and initialize a database manager."""
    manager = DatabaseManager(config)
    await manager.initialize_async()
    return manager


# Utility functions
async def execute_raw_query(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Execute a raw SQL query and return results."""
    db = get_database_manager()
    
    async with db.get_async_session() as session:
        result = await session.execute(text(query), params or {})
        return [dict(row) for row in result.fetchall()]


async def check_database_connection() -> bool:
    """Check if database connection is healthy."""
    try:
        db = get_database_manager()
        return await db.health_check()
    except Exception as e:
        logger.error("Database connection check failed", error=str(e))
        return False
