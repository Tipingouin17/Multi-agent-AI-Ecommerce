"""
Quality Control Agent
Handles product inspection, damage verification, quality assurance, and defect tracking
"""

import os
import sys
import asyncio
import structlog
from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum
from pydantic import BaseModel, Field
from decimal import Decimal

from shared.db_helpers import DatabaseHelper

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from shared.base_agent import BaseAgent
from shared.kafka_config import KafkaProducer, KafkaConsumer

logger = structlog.get_logger(__name__)


class InspectionType(str, Enum):
    """Types of inspections"""
    INCOMING = "incoming"  # New inventory from supplier
    OUTGOING = "outgoing"  # Before shipping to customer
    RETURN = "return"  # Returned products
    RANDOM = "random"  # Random quality checks
    COMPLAINT = "complaint"  # Customer complaint investigation


class ProductCondition(str, Enum):
    """Product condition assessment"""
    NEW = "new"
    LIKE_NEW = "like_new"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    DEFECTIVE = "defective"
    DAMAGED = "damaged"
    UNUSABLE = "unusable"


class DefectType(str, Enum):
    """Types of defects"""
    COSMETIC = "cosmetic"  # Scratches, dents, discoloration
    FUNCTIONAL = "functional"  # Doesn't work properly
    MISSING_PARTS = "missing_parts"
    WRONG_ITEM = "wrong_item"
    PACKAGING_DAMAGE = "packaging_damage"
    MANUFACTURING_DEFECT = "manufacturing_defect"
    SHIPPING_DAMAGE = "shipping_damage"


class DispositionAction(str, Enum):
    """What to do with inspected product"""
    APPROVE = "approve"  # Ship to customer / restock
    REJECT = "reject"  # Do not ship / do not restock
    RESTOCK = "restock"  # Return to inventory
    RESTOCK_AS_REFURBISHED = "restock_as_refurbished"
    RETURN_TO_SUPPLIER = "return_to_supplier"
    RETURN_TO_MANUFACTURER = "return_to_manufacturer"
    DISPOSE = "dispose"  # Discard/recycle
    REPAIR = "repair"  # Send for repair
    MANUAL_REVIEW = "manual_review"  # Needs human decision


