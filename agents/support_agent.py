from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

"""
Support Agent - Multi-Agent E-Commerce System

This agent manages customer support tickets, SLA tracking, escalation workflows,
knowledge base integration, and multi-channel support.

DATABASE SCHEMA (migration 019_support_agent.sql):

CREATE TABLE support_tickets (
    ticket_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'open', -- 'open', 'in_progress', 'waiting_customer', 'resolved', 'closed'
    priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
    category VARCHAR(100), -- 'order', 'product', 'payment', 'shipping', 'technical', 'other'
    assigned_to VARCHAR(100),
    channel VARCHAR(50), -- 'email', 'chat', 'phone', 'web'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    closed_at TIMESTAMP
);

CREATE TABLE ticket_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID REFERENCES support_tickets(ticket_id),
    sender_id VARCHAR(100) NOT NULL,
    sender_type VARCHAR(20) NOT NULL, -- 'customer', 'agent', 'system'
    message_body TEXT NOT NULL,
    attachments JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sla_policies (
    policy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    priority VARCHAR(20) NOT NULL,
    first_response_minutes INTEGER NOT NULL,
    resolution_minutes INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE sla_tracking (
    tracking_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID REFERENCES support_tickets(ticket_id),
    first_response_due TIMESTAMP,
    first_response_at TIMESTAMP,
    resolution_due TIMESTAMP,
    resolved_at TIMESTAMP,
    first_response_breached BOOLEAN DEFAULT false,
    resolution_breached BOOLEAN DEFAULT false
);

CREATE TABLE ticket_escalations (
    escalation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID REFERENCES support_tickets(ticket_id),
    escalated_from VARCHAR(100),
    escalated_to VARCHAR(100) NOT NULL,
    escalation_reason TEXT,
    escalated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID
from enum import Enum

from sqlalchemy import Column, String, TIMESTAMP, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.future import select
from sqlalchemy.sql import func

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field
import structlog
import uvicorn

# Configure logging
logger = structlog.get_logger(__name__)

# Add project root to sys.path for shared modules FIRST
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import shared modules
from shared.db_helpers import DatabaseHelper
from shared.database import DatabaseManager, get_database_manager
from shared.base_agent_v2 import BaseAgentV2, AgentMessage, MessageType

# ENUMS
class TicketStatus(str, Enum):
    """Enum for the status of a support ticket."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    """Enum for the priority of a support ticket."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class SenderType(str, Enum):
    """Enum for the type of sender in a ticket message."""
    CUSTOMER = "customer"
    AGENT = "agent"
    SYSTEM = "system"

# SQLAlchemy Base - import from shared models
from shared.models import Base

# SQLAlchemy Models
class SupportTicketDB(Base):
    """SQLAlchemy model for the support_tickets table."""
    __tablename__ = "support_tickets"

    ticket_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    ticket_number = Column(String(50), unique=True, nullable=False)
    customer_id = Column(String(100), nullable=False)
    subject = Column(String(500), nullable=False)
    description = Column(String)
    status = Column(String(50), default=TicketStatus.OPEN.value)
    priority = Column(String(20), default=TicketPriority.MEDIUM.value)
    category = Column(String(100))
    assigned_to = Column(String(100))
    channel = Column(String(50))
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    resolved_at = Column(TIMESTAMP)
    closed_at = Column(TIMESTAMP)

    messages = relationship("TicketMessageDB", back_populates="ticket", cascade="all, delete-orphan")
    sla_tracking = relationship("SLATrackingDB", back_populates="ticket", uselist=False, cascade="all, delete-orphan")
    escalations = relationship("TicketEscalationDB", back_populates="ticket", cascade="all, delete-orphan")

class TicketMessageDB(Base):
    """SQLAlchemy model for the ticket_messages table."""
    __tablename__ = "ticket_messages"

    message_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    ticket_id = Column(PG_UUID(as_uuid=True), ForeignKey("support_tickets.ticket_id"), nullable=False)
    sender_id = Column(String(100), nullable=False)
    sender_type = Column(String(20), nullable=False)
    message_body = Column(String, nullable=False)
    attachments = Column(JSONB)
    created_at = Column(TIMESTAMP, default=func.now())

    ticket = relationship("SupportTicketDB", back_populates="messages")

class SLAPolicyDB(Base):
    """SQLAlchemy model for the sla_policies table."""
    __tablename__ = "sla_policies"

    policy_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    priority = Column(String(20), nullable=False, unique=True)
    first_response_minutes = Column(Integer, nullable=False)
    resolution_minutes = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)

