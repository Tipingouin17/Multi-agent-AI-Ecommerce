"""
RMA (Return Merchandise Authorization) Workflow Agent v3
Handles complete return management from request to refund
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, date
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json

app = FastAPI(title="RMA Workflow Agent", version="3.0.0")

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

class RMARequestCreate(BaseModel):
    order_id: int
    customer_id: int
    return_reason: str
    return_reason_details: Optional[str] = None
    items: List[dict]  # [{product_id, quantity, condition}]

class RMAApproval(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None

class InspectionRecord(BaseModel):
    rma_item_id: int
    condition_assessment: str
    packaging_condition: Optional[str] = None
    inspection_notes: Optional[str] = None
    passed_inspection: bool = True

class RefundRequest(BaseModel):
    refund_method: str  # original_payment, store_credit, exchange
    restocking_fees: Optional[float] = 0
    return_shipping_cost: Optional[float] = 0

# ============================================================================
# Helper Functions
# ============================================================================

def generate_rma_number() -> str:
    """Generate unique RMA number"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"RMA{timestamp}"

def calculate_refund(rma_items: list, restocking_fees: float = 0, shipping_cost: float = 0) -> dict:
    """Calculate total refund amount"""
    subtotal = sum(item['refund_amount'] for item in rma_items)
    total = subtotal - restocking_fees - shipping_cost
    
    return {
        "subtotal": round(subtotal, 2),
        "restocking_fees": round(restocking_fees, 2),
        "return_shipping_cost": round(shipping_cost, 2),
        "total_refund_amount": round(max(total, 0), 2)
    }

def check_return_eligibility(order_id: int, days_since_delivery: int = 30) -> dict:
    """Check if return is eligible"""
    # Simplified eligibility check
    # In production, would check order date, product category, etc.
    
    return {
        "is_eligible": days_since_delivery <= 30,
        "eligibility_notes": f"Return window: 30 days. Days since delivery: {days_since_delivery}"
    }

