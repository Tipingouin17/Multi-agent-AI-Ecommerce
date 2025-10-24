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

from shared.db_helpers import DatabaseHelper

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
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
    """Enumeration for payment gateway types."""
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    BANK_TRANSFER = "bank_transfer"
    CRYPTO = "crypto"
    WALLET = "wallet"


class TransactionType(str, Enum):
    """Enumeration for transaction types."""
    AUTHORIZE = "authorize"
    CAPTURE = "capture"
    SALE = "sale"
    REFUND = "refund"
    VOID = "void"


class TransactionStatus(str, Enum):
    """Enumeration for transaction statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class RefundType(str, Enum):
    """Enumeration for refund types."""
    FULL = "full"
    PARTIAL = "partial"
    CHARGEBACK = "chargeback"


class RefundStatus(str, Enum):
    """Enumeration for refund statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =====================================================
# PYDANTIC MODELS
# =====================================================

class PaymentGateway(BaseModel):
    """Pydantic model representing a payment gateway.

    Attributes:
        gateway_id (int): Unique identifier for the payment gateway.
        gateway_name (str): Name of the payment gateway.
        gateway_type (GatewayType): Type of the payment gateway (e.g., credit_card, paypal).
        is_active (bool): Whether the gateway is active. Defaults to True.
        is_test_mode (bool): Whether the gateway is in test mode. Defaults to False.
        supported_currencies (List[str]): List of currencies supported by the gateway. Defaults to ["USD"].
        transaction_fee_percent (Decimal): Percentage fee charged per transaction. Defaults to "0.00".
        transaction_fee_fixed (Decimal): Fixed fee charged per transaction. Defaults to "0.00".
        created_at (datetime): Timestamp when the gateway was created.
        updated_at (datetime): Timestamp when the gateway was last updated.
    """
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
    """Pydantic model for creating a new payment method.

    Attributes:
        customer_id (str): Identifier of the customer.
        gateway_id (int): Identifier of the payment gateway used.
        method_type (str): Type of payment method (e.g., 'card', 'bank').
        is_default (bool): Whether this is the customer's default payment method. Defaults to False.
        card_last_four (Optional[str]): Last four digits of the card, if applicable.
        card_brand (Optional[str]): Brand of the card (e.g., 'Visa', 'Mastercard').
        card_expiry_month (Optional[int]): Expiry month of the card.
        card_expiry_year (Optional[int]): Expiry year of the card.
        card_holder_name (Optional[str]): Name of the card holder.
        gateway_token (Optional[str]): Token representing the payment method at the gateway.
        gateway_customer_id (Optional[str]): Customer ID at the payment gateway.
    """
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
    """Pydantic model representing a payment method, extending PaymentMethodCreate.

    Attributes:
        method_id (UUID): Unique identifier for the payment method.
        is_verified (bool): Whether the payment method has been verified. Defaults to False.
        created_at (datetime): Timestamp when the payment method was created.
        updated_at (datetime): Timestamp when the payment method was last updated.
    """
    method_id: UUID
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentTransactionCreate(BaseModel):
    """Pydantic model for creating a new payment transaction.

    Attributes:
        order_id (Optional[str]): Identifier of the associated order.
        customer_id (str): Identifier of the customer initiating the transaction.
        payment_method_id (Optional[UUID]): Identifier of the payment method used.
        gateway_id (int): Identifier of the payment gateway used.
        transaction_type (TransactionType): Type of transaction (e.g., 'authorize', 'capture').
        amount (Decimal): Amount of the transaction.
        currency (str): Currency of the transaction. Defaults to "USD".
    """
    order_id: Optional[str] = None
    customer_id: str
    payment_method_id: Optional[UUID] = None
    gateway_id: int
    transaction_type: TransactionType
    amount: Decimal
    currency: str = "USD"


