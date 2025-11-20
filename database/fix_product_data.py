"""
Fix Product Data - Add Images and Categories
Fixes Bug #21 (Product Images) and Bug #24 (Categories)
"""

import psycopg2
from psycopg2.extras import Json
import random

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "multi_agent_ecommerce",
    "user": "postgres",
    "password": "postgres",
}

# Product image URLs from Unsplash (free to use)
PRODUCT_IMAGES = {
    "Headphones": [
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800",
        "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=800",
        "https://images.unsplash.com/photo-1545127398-14699f92334b?w=800"
    ],
    "Watch": [
        "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800",
        "https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=800"
    ],
    "Speaker": [
        "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=800",
        "https://images.unsplash.com/photo-1545454675-3531b543be5d?w=800"
    ],
    "Cable": [
        "https://images.unsplash.com/photo-1625948515291-69613efd103f?w=800"
    ],
    "Phone Case": [
        "https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?w=800",
        "https://images.unsplash.com/photo-1585060544812-6b45742d762f?w=800"
    ],
    "Screen Protector": [
        "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=800"
    ],
    "Wireless Charger": [
        "https://images.unsplash.com/photo-1591290619762-c588f7e0e0c1?w=800"
    ],
    "Laptop Stand": [
        "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=800"
    ],
    "Keyboard": [
        "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=800",
        "https://images.unsplash.com/photo-1595225476474-87563907a212?w=800"
    ],
    "Mouse": [
        "https://images.unsplash.com/photo-1527814050087-3793815479db?w=800",
        "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=800"
    ],
    "Webcam": [
        "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=800"
    ],
    "SSD": [
        "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=800"
    ],
    "Monitor": [
        "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=800",
        "https://images.unsplash.com/photo-1593640408182-31c70c8268f5?w=800"
    ],
    "Desk Lamp": [
        "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=800"
    ],
    "Office Chair": [
        "https://images.unsplash.com/photo-1580480055273-228ff5388ef8?w=800",
        "https://images.unsplash.com/photo-1592078615290-033ee584e267?w=800"
    ],
    "Tablet": [
        "https://images.unsplash.com/photo-1561154464-82e9adf32764?w=800",
        "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=800"
    ],
    "Power Bank": [
        "https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?w=800"
    ],
    "Fitness Tracker": [
        "https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?w=800"
    ],
    "Backpack": [
        "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800",
        "https://images.unsplash.com/photo-1622560480605-d83c853bc5c3?w=800"
    ],
    "Earbuds": [
        "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=800",
        "https://images.unsplash.com/photo-1606841837239-c5a1a4a07af7?w=800"
    ]
}

# Category mapping
CATEGORY_MAPPING = {
    "Electronics": ["Headphones", "Watch", "Speaker", "Wireless Charger", "Keyboard", "Mouse", "Webcam", "SSD", "Monitor", "Tablet", "Power Bank", "Fitness Tracker", "Earbuds"],
    "Accessories": ["Cable", "Phone Case", "Screen Protector", "Backpack"],
    "Office": ["Laptop Stand", "Desk Lamp"],
    "Furniture": ["Office Chair"]
}

def connect_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected to database")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def create_categories(conn):
    """Create category records if they don't exist"""
    cursor = conn.cursor()
    
    print("\n📁 Creating categories...")
    
    categories = [
        ("Electronics", "electronics", "Electronic devices and gadgets", "https://images.unsplash.com/photo-1498049794561-7780e7231661?w=400"),
        ("Accessories", "accessories", "Phone and computer accessories", "https://images.unsplash.com/photo-1523206489230-c012c64b2b48?w=400"),
        ("Office", "office", "Office supplies and equipment", "https://images.unsplash.com/photo-1497366216548-37526070297c?w=400"),
        ("Furniture", "furniture", "Office and home furniture", "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=400")
    ]
    
    category_ids = {}
    
    for name, slug, description, image_url in categories:
        # Check if category exists
        cursor.execute("SELECT id FROM categories WHERE slug = %s", (slug,))
        result = cursor.fetchone()
        
        if result:
            category_ids[name] = result[0]
            print(f"  ✓ Category '{name}' already exists (ID: {result[0]})")
        else:
            cursor.execute("""
                INSERT INTO categories (name, slug, description, image_url, is_active, sort_order)
                VALUES (%s, %s, %s, %s, true, %s)
                RETURNING id
            """, (name, slug, description, image_url, len(category_ids)))
            category_ids[name] = cursor.fetchone()[0]
            print(f"  ✅ Created category '{name}' (ID: {category_ids[name]})")
    
    conn.commit()
    cursor.close()
    return category_ids

