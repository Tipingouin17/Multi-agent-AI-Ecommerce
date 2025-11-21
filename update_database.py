#!/usr/bin/env python3
"""
Database Update Script for Product Wizard
Cross-platform (Windows, Mac, Linux)
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Color codes for terminal output (works on Windows 10+, Mac, Linux)
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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

def check_psql():
    """Check if psql is installed"""
    try:
        result = subprocess.run(
            ['psql', '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        print_success(f"PostgreSQL client found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("PostgreSQL client (psql) not found!")
        print_info("Please install PostgreSQL:")
        print("  Windows: https://www.postgresql.org/download/windows/")
        print("  Mac: brew install postgresql")
        print("  Linux: sudo apt-get install postgresql-client")
        return False

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

def test_connection(config):
    """Test database connection"""
    print_info("Testing database connection...")
    
    env = os.environ.copy()
    env['PGPASSWORD'] = config['password']
    
    try:
        result = subprocess.run(
            [
                'psql',
                '-h', config['host'],
                '-p', config['port'],
                '-U', config['user'],
                '-d', config['database'],
                '-c', 'SELECT version();'
            ],
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        print_success("Database connection successful!")
        return True
    except subprocess.CalledProcessError as e:
        print_error("Database connection failed!")
        print(f"Error: {e.stderr}")
        return False

def create_backup(config):
    """Create database backup"""
    print_info("Creating database backup...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"backup_{config['database']}_{timestamp}.sql"
    
    env = os.environ.copy()
    env['PGPASSWORD'] = config['password']
    
    try:
        subprocess.run(
            [
                'pg_dump',
                '-h', config['host'],
                '-p', config['port'],
                '-U', config['user'],
                '-d', config['database'],
                '-f', backup_file
            ],
            env=env,
            check=True
        )
        print_success(f"Backup created: {backup_file}")
        return backup_file
    except subprocess.CalledProcessError as e:
        print_warning("Backup failed, but continuing anyway...")
        print(f"Error: {e}")
        return None

def run_migration(config, migration_file):
    """Run the database migration"""
    print_info("Running database migration...")
    
    env = os.environ.copy()
    env['PGPASSWORD'] = config['password']
    
    try:
        result = subprocess.run(
            [
                'psql',
                '-h', config['host'],
                '-p', config['port'],
                '-U', config['user'],
                '-d', config['database'],
                '-f', str(migration_file)
            ],
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        print_success("Migration completed successfully!")
        print()
        print("Migration output:")
        print(result.stdout)
        
        return True
    except subprocess.CalledProcessError as e:
        print_error("Migration failed!")
        print(f"Error output:\n{e.stderr}")
        return False

def verify_migration(config):
    """Verify migration was successful"""
    print_info("Verifying migration...")
    
    env = os.environ.copy()
    env['PGPASSWORD'] = config['password']
    
    # Check for new columns
    check_sql = """
    SELECT COUNT(*) as new_columns
    FROM information_schema.columns 
    WHERE table_name = 'products' 
    AND column_name IN ('display_name', 'brand', 'model_number', 'product_type');
    """
    
    try:
        result = subprocess.run(
            [
                'psql',
                '-h', config['host'],
                '-p', config['port'],
                '-U', config['user'],
                '-d', config['database'],
                '-t',  # Tuples only (no headers)
                '-c', check_sql
            ],
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        count = int(result.stdout.strip())
        if count == 4:
            print_success(f"Verification passed! Found {count} new columns.")
            return True
        else:
            print_warning(f"Verification incomplete. Found {count}/4 new columns.")
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
    
    # Check if psql is installed
    if not check_psql():
        sys.exit(1)
    
    print()
    
    # Find migration file
    migration_file = find_migration_file()
    if not migration_file:
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
    if run_migration(config, migration_file):
        print()
        verify_migration(config)
        print()
        print_next_steps()
        sys.exit(0)
    else:
        print()
        print_error("Migration failed. Please check the error messages above.")
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
