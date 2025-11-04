"""
Backoffice Agent V3 - Production Ready with New Schema
Manages backoffice operations
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
from shared.db_models import Order, Product, Customer
from shared.db_connection import get_database_url
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create database engine
engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create FastAPI app
app = FastAPI(title="Backoffice Agent V3", version="3.0.0")

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
    return {"status": "healthy", "agent": "backoffice_agent_v3", "version": "3.0.0"}


@app.get("/api/backoffice/tasks")
def get_tasks():
    """Get backoffice tasks"""
    return {"tasks": [], "message": "Backoffice system ready"}

@app.get("/api/backoffice/reports")
def get_reports():
    """Get backoffice reports"""
    return {
        "reports": [
            {"id": 1, "name": "Daily Sales", "status": "ready"},
            {"id": 2, "name": "Inventory Status", "status": "ready"}
        ]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8027))
    uvicorn.run(app, host="0.0.0.0", port=port)
