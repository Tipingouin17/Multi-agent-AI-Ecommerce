#!/usr/bin/env python3
"""
Analytics Agent v3 - Business Intelligence & Reporting
Provides aggregated analytics data for dashboards
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Analytics Agent", version="3.0.0")

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
    "database": os.getenv("POSTGRES_DB", "ecommerce_db"),
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

def parse_time_range(time_range: str) -> tuple:
    """Parse time range string to start and end dates"""
    now = datetime.now()
    if time_range == "7d":
        start_date = now - timedelta(days=7)
    elif time_range == "30d":
        start_date = now - timedelta(days=30)
    elif time_range == "90d":
        start_date = now - timedelta(days=90)
    elif time_range == "1y":
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=30)
    
    return start_date, now

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "analytics_agent",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# SALES & REVENUE ANALYTICS
# ============================================================================

@app.get("/api/analytics/sales-overview")
async def get_sales_overview(timeRange: str = Query("30d")):
    """Get sales overview metrics"""
    try:
        start_date, end_date = parse_time_range(timeRange)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate current period metrics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_orders,
                COALESCE(SUM(total_amount), 0) as total_revenue,
                COALESCE(AVG(total_amount), 0) as average_order_value,
                COUNT(DISTINCT customer_id) as total_customers
            FROM orders
            WHERE created_at >= %s AND created_at <= %s
                AND status NOT IN ('cancelled', 'failed')
        """, (start_date, end_date))
        
        current = cursor.fetchone()
        
        # Calculate previous period for comparison
        period_length = (end_date - start_date).days
        prev_start = start_date - timedelta(days=period_length)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_orders,
                COALESCE(SUM(total_amount), 0) as total_revenue,
                COALESCE(AVG(total_amount), 0) as average_order_value,
                COUNT(DISTINCT customer_id) as total_customers
            FROM orders
            WHERE created_at >= %s AND created_at < %s
                AND status NOT IN ('cancelled', 'failed')
        """, (prev_start, start_date))
        
        previous = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # Calculate changes
        def calc_change(current_val, prev_val):
            if prev_val == 0:
                return 100.0 if current_val > 0 else 0.0
            return ((float(current_val) - float(prev_val)) / float(prev_val)) * 100
        
        return {
            "totalRevenue": float(current['total_revenue']),
            "revenueChange": calc_change(current['total_revenue'], previous['total_revenue']),
            "totalOrders": current['total_orders'],
            "ordersChange": calc_change(current['total_orders'], previous['total_orders']),
            "averageOrderValue": float(current['average_order_value']),
            "aovChange": calc_change(current['average_order_value'], previous['average_order_value']),
            "totalCustomers": current['total_customers'],
            "customersChange": calc_change(current['total_customers'], previous['total_customers'])
        }
        
    except Exception as e:
        logger.error(f"Error getting sales overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/sales-trends")
async def get_sales_trends(timeRange: str = Query("30d")):
    """Get sales trends over time"""
    try:
        start_date, end_date = parse_time_range(timeRange)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                COALESCE(SUM(total_amount), 0) as revenue,
                COUNT(*) as orders
            FROM orders
            WHERE created_at >= %s AND created_at <= %s
                AND status NOT IN ('cancelled', 'failed')
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (start_date, end_date))
        
        trends = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [
            {
                "date": row['date'].strftime('%Y-%m-%d'),
                "revenue": float(row['revenue']),
                "orders": row['orders']
            }
            for row in trends
        ]
        
    except Exception as e:
        logger.error(f"Error getting sales trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/revenue-breakdown")
async def get_revenue_breakdown(timeRange: str = Query("30d")):
    """Get revenue breakdown by category"""
    try:
        start_date, end_date = parse_time_range(timeRange)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                p.category,
                COALESCE(SUM(oi.quantity * oi.price), 0) as value
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            JOIN products p ON oi.product_id = p.id
            WHERE o.created_at >= %s AND o.created_at <= %s
                AND o.status NOT IN ('cancelled', 'failed')
            GROUP BY p.category
            ORDER BY value DESC
            LIMIT 10
        """, (start_date, end_date))
        
        breakdown = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [
            {
                "name": row['category'] or 'Uncategorized',
                "value": float(row['value'])
            }
            for row in breakdown
        ]
        
    except Exception as e:
        logger.error(f"Error getting revenue breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/top-products")
