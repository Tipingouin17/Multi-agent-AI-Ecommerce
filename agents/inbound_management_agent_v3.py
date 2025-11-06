"""
Inbound Management Agent v3
Handles receiving, quality control, putaway, and discrepancy resolution
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Inbound Management Agent", version="3.0.0")

# CORS
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
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

# ============================================================================
# Pydantic Models
# ============================================================================

class InboundShipmentCreate(BaseModel):
    po_id: Optional[int] = None
    vendor_id: int
    expected_arrival_date: Optional[str] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    warehouse_id: Optional[int] = None
    dock_door: Optional[str] = None
    notes: Optional[str] = None
    items: List[Dict]  # [{"product_id": 1, "sku": "SKU001", "expected_quantity": 100, "unit_cost": 10.50}]

class InboundShipmentUpdate(BaseModel):
    status: Optional[str] = None
    actual_arrival_date: Optional[str] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    dock_door: Optional[str] = None
    notes: Optional[str] = None

class ReceiveItemRequest(BaseModel):
    shipment_item_id: int
    received_quantity: int
    accepted_quantity: int
    rejected_quantity: int
    notes: Optional[str] = None

class QualityInspectionCreate(BaseModel):
    shipment_item_id: int
    inspection_type: str  # random, full, sample
    sample_size: Optional[int] = None
    inspector_id: Optional[str] = None
    notes: Optional[str] = None

class QualityInspectionUpdate(BaseModel):
    passed_count: int
    failed_count: int
    status: str  # passed, failed, partial
    defect_types: Optional[List[str]] = None
    photos: Optional[List[str]] = None
    notes: Optional[str] = None

class QualityDefectCreate(BaseModel):
    inspection_id: int
    defect_type: str  # damaged, wrong_item, expired, missing_parts
    severity: str  # minor, major, critical
    quantity: int
    description: Optional[str] = None
    action_taken: Optional[str] = None  # reject, accept_with_discount, return_to_vendor
    photos: Optional[List[str]] = None

class PutawayTaskUpdate(BaseModel):
    status: str  # in_progress, completed, cancelled
    assigned_to: Optional[str] = None
    to_location: Optional[str] = None
    notes: Optional[str] = None

class DiscrepancyResolve(BaseModel):
    resolution_status: str  # investigating, resolved, closed
    resolution_notes: str
    resolved_by: str

# ============================================================================
# Helper Functions
# ============================================================================

def generate_shipment_number() -> str:
    """Generate unique shipment number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"ASN-{timestamp}"

def generate_task_number(prefix: str) -> str:
    """Generate unique task number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}-{timestamp}"

def generate_inspection_number() -> str:
    """Generate unique inspection number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"QC-{timestamp}"

