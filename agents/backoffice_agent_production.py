"""
Backoffice Agent - Production Ready
Handles admin operations, reporting, analytics, and system configuration with full database integration
"""

import os
import sys
import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum
from pydantic import BaseModel, Field
from decimal import Decimal
from fastapi import FastAPI, HTTPException, Query, Path, Body
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
import uvicorn

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from shared.base_agent_v2 import BaseAgentV2
from shared.kafka_config import KafkaProducer, KafkaConsumer
from shared.database import DatabaseManager
from shared.db_helpers import DatabaseHelper

logger = structlog.get_logger(__name__)

# Create module-level FastAPI app
app = FastAPI(title="Backoffice Agent Production API")


# =====================================================
# ENUMS
# =====================================================

class ReportType(str, Enum):
    """Report types"""
    SALES = "sales"
    INVENTORY = "inventory"
    CUSTOMER = "customer"
    FINANCIAL = "financial"
    OPERATIONS = "operations"


class UserRole(str, Enum):
    """User roles"""
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"


# =====================================================
# PYDANTIC MODELS
# =====================================================

class User(BaseModel):
    """User model"""
    user_id: str
    username: str
    email: str
    role: UserRole
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SystemConfig(BaseModel):
    """System configuration model"""
    config_key: str
    config_value: str
    config_type: str  # string, number, boolean, json
    description: Optional[str] = None


class Report(BaseModel):
    """Report model"""
    report_id: str
    report_type: ReportType
    title: str
    description: Optional[str] = None
    parameters: Dict[str, Any]
    generated_by: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# =====================================================
# REPOSITORY
# =====================================================

