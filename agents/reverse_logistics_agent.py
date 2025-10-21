"""
Reverse Logistics Agent - Multi-Agent E-commerce System

This agent manages the complete reverse supply chain including:
- Return request processing and authorization
- Quality assessment and grading of returned items
- Refurbishment and reconditioning operations
- Resale optimization and channel selection
- Waste management and disposal coordination
"""

import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4
from enum import Enum

from shared.db_helpers import DatabaseHelper

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import structlog
import sys
import os

# Get the absolute path of the current file
current_file_path = os.path.abspath(__file__)

# Get the directory containing the current file
current_dir = os.path.dirname(current_file_path)

# Get the parent directory (project root)
project_root = os.path.dirname(current_dir)

# Add the project root to the Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logger.info(f"Added {project_root} to Python path")

# Now try the import
try:
    from shared.openai_helper import chat_completion
    from shared.base_agent import BaseAgent, MessageType, AgentMessage
    logger.info("Successfully imported shared.base_agent")
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.info(f"Current sys.path: {sys.path}")
    
    # List files in the shared directory to verify it exists
    shared_dir = os.path.join(project_root, "shared")
    if os.path.exists(shared_dir):
        logger.info(f"Contents of {shared_dir}:")
        for item in os.listdir(shared_dir):
            logger.info(f"  - {item}")
    else:
        logger.info(f"Directory not found: {shared_dir}")

from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.models import APIResponse
from shared.database import DatabaseManager, get_database_manager


logger = structlog.get_logger(__name__)


class ReturnReason(str, Enum):
    """Enumeration of return reasons."""
    DEFECTIVE = "defective"
    WRONG_ITEM = "wrong_item"
    NOT_AS_DESCRIBED = "not_as_described"
    CHANGED_MIND = "changed_mind"
    DAMAGED_SHIPPING = "damaged_shipping"
    SIZE_ISSUE = "size_issue"
    QUALITY_ISSUE = "quality_issue"
    OTHER = "other"


class ItemCondition(str, Enum):
    """Enumeration of item conditions."""
    NEW = "new"
    LIKE_NEW = "like_new"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    DEFECTIVE = "defective"
    UNREPAIRABLE = "unrepairable"


class RefurbishmentAction(str, Enum):
    """Enumeration of refurbishment actions."""
    CLEAN_ONLY = "clean_only"
    MINOR_REPAIR = "minor_repair"
    MAJOR_REPAIR = "major_repair"
    REPLACE_PARTS = "replace_parts"
    REPACKAGE = "repackage"
    DISPOSE = "dispose"
    RECYCLE = "recycle"


class ResaleChannel(str, Enum):
    """Enumeration of resale channels."""
    MAIN_STORE = "main_store"
    OUTLET_STORE = "outlet_store"
    REFURBISHED_SECTION = "refurbished_section"
    THIRD_PARTY_MARKETPLACE = "third_party_marketplace"
    WHOLESALE = "wholesale"
    LIQUIDATION = "liquidation"
    DONATION = "donation"


class ReturnRequest(BaseModel):
    """Model for return requests."""
    return_id: str
    order_id: str
    customer_id: str
    product_id: str
    quantity: int
    return_reason: ReturnReason
    customer_description: str
    requested_at: datetime
    status: str = "pending"  # pending, approved, rejected, received, processed
    return_label_generated: bool = False
    estimated_refund: float
    return_deadline: datetime


class QualityAssessment(BaseModel):
    """Model for quality assessment of returned items."""
    assessment_id: str
    return_id: str
    product_id: str
    assessed_condition: ItemCondition
    defects_found: List[str]
    photos_taken: List[str]  # Photo file paths
    assessor_notes: str
    assessment_date: datetime
    resale_value_estimate: float
    recommended_action: RefurbishmentAction
    confidence_score: float


class RefurbishmentTask(BaseModel):
    """Model for refurbishment tasks."""
    task_id: str
    return_id: str
    product_id: str
    current_condition: ItemCondition
    target_condition: ItemCondition
    required_actions: List[RefurbishmentAction]
    estimated_cost: float
    estimated_time_hours: int
    assigned_technician: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    actual_cost: Optional[float] = None
    final_condition: Optional[ItemCondition] = None


class ResaleRecommendation(BaseModel):
    """Model for resale recommendations."""
    recommendation_id: str
    product_id: str
    current_condition: ItemCondition
    recommended_channel: ResaleChannel
    recommended_price: float
    expected_margin: float
    confidence_score: float
    reasoning: List[str]
    market_analysis: Dict[str, Any]
    generated_at: datetime


class ReverseLogisticsMetrics(BaseModel):
    """Model for reverse logistics performance metrics."""
    period_start: datetime
    period_end: datetime
    total_returns: int
    returns_processed: int
    average_processing_time_hours: float
    refurbishment_success_rate: float
    resale_rate: float
    total_recovery_value: float
    cost_per_return: float
    customer_satisfaction_score: float


