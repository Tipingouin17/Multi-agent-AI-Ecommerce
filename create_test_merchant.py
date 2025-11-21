#!/usr/bin/env python3
"""
Create a test merchant for product creation
"""

import psycopg2
import sys
from datetime import datetime

print("Creating test merchant...")
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
    conn = psycopg2.connect(**config)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Check if merchant already exists
    cursor.execute("SELECT id, business_name FROM merchants WHERE id = 1")
    existing = cursor.fetchone()
    
    if existing:
        print(f"✅ Merchant already exists:")
        print(f"   ID: {existing[0]}")
        print(f"   Name: {existing[1]}")
        print()
        print("You can now create products!")
    else:
        # Create test merchant
        cursor.execute("""
            INSERT INTO merchants (
                id,
                user_id,
                business_name,
                business_email,
                business_phone,
                status,
                created_at,
                updated_at
            ) VALUES (
                1,
                1,
                'Test Merchant',
                'merchant@test.com',
                '+1234567890',
                'active',
                %s,
                %s
            )
            ON CONFLICT (id) DO NOTHING
            RETURNING id, business_name;
        """, (datetime.now(), datetime.now()))
        
        result = cursor.fetchone()
        if result:
            print(f"✅ Test merchant created successfully!")
            print(f"   ID: {result[0]}")
            print(f"   Name: {result[1]}")
            print()
            print("You can now create products!")
        else:
            print("ℹ️  Merchant already exists (conflict)")
    
    cursor.close()
    conn.close()
    
except psycopg2.Error as e:
    print(f"❌ Database error: {e}")
    print()
    print("Possible issues:")
    print("- Merchants table doesn't exist")
    print("- User with ID=1 doesn't exist (foreign key)")
    print()
    print("Try creating a user first, or I can help you fix the schema.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
