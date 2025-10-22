
"""
Fraud Detection Agent - Multi-Agent E-Commerce System

This agent provides ML-based fraud detection, risk scoring, and anomaly detection
for transactions, orders, and user behavior.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID
from enum import Enum

from shared.db_helpers import DatabaseHelper
import hashlib

from fastapi import FastAPI, HTTPException, Depends, Body, Path
from pydantic import BaseModel, Field
import structlog
import sys
import os
import uvicorn

# Add project root to Python path for shared modules
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.base_agent_v2 import BaseAgentV2, MessageType, AgentMessage
from shared.database import DatabaseManager, get_database_manager

# Initialize structured logger
logger = structlog.get_logger(__name__)

# --- Enums ---
class RiskLevel(str, Enum):
    """Enumeration for different risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FraudDecision(str, Enum):
    """Enumeration for different fraud decisions."""
    APPROVED = "approved"
    FLAGGED = "flagged"
    BLOCKED = "blocked"
    MANUAL_REVIEW = "manual_review"

# --- Pydantic Models ---
class FraudCheckRequest(BaseModel):
    """Model for a fraud check request."""
    entity_type: str = Field(..., description="Type of entity to check (e.g., 'order', 'payment').")
    entity_id: str = Field(..., description="Unique ID of the entity.")
    customer_id: Optional[str] = Field(None, description="The ID of the customer associated with the entity.")
    data: Dict[str, Any] = Field(..., description="Entity-specific data for fraud analysis.")

class FraudSignal(BaseModel):
    """Model for a single fraud signal detected."""
    signal_type: str = Field(..., description="The type of fraud signal.")
    signal_value: str = Field(..., description="The value of the signal.")
    risk_contribution: int = Field(..., description="The risk score contribution of this signal.")

class FraudCheckResult(BaseModel):
    """Model for the result of a fraud check."""
    check_id: UUID = Field(..., description="The unique ID of the fraud check.")
    entity_type: str = Field(..., description="The type of entity checked.")
    entity_id: str = Field(..., description="The ID of the entity checked.")
    risk_score: int = Field(..., description="The calculated risk score (0-100).")
    risk_level: RiskLevel = Field(..., description="The determined risk level.")
    decision: FraudDecision = Field(..., description="The recommended fraud decision.")
    triggered_rules: List[Dict[str, Any]] = Field([], description="A list of fraud rules that were triggered.")
    signals: List[FraudSignal] = Field(..., description="A list of fraud signals that were detected.")
    recommendations: List[str] = Field(..., description="A list of recommended actions.")
    created_at: datetime = Field(..., description="The timestamp of when the check was created.")

class BlockEntityRequest(BaseModel):
    """Model for a request to block an entity."""
    entity_type: str = Field(..., description="Type of entity to block (e.g., 'email', 'ip').")
    entity_value: str = Field(..., description="The value of the entity to block.")
    reason: str = Field(..., description="The reason for blocking the entity.")
    duration_hours: Optional[int] = Field(None, description="Duration in hours for the block (None for permanent)." )