async def get_top_products(timeRange: str = Query("30d"), limit: int = Query(10)):
    """Get top selling products"""
    try:
        start_date, end_date = parse_time_range(timeRange)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                p.id,
                p.name,
                SUM(oi.quantity) as units,
                SUM(oi.quantity * oi.price) as revenue
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            JOIN products p ON oi.product_id = p.id
            WHERE o.created_at >= %s AND o.created_at <= %s
                AND o.status NOT IN ('cancelled', 'failed')
            GROUP BY p.id, p.name
            ORDER BY revenue DESC
            LIMIT %s
        """, (start_date, end_date, limit))
        
        products = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [
            {
                "id": row['id'],
                "name": row['name'],
                "units": row['units'],
                "revenue": float(row['revenue']),
                "growth": 15.5  # TODO: Calculate actual growth
            }
            for row in products
        ]
        
    except Exception as e:
        logger.error(f"Error getting top products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ORDER ANALYTICS
# ============================================================================

@app.get("/api/analytics/order-metrics")
async def get_order_metrics(timeRange: str = Query("30d")):
    """Get order management metrics"""
    try:
        start_date, end_date = parse_time_range(timeRange)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Current period metrics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_orders,
                COUNT(*) FILTER (WHERE status = 'pending') as pending_orders,
                COUNT(*) FILTER (WHERE status = 'delayed') as delayed_orders,
                COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_orders,
                COUNT(*) FILTER (WHERE status = 'delivered') as delivered_orders,
                AVG(EXTRACT(EPOCH FROM (delivered_at - created_at))/3600) as avg_fulfillment_hours
            FROM orders
            WHERE created_at >= %s AND created_at <= %s
        """, (start_date, end_date))
        
        metrics = cursor.fetchone()
        
        # Calculate success rate
        total = metrics['total_orders'] or 1
        success_rate = (metrics['delivered_orders'] / total) * 100
        
        cursor.close()
        conn.close()
        
        return {
            "totalOrders": metrics['total_orders'],
            "orderGrowth": 12.5,  # TODO: Calculate actual growth
            "pendingOrders": metrics['pending_orders'],
            "delayedOrders": metrics['delayed_orders'],
            "recentCancellations": metrics['cancelled_orders'],
            "avgFulfillmentTime": float(metrics['avg_fulfillment_hours'] or 0),
            "fulfillmentImprovement": 8.3,  # TODO: Calculate actual improvement
            "successRate": success_rate
        }
        
    except Exception as e:
        logger.error(f"Error getting order metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/order-status-distribution")
async def get_order_status_distribution(timeRange: str = Query("30d")):
    """Get order status distribution"""
    try:
        start_date, end_date = parse_time_range(timeRange)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as value
            FROM orders
            WHERE created_at >= %s AND created_at <= %s
            GROUP BY status
            ORDER BY value DESC
        """, (start_date, end_date))
        
        distribution = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [
            {
                "status": row['status'],
                "name": row['status'].title(),
                "value": row['value']
            }
            for row in distribution
        ]
        
    except Exception as e:
        logger.error(f"Error getting order status distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/order-trends")
async def get_order_trends(timeRange: str = Query("30d")):
    """Get order volume trends"""
    try:
        start_date, end_date = parse_time_range(timeRange)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as orders,
                COUNT(*) FILTER (WHERE status = 'delivered') as delivered,
                COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled
            FROM orders
            WHERE created_at >= %s AND created_at <= %s
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (start_date, end_date))
        
        trends = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [
            {
                "date": row['date'].strftime('%Y-%m-%d'),
                "orders": row['orders'],
                "delivered": row['delivered'],
                "cancelled": row['cancelled']
            }
            for row in trends
        ]
        
    except Exception as e:
        logger.error(f"Error getting order trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/fulfillment-metrics")
async def get_fulfillment_metrics(timeRange: str = Query("30d")):
    """Get fulfillment performance metrics"""
    try:
        # Mock data for now - TODO: Implement actual tracking
        return {
            "stages": [
                {"name": "Order Processing", "avgTime": 2.5},
                {"name": "Picking & Packing", "avgTime": 4.0},
                {"name": "Shipping", "avgTime": 48.0},
                {"name": "Delivery", "avgTime": 72.0}
            ],
            "maxTime": 72.0
        }
        
    except Exception as e:
        logger.error(f"Error getting fulfillment metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# INVENTORY ANALYTICS
# ============================================================================

@app.get("/api/analytics/inventory-overview")
async def get_inventory_overview():
    """Get inventory overview metrics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_skus,
                COUNT(*) FILTER (WHERE quantity > 0) as active_skus,
                COUNT(*) FILTER (WHERE quantity <= reorder_level) as low_stock_count,
                COUNT(*) FILTER (WHERE quantity = 0) as out_of_stock_count,
                COALESCE(SUM(quantity * price), 0) as total_value
            FROM products
        """)
        
        overview = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return {
            "totalSKUs": overview['total_skus'],
            "activeSKUs": overview['active_skus'],
            "lowStockCount": overview['low_stock_count'],
            "outOfStockCount": overview['out_of_stock_count'],
            "totalValue": float(overview['total_value']),
            "valueChange": 5.2,  # TODO: Calculate actual change
            "avgTurnoverRate": 4.5,
            "avgDaysInStock": 81,
            "deadStockCount": 12
        }
        
    except Exception as e:
        logger.error(f"Error getting inventory overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/low-stock-items")
async def get_low_stock_items(limit: int = Query(10)):
    """Get low stock items"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id,
                name,
                sku,
                quantity as current_stock,
                reorder_level as min_stock
            FROM products
            WHERE quantity <= reorder_level
            ORDER BY (quantity::float / NULLIF(reorder_level, 0))
            LIMIT %s
        """, (limit,))
        
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [
            {
                "id": row['id'],
                "name": row['name'],
                "sku": row['sku'],
                "currentStock": row['current_stock'],
                "minStock": row['min_stock']
            }
            for row in items
        ]
        
    except Exception as e:
        logger.error(f"Error getting low stock items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/warehouse-distribution")
async def get_warehouse_distribution():
    """Get warehouse stock distribution"""
    try:
        # Mock data for now - TODO: Implement actual warehouse tracking
        return [
            {"name": "Main Warehouse", "stock": 15000, "utilization": 75},
            {"name": "East Coast DC", "stock": 8500, "utilization": 60},
            {"name": "West Coast DC", "stock": 12000, "utilization": 85},
            {"name": "Midwest DC", "stock": 6500, "utilization": 45}
        ]
        
    except Exception as e:
        logger.error(f"Error getting warehouse distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/inventory-turnover")
async def get_inventory_turnover(timeRange: str = Query("30d")):
    """Get inventory turnover rate"""
    try:
        # Mock data for now - TODO: Implement actual turnover calculation
        start_date, end_date = parse_time_range(timeRange)
        days = (end_date - start_date).days
        
        data = []
        for i in range(min(days, 30)):
            date = start_date + timedelta(days=i)
            data.append({
                "date": date.strftime('%Y-%m-%d'),
                "turnoverRate": 4.2 + (i * 0.05),
                "daysToSell": 85 - (i * 0.5)
            })
        
        return data
        
    except Exception as e:
        logger.error(f"Error getting inventory turnover: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# FINANCIAL ANALYTICS
# ============================================================================

@app.get("/api/analytics/financial-overview")
async def get_financial_overview(timeRange: str = Query("30d")):
    """Get financial overview metrics"""
    try:
        start_date, end_date = parse_time_range(timeRange)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COALESCE(SUM(total_amount), 0) as total_revenue
            FROM orders
            WHERE created_at >= %s AND created_at <= %s
                AND status NOT IN ('cancelled', 'failed')
        """, (start_date, end_date))
        
        revenue = cursor.fetchone()
        total_revenue = float(revenue['total_revenue'])
        
        # Mock calculations for now - TODO: Implement actual expense tracking
        cogs = total_revenue * 0.45  # 45% COGS
        operating_expenses = total_revenue * 0.25  # 25% OpEx
        total_expenses = cogs + operating_expenses
        net_profit = total_revenue - total_expenses
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
        ebitda = net_profit + (operating_expenses * 0.2)  # Add back depreciation/amortization
        
        cursor.close()
        conn.close()
        
        return {
            "totalRevenue": total_revenue,
            "revenueChange": 15.3,
            "netProfit": net_profit,
            "profitChange": 18.7,
            "totalExpenses": total_expenses,
            "expensesChange": 12.1,
            "profitMargin": profit_margin,
            "marginChange": 2.4,
            "cogs": cogs,
            "operatingExpenses": operating_expenses,
            "ebitda": ebitda
        }
        
    except Exception as e:
        logger.error(f"Error getting financial overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/revenue-expenses")
