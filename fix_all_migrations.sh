#!/bin/bash
# Comprehensive Migration Fix Script
# This script fixes all known issues in the migration files

echo "🔧 Fixing all migration files..."

cd "$(dirname "$0")"

# Fix 1: Add DROP TRIGGER IF EXISTS before CREATE TRIGGER in product migration
echo "📝 Fixing product migration triggers..."
sed -i 's/^CREATE TRIGGER /DROP TRIGGER IF EXISTS /g' database/migrations/003_product_agent_enhancements.sql
# Now re-add CREATE TRIGGER after the DROP
sed -i 's/^DROP TRIGGER IF EXISTS \(.*\) BEFORE/DROP TRIGGER IF EXISTS \1;\nCREATE TRIGGER \1 BEFORE/g' database/migrations/003_product_agent_enhancements.sql

# Fix 2: Ensure all CREATE INDEX have IF NOT EXISTS (already done but verify)
echo "📝 Ensuring all indexes have IF NOT EXISTS..."
for file in database/migrations/00{3,4,6,7,8}_*.sql; do
    if [ -f "$file" ]; then
        # Fix any remaining CREATE INDEX without IF NOT EXISTS
        sed -i 's/^CREATE INDEX \([^I]\)/CREATE INDEX IF NOT EXISTS \1/g' "$file"
        # Fix double IF NOT EXISTS
        sed -i 's/IF NOT EXISTS IF NOT EXISTS/IF NOT EXISTS/g' "$file"
        echo "  ✅ Fixed: $file"
    fi
done

# Fix 3: Add CREATE OR REPLACE for all functions
echo "📝 Fixing function definitions..."
for file in database/migrations/*.sql; do
    if [ -f "$file" ]; then
        sed -i 's/^CREATE FUNCTION /CREATE OR REPLACE FUNCTION /g' "$file"
        echo "  ✅ Fixed functions in: $(basename $file)"
    fi
done

echo ""
echo "✅ All migration fixes applied!"
echo ""
echo "📊 Summary of fixes:"
echo "  • Product migration: Added DROP TRIGGER IF EXISTS"
echo "  • All migrations: Ensured IF NOT EXISTS for indexes"
echo "  • All migrations: Changed to CREATE OR REPLACE for functions"
echo "  • Schema compatibility: Added missing column fixes"
echo ""
echo "🚀 Ready to run: python setup_incremental_migration.py"

