"""
Unified Database Connection Module

This module provides a SINGLE, centralized way for all agents to connect to the database.
NO MORE multiple DatabaseConfig classes or different connection methods!

Usage:
    from shared.db_connection import get_database_url, get_async_database_url
    
    # For sync connections
    url = get_database_url()
    
    # For async connections
    async_url = get_async_database_url()
"""

import os
from dotenv import load_dotenv

# Load environment variables ONCE at module import
load_dotenv()


def get_database_url(async_mode: bool = False) -> str:
    """
    Get the database connection URL.
    
    This is the ONLY function all agents should use to get database URLs.
    It reads from environment variables in this priority:
    1. DATABASE_* variables (preferred)
    2. POSTGRES_* variables (fallback for Docker compatibility)
    3. Hardcoded defaults (last resort)
    
    Args:
        async_mode: If True, returns postgresql+asyncpg:// URL for async connections
                   If False, returns postgresql:// URL for sync connections
    
    Returns:
        Database connection URL string
    """
    # Read from environment with fallbacks
    host = os.getenv('DATABASE_HOST') or os.getenv('POSTGRES_HOST') or 'localhost'
    port = os.getenv('DATABASE_PORT') or os.getenv('POSTGRES_PORT') or '5432'
    database = os.getenv('DATABASE_NAME') or os.getenv('POSTGRES_DB') or 'multi_agent_ecommerce'
    user = os.getenv('DATABASE_USER') or os.getenv('POSTGRES_USER') or 'postgres'
    password = os.getenv('DATABASE_PASSWORD') or os.getenv('POSTGRES_PASSWORD') or 'postgres'
    
    # Debug logging (can be removed after testing)
    print(f"[DB Connection] Using credentials: user={user}, password={'*' * len(password)}, host={host}, port={port}, db={database}")
    
    # Build URL
    if async_mode:
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
    else:
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def get_async_database_url() -> str:
    """
    Get the async database connection URL (postgresql+asyncpg://).
    
    This is a convenience wrapper for get_database_url(async_mode=True).
    """
    return get_database_url(async_mode=True)


def get_sync_database_url() -> str:
    """
    Get the sync database connection URL (postgresql://).
    
    This is a convenience wrapper for get_database_url(async_mode=False).
    """
    return get_database_url(async_mode=False)


# For backward compatibility, provide DATABASE_URL constant
DATABASE_URL = get_database_url()
ASYNC_DATABASE_URL = get_async_database_url()


if __name__ == "__main__":
    # Test the connection URL generation
    print("Sync URL:", get_sync_database_url())
    print("Async URL:", get_async_database_url())

