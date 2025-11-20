"""
Supplier Management Agent v3
Manages suppliers, products sourcing, and purchase orders
Port: 8042
"""

import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import uvicorn
from dotenv import load_dotenv

from shared.db_connection import get_database_url
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, joinedload
from shared.auth import get_current_user, require_merchant, User
from shared.db_models import (
    Supplier, SupplierProduct, PurchaseOrder, PurchaseOrderItem, SupplierPayment,
    Product
)

# Load environment variables
load_dotenv()

# Create database engine and session
engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(title="Supplier Management Agent", version="3.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "supplier_agent_v3", "version": "3.0.0"}

# ==================== PYDANTIC MODELS ====================

class SupplierCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict] = None
    website: Optional[str] = None
    payment_terms: Optional[str] = None
    lead_time_days: Optional[int] = None
    minimum_order_value: Optional[float] = None
    currency: Optional[str] = "USD"
    rating: Optional[float] = None
    notes: Optional[str] = None

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict] = None
    website: Optional[str] = None
    payment_terms: Optional[str] = None
    lead_time_days: Optional[int] = None
    minimum_order_value: Optional[float] = None
    currency: Optional[str] = None
    is_active: Optional[bool] = None
    rating: Optional[float] = None
    notes: Optional[str] = None

class SupplierProductCreate(BaseModel):
    supplier_id: int
    product_id: int
    supplier_sku: Optional[str] = None
    cost_price: float
    currency: Optional[str] = "USD"
    lead_time_days: Optional[int] = None
    minimum_order_quantity: Optional[int] = 1
    is_preferred: Optional[bool] = False

class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    order_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    items: List[Dict[str, Any]]
    notes: Optional[str] = None

# ==================== SUPPLIER ENDPOINTS ====================

@app.get("/api/suppliers")
async def get_suppliers(
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant)
):
    """Get all suppliers with optional filters"""
    query = db.query(Supplier)
    
    if is_active is not None:
        query = query.filter(Supplier.is_active == is_active)
    
    if search:
        query = query.filter(
            (Supplier.name.ilike(f"%{search}%")) |
            (Supplier.contact_person.ilike(f"%{search}%")) |
            (Supplier.email.ilike(f"%{search}%"))
        )
    
    suppliers = query.order_by(Supplier.name).all()
    return [supplier.to_dict() for supplier in suppliers]

@app.get("/api/suppliers/{supplier_id}")
async def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant)
):
    """Get supplier by ID"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier.to_dict()

@app.post("/api/suppliers")
async def create_supplier(
    supplier_data: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant)
):
    """Create new supplier"""
    supplier = Supplier(
        name=supplier_data.name,
        contact_person=supplier_data.contact_person,
        email=supplier_data.email,
        phone=supplier_data.phone,
        address=supplier_data.address,
        website=supplier_data.website,
        payment_terms=supplier_data.payment_terms,
        lead_time_days=supplier_data.lead_time_days,
        minimum_order_value=supplier_data.minimum_order_value,
        currency=supplier_data.currency,
        rating=supplier_data.rating,
        notes=supplier_data.notes,
        created_by=current_user.user_id
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier.to_dict()

@app.patch("/api/suppliers/{supplier_id}")
async def update_supplier(
    supplier_id: int,
    supplier_data: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant)
):
    """Update supplier"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    for field, value in supplier_data.dict(exclude_unset=True).items():
        setattr(supplier, field, value)
    
    db.commit()
    db.refresh(supplier)
    return supplier.to_dict()

