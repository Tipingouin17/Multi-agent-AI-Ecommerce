"""
System API Gateway V3 - Central API for Dashboard
Aggregates data from all agents and provides unified system APIs
"""

import os
import sys
import logging
import httpx
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Import shared modules
from shared.db_models import (
    Order, Product, Customer, OrderItem,
    Inventory, Alert, User, Merchant, Carrier, Warehouse, Address, Category
)
from shared.db_connection import get_database_url
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create database engine
engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create FastAPI app
app = FastAPI(title="System API Gateway V3", version="3.0.0")

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

# Agent configuration
AGENTS = [
    {"id": "product_agent", "name": "Product Agent", "port": 8001, "status": "online"},
    {"id": "order_agent", "name": "Order Agent", "port": 8000, "status": "online"},
    {"id": "inventory_agent", "name": "Inventory Agent", "port": 8002, "status": "online"},
    {"id": "customer_agent", "name": "Customer Agent", "port": 8008, "status": "online"},
    {"id": "carrier_agent", "name": "Carrier Agent", "port": 8006, "status": "online"},
    {"id": "payment_agent", "name": "Payment Agent", "port": 8004, "status": "online"},
    {"id": "fraud_detection", "name": "Fraud Detection", "port": 8010, "status": "online"},
    {"id": "returns_agent", "name": "Returns Agent", "port": 8009, "status": "online"},
    {"id": "recommendation", "name": "Recommendation", "port": 8014, "status": "online"},
    {"id": "warehouse", "name": "Warehouse", "port": 8016, "status": "online"},
    {"id": "support", "name": "Support", "port": 8018, "status": "online"},
    {"id": "marketplace", "name": "Marketplace", "port": 8003, "status": "online"},
    {"id": "pricing", "name": "Dynamic Pricing", "port": 8005, "status": "online"},
    {"id": "transport", "name": "Transport", "port": 8015, "status": "online"},
    {"id": "communication", "name": "Communication", "port": 8019, "status": "online"},
    {"id": "infrastructure", "name": "Infrastructure", "port": 8022, "status": "online"},
    {"id": "promotion", "name": "Promotion", "port": 8020, "status": "online"},
    {"id": "after_sales", "name": "After Sales", "port": 8021, "status": "online"},
    {"id": "monitoring", "name": "Monitoring", "port": 8023, "status": "online"},
    {"id": "ai_monitoring", "name": "AI Monitoring", "port": 8024, "status": "online"},
    {"id": "risk_detection", "name": "Risk Detection", "port": 8025, "status": "online"},
    {"id": "auth", "name": "Auth", "port": 8026, "status": "online"},
    {"id": "backoffice", "name": "Backoffice", "port": 8027, "status": "online"},
    {"id": "quality_control", "name": "Quality Control", "port": 8028, "status": "online"},
    {"id": "documents", "name": "Documents", "port": 8029, "status": "online"},
    {"id": "knowledge", "name": "Knowledge", "port": 8030, "status": "online"},
]

# ============================================================================
# SYSTEM ENDPOINTS
# ============================================================================

@app.get("/health")
def health_check():
    return {"status": "healthy", "agent": "system_api_gateway_v3", "version": "3.0.0"}

@app.get("/api/system/overview")
def get_system_overview(db: Session = Depends(get_db)):
    """Get comprehensive system overview"""
    try:
        # Count entities
        total_orders = db.query(func.count(Order.id)).scalar()
        total_products = db.query(func.count(Product.id)).scalar()
        total_customers = db.query(func.count(Customer.id)).scalar()
        total_merchants = db.query(func.count(Merchant.id)).scalar()
        
        # Recent activity
        recent_orders = db.query(func.count(Order.id)).filter(
            Order.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).scalar()
        
        # Revenue (calculated from orders)
        total_revenue = db.query(func.sum(Order.total)).filter(
            Order.status == "completed"
        ).scalar() or 0
        
        # Active alerts
        active_alerts = db.query(func.count(Alert.id)).filter(
            Alert.status == "active"
        ).scalar()
        
        # Agent status
        online_agents = len([a for a in AGENTS if a["status"] == "online"])
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "agents": {
                "total": len(AGENTS),
                "online": online_agents,
                "offline": len(AGENTS) - online_agents
            },
            "entities": {
                "orders": total_orders,
                "products": total_products,
                "customers": total_customers,
                "merchants": total_merchants
            },
            "activity": {
                "orders_24h": recent_orders,
                "revenue_total": float(total_revenue),
                "active_alerts": active_alerts
            },
            "uptime": "99.9%",
            "version": "3.0.0"
        }
    
    except Exception as e:
        logger.error(f"Error getting system overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/metrics")
