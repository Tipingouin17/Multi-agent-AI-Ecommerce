#!/usr/bin/env python3
"""
Database Reset Script
Drops and recreates the database using Python/psycopg2
"""

import sys
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from shared.db_connection import get_database_url
import re

def reset_database():
    """Drop and recreate the database"""
    print("\n" + "="*60)
    print("🔄 DATABASE RESET")
    print("="*60 + "\n")
    
    # Get database URL and parse it
    db_url = get_database_url()
    
    # Parse URL: postgresql://user:password@host:port/database
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+)', db_url)
    if not match:
        print("\u274c Error: Could not parse database URL")
        return 1
    
    user, password, host, port, db_name = match.groups()
    
    print(f"⚠️  WARNING: This will DELETE database '{db_name}'!")
    print("\nPress Ctrl+C to cancel...")
    input("Press Enter to continue...")
    print()
    
    # Connect to postgres database (not the target database)
    try:
        print(f"🔗 Connecting to PostgreSQL server...")
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database='postgres'  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print(f"✅ Connected successfully!\n")
        
        # Terminate existing connections to target database
        print(f"🔌 Terminating existing connections to '{db_name}'...")
        cursor.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{db_name}'
            AND pid <> pg_backend_pid();
        """)
        print("✅ Connections terminated\n")
        
        # Drop database
        print(f"🗑️  Dropping database '{db_name}'...")
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name};")
        print("✅ Database dropped\n")
        
        # Create database
        print(f"🔨 Creating database '{db_name}'...")
        cursor.execute(f"CREATE DATABASE {db_name};")
        print("✅ Database created\n")
        
        cursor.close()
        conn.close()
        
        print("="*60)
        print("✅ DATABASE RESET COMPLETE!")
        print("="*60)
        print(f"\n📊 Database '{db_name}' is ready for initialization")
        print("\n📝 Next steps:")
        print("   1. Run: python init_database.py")
        print("   2. Run: python seed_database.py")
        print()
        
        return 0
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ Connection Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check PostgreSQL is running")
        print("   2. Verify credentials in environment variables:")
        print("      - POSTGRES_HOST (default: localhost)")
        print("      - POSTGRES_PORT (default: 5432)")
        print("      - POSTGRES_USER (default: postgres)")
        print("      - POSTGRES_PASSWORD (default: postgres)")
        print("   3. Ensure user has permission to create databases")
        return 1
        
    except psycopg2.Error as e:
        print(f"\n❌ Database Error: {e}")
        return 1
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = reset_database()
    sys.exit(exit_code)
