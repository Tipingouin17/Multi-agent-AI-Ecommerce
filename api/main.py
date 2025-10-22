#!/usr/bin/env python3
"""
Unified API Server for Multi-Agent E-commerce Platform
Serves all endpoints for the React dashboard
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import os
import uvicorn

# Database configuration
# Get password first and validate
DB_PASSWORD = os.environ.get("DATABASE_PASSWORD")
if not DB_PASSWORD:
    raise ValueError("DATABASE_PASSWORD must be set in environment variables")

DB_CONFIG = {
    "host": os.environ.get('DATABASE_HOST', 'localhost'),
    "port": 5432,
    "database": "multi_agent_ecommerce",
    "user": "postgres",
    "password": DB_PASSWORD,
}

app = FastAPI(title="Multi-Agent E-commerce API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(","),  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection helper
def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

# Pydantic models
class Product(BaseModel):
    id: str
    sku: str
    name: str
    description: Optional[str]
    category: str
    brand: str
    price: float
    cost: float
    weight: float
    dimensions: Optional[dict]
    condition: str
    grade: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

class Customer(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    shipping_address: dict
    billing_address: Optional[dict]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

class Order(BaseModel):
    id: str
    customer_id: str
    channel: str
    channel_order_id: str
    status: str
    shipping_address: dict
    billing_address: dict
    subtotal: float
    shipping_cost: float
    tax_amount: float
    total_amount: float
    notes: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

class Warehouse(BaseModel):
    id: str
    name: str
    address: dict
    capacity: int
    operational_hours: dict
    contact_email: str
    contact_phone: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

class Inventory(BaseModel):
    id: str
    product_id: str
    warehouse_id: str
    quantity: int
    reserved_quantity: int
    reorder_point: int
    max_stock: int
    last_updated: Optional[datetime]

# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# Products endpoints
@app.get("/api/products")
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = None
):
    """Get all products with pagination"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if category:
            cursor.execute("""
                SELECT * FROM products 
                WHERE category = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (category, limit, skip))
        else:
            cursor.execute("""
                SELECT * FROM products 
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (limit, skip))
        
        products = cursor.fetchall()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as count FROM products")
        total = cursor.fetchone()['count']
        
        conn.close()
        
        return {
            "products": products,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products/{product_id}")
async def get_product(product_id: str):
    """Get single product by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        
        conn.close()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/products")
async def create_product(product: Product):
    """Create new product"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO products (id, sku, name, description, category, brand, price, cost, weight, dimensions, condition, grade, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (
            product.id, product.sku, product.name, product.description, product.category,
            product.brand, product.price, product.cost, product.weight, Json(product.dimensions) if product.dimensions else None,
            product.condition, product.grade, datetime.now(), datetime.now()
        ))
        
        new_product = cursor.fetchone()
        conn.commit()
        conn.close()
        
        return new_product
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Customers endpoints
@app.get("/api/customers")
async def get_customers(skip: int = 0, limit: int = 100):
    """Get all customers"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM customers 
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (limit, skip))
        
        customers = cursor.fetchall()
        
        cursor.execute("SELECT COUNT(*) as count FROM customers")
        total = cursor.fetchone()['count']
        
        conn.close()
        
        return {
            "customers": customers,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/customers/{customer_id}")
async def get_customer(customer_id: str):
    """Get single customer by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        customer = cursor.fetchone()
        
        conn.close()
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return customer
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Orders endpoints
@app.get("/api/orders")
async def get_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    customer_id: Optional[str] = None
):
    """Get all orders with filters"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM orders WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        if customer_id:
            query += " AND customer_id = %s"
            params.append(customer_id)
        
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        cursor.execute(query, params)
        orders = cursor.fetchall()
        
        # Get order items for each order
        for order in orders:
            cursor.execute("""
                SELECT oi.*, p.name as product_name
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = %s
            """, (order['id'],))
            order['items'] = cursor.fetchall()
        
        # Get total count
        count_query = "SELECT COUNT(*) as count FROM orders WHERE 1=1"
        count_params = []
        if status:
            count_query += " AND status = %s"
            count_params.append(status)
        if customer_id:
            count_query += " AND customer_id = %s"
            count_params.append(customer_id)
        
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['count']
        
        conn.close()
        
        return {
            "orders": orders,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders/{order_id}")
async def get_order(order_id: str):
    """Get single order by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
        order = cursor.fetchone()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Get order items
        cursor.execute("""
            SELECT oi.*, p.name as product_name
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """, (order_id,))
        order['items'] = cursor.fetchall()
        
        conn.close()
        
        return order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Warehouses endpoints
