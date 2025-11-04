#!/usr/bin/env python3.11
"""
Simple Database Seeding Script
Matches the new schema exactly
"""

import psycopg2
from passlib.hash import bcrypt
import random
from datetime import datetime, timedelta
import json

# Connect to database
conn = psycopg2.connect(
    dbname='multi_agent_ecommerce',
    user='postgres',
    password='postgres',
    host='localhost',
    port=5432
)
cur = conn.cursor()

print("Starting database seeding...")

# 1. Seed Users
print("1. Seeding users...")
users_data = [
    ('admin@example.com', 'admin', bcrypt.hash('admin123'), 'admin', 'System', 'Admin', '+1-555-0001'),
    ('merchant1@example.com', 'merchant1', bcrypt.hash('merchant123'), 'merchant', 'Tech', 'Store', '+1-555-1001'),
    ('merchant2@example.com', 'merchant2', bcrypt.hash('merchant123'), 'merchant', 'Fashion', 'Hub', '+1-555-1002'),
    ('customer1@example.com', 'customer1', bcrypt.hash('customer123'), 'customer', 'Alice', 'Johnson', '+1-555-2001'),
    ('customer2@example.com', 'customer2', bcrypt.hash('customer123'), 'customer', 'Bob', 'Smith', '+1-555-2002'),
]

for user in users_data:
    cur.execute('''
        INSERT INTO users (email, username, password_hash, role, first_name, last_name, phone, is_active, is_verified)
        VALUES (%s, %s, %s, %s, %s, %s, %s, true, true)
    ''', user)

conn.commit()
print(f"   ✓ Seeded {len(users_data)} users")

# 2. Seed Merchants
print("2. Seeding merchants...")
cur.execute("SELECT id FROM users WHERE role = 'merchant'")
merchant_user_ids = [row[0] for row in cur.fetchall()]