@app.delete("/api/suppliers/{supplier_id}")
async def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant)
):
    """Delete supplier"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    db.delete(supplier)
    db.commit()
    return {"message": "Supplier deleted successfully"}

# ==================== SUPPLIER PRODUCTS ENDPOINTS ====================

@app.get("/api/suppliers/{supplier_id}/products")
async def get_supplier_products(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant)
):
    """Get all products from a supplier"""
    products = db.query(SupplierProduct).filter(
        SupplierProduct.supplier_id == supplier_id
    ).all()
    return [product.to_dict() for product in products]

@app.post("/api/supplier-products")
async def create_supplier_product(
    product_data: SupplierProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant)
):
    """Link product to supplier with pricing"""
    supplier_product = SupplierProduct(
        supplier_id=product_data.supplier_id,
        product_id=product_data.product_id,
        supplier_sku=product_data.supplier_sku,
        cost_price=product_data.cost_price,
        currency=product_data.currency,
        lead_time_days=product_data.lead_time_days,
        minimum_order_quantity=product_data.minimum_order_quantity,
        is_preferred=product_data.is_preferred
    )
    db.add(supplier_product)
    db.commit()
    db.refresh(supplier_product)
    return supplier_product.to_dict()

# ==================== PURCHASE ORDERS ENDPOINTS ====================

@app.get("/api/purchase-orders")
async def get_purchase_orders(
    supplier_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant)
):
    """Get all purchase orders with optional filters"""
    query = db.query(PurchaseOrder)
    
    if supplier_id:
        query = query.filter(PurchaseOrder.vendor_id == supplier_id)
    
    if status:
        query = query.filter(PurchaseOrder.status == status)
    
    orders = query.order_by(PurchaseOrder.order_date.desc()).all()
    return [order.to_dict() for order in orders]

@app.get("/api/purchase-orders/{order_id}")
async def get_purchase_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant)
):
    """Get purchase order by ID"""
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return order.to_dict()

@app.post("/api/purchase-orders")
async def create_purchase_order(
    order_data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant)
):
    """Create new purchase order"""
    # Generate PO number
    po_count = db.query(PurchaseOrder).count()
    po_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{po_count + 1:04d}"
    
    # Calculate totals
    total_amount = sum(item['quantity'] * item['unit_cost'] for item in order_data.items)
    
    # Create purchase order
    order = PurchaseOrder(
        po_number=po_number,
        vendor_id=order_data.supplier_id,
        status='draft',
        order_date=order_data.order_date or datetime.now(),
        expected_delivery_date=order_data.expected_delivery_date,
        total_amount=total_amount,
        notes=order_data.notes,
        created_by=current_user.user_id
    )
    db.add(order)
    db.flush()
    
    # Create order items
    for item_data in order_data.items:
        item = PurchaseOrderItem(
            po_id=order.id,
            product_id=item_data['product_id'],
            quantity=item_data['quantity'],
            unit_cost=item_data['unit_cost'],
            total_cost=item_data['quantity'] * item_data['unit_cost']
        )
        db.add(item)
    
    db.commit()
    db.refresh(order)
    return order.to_dict()

# ==================== SUPPLIER PERFORMANCE ====================

@app.get("/api/suppliers/{supplier_id}/performance")
async def get_supplier_performance(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant)
):
    """Get supplier performance metrics"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Get purchase orders
    orders = db.query(PurchaseOrder).filter(
        PurchaseOrder.vendor_id == supplier_id
    ).all()
    
    # Calculate metrics
    total_orders = len(orders)
    completed_orders = len([o for o in orders if o.status == 'completed'])
    on_time_deliveries = len([
        o for o in orders 
        if o.actual_delivery_date and o.expected_delivery_date 
        and o.actual_delivery_date <= o.expected_delivery_date
    ])
    
    total_spent = sum(float(o.total_amount) for o in orders)
    
    return {
        "supplier_id": supplier_id,
        "supplier_name": supplier.name,
        "total_orders": total_orders,
        "completed_orders": completed_orders,
        "on_time_delivery_rate": (on_time_deliveries / total_orders * 100) if total_orders > 0 else 0,
        "total_spent": total_spent,
        "average_order_value": total_spent / total_orders if total_orders > 0 else 0,
        "rating": float(supplier.rating) if supplier.rating else 0,
        "quality_score": float(supplier.quality_score) if supplier.quality_score else 0
    }

# ==================== RUN SERVER ====================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8042)