class SLATrackingDB(Base):
    """SQLAlchemy model for the sla_tracking table."""
    __tablename__ = "sla_tracking"

    tracking_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    ticket_id = Column(PG_UUID(as_uuid=True), ForeignKey("support_tickets.ticket_id"), nullable=False)
    first_response_due = Column(TIMESTAMP)
    first_response_at = Column(TIMESTAMP)
    resolution_due = Column(TIMESTAMP)
    resolved_at = Column(TIMESTAMP)
    first_response_breached = Column(Boolean, default=False)
    resolution_breached = Column(Boolean, default=False)

    ticket = relationship("SupportTicketDB", back_populates="sla_tracking")

class TicketEscalationDB(Base):
    """SQLAlchemy model for the ticket_escalations table."""
    __tablename__ = "ticket_escalations"

    escalation_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    ticket_id = Column(PG_UUID(as_uuid=True), ForeignKey("support_tickets.ticket_id"), nullable=False)
    escalated_from = Column(String(100))
    escalated_to = Column(String(100), nullable=False)
    escalation_reason = Column(String)
    escalated_at = Column(TIMESTAMP, default=func.now())

    ticket = relationship("SupportTicketDB", back_populates="escalations")


# Pydantic Models
class TicketCreate(BaseModel):
    """Pydantic model for creating a new support ticket."""
    customer_id: str = Field(..., description="ID of the customer creating the ticket")
    subject: str = Field(..., description="Subject of the support ticket")
    description: str = Field(..., description="Detailed description of the issue")
    priority: TicketPriority = Field(TicketPriority.MEDIUM, description="Priority level of the ticket")
    category: Optional[str] = Field(None, description="Category of the support ticket (e.g., order, product)")
    channel: str = Field("web", description="Channel through which the ticket was created (e.g., web, email)")

class Ticket(BaseModel):
    """Pydantic model for a support ticket, including its ID and current status."""
    ticket_id: UUID = Field(..., description="Unique identifier for the ticket")
    ticket_number: str = Field(..., description="Human-readable ticket number")
    customer_id: str = Field(..., description="ID of the customer")
    subject: str = Field(..., description="Subject of the ticket")
    description: Optional[str] = Field(None, description="Detailed description of the issue")
    status: TicketStatus = Field(..., description="Current status of the ticket")
    priority: TicketPriority = Field(..., description="Priority level of the ticket")
    category: Optional[str] = Field(None, description="Category of the ticket")
    assigned_to: Optional[str] = Field(None, description="Agent assigned to the ticket")
    channel: Optional[str] = Field(None, description="Channel through which the ticket was created")
    created_at: datetime = Field(..., description="Timestamp when the ticket was created")
    updated_at: datetime = Field(..., description="Timestamp when the ticket was last updated")
    resolved_at: Optional[datetime] = Field(None, description="Timestamp when the ticket was resolved")
    closed_at: Optional[datetime] = Field(None, description="Timestamp when the ticket was closed")

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    """Pydantic model for creating a new message within a ticket."""
    ticket_id: UUID = Field(..., description="ID of the ticket this message belongs to")
    sender_id: str = Field(..., description="ID of the sender (customer or agent)")
    sender_type: SenderType = Field(..., description="Type of the sender (customer, agent, or system)")
    message_body: str = Field(..., description="Content of the message")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Optional list of attachments")

class TicketMessage(BaseModel):
    """Pydantic model for a ticket message."""
    message_id: UUID = Field(..., description="Unique identifier for the message")
    ticket_id: UUID = Field(..., description="ID of the ticket this message belongs to")
    sender_id: str = Field(..., description="ID of the sender")
    sender_type: SenderType = Field(..., description="Type of the sender")
    message_body: str = Field(..., description="Content of the message")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Optional list of attachments")
    created_at: datetime = Field(..., description="Timestamp when the message was created")

    class Config:
        from_attributes = True

class TicketUpdate(BaseModel):
    """Pydantic model for updating an existing support ticket."""
    status: Optional[TicketStatus] = Field(None, description="New status for the ticket")
    priority: Optional[TicketPriority] = Field(None, description="New priority for the ticket")
    assigned_to: Optional[str] = Field(None, description="ID of the agent to assign the ticket to")

class EscalationCreate(BaseModel):
    """Pydantic model for escalating a support ticket."""
    ticket_id: UUID = Field(..., description="ID of the ticket to escalate")
    escalated_to: str = Field(..., description="ID of the agent/team to escalate the ticket to")
    escalation_reason: str = Field(..., description="Reason for the escalation")

class SLAStatus(BaseModel):
    """Pydantic model for reporting SLA status of a ticket."""
    ticket_id: UUID = Field(..., description="ID of the ticket")
    first_response_due: datetime = Field(..., description="Timestamp when the first response is due")
    first_response_breached: bool = Field(..., description="True if first response SLA is breached")
    resolution_due: datetime = Field(..., description="Timestamp when resolution is due")
    resolution_breached: bool = Field(..., description="True if resolution SLA is breached")
    minutes_until_breach: Optional[int] = Field(None, description="Minutes remaining until resolution SLA breach, if not breached")

