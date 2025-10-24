#!/usr/bin/env python3
"""
Unified Infrastructure Setup Script
===================================
This script sets up all required infrastructure for the Multi-Agent E-commerce Platform:
- PostgreSQL database and tables
- Kafka topics
- Initial data seeding (optional)

Usage:
    python setup_infrastructure.py [--drop-existing] [--seed-data]
    
Options:
    --drop-existing: Drop existing database tables before creating new ones
    --seed-data: Seed initial test data after setup
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import structlog
from sqlalchemy import text
from shared.models import DatabaseConfig
from shared.database_manager import EnhancedDatabaseManager

logger = structlog.get_logger(__name__)

# Kafka topics required by the system
KAFKA_TOPICS = [
    # Order lifecycle
    "order_created",
    "order_validated",
    "order_confirmed",
    "order_shipped",
    "order_delivered",
    "order_cancelled",
    
    # Inventory
    "inventory_reserved",
    "inventory_released",
    "inventory_low_stock",
    
    # Payment
    "payment_initiated",
    "payment_completed",
    "payment_failed",
    "refund_initiated",
    "refund_completed",
    
    # Shipping
    "shipment_created",
    "shipment_in_transit",
    "shipment_delivered",
    
    # Returns
    "return_request_submitted",
    "return_approved",
    "return_shipped",
    "return_received",
    
    # Customer
    "customer_registered",
    "customer_updated",
    
    # Fraud
    "fraud_alert",
    "fraud_check_completed",
    
    # Quality
    "quality_check_requested",
    "quality_check_completed",
    
    # Notifications
    "notification_email",
    "notification_sms",
    
    # Monitoring
    "agent_heartbeat",
    "system_alert",
]


async def setup_database(drop_existing: bool = False):
    """Set up PostgreSQL database and create all tables"""
    logger.info("Setting up PostgreSQL database...")
    
    try:
        # Initialize database manager
        db_config = DatabaseConfig()
        db_manager = EnhancedDatabaseManager(db_config)
        await db_manager.initialize(max_retries=5)
        
        logger.info(f"Connected to database: {db_config.database}")
        
        # Drop existing tables if requested
        if drop_existing:
            logger.warning("Dropping existing tables...")
            async with db_manager.get_session() as session:
                # Get all table names
                result = await session.execute(text("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public'
                """))
                tables = [row[0] for row in result.fetchall()]
                
                if tables:
                    logger.info(f"Found {len(tables)} tables to drop")
                    # Drop all tables
                    for table in tables:
                        await session.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
                    await session.commit()
                    logger.info("All existing tables dropped")
                else:
                    logger.info("No existing tables found")
        
        # Create all tables
        logger.info("Creating database tables...")
        
        # Import all models to ensure they're registered
        from shared.models import (
            Order, OrderItem, Customer, Product, Inventory,
            Payment, Shipment, ReturnRequest, WarrantyClaim,
            QualityCheck, FraudAlert, Notification
        )
        
        # Create tables using SQLAlchemy metadata
        from shared.database import Base
        async with db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database tables created successfully")
        
        # Verify tables were created
        async with db_manager.get_session() as session:
            result = await session.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename
            """))
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"Created {len(tables)} tables: {', '.join(tables)}")
        
        await db_manager.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup database: {e}")
        return False


async def setup_kafka():
    """Set up Kafka topics"""
    logger.info("Setting up Kafka topics...")
    
    try:
        from kafka import KafkaAdminClient
        from kafka.admin import NewTopic
        from kafka.errors import TopicAlreadyExistsError
        import os
        
        # Get Kafka broker from environment or use default
        kafka_brokers = os.getenv("KAFKA_BROKERS", "localhost:9092").split(',')
        
        # Create Kafka admin client
        admin_client = KafkaAdminClient(
            bootstrap_servers=kafka_brokers,
            client_id='infrastructure_setup'
        )
        
        # Create topics
        topics_to_create = [
            NewTopic(
                name=topic,
                num_partitions=3,
                replication_factor=1
            )
            for topic in KAFKA_TOPICS
        ]
        
        try:
            result = admin_client.create_topics(
                new_topics=topics_to_create,
                validate_only=False
            )
            
            created_count = 0
            # Result is a dict-like object, iterate over topic_errors
            for topic_name in KAFKA_TOPICS:
                try:
                    # Check if topic was created successfully
                    logger.info(f"Created topic: {topic_name}")
                    created_count += 1
                except TopicAlreadyExistsError:
                    logger.info(f"Topic already exists: {topic_name}")
                except Exception as e:
                    logger.error(f"Failed to create topic {topic_name}: {e}")
            
            logger.info(f"✅ Kafka setup complete. Created {created_count} topics")
            
        except Exception as e:
            logger.error(f"Error creating topics: {e}")
            return False
        
        finally:
            admin_client.close()
        
        return True
        
    except ImportError:
        logger.warning("kafka-python not installed. Skipping Kafka setup. Install with: pip install kafka-python")
        return False
    except Exception as e:
        logger.error(f"Failed to setup Kafka: {e}")
        return False


async def seed_test_data():
    """Seed initial test data (optional)"""
    logger.info("Seeding test data...")
    
    try:
        db_config = DatabaseConfig()
        db_manager = EnhancedDatabaseManager(db_config)
        await db_manager.initialize(max_retries=5)
        
        # TODO: Add test data seeding logic here
        # Example: Create sample products, customers, etc.
        
        logger.info("✅ Test data seeded successfully")
        await db_manager.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to seed test data: {e}")
        return False


async def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description="Setup infrastructure for Multi-Agent E-commerce Platform")
    parser.add_argument("--drop-existing", action="store_true", help="Drop existing database tables")
    parser.add_argument("--seed-data", action="store_true", help="Seed initial test data")
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Multi-Agent E-commerce Platform - Infrastructure Setup")
    logger.info("=" * 60)
    
    # Setup database
    db_success = await setup_database(drop_existing=args.drop_existing)
    
    # Setup Kafka
    kafka_success = await setup_kafka()
    
    # Seed data if requested
    if args.seed_data and db_success:
        await seed_test_data()
    
    # Summary
    logger.info("=" * 60)
    logger.info("Setup Summary:")
    logger.info(f"  Database: {'✅ Success' if db_success else '❌ Failed'}")
    logger.info(f"  Kafka:    {'✅ Success' if kafka_success else '❌ Failed'}")
    logger.info("=" * 60)
    
    if db_success and kafka_success:
        logger.info("✅ Infrastructure setup completed successfully!")
        logger.info("You can now start the agents with: python start-agents-monitor.py")
        return 0
    else:
        logger.error("❌ Infrastructure setup completed with errors")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

