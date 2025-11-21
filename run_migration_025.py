#!/usr/bin/env python3
"""
Quick script to run migration 025
"""

import psycopg2
import sys

print("Running migration 025: Fix array columns to JSON")
print()

# Database config
config = {
    'host': 'localhost',
    'port': '5432',
    'database': 'multi_agent_ecommerce',
    'user': 'postgres',
    'password': 'postgres'
}

try:
    # Read migration file
    with open('database/migrations/025_fix_array_columns_to_json_v2.sql', 'r') as f:
        sql = f.read()
    
    print("Connecting to database...")
    conn = psycopg2.connect(**config)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("Executing migration...")
    cursor.execute(sql)
    
    cursor.close()
    conn.close()
    
    print()
    print("✅ Migration completed successfully!")
    print()
    print("Next steps:")
    print("1. Restart your backend (product_agent_v3.py)")
    print("2. Try creating a product again")
    print()
    
except FileNotFoundError:
    print("❌ Error: Migration file not found!")
    print("Make sure you're in the project root directory")
    sys.exit(1)
except psycopg2.Error as e:
    print(f"❌ Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