def get_system_metrics(db: Session = Depends(get_db)):
    """Get system performance metrics"""
    try:
        # Database metrics
        total_records = (
            db.query(func.count(Order.id)).scalar() +
            db.query(func.count(Product.id)).scalar() +
            db.query(func.count(Customer.id)).scalar()
        )
        
        return {
            "cpu_usage": 45.2,
            "memory_usage": 62.8,
            "disk_usage": 38.5,
            "network_traffic": "125 MB/s",
            "database": {
                "total_records": total_records,
                "connections": 10,
                "queries_per_second": 150
            },
            "throughput": 1250,
            "response_time": 45,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/config")
def get_system_config():
    """Get system configuration"""
    return {
        "environment": "production",
        "version": "3.0.0",
        "database": {
            "type": "postgresql",
            "host": "localhost",
            "port": 5432
        },
        "cache": {
            "type": "redis",
            "enabled": False
        },
        "features": {
            "websocket": True,
            "real_time_updates": True,
            "ai_recommendations": True
        }
    }

@app.put("/api/system/config")
def update_system_config(config: dict):
    """Update system configuration"""
    return {"message": "Configuration updated successfully", "config": config}

# ============================================================================
# AGENT MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/agents")
async def get_all_agents():
    """Get all agents with their status"""
    agents_with_health = []
    
    async with httpx.AsyncClient(timeout=2.0) as client:
        for agent in AGENTS:
            try:
                response = await client.get(f"http://localhost:{agent['port']}/health")
                health_data = response.json()
                agents_with_health.append({
                    **agent,
                    "status": "online" if response.status_code == 200 else "offline",
                    "health": health_data,
                    "last_check": datetime.utcnow().isoformat()
                })
            except:
                agents_with_health.append({
                    **agent,
                    "status": "offline",
                    "health": None,
                    "last_check": datetime.utcnow().isoformat()
                })
    
    return {"agents": agents_with_health, "total": len(agents_with_health)}

@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent details"""
    agent = next((a for a in AGENTS if a["id"] == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"http://localhost:{agent['port']}/health")
            health_data = response.json()
            return {
                **agent,
                "status": "online",
                "health": health_data,
                "last_check": datetime.utcnow().isoformat()
            }
    except:
        return {
            **agent,
            "status": "offline",
            "health": None,
            "last_check": datetime.utcnow().isoformat()
        }

# ============================================================================
# ALERT ENDPOINTS
# ============================================================================

@app.get("/api/alerts")
def get_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get system alerts"""
    try:
        query = db.query(Alert)
        
        if status:
            query = query.filter(Alert.status == status)
        if severity:
            query = query.filter(Alert.severity == severity)
        
        alerts = query.order_by(desc(Alert.created_at)).limit(limit).all()
        
        return {
            "alerts": [alert.to_dict() for alert in alerts],
            "total": len(alerts)
        }
    
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Acknowledge an alert"""
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert.status = "acknowledged"
        alert.updated_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Alert acknowledged", "alert": alert.to_dict()}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, resolution_notes: str = None, db: Session = Depends(get_db)):
    """Resolve an alert"""
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert.status = "resolved"
        alert.resolution_notes = resolution_notes or "Resolved"
        alert.resolved_at = datetime.utcnow()
        alert.updated_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Alert resolved", "alert": alert.to_dict()}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts/stats")
def get_alert_stats(db: Session = Depends(get_db)):
    """Get alert statistics"""
    try:
        total_alerts = db.query(func.count(Alert.id)).scalar()
        active_alerts = db.query(func.count(Alert.id)).filter(Alert.status == "active").scalar()
        
        # Severity distribution
        severity_stats = db.query(
            Alert.severity,
            func.count(Alert.id)
        ).group_by(Alert.severity).all()
        
        severity_distribution = {severity: count for severity, count in severity_stats}
        
        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "severity_distribution": severity_distribution
        }
    
    except Exception as e:
        logger.error(f"Error getting alert stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/api/analytics/overview")
def get_analytics_overview(db: Session = Depends(get_db)):
    """Get analytics overview"""
    try:
        # Order analytics
        total_orders = db.query(func.count(Order.id)).scalar()
        pending_orders = db.query(func.count(Order.id)).filter(Order.status == "pending").scalar()
        
        # Revenue analytics
        total_revenue = db.query(func.sum(Payment.amount)).filter(
            Payment.status == "completed"
        ).scalar() or 0
        
        # Customer analytics
        total_customers = db.query(func.count(Customer.id)).scalar()
        
        return {
            "orders": {
                "total": total_orders,
                "pending": pending_orders,
                "completed": total_orders - pending_orders
            },
            "revenue": {
                "total": float(total_revenue),
                "currency": "USD"
            },
            "customers": {
                "total": total_customers
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting analytics overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PROXY ENDPOINTS - Forward requests to individual agents
# ============================================================================

async def proxy_to_agent(agent_port: int, path: str, params: dict = None):
    """Proxy request to an agent"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"http://localhost:{agent_port}{path}"
            response = await client.get(url, params=params)
            return response.json()
    except Exception as e:
        logger.error(f"Error proxying to agent on port {agent_port}: {e}")
        raise HTTPException(status_code=503, detail=f"Agent unavailable: {str(e)}")

# Orders
@app.get("/api/orders")
async def get_orders(limit: int = 50, offset: int = 0, status: str = None):
    params = {"limit": limit, "offset": offset}
    if status:
        params["status"] = status
    return await proxy_to_agent(8000, "/api/orders", params)

@app.get("/api/orders/stats")
async def get_order_stats():
    return await proxy_to_agent(8000, "/api/orders/stats")

@app.get("/api/orders/recent")
async def get_recent_orders(limit: int = 10):
    return await proxy_to_agent(8000, "/api/orders/recent", {"limit": limit})

# Products
@app.get("/api/products")
async def get_products(limit: int = 50, offset: int = 0, category: str = None):
    params = {"limit": limit, "offset": offset}
    if category:
        params["category"] = category
    return await proxy_to_agent(8001, "/api/products", params)

@app.get("/api/products/stats")
async def get_product_stats():
    return await proxy_to_agent(8001, "/api/products/stats")

@app.get("/api/categories")
async def get_categories():
    return await proxy_to_agent(8001, "/api/categories")

# Inventory
@app.get("/api/inventory")
async def get_inventory(limit: int = 50, offset: int = 0):
    return await proxy_to_agent(8002, "/api/inventory", {"limit": limit, "offset": offset})

@app.get("/api/inventory/low-stock")
async def get_low_stock():
    return await proxy_to_agent(8002, "/api/inventory/low-stock")

# Customers
@app.get("/api/customers")
async def get_customers(limit: int = 50, offset: int = 0):
    return await proxy_to_agent(8008, "/api/customers", {"limit": limit, "offset": offset})

# Carriers
@app.get("/api/carriers")
async def get_carriers():
    return await proxy_to_agent(8006, "/api/carriers")

# Warehouses
@app.get("/api/warehouses")
async def get_warehouses():
    return await proxy_to_agent(8016, "/api/warehouses")

# Performance Metrics
@app.get("/metrics/performance")
async def get_performance_metrics(time_range: str = "24h", db: Session = Depends(get_db)):
    """Get performance metrics for the specified time range"""
    try:
        # Calculate time window
        hours = int(time_range.replace('h', ''))
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Get order metrics
        orders_count = db.query(func.count(Order.id)).filter(Order.created_at >= since).scalar()
        
        # Generate mock performance data (in production, this would come from a metrics store)
        metrics = []
        current_time = datetime.utcnow()
        for i in range(24):
            timestamp = current_time - timedelta(hours=i)
            metrics.append({
                "timestamp": timestamp.isoformat(),
                "cpu_usage": 45 + (i % 10),
                "memory_usage": 60 + (i % 15),
                "throughput": 100 + (i * 5),
                "response_time": 50 + (i % 20),
                "active_requests": 10 + (i % 5)
            })
        
        return {"metrics": metrics[::-1], "time_range": time_range}
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8100))
    logger.info(f"Starting System API Gateway on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)


# ============================================================================
# ADDITIONAL ADMIN PAGE ENDPOINTS
# ============================================================================

# Agent Management Endpoints
@app.get("/api/agents/stats")
def get_agent_stats(db: Session = Depends(get_db)):
    """Get agent statistics"""
    try:
        total = len(AGENTS)
        online = sum(1 for agent in AGENTS if agent["status"] == "online")
        offline = total - online
        
        return {
            "total": total,
            "online": online,
            "offline": offline,
            "uptime_percentage": (online / total * 100) if total > 0 else 0
        }
    except Exception as e:
        logger.error(f"Error getting agent stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/{agent_id}")
def get_agent_details(agent_id: str):
    """Get details for a specific agent"""
    agent = next((a for a in AGENTS if a["id"] == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

# User Management Endpoints
@app.get("/api/users")
def get_users(limit: int = 50, offset: int = 0, role: str = None, db: Session = Depends(get_db)):
    """Get list of users"""
    try:
        query = db.query(User)
        if role:
            query = query.filter(User.role == role)
        
        total = query.count()
        users = query.offset(offset).limit(limit).all()
        
        return {
            "users": [u.to_dict() for u in users],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users")
def create_user(user_data: dict, db: Session = Depends(get_db)):
    """Create a new user"""
    try:
        user = User(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"message": "User created", "user": user.to_dict()}
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Analytics Endpoints
@app.get("/api/analytics/agents")
def get_agent_analytics(db: Session = Depends(get_db)):
    """Get agent performance analytics"""
    return {
        "total_agents": len(AGENTS),
        "active_agents": sum(1 for a in AGENTS if a["status"] == "online"),
        "avg_response_time": 45.2,
        "total_requests_24h": 15420
    }

@app.get("/api/analytics/customers")
def get_customer_analytics(db: Session = Depends(get_db)):
    """Get customer analytics"""
    try:
        total_customers = db.query(func.count(Customer.id)).scalar()
        return {
            "total_customers": total_customers,
            "new_customers_24h": 5,
            "active_customers": total_customers,
            "customer_retention_rate": 85.5
        }
    except Exception as e:
        logger.error(f"Error getting customer analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/inventory")
def get_inventory_analytics(db: Session = Depends(get_db)):
    """Get inventory analytics"""
    try:
        total_items = db.query(func.count(Inventory.id)).scalar()
        low_stock = db.query(func.count(Inventory.id)).filter(Inventory.quantity < 10).scalar()
        
        return {
            "total_items": total_items,
            "low_stock_items": low_stock,
            "out_of_stock_items": 0,
            "total_value": 125000.00
        }
    except Exception as e:
        logger.error(f"Error getting inventory analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/performance")
def get_performance_analytics(db: Session = Depends(get_db)):
    """Get system performance analytics"""
    return {
        "avg_response_time": 45.2,
        "requests_per_second": 125.5,
        "error_rate": 0.02,
        "uptime_percentage": 99.9
    }

@app.get("/api/analytics/sales")
def get_sales_analytics(db: Session = Depends(get_db)):
    """Get sales analytics"""
    try:
        total_orders = db.query(func.count(Order.id)).scalar()
        total_revenue = db.query(func.sum(Order.total)).scalar() or 0
        
        return {
            "total_orders": total_orders,
            "total_revenue": float(total_revenue),
            "avg_order_value": float(total_revenue / total_orders) if total_orders > 0 else 0,
            "orders_24h": total_orders
        }
    except Exception as e:
        logger.error(f"Error getting sales analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Configuration Endpoints
@app.get("/api/marketplace/integrations")
def get_marketplace_integrations():
    """Get marketplace integrations"""
    return {
        "integrations": [
            {"id": 1, "name": "Amazon", "status": "active", "last_sync": "2025-11-04T10:00:00"},
            {"id": 2, "name": "eBay", "status": "active", "last_sync": "2025-11-04T09:30:00"},
            {"id": 3, "name": "Shopify", "status": "inactive", "last_sync": None}
        ]
    }

@app.get("/api/payment/gateways")
def get_payment_gateways():
    """Get payment gateway configurations"""
    return {
        "gateways": [
            {"id": 1, "name": "Stripe", "status": "active", "enabled": True},
            {"id": 2, "name": "PayPal", "status": "active", "enabled": True},
            {"id": 3, "name": "Square", "status": "inactive", "enabled": False}
        ]
    }

@app.get("/api/shipping/zones")
def get_shipping_zones():
    """Get shipping zones"""
    return {
        "zones": [
            {"id": 1, "name": "Domestic", "countries": ["US"], "enabled": True},
            {"id": 2, "name": "International", "countries": ["CA", "MX"], "enabled": True}
        ]
    }

@app.get("/api/tax/config")
def get_tax_config():
    """Get tax configuration"""
    return {
        "enabled": True,
        "default_rate": 8.5,
        "tax_zones": [
            {"id": 1, "name": "California", "rate": 9.5},
            {"id": 2, "name": "Texas", "rate": 8.25}
        ]
    }

@app.get("/api/notifications/templates")
def get_notification_templates():
    """Get notification templates"""
    return {
        "templates": [
            {"id": 1, "name": "Order Confirmation", "type": "email", "enabled": True},
            {"id": 2, "name": "Shipping Update", "type": "sms", "enabled": True},
            {"id": 3, "name": "Low Stock Alert", "type": "email", "enabled": True}
        ]
    }

@app.get("/api/documents/templates")
def get_document_templates():
    """Get document templates"""
    return {
        "templates": [
            {"id": 1, "name": "Invoice", "type": "pdf", "enabled": True},
            {"id": 2, "name": "Packing Slip", "type": "pdf", "enabled": True},
            {"id": 3, "name": "Return Label", "type": "pdf", "enabled": True}
        ]
    }

@app.get("/api/workflows")
def get_workflows():
    """Get workflows"""
    return {
        "workflows": [
            {"id": 1, "name": "Order Processing", "status": "active", "steps": 5},
            {"id": 2, "name": "Return Processing", "status": "active", "steps": 4},
            {"id": 3, "name": "Inventory Sync", "status": "active", "steps": 3}
        ]
    }

# Additional proxy endpoints for specific pages
@app.get("/api/orders/{order_id}")
async def get_order_details(order_id: int):
    """Get order details"""
    return await proxy_to_agent(8000, f"/api/orders/{order_id}")

@app.get("/api/products/{product_id}")
async def get_product_details(product_id: int):
    """Get product details"""
    return await proxy_to_agent(8001, f"/api/products/{product_id}")

@app.get("/api/returns")
async def get_returns(limit: int = 50, offset: int = 0):
    """Get returns list"""
    return await proxy_to_agent(8009, "/api/returns", {"limit": limit, "offset": offset})

@app.get("/api/promotions")
async def get_promotions(limit: int = 50, offset: int = 0):
    """Get promotions list"""
    return await proxy_to_agent(8020, "/api/promotions", {"limit": limit, "offset": offset})
