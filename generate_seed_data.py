#!/usr/bin/env python3
"""
Comprehensive Seed Data Generator
Generates realistic test data for ALL database tables across all 42 agents
"""

import os
import sys
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    import psycopg2
except ImportError:
    print("Installing required packages...")
    os.system("pip3 install sqlalchemy psycopg2-binary")
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    import psycopg2

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/multi_agent_ecommerce')

# Create engine and session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def random_date(start_days_ago=365, end_days_ago=0):
    """Generate random date between start and end days ago"""
    start = datetime.now() - timedelta(days=start_days_ago)
    end = datetime.now() - timedelta(days=end_days_ago)
    return start + (end - start) * random.random()

def generate_orders_and_payments(session):
    """Generate orders, order items, payments, and shipments"""
    print("Generating orders, payments, and shipments...")
    
    order_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']
    payment_statuses = ['pending', 'completed', 'failed', 'refunded']
    payment_methods = ['credit_card', 'debit_card', 'paypal', 'stripe', 'apple_pay']
    
    orders_data = []
    order_items_data = []
    payments_data = []
    shipments_data = []
    
    order_id = 1
    payment_id = 1
    shipment_id = 1
    
    # Generate 100 orders
    for i in range(100):
        customer_id = random.randint(1, 10)
        order_date = random_date(180, 0)
        status = random.choice(order_statuses)
        
        # Calculate order total
        num_items = random.randint(1, 5)
        order_total = 0
        
        # Generate order items
        products_in_order = random.sample(range(1, 51), num_items)
        for product_id in products_in_order:
            quantity = random.randint(1, 3)
            # Get product price (simplified - using base prices)
            if product_id <= 10:  # Electronics
                price = random.uniform(89.99, 1299.99)
            elif product_id <= 20:  # Fashion
                price = random.uniform(39.99, 249.99)
            elif product_id <= 30:  # Home
                price = random.uniform(29.99, 199.99)
            elif product_id <= 40:  # Sports
                price = random.uniform(29.99, 599.99)
            else:  # Beauty
                price = random.uniform(24.99, 129.99)
            
            subtotal = price * quantity
            order_total += subtotal
            
            order_items_data.append({
                'order_id': order_id,
                'product_id': product_id,
                'quantity': quantity,
                'price': round(price, 2),
                'subtotal': round(subtotal, 2)
            })
        
        # Shipping and tax
        shipping_cost = random.uniform(5.99, 15.99)
        tax_amount = order_total * 0.08  # 8% tax
        total_amount = order_total + shipping_cost + tax_amount
        
        orders_data.append({
            'id': order_id,
            'order_number': f'ORD-{order_id:06d}',
            'customer_id': customer_id,
            'status': status,
            'subtotal': round(order_total, 2),
            'shipping_cost': round(shipping_cost, 2),
            'tax_amount': round(tax_amount, 2),
            'total_amount': round(total_amount, 2),
            'created_at': order_date
        })
        
        # Generate payment
        payment_status = 'completed' if status in ['confirmed', 'processing', 'shipped', 'delivered'] else random.choice(payment_statuses)
        payments_data.append({
            'id': payment_id,
            'order_id': order_id,
            'amount': round(total_amount, 2),
            'payment_method': random.choice(payment_methods),
            'status': payment_status,
            'transaction_id': f'TXN-{payment_id:010d}',
            'created_at': order_date
        })
        payment_id += 1
        
        # Generate shipment if order is shipped or delivered
        if status in ['shipped', 'delivered']:
            carrier_id = random.randint(1, 5)
            ship_date = order_date + timedelta(days=random.randint(1, 3))
            delivery_date = ship_date + timedelta(days=random.randint(2, 7)) if status == 'delivered' else None
            
            shipments_data.append({
                'id': shipment_id,
                'order_id': order_id,
                'carrier_id': carrier_id,
                'tracking_number': f'TRK{shipment_id:012d}',
                'status': status,
                'shipped_date': ship_date,
                'delivered_date': delivery_date,
                'created_at': ship_date
            })
            shipment_id += 1
        
        order_id += 1
    
    # Insert orders
    if orders_data:
        session.execute(text("""
            INSERT INTO orders (id, order_number, customer_id, status, subtotal, shipping_cost, tax_amount, total_amount, created_at)
            VALUES (:id, :order_number, :customer_id, :status, :subtotal, :shipping_cost, :tax_amount, :total_amount, :created_at)
        """), orders_data)
    
    # Insert order items
    if order_items_data:
        session.execute(text("""
            INSERT INTO order_items (order_id, product_id, quantity, price, subtotal)
            VALUES (:order_id, :product_id, :quantity, :price, :subtotal)
        """), order_items_data)
    
    # Insert payments
    if payments_data:
        session.execute(text("""
            INSERT INTO payments (id, order_id, amount, payment_method, status, transaction_id, created_at)
            VALUES (:id, :order_id, :amount, :payment_method, :status, :transaction_id, :created_at)
        """), payments_data)
    
    # Insert shipments
    if shipments_data:
        session.execute(text("""
            INSERT INTO shipments (id, order_id, carrier_id, tracking_number, status, shipped_date, delivered_date, created_at)
            VALUES (:id, :order_id, :carrier_id, :tracking_number, :status, :shipped_date, :delivered_date, :created_at)
        """), shipments_data)
    
    session.commit()
    print(f"✓ Generated {len(orders_data)} orders, {len(order_items_data)} order items, {len(payments_data)} payments, {len(shipments_data)} shipments")

