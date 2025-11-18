#!/usr/bin/env python3
"""
Fix user passwords by rehashing them with proper bcrypt
"""

import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import bcrypt

# Add the shared directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from db_models import User

# Database connection
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/multi_agent_ecommerce"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def fix_passwords():
    """Update all user passwords with proper bcrypt hashes"""
    session = Session()
    
    try:
        print("🔐 Fixing user passwords...")
        
        # Define the correct passwords for each user
        user_passwords = {
            'admin@ecommerce.com': 'admin123',
            'merchant1@example.com': 'merchant123',
            'merchant2@example.com': 'merchant123',
            'customer1@example.com': 'customer123',
            'customer2@example.com': 'customer123',
            'customer3@example.com': 'customer123',
        }
        
        updated_count = 0
        for email, password in user_passwords.items():
            user = session.query(User).filter_by(email=email).first()
            if user:
                # Hash the password properly
                user.password_hash = hash_password(password)
                print(f"✅ Updated password for {email}")
                updated_count += 1
            else:
                print(f"⚠️  User not found: {email}")
        
        session.commit()
        print(f"\n🎉 Successfully updated {updated_count} user passwords!")
        print("\n📋 You can now login with:")
        print("   Admin:    admin@ecommerce.com / admin123")
        print("   Merchant: merchant1@example.com / merchant123")
        print("   Customer: customer1@example.com / customer123")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error fixing passwords: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == '__main__':
    fix_passwords()
