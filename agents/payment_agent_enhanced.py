"""
Payment Agent Enhanced - Multi-Agent E-Commerce System

This agent provides comprehensive payment processing including gateway management,
payment methods, transactions, refunds, authorizations, and fraud detection.
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID
from enum import Enum

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
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

class GatewayType(str, Enum):
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    BANK_TRANSFER = "bank_transfer"
    CRYPTO = "crypto"
    WALLET = "wallet"


class TransactionType(str, Enum):
    AUTHORIZE = "authorize"
    CAPTURE = "capture"
    SALE = "sale"
    REFUND = "refund"
    VOID = "void"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class RefundType(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    CHARGEBACK = "chargeback"


class RefundStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =====================================================
# PYDANTIC MODELS
# =====================================================

class PaymentGateway(BaseModel):
    gateway_id: int
    gateway_name: str
    gateway_type: GatewayType
    is_active: bool = True
    is_test_mode: bool = False
    supported_currencies: List[str] = ["USD"]
    transaction_fee_percent: Decimal = Decimal("0.00")
    transaction_fee_fixed: Decimal = Decimal("0.00")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentMethodCreate(BaseModel):
    customer_id: str
    gateway_id: int
    method_type: str
    is_default: bool = False
    
    # Card details (will be tokenized)
    card_last_four: Optional[str] = None
    card_brand: Optional[str] = None
    card_expiry_month: Optional[int] = None
    card_expiry_year: Optional[int] = None
    card_holder_name: Optional[str] = None
    
    # Gateway token
    gateway_token: Optional[str] = None
    gateway_customer_id: Optional[str] = None


class PaymentMethod(PaymentMethodCreate):
    method_id: UUID
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentTransactionCreate(BaseModel):
    order_id: Optional[str] = None
    customer_id: str
    payment_method_id: Optional[UUID] = None
    gateway_id: int
    transaction_type: TransactionType
    amount: Decimal
    currency: str = "USD"


class PaymentTransaction(PaymentTransactionCreate):
    transaction_id: UUID
    transaction_status: TransactionStatus = TransactionStatus.PENDING
    fee_amount: Decimal = Decimal("0.00")
    net_amount: Optional[Decimal] = None
    gateway_transaction_id: Optional[str] = None
    authorization_code: Optional[str] = None
    risk_score: Optional[Decimal] = None
    risk_level: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    initiated_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentRefundCreate(BaseModel):
    transaction_id: UUID
    order_id: Optional[str] = None
    customer_id: str
    refund_type: RefundType
    refund_reason: Optional[str] = None
    refund_amount: Decimal
    currency: str = "USD"
    notes: Optional[str] = None
    requested_by: Optional[str] = None


class PaymentRefund(PaymentRefundCreate):
    refund_id: UUID
    refund_status: RefundStatus = RefundStatus.PENDING
    gateway_refund_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    requested_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentAuthorizationCreate(BaseModel):
    order_id: str
    customer_id: str
    payment_method_id: Optional[UUID] = None
    gateway_id: int
    authorization_amount: Decimal
    currency: str = "USD"


class PaymentAuthorization(PaymentAuthorizationCreate):
    authorization_id: UUID
    authorization_code: Optional[str] = None
    authorization_status: str = "pending"
    captured_amount: Decimal = Decimal("0.00")
    remaining_amount: Optional[Decimal] = None
    gateway_authorization_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    authorized_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# REPOSITORY
# =====================================================

class PaymentRepository:
    """Repository for payment operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def get_active_gateways(self) -> List[PaymentGateway]:
        """Get all active payment gateways."""
        query = "SELECT * FROM payment_gateways WHERE is_active = true ORDER BY gateway_name"
        results = await self.db.fetch_all(query)
        return [PaymentGateway(**r) for r in results]
    
    async def get_gateway(self, gateway_id: int) -> Optional[PaymentGateway]:
        """Get payment gateway by ID."""
        query = "SELECT * FROM payment_gateways WHERE gateway_id = $1"
        result = await self.db.fetch_one(query, gateway_id)
        return PaymentGateway(**result) if result else None
    
    async def create_payment_method(
        self,
        payment_method: PaymentMethodCreate
    ) -> PaymentMethod:
        """Create a new payment method."""
        query = """
            INSERT INTO payment_methods (customer_id, gateway_id, method_type, is_default,
                                        card_last_four, card_brand, card_expiry_month,
                                        card_expiry_year, card_holder_name, gateway_token,
                                        gateway_customer_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING *
        """
        result = await self.db.fetch_one(
            query, payment_method.customer_id, payment_method.gateway_id,
            payment_method.method_type, payment_method.is_default,
            payment_method.card_last_four, payment_method.card_brand,
            payment_method.card_expiry_month, payment_method.card_expiry_year,
            payment_method.card_holder_name, payment_method.gateway_token,
            payment_method.gateway_customer_id
        )
        return PaymentMethod(**result)
    
    async def get_customer_payment_methods(
        self,
        customer_id: str
    ) -> List[PaymentMethod]:
        """Get all payment methods for a customer."""
        query = """
            SELECT * FROM payment_methods 
            WHERE customer_id = $1 
            ORDER BY is_default DESC, created_at DESC
        """
        results = await self.db.fetch_all(query, customer_id)
        return [PaymentMethod(**r) for r in results]
    
    async def create_transaction(
        self,
        transaction: PaymentTransactionCreate
    ) -> PaymentTransaction:
        """Create a new payment transaction."""
        query = """
            INSERT INTO payment_transactions (order_id, customer_id, payment_method_id,
                                             gateway_id, transaction_type, amount, currency)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
        """
        result = await self.db.fetch_one(
            query, transaction.order_id, transaction.customer_id,
            transaction.payment_method_id, transaction.gateway_id,
            transaction.transaction_type.value, transaction.amount,
            transaction.currency
        )
        return PaymentTransaction(**result)
    
    async def update_transaction_status(
        self,
        transaction_id: UUID,
        status: TransactionStatus,
        gateway_transaction_id: Optional[str] = None,
        authorization_code: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[PaymentTransaction]:
        """Update transaction status."""
        query = """
            UPDATE payment_transactions 
            SET transaction_status = $2,
                gateway_transaction_id = COALESCE($3, gateway_transaction_id),
                authorization_code = COALESCE($4, authorization_code),
                error_code = $5,
                error_message = $6,
                completed_at = CASE WHEN $2 IN ('completed', 'failed', 'cancelled') 
                                    THEN CURRENT_TIMESTAMP ELSE completed_at END
            WHERE transaction_id = $1
            RETURNING *
        """
        result = await self.db.fetch_one(
            query, transaction_id, status.value, gateway_transaction_id,
            authorization_code, error_code, error_message
        )
        return PaymentTransaction(**result) if result else None
    
    async def get_transaction(self, transaction_id: UUID) -> Optional[PaymentTransaction]:
        """Get transaction by ID."""
        query = "SELECT * FROM payment_transactions WHERE transaction_id = $1"
        result = await self.db.fetch_one(query, transaction_id)
        return PaymentTransaction(**result) if result else None
    
    async def create_refund(self, refund: PaymentRefundCreate) -> PaymentRefund:
        """Create a new refund."""
        query = """
            INSERT INTO payment_refunds (transaction_id, order_id, customer_id, refund_type,
                                        refund_reason, refund_amount, currency, notes, requested_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
        """
        result = await self.db.fetch_one(
            query, refund.transaction_id, refund.order_id, refund.customer_id,
            refund.refund_type.value, refund.refund_reason, refund.refund_amount,
            refund.currency, refund.notes, refund.requested_by
        )
        return PaymentRefund(**result)
    
    async def update_refund_status(
        self,
        refund_id: UUID,
        status: RefundStatus,
        gateway_refund_id: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[PaymentRefund]:
        """Update refund status."""
        query = """
            UPDATE payment_refunds 
            SET refund_status = $2,
                gateway_refund_id = COALESCE($3, gateway_refund_id),
                error_code = $4,
                error_message = $5,
                completed_at = CASE WHEN $2 IN ('completed', 'failed', 'cancelled') 
                                   THEN CURRENT_TIMESTAMP ELSE completed_at END
            WHERE refund_id = $1
            RETURNING *
        """
        result = await self.db.fetch_one(
            query, refund_id, status.value, gateway_refund_id,
            error_code, error_message
        )
        return PaymentRefund(**result) if result else None
    
    async def create_authorization(
        self,
        authorization: PaymentAuthorizationCreate
    ) -> PaymentAuthorization:
        """Create a new payment authorization."""
        query = """
            INSERT INTO payment_authorizations (order_id, customer_id, payment_method_id,
                                               gateway_id, authorization_amount, currency,
                                               expires_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
        """
        expires_at = datetime.utcnow() + timedelta(days=7)  # 7 days expiry
        result = await self.db.fetch_one(
            query, authorization.order_id, authorization.customer_id,
            authorization.payment_method_id, authorization.gateway_id,
            authorization.authorization_amount, authorization.currency, expires_at
        )
        return PaymentAuthorization(**result)


# =====================================================
# SERVICE
# =====================================================

class PaymentService:
    """Service for payment operations."""
    
    def __init__(self, repo: PaymentRepository):
        self.repo = repo
    
    async def process_payment(
        self,
        transaction_data: PaymentTransactionCreate
    ) -> Dict[str, Any]:
        """Process a payment transaction."""
        # Get gateway
        gateway = await self.repo.get_gateway(transaction_data.gateway_id)
        if not gateway:
            raise ValueError(f"Gateway {transaction_data.gateway_id} not found")
        
        if not gateway.is_active:
            raise ValueError(f"Gateway {gateway.gateway_name} is not active")
        
        # Create transaction
        transaction = await self.repo.create_transaction(transaction_data)
        
        # Calculate fees
        fee_amount = (
            transaction.amount * gateway.transaction_fee_percent / 100 +
            gateway.transaction_fee_fixed
        )
        net_amount = transaction.amount - fee_amount
        
        # Simulate payment processing
        # In production, this would call the actual gateway API
        try:
            # Simulate gateway call
            gateway_transaction_id = f"TXN-{uuid4().hex[:12].upper()}"
            authorization_code = f"AUTH-{uuid4().hex[:8].upper()}"
            
            # Update transaction as completed
            transaction = await self.repo.update_transaction_status(
                transaction.transaction_id,
                TransactionStatus.COMPLETED,
                gateway_transaction_id=gateway_transaction_id,
                authorization_code=authorization_code
            )
            
            logger.info(
                "payment_processed",
                transaction_id=str(transaction.transaction_id),
                amount=float(transaction.amount),
                gateway=gateway.gateway_name
            )
            
            return {
                "transaction": transaction,
                "success": True,
                "message": "Payment processed successfully"
            }
            
        except Exception as e:
            # Update transaction as failed
            transaction = await self.repo.update_transaction_status(
                transaction.transaction_id,
                TransactionStatus.FAILED,
                error_code="PROCESSING_ERROR",
                error_message=str(e)
            )
            
            logger.error(
                "payment_failed",
                transaction_id=str(transaction.transaction_id),
                error=str(e)
            )
            
            raise ValueError(f"Payment processing failed: {str(e)}")
    
    async def process_refund(
        self,
        refund_data: PaymentRefundCreate
    ) -> Dict[str, Any]:
        """Process a refund."""
        # Get original transaction
        transaction = await self.repo.get_transaction(refund_data.transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {refund_data.transaction_id} not found")
        
        if transaction.transaction_status != TransactionStatus.COMPLETED:
            raise ValueError("Can only refund completed transactions")
        
        # Create refund
        refund = await self.repo.create_refund(refund_data)
        
        # Simulate refund processing
        try:
            gateway_refund_id = f"REF-{uuid4().hex[:12].upper()}"
            
            # Update refund as completed
            refund = await self.repo.update_refund_status(
                refund.refund_id,
                RefundStatus.COMPLETED,
                gateway_refund_id=gateway_refund_id
            )
            
            logger.info(
                "refund_processed",
                refund_id=str(refund.refund_id),
                amount=float(refund.refund_amount)
            )
            
            return {
                "refund": refund,
                "success": True,
                "message": "Refund processed successfully"
            }
            
        except Exception as e:
            # Update refund as failed
            refund = await self.repo.update_refund_status(
                refund.refund_id,
                RefundStatus.FAILED,
                error_code="REFUND_ERROR",
                error_message=str(e)
            )
            
            logger.error(
                "refund_failed",
                refund_id=str(refund.refund_id),
                error=str(e)
            )
            
            raise ValueError(f"Refund processing failed: {str(e)}")


# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI(
    title="Payment Agent Enhanced API",
    description="Comprehensive payment processing for multi-agent e-commerce",
    version="1.0.0"
)


async def get_payment_service() -> PaymentService:
    """Dependency injection for payment service."""
    db_manager = await get_database_manager()
    repo = PaymentRepository(db_manager)
    return PaymentService(repo)


# =====================================================
# API ENDPOINTS
# =====================================================

@app.get("/api/v1/payment/gateways", response_model=List[PaymentGateway])
async def get_payment_gateways(
    service: PaymentService = Depends(get_payment_service)
):
    """Get all active payment gateways."""
    try:
        gateways = await service.repo.get_active_gateways()
        return gateways
    except Exception as e:
        logger.error("get_gateways_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/payment/methods", response_model=PaymentMethod)
async def create_payment_method(
    payment_method: PaymentMethodCreate = Body(...),
    service: PaymentService = Depends(get_payment_service)
):
    """Create a new payment method."""
    try:
        result = await service.repo.create_payment_method(payment_method)
        return result
    except Exception as e:
        logger.error("create_payment_method_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/payment/methods/{customer_id}", response_model=List[PaymentMethod])
async def get_customer_payment_methods(
    customer_id: str = Path(...),
    service: PaymentService = Depends(get_payment_service)
):
    """Get all payment methods for a customer."""
    try:
        methods = await service.repo.get_customer_payment_methods(customer_id)
        return methods
    except Exception as e:
        logger.error("get_payment_methods_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/payment/process", response_model=Dict[str, Any])
async def process_payment(
    transaction: PaymentTransactionCreate = Body(...),
    service: PaymentService = Depends(get_payment_service)
):
    """Process a payment transaction."""
    try:
        result = await service.process_payment(transaction)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("process_payment_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/payment/transactions/{transaction_id}", response_model=PaymentTransaction)
async def get_transaction(
    transaction_id: UUID = Path(...),
    service: PaymentService = Depends(get_payment_service)
):
    """Get transaction by ID."""
    try:
        transaction = await service.repo.get_transaction(transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return transaction
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_transaction_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/payment/refund", response_model=Dict[str, Any])
async def process_refund(
    refund: PaymentRefundCreate = Body(...),
    service: PaymentService = Depends(get_payment_service)
):
    """Process a refund."""
    try:
        result = await service.process_refund(refund)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("process_refund_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/payment/authorize", response_model=PaymentAuthorization)
async def authorize_payment(
    authorization: PaymentAuthorizationCreate = Body(...),
    service: PaymentService = Depends(get_payment_service)
):
    """Authorize a payment (hold funds)."""
    try:
        result = await service.repo.create_authorization(authorization)
        return result
    except Exception as e:
        logger.error("authorize_payment_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "payment_agent_enhanced", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)

