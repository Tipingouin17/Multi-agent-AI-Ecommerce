
"""
Infrastructure Agents - Multi-Agent E-Commerce System

This module defines several infrastructure agents (Data Sync, API Gateway, Monitoring, Backup, and Admin)
for an e-commerce system. Each agent is designed to run independently, handle specific tasks,
communicate via Kafka, expose FastAPI endpoints, and interact with a database.
"""

import asyncio
import os
import sys
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Body
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

# Adjust the path to import shared modules
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.database import DatabaseManager, get_database_manager
from shared.db_helpers import DatabaseHelper
from shared.base_agent import BaseAgent, AgentMessage, MessageType

logger = structlog.get_logger(__name__)

# ==================== DATA SYNC AGENT ====================

class SyncStatus(str, Enum):
    """Enumeration for the status of a data synchronization operation."""
    PENDING = "pending"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"

class SyncRequest(BaseModel):
    """Pydantic model for a data synchronization request."""
    source_agent: str = Field(..., description="The ID of the agent initiating the sync.")
    target_agent: str = Field(..., description="The ID of the agent to synchronize data with.")
    data_type: str = Field(..., description="The type of data to synchronize (e.g., 'products', 'orders').")
    entity_ids: List[str] = Field(..., description="A list of entity IDs to synchronize.")

class DataSyncAgent(BaseAgent):
    """Agent responsible for synchronizing data between different agents or services.

    Inherits from BaseAgent, providing core functionalities like Kafka communication and agent lifecycle management.
    Exposes FastAPI endpoints for external interaction and uses DatabaseHelper for persistence.
    """

    def __init__(self, agent_id: str, db_manager: DatabaseManager, kafka_bootstrap_servers: str = "localhost:9092"):
        """Initializes the DataSyncAgent.

        Args:
            agent_id (str): A unique identifier for this agent instance.
            db_manager (DatabaseManager): An instance of the DatabaseManager for database access.
            kafka_bootstrap_servers (str): Kafka bootstrap servers for producer/consumer.
        """
        super().__init__(agent_id, "data_sync", kafka_bootstrap_servers)
        self.db_manager = db_manager
        self.db_helper = DatabaseHelper(db_manager)
        self._db_initialized = False # Placeholder for actual DB initialization check

        self.app = FastAPI(title="Data Sync Agent API", version="1.0.0")
        self.app.add_api_route("/health", self.health_check, methods=["GET"], summary="Health check for Data Sync Agent")
        self.app.add_api_route("/", self.root, methods=["GET"], summary="Root endpoint for Data Sync Agent")
        self.app.add_api_route("/api/v1/sync/execute", self.execute_sync_endpoint, methods=["POST"], summary="Execute data synchronization")

    async def root(self):
        """Root endpoint for the Data Sync Agent. Returns a welcome message."""
        return {"message": "Data Sync Agent is running!"}

    async def health_check(self):
        """Health check endpoint for the Data Sync Agent. Returns agent status."""
        return {"status": "healthy", "agent": "data_sync_agent", "version": "1.0.0"}

    async def execute_sync_endpoint(self, sync_request: SyncRequest = Body(...)):
        """FastAPI endpoint to trigger data synchronization.

        Args:
            sync_request (SyncRequest): The request body containing synchronization details.

        Returns:
            Dict: A dictionary with the sync_id and status.

        Raises:
            HTTPException: If the database is not initialized or an error occurs during sync.
        """
        if not self._db_initialized: 
            logger.warning("Database not initialized for DataSyncAgent. Cannot execute sync.")
            raise HTTPException(status_code=500, detail="Database not initialized")
        try:
            sync_id = await self.sync_data(sync_request)
            return {"sync_id": sync_id, "status": "started"}
        except Exception as e:
            logger.error("sync_failed", error=str(e), sync_request=sync_request.dict())
            raise HTTPException(status_code=500, detail=f"Failed to execute sync: {e}")

    async def sync_data(self, sync_request: SyncRequest) -> UUID:
        """Synchronizes data between agents and records the operation in the database.

        This method simulates a data synchronization process and logs its initiation.
        In a real implementation, this would involve complex data transfer logic.

        Args:
            sync_request (SyncRequest): The request containing details for data synchronization.

        Returns:
            UUID: The ID of the synchronization operation.
        """
        sync_id = uuid4()
        logger.info("data_sync_started", sync_id=str(sync_id),
                   source=sync_request.source_agent, target=sync_request.target_agent,
                   data_type=sync_request.data_type, entity_ids=sync_request.entity_ids)
        
        # Placeholder for actual database operation using self.db_helper
        # Example: await self.db_helper.create("SyncLog", {"sync_id": str(sync_id), "status": SyncStatus.PENDING.value, ...})
        async with self.db_manager.get_session() as session:
            # Simulate saving a sync log entry
            logger.info("Simulating database write for sync log.", session_type=type(session))
            # await self.db_helper.create(session, "SyncLog", {"sync_id": str(sync_id), "status": SyncStatus.PENDING.value})
        
        return sync_id

    async def process_message(self, message: AgentMessage):
        """Processes incoming Kafka messages for the Data Sync Agent.

        Handles COMMAND messages of type 'sync_request' to initiate data synchronization.
        Sends INFO or ERROR messages back to the sender based on the outcome.

        Args:
            message (AgentMessage): The message received from Kafka.
        """
        logger.info(f"DataSyncAgent received message: {message.message_type} from {message.sender_id}",
                    message_id=str(message.message_id), payload=message.payload)
        if message.message_type == MessageType.COMMAND and message.payload.get("command") == "sync_request":
            try:
                sync_request = SyncRequest(**message.payload.get("data", {}))
                sync_id = await self.sync_data(sync_request)
                await self.send_message(AgentMessage(
                    agent_id=self.agent_id,
                    sender_id=self.agent_id,
                    recipient_id=message.sender_id,
                    message_type=MessageType.INFO,
                    payload={"status": "sync_completed", "sync_id": str(sync_id), "source_message_id": str(message.message_id)}
                ))
            except Exception as e:
                logger.error("process_message_sync_failed", error=str(e), message_payload=message.payload)
                await self.send_message(AgentMessage(
                    agent_id=self.agent_id,
                    sender_id=self.agent_id,
                    recipient_id=message.sender_id,
                    message_type=MessageType.ERROR,
                    payload={"error": str(e), "original_message": message.payload}
                ))
        else:
            logger.warning("Unhandled message type or command", message_type=message.message_type, command=message.payload.get("command"))

    async def start_fastapi_app(self):
        """Starts the FastAPI application for the Data Sync Agent.

        The port is configured via the DATA_SYNC_AGENT_PORT environment variable, defaulting to 8022.
        """
        port = int(os.getenv("DATA_SYNC_AGENT_PORT", "8022"))
        config = uvicorn.Config(self.app, host="0.0.0.0", port=port)
        server = uvicorn.Server(config)
        logger.info(f"Data Sync Agent FastAPI app starting on port {port}")
        await server.serve()

