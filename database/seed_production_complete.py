#!/usr/bin/env python3
"""
Complete Production Database Seeder
Matches actual database schema and creates realistic data
"""

import random
import uuid
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import Json

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "multi_agent_ecommerce",
    "user": "postgres",
    "password": "postgres123",
}

class CompleteSeeder:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.customer_ids = []
        self.product_ids = []
        self.warehouse_ids = []
        self.order_ids = []
        
    def connect(self):
        print("🔌 Connecting to database...")
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            print("✅ Connected!")
            return True
        except Exception as e:
            print(f"❌ Failed: {e}")
            return False
    
    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("👋 Disconnected")
    
    def seed_warehouses(self):
        print("🏭 Seeding warehouses...")
        
        warehouses = [
            ("Main Warehouse - East Coast", {"street": "123 Industrial Pkwy", "city": "Newark", "state": "NJ", "zip": "07102", "country": "USA"}, 50000, "warehouse.east@example.com", "+1-555-0101"),
            ("Distribution Center - West", {"street": "456 Logistics Dr", "city": "Los Angeles", "state": "CA", "zip": "90001", "country": "USA"}, 75000, "warehouse.west@example.com", "+1-555-0102"),
            ("Fulfillment Hub - Central", {"street": "789 Commerce Blvd", "city": "Chicago", "state": "IL", "zip": "60601", "country": "USA"}, 60000, "warehouse.central@example.com", "+1-555-0103"),
        ]
        
        for name, address, capacity, email, phone in warehouses:
            warehouse_id = str(uuid.uuid4())
            operational_hours = {
                "monday": "8:00-20:00",
                "tuesday": "8:00-20:00",
                "wednesday": "8:00-20:00",
                "thursday": "8:00-20:00",
                "friday": "8:00-20:00",
                "saturday": "9:00-17:00",
                "sunday": "closed"
            }
            
            self.cursor.execute("""
                INSERT INTO warehouses (id, name, address, capacity, operational_hours, contact_email, contact_phone, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (warehouse_id, name, Json(address), capacity, Json(operational_hours), email, phone, datetime.now(), datetime.now()))
            
            self.warehouse_ids.append(warehouse_id)
        
        self.conn.commit()
        print(f"✅ Created {len(self.warehouse_ids)} warehouses")
    
    def seed_customers(self):
        print("👥 Seeding customers...")
        
        first_names = ["John", "Jane", "Bob", "Alice", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack", "Kate", "Liam", "Mia"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Wilson", "Anderson", "Taylor"]
        
        for i in range(50):
            customer_id = str(uuid.uuid4())
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            email = f"{first_name.lower()}.{last_name.lower()}{i}@example.com"
            phone = f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
            
            shipping_address = {
                "street": f"{random.randint(100, 9999)} Main St",
                "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]),
                "state": random.choice(["NY", "CA", "IL", "TX", "AZ", "PA", "FL"]),
                "zip": f"{random.randint(10000, 99999)}",
                "country": "USA"
            }
            
            self.cursor.execute("""
                INSERT INTO customers (id, email, first_name, last_name, phone, shipping_address, billing_address, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (customer_id, email, first_name, last_name, phone, Json(shipping_address), Json(shipping_address), datetime.now(), datetime.now()))
            
            self.customer_ids.append(customer_id)
        
        self.conn.commit()
        print(f"✅ Created {len(self.customer_ids)} customers")
    
    def seed_products(self):
        print("📦 Seeding products...")
        
        products = [
            ("Premium Wireless Headphones", "High-quality wireless headphones with active noise cancellation and 30-hour battery life", "Electronics", "AudioTech", 199.99, 89.99, 0.5, "new", "A"),
            ("Smart Watch Pro", "Advanced smartwatch with health tracking, GPS, and water resistance", "Electronics", "TechWear", 299.99, 149.99, 0.2, "new", "A"),
            ("Bluetooth Speaker", "Portable bluetooth speaker with 360-degree premium sound", "Electronics", "SoundWave", 79.99, 35.00, 0.8, "new", "A"),
            ("USB-C Cable (3ft)", "Fast charging USB-C to USB-C cable, braided design", "Accessories", "CablePro", 12.99, 3.50, 0.05, "new", "A"),
            ("Phone Case - Black", "Protective silicone phone case with shock absorption", "Accessories", "CaseMaster", 24.99, 8.00, 0.1, "new", "A"),
            ("Screen Protector", "Tempered glass screen protector with oleophobic coating", "Accessories", "ProtectPlus", 9.99, 2.50, 0.02, "new", "A"),
            ("Wireless Charger", "Fast 15W wireless charging pad with LED indicator", "Electronics", "ChargeTech", 34.99, 15.00, 0.3, "new", "A"),
            ("Laptop Stand", "Ergonomic aluminum laptop stand with adjustable height", "Office", "ErgoDesk", 49.99, 22.00, 1.2, "new", "A"),
            ("Mechanical Keyboard", "RGB mechanical gaming keyboard with blue switches", "Electronics", "GameGear", 129.99, 65.00, 1.5, "new", "A"),
            ("Gaming Mouse", "High-precision 16000 DPI gaming mouse with programmable buttons", "Electronics", "GameGear", 69.99, 28.00, 0.3, "new", "A"),
            ("Webcam HD", "1080p HD webcam with auto-focus and built-in microphone", "Electronics", "VisionTech", 89.99, 42.00, 0.4, "new", "A"),
            ("External SSD 1TB", "Portable solid state drive with USB 3.2 Gen 2", "Electronics", "DataDrive", 149.99, 75.00, 0.2, "new", "A"),
            ("Monitor 27\"", "4K UHD IPS monitor 27 inch with HDR support", "Electronics", "ViewMax", 399.99, 220.00, 8.5, "new", "A"),
            ("Desk Lamp LED", "Adjustable LED desk lamp with touch control and USB port", "Office", "LightPro", 39.99, 18.00, 1.0, "new", "A"),
            ("Office Chair", "Ergonomic mesh office chair with lumbar support", "Furniture", "ComfortSeating", 249.99, 125.00, 18.0, "new", "A"),
            ("Tablet 10\"", "10-inch tablet with 128GB storage and stylus support", "Electronics", "TabletCo", 349.99, 180.00, 0.6, "new", "A"),
            ("Power Bank 20000mAh", "High-capacity power bank with fast charging", "Electronics", "PowerPlus", 44.99, 20.00, 0.5, "new", "A"),
            ("Fitness Tracker", "Water-resistant fitness tracker with heart rate monitor", "Electronics", "FitTech", 59.99, 28.00, 0.1, "new", "A"),
            ("Backpack Laptop", "Water-resistant laptop backpack with USB charging port", "Accessories", "TravelGear", 69.99, 32.00, 1.2, "new", "A"),
            ("Noise Cancelling Earbuds", "True wireless earbuds with active noise cancellation", "Electronics", "AudioTech", 149.99, 68.00, 0.1, "new", "A"),
        ]
        
        for name, description, category, brand, price, cost, weight, condition, grade in products:
            product_id = str(uuid.uuid4())
            sku = f"SKU-{random.randint(10000, 99999)}"
            dimensions = {"length": random.randint(5, 50), "width": random.randint(5, 40), "height": random.randint(2, 30), "unit": "cm"}
            
            self.cursor.execute("""
                INSERT INTO products (id, sku, name, description, category, brand, price, cost, weight, dimensions, condition, grade, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (product_id, sku, name, description, category, brand, price, cost, weight, Json(dimensions), condition, grade, datetime.now(), datetime.now()))
            
            self.product_ids.append(product_id)
        
        self.conn.commit()
        print(f"✅ Created {len(self.product_ids)} products")
    
    def seed_inventory(self):
        print("📊 Seeding inventory...")
        
        count = 0
        for product_id in self.product_ids:
            for warehouse_id in self.warehouse_ids:
                inventory_id = str(uuid.uuid4())
                quantity = random.randint(10, 500)
                reserved = random.randint(0, min(50, quantity // 2))
                reorder_point = random.randint(20, 100)
                max_stock = random.randint(200, 1000)
                
                self.cursor.execute("""
                    INSERT INTO inventory (id, product_id, warehouse_id, quantity, reserved_quantity, reorder_point, max_stock, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (inventory_id, product_id, warehouse_id, quantity, reserved, reorder_point, max_stock, datetime.now()))
                
                count += 1
        
        self.conn.commit()
        print(f"✅ Created {count} inventory records")
    
    def seed_orders(self):
        print("🛒 Seeding orders...")
        
        statuses = ["pending", "processing", "shipped", "delivered"]
        channels = ["web", "mobile", "amazon", "ebay", "shopify"]
        
        for i in range(150):
            order_id = str(uuid.uuid4())
            customer_id = random.choice(self.customer_ids)
            status = random.choice(statuses)
            channel = random.choice(channels)
            channel_order_id = f"{channel.upper()}-{random.randint(100000, 999999)}"
            created_at = datetime.now() - timedelta(days=random.randint(0, 60), hours=random.randint(0, 23))
            
            # Get customer address
            self.cursor.execute("SELECT shipping_address, billing_address FROM customers WHERE id = %s", (customer_id,))
            shipping_address, billing_address = self.cursor.fetchone()
            
            # Create order
            self.cursor.execute("""
                INSERT INTO orders (id, customer_id, channel, channel_order_id, status, shipping_address, billing_address, subtotal, shipping_cost, tax_amount, total_amount, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (order_id, customer_id, channel, channel_order_id, status, Json(shipping_address), Json(billing_address), 0, 0, 0, 0, created_at, datetime.now()))
            
            # Add order items
            num_items = random.randint(1, 5)
            total_amount = 0
            
            for _ in range(num_items):
                product_id = random.choice(self.product_ids)
                self.cursor.execute("SELECT price FROM products WHERE id = %s", (product_id,))
                price = self.cursor.fetchone()[0]
                quantity = random.randint(1, 3)
                subtotal = float(price) * quantity
                total_amount += subtotal
                
                order_item_id = str(uuid.uuid4())
                self.cursor.execute("""
                    INSERT INTO order_items (id, order_id, product_id, quantity, unit_price, total_price)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (order_item_id, order_id, product_id, quantity, price, subtotal))
            
            # Calculate totals
            shipping_cost = random.choice([0, 5.99, 9.99, 14.99])
            tax_amount = total_amount * 0.08  # 8% tax
            final_total = total_amount + shipping_cost + tax_amount
            
            # Update order totals
            self.cursor.execute("""
                UPDATE orders 
                SET subtotal = %s, shipping_cost = %s, tax_amount = %s, total_amount = %s 
                WHERE id = %s
            """, (total_amount, shipping_cost, tax_amount, final_total, order_id))
            
            self.order_ids.append(order_id)
        
        self.conn.commit()
        print(f"✅ Created {len(self.order_ids)} orders")
    
    def seed_all(self):
        print("=" * 80)
        print("🌱 SEEDING PRODUCTION DATABASE")
        print("=" * 80)
        
        try:
            self.seed_warehouses()
            self.seed_customers()
            self.seed_products()
            self.seed_inventory()
            self.seed_orders()
            
            print("=" * 80)
            print("✅ DATABASE SEEDING COMPLETE!")
            print("=" * 80)
            print(f"📊 Summary:")
            print(f"   - Warehouses: {len(self.warehouse_ids)}")
            print(f"   - Customers: {len(self.customer_ids)}")
            print(f"   - Products: {len(self.product_ids)}")
            print(f"   - Inventory Records: {len(self.product_ids) * len(self.warehouse_ids)}")
            print(f"   - Orders: {len(self.order_ids)}")
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ Seeding failed: {e}")
            import traceback
            traceback.print_exc()
            self.conn.rollback()
            raise

def main():
    seeder = CompleteSeeder()
    
    if not seeder.connect():
        return
    
    try:
        seeder.seed_all()
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        seeder.disconnect()

if __name__ == "__main__":
    main()