class PaymentTransaction(PaymentTransactionCreate):
    """Pydantic model representing a payment transaction, extending PaymentTransactionCreate.

    Attributes:
        transaction_id (UUID): Unique identifier for the transaction.
        transaction_status (TransactionStatus): Current status of the transaction. Defaults to PENDING.
        fee_amount (Decimal): Fees incurred for the transaction. Defaults to "0.00".
        net_amount (Optional[Decimal]): Net amount after fees.
        gateway_transaction_id (Optional[str]): Transaction ID at the payment gateway.
        authorization_code (Optional[str]): Authorization code from the gateway.
        risk_score (Optional[Decimal]): Risk score associated with the transaction.
        risk_level (Optional[str]): Risk level (e.g., 'low', 'medium', 'high').
        error_code (Optional[str]): Error code if the transaction failed.
        error_message (Optional[str]): Error message if the transaction failed.
        initiated_at (datetime): Timestamp when the transaction was initiated.
        completed_at (Optional[datetime]): Timestamp when the transaction was completed.
        created_at (datetime): Timestamp when the transaction record was created.
        updated_at (datetime): Timestamp when the transaction record was last updated.
    """
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
    """Pydantic model for creating a new payment refund.

    Attributes:
        transaction_id (UUID): Identifier of the original transaction being refunded.
        order_id (Optional[str]): Identifier of the associated order.
        customer_id (str): Identifier of the customer.
        refund_type (RefundType): Type of refund (e.g., 'full', 'partial').
        refund_reason (Optional[str]): Reason for the refund.
        refund_amount (Decimal): Amount to be refunded.
        currency (str): Currency of the refund. Defaults to "USD".
        notes (Optional[str]): Additional notes for the refund.
        requested_by (Optional[str]): User who requested the refund.
    """
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
    """Pydantic model representing a payment refund, extending PaymentRefundCreate.

    Attributes:
        refund_id (UUID): Unique identifier for the refund.
        refund_status (RefundStatus): Current status of the refund. Defaults to PENDING.
        gateway_refund_id (Optional[str]): Refund ID at the payment gateway.
        error_code (Optional[str]): Error code if the refund failed.
        error_message (Optional[str]): Error message if the refund failed.
        requested_at (datetime): Timestamp when the refund was requested.
        completed_at (Optional[datetime]): Timestamp when the refund was completed.
        created_at (datetime): Timestamp when the refund record was created.
        updated_at (datetime): Timestamp when the refund record was last updated.
    """
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
    """Pydantic model for creating a new payment authorization.

    Attributes:
        order_id (str): Identifier of the associated order.
        customer_id (str): Identifier of the customer.
        payment_method_id (Optional[UUID]): Identifier of the payment method used.
        gateway_id (int): Identifier of the payment gateway used.
        authorization_amount (Decimal): Amount authorized.
        currency (str): Currency of the authorization. Defaults to "USD".
    """
    order_id: str
    customer_id: str
    payment_method_id: Optional[UUID] = None
    gateway_id: int
    authorization_amount: Decimal
    currency: str = "USD"