# ==================== API GATEWAY AGENT ====================

class GatewayRequest(BaseModel):
    """Pydantic model for an API Gateway routing request."""
    target_agent: str = Field(..., description="The ID of the agent to route the request to.")
    endpoint: str = Field(..., description="The specific API endpoint on the target agent.")
    method: str = Field("GET", description="The HTTP method for the request (e.g., GET, POST).")
    payload: Optional[Dict] = Field(None, description="Optional JSON payload for POST/PUT requests.")

class APIGatewayAgent(BaseAgent):
    """Agent responsible for routing API requests to appropriate target agents.

    Inherits from BaseAgent, providing core functionalities like Kafka communication and agent lifecycle management.
    Exposes FastAPI endpoints to receive and route external API calls.
    """

    def __init__(self, agent_id: str, db_manager: DatabaseManager, kafka_bootstrap_servers: str = "localhost:9092"):
        """Initializes the APIGatewayAgent.

        Args:
            agent_id (str): A unique identifier for this agent instance.
            db_manager (DatabaseManager): An instance of the DatabaseManager for database access.
            kafka_bootstrap_servers (str): Kafka bootstrap servers for producer/consumer.
        """
        super().__init__(agent_id, "api_gateway", kafka_bootstrap_servers)
        self.db_manager = db_manager
        self.db_helper = DatabaseHelper(db_manager)
        self._db_initialized = False

        self.app = FastAPI(title="API Gateway Agent API", version="1.0.0")
        self.app.add_api_route("/health", self.health_check, methods=["GET"], summary="Health check for API Gateway Agent")
        self.app.add_api_route("/", self.root, methods=["GET"], summary="Root endpoint for API Gateway Agent")
        self.app.add_api_route("/api/v1/gateway/route", self.route_request_endpoint, methods=["POST"], summary="Route an API request to a target agent")

    async def root(self):
        """Root endpoint for the API Gateway Agent. Returns a welcome message."""
        return {"message": "API Gateway Agent is running!"}

    async def health_check(self):
        """Health check endpoint for the API Gateway Agent. Returns agent status."""
        return {"status": "healthy", "agent": "api_gateway_agent", "version": "1.0.0"}

    async def route_request_endpoint(self, gateway_request: GatewayRequest = Body(...)):
        """FastAPI endpoint to route requests to target agents.

        Args:
            gateway_request (GatewayRequest): The request body containing routing details.

        Returns:
            Dict: Result of the routing operation.

        Raises:
            HTTPException: If the database is not initialized or an error occurs during routing.
        """
        if not self._db_initialized:
            logger.warning("Database not initialized for APIGatewayAgent. Cannot route request.")
            raise HTTPException(status_code=500, detail="Database not initialized")
        try:
            result = await self.route_request(gateway_request)
            return result
        except Exception as e:
            logger.error("routing_failed", error=str(e), gateway_request=gateway_request.dict())
            raise HTTPException(status_code=500, detail=f"Failed to route request: {e}")

    async def route_request(self, gateway_request: GatewayRequest) -> Dict:
        """Routes a request to a target agent and logs the operation.

        This method simulates the routing logic. In a real system, this would involve
        forwarding the request to the appropriate agent's API.

        Args:
            gateway_request (GatewayRequest): The request to be routed.

        Returns:
            Dict: A dictionary indicating the status and target of the routed request.
        """
        logger.info("request_routed", target=gateway_request.target_agent,
                   endpoint=gateway_request.endpoint, method=gateway_request.method,
                   payload=gateway_request.payload)
        # Placeholder for actual routing logic and database operation
        async with self.db_manager.get_session() as session:
            logger.info("Simulating database write for routing log.", session_type=type(session))
            # await self.db_helper.create(session, "RoutingLog", {"target": gateway_request.target_agent, ...})
        return {"status": "routed", "target": gateway_request.target_agent, "endpoint": gateway_request.endpoint}

    async def process_message(self, message: AgentMessage):
        """Processes incoming Kafka messages for the API Gateway Agent.

        Handles COMMAND messages of type 'route_request' to route API calls.
        Sends INFO or ERROR messages back to the sender based on the outcome.

        Args:
            message (AgentMessage): The message received from Kafka.
        """
        logger.info(f"APIGatewayAgent received message: {message.message_type} from {message.sender_id}",
                    message_id=str(message.message_id), payload=message.payload)
        if message.message_type == MessageType.COMMAND and message.payload.get("command") == "route_request":
            try:
                gateway_request = GatewayRequest(**message.payload.get("data", {}))
                result = await self.route_request(gateway_request)
                await self.send_message(AgentMessage(
                    agent_id=self.agent_id,
                    sender_id=self.agent_id,
                    recipient_id=message.sender_id,
                    message_type=MessageType.INFO,
                    payload={"status": "request_routed", "result": result, "source_message_id": str(message.message_id)}
                ))
            except Exception as e:
                logger.error("process_message_route_failed", error=str(e), message_payload=message.payload)
                await self.send_message(AgentMessage(
                    agent_id=self.agent_id,
                    sender_id=self.agent_id,
                    recipient_id=message.sender_id,
                    message_type=MessageType.ERROR,
                    payload={"error": str(e), "original_message": message.payload}
                ))
        else:
            logger.warning("Unhandled message type or command", message_type=message.message_type, command=message.payload.get("command"))

    async def start_fastapi_app(self):
        """Starts the FastAPI application for the API Gateway Agent.

        The port is configured via the API_GATEWAY_AGENT_PORT environment variable, defaulting to 8023.
        """
        port = int(os.getenv("API_GATEWAY_AGENT_PORT", "8023"))
        config = uvicorn.Config(self.app, host="0.0.0.0", port=port)
        server = uvicorn.Server(config)
        logger.info(f"API Gateway Agent FastAPI app starting on port {port}")
        await server.serve()

