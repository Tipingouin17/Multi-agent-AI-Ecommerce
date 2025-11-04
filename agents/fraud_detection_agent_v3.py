"""
Fraud Detection Agent V3 - Production Ready with New Schema
Detects and prevents fraudulent transactions and activities
"""

import os
import sys
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Import shared modules
from shared.db_models import Order, Payment, Customer, User, Alert
from shared.db_connection import get_database_url
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create database engine
engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create FastAPI app
app = FastAPI(title="Fraud Detection Agent V3", version="3.0.0")

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

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class FraudCheckRequest(BaseModel):
    order_id: Optional[int] = None
    customer_id: Optional[int] = None
    payment_id: Optional[int] = None

class FraudRule(BaseModel):
    rule_name: str
    enabled: bool
    threshold: Optional[float] = None

# ============================================================================
# FRAUD DETECTION LOGIC
# ============================================================================

def calculate_fraud_score(order: Order, customer: Customer, db: Session) -> Dict:
    """Calculate fraud risk score for an order"""
    score = 0
    flags = []
    
    # Rule 1: High order value (>$1000)
    if order.total > 1000:
        score += 20
        flags.append("High order value")
    
    # Rule 2: New customer (created within 24 hours)
    if customer and customer.created_at:
        hours_since_registration = (datetime.utcnow() - customer.created_at).total_seconds() / 3600
        if hours_since_registration < 24:
            score += 30
            flags.append("New customer account")
    
    # Rule 3: Multiple orders in short time
    if customer:
        recent_orders = db.query(func.count(Order.id)).filter(
            and_(
                Order.customer_id == customer.id,
                Order.created_at >= datetime.utcnow() - timedelta(hours=1)
            )
        ).scalar()
        
        if recent_orders > 3:
            score += 40
            flags.append(f"Multiple orders in 1 hour ({recent_orders})")
    
    # Rule 4: Failed payment attempts
    if order:
        failed_payments = db.query(func.count(Payment.id)).filter(
            and_(
                Payment.order_id == order.id,
                Payment.status == "failed"
            )
        ).scalar()
        
        if failed_payments > 2:
            score += 25
            flags.append(f"Multiple failed payments ({failed_payments})")
    
    # Rule 5: Mismatched billing/shipping addresses
    if order.billing_address_id and order.shipping_address_id:
        if order.billing_address_id != order.shipping_address_id:
            score += 15
            flags.append("Different billing and shipping addresses")
    
    # Rule 6: Large quantity of items
    if order.order_items:
        total_quantity = sum(item.quantity for item in order.order_items)
        if total_quantity > 10:
            score += 10
            flags.append(f"Large quantity ({total_quantity} items)")
    
    # Determine risk level
    if score >= 70:
        risk_level = "high"
    elif score >= 40:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    return {
        "score": score,
        "risk_level": risk_level,
        "flags": flags,
        "requires_review": score >= 40
    }

# ============================================================================
# FRAUD DETECTION ENDPOINTS
# ============================================================================

@app.get("/health")
def health_check():
    return {"status": "healthy", "agent": "fraud_detection_agent_v3", "version": "3.0.0"}

