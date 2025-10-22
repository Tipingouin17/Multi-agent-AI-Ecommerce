
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

import os
import sys
import uvicorn
import structlog
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID
from enum import Enum

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field, EmailStr

# Adjust the path to import from the project root
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.base_agent import BaseAgent, AgentMessage, MessageType
from shared.database import DatabaseManager, get_database_manager
from shared.db_helpers import DatabaseHelper

logger = structlog.get_logger(__name__)

# ENUMS
class RequestType(str, Enum):
    """Enumeration for types of data access requests."""
    ACCESS = "access"
    RECTIFICATION = "rectification"
    ERASURE = "erasure"
    PORTABILITY = "portability"
    RESTRICTION = "restriction"
    async def initialize(self):
        """Initialize agent."""
        await super().initialize()
        
    async def cleanup(self):
        """Cleanup agent."""
        await super().cleanup()
        
    async def process_business_logic(self, data):
        """Process business logic."""
        return {"status": "success"}


class RequestStatus(str, Enum):
    """Enumeration for the status of data access requests."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"

# MODELS
class ConsentUpdate(BaseModel):
    """Pydantic model for updating user consent."""
    customer_id: str = Field(..., description="Unique identifier for the customer.")
    consent_type: str = Field(..., description="Type of consent (e.g., marketing, analytics).")
    consent_given: bool = Field(..., description="Boolean indicating if consent is given.")
    consent_method: str = Field("explicit", description="Method by which consent was obtained.")
    ip_address: Optional[str] = Field(None, description="IP address of the user at the time of consent.")
    user_agent: Optional[str] = Field(None, description="User agent string of the user's browser.")

class DataAccessRequest(BaseModel):
    """Pydantic model for creating a data access request."""
    customer_id: str = Field(..., description="Unique identifier for the customer.")
    request_type: RequestType = Field(..., description="Type of data access request.")
    details: Optional[str] = Field(None, description="Additional details for the request.")

class DataAccessRequestResponse(BaseModel):
    """Pydantic model for the response of a data access request."""
    request_id: UUID = Field(..., description="Unique identifier for the data access request.")
    request_type: RequestType = Field(..., description="Type of data access request.")
    status: RequestStatus = Field(..., description="Current status of the request.")
    requested_at: datetime = Field(..., description="Timestamp when the request was made.")
    completed_at: Optional[datetime] = Field(None, description="Timestamp when the request was completed.")

    class Config:
        from_attributes = True

class AuditLogCreate(BaseModel):
    """Pydantic model for creating an audit log entry."""
    entity_type: str = Field(..., description="Type of entity being audited (e.g., order, customer).")
    entity_id: str = Field(..., description="ID of the entity being audited.")
    action: str = Field(..., description="Action performed (e.g., create, read, update, delete).")
    actor_id: str = Field(..., description="ID of the actor who performed the action.")
    actor_type: str = Field("system", description="Type of actor (e.g., user, system, agent).")
    changes: Optional[Dict[str, Any]] = Field(None, description="JSON object detailing changes made.")
    ip_address: Optional[str] = Field(None, description="IP address from which the action was performed.")

class AuditLogResponse(BaseModel):
    """Pydantic model for an audit log response."""
    audit_id: UUID = Field(..., description="Unique identifier for the audit log entry.")
    entity_type: str = Field(..., description="Type of entity being audited.")
    entity_id: str = Field(..., description="ID of the entity being audited.")
    action: str = Field(..., description="Action performed.")
    actor_id: str = Field(..., description="ID of the actor.")
    timestamp: datetime = Field(..., description="Timestamp of the audit log entry.")

    class Config:
        from_attributes = True

class ComplianceReportRequest(BaseModel):
    """Pydantic model for requesting a compliance report."""
    report_type: str = Field(..., description="Type of report to generate (e.g., gdpr_audit, consent_summary).")
    period_start: Optional[date] = Field(None, description="Start date for the report period.")
    period_end: Optional[date] = Field(None, description="End date for the report period.")

class ConsentSummary(BaseModel):
    """Pydantic model for a consent summary report."""
    total_subjects: int = Field(..., description="Total number of data subjects.")
    consent_breakdown: Dict[str, int] = Field(..., description="Breakdown of consent types and counts.")
    recent_changes: int = Field(..., description="Number of recent consent changes.")

# REPOSITORY
class ComplianceRepository:
    """Repository for handling database operations related to compliance."""
    def __init__(self, db_manager: DatabaseManager, db_helper: DatabaseHelper):
        """Initializes the ComplianceRepository with a database manager and helper."""
        self.db_manager = db_manager
        self.db_helper = db_helper

    async def _get_subject_id(self, customer_id: str, email: Optional[str] = None) -> Optional[UUID]:
        """Retrieves the subject_id for a given customer_id, creating one if it doesn't exist.

        Args:
            customer_id (str): The unique identifier for the customer.
            email (Optional[str]): The email address of the customer. Required if creating a new subject.

        Returns:
            Optional[UUID]: The subject_id if found or created, otherwise None.
        """
        async with self.db_manager.get_session() as session:
            try:
                subject = await self.db_helper.get_by_id(session, "data_subjects", "customer_id", customer_id)
                if subject:
                    return subject["subject_id"]
                elif email:
                    # Create new subject if not found and email is provided
                    new_subject_data = {"customer_id": customer_id, "email": email, "consent_status": {}}
                    new_subject = await self.db_helper.create(session, "data_subjects", new_subject_data)
                    return new_subject["subject_id"]
                return None
            except Exception as e:
                logger.error("failed_to_get_or_create_subject", customer_id=customer_id, error=str(e))
                raise

    async def update_consent(self, consent_data: ConsentUpdate) -> UUID:
        """Updates consent for a data subject and records the consent history.

        Args:
            consent_data (ConsentUpdate): Data for updating consent.

        Returns:
            UUID: The ID of the recorded consent entry.
        """
        if not self.db_manager.is_initialized: return uuid4() # Return a dummy UUID if DB not initialized
        async with self.db_manager.get_session() as session:
            try:
                subject_id = await self._get_subject_id(consent_data.customer_id, f"{consent_data.customer_id}@example.com") # Placeholder email
                if not subject_id:
                    raise ValueError(f"Data subject not found for customer_id: {consent_data.customer_id}")

                # Update consent_status in data_subjects
                current_subject = await self.db_helper.get_by_id(session, "data_subjects", "subject_id", subject_id)
                if current_subject:
                    current_consent_status = current_subject.get("consent_status", {})
                    current_consent_status[consent_data.consent_type] = consent_data.consent_given
                    await self.db_helper.update(session, "data_subjects", subject_id, {"consent_status": current_consent_status, "updated_at": datetime.now()})

                # Record consent in consent_records
                consent_record_data = {
                    "subject_id": subject_id,
                    "consent_type": consent_data.consent_type,
                    "consent_given": consent_data.consent_given,
                    "consent_method": consent_data.consent_method,
                    "ip_address": consent_data.ip_address,
                    "user_agent": consent_data.user_agent
                }
                new_consent = await self.db_helper.create(session, "consent_records", consent_record_data)
                return new_consent["consent_id"]
            except Exception as e:
                logger.error("update_consent_failed", customer_id=consent_data.customer_id, error=str(e))
                raise

    async def create_data_access_request(self, request_data: DataAccessRequest) -> DataAccessRequestResponse:
        """Creates a GDPR data access request.

        Args:
            request_data (DataAccessRequest): Data for the access request.

        Returns:
            DataAccessRequestResponse: The created data access request.
        """
        if not self.db_manager.is_initialized: return DataAccessRequestResponse(request_id=uuid4(), request_type=request_data.request_type, status=RequestStatus.PENDING, requested_at=datetime.now()) # Dummy response
        async with self.db_manager.get_session() as session:
            try:
                subject_id = await self._get_subject_id(request_data.customer_id)
                if not subject_id:
                    raise ValueError(f"Data subject not found for customer_id: {request_data.customer_id}")

                request_payload = {
                    "subject_id": subject_id,
                    "request_type": request_data.request_type.value,
                    "status": RequestStatus.PENDING.value,
                    "details": request_data.details
                }
                new_request = await self.db_helper.create(session, "data_access_requests", request_payload)
                return DataAccessRequestResponse(**new_request)
            except Exception as e:
                logger.error("create_data_access_request_failed", customer_id=request_data.customer_id, error=str(e))
                raise

    async def process_data_access_request(self, request_id: UUID, response_data: Dict[str, Any]) -> None:
        """Processes and completes a data access request.

        Args:
            request_id (UUID): The ID of the data access request.
            response_data (Dict[str, Any]): The data to be included in the response.
        """
        if not self.db_manager.is_initialized: return
        async with self.db_manager.get_session() as session:
            try:
                update_payload = {
                    "status": RequestStatus.COMPLETED.value,
                    "completed_at": datetime.now(),
                    "response_data": response_data
                }
                await self.db_helper.update(session, "data_access_requests", request_id, update_payload)
            except Exception as e:
                logger.error("process_data_access_request_failed", request_id=request_id, error=str(e))
                raise

    async def create_audit_log(self, log_data: AuditLogCreate) -> UUID:
        """Creates an audit log entry.

        Args:
            log_data (AuditLogCreate): Data for the audit log entry.

        Returns:
            UUID: The ID of the created audit log entry.
        """
        if not self.db_manager.is_initialized: return uuid4() # Dummy UUID
        async with self.db_manager.get_session() as session:
            try:
                new_log = await self.db_helper.create(session, "audit_logs", log_data.model_dump())
                return new_log["audit_id"]
            except Exception as e:
                logger.error("create_audit_log_failed", entity_type=log_data.entity_type, entity_id=log_data.entity_id, error=str(e))
                raise

    async def get_audit_logs(self, entity_type: Optional[str] = None, entity_id: Optional[str] = None, limit: int = 100) -> List[AuditLogResponse]:
        """Retrieves audit logs based on optional filters.

        Args:
            entity_type (Optional[str]): Filter by entity type.
            entity_id (Optional[str]): Filter by entity ID.
            limit (int): Maximum number of logs to retrieve.

        Returns:
            List[AuditLogResponse]: A list of audit log responses.
        """
        if not self.db_manager.is_initialized: return []
        async with self.db_manager.get_session() as session:
            try:
                conditions = {}
                if entity_type: conditions["entity_type"] = entity_type
                if entity_id: conditions["entity_id"] = entity_id

                logs = await self.db_helper.get_all(session, "audit_logs", conditions=conditions, order_by="timestamp DESC", limit=limit)
                return [AuditLogResponse(**r) for r in logs]
            except Exception as e:
                logger.error("get_audit_logs_failed", entity_type=entity_type, entity_id=entity_id, error=str(e))
                raise

    async def generate_consent_summary(self) -> ConsentSummary:
        """Generates a summary report of consent data.

        Returns:
            ConsentSummary: A summary of consent information.
        """
        if not self.db_manager.is_initialized: return ConsentSummary(total_subjects=0, consent_breakdown={}, recent_changes=0) # Dummy summary
        async with self.db_manager.get_session() as session:
            try:
                total_subjects_query = "SELECT COUNT(*) as count FROM data_subjects"
                total_result = await self.db_manager.fetch_one(total_subjects_query)
                total_subjects = total_result["count"]

                recent_changes_query = """
                    SELECT COUNT(*) as count FROM consent_records
                    WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '30 days'
                """
                recent_result = await self.db_manager.fetch_one(recent_changes_query)
                recent_changes = recent_result["count"]

                # For a more realistic breakdown, you'd query the database.
                # This is a placeholder for now.
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
            except Exception as e:
                logger.error("generate_consent_summary_failed", error=str(e))
                raise

# SERVICE
class ComplianceService:
    """Service layer for compliance-related business logic."""
    def __init__(self, repo: ComplianceRepository):
        """Initializes the ComplianceService with a ComplianceRepository."""
        self.repo = repo

    async def update_consent(self, consent_data: ConsentUpdate) -> UUID:
        """Updates user consent and logs the action.

        Args:
            consent_data (ConsentUpdate): The consent data to update.

        Returns:
            UUID: The ID of the recorded consent entry.
        """
        try:
            consent_id = await self.repo.update_consent(consent_data)

            logger.info("consent_updated", customer_id=consent_data.customer_id,
                       consent_type=consent_data.consent_type,
                       consent_given=consent_data.consent_given)

            await self.repo.create_audit_log(AuditLogCreate(
                entity_type="consent",
                entity_id=str(consent_id),
                action="update",
                actor_id=consent_data.customer_id,
                actor_type="user",
                changes={
                    "consent_type": consent_data.consent_type,
                    "consent_given": consent_data.consent_given
                }
            ))

            return consent_id
        except Exception as e:
            logger.error("update_consent_service_failed", customer_id=consent_data.customer_id, error=str(e))
            raise

    async def handle_data_access_request(self, request_data: DataAccessRequest) -> DataAccessRequestResponse:
        """Handles a GDPR data access request, creates it, and processes it.

        Args:
            request_data (DataAccessRequest): The data access request to handle.

        Returns:
            DataAccessRequestResponse: The response of the handled request.
        """
        try:
            request = await self.repo.create_data_access_request(request_data)

            logger.info("data_access_request_created", request_id=str(request.request_id),
                       customer_id=request_data.customer_id,
                       request_type=request_data.request_type.value)

            # In production, trigger data collection from all systems
            # For now, auto-complete with simulated data for ACCESS requests
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
        except Exception as e:
            logger.error("handle_data_access_request_service_failed", customer_id=request_data.customer_id, error=str(e))
            raise

# AGENT
class ComplianceAgent(BaseAgent):
    """Compliance Agent for managing GDPR, data retention, and regulatory reporting.

    This agent integrates with a FastAPI server for API endpoints and Kafka for message processing.
    """
    def __init__(self, agent_id: str, agent_type: str):
        """Initializes the ComplianceAgent.

        Args:
            agent_id (str): The unique identifier for this agent instance.
            agent_type (str): The type of the agent (e.g., 'compliance').
        """
        super().__init__(agent_id, agent_type)
        self.db_manager: Optional[DatabaseManager] = None
        self.db_helper: Optional[DatabaseHelper] = None
        self.repository: Optional[ComplianceRepository] = None
        self.service: Optional[ComplianceService] = None
        self._db_initialized = False
        self.fastapi_app = self._create_fastapi_app()

    async def setup(self):
        """Sets up the database connection and initializes repository and service."""
        try:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                logger.error("DATABASE_URL environment variable not set.")
                raise ValueError("DATABASE_URL environment variable not set.")

            self.db_manager = await get_database_manager(db_url)
            self.db_helper = DatabaseHelper(self.db_manager)
            self.repository = ComplianceRepository(self.db_manager, self.db_helper)
            self.service = ComplianceService(self.repository)
            self._db_initialized = True
            logger.info("ComplianceAgent database and services initialized.")
        except Exception as e:
            logger.error("ComplianceAgent setup failed", error=str(e))
            # Depending on the error, you might want to exit or retry
            raise

    async def process_message(self, message: AgentMessage):
        """Processes incoming messages for the Compliance Agent.

        Args:
            message (AgentMessage): The message received by the agent.
        """
        logger.info("Received message", message_type=message.message_type.value, sender=message.sender_id)
        try:
            if not self._db_initialized:
                logger.warning("Database not initialized, skipping message processing.")
                return

            if message.message_type == MessageType.CONSENT_UPDATE:
                consent_data = ConsentUpdate(**message.payload)
                await self.service.update_consent(consent_data)
                await self.send_message(MessageType.INFO, "Consent updated successfully.", recipient_id=message.sender_id)
            elif message.message_type == MessageType.DATA_ACCESS_REQUEST:
                request_data = DataAccessRequest(**message.payload)
                response = await self.service.handle_data_access_request(request_data)
                await self.send_message(MessageType.INFO, response.model_dump_json(), recipient_id=message.sender_id)
            elif message.message_type == MessageType.AUDIT_LOG_CREATE:
                log_data = AuditLogCreate(**message.payload)
                audit_id = await self.service.repo.create_audit_log(log_data)
                await self.send_message(MessageType.INFO, f"Audit log created with ID: {audit_id}", recipient_id=message.sender_id)
            else:
                logger.warning("Unknown message type received", message_type=message.message_type.value)
                await self.send_message(MessageType.ERROR, "Unknown message type.", recipient_id=message.sender_id)
        except Exception as e:
            logger.error("Error processing message", message_type=message.message_type.value, error=str(e))
            await self.send_message(MessageType.ERROR, f"Failed to process message: {str(e)}", recipient_id=message.sender_id)

    def _create_fastapi_app(self) -> FastAPI:
        """Creates and configures the FastAPI application for the agent."""
        app = FastAPI(title="Compliance Agent API", version="1.0.0", description="API for managing GDPR compliance, consent, data access requests, and audit logging.")

        @app.on_event("startup")
        async def startup_event():
            await self.setup()

        @app.on_event("shutdown")
        async def shutdown_event():
            if self.db_manager:
                await self.db_manager.close()
                logger.info("Database connection closed.")

        @app.get("/", summary="Root endpoint", tags=["General"])
        async def root():
            """Root endpoint returning basic agent information."""
            return {"message": "Compliance Agent is running", "agent_id": self.agent_id, "agent_type": self.agent_type}

        @app.get("/health", summary="Health check endpoint", tags=["Monitoring"])
        async def health_check():
            """Performs a health check of the agent and its dependencies."""
            db_status = "uninitialized"
            if self._db_initialized:
                try:
                    async with self.db_manager.get_session() as session:
                        # Perform a simple query to check DB connectivity
                        await self.db_manager.fetch_one("SELECT 1")
                    db_status = "healthy"
                except Exception as e:
                    db_status = f"unhealthy: {e}"
                    logger.error("Health check DB failed", error=str(e))
            return {"status": "healthy", "agent": "compliance_agent", "version": "1.0.0", "database": db_status}

        @app.post("/api/v1/compliance/consent", summary="Update user consent", response_model=Dict[str, UUID], tags=["Consent Management"])
        async def update_consent_endpoint(
            consent_data: ConsentUpdate = Body(..., description="Consent data to update."),
        ):
            """Updates or records user consent preferences.

            Args:
                consent_data (ConsentUpdate): The consent data containing customer ID, consent type, and status.

            Returns:
                Dict[str, UUID]: A dictionary containing the ID of the recorded consent.
            """
            try:
                if not self.service:
                    raise HTTPException(status_code=503, detail="Service not initialized.")
                consent_id = await self.service.update_consent(consent_data)
                return {"consent_id": consent_id}
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error("update_consent_endpoint_failed", error=str(e))
                raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

        @app.post("/api/v1/compliance/data-access-request", summary="Create a GDPR data access request", response_model=DataAccessRequestResponse, tags=["Data Access Requests"])
        async def create_data_access_request_endpoint(
            request_data: DataAccessRequest = Body(..., description="Data for the access request."),
        ):
            """Creates a new GDPR data access request (e.g., access, erasure, portability).

            Args:
                request_data (DataAccessRequest): The data access request details.

            Returns:
                DataAccessRequestResponse: The details of the created data access request.
            """
            try:
                if not self.service:
                    raise HTTPException(status_code=503, detail="Service not initialized.")
                request = await self.service.handle_data_access_request(request_data)
                return request
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error("create_data_access_request_endpoint_failed", error=str(e))
                raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

        @app.post("/api/v1/compliance/audit-log", summary="Create an audit log entry", response_model=AuditLogResponse, tags=["Audit Logging"])
        async def create_audit_log_endpoint(
            log_data: AuditLogCreate = Body(..., description="Data for the audit log entry."),
        ):
            """Records an audit trail of significant actions within the system.

            Args:
                log_data (AuditLogCreate): The audit log entry details.

            Returns:
                AuditLogResponse: The details of the created audit log entry.
            """
            try:
                if not self.service or not self.service.repo:
                    raise HTTPException(status_code=503, detail="Service or Repository not initialized.")
                audit_id = await self.service.repo.create_audit_log(log_data)
                # Fetch the created log to return a complete AuditLogResponse
                logs = await self.service.repo.get_audit_logs(entity_type=log_data.entity_type, entity_id=log_data.entity_id, limit=1)
                if logs:
                    return logs[0]
                raise HTTPException(status_code=500, detail="Failed to retrieve created audit log.")
            except Exception as e:
                logger.error("create_audit_log_endpoint_failed", error=str(e))
                raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

        @app.get("/api/v1/compliance/audit-logs", summary="Retrieve audit logs", response_model=List[AuditLogResponse], tags=["Audit Logging"])
        async def get_audit_logs_endpoint(
            entity_type: Optional[str] = Query(None, description="Filter logs by entity type."),
            entity_id: Optional[str] = Query(None, description="Filter logs by entity ID."),
            limit: int = Query(100, le=1000, description="Maximum number of logs to return."),
        ):
            """Retrieves a list of audit logs, with optional filtering.

            Args:
                entity_type (Optional[str]): Filter logs by the type of entity involved.
                entity_id (Optional[str]): Filter logs by the specific ID of the entity.
                limit (int): The maximum number of audit logs to retrieve.

            Returns:
                List[AuditLogResponse]: A list of matching audit log entries.
            """
            try:
                if not self.service or not self.service.repo:
                    raise HTTPException(status_code=503, detail="Service or Repository not initialized.")
                logs = await self.service.repo.get_audit_logs(entity_type, entity_id, limit)
                return logs
            except Exception as e:
                logger.error("get_audit_logs_endpoint_failed", error=str(e))
                raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

        @app.get("/api/v1/compliance/reports/consent-summary", summary="Generate consent summary report", response_model=ConsentSummary, tags=["Reporting"])
        async def get_consent_summary_endpoint(
        ):
            """Generates a summary report of all user consent information.

            Returns:
                ConsentSummary: A summary object detailing total subjects, consent breakdown, and recent changes.
            """
            try:
                if not self.service or not self.service.repo:
                    raise HTTPException(status_code=503, detail="Service or Repository not initialized.")
                summary = await self.service.repo.generate_consent_summary()
                return summary
            except Exception as e:
                logger.error("get_consent_summary_endpoint_failed", error=str(e))
                raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

        return app


if __name__ == "__main__":
    agent_id = os.getenv("AGENT_ID", "compliance-agent-001")
    agent_type = os.getenv("AGENT_TYPE", "compliance")
    compliance_agent = ComplianceAgent(agent_id=agent_id, agent_type=agent_type)

    # Run setup to initialize DB and services before starting FastAPI
    # This is handled by @app.on_event("startup") now, so we just need to run the app.

    # Get port from environment variable, default to 8017
    port = int(os.getenv("COMPLIANCE_AGENT_PORT", 8017))
    logger.info("Starting Compliance Agent FastAPI server", port=port, agent_id=agent_id)
    uvicorn.run(compliance_agent.fastapi_app, host="0.0.0.0", port=port)

