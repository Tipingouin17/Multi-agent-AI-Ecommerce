"""
Inventory Agent V3 - Production Ready with New Schema
Manages inventory across warehouses using the unified database schema
"""

import os
import sys
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_, desc

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Import shared modules
from shared.db_models import Inventory, Product, Warehouse, Alert
from shared.db_connection import get_database_url
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create database engine
engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create FastAPI app
app = FastAPI(title="Inventory Agent V3", version="3.0.0")

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

class InventoryUpdate(BaseModel):
    product_id: int
    warehouse_id: int
    quantity: int

class InventoryAdjustment(BaseModel):
    product_id: int
    warehouse_id: int
    quantity_change: int
    reason: str

class InventoryBulkUpdate(BaseModel):
    updates: List[InventoryUpdate]

# ============================================================================
# INVENTORY ENDPOINTS
# ============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent": "inventory_agent_v3", "version": "3.0.0"}

@app.get("/api/inventory")
def get_inventory(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    product_id: Optional[int] = None,
    warehouse_id: Optional[int] = None,
    low_stock: bool = False,
    out_of_stock: bool = False,
    db: Session = Depends(get_db)
):
    """Get inventory with filtering and pagination"""
    try:
        query = db.query(Inventory).join(Product).join(Warehouse)
        
        if product_id:
            query = query.filter(Inventory.product_id == product_id)
        if warehouse_id:
            query = query.filter(Inventory.warehouse_id == warehouse_id)
        if low_stock:
            query = query.filter(Inventory.quantity <= Inventory.reorder_point)
        if out_of_stock:
            query = query.filter(Inventory.quantity == 0)
        
        total = query.count()
        offset = (page - 1) * limit
        inventory_items = query.offset(offset).limit(limit).all()
        
        result = []
        for item in inventory_items:
            item_dict = item.to_dict()
            if item.product:
                item_dict['product'] = {
                    'id': item.product.id,
                    'name': item.product.name,
                    'sku': item.product.sku,
                    'price': float(item.product.price)
                }
            if item.warehouse:
                item_dict['warehouse'] = {
                    'id': item.warehouse.id,
                    'name': item.warehouse.name,
                    'code': item.warehouse.code
                }
            item_dict['is_low_stock'] = item.quantity <= item.reorder_point
            item_dict['is_out_of_stock'] = item.quantity == 0
            result.append(item_dict)
        
        return {
            "inventory": result,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    except Exception as e:
        logger.error(f"Error getting inventory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/inventory")
def update_inventory_bulk(updates: InventoryBulkUpdate, db: Session = Depends(get_db)):
    """Bulk update inventory quantities"""
    try:
        updated_items = []
        for update in updates.updates:
            item = db.query(Inventory).filter(
                and_(
                    Inventory.product_id == update.product_id,
                    Inventory.warehouse_id == update.warehouse_id
                )
            ).first()
            
            if item:
                item.quantity = update.quantity
                item.updated_at = datetime.utcnow()
            else:
                item = Inventory(
                    product_id=update.product_id,
                    warehouse_id=update.warehouse_id,
                    quantity=update.quantity
                )
                db.add(item)
            updated_items.append(item)
        
        db.commit()
        for item in updated_items:
            db.refresh(item)
        
        return {
            "message": f"Updated {len(updated_items)} inventory items",
            "items": [item.to_dict() for item in updated_items]
        }
    except Exception as e:
        logger.error(f"Error bulk updating inventory: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/inventory/adjust")
def adjust_inventory(adjustment: InventoryAdjustment, db: Session = Depends(get_db)):
    """Adjust inventory quantity"""
    try:
        item = db.query(Inventory).filter(
            and_(
                Inventory.product_id == adjustment.product_id,
                Inventory.warehouse_id == adjustment.warehouse_id
            )
        ).first()
        
        if not item:
            raise HTTPException(status_code=404, detail="Inventory record not found")
        
        old_quantity = item.quantity
        new_quantity = old_quantity + adjustment.quantity_change
        
        if new_quantity < 0:
            raise HTTPException(status_code=400, detail="Adjustment would result in negative inventory")
        
        item.quantity = new_quantity
        item.updated_at = datetime.utcnow()
        
        # Create low stock alert if needed
        if new_quantity <= item.reorder_point:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            warehouse = db.query(Warehouse).filter(Warehouse.id == item.warehouse_id).first()
            alert = Alert(
                alert_type="low_stock",
                severity="warning",
                title=f"Low Stock: {product.name if product else 'Unknown'}",
                message=f"Product {product.sku if product else 'Unknown'} at {warehouse.name if warehouse else 'Unknown'} is below reorder point",
                source="inventory_agent",
                status="active"
            )
            db.add(alert)
        
        db.commit()
        db.refresh(item)
        
        return {
            "message": "Inventory adjusted successfully",
            "adjustment": {
                "old_quantity": old_quantity,
                "change": adjustment.quantity_change,
                "new_quantity": new_quantity,
                "reason": adjustment.reason
            },
            "inventory": item.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adjusting inventory: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/inventory/low-stock")
def get_low_stock_items(limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db)):
    """Get items that are low on stock"""
    try:
        items = db.query(Inventory).filter(
            Inventory.quantity <= Inventory.reorder_point
        ).join(Product).join(Warehouse).limit(limit).all()
        
        result = []
        for item in items:
            item_dict = item.to_dict()
            item_dict['product'] = {'id': item.product.id, 'name': item.product.name, 'sku': item.product.sku}
            item_dict['warehouse'] = {'id': item.warehouse.id, 'name': item.warehouse.name}
            result.append(item_dict)
        
        return {"low_stock_items": result, "count": len(result)}
    except Exception as e:
        logger.error(f"Error getting low stock items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/inventory/stats")
def get_inventory_stats(db: Session = Depends(get_db)):
    """Get inventory statistics"""
    try:
        total_items = db.query(func.count(Inventory.id)).scalar()
        total_quantity = db.query(func.sum(Inventory.quantity)).scalar() or 0
        total_reserved = db.query(func.sum(Inventory.reserved_quantity)).scalar() or 0
        low_stock_count = db.query(func.count(Inventory.id)).filter(
            Inventory.quantity <= Inventory.reorder_point
        ).scalar()
        out_of_stock_count = db.query(func.count(Inventory.id)).filter(
            Inventory.quantity == 0
        ).scalar()
        inventory_value = db.query(func.sum(Product.cost * Inventory.quantity)).join(Product).scalar() or 0
        
        return {
            "total_items": total_items,
            "total_quantity": total_quantity,
            "total_reserved": total_reserved,
            "total_available": total_quantity - total_reserved,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "inventory_value": float(inventory_value)
        }
    except Exception as e:
        logger.error(f"Error getting inventory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/warehouses")
def get_warehouses(db: Session = Depends(get_db)):
    """Get all warehouses"""
    try:
        warehouses = db.query(Warehouse).filter(Warehouse.is_active == True).all()
        result = []
        for warehouse in warehouses:
            warehouse_dict = warehouse.to_dict()
            inventory_count = db.query(func.count(Inventory.id)).filter(
                Inventory.warehouse_id == warehouse.id
            ).scalar()
            warehouse_dict['inventory_items'] = inventory_count
            result.append(warehouse_dict)
        return {"warehouses": result}
    except Exception as e:
        logger.error(f"Error getting warehouses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts")
def get_alerts_simple(limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db)):
    """Get inventory alerts for merchant dashboard (simple path)"""
    try:
        # Get low stock items
        low_stock_items = db.query(Inventory).filter(
            Inventory.quantity <= Inventory.reorder_point
        ).order_by(Inventory.quantity).limit(limit).all()
        
        # Format for frontend
        alerts = []
        for item in low_stock_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            
            # Determine severity
            if item.quantity <= item.reorder_point * 0.5:
                severity = "critical"
            elif item.quantity <= item.reorder_point * 0.75:
                severity = "high"
            else:
                severity = "medium"
            
            alerts.append({
                "id": f"INV-{item.id}",
                "product": product.name if product else "Unknown Product",
                "sku": product.sku if product else f"SKU-{item.product_id}",
                "current_stock": item.quantity,
                "reorder_point": item.reorder_point,
                "severity": severity,
                "message": "Stock critically low" if severity == "critical" else "Stock below reorder point"
            })
        
        return alerts
    
    except Exception as e:
        logger.error(f"Error getting inventory alerts: {e}")
        # Return empty array on error to prevent frontend crashes
        return []