@app.post("/api/fraud/check")
def check_fraud(request: FraudCheckRequest, db: Session = Depends(get_db)):
    """Check an order, customer, or payment for fraud"""
    try:
        order = None
        customer = None
        
        # Get order
        if request.order_id:
            order = db.query(Order).filter(Order.id == request.order_id).first()
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            customer = order.customer
        
        # Get customer
        elif request.customer_id:
            customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")
            # Get most recent order
            order = db.query(Order).filter(
                Order.customer_id == customer.id
            ).order_by(desc(Order.created_at)).first()
        
        # Get payment
        elif request.payment_id:
            payment = db.query(Payment).filter(Payment.id == request.payment_id).first()
            if not payment:
                raise HTTPException(status_code=404, detail="Payment not found")
            order = payment.order
            customer = order.customer if order else None
        
        if not order:
            raise HTTPException(status_code=400, detail="No order found to analyze")
        
        # Calculate fraud score
        fraud_analysis = calculate_fraud_score(order, customer, db)
        
        # Create alert if high risk
        if fraud_analysis["risk_level"] == "high":
            alert = Alert(
                alert_type="fraud_detection",
                severity="critical",
                title=f"High Fraud Risk: Order {order.order_number}",
                message=f"Fraud score: {fraud_analysis['score']}. Flags: {', '.join(fraud_analysis['flags'])}",
                source="fraud_detection_agent",
                status="active"
            )
            db.add(alert)
            db.commit()
        
        return {
            "order_id": order.id,
            "order_number": order.order_number,
            "customer_id": customer.id if customer else None,
            "fraud_analysis": fraud_analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking fraud: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/fraud/high-risk-orders")
def get_high_risk_orders(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get orders flagged as high risk"""
    try:
        # Get recent orders
        orders = db.query(Order).order_by(desc(Order.created_at)).limit(limit * 2).all()
        
        high_risk_orders = []
        for order in orders:
            customer = order.customer
            fraud_analysis = calculate_fraud_score(order, customer, db)
            
            if fraud_analysis["risk_level"] == "high":
                order_dict = order.to_dict()
                order_dict["fraud_analysis"] = fraud_analysis
                if customer and customer.user:
                    order_dict["customer"] = {
                        "id": customer.id,
                        "email": customer.user.email,
                        "name": f"{customer.user.first_name} {customer.user.last_name}"
                    }
                high_risk_orders.append(order_dict)
                
                if len(high_risk_orders) >= limit:
                    break
        
        return {
            "high_risk_orders": high_risk_orders,
            "count": len(high_risk_orders)
        }
    
    except Exception as e:
        logger.error(f"Error getting high risk orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/fraud/stats")
def get_fraud_stats(db: Session = Depends(get_db)):
    """Get fraud detection statistics"""
    try:
        # Get recent orders for analysis
        recent_orders = db.query(Order).filter(
            Order.created_at >= datetime.utcnow() - timedelta(days=30)
        ).all()
        
        total_orders = len(recent_orders)
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0
        
        for order in recent_orders:
            customer = order.customer
            fraud_analysis = calculate_fraud_score(order, customer, db)
            
            if fraud_analysis["risk_level"] == "high":
                high_risk_count += 1
            elif fraud_analysis["risk_level"] == "medium":
                medium_risk_count += 1
            else:
                low_risk_count += 1
        
        # Get fraud alerts
        fraud_alerts = db.query(func.count(Alert.id)).filter(
            and_(
                Alert.alert_type == "fraud_detection",
                Alert.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        ).scalar()
        
        return {
            "total_orders_analyzed": total_orders,
            "high_risk_orders": high_risk_count,
            "medium_risk_orders": medium_risk_count,
            "low_risk_orders": low_risk_count,
            "fraud_alerts": fraud_alerts,
            "high_risk_percentage": (high_risk_count / total_orders * 100) if total_orders > 0 else 0
        }
    
    except Exception as e:
        logger.error(f"Error getting fraud stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/fraud/rules")
def get_fraud_rules():
    """Get fraud detection rules"""
    return {
        "rules": [
            {
                "id": 1,
                "name": "High Order Value",
                "description": "Orders over $1000",
                "weight": 20,
                "enabled": True
            },
            {
                "id": 2,
                "name": "New Customer",
                "description": "Account created within 24 hours",
                "weight": 30,
                "enabled": True
            },
            {
                "id": 3,
                "name": "Multiple Orders",
                "description": "More than 3 orders in 1 hour",
                "weight": 40,
                "enabled": True
            },
            {
                "id": 4,
                "name": "Failed Payments",
                "description": "More than 2 failed payment attempts",
                "weight": 25,
                "enabled": True
            },
            {
                "id": 5,
                "name": "Address Mismatch",
                "description": "Different billing and shipping addresses",
                "weight": 15,
                "enabled": True
            },
            {
                "id": 6,
                "name": "Large Quantity",
                "description": "More than 10 items in order",
                "weight": 10,
                "enabled": True
            }
        ]
    }

@app.get("/api/fraud/customer/{customer_id}/risk")
def get_customer_risk_profile(customer_id: int, db: Session = Depends(get_db)):
    """Get fraud risk profile for a customer"""
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Get customer's orders
        orders = db.query(Order).filter(Order.customer_id == customer_id).all()
        
        if not orders:
            return {
                "customer_id": customer_id,
                "total_orders": 0,
                "risk_profile": "unknown",
                "message": "No order history available"
            }
        
        # Analyze all orders
        risk_scores = []
        for order in orders:
            fraud_analysis = calculate_fraud_score(order, customer, db)
            risk_scores.append(fraud_analysis["score"])
        
        avg_risk_score = sum(risk_scores) / len(risk_scores)
        max_risk_score = max(risk_scores)
        
        # Determine overall risk profile
        if avg_risk_score >= 50 or max_risk_score >= 70:
            risk_profile = "high"
        elif avg_risk_score >= 30:
            risk_profile = "medium"
        else:
            risk_profile = "low"
        
        return {
            "customer_id": customer_id,
            "total_orders": len(orders),
            "average_risk_score": round(avg_risk_score, 2),
            "max_risk_score": max_risk_score,
            "risk_profile": risk_profile,
            "account_age_days": (datetime.utcnow() - customer.created_at).days if customer.created_at else 0
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer risk profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8010))
    uvicorn.run(app, host="0.0.0.0", port=port)
