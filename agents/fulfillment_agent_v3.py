"""
Advanced Fulfillment Agent v3
Handles intelligent order fulfillment, warehouse selection, and inventory allocation
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = FastAPI(title="Advanced Fulfillment Agent", version="3.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "multi_agent_ecommerce"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres")
}

def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# ============================================================================
# Pydantic Models
# ============================================================================

class OrderItem(BaseModel):
    product_id: int
    sku: str
    quantity: int

class FulfillmentAnalysisRequest(BaseModel):
    order_id: int
    customer_id: int
    items: List[OrderItem]
    shipping_address: dict
    priority: Optional[str] = "standard"  # standard, priority, express

class ReservationCreate(BaseModel):
    order_id: int
    product_id: int
    sku: str
    warehouse_id: int
    quantity: int
    reservation_type: Optional[str] = "soft"
    expires_in_minutes: Optional[int] = 30

class BackorderCreate(BaseModel):
    order_id: int
    product_id: int
    sku: str
    customer_id: int
    quantity: int
    priority_score: Optional[int] = 0

class WaveCreate(BaseModel):
    warehouse_id: int
    wave_type: Optional[str] = "standard"
    order_ids: List[int]

# ============================================================================
# Helper Functions
# ============================================================================

def calculate_warehouse_score(warehouse_id: int, items: List[OrderItem], shipping_address: dict, conn) -> dict:
    """
    Calculate score for warehouse based on multiple factors
    Returns: {warehouse_id, score, can_fulfill, shipping_cost, estimated_days}
    """
    cursor = conn.cursor()
    
    # Check inventory availability
    can_fulfill = True
    total_items = 0
    
    for item in items:
        cursor.execute("""
            SELECT quantity_available 
            FROM inventory 
            WHERE product_id = %s AND warehouse_id = %s
        """, (item.product_id, warehouse_id))
        
        result = cursor.fetchone()
        if not result or result['quantity_available'] < item.quantity:
            can_fulfill = False
            break
        total_items += item.quantity
    
    # Get warehouse capacity
    cursor.execute("""
        SELECT current_load, total_capacity, utilization_percentage
        FROM warehouse_capacity
        WHERE warehouse_id = %s AND date = CURRENT_DATE
    """, (warehouse_id,))
    
    capacity = cursor.fetchone()
    capacity_score = 100
    if capacity:
        capacity_score = 100 - float(capacity['utilization_percentage'] or 0)
    
    # Simplified scoring (in production, would include distance calculation, shipping costs, etc.)
    base_score = 100 if can_fulfill else 0
    final_score = base_score * 0.7 + capacity_score * 0.3
    
    # Estimate shipping cost and days (simplified)
    estimated_cost = 10.00 + (total_items * 0.50)  # Base + per item
    estimated_days = 3  # Default 3 days
    
    cursor.close()
    
    return {
        "warehouse_id": warehouse_id,
        "score": round(final_score, 2),
        "can_fulfill": can_fulfill,
        "shipping_cost": estimated_cost,
        "estimated_days": estimated_days,
        "capacity_score": round(capacity_score, 2)
    }

def create_inventory_reservation(order_id: int, product_id: int, sku: str, warehouse_id: int, 
                                 quantity: int, reservation_type: str, expires_in_minutes: int, conn):
    """Create inventory reservation"""
    cursor = conn.cursor()
    
    expires_at = datetime.now() + timedelta(minutes=expires_in_minutes)
    
    cursor.execute("""
        INSERT INTO inventory_reservations 
        (order_id, product_id, sku, warehouse_id, quantity, reservation_type, expires_at, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'active')
        RETURNING id
    """, (order_id, product_id, sku, warehouse_id, quantity, reservation_type, expires_at))
    
    result = cursor.fetchone()
    conn.commit()
    cursor.close()
    
    return result['id']

def release_expired_reservations(conn):
    """Release all expired reservations"""
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE inventory_reservations 
        SET status = 'expired', released_at = NOW()
        WHERE status = 'active' AND expires_at < NOW()
        RETURNING id
    """)
    
    expired = cursor.fetchall()
    conn.commit()
    cursor.close()
    
    return len(expired)

