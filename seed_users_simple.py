"""Simple seed script for test users"""
import sys
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import bcrypt

sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))
from db_models import User, Merchant, Customer

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/multi_agent_ecommerce"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def seed():
    session = Session()
    try:
        # Admin
        admin = User(
            email='admin@ecommerce.com',
            username='admin',
            password_hash=hash_password('admin123'),
            role='admin',
            first_name='System',
            last_name='Administrator',
            is_verified=True,
            is_active=True
        )
        session.add(admin)
        
        # Merchant
        merchant_user = User(
            email='merchant1@example.com',
            username='merchant1',
            password_hash=hash_password('merchant123'),
            role='merchant',
            first_name='John',
            last_name='Merchant',
            is_verified=True,
            is_active=True
        )
        session.add(merchant_user)
        session.flush()
        
        merchant_profile = Merchant(
            user_id=merchant_user.id,
            business_name='Tech Gadgets Store',
            business_type='Electronics',
            status='active'
        )
        session.add(merchant_profile)
        
        # Customer
        customer_user = User(
            email='customer1@example.com',
            username='customer1',
            password_hash=hash_password('customer123'),
            role='customer',
            first_name='Alice',
            last_name='Johnson',
            is_verified=True,
            is_active=True
        )
        session.add(customer_user)
        session.flush()
        
        customer_profile = Customer(
            user_id=customer_user.id,
            customer_group='retail'
        )
        session.add(customer_profile)
        
        session.commit()
        print("✅ Created 3 test users successfully!")
        print("   Admin: admin@ecommerce.com / admin123")
        print("   Merchant: merchant1@example.com / merchant123")
        print("   Customer: customer1@example.com / customer123")
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed()
