#!/usr/bin/env python3
"""
Database Migration Script for Product Wizard
Pure Python implementation using psycopg2 (no psql required)
Works on Windows, Mac, and Linux
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Try to import psycopg2
try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("❌ ERROR: psycopg2 library not found!")
    print()
    print("Please install it using:")
    print("  pip install psycopg2-binary")
    print()
    print("Or if that fails, try:")
    print("  pip install psycopg2")
    print()
    sys.exit(1)

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

def get_db_config():
    """Get database configuration from environment or user input"""
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'ecommerce'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '')
    }
    
    print_info("Database Configuration:")
    print(f"  Host: {config['host']}")
    print(f"  Port: {config['port']}")
    print(f"  Database: {config['database']}")
    print(f"  User: {config['user']}")
    print(f"  Password: {'*' * len(config['password']) if config['password'] else '(not set)'}")
    print()
    
    # Ask if user wants to change any settings
    change = input("Do you want to change any settings? (yes/no): ").strip().lower()
    if change == 'yes':
        config['host'] = input(f"Host [{config['host']}]: ").strip() or config['host']
        config['port'] = input(f"Port [{config['port']}]: ").strip() or config['port']
        config['database'] = input(f"Database [{config['database']}]: ").strip() or config['database']
        config['user'] = input(f"User [{config['user']}]: ").strip() or config['user']
        
        # Get password securely
        import getpass
        password = getpass.getpass("Password (leave empty to keep current): ")
        if password:
            config['password'] = password
    
    # If password is still empty, ask for it
    if not config['password']:
        import getpass
        config['password'] = getpass.getpass("Database Password: ")
    
    return config

def test_connection(config):
    """Test database connection"""
    print_info("Testing database connection...")
    
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
        
        # Get PostgreSQL version
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        print_success("Database connection successful!")
        print_info(f"PostgreSQL version: {version.split(',')[0]}")
        return True
        
    except psycopg2.Error as e:
        print_error("Database connection failed!")
        print(f"Error: {e}")
        return False

def find_migration_file():
    """Find the migration SQL file"""
    script_dir = Path(__file__).parent
    migration_file = script_dir / 'database' / 'migrations' / '024_product_wizard_fields_corrected.sql'
    
    if migration_file.exists():
        print_success(f"Migration file found: {migration_file}")
        return migration_file
    else:
        print_error(f"Migration file not found: {migration_file}")
        return None

def read_migration_file(migration_file):
    """Read and parse the migration SQL file"""
    print_info("Reading migration file...")
    
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Count statements (rough estimate)
        statement_count = sql_content.count(';')
        print_success(f"Migration file loaded (~{statement_count} SQL statements)")
        
        return sql_content
        
    except Exception as e:
        print_error(f"Failed to read migration file: {e}")
        return None

def create_backup(config):
    """Create a simple backup by exporting schema"""
    print_info("Creating backup...")
    
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
        
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"backup_schema_{timestamp}.txt"
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(f"Database Backup - {datetime.now()}\n")
            f.write(f"Database: {config['database']}\n")
            f.write(f"Tables: {', '.join(tables)}\n")
            f.write("\n" + "="*60 + "\n\n")
            
            for table in tables:
                cursor.execute(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}'
                    ORDER BY ordinal_position;
                """)
                columns = cursor.fetchall()
                
                f.write(f"Table: {table}\n")
                for col_name, col_type in columns:
                    f.write(f"  - {col_name}: {col_type}\n")
                f.write("\n")
        
        cursor.close()
        conn.close()
        
        print_success(f"Backup created: {backup_file}")
        return backup_file
        
    except Exception as e:
        print_warning(f"Backup failed: {e}")
        print_warning("Continuing without backup...")
        return None