# ============================================================================
# API Endpoints - Fulfillment Engine
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "fulfillment_agent",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/fulfillment/analyze")
async def analyze_order_fulfillment(request: FulfillmentAnalysisRequest):
    """
    Analyze order and determine optimal fulfillment strategy
    Returns warehouse selection, split recommendations, and cost estimates
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get all active warehouses
        cursor.execute("SELECT DISTINCT warehouse_id FROM inventory WHERE quantity_available > 0")
        warehouses = cursor.fetchall()
        
        if not warehouses:
            raise HTTPException(status_code=404, detail="No warehouses available")
        
        # Score each warehouse
        warehouse_scores = []
        for wh in warehouses:
            score_data = calculate_warehouse_score(
                wh['warehouse_id'], 
                request.items, 
                request.shipping_address,
                conn
            )
            warehouse_scores.append(score_data)
        
        # Sort by score descending
        warehouse_scores.sort(key=lambda x: x['score'], reverse=True)
        best_warehouse = warehouse_scores[0]
        
        # Determine fulfillment strategy
        if best_warehouse['can_fulfill']:
            strategy = "single_warehouse"
            split_required = False
            backorder_required = False
        else:
            # Check if any combination can fulfill
            # For MVP, we'll create backorder for unavailable items
            strategy = "backorder_partial"
            split_required = False
            backorder_required = True
        
        # Create fulfillment plan
        cursor.execute("""
            INSERT INTO fulfillment_plans 
            (order_id, fulfillment_strategy, primary_warehouse_id, 
             estimated_ship_date, total_shipping_cost, split_required, 
             backorder_required, priority_level, analysis_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            request.order_id,
            strategy,
            best_warehouse['warehouse_id'],
            datetime.now() + timedelta(days=1),  # Ship tomorrow
            best_warehouse['shipping_cost'],
            split_required,
            backorder_required,
            request.priority,
            best_warehouse['score']
        ))
        
        plan_id = cursor.fetchone()['id']
        conn.commit()
        
        return {
            "success": True,
            "plan_id": plan_id,
            "strategy": strategy,
            "primary_warehouse": best_warehouse,
            "alternative_warehouses": warehouse_scores[1:3],  # Top 3
            "split_required": split_required,
            "backorder_required": backorder_required,
            "estimated_ship_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "total_cost": best_warehouse['shipping_cost']
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/api/fulfillment/allocate")
async def allocate_inventory(request: FulfillmentAnalysisRequest):
    """
    Allocate inventory and create reservations for an order
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First analyze to get best warehouse
        cursor.execute("""
            SELECT primary_warehouse_id, fulfillment_strategy
            FROM fulfillment_plans
            WHERE order_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (request.order_id,))
        
        plan = cursor.fetchone()
        
        if not plan:
            raise HTTPException(status_code=404, detail="No fulfillment plan found. Run analysis first.")
        
        warehouse_id = plan['primary_warehouse_id']
        reservations_created = []
        backorders_created = []
        
        # Create reservations for available items
        for item in request.items:
            # Check availability
            cursor.execute("""
                SELECT quantity_available 
                FROM inventory 
                WHERE product_id = %s AND warehouse_id = %s
            """, (item.product_id, warehouse_id))
            
            inv = cursor.fetchone()
            
            if inv and inv['quantity_available'] >= item.quantity:
                # Create reservation
                reservation_id = create_inventory_reservation(
                    request.order_id,
                    item.product_id,
                    item.sku,
                    warehouse_id,
                    item.quantity,
                    "hard",  # Hard reservation for allocated orders
                    1440,  # 24 hours
                    conn
                )
                
                # Update inventory
                cursor.execute("""
                    UPDATE inventory 
                    SET quantity_reserved = quantity_reserved + %s,
                        quantity_available = quantity_available - %s
                    WHERE product_id = %s AND warehouse_id = %s
                """, (item.quantity, item.quantity, item.product_id, warehouse_id))
                
                reservations_created.append({
                    "reservation_id": reservation_id,
                    "product_id": item.product_id,
                    "sku": item.sku,
                    "quantity": item.quantity
                })
            else:
                # Create backorder
                cursor.execute("""
                    INSERT INTO backorders 
                    (order_id, product_id, sku, customer_id, quantity_backordered, priority_score)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (request.order_id, item.product_id, item.sku, request.customer_id, item.quantity, 50))
                
                backorder_id = cursor.fetchone()['id']
                backorders_created.append({
                    "backorder_id": backorder_id,
                    "product_id": item.product_id,
                    "sku": item.sku,
                    "quantity": item.quantity
                })
        
        conn.commit()
        
        return {
            "success": True,
            "order_id": request.order_id,
            "warehouse_id": warehouse_id,
            "reservations": reservations_created,
            "backorders": backorders_created,
            "message": f"Allocated {len(reservations_created)} items, {len(backorders_created)} backordered"
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/fulfillment/orders/{order_id}")
async def get_fulfillment_plan(order_id: int):
    """Get fulfillment plan for an order"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT * FROM fulfillment_plans
            WHERE order_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (order_id,))
        
        plan = cursor.fetchone()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Fulfillment plan not found")
        
        # Get reservations
        cursor.execute("""
            SELECT * FROM inventory_reservations
            WHERE order_id = %s AND status = 'active'
        """, (order_id,))
        
        reservations = cursor.fetchall()
        
        # Get backorders
        cursor.execute("""
            SELECT * FROM backorders
            WHERE order_id = %s AND status = 'pending'
        """, (order_id,))
        
        backorders = cursor.fetchall()
        
        return {
            "success": True,
            "plan": dict(plan),
            "reservations": [dict(r) for r in reservations],
            "backorders": [dict(b) for b in backorders]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# API Endpoints - Inventory Reservations
# ============================================================================

@app.post("/api/reservations")
async def create_reservation(reservation: ReservationCreate):
    """Create inventory reservation"""
    conn = get_db_connection()
    
    try:
        reservation_id = create_inventory_reservation(
            reservation.order_id,
            reservation.product_id,
            reservation.sku,
            reservation.warehouse_id,
            reservation.quantity,
            reservation.reservation_type,
            reservation.expires_in_minutes,
            conn
        )
        
        return {
            "success": True,
            "reservation_id": reservation_id,
            "expires_in_minutes": reservation.expires_in_minutes,
            "message": "Reservation created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/reservations")
async def list_reservations(
    status: Optional[str] = None,
    order_id: Optional[int] = None,
    limit: int = 50
):
    """List inventory reservations"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = "SELECT * FROM inventory_reservations WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        if order_id:
            query += " AND order_id = %s"
            params.append(order_id)
        
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        reservations = cursor.fetchall()
        
        return {
            "success": True,
            "reservations": [dict(r) for r in reservations],
            "total": len(reservations)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.put("/api/reservations/{reservation_id}/release")
async def release_reservation(reservation_id: int):
    """Release an inventory reservation"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get reservation details
        cursor.execute("""
            SELECT product_id, warehouse_id, quantity
            FROM inventory_reservations
            WHERE id = %s AND status = 'active'
        """, (reservation_id,))
        
        reservation = cursor.fetchone()
        
        if not reservation:
            raise HTTPException(status_code=404, detail="Active reservation not found")
        
        # Release reservation
        cursor.execute("""
            UPDATE inventory_reservations
            SET status = 'released', released_at = NOW()
            WHERE id = %s
        """, (reservation_id,))
        
        # Update inventory
        cursor.execute("""
            UPDATE inventory
            SET quantity_reserved = quantity_reserved - %s,
                quantity_available = quantity_available + %s
            WHERE product_id = %s AND warehouse_id = %s
        """, (reservation['quantity'], reservation['quantity'], 
              reservation['product_id'], reservation['warehouse_id']))
        
        conn.commit()
        
        return {
            "success": True,
            "reservation_id": reservation_id,
            "message": "Reservation released successfully"
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/reservations/expired")
async def get_expired_reservations():
    """Get and release expired reservations"""
    conn = get_db_connection()
    
    try:
        released_count = release_expired_reservations(conn)
        
        return {
            "success": True,
            "expired_count": released_count,
            "message": f"Released {released_count} expired reservations"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ============================================================================
# API Endpoints - Backorders
# ============================================================================

@app.post("/api/backorders")
async def create_backorder(backorder: BackorderCreate):
    """Create a backorder"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO backorders 
            (order_id, product_id, sku, customer_id, quantity_backordered, priority_score)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (backorder.order_id, backorder.product_id, backorder.sku, 
              backorder.customer_id, backorder.quantity, backorder.priority_score))
        
        backorder_id = cursor.fetchone()['id']
        conn.commit()
        
        return {
            "success": True,
            "backorder_id": backorder_id,
            "message": "Backorder created successfully"
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/backorders")
async def list_backorders(
    status: Optional[str] = None,
    limit: int = 50
):
    """List backorders with priority"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = "SELECT * FROM backorders WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        query += " ORDER BY priority_score DESC, created_at ASC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        backorders = cursor.fetchall()
        
        return {
            "success": True,
            "backorders": [dict(b) for b in backorders],
            "total": len(backorders)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/backorders/metrics")
async def get_backorder_metrics():
    """Get backorder performance metrics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                COUNT(*) as total_backorders,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                COUNT(CASE WHEN status = 'fulfilled' THEN 1 END) as fulfilled,
                AVG(CASE WHEN fulfilled_at IS NOT NULL 
                    THEN EXTRACT(EPOCH FROM (fulfilled_at - created_at))/3600 
                END) as avg_fulfillment_hours
            FROM backorders
            WHERE created_at >= NOW() - INTERVAL '30 days'
        """)
        
        metrics = cursor.fetchone()
        
        return {
            "success": True,
            "metrics": dict(metrics)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# API Endpoints - Warehouse Management
# ============================================================================

@app.get("/api/warehouses/capacity")
async def get_warehouse_capacity(warehouse_id: Optional[int] = None):
    """Get warehouse capacity status"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT * FROM warehouse_capacity
            WHERE date = CURRENT_DATE
        """
        params = []
        
        if warehouse_id:
            query += " AND warehouse_id = %s"
            params.append(warehouse_id)
        
        cursor.execute(query, params)
        capacity = cursor.fetchall()
        
        return {
            "success": True,
            "capacity": [dict(c) for c in capacity]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8033)
