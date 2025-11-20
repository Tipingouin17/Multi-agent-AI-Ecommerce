"""
Automated Database Migration Script
Runs SQL migrations for world-class features (Offers & Supplier Management)
Works with Docker PostgreSQL and local PostgreSQL
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration_with_psycopg2():
    """Run migrations using psycopg2 (Python PostgreSQL adapter)"""
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 not installed. Install it with: pip install psycopg2-binary")
        return False
    
    # Get database connection from environment
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'ecommerce_db')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    print(f"Connecting to PostgreSQL at {DB_HOST}:{DB_PORT}/{DB_NAME} as {DB_USER}...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected to database successfully!\n")
        
        # Migration files
        migrations = [
            'database/migrations/add_offers_management_fixed.sql',
            'database/migrations/add_supplier_management_fixed.sql'
        ]
        
        for migration_file in migrations:
            if not os.path.exists(migration_file):
                print(f"❌ Migration file not found: {migration_file}")
                continue
            
            print(f"Running migration: {migration_file}...")
            
            # Read and execute SQL file
            with open(migration_file, 'r') as f:
                sql = f.read()
                
                # Split by semicolon and execute each statement
                statements = [s.strip() for s in sql.split(';') if s.strip()]
                
                for i, statement in enumerate(statements, 1):
                    try:
                        cursor.execute(statement)
                        print(f"  ✅ Executed statement {i}/{len(statements)}")
                    except Exception as e:
                        # Skip if table already exists
                        if "already exists" in str(e):
                            print(f"  ⚠️  Statement {i} - Table already exists, skipping...")
                        else:
                            print(f"  ❌ Error in statement {i}: {e}")
                            raise
            
            print(f"✅ Successfully completed: {migration_file}\n")
        
        # Verify tables were created
        print("Verifying tables...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND (table_name LIKE 'offer%' OR table_name LIKE 'supplier%' OR table_name LIKE 'purchase%')
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        if tables:
            print("\n✅ Tables created successfully:")
            for table in tables:
                print(f"   - {table[0]}")
        else:
            print("\n⚠️  No tables found. Migration may have failed.")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("✅ ALL MIGRATIONS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nNext steps:")
        print("1. Start the Offers Agent: python agents/offers_agent_v3.py")
        print("2. Test the API: curl http://localhost:8040/health")
        print("3. Access the UI: http://localhost:5173/merchant/offers")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error running migrations: {e}")
        print("\nTroubleshooting:")
        print("1. Check your .env file has correct database credentials")
        print("2. Verify PostgreSQL is running (docker ps | grep postgres)")
        print("3. Try connecting manually: docker exec -it <container> psql -U <user> -d <db>")
        return False


def run_migration_with_sqlalchemy():
    """Run migrations using SQLAlchemy (alternative method)"""
    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        print("❌ SQLAlchemy not installed. Install it with: pip install sqlalchemy")
        return False
    
    from shared.db_connection import get_database_url
    
    print("Connecting to database using SQLAlchemy...")
    
    try:
        engine = create_engine(get_database_url())
        
        with engine.connect() as conn:
            print("✅ Connected to database successfully!\n")
            
            # Migration files
            migrations = [
                'database/migrations/add_offers_management_fixed.sql',
                'database/migrations/add_supplier_management_fixed.sql'
            ]
            
            for migration_file in migrations:
                if not os.path.exists(migration_file):
                    print(f"❌ Migration file not found: {migration_file}")
                    continue
                
                print(f"Running migration: {migration_file}...")
                
                # Read SQL file
                with open(migration_file, 'r') as f:
                    sql = f.read()
                    
                    # Split by semicolon and execute each statement separately
                    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
                    
                    for i, statement in enumerate(statements, 1):
                        try:
                            conn.execute(text(statement))
                            conn.commit()
                        except Exception as e:
                            if "already exists" in str(e):
                                pass  # Skip if already exists
                            else:
                                print(f"❌ Error in statement {i}: {e}")
                                raise
                    
                    print(f"✅ Successfully completed: {migration_file}\n")
            
            print("\n✅ ALL MIGRATIONS COMPLETED SUCCESSFULLY!")
            return True
            
    except Exception as e:
        print(f"\n❌ Error running migrations: {e}")
        return False


def main():
    print("="*60)
    print("DATABASE MIGRATION SCRIPT")
    print("World-Class Features: Offers & Supplier Management")
    print("="*60)
    print()
    
    # Check if migration files exist
    migrations = [
        'database/migrations/add_offers_management_fixed.sql',
        'database/migrations/add_supplier_management_fixed.sql'
    ]
    
    missing_files = [f for f in migrations if not os.path.exists(f)]
    if missing_files:
        print("❌ Migration files not found:")
        for f in missing_files:
            print(f"   - {f}")
        print("\nMake sure you're running this script from the project root directory.")
        sys.exit(1)
    
    # Try psycopg2 first (more reliable for raw SQL)
    print("Method 1: Using psycopg2...\n")
    success = run_migration_with_psycopg2()
    
    if not success:
        print("\n" + "="*60)
        print("Trying alternative method...")
        print("="*60 + "\n")
        
        print("Method 2: Using SQLAlchemy...\n")
        success = run_migration_with_sqlalchemy()
    
    if not success:
        print("\n" + "="*60)
        print("❌ MIGRATION FAILED")
        print("="*60)
        print("\nPlease try manual migration:")
        print("See DOCKER_DATABASE_MIGRATION_GUIDE.md for instructions")
        sys.exit(1)


if __name__ == "__main__":
    main()
