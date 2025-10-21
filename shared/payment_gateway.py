"""
Payment Gateway Integration (Simulated Stripe)
Handles payment processing, refunds, and merchant payouts
"""

import os
import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum
from pydantic import BaseModel, Field
from decimal import Decimal
import secrets
import hashlib

logger = structlog.get_logger(__name__)


class PaymentStatus(str, Enum):
    """Payment status"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentMethod(str, Enum):
    """Payment method types"""
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"


class RefundReason(str, Enum):
    """Refund reason"""
    REQUESTED_BY_CUSTOMER = "requested_by_customer"
    FRAUDULENT = "fraudulent"
    DUPLICATE = "duplicate"
    PRODUCT_DEFECT = "product_defect"
    ORDER_CANCELLED = "order_cancelled"


class PaymentIntent(BaseModel):
    """Payment intent model"""
    payment_intent_id: str = Field(default_factory=lambda: f"pi_{secrets.token_hex(12)}")
    amount: Decimal
    currency: str = "EUR"
    customer_id: Optional[str] = None
    order_id: Optional[str] = None
    payment_method: PaymentMethod
    status: PaymentStatus = PaymentStatus.PENDING
    description: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Refund(BaseModel):
    """Refund model"""
    refund_id: str = Field(default_factory=lambda: f"re_{secrets.token_hex(12)}")
    payment_intent_id: str
    amount: Decimal
    currency: str = "EUR"
    reason: RefundReason
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None


class Payout(BaseModel):
    """Merchant payout model"""
    payout_id: str = Field(default_factory=lambda: f"po_{secrets.token_hex(12)}")
    merchant_id: str
    amount: Decimal
    currency: str = "EUR"
    status: PaymentStatus = PaymentStatus.PENDING
    arrival_date: datetime
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None


class StripePaymentGateway:
    """
    Simulated Stripe Payment Gateway
    
    In production, this would use the actual Stripe API
    For now, it simulates payment processing
    """
    
    def __init__(self):
        self.api_key = os.getenv("STRIPE_API_KEY", "sk_test_simulated")
        self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_simulated")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_simulated")
        
        # In-memory storage for simulation
        self.payment_intents: Dict[str, PaymentIntent] = {}
        self.refunds: Dict[str, Refund] = {}
        self.payouts: Dict[str, Payout] = {}
    
    async def create_payment_intent(
        self,
        amount: Decimal,
        currency: str = "EUR",
        customer_id: Optional[str] = None,
        order_id: Optional[str] = None,
        payment_method: PaymentMethod = PaymentMethod.CARD,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentIntent:
        """
        Create a payment intent
        
        Args:
            amount: Amount to charge
            currency: Currency code
            customer_id: Customer ID
            order_id: Order ID
            payment_method: Payment method
            description: Payment description
            metadata: Additional metadata
            
        Returns:
            PaymentIntent object
        """
        try:
            payment_intent = PaymentIntent(
                amount=amount,
                currency=currency,
                customer_id=customer_id,
                order_id=order_id,
                payment_method=payment_method,
                description=description,
                metadata=metadata or {}
            )
            
            # Store payment intent
            self.payment_intents[payment_intent.payment_intent_id] = payment_intent
            
            logger.info("Payment intent created",
                       payment_intent_id=payment_intent.payment_intent_id,
                       amount=float(amount),
                       currency=currency)
            
            return payment_intent
            
        except Exception as e:
            logger.error("Failed to create payment intent", error=str(e))
            raise
    
    async def confirm_payment_intent(
        self,
        payment_intent_id: str,
        payment_method_details: Optional[Dict[str, Any]] = None
    ) -> PaymentIntent:
        """
        Confirm and process payment intent
        
        Args:
            payment_intent_id: Payment intent ID
            payment_method_details: Payment method details (card, etc.)
            
        Returns:
            Updated PaymentIntent
        """
        try:
            payment_intent = self.payment_intents.get(payment_intent_id)
            if not payment_intent:
                raise ValueError(f"Payment intent {payment_intent_id} not found")
            
            # Simulate payment processing
            payment_intent.status = PaymentStatus.PROCESSING
            await asyncio.sleep(0.1)  # Simulate processing delay
            
            # Simulate fraud check (99% success rate)
            import random
            if random.random() < 0.99:
                payment_intent.status = PaymentStatus.SUCCEEDED
                logger.info("Payment succeeded",
                           payment_intent_id=payment_intent_id,
                           amount=float(payment_intent.amount))
            else:
                payment_intent.status = PaymentStatus.FAILED
                logger.warning("Payment failed",
                             payment_intent_id=payment_intent_id,
                             reason="fraud_check_failed")
            
            payment_intent.updated_at = datetime.utcnow()
            
            return payment_intent
            
        except Exception as e:
            logger.error("Failed to confirm payment", error=str(e))
            raise
    
    async def get_payment_intent(
        self,
        payment_intent_id: str
    ) -> Optional[PaymentIntent]:
        """Get payment intent by ID"""
        return self.payment_intents.get(payment_intent_id)
    
    async def cancel_payment_intent(
        self,
        payment_intent_id: str
    ) -> PaymentIntent:
        """Cancel a payment intent"""
        try:
            payment_intent = self.payment_intents.get(payment_intent_id)
            if not payment_intent:
                raise ValueError(f"Payment intent {payment_intent_id} not found")
            
            if payment_intent.status == PaymentStatus.SUCCEEDED:
                raise ValueError("Cannot cancel succeeded payment")
            
            payment_intent.status = PaymentStatus.CANCELLED
            payment_intent.updated_at = datetime.utcnow()
            
            logger.info("Payment cancelled",
                       payment_intent_id=payment_intent_id)
            
            return payment_intent
            
        except Exception as e:
            logger.error("Failed to cancel payment", error=str(e))
            raise
    
    async def create_refund(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal] = None,
        reason: RefundReason = RefundReason.REQUESTED_BY_CUSTOMER
    ) -> Refund:
        """
        Create a refund for a payment
        
        Args:
            payment_intent_id: Original payment intent ID
            amount: Amount to refund (None for full refund)
            reason: Refund reason
            
        Returns:
            Refund object
        """
        try:
            payment_intent = self.payment_intents.get(payment_intent_id)
            if not payment_intent:
                raise ValueError(f"Payment intent {payment_intent_id} not found")
            
            if payment_intent.status != PaymentStatus.SUCCEEDED:
                raise ValueError("Can only refund succeeded payments")
            
            # Default to full refund
            refund_amount = amount or payment_intent.amount
            
            if refund_amount > payment_intent.amount:
                raise ValueError("Refund amount exceeds payment amount")
            
            refund = Refund(
                payment_intent_id=payment_intent_id,
                amount=refund_amount,
                currency=payment_intent.currency,
                reason=reason,
                status=PaymentStatus.PROCESSING
            )
            
            # Simulate refund processing
            await asyncio.sleep(0.1)
            refund.status = PaymentStatus.SUCCEEDED
            refund.processed_at = datetime.utcnow()
            
            # Update payment intent status
            if refund_amount == payment_intent.amount:
                payment_intent.status = PaymentStatus.REFUNDED
            else:
                payment_intent.status = PaymentStatus.PARTIALLY_REFUNDED
            
            payment_intent.updated_at = datetime.utcnow()
            
            # Store refund
            self.refunds[refund.refund_id] = refund
            
            logger.info("Refund processed",
                       refund_id=refund.refund_id,
                       payment_intent_id=payment_intent_id,
                       amount=float(refund_amount))
            
            return refund
            
        except Exception as e:
            logger.error("Failed to create refund", error=str(e))
            raise
    
    async def get_refund(
        self,
        refund_id: str
    ) -> Optional[Refund]:
        """Get refund by ID"""
        return self.refunds.get(refund_id)
    
    async def create_payout(
        self,
        merchant_id: str,
        amount: Decimal,
        currency: str = "EUR",
        description: Optional[str] = None
    ) -> Payout:
        """
        Create a payout to merchant
        
        Args:
            merchant_id: Merchant ID
            amount: Payout amount
            currency: Currency code
            description: Payout description
            
        Returns:
            Payout object
        """
        try:
            # Calculate arrival date (typically 2-3 business days)
            arrival_date = datetime.utcnow() + timedelta(days=3)
            
            payout = Payout(
                merchant_id=merchant_id,
                amount=amount,
                currency=currency,
                status=PaymentStatus.PENDING,
                arrival_date=arrival_date,
                description=description
            )
            
            # Store payout
            self.payouts[payout.payout_id] = payout
            
            logger.info("Payout created",
                       payout_id=payout.payout_id,
                       merchant_id=merchant_id,
                       amount=float(amount),
                       arrival_date=arrival_date.isoformat())
            
            return payout
            
        except Exception as e:
            logger.error("Failed to create payout", error=str(e))
            raise
    
    async def process_payout(
        self,
        payout_id: str
    ) -> Payout:
        """Process a pending payout"""
        try:
            payout = self.payouts.get(payout_id)
            if not payout:
                raise ValueError(f"Payout {payout_id} not found")
            
            # Simulate payout processing
            payout.status = PaymentStatus.PROCESSING
            await asyncio.sleep(0.1)
            
            payout.status = PaymentStatus.SUCCEEDED
            payout.processed_at = datetime.utcnow()
            
            logger.info("Payout processed",
                       payout_id=payout_id,
                       merchant_id=payout.merchant_id,
                       amount=float(payout.amount))
            
            return payout
            
        except Exception as e:
            logger.error("Failed to process payout", error=str(e))
            raise
    
    async def get_payout(
        self,
        payout_id: str
    ) -> Optional[Payout]:
        """Get payout by ID"""
        return self.payouts.get(payout_id)
    
    async def calculate_merchant_payout(
        self,
        order_amount: Decimal,
        commission_rate: Decimal,
        marketplace_fees: Decimal = Decimal("0.00")
    ) -> Dict[str, Decimal]:
        """
        Calculate merchant payout after commission and fees
        
        Args:
            order_amount: Total order amount
            commission_rate: Commission rate (e.g., 0.15 for 15%)
            marketplace_fees: Additional marketplace fees
            
        Returns:
            Dictionary with breakdown
        """
        commission = order_amount * commission_rate
        total_fees = commission + marketplace_fees
        merchant_payout = order_amount - total_fees
        
        return {
            "order_amount": order_amount,
            "commission": commission,
            "marketplace_fees": marketplace_fees,
            "total_fees": total_fees,
            "merchant_payout": merchant_payout
        }
    
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str
    ) -> bool:
        """
        Verify Stripe webhook signature
        
        Args:
            payload: Webhook payload
            signature: Stripe signature header
            
        Returns:
            True if signature is valid
        """
        try:
            # In production, use actual Stripe signature verification
            # For simulation, always return True
            return True
        except Exception as e:
            logger.error("Webhook signature verification failed", error=str(e))
            return False


# Singleton instance
_payment_gateway: Optional[StripePaymentGateway] = None


def get_payment_gateway() -> StripePaymentGateway:
    """Get singleton payment gateway instance"""
    global _payment_gateway
    if _payment_gateway is None:
        _payment_gateway = StripePaymentGateway()
    return _payment_gateway


# Example usage
async def example_payment_flow():
    """Example payment flow"""
    gateway = get_payment_gateway()
    
    # Create payment intent
    payment_intent = await gateway.create_payment_intent(
        amount=Decimal("99.99"),
        currency="EUR",
        customer_id="CUST123",
        order_id="ORD123",
        description="Order #123"
    )
    
    print(f"Payment intent created: {payment_intent.payment_intent_id}")
    
    # Confirm payment
    confirmed = await gateway.confirm_payment_intent(payment_intent.payment_intent_id)
    print(f"Payment status: {confirmed.status}")
    
    # Create refund
    if confirmed.status == PaymentStatus.SUCCEEDED:
        refund = await gateway.create_refund(
            payment_intent.payment_intent_id,
            amount=Decimal("50.00"),
            reason=RefundReason.REQUESTED_BY_CUSTOMER
        )
        print(f"Refund created: {refund.refund_id}, status: {refund.status}")


if __name__ == "__main__":
    asyncio.run(example_payment_flow())