# ==================== MONITORING AGENT ====================

class MetricType(str, Enum):
    """Enumeration for different types of system metrics."""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"

class MetricData(BaseModel):
    """Pydantic model for system metric data."""
    agent_name: str = Field(..., description="The name of the agent reporting the metric.")
    metric_type: MetricType = Field(..., description="The type of metric.")
    value: float = Field(..., description="The value of the metric.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the metric was recorded.")

class MonitoringAgent(BaseAgent):
    """Agent responsible for collecting, storing, and providing system metrics and health information.

    Inherits from BaseAgent, providing core functionalities like Kafka communication and agent lifecycle management.
    Exposes FastAPI endpoints for recording metrics and querying system health.
    """

    def __init__(self, agent_id: str, db_manager: DatabaseManager, kafka_bootstrap_servers: str = "localhost:9092"):
        """Initializes the MonitoringAgent.

        Args:
            agent_id (str): A unique identifier for this agent instance.
            db_manager (DatabaseManager): An instance of the DatabaseManager for database access.
            kafka_bootstrap_servers (str): Kafka bootstrap servers for producer/consumer.
        """
        super().__init__(agent_id, "monitoring", kafka_bootstrap_servers)
        self.db_manager = db_manager
        self.db_helper = DatabaseHelper(db_manager)
        self._db_initialized = False

        self.app = FastAPI(title="Monitoring Agent API", version="1.0.0")
        self.app.add_api_route("/health", self.health_check, methods=["GET"], summary="Health check for Monitoring Agent")
        self.app.add_api_route("/", self.root, methods=["GET"], summary="Root endpoint for Monitoring Agent")
        self.app.add_api_route("/api/v1/monitoring/metrics", self.record_metric_endpoint, methods=["POST"], summary="Record a system metric")
        self.app.add_api_route("/api/v1/monitoring/health", self.get_system_health_endpoint, methods=["GET"], summary="Get overall system health")

    async def root(self):
        """Root endpoint for the Monitoring Agent. Returns a welcome message."""
        return {"message": "Monitoring Agent is running!"}

    async def health_check(self):
        """Health check endpoint for the Monitoring Agent. Returns agent status."""
        return {"status": "healthy", "agent": "monitoring_agent", "version": "1.0.0"}

    async def record_metric_endpoint(self, metric_data: MetricData = Body(...)):
        """FastAPI endpoint to record system metrics.

        Args:
            metric_data (MetricData): The metric data to record.

        Returns:
            Dict: A dictionary with the metric_id and status.

        Raises:
            HTTPException: If the database is not initialized or an error occurs during metric recording.
        """
        if not self._db_initialized:
            logger.warning("Database not initialized for MonitoringAgent. Cannot record metric.")
            raise HTTPException(status_code=500, detail="Database not initialized")
        try:
            metric_id = await self.record_metric(metric_data)
            return {"metric_id": metric_id, "status": "recorded"}
        except Exception as e:
            logger.error("record_metric_failed", error=str(e), metric_data=metric_data.dict())
            raise HTTPException(status_code=500, detail=f"Failed to record metric: {e}")

    async def get_system_health_endpoint(self):
        """FastAPI endpoint to get overall system health.

        Returns:
            Dict: A dictionary containing system health information.

        Raises:
            HTTPException: If the database is not initialized or an error occurs during health retrieval.
        """
        if not self._db_initialized:
            logger.warning("Database not initialized for MonitoringAgent. Cannot get system health.")
            raise HTTPException(status_code=500, detail="Database not initialized")
        try:
            health = await self.get_system_health()
            return health
        except Exception as e:
            logger.error("get_health_failed", error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to get system health: {e}")

    async def record_metric(self, metric_data: MetricData) -> UUID:
        """Records system metric and stores it in the database.

        Args:
            metric_data (MetricData): The metric data to record.

        Returns:
            UUID: The ID of the recorded metric.
        """
        metric_id = uuid4()
        logger.info("metric_recorded", metric_id=str(metric_id),
                   agent=metric_data.agent_name, type=metric_data.metric_type.value,
                   value=metric_data.value, timestamp=metric_data.timestamp.isoformat())
        # Placeholder for actual database operation using self.db_helper
        async with self.db_manager.get_session() as session:
            logger.info("Simulating database write for metric record.", session_type=type(session))
            # await self.db_helper.create(session, "Metric", metric_data.dict())
        return metric_id

    async def get_system_health(self) -> Dict:
        """Retrieves overall system health metrics from the database.

        Returns:
            Dict: A dictionary containing system health information.
        """
        # Placeholder for actual database retrieval using self.db_helper
        async with self.db_manager.get_session() as session:
            logger.info("Simulating database read for system health.", session_type=type(session))
            # metrics = await self.db_helper.get_all(session, "Metric", limit=100) # Example
        return {
            "status": "healthy",
            "agents_online": 26,
            "cpu_usage": 45.2,
            "memory_usage": 62.8,
            "uptime_hours": 168
        }

    async def process_message(self, message: AgentMessage):
        """Processes incoming Kafka messages for the Monitoring Agent.

        Handles EVENT messages of type 'metric_update' to record new metrics.
        Sends INFO or ERROR messages back to the sender based on the outcome.

        Args:
            message (AgentMessage): The message received from Kafka.
        """
        logger.info(f"MonitoringAgent received message: {message.message_type} from {message.sender_id}",
                    message_id=str(message.message_id), payload=message.payload)
        if message.message_type == MessageType.EVENT and message.payload.get("event") == "metric_update":
            try:
                metric_data = MetricData(**message.payload.get("data", {}))
                metric_id = await self.record_metric(metric_data)
                await self.send_message(AgentMessage(
                    agent_id=self.agent_id,
                    sender_id=self.agent_id,
                    recipient_id=message.sender_id,
                    message_type=MessageType.INFO,
                    payload={"status": "metric_recorded", "metric_id": str(metric_id), "source_message_id": str(message.message_id)}
                ))
            except Exception as e:
                logger.error("process_message_metric_failed", error=str(e), message_payload=message.payload)
                await self.send_message(AgentMessage(
                    agent_id=self.agent_id,
                    sender_id=self.agent_id,
                    recipient_id=message.sender_id,
                    message_type=MessageType.ERROR,
                    payload={"error": str(e), "original_message": message.payload}
                ))
        else:
            logger.warning("Unhandled message type or command", message_type=message.message_type, command=message.payload.get("command"))

    async def start_fastapi_app(self):
        """Starts the FastAPI application for the Monitoring Agent.

        The port is configured via the MONITORING_AGENT_PORT environment variable, defaulting to 8024.
        """
        port = int(os.getenv("MONITORING_AGENT_PORT", "8024"))
        config = uvicorn.Config(self.app, host="0.0.0.0", port=port)
        server = uvicorn.Server(config)
        logger.info(f"Monitoring Agent FastAPI app starting on port {port}")
        await server.serve()

# ==================== BACKUP AGENT ====================

class BackupType(str, Enum):
    """Enumeration for different types of backups."""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"

class BackupRequest(BaseModel):
    """Pydantic model for a backup request."""
    backup_type: BackupType = Field(..., description="The type of backup to perform.")
    agents: List[str] = Field(..., description="A list of agent IDs to include in the backup.")
    retention_days: int = Field(30, description="Number of days to retain the backup.")

class BackupAgent(BaseAgent):
    """Agent responsible for creating and restoring system backups.

    Inherits from BaseAgent, providing core functionalities like Kafka communication and agent lifecycle management.
    Exposes FastAPI endpoints for initiating backups and restores.
    """

    def __init__(self, agent_id: str, db_manager: DatabaseManager, kafka_bootstrap_servers: str = "localhost:9092"):
        """Initializes the BackupAgent.

        Args:
            agent_id (str): A unique identifier for this agent instance.
            db_manager (DatabaseManager): An instance of the DatabaseManager for database access.
            kafka_bootstrap_servers (str): Kafka bootstrap servers for producer/consumer.
        """
        super().__init__(agent_id, "backup", kafka_bootstrap_servers)
        self.db_manager = db_manager
        self.db_helper = DatabaseHelper(db_manager)
        self._db_initialized = False

        self.app = FastAPI(title="Backup Agent API", version="1.0.0")
        self.app.add_api_route("/health", self.health_check, methods=["GET"], summary="Health check for Backup Agent")
        self.app.add_api_route("/", self.root, methods=["GET"], summary="Root endpoint for Backup Agent")
        self.app.add_api_route("/api/v1/backup/create", self.create_backup_endpoint, methods=["POST"], summary="Create a system backup")
        self.app.add_api_route("/api/v1/backup/{backup_id}/restore", self.restore_backup_endpoint, methods=["POST"], summary="Restore from a system backup")

    async def root(self):
        """Root endpoint for the Backup Agent. Returns a welcome message."""
        return {"message": "Backup Agent is running!"}

    async def health_check(self):
        """Health check endpoint for the Backup Agent. Returns agent status."""
        return {"status": "healthy", "agent": "backup_agent", "version": "1.0.0"}

    async def create_backup_endpoint(self, backup_request: BackupRequest = Body(...)):
        """FastAPI endpoint to create a system backup.

        Args:
            backup_request (BackupRequest): The request body containing backup details.

        Returns:
            Dict: A dictionary with the backup_id and status.

        Raises:
            HTTPException: If the database is not initialized or an error occurs during backup creation.
        """
        if not self._db_initialized:
            logger.warning("Database not initialized for BackupAgent. Cannot create backup.")
            raise HTTPException(status_code=500, detail="Database not initialized")
        try:
            backup_id = await self.create_backup(backup_request)
            return {"backup_id": backup_id, "status": "created"}
        except Exception as e:
            logger.error("create_backup_failed", error=str(e), backup_request=backup_request.dict())
            raise HTTPException(status_code=500, detail=f"Failed to create backup: {e}")

    async def restore_backup_endpoint(self, backup_id: UUID):
        """FastAPI endpoint to restore from a system backup.

        Args:
            backup_id (UUID): The ID of the backup to restore.

        Returns:
            Dict: A dictionary with the backup_id and restoration status.

        Raises:
            HTTPException: If the database is not initialized or an error occurs during restore.
        """
        if not self._db_initialized:
            logger.warning("Database not initialized for BackupAgent. Cannot restore backup.")
            raise HTTPException(status_code=500, detail="Database not initialized")
        try:
            success = await self.restore_backup(backup_id)
            return {"backup_id": backup_id, "status": "restored" if success else "failed"}
        except Exception as e:
            logger.error("restore_backup_failed", error=str(e), backup_id=str(backup_id))
            raise HTTPException(status_code=500, detail=f"Failed to restore backup: {e}")

    async def create_backup(self, backup_request: BackupRequest) -> UUID:
        """Creates a system backup and records the operation in the database.

        This method simulates a backup process. In a real system, this would involve
        archiving data and storing it in a secure location.

        Args:
            backup_request (BackupRequest): The request containing details for the backup.

        Returns:
            UUID: The ID of the created backup.
        """
        backup_id = uuid4()
        logger.info("backup_created", backup_id=str(backup_id),
                   type=backup_request.backup_type.value, agents=len(backup_request.agents),
                   retention_days=backup_request.retention_days)
        # Placeholder for actual database operation using self.db_helper
        async with self.db_manager.get_session() as session:
            logger.info("Simulating database write for backup creation.", session_type=type(session))
            # await self.db_helper.create(session, "BackupLog", {"backup_id": str(backup_id), "type": backup_request.backup_type.value})
        return backup_id

    async def restore_backup(self, backup_id: UUID) -> bool:
        """Restores from a backup and records the operation in the database.

        This method simulates a restore process. In a real system, this would involve
        retrieving and deploying archived data.

        Args:
            backup_id (UUID): The ID of the backup to restore.

        Returns:
            bool: True if restore was successful, False otherwise.
        """
        logger.info("backup_restored", backup_id=str(backup_id))
        # Placeholder for actual database operation using self.db_helper
        async with self.db_manager.get_session() as session:
            logger.info("Simulating database write for backup restoration.", session_type=type(session))
            # await self.db_helper.update(session, "BackupLog", str(backup_id), {"status": "restored"})
        return True

    async def process_message(self, message: AgentMessage):
        """Processes incoming Kafka messages for the Backup Agent.

        Handles COMMAND messages for 'create_backup' and 'restore_backup'.
        Sends INFO or ERROR messages back to the sender based on the outcome.

        Args:
            message (AgentMessage): The message received from Kafka.
        """
        logger.info(f"BackupAgent received message: {message.message_type} from {message.sender_id}",
                    message_id=str(message.message_id), payload=message.payload)
        if message.message_type == MessageType.COMMAND:
            command = message.payload.get("command")
            try:
                if command == "create_backup":
                    backup_request = BackupRequest(**message.payload.get("data", {}))
                    backup_id = await self.create_backup(backup_request)
                    await self.send_message(AgentMessage(
                        agent_id=self.agent_id,
                        sender_id=self.agent_id,
                        recipient_id=message.sender_id,
                        message_type=MessageType.INFO,
                        payload={"status": "backup_created", "backup_id": str(backup_id), "source_message_id": str(message.message_id)}
                    ))
                elif command == "restore_backup":
                    backup_id = UUID(message.payload.get("data", {}).get("backup_id"))
                    success = await self.restore_backup(backup_id)
                    await self.send_message(AgentMessage(
                        agent_id=self.agent_id,
                        sender_id=self.agent_id,
                        recipient_id=message.sender_id,
                        message_type=MessageType.INFO,
                        payload={"status": "backup_restored" if success else "backup_restore_failed", "backup_id": str(backup_id), "source_message_id": str(message.message_id)}
                    ))
                else:
                    logger.warning("Unknown command received for BackupAgent", command=command, message_payload=message.payload)
            except Exception as e:
                logger.error("process_message_backup_failed", error=str(e), message_payload=message.payload)
                await self.send_message(AgentMessage(
                    agent_id=self.agent_id,
                    sender_id=self.agent_id,
                    recipient_id=message.sender_id,
                    message_type=MessageType.ERROR,
                    payload={"error": str(e), "original_message": message.payload}
                ))
        else:
            logger.warning("Unhandled message type for BackupAgent", message_type=message.message_type, command=message.payload.get("command"))

    async def start_fastapi_app(self):
        """Starts the FastAPI application for the Backup Agent.

        The port is configured via the BACKUP_AGENT_PORT environment variable, defaulting to 8025.
        """
        port = int(os.getenv("BACKUP_AGENT_PORT", "8025"))
        config = uvicorn.Config(self.app, host="0.0.0.0", port=port)
        server = uvicorn.Server(config)
        logger.info(f"Backup Agent FastAPI app starting on port {port}")
        await server.serve()

# ==================== ADMIN AGENT ====================

class UserRole(str, Enum):
    """Enumeration for different user roles in the system."""
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"
    VIEWER = "viewer"

class UserCreate(BaseModel):
    """Pydantic model for creating a new user."""
    username: str = Field(..., description="The username for the new user.")
    email: str = Field(..., description="The email address for the new user.")
    role: UserRole = Field(..., description="The role assigned to the new user.")

class AdminAgent(BaseAgent):
    """Agent responsible for administrative tasks such as user management and system statistics retrieval.

    Inherits from BaseAgent, providing core functionalities like Kafka communication and agent lifecycle management.
    Exposes FastAPI endpoints for user management and system statistics.
    """

    def __init__(self, agent_id: str, db_manager: DatabaseManager, kafka_bootstrap_servers: str = "localhost:9092"):
        """Initializes the AdminAgent.

        Args:
            agent_id (str): A unique identifier for this agent instance.
            db_manager (DatabaseManager): An instance of the DatabaseManager for database access.
            kafka_bootstrap_servers (str): Kafka bootstrap servers for producer/consumer.
        """
        super().__init__(agent_id, "admin", kafka_bootstrap_servers)
        self.db_manager = db_manager
        self.db_helper = DatabaseHelper(db_manager)
        self._db_initialized = False

        self.app = FastAPI(title="Admin Agent API", version="1.0.0")
        self.app.add_api_route("/health", self.health_check, methods=["GET"], summary="Health check for Admin Agent")
        self.app.add_api_route("/", self.root, methods=["GET"], summary="Root endpoint for Admin Agent")
        self.app.add_api_route("/api/v1/admin/users", self.create_user_endpoint, methods=["POST"], summary="Create a new system user")
        self.app.add_api_route("/api/v1/admin/stats", self.get_system_stats_endpoint, methods=["GET"], summary="Get overall system statistics")

    async def root(self):
        """Root endpoint for the Admin Agent. Returns a welcome message."""
        return {"message": "Admin Agent is running!"}

    async def health_check(self):
        """Health check endpoint for the Admin Agent. Returns agent status."""
        return {"status": "healthy", "agent": "admin_agent", "version": "1.0.0"}

    async def create_user_endpoint(self, user_data: UserCreate = Body(...)):
        """FastAPI endpoint to create a new system user.

        Args:
            user_data (UserCreate): The data for the user to be created.

        Returns:
            Dict: A dictionary with the user_id and status.

        Raises:
            HTTPException: If the database is not initialized or an error occurs during user creation.
        """
        if not self._db_initialized:
            logger.warning("Database not initialized for AdminAgent. Cannot create user.")
            raise HTTPException(status_code=500, detail="Database not initialized")
        try:
            user_id = await self.create_user(user_data)
            return {"user_id": user_id, "status": "created"}
        except Exception as e:
            logger.error("create_user_failed", error=str(e), user_data=user_data.dict())
            raise HTTPException(status_code=500, detail=f"Failed to create user: {e}")

    async def get_system_stats_endpoint(self):
        """FastAPI endpoint to get overall system statistics.

        Returns:
            Dict: A dictionary containing system statistics.

        Raises:
            HTTPException: If the database is not initialized or an error occurs during stats retrieval.
        """
        if not self._db_initialized:
            logger.warning("Database not initialized for AdminAgent. Cannot get system stats.")
            raise HTTPException(status_code=500, detail="Database not initialized")
        try:
            stats = await self.get_system_stats()
            return stats
        except Exception as e:
            logger.error("get_stats_failed", error=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to get system stats: {e}")

    async def create_user(self, user_data: UserCreate) -> UUID:
        """Creates a system user and records the operation in the database.

        Args:
            user_data (UserCreate): The data for the user to be created.

        Returns:
            UUID: The ID of the created user.
        """
        user_id = uuid4()
        logger.info("user_created", user_id=str(user_id),
                   username=user_data.username, email=user_data.email, role=user_data.role.value)
        # Placeholder for actual database operation using self.db_helper
        async with self.db_manager.get_session() as session:
            logger.info("Simulating database write for user creation.", session_type=type(session))
            # await self.db_helper.create(session, "User", user_data.dict())
        return user_id

    async def get_system_stats(self) -> Dict:
        """Retrieves system statistics from the database.

        Returns:
            Dict: A dictionary containing system statistics.
        """
        # Placeholder for actual database retrieval using self.db_helper
        async with self.db_manager.get_session() as session:
            logger.info("Simulating database read for system stats.", session_type=type(session))
            # stats_data = await self.db_helper.get_all(session, "SystemStats") # Example
        return {
            "total_users": 150,
            "active_agents": 26,
            "total_orders": 15420,
            "total_products": 8950,
            "total_customers": 12300
        }

    async def process_message(self, message: AgentMessage):
        """Processes incoming Kafka messages for the Admin Agent.

        Handles COMMAND messages for 'create_user' and 'get_system_stats'.
        Sends INFO or ERROR messages back to the sender based on the outcome.

        Args:
            message (AgentMessage): The message received from Kafka.
        """
        logger.info(f"AdminAgent received message: {message.message_type} from {message.sender_id}",
                    message_id=str(message.message_id), payload=message.payload)
        if message.message_type == MessageType.COMMAND:
            command = message.payload.get("command")
            try:
                if command == "create_user":
                    user_data = UserCreate(**message.payload.get("data", {}))
                    user_id = await self.create_user(user_data)
                    await self.send_message(AgentMessage(
                        agent_id=self.agent_id,
                        sender_id=self.agent_id,
                        recipient_id=message.sender_id,
                        message_type=MessageType.INFO,
                        payload={"status": "user_created", "user_id": str(user_id), "source_message_id": str(message.message_id)}
                    ))
                elif command == "get_system_stats":
                    stats = await self.get_system_stats()
                    await self.send_message(AgentMessage(
                        agent_id=self.agent_id,
                        sender_id=self.agent_id,
                        recipient_id=message.sender_id,
                        message_type=MessageType.INFO,
                        payload={"status": "system_stats", "stats": stats, "source_message_id": str(message.message_id)}
                    ))
                else:
                    logger.warning("Unknown command received for AdminAgent", command=command, message_payload=message.payload)
            except Exception as e:
                logger.error("process_message_admin_failed", error=str(e), message_payload=message.payload)
                await self.send_message(AgentMessage(
                    agent_id=self.agent_id,
                    sender_id=self.agent_id,
                    recipient_id=message.sender_id,
                    message_type=MessageType.ERROR,
                    payload={"error": str(e), "original_message": message.payload}
                ))
        else:
            logger.warning("Unhandled message type for AdminAgent", message_type=message.message_type, command=message.payload.get("command"))

    async def start_fastapi_app(self):
        """Starts the FastAPI application for the Admin Agent.

        The port is configured via the ADMIN_AGENT_PORT environment variable, defaulting to 8026.
        """
        port = int(os.getenv("ADMIN_AGENT_PORT", "8026"))
        config = uvicorn.Config(self.app, host="0.0.0.0", port=port)
        server = uvicorn.Server(config)
        logger.info(f"Admin Agent FastAPI app starting on port {port}")
        await server.serve()

# ==================== MAIN APPLICATION ENTRY POINT ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run a specific infrastructure agent.")
    parser.add_argument("--agent", choices=["data_sync", "api_gateway", "monitoring", "backup", "admin"],
                       required=True, help="Specify which agent to run.")
    args = parser.parse_args()
    
    agent_type = args.agent
    agent_id = os.getenv("AGENT_ID", f"{agent_type}_001")
    db_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    db_manager = DatabaseManager(db_url)

    agent = None
    if agent_type == "data_sync":
        agent = DataSyncAgent(agent_id, db_manager, kafka_servers)
    elif agent_type == "api_gateway":
        agent = APIGatewayAgent(agent_id, db_manager, kafka_servers)
    elif agent_type == "monitoring":
        agent = MonitoringAgent(agent_id, db_manager, kafka_servers)
    elif agent_type == "backup":
        agent = BackupAgent(agent_id, db_manager, kafka_servers)
    elif agent_type == "admin":
        agent = AdminAgent(agent_id, db_manager, kafka_servers)

    if agent:
        loop = asyncio.get_event_loop()
        try:
            # Simulate database initialization. In a real scenario, this would involve migrations or schema creation.
            agent._db_initialized = True 
            logger.info(f"Database connection for {agent_type} agent initialized: {db_url}")
            
            # Run both the agent's Kafka message processing loop and FastAPI app concurrently
            loop.run_until_complete(asyncio.gather(
                agent.run(),
                agent.start_fastapi_app()
            ))
        except KeyboardInterrupt:
            logger.info(f"{agent_type} Agent shutting down due to KeyboardInterrupt.")
        except Exception as e:
            logger.error(f"An unexpected error occurred in {agent_type} Agent: {e}", exc_info=True)
        finally:
            agent.stop()
            loop.close()
    else:
        logger.error(f"Unknown agent type specified: {agent_type}. Please choose from: data_sync, api_gateway, monitoring, backup, admin.")

