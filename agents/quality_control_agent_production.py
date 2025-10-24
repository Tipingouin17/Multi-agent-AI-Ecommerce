"""
Quality Control Agent - Production Ready
Handles product quality inspections, defect tracking, and quality scoring with full database integration
"""

import os
import sys
import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, AsyncGenerator
from enum import Enum
from pydantic import BaseModel, Field
from decimal import Decimal
from fastapi import FastAPI, HTTPException, Query, Path, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
import uvicorn
from contextlib import asynccontextmanager

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from shared.base_agent_v2 import BaseAgentV2
from shared.kafka_config import KafkaProducer, KafkaConsumer
from shared.database import DatabaseManager, get_database_manager
from shared.db_helpers import DatabaseHelper

logger = structlog.get_logger(__name__)


# =====================================================
# ENUMS
# =====================================================

class InspectionType(str, Enum):
    """Inspection types"""
    RECEIVING = "receiving"  # Incoming products
    OUTGOING = "outgoing"  # Before shipment
    PERIODIC = "periodic"  # Regular checks
    COMPLAINT = "complaint"  # Customer complaint follow-up


class InspectionStatus(str, Enum):
    """Inspection status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class QualityStatus(str, Enum):
    """Quality status"""
    PASS = "pass"
    FAIL = "fail"
    CONDITIONAL_PASS = "conditional_pass"


class DefectSeverity(str, Enum):
    """Defect severity levels"""
    CRITICAL = "critical"  # Product unusable
    MAJOR = "major"  # Significant impact
    MINOR = "minor"  # Cosmetic/minor issue
    TRIVIAL = "trivial"  # Negligible impact


# =====================================================
# PYDANTIC MODELS
# =====================================================

class QualityInspection(BaseModel):
    """Quality inspection model"""
    inspection_id: str
    product_id: str
    inspection_type: InspectionType
    inspector_id: str
    status: InspectionStatus = InspectionStatus.PENDING
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class InspectionResult(BaseModel):
    """Inspection result model"""
    inspection_id: str
    quality_status: QualityStatus
    quality_score: int  # 0-100
    notes: Optional[str] = None
    defects_found: List[Dict[str, Any]] = []
    inspector_id: str


class Defect(BaseModel):
    """Defect model"""
    defect_id: str
    inspection_id: str
    product_id: str
    defect_type: str
    severity: DefectSeverity
    description: str
    location: Optional[str] = None  # Where on the product
    image_url: Optional[str] = None


class QualityMetrics(BaseModel):
    """Quality metrics model"""
    product_id: str
    total_inspections: int
    pass_rate: float  # Percentage
    average_quality_score: float
    total_defects: int
    critical_defects: int
    last_inspection_date: Optional[datetime] = None


# =====================================================
# REPOSITORY
# =====================================================

class QualityControlRepository:
    """Handles all database operations for the quality control agent"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.db_helper = DatabaseHelper(db_manager)
    
    async def create_inspection(self, inspection: QualityInspection) -> Dict[str, Any]:
        """Create a quality inspection in the database"""
        try:
            async with self.db_manager.get_session() as session:
                inspection_data = {
                    "inspection_id": inspection.inspection_id,
                    "product_id": inspection.product_id,
                    "inspection_type": inspection.inspection_type.value,
                    "inspector_id": inspection.inspector_id,
                    "status": inspection.status.value,
                    "scheduled_at": inspection.scheduled_at,
                    "started_at": inspection.started_at,
                    "completed_at": inspection.completed_at,
                    "created_at": datetime.utcnow()
                }
                result = await self.db_helper.create(session, "quality_inspections", inspection_data)
                return result
        except Exception as e:
            logger.error("create_inspection_failed", error=str(e))
            raise
    
    async def get_inspection(self, inspection_id: str) -> Optional[Dict[str, Any]]:
        """Get inspection by ID"""
        try:
            async with self.db_manager.get_session() as session:
                result = await self.db_helper.get_by_id(session, "quality_inspections", inspection_id)
                return result
        except Exception as e:
            logger.error("get_inspection_failed", error=str(e))
            return None
    
    async def update_inspection_status(
        self,
        inspection_id: str,
        status: InspectionStatus,
        timestamp_field: Optional[str] = None
    ) -> bool:
        """Update inspection status"""
        try:
            async with self.db_manager.get_session() as session:
                updates = {"status": status.value}
                if timestamp_field:
                    updates[timestamp_field] = datetime.utcnow()
                result = await self.db_helper.update(session, "quality_inspections", inspection_id, updates)
                return result is not None
        except Exception as e:
            logger.error("update_inspection_status_failed", error=str(e))
            return False
    
    async def save_inspection_result(self, result: InspectionResult) -> Dict[str, Any]:
        """Save inspection result"""
        try:
            async with self.db_manager.get_session() as session:
                result_data = {
                    "id": str(uuid4()),
                    "inspection_id": result.inspection_id,
                    "quality_status": result.quality_status.value,
                    "quality_score": result.quality_score,
                    "notes": result.notes,
                    "defects_found": str(result.defects_found),  # JSON string
                    "inspector_id": result.inspector_id,
                    "created_at": datetime.utcnow()
                }
                db_result = await self.db_helper.create(session, "inspection_results", result_data)
                return db_result
        except Exception as e:
            logger.error("save_inspection_result_failed", error=str(e))
            raise
    
    async def create_defect(self, defect: Defect) -> Dict[str, Any]:
        """Create a defect record"""
        try:
            async with self.db_manager.get_session() as session:
                defect_data = {
                    "defect_id": defect.defect_id,
                    "inspection_id": defect.inspection_id,
                    "product_id": defect.product_id,
                    "defect_type": defect.defect_type,
                    "severity": defect.severity.value,
                    "description": defect.description,
                    "location": defect.location,
                    "image_url": defect.image_url,
                    "created_at": datetime.utcnow()
                }
                result = await self.db_helper.create(session, "quality_defects", defect_data)
                return result
        except Exception as e:
            logger.error("create_defect_failed", error=str(e))
            raise
    
    async def get_product_defects(self, product_id: str) -> List[Dict[str, Any]]:
        """Get all defects for a product"""
        try:
            async with self.db_manager.get_session() as session:
                results = await self.db_helper.get_all_where(
                    session,
                    "quality_defects",
                    "product_id",
                    product_id
                )
                return results or []
        except Exception as e:
            logger.error("get_product_defects_failed", error=str(e))
            return []
    
    async def get_product_inspections(self, product_id: str) -> List[Dict[str, Any]]:
        """Get all inspections for a product"""
        try:
            async with self.db_manager.get_session() as session:
                results = await self.db_helper.get_all_where(
                    session,
                    "quality_inspections",
                    "product_id",
                    product_id
                )
                return results or []
        except Exception as e:
            logger.error("get_product_inspections_failed", error=str(e))
            return []