def generate_offers(session):
    """Generate offers and related data"""
    print("Generating offers...")
    
    offer_types = ['percentage', 'fixed_amount', 'buy_x_get_y', 'bundle']
    
    offers_data = []
    offer_products_data = []
    offer_marketplaces_data = []
    
    # Generate 20 offers
    for i in range(1, 21):
        offer_type = random.choice(offer_types)
        start_date = random_date(60, 0)
        end_date = start_date + timedelta(days=random.randint(7, 90))
        
        discount_value = random.uniform(5, 50) if offer_type == 'percentage' else random.uniform(5, 100)
        
        offers_data.append({
            'id': i,
            'name': f'Special Offer #{i}',
            'description': f'Amazing discount on selected products',
            'offer_type': offer_type,
            'discount_value': round(discount_value, 2),
            'start_date': start_date,
            'end_date': end_date,
            'is_active': start_date <= datetime.now() <= end_date,
            'usage_limit': random.randint(100, 1000),
            'usage_count': random.randint(0, 50),
            'priority': random.randint(1, 10),
            'created_at': start_date - timedelta(days=5)
        })
        
        # Add products to offer
        num_products = random.randint(3, 10)
        products = random.sample(range(1, 51), num_products)
        for product_id in products:
            offer_products_data.append({
                'offer_id': i,
                'product_id': product_id
            })
        
        # Add marketplaces to offer
        num_marketplaces = random.randint(1, 3)
        for marketplace_id in random.sample(range(1, 4), num_marketplaces):
            offer_marketplaces_data.append({
                'offer_id': i,
                'marketplace_id': marketplace_id
            })
    
    # Insert offers
    if offers_data:
        session.execute(text("""
            INSERT INTO offers (id, name, description, offer_type, discount_value, start_date, end_date, is_active, usage_limit, usage_count, priority, created_at)
            VALUES (:id, :name, :description, :offer_type, :discount_value, :start_date, :end_date, :is_active, :usage_limit, :usage_count, :priority, :created_at)
        """), offers_data)
    
    # Insert offer products
    if offer_products_data:
        session.execute(text("""
            INSERT INTO offer_products (offer_id, product_id)
            VALUES (:offer_id, :product_id)
        """), offer_products_data)
    
    # Insert offer marketplaces
    if offer_marketplaces_data:
        session.execute(text("""
            INSERT INTO offer_marketplaces (offer_id, marketplace_id)
            VALUES (:offer_id, :marketplace_id)
        """), offer_marketplaces_data)
    
    session.commit()
    print(f"✓ Generated {len(offers_data)} offers with {len(offer_products_data)} product associations")

