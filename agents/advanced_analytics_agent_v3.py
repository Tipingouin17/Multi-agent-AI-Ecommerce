"""
Advanced Analytics & Reporting Agent v3
Comprehensive analytics and reporting system with pre-built reports and exports
"""

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, date
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
import csv
import io

app = FastAPI(title="Advanced Analytics Agent", version="3.0.0")

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

class ReportCreate(BaseModel):
    name: str
    description: Optional[str] = None
    report_type: str
    data_sources: Optional[Dict] = None
    fields: Optional[List[str]] = None
    filters: Optional[Dict] = None

class ReportExport(BaseModel):
    format: str  # csv, json

# ============================================================================
# Helper Functions
# ============================================================================

def execute_query(query: str, params: tuple = None) -> List[Dict]:
    """Execute SQL query and return results"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def generate_csv(data: List[Dict]) -> str:
    """Generate CSV from data"""
    if not data:
        return ""
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    
    return output.getvalue()

# ============================================================================
# API Endpoints - Health & Info
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "advanced_analytics_agent",
        "version": "3.0.0",
        "features": ["pre_built_reports", "exports", "dashboards"],
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# API Endpoints - Pre-built Reports
# ============================================================================

@app.get("/api/analytics/sales-summary")
async def get_sales_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get sales summary report"""
    
    # Default to last 30 days if not specified
    if not start_date:
        start_date = (date.today() - timedelta(days=30)).isoformat()
    if not end_date:
        end_date = date.today().isoformat()
    
    # Note: This is a simulated query as we don't have orders table populated yet
    # In production, this would query actual orders data
    
    return {
        "success": True,
        "report_type": "sales_summary",
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "metrics": {
            "total_sales": 0,
            "total_orders": 0,
            "average_order_value": 0,
            "total_items_sold": 0
        },
        "daily_sales": [],
        "top_products": [],
        "sales_by_category": []
    }

