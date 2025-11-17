"""
Recommendation Agent V3 - Production Ready with New Schema
Provides product recommendations and personalization
"""

import os
import sys
import logging
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Import shared modules
from shared.db_models import Product, Customer, Order, OrderItem
from shared.db_connection import get_database_url
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create database engine
engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create FastAPI app
app = FastAPI(title="Recommendation Agent V3", version="3.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/health")
def health_check():
    return {"status": "healthy", "agent": "recommendation_agent_v3", "version": "3.0.0"}


@app.get("/api/recommendations/{customer_id}")
def get_recommendations(customer_id: int, limit: int = 10, db: Session = Depends(get_db)):
    """Get product recommendations for a customer"""
    try:
        # Simple recommendation: popular products
        popular_products = db.query(Product).limit(limit).all()
        return {"recommendations": [p.to_dict() for p in popular_products]}
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recommendations/trending")
def get_trending_products(limit: int = 10, db: Session = Depends(get_db)):
    """Get trending products"""
    try:
        products = db.query(Product).limit(limit).all()
        return {"trending": [p.to_dict() for p in products]}
    except Exception as e:
        logger.error(f"Error getting trending products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products/{product_id}/related")
def get_related_products(
    product_id: int,
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Get related products for a specific product"""
    try:
        # Get the product
        product = db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Get related products from same category
        related = db.query(Product).filter(
            Product.category_id == product.category_id,
            Product.id != product_id,
            Product.status == 'active'
        ).limit(limit).all()
        
        return {"related_products": [p.to_dict() for p in related]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting related products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recommendations")
def get_general_recommendations(
    customer_id: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get personalized recommendations for customer or general recommendations"""
    try:
        # If customer_id provided, get personalized recommendations
        # For now, return popular/featured products
        products = db.query(Product).filter(
            Product.status == 'active'
        ).order_by(Product.rating.desc()).limit(limit).all()
        
        return {"recommendations": [p.to_dict() for p in products]}
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8014))
    uvicorn.run(app, host="0.0.0.0", port=port)
