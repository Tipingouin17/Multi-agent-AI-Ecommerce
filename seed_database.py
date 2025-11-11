#!/usr/bin/env python3
"""
Database Seed Script for Multi-Agent E-commerce Platform
Populates all tables with realistic sample data for testing
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from shared.db_models import (
    Base, User, Merchant, Category, Product, Warehouse, Inventory,
    Customer, Address, Order, OrderItem, Carrier, Alert, Payment,
    PaymentMethod, Shipment
)
from shared.db_connection import get_database_url
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

# Create database engine
engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Sample data
FIRST_NAMES = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa", "James", "Maria"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

CATEGORIES_DATA = [
    {"name": "Electronics", "slug": "electronics", "description": "Electronic devices and accessories"},
    {"name": "Computers", "slug": "computers", "description": "Laptops, desktops, and accessories", "parent": "Electronics"},
    {"name": "Smartphones", "slug": "smartphones", "description": "Mobile phones and accessories", "parent": "Electronics"},
    {"name": "Clothing", "slug": "clothing", "description": "Men's and women's apparel"},
    {"name": "Men's Clothing", "slug": "mens-clothing", "description": "Clothing for men", "parent": "Clothing"},
    {"name": "Women's Clothing", "slug": "womens-clothing", "description": "Clothing for women", "parent": "Clothing"},
    {"name": "Home & Garden", "slug": "home-garden", "description": "Home improvement and garden supplies"},
    {"name": "Sports & Outdoors", "slug": "sports-outdoors", "description": "Sporting goods and outdoor equipment"},
    {"name": "Books", "slug": "books", "description": "Physical and digital books"},
    {"name": "Toys & Games", "slug": "toys-games", "description": "Toys and games for all ages"},
]

PRODUCTS_DATA = [
    {"name": "Wireless Headphones", "category": "Electronics", "price": 79.99, "cost": 45.00},
    {"name": "Smart Watch", "category": "Electronics", "price": 199.99, "cost": 120.00},
    {"name": "Laptop Stand", "category": "Computers", "price": 34.99, "cost": 18.00},
    {"name": "USB-C Hub", "category": "Computers", "price": 49.99, "cost": 25.00},
    {"name": "Mechanical Keyboard", "category": "Computers", "price": 129.99, "cost": 70.00},
    {"name": "Wireless Mouse", "category": "Computers", "price": 29.99, "cost": 15.00},
    {"name": "Phone Case", "category": "Smartphones", "price": 19.99, "cost": 8.00},
    {"name": "Screen Protector", "category": "Smartphones", "price": 9.99, "cost": 3.00},
    {"name": "Men's T-Shirt", "category": "Men's Clothing", "price": 24.99, "cost": 10.00},
    {"name": "Men's Jeans", "category": "Men's Clothing", "price": 59.99, "cost": 30.00},
    {"name": "Women's Dress", "category": "Women's Clothing", "price": 79.99, "cost": 40.00},
    {"name": "Women's Blouse", "category": "Women's Clothing", "price": 39.99, "cost": 20.00},
    {"name": "Yoga Mat", "category": "Sports & Outdoors", "price": 29.99, "cost": 12.00},
    {"name": "Dumbbell Set", "category": "Sports & Outdoors", "price": 89.99, "cost": 50.00},
    {"name": "Garden Tools Set", "category": "Home & Garden", "price": 49.99, "cost": 25.00},
    {"name": "LED Desk Lamp", "category": "Home & Garden", "price": 34.99, "cost": 18.00},
    {"name": "Fiction Novel", "category": "Books", "price": 14.99, "cost": 6.00},
    {"name": "Cookbook", "category": "Books", "price": 24.99, "cost": 12.00},
    {"name": "Board Game", "category": "Toys & Games", "price": 39.99, "cost": 20.00},
    {"name": "Building Blocks", "category": "Toys & Games", "price": 49.99, "cost": 25.00},
]

WAREHOUSES_DATA = [
    {"name": "Main Warehouse", "code": "WH-001", "city": "New York", "state": "NY", "country": "USA"},
    {"name": "West Coast Hub", "code": "WH-002", "city": "Los Angeles", "state": "CA", "country": "USA"},
    {"name": "Central Distribution", "code": "WH-003", "city": "Chicago", "state": "IL", "country": "USA"},
]

CARRIERS_DATA = [
    {"name": "FedEx", "code": "FEDEX", "type": "express"},
    {"name": "UPS", "code": "UPS", "type": "express"},
    {"name": "USPS", "code": "USPS", "type": "standard"},
    {"name": "DHL", "code": "DHL", "type": "express"},
]

ORDER_STATUSES = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
PAYMENT_STATUSES = ["pending", "paid", "failed", "refunded"]
FULFILLMENT_STATUSES = ["unfulfilled", "partially_fulfilled", "fulfilled"]


def clear_database(session):
    """Clear all data from database (for testing)"""
    print("🗑️  Clearing existing data...")
    
    # Delete in reverse order of dependencies
    # Use try-except to handle tables that don't exist yet
    tables_to_clear = [
        (OrderItem, "order_items"),
        (Order, "orders"),
        (Shipment, "shipments"),
        (Payment, "transactions"),
        (PaymentMethod, "payment_methods"),
        (Alert, "alerts"),
        (Inventory, "inventory"),
        (Product, "products"),
        (Category, "categories"),
        (Warehouse, "warehouses"),
        (Carrier, "carriers"),
        (Address, "addresses"),
        (Customer, "customers"),
        (Merchant, "merchants"),
        (User, "users"),
    ]
    
    for model, table_name in tables_to_clear:
        try:
            count = session.query(model).delete()
            if count > 0:
                print(f"   Cleared {count} records from {table_name}")
        except Exception as e:
            # Table doesn't exist or other error - skip it
            print(f"   Skipped {table_name} (table may not exist)")
            session.rollback()
    
    session.commit()
    print("✅ Database cleared")


def create_users(session, count=20):
    """Create sample users"""
    print(f"👥 Creating {count} users...")
    users = []
    
    # Create admin user
    admin = User(
        email="admin@ecommerce.com",
        username="admin",
        password_hash=generate_password_hash("admin123"),
        role="admin",
        first_name="Admin",
        last_name="User",
        phone="+1-555-0001",
        is_active=True,
        is_verified=True,
        created_at=datetime.now() - timedelta(days=365)
    )
    session.add(admin)
    users.append(admin)
    
    # Create merchant users
    for i in range(1, 4):
        merchant_user = User(
            email=f"merchant{i}@example.com",
            username=f"merchant{i}",
            password_hash=generate_password_hash("merchant123"),
            role="merchant",
            first_name=random.choice(FIRST_NAMES),
            last_name=random.choice(LAST_NAMES),
            phone=f"+1-555-{1000+i:04d}",
            is_active=True,
            is_verified=True,
            created_at=datetime.now() - timedelta(days=random.randint(180, 365))
        )
        session.add(merchant_user)
        users.append(merchant_user)
    
    # Create customer users
    for i in range(1, count - 3):
        customer_user = User(
            email=f"customer{i}@example.com",
            username=f"customer{i}",
            password_hash=generate_password_hash("customer123"),
            role="customer",
            first_name=random.choice(FIRST_NAMES),
            last_name=random.choice(LAST_NAMES),
            phone=f"+1-555-{2000+i:04d}",
            is_active=True,
            is_verified=random.choice([True, False]),
            created_at=datetime.now() - timedelta(days=random.randint(1, 365))
        )
        session.add(customer_user)
        users.append(customer_user)
    
    session.commit()
    print(f"✅ Created {len(users)} users")
    return users


def create_merchants(session, users):
    """Create merchant profiles"""
    print("🏪 Creating merchants...")
    merchants = []
    merchant_users = [u for u in users if u.role == "merchant"]
    
    business_types = ["Electronics", "Fashion", "Home & Garden"]
    
    for i, user in enumerate(merchant_users):
        merchant = Merchant(
            user_id=user.id,
            business_name=f"{user.first_name}'s {business_types[i % len(business_types)]} Store",
            business_type=business_types[i % len(business_types)],
            tax_id=f"TAX-{1000+i:04d}",
            website=f"https://merchant{i+1}.example.com",
            description=f"Quality {business_types[i % len(business_types)].lower()} products",
            rating=Decimal(str(round(random.uniform(3.5, 5.0), 2))),
            total_sales=Decimal("0.00"),
            total_orders=0,
            commission_rate=Decimal("10.00"),
            status="active",
            created_at=user.created_at
        )
        session.add(merchant)
        merchants.append(merchant)
    
    session.commit()
    print(f"✅ Created {len(merchants)} merchants")
    return merchants


def create_categories(session):
    """Create product categories"""
    print("📁 Creating categories...")
    categories = {}
    
    # First pass: create parent categories
    for cat_data in CATEGORIES_DATA:
        if "parent" not in cat_data:
            category = Category(
                name=cat_data["name"],
                slug=cat_data["slug"],
                description=cat_data["description"],
                is_active=True,
                sort_order=len(categories)
            )
            session.add(category)
            categories[cat_data["name"]] = category
    
    session.commit()
    
    # Second pass: create child categories
    for cat_data in CATEGORIES_DATA:
        if "parent" in cat_data:
            parent = categories.get(cat_data["parent"])
            category = Category(
                name=cat_data["name"],
                slug=cat_data["slug"],
                description=cat_data["description"],
                parent_id=parent.id if parent else None,
                is_active=True,
                sort_order=len(categories)
            )
            session.add(category)
            categories[cat_data["name"]] = category
    
    session.commit()
    print(f"✅ Created {len(categories)} categories")
    return categories


def create_products(session, merchants, categories):
    """Create products"""
    print("📦 Creating products...")
    products = []
    
    for i, prod_data in enumerate(PRODUCTS_DATA):
        merchant = random.choice(merchants)
        category = categories.get(prod_data["category"])
        
        product = Product(
            merchant_id=merchant.id,
            category_id=category.id if category else None,
            sku=f"SKU-{1000+i:04d}",
            name=prod_data["name"],
            slug=prod_data["name"].lower().replace(" ", "-").replace("'", ""),
            description=f"High-quality {prod_data['name'].lower()} for everyday use",
            price=Decimal(str(prod_data["price"])),
            cost=Decimal(str(prod_data["cost"])),
            currency="USD",
            stock_quantity=random.randint(10, 500),
            low_stock_threshold=20,
            weight=Decimal(str(round(random.uniform(0.1, 5.0), 2))),
            weight_unit="kg",
            status="active",
            is_featured=random.choice([True, False]),
            rating=Decimal(str(round(random.uniform(3.0, 5.0), 2))),
            review_count=random.randint(0, 500),
            created_at=datetime.now() - timedelta(days=random.randint(30, 365))
        )
        session.add(product)
        products.append(product)
    
    session.commit()
    print(f"✅ Created {len(products)} products")
    return products


def create_warehouses(session):
    """Create warehouses"""
    print("🏭 Creating warehouses...")
    warehouses = []
    
    for wh_data in WAREHOUSES_DATA:
        warehouse = Warehouse(
            name=wh_data["name"],
            code=wh_data["code"],
            address=f"123 Warehouse St",
            city=wh_data["city"],
            state=wh_data["state"],
            postal_code="12345",
            country=wh_data["country"],
            phone="+1-555-9999",
            email=f"{wh_data['code'].lower()}@warehouse.com",
            manager_name="Warehouse Manager",
            capacity=10000,
            current_utilization=random.randint(3000, 8000),
            status="active"
        )
        session.add(warehouse)
        warehouses.append(warehouse)
    
    session.commit()
    print(f"✅ Created {len(warehouses)} warehouses")
    return warehouses


def create_inventory(session, products, warehouses):
    """Create inventory records"""
    print("📊 Creating inventory records...")
    inventory_records = []
    
    for product in products:
        # Create inventory in 1-3 warehouses
        num_warehouses = random.randint(1, min(3, len(warehouses)))
        selected_warehouses = random.sample(warehouses, num_warehouses)
        
        for warehouse in selected_warehouses:
            quantity = random.randint(10, 200)
            inventory = Inventory(
                product_id=product.id,
                warehouse_id=warehouse.id,
                quantity=quantity,
                reserved_quantity=random.randint(0, min(10, quantity)),
                reorder_point=20,
                reorder_quantity=100,
                last_restock_date=datetime.now() - timedelta(days=random.randint(1, 90)),
                location=f"A{random.randint(1,10)}-B{random.randint(1,20)}-C{random.randint(1,30)}"
            )
            session.add(inventory)
            inventory_records.append(inventory)
    
    session.commit()
    print(f"✅ Created {len(inventory_records)} inventory records")
    return inventory_records


def create_customers(session, users):
    """Create customer profiles"""
    print("👤 Creating customers...")
    customers = []
    customer_users = [u for u in users if u.role == "customer"]
    
    for user in customer_users:
        customer = Customer(
            user_id=user.id,
            name=f"{user.first_name} {user.last_name}",
            email=user.email,
            phone=user.phone,
            customer_type="individual",
            status="active",
            total_spent=Decimal("0.00"),
            total_orders=0,
            created_at=user.created_at
        )
        session.add(customer)
        customers.append(customer)
    
    session.commit()
    print(f"✅ Created {len(customers)} customers")
    return customers


def create_addresses(session, users, customers):
    """Create addresses"""
    print("🏠 Creating addresses...")
    addresses = []
    
    address_types = ["shipping", "billing"]
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]
    states = ["NY", "CA", "IL", "TX", "AZ"]
    
    for customer in customers:
        user = next(u for u in users if u.id == customer.user_id)
        
        # Create 1-2 addresses per customer
        for i in range(random.randint(1, 2)):
            city_idx = random.randint(0, len(cities) - 1)
            address = Address(
                user_id=user.id,
                customer_id=customer.id,
                address_type=random.choice(address_types),
                first_name=user.first_name,
                last_name=user.last_name,
                company=None,
                address_line1=f"{random.randint(100, 9999)} Main St",
                address_line2=f"Apt {random.randint(1, 500)}" if random.random() > 0.5 else None,
                city=cities[city_idx],
                state=states[city_idx],
                postal_code=f"{random.randint(10000, 99999)}",
                country="USA",
                phone=user.phone,
                is_default=i == 0
            )
            session.add(address)
            addresses.append(address)
    
    session.commit()
    print(f"✅ Created {len(addresses)} addresses")
    return addresses


def create_carriers(session):
    """Create carriers"""
    print("🚚 Creating carriers...")
    carriers = []
    
    for carr_data in CARRIERS_DATA:
        carrier = Carrier(
            name=carr_data["name"],
            code=carr_data["code"],
            type=carr_data["type"],
            contact_email=f"support@{carr_data['code'].lower()}.com",
            contact_phone="+1-800-555-0000",
            api_endpoint=f"https://api.{carr_data['code'].lower()}.com",
            is_active=True,
            rating=Decimal(str(round(random.uniform(3.5, 5.0), 2)))
        )
        session.add(carrier)
        carriers.append(carrier)
    
    session.commit()
    print(f"✅ Created {len(carriers)} carriers")
    return carriers


def create_orders(session, customers, products, addresses, merchants):
    """Create orders with items"""
    print("🛒 Creating orders...")
    orders = []
    order_items = []
    
    # Create orders for the last 90 days
    num_orders = 150
    
    for i in range(num_orders):
        customer = random.choice(customers)
        merchant = random.choice(merchants)
        
        # Get customer's addresses
        customer_addresses = [a for a in addresses if a.customer_id == customer.id]
        if not customer_addresses:
            continue
        
        shipping_address = random.choice(customer_addresses)
        
        # Random date in last 90 days
        days_ago = random.randint(0, 90)
        order_date = datetime.now() - timedelta(days=days_ago)
        
        # Determine order status based on age
        if days_ago < 2:
            status = random.choice(["pending", "confirmed"])
            payment_status = "pending"
            fulfillment_status = "unfulfilled"
        elif days_ago < 5:
            status = "processing"
            payment_status = "paid"
            fulfillment_status = "partially_fulfilled"
        elif days_ago < 10:
            status = "shipped"
            payment_status = "paid"
            fulfillment_status = "fulfilled"
        else:
            status = random.choice(["delivered", "delivered", "delivered", "cancelled"])
            payment_status = "paid" if status == "delivered" else random.choice(["failed", "refunded"])
            fulfillment_status = "fulfilled" if status == "delivered" else "unfulfilled"
        
        # Create order
        order = Order(
            order_number=f"ORD-2024-{1000+i:04d}",
            customer_id=customer.id,
            merchant_id=merchant.id,
            status=status,
            payment_status=payment_status,
            fulfillment_status=fulfillment_status,
            subtotal=Decimal("0.00"),
            tax=Decimal("0.00"),
            shipping_cost=Decimal(str(round(random.uniform(5.0, 15.0), 2))),
            discount=Decimal("0.00"),
            total=Decimal("0.00"),
            currency="USD",
            shipping_address_id=shipping_address.id,
            billing_address_id=shipping_address.id,
            created_at=order_date,
            updated_at=order_date,
            confirmed_at=order_date + timedelta(hours=1) if status != "pending" else None,
            shipped_at=order_date + timedelta(days=2) if status in ["shipped", "delivered"] else None,
            delivered_at=order_date + timedelta(days=5) if status == "delivered" else None,
            cancelled_at=order_date + timedelta(hours=2) if status == "cancelled" else None
        )
        
        # Add 1-5 items to order
        num_items = random.randint(1, 5)
        subtotal = Decimal("0.00")
        
        for _ in range(num_items):
            product = random.choice(products)
            quantity = random.randint(1, 3)
            unit_price = product.price
            item_total = unit_price * quantity
            subtotal += item_total
            
            order_item = OrderItem(
                order=order,
                product_id=product.id,
                product_name=product.name,
                product_sku=product.sku,
                quantity=quantity,
                unit_price=unit_price,
                total_price=item_total,
                currency="USD"
            )
            order_items.append(order_item)
        
        # Calculate totals
        order.subtotal = subtotal
        order.tax = subtotal * Decimal("0.08")  # 8% tax
        order.total = order.subtotal + order.tax + order.shipping_cost
        
        session.add(order)
        orders.append(order)
    
    session.commit()
    print(f"✅ Created {len(orders)} orders with {len(order_items)} items")
    return orders


def create_alerts(session, inventory_records):
    """Create inventory alerts"""
    print("⚠️  Creating alerts...")
    alerts = []
    
    # Create alerts for low stock items
    for inv in inventory_records:
        if inv.quantity <= inv.reorder_point:
            severity = "critical" if inv.quantity <= inv.reorder_point * 0.5 else "high"
            alert = Alert(
                type="low_stock",
                severity=severity,
                title=f"Low stock alert for product {inv.product_id}",
                message=f"Current stock: {inv.quantity}, Reorder point: {inv.reorder_point}",
                source="inventory_agent",
                status="active",
                created_at=datetime.now() - timedelta(days=random.randint(0, 7))
            )
            session.add(alert)
            alerts.append(alert)
    
    session.commit()
    print(f"✅ Created {len(alerts)} alerts")
    return alerts


def update_merchant_totals(session, merchants, orders):
    """Update merchant total sales and orders"""
    print("💰 Updating merchant totals...")
    
    for merchant in merchants:
        merchant_orders = [o for o in orders if o.merchant_id == merchant.id and o.status == "delivered"]
        merchant.total_orders = len(merchant_orders)
        merchant.total_sales = sum(o.total for o in merchant_orders)
    
    session.commit()
    print("✅ Updated merchant totals")


def update_customer_totals(session, customers, orders):
    """Update customer total spent and orders"""
    print("💳 Updating customer totals...")
    
    for customer in customers:
        customer_orders = [o for o in orders if o.customer_id == customer.id and o.status == "delivered"]
        customer.total_orders = len(customer_orders)
        customer.total_spent = sum(o.total for o in customer_orders)
    
    session.commit()
    print("✅ Updated customer totals")


def main():
    """Main seed function"""
    print("\n" + "="*60)
    print("🌱 DATABASE SEED SCRIPT")
    print("="*60 + "\n")
    
    session = SessionLocal()
    
    try:
        # Clear existing data
        clear_database(session)
        
        # Create data in order of dependencies
        users = create_users(session, count=20)
        merchants = create_merchants(session, users)
        categories = create_categories(session)
        products = create_products(session, merchants, categories)
        warehouses = create_warehouses(session)
        inventory_records = create_inventory(session, products, warehouses)
        customers = create_customers(session, users)
        addresses = create_addresses(session, users, customers)
        carriers = create_carriers(session)
        orders = create_orders(session, customers, products, addresses, merchants)
        alerts = create_alerts(session, inventory_records)
        
        # Update aggregated totals
        update_merchant_totals(session, merchants, orders)
        update_customer_totals(session, customers, orders)
        
        print("\n" + "="*60)
        print("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"\n📊 Summary:")
        print(f"   - Users: {len(users)}")
        print(f"   - Merchants: {len(merchants)}")
        print(f"   - Customers: {len(customers)}")
        print(f"   - Categories: {len(categories)}")
        print(f"   - Products: {len(products)}")
        print(f"   - Warehouses: {len(warehouses)}")
        print(f"   - Inventory Records: {len(inventory_records)}")
        print(f"   - Addresses: {len(addresses)}")
        print(f"   - Carriers: {len(carriers)}")
        print(f"   - Orders: {len(orders)}")
        print(f"   - Alerts: {len(alerts)}")
        print("\n🎉 Your dashboard should now be populated with data!")
        print("\n📝 Login credentials:")
        print("   Admin: admin@ecommerce.com / admin123")
        print("   Merchant: merchant1@example.com / merchant123")
        print("   Customer: customer1@example.com / customer123")
        print()
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