class InspectionRequest(BaseModel):
    """Inspection request model"""
    inspection_id: str = Field(default_factory=lambda: f"INSP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
    inspection_type: InspectionType
    product_id: str
    sku: str
    order_id: Optional[str] = None
    rma_number: Optional[str] = None
    warehouse_id: str
    requested_by: str
    priority: int = 5  # 1-10, 10 being highest
    requested_at: datetime = Field(default_factory=datetime.utcnow)


class InspectionResult(BaseModel):
    """Inspection result model"""
    inspection_id: str
    product_id: str
    sku: str
    condition: ProductCondition
    defects_found: List[DefectType] = []
    defect_description: Optional[str] = None
    photos: List[str] = []  # URLs to photos
    disposition: DispositionAction
    disposition_reason: str
    inspector_id: str
    inspected_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class QualityIssue(BaseModel):
    """Quality issue tracking"""
    issue_id: str = Field(default_factory=lambda: f"QI-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
    product_id: str
    sku: str
    supplier_id: Optional[str] = None
    defect_type: DefectType
    severity: str  # low, medium, high, critical
    description: str
    affected_quantity: int
    reported_by: str
    reported_at: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False


class QualityControlAgent(BaseAgent):
    """
    Quality Control Agent
    
    Responsibilities:
    - Inspect incoming products from suppliers
    - Inspect outgoing products before shipping
    - Inspect returned products
    - Verify product condition and authenticity
    - Detect and track defects
    - Determine product disposition
    - Track quality metrics by supplier/product
    - Trigger supplier quality reviews
    """
    
    def __init__(self):
        super().__init__("QualityControlAgent")
        self.kafka_producer = None
        self.kafka_consumer = None
        self.quality_standards = {}
        self.defect_thresholds = {
            "cosmetic": 0.05,  # 5% acceptable
            "functional": 0.01,  # 1% acceptable
            "critical": 0.001  # 0.1% acceptable
        }
        
    async def initialize(self):
        """Initialize agent"""
        await super().initialize()
        self.kafka_producer = KafkaProducer()
        self.kafka_consumer = KafkaConsumer(
            topics=[
                "inventory_received",
                "order_ready_to_ship",
                "return_received",
                "quality_inspection_requested"
            ],
            group_id="quality_control_agent"
        )
        await self._load_quality_standards()
        logger.info("Quality Control Agent initialized")
    
    async def inspect_product(
        self,
        request: InspectionRequest
    ) -> InspectionResult:
        """
        Perform product inspection
        
        Args:
            request: Inspection request details
            
        Returns:
            Inspection result with disposition
        """
        try:
            logger.info("Starting product inspection",
                       inspection_id=request.inspection_id,
                       product_id=request.product_id,
                       type=request.inspection_type)
            
            # Get product details and quality standards
            product = await self._get_product_details(request.product_id)
            standards = await self._get_quality_standards(request.product_id)
            
            # Perform inspection checks
            condition, defects = await self._perform_inspection_checks(
                product,
                standards,
                request.inspection_type
            )
            
            # Determine disposition based on condition and defects
            disposition, reason = await self._determine_disposition(
                condition,
                defects,
                request.inspection_type
            )
            
            # Create inspection result
            result = InspectionResult(
                inspection_id=request.inspection_id,
                product_id=request.product_id,
                sku=request.sku,
                condition=condition,
                defects_found=defects,
                defect_description=self._format_defect_description(defects),
                disposition=disposition,
                disposition_reason=reason,
                inspector_id="QC_AGENT",
                notes=f"Inspection type: {request.inspection_type}"
            )
            
            # Save inspection result
            await self._save_inspection_result(result)
            
            # Track quality issues if defects found
            if defects:
                await self._track_quality_issue(request, result, product)
            
            # Publish inspection completed event
            await self.kafka_producer.send(
                "inspection_completed",
                {
                    "inspection_id": result.inspection_id,
                    "product_id": result.product_id,
                    "condition": result.condition.value,
                    "disposition": result.disposition.value,
                    "defects_found": [d.value for d in result.defects_found],
                    "order_id": request.order_id,
                    "rma_number": request.rma_number,
                    "inspected_at": result.inspected_at.isoformat()
                }
            )
            
            logger.info("Inspection completed",
                       inspection_id=result.inspection_id,
                       condition=result.condition,
                       disposition=result.disposition)
            
            return result
            
        except Exception as e:
            logger.error("Failed to inspect product",
                        error=str(e),
                        inspection_id=request.inspection_id)
            raise
    
    async def _perform_inspection_checks(
        self,
        product: Dict[str, Any],
        standards: Dict[str, Any],
        inspection_type: InspectionType
    ) -> tuple[ProductCondition, List[DefectType]]:
        """
        Perform actual inspection checks
        
        Returns:
            Tuple of (condition, list of defects)
        """
        defects = []
        
        # In a real implementation, this would involve:
        # - Physical inspection by warehouse staff
        # - Computer vision for automated checks
        # - Barcode/serial number verification
        # - Functional testing for electronics
        # - Packaging integrity checks
        
        # For simulation, we'll use probabilistic defect detection
        import random
        
        # Check for cosmetic defects
        if random.random() < 0.05:  # 5% chance
            defects.append(DefectType.COSMETIC)
        
        # Check for functional defects (lower probability)
        if random.random() < 0.01:  # 1% chance
            defects.append(DefectType.FUNCTIONAL)
        
        # Check for shipping damage (only for returns)
        if inspection_type == InspectionType.RETURN and random.random() < 0.10:
            defects.append(DefectType.SHIPPING_DAMAGE)
        
        # Check for missing parts
        if random.random() < 0.02:  # 2% chance
            defects.append(DefectType.MISSING_PARTS)
        
        # Determine overall condition based on defects
        if not defects:
            condition = ProductCondition.NEW if inspection_type == InspectionType.INCOMING else ProductCondition.LIKE_NEW
        elif DefectType.FUNCTIONAL in defects:
            condition = ProductCondition.DEFECTIVE
        elif DefectType.SHIPPING_DAMAGE in defects:
            condition = ProductCondition.DAMAGED
        elif DefectType.COSMETIC in defects:
            condition = ProductCondition.GOOD
        else:
            condition = ProductCondition.FAIR
        
        return condition, defects
    
    async def _determine_disposition(
        self,
        condition: ProductCondition,
        defects: List[DefectType],
        inspection_type: InspectionType
    ) -> tuple[DispositionAction, str]:
        """
        Determine what to do with the product
        
        Returns:
            Tuple of (disposition action, reason)
        """
        # Outgoing inspection (before shipping to customer)
        if inspection_type == InspectionType.OUTGOING:
            if condition in [ProductCondition.NEW, ProductCondition.LIKE_NEW]:
                return DispositionAction.APPROVE, "Product meets quality standards"
            elif condition == ProductCondition.GOOD and not any(d in [DefectType.FUNCTIONAL, DefectType.MISSING_PARTS] for d in defects):
                return DispositionAction.APPROVE, "Minor cosmetic issues acceptable"
            else:
                return DispositionAction.REJECT, f"Product does not meet shipping standards: {condition}"
        
        # Incoming inspection (from supplier)
        elif inspection_type == InspectionType.INCOMING:
            if condition in [ProductCondition.NEW, ProductCondition.LIKE_NEW]:
                return DispositionAction.RESTOCK, "Product approved for inventory"
            elif DefectType.FUNCTIONAL in defects or DefectType.MANUFACTURING_DEFECT in defects:
                return DispositionAction.RETURN_TO_SUPPLIER, "Manufacturing defect detected"
            elif condition == ProductCondition.DAMAGED:
                return DispositionAction.RETURN_TO_SUPPLIER, "Product damaged in transit"
            else:
                return DispositionAction.MANUAL_REVIEW, "Requires manual review"
        
        # Return inspection
        elif inspection_type == InspectionType.RETURN:
            if condition == ProductCondition.DEFECTIVE:
                return DispositionAction.RETURN_TO_MANUFACTURER, "Defective product - warranty claim"
            elif condition == ProductCondition.DAMAGED:
                return DispositionAction.DISPOSE, "Product too damaged to resell"
            elif condition in [ProductCondition.NEW, ProductCondition.LIKE_NEW]:
                return DispositionAction.RESTOCK, "Product in excellent condition - restock"
            elif condition in [ProductCondition.GOOD, ProductCondition.FAIR]:
                return DispositionAction.RESTOCK_AS_REFURBISHED, "Restock as refurbished item"
            else:
                return DispositionAction.MANUAL_REVIEW, "Requires manual review"
        
        # Default
        return DispositionAction.MANUAL_REVIEW, "Standard inspection - manual review required"
    
    def _format_defect_description(self, defects: List[DefectType]) -> Optional[str]:
        """Format defects into human-readable description"""
        if not defects:
            return None
        
        descriptions = {
            DefectType.COSMETIC: "Minor cosmetic issues (scratches, scuffs)",
            DefectType.FUNCTIONAL: "Product does not function properly",
            DefectType.MISSING_PARTS: "Missing parts or accessories",
            DefectType.WRONG_ITEM: "Wrong item received",
            DefectType.PACKAGING_DAMAGE: "Packaging is damaged",
            DefectType.MANUFACTURING_DEFECT: "Manufacturing defect detected",
            DefectType.SHIPPING_DAMAGE: "Damage occurred during shipping"
        }
        
        return "; ".join([descriptions.get(d, str(d)) for d in defects])
    
    async def _track_quality_issue(
        self,
        request: InspectionRequest,
        result: InspectionResult,
        product: Dict[str, Any]
    ):
        """Track quality issues for reporting and supplier management"""
        for defect in result.defects_found:
            # Determine severity
            if defect in [DefectType.FUNCTIONAL, DefectType.MANUFACTURING_DEFECT]:
                severity = "critical"
            elif defect in [DefectType.MISSING_PARTS, DefectType.WRONG_ITEM]:
                severity = "high"
            elif defect == DefectType.SHIPPING_DAMAGE:
                severity = "medium"
            else:
                severity = "low"
            
            issue = QualityIssue(
                product_id=product["product_id"],
                sku=product["sku"],
                supplier_id=product.get("supplier_id"),
                defect_type=defect,
                severity=severity,
                description=result.defect_description or "",
                affected_quantity=1,
                reported_by="QC_AGENT"
            )
            
            await self._save_quality_issue(issue)
            
            # Publish quality issue event
            await self.kafka_producer.send(
                "quality_issue_detected",
                {
                    "issue_id": issue.issue_id,
                    "product_id": issue.product_id,
                    "supplier_id": issue.supplier_id,
                    "defect_type": issue.defect_type.value,
                    "severity": issue.severity,
                    "reported_at": issue.reported_at.isoformat()
                }
            )
    
    async def analyze_supplier_quality(
        self,
        supplier_id: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze quality metrics for a supplier
        
        Args:
            supplier_id: Supplier ID
            period_days: Analysis period in days
            
        Returns:
            Quality metrics and recommendations
        """
        try:
            logger.info("Analyzing supplier quality",
                       supplier_id=supplier_id,
                       period_days=period_days)
            
            # Get quality issues for supplier in period
            issues = await self._get_supplier_quality_issues(
                supplier_id,
                period_days
            )
            
            # Calculate metrics
            total_received = await self._get_supplier_received_quantity(
                supplier_id,
                period_days
            )
            
            defect_rate = len(issues) / total_received if total_received > 0 else 0
            
            # Categorize issues
            critical_issues = [i for i in issues if i["severity"] == "critical"]
            high_issues = [i for i in issues if i["severity"] == "high"]
            
            # Determine quality rating
            if defect_rate < 0.01:
                rating = "excellent"
            elif defect_rate < 0.03:
                rating = "good"
            elif defect_rate < 0.05:
                rating = "fair"
            else:
                rating = "poor"
            
            # Generate recommendations
            recommendations = []
            if critical_issues:
                recommendations.append("Review supplier contract - critical defects detected")
            if defect_rate > 0.05:
                recommendations.append("Consider alternative suppliers")
            if len(high_issues) > 5:
                recommendations.append("Schedule quality review meeting with supplier")
            
            result = {
                "supplier_id": supplier_id,
                "period_days": period_days,
                "total_received": total_received,
                "total_issues": len(issues),
                "defect_rate": defect_rate,
                "critical_issues": len(critical_issues),
                "high_issues": len(high_issues),
                "quality_rating": rating,
                "recommendations": recommendations
            }
            
            logger.info("Supplier quality analysis complete",
                       supplier_id=supplier_id,
                       rating=rating,
                       defect_rate=defect_rate)
            
            return result
            
        except Exception as e:
            logger.error("Failed to analyze supplier quality",
                        error=str(e),
                        supplier_id=supplier_id)
            if not self._db_initialized:
                return {}
        
        async with self.db_manager.get_session() as session:
            record = await self.db_helper.get_by_id(session, QualityInspectionDB, record_id)
            return self.db_helper.to_dict(record) if record else {}
    
    # Database helper methods
    async def _load_quality_standards(self):
        """Load quality standards from database"""
        # Implementation would load from database
        self.quality_standards = {
            "default": {
                "max_cosmetic_defects": 0,
                "functional_test_required": True,
                "packaging_integrity_required": True
            }
        }
    
    async def _get_product_details(self, product_id: str) -> Dict[str, Any]:
        """Get product details from database"""
        # Implementation would query database
        return {
            "product_id": product_id,
            "sku": "SKU123",
            "name": "Product Name",
            "supplier_id": "SUP123"
        }
    
    async def _get_quality_standards(self, product_id: str) -> Dict[str, Any]:
        """Get quality standards for product"""
        return self.quality_standards.get(product_id, self.quality_standards["default"])
    
    async def _save_inspection_result(self, result: InspectionResult) -> bool:
        """Save inspection result to database"""
        # Implementation would save to database
        return True
    
    async def _save_quality_issue(self, issue: QualityIssue) -> bool:
        """Save quality issue to database"""
        # Implementation would save to database
        return True
    
    async def _get_supplier_quality_issues(
        self,
        supplier_id: str,
        period_days: int
    ) -> List[Dict[str, Any]]:
        """Get quality issues for supplier in period"""
        # Implementation would query database
        if not self._db_initialized:
            return []
        
        async with self.db_manager.get_session() as session:
            records = await self.db_helper.get_all(session, QualityInspectionDB, limit=100)
            return [self.db_helper.to_dict(r) for r in records]
    
    async def _get_supplier_received_quantity(
        self,
        supplier_id: str,
        period_days: int
    ) -> int:
        """Get total quantity received from supplier in period"""
        # Implementation would query database
        return 100
    
    async def run(self):
        """Main agent loop"""
        logger.info("Quality Control Agent starting...")
        await self.initialize()
        
        try:
            async for message in self.kafka_consumer:
                topic = message.topic
                data = message.value
                
                if topic == "inventory_received":
                    # Inspect incoming inventory
                    request = InspectionRequest(
                        inspection_type=InspectionType.INCOMING,
                        product_id=data["product_id"],
                        sku=data["sku"],
                        warehouse_id=data["warehouse_id"],
                        requested_by="SYSTEM"
                    )
                    await self.inspect_product(request)
                
                elif topic == "order_ready_to_ship":
                    # Random outgoing inspection (10% of orders)
                    import random
                    if random.random() < 0.10:
                        request = InspectionRequest(
                            inspection_type=InspectionType.OUTGOING,
                            product_id=data["product_id"],
                            sku=data["sku"],
                            order_id=data["order_id"],
                            warehouse_id=data["warehouse_id"],
                            requested_by="SYSTEM"
                        )
                        await self.inspect_product(request)
                
                elif topic == "return_received":
                    # Inspect returned product
                    request = InspectionRequest(
                        inspection_type=InspectionType.RETURN,
                        product_id=data["product_id"],
                        sku=data["sku"],
                        rma_number=data["rma_number"],
                        warehouse_id=data["warehouse_id"],
                        requested_by="SYSTEM",
                        priority=8
                    )
                    result = await self.inspect_product(request)
                    
                    # Send result to after-sales agent
                    await self.kafka_producer.send(
                        "return_inspected",
                        {
                            "rma_number": data["rma_number"],
                            "condition": result.condition.value,
                            "disposition": result.disposition.value,
                            "inspection_notes": result.defect_description or "No defects found"
                        }
                    )
                
                elif topic == "quality_inspection_requested":
                    # Manual inspection request
                    request = InspectionRequest(**data)
                    await self.inspect_product(request)
                
        except Exception as e:
            logger.error("Error in agent loop", error=str(e))
        finally:
            await self.shutdown()


if __name__ == "__main__":
    agent = QualityControlAgent()
    asyncio.run(agent.run())

