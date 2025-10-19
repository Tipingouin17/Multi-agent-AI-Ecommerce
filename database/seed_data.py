"""
Database Seed Script for Multi-Agent E-commerce Platform (Synchronous Version)

This script populates the database with realistic sample data for:
- Products and inventory
- Orders and order items
- Customers and merchants
- Warehouses and carriers
- Agent performance metrics
- System alerts and logs
"""

import random
from datetime import datetime, timedelta
import json
import os
import time
import psycopg2
from psycopg2.extras import Json

# Database connection configuration
DATABASE_CONFIG = {
    "host": os.environ.get('DATABASE_HOST', 'localhost'),
    "port": 5432,
    "database": "multi_agent_ecommerce",
    "user": "postgres",
    "password": os.environ.get('DATABASE_PASSWORD', 'postgres123'),
    "connect_timeout": 30  # Added timeout for Windows connections
}

class DatabaseSeeder:
    def __init__(self):
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Connect to the database"""
        try:
            print("Connecting to database...")
            self.conn = psycopg2.connect(**DATABASE_CONFIG)
            self.cursor = self.conn.cursor()
            print("✅ Connected to database")
            return True
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
        
    def disconnect(self):
        """Disconnect from the database"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("Disconnected from database")
    
    def create_tables(self):
        """Create all necessary tables"""
        print("Creating database tables...")
        
        # Products table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                sku VARCHAR(100) UNIQUE NOT NULL,
                name VARCHAR(500) NOT NULL,
                description TEXT,
                category VARCHAR(100),
                brand VARCHAR(100),
                price DECIMAL(10,2) NOT NULL,
                cost DECIMAL(10,2),
                weight DECIMAL(8,3),
                dimensions JSONB,
                condition VARCHAR(50) DEFAULT 'new',
                grade VARCHAR(10),
                warranty_months INTEGER DEFAULT 12,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Inventory table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                product_id UUID REFERENCES products(id),
                warehouse_id UUID NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                reserved_quantity INTEGER NOT NULL DEFAULT 0,
                reorder_point INTEGER DEFAULT 10,
                max_stock INTEGER DEFAULT 1000,
                location VARCHAR(50),
                last_updated TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Warehouses table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS warehouses (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(200) NOT NULL,
                code VARCHAR(20) UNIQUE NOT NULL,
                address JSONB NOT NULL,
                capacity INTEGER,
                current_utilization DECIMAL(5,2) DEFAULT 0,
                operational_hours JSONB,
                contact_info JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Customers table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                phone VARCHAR(20),
                addresses JSONB,
                preferences JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                last_login TIMESTAMP
            )
        """)
        
        # Orders table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                order_number VARCHAR(50) UNIQUE NOT NULL,
                customer_id UUID REFERENCES customers(id),
                status VARCHAR(50) NOT NULL,
                channel VARCHAR(50) NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                shipping_cost DECIMAL(10,2) DEFAULT 0,
                tax_amount DECIMAL(10,2) DEFAULT 0,
                shipping_address JSONB NOT NULL,
                billing_address JSONB,
                payment_method VARCHAR(50),
                payment_status VARCHAR(50),
                warehouse_id UUID,
                carrier_id UUID,
                tracking_number VARCHAR(100),
                estimated_delivery DATE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Order items table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                order_id UUID REFERENCES orders(id),
                product_id UUID REFERENCES products(id),
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                total_price DECIMAL(10,2) NOT NULL,
                status VARCHAR(50) DEFAULT 'pending'
            )
        """)
        
        # Carriers table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS carriers (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(200) NOT NULL,
                code VARCHAR(20) UNIQUE NOT NULL,
                service_types JSONB,
                coverage_areas JSONB,
                pricing_model JSONB,
                performance_metrics JSONB,
                api_credentials JSONB,
                active BOOLEAN DEFAULT true
            )
        """)
        
        # Agent metrics table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_metrics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_id VARCHAR(100) NOT NULL,
                agent_name VARCHAR(200) NOT NULL,
                timestamp TIMESTAMP DEFAULT NOW(),
                cpu_usage DECIMAL(5,2),
                memory_usage DECIMAL(5,2),
                response_time DECIMAL(8,2),
                success_rate DECIMAL(5,2),
                error_count INTEGER DEFAULT 0,
                active_tasks INTEGER DEFAULT 0,
                queue_size INTEGER DEFAULT 0,
                custom_metrics JSONB
            )
        """)
        
        # System alerts table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_alerts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                alert_id VARCHAR(100) UNIQUE NOT NULL,
                severity VARCHAR(20) NOT NULL,
                title VARCHAR(500) NOT NULL,
                description TEXT,
                affected_agents JSONB,
                root_cause TEXT,
                ai_recommendation TEXT,
                confidence_score DECIMAL(5,2),
                auto_resolution_possible BOOLEAN DEFAULT false,
                human_approval_required BOOLEAN DEFAULT true,
                resolution_steps JSONB,
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT NOW(),
                resolved_at TIMESTAMP
            )
        """)
        
        self.conn.commit()
        print("✅ Database tables created successfully")
    
    def seed_warehouses(self):
        """Seed warehouses data"""
        print("Seeding warehouses...")
        
        warehouses = [
            {
                'name': 'North America Distribution Center',
                'code': 'NA-DC-01',
                'address': {
                    'street': '1234 Industrial Blvd',
                    'city': 'Chicago',
                    'state': 'IL',
                    'country': 'USA',
                    'postal_code': '60601'
                },
                'capacity': 50000,
                'current_utilization': 68.5,
                'operational_hours': {
                    'monday': '06:00-22:00',
                    'tuesday': '06:00-22:00',
                    'wednesday': '06:00-22:00',
                    'thursday': '06:00-22:00',
                    'friday': '06:00-22:00',
                    'saturday': '08:00-18:00',
                    'sunday': 'closed'
                },
                'contact_info': {
                    'manager': 'John Smith',
                    'phone': '+1-555-0101',
                    'email': 'chicago@warehouse.com'
                }
            },
            {
                'name': 'Europe Distribution Hub',
                'code': 'EU-DH-01',
                'address': {
                    'street': '456 Logistics Park',
                    'city': 'Amsterdam',
                    'country': 'Netherlands',
                    'postal_code': '1012 AB'
                },
                'capacity': 35000,
                'current_utilization': 72.3,
                'operational_hours': {
                    'monday': '07:00-21:00',
                    'tuesday': '07:00-21:00',
                    'wednesday': '07:00-21:00',
                    'thursday': '07:00-21:00',
                    'friday': '07:00-21:00',
                    'saturday': '09:00-17:00',
                    'sunday': 'closed'
                },
                'contact_info': {
                    'manager': 'Emma Johnson',
                    'phone': '+31-20-555-0102',
                    'email': 'amsterdam@warehouse.com'
                }
            },
            {
                'name': 'Asia Pacific Center',
                'code': 'AP-DC-01',
                'address': {
                    'street': '789 Commerce Street',
                    'city': 'Singapore',
                    'country': 'Singapore',
                    'postal_code': '018989'
                },
                'capacity': 40000,
                'current_utilization': 45.8,
                'operational_hours': {
                    'monday': '08:00-20:00',
                    'tuesday': '08:00-20:00',
                    'wednesday': '08:00-20:00',
                    'thursday': '08:00-20:00',
                    'friday': '08:00-20:00',
                    'saturday': '10:00-16:00',
                    'sunday': 'closed'
                },
                'contact_info': {
                    'manager': 'Li Wei',
                    'phone': '+65-6555-0103',
                    'email': 'singapore@warehouse.com'
                }
            }
        ]
        
        warehouse_ids = []
        for warehouse in warehouses:
            self.cursor.execute("""
                INSERT INTO warehouses (name, code, address, capacity, current_utilization, operational_hours, contact_info)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                warehouse['name'], 
                warehouse['code'], 
                Json(warehouse['address']),
                warehouse['capacity'], 
                warehouse['current_utilization'],
                Json(warehouse['operational_hours']), 
                Json(warehouse['contact_info'])
            ))
            warehouse_id = self.cursor.fetchone()[0]
            warehouse_ids.append(warehouse_id)
            warehouse['id'] = warehouse_id
        
        self.conn.commit()
        self.warehouses = warehouses
        return warehouse_ids
    
    def seed_carriers(self):
        """Seed carriers data"""
        print("Seeding carriers...")
        
        carriers = [
            {
                'name': 'FastShip Express',
                'code': 'FSE',
                'service_types': ['standard', 'express', 'overnight', 'international'],
                'coverage_areas': ['North America', 'Europe', 'Asia Pacific'],
                'pricing_model': {
                    'standard': {'base': 5.99, 'per_kg': 1.50},
                    'express': {'base': 12.99, 'per_kg': 2.25},
                    'overnight': {'base': 24.99, 'per_kg': 3.50}
                },
                'performance_metrics': {
                    'on_time_delivery': 94.5,
                    'damage_rate': 0.2,
                    'customer_satisfaction': 4.3
                }
            },
            {
                'name': 'Global Logistics Network',
                'code': 'GLN',
                'service_types': ['economy', 'standard', 'premium'],
                'coverage_areas': ['Worldwide'],
                'pricing_model': {
                    'economy': {'base': 3.99, 'per_kg': 0.99},
                    'standard': {'base': 7.99, 'per_kg': 1.75},
                    'premium': {'base': 19.99, 'per_kg': 2.99}
                },
                'performance_metrics': {
                    'on_time_delivery': 89.2,
                    'damage_rate': 0.4,
                    'customer_satisfaction': 4.0
                }
            },
            {
                'name': 'EcoDelivery Solutions',
                'code': 'EDS',
                'service_types': ['green_standard', 'green_express', 'carbon_neutral'],
                'coverage_areas': ['North America', 'Europe'],
                'pricing_model': {
                    'green_standard': {'base': 6.99, 'per_kg': 1.25},
                    'green_express': {'base': 14.99, 'per_kg': 2.50},
                    'carbon_neutral': {'base': 8.99, 'per_kg': 1.99}
                },
                'performance_metrics': {
                    'on_time_delivery': 91.8,
                    'damage_rate': 0.1,
                    'customer_satisfaction': 4.5
                }
            }
        ]
        
        carrier_ids = []
        for carrier in carriers:
            self.cursor.execute("""
                INSERT INTO carriers (name, code, service_types, coverage_areas, pricing_model, performance_metrics)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                carrier['name'], 
                carrier['code'], 
                Json(carrier['service_types']),
                Json(carrier['coverage_areas']), 
                Json(carrier['pricing_model']),
                Json(carrier['performance_metrics'])
            ))
            carrier_id = self.cursor.fetchone()[0]
            carrier_ids.append(carrier_id)
            carrier['id'] = carrier_id
        
        self.conn.commit()
        self.carriers = carriers
        return carrier_ids
    
    def seed_products(self):
        """Seed products data"""
        print("Seeding products...")
        
        categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books', 'Toys']
        brands = ['TechCorp', 'StyleBrand', 'HomeMax', 'SportsPro', 'BookWorld', 'PlayTime']
        conditions = ['new', 'refurbished', 'open_box']
        grades = ['A+', 'A', 'B+', 'B', 'C']
        
        products = []
        product_ids = []
        
        # Create a smaller number of products for testing
        num_products = 100  # Reduced from 500 for faster seeding
        
        for i in range(num_products):
            category = random.choice(categories)
            brand = random.choice(brands)
            condition = random.choice(conditions)
            
            product = {
                'sku': f'SKU-{i+1:06d}',
                'name': f'{brand} {category} Product {i+1}',
                'description': f'High-quality {category.lower()} product from {brand}. Perfect for everyday use.',
                'category': category,
                'brand': brand,
                'price': round(random.uniform(10.99, 999.99), 2),
                'weight': round(random.uniform(0.1, 5.0), 3),
                'dimensions': {
                    'length': round(random.uniform(5, 50), 1),
                    'width': round(random.uniform(5, 40), 1),
                    'height': round(random.uniform(2, 30), 1),
                    'unit': 'cm'
                },
                'condition': condition,
                'grade': random.choice(grades) if condition == 'refurbished' else None,
                'warranty_months': random.choice([6, 12, 24, 36])
            }
            
            # Calculate cost as 60-80% of price
            product['cost'] = round(float(product['price']) * random.uniform(0.6, 0.8), 2)
            products.append(product)
        
        for product in products:
            self.cursor.execute("""
                INSERT INTO products (sku, name, description, category, brand, price, cost, weight, dimensions, condition, grade, warranty_months)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                product['sku'], 
                product['name'], 
                product['description'], 
                product['category'],
                product['brand'], 
                product['price'], 
                product['cost'], 
                product['weight'],
                Json(product['dimensions']), 
                product['condition'], 
                product['grade'],
                product['warranty_months']
            ))
            product_id = self.cursor.fetchone()[0]
            product_ids.append(product_id)
            product['id'] = product_id
        
        self.conn.commit()
        self.products = products
        return product_ids
    
    def seed_inventory(self):
        """Seed inventory data"""
        print("Seeding inventory...")
        
        if not hasattr(self, 'products') or not hasattr(self, 'warehouses'):
            print("❌ Products or warehouses not seeded yet")
            return []
        
        inventory_ids = []
        
        for product in self.products:
            for warehouse in self.warehouses:
                quantity = random.randint(0, 100)
                reserved = random.randint(0, min(10, quantity))
                reorder_point = random.randint(5, 20)
                max_stock = random.randint(100, 200)
                location = f"AISLE-{random.randint(1, 20)}-SHELF-{random.randint(1, 50)}"
                
                self.cursor.execute("""
                    INSERT INTO inventory (product_id, warehouse_id, quantity, reserved_quantity, reorder_point, max_stock, location)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    product['id'], 
                    warehouse['id'], 
                    quantity, 
                    reserved, 
                    reorder_point, 
                    max_stock, 
                    location
                ))
                inventory_id = self.cursor.fetchone()[0]
                inventory_ids.append(inventory_id)
        
        self.conn.commit()
        return inventory_ids
    
    def seed_customers(self):
        """Seed customers data"""
        print("Seeding customers...")
        
        first_names = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 'William', 'Elizabeth']
        last_names = ['Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis', 'Miller', 'Wilson', 'Moore', 'Taylor']
        
        customers = []
        customer_ids = []
        
        for i in range(50):  # Create 50 customers
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@example.com"
            
            addresses = []
            for j in range(random.randint(1, 3)):  # 1-3 addresses per customer
                addresses.append({
                    'type': 'home' if j == 0 else 'work' if j == 1 else 'other',
                    'street': f"{random.randint(100, 9999)} Main St",
                    'city': random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']),
                    'state': random.choice(['NY', 'CA', 'IL', 'TX', 'AZ']),
                    'postal_code': f"{random.randint(10000, 99999)}",
                    'country': 'USA',
                    'is_default': j == 0
                })
            
            preferences = {
                'marketing_emails': random.choice([True, False]),
                'order_updates': random.choice(['email', 'sms', 'both']),
                'preferred_categories': random.sample(['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books', 'Toys'], k=random.randint(1, 3))
            }
            
            self.cursor.execute("""
                INSERT INTO customers (email, first_name, last_name, phone, addresses, preferences, created_at, last_login)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                email, 
                first_name, 
                last_name, 
                f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                Json(addresses), 
                Json(preferences),
                datetime.now() - timedelta(days=random.randint(1, 365)),
                datetime.now() - timedelta(days=random.randint(0, 30))
            ))
            customer_id = self.cursor.fetchone()[0]
            customer_ids.append(customer_id)
            
            customer = {
                'id': customer_id,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'addresses': addresses
            }
            customers.append(customer)
        
        self.conn.commit()
        self.customers = customers
        return customer_ids
    
    def seed_orders(self):
        """Seed orders data"""
        print("Seeding orders...")
        
        if not hasattr(self, 'customers') or not hasattr(self, 'products') or not hasattr(self, 'warehouses') or not hasattr(self, 'carriers'):
            print("❌ Required data not seeded yet")
            return []
        
        statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        channels = ['website', 'mobile_app', 'marketplace', 'phone', 'in_store']
        payment_methods = ['credit_card', 'paypal', 'apple_pay', 'google_pay', 'bank_transfer']
        
        order_ids = []
        
        for i in range(100):  # Create 100 orders
            customer = random.choice(self.customers)
            warehouse = random.choice(self.warehouses)
            carrier = random.choice(self.carriers)
            
            # Use customer's default address as shipping address
            shipping_address = next((addr for addr in customer['addresses'] if addr.get('is_default')), customer['addresses'][0])
            
            order = {
                'order_number': f'ORD-{datetime.now().year}-{i+1:06d}',
                'customer_id': customer['id'],
                'status': random.choice(statuses),
                'channel': random.choice(channels),
                'shipping_address': shipping_address,
                'payment_method': random.choice(payment_methods),
                'payment_status': 'completed' if random.random() < 0.9 else 'pending',
                'warehouse_id': warehouse['id'],
                'carrier_id': carrier['id'],
                'tracking_number': f'TRK{random.randint(100000000, 999999999)}',
                'estimated_delivery': datetime.now() + timedelta(days=random.randint(1, 7)),
                'created_at': datetime.now() - timedelta(days=random.randint(0, 30))
            }
            
            # Insert order
            self.cursor.execute("""
                INSERT INTO orders (order_number, customer_id, status, channel, total_amount, shipping_cost, tax_amount,
                                  shipping_address, payment_method, payment_status, warehouse_id, carrier_id,
                                  tracking_number, estimated_delivery, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                order['order_number'], 
                order['customer_id'], 
                order['status'], 
                order['channel'],
                0, 0, 0,  # Will be updated after adding items
                Json(order['shipping_address']), 
                order['payment_method'], 
                order['payment_status'],
                order['warehouse_id'], 
                order['carrier_id'], 
                order['tracking_number'],
                order['estimated_delivery'], 
                order['created_at']
            ))
            
            order_id = self.cursor.fetchone()[0]
            order_ids.append(order_id)
            
            # Add order items
            num_items = random.randint(1, 5)
            selected_products = random.sample(self.products, min(num_items, len(self.products)))
            
            total_amount = 0
            
            for product in selected_products:
                quantity = random.randint(1, 3)
                unit_price = float(product['price'])
                total_price = unit_price * quantity
                total_amount += total_price
                
                # Insert order item
                self.cursor.execute("""
                    INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    order_id, 
                    product['id'], 
                    quantity, 
                    unit_price, 
                    total_price
                ))
            
            # Update order totals
            shipping_cost = round(random.uniform(5.99, 19.99), 2)
            tax_amount = round(total_amount * 0.08, 2)  # 8% tax
            final_total = total_amount + shipping_cost + tax_amount
            
            self.cursor.execute("""
                UPDATE orders SET total_amount = %s, shipping_cost = %s, tax_amount = %s
                WHERE id = %s
            """, (
                final_total, 
                shipping_cost, 
                tax_amount, 
                order_id
            ))
        
        self.conn.commit()
        return order_ids
    
    def seed_agent_metrics(self):
        """Seed agent performance metrics"""
        print("Seeding agent metrics...")
        
        agents = [
            {'id': 'order_agent', 'name': 'Order Management Agent'},
            {'id': 'product_agent', 'name': 'Product Management Agent'},
            {'id': 'inventory_agent', 'name': 'Inventory Management Agent'},
            {'id': 'warehouse_agent', 'name': 'Warehouse Selection Agent'},
            {'id': 'carrier_agent', 'name': 'Carrier Selection Agent'},
            {'id': 'demand_agent', 'name': 'Demand Forecasting Agent'},
            {'id': 'pricing_agent', 'name': 'Dynamic Pricing Agent'},
            {'id': 'communication_agent', 'name': 'Customer Communication Agent'},
            {'id': 'logistics_agent', 'name': 'Reverse Logistics Agent'},
            {'id': 'risk_agent', 'name': 'Risk & Anomaly Detection Agent'},
            {'id': 'marketplace_agent', 'name': 'Standard Marketplace Agent'},
            {'id': 'refurb_agent', 'name': 'Refurbished Marketplace Agent'},
            {'id': 'd2c_agent', 'name': 'D2C E-commerce Agent'},
            {'id': 'monitoring_agent', 'name': 'AI Monitoring Agent'}
        ]
        
        # Generate metrics for the last 3 days (reduced from 7 for faster seeding)
        for days_ago in range(3):
            timestamp = datetime.now() - timedelta(days=days_ago)
            
            for agent in agents:
                # Generate 6 hourly metrics for each day (reduced from 24 for faster seeding)
                for hour in range(0, 24, 4):
                    metric_time = timestamp.replace(hour=hour, minute=0, second=0, microsecond=0)
                    
                    # Generate realistic metrics with some variation
                    base_cpu = random.uniform(20, 80)
                    base_memory = random.uniform(30, 85)
                    base_response = random.uniform(100, 500)
                    base_success = random.uniform(95, 99.9)
                    
                    self.cursor.execute("""
                        INSERT INTO agent_metrics (agent_id, agent_name, timestamp, cpu_usage, memory_usage,
                                                 response_time, success_rate, error_count, active_tasks, queue_size, custom_metrics)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        agent['id'], 
                        agent['name'], 
                        metric_time, 
                        base_cpu, 
                        base_memory,
                        base_response, 
                        base_success, 
                        random.randint(0, 5),
                        random.randint(0, 20), 
                        random.randint(0, 50),
                        Json({
                            'requests_processed': random.randint(100, 1000),
                            'cache_hit_rate': random.uniform(80, 95),
                            'database_connections': random.randint(5, 25)
                        })
                    ))
        
        self.conn.commit()
    
    def seed_system_alerts(self):
        """Seed system alerts"""
        print("Seeding system alerts...")
        
        alert_templates = [
            {
                'severity': 'medium',
                'title': 'High CPU Usage Detected',
                'description': 'Agent CPU usage exceeded 80% threshold',
                'root_cause': 'Increased processing load during peak hours'
            },
            {
                'severity': 'high',
                'title': 'Agent Response Time Degradation',
                'description': 'Response times increased beyond acceptable limits',
                'root_cause': 'Database connection pool exhaustion'
            },
            {
                'severity': 'low',
                'title': 'Low Inventory Alert',
                'description': 'Multiple products below reorder point',
                'root_cause': 'Higher than expected demand for seasonal items'
            },
            {
                'severity': 'critical',
                'title': 'Payment Processing Failure',
                'description': 'Payment gateway returning errors',
                'root_cause': 'Third-party payment service outage'
            }
        ]
        
        for i, template in enumerate(alert_templates):
            self.cursor.execute("""
                INSERT INTO system_alerts (alert_id, severity, title, description, affected_agents,
                                         root_cause, ai_recommendation, confidence_score,
                                         auto_resolution_possible, resolution_steps, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                f'alert_{int(datetime.now().timestamp())}_{i}',
                template['severity'], 
                template['title'], 
                template['description'],
                Json(['order_agent', 'inventory_agent']),
                template['root_cause'],
                'Recommend scaling resources and monitoring performance metrics',
                random.uniform(70, 95), 
                random.choice([True, False]),
                Json(['Restart affected agents', 'Scale resources', 'Monitor performance']),
                'active' if i < 2 else 'resolved'
            ))
        
        self.conn.commit()
    
    def run_seed(self):
        """Run the complete seeding process"""
        try:
            if not self.connect():
                return False
            
            print("Starting database seeding...")
            
            # Create tables
            self.create_tables()
            
            # Seed data in order (respecting foreign key constraints)
            self.seed_warehouses()
            self.seed_carriers()
            self.seed_products()
            self.seed_inventory()
            self.seed_customers()
            self.seed_orders()
            self.seed_agent_metrics()
            self.seed_system_alerts()
            
            print("✅ Database seeding completed successfully!")
            
            # Print summary
            counts = {}
            tables = ['warehouses', 'carriers', 'products', 'inventory', 'customers', 'orders', 'order_items', 'agent_metrics', 'system_alerts']
            
            for table in tables:
                self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = self.cursor.fetchone()[0]
                counts[table] = count
            
            print("\n📊 Seeded Data Summary:")
            for table, count in counts.items():
                print(f"  {table}: {count:,} records")
            
            return True
                
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Error during seeding: {e}")
            return False
        finally:
            self.disconnect()

if __name__ == "__main__":
    # Add a delay to ensure the database is fully ready
    print("Waiting 5 seconds for database to be ready...")
    time.sleep(5)
    
    seeder = DatabaseSeeder()
    success = seeder.run_seed()
    
    if success:
        print("✅ All data seeded successfully!")
    else:
        print("❌ Seeding process encountered errors.")
