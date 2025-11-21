#!/usr/bin/env python3
"""
Create a test merchant for product creation (FIXED VERSION)
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
    cursor.execute("SELECT id, business_name, status FROM merchants WHERE id = 1")
    existing = cursor.fetchone()
    
    if existing:
        print(f"✅ Merchant already exists:")
        print(f"   ID: {existing[0]}")
        print(f"   Name: {existing[1]}")
        print(f"   Status: {existing[2]}")
        print()
        print("You can now create products!")
    else:
        # Create test merchant with actual table columns
        cursor.execute("""
            INSERT INTO merchants (
                id,
                business_name,
                business_type,
                website,
                description,
                status,
                created_at,
                updated_at
            ) VALUES (
                1,
                'Test Merchant',
                'Retail',
                'https://testmerchant.com',
                'Test merchant for product creation',
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
            print(f"   Status: active")
            print()
            print("You can now create products!")
        else:
            print("ℹ️  Merchant already exists (conflict)")
    
    cursor.close()
    conn.close()
    
except psycopg2.Error as e:
    print(f"❌ Database error: {e}")
    print()
    print("Let me try a simpler approach...")
    
    # Try again with minimal fields
    try:
        conn = psycopg2.connect(**config)
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO merchants (business_name, status)
            VALUES ('Test Merchant', 'active')
            ON CONFLICT DO NOTHING
            RETURNING id, business_name;
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"✅ Test merchant created with minimal fields!")
            print(f"   ID: {result[0]}")
            print(f"   Name: {result[1]}")
        
        cursor.close()
        conn.close()
    except Exception as e2:
        print(f"❌ Still failed: {e2}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
