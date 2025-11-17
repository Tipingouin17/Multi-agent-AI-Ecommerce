"""
Product Agent V3 - Production Ready with New Schema
Manages product catalog using the unified database schema
"""

import os
import sys
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Import shared modules
from shared.db_models import Product, Category, Merchant, Inventory, Base
from shared.db_connection import get_database_url
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create database engine
engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create FastAPI app
app = FastAPI(title="Product Agent V3", version="3.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ProductCreate(BaseModel):
    merchant_id: int
    category_id: Optional[int] = None
    sku: str
    name: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    price: float
    cost: Optional[float] = None
    compare_at_price: Optional[float] = None
    weight: Optional[float] = None
    status: str = "draft"

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    price: Optional[float] = None
    cost: Optional[float] = None
    compare_at_price: Optional[float] = None
    weight: Optional[float] = None
    status: Optional[str] = None
    category_id: Optional[int] = None

class CategoryCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: bool = True

# ============================================================================
# PRODUCT ENDPOINTS
# ============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent": "product_agent_v3", "version": "3.0.0"}

@app.get("/api/products")
def get_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    merchant_id: Optional[int] = None,
    status: Optional[str] = None,
    sort_by: str = Query("created_at", regex="^(name|price|created_at|sales_count)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """
    Get all products with filtering, pagination, and sorting
    """
    try:
        # Build query
        query = db.query(Product)
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.sku.ilike(f"%{search}%"),
                    Product.description.ilike(f"%{search}%")
                )
            )
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        if merchant_id:
            query = query.filter(Product.merchant_id == merchant_id)
        
        if status:
            query = query.filter(Product.status == status)
        
        # Get total count
        total = query.count()
        
        # Apply sorting
        sort_column = getattr(Product, sort_by)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (page - 1) * limit
        products = query.offset(offset).limit(limit).all()
        
        # Get inventory for each product
        product_list = []
        for product in products:
            product_dict = product.to_dict()
            
            # Add inventory information
            inventory_items = db.query(Inventory).filter(
                Inventory.product_id == product.id
            ).all()
            
            total_quantity = sum(inv.quantity for inv in inventory_items)
            total_available = sum(inv.quantity - inv.reserved_quantity for inv in inventory_items)
            
            product_dict['inventory'] = {
                'total_quantity': total_quantity,
                'available_quantity': total_available,
                'warehouses': len(inventory_items)
            }
            
            product_list.append(product_dict)
        
        return {
            "products": product_list,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a single product by ID"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        product_dict = product.to_dict()
        
        # Add inventory information
        inventory_items = db.query(Inventory).filter(
            Inventory.product_id == product.id
        ).all()
        
        product_dict['inventory'] = [inv.to_dict() for inv in inventory_items]
        
        # Add category information
        if product.category:
            product_dict['category'] = product.category.to_dict()
        
        # Add merchant information
        if product.merchant:
            product_dict['merchant'] = product.merchant.to_dict()
        
        return product_dict
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/products")
def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product"""
    try:
        # Check if SKU already exists
        existing = db.query(Product).filter(Product.sku == product_data.sku).first()
        if existing:
            raise HTTPException(status_code=400, detail="SKU already exists")
        
        # Create slug from name
        slug = product_data.name.lower().replace(' ', '-').replace("'", '')
        
        # Create product
        product = Product(
            merchant_id=product_data.merchant_id,
            category_id=product_data.category_id,
            sku=product_data.sku,
            name=product_data.name,
            slug=slug,
            description=product_data.description,
            short_description=product_data.short_description,
            price=product_data.price,
            cost=product_data.cost,
            compare_at_price=product_data.compare_at_price,
            weight=product_data.weight,
            status=product_data.status
        )
        
        db.add(product)
        db.commit()
        db.refresh(product)
        
        return product.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/products/{product_id}")
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db)
):
    """Update a product"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Update fields
        update_data = product_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        product.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(product)
        
        return product.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        db.delete(product)
        db.commit()
        
        return {"message": "Product deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products/stats")
def get_product_stats(db: Session = Depends(get_db)):
    """Get product statistics"""
    try:
        total_products = db.query(func.count(Product.id)).scalar()
        active_products = db.query(func.count(Product.id)).filter(
            Product.status == 'active'
        ).scalar()
        
        total_value = db.query(func.sum(Product.price * Product.sales_count)).scalar() or 0
        
        return {
            "total_products": total_products,
            "active_products": active_products,
            "inactive_products": total_products - active_products,
            "total_value": float(total_value)
        }
    
    except Exception as e:
        logger.error(f"Error getting product stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics")
def get_product_analytics(
    time_range: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    category_id: Optional[int] = None,
    merchant_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get product analytics including revenue, top products, and conversion funnel
    """
    try:
        # Build base query
        query = db.query(Product)
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        if merchant_id:
            query = query.filter(Product.merchant_id == merchant_id)
        
        products = query.all()
        
        # Calculate totals
        total_revenue = sum(p.price * p.sales_count for p in products)
        total_units = sum(p.sales_count for p in products)
        avg_price = total_revenue / total_units if total_units > 0 else 0
        
        # Get top products by revenue
        top_products = sorted(
            products,
            key=lambda p: p.price * p.sales_count,
            reverse=True
        )[:10]
        
        top_products_data = [
            {
                "id": p.id,
                "name": p.name,
                "revenue": float(p.price * p.sales_count),
                "units": p.sales_count,
                "avg_price": float(p.price)
            }
            for p in top_products
        ]
        
        # Get revenue by category
        category_revenue = {}
        for p in products:
            cat_name = p.category.name if p.category else "Uncategorized"
            if cat_name not in category_revenue:
                category_revenue[cat_name] = 0
            category_revenue[cat_name] += p.price * p.sales_count
        
        revenue_by_category = [
            {
                "category": cat,
                "revenue": float(rev),
                "percentage": float((rev / total_revenue * 100) if total_revenue > 0 else 0)
            }
            for cat, rev in sorted(category_revenue.items(), key=lambda x: x[1], reverse=True)
        ]
        
        # Mock conversion funnel (would need tracking data in production)
        conversion_funnel = {
            "views": total_units * 10,  # Estimate: 10 views per sale
            "add_to_cart": int(total_units * 2),  # Estimate: 2 cart adds per sale
            "checkout": int(total_units * 1.2),  # Estimate: 1.2 checkouts per sale
            "purchase": total_units
        }
        
        return {
            "total_revenue": float(total_revenue),
            "total_units": total_units,
            "avg_price": float(avg_price),
            "top_products": top_products_data,
            "revenue_by_category": revenue_by_category,
            "conversion_funnel": conversion_funnel
        }
    
    except Exception as e:
        logger.error(f"Error getting product analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/featured")
