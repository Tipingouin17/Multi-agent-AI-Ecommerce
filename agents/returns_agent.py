
"""
Returns Agent - Multi-Agent E-Commerce System

This agent manages product returns, RMA (Return Merchandise Authorization),
refund processing, and return analytics.
"""

import os
import sys
import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID
from enum import Enum

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field
import structlog
import uvicorn

# Add project root to sys.path for shared modules
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.database import DatabaseManager, get_database_manager
from shared.db_helpers import DatabaseHelper

# Initialize logger
logger = structlog.get_logger(__name__)

# Environment variables for configuration
KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "localhost:9092")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/ecommerce")
AGENT_ID = os.getenv("AGENT_ID", "returns_agent")
AGENT_TYPE = os.getenv("AGENT_TYPE", "returns_management")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "8009"))

# ENUMS
class ReturnStatus(str, Enum):
    """Enum for the status of a return request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    RECEIVED = "received"
    INSPECTED = "inspected"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
    async def initialize(self):
        """Initialize agent."""
        await super().initialize()
        
    async def cleanup(self):
        """Cleanup agent."""
        await super().cleanup()
        
    async def process_business_logic(self, data):
        """Process business logic."""
        return {"status": "success"}


class RefundMethod(str, Enum):
    """Enum for the method of refund."""
    ORIGINAL = "original"
    STORE_CREDIT = "store_credit"
    EXCHANGE = "exchange"

# MODELS
class ReturnReason(BaseModel):
    """Pydantic model for a return reason."""
    reason_id: int = Field(..., description="Unique identifier for the return reason")
    reason_code: str = Field(..., description="Short code for the return reason (e.g., 'DEFECTIVE')")
    reason_name: str = Field(..., description="Human-readable name of the return reason")
    category: str = Field(..., description="Category of the return reason (e.g., 'defective', 'wrong_item')")
    requires_images: bool = Field(False, description="Indicates if images are required for this reason")
    auto_approve: bool = Field(False, description="Indicates if returns with this reason are auto-approved")

class ReturnItemRequest(BaseModel):
    """Pydantic model for an item within a return request."""
    order_item_id: str = Field(..., description="ID of the original order item")
    product_id: str = Field(..., description="ID of the product being returned")
    quantity: int = Field(..., gt=0, description="Quantity of the product being returned")
    reason: str = Field(..., description="Specific reason for returning this item")

class ReturnRequestCreate(BaseModel):
    """Pydantic model for creating a new return request."""
    order_id: str = Field(..., description="ID of the original order")
    customer_id: str = Field(..., description="ID of the customer initiating the return")
    reason_id: int = Field(..., description="ID of the return reason")
    reason_details: Optional[str] = Field(None, description="Additional details about the return reason")
    requested_items: List[ReturnItemRequest] = Field(..., description="List of items requested for return")
    return_method: str = Field("mail", description="Method of return (e.g., 'pickup', 'dropoff', 'mail')")
    refund_method: RefundMethod = Field(RefundMethod.ORIGINAL, description="Preferred refund method")
    images: List[str] = Field([], description="List of image URLs supporting the return request")

class ReturnRequest(BaseModel):
    """Pydantic model for a complete return request."""
    return_id: UUID = Field(..., description="Unique identifier for the return request")
    order_id: str = Field(..., description="ID of the original order")
    customer_id: str = Field(..., description="ID of the customer")
    return_status: ReturnStatus = Field(..., description="Current status of the return request")
    reason_id: int = Field(..., description="ID of the return reason")
    reason_details: Optional[str] = Field(None, description="Additional details about the return reason")
    refund_amount: Optional[Decimal] = Field(None, description="Calculated refund amount")
    refund_method: str = Field(..., description="Method used for refund")
    tracking_number: Optional[str] = Field(None, description="Tracking number for the return shipment")
    created_at: datetime = Field(..., description="Timestamp of creation")
    updated_at: datetime = Field(..., description="Timestamp of last update")

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda dt: dt.isoformat(),
            Decimal: lambda d: str(d)
        }

# REPOSITORY
class ReturnsRepository:
    """Handles database operations for return-related entities."""
    def __init__(self, db_manager: DatabaseManager):
        """
        Initializes the ReturnsRepository with a database manager.

        Args:
            db_manager (DatabaseManager): The database manager instance.
        """
        self.db_manager = db_manager
        self.db_helper = DatabaseHelper(db_manager)

    async def get_return_reasons(self) -> List[ReturnReason]:
        """
        Retrieves all active return reasons from the database.

        Returns:
            List[ReturnReason]: A list of active return reasons.
        """
        if not self.db_manager._db_initialized: # Accessing protected member for check
            logger.warning("Database not initialized, returning empty list for return reasons.")
            return []
        try:
            query = "SELECT * FROM return_reasons WHERE is_active = true"
            async with self.db_manager.get_session() as session:
                results = await self.db_helper.get_all(session, query)
                return [ReturnReason(**r) for r in results]
        except Exception as e:
            logger.error("get_return_reasons_db_error", error=str(e))
            raise

    async def create_return_request(self, return_data: ReturnRequestCreate) -> ReturnRequest:
        """
        Creates a new return request in the database.

        Args:
            return_data (ReturnRequestCreate): The data for the new return request.

        Returns:
            ReturnRequest: The created return request.
        """
        if not self.db_manager._db_initialized:
            logger.warning("Database not initialized, cannot create return request.")
            raise HTTPException(status_code=500, detail="Database not initialized")
        try:
            query = """
                INSERT INTO return_requests (order_id, customer_id, reason_id, reason_details,
                                            requested_items, return_method, refund_method, images, return_status)
                VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8::jsonb, $9)
                RETURNING *
            """
            async with self.db_manager.get_session() as session:
                result = await self.db_helper.create(
                    session, query, return_data.order_id, return_data.customer_id, return_data.reason_id,
                    return_data.reason_details, json.dumps([item.model_dump() for item in return_data.requested_items]),
                    return_data.return_method, return_data.refund_method.value, json.dumps(return_data.images),
                    ReturnStatus.PENDING.value
                )
                return ReturnRequest(**result)
        except Exception as e:
            logger.error("create_return_request_db_error", error=str(e), return_data=return_data.model_dump_json())
            raise

    async def get_return_request(self, return_id: UUID) -> Optional[ReturnRequest]:
        """
        Retrieves a specific return request by its ID.

        Args:
            return_id (UUID): The unique identifier of the return request.

        Returns:
            Optional[ReturnRequest]: The return request if found, otherwise None.
        """
        if not self.db_manager._db_initialized:
            logger.warning("Database not initialized, cannot get return request.")
            return None
        try:
            query = "SELECT * FROM return_requests WHERE return_id = $1"
            async with self.db_manager.get_session() as session:
                result = await self.db_helper.get_by_id(session, query, return_id)
                return ReturnRequest(**result) if result else None
        except Exception as e:
            logger.error("get_return_request_db_error", error=str(e), return_id=str(return_id))
            raise

    async def update_return_status(self, return_id: UUID, status: ReturnStatus, approved_by: Optional[str] = None) -> Optional[ReturnRequest]:
        """
        Updates the status of a return request.

        Args:
            return_id (UUID): The unique identifier of the return request.
            status (ReturnStatus): The new status for the return request.
            approved_by (Optional[str]): The user who approved the return, if applicable.

        Returns:
            Optional[ReturnRequest]: The updated return request if found, otherwise None.
        """
        if not self.db_manager._db_initialized:
            logger.warning("Database not initialized, cannot update return status.")
            return None
        try:
            set_clauses = ["return_status = $2", "updated_at = CURRENT_TIMESTAMP"]
            params = [return_id, status.value]

            if status == ReturnStatus.APPROVED:
                set_clauses.append("approved_at = COALESCE(approved_at, CURRENT_TIMESTAMP)")
                if approved_by:
                    set_clauses.append("approved_by = $3")
                    params.append(approved_by)
            elif status == ReturnStatus.RECEIVED:
                set_clauses.append("received_at = COALESCE(received_at, CURRENT_TIMESTAMP)")
            elif status == ReturnStatus.INSPECTED:
                set_clauses.append("inspected_at = COALESCE(inspected_at, CURRENT_TIMESTAMP)")
            elif status == ReturnStatus.REFUNDED:
                set_clauses.append("refunded_at = COALESCE(refunded_at, CURRENT_TIMESTAMP)")

            query = f"UPDATE return_requests SET {', '.join(set_clauses)} WHERE return_id = $1 RETURNING *"
            
            async with self.db_manager.get_session() as session:
                result = await self.db_helper.update(session, query, *params)
                return ReturnRequest(**result) if result else None
        except Exception as e:
            logger.error("update_return_status_db_error", error=str(e), return_id=str(return_id), status=status.value)
            raise

    async def get_customer_returns(self, customer_id: str, limit: int = 50) -> List[ReturnRequest]:
        """
        Retrieves a list of return requests for a given customer.

        Args:
            customer_id (str): The ID of the customer.
            limit (int): The maximum number of returns to retrieve.

        Returns:
            List[ReturnRequest]: A list of return requests for the customer.
        """
        if not self.db_manager._db_initialized:
            logger.warning("Database not initialized, returning empty list for customer returns.")
            return []
        try:
            query = "SELECT * FROM return_requests WHERE customer_id = $1 ORDER BY created_at DESC LIMIT $2"
            async with self.db_manager.get_session() as session:
                results = await self.db_helper.get_all(session, query, customer_id, limit)
                return [ReturnRequest(**r) for r in results]
        except Exception as e:
            logger.error("get_customer_returns_db_error", error=str(e), customer_id=customer_id)
            raise

# SERVICE
class ReturnsService:
    """Handles business logic for return operations."""
    def __init__(self, repo: ReturnsRepository):
        """
        Initializes the ReturnsService with a ReturnsRepository.

        Args:
            repo (ReturnsRepository): The repository for return data.
        """
        self.repo = repo

    async def create_return(self, return_data: ReturnRequestCreate) -> Dict[str, Any]:
        """
        Creates a new return request and processes auto-approval if applicable.

        Args:
            return_data (ReturnRequestCreate): The data for the new return request.

        Returns:
            Dict[str, Any]: A dictionary containing the created return request and status.
        """
        try:
            return_request = await self.repo.create_return_request(return_data)

            reasons = await self.repo.get_return_reasons()
            reason = next((r for r in reasons if r.reason_id == return_data.reason_id), None)

            auto_approved = False
            if reason and reason.auto_approve:
                return_request = await self.repo.update_return_status(
                    return_request.return_id, ReturnStatus.APPROVED
                )
                auto_approved = True

            logger.info("return_created", return_id=str(return_request.return_id),
                       customer_id=return_data.customer_id, auto_approved=auto_approved)

            return {
                "return_request": return_request,
                "message": "Return request created successfully",
                "auto_approved": auto_approved
            }
        except Exception as e:
            logger.error("create_return_service_error", error=str(e), customer_id=return_data.customer_id)
            raise

    async def approve_return(self, return_id: UUID, approved_by: str) -> ReturnRequest:
        """
        Approves a return request.

        Args:
            return_id (UUID): The ID of the return request to approve.
            approved_by (str): The identifier of the user approving the return.

        Returns:
            ReturnRequest: The approved return request.

        Raises:
            ValueError: If the return request is not found.
        """
        try:
            return_request = await self.repo.update_return_status(return_id, ReturnStatus.APPROVED, approved_by)
            if not return_request:
                raise ValueError("Return request not found")

            logger.info("return_approved", return_id=str(return_id), approved_by=approved_by)
            return return_request
        except Exception as e:
            logger.error("approve_return_service_error", error=str(e), return_id=str(return_id))
            raise

    async def process_refund(self, return_id: UUID, refund_amount: Decimal) -> Dict[str, Any]:
        """
        Processes a refund for a given return request.

        Args:
            return_id (UUID): The ID of the return request.
            refund_amount (Decimal): The amount to be refunded.

        Returns:
            Dict[str, Any]: A dictionary containing the updated return request and refund details.

        Raises:
            ValueError: If the return request is not found.
        """
        try:
            return_request = await self.repo.get_return_request(return_id)
            if not return_request:
                raise ValueError("Return request not found")

            # In a real system, this would interact with a payment gateway
            # For now, we just update the status to REFUNDED
            return_request = await self.repo.update_return_status(return_id, ReturnStatus.REFUNDED)

            logger.info("refund_processed", return_id=str(return_id), amount=float(refund_amount))

            return {
                "return_request": return_request,
                "refund_amount": refund_amount,
                "message": "Refund processed successfully"
            }
        except Exception as e:
            logger.error("process_refund_service_error", error=str(e), return_id=str(return_id))
            raise

# AGENT
class ReturnsAgent(BaseAgent):
    """Returns Agent for managing product returns and refunds in the e-commerce system."""
    def __init__(self, agent_id: str, agent_type: str, kafka_broker_url: str, database_url: str):
        """
        Initializes the ReturnsAgent.

        Args:
            agent_id (str): Unique identifier for the agent.
            agent_type (str): Type of the agent.
            kafka_broker_url (str): URL for the Kafka broker.
            database_url (str): URL for the database connection.
        """
        super().__init__(agent_id=agent_id, kafka_broker_url=kafka_broker_url)
        self.db_manager = DatabaseManager(database_url)
        self.returns_repo = ReturnsRepository(self.db_manager)
        self.returns_service = ReturnsService(self.returns_repo)
        self._db_initialized = False

    async def setup(self):
        """
        Performs initial setup for the agent, including database connection.
        """
        logger.info("ReturnsAgent setup initiated.")
        try:
            await self.db_manager.connect()
            self._db_initialized = True
            logger.info("ReturnsAgent database connected successfully.")
        except Exception as e:
            logger.error("ReturnsAgent database connection failed", error=str(e))
            sys.exit(1) # Exit if database connection fails

    async def process_message(self, message: AgentMessage):
        """
        Processes incoming Kafka messages relevant to return operations.

        Args:
            message (AgentMessage): The incoming message from Kafka.
        """
        logger.info("Processing message", message_type=message.message_type, sender=message.sender, topic=message.topic)
        if not self._db_initialized:
            logger.warning("Database not initialized, skipping message processing.")
            return

        try:
            if message.message_type == MessageType.RETURN_REQUEST_CREATED:
                # Example: A new return request was created by another agent or system
                return_id = message.payload.get("return_id")
                if return_id:
                    return_request = await self.returns_repo.get_return_request(UUID(return_id))
                    if return_request:
                        logger.info("Received and processed new return request notification", return_id=str(return_request.return_id))
                        # Potentially trigger further internal processing or notifications
                        await self.send_message(
                            recipient_agent_id="notification_agent",
                            message_type=MessageType.NOTIFICATION,
                            payload={
                                "type": "return_request_received",
                                "return_id": str(return_request.return_id),
                                "customer_id": return_request.customer_id,
                                "status": return_request.return_status.value
                            }
                        )

            elif message.message_type == MessageType.ORDER_CANCELLED:
                # Example: An order was cancelled, check if it had an associated return
                order_id = message.payload.get("order_id")
                if order_id:
                    # This would require a method to get returns by order_id
                    # For now, simulate checking for related returns
                    logger.info("Received order cancelled notification, checking for related returns", order_id=order_id)
                    # In a real scenario, we'd query the DB for returns linked to this order_id
                    # If found, we might cancel the return or update its status

            elif message.message_type == MessageType.RETURN_APPROVED_EXTERNAL:
                # Example: A return was approved via an external system, update our records
                return_id = message.payload.get("return_id")
                approved_by = message.payload.get("approved_by", "external_system")
                if return_id:
                    await self.returns_service.approve_return(UUID(return_id), approved_by)
                    logger.info("Return status updated to APPROVED by external system", return_id=return_id)

            # Add other message types as needed

        except Exception as e:
            logger.error("Error processing Kafka message", error=str(e), message=message.model_dump_json())

    async def shutdown(self):
        """
        Performs cleanup operations during agent shutdown.
        """
        logger.info("ReturnsAgent shutdown initiated.")
        try:
            await self.db_manager.disconnect()
            logger.info("ReturnsAgent database disconnected.")
        except Exception as e:
            logger.error("ReturnsAgent database disconnection failed", error=str(e))

# FastAPI APP
app = FastAPI(title="Returns Agent API", version="1.0.0",
              description="API for managing product returns and refunds in the e-commerce system.")

@app.on_event("startup")
async def startup_event():
    """Handles startup events for the FastAPI application."""
    global returns_agent
    returns_agent = ReturnsAgent(AGENT_ID, AGENT_TYPE, KAFKA_BROKER_URL, DATABASE_URL)
    await returns_agent.setup()
    # Start Kafka consumer in a background task if needed

@app.on_event("shutdown")
async def shutdown_event():
    """Handles shutdown events for the FastAPI application."""
    global returns_agent
    await returns_agent.shutdown()

async def get_returns_service() -> ReturnsService:
    """
    Dependency injection for ReturnsService.

    Returns:
        ReturnsService: An instance of ReturnsService.
    """
    if not returns_agent._db_initialized:
        raise HTTPException(status_code=503, detail="Service unavailable: Database not initialized")
    return returns_agent.returns_service

# ENDPOINTS
@app.get("/health", tags=["Monitoring"], summary="Health check endpoint")
async def health_check():
    """
    Performs a health check for the Returns Agent.

    Returns:
        Dict[str, Any]: A dictionary indicating the health status.
    """
    db_status = "connected" if returns_agent._db_initialized else "disconnected"
    return {"status": "healthy", "agent": AGENT_ID, "version": "1.0.0", "database_status": db_status}

@app.get("/", tags=["Root"], summary="Root endpoint for Returns Agent API")
async def root():
    """
    Root endpoint providing basic information about the Returns Agent API.

    Returns:
        Dict[str, str]: A welcome message and API version.
    """
    return {"message": "Returns Agent API", "version": "1.0.0"}

@app.get("/api/v1/returns/reasons", response_model=List[ReturnReason], tags=["Returns"], summary="Get all active return reasons")
async def get_return_reasons(service: ReturnsService = Depends(get_returns_service)):
    """
    Retrieves a list of all active return reasons.

    Returns:
        List[ReturnReason]: A list of available return reasons.
    """
    try:
        reasons = await service.repo.get_return_reasons()
        return reasons
    except Exception as e:
        logger.error("get_return_reasons_api_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve return reasons: {e}")

@app.post("/api/v1/returns", response_model=ReturnRequest, tags=["Returns"], summary="Create a new return request")
async def create_return(
    return_data: ReturnRequestCreate = Body(..., description="Data for creating a new return request"),
    service: ReturnsService = Depends(get_returns_service)
):
    """
    Creates a new return request in the system.

    Args:
        return_data (ReturnRequestCreate): The details of the return request.

    Returns:
        ReturnRequest: The newly created return request.
    """
    try:
        result = await service.create_return(return_data)
        return result["return_request"]
    except ValueError as e:
        logger.warning("create_return_invalid_data", error=str(e), return_data=return_data.model_dump_json())
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise # Re-raise HTTPExceptions directly
    except Exception as e:
        logger.error("create_return_api_error", error=str(e), return_data=return_data.model_dump_json())
        raise HTTPException(status_code=500, detail=f"Failed to create return request: {e}")

@app.get("/api/v1/returns/{return_id}", response_model=ReturnRequest, tags=["Returns"], summary="Get a return request by ID")
async def get_return(
    return_id: UUID = Path(..., description="The UUID of the return request"),
    service: ReturnsService = Depends(get_returns_service)
):
    """
    Retrieves details of a specific return request by its ID.

    Args:
        return_id (UUID): The unique identifier of the return request.

    Returns:
        ReturnRequest: The details of the specified return request.

    Raises:
        HTTPException: If the return request is not found (404) or a server error occurs (500).
    """
    try:
        return_request = await service.repo.get_return_request(return_id)
        if not return_request:
            raise HTTPException(status_code=404, detail="Return not found")
        return return_request
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_return_api_error", error=str(e), return_id=str(return_id))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve return: {e}")

@app.post("/api/v1/returns/{return_id}/approve", response_model=ReturnRequest, tags=["Returns"], summary="Approve a return request")
async def approve_return_api(
    return_id: UUID = Path(..., description="The UUID of the return request to approve"),
    approved_by: str = Body(..., embed=True, description="Identifier of the user approving the return"),
    service: ReturnsService = Depends(get_returns_service)
):
    """
    Approves a specific return request.

    Args:
        return_id (UUID): The unique identifier of the return request.
        approved_by (str): The identifier of the user or system approving the return.

    Returns:
        ReturnRequest: The approved return request.

    Raises:
        HTTPException: If the return request is not found (400) or a server error occurs (500).
    """
    try:
        return_request = await service.approve_return(return_id, approved_by)
        return return_request
    except ValueError as e:
        logger.warning("approve_return_not_found", error=str(e), return_id=str(return_id))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("approve_return_api_error", error=str(e), return_id=str(return_id))
        raise HTTPException(status_code=500, detail=f"Failed to approve return: {e}")

@app.post("/api/v1/returns/{return_id}/refund", response_model=Dict[str, Any], tags=["Returns"], summary="Process a refund for a return request")
async def process_refund_api(
    return_id: UUID = Path(..., description="The UUID of the return request for which to process refund"),
    refund_amount: Decimal = Body(..., embed=True, description="The amount to refund"),
    service: ReturnsService = Depends(get_returns_service)
):
    """
    Processes a refund for a specific return request.

    Args:
        return_id (UUID): The unique identifier of the return request.
        refund_amount (Decimal): The amount to be refunded.

    Returns:
        Dict[str, Any]: A dictionary containing the updated return request and refund details.

    Raises:
        HTTPException: If the return request is not found (400) or a server error occurs (500).
    """
    try:
        result = await service.process_refund(return_id, refund_amount)
        return result
    except ValueError as e:
        logger.warning("process_refund_not_found", error=str(e), return_id=str(return_id))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("process_refund_api_error", error=str(e), return_id=str(return_id))
        raise HTTPException(status_code=500, detail=f"Failed to process refund: {e}")

@app.get("/api/v1/returns/customer/{customer_id}", response_model=List[ReturnRequest], tags=["Returns"], summary="Get all return requests for a customer")
async def get_customer_returns_api(
    customer_id: str = Path(..., description="The ID of the customer"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of returns to retrieve"),
    service: ReturnsService = Depends(get_returns_service)
):
    """
    Retrieves a list of return requests associated with a specific customer.

    Args:
        customer_id (str): The unique identifier of the customer.
        limit (int): The maximum number of return requests to return.

    Returns:
        List[ReturnRequest]: A list of return requests for the specified customer.
    """
    try:
        returns = await service.repo.get_customer_returns(customer_id, limit)
        return returns
    except Exception as e:
        logger.error("get_customer_returns_api_error", error=str(e), customer_id=customer_id)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve customer returns: {e}")


# Main execution block
if __name__ == "__main__":
    # Initialize agent and FastAPI app
    # The agent will be initialized and setup in the startup_event of FastAPI
    logger.info("Starting Returns Agent FastAPI application...")
    uvicorn.run(app, host="0.0.0.0", port=FASTAPI_PORT)