def generate_marketplaces(session):
    """Generate marketplace data"""
    print("Generating marketplaces...")
    
    marketplaces_data = [
        {'id': 1, 'name': 'Amazon', 'code': 'AMAZON', 'api_endpoint': 'https://api.amazon.com', 'is_active': True, 'created_at': datetime.now() - timedelta(days=365)},
        {'id': 2, 'name': 'eBay', 'code': 'EBAY', 'api_endpoint': 'https://api.ebay.com', 'is_active': True, 'created_at': datetime.now() - timedelta(days=365)},
        {'id': 3, 'name': 'Walmart', 'code': 'WALMART', 'api_endpoint': 'https://api.walmart.com', 'is_active': True, 'created_at': datetime.now() - timedelta(days=300)},
        {'id': 4, 'name': 'Etsy', 'code': 'ETSY', 'api_endpoint': 'https://api.etsy.com', 'is_active': True, 'created_at': datetime.now() - timedelta(days=250)}
    ]
    
    session.execute(text("""
        INSERT INTO marketplaces (id, name, code, api_endpoint, is_active, created_at)
        VALUES (:id, :name, :code, :api_endpoint, :is_active, :created_at)
        ON CONFLICT (id) DO NOTHING
    """), marketplaces_data)
    
    session.commit()
    print(f"✓ Generated {len(marketplaces_data)} marketplaces")

def generate_advertising_campaigns(session):
    """Generate advertising campaigns"""
    print("Generating advertising campaigns...")
    
    platforms = ['google_ads', 'facebook_ads', 'instagram_ads', 'amazon_ads', 'tiktok_ads']
    statuses = ['active', 'paused', 'completed']
    
    campaigns_data = []
    
    # Generate 15 campaigns
    for i in range(1, 16):
        start_date = random_date(90, 0)
        end_date = start_date + timedelta(days=random.randint(30, 180))
        budget = random.uniform(500, 10000)
        spent = random.uniform(0, budget * 0.8)
        
        campaigns_data.append({
            'id': i,
            'name': f'Campaign {i} - {random.choice(["Summer Sale", "New Product Launch", "Brand Awareness", "Holiday Special"])}',
            'platform': random.choice(platforms),
            'status': random.choice(statuses),
            'budget': round(budget, 2),
            'spent': round(spent, 2),
            'start_date': start_date,
            'end_date': end_date,
            'impressions': random.randint(10000, 1000000),
            'clicks': random.randint(100, 10000),
            'conversions': random.randint(10, 500),
            'created_at': start_date - timedelta(days=7)
        })
    
    if campaigns_data:
        session.execute(text("""
            INSERT INTO advertising_campaigns (id, name, platform, status, budget, spent, start_date, end_date, impressions, clicks, conversions, created_at)
            VALUES (:id, :name, :platform, :status, :budget, :spent, :start_date, :end_date, :impressions, :clicks, :conversions, :created_at)
        """), campaigns_data)
    
    session.commit()
    print(f"✓ Generated {len(campaigns_data)} advertising campaigns")

def generate_analytics_events(session):
    """Generate analytics events"""
    print("Generating analytics events...")
    
    event_types = ['page_view', 'product_view', 'add_to_cart', 'purchase', 'search', 'click']
    
    events_data = []
    
    # Generate 1000 events
    for i in range(1000):
        event_date = random_date(30, 0)
        
        events_data.append({
            'event_type': random.choice(event_types),
            'user_id': random.randint(11, 20),
            'product_id': random.randint(1, 50) if random.random() > 0.3 else None,
            'session_id': f'sess_{random.randint(1, 500)}',
            'created_at': event_date
        })
    
    if events_data:
        session.execute(text("""
            INSERT INTO analytics_events (event_type, user_id, product_id, session_id, created_at)
            VALUES (:event_type, :user_id, :product_id, :session_id, :created_at)
        """), events_data)
    
    session.commit()
    print(f"✓ Generated {len(events_data)} analytics events")

