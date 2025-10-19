#!/usr/bin/env python3
"""
Database Initialization Script for Multi-Agent E-commerce System

This script creates all necessary database tables for the system.
Run this once before starting the agents.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.database import DatabaseManager
from shared.models import DatabaseConfig


async def init_database():
    """Initialize the database with all required tables."""
    
    print("="*70)
    print("Multi-Agent E-commerce System - Database Initialization")
    print("="*70)
    print()
    
    # Get database configuration from environment
    db_config = DatabaseConfig(
        host=os.getenv("DATABASE_HOST", "localhost"),
        port=int(os.getenv("DATABASE_PORT", "5432")),
        database=os.getenv("DATABASE_NAME", "multi_agent_ecommerce"),
        username=os.getenv("DATABASE_USER", "postgres"),
        password=os.getenv("DATABASE_PASSWORD", "postgres"),
        echo=False
    )
    
    print(f"Database Configuration:")
    print(f"  Host: {db_config.host}")
    print(f"  Port: {db_config.port}")
    print(f"  Database: {db_config.database}")
    print(f"  User: {db_config.username}")
    print()
    
    # Create database manager
    db_manager = DatabaseManager(db_config)
    
    try:
        print("Initializing database connection...")
        await db_manager.initialize_async()
        print("✓ Database connection established")
        print()
        
        print("Creating database tables...")
        await db_manager.create_tables()
        print("✓ All tables created successfully!")
        print()
        
        print("="*70)
        print("Database initialization complete!")
        print("="*70)
        print()
        print("You can now start the agents with: .\\start-system.ps1")
        print()
        
        return True
        
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Ensure PostgreSQL is running")
        print("  2. Check your .env file has correct database credentials")
        print("  3. Verify the database exists:")
        print(f"     psql -h {db_config.host} -U {db_config.username} -l")
        print("  4. Create database if needed:")
        print(f"     createdb -h {db_config.host} -U {db_config.username} {db_config.database}")
        print()
        return False
    
    finally:
        if db_manager.async_engine:
            await db_manager.async_engine.dispose()


if __name__ == "__main__":
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("Warning: python-dotenv not installed, using environment variables only")
    
    # Run initialization
    success = asyncio.run(init_database())
    sys.exit(0 if success else 1)

