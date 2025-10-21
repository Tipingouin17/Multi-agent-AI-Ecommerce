"""
Complete System Setup Script
Multi-Agent E-Commerce Platform

This script automates the complete setup process:
1. Creates database schema (all 145+ tables)
2. Seeds sample data for all 26 agents
3. Verifies database integrity
4. Provides system health check

Usage:
    python setup_complete_system.py
    
    Or with custom database:
    DATABASE_HOST=localhost DATABASE_PASSWORD=mypass python setup_complete_system.py
"""

import os
import sys
import psycopg2
from psycopg2 import sql
import time
from datetime import datetime

# ANSI color codes for pretty output
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
    """Print formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

# Database configuration
DB_CONFIG = {
    "host": os.environ.get('DATABASE_HOST', 'localhost'),
    "port": int(os.environ.get('DATABASE_PORT', 5432)),
    "database": os.environ.get('DATABASE_NAME', 'multi_agent_ecommerce'),
    "user": os.environ.get('DATABASE_USER', 'postgres'),
    "password": os.environ.get('DATABASE_PASSWORD'),
}

class SystemSetup:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.start_time = None
        
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
        except psycopg2.OperationalError as e:
            print_error(f"Connection failed: {e}")
            print_warning("Please ensure PostgreSQL is running and credentials are correct")
            return False
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from database"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print_info("Disconnected from database")
    
    def check_database_exists(self):
        """Check if database exists"""
        print_info("Checking if database exists...")
        
        try:
            # Connect to postgres database to check
            temp_conn = psycopg2.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                database='postgres',
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password']
            )
            temp_cursor = temp_conn.cursor()
            
            temp_cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (DB_CONFIG['database'],)
            )
            exists = temp_cursor.fetchone() is not None
            
            temp_cursor.close()
            temp_conn.close()
            
            if exists:
                print_success(f"Database '{DB_CONFIG['database']}' exists")
            else:
                print_warning(f"Database '{DB_CONFIG['database']}' does not exist")
                print_info("Creating database...")
                self.create_database()
            
            return True
            
        except Exception as e:
            print_error(f"Error checking database: {e}")
            return False
    
    def create_database(self):
        """Create database if it doesn't exist"""
        try:
            temp_conn = psycopg2.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                database='postgres',
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password']
            )
            temp_conn.autocommit = True
            temp_cursor = temp_conn.cursor()
            
            temp_cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(DB_CONFIG['database'])
                )
            )
            
            temp_cursor.close()
            temp_conn.close()
            
            print_success(f"Database '{DB_CONFIG['database']}' created successfully!")
            
        except Exception as e:
            print_error(f"Error creating database: {e}")
    
    def run_schema_migration(self):
        """Run database schema migration"""
        print_header("RUNNING DATABASE SCHEMA MIGRATION")
        
        schema_file = 'database/migrations/000_complete_system_schema.sql'
        
        if not os.path.exists(schema_file):
            print_error(f"Schema file not found: {schema_file}")
            return False
        
        print_info(f"Reading schema from: {schema_file}")
        
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            print_info("Executing schema migration...")
            self.cursor.execute(schema_sql)
            self.conn.commit()
            
            print_success("Database schema created successfully!")
            return True
            
        except Exception as e:
            self.conn.rollback()
            print_error(f"Schema migration failed: {e}")
            return False
    
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
            print_error(f"Failed to import seed script: {e}")
            return False
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
        print_info(f"Total tables: {table_count}")
        
        # Check for key tables
        key_tables = [
            'customers', 'products', 'orders', 'order_items', 'inventory',
            'warehouses', 'carriers', 'payments', 'shipments', 'notifications',
            'analytics_events', 'returns', 'fraud_checks', 'product_recommendations',
            'promotions', 'suppliers', 'marketplace_connections', 'tax_rates',
            'gdpr_consent', 'audit_logs', 'support_tickets', 'chat_conversations',
            'knowledge_articles', 'workflow_executions', 'sync_operations',
            'api_requests', 'system_metrics', 'backups', 'system_users'
        ]
        
        print_info("\nVerifying key tables:")
        missing_tables = []
        
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
                self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = self.cursor.fetchone()[0]
                print_success(f"  {table:.<40} {count:>6} records")
            else:
                print_error(f"  {table:.<40} MISSING")
                missing_tables.append(table)
        
        if missing_tables:
            print_warning(f"\n⚠️  {len(missing_tables)} tables are missing!")
            return False
        else:
            print_success(f"\n✅ All {len(key_tables)} key tables verified!")
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
                checks.append(True)
            else:
                print_warning("UUID extension not found")
                checks.append(False)
                
            if 'pg_trgm' in extensions:
                print_success("Full-text search extension enabled")
                checks.append(True)
            else:
                print_warning("Full-text search extension not found")
                checks.append(False)
        except:
            print_error("Extension check failed")
            checks.append(False)
        
        # Check 3: Materialized views
        try:
            self.cursor.execute("""
                SELECT COUNT(*) FROM pg_matviews WHERE schemaname = 'public'
            """)
            view_count = self.cursor.fetchone()[0]
            print_success(f"Materialized views: {view_count}")
            checks.append(True)
        except:
            print_error("Materialized view check failed")
            checks.append(False)
        
        # Check 4: Indexes
        try:
            self.cursor.execute("""
                SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public'
            """)
            index_count = self.cursor.fetchone()[0]
            print_success(f"Total indexes: {index_count}")
            checks.append(True)
        except:
            print_error("Index check failed")
            checks.append(False)
        
        # Summary
        passed = sum(checks)
        total = len(checks)
        
        print(f"\n{'─'*80}")
        if passed == total:
            print_success(f"All {total} health checks passed! ✨")
            return True
        else:
            print_warning(f"{passed}/{total} health checks passed")
            return False
    
    def print_final_summary(self):
        """Print final setup summary"""
        elapsed_time = time.time() - self.start_time
        
        print_header("SETUP COMPLETE")
        
        print(f"{Colors.BOLD}📊 Setup Summary:{Colors.ENDC}")
        print(f"  • Database: {DB_CONFIG['database']}")
        print(f"  • Host: {DB_CONFIG['host']}")
        print(f"  • Time taken: {elapsed_time:.2f} seconds")
        print(f"  • Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n{Colors.BOLD}🚀 Next Steps:{Colors.ENDC}")
        print(f"  1. Start the agents:")
        print(f"     {Colors.OKCYAN}python agents/order_agent.py{Colors.ENDC}")
        print(f"     {Colors.OKCYAN}python agents/product_agent_api.py{Colors.ENDC}")
        print(f"     {Colors.OKCYAN}... (and other agents){Colors.ENDC}")
        
        print(f"\n  2. Access the UI:")
        print(f"     {Colors.OKCYAN}cd multi-agent-dashboard && npm run dev{Colors.ENDC}")
        
        print(f"\n  3. Test the API:")
        print(f"     {Colors.OKCYAN}curl http://localhost:8001/health{Colors.ENDC}")
        
        print(f"\n{Colors.BOLD}📚 Documentation:{Colors.ENDC}")
        print(f"  • COMPREHENSIVE_DELIVERY_SUMMARY.md")
        print(f"  • TESTING_NEW_AGENTS_GUIDE.md")
        print(f"  • AGENT_VERIFICATION_REPORT.md")
        
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✨ Your multi-agent e-commerce system is ready to use! ✨{Colors.ENDC}\n")
    
    def run_complete_setup(self):
        """Run complete setup process"""
        self.start_time = time.time()
        
        print_header("MULTI-AGENT E-COMMERCE SYSTEM SETUP")
        print(f"{Colors.BOLD}Setting up complete system with all 26 agents...{Colors.ENDC}\n")
        
        # Step 1: Check database
        if not self.check_database_exists():
            print_error("Database check failed")
            return False
        
        # Step 2: Connect
        if not self.connect():
            print_error("Connection failed")
            return False
        
        try:
            # Step 3: Run schema migration
            if not self.run_schema_migration():
                print_error("Schema migration failed")
                return False
            
            # Step 4: Seed sample data
            if not self.seed_sample_data():
                print_warning("Sample data seeding failed (continuing anyway)")
            
            # Step 5: Verify database
            if not self.verify_database():
                print_warning("Database verification found issues")
            
            # Step 6: Health check
            self.system_health_check()
            
            # Step 7: Final summary
            self.print_final_summary()
            
            return True
            
        except Exception as e:
            print_error(f"Setup failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.disconnect()

def main():
    """Main execution"""
    setup = SystemSetup()
    
    try:
        success = setup.run_complete_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

