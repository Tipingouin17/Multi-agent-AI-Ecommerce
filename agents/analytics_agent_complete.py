from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
"""
Analytics Agent - Multi-Agent E-Commerce System

This agent provides comprehensive analytics and reporting across all business areas.

DATABASE SCHEMA (to be created via migration 009):

-- Sales Analytics
CREATE TABLE sales_analytics (
    analytics_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'monthly', 'yearly'
    
    -- Metrics
    total_orders INTEGER DEFAULT 0,
    total_revenue DECIMAL(15, 2) DEFAULT 0.00,
    total_items_sold INTEGER DEFAULT 0,
    average_order_value DECIMAL(10, 2) DEFAULT 0.00,
    
    -- Customer metrics
    new_customers INTEGER DEFAULT 0,
    returning_customers INTEGER DEFAULT 0,
    
    -- Product metrics
    top_products JSONB DEFAULT '[]',
    top_categories JSONB DEFAULT '[]',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer Analytics
CREATE TABLE customer_analytics (
    analytics_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Metrics
    total_customers INTEGER DEFAULT 0,
    active_customers INTEGER DEFAULT 0,
    customer_lifetime_value DECIMAL(10, 2) DEFAULT 0.00,
    customer_acquisition_cost DECIMAL(10, 2) DEFAULT 0.00,
    churn_rate DECIMAL(5, 2) DEFAULT 0.00,
    
    -- Segments
    customer_segments JSONB DEFAULT '[]',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product Analytics
CREATE TABLE product_analytics (
    analytics_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(100) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Metrics
    units_sold INTEGER DEFAULT 0,
    revenue DECIMAL(15, 2) DEFAULT 0.00,
    views INTEGER DEFAULT 0,
    conversion_rate DECIMAL(5, 2) DEFAULT 0.00,
    average_rating DECIMAL(3, 2) DEFAULT 0.00,
    review_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inventory Analytics
CREATE TABLE inventory_analytics (
    analytics_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Metrics
    total_stock_value DECIMAL(15, 2) DEFAULT 0.00,
    stockout_incidents INTEGER DEFAULT 0,
    inventory_turnover DECIMAL(5, 2) DEFAULT 0.00,
    dead_stock_value DECIMAL(15, 2) DEFAULT 0.00,
    
    -- Top movers
    fast_moving_products JSONB DEFAULT '[]',
    slow_moving_products JSONB DEFAULT '[]',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payment Analytics
CREATE TABLE payment_analytics (
    analytics_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Metrics
    total_transactions INTEGER DEFAULT 0,
    successful_transactions INTEGER DEFAULT 0,
    failed_transactions INTEGER DEFAULT 0,
    total_amount DECIMAL(15, 2) DEFAULT 0.00,
    average_transaction_value DECIMAL(10, 2) DEFAULT 0.00,
    
    -- By payment method
    payment_methods JSONB DEFAULT '[]',
    
    -- Refunds
    total_refunds INTEGER DEFAULT 0,
    refund_amount DECIMAL(15, 2) DEFAULT 0.00,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shipping Analytics
CREATE TABLE shipping_analytics (
    analytics_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Metrics
    total_shipments INTEGER DEFAULT 0,
    on_time_deliveries INTEGER DEFAULT 0,
    late_deliveries INTEGER DEFAULT 0,
    failed_deliveries INTEGER DEFAULT 0,
    average_delivery_days DECIMAL(5, 2) DEFAULT 0.00,
    
    -- By carrier
    carrier_performance JSONB DEFAULT '[]',
    
    -- Costs
    total_shipping_cost DECIMAL(15, 2) DEFAULT 0.00,
    average_shipping_cost DECIMAL(10, 2) DEFAULT 0.00,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

"""

import asyncio
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID
from enum import Enum

from shared.db_helpers import DatabaseHelper

from fastapi import FastAPI, HTTPException, Depends, Query, Path
from pydantic import BaseModel, Field
import structlog
import sys
import os

# Path setup
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.database import DatabaseManager, get_database_manager


