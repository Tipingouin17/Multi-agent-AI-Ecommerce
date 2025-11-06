#!/usr/bin/env python3
"""
Replenishment Agent v3
Handles automated inventory replenishment, demand forecasting, and purchase order management
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import math
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.database import get_db_connection
from shared.db_models import (
    Product, Inventory, PurchaseOrder, PurchaseOrderItem,
    ReplenishmentSetting, ReplenishmentRecommendation, DemandForecast
)

app = FastAPI(title="Replenishment Agent", version="3.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Pydantic Models
# ============================================================================

class ReplenishmentSettingCreate(BaseModel):
    product_id: int
    enabled: bool = True
    lead_time_days: int = 7
    ordering_cost: float = 50.00
    holding_cost_per_unit: float = 2.00

class PurchaseOrderCreate(BaseModel):
    vendor_id: int
    items: List[Dict]  # [{"product_id": 1, "quantity": 100, "unit_cost": 10.50}]
    expected_delivery_date: Optional[str] = None
    notes: Optional[str] = None

class PurchaseOrderUpdate(BaseModel):
    status: Optional[str] = None
    actual_delivery_date: Optional[str] = None
    notes: Optional[str] = None

# ============================================================================
# Helper Functions
# ============================================================================

def calculate_avg_daily_sales(product_id: int, days: int = 30) -> float:
    """Calculate average daily sales over the past N days"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT COALESCE(SUM(oi.quantity), 0) as total_quantity
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE oi.product_id = %s
            AND o.created_at >= NOW() - INTERVAL '%s days'
            AND o.status NOT IN ('cancelled', 'refunded')
        """
        cursor.execute(query, (product_id, days))
        result = cursor.fetchone()
        total_quantity = result[0] if result else 0
        
        return float(total_quantity) / days if days > 0 else 0.0
    finally:
        cursor.close()
        conn.close()

def calculate_max_daily_sales(product_id: int, days: int = 90) -> float:
    """Calculate maximum daily sales over the past N days"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT COALESCE(MAX(daily_sales), 0) as max_sales
            FROM (
                SELECT DATE(o.created_at) as sale_date, SUM(oi.quantity) as daily_sales
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE oi.product_id = %s
                AND o.created_at >= NOW() - INTERVAL '%s days'
                AND o.status NOT IN ('cancelled', 'refunded')
                GROUP BY DATE(o.created_at)
            ) daily_totals
        """
        cursor.execute(query, (product_id, days))
        result = cursor.fetchone()
        return float(result[0]) if result else 0.0
    finally:
        cursor.close()
        conn.close()

def calculate_reorder_point(avg_daily_sales: float, lead_time_days: int, safety_stock: int) -> int:
    """Calculate Reorder Point (ROP)"""
    # ROP = (Average Daily Sales × Lead Time) + Safety Stock
    rop = (avg_daily_sales * lead_time_days) + safety_stock
    return math.ceil(rop)

def calculate_safety_stock(avg_daily_sales: float, max_daily_sales: float, 
                          avg_lead_time: int, max_lead_time: int) -> int:
    """Calculate Safety Stock"""
    # Safety Stock = (Max Daily Sales × Max Lead Time) - (Avg Daily Sales × Avg Lead Time)
    safety_stock = (max_daily_sales * max_lead_time) - (avg_daily_sales * avg_lead_time)
    return math.ceil(max(safety_stock, 0))

def calculate_eoq(annual_demand: float, ordering_cost: float, holding_cost: float) -> int:
    """Calculate Economic Order Quantity (EOQ)"""
    if holding_cost <= 0:
        return 0
    
    # EOQ = √[(2 × Annual Demand × Ordering Cost) / Holding Cost per Unit]
    eoq = math.sqrt((2 * annual_demand * ordering_cost) / holding_cost)
    return math.ceil(eoq)

def generate_po_number() -> str:
    """Generate unique PO number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"PO-{timestamp}"

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "replenishment_agent",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/replenishment/settings")
async def create_replenishment_setting(setting: ReplenishmentSettingCreate):
    """Create or update replenishment settings for a product"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Calculate metrics
        avg_daily_sales = calculate_avg_daily_sales(setting.product_id, 30)
        max_daily_sales = calculate_max_daily_sales(setting.product_id, 90)
        
        # Calculate safety stock (assume max lead time is 1.5x avg)
        max_lead_time = math.ceil(setting.lead_time_days * 1.5)
        safety_stock = calculate_safety_stock(
            avg_daily_sales, max_daily_sales,
            setting.lead_time_days, max_lead_time
        )
        
        # Calculate reorder point
        reorder_point = calculate_reorder_point(
            avg_daily_sales, setting.lead_time_days, safety_stock
        )
        
        # Calculate EOQ
        annual_demand = avg_daily_sales * 365
        eoq = calculate_eoq(annual_demand, setting.ordering_cost, setting.holding_cost_per_unit)
        
        # Upsert replenishment settings
        query = """
            INSERT INTO replenishment_settings 
            (product_id, enabled, reorder_point, safety_stock, economic_order_quantity,
             lead_time_days, ordering_cost, holding_cost_per_unit, avg_daily_sales, 
             max_daily_sales, last_calculated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (product_id) 
            DO UPDATE SET
                enabled = EXCLUDED.enabled,
                reorder_point = EXCLUDED.reorder_point,
                safety_stock = EXCLUDED.safety_stock,
                economic_order_quantity = EXCLUDED.economic_order_quantity,
                lead_time_days = EXCLUDED.lead_time_days,
                ordering_cost = EXCLUDED.ordering_cost,
                holding_cost_per_unit = EXCLUDED.holding_cost_per_unit,
                avg_daily_sales = EXCLUDED.avg_daily_sales,
                max_daily_sales = EXCLUDED.max_daily_sales,
                last_calculated_at = NOW(),
                updated_at = NOW()
            RETURNING *
        """
        
        cursor.execute(query, (
            setting.product_id, setting.enabled, reorder_point, safety_stock, eoq,
            setting.lead_time_days, setting.ordering_cost, setting.holding_cost_per_unit,
            avg_daily_sales, max_daily_sales
        ))
        
        result = cursor.fetchone()
        conn.commit()
        
        return {
            "success": True,
            "message": "Replenishment settings created/updated successfully",
            "data": {
                "id": result[0],
                "product_id": result[1],
                "enabled": result[2],
                "reorder_point": result[3],
                "safety_stock": result[4],
                "economic_order_quantity": result[5],
                "lead_time_days": result[6],
                "avg_daily_sales": float(result[9]),
                "max_daily_sales": float(result[10])
            }
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/replenishment/settings/{product_id}")
async def get_replenishment_setting(product_id: int):
    """Get replenishment settings for a product"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = "SELECT * FROM replenishment_settings WHERE product_id = %s"
        cursor.execute(query, (product_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Replenishment settings not found")
        
        return {
            "success": True,
            "data": {
                "id": result[0],
                "product_id": result[1],
                "enabled": result[2],
                "reorder_point": result[3],
                "safety_stock": result[4],
                "economic_order_quantity": result[5],
                "lead_time_days": result[6],
                "ordering_cost": float(result[7]),
                "holding_cost_per_unit": float(result[8]),
                "avg_daily_sales": float(result[9]),
                "max_daily_sales": float(result[10]),
                "last_calculated_at": result[11].isoformat() if result[11] else None
            }
        }
        
    finally:
        cursor.close()
        conn.close()

@app.post("/api/replenishment/analyze")
async def analyze_replenishment_needs():
    """Analyze all products and generate replenishment recommendations"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get all products with replenishment settings enabled
        query = """
            SELECT rs.product_id, rs.reorder_point, rs.economic_order_quantity, rs.safety_stock,
                   p.name, p.sku, COALESCE(SUM(i.quantity), 0) as current_stock
            FROM replenishment_settings rs
            JOIN products p ON rs.product_id = p.id
            LEFT JOIN inventory i ON p.id = i.product_id
            WHERE rs.enabled = true
            GROUP BY rs.product_id, rs.reorder_point, rs.economic_order_quantity, 
                     rs.safety_stock, p.name, p.sku
        """
        
        cursor.execute(query)
        products = cursor.fetchall()
        
        recommendations = []
        
        for product in products:
            product_id, reorder_point, eoq, safety_stock, name, sku, current_stock = product
            
            # Check if stock is below reorder point
            if current_stock <= reorder_point:
                # Determine priority
                if current_stock <= safety_stock:
                    priority = 'critical'
                    reason = 'stockout_risk'
                elif current_stock <= reorder_point * 0.5:
                    priority = 'high'
                    reason = 'below_reorder_point'
                else:
                    priority = 'medium'
                    reason = 'approaching_reorder_point'
                
                # Insert recommendation
                insert_query = """
                    INSERT INTO replenishment_recommendations
                    (product_id, current_stock, reorder_point, recommended_quantity, 
                     reason, priority, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'pending')
                    ON CONFLICT (product_id) WHERE status = 'pending'
                    DO UPDATE SET
                        current_stock = EXCLUDED.current_stock,
                        recommended_quantity = EXCLUDED.recommended_quantity,
                        priority = EXCLUDED.priority,
                        updated_at = NOW()
                    RETURNING id
                """
                
                cursor.execute(insert_query, (
                    product_id, current_stock, reorder_point, eoq, reason, priority
                ))
                
                rec_id = cursor.fetchone()[0]
                
                recommendations.append({
                    "id": rec_id,
                    "product_id": product_id,
                    "product_name": name,
                    "sku": sku,
                    "current_stock": current_stock,
                    "reorder_point": reorder_point,
                    "recommended_quantity": eoq,
                    "priority": priority,
                    "reason": reason
                })
        
        conn.commit()
        
        return {
            "success": True,
            "message": f"Analysis complete. Found {len(recommendations)} products needing replenishment",
            "data": {
                "total_recommendations": len(recommendations),
                "critical": len([r for r in recommendations if r['priority'] == 'critical']),
                "high": len([r for r in recommendations if r['priority'] == 'high']),
                "medium": len([r for r in recommendations if r['priority'] == 'medium']),
                "recommendations": recommendations
            }
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/replenishment/recommendations")
async def get_recommendations(
    status: str = Query("pending", description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority")
):
    """Get replenishment recommendations"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT rr.*, p.name, p.sku
            FROM replenishment_recommendations rr
            JOIN products p ON rr.product_id = p.id
            WHERE rr.status = %s
        """
        params = [status]
        
        if priority:
            query += " AND rr.priority = %s"
            params.append(priority)
        
        query += " ORDER BY rr.priority DESC, rr.created_at DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        recommendations = []
        for row in results:
            recommendations.append({
                "id": row[0],
                "product_id": row[1],
                "product_name": row[11],
                "sku": row[12],
                "current_stock": row[2],
                "reorder_point": row[3],
                "recommended_quantity": row[4],
                "reason": row[5],
                "priority": row[6],
                "status": row[7],
                "po_id": row[8],
                "created_at": row[9].isoformat() if row[9] else None
            })
        
        return {
            "success": True,
            "data": recommendations
        }
        
    finally:
        cursor.close()
        conn.close()

@app.post("/api/purchase-orders")
async def create_purchase_order(po: PurchaseOrderCreate):
    """Create a new purchase order"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Generate PO number
        po_number = generate_po_number()
        
        # Calculate total amount
        total_amount = sum(item['quantity'] * item['unit_cost'] for item in po.items)
        
        # Insert purchase order
        po_query = """
            INSERT INTO purchase_orders
            (po_number, vendor_id, status, order_date, expected_delivery_date, 
             total_amount, notes)
            VALUES (%s, %s, 'draft', NOW(), %s, %s, %s)
            RETURNING id
        """
        
        cursor.execute(po_query, (
            po_number, po.vendor_id, po.expected_delivery_date, 
            total_amount, po.notes
        ))
        
        po_id = cursor.fetchone()[0]
        
        # Insert purchase order items
        for item in po.items:
            item_query = """
                INSERT INTO purchase_order_items
                (po_id, product_id, quantity, unit_cost, total_cost, status)
                VALUES (%s, %s, %s, %s, %s, 'pending')
            """
            
            total_cost = item['quantity'] * item['unit_cost']
            cursor.execute(item_query, (
                po_id, item['product_id'], item['quantity'], 
                item['unit_cost'], total_cost
            ))
            
            # Update recommendation status if exists
            cursor.execute("""
                UPDATE replenishment_recommendations
                SET status = 'po_created', po_id = %s, resolved_at = NOW()
                WHERE product_id = %s AND status = 'pending'
            """, (po_id, item['product_id']))
        
        conn.commit()
        
        return {
            "success": True,
            "message": "Purchase order created successfully",
            "data": {
                "id": po_id,
                "po_number": po_number,
                "total_amount": total_amount,
                "items_count": len(po.items)
            }
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/purchase-orders")
async def get_purchase_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    vendor_id: Optional[int] = Query(None, description="Filter by vendor")
):
    """Get purchase orders"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = "SELECT * FROM purchase_orders WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        if vendor_id:
            query += " AND vendor_id = %s"
            params.append(vendor_id)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        purchase_orders = []
        for row in results:
            purchase_orders.append({
                "id": row[0],
                "po_number": row[1],
                "vendor_id": row[2],
                "status": row[3],
                "order_date": row[4].isoformat() if row[4] else None,
                "expected_delivery_date": row[5].isoformat() if row[5] else None,
                "actual_delivery_date": row[6].isoformat() if row[6] else None,
                "total_amount": float(row[7]),
                "currency": row[8],
                "notes": row[12]
            })
        
        return {
            "success": True,
            "data": purchase_orders
        }
        
    finally:
        cursor.close()
        conn.close()

@app.get("/api/purchase-orders/{po_id}")
async def get_purchase_order(po_id: int):
    """Get purchase order details with items"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get PO
        po_query = "SELECT * FROM purchase_orders WHERE id = %s"
        cursor.execute(po_query, (po_id,))
        po_result = cursor.fetchone()
        
        if not po_result:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        
        # Get PO items
        items_query = """
            SELECT poi.*, p.name, p.sku
            FROM purchase_order_items poi
            JOIN products p ON poi.product_id = p.id
            WHERE poi.po_id = %s
        """
        cursor.execute(items_query, (po_id,))
        items_results = cursor.fetchall()
        
        items = []
        for item in items_results:
            items.append({
                "id": item[0],
                "product_id": item[2],
                "product_name": item[10],
                "sku": item[11],
                "quantity": item[3],
                "unit_cost": float(item[4]),
                "total_cost": float(item[5]),
                "received_quantity": item[6],
                "status": item[7]
            })
        
        return {
            "success": True,
            "data": {
                "id": po_result[0],
                "po_number": po_result[1],
                "vendor_id": po_result[2],
                "status": po_result[3],
                "order_date": po_result[4].isoformat() if po_result[4] else None,
                "expected_delivery_date": po_result[5].isoformat() if po_result[5] else None,
                "actual_delivery_date": po_result[6].isoformat() if po_result[6] else None,
                "total_amount": float(po_result[7]),
                "currency": po_result[8],
                "notes": po_result[12],
                "items": items
            }
        }
        
    finally:
        cursor.close()
        conn.close()

@app.put("/api/purchase-orders/{po_id}")
async def update_purchase_order(po_id: int, update: PurchaseOrderUpdate):
    """Update purchase order"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        updates = []
        params = []
        
        if update.status:
            updates.append("status = %s")
            params.append(update.status)
        
        if update.actual_delivery_date:
            updates.append("actual_delivery_date = %s")
            params.append(update.actual_delivery_date)
        
        if update.notes:
            updates.append("notes = %s")
            params.append(update.notes)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        updates.append("updated_at = NOW()")
        params.append(po_id)
        
        query = f"UPDATE purchase_orders SET {', '.join(updates)} WHERE id = %s RETURNING *"
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        
        conn.commit()
        
        return {
            "success": True,
            "message": "Purchase order updated successfully",
            "data": {
                "id": result[0],
                "po_number": result[1],
                "status": result[3]
            }
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/replenishment/stats")
async def get_replenishment_stats():
    """Get replenishment statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        stats = {}
        
        # Total products with replenishment enabled
        cursor.execute("SELECT COUNT(*) FROM replenishment_settings WHERE enabled = true")
        stats['products_monitored'] = cursor.fetchone()[0]
        
        # Pending recommendations by priority
        cursor.execute("""
            SELECT priority, COUNT(*) 
            FROM replenishment_recommendations 
            WHERE status = 'pending'
            GROUP BY priority
        """)
        priority_counts = {row[0]: row[1] for row in cursor.fetchall()}
        stats['pending_recommendations'] = {
            'critical': priority_counts.get('critical', 0),
            'high': priority_counts.get('high', 0),
            'medium': priority_counts.get('medium', 0),
            'low': priority_counts.get('low', 0),
            'total': sum(priority_counts.values())
        }
        
        # PO stats
        cursor.execute("""
            SELECT status, COUNT(*), COALESCE(SUM(total_amount), 0)
            FROM purchase_orders
            WHERE created_at >= NOW() - INTERVAL '30 days'
            GROUP BY status
        """)
        po_stats = cursor.fetchall()
        stats['purchase_orders_30d'] = {
            row[0]: {"count": row[1], "total_amount": float(row[2])}
            for row in po_stats
        }
        
        return {
            "success": True,
            "data": stats
        }
        
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8032))
    uvicorn.run(app, host="0.0.0.0", port=port)
