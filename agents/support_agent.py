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

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID
from enum import Enum

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field
import structlog
import sys
import os

current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.database import DatabaseManager, get_database_manager

logger = structlog.get_logger(__name__)

# ENUMS
class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class SenderType(str, Enum):
    CUSTOMER = "customer"
    AGENT = "agent"
    SYSTEM = "system"

# MODELS
class TicketCreate(BaseModel):
    customer_id: str
    subject: str
    description: str
    priority: TicketPriority = TicketPriority.MEDIUM
    category: Optional[str] = None
    channel: str = "web"

class Ticket(BaseModel):
    ticket_id: UUID
    ticket_number: str
    customer_id: str
    subject: str
    status: TicketStatus
    priority: TicketPriority
    category: Optional[str]
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    ticket_id: UUID
    sender_id: str
    sender_type: SenderType
    message_body: str
    attachments: Optional[List[Dict[str, Any]]] = None

class TicketMessage(BaseModel):
    message_id: UUID
    ticket_id: UUID
    sender_id: str
    sender_type: SenderType
    message_body: str
    created_at: datetime

    class Config:
        from_attributes = True

class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_to: Optional[str] = None

class EscalationCreate(BaseModel):
    ticket_id: UUID
    escalated_to: str
    escalation_reason: str

class SLAStatus(BaseModel):
    ticket_id: UUID
    first_response_due: datetime
    first_response_breached: bool
    resolution_due: datetime
    resolution_breached: bool
    minutes_until_breach: Optional[int] = None

# REPOSITORY
class SupportRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_ticket(self, ticket_data: TicketCreate) -> Ticket:
        """Create support ticket."""
        ticket_number = f"TKT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
        
        query = """
            INSERT INTO support_tickets (ticket_number, customer_id, subject, description,
                                        priority, category, channel)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
        """
        result = await self.db.fetch_one(
            query, ticket_number, ticket_data.customer_id, ticket_data.subject,
            ticket_data.description, ticket_data.priority.value,
            ticket_data.category, ticket_data.channel
        )
        
        ticket = Ticket(**result)
        
        # Create SLA tracking
        await self._create_sla_tracking(ticket.ticket_id, ticket.priority.value)
        
        return ticket
    
    async def _create_sla_tracking(self, ticket_id: UUID, priority: str) -> None:
        """Create SLA tracking for ticket."""
        # Get SLA policy
        policy_query = "SELECT * FROM sla_policies WHERE priority = $1 AND is_active = true LIMIT 1"
        policy = await self.db.fetch_one(policy_query, priority)
        
        if not policy:
            # Default SLA
            first_response_minutes = 60
            resolution_minutes = 1440  # 24 hours
        else:
            first_response_minutes = policy['first_response_minutes']
            resolution_minutes = policy['resolution_minutes']
        
        now = datetime.utcnow()
        first_response_due = now + timedelta(minutes=first_response_minutes)
        resolution_due = now + timedelta(minutes=resolution_minutes)
        
        query = """
            INSERT INTO sla_tracking (ticket_id, first_response_due, resolution_due)
            VALUES ($1, $2, $3)
        """
        await self.db.execute(query, ticket_id, first_response_due, resolution_due)
    
    async def get_ticket(self, ticket_id: UUID) -> Optional[Ticket]:
        """Get ticket by ID."""
        query = "SELECT * FROM support_tickets WHERE ticket_id = $1"
        result = await self.db.fetch_one(query, ticket_id)
        return Ticket(**result) if result else None
    
    async def update_ticket(self, ticket_id: UUID, update_data: TicketUpdate) -> Optional[Ticket]:
        """Update ticket."""
        updates = []
        params = []
        param_count = 1
        
        if update_data.status:
            params.append(update_data.status.value)
            updates.append(f"status = ${param_count}")
            param_count += 1
            
            if update_data.status == TicketStatus.RESOLVED:
                updates.append("resolved_at = CURRENT_TIMESTAMP")
            elif update_data.status == TicketStatus.CLOSED:
                updates.append("closed_at = CURRENT_TIMESTAMP")
        
        if update_data.priority:
            params.append(update_data.priority.value)
            updates.append(f"priority = ${param_count}")
            param_count += 1
        
        if update_data.assigned_to:
            params.append(update_data.assigned_to)
            updates.append(f"assigned_to = ${param_count}")
            param_count += 1
        
        if not updates:
            return await self.get_ticket(ticket_id)
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(ticket_id)
        
        query = f"""
            UPDATE support_tickets
            SET {', '.join(updates)}
            WHERE ticket_id = ${param_count}
            RETURNING *
        """
        result = await self.db.fetch_one(query, *params)
        return Ticket(**result) if result else None
    
    async def add_message(self, message_data: MessageCreate) -> UUID:
        """Add message to ticket."""
        query = """
            INSERT INTO ticket_messages (ticket_id, sender_id, sender_type, message_body, attachments)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING message_id
        """
        result = await self.db.fetch_one(
            query, message_data.ticket_id, message_data.sender_id,
            message_data.sender_type.value, message_data.message_body,
            str(message_data.attachments) if message_data.attachments else None
        )
        
        # Update first response SLA if this is agent's first response
        if message_data.sender_type == SenderType.AGENT:
            await self._update_first_response_sla(message_data.ticket_id)
        
        return result['message_id']
    
    async def _update_first_response_sla(self, ticket_id: UUID) -> None:
        """Update first response SLA."""
        query = """
            UPDATE sla_tracking
            SET first_response_at = CURRENT_TIMESTAMP,
                first_response_breached = (CURRENT_TIMESTAMP > first_response_due)
            WHERE ticket_id = $1 AND first_response_at IS NULL
        """
        await self.db.execute(query, ticket_id)
    
    async def get_ticket_messages(self, ticket_id: UUID) -> List[TicketMessage]:
        """Get all messages for ticket."""
        query = "SELECT * FROM ticket_messages WHERE ticket_id = $1 ORDER BY created_at ASC"
        results = await self.db.fetch_all(query, ticket_id)
        return [TicketMessage(**r) for r in results]
    
    async def escalate_ticket(self, escalation_data: EscalationCreate) -> UUID:
        """Escalate ticket."""
        query = """
            INSERT INTO ticket_escalations (ticket_id, escalated_to, escalation_reason)
            VALUES ($1, $2, $3)
            RETURNING escalation_id
        """
        result = await self.db.fetch_one(
            query, escalation_data.ticket_id, escalation_data.escalated_to,
            escalation_data.escalation_reason
        )
        
        # Update ticket assignment
        await self.update_ticket(
            escalation_data.ticket_id,
            TicketUpdate(assigned_to=escalation_data.escalated_to)
        )
        
        return result['escalation_id']
    
    async def get_sla_status(self, ticket_id: UUID) -> Optional[SLAStatus]:
        """Get SLA status for ticket."""
        query = "SELECT * FROM sla_tracking WHERE ticket_id = $1"
        result = await self.db.fetch_one(query, ticket_id)
        
        if not result:
            return None
        
        now = datetime.utcnow()
        resolution_due = result['resolution_due']
        minutes_until_breach = int((resolution_due - now).total_seconds() / 60) if resolution_due > now else 0
        
        return SLAStatus(
            ticket_id=ticket_id,
            first_response_due=result['first_response_due'],
            first_response_breached=result['first_response_breached'],
            resolution_due=resolution_due,
            resolution_breached=result['resolution_breached'],
            minutes_until_breach=minutes_until_breach if minutes_until_breach > 0 else None
        )

