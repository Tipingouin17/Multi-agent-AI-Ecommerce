"""
Compliance Agent - Multi-Agent E-Commerce System

This agent manages GDPR compliance, data retention policies, consent management,
audit trail generation, and regulatory reporting.

DATABASE SCHEMA (migration 018_compliance_agent.sql):

CREATE TABLE data_subjects (
    subject_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    consent_status JSONB NOT NULL, -- {marketing: true, analytics: false, ...}
    data_processing_purposes JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE consent_records (
    consent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID REFERENCES data_subjects(subject_id),
    consent_type VARCHAR(100) NOT NULL, -- 'marketing', 'analytics', 'profiling', 'third_party'
    consent_given BOOLEAN NOT NULL,
    consent_method VARCHAR(50), -- 'explicit', 'implicit', 'opt_in', 'opt_out'
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE data_access_requests (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID REFERENCES data_subjects(subject_id),
    request_type VARCHAR(50) NOT NULL, -- 'access', 'rectification', 'erasure', 'portability', 'restriction'
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'rejected'
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    response_data JSONB
);

CREATE TABLE audit_logs (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(100) NOT NULL, -- 'order', 'customer', 'product', 'payment'
    entity_id VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL, -- 'create', 'read', 'update', 'delete'
    actor_id VARCHAR(100) NOT NULL, -- User or system that performed action
    actor_type VARCHAR(50), -- 'user', 'system', 'agent'
    changes JSONB, -- Before/after values
    ip_address VARCHAR(45),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE retention_policies (
    policy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_type VARCHAR(100) NOT NULL, -- 'order', 'customer', 'payment', 'log'
    retention_period_days INTEGER NOT NULL,
    deletion_method VARCHAR(50), -- 'hard_delete', 'anonymize', 'archive'
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE compliance_reports (
    report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_type VARCHAR(100) NOT NULL, -- 'gdpr_audit', 'data_breach', 'consent_summary'
    period_start DATE,
    period_end DATE,
    report_data JSONB NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID
from enum import Enum

from shared.db_helpers import DatabaseHelper

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field, EmailStr
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
class RequestType(str, Enum):
    ACCESS = "access"
    RECTIFICATION = "rectification"
    ERASURE = "erasure"
    PORTABILITY = "portability"
    RESTRICTION = "restriction"

class RequestStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"

# MODELS
class ConsentUpdate(BaseModel):
    customer_id: str
    consent_type: str
    consent_given: bool
    consent_method: str = "explicit"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class DataAccessRequest(BaseModel):
    customer_id: str
    request_type: RequestType
    details: Optional[str] = None

class DataAccessRequestResponse(BaseModel):
    request_id: UUID
    request_type: RequestType
    status: RequestStatus
    requested_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AuditLogCreate(BaseModel):
    entity_type: str
    entity_id: str
    action: str
    actor_id: str
    actor_type: str = "system"
    changes: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None

class AuditLogResponse(BaseModel):
    audit_id: UUID
    entity_type: str
    entity_id: str
    action: str
    actor_id: str
    timestamp: datetime

    class Config:
        from_attributes = True

class ComplianceReportRequest(BaseModel):
    report_type: str
    period_start: Optional[date] = None
    period_end: Optional[date] = None

class ConsentSummary(BaseModel):
    total_subjects: int
    consent_breakdown: Dict[str, int]
    recent_changes: int

# REPOSITORY
class ComplianceRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def update_consent(self, consent_data: ConsentUpdate) -> UUID:
        """Update consent for data subject."""
        # Get or create subject
        query_subject = """
            INSERT INTO data_subjects (customer_id, email, consent_status)
            VALUES ($1, $2, $3)
            ON CONFLICT (customer_id) DO UPDATE
            SET consent_status = data_subjects.consent_status || $3,
                updated_at = CURRENT_TIMESTAMP
            RETURNING subject_id
        """
        consent_status = {consent_data.consent_type: consent_data.consent_given}
        result = await self.db.fetch_one(
            query_subject, consent_data.customer_id,
            f"{consent_data.customer_id}@example.com",  # Placeholder
            str(consent_status)
        )
        subject_id = result['subject_id']
        
        # Record consent
        query_consent = """
            INSERT INTO consent_records (subject_id, consent_type, consent_given,
                                        consent_method, ip_address, user_agent)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING consent_id
        """
        consent_result = await self.db.fetch_one(
            query_consent, subject_id, consent_data.consent_type,
            consent_data.consent_given, consent_data.consent_method,
            consent_data.ip_address, consent_data.user_agent
        )
        return consent_result['consent_id']
    
    async def create_data_access_request(
        self, request_data: DataAccessRequest
    ) -> DataAccessRequestResponse:
        """Create GDPR data access request."""
        # Get subject
        query_subject = "SELECT subject_id FROM data_subjects WHERE customer_id = $1"
        subject = await self.db.fetch_one(query_subject, request_data.customer_id)
        
        if not subject:
            raise ValueError("Data subject not found")
        
        query = """
            INSERT INTO data_access_requests (subject_id, request_type, status)
            VALUES ($1, $2, 'pending')
            RETURNING request_id, request_type, status, requested_at, completed_at
        """
        result = await self.db.fetch_one(
            query, subject['subject_id'], request_data.request_type.value
        )
        return DataAccessRequestResponse(**result)
    
    async def process_data_access_request(
        self, request_id: UUID, response_data: Dict[str, Any]
    ) -> None:
        """Process and complete data access request."""
        query = """
            UPDATE data_access_requests
            SET status = 'completed',
                completed_at = CURRENT_TIMESTAMP,
                response_data = $2
            WHERE request_id = $1
        """
        await self.db.execute(query, request_id, str(response_data))
    
    async def create_audit_log(self, log_data: AuditLogCreate) -> UUID:
        """Create audit log entry."""
        query = """
            INSERT INTO audit_logs (entity_type, entity_id, action, actor_id,
                                   actor_type, changes, ip_address)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING audit_id
        """
        result = await self.db.fetch_one(
            query, log_data.entity_type, log_data.entity_id, log_data.action,
            log_data.actor_id, log_data.actor_type,
            str(log_data.changes) if log_data.changes else None,
            log_data.ip_address
        )
        return result['audit_id']
    
    async def get_audit_logs(
        self, entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLogResponse]:
        """Retrieve audit logs."""
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        
        if entity_type:
            params.append(entity_type)
            query += f" AND entity_type = ${len(params)}"
        
        if entity_id:
            params.append(entity_id)
            query += f" AND entity_id = ${len(params)}"
        
        query += f" ORDER BY timestamp DESC LIMIT {limit}"
        
        results = await self.db.fetch_all(query, *params)
        return [AuditLogResponse(**r) for r in results]
    
    async def generate_consent_summary(self) -> ConsentSummary:
        """Generate consent summary report."""
        # Total subjects
        total_query = "SELECT COUNT(*) as count FROM data_subjects"
        total_result = await self.db.fetch_one(total_query)
        total_subjects = total_result['count']
        
        # Recent changes (last 30 days)
        recent_query = """
            SELECT COUNT(*) as count FROM consent_records
            WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '30 days'
        """
        recent_result = await self.db.fetch_one(recent_query)
        recent_changes = recent_result['count']
        
        # Simulated breakdown
        consent_breakdown = {
            "marketing": 450,
            "analytics": 380,
            "profiling": 200,
            "third_party": 150
        }
        
        return ConsentSummary(
            total_subjects=total_subjects,
            consent_breakdown=consent_breakdown,
            recent_changes=recent_changes
        )

# SERVICE
class ComplianceService:
    def __init__(self, repo: ComplianceRepository):
        self.repo = repo
    
    async def update_consent(self, consent_data: ConsentUpdate) -> UUID:
        """Update user consent."""
        consent_id = await self.repo.update_consent(consent_data)
        
        logger.info("consent_updated", customer_id=consent_data.customer_id,
                   consent_type=consent_data.consent_type,
                   consent_given=consent_data.consent_given)
        
        # Create audit log
        await self.repo.create_audit_log(AuditLogCreate(
            entity_type="consent",
            entity_id=str(consent_id),
            action="update",
            actor_id=consent_data.customer_id,
            actor_type="user",
            changes={"consent_type": consent_data.consent_type,
                    "consent_given": consent_data.consent_given}
        ))
        
        return consent_id
    
    async def handle_data_access_request(
        self, request_data: DataAccessRequest
    ) -> DataAccessRequestResponse:
        """Handle GDPR data access request."""
        request = await self.repo.create_data_access_request(request_data)
        
        logger.info("data_access_request_created", request_id=str(request.request_id),
                   customer_id=request_data.customer_id,
                   request_type=request_data.request_type.value)
        
        # In production, trigger data collection from all systems
        # For now, auto-complete with simulated data
        if request_data.request_type == RequestType.ACCESS:
            response_data = {
                "customer_data": {"id": request_data.customer_id},
                "orders": [],
                "payments": []
            }
            await self.repo.process_data_access_request(
                request.request_id, response_data
            )
        
        return request

# FASTAPI APP
app = FastAPI(title="Compliance Agent API", version="1.0.0")

async def get_compliance_service() -> ComplianceService:
    db_manager = await get_database_manager()
    repo = ComplianceRepository(db_manager)
    return ComplianceService(repo)

# ENDPOINTS
@app.post("/api/v1/compliance/consent")
async def update_consent(
    consent_data: ConsentUpdate = Body(...),
    service: ComplianceService = Depends(get_compliance_service)
):
    try:
        consent_id = await service.update_consent(consent_data)
        return {"consent_id": consent_id, "message": "Consent updated successfully"}
    except Exception as e:
        logger.error("update_consent_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/compliance/data-access-request", response_model=DataAccessRequestResponse)
async def create_data_access_request(
    request_data: DataAccessRequest = Body(...),
    service: ComplianceService = Depends(get_compliance_service)
):
    try:
        request = await service.handle_data_access_request(request_data)
        return request
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("create_data_access_request_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/compliance/audit-log", response_model=AuditLogResponse)
async def create_audit_log(
    log_data: AuditLogCreate = Body(...),
    service: ComplianceService = Depends(get_compliance_service)
):
    try:
        audit_id = await service.repo.create_audit_log(log_data)
        # Fetch created log
        logs = await service.repo.get_audit_logs(limit=1)
        return logs[0] if logs else None
    except Exception as e:
        logger.error("create_audit_log_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/compliance/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    service: ComplianceService = Depends(get_compliance_service)
):
    try:
        logs = await service.repo.get_audit_logs(entity_type, entity_id, limit)
        return logs
    except Exception as e:
        logger.error("get_audit_logs_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/compliance/reports/consent-summary", response_model=ConsentSummary)
async def get_consent_summary(
    service: ComplianceService = Depends(get_compliance_service)
):
    try:
        summary = await service.repo.generate_consent_summary()
        return summary
    except Exception as e:
        logger.error("get_consent_summary_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "compliance_agent", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8017)

