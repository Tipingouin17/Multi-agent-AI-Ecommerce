"""
Complete Seed Data Script for All 26 Agents
Multi-Agent E-Commerce Platform

This script populates the database with realistic sample data for all 26 agents:
- Core E-Commerce (8 agents)
- Advanced Business Logic (4 agents)
- Supply Chain (4 agents)
- Customer-Facing (4 agents)
- Infrastructure (3 agents)
- Operations (3 agents)

Usage:
    python database/seed_data_complete.py
"""

import random
import uuid
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import Json
import os

# Database configuration
DB_CONFIG = {
    "host": os.environ.get('DATABASE_HOST', 'localhost'),
    "port": 5432,
    "database": "multi_agent_ecommerce",
    "user": "postgres",
    "password": os.environ.get('DATABASE_PASSWORD'),
}

class CompleteDatabaseSeeder:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.data = {}  # Store generated IDs for relationships
        
    def connect(self):
        """Connect to database"""
        print("🔌 Connecting to database...")
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            print("✅ Connected successfully!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from database"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("👋 Disconnected from database")
    
    def seed_all(self):
        """Seed all data"""
        print("\n" + "="*80)
        print("🌱 SEEDING COMPLETE MULTI-AGENT E-COMMERCE DATABASE")
        print("="*80 + "\n")
        
        try:
            # Core E-Commerce Agents (1-8)
            self.seed_customers()  # Agent 4
            self.seed_products()   # Agent 2
            self.seed_warehouses() # Agent 13
            self.seed_inventory()  # Agent 3
            self.seed_carriers()   # Agent 6
            self.seed_orders()     # Agent 1
            self.seed_payments()   # Agent 5
            self.seed_shipments()  # Agent 6
            self.seed_notifications()  # Agent 7
            self.seed_analytics_events()  # Agent 8
            
            # Advanced Business Logic (9-12)
            self.seed_returns()  # Agent 9
            self.seed_fraud_checks()  # Agent 10
            self.seed_recommendations()  # Agent 11
            self.seed_promotions()  # Agent 12
            
            # Supply Chain (13-16)
            self.seed_suppliers()  # Agent 14
            self.seed_marketplace_connections()  # Agent 15
            self.seed_tax_rates()  # Agent 16
            
            # Customer-Facing (17-20)
            self.seed_gdpr_consent()  # Agent 17
            self.seed_audit_logs()  # Agent 17
            self.seed_support_tickets()  # Agent 18
            self.seed_chat_conversations()  # Agent 19
            self.seed_knowledge_articles()  # Agent 20
            
            # Infrastructure (21-23)
            self.seed_workflow_executions()  # Agent 21
            self.seed_sync_operations()  # Agent 22
            self.seed_api_requests()  # Agent 23
            
            # Operations (24-26)
            self.seed_system_metrics()  # Agent 24
            self.seed_backups()  # Agent 25
            self.seed_system_users()  # Agent 26
            
            self.conn.commit()
            
            print("\n" + "="*80)
            print("✅ COMPLETE DATABASE SEEDING SUCCESSFUL!")
            print("="*80)
            self.print_summary()
            
        except Exception as e:
            self.conn.rollback()
            print(f"\n❌ Seeding failed: {e}")
            raise
    
    def seed_customers(self):
        """Seed customers (Agent 4)"""
        print("👥 Seeding customers...")
        
        first_names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Robert', 'Lisa', 'James', 'Maria']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        
        customer_ids = []
        for i in range(100):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            email = f"{first_name.lower()}.{last_name.lower()}{i}@example.com"
            
            self.cursor.execute("""
                INSERT INTO customers (
                    email, first_name, last_name, phone, loyalty_tier, 
                    loyalty_points, total_spent, total_orders, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING customer_id
            """, (
                email, first_name, last_name, f"+1-555-{random.randint(1000, 9999)}",
                random.choice(['bronze', 'silver', 'gold', 'platinum', 'diamond']),
                random.randint(0, 10000), random.uniform(0, 50000), random.randint(0, 100),
                random.choice(['active', 'active', 'active', 'inactive'])
            ))
            customer_ids.append(self.cursor.fetchone()[0])
        
        self.data['customer_ids'] = customer_ids
        print(f"  ✅ Created {len(customer_ids)} customers")
    
    def seed_products(self):
        """Seed products (Agent 2)"""
        print("📦 Seeding products...")
        
        categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books', 'Toys', 'Beauty', 'Food']
        brands = ['Apple', 'Samsung', 'Nike', 'Adidas', 'Sony', 'LG', 'Dell', 'HP']
        
        product_ids = []
        for i in range(200):
            sku = f"SKU-{random.randint(10000, 99999)}"
            category = random.choice(categories)
            brand = random.choice(brands)
            
            self.cursor.execute("""
                INSERT INTO products (
                    sku, name, description, category, brand, price, cost, 
                    weight, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING product_id
            """, (
                sku, f"{brand} {category} Product {i}", 
                f"High-quality {category.lower()} from {brand}",
                category, brand, 
                round(random.uniform(10, 1000), 2),
                round(random.uniform(5, 500), 2),
                round(random.uniform(0.1, 10), 3),
                random.choice(['active', 'active', 'active', 'inactive'])
            ))
            product_ids.append(self.cursor.fetchone()[0])
        
        self.data['product_ids'] = product_ids
        print(f"  ✅ Created {len(product_ids)} products")
    
    def seed_warehouses(self):
        """Seed warehouses (Agent 13)"""
        print("🏭 Seeding warehouses...")
        
        warehouses_data = [
            {'code': 'WH-US-01', 'name': 'North America DC', 'city': 'Chicago', 'country': 'USA'},
            {'code': 'WH-EU-01', 'name': 'Europe Hub', 'city': 'Amsterdam', 'country': 'Netherlands'},
            {'code': 'WH-AP-01', 'name': 'Asia Pacific Center', 'city': 'Singapore', 'country': 'Singapore'},
            {'code': 'WH-UK-01', 'name': 'UK Distribution', 'city': 'London', 'country': 'UK'},
            {'code': 'WH-CA-01', 'name': 'Canada Warehouse', 'city': 'Toronto', 'country': 'Canada'},
        ]
        
        warehouse_ids = []
        for wh in warehouses_data:
            self.cursor.execute("""
                INSERT INTO warehouses (code, name, address, capacity, status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING warehouse_id
            """, (
                wh['code'], wh['name'],
                Json({'city': wh['city'], 'country': wh['country']}),
                random.randint(10000, 100000), 'active'
            ))
            warehouse_ids.append(self.cursor.fetchone()[0])
        
        self.data['warehouse_ids'] = warehouse_ids
        print(f"  ✅ Created {len(warehouse_ids)} warehouses")
    
    def seed_inventory(self):
        """Seed inventory (Agent 3)"""
        print("📊 Seeding inventory...")
        
        count = 0
        for product_id in self.data['product_ids'][:100]:  # First 100 products
            for warehouse_id in self.data['warehouse_ids']:
                self.cursor.execute("""
                    INSERT INTO inventory (
                        product_id, warehouse_id, quantity, reserved_quantity,
                        reorder_point, max_stock
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    product_id, warehouse_id,
                    random.randint(0, 1000), random.randint(0, 50),
                    random.randint(10, 50), random.randint(500, 2000)
                ))
                count += 1
        
        print(f"  ✅ Created {count} inventory records")
    
    def seed_carriers(self):
        """Seed carriers (Agent 6)"""
        print("🚚 Seeding carriers...")
        
        carriers_data = [
            {'code': 'COLISPRIVE', 'name': 'Colis Privé'},
            {'code': 'UPS', 'name': 'UPS'},
            {'code': 'CHRONOPOST', 'name': 'Chronopost'},
            {'code': 'COLISSIMO', 'name': 'Colissimo'},
            {'code': 'FEDEX', 'name': 'FedEx'},
        ]
        
        carrier_ids = []
        for carrier in carriers_data:
            self.cursor.execute("""
                INSERT INTO carriers (code, name, active)
                VALUES (%s, %s, %s)
                RETURNING carrier_id
            """, (carrier['code'], carrier['name'], True))
            carrier_ids.append(self.cursor.fetchone()[0])
        
        self.data['carrier_ids'] = carrier_ids
        print(f"  ✅ Created {len(carrier_ids)} carriers")
    
    def seed_orders(self):
        """Seed orders (Agent 1)"""
        print("🛒 Seeding orders...")
        
        order_ids = []
        for i in range(500):
            customer_id = random.choice(self.data['customer_ids'])
            order_number = f"ORD-{datetime.now().year}-{i+1:06d}"
            
            self.cursor.execute("""
                INSERT INTO orders (
                    order_number, customer_id, status, channel, total_amount,
                    subtotal, tax_amount, shipping_cost, currency, payment_status,
                    shipping_address
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING order_id
            """, (
                order_number, customer_id,
                random.choice(['pending', 'processing', 'shipped', 'delivered', 'cancelled']),
                random.choice(['web', 'mobile', 'marketplace']),
                round(random.uniform(20, 2000), 2),
                round(random.uniform(15, 1800), 2),
                round(random.uniform(2, 200), 2),
                round(random.uniform(5, 50), 2),
                'USD', random.choice(['paid', 'pending', 'failed']),
                Json({'city': 'New York', 'country': 'USA'})
            ))
            order_ids.append(self.cursor.fetchone()[0])
            
            # Add order items
            num_items = random.randint(1, 5)
            for _ in range(num_items):
                product_id = random.choice(self.data['product_ids'])
                quantity = random.randint(1, 5)
                unit_price = round(random.uniform(10, 500), 2)
                
                self.cursor.execute("""
                    INSERT INTO order_items (
                        order_id, product_id, quantity, unit_price, total_price
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    order_ids[-1], product_id, quantity, unit_price,
                    round(unit_price * quantity, 2)
                ))
        
        self.data['order_ids'] = order_ids
        print(f"  ✅ Created {len(order_ids)} orders with items")
    
    def seed_payments(self):
        """Seed payments (Agent 5)"""
        print("💳 Seeding payments...")
        
        count = 0
        for order_id in self.data['order_ids'][:400]:  # Most orders have payments
            self.cursor.execute("""
                INSERT INTO payments (
                    order_id, customer_id, amount, currency, payment_method,
                    gateway, status
                )
                SELECT 
                    %s, customer_id, total_amount, 'USD',
                    %s, %s, %s
                FROM orders WHERE order_id = %s
            """, (
                order_id,
                random.choice(['credit_card', 'paypal', 'stripe']),
                random.choice(['stripe', 'paypal', 'square']),
                random.choice(['completed', 'pending', 'failed']),
                order_id
            ))
            count += 1
        
        print(f"  ✅ Created {count} payments")
    
    def seed_shipments(self):
        """Seed shipments (Agent 6)"""
        print("📮 Seeding shipments...")
        
        count = 0
        for order_id in self.data['order_ids'][:300]:  # Shipped orders
            carrier_id = random.choice(self.data['carrier_ids'])
            
            self.cursor.execute("""
                INSERT INTO shipments (
                    order_id, carrier_code, carrier_name, tracking_number,
                    status, shipping_cost, estimated_delivery, shipping_address
                )
                SELECT 
                    %s, c.code, c.name, %s, %s, %s, %s, o.shipping_address
                FROM carriers c, orders o
                WHERE c.carrier_id = %s AND o.order_id = %s
            """, (
                order_id, f"TRK-{random.randint(100000, 999999)}",
                random.choice(['pending', 'in_transit', 'delivered']),
                round(random.uniform(5, 50), 2),
                datetime.now() + timedelta(days=random.randint(1, 7)),
                carrier_id, order_id
            ))
            count += 1
        
        print(f"  ✅ Created {count} shipments")
    
    def seed_notifications(self):
        """Seed notifications (Agent 7)"""
        print("🔔 Seeding notifications...")
        
        count = 0
        for customer_id in self.data['customer_ids'][:50]:
            for _ in range(random.randint(1, 5)):
                self.cursor.execute("""
                    INSERT INTO notifications (
                        customer_id, channel, type, title, message, status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    customer_id,
                    random.choice(['email', 'sms', 'push']),
                    random.choice(['order_update', 'promotion', 'account']),
                    'Order Update', 'Your order has been updated',
                    random.choice(['sent', 'pending', 'failed'])
                ))
                count += 1
        
        print(f"  ✅ Created {count} notifications")
    
    def seed_analytics_events(self):
        """Seed analytics events (Agent 8)"""
        print("📈 Seeding analytics events...")
        
        event_types = ['page_view', 'product_view', 'add_to_cart', 'purchase', 'search']
        count = 0
        
        for _ in range(1000):
            self.cursor.execute("""
                INSERT INTO analytics_events (
                    event_type, event_category, entity_type, entity_id,
                    user_id, properties
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                random.choice(event_types), 'user_action', 'product',
                str(random.choice(self.data['product_ids'])),
                str(random.choice(self.data['customer_ids'])),
                Json({'source': 'web'})
            ))
            count += 1
        
        print(f"  ✅ Created {count} analytics events")
    
    def seed_returns(self):
        """Seed returns (Agent 9)"""
        print("↩️  Seeding returns...")
        
        count = 0
        for order_id in self.data['order_ids'][:50]:  # 10% return rate
            self.cursor.execute("""
                INSERT INTO returns (
                    rma_number, order_id, customer_id, reason, status,
                    refund_amount
                )
                SELECT 
                    %s, %s, customer_id, %s, %s, total_amount * 0.9
                FROM orders WHERE order_id = %s
            """, (
                f"RMA-{random.randint(10000, 99999)}", order_id,
                random.choice(['defective', 'wrong_item', 'not_satisfied']),
                random.choice(['requested', 'approved', 'completed']),
                order_id
            ))
            count += 1
        
        print(f"  ✅ Created {count} returns")
    
    def seed_fraud_checks(self):
        """Seed fraud checks (Agent 10)"""
        print("🛡️  Seeding fraud checks...")
        
        count = 0
        for order_id in self.data['order_ids'][:200]:
            self.cursor.execute("""
                INSERT INTO fraud_checks (
                    order_id, customer_id, risk_score, risk_level, decision
                )
                SELECT 
                    %s, customer_id, %s, %s, %s
                FROM orders WHERE order_id = %s
            """, (
                order_id, round(random.uniform(0, 100), 2),
                random.choice(['low', 'medium', 'high']),
                random.choice(['approve', 'review', 'decline']),
                order_id
            ))
            count += 1
        
        print(f"  ✅ Created {count} fraud checks")
    
    def seed_recommendations(self):
        """Seed recommendations (Agent 11)"""
        print("💡 Seeding recommendations...")
        
        count = 0
        for customer_id in self.data['customer_ids'][:50]:
            for _ in range(5):
                self.cursor.execute("""
                    INSERT INTO product_recommendations (
                        customer_id, product_id, recommendation_type, score
                    )
                    VALUES (%s, %s, %s, %s)
                """, (
                    customer_id, random.choice(self.data['product_ids']),
                    random.choice(['collaborative', 'content_based', 'trending']),
                    round(random.uniform(0.5, 1.0), 4)
                ))
                count += 1
        
        print(f"  ✅ Created {count} recommendations")
    
    def seed_promotions(self):
        """Seed promotions (Agent 12)"""
        print("🎁 Seeding promotions...")
        
        promo_codes = ['SAVE10', 'WELCOME20', 'SUMMER25', 'FLASH30', 'VIP50']
        count = 0
        
        for code in promo_codes:
            self.cursor.execute("""
                INSERT INTO promotions (
                    code, name, description, discount_type, discount_value,
                    start_date, end_date, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                code, f"{code} Promotion", "Special discount",
                random.choice(['percentage', 'fixed']),
                random.uniform(5, 50),
                datetime.now() - timedelta(days=30),
                datetime.now() + timedelta(days=30),
                'active'
            ))
            count += 1
        
        print(f"  ✅ Created {count} promotions")
    
    def seed_suppliers(self):
        """Seed suppliers (Agent 14)"""
        print("🏢 Seeding suppliers...")
        
        suppliers = ['Acme Corp', 'Global Supplies Inc', 'Premium Goods Ltd', 'Wholesale Direct']
        count = 0
        
        for supplier in suppliers:
            self.cursor.execute("""
                INSERT INTO suppliers (
                    code, name, payment_terms, lead_time_days, rating, status
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                f"SUP-{random.randint(1000, 9999)}", supplier,
                random.choice(['net30', 'net60', 'prepaid']),
                random.randint(5, 30), round(random.uniform(3.5, 5.0), 2),
                'active'
            ))
            count += 1
        
        print(f"  ✅ Created {count} suppliers")
    
    def seed_marketplace_connections(self):
        """Seed marketplace connections (Agent 15)"""
        print("🌐 Seeding marketplace connections...")
        
        marketplaces = [
            ('amazon', 'Amazon'), ('ebay', 'eBay'), ('walmart', 'Walmart'),
            ('etsy', 'Etsy'), ('shopify', 'Shopify'), ('alibaba', 'Alibaba')
        ]
        count = 0
        
        for code, name in marketplaces:
            self.cursor.execute("""
                INSERT INTO marketplace_connections (
                    marketplace_code, marketplace_name, status
                )
                VALUES (%s, %s, %s)
            """, (code, name, 'active'))
            count += 1
        
        print(f"  ✅ Created {count} marketplace connections")
    
    def seed_tax_rates(self):
        """Seed tax rates (Agent 16)"""
        print("💰 Seeding tax rates...")
        
        jurisdictions = [
            ('US-CA', 0.0725), ('US-NY', 0.0800), ('US-TX', 0.0625),
            ('UK', 0.2000), ('FR', 0.2000), ('DE', 0.1900)
        ]
        count = 0
        
        for jurisdiction, rate in jurisdictions:
            self.cursor.execute("""
                INSERT INTO tax_rates (
                    jurisdiction, tax_type, rate, effective_date
                )
                VALUES (%s, %s, %s, %s)
            """, (jurisdiction, 'sales_tax', rate, datetime.now()))
            count += 1
        
        print(f"  ✅ Created {count} tax rates")
    
    def seed_gdpr_consent(self):
        """Seed GDPR consent (Agent 17)"""
        print("🔒 Seeding GDPR consent...")
        
        count = 0
        for customer_id in self.data['customer_ids']:
            for consent_type in ['marketing', 'analytics', 'third_party']:
                self.cursor.execute("""
                    INSERT INTO gdpr_consent (
                        customer_id, consent_type, granted, consent_method
                    )
                    VALUES (%s, %s, %s, %s)
                """, (customer_id, consent_type, random.choice([True, False]), 'explicit'))
                count += 1
        
        print(f"  ✅ Created {count} GDPR consent records")
    
    def seed_audit_logs(self):
        """Seed audit logs (Agent 17)"""
        print("📝 Seeding audit logs...")
        
        count = 0
        for _ in range(500):
            self.cursor.execute("""
                INSERT INTO audit_logs (
                    entity_type, entity_id, action, actor
                )
                VALUES (%s, %s, %s, %s)
            """, (
                random.choice(['order', 'customer', 'product']),
                str(uuid.uuid4()), random.choice(['create', 'update', 'delete']),
                f"user_{random.randint(1, 10)}"
            ))
            count += 1
        
        print(f"  ✅ Created {count} audit logs")
    
    def seed_support_tickets(self):
        """Seed support tickets (Agent 18)"""
        print("🎫 Seeding support tickets...")
        
        count = 0
        for customer_id in self.data['customer_ids'][:30]:
            self.cursor.execute("""
                INSERT INTO support_tickets (
                    ticket_number, customer_id, subject, description,
                    priority, status, category
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                f"TKT-{random.randint(10000, 99999)}", customer_id,
                "Need help with order", "I have a question about my order",
                random.choice(['low', 'medium', 'high', 'urgent']),
                random.choice(['open', 'in_progress', 'resolved', 'closed']),
                random.choice(['order_issue', 'product_question', 'technical'])
            ))
            count += 1
        
        print(f"  ✅ Created {count} support tickets")
    
    def seed_chat_conversations(self):
        """Seed chat conversations (Agent 19)"""
        print("💬 Seeding chat conversations...")
        
        count = 0
        for customer_id in self.data['customer_ids'][:20]:
            session_id = f"sess_{uuid.uuid4()}"
            self.cursor.execute("""
                INSERT INTO chat_conversations (
                    customer_id, session_id, channel, status
                )
                VALUES (%s, %s, %s, %s)
                RETURNING conversation_id
            """, (str(customer_id), session_id, 'web', 'active'))
            
            conversation_id = self.cursor.fetchone()[0]
            
            # Add messages
            for _ in range(random.randint(2, 10)):
                self.cursor.execute("""
                    INSERT INTO chat_messages (
                        conversation_id, sender_type, message_text, intent
                    )
                    VALUES (%s, %s, %s, %s)
                """, (
                    conversation_id,
                    random.choice(['customer', 'bot', 'agent']),
                    "Hello, I need help", random.choice(['greeting', 'order_status', 'product_info'])
                ))
            count += 1
        
        print(f"  ✅ Created {count} chat conversations")
    
    def seed_knowledge_articles(self):
        """Seed knowledge articles (Agent 20)"""
        print("📚 Seeding knowledge articles...")
        
        articles = [
            ('How to track your order', 'shipping'),
            ('Return policy explained', 'returns'),
            ('Payment methods accepted', 'payments'),
            ('Product warranty information', 'products'),
            ('Account security tips', 'account')
        ]
        count = 0
        
        for title, category in articles:
            self.cursor.execute("""
                INSERT INTO knowledge_articles (
                    title, content, category, status, views
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (title, f"Detailed information about {title.lower()}", category, 'published', random.randint(0, 1000)))
            count += 1
        
        print(f"  ✅ Created {count} knowledge articles")
    
    def seed_workflow_executions(self):
        """Seed workflow executions (Agent 21)"""
        print("⚙️  Seeding workflow executions...")
        
        workflows = ['order_processing', 'inventory_sync', 'payment_reconciliation']
        count = 0
        
        for _ in range(100):
            self.cursor.execute("""
                INSERT INTO workflow_executions (
                    workflow_name, status
                )
                VALUES (%s, %s)
            """, (random.choice(workflows), random.choice(['completed', 'failed', 'pending'])))
            count += 1
        
        print(f"  ✅ Created {count} workflow executions")
    
    def seed_sync_operations(self):
        """Seed sync operations (Agent 22)"""
        print("🔄 Seeding sync operations...")
        
        agents = ['order_agent', 'inventory_agent', 'product_agent']
        count = 0
        
        for _ in range(50):
            self.cursor.execute("""
                INSERT INTO sync_operations (
                    source_agent, target_agent, data_type, status, records_synced
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                random.choice(agents), random.choice(agents),
                'product_data', random.choice(['completed', 'failed', 'pending']),
                random.randint(0, 1000)
            ))
            count += 1
        
        print(f"  ✅ Created {count} sync operations")
    
    def seed_api_requests(self):
        """Seed API requests (Agent 23)"""
        print("🌐 Seeding API requests...")
        
        endpoints = ['/api/orders', '/api/products', '/api/customers', '/api/inventory']
        count = 0
        
        for _ in range(1000):
            self.cursor.execute("""
                INSERT INTO api_requests (
                    endpoint, method, status_code, response_time_ms
                )
                VALUES (%s, %s, %s, %s)
            """, (
                random.choice(endpoints), random.choice(['GET', 'POST', 'PUT', 'DELETE']),
                random.choice([200, 201, 400, 404, 500]), random.randint(10, 1000)
            ))
            count += 1
        
        print(f"  ✅ Created {count} API requests")
    
    def seed_system_metrics(self):
        """Seed system metrics (Agent 24)"""
        print("📊 Seeding system metrics...")
        
        agents = ['order_agent', 'product_agent', 'inventory_agent', 'customer_agent']
        metrics = ['cpu_usage', 'memory_usage', 'response_time']
        count = 0
        
        for _ in range(500):
            self.cursor.execute("""
                INSERT INTO system_metrics (
                    agent_name, metric_type, metric_value
                )
                VALUES (%s, %s, %s)
            """, (random.choice(agents), random.choice(metrics), round(random.uniform(0, 100), 2)))
            count += 1
        
        print(f"  ✅ Created {count} system metrics")
    
    def seed_backups(self):
        """Seed backups (Agent 25)"""
        print("💾 Seeding backups...")
        
        count = 0
        for i in range(30):
            self.cursor.execute("""
                INSERT INTO backups (
                    backup_type, file_path, file_size_mb, status
                )
                VALUES (%s, %s, %s, %s)
            """, (
                random.choice(['full', 'incremental', 'differential']),
                f"/backups/backup_{i}.sql", round(random.uniform(100, 10000), 2),
                random.choice(['completed', 'in_progress', 'failed'])
            ))
            count += 1
        
        print(f"  ✅ Created {count} backups")
    
    def seed_system_users(self):
        """Seed system users (Agent 26)"""
        print("👤 Seeding system users...")
        
        users = [
            ('admin', 'admin@example.com', 'admin'),
            ('merchant1', 'merchant1@example.com', 'merchant'),
            ('merchant2', 'merchant2@example.com', 'merchant'),
            ('support1', 'support1@example.com', 'support'),
            ('support2', 'support2@example.com', 'support'),
        ]
        count = 0
        
        for username, email, role in users:
            self.cursor.execute("""
                INSERT INTO system_users (
                    username, email, role, status
                )
                VALUES (%s, %s, %s, %s)
            """, (username, email, role, 'active'))
            count += 1
        
        print(f"  ✅ Created {count} system users")
    
    def print_summary(self):
        """Print seeding summary"""
        print("\n📊 SEEDING SUMMARY:")
        print("-" * 80)
        
        tables = [
            'customers', 'products', 'warehouses', 'inventory', 'carriers',
            'orders', 'order_items', 'payments', 'shipments', 'notifications',
            'analytics_events', 'returns', 'fraud_checks', 'product_recommendations',
            'promotions', 'suppliers', 'marketplace_connections', 'tax_rates',
            'gdpr_consent', 'audit_logs', 'support_tickets', 'chat_conversations',
            'chat_messages', 'knowledge_articles', 'workflow_executions',
            'sync_operations', 'api_requests', 'system_metrics', 'backups',
            'system_users'
        ]
        
        for table in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cursor.fetchone()[0]
            print(f"  {table:.<40} {count:>6} records")
        
        print("-" * 80)
        print("✅ All data seeded successfully!")

def main():
    """Main execution"""
    seeder = CompleteDatabaseSeeder()
    
    if not seeder.connect():
        return
    
    try:
        seeder.seed_all()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        seeder.disconnect()

if __name__ == "__main__":
    main()