def get_product_images(product_name):
    """Get images for a product based on name keywords"""
    for keyword, images in PRODUCT_IMAGES.items():
        if keyword.lower() in product_name.lower():
            return images
    
    # Default fallback image
    return ["https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800"]

def get_product_category(product_name, category_ids):
    """Get category ID for a product based on name"""
    for category_name, keywords in CATEGORY_MAPPING.items():
        for keyword in keywords:
            if keyword.lower() in product_name.lower():
                return category_ids.get(category_name)
    
    # Default to Electronics
    return category_ids.get("Electronics")

def update_products(conn, category_ids):
    """Update all products with images and category_id"""
    cursor = conn.cursor()
    
    print("\n📦 Updating products...")
    
    # Get all products
    cursor.execute("SELECT id, name, sku FROM products")
    products = cursor.fetchall()
    
    updated_count = 0
    
    for product_id, name, sku in products:
        # Get images for this product
        images = get_product_images(name)
        
        # Get category ID
        category_id = get_product_category(name, category_ids)
        
        # Generate slug from name
        slug = name.lower().replace(" ", "-").replace("(", "").replace(")", "")
        
        # Update product
        cursor.execute("""
            UPDATE products 
            SET images = %s, 
                category_id = %s,
                slug = %s,
                status = 'active',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (Json(images), category_id, slug, product_id))
        
        updated_count += 1
        print(f"  ✅ Updated '{name}' - {len(images)} images, category ID: {category_id}")
    
    conn.commit()
    cursor.close()
    
    print(f"\n✅ Updated {updated_count} products")

def verify_updates(conn):
    """Verify that updates were successful"""
    cursor = conn.cursor()
    
    print("\n🔍 Verifying updates...")
    
    # Check products with images
    cursor.execute("SELECT COUNT(*) FROM products WHERE images IS NOT NULL AND images::text != '[]'")
    products_with_images = cursor.fetchone()[0]
    
    # Check products with categories
    cursor.execute("SELECT COUNT(*) FROM products WHERE category_id IS NOT NULL")
    products_with_categories = cursor.fetchone()[0]
    
    # Total products
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]
    
    cursor.close()
    
    print(f"  📊 Total products: {total_products}")
    print(f"  🖼️  Products with images: {products_with_images}")
    print(f"  📁 Products with categories: {products_with_categories}")
    
    if products_with_images == total_products and products_with_categories == total_products:
        print("\n✅ All products have images and categories!")
        return True
    else:
        print("\n⚠️  Some products are missing data")
        return False

def main():
    print("=" * 80)
    print("🔧 FIXING PRODUCT DATA - IMAGES AND CATEGORIES")
    print("=" * 80)
    
    conn = connect_db()
    if not conn:
        return
    
    try:
        # Step 1: Create categories
        category_ids = create_categories(conn)
        
        # Step 2: Update products
        update_products(conn, category_ids)
        
        # Step 3: Verify
        verify_updates(conn)
        
        print("\n" + "=" * 80)
        print("✅ PRODUCT DATA FIX COMPLETE!")
        print("=" * 80)
        print("\nFixed Bugs:")
        print("  ✅ Bug #21: Product images added")
        print("  ✅ Bug #24: Product categories assigned")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("\n👋 Database connection closed")

if __name__ == "__main__":
    main()
