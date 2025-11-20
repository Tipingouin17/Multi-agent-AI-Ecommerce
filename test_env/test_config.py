"""
Test configuration for sandbox testing
Uses SQLite instead of PostgreSQL for easier testing
"""
import os

# Test database configuration
TEST_DB_PATH = "/home/ubuntu/Multi-agent-AI-Ecommerce/test_env/test_ecommerce.db"
DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

# Test environment variables
os.environ['DATABASE_URL'] = DATABASE_URL
os.environ['DB_TYPE'] = 'sqlite'
os.environ['JWT_SECRET_KEY'] = 'test_secret_key_for_sandbox_testing_only'

print(f"Test configuration loaded")
print(f"Database: {DATABASE_URL}")