# REPOSITORY
class SupportRepository:
    """Repository for handling database operations related to support tickets and SLAs."""
    def __init__(self, db_manager: DatabaseManager, db_helper: DatabaseHelper):
        """Initializes the SupportRepository with a database manager and helper."""
        self.db_manager = db_manager
        self.db_helper = db_helper
        logger.info("SupportRepository initialized")

    async def create_ticket(self, ticket_data: TicketCreate) -> Ticket:
        """Creates a new support ticket in the database.

        Args:
            ticket_data (TicketCreate): Data for creating the new ticket.

        Returns:
            Ticket: The newly created ticket.

        Raises:
            Exception: If there is an error during database operation.
        """
        try:
            ticket_number = f"TKT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
            async with self.db_manager.get_session() as session:
                new_ticket_db = SupportTicketDB(
                    ticket_number=ticket_number,
                    customer_id=ticket_data.customer_id,
                    subject=ticket_data.subject,
                    description=ticket_data.description,
                    priority=ticket_data.priority.value,
                    category=ticket_data.category,
                    channel=ticket_data.channel
                )
                created_ticket = await self.db_helper.create(session, new_ticket_db)
                await self._create_sla_tracking(session, created_ticket.ticket_id, created_ticket.priority)
                logger.info("Ticket created successfully", ticket_id=str(created_ticket.ticket_id))
                return Ticket.model_validate(created_ticket)
        except Exception as e:
            logger.error("Failed to create ticket", error=str(e), ticket_data=ticket_data.model_dump_json())
            raise

    async def _create_sla_tracking(self, session, ticket_id: UUID, priority: str) -> None:
        """Creates SLA tracking entry for a given ticket.

        Args:
            session: The database session.
            ticket_id (UUID): The ID of the ticket.
            priority (str): The priority of the ticket.

        Raises:
            Exception: If there is an error during database operation.
        """
        try:
            policy = await self.db_helper.get_by_id(session, SLAPolicyDB, priority, id_column='priority')

            if not policy:
                # Default SLA if no policy found for priority
                first_response_minutes = int(os.getenv("DEFAULT_SLA_FIRST_RESPONSE_MINUTES", 60))
                resolution_minutes = int(os.getenv("DEFAULT_SLA_RESOLUTION_MINUTES", 1440)) # 24 hours
                logger.warning("No SLA policy found for priority, using defaults", priority=priority)
            else:
                first_response_minutes = policy.first_response_minutes
                resolution_minutes = policy.resolution_minutes

            now = datetime.utcnow()
            first_response_due = now + timedelta(minutes=first_response_minutes)
            resolution_due = now + timedelta(minutes=resolution_minutes)

            new_sla_tracking = SLATrackingDB(
                ticket_id=ticket_id,
                first_response_due=first_response_due,
                resolution_due=resolution_due
            )
            await self.db_helper.create(session, new_sla_tracking)
            logger.info("SLA tracking created", ticket_id=str(ticket_id), priority=priority)
        except Exception as e:
            logger.error("Failed to create SLA tracking", error=str(e), ticket_id=str(ticket_id))
            raise

    async def get_ticket(self, ticket_id: UUID) -> Optional[Ticket]:
        """Retrieves a support ticket by its ID.

        Args:
            ticket_id (UUID): The unique identifier of the ticket.

        Returns:
            Optional[Ticket]: The ticket if found, otherwise None.

        Raises:
            Exception: If there is an error during database operation.
        """
        try:
            async with self.db_manager.get_session() as session:
                ticket_db = await self.db_helper.get_by_id(session, SupportTicketDB, ticket_id)
                if ticket_db:
                    logger.info("Ticket retrieved", ticket_id=str(ticket_id))
                    return Ticket.model_validate(ticket_db)
                logger.info("Ticket not found", ticket_id=str(ticket_id))
                return None
        except Exception as e:
            logger.error("Failed to get ticket", error=str(e), ticket_id=str(ticket_id))
            raise

    async def update_ticket(self, ticket_id: UUID, update_data: TicketUpdate) -> Optional[Ticket]:
        """Updates an existing support ticket.

        Args:
            ticket_id (UUID): The unique identifier of the ticket to update.
            update_data (TicketUpdate): The data to update the ticket with.

        Returns:
            Optional[Ticket]: The updated ticket if found, otherwise None.

        Raises:
            Exception: If there is an error during database operation.
        """
        try:
            async with self.db_manager.get_session() as session:
                ticket_db = await self.db_helper.get_by_id(session, SupportTicketDB, ticket_id)
                if not ticket_db:
                    logger.warning("Ticket not found for update", ticket_id=str(ticket_id))
                    return None

                update_fields = update_data.model_dump(exclude_unset=True)
                if "status" in update_fields:
                    ticket_db.status = update_fields["status"]
                    if ticket_db.status == TicketStatus.RESOLVED.value:
                        ticket_db.resolved_at = datetime.utcnow()
                    elif ticket_db.status == TicketStatus.CLOSED.value:
                        ticket_db.closed_at = datetime.utcnow()
                if "priority" in update_fields:
                    ticket_db.priority = update_fields["priority"]
                if "assigned_to" in update_fields:
                    ticket_db.assigned_to = update_fields["assigned_to"]

                updated_ticket = await self.db_helper.update(session, ticket_db)
                logger.info("Ticket updated successfully", ticket_id=str(ticket_id), updates=update_fields)
                return Ticket.model_validate(updated_ticket)
        except Exception as e:
            logger.error("Failed to update ticket", error=str(e), ticket_id=str(ticket_id), update_data=update_data.model_dump_json())
            raise

    async def add_message(self, message_data: MessageCreate) -> UUID:
        """Adds a new message to a support ticket.

        Args:
            message_data (MessageCreate): Data for the new message.

        Returns:
            UUID: The ID of the newly created message.

        Raises:
            Exception: If there is an error during database operation.
        """
        try:
            async with self.db_manager.get_session() as session:
                new_message_db = TicketMessageDB(
                    ticket_id=message_data.ticket_id,
                    sender_id=message_data.sender_id,
                    sender_type=message_data.sender_type.value,
                    message_body=message_data.message_body,
                    attachments=message_data.attachments
                )
                created_message = await self.db_helper.create(session, new_message_db)

                # Update first response SLA if this is agent's first response
                if message_data.sender_type == SenderType.AGENT:
                    await self._update_first_response_sla(session, message_data.ticket_id)

                logger.info("Message added successfully", message_id=str(created_message.message_id), ticket_id=str(message_data.ticket_id))
                return created_message.message_id
        except Exception as e:
            logger.error("Failed to add message", error=str(e), message_data=message_data.model_dump_json())
            raise

    async def _update_first_response_sla(self, session, ticket_id: UUID) -> None:
        """Updates the first response SLA for a ticket if not already recorded.

        Args:
            session: The database session.
            ticket_id (UUID): The ID of the ticket.

        Raises:
            Exception: If there is an error during database operation.
        """
        try:
            sla_tracking_db = await self.db_helper.get_by_id(session, SLATrackingDB, ticket_id, id_column='ticket_id')
            if sla_tracking_db and not sla_tracking_db.first_response_at:
                now = datetime.utcnow()
                sla_tracking_db.first_response_at = now
                sla_tracking_db.first_response_breached = (now > sla_tracking_db.first_response_due)
                await self.db_helper.update(session, sla_tracking_db)
                logger.info("First response SLA updated", ticket_id=str(ticket_id))
        except Exception as e:
            logger.error("Failed to update first response SLA", error=str(e), ticket_id=str(ticket_id))
            raise

    async def get_ticket_messages(self, ticket_id: UUID) -> List[TicketMessage]:
        """Retrieves all messages for a specific ticket.

        Args:
            ticket_id (UUID): The ID of the ticket.

        Returns:
            List[TicketMessage]: A list of messages for the ticket.

        Raises:
            Exception: If there is an error during database operation.
        """
        try:
            async with self.db_manager.get_session() as session:
                messages_db = await self.db_helper.get_all(session, TicketMessageDB, filter_by={'ticket_id': ticket_id}, order_by='created_at')
                logger.info("Messages retrieved for ticket", ticket_id=str(ticket_id), count=len(messages_db))
                return [TicketMessage.model_validate(msg) for msg in messages_db]
        except Exception as e:
            logger.error("Failed to get ticket messages", error=str(e), ticket_id=str(ticket_id))
            raise

    async def escalate_ticket(self, escalation_data: EscalationCreate) -> UUID:
        """Escalates a support ticket and updates its assignment.

        Args:
            escalation_data (EscalationCreate): Data for the escalation.

        Returns:
            UUID: The ID of the newly created escalation record.

        Raises:
            Exception: If there is an error during database operation.
        """
        try:
            async with self.db_manager.get_session() as session:
                new_escalation_db = TicketEscalationDB(
                    ticket_id=escalation_data.ticket_id,
                    escalated_to=escalation_data.escalated_to,
                    escalation_reason=escalation_data.escalation_reason
                )
                created_escalation = await self.db_helper.create(session, new_escalation_db)

                # Update ticket assignment
                ticket_db = await self.db_helper.get_by_id(session, SupportTicketDB, escalation_data.ticket_id)
                if ticket_db:
                    ticket_db.assigned_to = escalation_data.escalated_to
                    await self.db_helper.update(session, ticket_db)
                    logger.info("Ticket assignment updated due to escalation", ticket_id=str(escalation_data.ticket_id), assigned_to=escalation_data.escalated_to)

                logger.info("Ticket escalated successfully", escalation_id=str(created_escalation.escalation_id), ticket_id=str(escalation_data.ticket_id))
                return created_escalation.escalation_id
        except Exception as e:
            logger.error("Failed to escalate ticket", error=str(e), escalation_data=escalation_data.model_dump_json())
            raise

    async def get_sla_status(self, ticket_id: UUID) -> Optional[SLAStatus]:
        """Retrieves the SLA status for a specific ticket.

        Args:
            ticket_id (UUID): The ID of the ticket.

        Returns:
            Optional[SLAStatus]: The SLA status if found, otherwise None.

        Raises:
            Exception: If there is an error during database operation.
        """
        try:
            async with self.db_manager.get_session() as session:
                sla_tracking_db = await self.db_helper.get_by_id(session, SLATrackingDB, ticket_id, id_column='ticket_id')
                if not sla_tracking_db:
                    logger.info("SLA tracking not found for ticket", ticket_id=str(ticket_id))
                    return None

                now = datetime.utcnow()
                resolution_due = sla_tracking_db.resolution_due
                minutes_until_breach = int((resolution_due - now).total_seconds() / 60) if resolution_due > now else 0

                sla_status = SLAStatus(
                    ticket_id=ticket_id,
                    first_response_due=sla_tracking_db.first_response_due,
                    first_response_breached=sla_tracking_db.first_response_breached,
                    resolution_due=resolution_due,
                    resolution_breached=sla_tracking_db.resolution_breached,
                    minutes_until_breach=minutes_until_breach if minutes_until_breach > 0 else None
                )
                logger.info("SLA status retrieved", ticket_id=str(ticket_id))
                return sla_status
        except Exception as e:
            logger.error("Failed to get SLA status", error=str(e), ticket_id=str(ticket_id))
            raise

