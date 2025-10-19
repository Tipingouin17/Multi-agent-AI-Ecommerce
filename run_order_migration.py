"""
Database Migration Runner for Order Agent Enhancements

This script runs the Order Agent enhancement migration on both Windows and Linux.
It creates all necessary tables, views, and indexes for the enhanced features.
"""

import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


async def run_migration():
    """Run the Order Agent enhancement migration."""
    
    # Get database configuration from environment
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = int(os.getenv('POSTGRES_PORT', 5432))
    db_name = os.getenv('POSTGRES_DB', 'multi_agent_ecommerce')
    db_user = os.getenv('POSTGRES_USER', 'postgres')
    db_password = os.getenv('POSTGRES_PASSWORD', 'postgres123')
    
    print("=" * 70)
    print("Order Agent Enhancement - Database Migration")
    print("=" * 70)
    print(f"\nDatabase Configuration:")
    print(f"  Host: {db_host}")
    print(f"  Port: {db_port}")
    print(f"  Database: {db_name}")
    print(f"  User: {db_user}")
    print()
    
    # Read migration SQL
    migration_file = Path(__file__).parent / 'database' / 'migrations' / '002_order_agent_enhancements.sql'
    
    if not migration_file.exists():
        print(f"ERROR: Migration file not found: {migration_file}")
        return False
    
    print(f"Reading migration from: {migration_file}")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    print(f"Migration SQL loaded: {len(migration_sql)} characters")
    print()
    
    # Connect to database
    print("Connecting to database...")
    
    try:
        conn = await asyncpg.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            timeout=30
        )
        
        print("✓ Connected successfully")
        print()
        
        # Run migration
        print("Running migration...")
        print("-" * 70)
        
        try:
            await conn.execute(migration_sql)
            print("✓ Migration completed successfully")
            print()
            
            # Verify tables were created
            print("Verifying tables...")
            
            tables_to_check = [
                'order_modifications',
                'order_splits',
                'partial_shipments',
                'fulfillment_plans',
                'delivery_attempts',
                'cancellation_requests',
                'order_timeline',
                'order_notes',
                'order_tags',
                'gift_options',
                'scheduled_deliveries'
            ]
            
            for table in tables_to_check:
                result = await conn.fetchval(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = $1
                    )
                    """,
                    table
                )
                
                if result:
                    print(f"  ✓ {table}")
                else:
                    print(f"  ✗ {table} - NOT FOUND")
            
            print()
            
            # Verify views were created
            print("Verifying views...")
            
            views_to_check = [
                'order_fulfillment_summary',
                'order_cancellation_stats',
                'order_modification_audit'
            ]
            
            for view in views_to_check:
                result = await conn.fetchval(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.views 
                        WHERE table_schema = 'public' 
                        AND table_name = $1
                    )
                    """,
                    view
                )
                
                if result:
                    print(f"  ✓ {view}")
                else:
                    print(f"  ✗ {view} - NOT FOUND")
            
            print()
            print("=" * 70)
            print("Migration completed successfully!")
            print("=" * 70)
            print()
            print("Next steps:")
            print("1. Review ORDER_AGENT_INTEGRATION_GUIDE.md")
            print("2. Test the enhanced features")
            print("3. Integrate into order_agent.py")
            print()
            
            return True
            
        except Exception as e:
            print(f"\n✗ Migration failed: {e}")
            print()
            print("Error details:")
            print(str(e))
            return False
        
        finally:
            await conn.close()
            print("Database connection closed")
    
    except Exception as e:
        print(f"\n✗ Failed to connect to database: {e}")
        print()
        print("Please check:")
        print("1. PostgreSQL is running")
        print("2. Database credentials in .env are correct")
        print("3. Database exists")
        print("4. Network connectivity")
        return False


def main():
    """Main entry point."""
    try:
        success = asyncio.run(run_migration())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