def auto_generate_putaway_tasks(shipment_item_id: int, product_id: int, sku: str, 
                                quantity: int, warehouse_id: int = None):
    """Automatically generate putaway tasks after receiving"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Generate putaway task
        task_number = generate_task_number("PUT")
        from_location = f"DOCK-{warehouse_id or 1}"
        to_location = f"SHELF-{product_id % 100:03d}"  # Simple location assignment
        
        query = """
            INSERT INTO putaway_tasks 
            (shipment_item_id, task_number, product_id, sku, quantity, 
             from_location, to_location, status, priority)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        cursor.execute(query, (
            shipment_item_id, task_number, product_id, sku, quantity,
            from_location, to_location, 'pending', 'medium'
        ))
        task_id = cursor.fetchone()[0]
        conn.commit()
        
        return task_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def update_inventory_from_putaway(product_id: int, quantity: int, location: str):
    """Update inventory when putaway is completed"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update or create inventory record
        query = """
            INSERT INTO inventory (product_id, warehouse_id, quantity, location, last_updated)
            VALUES (%s, 1, %s, %s, NOW())
            ON CONFLICT (product_id, warehouse_id) 
            DO UPDATE SET
                quantity = inventory.quantity + EXCLUDED.quantity,
                location = EXCLUDED.location,
                last_updated = NOW()
        """
        cursor.execute(query, (product_id, quantity, location))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def calculate_inbound_metrics(date: str = None, warehouse_id: int = None):
    """Calculate and store inbound performance metrics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        target_date = date or datetime.now().strftime("%Y-%m-%d")
        
        # Calculate metrics
        metrics_query = """
            WITH daily_stats AS (
                SELECT 
                    COUNT(DISTINCT s.id) as shipments_received,
                    SUM(si.received_quantity) as items_received,
                    SUM(si.accepted_quantity) as items_accepted,
                    SUM(si.rejected_quantity) as items_rejected
                FROM inbound_shipments s
                JOIN inbound_shipment_items si ON s.id = si.shipment_id
                WHERE DATE(s.actual_arrival_date) = %s
                AND s.status IN ('receiving', 'completed')
            ),
            discrepancy_stats AS (
                SELECT COUNT(*) as discrepancy_count
                FROM receiving_discrepancies
                WHERE DATE(created_at) = %s
            ),
            quality_stats AS (
                SELECT 
                    COUNT(CASE WHEN status = 'passed' THEN 1 END) as passed,
                    COUNT(*) as total
                FROM quality_inspections
                WHERE DATE(completed_at) = %s
            )
            SELECT 
                ds.shipments_received,
                ds.items_received,
                ds.items_accepted,
                ds.items_rejected,
                CASE WHEN ds.items_received > 0 
                    THEN (disc.discrepancy_count::DECIMAL / ds.items_received * 100)
                    ELSE 0 END as discrepancy_rate,
                CASE WHEN qs.total > 0 
                    THEN (qs.passed::DECIMAL / qs.total * 100)
                    ELSE 100 END as quality_pass_rate
            FROM daily_stats ds
            CROSS JOIN discrepancy_stats disc
            CROSS JOIN quality_stats qs
        """
        cursor.execute(metrics_query, (target_date, target_date, target_date))
        result = cursor.fetchone()
        
        if result:
            # Insert or update metrics
            insert_query = """
                INSERT INTO inbound_metrics 
                (date, warehouse_id, shipments_received, items_received, items_accepted,
                 items_rejected, discrepancy_rate, quality_pass_rate)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (date, warehouse_id) 
                DO UPDATE SET
                    shipments_received = EXCLUDED.shipments_received,
                    items_received = EXCLUDED.items_received,
                    items_accepted = EXCLUDED.items_accepted,
                    items_rejected = EXCLUDED.items_rejected,
                    discrepancy_rate = EXCLUDED.discrepancy_rate,
                    quality_pass_rate = EXCLUDED.quality_pass_rate,
                    created_at = NOW()
            """
            cursor.execute(insert_query, (
                target_date, warehouse_id or 1,
                result['shipments_received'] or 0, result['items_received'] or 0, result['items_accepted'] or 0,
                result['items_rejected'] or 0, result['discrepancy_rate'] or 0, result['quality_pass_rate'] or 100
            ))
            conn.commit()
            
        return result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# API Endpoints - Inbound Shipments
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "inbound_management_agent",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/inbound/shipments")
async def create_inbound_shipment(shipment: InboundShipmentCreate):
    """Create a new inbound shipment (ASN)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Generate shipment number
        shipment_number = generate_shipment_number()
        
        # Create shipment
        query = """
            INSERT INTO inbound_shipments 
            (shipment_number, po_id, vendor_id, expected_arrival_date, carrier,
             tracking_number, warehouse_id, dock_door, notes, total_items, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'expected')
            RETURNING id, shipment_number, created_at
        """
        cursor.execute(query, (
            shipment_number, shipment.po_id, shipment.vendor_id,
            shipment.expected_arrival_date, shipment.carrier,
            shipment.tracking_number, shipment.warehouse_id,
            shipment.dock_door, shipment.notes, len(shipment.items)
        ))
        result = cursor.fetchone()
        shipment_id = result['id']
        
        # Create shipment items
        for item in shipment.items:
            item_query = """
                INSERT INTO inbound_shipment_items 
                (shipment_id, product_id, sku, expected_quantity, unit_cost, status)
                VALUES (%s, %s, %s, %s, %s, 'pending')
            """
            cursor.execute(item_query, (
                shipment_id, item['product_id'], item['sku'],
                item['expected_quantity'], item.get('unit_cost', 0)
            ))
        
        conn.commit()
        
        return {
            "success": True,
            "shipment_id": shipment_id,
            "shipment_number": shipment_number,
            "message": "Inbound shipment created successfully"
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/inbound/shipments")
async def get_inbound_shipments(
    status: Optional[str] = None,
    warehouse_id: Optional[int] = None,
    limit: int = Query(50, le=200),
    offset: int = 0
):
    """Get list of inbound shipments with filters"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Build query with filters
        where_clauses = []
        params = []
        
        if status:
            where_clauses.append("s.status = %s")
            params.append(status)
        
        if warehouse_id:
            where_clauses.append("s.warehouse_id = %s")
            params.append(warehouse_id)
        
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        query = f"""
            SELECT 
                s.id, s.shipment_number, s.po_id, s.vendor_id,
                s.expected_arrival_date, s.actual_arrival_date, s.status,
                s.carrier, s.tracking_number, s.total_items, s.received_items,
                s.warehouse_id, s.dock_door, s.notes, s.created_at, s.updated_at,
                COUNT(si.id) as item_count,
                SUM(si.expected_quantity) as total_expected_qty,
                SUM(si.received_quantity) as total_received_qty
            FROM inbound_shipments s
            LEFT JOIN inbound_shipment_items si ON s.id = si.shipment_id
            {where_sql}
            GROUP BY s.id
            ORDER BY s.created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        shipments = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM inbound_shipments s {where_sql}"
        cursor.execute(count_query, params[:-2])  # Exclude limit and offset
        count_result = cursor.fetchone()
        total_count = count_result['count'] if count_result else 0
        
        return {
            "success": True,
            "shipments": shipments,
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/inbound/shipments/{shipment_id}")
async def get_inbound_shipment(shipment_id: int):
    """Get detailed information about a specific shipment"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get shipment details
        query = """
            SELECT 
                s.id, s.shipment_number, s.po_id, s.vendor_id,
                s.expected_arrival_date, s.actual_arrival_date, s.status,
                s.carrier, s.tracking_number, s.total_items, s.received_items,
                s.warehouse_id, s.dock_door, s.notes, s.created_at, s.updated_at
            FROM inbound_shipments s
            WHERE s.id = %s
        """
        cursor.execute(query, (shipment_id,))
        shipment = cursor.fetchone()
        
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")
        
        columns = [desc[0] for desc in cursor.description]
        shipment_dict = dict(zip(columns, shipment))
        
        # Get shipment items
        items_query = """
            SELECT 
                si.id, si.product_id, si.sku, si.expected_quantity,
                si.received_quantity, si.accepted_quantity, si.rejected_quantity,
                si.unit_cost, si.status, si.created_at, si.updated_at,
                p.name as product_name
            FROM inbound_shipment_items si
            LEFT JOIN products p ON si.product_id = p.id
            WHERE si.shipment_id = %s
        """
        cursor.execute(items_query, (shipment_id,))
        items_columns = [desc[0] for desc in cursor.description]
        items = [dict(zip(items_columns, row)) for row in cursor.fetchall()]
        
        shipment_dict['items'] = items
        
        return {
            "success": True,
            "shipment": shipment_dict
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.put("/api/inbound/shipments/{shipment_id}")
async def update_inbound_shipment(shipment_id: int, update: InboundShipmentUpdate):
    """Update inbound shipment details"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Build update query dynamically
        update_fields = []
        params = []
        
        if update.status:
            update_fields.append("status = %s")
            params.append(update.status)
        
        if update.actual_arrival_date:
            update_fields.append("actual_arrival_date = %s")
            params.append(update.actual_arrival_date)
        
        if update.carrier:
            update_fields.append("carrier = %s")
            params.append(update.carrier)
        
        if update.tracking_number:
            update_fields.append("tracking_number = %s")
            params.append(update.tracking_number)
        
        if update.dock_door:
            update_fields.append("dock_door = %s")
            params.append(update.dock_door)
        
        if update.notes:
            update_fields.append("notes = %s")
            params.append(update.notes)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_fields.append("updated_at = NOW()")
        params.append(shipment_id)
        
        query = f"""
            UPDATE inbound_shipments 
            SET {', '.join(update_fields)}
            WHERE id = %s
            RETURNING id, shipment_number, status
        """
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Shipment not found")
        
        conn.commit()
        
        return {
            "success": True,
            "shipment_id": result['id'],
            "shipment_number": result['shipment_number'],
            "status": result['status'],
            "message": "Shipment updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# API Endpoints - Receiving Workflow
# ============================================================================

@app.post("/api/inbound/shipments/{shipment_id}/receive")
async def start_receiving(shipment_id: int):
    """Start receiving process for a shipment"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update shipment status
        update_query = """
            UPDATE inbound_shipments 
            SET status = 'receiving', actual_arrival_date = NOW(), updated_at = NOW()
            WHERE id = %s AND status IN ('expected', 'in_transit', 'arrived')
            RETURNING id, shipment_number
        """
        cursor.execute(update_query, (shipment_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=400, detail="Shipment cannot be received in current status")
        
        # Create receiving task
        task_number = generate_task_number("RCV")
        task_query = """
            INSERT INTO receiving_tasks 
            (shipment_id, task_number, status, priority, started_at)
            VALUES (%s, %s, 'in_progress', 'high', NOW())
            RETURNING id, task_number
        """
        cursor.execute(task_query, (shipment_id, task_number))
        task_result = cursor.fetchone()
        
        conn.commit()
        
        return {
            "success": True,
            "shipment_id": result['id'],
            "shipment_number": result['shipment_number'],
            "task_id": task_result['id'],
            "task_number": task_result['task_number'],
            "message": "Receiving started successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/api/inbound/receive-item")
async def receive_item(receive: ReceiveItemRequest):
    """Record received quantities for a shipment item"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update shipment item
        update_query = """
            UPDATE inbound_shipment_items 
            SET 
                received_quantity = %s,
                accepted_quantity = %s,
                rejected_quantity = %s,
                status = CASE 
                    WHEN %s = expected_quantity THEN 'completed'
                    WHEN %s > 0 THEN 'discrepancy'
                    ELSE 'receiving'
                END,
                updated_at = NOW()
            WHERE id = %s
            RETURNING id, shipment_id, product_id, sku, expected_quantity
        """
        cursor.execute(update_query, (
            receive.received_quantity,
            receive.accepted_quantity,
            receive.rejected_quantity,
            receive.received_quantity,
            abs(receive.received_quantity - receive.accepted_quantity),
            receive.shipment_item_id
        ))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Shipment item not found")
        
        item_id = result['id']
        shipment_id = result['shipment_id']
        product_id = result['product_id']
        sku = result['sku']
        expected_quantity = result['expected_quantity']
        
        # Check for discrepancies
        if receive.received_quantity != expected_quantity or receive.rejected_quantity > 0:
            # Create discrepancy record
            discrepancy_type = "quantity_mismatch" if receive.received_quantity != expected_quantity else "damaged"
            variance = receive.received_quantity - expected_quantity
            
            disc_query = """
                INSERT INTO receiving_discrepancies 
                (shipment_id, shipment_item_id, discrepancy_type, expected_quantity,
                 actual_quantity, variance, resolution_status, reported_by)
                VALUES (%s, %s, %s, %s, %s, %s, 'open', 'system')
            """
            cursor.execute(disc_query, (
                shipment_id, item_id, discrepancy_type,
                expected_quantity, receive.received_quantity, variance
            ))
        
        # Auto-generate putaway task if accepted quantity > 0
        if receive.accepted_quantity > 0:
            auto_generate_putaway_tasks(
                item_id, product_id, sku,
                receive.accepted_quantity, 1
            )
        
        # Update shipment received count
        count_query = """
            UPDATE inbound_shipments 
            SET received_items = (
                SELECT COUNT(*) FROM inbound_shipment_items 
                WHERE shipment_id = %s AND status = 'completed'
            ),
            status = CASE 
                WHEN (SELECT COUNT(*) FROM inbound_shipment_items WHERE shipment_id = %s AND status = 'completed') 
                     = total_items THEN 'completed'
                ELSE 'receiving'
            END,
            updated_at = NOW()
            WHERE id = %s
        """
        cursor.execute(count_query, (shipment_id, shipment_id, shipment_id))
        
        conn.commit()
        
        return {
            "success": True,
            "shipment_item_id": item_id,
            "message": "Item received successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# API Endpoints - Quality Inspections
# ============================================================================

@app.post("/api/inbound/inspections")
async def create_quality_inspection(inspection: QualityInspectionCreate):
    """Create a new quality inspection"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        inspection_number = generate_inspection_number()
        
        query = """
            INSERT INTO quality_inspections 
            (shipment_item_id, inspection_number, inspector_id, inspection_type,
             sample_size, status, started_at, notes)
            VALUES (%s, %s, %s, %s, %s, 'in_progress', NOW(), %s)
            RETURNING id, inspection_number
        """
        cursor.execute(query, (
            inspection.shipment_item_id, inspection_number,
            inspection.inspector_id, inspection.inspection_type,
            inspection.sample_size, inspection.notes
        ))
        result = cursor.fetchone()
        
        conn.commit()
        
        return {
            "success": True,
            "inspection_id": result['id'],
            "inspection_number": result['inspection_number'],
            "message": "Quality inspection created successfully"
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.put("/api/inbound/inspections/{inspection_id}")
async def update_quality_inspection(inspection_id: int, update: QualityInspectionUpdate):
    """Update quality inspection results"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            UPDATE quality_inspections 
            SET 
                passed_count = %s,
                failed_count = %s,
                status = %s,
                defect_types = %s,
                photos = %s,
                notes = %s,
                completed_at = NOW()
            WHERE id = %s
            RETURNING id, inspection_number, status
        """
        cursor.execute(query, (
            update.passed_count,
            update.failed_count,
            update.status,
            json.dumps(update.defect_types) if update.defect_types else None,
            json.dumps(update.photos) if update.photos else None,
            update.notes,
            inspection_id
        ))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Inspection not found")
        
        conn.commit()
        
        return {
            "success": True,
            "inspection_id": result['id'],
            "inspection_number": result['inspection_number'],
            "status": result['status'],
            "message": "Inspection updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/inbound/inspections")
async def get_quality_inspections(
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0
):
    """Get list of quality inspections"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        where_sql = "WHERE qi.status = %s" if status else ""
        params = [status] if status else []
        
        query = f"""
            SELECT 
                qi.id, qi.inspection_number, qi.shipment_item_id,
                qi.inspector_id, qi.inspection_type, qi.sample_size,
                qi.passed_count, qi.failed_count, qi.status,
                qi.defect_types, qi.photos, qi.notes,
                qi.started_at, qi.completed_at, qi.created_at,
                si.sku, si.product_id, s.shipment_number
            FROM quality_inspections qi
            JOIN inbound_shipment_items si ON qi.shipment_item_id = si.id
            JOIN inbound_shipments s ON si.shipment_id = s.id
            {where_sql}
            ORDER BY qi.created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        inspections = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return {
            "success": True,
            "inspections": inspections
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/api/inbound/defects")
async def create_quality_defect(defect: QualityDefectCreate):
    """Record a quality defect"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            INSERT INTO quality_defects 
            (inspection_id, defect_type, severity, quantity, description,
             action_taken, photos)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        cursor.execute(query, (
            defect.inspection_id, defect.defect_type, defect.severity,
            defect.quantity, defect.description, defect.action_taken,
            json.dumps(defect.photos) if defect.photos else None
        ))
        defect_id = cursor.fetchone()[0]
        
        conn.commit()
        
        return {
            "success": True,
            "defect_id": defect_id,
            "message": "Defect recorded successfully"
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# API Endpoints - Putaway Tasks
# ============================================================================

@app.get("/api/inbound/putaway-tasks")
async def get_putaway_tasks(
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0
):
    """Get list of putaway tasks"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        where_clauses = []
        params = []
        
        if status:
            where_clauses.append("pt.status = %s")
            params.append(status)
        
        if assigned_to:
            where_clauses.append("pt.assigned_to = %s")
            params.append(assigned_to)
        
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        query = f"""
            SELECT 
                pt.id, pt.task_number, pt.shipment_item_id, pt.product_id,
                pt.sku, pt.quantity, pt.from_location, pt.to_location,
                pt.assigned_to, pt.status, pt.priority, pt.notes,
                pt.started_at, pt.completed_at, pt.created_at, pt.updated_at,
                p.name as product_name, s.shipment_number
            FROM putaway_tasks pt
            LEFT JOIN products p ON pt.product_id = p.id
            LEFT JOIN inbound_shipment_items si ON pt.shipment_item_id = si.id
            LEFT JOIN inbound_shipments s ON si.shipment_id = s.id
            {where_sql}
            ORDER BY pt.priority DESC, pt.created_at ASC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        tasks = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return {
            "success": True,
            "tasks": tasks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.put("/api/inbound/putaway-tasks/{task_id}")
async def update_putaway_task(task_id: int, update: PutawayTaskUpdate):
    """Update putaway task status"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get task details first
        select_query = """
            SELECT product_id, quantity, to_location, status
            FROM putaway_tasks
            WHERE id = %s
        """
        cursor.execute(select_query, (task_id,))
        task = cursor.fetchone()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        product_id = task['product_id']
        quantity = task['quantity']
        current_location = task['to_location']
        current_status = task['status']
        
        # Build update query
        update_fields = ["status = %s"]
        params = [update.status]
        
        if update.assigned_to:
            update_fields.append("assigned_to = %s")
            params.append(update.assigned_to)
        
        if update.to_location:
            update_fields.append("to_location = %s")
            params.append(update.to_location)
        
        if update.notes:
            update_fields.append("notes = %s")
            params.append(update.notes)
        
        if update.status == 'in_progress':
            update_fields.append("started_at = NOW()")
        elif update.status == 'completed':
            update_fields.append("completed_at = NOW()")
        
        update_fields.append("updated_at = NOW()")
        params.append(task_id)
        
        query = f"""
            UPDATE putaway_tasks 
            SET {', '.join(update_fields)}
            WHERE id = %s
            RETURNING id, task_number, status
        """
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        # If completed, update inventory
        if update.status == 'completed' and current_status != 'completed':
            location = update.to_location or current_location
            update_inventory_from_putaway(product_id, quantity, location)
        
        conn.commit()
        
        return {
            "success": True,
            "task_id": result['id'],
            "task_number": result['task_number'],
            "status": result['status'],
            "message": "Putaway task updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# API Endpoints - Discrepancy Management
# ============================================================================

@app.get("/api/inbound/discrepancies")
async def get_discrepancies(
    resolution_status: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0
):
    """Get list of receiving discrepancies"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        where_sql = "WHERE rd.resolution_status = %s" if resolution_status else ""
        params = [resolution_status] if resolution_status else []
        
        query = f"""
            SELECT 
                rd.id, rd.shipment_id, rd.shipment_item_id,
                rd.discrepancy_type, rd.expected_quantity, rd.actual_quantity,
                rd.variance, rd.resolution_status, rd.resolution_notes,
                rd.reported_by, rd.resolved_by, rd.resolved_at, rd.created_at,
                s.shipment_number, si.sku, si.product_id
            FROM receiving_discrepancies rd
            JOIN inbound_shipments s ON rd.shipment_id = s.id
            LEFT JOIN inbound_shipment_items si ON rd.shipment_item_id = si.id
            {where_sql}
            ORDER BY rd.created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        discrepancies = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return {
            "success": True,
            "discrepancies": discrepancies
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.put("/api/inbound/discrepancies/{discrepancy_id}/resolve")
async def resolve_discrepancy(discrepancy_id: int, resolution: DiscrepancyResolve):
    """Resolve a receiving discrepancy"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            UPDATE receiving_discrepancies 
            SET 
                resolution_status = %s,
                resolution_notes = %s,
                resolved_by = %s,
                resolved_at = NOW()
            WHERE id = %s
            RETURNING id, discrepancy_type, resolution_status
        """
        cursor.execute(query, (
            resolution.resolution_status,
            resolution.resolution_notes,
            resolution.resolved_by,
            discrepancy_id
        ))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Discrepancy not found")
        
        conn.commit()
        
        return {
            "success": True,
            "discrepancy_id": result['id'],
            "discrepancy_type": result['discrepancy_type'],
            "resolution_status": result['resolution_status'],
            "message": "Discrepancy resolved successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# API Endpoints - Metrics & Analytics
# ============================================================================

@app.get("/api/inbound/metrics")
async def get_inbound_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    warehouse_id: Optional[int] = None
):
    """Get inbound performance metrics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        where_clauses = ["date BETWEEN %s AND %s"]
        params = [start_date, end_date]
        
        if warehouse_id:
            where_clauses.append("warehouse_id = %s")
            params.append(warehouse_id)
        
        where_sql = "WHERE " + " AND ".join(where_clauses)
        
        # Get metrics
        query = f"""
            SELECT 
                date,
                warehouse_id,
                shipments_received,
                items_received,
                items_accepted,
                items_rejected,
                average_receiving_time,
                average_putaway_time,
                discrepancy_rate,
                quality_pass_rate,
                on_time_arrival_rate
            FROM inbound_metrics
            {where_sql}
            ORDER BY date DESC
        """
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        metrics = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Calculate summary statistics
        summary_query = f"""
            SELECT 
                SUM(shipments_received) as total_shipments,
                SUM(items_received) as total_items,
                SUM(items_accepted) as total_accepted,
                SUM(items_rejected) as total_rejected,
                AVG(discrepancy_rate) as avg_discrepancy_rate,
                AVG(quality_pass_rate) as avg_quality_pass_rate,
                AVG(on_time_arrival_rate) as avg_on_time_rate
            FROM inbound_metrics
            {where_sql}
        """
        cursor.execute(summary_query, params)
        summary = cursor.fetchone()
        
        summary_dict = {
            "total_shipments": summary['total_shipments'] or 0,
            "total_items": summary['total_items'] or 0,
            "total_accepted": summary['total_accepted'] or 0,
            "total_rejected": summary['total_rejected'] or 0,
            "avg_discrepancy_rate": float(summary['avg_discrepancy_rate']) if summary['avg_discrepancy_rate'] else 0,
            "avg_quality_pass_rate": float(summary['avg_quality_pass_rate']) if summary['avg_quality_pass_rate'] else 100,
            "avg_on_time_rate": float(summary['avg_on_time_rate']) if summary['avg_on_time_rate'] else 0
        }
        
        return {
            "success": True,
            "metrics": metrics,
            "summary": summary_dict,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/api/inbound/metrics/calculate")
async def trigger_metrics_calculation(date: Optional[str] = None, warehouse_id: Optional[int] = None):
    """Manually trigger metrics calculation for a specific date"""
    try:
        result = calculate_inbound_metrics(date, warehouse_id)
        
        return {
            "success": True,
            "message": "Metrics calculated successfully",
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "warehouse_id": warehouse_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8032))
    uvicorn.run(app, host="0.0.0.0", port=port)