async def get_revenue_expenses(timeRange: str = Query("30d")):
    """Get revenue vs expenses over time"""
    try:
        start_date, end_date = parse_time_range(timeRange)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                COALESCE(SUM(total_amount), 0) as revenue
            FROM orders
            WHERE created_at >= %s AND created_at <= %s
                AND status NOT IN ('cancelled', 'failed')
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (start_date, end_date))
        
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [
            {
                "date": row['date'].strftime('%Y-%m-%d'),
                "revenue": float(row['revenue']),
                "expenses": float(row['revenue']) * 0.70  # Mock 70% expense ratio
            }
            for row in data
        ]
        
    except Exception as e:
        logger.error(f"Error getting revenue expenses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/profit-margins")
async def get_profit_margins(timeRange: str = Query("30d")):
    """Get profit margins over time"""
    try:
        start_date, end_date = parse_time_range(timeRange)
        days = (end_date - start_date).days
        
        # Mock data for now - TODO: Implement actual margin tracking
        data = []
        for i in range(min(days, 30)):
            date = start_date + timedelta(days=i)
            data.append({
                "date": date.strftime('%Y-%m-%d'),
                "grossMargin": 55.0 + (i * 0.1),
                "netMargin": 30.0 + (i * 0.08)
            })
        
        return data
        
    except Exception as e:
        logger.error(f"Error getting profit margins: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/payment-methods-breakdown")
async def get_payment_methods_breakdown(timeRange: str = Query("30d")):
    """Get payment methods breakdown"""
    try:
        # Mock data for now - TODO: Implement actual payment method tracking
        return [
            {"method": "Credit Card", "amount": 125000},
            {"method": "PayPal", "amount": 45000},
            {"method": "Debit Card", "amount": 32000},
            {"method": "Bank Transfer", "amount": 18000},
            {"method": "Other", "amount": 5000}
        ]
        
    except Exception as e:
        logger.error(f"Error getting payment methods breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8031))
    uvicorn.run(app, host="0.0.0.0", port=port)
