"""
Notification Agent - Multi-Agent E-Commerce System

This agent provides multi-channel notification management (email, SMS, push, in-app).
"""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID
from enum import Enum

from shared.db_helpers import DatabaseHelper

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

class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"

    async def initialize(self):
        """Initialize agent."""
        await super().initialize()
        
    async def cleanup(self):
        """Cleanup agent."""
        await super().cleanup()
        
    async def process_business_logic(self, data):
        """Process business logic."""
        return {"status": "success"}


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


# =====================================================
# PYDANTIC MODELS
# =====================================================

class NotificationTemplate(BaseModel):
    template_id: int
    template_name: str
    template_code: str
    channel: NotificationChannel
    category: str
    subject: Optional[str] = None
    body_text: str
    language: str = "en"
    is_active: bool = True

    class Config:
        from_attributes = True


class NotificationCreate(BaseModel):
    template_code: Optional[str] = None
    recipient_id: str
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    channel: NotificationChannel
    subject: Optional[str] = None
    body: str
    context_type: Optional[str] = None
    context_id: Optional[str] = None
    metadata: Dict[str, Any] = {}


class Notification(NotificationCreate):
    notification_id: UUID
    notification_status: NotificationStatus = NotificationStatus.PENDING
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    error_message: Optional[str] = None
    provider: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationPreferences(BaseModel):
    customer_id: str
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True
    in_app_enabled: bool = True
    order_notifications: bool = True
    shipping_notifications: bool = True
    payment_notifications: bool = True
    marketing_notifications: bool = False
    system_notifications: bool = True


# =====================================================
# REPOSITORY
# =====================================================

