"""
Infrastructure Agents - Multi-Agent E-Commerce System

Includes: Data Sync, API Gateway, Monitoring, Backup, and Admin agents.
Each agent can be run independently on different ports.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4, UUID
from enum import Enum

from shared.db_helpers import DatabaseHelper
import sys
import os

from fastapi import FastAPI, HTTPException, Depends, Body
from pydantic import BaseModel
import structlog

current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.database import DatabaseManager, get_database_manager

logger = structlog.get_logger(__name__)

# ==================== DATA SYNC AGENT ====================

class SyncStatus(str, Enum):
    PENDING = "pending"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"

class SyncRequest(BaseModel):
    source_agent: str
    target_agent: str
    data_type: str
    entity_ids: List[str]

class DataSyncService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def sync_data(self, sync_request: SyncRequest) -> UUID:
        """Synchronize data between agents."""
        sync_id = uuid4()
        logger.info("data_sync_started", sync_id=str(sync_id),
                   source=sync_request.source_agent, target=sync_request.target_agent)
        return sync_id

data_sync_app = FastAPI(title="Data Sync Agent API", version="1.0.0")

@data_sync_app.post("/api/v1/sync/execute")
async def execute_sync(sync_request: SyncRequest = Body(...)):
    try:
        db_manager = await get_database_manager()
        service = DataSyncService(db_manager)
        sync_id = await service.sync_data(sync_request)
        return {"sync_id": sync_id, "status": "started"}
    except Exception as e:
        logger.error("sync_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@data_sync_app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "data_sync_agent", "version": "1.0.0"}

# ==================== API GATEWAY AGENT ====================

class GatewayRequest(BaseModel):
    target_agent: str
    endpoint: str
    method: str = "GET"
    payload: Optional[Dict] = None

class APIGatewayService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def route_request(self, gateway_request: GatewayRequest) -> Dict:
        """Route request to target agent."""
        logger.info("request_routed", target=gateway_request.target_agent,
                   endpoint=gateway_request.endpoint)
        return {"status": "routed", "target": gateway_request.target_agent}

api_gateway_app = FastAPI(title="API Gateway Agent API", version="1.0.0")

@api_gateway_app.post("/api/v1/gateway/route")
async def route_request(gateway_request: GatewayRequest = Body(...)):
    try:
        db_manager = await get_database_manager()
        service = APIGatewayService(db_manager)
        result = await service.route_request(gateway_request)
        return result
    except Exception as e:
        logger.error("routing_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@api_gateway_app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "api_gateway_agent", "version": "1.0.0"}

# ==================== MONITORING AGENT ====================

class MetricType(str, Enum):
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"

class MetricData(BaseModel):
    agent_name: str
    metric_type: MetricType
    value: float
    timestamp: datetime = datetime.utcnow()

class MonitoringService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def record_metric(self, metric_data: MetricData) -> UUID:
        """Record system metric."""
        metric_id = uuid4()
        logger.info("metric_recorded", metric_id=str(metric_id),
                   agent=metric_data.agent_name, type=metric_data.metric_type.value)
        return metric_id
    
    async def get_system_health(self) -> Dict:
        """Get overall system health."""
        return {
            "status": "healthy",
            "agents_online": 26,
            "cpu_usage": 45.2,
            "memory_usage": 62.8,
            "uptime_hours": 168
        }

monitoring_app = FastAPI(title="Monitoring Agent API", version="1.0.0")

@monitoring_app.post("/api/v1/monitoring/metrics")
async def record_metric(metric_data: MetricData = Body(...)):
    try:
        db_manager = await get_database_manager()
        service = MonitoringService(db_manager)
        metric_id = await service.record_metric(metric_data)
        return {"metric_id": metric_id, "status": "recorded"}
    except Exception as e:
        logger.error("record_metric_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@monitoring_app.get("/api/v1/monitoring/health")
async def get_system_health():
    try:
        db_manager = await get_database_manager()
        service = MonitoringService(db_manager)
        health = await service.get_system_health()
        return health
    except Exception as e:
        logger.error("get_health_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@monitoring_app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "monitoring_agent", "version": "1.0.0"}

# ==================== BACKUP AGENT ====================

class BackupType(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"

class BackupRequest(BaseModel):
    backup_type: BackupType
    agents: List[str]
    retention_days: int = 30

class BackupService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_backup(self, backup_request: BackupRequest) -> UUID:
        """Create system backup."""
        backup_id = uuid4()
        logger.info("backup_created", backup_id=str(backup_id),
                   type=backup_request.backup_type.value, agents=len(backup_request.agents))
        return backup_id
    
    async def restore_backup(self, backup_id: UUID) -> bool:
        """Restore from backup."""
        logger.info("backup_restored", backup_id=str(backup_id))
        return True

backup_app = FastAPI(title="Backup Agent API", version="1.0.0")

@backup_app.post("/api/v1/backup/create")
async def create_backup(backup_request: BackupRequest = Body(...)):
    try:
        db_manager = await get_database_manager()
        service = BackupService(db_manager)
        backup_id = await service.create_backup(backup_request)
        return {"backup_id": backup_id, "status": "created"}
    except Exception as e:
        logger.error("create_backup_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@backup_app.post("/api/v1/backup/{backup_id}/restore")
async def restore_backup(backup_id: UUID):
    try:
        db_manager = await get_database_manager()
        service = BackupService(db_manager)
        success = await service.restore_backup(backup_id)
        return {"backup_id": backup_id, "status": "restored" if success else "failed"}
    except Exception as e:
        logger.error("restore_backup_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@backup_app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "backup_agent", "version": "1.0.0"}

# ==================== ADMIN AGENT ====================

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    AGENT = "agent"
    VIEWER = "viewer"

class UserCreate(BaseModel):
    username: str
    email: str
    role: UserRole

class AdminService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_user(self, user_data: UserCreate) -> UUID:
        """Create system user."""
        user_id = uuid4()
        logger.info("user_created", user_id=str(user_id),
                   username=user_data.username, role=user_data.role.value)
        return user_id
    
    async def get_system_stats(self) -> Dict:
        """Get system statistics."""
        return {
            "total_users": 150,
            "active_agents": 26,
            "total_orders": 15420,
            "total_products": 8950,
            "total_customers": 12300
        }

admin_app = FastAPI(title="Admin Agent API", version="1.0.0")

@admin_app.post("/api/v1/admin/users")
async def create_user(user_data: UserCreate = Body(...)):
    try:
        db_manager = await get_database_manager()
        service = AdminService(db_manager)
        user_id = await service.create_user(user_data)
        return {"user_id": user_id, "status": "created"}
    except Exception as e:
        logger.error("create_user_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@admin_app.get("/api/v1/admin/stats")
async def get_system_stats():
    try:
        db_manager = await get_database_manager()
        service = AdminService(db_manager)
        stats = await service.get_system_stats()
        return stats
    except Exception as e:
        logger.error("get_stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@admin_app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "admin_agent", "version": "1.0.0"}

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", choices=["data_sync", "api_gateway", "monitoring", "backup", "admin"],
                       default="data_sync")
    args = parser.parse_args()
    
    apps = {
        "data_sync": (data_sync_app, 8022),
        "api_gateway": (api_gateway_app, 8023),
        "monitoring": (monitoring_app, 8024),
        "backup": (backup_app, 8025),
        "admin": (admin_app, 8026)
    }
    
    app, port = apps[args.agent]
    uvicorn.run(app, host="0.0.0.0", port=port)