# SERVICE
class SupportService:
    """Service layer for business logic related to support tickets."""
    def __init__(self, repo: SupportRepository):
        """Initializes the SupportService with a SupportRepository."""
        self.repo = repo
        logger.info("SupportService initialized")

    async def create_ticket(self, ticket_data: TicketCreate) -> Ticket:
        """Creates a new support ticket.

        Args:
            ticket_data (TicketCreate): Data for creating the new ticket.

        Returns:
            Ticket: The newly created ticket.
        """
        ticket = await self.repo.create_ticket(ticket_data)
        logger.info("Ticket created in service", ticket_id=str(ticket.ticket_id),
                   ticket_number=ticket.ticket_number, priority=ticket.priority.value)
        return ticket

    async def add_message(self, message_data: MessageCreate) -> UUID:
        """Adds a message to an existing ticket.

        Args:
            message_data (MessageCreate): Data for the new message.

        Returns:
            UUID: The ID of the newly added message.
        """
        message_id = await self.repo.add_message(message_data)
        logger.info("Message added in service", ticket_id=str(message_data.ticket_id),
                   sender_type=message_data.sender_type.value)
        return message_id

# FastAPI app instance
app = FastAPI(
    title="Support Agent API",
    version=os.getenv("AGENT_VERSION", "1.0.0"),
    description="API for managing customer support tickets and SLAs."
)