@app.get("/api/warehouses")
async def get_warehouses():
    """Get all warehouses"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM warehouses ORDER BY name")
        warehouses = cursor.fetchall()
        
        conn.close()
        
        return {"warehouses": warehouses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/warehouses/{warehouse_id}")
async def get_warehouse(warehouse_id: str):
    """Get single warehouse by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM warehouses WHERE id = %s", (warehouse_id,))
        warehouse = cursor.fetchone()
        
        conn.close()
        
        if not warehouse:
            raise HTTPException(status_code=404, detail="Warehouse not found")
        
        return warehouse
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Inventory endpoints
@app.get("/api/inventory")
async def get_inventory(
    warehouse_id: Optional[str] = None,
    product_id: Optional[str] = None
):
    """Get inventory with filters"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT i.*, p.name as product_name, p.sku, w.name as warehouse_name
            FROM inventory i
            JOIN products p ON i.product_id = p.id
            JOIN warehouses w ON i.warehouse_id = w.id
            WHERE 1=1
        """
        params = []
        
        if warehouse_id:
            query += " AND i.warehouse_id = %s"
            params.append(warehouse_id)
        
        if product_id:
            query += " AND i.product_id = %s"
            params.append(product_id)
        
        query += " ORDER BY i.last_updated DESC"
        
        cursor.execute(query, params)
        inventory = cursor.fetchall()
        
        conn.close()
        
        return {"inventory": inventory}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Dashboard metrics endpoints
@app.get("/api/metrics/dashboard")
async def get_dashboard_metrics():
    """Get dashboard metrics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total revenue
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as total_revenue FROM orders WHERE status != 'cancelled'")
        total_revenue = cursor.fetchone()['total_revenue']
        
        # Total orders
        cursor.execute("SELECT COUNT(*) as total_orders FROM orders")
        total_orders = cursor.fetchone()['total_orders']
        
        # Total products
        cursor.execute("SELECT COUNT(*) as total_products FROM products")
        total_products = cursor.fetchone()['total_products']
        
        # Total customers
        cursor.execute("SELECT COUNT(*) as total_customers FROM customers")
        total_customers = cursor.fetchone()['total_customers']
        
        # Average order value
        cursor.execute("SELECT COALESCE(AVG(total_amount), 0) as avg_order_value FROM orders WHERE status != 'cancelled'")
        avg_order_value = cursor.fetchone()['avg_order_value']
        
        # Orders by status
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM orders 
            GROUP BY status
        """)
        orders_by_status = cursor.fetchall()
        
        # Low stock products
        cursor.execute("""
            SELECT COUNT(DISTINCT product_id) as low_stock_count
            FROM inventory
            WHERE quantity < reorder_point
        """)
        low_stock_count = cursor.fetchone()['low_stock_count']
        
        # Recent orders
        cursor.execute("""
            SELECT o.*, c.first_name, c.last_name
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            ORDER BY o.created_at DESC
            LIMIT 10
        """)
        recent_orders = cursor.fetchall()
        
        conn.close()
        
        return {
            "total_revenue": float(total_revenue),
            "total_orders": total_orders,
            "total_products": total_products,
            "total_customers": total_customers,
            "avg_order_value": float(avg_order_value),
            "orders_by_status": orders_by_status,
            "low_stock_count": low_stock_count,
            "recent_orders": recent_orders
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Agent status endpoints
@app.get("/api/agents")
async def get_agents_status():
    """Get all agents status"""
    # This would normally query agent_metrics table or agent health endpoints
    # For now, return mock data structure
    agents = [
        {"name": "Order Agent", "status": "active", "messages_processed": 1247, "avg_response_time": 0.12, "error_rate": 0.02},
        {"name": "Product Agent", "status": "active", "messages_processed": 892, "avg_response_time": 0.08, "error_rate": 0.01},
        {"name": "Payment Agent", "status": "degraded", "messages_processed": 534, "avg_response_time": 0.45, "error_rate": 0.08},
        {"name": "Inventory Agent", "status": "active", "messages_processed": 1089, "avg_response_time": 0.15, "error_rate": 0.03},
        {"name": "Warehouse Agent", "status": "active", "messages_processed": 756, "avg_response_time": 0.10, "error_rate": 0.01},
        {"name": "Shipping Agent", "status": "active", "messages_processed": 623, "avg_response_time": 0.18, "error_rate": 0.02},
    ]
    
    return {"agents": agents, "total": len(agents), "active": 5, "degraded": 1, "inactive": 0}

# System health endpoints
@app.get("/api/system/health")
async def get_system_health():
    """Get system health metrics"""
    try:
        conn = get_db_connection()
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "uptime": "99.9%",
            "cpu_usage": 45,
            "memory_usage": 62,
            "disk_usage": 38,
            "active_agents": 24,
            "total_agents": 26,
            "throughput": 342,  # requests/sec
            "active_alerts": 3
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    print("🚀 Starting Multi-Agent E-commerce API Server...")
    print("📊 Database:", DB_CONFIG['database'])
    print("🌐 Server: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)