# SERVICE
class SupportService:
    def __init__(self, repo: SupportRepository):
        self.repo = repo
    
    async def create_ticket(self, ticket_data: TicketCreate) -> Ticket:
        """Create support ticket."""
        ticket = await self.repo.create_ticket(ticket_data)
        
        logger.info("ticket_created", ticket_id=str(ticket.ticket_id),
                   ticket_number=ticket.ticket_number, priority=ticket.priority.value)
        
        return ticket
    
    async def add_message(self, message_data: MessageCreate) -> UUID:
        """Add message to ticket."""
        message_id = await self.repo.add_message(message_data)
        
        logger.info("message_added", ticket_id=str(message_data.ticket_id),
                   sender_type=message_data.sender_type.value)
        
        return message_id

# FASTAPI APP
app = FastAPI(title="Support Agent API", version="1.0.0")

async def get_support_service() -> SupportService:
    db_manager = await get_database_manager()
    repo = SupportRepository(db_manager)
    return SupportService(repo)

# ENDPOINTS
@app.post("/api/v1/support/tickets", response_model=Ticket)
async def create_ticket(
    ticket_data: TicketCreate = Body(...),
    service: SupportService = Depends(get_support_service)
):
    try:
        ticket = await service.create_ticket(ticket_data)
        return ticket
    except Exception as e:
        logger.error("create_ticket_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/support/tickets/{ticket_id}", response_model=Ticket)
async def get_ticket(
    ticket_id: UUID = Path(...),
    service: SupportService = Depends(get_support_service)
):
    try:
        ticket = await service.repo.get_ticket(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return ticket
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_ticket_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/v1/support/tickets/{ticket_id}", response_model=Ticket)
async def update_ticket(
    ticket_id: UUID = Path(...),
    update_data: TicketUpdate = Body(...),
    service: SupportService = Depends(get_support_service)
):
    try:
        ticket = await service.repo.update_ticket(ticket_id, update_data)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return ticket
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_ticket_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/support/tickets/{ticket_id}/messages")
async def add_message(
    ticket_id: UUID = Path(...),
    message_body: str = Body(..., embed=True),
    sender_id: str = Body(..., embed=True),
    sender_type: SenderType = Body(..., embed=True),
    service: SupportService = Depends(get_support_service)
):
    try:
        message_data = MessageCreate(
            ticket_id=ticket_id,
            sender_id=sender_id,
            sender_type=sender_type,
            message_body=message_body
        )
        message_id = await service.add_message(message_data)
        return {"message_id": message_id, "message": "Message added successfully"}
    except Exception as e:
        logger.error("add_message_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/support/tickets/{ticket_id}/messages", response_model=List[TicketMessage])
async def get_ticket_messages(
    ticket_id: UUID = Path(...),
    service: SupportService = Depends(get_support_service)
):
    try:
        messages = await service.repo.get_ticket_messages(ticket_id)
        return messages
    except Exception as e:
        logger.error("get_ticket_messages_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/support/tickets/escalate")
async def escalate_ticket(
    escalation_data: EscalationCreate = Body(...),
    service: SupportService = Depends(get_support_service)
):
    try:
        escalation_id = await service.repo.escalate_ticket(escalation_data)
        return {"escalation_id": escalation_id, "message": "Ticket escalated successfully"}
    except Exception as e:
        logger.error("escalate_ticket_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/support/tickets/{ticket_id}/sla", response_model=SLAStatus)
async def get_sla_status(
    ticket_id: UUID = Path(...),
    service: SupportService = Depends(get_support_service)
):
    try:
        sla_status = await service.repo.get_sla_status(ticket_id)
        if not sla_status:
            raise HTTPException(status_code=404, detail="SLA status not found")
        return sla_status
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_sla_status_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "support_agent", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8018)

