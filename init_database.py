#!/usr/bin/env python3
"""
Database Initialization Script
Creates all required tables in the PostgreSQL database
"""

import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from shared.db_models import Base
from shared.db_connection import get_database_url
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError

def check_database_connection(engine):
    """Check if database is accessible"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except OperationalError as e:
        print(f"❌ Cannot connect to database: {e}")
        return False

def get_existing_tables(engine):
    """Get list of existing tables"""
    inspector = inspect(engine)
    return inspector.get_table_names()

def create_all_tables(engine):
    """Create all tables defined in models"""
    print("📋 Creating database tables...")
    
    # Get existing tables
    existing_tables = get_existing_tables(engine)
    print(f"\n📊 Found {len(existing_tables)} existing tables:")
    for table in sorted(existing_tables):
        print(f"   ✓ {table}")
    
    # Get all model tables
    model_tables = Base.metadata.tables.keys()
    print(f"\n📦 Models define {len(model_tables)} tables:")
    for table in sorted(model_tables):
        status = "✓ exists" if table in existing_tables else "➕ will create"
        print(f"   {status}: {table}")
    
    # Create missing tables
    new_tables = [t for t in model_tables if t not in existing_tables]
    
    if new_tables:
        print(f"\n🔨 Creating {len(new_tables)} new tables...")
        Base.metadata.create_all(engine, checkfirst=True)
        print("✅ Tables created successfully!")
    else:
        print("\n✅ All tables already exist!")
    
    # Verify final state
    final_tables = get_existing_tables(engine)
    print(f"\n📊 Final database state: {len(final_tables)} tables")
    
    return final_tables

def main():
    """Main initialization function"""
    print("\n" + "="*60)
    print("🗄️  DATABASE INITIALIZATION")
    print("="*60 + "\n")
    
    # Get database URL
    db_url = get_database_url()
    print(f"🔗 Connecting to database...")
    print(f"   URL: {db_url.split('@')[1] if '@' in db_url else 'localhost'}\n")
    
    # Create engine
    engine = create_engine(db_url, pool_pre_ping=True)
    
    # Check connection
    if not check_database_connection(engine):
        print("\n❌ Failed to connect to database!")
        print("\n💡 Troubleshooting:")
        print("   1. Check PostgreSQL is running")
        print("   2. Verify connection settings:")
        print("      - POSTGRES_HOST (default: localhost)")
        print("      - POSTGRES_PORT (default: 5432)")
        print("      - POSTGRES_DB (default: ecommerce_db)")
        print("      - POSTGRES_USER (default: postgres)")
        print("      - POSTGRES_PASSWORD")
        print("   3. Ensure database exists (create it if needed)")
        return 1
    
    print("✅ Database connection successful!\n")
    
    try:
        # Create all tables
        final_tables = create_all_tables(engine)
        
        print("\n" + "="*60)
        print("✅ DATABASE INITIALIZATION COMPLETED!")
        print("="*60)
        print(f"\n📊 Total tables: {len(final_tables)}")
        print("\n🎉 Your database is ready for seeding!")
        print("\n📝 Next steps:")
        print("   1. Run: SeedDatabase.bat")
        print("   2. Start agents: StartPlatform.bat")
        print("   3. Open dashboard: http://localhost:5173")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