class NotificationRepository:
    """Repository for notification operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def get_template(self, template_code: str) -> Optional[NotificationTemplate]:
        """Get notification template by code."""
        query = "SELECT * FROM notification_templates WHERE template_code = $1 AND is_active = true"
        result = await self.db.fetch_one(query, template_code)
        return NotificationTemplate(**result) if result else None
    
    async def create_notification(self, notification: NotificationCreate) -> Notification:
        """Create a new notification."""
        query = """
            INSERT INTO notifications (recipient_id, recipient_email, recipient_phone,
                                      channel, subject, body, context_type, context_id, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
        """
        result = await self.db.fetch_one(
            query, notification.recipient_id, notification.recipient_email,
            notification.recipient_phone, notification.channel.value,
            notification.subject, notification.body, notification.context_type,
            notification.context_id, str(notification.metadata)
        )
        return Notification(**result)
    
    async def update_notification_status(
        self,
        notification_id: UUID,
        status: NotificationStatus,
        error_message: Optional[str] = None
    ) -> Optional[Notification]:
        """Update notification status."""
        query = """
            UPDATE notifications 
            SET notification_status = $2,
                sent_at = CASE WHEN $2 = 'sent' THEN CURRENT_TIMESTAMP ELSE sent_at END,
                delivered_at = CASE WHEN $2 = 'delivered' THEN CURRENT_TIMESTAMP ELSE delivered_at END,
                failed_at = CASE WHEN $2 = 'failed' THEN CURRENT_TIMESTAMP ELSE failed_at END,
                error_message = $3
            WHERE notification_id = $1
            RETURNING *
        """
        result = await self.db.fetch_one(query, notification_id, status.value, error_message)
        return Notification(**result) if result else None
    
    async def get_notification(self, notification_id: UUID) -> Optional[Notification]:
        """Get notification by ID."""
        query = "SELECT * FROM notifications WHERE notification_id = $1"
        result = await self.db.fetch_one(query, notification_id)
        return Notification(**result) if result else None
    
    async def get_customer_notifications(
        self,
        customer_id: str,
        limit: int = 50
    ) -> List[Notification]:
        """Get notifications for a customer."""
        query = """
            SELECT * FROM notifications 
            WHERE recipient_id = $1 
            ORDER BY created_at DESC 
            LIMIT $2
        """
        results = await self.db.fetch_all(query, customer_id, limit)
        return [Notification(**r) for r in results]
    
    async def get_preferences(self, customer_id: str) -> Optional[NotificationPreferences]:
        """Get customer notification preferences."""
        query = "SELECT * FROM notification_preferences WHERE customer_id = $1"
        result = await self.db.fetch_one(query, customer_id)
        return NotificationPreferences(**result) if result else None
    
    async def update_preferences(
        self,
        preferences: NotificationPreferences
    ) -> NotificationPreferences:
        """Update customer notification preferences."""
        query = """
            INSERT INTO notification_preferences (
                customer_id, email_enabled, sms_enabled, push_enabled, in_app_enabled,
                order_notifications, shipping_notifications, payment_notifications,
                marketing_notifications, system_notifications
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (customer_id) DO UPDATE SET
                email_enabled = EXCLUDED.email_enabled,
                sms_enabled = EXCLUDED.sms_enabled,
                push_enabled = EXCLUDED.push_enabled,
                in_app_enabled = EXCLUDED.in_app_enabled,
                order_notifications = EXCLUDED.order_notifications,
                shipping_notifications = EXCLUDED.shipping_notifications,
                payment_notifications = EXCLUDED.payment_notifications,
                marketing_notifications = EXCLUDED.marketing_notifications,
                system_notifications = EXCLUDED.system_notifications
            RETURNING *
        """
        result = await self.db.fetch_one(
            query, preferences.customer_id, preferences.email_enabled,
            preferences.sms_enabled, preferences.push_enabled, preferences.in_app_enabled,
            preferences.order_notifications, preferences.shipping_notifications,
            preferences.payment_notifications, preferences.marketing_notifications,
            preferences.system_notifications
        )
        return NotificationPreferences(**result)


# =====================================================
# SERVICE
# =====================================================

class NotificationService:
    """Service for notification operations."""
    
    def __init__(self, repo: NotificationRepository):
        self.repo = repo
    
    async def send_notification(
        self,
        notification_data: NotificationCreate
    ) -> Dict[str, Any]:
        """Send a notification."""
        # Create notification record
        notification = await self.repo.create_notification(notification_data)
        
        # Check customer preferences
        preferences = await self.repo.get_preferences(notification_data.recipient_id)
        if preferences:
            channel_enabled = getattr(preferences, f"{notification_data.channel.value}_enabled", True)
            if not channel_enabled:
                await self.repo.update_notification_status(
                    notification.notification_id,
                    NotificationStatus.FAILED,
                    "Channel disabled by customer preferences"
                )
                return {
                    "notification": notification,
                    "success": False,
                    "message": "Channel disabled by customer preferences"
                }
        
        # Simulate sending (in production, integrate with actual providers)
        try:
            # Simulate provider call
            await self._send_via_provider(notification)
            
            # Update status
            notification = await self.repo.update_notification_status(
                notification.notification_id,
                NotificationStatus.SENT
            )
            
            logger.info(
                "notification_sent",
                notification_id=str(notification.notification_id),
                channel=notification_data.channel.value,
                recipient=notification_data.recipient_id
            )
            
            return {
                "notification": notification,
                "success": True,
                "message": "Notification sent successfully"
            }
            
        except Exception as e:
            # Update status as failed
            notification = await self.repo.update_notification_status(
                notification.notification_id,
                NotificationStatus.FAILED,
                str(e)
            )
            
            logger.error(
                "notification_failed",
                notification_id=str(notification.notification_id),
                error=str(e)
            )
            
            raise ValueError(f"Failed to send notification: {str(e)}")
    
    async def _send_via_provider(self, notification: Notification):
        """Send notification via provider (simulated)."""
        # In production, integrate with:
        # - Email: SendGrid, AWS SES, Mailgun
        # - SMS: Twilio, AWS SNS
        # - Push: FCM, APNs
        await asyncio.sleep(0.1)  # Simulate API call


# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI(
    title="Notification Agent API",
    description="Multi-channel notification management",
    version="1.0.0"
)


async def get_notification_service() -> NotificationService:
    """Dependency injection for notification service."""
    db_manager = await get_database_manager()
    repo = NotificationRepository(db_manager)
    return NotificationService(repo)


# =====================================================
# API ENDPOINTS
# =====================================================

@app.post("/api/v1/notifications/send", response_model=Dict[str, Any])
async def send_notification(
    notification: NotificationCreate = Body(...),
    service: NotificationService = Depends(get_notification_service)
):
    """Send a notification."""
    try:
        result = await service.send_notification(notification)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("send_notification_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/notifications/{notification_id}", response_model=Notification)
async def get_notification(
    notification_id: UUID = Path(...),
    service: NotificationService = Depends(get_notification_service)
):
    """Get notification by ID."""
    try:
        notification = await service.repo.get_notification(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_notification_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/notifications/customer/{customer_id}", response_model=List[Notification])
async def get_customer_notifications(
    customer_id: str = Path(...),
    limit: int = Query(50, ge=1, le=100),
    service: NotificationService = Depends(get_notification_service)
):
    """Get notifications for a customer."""
    try:
        notifications = await service.repo.get_customer_notifications(customer_id, limit)
        return notifications
    except Exception as e:
        logger.error("get_customer_notifications_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/notifications/preferences/{customer_id}", response_model=NotificationPreferences)
async def get_preferences(
    customer_id: str = Path(...),
    service: NotificationService = Depends(get_notification_service)
):
    """Get customer notification preferences."""
    try:
        preferences = await service.repo.get_preferences(customer_id)
        if not preferences:
            # Return default preferences
            return NotificationPreferences(customer_id=customer_id)
        return preferences
    except Exception as e:
        logger.error("get_preferences_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/notifications/preferences", response_model=NotificationPreferences)
async def update_preferences(
    preferences: NotificationPreferences = Body(...),
    service: NotificationService = Depends(get_notification_service)
):
    """Update customer notification preferences."""
    try:
        result = await service.repo.update_preferences(preferences)
        return result
    except Exception as e:
        logger.error("update_preferences_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "notification_agent", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)