@app.get("/api/analytics/inventory-status")
async def get_inventory_status():
    """Get inventory status report"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get inventory summary
        cursor.execute("""
            SELECT 
                COUNT(*) as total_products,
                SUM(quantity) as total_quantity,
                COUNT(CASE WHEN quantity <= reorder_point THEN 1 END) as low_stock_items,
                COUNT(CASE WHEN quantity = 0 THEN 1 END) as out_of_stock_items
            FROM inventory
        """)
        
        summary = cursor.fetchone()
        
        # Get low stock items
        cursor.execute("""
            SELECT 
                product_id,
                warehouse_id,
                quantity,
                reorder_point,
                last_updated
            FROM inventory
            WHERE quantity <= reorder_point
            ORDER BY quantity ASC
            LIMIT 20
        """)
        
        low_stock = cursor.fetchall()
        
        return {
            "success": True,
            "report_type": "inventory_status",
            "summary": dict(summary) if summary else {},
            "low_stock_items": [dict(item) for item in low_stock],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/analytics/fulfillment-metrics")
async def get_fulfillment_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get fulfillment metrics report"""
    
    if not start_date:
        start_date = (date.today() - timedelta(days=30)).isoformat()
    if not end_date:
        end_date = date.today().isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get reservation metrics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_reservations,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_reservations,
                COUNT(CASE WHEN status = 'fulfilled' THEN 1 END) as fulfilled_reservations,
                COUNT(CASE WHEN status = 'expired' THEN 1 END) as expired_reservations
            FROM inventory_reservations
            WHERE created_at BETWEEN %s AND %s
        """, (start_date, end_date))
        
        reservations = cursor.fetchone()
        
        # Get backorder metrics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_backorders,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_backorders,
                COUNT(CASE WHEN status = 'fulfilled' THEN 1 END) as fulfilled_backorders,
                AVG(EXTRACT(EPOCH FROM (fulfilled_at - created_at)) / 86400) as avg_fulfillment_days
            FROM backorders
            WHERE created_at BETWEEN %s AND %s
        """, (start_date, end_date))
        
        backorders = cursor.fetchone()
        
        return {
            "success": True,
            "report_type": "fulfillment_metrics",
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "reservations": dict(reservations) if reservations else {},
            "backorders": dict(backorders) if backorders else {},
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/analytics/inbound-metrics")
async def get_inbound_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get inbound management metrics"""
    
    if not start_date:
        start_date = (date.today() - timedelta(days=30)).isoformat()
    if not end_date:
        end_date = date.today().isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get shipment metrics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_shipments,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_shipments,
                COUNT(CASE WHEN status = 'receiving' THEN 1 END) as in_progress_shipments,
                AVG(EXTRACT(EPOCH FROM (completed_at - created_at)) / 86400) as avg_processing_days
            FROM inbound_shipments
            WHERE created_at BETWEEN %s AND %s
        """, (start_date, end_date))
        
        shipments = cursor.fetchone()
        
        # Get inspection metrics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_inspections,
                COUNT(CASE WHEN passed THEN 1 END) as passed_inspections,
                COUNT(CASE WHEN NOT passed THEN 1 END) as failed_inspections
            FROM quality_inspections
            WHERE inspection_date BETWEEN %s AND %s
        """, (start_date, end_date))
        
        inspections = cursor.fetchone()
        
        # Get discrepancy metrics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_discrepancies,
                COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_discrepancies,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_discrepancies
            FROM receiving_discrepancies
            WHERE created_at BETWEEN %s AND %s
        """, (start_date, end_date))
        
        discrepancies = cursor.fetchone()
        
        return {
            "success": True,
            "report_type": "inbound_metrics",
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "shipments": dict(shipments) if shipments else {},
            "inspections": dict(inspections) if inspections else {},
            "discrepancies": dict(discrepancies) if discrepancies else {},
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/analytics/rma-metrics")
async def get_rma_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get RMA workflow metrics"""
    
    if not start_date:
        start_date = (date.today() - timedelta(days=30)).isoformat()
    if not end_date:
        end_date = date.today().isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get RMA request metrics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_requests,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_requests,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_requests,
                AVG(EXTRACT(EPOCH FROM (completed_at - requested_at)) / 86400) as avg_processing_days
            FROM rma_requests
            WHERE requested_at BETWEEN %s AND %s
        """, (start_date, end_date))
        
        requests = cursor.fetchone()
        
        # Get refund metrics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_refunds,
                SUM(total_refund_amount) as total_refund_amount,
                AVG(total_refund_amount) as avg_refund_amount,
                COUNT(CASE WHEN refund_status = 'completed' THEN 1 END) as completed_refunds
            FROM rma_refunds
            WHERE created_at BETWEEN %s AND %s
        """, (start_date, end_date))
        
        refunds = cursor.fetchone()
        
        return {
            "success": True,
            "report_type": "rma_metrics",
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "requests": dict(requests) if requests else {},
            "refunds": dict(refunds) if refunds else {},
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/analytics/carrier-metrics")
async def get_carrier_metrics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get carrier performance metrics"""
    
    if not start_date:
        start_date = (date.today() - timedelta(days=30)).isoformat()
    if not end_date:
        end_date = date.today().isoformat()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get carrier metrics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_shipments,
                COUNT(DISTINCT carrier_id) as active_carriers,
                AVG(label_cost) as avg_shipping_cost
            FROM shipping_labels
            WHERE created_at BETWEEN %s AND %s
        """, (start_date, end_date))
        
        shipments = cursor.fetchone()
        
        # Get rate card uploads
        cursor.execute("""
            SELECT 
                COUNT(*) as total_uploads,
                COUNT(CASE WHEN extraction_status = 'completed' THEN 1 END) as successful_extractions,
                COUNT(CASE WHEN import_status = 'completed' THEN 1 END) as imported_rates
            FROM rate_card_uploads
            WHERE uploaded_at BETWEEN %s AND %s
        """, (start_date, end_date))
        
        uploads = cursor.fetchone()
        
        return {
            "success": True,
            "report_type": "carrier_metrics",
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "shipments": dict(shipments) if shipments else {},
            "rate_card_uploads": dict(uploads) if uploads else {},
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# API Endpoints - Comprehensive Dashboard
# ============================================================================

@app.get("/api/analytics/comprehensive-dashboard")
async def get_comprehensive_dashboard():
    """Get comprehensive platform dashboard with all metrics"""
    
    # Get date range (last 30 days)
    end_date = date.today().isoformat()
    start_date = (date.today() - timedelta(days=30)).isoformat()
    
    try:
        # Gather all metrics
        inventory = await get_inventory_status()
        fulfillment = await get_fulfillment_metrics(start_date, end_date)
        inbound = await get_inbound_metrics(start_date, end_date)
        rma = await get_rma_metrics(start_date, end_date)
        carrier = await get_carrier_metrics(start_date, end_date)
        
        return {
            "success": True,
            "dashboard_type": "comprehensive",
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "inventory": inventory,
            "fulfillment": fulfillment,
            "inbound": inbound,
            "rma": rma,
            "carrier": carrier,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# API Endpoints - Report Management
# ============================================================================

@app.post("/api/analytics/reports")
async def create_report(report: ReportCreate):
    """Create custom report"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO reports
            (name, description, report_type, data_sources, fields, filters)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (report.name, report.description, report.report_type,
              json.dumps(report.data_sources) if report.data_sources else None,
              json.dumps(report.fields) if report.fields else None,
              json.dumps(report.filters) if report.filters else None))
        
        report_id = cursor.fetchone()['id']
        conn.commit()
        
        return {
            "success": True,
            "report_id": report_id,
            "message": "Report created successfully"
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/analytics/reports")
async def list_reports(report_type: Optional[str] = None):
    """List reports"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = "SELECT * FROM reports WHERE 1=1"
        params = []
        
        if report_type:
            query += " AND report_type = %s"
            params.append(report_type)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params if params else None)
        reports = cursor.fetchall()
        
        return {
            "success": True,
            "reports": [dict(r) for r in reports],
            "total": len(reports)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# API Endpoints - Export
# ============================================================================

@app.get("/api/analytics/export/inventory-status")
async def export_inventory_status(format: str = "csv"):
    """Export inventory status report"""
    
    # Get inventory data
    inventory_data = await get_inventory_status()
    
    if format == "csv":
        # Generate CSV
        csv_data = generate_csv(inventory_data.get("low_stock_items", []))
        
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=inventory_status.csv"}
        )
    else:
        return inventory_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8036)