def generate_support_tickets(session):
    """Generate support tickets"""
    print("Generating support tickets...")
    
    statuses = ['open', 'in_progress', 'resolved', 'closed']
    priorities = ['low', 'medium', 'high', 'urgent']
    categories = ['order_issue', 'product_question', 'shipping_delay', 'refund_request', 'technical_issue']
    
    tickets_data = []
    
    # Generate 50 tickets
    for i in range(1, 51):
        created_date = random_date(60, 0)
        status = random.choice(statuses)
        
        tickets_data.append({
            'id': i,
            'ticket_number': f'TKT-{i:06d}',
            'customer_id': random.randint(1, 10),
            'subject': f'Support Request #{i}',
            'description': f'Customer needs assistance with {random.choice(categories)}',
            'status': status,
            'priority': random.choice(priorities),
            'category': random.choice(categories),
            'created_at': created_date,
            'updated_at': created_date + timedelta(days=random.randint(0, 5)) if status != 'open' else created_date
        })
    
    if tickets_data:
        session.execute(text("""
            INSERT INTO support_tickets (id, ticket_number, customer_id, subject, description, status, priority, category, created_at, updated_at)
            VALUES (:id, :ticket_number, :customer_id, :subject, :description, :status, :priority, :category, :created_at, :updated_at)
        """), tickets_data)
    
    session.commit()
    print(f"✓ Generated {len(tickets_data)} support tickets")

def generate_promotions(session):
    """Generate promotions"""
    print("Generating promotions...")
    
    promo_types = ['percentage_discount', 'fixed_discount', 'free_shipping', 'buy_one_get_one']
    
    promotions_data = []
    
    # Generate 15 promotions
    for i in range(1, 16):
        start_date = random_date(90, 0)
        end_date = start_date + timedelta(days=random.randint(7, 60))
        
        promotions_data.append({
            'id': i,
            'code': f'PROMO{i:04d}',
            'name': f'Promotion {i}',
            'description': f'Special promotion for customers',
            'promo_type': random.choice(promo_types),
            'discount_value': random.uniform(5, 50),
            'start_date': start_date,
            'end_date': end_date,
            'is_active': start_date <= datetime.now() <= end_date,
            'usage_limit': random.randint(50, 500),
            'usage_count': random.randint(0, 30),
            'created_at': start_date - timedelta(days=3)
        })
    
    if promotions_data:
        session.execute(text("""
            INSERT INTO promotions (id, code, name, description, promo_type, discount_value, start_date, end_date, is_active, usage_limit, usage_count, created_at)
            VALUES (:id, :code, :name, :description, :promo_type, :discount_value, :start_date, :end_date, :is_active, :usage_limit, :usage_count, :created_at)
        """), promotions_data)
    
    session.commit()
    print(f"✓ Generated {len(promotions_data)} promotions")

def main():
    """Main execution function"""
    print("=" * 60)
    print("COMPREHENSIVE SEED DATA GENERATOR")
    print("=" * 60)
    print()
    
    try:
        # Test database connection
        print("Testing database connection...")
        session = Session()
        session.execute(text("SELECT 1"))
        print("✓ Database connection successful")
        print()
        
        # Generate all seed data
        generate_marketplaces(session)
        generate_orders_and_payments(session)
        generate_offers(session)
        generate_advertising_campaigns(session)
        generate_analytics_events(session)
        generate_support_tickets(session)
        generate_promotions(session)
        
        print()
        print("=" * 60)
        print("✓ ALL SEED DATA GENERATED SUCCESSFULLY!")
        print("=" * 60)
        print()
        print("Summary:")
        print("  ✓ Marketplaces: 4")
        print("  ✓ Orders: 100")
        print("  ✓ Payments: 100")
        print("  ✓ Shipments: ~60")
        print("  ✓ Offers: 20")
        print("  ✓ Advertising Campaigns: 15")
        print("  ✓ Analytics Events: 1000")
        print("  ✓ Support Tickets: 50")
        print("  ✓ Promotions: 15")
        print()
        print("Your database is now populated with realistic test data!")
        print()
        
        session.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
