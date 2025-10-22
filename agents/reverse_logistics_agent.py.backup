
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
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import structlog
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

# Get the absolute path of the current file
current_file_path = os.path.abspath(__file__)

# Get the directory containing the current file
current_dir = os.path.dirname(current_file_path)

# Get the parent directory (project root)
project_root = os.path.dirname(current_dir)

# Add the project root to the Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.db_helpers import DatabaseHelper
from shared.database import DatabaseManager, get_database_manager
from shared.models import APIResponse
from shared.openai_helper import chat_completion
from shared.base_agent import BaseAgent, MessageType, AgentMessage

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
    
    def __init__(self, agent_id: str, agent_type: str = "reverse_logistics", **kwargs):
        """
        Initializes the ReverseLogisticsAgent.

        Args:
            agent_id (str): The unique identifier for the agent.
            agent_type (str): The type of the agent, defaults to 'reverse_logistics'.
            **kwargs: Additional keyword arguments to pass to the BaseAgent constructor.
        """
        super().__init__(agent_id=agent_id, **kwargs)
        self.app = FastAPI(title="Reverse Logistics Agent API", version="1.0.0")
        self.db_manager = get_database_manager()
        self.db_helper = DatabaseHelper(self.db_manager)
        self._db_initialized = False

        # Initialize data stores (these will be replaced by database operations)
        self.return_requests: Dict[str, ReturnRequest] = {}
        self.quality_assessments: Dict[str, QualityAssessment] = {}
        self.refurbishment_tasks: Dict[str, RefurbishmentTask] = {}
        self.resale_recommendations: Dict[str, ResaleRecommendation] = {}
        self.metrics_history: List[ReverseLogisticsMetrics] = []

        self.setup_routes()
        self.register_handler(MessageType.RETURN_REQUESTED, self._handle_return_requested)
        self.register_handler(MessageType.ITEM_RECEIVED, self._handle_item_received)
        self.register_handler(MessageType.REFURBISHMENT_COMPLETED, self._handle_refurbishment_completed)

    async def initialize(self):
        """Initialize the Reverse Logistics Agent, including database connection and background tasks."""
        self.logger.info("Initializing Reverse Logistics Agent")
        try:
            await self.db_manager.initialize_async()
            self._db_initialized = True
            self.logger.info("Database connected successfully.")

            await self._initialize_refurbishment_capabilities()
            await self._load_market_data()

            asyncio.create_task(self._process_return_queue())
            asyncio.create_task(self._monitor_refurbishment_tasks())
            asyncio.create_task(self._optimize_resale_strategies())
            asyncio.create_task(self._generate_performance_reports())

            self.logger.info("Reverse Logistics Agent initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Reverse Logistics Agent: {e}")
            sys.exit(1) # Exit if essential services like DB cannot be initialized

    async def cleanup(self):
        """Cleanup resources, including closing the database connection."""
        self.logger.info("Cleaning up Reverse Logistics Agent")
        try:
            await self.db_manager.close()
            self.logger.info("Database disconnected successfully.")
        except Exception as e:
            self.logger.error(f"Error during database disconnection: {e}")

    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process reverse logistics business logic based on the given action.

        Args:
            data (Dict[str, Any]): A dictionary containing the action and relevant data.

        Returns:
            Dict[str, Any]: The result of the business logic operation.

        Raises:
            ValueError: If an unknown action is provided.
        """
        action = data.get("action")
        try:
            if action == "process_return":
                return await self._process_return_request(ReturnRequest(**data["return_data"]))
            elif action == "assess_quality":
                return await self._assess_item_quality(data["return_id"])
            elif action == "create_refurbishment_task":
                return await self._create_refurbishment_task(data["assessment_id"])
            elif action == "get_resale_recommendation":
                return await self._get_resale_recommendation(data["product_id"], ItemCondition(data["condition"]))
            elif action == "get_metrics":
                return await self._get_performance_metrics(data.get("period_days", 30))
            else:
                raise ValueError(f"Unknown action: {action}")
        except Exception as e:
            self.logger.error(f"Error processing business logic for action {action}: {e}")
            raise

    def setup_routes(self):
        """Setup FastAPI routes for the Reverse Logistics Agent API."""
        @self.app.get("/health", response_model=Dict[str, str])
        async def health_check():
            """Health check endpoint."""
            return {"status": "ok"}

        @self.app.get("/", response_model=Dict[str, str])
        async def root():
            """Root endpoint providing basic agent information."""
            return {"message": "Reverse Logistics Agent is running", "agent_id": self.agent_id}

        @self.app.post("/returns", response_model=APIResponse)
        async def process_return_request_api(return_data: ReturnRequest):
            """Process a return request via API.

            Args:
                return_data (ReturnRequest): The return request data.

            Returns:
                APIResponse: The API response indicating success or failure.
            """
            try:
                result = await self._process_return_request(return_data)
                return APIResponse(
                    success=True,
                    message="Return request processed successfully",
                    data=result
                )
            except Exception as e:
                self.logger.error("Failed to process return request via API", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/returns/{return_id}/assess", response_model=APIResponse)
        async def assess_item_quality_api(return_id: str):
            """Assess quality of returned item via API.

            Args:
                return_id (str): The ID of the return request.

            Returns:
                APIResponse: The API response indicating success or failure.
            """
            try:
                result = await self._assess_item_quality(return_id)
                return APIResponse(
                    success=True,
                    message="Quality assessment completed successfully",
                    data=result
                )
            except Exception as e:
                self.logger.error("Failed to assess item quality via API", error=str(e), return_id=return_id)
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/refurbishment", response_model=APIResponse)
        async def create_refurbishment_task_api(assessment_id: str):
            """Create a refurbishment task via API.

            Args:
                assessment_id (str): The ID of the quality assessment.

            Returns:
                APIResponse: The API response indicating success or failure.
            """
            try:
                result = await self._create_refurbishment_task(assessment_id)
                return APIResponse(
                    success=True,
                    message="Refurbishment task created successfully",
                    data=result
                )
            except Exception as e:
                self.logger.error("Failed to create refurbishment task via API", error=str(e), assessment_id=assessment_id)
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/resale-recommendation/{product_id}/{condition}", response_model=APIResponse)
        async def get_resale_recommendation_api(product_id: str, condition: ItemCondition):
            """Get resale recommendation via API.

            Args:
                product_id (str): The ID of the product.
                condition (ItemCondition): The condition of the item.

            Returns:
                APIResponse: The API response indicating success or failure.
            """
            try:
                result = await self._get_resale_recommendation(product_id, condition)
                return APIResponse(
                    success=True,
                    message="Resale recommendation generated successfully",
                    data=result
                )
            except Exception as e:
                self.logger.error("Failed to get resale recommendation via API", error=str(e), product_id=product_id, condition=condition.value)
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/metrics", response_model=APIResponse)
        async def get_performance_metrics_api(period_days: int = 30):
            """Get reverse logistics performance metrics via API.

            Args:
                period_days (int): The number of days for which to retrieve metrics.

            Returns:
                APIResponse: The API response indicating success or failure.
            """
            try:
                result = await self._get_performance_metrics(period_days)
                return APIResponse(
                    success=True,
                    message="Performance metrics retrieved successfully",
                    data=result
                )
            except Exception as e:
                self.logger.error("Failed to get performance metrics via API", error=str(e), period_days=period_days)
                raise HTTPException(status_code=500, detail=str(e))

    async def _process_return_request(self, return_data: ReturnRequest) -> Dict[str, Any]:
        """Processes a new return request, generates a return label, and stores it in the database.

        Args:
            return_data (ReturnRequest): The return request data.

        Returns:
            Dict[str, Any]: A dictionary containing the return ID and return label information.

        Raises:
            SQLAlchemyError: If there is an issue with database operations.
        """
        if not self._db_initialized: 
            self.logger.warning("Database not initialized. Cannot process return request.")
            return {"error": "Database not initialized"}

        try:
            return_id = str(uuid4())
            return_data.return_id = return_id
            return_data.requested_at = datetime.utcnow()
            return_data.return_deadline = datetime.utcnow() + timedelta(days=int(os.getenv("RETURN_DEADLINE_DAYS", 30)))
            
            async with self.db_manager.get_session() as session:
                await self.db_helper.create(session, return_data.dict(), "return_requests")

            return_label = await self._generate_return_label(return_data)

            self.logger.info("Return request processed", return_id=return_id, customer_id=return_data.customer_id)
            return {"return_id": return_id, "return_label": return_label}
        except SQLAlchemyError as e:
            self.logger.error(f"Database error processing return request: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to process return request: {e}")
            raise

    async def _generate_return_label(self, return_request: ReturnRequest) -> Dict[str, Any]:
        """Generates a simulated return label.

        Args:
            return_request (ReturnRequest): The return request for which to generate a label.

        Returns:
            Dict[str, Any]: A dictionary containing return label details.
        """
        try:
            tracking_number = f"RTN-{str(uuid4())[:8].upper()}"
            return_label = {
                "tracking_number": tracking_number,
                "carrier": os.getenv("RETURN_CARRIER", "UPS"),
                "instructions": "Print this label and attach to package. Drop off at nearest carrier location.",
                "valid_until": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
            return return_label
        except Exception as e:
            self.logger.error(f"Failed to generate return label: {e}")
            raise

    async def _assess_item_quality(self, return_id: str) -> Dict[str, Any]:
        """Assess the quality of a returned item using AI and manual inspection.

        Args:
            return_id (str): The ID of the return request to assess.

        Returns:
            Dict[str, Any]: A dictionary containing the quality assessment details.

        Raises:
            ValueError: If the return request is not found.
            SQLAlchemyError: If there is an issue with database operations.
        """
        if not self._db_initialized: 
            self.logger.warning("Database not initialized. Cannot assess item quality.")
            return {"error": "Database not initialized"}

        try:
            async with self.db_manager.get_session() as session:
                return_request_data = await self.db_helper.get_by_id(session, "return_requests", return_id)
                if not return_request_data:
                    raise ValueError(f"Return request {return_id} not found")
                return_request = ReturnRequest(**return_request_data)

            ai_assessment = await self._ai_quality_assessment(return_request)

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

            async with self.db_manager.get_session() as session:
                await self.db_helper.create(session, assessment.dict(), "quality_assessments")
                await self.db_helper.update(session, "return_requests", return_id, {"status": "assessed"})

            next_steps = await self._determine_next_steps(assessment)

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
        except SQLAlchemyError as e:
            self.logger.error(f"Database error assessing item quality: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to assess item quality: {e}", return_id=return_id)
            raise

    async def _ai_quality_assessment(self, return_request: ReturnRequest) -> Dict[str, Any]:
        """Uses AI to assist in quality assessment.

        Args:
            return_request (ReturnRequest): The return request to assess.

        Returns:
            Dict[str, Any]: A dictionary containing the AI-generated assessment.
        """
        try:
            if not os.getenv("OPENAI_API_KEY"):
                self.logger.warning("OPENAI_API_KEY not set. Falling back to rule-based assessment.")
                return self._rule_based_quality_assessment(return_request)

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
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                messages=[
                    {"role": "system", "content": "You are an expert quality assessor for returned e-commerce products."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=400
            )
            
            content = response["choices"][0]["message"]["content"]
            ai_result = json.loads(content)
            
            original_price = float(os.getenv("DEFAULT_PRODUCT_PRICE", 50.0))
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
            self.logger.error(f"AI quality assessment failed, falling back to rule-based: {e}")
            return self._rule_based_quality_assessment(return_request)

    def _rule_based_quality_assessment(self, return_request: ReturnRequest) -> Dict[str, Any]:
        """Provides a rule-based quality assessment as a fallback when AI is unavailable or fails.

        Args:
            return_request (ReturnRequest): The return request to assess.

        Returns:
            Dict[str, Any]: A dictionary containing the rule-based assessment.
        """
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
            },
            ReturnReason.NOT_AS_DESCRIBED: {
                "condition": ItemCondition.POOR,
                "defects": ["Description mismatch"],
                "resale_value": 25.0,
                "action": RefurbishmentAction.MAJOR_REPAIR
            },
            ReturnReason.QUALITY_ISSUE: {
                "condition": ItemCondition.POOR,
                "defects": ["Quality issues reported"],
                "resale_value": 20.0,
                "action": RefurbishmentAction.MAJOR_REPAIR
            },
            ReturnReason.OTHER: {
                "condition": ItemCondition.GOOD,
                "defects": [],
                "resale_value": 35.0,
                "action": RefurbishmentAction.CLEAN_ONLY
            }
        }
        
        rule = assessment_rules.get(return_request.return_reason, assessment_rules[ReturnReason.OTHER])
        
        return {
            "condition": rule["condition"],
            "defects": rule["defects"],
            "notes": f"Rule-based assessment for {return_request.return_reason.value}",
            "resale_value": rule["resale_value"],
            "recommended_action": rule["action"],
            "confidence": 0.6
        }

    async def _determine_next_steps(self, assessment: QualityAssessment) -> List[str]:
        """Determines the next steps based on the quality assessment.

        Args:
            assessment (QualityAssessment): The quality assessment of the item.

        Returns:
            List[str]: A list of recommended next steps.
        """
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
        next_steps.append("Process customer refund")
        return next_steps

    async def _create_refurbishment_task(self, assessment_id: str) -> Dict[str, Any]:
        """Creates a refurbishment task based on a quality assessment and stores it in the database.

        Args:
            assessment_id (str): The ID of the quality assessment.

        Returns:
            Dict[str, Any]: A dictionary containing the created refurbishment task details.

        Raises:
            ValueError: If the assessment is not found.
            SQLAlchemyError: If there is an issue with database operations.
        """
        if not self._db_initialized: 
            self.logger.warning("Database not initialized. Cannot create refurbishment task.")
            return {"error": "Database not initialized"}

        try:
            async with self.db_manager.get_session() as session:
                assessment_data = await self.db_helper.get_by_id(session, "quality_assessments", assessment_id)
                if not assessment_data:
                    raise ValueError(f"Assessment {assessment_id} not found")
                assessment = QualityAssessment(**assessment_data)

            target_condition, actions, estimated_cost, estimated_time = await self._plan_refurbishment(assessment)

            task = RefurbishmentTask(
                task_id=str(uuid4()),
                return_id=assessment.return_id,
                product_id=assessment.product_id,
                current_condition=assessment.assessed_condition,
                target_condition=target_condition,
                required_actions=actions,
                estimated_cost=estimated_cost,
                estimated_time_hours=estimated_time,
                status="pending"
            )

            async with self.db_manager.get_session() as session:
                await self.db_helper.create(session, task.dict(), "refurbishment_tasks")

            self.logger.info("Refurbishment task created", task_id=task.task_id, product_id=task.product_id)
            return task.dict()
        except SQLAlchemyError as e:
            self.logger.error(f"Database error creating refurbishment task: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to create refurbishment task: {e}", assessment_id=assessment_id)
            raise

    async def _plan_refurbishment(self, assessment: QualityAssessment) -> Tuple[ItemCondition, List[RefurbishmentAction], float, int]:
        """Plans the refurbishment process based on the quality assessment.

        Args:
            assessment (QualityAssessment): The quality assessment of the item.

        Returns:
            Tuple[ItemCondition, List[RefurbishmentAction], float, int]: A tuple containing
            the target condition, required actions, estimated cost, and estimated time in hours.
        """
        try:
            target_condition = ItemCondition.LIKE_NEW
            actions = [assessment.recommended_action]
            estimated_cost = 0.0
            estimated_time = 0

            if assessment.recommended_action == RefurbishmentAction.CLEAN_ONLY:
                estimated_cost = 5.0
                estimated_time = 1
            elif assessment.recommended_action == RefurbishmentAction.MINOR_REPAIR:
                estimated_cost = 25.0
                estimated_time = 4
            elif assessment.recommended_action == RefurbishmentAction.MAJOR_REPAIR:
                estimated_cost = 75.0
                estimated_time = 12
            elif assessment.recommended_action == RefurbishmentAction.REPLACE_PARTS:
                estimated_cost = 100.0
                estimated_time = 16
            elif assessment.recommended_action == RefurbishmentAction.REPACKAGE:
                estimated_cost = 10.0
                estimated_time = 2
            elif assessment.recommended_action in [RefurbishmentAction.DISPOSE, RefurbishmentAction.RECYCLE]:
                target_condition = ItemCondition.UNREPAIRABLE
                estimated_cost = 0.0
                estimated_time = 0

            return target_condition, actions, estimated_cost, estimated_time
        except Exception as e:
            self.logger.error(f"Failed to plan refurbishment: {e}", assessment_id=assessment.assessment_id)
            raise

    async def _get_resale_recommendation(self, product_id: str, condition: ItemCondition) -> Dict[str, Any]:
        """Generates a resale recommendation for a product based on its condition.

        Args:
            product_id (str): The ID of the product.
            condition (ItemCondition): The current condition of the product.

        Returns:
            Dict[str, Any]: A dictionary containing the resale recommendation details.

        Raises:
            Exception: If there is an issue generating the recommendation.
        """
        try:
            # Simulate market analysis and pricing
            market_analysis = {
                "demand": "high",
                "competitor_prices": {"new": 100.0, "used": 70.0},
                "trends": "stable"
            }

            recommended_channel = ResaleChannel.MAIN_STORE
            recommended_price = 0.0
            expected_margin = 0.0

            if condition == ItemCondition.NEW:
                recommended_channel = ResaleChannel.MAIN_STORE
                recommended_price = 90.0
                expected_margin = 0.4
            elif condition == ItemCondition.LIKE_NEW:
                recommended_channel = ResaleChannel.REFURBISHED_SECTION
                recommended_price = 75.0
                expected_margin = 0.3
            elif condition == ItemCondition.GOOD:
                recommended_channel = ResaleChannel.OUTLET_STORE
                recommended_price = 60.0
                expected_margin = 0.25
            elif condition == ItemCondition.FAIR:
                recommended_channel = ResaleChannel.THIRD_PARTY_MARKETPLACE
                recommended_price = 40.0
                expected_margin = 0.15
            else:
                recommended_channel = ResaleChannel.LIQUIDATION
                recommended_price = 20.0
                expected_margin = 0.05

            recommendation = ResaleRecommendation(
                recommendation_id=str(uuid4()),
                product_id=product_id,
                current_condition=condition,
                recommended_channel=recommended_channel,
                recommended_price=recommended_price,
                expected_margin=expected_margin,
                confidence_score=0.85,
                reasoning=["Based on current market data and item condition"],
                market_analysis=market_analysis,
                generated_at=datetime.utcnow()
            )
            
            async with self.db_manager.get_session() as session:
                await self.db_helper.create(session, recommendation.dict(), "resale_recommendations")

            self.logger.info("Resale recommendation generated", product_id=product_id, channel=recommended_channel.value)
            return recommendation.dict()
        except SQLAlchemyError as e:
            self.logger.error(f"Database error getting resale recommendation: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to get resale recommendation: {e}", product_id=product_id, condition=condition.value)
            raise

    async def _get_performance_metrics(self, period_days: int = 30) -> Dict[str, Any]:
        """Retrieves reverse logistics performance metrics for a specified period.

        Args:
            period_days (int): The number of days for which to retrieve metrics.

        Returns:
            Dict[str, Any]: A dictionary containing the performance metrics.

        Raises:
            SQLAlchemyError: If there is an issue with database operations.
        """
        if not self._db_initialized: 
            self.logger.warning("Database not initialized. Cannot get performance metrics.")
            return {"error": "Database not initialized"}

        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            async with self.db_manager.get_session() as session:
                all_returns_data = await self.db_helper.get_all(session, "return_requests")
                all_assessments_data = await self.db_helper.get_all(session, "quality_assessments")
                all_tasks_data = await self.db_helper.get_all(session, "refurbishment_tasks")

            period_returns = [ReturnRequest(**r) for r in all_returns_data 
                              if start_date <= r["requested_at"] <= end_date]
            period_assessments = [QualityAssessment(**a) for a in all_assessments_data 
                                  if start_date <= a["assessment_date"] <= end_date]
            period_tasks = [RefurbishmentTask(**t) for t in all_tasks_data 
                            if t.get("started_at") and start_date <= t["started_at"] <= end_date]

            total_returns = len(period_returns)
            returns_processed = len([r for r in period_returns if r.status in ["processed", "completed"]])

            avg_processing_time = 0.0
            if returns_processed > 0:
                # This would ideally come from actual processing time data
                avg_processing_time = sum([ (r.completed_at - r.requested_at).total_seconds() / 3600 
                                           for r in period_returns if r.status == "processed" and r.completed_at]) / returns_processed
            
            completed_tasks = [t for t in period_tasks if t.status == "completed"]
            refurbishment_success_rate = (len(completed_tasks) / len(period_tasks) * 100) if period_tasks else 0.0

            resale_rate = float(os.getenv("DEFAULT_RESALE_RATE", 75.0)) # Simulated

            total_recovery_value = sum(a.resale_value_estimate for a in period_assessments)

            total_costs = sum(t.actual_cost if t.actual_cost is not None else t.estimated_cost for t in period_tasks)
            cost_per_return = (total_costs / total_returns) if total_returns > 0 else 0.0

            customer_satisfaction = float(os.getenv("DEFAULT_CUSTOMER_SATISFACTION_SCORE", 4.2)) # Simulated

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

            self.logger.info("Performance metrics generated for period", start=start_date, end=end_date)
            return metrics.dict()
        except SQLAlchemyError as e:
            self.logger.error(f"Database error getting performance metrics: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {e}", period_days=period_days)
            raise

    async def _initialize_refurbishment_capabilities(self):
        """Initializes refurbishment capabilities and resources. This method simulates the setup of physical or digital resources needed for refurbishment operations.
        """
        try:
            self.logger.info("Refurbishment capabilities initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize refurbishment capabilities: {e}")
            raise

    async def _load_market_data(self):
        """Loads market data for resale optimization. This method simulates fetching and processing market data to inform resale strategies.
        """
        try:
            self.logger.info("Market data loaded for resale optimization")
        except Exception as e:
            self.logger.error(f"Failed to load market data: {e}")
            raise

    async def process_message(self, message: AgentMessage):
        """Processes incoming messages for the Reverse Logistics Agent.

        Args:
            message (AgentMessage): The incoming message to process.
        """
        self.logger.info(f"Received message: {message.message_type.value}")
        handler = self.get_handler(message.message_type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                self.logger.error(f"Error processing message type {message.message_type.value}: {e}")
        else:
            self.logger.warning(f"No handler registered for message type: {message.message_type.value}")

    async def _handle_return_requested(self, message: AgentMessage):
        """Handles messages indicating a return has been requested.

        Args:
            message (AgentMessage): The message containing return request payload.
        """
        payload = message.payload
        try:
            return_data = ReturnRequest(
                return_id=str(uuid4()), # Generate new ID as this is a new request
                order_id=payload.get("order_id"),
                customer_id=payload.get("customer_id"),
                product_id=payload.get("product_id"),
                quantity=payload.get("quantity", 1),
                return_reason=ReturnReason(payload.get("return_reason", "other")),
                customer_description=payload.get("description", ""),
                requested_at=datetime.utcnow(),
                estimated_refund=payload.get("refund_amount", 0.0),
                return_deadline=datetime.utcnow() + timedelta(days=int(os.getenv("RETURN_DEADLINE_DAYS", 30)))
            )
            await self._process_return_request(return_data)
            self.logger.info("Handled RETURN_REQUESTED message", return_id=return_data.return_id)
        except Exception as e:
            self.logger.error(f"Failed to handle RETURN_REQUESTED message: {e}", payload=payload)

    async def _handle_item_received(self, message: AgentMessage):
        """Handles messages indicating a returned item has been received.

        Args:
            message (AgentMessage): The message containing item received payload.
        """
        payload = message.payload
        return_id = payload.get("return_id")
        
        if not self._db_initialized: 
            self.logger.warning("Database not initialized. Cannot handle item received.")
            return

        if return_id:
            try:
                async with self.db_manager.get_session() as session:
                    # Update return status to 'received'
                    await self.db_helper.update(session, "return_requests", return_id, {"status": "received"})
                
                await self._assess_item_quality(return_id)
                self.logger.info("Handled ITEM_RECEIVED message", return_id=return_id)
            except Exception as e:
                self.logger.error(f"Failed to handle ITEM_RECEIVED message: {e}", return_id=return_id)
        else:
            self.logger.warning("ITEM_RECEIVED message missing return_id", payload=payload)

    async def _handle_refurbishment_completed(self, message: AgentMessage):
        """Handles messages indicating a refurbishment task has been completed.

        Args:
            message (AgentMessage): The message containing refurbishment completion payload.
        """
        payload = message.payload
        task_id = payload.get("task_id")
        final_condition_str = payload.get("final_condition")
        actual_cost = payload.get("actual_cost")

        if not self._db_initialized: 
            self.logger.warning("Database not initialized. Cannot handle refurbishment completed.")
            return

        if task_id:
            try:
                async with self.db_manager.get_session() as session:
                    task_data = await self.db_helper.get_by_id(session, "refurbishment_tasks", task_id)
                    if not task_data:
                        self.logger.warning(f"Refurbishment task {task_id} not found for completion.")
                        return
                    task = RefurbishmentTask(**task_data)

                    final_condition = ItemCondition(final_condition_str) if final_condition_str else task.target_condition

                    update_data = {
                        "status": "completed",
                        "completed_at": datetime.utcnow(),
                        "final_condition": final_condition.value,
                        "actual_cost": actual_cost or task.estimated_cost
                    }
                    await self.db_helper.update(session, "refurbishment_tasks", task_id, update_data)

                await self._get_resale_recommendation(task.product_id, final_condition)

                await self.send_message(
                    recipient_agent="inventory_agent",
                    message_type=MessageType.ITEM_READY_FOR_RESALE,
                    payload={
                        "product_id": task.product_id,
                        "condition": final_condition.value,
                        "refurbishment_cost": actual_cost or task.estimated_cost
                    }
                )
                self.logger.info("Handled REFURBISHMENT_COMPLETED message", task_id=task_id)
            except Exception as e:
                self.logger.error(f"Failed to handle REFURBISHMENT_COMPLETED message: {e}", task_id=task_id)
        else:
            self.logger.warning("REFURBISHMENT_COMPLETED message missing task_id", payload=payload)

    async def _process_return_queue(self):
        """Background task to periodically process pending return requests and send reminders.
        """
        while not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(int(os.getenv("RETURN_QUEUE_PROCESSING_INTERVAL_SECONDS", 21600))) # Default 6 hours
                if not self._db_initialized: 
                    self.logger.warning("Database not initialized. Skipping return queue processing.")
                    continue

                async with self.db_manager.get_session() as session:
                    all_returns_data = await self.db_helper.get_all(session, "return_requests")
                pending_returns = [ReturnRequest(**r) for r in all_returns_data if r["status"] == "approved"]

                for return_request in pending_returns:
                    days_until_deadline = (return_request.return_deadline - datetime.utcnow()).days
                    
                    if days_until_deadline <= int(os.getenv("RETURN_REMINDER_DAYS_BEFORE_DEADLINE", 3)):
                        await self.send_message(
                            recipient_agent="customer_communication_agent",
                            message_type=MessageType.RETURN_REMINDER,
                            payload={
                                "return_id": return_request.return_id,
                                "customer_id": return_request.customer_id,
                                "days_remaining": days_until_deadline
                            }
                        )
                self.logger.info("Return queue processed.")
            except Exception as e:
                self.logger.error(f"Error processing return queue: {e}")
                await asyncio.sleep(int(os.getenv("ERROR_RETRY_INTERVAL_SECONDS", 3600))) # Wait 1 hour on error

    async def _monitor_refurbishment_tasks(self):
        """Background task to monitor refurbishment tasks and alert on overdue tasks.
        """
        while not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(int(os.getenv("REFURBISHMENT_MONITOR_INTERVAL_SECONDS", 7200))) # Default 2 hours
                if not self._db_initialized: 
                    self.logger.warning("Database not initialized. Skipping refurbishment task monitoring.")
                    continue

                async with self.db_manager.get_session() as session:
                    all_tasks_data = await self.db_helper.get_all(session, "refurbishment_tasks")
                
                current_time = datetime.utcnow()
                for task_data in all_tasks_data:
                    task = RefurbishmentTask(**task_data)
                    if (task.status == "in_progress" and 
                        task.started_at and 
                        (current_time - task.started_at).total_seconds() > task.estimated_time_hours * 3600 * float(os.getenv("OVERDUE_TASK_MULTIPLIER", 1.5))):
                        
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
                self.logger.info("Refurbishment tasks monitored.")
            except Exception as e:
                self.logger.error(f"Error monitoring refurbishment tasks: {e}")
                await asyncio.sleep(int(os.getenv("ERROR_RETRY_INTERVAL_SECONDS", 3600))) # Wait 1 hour on error

    async def _optimize_resale_strategies(self):
        """Background task to periodically optimize resale strategies based on performance data.
        """
        while not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(int(os.getenv("RESALE_OPTIMIZATION_INTERVAL_SECONDS", 86400))) # Default 24 hours
                if not self._db_initialized: 
                    self.logger.warning("Database not initialized. Skipping resale optimization.")
                    continue

                performance_data = await self._analyze_resale_performance()
                
                await self.send_message(
                    recipient_agent="monitoring_agent",
                    message_type=MessageType.OPTIMIZATION_RECOMMENDATION,
                    payload={
                        "recommendation_type": "resale_strategy",
                        "details": "Adjust pricing and channel allocation based on recent performance",
                        "performance_summary": performance_data
                    }
                )
                self.logger.info("Resale strategies optimized.")
            except Exception as e:
                self.logger.error(f"Error optimizing resale strategies: {e}")
                await asyncio.sleep(int(os.getenv("ERROR_RETRY_INTERVAL_SECONDS", 3600))) # Wait 1 hour on error

    async def _analyze_resale_performance(self) -> Dict[str, Any]:
        """Analyzes historical resale performance to identify trends and areas for improvement.

        Returns:
            Dict[str, Any]: A summary of resale performance.
        """
        if not self._db_initialized: 
            self.logger.warning("Database not initialized. Cannot analyze resale performance.")
            return {"error": "Database not initialized"}

        try:
            async with self.db_manager.get_session() as session:
                recommendations_data = await self.db_helper.get_all(session, "resale_recommendations")
            
            total_recommendations = len(recommendations_data)
            if total_recommendations == 0:
                return {"message": "No resale recommendations to analyze."}

            # Simulate analysis
            successful_resales = len([r for r in recommendations_data if r.get("status") == "sold"])
            success_rate = (successful_resales / total_recommendations) * 100 if total_recommendations > 0 else 0
            avg_margin = sum([r.get("expected_margin", 0.0) for r in recommendations_data]) / total_recommendations

            return {
                "total_recommendations": total_recommendations,
                "successful_resales": successful_resales,
                "success_rate": success_rate,
                "average_margin": avg_margin,
                "analysis_date": datetime.utcnow().isoformat()
            }
        except SQLAlchemyError as e:
            self.logger.error(f"Database error analyzing resale performance: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to analyze resale performance: {e}")
            raise

    async def _generate_performance_reports(self):
        """Background task to periodically generate and store performance reports.
        """
        while not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(int(os.getenv("REPORT_GENERATION_INTERVAL_SECONDS", 86400))) # Default 24 hours
                if not self._db_initialized: 
                    self.logger.warning("Database not initialized. Skipping performance report generation.")
                    continue

                metrics = await self._get_performance_metrics(period_days=30) # Last 30 days
                # In a real system, these metrics would be stored in a dedicated reports table
                self.metrics_history.append(ReverseLogisticsMetrics(**metrics))

                await self.send_message(
                    recipient_agent="monitoring_agent",
                    message_type=MessageType.PERFORMANCE_REPORT,
                    payload={
                        "report_type": "reverse_logistics_monthly",
                        "metrics": metrics,
                        "generated_at": datetime.utcnow().isoformat()
                    }
                )
                self.logger.info("Performance report generated.")
            except Exception as e:
                self.logger.error(f"Error generating performance reports: {e}")
                await asyncio.sleep(int(os.getenv("ERROR_RETRY_INTERVAL_SECONDS", 3600))) # Wait 1 hour on error


if __name__ == "__main__":
    # Set environment variables for testing or default values
    os.environ.setdefault("AGENT_ID", "reverse_logistics_agent_001")
    os.environ.setdefault("AGENT_TYPE", "reverse_logistics")
    os.environ.setdefault("KAFKA_BROKER_URL", "localhost:9092")
    os.environ.setdefault("DB_URL", "sqlite:///./reverse_logistics.db")
    os.environ.setdefault("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY") # Replace with actual key or manage securely
    os.environ.setdefault("OPENAI_MODEL", "gpt-4.1-mini")
    os.environ.setdefault("RETURN_DEADLINE_DAYS", "30")
    os.environ.setdefault("DEFAULT_PRODUCT_PRICE", "50.0")
    os.environ.setdefault("DEFAULT_RESALE_RATE", "75.0")
    os.environ.setdefault("DEFAULT_CUSTOMER_SATISFACTION_SCORE", "4.2")
    os.environ.setdefault("RETURN_QUEUE_PROCESSING_INTERVAL_SECONDS", "21600")
    os.environ.setdefault("REFURBISHMENT_MONITOR_INTERVAL_SECONDS", "7200")
    os.environ.setdefault("RESALE_OPTIMIZATION_INTERVAL_SECONDS", "86400")
    os.environ.setdefault("REPORT_GENERATION_INTERVAL_SECONDS", "86400")
    os.environ.setdefault("ERROR_RETRY_INTERVAL_SECONDS", "3600")
    os.environ.setdefault("RETURN_CARRIER", "UPS")
    os.environ.setdefault("RETURN_REMINDER_DAYS_BEFORE_DEADLINE", "3")
    os.environ.setdefault("OVERDUE_TASK_MULTIPLIER", "1.5")

    agent_id = os.getenv("AGENT_ID")
    agent_type = os.getenv("AGENT_TYPE")
    kafka_broker_url = os.getenv("KAFKA_BROKER_URL")
    db_url = os.getenv("DB_URL")
    api_port = int(os.getenv("API_PORT", 8000))

    if not all([agent_id, agent_type, kafka_broker_url, db_url]):
        logger.error("Missing required environment variables. Exiting.")
        sys.exit(1)

    agent = ReverseLogisticsAgent(agent_id=agent_id, agent_type=agent_type, kafka_broker_url=kafka_broker_url)

    @agent.app.on_event("startup")
    async def startup_event():
        await agent.initialize()

    @agent.app.on_event("shutdown")
    async def shutdown_event():
        await agent.cleanup()

    import uvicorn
    uvicorn.run(agent.app, host="0.0.0.0", port=api_port)