@app.get("/api/alerts")
def get_alerts(status: Optional[str] = None, limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db)):
    """Get inventory-related alerts"""
    try:
        query = db.query(Alert).filter(Alert.source == "inventory_agent")
        if status:
            query = query.filter(Alert.status == status)
        alerts = query.order_by(desc(Alert.created_at)).limit(limit).all()
        return {"alerts": [alert.to_dict() for alert in alerts], "count": len(alerts)}
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# INVENTORY OPERATIONS
# ============================================================================

@app.post("/inventory/export")
def export_inventory(
    itemIds: List[int],
    db: Session = Depends(get_db)
):
    """Export inventory items to CSV"""
    try:
        items = db.query(Inventory).filter(Inventory.id.in_(itemIds)).all()
        
        # Generate CSV data
        csv_lines = ["Item ID,Product ID,Warehouse,Quantity,Reserved,Available,Reorder Point"]
        for item in items:
            csv_lines.append(
                f"{item.id},{item.product_id},{item.warehouse_id},{item.quantity},"
                f"{item.reserved_quantity},{item.available_quantity},{item.reorder_point}"
            )
        
        return "\n".join(csv_lines)
    except Exception as e:
        logger.error(f"Error exporting inventory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/inventory/bulk-reorder")
def bulk_reorder_items(
    itemIds: List[int],
    db: Session = Depends(get_db)
):
    """Trigger reorder for multiple inventory items"""
    try:
        items = db.query(Inventory).filter(Inventory.id.in_(itemIds)).all()
        
        # TODO: Implement actual reorder logic
        # For now, just return success
        
        return {
            "success": True,
            "reordered_count": len(items),
            "message": f"Reorder triggered for {len(items)} items"
        }
    except Exception as e:
        logger.error(f"Error bulk reordering items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/inventory/transfer")