# ============================================================================
# API Endpoints - Return Requests
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "rma_agent",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/rma/requests")
async def create_rma_request(request: RMARequestCreate):
    """Create new RMA request"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Generate RMA number
        rma_number = generate_rma_number()
        
        # Check eligibility (simplified)
        eligibility = check_return_eligibility(request.order_id)
        
        # Create RMA request
        cursor.execute("""
            INSERT INTO rma_requests
            (rma_number, order_id, customer_id, status, return_reason,
             return_reason_details, is_eligible, eligibility_notes)
            VALUES (%s, %s, %s, 'requested', %s, %s, %s, %s)
            RETURNING id
        """, (rma_number, request.order_id, request.customer_id,
              request.return_reason, request.return_reason_details,
              eligibility['is_eligible'], eligibility['eligibility_notes']))
        
        rma_id = cursor.fetchone()['id']
        
        # Add RMA items
        for item in request.items:
            cursor.execute("""
                INSERT INTO rma_items
                (rma_id, order_item_id, product_id, product_sku, product_name,
                 quantity_requested, unit_price, condition_requested)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (rma_id, item.get('order_item_id', 0), item['product_id'],
                  item.get('sku', ''), item.get('name', ''),
                  item['quantity'], item.get('price', 0),
                  item.get('condition', 'opened')))
        
        # Create communication record
        cursor.execute("""
            INSERT INTO rma_communications
            (rma_id, communication_type, direction, subject, message)
            VALUES (%s, 'email', 'outbound', 'Return Request Received',
                    'Your return request has been received and is being reviewed.')
        """, (rma_id,))
        
        conn.commit()
        
        return {
            "success": True,
            "rma_id": rma_id,
            "rma_number": rma_number,
            "status": "requested",
            "is_eligible": eligibility['is_eligible'],
            "message": "Return request created successfully"
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/rma/requests")
async def list_rma_requests(
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    limit: int = 50
):
    """List RMA requests"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = "SELECT * FROM rma_requests WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        if customer_id:
            query += " AND customer_id = %s"
            params.append(customer_id)
        
        query += " ORDER BY requested_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        requests = cursor.fetchall()
        
        return {
            "success": True,
            "requests": [dict(r) for r in requests],
            "total": len(requests)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/rma/requests/{rma_id}")
async def get_rma_details(rma_id: int):
    """Get RMA request details"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get RMA request
        cursor.execute("SELECT * FROM rma_requests WHERE id = %s", (rma_id,))
        rma = cursor.fetchone()
        
        if not rma:
            raise HTTPException(status_code=404, detail="RMA not found")
        
        # Get items
        cursor.execute("SELECT * FROM rma_items WHERE rma_id = %s", (rma_id,))
        items = cursor.fetchall()
        
        # Get inspections
        cursor.execute("SELECT * FROM rma_inspections WHERE rma_id = %s", (rma_id,))
        inspections = cursor.fetchall()
        
        # Get refund
        cursor.execute("SELECT * FROM rma_refunds WHERE rma_id = %s", (rma_id,))
        refund = cursor.fetchone()
        
        # Get shipping
        cursor.execute("SELECT * FROM rma_shipping WHERE rma_id = %s", (rma_id,))
        shipping = cursor.fetchone()
        
        return {
            "success": True,
            "rma": dict(rma),
            "items": [dict(i) for i in items],
            "inspections": [dict(i) for i in inspections],
            "refund": dict(refund) if refund else None,
            "shipping": dict(shipping) if shipping else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/api/rma/requests/{rma_id}/approve")
async def approve_rma(rma_id: int, approval: RMAApproval):
    """Approve or reject RMA request"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if approval.approved:
            # Approve RMA
            cursor.execute("""
                UPDATE rma_requests
                SET status = 'approved',
                    approved_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s
            """, (rma_id,))
            
            # Create communication
            cursor.execute("""
                INSERT INTO rma_communications
                (rma_id, communication_type, direction, subject, message)
                VALUES (%s, 'email', 'outbound', 'Return Approved',
                        'Your return has been approved. Return label will be sent shortly.')
            """, (rma_id,))
            
            message = "RMA approved successfully"
            
        else:
            # Reject RMA
            cursor.execute("""
                UPDATE rma_requests
                SET status = 'rejected',
                    rejected_at = NOW(),
                    rejection_reason = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (approval.rejection_reason, rma_id))
            
            # Create communication
            cursor.execute("""
                INSERT INTO rma_communications
                (rma_id, communication_type, direction, subject, message)
                VALUES (%s, 'email', 'outbound', 'Return Not Approved',
                        %s)
            """, (rma_id, approval.rejection_reason))
            
            message = "RMA rejected"
        
        conn.commit()
        
        return {
            "success": True,
            "message": message
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# API Endpoints - Shipping & Receiving
# ============================================================================

@app.post("/api/rma/{rma_id}/shipping-label")
async def generate_return_label(rma_id: int):
    """Generate return shipping label"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get RMA details
        cursor.execute("SELECT * FROM rma_requests WHERE id = %s", (rma_id,))
        rma = cursor.fetchone()
        
        if not rma:
            raise HTTPException(status_code=404, detail="RMA not found")
        
        # Generate tracking number (simulated)
        tracking_number = f"RTN{datetime.now().strftime('%Y%m%d%H%M%S')}{rma_id}"
        
        # Create shipping record
        cursor.execute("""
            INSERT INTO rma_shipping
            (rma_id, tracking_number, label_cost, estimated_arrival)
            VALUES (%s, %s, 0, %s)
            RETURNING id
        """, (rma_id, tracking_number, date.today() + timedelta(days=5)))
        
        shipping_id = cursor.fetchone()['id']
        
        # Update RMA status
        cursor.execute("""
            UPDATE rma_requests
            SET status = 'label_sent',
                updated_at = NOW()
            WHERE id = %s
        """, (rma_id,))
        
        # Create communication
        cursor.execute("""
            INSERT INTO rma_communications
            (rma_id, communication_type, direction, subject, message)
            VALUES (%s, 'email', 'outbound', 'Return Label Ready',
                    'Your return shipping label is ready. Tracking: ' || %s)
        """, (rma_id, tracking_number))
        
        conn.commit()
        
        return {
            "success": True,
            "shipping_id": shipping_id,
            "tracking_number": tracking_number,
            "message": "Return label generated successfully"
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/api/rma/{rma_id}/receive")
async def receive_return(rma_id: int):
    """Mark return as received"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE rma_requests
            SET status = 'received',
                received_at = NOW(),
                updated_at = NOW()
            WHERE id = %s
        """, (rma_id,))
        
        # Update shipping
        cursor.execute("""
            UPDATE rma_shipping
            SET actual_arrival = NOW()
            WHERE rma_id = %s
        """, (rma_id,))
        
        # Create communication
        cursor.execute("""
            INSERT INTO rma_communications
            (rma_id, communication_type, direction, subject, message)
            VALUES (%s, 'email', 'outbound', 'Return Received',
                    'We have received your return and will inspect it shortly.')
        """, (rma_id,))
        
        conn.commit()
        
        return {
            "success": True,
            "message": "Return marked as received"
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# API Endpoints - Inspection
# ============================================================================

@app.post("/api/rma/{rma_id}/inspect")
async def record_inspection(rma_id: int, inspection: InspectionRecord):
    """Record inspection results"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create inspection record
        cursor.execute("""
            INSERT INTO rma_inspections
            (rma_id, rma_item_id, condition_assessment, packaging_condition,
             inspection_notes, passed_inspection)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (rma_id, inspection.rma_item_id, inspection.condition_assessment,
              inspection.packaging_condition, inspection.inspection_notes,
              inspection.passed_inspection))
        
        inspection_id = cursor.fetchone()['id']
        
        # Update item condition
        cursor.execute("""
            UPDATE rma_items
            SET condition_actual = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (inspection.condition_assessment, inspection.rma_item_id))
        
        # Update RMA status
        cursor.execute("""
            UPDATE rma_requests
            SET status = 'inspected',
                inspected_at = NOW(),
                updated_at = NOW()
            WHERE id = %s
        """, (rma_id,))
        
        conn.commit()
        
        return {
            "success": True,
            "inspection_id": inspection_id,
            "message": "Inspection recorded successfully"
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# API Endpoints - Refunds
# ============================================================================

@app.post("/api/rma/{rma_id}/calculate-refund")
async def calculate_refund_amount(rma_id: int):
    """Calculate refund amount"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get RMA items
        cursor.execute("""
            SELECT * FROM rma_items WHERE rma_id = %s
        """, (rma_id,))
        
        items = cursor.fetchall()
        
        # Calculate refund for each item
        total_refund = 0
        for item in items:
            item_refund = float(item['unit_price']) * item['quantity_received']
            
            # Apply restocking fee if applicable
            if item['restocking_fee_percent'] > 0:
                restocking_fee = item_refund * (float(item['restocking_fee_percent']) / 100)
                item_refund -= restocking_fee
            
            total_refund += item_refund
            
            # Update item refund amount
            cursor.execute("""
                UPDATE rma_items
                SET refund_amount = %s
                WHERE id = %s
            """, (item_refund, item['id']))
        
        conn.commit()
        
        return {
            "success": True,
            "total_refund_amount": round(total_refund, 2),
            "items": [dict(i) for i in items]
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/api/rma/{rma_id}/process-refund")
async def process_refund(rma_id: int, refund_request: RefundRequest):
    """Process refund"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get items for refund calculation
        cursor.execute("""
            SELECT SUM(refund_amount) as subtotal FROM rma_items WHERE rma_id = %s
        """, (rma_id,))
        
        result = cursor.fetchone()
        subtotal = float(result['subtotal']) if result['subtotal'] else 0
        
        # Calculate total refund
        refund_calc = calculate_refund(
            [{"refund_amount": subtotal}],
            refund_request.restocking_fees,
            refund_request.return_shipping_cost
        )
        
        # Create refund record
        cursor.execute("""
            INSERT INTO rma_refunds
            (rma_id, refund_method, subtotal, restocking_fees, return_shipping_cost,
             total_refund_amount, refund_status)
            VALUES (%s, %s, %s, %s, %s, %s, 'processing')
            RETURNING id
        """, (rma_id, refund_request.refund_method, refund_calc['subtotal'],
              refund_calc['restocking_fees'], refund_calc['return_shipping_cost'],
              refund_calc['total_refund_amount']))
        
        refund_id = cursor.fetchone()['id']
        
        # Update RMA status
        cursor.execute("""
            UPDATE rma_requests
            SET status = 'refund_pending',
                updated_at = NOW()
            WHERE id = %s
        """, (rma_id,))
        
        # Simulate refund processing (in production, would call payment gateway)
        cursor.execute("""
            UPDATE rma_refunds
            SET refund_status = 'completed',
                processed_at = NOW()
            WHERE id = %s
        """, (refund_id,))
        
        cursor.execute("""
            UPDATE rma_requests
            SET status = 'refund_processed',
                updated_at = NOW()
            WHERE id = %s
        """, (rma_id,))
        
        # Create communication
        cursor.execute("""
            INSERT INTO rma_communications
            (rma_id, communication_type, direction, subject, message)
            VALUES (%s, 'email', 'outbound', 'Refund Processed',
                    'Your refund of $' || %s || ' has been processed.')
        """, (rma_id, refund_calc['total_refund_amount']))
        
        conn.commit()
        
        return {
            "success": True,
            "refund_id": refund_id,
            "refund_amount": refund_calc['total_refund_amount'],
            "message": "Refund processed successfully"
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# API Endpoints - Analytics
# ============================================================================

@app.get("/api/rma/metrics")
async def get_rma_metrics():
    """Get RMA metrics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Total requests
        cursor.execute("SELECT COUNT(*) as total FROM rma_requests")
        total = cursor.fetchone()['total']
        
        # By status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM rma_requests
            GROUP BY status
        """)
        status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Total refund amount
        cursor.execute("""
            SELECT SUM(total_refund_amount) as total_refunds
            FROM rma_refunds
            WHERE refund_status = 'completed'
        """)
        result = cursor.fetchone()
        total_refunds = float(result['total_refunds']) if result['total_refunds'] else 0
        
        # Average processing time (days)
        cursor.execute("""
            SELECT AVG(EXTRACT(EPOCH FROM (completed_at - requested_at)) / 86400) as avg_days
            FROM rma_requests
            WHERE completed_at IS NOT NULL
        """)
        result = cursor.fetchone()
        avg_days = float(result['avg_days']) if result['avg_days'] else 0
        
        return {
            "success": True,
            "metrics": {
                "total_requests": total,
                "status_distribution": status_counts,
                "total_refunds": round(total_refunds, 2),
                "average_processing_days": round(avg_days, 1)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8035)
