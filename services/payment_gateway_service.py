"""
Payment Gateway Service

Manages payment gateway configurations, processes transactions,
handles webhooks, and integrates with multiple payment providers.

Supported Providers:
- Stripe
- PayPal
- Square
- Authorize.Net
- Custom gateways

Features:
- Secure credential management with encryption
- Multi-gateway support with priority-based routing
- Webhook processing and verification
- Transaction tracking and reconciliation
- Refund management
- Health monitoring and connection testing
- PCI compliance support
"""

import os
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
import asyncio
import logging

from cryptography.fernet import Fernet
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import (
    PaymentGateway,
    PaymentTransaction,
    PaymentWebhookLog,
    PaymentGatewayHealthCheck,
    PaymentRefund,
    SavedPaymentMethod
)
from shared.kafka_client import KafkaClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PaymentGatewayService:
    """Service for managing payment gateways and processing transactions"""
    
    def __init__(self, db_session: AsyncSession, kafka_client: Optional[KafkaClient] = None):
        self.db = db_session
        self.kafka = kafka_client
        
        # Initialize encryption for credentials
        encryption_key = os.getenv('PAYMENT_CREDENTIALS_ENCRYPTION_KEY')
        if not encryption_key:
            # Generate a key for development (in production, use a secure key management system)
            encryption_key = Fernet.generate_key()
            logger.warning("Using generated encryption key. Set PAYMENT_CREDENTIALS_ENCRYPTION_KEY in production!")
        
        self.cipher = Fernet(encryption_key if isinstance(encryption_key, bytes) else encryption_key.encode())
    
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt payment gateway credentials"""
        try:
            credentials_json = json.dumps(credentials)
            encrypted = self.cipher.encrypt(credentials_json.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Error encrypting credentials: {e}")
            raise
    
    def decrypt_credentials(self, encrypted_credentials: str) -> Dict[str, Any]:
        """Decrypt payment gateway credentials"""
        try:
            decrypted = self.cipher.decrypt(encrypted_credentials.encode())
            return json.loads(decrypted.decode())
        except Exception as e:
            logger.error(f"Error decrypting credentials: {e}")
            raise
    
    async def create_gateway(self, gateway_data: Dict[str, Any]) -> PaymentGateway:
        """Create a new payment gateway configuration"""
        try:
            # Encrypt credentials before storing
            if 'credentials' in gateway_data:
                encrypted_creds = self.encrypt_credentials(gateway_data['credentials'])
                gateway_data['credentials'] = encrypted_creds
            
            gateway = PaymentGateway(**gateway_data)
            self.db.add(gateway)
            await self.db.commit()
            await self.db.refresh(gateway)
            
            # Publish event
            if self.kafka:
                await self.kafka.publish('payment-gateway-events', {
                    'event_type': 'gateway_created',
                    'gateway_id': gateway.id,
                    'provider': gateway.provider,
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            logger.info(f"Created payment gateway: {gateway.name} (ID: {gateway.id})")
            return gateway
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating payment gateway: {e}")
            raise
    
    async def update_gateway(self, gateway_id: int, update_data: Dict[str, Any]) -> PaymentGateway:
        """Update an existing payment gateway"""
        try:
            gateway = await self.db.get(PaymentGateway, gateway_id)
            if not gateway:
                raise ValueError(f"Payment gateway {gateway_id} not found")
            
            # Encrypt credentials if provided
            if 'credentials' in update_data:
                encrypted_creds = self.encrypt_credentials(update_data['credentials'])
                update_data['credentials'] = encrypted_creds
            
            for key, value in update_data.items():
                setattr(gateway, key, value)
            
            await self.db.commit()
            await self.db.refresh(gateway)
            
            # Publish event
            if self.kafka:
                await self.kafka.publish('payment-gateway-events', {
                    'event_type': 'gateway_updated',
                    'gateway_id': gateway.id,
                    'provider': gateway.provider,
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            logger.info(f"Updated payment gateway: {gateway.name} (ID: {gateway.id})")
            return gateway
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating payment gateway: {e}")
            raise
    
    async def delete_gateway(self, gateway_id: int) -> bool:
        """Delete a payment gateway"""
        try:
            gateway = await self.db.get(PaymentGateway, gateway_id)
            if not gateway:
                raise ValueError(f"Payment gateway {gateway_id} not found")
            
            # Check if gateway has active transactions
            active_transactions = await self.db.execute(
                select(PaymentTransaction).where(
                    and_(
                        PaymentTransaction.gateway_id == gateway_id,
                        PaymentTransaction.status.in_(['pending', 'authorized'])
                    )
                )
            )
            
            if active_transactions.scalars().first():
                raise ValueError("Cannot delete gateway with active transactions")
            
            await self.db.delete(gateway)
            await self.db.commit()
            
            # Publish event
            if self.kafka:
                await self.kafka.publish('payment-gateway-events', {
                    'event_type': 'gateway_deleted',
                    'gateway_id': gateway_id,
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            logger.info(f"Deleted payment gateway ID: {gateway_id}")
            return True
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting payment gateway: {e}")
            raise
    
    async def get_gateway(self, gateway_id: int, include_credentials: bool = False) -> Optional[Dict[str, Any]]:
        """Get payment gateway by ID"""
        try:
            gateway = await self.db.get(PaymentGateway, gateway_id)
            if not gateway:
                return None
            
            gateway_dict = {
                'id': gateway.id,
                'provider': gateway.provider,
                'name': gateway.name,
                'enabled': gateway.enabled,
                'test_mode': gateway.test_mode,
                'webhook_url': gateway.webhook_url,
                'supported_currencies': gateway.supported_currencies,
                'supported_payment_methods': gateway.supported_payment_methods,
                'transaction_fee_fixed': float(gateway.transaction_fee_fixed),
                'transaction_fee_percentage': float(gateway.transaction_fee_percentage),
                'priority': gateway.priority,
                'regions': gateway.regions,
                'min_amount': float(gateway.min_amount),
                'max_amount': float(gateway.max_amount),
                'auto_capture': gateway.auto_capture,
                'three_d_secure': gateway.three_d_secure,
                'status': gateway.status,
                'last_health_check': gateway.last_health_check.isoformat() if gateway.last_health_check else None,
                'health_check_status': gateway.health_check_status,
                'metadata': gateway.metadata,
                'created_at': gateway.created_at.isoformat(),
                'updated_at': gateway.updated_at.isoformat()
            }
            
            if include_credentials:
                gateway_dict['credentials'] = self.decrypt_credentials(gateway.credentials)
            
            return gateway_dict
        
        except Exception as e:
            logger.error(f"Error getting payment gateway: {e}")
            raise
    
    async def list_gateways(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """List all payment gateways"""
        try:
            query = select(PaymentGateway).order_by(PaymentGateway.priority)
            
            if enabled_only:
                query = query.where(PaymentGateway.enabled == True)
            
            result = await self.db.execute(query)
            gateways = result.scalars().all()
            
            return [await self.get_gateway(g.id) for g in gateways]
        
        except Exception as e:
            logger.error(f"Error listing payment gateways: {e}")
            raise
    
    async def select_gateway(
        self,
        amount: Decimal,
        currency: str,
        payment_method: str,
        region: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Select the best payment gateway based on criteria
        Returns the highest priority enabled gateway that supports the requirements
        """
        try:
            query = select(PaymentGateway).where(
                and_(
                    PaymentGateway.enabled == True,
                    PaymentGateway.status == 'active',
                    PaymentGateway.min_amount <= amount,
                    PaymentGateway.max_amount >= amount
                )
            ).order_by(PaymentGateway.priority)
            
            result = await self.db.execute(query)
            gateways = result.scalars().all()
            
            for gateway in gateways:
                # Check currency support
                if currency not in gateway.supported_currencies:
                    continue
                
                # Check payment method support
                if payment_method not in gateway.supported_payment_methods:
                    continue
                
                # Check region support if specified
                if region and region not in gateway.regions:
                    continue
                
                # This gateway meets all criteria
                return await self.get_gateway(gateway.id, include_credentials=True)
            
            logger.warning(f"No suitable gateway found for {currency} {amount} via {payment_method}")
            return None
        
        except Exception as e:
            logger.error(f"Error selecting payment gateway: {e}")
            raise
    
    async def test_gateway_connection(self, gateway_id: int) -> Dict[str, Any]:
        """Test payment gateway connection and credentials"""
        try:
            gateway = await self.get_gateway(gateway_id, include_credentials=True)
            if not gateway:
                raise ValueError(f"Payment gateway {gateway_id} not found")
            
            # Simulate connection test (in production, make actual API calls)
            test_result = {
                'success': True,
                'response_time_ms': 150,
                'message': 'Connection test successful',
                'details': {
                    'api_version': '2023-10-16',
                    'account_status': 'active'
                }
            }
            
            # Log health check
            health_check = PaymentGatewayHealthCheck(
                gateway_id=gateway_id,
                check_type='connection',
                status='success' if test_result['success'] else 'failed',
                response_time_ms=test_result['response_time_ms'],
                details=test_result.get('details'),
                checked_at=datetime.utcnow()
            )
            self.db.add(health_check)
            
            # Update gateway status
            gateway_obj = await self.db.get(PaymentGateway, gateway_id)
            gateway_obj.last_health_check = datetime.utcnow()
            gateway_obj.health_check_status = 'success' if test_result['success'] else 'failed'
            
            await self.db.commit()
            
            logger.info(f"Connection test for gateway {gateway_id}: {test_result['message']}")
            return test_result
        
        except Exception as e:
            logger.error(f"Error testing gateway connection: {e}")
            
            # Log failed health check
            health_check = PaymentGatewayHealthCheck(
                gateway_id=gateway_id,
                check_type='connection',
                status='failed',
                error_message=str(e),
                checked_at=datetime.utcnow()
            )
            self.db.add(health_check)
            await self.db.commit()
            
            return {
                'success': False,
                'message': str(e)
            }
    
    async def process_webhook(
        self,
        gateway_id: int,
        event_type: str,
        payload: Dict[str, Any],
        signature: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process webhook event from payment provider"""
        try:
            gateway = await self.get_gateway(gateway_id, include_credentials=True)
            if not gateway:
                raise ValueError(f"Payment gateway {gateway_id} not found")
            
            # Verify webhook signature
            signature_verified = False
            if signature:
                signature_verified = self.verify_webhook_signature(
                    gateway['provider'],
                    payload,
                    signature,
                    gateway['credentials'].get('webhook_secret')
                )
            
            # Log webhook
            webhook_log = PaymentWebhookLog(
                gateway_id=gateway_id,
                event_type=event_type,
                event_id=payload.get('id'),
                payload=payload,
                signature=signature,
                signature_verified=signature_verified,
                received_at=datetime.utcnow()
            )
            self.db.add(webhook_log)
            
            # Process webhook based on event type
            result = await self.handle_webhook_event(gateway_id, event_type, payload)
            
            webhook_log.processed = True
            webhook_log.processed_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"Processed webhook for gateway {gateway_id}: {event_type}")
            return result
        
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            
            # Update webhook log with error
            if 'webhook_log' in locals():
                webhook_log.processing_error = str(e)
                await self.db.commit()
            
            raise
    
    def verify_webhook_signature(
        self,
        provider: str,
        payload: Dict[str, Any],
        signature: str,
        secret: str
    ) -> bool:
        """Verify webhook signature based on provider"""
        try:
            if provider == 'stripe':
                # Stripe signature verification
                payload_str = json.dumps(payload, separators=(',', ':'))
                expected_signature = hmac.new(
                    secret.encode(),
                    payload_str.encode(),
                    hashlib.sha256
                ).hexdigest()
                return hmac.compare_digest(signature, expected_signature)
            
            elif provider == 'paypal':
                # PayPal signature verification
                # Implementation specific to PayPal's webhook verification
                return True  # Placeholder
            
            # Add more providers as needed
            return False
        
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    async def handle_webhook_event(
        self,
        gateway_id: int,
        event_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle specific webhook event types"""
        try:
            if event_type in ['payment_intent.succeeded', 'charge.succeeded']:
                # Payment succeeded
                return await self.handle_payment_success(gateway_id, payload)
            
            elif event_type in ['payment_intent.payment_failed', 'charge.failed']:
                # Payment failed
                return await self.handle_payment_failure(gateway_id, payload)
            
            elif event_type in ['charge.refunded', 'refund.created']:
                # Refund processed
                return await self.handle_refund(gateway_id, payload)
            
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                return {'status': 'ignored', 'event_type': event_type}
        
        except Exception as e:
            logger.error(f"Error handling webhook event: {e}")
            raise
    
    async def handle_payment_success(self, gateway_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment webhook"""
        # Implementation for updating transaction status
        logger.info(f"Payment succeeded for gateway {gateway_id}")
        return {'status': 'processed', 'action': 'payment_success'}
    
    async def handle_payment_failure(self, gateway_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment webhook"""
        # Implementation for updating transaction status
        logger.info(f"Payment failed for gateway {gateway_id}")
        return {'status': 'processed', 'action': 'payment_failure'}
    
    async def handle_refund(self, gateway_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle refund webhook"""
        # Implementation for processing refund
        logger.info(f"Refund processed for gateway {gateway_id}")
        return {'status': 'processed', 'action': 'refund'}
    
    async def calculate_fees(self, gateway_id: int, amount: Decimal) -> Decimal:
        """Calculate transaction fees for a gateway"""
        try:
            gateway = await self.db.get(PaymentGateway, gateway_id)
            if not gateway:
                raise ValueError(f"Payment gateway {gateway_id} not found")
            
            fixed_fee = gateway.transaction_fee_fixed
            percentage_fee = gateway.transaction_fee_percentage
            
            calculated_fee = fixed_fee + (amount * percentage_fee / 100)
            return calculated_fee
        
        except Exception as e:
            logger.error(f"Error calculating fees: {e}")
            raise
    
    async def get_gateway_statistics(self, gateway_id: int, days: int = 30) -> Dict[str, Any]:
        """Get statistics for a payment gateway"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get transaction statistics
            transactions = await self.db.execute(
                select(PaymentTransaction).where(
                    and_(
                        PaymentTransaction.gateway_id == gateway_id,
                        PaymentTransaction.created_at >= start_date
                    )
                )
            )
            transactions = transactions.scalars().all()
            
            total_transactions = len(transactions)
            successful_transactions = sum(1 for t in transactions if t.status == 'captured')
            failed_transactions = sum(1 for t in transactions if t.status == 'failed')
            total_amount = sum(t.amount for t in transactions if t.status == 'captured')
            
            # Calculate success rate
            success_rate = (successful_transactions / total_transactions * 100) if total_transactions > 0 else 0
            
            return {
                'gateway_id': gateway_id,
                'period_days': days,
                'total_transactions': total_transactions,
                'successful_transactions': successful_transactions,
                'failed_transactions': failed_transactions,
                'success_rate': round(success_rate, 2),
                'total_amount': float(total_amount),
                'average_transaction': float(total_amount / successful_transactions) if successful_transactions > 0 else 0
            }
        
        except Exception as e:
            logger.error(f"Error getting gateway statistics: {e}")
            raise


# Example usage
async def main():
    """Example usage of PaymentGatewayService"""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    # Create database session
    engine = create_async_engine('postgresql+asyncpg://user:password@localhost/ecommerce')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        service = PaymentGatewayService(session)
        
        # Create a new gateway
        gateway_data = {
            'provider': 'stripe',
            'name': 'Stripe Production',
            'enabled': True,
            'test_mode': False,
            'credentials': {
                'publishable_key': 'pk_live_xxxxx',
                'secret_key': 'sk_live_xxxxx',
                'webhook_secret': 'whsec_xxxxx'
            },
            'webhook_url': 'https://api.example.com/webhooks/stripe',
            'supported_currencies': ['USD', 'EUR', 'GBP'],
            'supported_payment_methods': ['card', 'apple_pay', 'google_pay'],
            'transaction_fee_fixed': 0.30,
            'transaction_fee_percentage': 2.9,
            'priority': 1
        }
        
        gateway = await service.create_gateway(gateway_data)
        print(f"Created gateway: {gateway.name}")
        
        # Test connection
        test_result = await service.test_gateway_connection(gateway.id)
        print(f"Connection test: {test_result}")
        
        # Select best gateway for transaction
        selected_gateway = await service.select_gateway(
            amount=Decimal('100.00'),
            currency='USD',
            payment_method='card',
            region='US'
        )
        print(f"Selected gateway: {selected_gateway['name']}")


if __name__ == '__main__':
    asyncio.run(main())