for i, user_id in enumerate(merchant_user_ids):
    cur.execute('''
        INSERT INTO merchants (user_id, business_name, business_type, tax_id, total_sales, total_orders, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (user_id, f'Business {i+1}', 'Retail', f'TAX-{i+1:03d}', 50000.00, 200, 'active'))

conn.commit()
print(f"   ✓ Seeded {len(merchant_user_ids)} merchants")

# 3. Seed Categories
print("3. Seeding categories...")
categories = [
    ('Electronics', 'electronics', 'Electronic devices'),
    ('Fashion', 'fashion', 'Clothing and accessories'),
    ('Home', 'home', 'Home products'),
]

for cat in categories:
    cur.execute('''
        INSERT INTO categories (name, slug, description, is_active)
        VALUES (%s, %s, %s, true)
    ''', cat)

conn.commit()
print(f"   ✓ Seeded {len(categories)} categories")

# 4. Seed Warehouses
print("4. Seeding warehouses...")
warehouses = [
    ('Main Warehouse', 'WH-001', '123 Industrial Blvd', 'Los Angeles', 'CA', 'USA', '90001', 50000, 25000),
    ('East Hub', 'WH-002', '456 Logistics Way', 'New York', 'NY', 'USA', '10001', 40000, 18000),
]

for wh in warehouses:
    cur.execute('''
        INSERT INTO warehouses (name, code, address, city, state, country, postal_code, capacity, current_utilization, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, true)
    ''', wh)

conn.commit()
print(f"   ✓ Seeded {len(warehouses)} warehouses")

# 5. Seed Products
print("5. Seeding products...")
cur.execute("SELECT id FROM merchants LIMIT 1")
merchant_id = cur.fetchone()[0]

cur.execute("SELECT id FROM categories")
category_ids = [row[0] for row in cur.fetchall()]

products = [
    ('Laptop Pro', 'High-performance laptop', 1299.99, 899.00, 2.5),
    ('Smartphone X', 'Latest smartphone', 999.99, 650.00, 0.2),
    ('T-Shirt', 'Cotton t-shirt', 19.99, 8.00, 0.2),
    ('Jeans', 'Denim jeans', 49.99, 22.00, 0.6),
    ('Coffee Maker', 'Programmable coffee maker', 89.99, 40.00, 4.0),
]

for i, prod in enumerate(products):
    cur.execute('''
        INSERT INTO products (merchant_id, category_id, sku, name, slug, description, price, cost, weight, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
    ''', (merchant_id, category_ids[i % len(category_ids)], f'SKU-{i+1:05d}', 
          prod[0], prod[0].lower().replace(' ', '-'), prod[1], prod[2], prod[3], prod[4]))

conn.commit()
print(f"   ✓ Seeded {len(products)} products")

# 6. Seed Inventory
print("6. Seeding inventory...")
cur.execute("SELECT id FROM products")
product_ids = [row[0] for row in cur.fetchall()]

cur.execute("SELECT id FROM warehouses")
warehouse_ids = [row[0] for row in cur.fetchall()]

inventory_count = 0
for product_id in product_ids:
    for warehouse_id in warehouse_ids:
        cur.execute('''
            INSERT INTO inventory (product_id, warehouse_id, quantity, reserved_quantity, reorder_point)
            VALUES (%s, %s, %s, %s, %s)
        ''', (product_id, warehouse_id, random.randint(50, 200), 0, 10))
        inventory_count += 1

conn.commit()
print(f"   ✓ Seeded {inventory_count} inventory records")

# 7. Seed Customers
print("7. Seeding customers...")
cur.execute("SELECT id FROM users WHERE role = 'customer'")
customer_user_ids = [row[0] for row in cur.fetchall()]

for user_id in customer_user_ids:
    cur.execute('''
        INSERT INTO customers (user_id, customer_group, total_orders, total_spent)
        VALUES (%s, %s, %s, %s)
    ''', (user_id, 'regular', random.randint(1, 10), round(random.uniform(100, 1000), 2)))

conn.commit()
print(f"   ✓ Seeded {len(customer_user_ids)} customers")

# 8. Seed Addresses
print("8. Seeding addresses...")
for user_id in customer_user_ids:
    cur.execute('''
        INSERT INTO addresses (user_id, address_type, first_name, last_name, address_line1, city, state, country, postal_code, is_default)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, true)
    ''', (user_id, 'both', 'John', 'Doe', '123 Main St', 'New York', 'NY', 'USA', '10001'))

conn.commit()
print(f"   ✓ Seeded {len(customer_user_ids)} addresses")

# 9. Seed Orders
print("9. Seeding orders...")
cur.execute("SELECT id FROM customers")
customer_ids = [row[0] for row in cur.fetchall()]

cur.execute("SELECT id FROM addresses")
address_ids = [row[0] for row in cur.fetchall()]

for i in range(20):
    customer_id = random.choice(customer_ids)
    address_id = random.choice(address_ids)
    subtotal = round(random.uniform(50, 500), 2)
    tax = round(subtotal * 0.08, 2)
    shipping = 10.00
    total = subtotal + tax + shipping
    
    cur.execute('''
        INSERT INTO orders (order_number, customer_id, merchant_id, status, payment_status, fulfillment_status,
                          subtotal, tax, shipping_cost, total, shipping_address_id, billing_address_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (f'ORD-{i+1:06d}', customer_id, merchant_id, 'confirmed', 'paid', 'fulfilled',
          subtotal, tax, shipping, total, address_id, address_id))

conn.commit()
print(f"   ✓ Seeded 20 orders")

# 10. Seed Order Items
print("10. Seeding order items...")
cur.execute("SELECT id FROM orders")
order_ids = [row[0] for row in cur.fetchall()]

order_items_count = 0
for order_id in order_ids:
    num_items = random.randint(1, 3)
    selected_products = random.sample(product_ids, min(num_items, len(product_ids)))
    
    for product_id in selected_products:
        cur.execute("SELECT sku, name, price FROM products WHERE id = %s", (product_id,))
        sku, name, price = cur.fetchone()
        quantity = random.randint(1, 2)
        total_price = float(price) * quantity
        
        cur.execute('''
            INSERT INTO order_items (order_id, product_id, sku, name, quantity, unit_price, total_price)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (order_id, product_id, sku, name, quantity, price, total_price))
        order_items_count += 1

conn.commit()
print(f"   ✓ Seeded {order_items_count} order items")

# 11. Seed Carriers
print("11. Seeding carriers...")
carriers = [
    ('UPS', 'ups', 'https://ups.com/track?num={tracking_number}'),
    ('FedEx', 'fedex', 'https://fedex.com/track?num={tracking_number}'),
    ('USPS', 'usps', 'https://usps.com/track?num={tracking_number}'),
]

for carrier in carriers:
    cur.execute('''
        INSERT INTO carriers (name, code, tracking_url_template, is_active)
        VALUES (%s, %s, %s, true)
    ''', carrier)

conn.commit()
print(f"   ✓ Seeded {len(carriers)} carriers")

# 12. Seed Alerts
print("12. Seeding alerts...")
alerts = [
    ('inventory_low', 'warning', 'Low Inventory', 'Product running low in warehouse', 'inventory_agent', 'active'),
    ('order_delayed', 'warning', 'Order Delayed', 'Order shipment delayed', 'order_agent', 'active'),
    ('system_ok', 'info', 'System Healthy', 'All systems operational', 'infrastructure_agent', 'resolved'),
]

for alert in alerts:
    cur.execute('''
        INSERT INTO alerts (alert_type, severity, title, message, source, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', alert)

conn.commit()
print(f"   ✓ Seeded {len(alerts)} alerts")

# Close connection
cur.close()
conn.close()

print("\n" + "="*60)
print("✓ DATABASE SEEDING COMPLETE!")
print("="*60)
print("\nLogin Credentials:")
print("  Admin: admin@example.com / admin123")
print("  Merchant: merchant1@example.com / merchant123")
print("  Customer: customer1@example.com / customer123")
print()
