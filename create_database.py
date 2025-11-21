#!/usr/bin/env python3
"""
Create Database Script
Creates the ecommerce database if it doesn't exist
"""

import sys
import os

try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("❌ ERROR: psycopg2 library not found!")
    print()
    print("Please install it using:")
    print("  pip install psycopg2-binary")
    sys.exit(1)

# Color codes
class Colors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    OKCYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

def main():
    print()
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{'Create Database'.center(60)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print()
    
    # Get connection details
    print_info("PostgreSQL Server Configuration:")
    host = input(f"Host [localhost]: ").strip() or "localhost"
    port = input(f"Port [5432]: ").strip() or "5432"
    user = input(f"Admin User [postgres]: ").strip() or "postgres"
    
    import getpass
    password = getpass.getpass("Password: ")
    
    print()
    
    # Database name to create
    db_name = input("Database name to create [ecommerce]: ").strip() or "ecommerce"
    
    print()
    print_info(f"Will create database: {db_name}")
    print()
    
    try:
        # Connect to PostgreSQL server (not to a specific database)
        print_info("Connecting to PostgreSQL server...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database='postgres'  # Connect to default postgres database
        )
        
        # Set autocommit mode (required for CREATE DATABASE)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print_success("Connected to PostgreSQL server!")
        print()
        
        # Check if database already exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )
        
        if cursor.fetchone():
            print_info(f"Database '{db_name}' already exists!")
            print()
            overwrite = input("Do you want to drop and recreate it? (yes/no): ").strip().lower()
            
            if overwrite == 'yes':
                print_info(f"Dropping database '{db_name}'...")
                cursor.execute(sql.SQL("DROP DATABASE {}").format(
                    sql.Identifier(db_name)
                ))
                print_success(f"Database '{db_name}' dropped!")
                print()
            else:
                print_info("Keeping existing database.")
                cursor.close()
                conn.close()
                print()
                print_success("You can now run: python migrate_database.py")
                sys.exit(0)
        
        # Create database
        print_info(f"Creating database '{db_name}'...")
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(db_name)
        ))
        print_success(f"Database '{db_name}' created successfully!")
        
        cursor.close()
        conn.close()
        
        print()
        print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}✅ Success!{Colors.ENDC}")
        print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print()
        
        print_info("Next steps:")
        print("  1. Run the migration script:")
        print(f"     python migrate_database.py")
        print()
        print("  2. Or set environment variables:")
        print(f"     set DB_NAME={db_name}")
        print(f"     set DB_HOST={host}")
        print(f"     set DB_PORT={port}")
        print(f"     set DB_USER={user}")
        print(f"     set DB_PASSWORD=your_password")
        print(f"     python migrate_database.py")
        print()
        
    except psycopg2.Error as e:
        print()
        print_error("Failed to create database!")
        print(f"Error: {e}")
        print()
        print_info("Common issues:")
        print("  - Wrong password")
        print("  - User doesn't have CREATE DATABASE permission")
        print("  - PostgreSQL server not running")
        sys.exit(1)
    except Exception as e:
        print()
        print_error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_info("Cancelled by user.")
        sys.exit(0)
