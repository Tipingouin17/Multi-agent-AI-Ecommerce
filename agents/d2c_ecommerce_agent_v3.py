"""
D2C E-commerce Agent V3 - Production Ready with New Schema
Direct-to-consumer e-commerce operations
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
from shared.db_models import Product, Order, Customer
from shared.db_connection import get_database_url
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create database engine
engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create FastAPI app
app = FastAPI(title="D2C E-commerce Agent V3", version="3.0.0")

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
    return {"status": "healthy", "agent": "d2c_ecommerce_agent_v3", "version": "3.0.0"}


@app.get("/api/d2c/storefront")
def get_storefront():
    """Get D2C storefront configuration"""
    return {
        "store_name": "My Store",
        "theme": "default",
        "status": "active"
    }

@app.get("/api/d2c/products")
def get_d2c_products(db: Session = Depends(get_db)):
    """Get products for D2C storefront"""
    try:
        products = db.query(Product).limit(20).all()
        return {"products": [p.to_dict() for p in products]}
    except Exception as e:
        logger.error(f"Error getting D2C products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8031))
    uvicorn.run(app, host="0.0.0.0", port=port)
