#!/usr/bin/env python3
"""
Migration script to add extra_data column to offers table
"""

import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from shared.db_connection import get_database_url
from sqlalchemy import create_engine, text

def migrate_offers_table():
    """Add extra_data column to offers table if it doesn't exist"""
    print("=" * 60)
    print("🔧 OFFERS TABLE MIGRATION")
    print("=" * 60)
    
    engine = create_engine(get_database_url())
    
    try:
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='offers' AND column_name='extra_data'
            """))
            
            if result.fetchone():
                print("✅ Column 'extra_data' already exists!")
                return
            
            print("➕ Adding 'extra_data' column to offers table...")
            
            # Add the column
            conn.execute(text("""
                ALTER TABLE offers 
                ADD COLUMN extra_data JSON
            """))
            
            conn.commit()
            
            print("✅ Column 'extra_data' added successfully!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("=" * 60)
    print("✅ MIGRATION COMPLETED!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    migrate_offers_table()