logger = structlog.get_logger(__name__)


# =====================================================
# ENUMS
# =====================================================

class PeriodType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

    async def initialize(self):
        """Initialize agent."""
        await super().initialize()
        
    async def cleanup(self):
        """Cleanup agent."""
        await super().cleanup()
        
    async def process_business_logic(self, data):
        """Process business logic."""
        return {"status": "success"}


class AnalyticsType(str, Enum):
    SALES = "sales"
    CUSTOMER = "customer"
    PRODUCT = "product"
    INVENTORY = "inventory"
    PAYMENT = "payment"
    SHIPPING = "shipping"


# =====================================================
# PYDANTIC MODELS
# =====================================================

class SalesAnalytics(BaseModel):
    analytics_id: UUID
    period_start: date
    period_end: date
    period_type: PeriodType
    total_orders: int = 0
    total_revenue: Decimal = Decimal("0.00")
    total_items_sold: int = 0
    average_order_value: Decimal = Decimal("0.00")
    new_customers: int = 0
    returning_customers: int = 0
    top_products: List[Dict[str, Any]] = []
    top_categories: List[Dict[str, Any]] = []
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerAnalytics(BaseModel):
    analytics_id: UUID
    period_start: date
    period_end: date
    total_customers: int = 0
    active_customers: int = 0
    customer_lifetime_value: Decimal = Decimal("0.00")
    customer_acquisition_cost: Decimal = Decimal("0.00")
    churn_rate: Decimal = Decimal("0.00")
    customer_segments: List[Dict[str, Any]] = []
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardMetrics(BaseModel):
    """Real-time dashboard metrics."""
    period: str
    sales: Dict[str, Any]
    customers: Dict[str, Any]
    inventory: Dict[str, Any]
    shipping: Dict[str, Any]
    generated_at: datetime


# =====================================================
# REPOSITORY
# =====================================================

