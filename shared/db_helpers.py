"""
Universal Database Helper Module
Provides common CRUD operations for all agents
"""

import logging
from typing import List, Dict, Any, Optional, Type, TypeVar
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .database import DatabaseManager
from .models import Base

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Base)


class DatabaseHelper:
    """
    Universal database helper providing common CRUD operations
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create(self, session: AsyncSession, model: Type[T], data: Dict[str, Any]) -> T:
        """
        Create a new record
        
        Args:
            session: Database session
            model: SQLAlchemy model class
            data: Data dictionary
        
        Returns:
            Created record
        """
        try:
            # Add UUID if not present
            if hasattr(model, 'id') and 'id' not in data:
                data['id'] = uuid4()
            
            # Add timestamps if not present
            if hasattr(model, 'created_at') and 'created_at' not in data:
                data['created_at'] = datetime.utcnow()
            if hasattr(model, 'updated_at'):
                data['updated_at'] = datetime.utcnow()
            
            instance = model(**data)
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
            
            logger.info(f"Created {model.__name__} with ID: {instance.id}")
            return instance
            
        except Exception as e:
            logger.error(f"Error creating {model.__name__}: {e}")
            raise
    
    async def get_by_id(self, session: AsyncSession, model: Type[T], record_id: Any) -> Optional[T]:
        """
        Get record by ID
        
        Args:
            session: Database session
            model: SQLAlchemy model class
            record_id: Record ID
        
        Returns:
            Record or None
        """
        try:
            result = await session.execute(
                select(model).where(model.id == record_id)
            )
            record = result.scalar_one_or_none()
            
            if record:
                logger.debug(f"Found {model.__name__} with ID: {record_id}")
            else:
                logger.debug(f"{model.__name__} not found with ID: {record_id}")
            
            return record
            
        except Exception as e:
            logger.error(f"Error getting {model.__name__} by ID {record_id}: {e}")
            raise
    
    async def get_all(
        self,
        session: AsyncSession,
        model: Type[T],
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[Any] = None
    ) -> List[T]:
        """
        Get all records with pagination and filtering
        
        Args:
            session: Database session
            model: SQLAlchemy model class
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Filter conditions
            order_by: Order by clause
        
        Returns:
            List of records
        """
        try:
            query = select(model)
            
            # Apply filters
            if filters:
                conditions = []
                for key, value in filters.items():
                    if hasattr(model, key):
                        if isinstance(value, list):
                            conditions.append(getattr(model, key).in_(value))
                        else:
                            conditions.append(getattr(model, key) == value)
                
                if conditions:
                    query = query.where(and_(*conditions))
            
            # Apply ordering
            if order_by is not None:
                query = query.order_by(order_by)
            elif hasattr(model, 'created_at'):
                query = query.order_by(model.created_at.desc())
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            result = await session.execute(query)
            records = result.scalars().all()
            
            logger.debug(f"Retrieved {len(records)} {model.__name__} records")
            return list(records)
            
        except Exception as e:
            logger.error(f"Error getting all {model.__name__}: {e}")
            raise
    
    async def update_by_id(
        self,
        session: AsyncSession,
        model: Type[T],
        record_id: Any,
        data: Dict[str, Any]
    ) -> Optional[T]:
        """
        Update record by ID
        
        Args:
            session: Database session
            model: SQLAlchemy model class
            record_id: Record ID
            data: Update data
        
        Returns:
            Updated record or None
        """
        try:
            # Add updated_at timestamp
            if hasattr(model, 'updated_at'):
                data['updated_at'] = datetime.utcnow()
            
            stmt = (
                update(model)
                .where(model.id == record_id)
                .values(**data)
                .returning(model)
            )
            
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()
            
            if record:
                await session.flush()
                await session.refresh(record)
                logger.info(f"Updated {model.__name__} with ID: {record_id}")
            else:
                logger.warning(f"{model.__name__} not found for update with ID: {record_id}")
            
            return record
            
        except Exception as e:
            logger.error(f"Error updating {model.__name__} with ID {record_id}: {e}")
            raise
    
    async def delete_by_id(self, session: AsyncSession, model: Type[T], record_id: Any) -> bool:
        """
        Delete record by ID
        
        Args:
            session: Database session
            model: SQLAlchemy model class
            record_id: Record ID
        
        Returns:
            True if deleted, False if not found
        """
        try:
            stmt = delete(model).where(model.id == record_id)
            result = await session.execute(stmt)
            
            deleted = result.rowcount > 0
            
            if deleted:
                logger.info(f"Deleted {model.__name__} with ID: {record_id}")
            else:
                logger.warning(f"{model.__name__} not found for deletion with ID: {record_id}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting {model.__name__} with ID {record_id}: {e}")
            raise
    
    async def count(
        self,
        session: AsyncSession,
        model: Type[T],
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count records with optional filtering
        
        Args:
            session: Database session
            model: SQLAlchemy model class
            filters: Filter conditions
        
        Returns:
            Count of records
        """
        try:
            query = select(func.count()).select_from(model)
            
            # Apply filters
            if filters:
                conditions = []
                for key, value in filters.items():
                    if hasattr(model, key):
                        if isinstance(value, list):
                            conditions.append(getattr(model, key).in_(value))
                        else:
                            conditions.append(getattr(model, key) == value)
                
                if conditions:
                    query = query.where(and_(*conditions))
            
            result = await session.execute(query)
            count = result.scalar()
            
            logger.debug(f"Counted {count} {model.__name__} records")
            return count
            
        except Exception as e:
            logger.error(f"Error counting {model.__name__}: {e}")
            raise
    
    async def exists(self, session: AsyncSession, model: Type[T], record_id: Any) -> bool:
        """
        Check if record exists by ID
        
        Args:
            session: Database session
            model: SQLAlchemy model class
            record_id: Record ID
        
        Returns:
            True if exists, False otherwise
        """
        try:
            query = select(func.count()).select_from(model).where(model.id == record_id)
            result = await session.execute(query)
            count = result.scalar()
            
            exists = count > 0
            logger.debug(f"{model.__name__} with ID {record_id} exists: {exists}")
            return exists
            
        except Exception as e:
            logger.error(f"Error checking existence of {model.__name__} with ID {record_id}: {e}")
            raise
    
    async def bulk_create(self, session: AsyncSession, model: Type[T], data_list: List[Dict[str, Any]]) -> List[T]:
        """
        Create multiple records in bulk
        
        Args:
            session: Database session
            model: SQLAlchemy model class
            data_list: List of data dictionaries
        
        Returns:
            List of created records
        """
        try:
            instances = []
            
            for data in data_list:
                # Add UUID if not present
                if hasattr(model, 'id') and 'id' not in data:
                    data['id'] = uuid4()
                
                # Add timestamps if not present
                if hasattr(model, 'created_at') and 'created_at' not in data:
                    data['created_at'] = datetime.utcnow()
                if hasattr(model, 'updated_at'):
                    data['updated_at'] = datetime.utcnow()
                
                instance = model(**data)
                instances.append(instance)
            
            session.add_all(instances)
            await session.flush()
            
            for instance in instances:
                await session.refresh(instance)
            
            logger.info(f"Bulk created {len(instances)} {model.__name__} records")
            return instances
            
        except Exception as e:
            logger.error(f"Error bulk creating {model.__name__}: {e}")
            raise
    
    async def search(
        self,
        session: AsyncSession,
        model: Type[T],
        search_fields: List[str],
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[T]:
        """
        Search records by text in specified fields
        
        Args:
            session: Database session
            model: SQLAlchemy model class
            search_fields: List of field names to search
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of matching records
        """
        try:
            conditions = []
            
            for field in search_fields:
                if hasattr(model, field):
                    field_attr = getattr(model, field)
                    conditions.append(field_attr.ilike(f"%{search_term}%"))
            
            if not conditions:
                logger.warning(f"No valid search fields found for {model.__name__}")
                return []
            
            query = (
                select(model)
                .where(or_(*conditions))
                .offset(skip)
                .limit(limit)
            )
            
            result = await session.execute(query)
            records = result.scalars().all()
            
            logger.debug(f"Found {len(records)} {model.__name__} records matching '{search_term}'")
            return list(records)
            
        except Exception as e:
            logger.error(f"Error searching {model.__name__}: {e}")
            raise
    
    def to_dict(self, instance: Base) -> Dict[str, Any]:
        """
        Convert SQLAlchemy model instance to dictionary
        
        Args:
            instance: Model instance
        
        Returns:
            Dictionary representation
        """
        result = {}
        
        for column in instance.__table__.columns:
            value = getattr(instance, column.name)
            
            # Convert special types
            if isinstance(value, UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.isoformat()
            
            result[column.name] = value
        
        return result
    
    def to_dict_list(self, instances: List[Base]) -> List[Dict[str, Any]]:
        """
        Convert list of SQLAlchemy model instances to list of dictionaries
        
        Args:
            instances: List of model instances
        
        Returns:
            List of dictionary representations
        """
        return [self.to_dict(instance) for instance in instances]


# Singleton instance
_db_helper_instance: Optional[DatabaseHelper] = None


def get_db_helper(db_manager: DatabaseManager) -> DatabaseHelper:
    """
    Get or create DatabaseHelper singleton instance
    
    Args:
        db_manager: Database manager instance
    
    Returns:
        DatabaseHelper instance
    """
    global _db_helper_instance
    
    if _db_helper_instance is None:
        _db_helper_instance = DatabaseHelper(db_manager)
    
    return _db_helper_instance

