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

app = FastAPI()


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
        