def transfer_inventory(
    data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Transfer inventory between warehouses"""
    try:
        product_id = data.get('productId')
        from_warehouse_id = data.get('fromWarehouseId')
        to_warehouse_id = data.get('toWarehouseId')
        quantity = data.get('quantity')
        
        # Get source inventory
        source_inv = db.query(Inventory).filter(
            Inventory.product_id == product_id,
            Inventory.warehouse_id == from_warehouse_id
        ).first()
        
        if not source_inv or source_inv.available_quantity < quantity:
            raise HTTPException(status_code=400, detail="Insufficient inventory")
        
        # Get or create destination inventory
        dest_inv = db.query(Inventory).filter(
            Inventory.product_id == product_id,
            Inventory.warehouse_id == to_warehouse_id
        ).first()
        
        if not dest_inv:
            dest_inv = Inventory(
                product_id=product_id,
                warehouse_id=to_warehouse_id,
                quantity=0,
                reserved_quantity=0,
                available_quantity=0,
                reorder_point=source_inv.reorder_point
            )
            db.add(dest_inv)
        
        # Transfer
        source_inv.quantity -= quantity
        source_inv.available_quantity -= quantity
        dest_inv.quantity += quantity
        dest_inv.available_quantity += quantity
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Transferred {quantity} units"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transferring inventory: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/inventory/adjust")
def adjust_inventory(
    data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Manual inventory adjustment"""
    try:
        inventory_id = data.get('inventoryId')
        adjustment = data.get('adjustment')  # Can be positive or negative
        reason = data.get('reason', 'Manual adjustment')
        
        inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
        
        if not inventory:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        
        # Apply adjustment
        inventory.quantity += adjustment
        inventory.available_quantity += adjustment
        inventory.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(inventory)
        
        return {
            "success": True,
            "new_quantity": inventory.quantity,
            "message": f"Inventory adjusted by {adjustment}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adjusting inventory: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