# --- Repository ---
class FraudDetectionRepository:
    """Repository for interacting with fraud detection related data in the database."""
    def __init__(self, db_helper: DatabaseHelper):
        """Initializes the FraudDetectionRepository with a DatabaseHelper instance.

        Args:
            db_helper (DatabaseHelper): The database helper instance for database operations.
        """
        self.db_helper = db_helper

    async def create_fraud_check(self, check_data: Dict[str, Any]) -> UUID:
        """Creates a new fraud check entry in the database.

        Args:
            check_data (Dict[str, Any]): Dictionary containing fraud check data.

        Returns:
            UUID: The UUID of the newly created fraud check.
        """
        try:
            async with self.db_helper.get_session() as session:
                check_id = await self.db_helper.create(
                    session, "fraud_checks", {
                        "entity_type": check_data["entity_type"],
                        "entity_id": check_data["entity_id"],
                        "customer_id": check_data.get("customer_id"),
                        "risk_score": check_data["risk_score"],
                        "risk_level": check_data["risk_level"],
                        "triggered_rules": check_data.get("triggered_rules", []),
                        "signals": check_data.get("signals", {}),
                        "decision": check_data["decision"],
                        "created_at": datetime.utcnow()
                    }
                )
                logger.info("Fraud check created successfully", check_id=str(check_id), entity_id=check_data["entity_id"])
                return check_id
        except Exception as e:
            logger.error("Error creating fraud check", error=str(e), check_data=check_data)
            raise HTTPException(status_code=500, detail=f"Failed to create fraud check: {e}")

    async def get_fraud_check(self, check_id: UUID) -> Optional[Dict[str, Any]]:
        """Retrieves a fraud check by its ID.

        Args:
            check_id (UUID): The UUID of the fraud check.

        Returns:
            Optional[Dict[str, Any]]: The fraud check data if found, otherwise None.
        """
        try:
            async with self.db_helper.get_session() as session:
                result = await self.db_helper.get_by_id(session, "fraud_checks", check_id)
                if result:
                    logger.info("Fraud check retrieved successfully", check_id=str(check_id))
                else:
                    logger.warning("Fraud check not found", check_id=str(check_id))
                return result
        except Exception as e:
            logger.error("Error retrieving fraud check", error=str(e), check_id=check_id)
            raise HTTPException(status_code=500, detail=f"Failed to retrieve fraud check: {e}")

    async def is_entity_blocked(self, entity_type: str, entity_value: str) -> bool:
        """Checks if a given entity is currently blocked.

        Args:
            entity_type (str): The type of the entity (e.g., 'email', 'ip').
            entity_value (str): The value of the entity (e.g., 'bad@example.com').

        Returns:
            bool: True if the entity is blocked, False otherwise.
        """
        try:
            async with self.db_helper.get_session() as session:
                query = """
                    SELECT COUNT(*) as count FROM blocked_entities
                    WHERE entity_type = :entity_type AND entity_value = :entity_value AND is_active = true
                    AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """
                result = await session.execute(query, {"entity_type": entity_type, "entity_value": entity_value})
                count = result.scalar_one()
                logger.info("Checked if entity is blocked", entity_type=entity_type, entity_value=entity_value, is_blocked=(count > 0))
                return count > 0
        except Exception as e:
            logger.error("Error checking if entity is blocked", error=str(e), entity_type=entity_type, entity_value=entity_value)
            raise HTTPException(status_code=500, detail=f"Failed to check blocked entity: {e}")

    async def block_entity(self, block_data: BlockEntityRequest, blocked_by: str) -> UUID:
        """Blocks an entity from performing transactions.

        Args:
            block_data (BlockEntityRequest): Data for the entity to be blocked.
            blocked_by (str): Identifier of the agent or user who initiated the block.

        Returns:
            UUID: The UUID of the newly created block entry.
        """
        try:
            expires_at = None
            if block_data.duration_hours:
                expires_at = datetime.utcnow() + timedelta(hours=block_data.duration_hours)

            async with self.db_helper.get_session() as session:
                block_id = await self.db_helper.create(
                    session, "blocked_entities", {
                        "entity_type": block_data.entity_type,
                        "entity_value": block_data.entity_value,
                        "reason": block_data.reason,
                        "blocked_by": blocked_by,
                        "blocked_at": datetime.utcnow(),
                        "expires_at": expires_at,
                        "is_active": True
                    }
                )
                logger.info("Entity blocked successfully", block_id=str(block_id), entity_type=block_data.entity_type, entity_value=block_data.entity_value)
                return block_id
        except Exception as e:
            logger.error("Error blocking entity", error=str(e), block_data=block_data.dict(), blocked_by=blocked_by)
            raise HTTPException(status_code=500, detail=f"Failed to block entity: {e}")

    async def get_customer_fraud_history(self, customer_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves the fraud history for a given customer.

        Args:
            customer_id (str): The ID of the customer.
            limit (int): The maximum number of history entries to retrieve. Defaults to 10.

        Returns:
            List[Dict[str, Any]]: A list of fraud check records for the customer.
        """
        try:
            async with self.db_helper.get_session() as session:
                query = """
                    SELECT * FROM fraud_checks
                    WHERE customer_id = :customer_id
                    ORDER BY created_at DESC
                    LIMIT :limit
                """
                results = await session.execute(query, {"customer_id": customer_id, "limit": limit})
                history = [dict(r) for r in results.fetchall()]
                logger.info("Retrieved customer fraud history", customer_id=customer_id, count=len(history))
                return history
        except Exception as e:
            logger.error("Error retrieving customer fraud history", error=str(e), customer_id=customer_id)
            raise HTTPException(status_code=500, detail=f"Failed to retrieve customer fraud history: {e}")


# --- Service ---
class FraudDetectionService:
    """Service layer for fraud detection business logic."""
    def __init__(self, repo: FraudDetectionRepository):
        """Initializes the FraudDetectionService with a repository.

        Args:
            repo (FraudDetectionRepository): The repository for database operations.
        """
        self.repo = repo

    def calculate_risk_score(self, data: Dict[str, Any]) -> tuple[int, List[FraudSignal]]:
        """Calculate risk score based on various signals.

        Args:
            data (Dict[str, Any]): Input data for fraud analysis.

        Returns:
            tuple[int, List[FraudSignal]]: A tuple containing the calculated risk score and a list of triggered fraud signals.
        """
        risk_score = 0
        signals = []

        # Check amount anomaly (high value orders)
        if 'amount' in data:
            try:
                amount = float(data['amount'])
                if amount > 1000:
                    contribution = min(30, int((amount - 1000) / 100))
                    risk_score += contribution
                    signals.append(FraudSignal(
                        signal_type="high_amount",
                        signal_value=f"${amount:.2f}",
                        risk_contribution=contribution
                    ))
                    logger.info("Fraud signal detected: high_amount", amount=amount, contribution=contribution)
            except (ValueError, TypeError) as e:
                logger.warning("Invalid amount data for fraud check", amount=data['amount'], error=str(e))

        # Check velocity (multiple orders in short time)
        if 'order_count_24h' in data and isinstance(data['order_count_24h'], int):
            if data['order_count_24h'] > 5:
                contribution = min(25, data['order_count_24h'] * 3)
                risk_score += contribution
                signals.append(FraudSignal(
                    signal_type="high_velocity",
                    signal_value=f"{data['order_count_24h']} orders in 24h",
                    risk_contribution=contribution
                ))
                logger.info("Fraud signal detected: high_velocity", order_count_24h=data['order_count_24h'], contribution=contribution)

        # Check IP reputation
        if 'ip_reputation' in data and data['ip_reputation'] == 'bad':
            contribution = 40
            risk_score += contribution
            signals.append(FraudSignal(
                signal_type="bad_ip_reputation",
                signal_value=data.get('ip_address', 'unknown'),
                risk_contribution=contribution
            ))
            logger.info("Fraud signal detected: bad_ip_reputation", ip_address=data.get('ip_address', 'unknown'), contribution=contribution)

        # Check shipping/billing mismatch
        if 'address_mismatch' in data and data['address_mismatch']:
            contribution = 20
            risk_score += contribution
            signals.append(FraudSignal(
                signal_type="address_mismatch",
                signal_value="Shipping and billing addresses differ significantly",
                risk_contribution=contribution
            ))
            logger.info("Fraud signal detected: address_mismatch", contribution=contribution)

        # Check new account
        if 'account_age_days' in data and isinstance(data['account_age_days'], (int, float)):
            if data['account_age_days'] < 1:
                contribution = 15
                risk_score += contribution
                signals.append(FraudSignal(
                    signal_type="new_account",
                    signal_value=f"Account created {data['account_age_days']} days ago",
                    risk_contribution=contribution
                ))
                logger.info("Fraud signal detected: new_account", account_age_days=data['account_age_days'], contribution=contribution)

        # Check payment method changes
        if 'payment_method_changes_7d' in data and isinstance(data['payment_method_changes_7d'], int):
            if data['payment_method_changes_7d'] > 2:
                contribution = 15
                risk_score += contribution
                signals.append(FraudSignal(
                    signal_type="frequent_payment_changes",
                    signal_value=f"{data['payment_method_changes_7d']} changes in 7 days",
                    risk_contribution=contribution
                ))
                logger.info("Fraud signal detected: frequent_payment_changes", changes_7d=data['payment_method_changes_7d'], contribution=contribution)

        logger.info("Risk score calculated", final_risk_score=min(100, risk_score), num_signals=len(signals))
        return min(100, risk_score), signals

    def determine_risk_level(self, risk_score: int) -> RiskLevel:
        """Determine risk level based on score.

        Args:
            risk_score (int): The calculated risk score.

        Returns:
            RiskLevel: The corresponding risk level.
        """
        if risk_score >= 75:
            level = RiskLevel.CRITICAL
        elif risk_score >= 50:
            level = RiskLevel.HIGH
        elif risk_score >= 25:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW
        logger.info("Risk level determined", risk_score=risk_score, risk_level=level.value)
        return level

    def determine_decision(self, risk_level: RiskLevel) -> FraudDecision:
        """Determine action based on risk level.

        Args:
            risk_level (RiskLevel): The determined risk level.

        Returns:
            FraudDecision: The recommended fraud decision.
        """
        if risk_level == RiskLevel.CRITICAL:
            decision = FraudDecision.BLOCKED
        elif risk_level == RiskLevel.HIGH:
            decision = FraudDecision.MANUAL_REVIEW
        elif risk_level == RiskLevel.MEDIUM:
            decision = FraudDecision.FLAGGED
        else:
            decision = FraudDecision.APPROVED
        logger.info("Fraud decision determined", risk_level=risk_level.value, decision=decision.value)
        return decision

    def generate_recommendations(self, risk_level: RiskLevel, signals: List[FraudSignal]) -> List[str]:
        """Generate recommendations based on fraud analysis.

        Args:
            risk_level (RiskLevel): The determined risk level.
            signals (List[FraudSignal]): A list of triggered fraud signals.

        Returns:
            List[str]: A list of recommendations.
        """
        recommendations = []

        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("Contact customer to verify order details")
            recommendations.append("Request additional identity verification")

        for signal in signals:
            if signal.signal_type == "high_amount":
                recommendations.append(f"Review order with high amount: {signal.signal_value}")
            elif signal.signal_type == "high_velocity":
                recommendations.append(f"Investigate high order velocity: {signal.signal_value}")
            elif signal.signal_type == "bad_ip_reputation":
                recommendations.append(f"Block IP address: {signal.signal_value}")
            elif signal.signal_type == "address_mismatch":
                recommendations.append("Verify shipping and billing addresses")
            elif signal.signal_type == "new_account":
                recommendations.append("Monitor new account activity closely")
            elif signal.signal_type == "frequent_payment_changes":
                recommendations.append("Verify payment method changes")
        logger.info("Recommendations generated", risk_level=risk_level.value, num_recommendations=len(recommendations))
        return recommendations

    async def perform_fraud_check(self, request: FraudCheckRequest) -> FraudCheckResult:
        """Perform comprehensive fraud check.

        Args:
            request (FraudCheckRequest): The fraud check request data.

        Returns:
            FraudCheckResult: The result of the fraud check.
        """
        try:
            logger.info("Initiating fraud check", entity_type=request.entity_type, entity_id=request.entity_id)
            # Check if entity is already blocked
            if 'email' in request.data:
                if await self.repo.is_entity_blocked('email', request.data['email']):
                    logger.warning("Blocked entity detected", entity_type='email', entity_value=request.data['email'])
                    return FraudCheckResult(
                        check_id=uuid4(),
                        entity_type=request.entity_type,
                        entity_id=request.entity_id,
                        risk_score=100,
                        risk_level=RiskLevel.CRITICAL,
                        decision=FraudDecision.BLOCKED,
                        triggered_rules=[{"rule": "blocked_entity", "type": "email"}],
                        signals=[],
                        recommendations=["Entity is blocked"],
                        created_at=datetime.utcnow()
                    )

            # Calculate risk score
            risk_score, signals = self.calculate_risk_score(request.data)
            risk_level = self.determine_risk_level(risk_score)
            decision = self.determine_decision(risk_level)
            recommendations = self.generate_recommendations(risk_level, signals)

            # Save fraud check
            check_data = {
                'entity_type': request.entity_type,
                'entity_id': request.entity_id,
                'customer_id': request.customer_id,
                'risk_score': risk_score,
                'risk_level': risk_level.value,
                'decision': decision.value,
                'triggered_rules': [],  # Assuming rules are not directly stored here yet
                'signals': {s.signal_type: s.signal_value for s in signals},
                'created_at': datetime.utcnow()
            }
            check_id = await self.repo.create_fraud_check(check_data)

            logger.info("Fraud check completed", check_id=str(check_id), risk_score=risk_score,
                       decision=decision.value, entity_id=request.entity_id)

            return FraudCheckResult(
                check_id=check_id,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                risk_score=risk_score,
                risk_level=risk_level,
                decision=decision,
                triggered_rules=[],
                signals=signals,
                recommendations=recommendations,
                created_at=datetime.utcnow()
            )
        except Exception as e:
            logger.error("Error performing fraud check", error=str(e), request=request.dict())
            raise HTTPException(status_code=500, detail=f"Failed to perform fraud check: {e}")

    async def block_entity(self, request: BlockEntityRequest, blocked_by: str) -> UUID:
        """Blocks an entity and logs the action.

        Args:
            request (BlockEntityRequest): The request to block an entity.
            blocked_by (str): The identifier of the blocking agent/user.

        Returns:
            UUID: The ID of the created block entry.
        """
        try:
            logger.info("Initiating entity block", entity_type=request.entity_type, entity_value=request.entity_value, blocked_by=blocked_by)
            block_id = await self.repo.block_entity(request, blocked_by)
            logger.info("Entity blocked successfully", block_id=str(block_id), entity_type=request.entity_type, entity_value=request.entity_value)
            return block_id
        except Exception as e:
            logger.error("Error in blocking entity service", error=str(e), request=request.dict())
            raise HTTPException(status_code=500, detail=f"Failed to block entity: {e}")


# --- Agent ---
class FraudDetectionAgent(BaseAgentV2):
    """Fraud Detection Agent for the Multi-Agent E-Commerce System.

    This agent provides ML-based fraud detection, risk scoring, and anomaly detection
    for transactions, orders, and user behavior.
    """
    def __init__(self):
        """Initializes the FraudDetectionAgent."""
        super().__init__(agent_id="fraud_detection_agent")
        # Initialize database manager with fallback
        try:
            self.db_manager = get_database_manager()
        except RuntimeError:
            from shared.models import DatabaseConfig
            db_config = DatabaseConfig()
            self.db_manager = DatabaseManager(db_config)
        self.db_helper = DatabaseHelper(self.db_manager)
        self.repository = FraudDetectionRepository(self.db_helper)
        self.service = FraudDetectionService(self.repository)
        self.app = FastAPI(title="FraudDetectionAgent",
                           description="Agent for detecting and managing fraudulent activities.",
                           on_startup=[self.on_startup],
                           on_shutdown=[self.on_shutdown])
        self._db_initialized = False

        self.setup_routes()

    async def initialize(self):
        """Initializes the agent, ensuring database connection and tables are ready."""
        await super().initialize()
        try:
            await self.db_manager.initialize_async()
            # In a real scenario, you'd run migrations or check tables here.
            # For this example, we assume tables exist.
            logger.info("Database connected and initialized.")
            self._db_initialized = True
        except Exception as e:
            logger.error("Failed to connect to database", error=str(e))
            self._db_initialized = False

    async def on_startup(self):
        """Handles agent startup tasks, such as initializing the database connection."""
        logger.info("Fraud Detection Agent starting up...")
        await self.initialize()

    async def on_shutdown(self):
        """Handles agent shutdown tasks, such as disconnecting from the database."""
        logger.info("Fraud Detection Agent shutting down...")
        await self.db_manager.close()

    def setup_routes(self):
        """Sets up FastAPI routes for the agent.

        Includes health check, root endpoint, and business logic endpoints.
        """
        @self.app.get("/health", summary="Health Check", tags=["Monitoring"])
        async def health_check():
            """Endpoint to check the health of the agent and its database connection."""
            logger.info("Health check requested")
            if not self._db_initialized:
                logger.error("Health check failed: Database not initialized")
                raise HTTPException(status_code=503, detail="Database not initialized")
            return {"status": "healthy", "db_connected": self._db_initialized}

        @self.app.get("/", summary="Root endpoint", tags=["General"])
        async def root():
            """Root endpoint providing a simple status message."""
            logger.info("Root endpoint accessed")
            return {"message": "Fraud Detection Agent is running"}

        @self.app.post("/check_fraud", response_model=FraudCheckResult, summary="Perform a fraud check", tags=["Fraud Detection"])
        async def check_fraud_endpoint(request: FraudCheckRequest):
            """Endpoint to perform a comprehensive fraud check on an entity."""
            logger.info("Fraud check endpoint called", entity_type=request.entity_type, entity_id=request.entity_id)
            if not self._db_initialized:
                logger.error("Fraud check failed: Database not initialized")
                raise HTTPException(status_code=503, detail="Database not initialized")
            return await self.service.perform_fraud_check(request)

        @self.app.post("/block_entity", summary="Block an entity", tags=["Fraud Management"])
        async def block_entity_endpoint(request: BlockEntityRequest, blocked_by: str = Body(..., embed=True)):
            """Endpoint to block an entity from performing transactions."""
            logger.info("Block entity endpoint called", entity_type=request.entity_type, entity_value=request.entity_value)
            if not self._db_initialized:
                logger.error("Block entity failed: Database not initialized")
                raise HTTPException(status_code=503, detail="Database not initialized")
            return await self.service.block_entity(request, blocked_by)

        @self.app.get("/customer_fraud_history/{customer_id}", response_model=List[Dict[str, Any]], summary="Get customer fraud history", tags=["Fraud Detection"])
        async def get_customer_history_endpoint(customer_id: str = Path(..., description="The ID of the customer"), limit: int = 10):
            """Endpoint to retrieve the fraud history for a specific customer."""
            logger.info("Customer fraud history endpoint called", customer_id=customer_id, limit=limit)
            if not self._db_initialized:
                logger.error("Get customer fraud history failed: Database not initialized")
                raise HTTPException(status_code=503, detail="Database not initialized")
            return await self.repository.get_customer_fraud_history(customer_id, limit)

    async def process_message(self, message: AgentMessage):
        """Processes incoming messages for the agent from the Kafka bus.

        Args:
            message (AgentMessage): The incoming message to process.
        """
        logger.info("Received message", message_type=message.message_type, sender=message.sender)

        try:
            if not self._db_initialized:
                logger.warning("Database not initialized, cannot process message.")
                await self.send_message(
                    recipient_agent_id=message.sender,
                    message_type=MessageType.ERROR,
                    body={"error": "Database not initialized", "original_message": message.dict()}
                )
                return

            if message.message_type == MessageType.FRAUD_CHECK_REQUEST:
                fraud_request = FraudCheckRequest(**message.body)
                result = await self.service.perform_fraud_check(fraud_request)
                await self.send_message(
                    recipient_agent_id=message.sender,
                    message_type=MessageType.FRAUD_CHECK_RESPONSE,
                    body=result.dict()
                )
                logger.info("Processed FRAUD_CHECK_REQUEST and sent response", check_id=str(result.check_id))
            elif message.message_type == MessageType.BLOCK_ENTITY_REQUEST:
                block_request = BlockEntityRequest(**message.body)
                blocked_by = message.sender  # Assuming the sender is the one initiating the block
                block_id = await self.service.block_entity(block_request, blocked_by)
                await self.send_message(
                    recipient_agent_id=message.sender,
                    message_type=MessageType.BLOCK_ENTITY_RESPONSE,
                    body={"block_id": str(block_id), "status": "success"}
                )
                logger.info("Processed BLOCK_ENTITY_REQUEST and sent response", block_id=str(block_id))
            else:
                logger.warning("Unknown message type received", message_type=message.message_type)
                await self.send_message(
                    recipient_agent_id=message.sender,
                    message_type=MessageType.ERROR,
                    body={"error": f"Unknown message type: {message.message_type}", "original_message": message.dict()}
                )
        except Exception as e:
            logger.error("Error processing message", error=str(e), message=message.dict())
            await self.send_message(
                recipient_agent_id=message.sender,
                message_type=MessageType.ERROR,
                body={"error": str(e), "original_message": message.dict()}
            )

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
        """Process agent-specific business logic
        
        Args:
            data: Dictionary containing operation type and parameters
            
        Returns:
            Dictionary with processing results
        """
        try:
            operation = data.get("operation", "process")
            return {"status": "success", "operation": operation, "data": data}
        except Exception as e:
            logger.error(f"Error in process_business_logic: {e}")
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    """Main entry point for running the Fraud Detection Agent.

    Initializes and runs the agent's FastAPI server using uvicorn.
    Configuration is loaded from environment variables.
    """
    agent_id = os.getenv("AGENT_ID", "fraud_detection_agent_001")
    agent_type = os.getenv("AGENT_TYPE", "fraud_detection")

    # Initialize DatabaseManager with DATABASE_URL from environment variables
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.critical("DATABASE_URL environment variable not set. Exiting.")
        sys.exit(1)

    db_manager = DatabaseManager(database_url)

    # Create the agent instance and assign the database manager
    agent = FraudDetectionAgent(agent_id=agent_id, agent_type=agent_type)
    agent.db_manager = db_manager
    agent.db_helper = DatabaseHelper(db_manager)
    agent.repository = FraudDetectionRepository(agent.db_helper)
    agent.service = FraudDetectionService(agent.repository)

    # Get port from environment variables
    port = int(os.getenv("PORT", "8000"))

    logger.info("Starting Fraud Detection Agent FastAPI server", port=port, agent_id=agent_id)

    # Run the FastAPI server
    uvicorn.run(agent.app, host="0.0.0.0", port=port, log_level="info")