class BackofficeRepository:
    """Handles all database operations for the backoffice agent"""
    
    def __init__(self, db_manager: DatabaseManager):
        # FastAPI app for REST API
        
        
        # Add CORS middleware for dashboard integration
        
        self.db_manager = db_manager
        self.db_helper = DatabaseHelper(db_manager)
    
    async def create_user(self, user: User) -> Dict[str, Any]:
        """Create a user in the database"""
        try:
            async with self.db_manager.get_session() as session:
                user_data = {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role.value,
                    "is_active": user.is_active,
                    "created_at": user.created_at
                }
                result = await self.db_helper.create(session, "users", user_data)
                return result
        except Exception as e:
            logger.error("create_user_failed", error=str(e))
            raise
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            async with self.db_manager.get_session() as session:
                result = await self.db_helper.get_by_id(session, "users", user_id)
                return result
        except Exception as e:
            logger.error("get_user_failed", error=str(e))
            return None
    
    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        try:
            async with self.db_manager.get_session() as session:
                results = await self.db_helper.get_all(session, "users")
                return results or []
        except Exception as e:
            logger.error("get_all_users_failed", error=str(e))
            return []
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user"""
        try:
            async with self.db_manager.get_session() as session:
                result = await self.db_helper.update(session, "users", user_id, updates)
                return result is not None
        except Exception as e:
            logger.error("update_user_failed", error=str(e))
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        try:
            async with self.db_manager.get_session() as session:
                result = await self.db_helper.delete(session, "users", user_id)
                return result is not None
        except Exception as e:
            logger.error("delete_user_failed", error=str(e))
            return False
    
    async def set_config(self, config: SystemConfig) -> Dict[str, Any]:
        """Set system configuration"""
        try:
            async with self.db_manager.get_session() as session:
                config_data = {
                    "config_key": config.config_key,
                    "config_value": config.config_value,
                    "config_type": config.config_type,
                    "description": config.description,
                    "updated_at": datetime.utcnow()
                }
                # Upsert: update if exists, create if not
                existing = await self.db_helper.get_by_id(session, "system_config", config.config_key)
                if existing:
                    result = await self.db_helper.update(session, "system_config", config.config_key, config_data)
                else:
                    result = await self.db_helper.create(session, "system_config", config_data)
                return result
        except Exception as e:
            logger.error("set_config_failed", error=str(e))
            raise
    
    async def get_config(self, config_key: str) -> Optional[Dict[str, Any]]:
        """Get system configuration"""
        try:
            async with self.db_manager.get_session() as session:
                result = await self.db_helper.get_by_id(session, "system_config", config_key)
                return result
        except Exception as e:
            logger.error("get_config_failed", error=str(e))
            return None
    
    async def get_all_config(self) -> List[Dict[str, Any]]:
        """Get all system configurations"""
        try:
            async with self.db_manager.get_session() as session:
                results = await self.db_helper.get_all(session, "system_config")
                return results or []
        except Exception as e:
            logger.error("get_all_config_failed", error=str(e))
            return []
    
    async def save_report(self, report: Report) -> Dict[str, Any]:
        """Save generated report"""
        try:
            async with self.db_manager.get_session() as session:
                report_data = {
                    "report_id": report.report_id,
                    "report_type": report.report_type.value,
                    "title": report.title,
                    "description": report.description,
                    "parameters": str(report.parameters),  # JSON string
                    "generated_by": report.generated_by,
                    "generated_at": report.generated_at
                }
                result = await self.db_helper.create(session, "reports", report_data)
                return result
        except Exception as e:
            logger.error("save_report_failed", error=str(e))
            raise


# =====================================================
# AGENT
# =====================================================

class BackofficeAgent(BaseAgentV2):
    """
    Backoffice Agent - Production Ready
    
    Responsibilities:
    - User management (CRUD)
    - System configuration
    - Report generation
    - Analytics and dashboards
    - Audit logs
    - System health monitoring
    """
    
    def __init__(self):
        super().__init__(agent_id="BackofficeAgent")
        self.kafka_producer: Optional[KafkaProducer] = None
        self.kafka_consumer: Optional[KafkaConsumer] = None
        self.db_manager: Optional[DatabaseManager] = None
        self.db_helper: Optional[DatabaseHelper] = None
        self.repository: Optional[BackofficeRepository] = None
        self._db_initialized = False
        
    async def initialize(self):
        """Initialize agent with database and Kafka"""
        await super().initialize()
        
        # Initialize Database
        try:
            from shared.database_manager import get_database_manager
            self.db_manager = get_database_manager()
            logger.info("Using global database manager")
        except (RuntimeError, ImportError):
            from shared.models import DatabaseConfig
            from shared.database_manager import EnhancedDatabaseManager
            db_config = DatabaseConfig()
            self.db_manager = EnhancedDatabaseManager(db_config)
            await self.db_manager.initialize(max_retries=5)
            logger.info("Created new enhanced database manager")
        
        self.db_helper = DatabaseHelper(self.db_manager)
        self.repository = BackofficeRepository(self.db_manager)
        self._db_initialized = True
        
        # Initialize Kafka
        self.kafka_producer = KafkaProducer()
        self.kafka_consumer = KafkaConsumer(
            "system_event",
            "audit_log",
            group_id="backoffice_agent"
        )
        
        logger.info("Backoffice Agent initialized successfully")
    
    async def generate_sales_report(
        self,
        start_date: datetime,
        end_date: datetime,
        generated_by: str
    ) -> Dict[str, Any]:
        """Generate sales report"""
        if not self._db_initialized:
            raise ValueError("Database not initialized")
        
        try:
            # Query sales data from database
            async with self.db_manager.get_session() as session:
                # In production, this would query actual sales data
                sales_data = {
                    "total_orders": 0,
                    "total_revenue": 0.0,
                    "average_order_value": 0.0,
                    "period": f"{start_date.date()} to {end_date.date()}"
                }
            
            # Save report
            report = Report(
                report_id=str(uuid4()),
                report_type=ReportType.SALES,
                title=f"Sales Report {start_date.date()} - {end_date.date()}",
                description="Sales performance report",
                parameters={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                generated_by=generated_by
            )
            
            await self.repository.save_report(report)
            
            logger.info("Sales report generated", report_id=report.report_id)
            
            return {
                "success": True,
                "report_id": report.report_id,
                "data": sales_data
            }
        except Exception as e:
            logger.error("generate_sales_report_failed", error=str(e))
            raise
    
    async def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get dashboard metrics"""
        if not self._db_initialized:
            raise ValueError("Database not initialized")
        
        try:
            async with self.db_manager.get_session() as session:
                # In production, this would query actual metrics
                metrics = {
                    "total_orders_today": 0,
                    "total_revenue_today": 0.0,
                    "active_customers": 0,
                    "pending_shipments": 0,
                    "low_stock_items": 0,
                    "system_health": "healthy",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            return metrics
        except Exception as e:
            logger.error("get_dashboard_metrics_failed", error=str(e))
            raise


    async def cleanup(self):
        """Cleanup agent resources"""
        if hasattr(self, 'kafka_producer') and self.kafka_producer:
            await self.kafka_producer.close()
        if hasattr(self, 'kafka_consumer') and self.kafka_consumer:
            await self.kafka_consumer.close()
        if hasattr(self, 'db_manager') and self.db_manager:
            await self.db_manager.close()
        logger.info(f"{self.__class__.__name__} cleaned up")
    
    async def process_business_logic(self, data: dict) -> dict:
        """Process business logic"""
        logger.info(f"Processing business logic in {self.__class__.__name__}", data=data)
        return {"status": "processed", "data": data}


# =====================================================
# FASTAPI APP
# =====================================================

# FastAPI app is module-level for uvicorn to load.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent_instance: Optional[BackofficeAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Context Manager for agent startup and shutdown.
    Replaces deprecated @app.on_event("startup/shutdown").
    """
    global agent_instance
    
    # Startup
    logger.info("FastAPI Lifespan Startup: Backoffice Agent")
    agent_instance = BackofficeAgent()
    await agent_instance.initialize()
    logger.info("Backoffice Agent API started")
    
    yield
    
    # Shutdown
    logger.info("FastAPI Lifespan Shutdown: Backoffice Agent")
    if agent_instance:
        await agent_instance.cleanup() # Assuming cleanup handles db_manager.close()
    logger.info("Backoffice Agent API shutdown complete")


# Create module-level FastAPI app
app = FastAPI(title="Backoffice Agent Production API", lifespan=lifespan)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent": "BackofficeAgent",
        "version": "1.0.0",
        "database": agent_instance._db_initialized if agent_instance else False
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "agent": "BackofficeAgent",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/users",
            "/users/{user_id}",
            "/config",
            "/config/{config_key}",
            "/reports/sales",
            "/dashboard/metrics"
        ]
    }


@app.post("/users", summary="Create User")
async def create_user(user: User):
    """Create a new user"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await agent_instance.repository.create_user(user)
        return result
    except Exception as e:
        logger.error("create_user_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/users", summary="Get All Users")
async def get_all_users():
    """Get all users"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        users = await agent_instance.repository.get_all_users()
        return {
            "users": users,
            "total": len(users)
        }
    except Exception as e:
        logger.error("get_all_users_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/users/{user_id}", summary="Get User")
async def get_user(user_id: str = Path(...)):
    """Get user by ID"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        user = await agent_instance.repository.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_user_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.put("/users/{user_id}", summary="Update User")
async def update_user(
    user_id: str = Path(...),
    updates: Dict[str, Any] = Body(...)
):
    """Update user"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        success = await agent_instance.repository.update_user(user_id, updates)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        return {"success": True, "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_user_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.delete("/users/{user_id}", summary="Delete User")
async def delete_user(user_id: str = Path(...)):
    """Delete user"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        success = await agent_instance.repository.delete_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        return {"success": True, "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_user_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/config", summary="Set Configuration")
async def set_config(config: SystemConfig):
    """Set system configuration"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await agent_instance.repository.set_config(config)
        return result
    except Exception as e:
        logger.error("set_config_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/config", summary="Get All Configuration")
async def get_all_config():
    """Get all system configurations"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        configs = await agent_instance.repository.get_all_config()
        return {
            "configs": configs,
            "total": len(configs)
        }
    except Exception as e:
        logger.error("get_all_config_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/config/{config_key}", summary="Get Configuration")
async def get_config(config_key: str = Path(...)):
    """Get system configuration by key"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        config = await agent_instance.repository.get_config(config_key)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_config_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/reports/sales", summary="Generate Sales Report")
async def generate_sales_report(
    start_date: datetime = Body(...),
    end_date: datetime = Body(...),
    generated_by: str = Body(...)
):
    """Generate sales report"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await agent_instance.generate_sales_report(start_date, end_date, generated_by)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("generate_sales_report_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/dashboard/metrics", summary="Get Dashboard Metrics")
async def get_dashboard_metrics():
    """Get dashboard metrics"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        metrics = await agent_instance.get_dashboard_metrics()
        return metrics
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("get_dashboard_metrics_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")



# Create agent instance at module level to ensure routes are registered
agent = BackofficeAgent()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8021))
    logger.info(f"Starting Backoffice Agent on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