async def get_support_service() -> SupportService:
    """Dependency injector for SupportService."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set.")
        raise HTTPException(status_code=500, detail="Database configuration error")

    db_manager = get_database_manager(db_url)
    db_helper = DatabaseHelper(Base)
    repo = SupportRepository(db_manager, db_helper)
    return SupportService(repo)

# FastAPI ENDPOINTS
@app.post("/api/v1/support/tickets", response_model=Ticket, status_code=201)
async def create_ticket_endpoint(
    ticket_data: TicketCreate = Body(..., description="Data for creating a new support ticket"),
    service: SupportService = Depends(get_support_service)
):
    """Creates a new support ticket.

    Args:
        ticket_data (TicketCreate): The data required to create a new ticket.
        service (SupportService): Dependency-injected SupportService instance.

    Returns:
        Ticket: The newly created support ticket.

    Raises:
        HTTPException: If ticket creation fails.
    """
    try:
        logger.info("Received request to create ticket")
        ticket = await service.create_ticket(ticket_data)
        return ticket
    except Exception as e:
        logger.error("API: create_ticket_failed", error=str(e), ticket_data=ticket_data.model_dump_json())
        raise HTTPException(status_code=500, detail=f"Failed to create ticket: {e}")

@app.get("/api/v1/support/tickets/{ticket_id}", response_model=Ticket)
async def get_ticket_endpoint(
    ticket_id: UUID = Path(..., description="Unique identifier of the ticket"),
    service: SupportService = Depends(get_support_service)
):
    """Retrieves a support ticket by its ID.

    Args:
        ticket_id (UUID): The unique identifier of the ticket.
        service (SupportService): Dependency-injected SupportService instance.

    Returns:
        Ticket: The requested support ticket.

    Raises:
        HTTPException: If the ticket is not found or an error occurs.
    """
    try:
        logger.info("Received request to get ticket", ticket_id=str(ticket_id))
        ticket = await service.repo.get_ticket(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return ticket
    except HTTPException:
        raise
    except Exception as e:
        logger.error("API: get_ticket_failed", error=str(e), ticket_id=str(ticket_id))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve ticket: {e}")

@app.patch("/api/v1/support/tickets/{ticket_id}", response_model=Ticket)
async def update_ticket_endpoint(
    ticket_id: UUID = Path(..., description="Unique identifier of the ticket to update"),
    update_data: TicketUpdate = Body(..., description="Data to update the ticket with"),
    service: SupportService = Depends(get_support_service)
):
    """Updates an existing support ticket.

    Args:
        ticket_id (UUID): The unique identifier of the ticket to update.
        update_data (TicketUpdate): The data to apply to the ticket.
        service (SupportService): Dependency-injected SupportService instance.

    Returns:
        Ticket: The updated support ticket.

    Raises:
        HTTPException: If the ticket is not found or an error occurs.
    """
    try:
        logger.info("Received request to update ticket", ticket_id=str(ticket_id), update_data=update_data.model_dump_json())
        ticket = await service.repo.update_ticket(ticket_id, update_data)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return ticket
    except HTTPException:
        raise
    except Exception as e:
        logger.error("API: update_ticket_failed", error=str(e), ticket_id=str(ticket_id), update_data=update_data.model_dump_json())
        raise HTTPException(status_code=500, detail=f"Failed to update ticket: {e}")

@app.post("/api/v1/support/tickets/{ticket_id}/messages", status_code=201)
async def add_message_endpoint(
    ticket_id: UUID = Path(..., description="Unique identifier of the ticket to add message to"),
    message_body: str = Body(..., embed=True, description="Content of the message"),
    sender_id: str = Body(..., embed=True, description="ID of the sender"),
    sender_type: SenderType = Body(..., embed=True, description="Type of the sender"),
    service: SupportService = Depends(get_support_service)
):
    """Adds a new message to a specific support ticket.

    Args:
        ticket_id (UUID): The ID of the ticket.
        message_body (str): The content of the message.
        sender_id (str): The ID of the sender.
        sender_type (SenderType): The type of the sender.
        service (SupportService): Dependency-injected SupportService instance.

    Returns:
        Dict[str, Any]: Confirmation of message addition.

    Raises:
        HTTPException: If message addition fails.
    """
    try:
        logger.info("Received request to add message", ticket_id=str(ticket_id), sender_id=sender_id, sender_type=sender_type.value)
        message_data = MessageCreate(
            ticket_id=ticket_id,
            sender_id=sender_id,
            sender_type=sender_type,
            message_body=message_body
        )
        message_id = await service.add_message(message_data)
        return {"message_id": message_id, "message": "Message added successfully"}
    except Exception as e:
        logger.error("API: add_message_failed", error=str(e), ticket_id=str(ticket_id))
        raise HTTPException(status_code=500, detail=f"Failed to add message: {e}")

@app.get("/api/v1/support/tickets/{ticket_id}/messages", response_model=List[TicketMessage])
async def get_ticket_messages_endpoint(
    ticket_id: UUID = Path(..., description="Unique identifier of the ticket to retrieve messages from"),
    service: SupportService = Depends(get_support_service)
):
    """Retrieves all messages for a specific support ticket.

    Args:
        ticket_id (UUID): The ID of the ticket.
        service (SupportService): Dependency-injected SupportService instance.

    Returns:
        List[TicketMessage]: A list of messages associated with the ticket.

    Raises:
        HTTPException: If message retrieval fails.
    """
    try:
        logger.info("Received request to get ticket messages", ticket_id=str(ticket_id))
        messages = await service.repo.get_ticket_messages(ticket_id)
        return messages
    except Exception as e:
        logger.error("API: get_ticket_messages_failed", error=str(e), ticket_id=str(ticket_id))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve ticket messages: {e}")

@app.post("/api/v1/support/tickets/escalate", status_code=201)
async def escalate_ticket_endpoint(
    escalation_data: EscalationCreate = Body(..., description="Data for escalating a support ticket"),
    service: SupportService = Depends(get_support_service)
):
    """Escalates a support ticket.

    Args:
        escalation_data (EscalationCreate): The data required for ticket escalation.
        service (SupportService): Dependency-injected SupportService instance.

    Returns:
        Dict[str, Any]: Confirmation of ticket escalation.

    Raises:
        HTTPException: If ticket escalation fails.
    """
    try:
        logger.info("Received request to escalate ticket", ticket_id=str(escalation_data.ticket_id), escalated_to=escalation_data.escalated_to)
        escalation_id = await service.repo.escalate_ticket(escalation_data)
        return {"escalation_id": escalation_id, "message": "Ticket escalated successfully"}
    except Exception as e:
        logger.error("API: escalate_ticket_failed", error=str(e), escalation_data=escalation_data.model_dump_json())
        raise HTTPException(status_code=500, detail=f"Failed to escalate ticket: {e}")

@app.get("/api/v1/support/tickets/{ticket_id}/sla", response_model=SLAStatus)
async def get_sla_status_endpoint(
    ticket_id: UUID = Path(..., description="Unique identifier of the ticket to get SLA status for"),
    service: SupportService = Depends(get_support_service)
):
    """Retrieves the SLA status for a specific support ticket.

    Args:
        ticket_id (UUID): The ID of the ticket.
        service (SupportService): Dependency-injected SupportService instance.

    Returns:
        SLAStatus: The SLA status of the ticket.

    Raises:
        HTTPException: If SLA status is not found or an error occurs.
    """
    try:
        logger.info("Received request to get SLA status", ticket_id=str(ticket_id))
        sla_status = await service.repo.get_sla_status(ticket_id)
        if not sla_status:
            raise HTTPException(status_code=404, detail="SLA status not found for this ticket")
        return sla_status
    except HTTPException:
        raise
    except Exception as e:
        logger.error("API: get_sla_status_failed", error=str(e), ticket_id=str(ticket_id))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve SLA status: {e}")

@app.get("/health", status_code=200)
async def health_check():
    """Health check endpoint for the Support Agent API.

    Returns:
        Dict[str, str]: A dictionary indicating the health status.
    """
    logger.info("Health check requested")
    return {"status": "healthy", "agent": "support_agent", "version": os.getenv("AGENT_VERSION", "1.0.0")}


class SupportAgent(BaseAgentV2):
    """Support Agent for managing customer support tickets, SLAs, and escalations.

    This agent integrates with a database for ticket management, uses FastAPI for API exposure,
    and handles inter-agent communication via Kafka.
    """
    def __init__(self, agent_id: str = "support_agent_001", agent_type: str = "support_agent"):
        """Initializes the SupportAgent.

        Args:
            agent_id (str): The unique identifier for this agent instance.
            agent_type (str): The type of the agent (e.g., 'support_agent').
        """
        super().__init__(agent_id=agent_id)
        self.agent_type = agent_type
        self.db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/multi_agent_ecommerce")
        self.db_manager = None
        self.db_helper = None
        self.repository = None
        self.service = None
        logger.info("SupportAgent initialized", agent_id=self.agent_id, agent_type=self.agent_type)

    async def setup(self):
        """Performs initial setup for the agent, including database connection.

        Raises:
            Exception: If database connection fails.
        """
        logger.info("SupportAgent setup initiated")
        try:
            # Initialize database manager first
            if self.db_manager is None:
                try:
                    self.db_manager = get_database_manager()
                    logger.info("Using global database manager")
                except RuntimeError:
                    from shared.models import DatabaseConfig
                    db_config = DatabaseConfig()
                    self.db_manager = DatabaseManager(db_config)
                    await self.db_manager.initialize()
                    logger.info("Created new database manager")
                
                self.db_helper = DatabaseHelper(self.db_manager)
            
            # Ensure database tables are created if not exist (for development/testing)
            # In a production environment, migrations would handle this.
            async with self.db_manager.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables checked/created")

            # Insert default SLA policies if they don't exist
            async with self.db_manager.get_session() as session:
                existing_policies = await self.db_helper.get_all(session, SLAPolicyDB)
                if not existing_policies:
                    default_slas = [
                        SLAPolicyDB(priority=TicketPriority.LOW.value, first_response_minutes=240, resolution_minutes=2880),
                        SLAPolicyDB(priority=TicketPriority.MEDIUM.value, first_response_minutes=60, resolution_minutes=1440),
                        SLAPolicyDB(priority=TicketPriority.HIGH.value, first_response_minutes=30, resolution_minutes=720),
                        SLAPolicyDB(priority=TicketPriority.URGENT.value, first_response_minutes=10, resolution_minutes=180),
                    ]
                    for sla in default_slas:
                        session.add(sla)
                    await session.commit()
                    logger.info("Default SLA policies inserted")
                else:
                    logger.info("SLA policies already exist")

            logger.info("SupportAgent setup complete")
        except Exception as e:
            logger.error("SupportAgent setup failed", error=str(e))
            raise

    async def process_message(self, message: AgentMessage):
        """Processes incoming messages from other agents or Kafka topics.

        Args:
            message (AgentMessage): The incoming message to process.

        Raises:
            ValueError: If an unknown message type is received.
            Exception: For other processing errors.
        """
        logger.info("Processing message", message_type=message.message_type.value, sender_id=message.sender_id)
        try:
            if message.message_type == MessageType.CREATE_TICKET:
                ticket_data = TicketCreate(**message.payload)
                new_ticket = await self.service.create_ticket(ticket_data)
                response_payload = {"ticket_id": str(new_ticket.ticket_id), "ticket_number": new_ticket.ticket_number}
                await self.send_message(MessageType.TICKET_CREATED, new_ticket.customer_id, response_payload)
                logger.info("CREATE_TICKET processed", ticket_id=str(new_ticket.ticket_id))

            elif message.message_type == MessageType.ADD_TICKET_MESSAGE:
                message_data = MessageCreate(**message.payload)
                message_id = await self.service.add_message(message_data)
                response_payload = {"message_id": str(message_id), "ticket_id": str(message_data.ticket_id)}
                await self.send_message(MessageType.TICKET_MESSAGE_ADDED, message_data.sender_id, response_payload)
                logger.info("ADD_TICKET_MESSAGE processed", message_id=str(message_id))

            elif message.message_type == MessageType.UPDATE_TICKET:
                ticket_id = UUID(message.payload["ticket_id"])
                update_data = TicketUpdate(**message.payload["update_data"])
                updated_ticket = await self.repository.update_ticket(ticket_id, update_data)
                if updated_ticket:
                    response_payload = {"ticket_id": str(updated_ticket.ticket_id), "status": updated_ticket.status}
                    await self.send_message(MessageType.TICKET_UPDATED, updated_ticket.customer_id, response_payload)
                    logger.info("UPDATE_TICKET processed", ticket_id=str(updated_ticket.ticket_id))
                else:
                    logger.warning("UPDATE_TICKET failed, ticket not found", ticket_id=str(ticket_id))
                    await self.send_message(MessageType.ERROR, message.sender_id, {"error": "Ticket not found", "ticket_id": str(ticket_id)})

            elif message.message_type == MessageType.ESCALATE_TICKET:
                escalation_data = EscalationCreate(**message.payload)
                escalation_id = await self.repository.escalate_ticket(escalation_data)
                response_payload = {"escalation_id": str(escalation_id), "ticket_id": str(escalation_data.ticket_id)}
                await self.send_message(MessageType.TICKET_ESCALATED, escalation_data.escalated_to, response_payload)
                logger.info("ESCALATE_TICKET processed", ticket_id=str(escalation_data.ticket_id))

            else:
                logger.warning("Unknown message type received", message_type=message.message_type.value)
                raise ValueError(f"Unknown message type: {message.message_type}")

        except Exception as e:
            logger.error("Error processing message", error=str(e), message=message.model_dump_json())
            await self.send_message(MessageType.ERROR, message.sender_id, {"error": str(e), "original_message": message.model_dump()})
    
    async def initialize(self):
        """Initialize the Support Agent."""
        await super().initialize()
        try:
            self.db_manager = get_database_manager(self.db_url)
            self.db_helper = DatabaseHelper(Base)
            self.repository = SupportRepository(self.db_manager, self.db_helper)
            self.service = SupportService(self.repository)
            await self.setup()
            logger.info("SupportAgent initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize database components: {e}. Agent will run in limited mode.")
    
    async def cleanup(self):
        """Cleanup agent resources."""
        try:
            if self.db_manager:
                await self.db_manager.close()
            await super().cleanup()
            logger.info("SupportAgent cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process support business logic.
        
        Args:
            data: Dictionary containing operation type and parameters
            
        Returns:
            Dictionary with processing results
        """
        try:
            operation = data.get("operation", "process")
            logger.info(f"Processing support operation: {operation}")
            return {"status": "success", "operation": operation, "data": data}
        except Exception as e:
            logger.error(f"Error in process_business_logic: {e}")
            return {"status": "error", "message": str(e)}


# Main execution block for running the FastAPI app and agent

# Create agent instance at module level to ensure routes are registered
agent = SupportAgent()

if __name__ == "__main__":
    # Environment variables for agent and FastAPI
    AGENT_ID = os.getenv("AGENT_ID", "support_agent_001")
    AGENT_TYPE = os.getenv("AGENT_TYPE", "support_agent")
    KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
    API_PORT = int(os.getenv("API_PORT", 8018))

    # Initialize and run the SupportAgent in a separate task
    support_agent_instance = SupportAgent(AGENT_ID, AGENT_TYPE)

    async def start_agent_and_api():
        await support_agent_instance.setup()
        # Start agent initialization in background (non-blocking)
        asyncio.create_task(support_agent_instance.start())
        # Start API server
        config = uvicorn.Config(app, host="0.0.0.0", port=API_PORT)
        server = uvicorn.Server(config)
        await server.serve()

    # Run the combined agent and API
    asyncio.run(start_agent_and_api())