class ReverseLogisticsAgent(BaseAgent):
    """
    Reverse Logistics Agent manages the complete reverse supply chain including:
    - Return authorization and processing
    - Quality assessment and grading
    - Refurbishment operations management
    - Resale optimization and channel selection
    - Performance analytics and optimization
    """
    
    def __init__(self, **kwargs):
        super().__init__(agent_id="reverse_logistics_agent", **kwargs)
        self.app = FastAPI(title="Reverse Logistics Agent API", version="1.0.0")
        self.setup_routes()
        # OpenAI client is initialized in openai_helper
        # Reverse logistics data
        self.return_requests: Dict[str, ReturnRequest] = {}
        self.quality_assessments: Dict[str, QualityAssessment] = {}
        self.refurbishment_tasks: Dict[str, RefurbishmentTask] = {}
        self.resale_recommendations: Dict[str, ResaleRecommendation] = {}
        
        # Performance tracking
        self.metrics_history: List[ReverseLogisticsMetrics] = []
        
        # Register message handlers
        self.register_handler(MessageType.RETURN_REQUESTED, self._handle_return_requested)
        self.register_handler(MessageType.ITEM_RECEIVED, self._handle_item_received)
        self.register_handler(MessageType.REFURBISHMENT_COMPLETED, self._handle_refurbishment_completed)
    
    async def initialize(self):
        """Initialize the Reverse Logistics Agent."""
        self.logger.info("Initializing Reverse Logistics Agent")
        
        # Initialize refurbishment capabilities
        await self._initialize_refurbishment_capabilities()
        
        # Load market data for resale optimization
        await self._load_market_data()
        
        # Start background tasks
        asyncio.create_task(self._process_return_queue())
        asyncio.create_task(self._monitor_refurbishment_tasks())
        asyncio.create_task(self._optimize_resale_strategies())
        asyncio.create_task(self._generate_performance_reports())
        
        self.logger.info("Reverse Logistics Agent initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up Reverse Logistics Agent")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process reverse logistics business logic."""
        action = data.get("action")
        
        if action == "process_return":
            return await self._process_return_request(data["return_data"])
        elif action == "assess_quality":
            return await self._assess_item_quality(data["return_id"])
        elif action == "create_refurbishment_task":
            return await self._create_refurbishment_task(data["assessment_id"])
        elif action == "get_resale_recommendation":
            return await self._get_resale_recommendation(data["product_id"], data["condition"])
        elif action == "get_metrics":
            return await self._get_performance_metrics(data.get("period_days", 30))
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def setup_routes(self):
        """Setup FastAPI routes for the Reverse Logistics Agent."""
        
        @self.app.post("/returns", response_model=APIResponse)
        async def process_return_request(return_data: ReturnRequest):
            """Process a return request."""
            try:
                result = await self._process_return_request(return_data.dict())
                
                return APIResponse(
                    success=True,
                    message="Return request processed successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to process return request", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/returns/{return_id}/assess", response_model=APIResponse)
        async def assess_item_quality(return_id: str):
            """Assess quality of returned item."""
            try:
                result = await self._assess_item_quality(return_id)
                
                return APIResponse(
                    success=True,
                    message="Quality assessment completed successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to assess item quality", error=str(e), return_id=return_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/refurbishment", response_model=APIResponse)
        async def create_refurbishment_task(assessment_id: str):
            """Create refurbishment task based on quality assessment."""
            try:
                result = await self._create_refurbishment_task(assessment_id)
                
                return APIResponse(
                    success=True,
                    message="Refurbishment task created successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to create refurbishment task", error=str(e), assessment_id=assessment_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/resale-recommendation", response_model=APIResponse)
        async def get_resale_recommendation(product_id: str, condition: ItemCondition):
            """Get resale recommendation for a product."""
            try:
                result = await self._get_resale_recommendation(product_id, condition)
                
                return APIResponse(
                    success=True,
                    message="Resale recommendation generated successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to get resale recommendation", error=str(e), product_id=product_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/metrics", response_model=APIResponse)
        async def get_performance_metrics(period_days: int = 30):
            """Get reverse logistics performance metrics."""
            try:
                result = await self._get_performance_metrics(period_days)
                
                return APIResponse(
                    success=True,
                    message="Performance metrics retrieved successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to get performance metrics", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/returns", response_model=APIResponse)
        async def list_returns(status: Optional[str] = None):
            """List return requests with optional status filter."""
            try:
                returns = list(self.return_requests.values())
                
                if status:
                    returns = [r for r in returns if r.status == status]
                
                return APIResponse(
                    success=True,
                    message="Return requests retrieved successfully",
                    data={"returns": [r.dict() for r in returns]}
                )
            
            except Exception as e:
                self.logger.error("Failed to list returns", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/refurbishment/tasks", response_model=APIResponse)
        async def list_refurbishment_tasks(status: Optional[str] = None):
            """List refurbishment tasks with optional status filter."""
            try:
                tasks = list(self.refurbishment_tasks.values())
                
                if status:
                    tasks = [t for t in tasks if t.status == status]
                
                return APIResponse(
                    success=True,
                    message="Refurbishment tasks retrieved successfully",
                    data={"tasks": [t.dict() for t in tasks]}
                )
            
            except Exception as e:
                self.logger.error("Failed to list refurbishment tasks", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _process_return_request(self, return_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate a return request."""
        try:
            # Create return request
            return_request = ReturnRequest(
                return_id=return_data.get("return_id", str(uuid4())),
                order_id=return_data["order_id"],
                customer_id=return_data["customer_id"],
                product_id=return_data["product_id"],
                quantity=return_data["quantity"],
                return_reason=ReturnReason(return_data["return_reason"]),
                customer_description=return_data.get("customer_description", ""),
                requested_at=datetime.utcnow(),
                estimated_refund=return_data.get("estimated_refund", 0.0),
                return_deadline=datetime.utcnow() + timedelta(days=30)
            )
            
            # Validate return eligibility
            eligibility_result = await self._validate_return_eligibility(return_request)
            
            if eligibility_result["eligible"]:
                return_request.status = "approved"
                
                # Generate return label
                return_label = await self._generate_return_label(return_request)
                return_request.return_label_generated = True
                
                # Store return request
                self.return_requests[return_request.return_id] = return_request
                
                # Send confirmation to customer
                await self.send_message(
                    recipient_agent="customer_communication_agent",
                    message_type=MessageType.RETURN_APPROVED,
                    payload={
                        "return_id": return_request.return_id,
                        "customer_id": return_request.customer_id,
                        "return_label": return_label,
                        "return_deadline": return_request.return_deadline.isoformat()
                    }
                )
                
                self.logger.info("Return request approved", return_id=return_request.return_id)
                
                return {
                    "return_id": return_request.return_id,
                    "status": "approved",
                    "return_label": return_label,
                    "return_deadline": return_request.return_deadline.isoformat(),
                    "estimated_refund": return_request.estimated_refund
                }
            
            else:
                return_request.status = "rejected"
                self.return_requests[return_request.return_id] = return_request
                
                # Send rejection notification
                await self.send_message(
                    recipient_agent="customer_communication_agent",
                    message_type=MessageType.RETURN_REJECTED,
                    payload={
                        "return_id": return_request.return_id,
                        "customer_id": return_request.customer_id,
                        "rejection_reason": eligibility_result["reason"]
                    }
                )
                
                return {
                    "return_id": return_request.return_id,
                    "status": "rejected",
                    "reason": eligibility_result["reason"]
                }
        
        except Exception as e:
            self.logger.error("Failed to process return request", error=str(e))
            raise
    
    async def _validate_return_eligibility(self, return_request: ReturnRequest) -> Dict[str, Any]:
        """Validate if a return request is eligible."""
        try:
            # Check return window (30 days from purchase)
            # In production, this would check the actual order date
            order_date = datetime.utcnow() - timedelta(days=15)  # Simulated order date
            days_since_order = (datetime.utcnow() - order_date).days
            
            if days_since_order > 30:
                return {"eligible": False, "reason": "Return window expired (30 days)"}
            
            # Check return reason eligibility
            non_returnable_reasons = []  # Define non-returnable reasons if any
            
            if return_request.return_reason in non_returnable_reasons:
                return {"eligible": False, "reason": f"Returns not accepted for reason: {return_request.return_reason}"}
            
            # Check product eligibility (some products may not be returnable)
            # In production, this would check product return policy
            
            # Check if item was already returned
            existing_returns = [r for r in self.return_requests.values() 
                             if r.order_id == return_request.order_id and 
                                r.product_id == return_request.product_id and 
                                r.status in ["approved", "received", "processed"]]
            
            if existing_returns:
                return {"eligible": False, "reason": "Item already returned"}
            
            return {"eligible": True, "reason": "Return request approved"}
        
        except Exception as e:
            self.logger.error("Failed to validate return eligibility", error=str(e))
            return {"eligible": False, "reason": "Validation error"}
    
    async def _generate_return_label(self, return_request: ReturnRequest) -> Dict[str, Any]:
        """Generate return shipping label."""
        try:
            # In production, this would integrate with shipping carriers
            return_label = {
                "label_id": f"RL{return_request.return_id[-8:]}",
                "tracking_number": f"RT{uuid4().hex[:12].upper()}",
                "carrier": "Return Carrier",
                "service_type": "Ground Return",
                "label_url": f"https://returns.example.com/labels/{return_request.return_id}.pdf",
                "instructions": "Package item securely and attach this label"
            }
            
            return return_label
        
        except Exception as e:
            self.logger.error("Failed to generate return label", error=str(e))
            raise
    
    async def _assess_item_quality(self, return_id: str) -> Dict[str, Any]:
        """Assess the quality of a returned item using AI and manual inspection."""
        try:
            return_request = self.return_requests.get(return_id)
            if not return_request:
                raise ValueError(f"Return request {return_id} not found")
            
            # Simulate quality assessment process
            # In production, this would involve:
            # 1. Physical inspection by technicians
            # 2. Photo analysis using computer vision
            # 3. Functional testing
            # 4. Comparison with return reason
            
            # Use AI to analyze return reason and generate initial assessment
            ai_assessment = await self._ai_quality_assessment(return_request)
            
            # Create quality assessment record
            assessment = QualityAssessment(
                assessment_id=str(uuid4()),
                return_id=return_id,
                product_id=return_request.product_id,
                assessed_condition=ai_assessment["condition"],
                defects_found=ai_assessment["defects"],
                photos_taken=[],  # Would be populated with actual photo paths
                assessor_notes=ai_assessment["notes"],
                assessment_date=datetime.utcnow(),
                resale_value_estimate=ai_assessment["resale_value"],
                recommended_action=ai_assessment["recommended_action"],
                confidence_score=ai_assessment["confidence"]
            )
            
            # Store assessment
            self.quality_assessments[assessment.assessment_id] = assessment
            
            # Update return status
            return_request.status = "assessed"
            
            # Determine next steps based on assessment
            next_steps = await self._determine_next_steps(assessment)
            
            # Send assessment results
            await self.send_message(
                recipient_agent="monitoring_agent",
                message_type=MessageType.QUALITY_ASSESSMENT_COMPLETED,
                payload={
                    "assessment_id": assessment.assessment_id,
                    "return_id": return_id,
                    "condition": assessment.assessed_condition.value,
                    "resale_value": assessment.resale_value_estimate,
                    "recommended_action": assessment.recommended_action.value
                }
            )
            
            self.logger.info("Quality assessment completed", 
                           return_id=return_id,
                           condition=assessment.assessed_condition,
                           confidence=assessment.confidence_score)
            
            return {
                "assessment_id": assessment.assessment_id,
                "condition": assessment.assessed_condition.value,
                "defects_found": assessment.defects_found,
                "resale_value_estimate": assessment.resale_value_estimate,
                "recommended_action": assessment.recommended_action.value,
                "confidence_score": assessment.confidence_score,
                "next_steps": next_steps
            }
        
        except Exception as e:
            self.logger.error("Failed to assess item quality", error=str(e), return_id=return_id)
            raise
    
    async def _ai_quality_assessment(self, return_request: ReturnRequest) -> Dict[str, Any]:
        """Use AI to assist in quality assessment."""
        try:
            if not os.getenv("OPENAI_API_KEY"):
                return self._rule_based_quality_assessment(return_request)
            
            # Prepare AI prompt
            prompt = f"""
            Analyze this product return and provide a quality assessment:
            
            Product ID: {return_request.product_id}
            Return Reason: {return_request.return_reason.value}
            Customer Description: "{return_request.customer_description}"
            Quantity: {return_request.quantity}
            
            Based on the return reason and customer description, assess:
            1. Likely condition of the item
            2. Potential defects or issues
            3. Estimated resale value (as percentage of original price)
            4. Recommended refurbishment action
            
            Respond in JSON format:
            {{
                "condition": "new|like_new|good|fair|poor|defective|unrepairable",
                "defects": ["list", "of", "likely", "defects"],
                "notes": "Assessment notes",
                "resale_value_percent": 85,
                "recommended_action": "clean_only|minor_repair|major_repair|replace_parts|repackage|dispose|recycle",
                "confidence": 0.8
            }}
            """
            
            response = await chat_completion(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert quality assessor for returned e-commerce products."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=400
            )
            
            content = response["choices"][0]["message"]["content"]
            ai_result = json.loads(content)
            
            # Calculate resale value (assuming original price of €50 for simulation)
            original_price = 50.0
            resale_value = original_price * (ai_result.get("resale_value_percent", 50) / 100)
            
            return {
                "condition": ItemCondition(ai_result.get("condition", "good")),
                "defects": ai_result.get("defects", []),
                "notes": ai_result.get("notes", "AI-generated assessment"),
                "resale_value": resale_value,
                "recommended_action": RefurbishmentAction(ai_result.get("recommended_action", "clean_only")),
                "confidence": ai_result.get("confidence", 0.7)
            }
        
        except Exception as e:
            self.logger.error("AI quality assessment failed", error=str(e))
            return self._rule_based_quality_assessment(return_request)
    
    def _rule_based_quality_assessment(self, return_request: ReturnRequest) -> Dict[str, Any]:
        """Rule-based quality assessment as fallback."""
        # Simple rule-based assessment based on return reason
        assessment_rules = {
            ReturnReason.DEFECTIVE: {
                "condition": ItemCondition.DEFECTIVE,
                "defects": ["Manufacturing defect"],
                "resale_value": 10.0,
                "action": RefurbishmentAction.MAJOR_REPAIR
            },
            ReturnReason.DAMAGED_SHIPPING: {
                "condition": ItemCondition.FAIR,
                "defects": ["Shipping damage"],
                "resale_value": 30.0,
                "action": RefurbishmentAction.MINOR_REPAIR
            },
            ReturnReason.WRONG_ITEM: {
                "condition": ItemCondition.NEW,
                "defects": [],
                "resale_value": 45.0,
                "action": RefurbishmentAction.REPACKAGE
            },
            ReturnReason.CHANGED_MIND: {
                "condition": ItemCondition.LIKE_NEW,
                "defects": [],
                "resale_value": 42.0,
                "action": RefurbishmentAction.CLEAN_ONLY
            },
            ReturnReason.SIZE_ISSUE: {
                "condition": ItemCondition.LIKE_NEW,
                "defects": [],
                "resale_value": 42.0,
                "action": RefurbishmentAction.CLEAN_ONLY
            }
        }
        
        rule = assessment_rules.get(return_request.return_reason, assessment_rules[ReturnReason.CHANGED_MIND])
        
        return {
            "condition": rule["condition"],
            "defects": rule["defects"],
            "notes": f"Rule-based assessment for {return_request.return_reason.value}",
            "resale_value": rule["resale_value"],
            "recommended_action": rule["action"],
            "confidence": 0.6
        }
    
    async def _determine_next_steps(self, assessment: QualityAssessment) -> List[str]:
        """Determine next steps based on quality assessment."""
        next_steps = []
        
        if assessment.recommended_action == RefurbishmentAction.DISPOSE:
            next_steps.append("Schedule for disposal")
            next_steps.append("Update inventory as loss")
        elif assessment.recommended_action == RefurbishmentAction.RECYCLE:
            next_steps.append("Send to recycling facility")
            next_steps.append("Generate recycling certificate")
        elif assessment.recommended_action in [RefurbishmentAction.CLEAN_ONLY, RefurbishmentAction.REPACKAGE]:
            next_steps.append("Schedule basic refurbishment")
            next_steps.append("Prepare for resale")
        else:
            next_steps.append("Create refurbishment task")
            next_steps.append("Assign to technician")
        
        # Always process refund
        next_steps.append("Process customer refund")
        
        return next_steps
    
    async def _create_refurbishment_task(self, assessment_id: str) -> Dict[str, Any]:
        """Create refurbishment task based on quality assessment."""
        try:
            assessment = self.quality_assessments.get(assessment_id)
            if not assessment:
                raise ValueError(f"Assessment {assessment_id} not found")
            
            # Determine target condition and required actions
            target_condition, actions, estimated_cost, estimated_time = await self._plan_refurbishment(assessment)
            
            # Create refurbishment task
            task = RefurbishmentTask(
                task_id=str(uuid4()),
                return_id=assessment.return_id,
                product_id=assessment.product_id,
                current_condition=assessment.assessed_condition,
                target_condition=target_condition,
                required_actions=actions,
                estimated_cost=estimated_cost,
                estimated_time_hours=estimated_time
            )
            
            # Store task
            self.refurbishment_tasks[task.task_id] = task
            
            # Send task to refurbishment team
            await self.send_message(
                recipient_agent="monitoring_agent",
                message_type=MessageType.REFURBISHMENT_TASK_CREATED,
                payload={
                    "task_id": task.task_id,
                    "product_id": task.product_id,
                    "current_condition": task.current_condition.value,
                    "target_condition": task.target_condition.value,
                    "estimated_cost": task.estimated_cost,
                    "estimated_time": task.estimated_time_hours
                }
            )
            
            self.logger.info("Refurbishment task created", 
                           task_id=task.task_id,
                           product_id=task.product_id,
                           estimated_cost=task.estimated_cost)
            
            return task.dict()
        
        except Exception as e:
            self.logger.error("Failed to create refurbishment task", error=str(e), assessment_id=assessment_id)
            raise
    
    async def _plan_refurbishment(self, assessment: QualityAssessment) -> Tuple[ItemCondition, List[RefurbishmentAction], float, int]:
        """Plan refurbishment process based on assessment."""
        current_condition = assessment.assessed_condition
        
        # Define refurbishment plans
        refurbishment_plans = {
            ItemCondition.DEFECTIVE: {
                "target": ItemCondition.GOOD,
                "actions": [RefurbishmentAction.MAJOR_REPAIR, RefurbishmentAction.REPLACE_PARTS, RefurbishmentAction.CLEAN_ONLY],
                "cost": 25.0,
                "time": 4
            },
            ItemCondition.POOR: {
                "target": ItemCondition.GOOD,
                "actions": [RefurbishmentAction.MINOR_REPAIR, RefurbishmentAction.CLEAN_ONLY, RefurbishmentAction.REPACKAGE],
                "cost": 15.0,
                "time": 2
            },
            ItemCondition.FAIR: {
                "target": ItemCondition.GOOD,
                "actions": [RefurbishmentAction.MINOR_REPAIR, RefurbishmentAction.CLEAN_ONLY],
                "cost": 10.0,
                "time": 1
            },
            ItemCondition.GOOD: {
                "target": ItemCondition.LIKE_NEW,
                "actions": [RefurbishmentAction.CLEAN_ONLY, RefurbishmentAction.REPACKAGE],
                "cost": 5.0,
                "time": 0.5
            },
            ItemCondition.LIKE_NEW: {
                "target": ItemCondition.LIKE_NEW,
                "actions": [RefurbishmentAction.CLEAN_ONLY],
                "cost": 2.0,
                "time": 0.25
            }
        }
        
        plan = refurbishment_plans.get(current_condition, refurbishment_plans[ItemCondition.FAIR])
        
        return (
            plan["target"],
            plan["actions"],
            plan["cost"],
            plan["time"]
        )
    
    async def _get_resale_recommendation(self, product_id: str, condition: ItemCondition) -> Dict[str, Any]:
        """Get AI-powered resale recommendation."""
        try:
            # Analyze market conditions and product data
            market_analysis = await self._analyze_resale_market(product_id, condition)
            
            # Use AI to generate recommendation
            ai_recommendation = await self._ai_resale_recommendation(product_id, condition, market_analysis)
            
            if ai_recommendation:
                recommendation = ResaleRecommendation(
                    recommendation_id=str(uuid4()),
                    product_id=product_id,
                    current_condition=condition,
                    recommended_channel=ai_recommendation["channel"],
                    recommended_price=ai_recommendation["price"],
                    expected_margin=ai_recommendation["margin"],
                    confidence_score=ai_recommendation["confidence"],
                    reasoning=ai_recommendation["reasoning"],
                    market_analysis=market_analysis,
                    generated_at=datetime.utcnow()
                )
            else:
                # Fallback to rule-based recommendation
                recommendation = await self._rule_based_resale_recommendation(product_id, condition, market_analysis)
            
            # Store recommendation
            self.resale_recommendations[recommendation.recommendation_id] = recommendation
            
            return recommendation.dict()
        
        except Exception as e:
            self.logger.error("Failed to get resale recommendation", error=str(e), product_id=product_id)
            raise
    
    async def _analyze_resale_market(self, product_id: str, condition: ItemCondition) -> Dict[str, Any]:
        """Analyze market conditions for resale optimization."""
        try:
            # In production, this would analyze:
            # - Historical sales data
            # - Competitor pricing
            # - Market demand
            # - Seasonal trends
            # - Channel performance
            
            # Simulated market analysis
            import random
            
            return {
                "demand_level": random.choice(["low", "medium", "high"]),
                "competitor_count": random.randint(3, 15),
                "average_market_price": random.uniform(20.0, 45.0),
                "price_trend": random.choice(["declining", "stable", "increasing"]),
                "seasonal_factor": random.uniform(0.8, 1.2),
                "channel_performance": {
                    "main_store": random.uniform(0.6, 0.9),
                    "outlet_store": random.uniform(0.7, 0.95),
                    "refurbished_section": random.uniform(0.8, 0.98),
                    "third_party_marketplace": random.uniform(0.5, 0.85)
                }
            }
        
        except Exception as e:
            self.logger.error("Failed to analyze resale market", error=str(e))
            if not self._db_initialized:
            return {}
        
        async with self.db_manager.get_session() as session:
            record = await self.db_helper.get_by_id(session, OrderDB, record_id)
            return self.db_helper.to_dict(record) if record else {}
    
    async def _ai_resale_recommendation(self, product_id: str, condition: ItemCondition, market_analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Use AI to generate resale recommendation."""
        try:
            if not os.getenv("OPENAI_API_KEY"):
                if not self._db_initialized:
            return None
        
        async with self.db_manager.get_session() as session:
            record = await self.db_helper.get_by_id(session, OrderDB, record_id)
            return self.db_helper.to_dict(record) if record else None
            
            prompt = f"""
            Generate an optimal resale recommendation for this returned product:
            
            Product ID: {product_id}
            Current Condition: {condition.value}
            
            Market Analysis:
            {json.dumps(market_analysis, indent=2)}
            
            Available Resale Channels:
            - main_store: Full-price retail channel
            - outlet_store: Discounted retail channel
            - refurbished_section: Dedicated refurbished products section
            - third_party_marketplace: External marketplace (Amazon, eBay, etc.)
            - wholesale: Bulk sales to retailers
            - liquidation: Quick sale at low prices
            
            Consider:
            1. Maximize revenue while ensuring quick sale
            2. Match condition to appropriate channel
            3. Account for market demand and competition
            4. Consider operational costs of each channel
            
            Respond in JSON format:
            {{
                "channel": "recommended_channel",
                "price": 35.99,
                "margin": 0.65,
                "reasoning": ["reason1", "reason2", "reason3"],
                "confidence": 0.85
            }}
            """
            
            response = await chat_completion(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert in e-commerce resale optimization and pricing strategy."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=400
            )
            
            content = response["choices"][0]["message"]["content"]
            ai_result = json.loads(content)
            
            return {
                "channel": ResaleChannel(ai_result.get("channel", "outlet_store")),
                "price": ai_result.get("price", 30.0),
                "margin": ai_result.get("margin", 0.6),
                "reasoning": ai_result.get("reasoning", ["AI-generated recommendation"]),
                "confidence": ai_result.get("confidence", 0.7)
            }
        
        except Exception as e:
            self.logger.error("AI resale recommendation failed", error=str(e))
            if not self._db_initialized:
            return None
        
        async with self.db_manager.get_session() as session:
            record = await self.db_helper.get_by_id(session, OrderDB, record_id)
            return self.db_helper.to_dict(record) if record else None
    
    async def _rule_based_resale_recommendation(self, product_id: str, condition: ItemCondition, market_analysis: Dict[str, Any]) -> ResaleRecommendation:
        """Rule-based resale recommendation as fallback."""
        # Simple rule-based recommendations
        condition_rules = {
            ItemCondition.NEW: {
                "channel": ResaleChannel.MAIN_STORE,
                "price_factor": 0.95,
                "margin": 0.8
            },
            ItemCondition.LIKE_NEW: {
                "channel": ResaleChannel.REFURBISHED_SECTION,
                "price_factor": 0.85,
                "margin": 0.75
            },
            ItemCondition.GOOD: {
                "channel": ResaleChannel.OUTLET_STORE,
                "price_factor": 0.7,
                "margin": 0.65
            },
            ItemCondition.FAIR: {
                "channel": ResaleChannel.THIRD_PARTY_MARKETPLACE,
                "price_factor": 0.5,
                "margin": 0.5
            },
            ItemCondition.POOR: {
                "channel": ResaleChannel.LIQUIDATION,
                "price_factor": 0.3,
                "margin": 0.3
            }
        }
        
        rule = condition_rules.get(condition, condition_rules[ItemCondition.GOOD])
        
        # Base price (simulated)
        base_price = 50.0
        recommended_price = base_price * rule["price_factor"]
        
        return ResaleRecommendation(
            recommendation_id=str(uuid4()),
            product_id=product_id,
            current_condition=condition,
            recommended_channel=rule["channel"],
            recommended_price=recommended_price,
            expected_margin=rule["margin"],
            confidence_score=0.6,
            reasoning=[f"Rule-based recommendation for {condition.value} condition"],
            market_analysis=market_analysis,
            generated_at=datetime.utcnow()
        )
    
    async def _get_performance_metrics(self, period_days: int = 30) -> Dict[str, Any]:
        """Get reverse logistics performance metrics."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # Filter data for the period
            period_returns = [r for r in self.return_requests.values() 
                            if start_date <= r.requested_at <= end_date]
            
            period_assessments = [a for a in self.quality_assessments.values() 
                                if start_date <= a.assessment_date <= end_date]
            
            period_tasks = [t for t in self.refurbishment_tasks.values() 
                          if t.started_at and start_date <= t.started_at <= end_date]
            
            # Calculate metrics
            total_returns = len(period_returns)
            returns_processed = len([r for r in period_returns if r.status in ["processed", "completed"]])
            
            # Processing time calculation
            completed_returns = [r for r in period_returns if r.status == "processed"]
            if completed_returns:
                # Simulate processing times
                processing_times = [24, 48, 36, 72, 18, 60]  # hours
                avg_processing_time = sum(processing_times) / len(processing_times)
            else:
                avg_processing_time = 0
            
            # Refurbishment success rate
            completed_tasks = [t for t in period_tasks if t.status == "completed"]
            refurbishment_success_rate = (len(completed_tasks) / len(period_tasks) * 100) if period_tasks else 0
            
            # Resale rate (simulated)
            resale_rate = 75.0  # 75% of items successfully resold
            
            # Recovery value (simulated)
            total_recovery_value = sum(a.resale_value_estimate for a in period_assessments)
            
            # Cost per return (simulated)
            total_costs = sum(t.estimated_cost for t in period_tasks)
            cost_per_return = (total_costs / total_returns) if total_returns > 0 else 0
            
            # Customer satisfaction (simulated)
            customer_satisfaction = 4.2  # Out of 5
            
            metrics = ReverseLogisticsMetrics(
                period_start=start_date,
                period_end=end_date,
                total_returns=total_returns,
                returns_processed=returns_processed,
                average_processing_time_hours=avg_processing_time,
                refurbishment_success_rate=refurbishment_success_rate,
                resale_rate=resale_rate,
                total_recovery_value=total_recovery_value,
                cost_per_return=cost_per_return,
                customer_satisfaction_score=customer_satisfaction
            )
            
            return metrics.dict()
        
        except Exception as e:
            self.logger.error("Failed to get performance metrics", error=str(e))
            raise
    
    async def _initialize_refurbishment_capabilities(self):
        """Initialize refurbishment capabilities and resources."""
        try:
            # In production, this would initialize:
            # - Available technicians and their skills
            # - Refurbishment equipment and tools
            # - Parts inventory
            # - Quality standards and procedures
            
            self.logger.info("Refurbishment capabilities initialized")
        
        except Exception as e:
            self.logger.error("Failed to initialize refurbishment capabilities", error=str(e))
    
    async def _load_market_data(self):
        """Load market data for resale optimization."""
        try:
            # In production, this would load:
            # - Historical pricing data
            # - Competitor analysis
            # - Market trends
            # - Channel performance data
            
            self.logger.info("Market data loaded for resale optimization")
        
        except Exception as e:
            self.logger.error("Failed to load market data", error=str(e))
    
    async def _handle_return_requested(self, message: AgentMessage):
        """Handle return request messages."""
        payload = message.payload
        
        try:
            # Process the return request
            return_data = {
                "order_id": payload.get("order_id"),
                "customer_id": payload.get("customer_id"),
                "product_id": payload.get("product_id"),
                "quantity": payload.get("quantity", 1),
                "return_reason": payload.get("return_reason", "other"),
                "customer_description": payload.get("description", ""),
                "estimated_refund": payload.get("refund_amount", 0.0)
            }
            
            await self._process_return_request(return_data)
        
        except Exception as e:
            self.logger.error("Failed to handle return request", error=str(e))
    
    async def _handle_item_received(self, message: AgentMessage):
        """Handle item received notifications."""
        payload = message.payload
        return_id = payload.get("return_id")
        
        if return_id and return_id in self.return_requests:
            try:
                # Update return status
                self.return_requests[return_id].status = "received"
                
                # Trigger quality assessment
                await self._assess_item_quality(return_id)
            
            except Exception as e:
                self.logger.error("Failed to handle item received", error=str(e), return_id=return_id)
    
    async def _handle_refurbishment_completed(self, message: AgentMessage):
        """Handle refurbishment completion notifications."""
        payload = message.payload
        task_id = payload.get("task_id")
        final_condition = payload.get("final_condition")
        actual_cost = payload.get("actual_cost")
        
        if task_id and task_id in self.refurbishment_tasks:
            try:
                task = self.refurbishment_tasks[task_id]
                task.status = "completed"
                task.completed_at = datetime.utcnow()
                task.final_condition = ItemCondition(final_condition) if final_condition else task.target_condition
                task.actual_cost = actual_cost or task.estimated_cost
                
                # Generate resale recommendation
                await self._get_resale_recommendation(task.product_id, task.final_condition)
                
                # Send completion notification
                await self.send_message(
                    recipient_agent="inventory_agent",
                    message_type=MessageType.ITEM_READY_FOR_RESALE,
                    payload={
                        "product_id": task.product_id,
                        "condition": task.final_condition.value,
                        "refurbishment_cost": task.actual_cost
                    }
                )
            
            except Exception as e:
                self.logger.error("Failed to handle refurbishment completion", error=str(e), task_id=task_id)
    
    async def _process_return_queue(self):
        """Background task to process return queue."""
        while not self.shutdown_event.is_set():
            try:
                # Process pending returns
                pending_returns = [r for r in self.return_requests.values() if r.status == "approved"]
                
                for return_request in pending_returns:
                    # Check if return deadline is approaching
                    days_until_deadline = (return_request.return_deadline - datetime.utcnow()).days
                    
                    if days_until_deadline <= 3:
                        # Send reminder to customer
                        await self.send_message(
                            recipient_agent="customer_communication_agent",
                            message_type=MessageType.RETURN_REMINDER,
                            payload={
                                "return_id": return_request.return_id,
                                "customer_id": return_request.customer_id,
                                "days_remaining": days_until_deadline
                            }
                        )
                
                # Sleep for 6 hours before next check
                await asyncio.sleep(6 * 3600)
            
            except Exception as e:
                self.logger.error("Error processing return queue", error=str(e))
                await asyncio.sleep(3600)  # Wait 1 hour on error
    
    async def _monitor_refurbishment_tasks(self):
        """Background task to monitor refurbishment tasks."""
        while not self.shutdown_event.is_set():
            try:
                # Monitor task progress every 2 hours
                await asyncio.sleep(2 * 3600)
                
                if not self.shutdown_event.is_set():
                    # Check for overdue tasks
                    current_time = datetime.utcnow()
                    
                    for task in self.refurbishment_tasks.values():
                        if (task.status == "in_progress" and 
                            task.started_at and 
                            (current_time - task.started_at).total_seconds() > task.estimated_time_hours * 3600 * 1.5):
                            
                            # Task is overdue
                            await self.send_message(
                                recipient_agent="monitoring_agent",
                                message_type=MessageType.RISK_ALERT,
                                payload={
                                    "alert_type": "refurbishment_overdue",
                                    "task_id": task.task_id,
                                    "product_id": task.product_id,
                                    "estimated_hours": task.estimated_time_hours,
                                    "actual_hours": (current_time - task.started_at).total_seconds() / 3600,
                                    "severity": "warning"
                                }
                            )
            
            except Exception as e:
                self.logger.error("Error monitoring refurbishment tasks", error=str(e))
                await asyncio.sleep(3600)  # Wait 1 hour on error
    
    async def _optimize_resale_strategies(self):
        """Background task to optimize resale strategies."""
        while not self.shutdown_event.is_set():
            try:
                # Optimize strategies every 24 hours
                await asyncio.sleep(24 * 3600)
                
                if not self.shutdown_event.is_set():
                    # Analyze resale performance and adjust strategies
                    performance_data = await self._analyze_resale_performance()
                    
                    # Send optimization recommendations
                    await self.send_message(
                        recipient_agent="monitoring_agent",
                        message_type=MessageType.OPTIMIZATION_RECOMMENDATION,
                        payload={
                            "optimization_type": "resale_strategy",
                            "performance_data": performance_data,
                            "recommendations": await self._generate_optimization_recommendations(performance_data)
                        }
                    )
            
            except Exception as e:
                self.logger.error("Error optimizing resale strategies", error=str(e))
                await asyncio.sleep(12 * 3600)  # Wait 12 hours on error
    
    async def _analyze_resale_performance(self) -> Dict[str, Any]:
        """Analyze resale performance across channels."""
        # Simulated performance analysis
        return {
            "channel_performance": {
                "main_store": {"sales": 45, "revenue": 2250.0, "margin": 0.8},
                "outlet_store": {"sales": 78, "revenue": 3120.0, "margin": 0.65},
                "refurbished_section": {"sales": 62, "revenue": 2480.0, "margin": 0.75},
                "third_party_marketplace": {"sales": 34, "revenue": 1020.0, "margin": 0.5}
            },
            "condition_performance": {
                "like_new": {"avg_sale_time": 3.2, "success_rate": 0.95},
                "good": {"avg_sale_time": 7.8, "success_rate": 0.87},
                "fair": {"avg_sale_time": 15.6, "success_rate": 0.72}
            }
        }
    
    async def _generate_optimization_recommendations(self, performance_data: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on performance data."""
        recommendations = []
        
        # Analyze channel performance
        channel_perf = performance_data.get("channel_performance", {})
        
        # Find best performing channel
        best_channel = max(channel_perf.items(), key=lambda x: x[1]["revenue"])
        recommendations.append(f"Focus more inventory on {best_channel[0]} - highest revenue channel")
        
        # Find underperforming channels
        avg_margin = sum(ch["margin"] for ch in channel_perf.values()) / len(channel_perf)
        for channel, perf in channel_perf.items():
            if perf["margin"] < avg_margin * 0.8:
                recommendations.append(f"Review pricing strategy for {channel} - below average margin")
        
        return recommendations
    
    async def _generate_performance_reports(self):
        """Background task to generate performance reports."""
        while not self.shutdown_event.is_set():
            try:
                # Generate reports every 7 days
                await asyncio.sleep(7 * 24 * 3600)
                
                if not self.shutdown_event.is_set():
                    # Generate weekly performance report
                    metrics = await self._get_performance_metrics(7)
                    
                    # Send report to monitoring agent
                    await self.send_message(
                        recipient_agent="monitoring_agent",
                        message_type=MessageType.PERFORMANCE_REPORT,
                        payload={
                            "report_type": "reverse_logistics_weekly",
                            "metrics": metrics,
                            "generated_at": datetime.utcnow().isoformat()
                        }
                    )
            
            except Exception as e:
                self.logger.error("Error generating performance reports", error=str(e))
                await asyncio.sleep(24 * 3600)  # Wait 24 hours on error


# FastAPI app instance for running the agent as a service
app = FastAPI(title="Reverse Logistics Agent", version="1.0.0")

# Global agent instance
reverse_logistics_agent: Optional[ReverseLogisticsAgent] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the Reverse Logistics Agent on startup."""
    global reverse_logistics_agent
    reverse_logistics_agent = ReverseLogisticsAgent()
    await reverse_logistics_agent.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup the Reverse Logistics Agent on shutdown."""
    global reverse_logistics_agent
    if reverse_logistics_agent:
        await reverse_logistics_agent.stop()


# Include agent routes
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if reverse_logistics_agent:
        health_status = reverse_logistics_agent.get_health_status()
        return {"status": "healthy", "agent_status": health_status.dict()}
    return {"status": "unhealthy", "message": "Agent not initialized"}


# Mount agent's FastAPI app
app.mount("/api/v1", reverse_logistics_agent.app if reverse_logistics_agent else FastAPI())


if __name__ == "__main__":
    import uvicorn
    from shared.database import initialize_database_manager, DatabaseConfig
    import os
    
    # Initialize database
    db_config = DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "multi_agent_ecommerce"),
        username=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD")
        if not password:
            raise ValueError("Database password must be set in environment variables")
    )
    initialize_database_manager(db_config)
    
    # Run the agent
    uvicorn.run(
        "reverse_logistics_agent:app",
        host="0.0.0.0",
        port=8009,
        reload=False,
        log_level="info"
    )
