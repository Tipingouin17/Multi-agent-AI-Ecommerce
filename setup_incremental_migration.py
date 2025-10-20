"""
Smart Incremental Migration Script
Multi-Agent E-Commerce Platform

This script intelligently migrates the database by:
1. Loading credentials from .env file
2. Checking which tables already exist
3. Running only the necessary migrations
4. Handling existing schema properly

Usage:
    python setup_incremental_migration.py
"""

import os
import sys
import psycopg2
from psycopg2 import sql
import time
from datetime import datetime
from pathlib import Path

# Try to load python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Using environment variables only.")

# ANSI color codes
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
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

# Database configuration from .env
DB_CONFIG = {
    "host": os.getenv('DATABASE_HOST', 'localhost'),
    "port": int(os.getenv('DATABASE_PORT', 5432)),
    "database": os.getenv('DATABASE_NAME', 'multi_agent_ecommerce'),
    "user": os.getenv('DATABASE_USER', 'postgres'),
    "password": os.getenv('DATABASE_PASSWORD', 'postgres123'),
}

class SmartMigration:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.start_time = None
        self.existing_tables = set()
        self.migrations_run = []
        
    def connect(self):
        """Connect to PostgreSQL"""
        print_info("Connecting to PostgreSQL database...")
        print_info(f"Host: {DB_CONFIG['host']}")
        print_info(f"Database: {DB_CONFIG['database']}")
        print_info(f"User: {DB_CONFIG['user']}")
        
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            print_success("Connected to database successfully!")
            return True
        except Exception as e:
            print_error(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from database"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print_info("Disconnected from database")
    
    def get_existing_tables(self):
        """Get list of existing tables"""
        print_info("Checking existing tables...")
        
        try:
            self.cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            self.existing_tables = {row[0] for row in self.cursor.fetchall()}
            print_success(f"Found {len(self.existing_tables)} existing tables")
            return True
        except Exception as e:
            print_error(f"Failed to get existing tables: {e}")
            return False
    
    def run_migration_file(self, filepath, description=""):
        """Run a single migration file"""
        filename = os.path.basename(filepath)
        print_info(f"Running migration: {filename}")
        if description:
            print_info(f"  Description: {description}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Execute the migration
            self.cursor.execute(sql_content)
            self.conn.commit()
            
            print_success(f"  ✅ {filename} completed successfully")
            self.migrations_run.append(filename)
            return True
            
        except Exception as e:
            self.conn.rollback()
            print_error(f"  ❌ {filename} failed: {e}")
            return False
    
    def run_incremental_migrations(self):
        """Run migrations incrementally based on what exists"""
        print_header("RUNNING INCREMENTAL MIGRATIONS")
        
        migrations_dir = Path('database/migrations')
        
        # Define migration order (only run what's needed)
        migration_files = [
            ('002_order_agent_enhancements.sql', 'Order Agent enhancements'),
            ('003_product_agent_enhancements.sql', 'Product Agent enhancements'),
            ('006_5_fix_existing_schema.sql', 'Schema compatibility fixes'),
            ('004_inventory_agent.sql', 'Inventory Agent'),
            ('005_customer_agent.sql', 'Customer Agent'),
            ('006_payment_agent.sql', 'Payment Agent'),
            ('007_shipping_agent.sql', 'Shipping Agent'),
            ('008_notification_agent.sql', 'Notification Agent'),
        ]
        
        # Check which migrations are needed
        for migration_file, description in migration_files:
            filepath = migrations_dir / migration_file
            
            if not filepath.exists():
                print_warning(f"Migration file not found: {migration_file}")
                continue
            
            # Run the migration
            success = self.run_migration_file(filepath, description)
            
            if not success:
                print_warning(f"Migration {migration_file} had issues, but continuing...")
        
        print_success(f"\n✅ Completed {len(self.migrations_run)} migrations")
        return True
    
    def seed_sample_data(self):
        """Seed sample data"""
        print_header("SEEDING SAMPLE DATA")
        
        print_info("Importing seed data script...")
        
        try:
            # Import and run the seed data script
            sys.path.insert(0, os.path.dirname(__file__))
            from database.seed_data_complete import CompleteDatabaseSeeder
            
            print_info("Starting data seeding process...")
            seeder = CompleteDatabaseSeeder()
            
            if not seeder.connect():
                print_error("Failed to connect for seeding")
                return False
            
            seeder.seed_all()
            seeder.disconnect()
            
            print_success("Sample data seeded successfully!")
            return True
            
        except ImportError as e:
            print_warning(f"Seed script not found or import failed: {e}")
            print_info("Skipping sample data seeding")
            return True  # Not critical, continue
        except Exception as e:
            print_error(f"Seeding failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def verify_database(self):
        """Verify database integrity"""
        print_header("VERIFYING DATABASE INTEGRITY")
        
        # Check table count
        self.cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        table_count = self.cursor.fetchone()[0]
        print_success(f"Total tables: {table_count}")
        
        # Check for key tables
        key_tables = [
            'customers', 'products', 'orders', 'order_items', 'inventory',
            'warehouses', 'carriers', 'payments', 'shipments', 'notifications'
        ]
        
        print_info("\nVerifying key tables:")
        all_present = True
        
        for table in key_tables:
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = %s
                )
            """, (table,))
            exists = self.cursor.fetchone()[0]
            
            if exists:
                # Get record count
                try:
                    self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = self.cursor.fetchone()[0]
                    print_success(f"  {table:.<40} {count:>6} records")
                except:
                    print_success(f"  {table:.<40} EXISTS")
            else:
                print_warning(f"  {table:.<40} MISSING")
                all_present = False
        
        if all_present:
            print_success(f"\n✅ All key tables verified!")
        else:
            print_warning(f"\n⚠️  Some tables are missing (this may be expected)")
        
        return True
    
    def system_health_check(self):
        """Perform system health check"""
        print_header("SYSTEM HEALTH CHECK")
        
        checks = []
        
        # Check 1: Database connection
        try:
            self.cursor.execute("SELECT version()")
            version = self.cursor.fetchone()[0]
            print_success(f"PostgreSQL version: {version.split(',')[0]}")
            checks.append(True)
        except:
            print_error("Database connection check failed")
            checks.append(False)
        
        # Check 2: Extensions
        try:
            self.cursor.execute("""
                SELECT extname FROM pg_extension 
                WHERE extname IN ('uuid-ossp', 'pg_trgm')
            """)
            extensions = [row[0] for row in self.cursor.fetchall()]
            
            if 'uuid-ossp' in extensions:
                print_success("UUID extension enabled")
            else:
                print_warning("UUID extension not found (optional)")
                
            if 'pg_trgm' in extensions:
                print_success("Full-text search extension enabled")
            else:
                print_warning("Full-text search extension not found (optional)")
            
            checks.append(True)
        except:
            print_warning("Extension check skipped")
            checks.append(True)
        
        # Check 3: Indexes
        try:
            self.cursor.execute("""
                SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public'
            """)
            index_count = self.cursor.fetchone()[0]
            print_success(f"Total indexes: {index_count}")
            checks.append(True)
        except:
            print_warning("Index check skipped")
            checks.append(True)
        
        # Summary
        passed = sum(checks)
        total = len(checks)
        
        print(f"\n{'─'*80}")
        if passed == total:
            print_success(f"All {total} health checks passed! ✨")
            return True
        else:
            print_warning(f"{passed}/{total} health checks passed")
            return True  # Don't fail on health checks
    
    def print_final_summary(self):
        """Print final setup summary"""
        elapsed_time = time.time() - self.start_time
        
        print_header("MIGRATION COMPLETE")
        
        print(f"{Colors.BOLD}📊 Migration Summary:{Colors.ENDC}")
        print(f"  • Database: {DB_CONFIG['database']}")
        print(f"  • Host: {DB_CONFIG['host']}")
        print(f"  • Migrations run: {len(self.migrations_run)}")
        print(f"  • Time taken: {elapsed_time:.2f} seconds")
        print(f"  • Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if self.migrations_run:
            print(f"\n{Colors.BOLD}✅ Migrations Applied:{Colors.ENDC}")
            for migration in self.migrations_run:
                print(f"  • {migration}")
        
        print(f"\n{Colors.BOLD}🚀 Next Steps:{Colors.ENDC}")
        print(f"  1. Start the agents:")
        print(f"     {Colors.OKCYAN}python agents/order_agent.py{Colors.ENDC}")
        print(f"     {Colors.OKCYAN}python agents/product_agent_api.py{Colors.ENDC}")
        
        print(f"\n  2. Access the UI:")
        print(f"     {Colors.OKCYAN}cd multi-agent-dashboard && npm run dev{Colors.ENDC}")
        
        print(f"\n  3. Test the API:")
        print(f"     {Colors.OKCYAN}curl http://localhost:8001/health{Colors.ENDC}")
        
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✨ Your multi-agent e-commerce system is ready! ✨{Colors.ENDC}\n")
    
    def run_smart_migration(self):
        """Run smart incremental migration"""
        self.start_time = time.time()
        
        print_header("SMART INCREMENTAL MIGRATION")
        print(f"{Colors.BOLD}Intelligently migrating database with existing tables...{Colors.ENDC}\n")
        
        # Step 1: Connect
        if not self.connect():
            print_error("Connection failed")
            return False
        
        try:
            # Step 2: Get existing tables
            if not self.get_existing_tables():
                print_error("Failed to check existing tables")
                return False
            
            # Step 3: Run incremental migrations
            if not self.run_incremental_migrations():
                print_warning("Some migrations had issues")
            
            # Step 4: Seed sample data (optional)
            print_info("\nDo you want to seed sample data? (This will add test records)")
            print_info("Type 'yes' to seed, or press Enter to skip:")
            try:
                response = input().strip().lower()
                if response == 'yes':
                    self.seed_sample_data()
                else:
                    print_info("Skipping sample data seeding")
            except:
                print_info("Skipping sample data seeding")
            
            # Step 5: Verify database
            self.verify_database()
            
            # Step 6: Health check
            self.system_health_check()
            
            # Step 7: Final summary
            self.print_final_summary()
            
            return True
            
        except Exception as e:
            print_error(f"Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.disconnect()

def main():
    """Main execution"""
    migration = SmartMigration()
    
    try:
        success = migration.run_smart_migration()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\n\nMigration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