class PaymentAuthorization(PaymentAuthorizationCreate):
    """Pydantic model representing a payment authorization, extending PaymentAuthorizationCreate.

    Attributes:
        authorization_id (UUID): Unique identifier for the authorization.
        authorization_code (Optional[str]): Authorization code from the gateway.
        authorization_status (str): Current status of the authorization. Defaults to "pending".
        captured_amount (Decimal): Amount captured from the authorization. Defaults to "0.00".
        remaining_amount (Optional[Decimal]): Remaining authorized amount.
        gateway_authorization_id (Optional[str]): Authorization ID at the payment gateway.
        expires_at (Optional[datetime]): Timestamp when the authorization expires.
        authorized_at (Optional[datetime]): Timestamp when the authorization was performed.
        created_at (datetime): Timestamp when the authorization record was created.
        updated_at (datetime): Timestamp when the authorization record was last updated.
    """
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
    """Handles all database operations for the payment agent."""

    def __init__(self, db_manager: DatabaseManager):
        # FastAPI app for REST API
        self.app = FastAPI(title="Payment Agent API")
        
        # Add CORS middleware for dashboard integration
        
        """Initializes the PaymentRepository with a database manager.

        Args:
            db_manager (DatabaseManager): The database manager instance.
        """
        self.db_manager = db_manager
        self.db_helper = DatabaseHelper(db_manager.engine)

    async def get_active_gateways(self) -> List[PaymentGateway]:
        """Retrieves all active payment gateways from the database.

        Returns:
            List[PaymentGateway]: A list of active payment gateways.
        """
        try:
            async with self.db_manager.get_session() as session:
                return await self.db_helper.get_all(session, PaymentGateway, is_active=True)
        except Exception as e:
            logger.error(f"Error getting active gateways: {e}")
            return []

    async def get_gateway(self, gateway_id: int) -> Optional[PaymentGateway]:
        """Retrieves a single payment gateway by its ID.

        Args:
            gateway_id (int): The unique identifier of the payment gateway.

        Returns:
            Optional[PaymentGateway]: The payment gateway if found, otherwise None.
        """
        try:
            async with self.db_manager.get_session() as session:
                return await self.db_helper.get_by_id(session, PaymentGateway, gateway_id)
        except Exception as e:
            logger.error(f"Error getting gateway by ID {gateway_id}: {e}")
            return None

    async def create_payment_method(
        self,
        payment_method: PaymentMethodCreate
    ) -> PaymentMethod:
        """Creates a new payment method in the database.

        Args:
            payment_method (PaymentMethodCreate): The data for creating the payment method.

        Returns:
            PaymentMethod: The newly created payment method.
        """
        try:
            async with self.db_manager.get_session() as session:
                return await self.db_helper.create(session, PaymentMethod, **payment_method.model_dump())
        except Exception as e:
            logger.error(f"Error creating payment method for customer {payment_method.customer_id}: {e}")
            raise

    async def get_customer_payment_methods(
        self,
        customer_id: str
    ) -> List[PaymentMethod]:
        """Retrieves all payment methods associated with a given customer ID.

        Args:
            customer_id (str): The unique identifier of the customer.

        Returns:
            List[PaymentMethod]: A list of payment methods for the customer.
        """
        try:
            async with self.db_manager.get_session() as session:
                return await self.db_helper.get_all(session, PaymentMethod, customer_id=customer_id, order_by=[("is_default", False), ("created_at", False)])
        except Exception as e:
            logger.error(f"Error getting payment methods for customer {customer_id}: {e}")
            return []

    async def create_transaction(
        self,
        transaction: PaymentTransactionCreate
    ) -> PaymentTransaction:
        """Creates a new payment transaction record in the database.

        Args:
            transaction (PaymentTransactionCreate): The data for creating the transaction.

        Returns:
            PaymentTransaction: The newly created payment transaction.
        """
        try:
            async with self.db_manager.get_session() as session:
                return await self.db_helper.create(session, PaymentTransaction, **transaction.model_dump())
        except Exception as e:
            logger.error(f"Error creating transaction for customer {transaction.customer_id}: {e}")
            raise

    async def update_transaction_status(
        self,
        transaction_id: UUID,
        status: TransactionStatus,
        gateway_transaction_id: Optional[str] = None,
        authorization_code: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[PaymentTransaction]:
        """Updates the status of an existing payment transaction.

        Args:
            transaction_id (UUID): The unique identifier of the transaction.
            status (TransactionStatus): The new status of the transaction.
            gateway_transaction_id (Optional[str]): The transaction ID from the payment gateway.
            authorization_code (Optional[str]): The authorization code from the payment gateway.
            error_code (Optional[str]): An error code if the transaction failed.
            error_message (Optional[str]): A detailed error message if the transaction failed.

        Returns:
            Optional[PaymentTransaction]: The updated payment transaction if found, otherwise None.
        """
        try:
            async with self.db_manager.get_session() as session:
                update_data = {
                    "transaction_status": status.value,
                    "completed_at": datetime.utcnow() if status in (TransactionStatus.COMPLETED, TransactionStatus.FAILED, TransactionStatus.CANCELLED) else None
                }
                if gateway_transaction_id: update_data["gateway_transaction_id"] = gateway_transaction_id
                if authorization_code: update_data["authorization_code"] = authorization_code
                if error_code: update_data["error_code"] = error_code
                if error_message: update_data["error_message"] = error_message
                return await self.db_helper.update(session, PaymentTransaction, transaction_id, update_data)
        except Exception as e:
            logger.error(f"Error updating transaction status for {transaction_id}: {e}")
            raise

    async def get_transaction(self, transaction_id: UUID) -> Optional[PaymentTransaction]:
        """Retrieves a single payment transaction by its ID.

        Args:
            transaction_id (UUID): The unique identifier of the transaction.

        Returns:
            Optional[PaymentTransaction]: The payment transaction if found, otherwise None.
        """
        try:
            async with self.db_manager.get_session() as session:
                return await self.db_helper.get_by_id(session, PaymentTransaction, transaction_id)
        except Exception as e:
            logger.error(f"Error getting transaction by ID {transaction_id}: {e}")
            return None

    async def create_refund(
        self,
        refund: PaymentRefundCreate
    ) -> PaymentRefund:
        """Creates a new refund record in the database.

        Args:
            refund (PaymentRefundCreate): The data for creating the refund.

        Returns:
            PaymentRefund: The newly created refund record.
        """
        try:
            async with self.db_manager.get_session() as session:
                return await self.db_helper.create(session, PaymentRefund, **refund.model_dump())
        except Exception as e:
            logger.error(f"Error creating refund for transaction {refund.transaction_id}: {e}")
            raise

    async def update_refund_status(
        self,
        refund_id: UUID,
        status: RefundStatus,
        gateway_refund_id: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[PaymentRefund]:
        """Updates the status of an existing refund.

        Args:
            refund_id (UUID): The unique identifier of the refund.
            status (RefundStatus): The new status of the refund.
            gateway_refund_id (Optional[str]): The refund ID from the payment gateway.
            error_code (Optional[str]): An error code if the refund failed.
            error_message (Optional[str]): A detailed error message if the refund failed.

        Returns:
            Optional[PaymentRefund]: The updated refund if found, otherwise None.
        """
        try:
            async with self.db_manager.get_session() as session:
                update_data = {
                    "refund_status": status.value,
                    "completed_at": datetime.utcnow() if status in (RefundStatus.COMPLETED, RefundStatus.FAILED, RefundStatus.CANCELLED) else None
                }
                if gateway_refund_id: update_data["gateway_refund_id"] = gateway_refund_id
                if error_code: update_data["error_code"] = error_code
                if error_message: update_data["error_message"] = error_message
                return await self.db_helper.update(session, PaymentRefund, refund_id, update_data)
        except Exception as e:
            logger.error(f"Error updating refund status for {refund_id}: {e}")
            raise

    async def get_refund(self, refund_id: UUID) -> Optional[PaymentRefund]:
        """Retrieves a single refund record by its ID.

        Args:
            refund_id (UUID): The unique identifier of the refund.

        Returns:
            Optional[PaymentRefund]: The refund record if found, otherwise None.
        """
        try:
            async with self.db_manager.get_session() as session:
                return await self.db_helper.get_by_id(session, PaymentRefund, refund_id)
        except Exception as e:
            logger.error(f"Error getting refund by ID {refund_id}: {e}")
            return None

    async def create_authorization(
        self,
        authorization: PaymentAuthorizationCreate
    ) -> PaymentAuthorization:
        """Creates a new payment authorization record in the database.

        Args:
            authorization (PaymentAuthorizationCreate): The data for creating the authorization.

        Returns:
            PaymentAuthorization: The newly created authorization record.
        """
        try:
            async with self.db_manager.get_session() as session:
                return await self.db_helper.create(session, PaymentAuthorization, **authorization.model_dump())
        except Exception as e:
            logger.error(f"Error creating authorization for order {authorization.order_id}: {e}")
            raise

    async def update_authorization_status(
        self,
        authorization_id: UUID,
        status: str,
        authorization_code: Optional[str] = None,
        gateway_authorization_id: Optional[str] = None
    ) -> Optional[PaymentAuthorization]:
        """Updates the status of an existing payment authorization.

        Args:
            authorization_id (UUID): The unique identifier of the authorization.
            status (str): The new status of the authorization.
            authorization_code (Optional[str]): The authorization code from the payment gateway.
            gateway_authorization_id (Optional[str]): The authorization ID from the payment gateway.

        Returns:
            Optional[PaymentAuthorization]: The updated authorization if found, otherwise None.
        """
        try:
            async with self.db_manager.get_session() as session:
                update_data = {"authorization_status": status}
                if authorization_code: update_data["authorization_code"] = authorization_code
                if gateway_authorization_id: update_data["gateway_authorization_id"] = gateway_authorization_id
                return await self.db_helper.update(session, PaymentAuthorization, authorization_id, update_data)
        except Exception as e:
            logger.error(f"Error updating authorization status for {authorization_id}: {e}")
            raise

    async def get_authorization(self, authorization_id: UUID) -> Optional[PaymentAuthorization]:
        """Retrieves a single authorization record by its ID.

        Args:
            authorization_id (UUID): The unique identifier of the authorization.

        Returns:
            Optional[PaymentAuthorization]: The authorization record if found, otherwise None.
        """
        try:
            async with self.db_manager.get_session() as session:
                return await self.db_helper.get_by_id(session, PaymentAuthorization, authorization_id)
        except Exception as e:
            logger.error(f"Error getting authorization by ID {authorization_id}: {e}")
            return None


# REMOVED DUPLICATE CLASS



class PaymentAgent(BaseAgent):
    """Payment Agent for handling all payment-related operations.

    This agent manages payment gateways, methods, transactions, refunds, and authorizations.
    It interacts with the database for persistence and processes messages for inter-agent communication.
    """

    def __init__(self):
        """Initializes the PaymentAgent.
        
        Database manager will be initialized in the initialize() method.
        """
        super().__init__(agent_id="payment_agent")
        self.db_manager = None
        self.repo = None
        self._db_initialized = False
        logger.info(f"PaymentAgent initialized with ID: {self.agent_id}")

    async def setup(self):
        """Initializes the database connection and sets up necessary components for the agent.

        This method connects to the database and sets the `_db_initialized` flag.
        """
        try:
            await self.db_manager.initialize_async()
            self._db_initialized = True
            logger.info("PaymentAgent database connection established and initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize PaymentAgent database: {e}")
            self._db_initialized = False

    async def teardown(self):
        """Closes the database connection when the agent is shutting down.

        This method ensures proper resource management by disconnecting from the database.
        """
        try:
            await self.db_manager.close()
            logger.info("PaymentAgent database connection closed.")
        except Exception as e:
            logger.error(f"Failed to close PaymentAgent database connection: {e}")

    async def process_message(self, message: AgentMessage):
        """Processes incoming messages relevant to payment operations.

        Args:
            message (AgentMessage): The incoming message containing type and payload.

        Raises:
            ValueError: If the database is not initialized or payment processing fails.
        """
        if not self._db_initialized:
            logger.warning("Database not initialized. Cannot process message.")
            return

        logger.info(f"PaymentAgent received message: {message.message_type}")

        try:
            if message.message_type == MessageType.PAYMENT_REQUEST:
                # Example: Process a payment request
                transaction_data = PaymentTransactionCreate(**message.payload)
                result = await self.process_payment(transaction_data)
                await self.send_message(
                    recipient_id=message.sender_id,
                    message_type=MessageType.PAYMENT_CONFIRMATION,
                    payload=result
                )
            elif message.message_type == MessageType.REFUND_REQUEST:
                # Example: Process a refund request
                refund_data = PaymentRefundCreate(**message.payload)
                result = await self.process_refund(refund_data)
                await self.send_message(
                    recipient_id=message.sender_id,
                    message_type=MessageType.REFUND_CONFIRMATION,
                    payload=result
                )
            # Add other message types as needed
            else:
                logger.warning(f"Unknown message type received: {message.message_type}")
        except Exception as e:
            logger.error(f"Error processing message {message.message_type}: {e}")
            await self.send_message(
                recipient_id=message.sender_id,
                message_type=MessageType.ERROR,
                payload={"original_message_type": message.message_type, "error": str(e)}
            )

    async def process_payment(self, transaction: PaymentTransactionCreate) -> Dict[str, Any]:
        """Processes a payment transaction, simulating interaction with a payment gateway
        and updating the transaction status in the database.

        Args:
            transaction (PaymentTransactionCreate): The details of the payment transaction to process.

        Returns:
            Dict[str, Any]: A dictionary representing the updated transaction details.

        Raises:
            ValueError: If the database is not initialized or payment processing encounters an error.
        """
        if not self._db_initialized:
            logger.error("Database not initialized. Cannot process payment.")
            raise ValueError("Payment service not ready: database not initialized.")

        try:
            # 1. Create initial transaction record
            new_transaction = await self.repo.create_transaction(transaction)
            logger.info("Initial transaction created", transaction_id=str(new_transaction.transaction_id))

            # 2. Simulate payment gateway interaction
            # In a real system, this would involve calling an external payment gateway API.
            # For now, we'll simulate success/failure based on amount.
            if transaction.amount > Decimal("0.00"):
                # Simulate success
                gateway_transaction_id = str(uuid4())
                authorization_code = "AUTH-" + str(uuid4())[:8].upper()
                status = TransactionStatus.COMPLETED
                logger.info("Payment gateway simulated success", transaction_id=str(new_transaction.transaction_id))
            else:
                # Simulate failure for zero amount
                gateway_transaction_id = None
                authorization_code = None
                status = TransactionStatus.FAILED
                error_code = "ZERO_AMOUNT"
                error_message = "Cannot process zero amount payment."
                logger.warning("Payment gateway simulated failure: zero amount", transaction_id=str(new_transaction.transaction_id))

            # 3. Update transaction status
            updated_transaction = await self.repo.update_transaction_status(
                new_transaction.transaction_id,
                status,
                gateway_transaction_id=gateway_transaction_id,
                authorization_code=authorization_code,
                error_code=error_code if status == TransactionStatus.FAILED else None,
                error_message=error_message if status == TransactionStatus.FAILED else None
            )
            if not updated_transaction:
                raise ValueError("Failed to update transaction status after gateway processing.")

            logger.info("Transaction processed", transaction_id=str(updated_transaction.transaction_id), status=updated_transaction.transaction_status.value)
            return updated_transaction.model_dump()

        except Exception as e:
            logger.error("process_payment_failed", customer_id=transaction.customer_id, error=str(e))
            # Attempt to update transaction to FAILED if it was created
            if 'new_transaction' in locals():
                await self.repo.update_transaction_status(
                    new_transaction.transaction_id,
                    TransactionStatus.FAILED,
                    error_code="PROCESSING_ERROR",
                    error_message=str(e)
                )
            raise ValueError(f"Payment processing failed: {str(e)}")

    async def process_refund(self, refund: PaymentRefundCreate) -> Dict[str, Any]:
        """Processes a refund request, simulating interaction with a payment gateway
        and updating the refund status in the database.

        Args:
            refund (PaymentRefundCreate): The details of the refund to process.

        Returns:
            Dict[str, Any]: A dictionary representing the updated refund details.

        Raises:
            ValueError: If the database is not initialized or refund processing encounters an error.
        """
        if not self._db_initialized:
            logger.error("Database not initialized. Cannot process refund.")
            raise ValueError("Refund service not ready: database not initialized.")

        try:
            # 1. Create initial refund record
            new_refund = await self.repo.create_refund(refund)
            logger.info("Initial refund created", refund_id=str(new_refund.refund_id))

            # 2. Simulate refund gateway interaction
            # In a real system, this would involve calling an external payment gateway API.
            # For now, we'll simulate success/failure.
            if refund.refund_amount > Decimal("0.00"):
                gateway_refund_id = str(uuid4())
                status = RefundStatus.COMPLETED
                logger.info("Refund gateway simulated success", refund_id=str(new_refund.refund_id))
            else:
                gateway_refund_id = None
                status = RefundStatus.FAILED
                error_code = "ZERO_AMOUNT_REFUND"
                error_message = "Cannot process zero amount refund."
                logger.warning("Refund gateway simulated failure: zero amount", refund_id=str(new_refund.refund_id))

            # 3. Update refund status
            updated_refund = await self.repo.update_refund_status(
                new_refund.refund_id,
                status,
                gateway_refund_id=gateway_refund_id,
                error_code=error_code if status == RefundStatus.FAILED else None,
                error_message=error_message if status == RefundStatus.FAILED else None
            )
            if not updated_refund:
                raise ValueError("Failed to update refund status after gateway processing.")

            logger.info("Refund processed", refund_id=str(updated_refund.refund_id), status=updated_refund.refund_status.value)
            return updated_refund.model_dump()

        except Exception as e:
            logger.error("process_refund_failed", transaction_id=refund.transaction_id, error=str(e))
            # Attempt to update refund to FAILED if it was created
            if 'new_refund' in locals():
                await self.repo.update_refund_status(
                    new_refund.refund_id,
                    RefundStatus.FAILED,
                    error_code="PROCESSING_ERROR",
                    error_message=str(e)
                )
            raise ValueError(f"Refund processing failed: {str(e)}")
    
    async def initialize(self):
        """Initialize agent-specific components"""
        await super().initialize()
        try:
            # Create database manager if not available globally
            try:
                self.db_manager = get_database_manager()
            except RuntimeError:
                # Create our own database manager
                from shared.models import DatabaseConfig
                db_config = DatabaseConfig()
                self.db_manager = DatabaseManager(db_config)
                await self.db_manager.initialize_async()
            
            # PaymentRepository expects db_manager.engine, but we have async_engine
            # Create a temporary wrapper or use DatabaseHelper directly
            from shared.db_helpers import DatabaseHelper
            if hasattr(self.db_manager, 'async_engine'):
                self.db_helper = DatabaseHelper(self.db_manager.async_engine)
            self._db_initialized = True
            logger.info(f"{self.agent_name} initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing {self.agent_name}: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup agent resources"""
        try:
            if hasattr(self, 'db_manager') and self.db_manager:
                await self.db_manager.close()
            await super().cleanup()
            logger.info(f"{self.agent_name} cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment business logic
        
        Args:
            data: Dictionary containing operation type and parameters
            
        Returns:
            Dictionary with processing results
        """
        try:
            operation = data.get("operation", "process_payment")
            
            if operation == "process_payment":
                # Process payment
                order_id = data.get("order_id")
                amount = Decimal(str(data.get("amount", 0)))
                currency = data.get("currency", "EUR")
                customer_id = data.get("customer_id")
                payment_method = data.get("payment_method")
                gateway = GatewayType(data.get("gateway", "stripe"))
                
                transaction = await self.process_payment(
                    order_id=order_id,
                    amount=amount,
                    currency=currency,
                    customer_id=customer_id,
                    payment_method=payment_method,
                    gateway=gateway
                )
                return {"status": "success", "transaction": transaction}
            
            elif operation == "capture_payment":
                # Capture authorized payment
                transaction_id = data.get("transaction_id")
                amount = data.get("amount")
                result = await self.capture_payment(transaction_id, amount)
                return {"status": "success", "result": result}
            
            elif operation == "refund":
                # Process refund
                transaction_id = data.get("transaction_id")
                amount = Decimal(str(data.get("amount", 0)))
                reason = data.get("reason", "customer_request")
                refund_type = RefundType(data.get("refund_type", "full"))
                
                refund = await self.process_refund(
                    transaction_id=transaction_id,
                    amount=amount,
                    reason=reason,
                    refund_type=refund_type
                )
                return {"status": "success", "refund": refund}
            
            else:
                return {"status": "error", "message": f"Unknown operation: {operation}"}
                
        except Exception as e:
            logger.error(f"Error in process_business_logic: {e}")
            return {"status": "error", "message": str(e)}




# =====================================================
# FASTAPI APP
# =====================================================

# FastAPI app moved to __init__ method as self.app


async def get_payment_agent() -> PaymentAgent:
    """Dependency injection for payment agent."""
    db_manager = await get_database_manager()
    agent_id = os.getenv("AGENT_ID", "payment-agent-001")
    agent_type = os.getenv("AGENT_TYPE", "payment_agent")
    agent = PaymentAgent(agent_id, agent_type, db_manager)
    await agent.setup()
    return agent


# =====================================================
# API ENDPOINTS
# =====================================================

@self.app.get("/api/v1/payment/gateways", response_model=List[PaymentGateway])
async def get_payment_gateways(
    agent: PaymentAgent = Depends(get_payment_agent)
):
    """Get all active payment gateways."""
    try:
        gateways = await agent.repo.get_active_gateways()
        return gateways
    except Exception as e:
        logger.error("get_gateways_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@self.app.post("/api/v1/payment/methods", response_model=PaymentMethod)
async def create_payment_method(
    payment_method: PaymentMethodCreate = Body(...),
    agent: PaymentAgent = Depends(get_payment_agent)
):
    """Create a new payment method."""
    try:
        result = await agent.repo.create_payment_method(payment_method)
        return result
    except Exception as e:
        logger.error("create_payment_method_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@self.app.get("/api/v1/payment/methods/{customer_id}", response_model=List[PaymentMethod])
async def get_customer_payment_methods(
    customer_id: str = Path(...),
    agent: PaymentAgent = Depends(get_payment_agent)
):
    """Get all payment methods for a customer."""
    try:
        methods = await agent.repo.get_customer_payment_methods(customer_id)
        return methods
    except Exception as e:
        logger.error("get_payment_methods_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@self.app.post("/api/v1/payment/process", response_model=Dict[str, Any])
async def process_payment(
    transaction: PaymentTransactionCreate = Body(...),
    agent: PaymentAgent = Depends(get_payment_agent)
):
    """Process a payment transaction."""
    try:
        result = await agent.process_payment(transaction)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("process_payment_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@self.app.get("/api/v1/payment/transactions/{transaction_id}", response_model=PaymentTransaction)
async def get_transaction(
    transaction_id: UUID = Path(...),
    agent: PaymentAgent = Depends(get_payment_agent)
):
    """Get transaction by ID."""
    try:
        transaction = await agent.repo.get_transaction(transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return transaction
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_transaction_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@self.app.post("/api/v1/payment/refund", response_model=Dict[str, Any])
async def process_refund(
    refund: PaymentRefundCreate = Body(...),
    agent: PaymentAgent = Depends(get_payment_agent)
):
    """Process a refund."""
    try:
        result = await agent.process_refund(refund)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("process_refund_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@self.app.post("/api/v1/payment/authorize", response_model=PaymentAuthorization)
async def authorize_payment(
    authorization: PaymentAuthorizationCreate = Body(...),
    agent: PaymentAgent = Depends(get_payment_agent)
):
    """Authorize a payment (hold funds)."""
    try:
        result = await agent.repo.create_authorization(authorization)
        return result
    except Exception as e:
        logger.error("authorize_payment_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@self.app.get("/")
async def read_root():
    """Root endpoint for the Payment Agent API."""
    return {"message": "Payment Agent Enhanced API is running!"}

@self.app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "payment_agent_enhanced", "version": "1.0.0"}


# =====================================================
# ANALYTICS ENDPOINTS
# =====================================================

@self.app.get("/api/v1/payment/analytics/transactions")
async def get_transaction_analytics(
    days: int = Query(30, ge=1, le=365),
    agent: PaymentAgent = Depends(get_payment_agent)
):
    """Get payment transaction analytics for the specified period."""
    try:
        from_date = datetime.utcnow() - timedelta(days=days)
        
        # Query transactions from database
        async with agent.db_manager.get_session() as session:
            from sqlalchemy import select, func
            from agents.payment_repository import PaymentTransactionDB
            
            # Total transactions
            total_result = await session.execute(
                select(func.count(PaymentTransactionDB.transaction_id))
                .where(PaymentTransactionDB.created_at >= from_date)
            )
            total_transactions = total_result.scalar() or 0
            
            # Total revenue
            revenue_result = await session.execute(
                select(func.sum(PaymentTransactionDB.amount))
                .where(PaymentTransactionDB.created_at >= from_date)
                .where(PaymentTransactionDB.status == TransactionStatus.COMPLETED)
            )
            total_revenue = revenue_result.scalar() or Decimal('0')
            
            # Transactions by status
            status_result = await session.execute(
                select(
                    PaymentTransactionDB.status,
                    func.count(PaymentTransactionDB.transaction_id)
                )
                .where(PaymentTransactionDB.created_at >= from_date)
                .group_by(PaymentTransactionDB.status)
            )
            transactions_by_status = {
                row[0]: row[1] for row in status_result.all()
            }
            
            # Transactions by gateway
            gateway_result = await session.execute(
                select(
                    PaymentTransactionDB.gateway_id,
                    func.count(PaymentTransactionDB.transaction_id),
                    func.sum(PaymentTransactionDB.amount)
                )
                .where(PaymentTransactionDB.created_at >= from_date)
                .where(PaymentTransactionDB.status == TransactionStatus.COMPLETED)
                .group_by(PaymentTransactionDB.gateway_id)
            )
            transactions_by_gateway = {
                str(row[0]): {
                    "count": row[1],
                    "revenue": str(row[2] or Decimal('0'))
                }
                for row in gateway_result.all()
            }
            
            # Success rate
            success_count = transactions_by_status.get(TransactionStatus.COMPLETED, 0)
            success_rate = (success_count / total_transactions * 100) if total_transactions > 0 else 0
            
            return {
                "period_days": days,
                "from_date": from_date.isoformat(),
                "total_transactions": total_transactions,
                "total_revenue": str(total_revenue),
                "success_rate": round(success_rate, 2),
                "transactions_by_status": transactions_by_status,
                "transactions_by_gateway": transactions_by_gateway,
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error("get_transaction_analytics_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@self.app.get("/api/v1/payment/analytics/refunds")
async def get_refund_analytics(
    days: int = Query(30, ge=1, le=365),
    agent: PaymentAgent = Depends(get_payment_agent)
):
    """Get refund analytics for the specified period."""
    try:
        from_date = datetime.utcnow() - timedelta(days=days)
        
        async with agent.db_manager.get_session() as session:
            from sqlalchemy import select, func
            from agents.payment_repository import PaymentRefundDB
            
            # Total refunds
            total_result = await session.execute(
                select(func.count(PaymentRefundDB.refund_id))
                .where(PaymentRefundDB.created_at >= from_date)
            )
            total_refunds = total_result.scalar() or 0
            
            # Total refund amount
            amount_result = await session.execute(
                select(func.sum(PaymentRefundDB.refund_amount))
                .where(PaymentRefundDB.created_at >= from_date)
                .where(PaymentRefundDB.status == RefundStatus.COMPLETED)
            )
            total_refund_amount = amount_result.scalar() or Decimal('0')
            
            # Refunds by type
            type_result = await session.execute(
                select(
                    PaymentRefundDB.refund_type,
                    func.count(PaymentRefundDB.refund_id),
                    func.sum(PaymentRefundDB.refund_amount)
                )
                .where(PaymentRefundDB.created_at >= from_date)
                .where(PaymentRefundDB.status == RefundStatus.COMPLETED)
                .group_by(PaymentRefundDB.refund_type)
            )
            refunds_by_type = {
                row[0]: {
                    "count": row[1],
                    "amount": str(row[2] or Decimal('0'))
                }
                for row in type_result.all()
            }
            
            # Refunds by status
            status_result = await session.execute(
                select(
                    PaymentRefundDB.status,
                    func.count(PaymentRefundDB.refund_id)
                )
                .where(PaymentRefundDB.created_at >= from_date)
                .group_by(PaymentRefundDB.status)
            )
            refunds_by_status = {
                row[0]: row[1] for row in status_result.all()
            }
            
            return {
                "period_days": days,
                "from_date": from_date.isoformat(),
                "total_refunds": total_refunds,
                "total_refund_amount": str(total_refund_amount),
                "refunds_by_type": refunds_by_type,
                "refunds_by_status": refunds_by_status,
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error("get_refund_analytics_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@self.app.get("/api/v1/payment/analytics/revenue")
async def get_revenue_analytics(
    days: int = Query(30, ge=1, le=365),
    agent: PaymentAgent = Depends(get_payment_agent)
):
    """Get revenue analytics with daily breakdown."""
    try:
        from_date = datetime.utcnow() - timedelta(days=days)
        
        async with agent.db_manager.get_session() as session:
            from sqlalchemy import select, func, cast, Date
            from agents.payment_repository import PaymentTransactionDB
            
            # Daily revenue
            daily_result = await session.execute(
                select(
                    cast(PaymentTransactionDB.created_at, Date).label('date'),
                    func.count(PaymentTransactionDB.transaction_id),
                    func.sum(PaymentTransactionDB.amount)
                )
                .where(PaymentTransactionDB.created_at >= from_date)
                .where(PaymentTransactionDB.status == TransactionStatus.COMPLETED)
                .group_by('date')
                .order_by('date')
            )
            daily_revenue = [
                {
                    "date": row[0].isoformat(),
                    "transactions": row[1],
                    "revenue": str(row[2] or Decimal('0'))
                }
                for row in daily_result.all()
            ]
            
            # Total revenue
            total_revenue = sum(
                Decimal(day["revenue"]) for day in daily_revenue
            )
            
            # Average transaction value
            total_transactions = sum(day["transactions"] for day in daily_revenue)
            avg_transaction_value = (
                total_revenue / total_transactions if total_transactions > 0 else Decimal('0')
            )
            
            return {
                "period_days": days,
                "from_date": from_date.isoformat(),
                "total_revenue": str(total_revenue),
                "total_transactions": total_transactions,
                "average_transaction_value": str(avg_transaction_value),
                "daily_revenue": daily_revenue,
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error("get_revenue_analytics_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PAYMENT_AGENT_PORT", 8004))
    uvicorn.run(agent.app, host="0.0.0.0", port=port)