class AnalyticsRepository:
    """Repository for analytics operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def get_sales_analytics(
        self,
        start_date: date,
        end_date: date
    ) -> Optional[SalesAnalytics]:
        """Get sales analytics for a period."""
        # In production, query from sales_analytics table
        # For now, calculate from orders
        query = """
            SELECT 
                COUNT(DISTINCT order_id) as total_orders,
                COALESCE(SUM(total_amount), 0) as total_revenue,
                COALESCE(SUM(total_quantity), 0) as total_items_sold,
                COALESCE(AVG(total_amount), 0) as average_order_value
            FROM orders
            WHERE created_at BETWEEN $1 AND $2
        """
        result = await self.db.fetch_one(query, start_date, end_date)
        
        if result:
            return SalesAnalytics(
                analytics_id=uuid4(),
                period_start=start_date,
                period_end=end_date,
                period_type=PeriodType.DAILY,
                total_orders=result['total_orders'] or 0,
                total_revenue=Decimal(str(result['total_revenue'] or 0)),
                total_items_sold=result['total_items_sold'] or 0,
                average_order_value=Decimal(str(result['average_order_value'] or 0)),
                created_at=datetime.utcnow()
            )
        if not self._db_initialized:
            return None
        
        async with self.db_manager.get_session() as session:
            record = await self.db_helper.get_by_id(session, OrderDB, record_id)
            return self.db_helper.to_dict(record) if record else None
    
    async def get_customer_analytics(
        self,
        start_date: date,
        end_date: date
    ) -> Optional[CustomerAnalytics]:
        """Get customer analytics for a period."""
        # In production, query from customer_analytics table
        query = """
            SELECT 
                COUNT(DISTINCT customer_id) as total_customers
            FROM customers
            WHERE created_at BETWEEN $1 AND $2
        """
        result = await self.db.fetch_one(query, start_date, end_date)
        
        if result:
            return CustomerAnalytics(
                analytics_id=uuid4(),
                period_start=start_date,
                period_end=end_date,
                total_customers=result['total_customers'] or 0,
                created_at=datetime.utcnow()
            )
        if not self._db_initialized:
            return None
        
        async with self.db_manager.get_session() as session:
            record = await self.db_helper.get_by_id(session, OrderDB, record_id)
            return self.db_helper.to_dict(record) if record else None
    
    async def get_dashboard_metrics(self) -> DashboardMetrics:
        """Get real-time dashboard metrics."""
        today = date.today()
        week_ago = today - timedelta(days=7)
        
        # Sales metrics
        sales = await self.get_sales_analytics(week_ago, today)
        
        # Customer metrics
        customers = await self.get_customer_analytics(week_ago, today)
        
        return DashboardMetrics(
            period="last_7_days",
            sales={
                "total_orders": sales.total_orders if sales else 0,
                "total_revenue": float(sales.total_revenue) if sales else 0.0,
                "average_order_value": float(sales.average_order_value) if sales else 0.0
            },
            customers={
                "total_customers": customers.total_customers if customers else 0,
                "active_customers": customers.active_customers if customers else 0
            },
            inventory={
                "total_stock_value": 0.0,
                "stockout_incidents": 0
            },
            shipping={
                "total_shipments": 0,
                "on_time_rate": 0.0
            },
            generated_at=datetime.utcnow()
        )


# =====================================================
# SERVICE
# =====================================================

class AnalyticsService:
    """Service for analytics operations."""
    
    def __init__(self, repo: AnalyticsRepository):
        self.repo = repo
    
    async def generate_sales_report(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Generate sales report."""
        analytics = await self.repo.get_sales_analytics(start_date, end_date)
        
        if not analytics:
            return {
                "period": {"start": start_date, "end": end_date},
                "metrics": {},
                "message": "No data available for this period"
            }
        
        return {
            "period": {"start": start_date, "end": end_date},
            "metrics": {
                "total_orders": analytics.total_orders,
                "total_revenue": float(analytics.total_revenue),
                "total_items_sold": analytics.total_items_sold,
                "average_order_value": float(analytics.average_order_value)
            },
            "top_products": analytics.top_products,
            "top_categories": analytics.top_categories
        }
    
    async def generate_customer_report(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Generate customer report."""
        analytics = await self.repo.get_customer_analytics(start_date, end_date)
        
        if not analytics:
            return {
                "period": {"start": start_date, "end": end_date},
                "metrics": {},
                "message": "No data available for this period"
            }
        
        return {
            "period": {"start": start_date, "end": end_date},
            "metrics": {
                "total_customers": analytics.total_customers,
                "active_customers": analytics.active_customers,
                "customer_lifetime_value": float(analytics.customer_lifetime_value),
                "churn_rate": float(analytics.churn_rate)
            },
            "segments": analytics.customer_segments
        }


# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI(
    title="Analytics Agent API",
    description="Comprehensive analytics and reporting",
    version="1.0.0"
)


async def get_analytics_service() -> AnalyticsService:
    """Dependency injection for analytics service."""
    db_manager = await get_database_manager()
    repo = AnalyticsRepository(db_manager)
    return AnalyticsService(repo)


# =====================================================
# API ENDPOINTS
# =====================================================

@app.get("/api/v1/analytics/dashboard", response_model=DashboardMetrics)
async def get_dashboard(
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get real-time dashboard metrics."""
    try:
        metrics = await service.repo.get_dashboard_metrics()
        return metrics
    except Exception as e:
        logger.error("get_dashboard_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analytics/sales", response_model=Dict[str, Any])
async def get_sales_analytics(
    start_date: date = Query(...),
    end_date: date = Query(...),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get sales analytics report."""
    try:
        report = await service.generate_sales_report(start_date, end_date)
        return report
    except Exception as e:
        logger.error("get_sales_analytics_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analytics/customers", response_model=Dict[str, Any])
async def get_customer_analytics(
    start_date: date = Query(...),
    end_date: date = Query(...),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get customer analytics report."""
    try:
        report = await service.generate_customer_report(start_date, end_date)
        return report
    except Exception as e:
        logger.error("get_customer_analytics_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "analytics_agent", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)

