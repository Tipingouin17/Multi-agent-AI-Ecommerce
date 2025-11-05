"""
Payment Agent V3 - Production Ready with New Schema
Manages payment processing, transactions, and payment methods
"""

import os
import sys
import logging
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import hashlib

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
from shared.db_models import Payment, Order, Customer
from shared.db_connection import get_database_url
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create database engine
engine = create_engine(get_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create FastAPI app
app = FastAPI(title="Payment Agent V3", version="3.0.0")

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

class PaymentCreate(BaseModel):
    order_id: int
    payment_method: str  # credit_card, debit_card, paypal, stripe, etc.
    amount: float
    currency: str = "USD"
    card_last4: Optional[str] = None
    card_brand: Optional[str] = None

class PaymentRefund(BaseModel):
    amount: float
    reason: str

# ============================================================================
# PAYMENT ENDPOINTS
# ============================================================================

@app.get("/health")
def health_check():
    return {"status": "healthy", "agent": "payment_agent_v3", "version": "3.0.0"}

@app.get("/api/payments")
def get_payments(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    payment_method: Optional[str] = None,
    order_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all payments with filtering"""
    try:
        query = db.query(Payment)
        
        if status:
            query = query.filter(Payment.status == status)
        if payment_method:
            query = query.filter(Payment.payment_method == payment_method)
        if order_id:
            query = query.filter(Payment.order_id == order_id)
        
        total = query.count()
        offset = (page - 1) * limit
        payments = query.order_by(desc(Payment.created_at)).offset(offset).limit(limit).all()
        
        result = []
        for payment in payments:
            payment_dict = payment.to_dict()
            if payment.order:
                payment_dict['order'] = {
                    'id': payment.order.id,
                    'order_number': payment.order.order_number,
                    'total': float(payment.order.total)
                }
            result.append(payment_dict)
        
        return {
            "payments": result,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting payments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/payments/stats")
def get_payment_stats(db: Session = Depends(get_db)):
    """Get payment statistics"""
    try:
        total_payments = db.query(func.count(Payment.id)).scalar()
        
        completed_payments = db.query(func.count(Payment.id)).filter(
            Payment.status == "completed"
        ).scalar()
        
        total_revenue = db.query(func.sum(Payment.amount)).filter(
            Payment.status == "completed"
        ).scalar() or 0
        
        total_refunded = db.query(func.sum(Payment.refunded_amount)).scalar() or 0
        
        # Payment method distribution
        payment_methods = db.query(
            Payment.payment_method,
            func.count(Payment.id)
        ).group_by(Payment.payment_method).all()
        
        method_distribution = {method: count for method, count in payment_methods}
        
        # Status distribution
        status_stats = db.query(
            Payment.status,
            func.count(Payment.id)
        ).group_by(Payment.status).all()
        
        status_distribution = {status: count for status, count in status_stats}
        
        return {
            "total_payments": total_payments,
            "completed_payments": completed_payments,
            "total_revenue": float(total_revenue),
            "total_refunded": float(total_refunded),
            "net_revenue": float(total_revenue - total_refunded),
            "success_rate": (completed_payments / total_payments * 100) if total_payments > 0 else 0,
            "payment_method_distribution": method_distribution,
            "status_distribution": status_distribution
        }
    
    except Exception as e:
        logger.error(f"Error getting payment stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/payments/methods")
def get_payment_methods():
    """Get available payment methods"""
    return {
        "payment_methods": [
            {"id": "credit_card", "name": "Credit Card", "enabled": True},
            {"id": "debit_card", "name": "Debit Card", "enabled": True},
            {"id": "paypal", "name": "PayPal", "enabled": True},
            {"id": "stripe", "name": "Stripe", "enabled": True},
            {"id": "bank_transfer", "name": "Bank Transfer", "enabled": True},
            {"id": "cash_on_delivery", "name": "Cash on Delivery", "enabled": False}
        ]
    }

@app.get("/api/payments/{payment_id}")
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    """Get a single payment by ID"""
    try:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        payment_dict = payment.to_dict()
        if payment.order:
            payment_dict['order'] = payment.order.to_dict()
        
        return payment_dict
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/payments")
def create_payment(payment_data: PaymentCreate, db: Session = Depends(get_db)):
    """Process a new payment"""
    try:
        # Verify order exists
        order = db.query(Order).filter(Order.id == payment_data.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Check if order already has a successful payment
        existing_payment = db.query(Payment).filter(
            and_(
                Payment.order_id == payment_data.order_id,
                Payment.status == "completed"
            )
        ).first()
        
        if existing_payment:
            raise HTTPException(status_code=400, detail="Order already paid")
        
        # Generate transaction ID
        transaction_id = hashlib.sha256(
            f"{payment_data.order_id}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16].upper()
        
        # Create payment record
        payment = Payment(
            order_id=payment_data.order_id,
            transaction_id=transaction_id,
            payment_method=payment_data.payment_method,
            amount=Decimal(str(payment_data.amount)),
            currency=payment_data.currency,
            status="processing"
        )
        
        db.add(payment)
        db.flush()
        
        # Simulate payment processing
        # In production, this would call payment gateway APIs (Stripe, PayPal, etc.)
        try:
            # Simulate payment gateway call
            payment_successful = True  # In production: call actual gateway
            
            if payment_successful:
                payment.status = "completed"
                payment.paid_at = datetime.utcnow()
                
                # Update order payment status
                order.payment_status = "paid"
                order.status = "confirmed"
                order.confirmed_at = datetime.utcnow()
                
                logger.info(f"Payment {transaction_id} completed successfully")
            else:
                payment.status = "failed"
                payment.error_message = "Payment declined by gateway"
                logger.warning(f"Payment {transaction_id} failed")
        
        except Exception as gateway_error:
            payment.status = "failed"
            payment.error_message = str(gateway_error)
            logger.error(f"Payment gateway error: {gateway_error}")
        
        db.commit()
        db.refresh(payment)
        
        return payment.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/payments/{payment_id}/refund")
def refund_payment(
    payment_id: int,
    refund_data: PaymentRefund,
    db: Session = Depends(get_db)
):
    """Refund a payment"""
    try:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        if payment.status != "completed":
            raise HTTPException(status_code=400, detail="Can only refund completed payments")
        
        if payment.refunded_amount and payment.refunded_amount >= payment.amount:
            raise HTTPException(status_code=400, detail="Payment already fully refunded")
        
        refund_amount = Decimal(str(refund_data.amount))
        current_refunded = payment.refunded_amount or Decimal('0')
        
        if current_refunded + refund_amount > payment.amount:
            raise HTTPException(status_code=400, detail="Refund amount exceeds payment amount")
        
        # Process refund (in production: call payment gateway)
        payment.refunded_amount = current_refunded + refund_amount
        payment.updated_at = datetime.utcnow()
        
        # Update status
        if payment.refunded_amount >= payment.amount:
            payment.status = "refunded"
            if payment.order:
                payment.order.payment_status = "refunded"
        else:
            payment.status = "partially_refunded"
            if payment.order:
                payment.order.payment_status = "partially_refunded"
        
        db.commit()
        db.refresh(payment)
        
        return {
            "message": "Refund processed successfully",
            "payment": payment.to_dict(),
            "refund": {
                "amount": float(refund_amount),
                "reason": refund_data.reason,
                "total_refunded": float(payment.refunded_amount)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing refund: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/payments/{payment_id}/capture")
def capture_payment(payment_id: int, db: Session = Depends(get_db)):
    """Capture an authorized payment"""
    try:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        if payment.status != "authorized":
            raise HTTPException(status_code=400, detail="Payment not in authorized state")
        
        # Capture payment (in production: call payment gateway)
        payment.status = "completed"
        payment.paid_at = datetime.utcnow()
        
        if payment.order:
            payment.order.payment_status = "paid"
            payment.order.status = "confirmed"
            payment.order.confirmed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(payment)
        
        return payment.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error capturing payment: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/payments/{payment_id}/cancel")
def cancel_payment(payment_id: int, db: Session = Depends(get_db)):
    """Cancel a pending/processing payment"""
    try:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        if payment.status not in ["pending", "processing", "authorized"]:
            raise HTTPException(status_code=400, detail="Cannot cancel payment in current state")
        
        payment.status = "cancelled"
        payment.updated_at = datetime.utcnow()
        
        if payment.order:
            payment.order.payment_status = "cancelled"
        
        db.commit()
        db.refresh(payment)
        
        return payment.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling payment: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