def run_migration(config, sql_content):
    """Run the database migration"""
    print_info("Running database migration...")
    print_warning("This may take 30-60 seconds...")
    print()
    
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
        
        # Set autocommit to handle DDL statements properly
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Execute the entire migration
        # Note: psycopg2 can handle multiple statements separated by semicolons
        cursor.execute(sql_content)
        
        cursor.close()
        conn.close()
        
        print()
        print_success("Migration completed successfully!")
        return True
        
    except psycopg2.Error as e:
        print()
        print_error("Migration failed!")
        print(f"Error: {e}")
        print()
        print("Common issues:")
        print("  - Table or column already exists (safe to ignore if re-running)")
        print("  - Insufficient permissions (need CREATE, ALTER privileges)")
        print("  - Syntax error in SQL file")
        return False

def verify_migration(config):
    """Verify migration was successful"""
    print_info("Verifying migration...")
    
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
        
        cursor = conn.cursor()
        
        # Check for new columns in products table
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'products' 
            AND column_name IN ('display_name', 'brand', 'model_number', 'product_type');
        """)
        column_count = cursor.fetchone()[0]
        
        # Check for new tables
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN (
                'product_specifications',
                'product_media',
                'product_pricing_tiers',
                'product_warehouse_inventory',
                'product_marketplace_listings'
            );
        """)
        table_count = cursor.fetchone()[0]
        
        # Check for triggers
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.triggers 
            WHERE trigger_name LIKE '%product%';
        """)
        trigger_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print()
        print_success(f"Verification Results:")
        print(f"  • New columns in products table: {column_count}/4")
        print(f"  • New tables created: {table_count}/5")
        print(f"  • Triggers created: {trigger_count}")
        print()
        
        if column_count >= 4 and table_count >= 5:
            print_success("✅ Migration verified successfully!")
            return True
        else:
            print_warning("⚠️  Migration may be incomplete. Check the results above.")
            return False
            
    except Exception as e:
        print_warning(f"Verification failed: {e}")
        return False

def print_next_steps():
    """Print next steps after successful migration"""
    print_header("Next Steps")
    
    print(f"{Colors.OKGREEN}✅ What was added:{Colors.ENDC}")
    print("  • 35+ new fields to products table")
    print("  • 10 new tables for wizard data")
    print("  • 2 auto-calculation triggers")
    print("  • 2 views for easy querying")
    print("  • 20+ indexes for performance")
    print()
    
    print(f"{Colors.OKCYAN}📋 Next steps:{Colors.ENDC}")
    print("  1. Restart your backend (product agent)")
    print("     - Stop the current process")
    print("     - Run: python agents/product_agent_v3.py")
    print()
    print("  2. Restart your frontend")
    print("     - cd multi-agent-dashboard")
    print("     - npm run dev")
    print()
    print("  3. Test product creation")
    print("     - Navigate to http://localhost:5173/merchant/products")
    print("     - Click 'Add Product'")
    print("     - Fill in the 8-step wizard")
    print("     - Click 'Create Product'")
    print()

def main():
    """Main function"""
    print_header("Product Wizard Database Migration")
    print_info("Pure Python implementation (no psql required)")
    print()
    
    # Find migration file
    migration_file = find_migration_file()
    if not migration_file:
        sys.exit(1)
    
    print()
    
    # Read migration file
    sql_content = read_migration_file(migration_file)
    if not sql_content:
        sys.exit(1)
    
    print()
    
    # Get database configuration
    config = get_db_config()
    
    print()
    
    # Test connection
    if not test_connection(config):
        sys.exit(1)
    
    print()
    
    # Ask for confirmation
    print_warning("This will modify your database structure.")
    confirm = input("Do you want to proceed? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print_info("Migration cancelled.")
        sys.exit(0)
    
    print()
    
    # Create backup
    backup = input("Do you want to create a backup first? (recommended, yes/no): ").strip().lower()
    if backup == 'yes':
        create_backup(config)
        print()
    
    # Run migration
    if run_migration(config, sql_content):
        print()
        verify_migration(config)
        print()
        print_next_steps()
        sys.exit(0)
    else:
        print()
        print_error("Migration failed. Please check the error messages above.")
        print()
        print_info("If the error says 'already exists', the migration may have")
        print_info("already been run. You can safely ignore this error.")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_info("Migration cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print()
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
