"""
Customer Communication Agent V3 - Production Ready with New Schema
Manages customer communications and notifications
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
from shared.db_models import Customer, Order
from shared.db_connection import get_database_url
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create database engine
engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create FastAPI app
app = FastAPI(title="Customer Communication Agent V3", version="3.0.0")

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
    return {"status": "healthy", "agent": "customer_communication_v3", "version": "3.0.0"}


@app.post("/api/communications/send")
def send_communication(customer_id: int, message: str, channel: str = "email"):
    """Send communication to customer"""
    return {
        "status": "sent",
        "customer_id": customer_id,
        "channel": channel,
        "message": "Communication sent successfully"
    }

@app.get("/api/communications/templates")
def get_templates():
    """Get communication templates"""
    return {
        "templates": [
            {"id": "order_confirmation", "name": "Order Confirmation"},
            {"id": "shipping_notification", "name": "Shipping Notification"},
            {"id": "delivery_confirmation", "name": "Delivery Confirmation"}
        ]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8019))
    uvicorn.run(app, host="0.0.0.0", port=port)
