#!/usr/bin/env python3
"""
Seed authentication users for testing
Creates admin, merchant, and customer users with proper password hashing
"""

import sys
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import bcrypt

# Add the shared directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from db_models import User, Merchant, Customer

# Database connection
DATABASE_URL = "postgresql://admin:admin123@localhost:5432/multi_agent_ecommerce"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def seed_auth_users():
    """Create test users for authentication"""
    session = Session()
    
    try:
        print("🔐 Seeding authentication users...")
        
        # Check if users already exist
        existing_admin = session.query(User).filter_by(email='admin@ecommerce.com').first()
        if existing_admin:
            print("⚠️  Users already exist. Skipping seed...")
            return
        
        # Create Admin User
        admin_user = User(
            email='admin@ecommerce.com',
            username='admin',
            password_hash=hash_password('admin123'),
            role='admin',
            first_name='System',
            last_name='Administrator',
            verified=True,
            active=True,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        session.add(admin_user)
        print("✅ Created admin user: admin@ecommerce.com / admin123")
        
        # Create Merchant User 1
        merchant_user1 = User(
            email='merchant1@example.com',
            username='merchant1',
            password_hash=hash_password('merchant123'),
            role='merchant',
            first_name='John',
            last_name='Merchant',
            verified=True,
            active=True,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        session.add(merchant_user1)
        session.flush()  # Get the user_id
        
        # Create Merchant Profile
        merchant_profile1 = Merchant(
            user_id=merchant_user1.user_id,
            business_name='Tech Gadgets Store',
            business_email='merchant1@example.com',
            business_phone='+1-555-0101',
            tax_id='TAX-001',
            business_address='123 Tech Street',
            business_city='San Francisco',
            business_state='CA',
            business_country='USA',
            business_postal_code='94102',
            status='active',
            commission_rate=15.0,
            created_at=datetime.utcnow()
        )
        session.add(merchant_profile1)
        print("✅ Created merchant user: merchant1@example.com / merchant123")
        
        # Create Merchant User 2
        merchant_user2 = User(
            email='merchant2@example.com',
            username='merchant2',
            password_hash=hash_password('merchant123'),
            role='merchant',
            first_name='Sarah',
            last_name='Seller',
            verified=True,
            active=True,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        session.add(merchant_user2)
        session.flush()
        
        merchant_profile2 = Merchant(
            user_id=merchant_user2.user_id,
            business_name='Fashion Boutique',
            business_email='merchant2@example.com',
            business_phone='+1-555-0102',
            tax_id='TAX-002',
            business_address='456 Fashion Ave',
            business_city='New York',
            business_state='NY',
            business_country='USA',
            business_postal_code='10001',
            status='active',
            commission_rate=12.0,
            created_at=datetime.utcnow()
        )
        session.add(merchant_profile2)
        print("✅ Created merchant user: merchant2@example.com / merchant123")
        
        # Create Customer User 1
        customer_user1 = User(
            email='customer1@example.com',
            username='customer1',
            password_hash=hash_password('customer123'),
            role='customer',
            first_name='Alice',
            last_name='Johnson',
            verified=True,
            active=True,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        session.add(customer_user1)
        session.flush()
        
        # Create Customer Profile
        customer_profile1 = Customer(
            user_id=customer_user1.user_id,
            email='customer1@example.com',
            first_name='Alice',
            last_name='Johnson',
            phone='+1-555-1001',
            address='789 Customer Lane',
            city='Los Angeles',
            state='CA',
            country='USA',
            postal_code='90001',
            loyalty_points=100,
            total_spent=500.00,
            created_at=datetime.utcnow()
        )
        session.add(customer_profile1)
        print("✅ Created customer user: customer1@example.com / customer123")
        
        # Create Customer User 2
        customer_user2 = User(
            email='customer2@example.com',
            username='customer2',
            password_hash=hash_password('customer123'),
            role='customer',
            first_name='Bob',
            last_name='Smith',
            verified=True,
            active=True,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        session.add(customer_user2)
        session.flush()
        
        customer_profile2 = Customer(
            user_id=customer_user2.user_id,
            email='customer2@example.com',
            first_name='Bob',
            last_name='Smith',
            phone='+1-555-1002',
            address='321 Buyer Street',
            city='Chicago',
            state='IL',
            country='USA',
            postal_code='60601',
            loyalty_points=250,
            total_spent=1200.00,
            created_at=datetime.utcnow()
        )
        session.add(customer_profile2)
        print("✅ Created customer user: customer2@example.com / customer123")
        
        # Create Customer User 3
        customer_user3 = User(
            email='customer3@example.com',
            username='customer3',
            password_hash=hash_password('customer123'),
            role='customer',
            first_name='Carol',
            last_name='Williams',
            verified=True,
            active=True,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        session.add(customer_user3)
        session.flush()
        
        customer_profile3 = Customer(
            user_id=customer_user3.user_id,
            email='customer3@example.com',
            first_name='Carol',
            last_name='Williams',
            phone='+1-555-1003',
            address='555 Shopper Blvd',
            city='Seattle',
            state='WA',
            country='USA',
            postal_code='98101',
            loyalty_points=500,
            total_spent=2500.00,
            created_at=datetime.utcnow()
        )
        session.add(customer_profile3)
        print("✅ Created customer user: customer3@example.com / customer123")
        
        session.commit()
        print("\n🎉 Authentication users seeded successfully!")
        print("\n📋 Test Accounts:")
        print("   Admin:    admin@ecommerce.com / admin123")
        print("   Merchant: merchant1@example.com / merchant123")
        print("   Merchant: merchant2@example.com / merchant123")
        print("   Customer: customer1@example.com / customer123")
        print("   Customer: customer2@example.com / customer123")
        print("   Customer: customer3@example.com / customer123")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error seeding users: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == '__main__':
    seed_auth_users()
