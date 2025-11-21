#!/bin/bash
# =====================================================
# Database Update Script for Product Wizard
# =====================================================

echo "=========================================="
echo "Product Wizard Database Migration"
echo "=========================================="
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ ERROR: PostgreSQL client (psql) not found!"
    echo "Please install PostgreSQL client first."
    exit 1
fi

# Database connection details
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-ecommerce}"
DB_USER="${DB_USER:-postgres}"

echo "Database Configuration:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""

# Confirm before proceeding
read -p "Do you want to proceed with the migration? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Migration cancelled."
    exit 0
fi

echo ""
echo "Starting migration..."
echo ""

# Run the migration
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/migrations/024_product_wizard_fields_corrected.sql

# Check if migration was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Migration completed successfully!"
    echo "=========================================="
    echo ""
    echo "What was added:"
    echo "  ✅ 35+ new fields to products table"
    echo "  ✅ 10 new tables for wizard data"
    echo "  ✅ 2 auto-calculation triggers"
    echo "  ✅ 2 views for easy querying"
    echo "  ✅ 20+ indexes for performance"
    echo ""
    echo "Next steps:"
    echo "  1. Restart your backend (product agent)"
    echo "  2. Restart your frontend (npm run dev)"
    echo "  3. Test product creation with the wizard"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "❌ Migration failed!"
    echo "=========================================="
    echo ""
    echo "Please check the error messages above."
    echo "Common issues:"
    echo "  - Wrong database credentials"
    echo "  - Database not running"
    echo "  - Insufficient permissions"
    echo ""
    exit 1
fi