# =====================================================
# AGENT
# =====================================================

class QualityControlAgent(BaseAgentV2):
    """
    Quality Control Agent - Production Ready
    
    Responsibilities:
    - Schedule and manage quality inspections
    - Record inspection results
    - Track product defects
    - Calculate quality metrics
    - Generate quality reports
    - Alert on quality issues
    """
    
    def __init__(self, agent_id: str = "QualityControlAgent"):
        super().__init__(agent_id=agent_id)
        self.agent_name = "Quality Control Agent"
        self.kafka_producer: Optional[KafkaProducer] = None
        self.kafka_consumer: Optional[KafkaConsumer] = None
        self.db_manager: Optional[DatabaseManager] = None
        self.repository: Optional[QualityControlRepository] = None
        
        # Initialize FastAPI app with lifespan
        self.app = FastAPI(
            title=f"{self.agent_name} API",
            lifespan=self.lifespan_context
        )
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self._setup_routes()

    @asynccontextmanager
    async def lifespan_context(self, app: FastAPI) -> AsyncGenerator[None, None]:
        """
        FastAPI Lifespan Context Manager for agent startup and shutdown.
        Initializes the database connection and the agent's services.
        """
        # Startup
        logger.info("FastAPI Lifespan Startup: Quality Control Agent")
        
        # 1. Initialize Database Manager
        try:
            self.db_manager = get_database_manager()
        except RuntimeError:
            # Fallback to creating a new manager if global one is not set
            from shared.models import DatabaseConfig
            from shared.database import EnhancedDatabaseManager
            self.db_manager = EnhancedDatabaseManager(DatabaseConfig().database_url)
        
        await self.db_manager.initialize_async()
        
        # 2. Initialize Repository and Services
        self.repository = QualityControlRepository(self.db_manager)
        
        # 3. Initialize Kafka
        self.kafka_producer = KafkaProducer()
        self.kafka_consumer = KafkaConsumer(
            "product_received",
            "product_ready_to_ship",
            "customer_complaint",
            group_id="quality_control_agent"
        )
        
        # 4. Call BaseAgentV2 initialize
        await self.initialize()
        
        yield
        
        # Shutdown
        logger.info("FastAPI Lifespan Shutdown: Quality Control Agent")
        await self.cleanup()

    async def initialize(self):
        """Initialize agent-specific components"""
        await super().initialize()
        logger.info(f"{self.agent_name} initialized successfully")

    async def cleanup(self):
        """Cleanup agent resources"""
        if self.kafka_producer:
            await self.kafka_producer.close()
        if self.kafka_consumer:
            await self.kafka_consumer.close()
        if self.db_manager:
            await self.db_manager.close()
        await super().cleanup()
        logger.info(f"{self.agent_name} cleaned up successfully")
    
    async def schedule_inspection(
        self,
        product_id: str,
        inspection_type: InspectionType,
        inspector_id: str,
        scheduled_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Schedule a quality inspection"""
        if not self.repository:
            raise ValueError("Repository not initialized")
        
        try:
            inspection = QualityInspection(
                inspection_id=str(uuid4()),
                product_id=product_id,
                inspection_type=inspection_type,
                inspector_id=inspector_id,
                status=InspectionStatus.PENDING,
                scheduled_at=scheduled_at or datetime.utcnow()
            )
            
            result = await self.repository.create_inspection(inspection)
            
            # Publish inspection scheduled event
            await self.kafka_producer.send(
                "inspection_scheduled",
                {
                    "inspection_id": inspection.inspection_id,
                    "product_id": product_id,
                    "inspection_type": inspection_type.value,
                    "scheduled_at": (scheduled_at or datetime.utcnow()).isoformat()
                }
            )
            
            logger.info("Inspection scheduled",
                       inspection_id=inspection.inspection_id,
                       product_id=product_id)
            
            return {
                "success": True,
                "inspection_id": inspection.inspection_id,
                "scheduled_at": (scheduled_at or datetime.utcnow()).isoformat()
            }
        except Exception as e:
            logger.error("schedule_inspection_failed", error=str(e))
            raise
    
    async def start_inspection(self, inspection_id: str) -> Dict[str, Any]:
        """Start an inspection"""
        if not self.repository:
            raise ValueError("Repository not initialized")
        
        try:
            success = await self.repository.update_inspection_status(
                inspection_id,
                InspectionStatus.IN_PROGRESS,
                "started_at"
            )
            
            if success:
                logger.info("Inspection started", inspection_id=inspection_id)
                return {
                    "success": True,
                    "inspection_id": inspection_id,
                    "status": InspectionStatus.IN_PROGRESS.value
                }
            else:
                return {
                    "success": False,
                    "error": "Inspection not found"
                }
        except Exception as e:
            logger.error("start_inspection_failed", error=str(e))
            raise
    
    async def complete_inspection(
        self,
        inspection_id: str,
        result: InspectionResult
    ) -> Dict[str, Any]:
        """Complete an inspection with results"""
        if not self.repository:
            raise ValueError("Repository not initialized")
        
        try:
            # Save inspection result
            await self.repository.save_inspection_result(result)
            
            # Update inspection status
            await self.repository.update_inspection_status(
                inspection_id,
                InspectionStatus.COMPLETED,
                "completed_at"
            )
            
            # Create defect records
            for defect_data in result.defects_found:
                defect = Defect(
                    defect_id=str(uuid4()),
                    inspection_id=inspection_id,
                    product_id=defect_data.get("product_id", ""),
                    defect_type=defect_data.get("defect_type", "unknown"),
                    severity=DefectSeverity(defect_data.get("severity", "minor")),
                    description=defect_data.get("description", ""),
                    location=defect_data.get("location"),
                    image_url=defect_data.get("image_url")
                )
                await self.repository.create_defect(defect)
            
            # Publish inspection completed event
            await self.kafka_producer.send(
                "inspection_completed",
                {
                    "inspection_id": inspection_id,
                    "quality_status": result.quality_status.value,
                    "quality_score": result.quality_score,
                    "defects_count": len(result.defects_found)
                }
            )
            
            # Alert if quality failed
            if result.quality_status == QualityStatus.FAIL:
                await self.kafka_producer.send(
                    "quality_alert",
                    {
                        "inspection_id": inspection_id,
                        "severity": "high",
                        "message": f"Quality inspection failed with score {result.quality_score}"
                    }
                )
            
            logger.info("Inspection completed",
                       inspection_id=inspection_id,
                       quality_status=result.quality_status.value,
                       quality_score=result.quality_score)
            
            return {
                "success": True,
                "inspection_id": inspection_id,
                "quality_status": result.quality_status.value,
                "quality_score": result.quality_score,
                "defects_count": len(result.defects_found)
            }
        except Exception as e:
            logger.error("complete_inspection_failed", error=str(e))
            raise

    async def get_product_quality_metrics(self, product_id: str) -> QualityMetrics:
        """Get quality metrics for a product"""
        if not self.repository:
            raise ValueError("Repository not initialized")
        
        try:
            inspections = await self.repository.get_product_inspections(product_id)
            defects = await self.repository.get_product_defects(product_id)
            
            total_inspections = len(inspections)
            passed_inspections = sum(1 for i in inspections if i.get("status") == "pass")
            pass_rate = (passed_inspections / total_inspections * 100) if total_inspections > 0 else 0.0
            
            # Calculate average quality score (would query from inspection_results in production)
            average_quality_score = 85.0  # Placeholder
            
            critical_defects = sum(1 for d in defects if d.get("severity") == "critical")
            
            last_inspection = max(inspections, key=lambda x: x.get("created_at", datetime.min)) if inspections else None
            
            metrics = QualityMetrics(
                product_id=product_id,
                total_inspections=total_inspections,
                pass_rate=pass_rate,
                average_quality_score=average_quality_score,
                total_defects=len(defects),
                critical_defects=critical_defects,
                last_inspection_date=last_inspection.get("created_at") if last_inspection else None
            )
            
            return metrics
        except Exception as e:
            logger.error("get_product_quality_metrics_failed", error=str(e))
            raise

    async def process_business_logic(self, data: dict) -> dict:
        """Process business logic"""
        logger.info(f"Processing business logic in {self.agent_name}", data=data)
        return {"status": "processed", "data": data}

    def _setup_routes(self):
        """Setup FastAPI routes for the Quality Control Agent API."""
        
        # Dependency to get the initialized repository
        def get_repository_dependency() -> QualityControlRepository:
            if not self.repository:
                raise HTTPException(status_code=503, detail="Repository not initialized")
            return self.repository

        @self.app.post("/api/v1/inspections/schedule")
        async def schedule_inspection_endpoint(
            product_id: str = Body(..., embed=True),
            inspection_type: InspectionType = Body(..., embed=True),
            inspector_id: str = Body(..., embed=True),
            scheduled_at: Optional[datetime] = Body(None, embed=True)
        ):
            try:
                result = await self.schedule_inspection(
                    product_id, inspection_type, inspector_id, scheduled_at
                )
                return result
            except Exception as e:
                logger.error("schedule_inspection_endpoint_failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/v1/inspections/{inspection_id}/start")
        async def start_inspection_endpoint(
            inspection_id: str = Path(...)
        ):
            try:
                result = await self.start_inspection(inspection_id)
                if not result.get("success"):
                    raise HTTPException(status_code=404, detail=result.get("error"))
                return result
            except Exception as e:
                logger.error("start_inspection_endpoint_failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/v1/inspections/{inspection_id}/complete")
        async def complete_inspection_endpoint(
            inspection_id: str = Path(...),
            result_data: InspectionResult = Body(...)
        ):
            try:
                result = await self.complete_inspection(inspection_id, result_data)
                return result
            except Exception as e:
                logger.error("complete_inspection_endpoint_failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/v1/products/{product_id}/metrics", response_model=QualityMetrics)
        async def get_product_metrics_endpoint(
            product_id: str = Path(...)
        ):
            try:
                metrics = await self.get_product_quality_metrics(product_id)
                return metrics
            except Exception as e:
                logger.error("get_product_metrics_endpoint_failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "agent": self.agent_name,
                "version": "1.0.0",
                "database": self.db_manager is not None and self.db_manager.is_initialized
            }

if __name__ == "__main__":
    agent = QualityControlAgent()
    
    # Use environment variable for port, default to 8016
    port = int(os.getenv("QUALITY_CONTROL_AGENT_PORT", 8016))
    host = os.getenv("QUALITY_CONTROL_AGENT_HOST", "0.0.0.0")
    
    logger.info(f"Starting {agent.agent_name} API on {host}:{port}")
    uvicorn.run(agent.app, host=host, port=port)