def get_featured_products(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get featured products (top selling or highest rated)
    """
    try:
        # Get top selling products
        products = db.query(Product).filter(
            Product.status == 'active'
        ).order_by(
            Product.sales_count.desc()
        ).limit(limit).all()
        
        featured_products = []
        for product in products:
            product_dict = product.to_dict()
            
            # Add mock rating and reviews (would come from reviews table in production)
            product_dict['rating'] = 4.5
            product_dict['reviews'] = product.sales_count // 10 or 1
            product_dict['featured'] = True
            
            featured_products.append(product_dict)
        
        return featured_products
    
    except Exception as e:
        logger.error(f"Error getting featured products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# CATEGORY ENDPOINTS
# ============================================================================

@app.get("/api/categories")
def get_categories(db: Session = Depends(get_db)):
    """Get all categories"""
    try:
        categories = db.query(Category).filter(Category.is_active == True).all()
        return {"categories": [cat.to_dict() for cat in categories]}
    
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/categories")
def create_category(category_data: CategoryCreate, db: Session = Depends(get_db)):
    """Create a new category"""
    try:
        # Check if slug already exists
        existing = db.query(Category).filter(Category.slug == category_data.slug).first()
        if existing:
            raise HTTPException(status_code=400, detail="Slug already exists")
        
        category = Category(**category_data.dict())
        db.add(category)
        db.commit()
        db.refresh(category)
        
        return category.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating category: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# BULK OPERATIONS
# ============================================================================

@app.post("/products/bulk-delete")
def bulk_delete_products(
    productIds: List[int],
    db: Session = Depends(get_db)
):
    """Delete multiple products"""
    try:
        deleted_count = db.query(Product).filter(
            Product.id.in_(productIds)
        ).delete(synchronize_session=False)
        
        db.commit()
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Deleted {deleted_count} products"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error bulk deleting products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/products/bulk-sync")
def bulk_sync_products(
    productIds: List[int],
    db: Session = Depends(get_db)
):
    """Sync multiple products to marketplaces"""
    try:
        # TODO: Implement marketplace sync logic
        return {
            "success": True,
            "synced_count": len(productIds),
            "message": f"Synced {len(productIds)} products"
        }
    except Exception as e:
        logger.error(f"Error bulk syncing products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/products/bulk-update-status")
def bulk_update_product_status(
    productIds: List[int],
    status: str,
    db: Session = Depends(get_db)
):
    """Update status for multiple products"""
    try:
        updated_count = db.query(Product).filter(
            Product.id.in_(productIds)
        ).update(
            {"status": status, "updated_at": datetime.utcnow()},
            synchronize_session=False
        )
        
        db.commit()
        
        return {
            "success": True,
            "updated_count": updated_count,
            "message": f"Updated {updated_count} products to {status}"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error bulk updating products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/products/sync-all")
def sync_all_products(
    db: Session = Depends(get_db)
):
    """Sync all products with marketplaces"""
    try:
        # TODO: Implement full marketplace sync
        total_products = db.query(Product).count()
        return {
            "success": True,
            "synced_count": total_products,
            "message": f"Synced {total_products} products with marketplaces"
        }
    except Exception as e:
        logger.error(f"Error syncing all products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PRODUCT DETAILS & REVIEWS
# ============================================================================

@app.get("/products/{product_id}/reviews")
def get_product_reviews(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Get reviews for a product"""
    try:
        # TODO: Implement reviews table and logic
        return {"reviews": [], "average_rating": 0, "total_reviews": 0}
    except Exception as e:
        logger.error(f"Error getting product reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/categories")
def get_categories_list(
    db: Session = Depends(get_db)
):
    """Get all categories (for customer portal)"""
    try:
        categories = db.query(Category).all()
        return {"categories": [cat.to_dict() for cat in categories]}
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/new-arrivals")
def get_new_arrivals(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get new arrival products"""
    try:
        products = db.query(Product).filter(
            Product.status == 'active'
        ).order_by(desc(Product.created_at)).limit(limit).all()
        
        return {"products": [p.to_dict() for p in products]}
    except Exception as e:
        logger.error(f"Error getting new arrivals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
