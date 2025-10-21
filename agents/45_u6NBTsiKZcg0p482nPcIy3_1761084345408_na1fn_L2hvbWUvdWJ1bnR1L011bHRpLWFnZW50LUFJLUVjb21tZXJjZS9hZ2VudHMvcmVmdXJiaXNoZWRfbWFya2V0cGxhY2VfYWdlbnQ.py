"""
Refurbished Marketplace Agent - Multi-Agent E-commerce System

This agent manages connections to specialized refurbished product marketplaces including:
- Back Market (refurbished electronics marketplace)
- Refurbed (European refurbished marketplace)
- Other specialized refurbished product platforms
- Product grading and condition management
- Specialized pricing strategies for refurbished items
- Quality certification and warranty handling
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4
from enum import Enum
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.db_helpers import DatabaseHelper
from shared.models import RefurbishedCredentialsDB, RefurbishedProductDB, RefurbishedOrderDB, QualityReportDB, MarketplaceOrderDB

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import structlog
import aiohttp
import sys
import os
from aiokafka import AIOKafkaProducer

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


class RefurbishedMarketplace(str, Enum):
    """Types of refurbished marketplaces."""
    BACK_MARKET = "back_market"
    REFURBED = "refurbed"
    SWAPPIE = "swappie"
    REBUY = "rebuy"
    RECOMMERCE = "recommerce"
    GENERIC_REFURB = "generic_refurb"


class ProductCondition(str, Enum):
    """Product condition grades for refurbished items."""
    # Back Market grading system
    EXCELLENT = "excellent"  # Like new, no visible wear
    VERY_GOOD = "very_good"  # Light signs of wear
    GOOD = "good"  # Moderate signs of wear
    CORRECT = "correct"  # Heavy signs of wear but fully functional
    
    # Additional conditions for other platforms
    GRADE_A = "grade_a"
    GRADE_B = "grade_b"
    GRADE_C = "grade_c"
    REFURBISHED = "refurbished"
    OPEN_BOX = "open_box"


class WarrantyType(str, Enum):
    """Types of warranties for refurbished products."""
    MARKETPLACE_WARRANTY = "marketplace_warranty"
    SELLER_WARRANTY = "seller_warranty"
    MANUFACTURER_WARRANTY = "manufacturer_warranty"
    EXTENDED_WARRANTY = "extended_warranty"
    NO_WARRANTY = "no_warranty"


class CertificationLevel(str, Enum):
    """Certification levels for refurbished products."""
    CERTIFIED = "certified"
    TESTED = "tested"
    BASIC = "basic"
    UNCERTIFIED = "uncertified"


class RefurbishedCredentials(BaseModel):
    """Model for refurbished marketplace API credentials."""
    marketplace_type: RefurbishedMarketplace
    marketplace_id: str
    api_key: str
    secret_key: Optional[str] = None
    seller_id: str
    api_endpoint: str
    additional_params: Dict[str, str] = {}
    active: bool = True
    last_sync: Optional[datetime] = None


class RefurbishedProduct(BaseModel):
    """Model for refurbished product listings."""
    listing_id: str
    marketplace_type: RefurbishedMarketplace
    marketplace_id: str
    product_id: str
    marketplace_product_id: Optional[str] = None
    
    # Basic product info
    title: str
    description: str
    brand: str
    model: str
    category: str
    sku: str
    
    # Condition and grading
    condition: ProductCondition
    condition_description: str
    aesthetic_grade: Optional[str] = None  # Platform-specific grading
    functional_grade: Optional[str] = None
    
    # Pricing
    price: float
    original_price: Optional[float] = None  # Original retail price
    currency: str = "EUR"
    
    # Inventory
    quantity: int
    
    # Technical specifications
    specifications: Dict[str, Any] = {}
    
    # Quality and warranty
    warranty_type: WarrantyType
    warranty_duration_months: int
    certification_level: CertificationLevel
    quality_checks: List[str] = []
    
    # Media
    images: List[str] = []
    videos: List[str] = []
    
    # Marketplace specific
    marketplace_category_id: Optional[str] = None
    shipping_profile: Optional[str] = None
    
    # Status and tracking
    status: str = "pending"  # pending, active, inactive, rejected
    created_at: datetime
    updated_at: datetime
    last_sync: Optional[datetime] = None


class RefurbishedOrder(BaseModel):
    """Model for refurbished marketplace orders."""
    order_id: str
    marketplace_type: RefurbishedMarketplace
    marketplace_id: str
    marketplace_order_id: str
    
    # Customer information
    customer_info: Dict[str, Any]
    
    # Order details
    items: List[Dict[str, Any]]
    total_amount: float
    currency: str = "EUR"
    
    # Order status
    status: str  # pending, confirmed, shipped, delivered, cancelled, returned
    order_date: datetime
    
    # Shipping and billing
    shipping_address: Dict[str, str]
    billing_address: Dict[str, str]
    shipping_method: str
    tracking_number: Optional[str] = None
    
    # Refurbished-specific
    warranty_activated: bool = False
    warranty_start_date: Optional[datetime] = None
    quality_guarantee: Optional[str] = None
    
    # Tracking
    last_sync: Optional[datetime] = None


class QualityReport(BaseModel):
    """Model for product quality reports."""
    report_id: str
    product_id: str
    listing_id: str
    
    # Quality assessment
    overall_condition: ProductCondition
    aesthetic_score: int  # 1-10 scale
    functional_score: int  # 1-10 scale
    
    # Detailed checks
    battery_health: Optional[int] = None  # Percentage for electronics
    screen_condition: Optional[str] = None
    body_condition: Optional[str] = None
    accessories_included: List[str] = []
    
    # Test results
    functional_tests: Dict[str, bool] = {}
    performance_benchmarks: Dict[str, Any] = {}
    
    # Certification
    certified_by: str
    certification_date: datetime
    certification_valid_until: Optional[datetime] = None
    
    # Notes
    inspector_notes: str
    customer_notes: Optional[str] = None


class RefurbishedMarketplaceAgent(BaseAgent):
    """
    Refurbished Marketplace Agent manages connections to specialized refurbished marketplaces including:
    - Back Market API integration with grading system
    - Refurbed platform integration
    - Product condition management and grading
    - Quality certification and warranty handling
    - Specialized pricing for refurbished items
    """
    
    def __init__(self,
                 agent_id: str = "refurbished_marketplace_agent",
                 agent_type: str = "refurbished_marketplace_agent",
                 **kwargs):
        """Initializes the RefurbishedMarketplaceAgent.

        Args:
            agent_id (str, optional): The unique identifier for the agent. Defaults to "refurbished_marketplace_agent".
            agent_type (str, optional): The type of the agent. Defaults to "refurbished_marketplace_agent".
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(agent_id=agent_id, agent_type=agent_type, **kwargs)
        self.db_manager = get_database_manager()
        self.db_helper = DatabaseHelper()
        self._db_initialized = False
        self.app = FastAPI(title="Refurbished Marketplace Agent API", version="1.0.0")
        self.setup_routes()
        
        # Refurbished marketplace data
        self.marketplace_credentials: Dict[str, RefurbishedCredentials] = {} # Stored in DB
        self.refurbished_products: Dict[str, RefurbishedProduct] = {} # Stored in DB
        self.refurbished_orders: Dict[str, RefurbishedOrder] = {} # Stored in DB
        self.quality_reports: Dict[str, QualityReport] = {} # Stored in DB
        
        # Grading systems for different marketplaces
        self.grading_systems = self._initialize_grading_systems()
        
        # Load Kafka topics from environment variables
        self.kafka_product_topic = os.getenv("KAFKA_PRODUCT_TOPIC", "product_updates")
        self.kafka_inventory_topic = os.getenv("KAFKA_INVENTORY_TOPIC", "inventory_updates")
        self.kafka_quality_topic = os.getenv("KAFKA_QUALITY_TOPIC", "quality_assessments")
        self.kafka_refurbishment_topic = os.getenv("KAFKA_REFURBISHMENT_TOPIC", "refurbishment_events")
        self.kafka_group_id = os.getenv("KAFKA_GROUP_ID", "refurbished_marketplace_group")

        self.kafka_producer = AIOKafkaProducer(bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"))

        # HTTP session for API calls
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Register message handlers
        self.register_handler(MessageType.PRODUCT_UPDATED, self._handle_product_updated)
        self.register_handler(MessageType.INVENTORY_UPDATED, self._handle_inventory_updated)
        self.register_handler(MessageType.QUALITY_ASSESSMENT_COMPLETED, self._handle_quality_assessment)
        self.register_handler(MessageType.REFURBISHMENT_COMPLETED, self._handle_refurbishment_completed)
    
    async def initialize(self):
        """Initializes the Refurbished Marketplace Agent.

        This method performs several asynchronous initialization steps:
        1. Initializes an aiohttp ClientSession for making HTTP requests.
        2. Starts the AIOKafkaProducer for publishing messages to Kafka topics.
        3. Initializes the database and loads existing marketplace credentials.
        4. Starts various background tasks for syncing orders, inventory, monitoring quality, and updating pricing.
        """
        self.logger.info("Initializing Refurbished Marketplace Agent")
        
        # Initialize HTTP session
        self.session = aiohttp.ClientSession()
        
        # Start Kafka producer
        await self.kafka_producer.start()

        # Load marketplace credentials
        await self._initialize_db()
        await self._load_refurbished_credentials_from_db()
        
        # Start background tasks
        asyncio.create_task(self._sync_refurbished_orders())
        asyncio.create_task(self._sync_refurbished_inventory())
        asyncio.create_task(self._monitor_quality_standards())
        asyncio.create_task(self._update_condition_pricing())
        
        self.logger.info("Refurbished Marketplace Agent initialized successfully")

    async def _on_shutdown(self):
        """Handles the shutdown process for the Refurbished Marketplace Agent.

        This method ensures that all active connections and resources are properly closed.
        Specifically, it closes the aiohttp client session and stops the AIOKafkaProducer,
        preventing resource leaks and ensuring a graceful shutdown.
        """
        self.logger.info("Shutting down Refurbished Marketplace Agent")
        if self.session:
            await self.session.close()
        if self.kafka_producer:
            await self.kafka_producer.stop()
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processes incoming business logic requests for the refurbished marketplace agent.

        This method acts as a central dispatcher for various business operations,
        delegating tasks based on the 'action' specified in the input data.

        Args:
            data (Dict[str, Any]): A dictionary containing the action to be performed
                                   and any relevant data for that action.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the processed action.
        
        Raises:
            HTTPException: If an unknown action is requested.
        """
        action = data.get("action")
        
        if action == "create_refurbished_listing":
            return await self._create_refurbished_listing(data["listing_data"])
        elif action == "update_condition_grade":
            return await self._update_condition_grade(data["listing_id"], data["new_condition"])
        elif action == "sync_orders":
            return await self._sync_orders(data["marketplace_id"])
        elif action == "generate_quality_report":
            return await self._generate_quality_report(data["product_id"], data["assessment_data"])
        elif action == "update_warranty_info":
            return await self._update_warranty_info(data["listing_id"], data["warranty_data"])
        elif action == "get_condition_pricing":
            return await self._get_condition_pricing_recommendations(data["product_id"])
        elif action == "validate_grading":
            return await self._validate_product_grading(data["listing_id"])
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def setup_routes(self):
        """Setup FastAPI routes for the Refurbished Marketplace Agent."""
        
        @self.app.post("/credentials", response_model=APIResponse)
        async def add_refurbished_credentials(credentials: RefurbishedCredentials):
            """Add refurbished marketplace API credentials."""
            try:
                # Validate credentials
                validation_result = await self._validate_refurbished_credentials(credentials)
                
                if validation_result["valid"]:
                    await self._save_refurbished_credentials(credentials)
                    
                    return APIResponse(
                        success=True,
                        message="Refurbished marketplace credentials added successfully",
                        data={"marketplace_id": credentials.marketplace_id, "validation": validation_result}
                    )
                else:
                    raise HTTPException(status_code=400, detail=f"Invalid credentials: {validation_result['error']}")
            
            except Exception as e:
                self.logger.error("Failed to add refurbished credentials", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/listings", response_model=APIResponse)
        async def create_refurbished_listing(listing_data: RefurbishedProduct):
    
            try:
                result = await self._create_refurbished_listing(listing_data.dict())
                
                return APIResponse(
                    success=True,
                    message="Refurbished listing created successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to create refurbished listing", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.put("/listings/{listing_id}/condition", response_model=APIResponse)
        async def update_condition_grade(listing_id: str, condition_data: Dict[str, Any]):
    
            try:
                result = await self._update_condition_grade(listing_id, condition_data)
                
                return APIResponse(
                    success=True,
                    message="Product condition updated successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to update condition grade", error=str(e), listing_id=listing_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/quality-reports", response_model=APIResponse)
        async def generate_quality_report(product_id: str, assessment_data: Dict[str, Any]):
    
            try:
                result = await self._generate_quality_report(product_id, assessment_data)
                
                return APIResponse(
                    success=True,
                    message="Quality report generated successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to generate quality report", error=str(e), product_id=product_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/pricing/condition/{product_id}", response_model=APIResponse)
        async def get_condition_pricing(product_id: str):
            """Get pricing recommendations based on product condition."""
            try:
                result = await self._get_condition_pricing_recommendations(product_id)
                
                return APIResponse(
                    success=True,
                    message="Condition pricing recommendations retrieved successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to get condition pricing", error=str(e), product_id=product_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/listings/{listing_id}/validate-grading", response_model=APIResponse)
        async def validate_grading(listing_id: str):
            """Validate product grading against marketplace standards."""
            try:
                result = await self._validate_product_grading(listing_id)
                
                return APIResponse(
                    success=True,
                    message="Product grading validated successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to validate grading", error=str(e), listing_id=listing_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/listings", response_model=APIResponse)
        async def list_refurbished_products(
            marketplace_id: Optional[str] = None,
            condition: Optional[ProductCondition] = None,
            status: Optional[str] = None
        ):
            """List refurbished product listings with filters."""
            try:
                async with self.db_manager.get_session() as session:
                    products_db = await self.db_helper.get_all(session, RefurbishedProductDB)
                    products = [RefurbishedProduct(**self.db_helper.to_dict(p)) for p in products_db]
                
                if marketplace_id:
                    products = [p for p in products if p.marketplace_id == marketplace_id]
                
                if condition:
                    products = [p for p in products if p.condition == condition]
                
                if status:
                    products = [p for p in products if p.status == status]
                
                return APIResponse(
                    success=True,
                    message="Refurbished products retrieved successfully",
                    data={"products": [p.dict() for p in products]}
                )
            
            except Exception as e:
                self.logger.error("Failed to list refurbished products", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/quality-reports", response_model=APIResponse)
        async def list_quality_reports(product_id: Optional[str] = None):
            """List quality reports with optional product filter."""
            try:
                async with self.db_manager.get_session() as session:
                    reports_db = await self.db_helper.get_all(session, QualityReportDB)
                    reports = [QualityReport(**self.db_helper.to_dict(r)) for r in reports_db]
                
                if product_id:
                    reports = [r for r in reports if r.product_id == product_id]
                
                return APIResponse(
                    success=True,
                    message="Quality reports retrieved successfully",
                    data={"reports": [r.dict() for r in reports]}
                )
            
            except Exception as e:
                self.logger.error("Failed to list quality reports", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
    
    def _initialize_grading_systems(self) -> Dict[str, Dict[str, Any]]:
        """Initialize grading systems for different marketplaces."""
        return {
            RefurbishedMarketplace.BACK_MARKET.value: {
                "conditions": {
                    ProductCondition.EXCELLENT.value: {
                        "name": "Excellent",
                        "description": "Like new condition with no visible signs of wear",
                        "aesthetic_score_min": 9,
                        "functional_score_min": 10,
                        "price_factor": 0.85
                    },
                    ProductCondition.VERY_GOOD.value: {
                        "name": "Very Good",
                        "description": "Light signs of wear that don't affect functionality",
                        "aesthetic_score_min": 7,
                        "functional_score_min": 9,
                        "price_factor": 0.75
                    },
                    ProductCondition.GOOD.value: {
                        "name": "Good",
                        "description": "Moderate signs of wear but fully functional",
                        "aesthetic_score_min": 5,
                        "functional_score_min": 8,
                        "price_factor": 0.65
                    },
                    ProductCondition.CORRECT.value: {
                        "name": "Correct",
                        "description": "Heavy signs of wear but fully functional",
                        "aesthetic_score_min": 3,
                        "functional_score_min": 7,
                        "price_factor": 0.55
                    }
                },
                "required_tests": ["battery_test", "screen_test", "connectivity_test", "camera_test"],
                "warranty_months": 12
            },
            RefurbishedMarketplace.REFURBED.value: {
                "conditions": {
                    ProductCondition.EXCELLENT.value: {
                        "name": "Like New",
                        "description": "Perfect condition, like new",
                        "aesthetic_score_min": 9,
                        "functional_score_min": 10,
                        "price_factor": 0.88
                    },
                    ProductCondition.VERY_GOOD.value: {
                        "name": "Very Good",
                        "description": "Minimal signs of use",
                        "aesthetic_score_min": 7,
                        "functional_score_min": 9,
                        "price_factor": 0.78
                    },
                    ProductCondition.GOOD.value: {
                        "name": "Good",
                        "description": "Visible signs of use but good condition",
                        "aesthetic_score_min": 5,
                        "functional_score_min": 8,
                        "price_factor": 0.68
                    }
                },
                "required_tests": ["functionality_test", "performance_test", "quality_check"],
                "warranty_months": 12
            }
        }
    
    async def _validate_refurbished_credentials(self, credentials: RefurbishedCredentials) -> Dict[str, Any]:
        """Validate refurbished marketplace API credentials."""
        try:
            if credentials.marketplace_type == RefurbishedMarketplace.BACK_MARKET:
                return await self._validate_back_market_credentials(credentials)
            elif credentials.marketplace_type == RefurbishedMarketplace.REFURBED:
                return await self._validate_refurbed_credentials(credentials)
            else:
                # Generic validation
                return {"valid": True, "message": "Credentials format validated"}
        
        except Exception as e:
            self.logger.error("Failed to validate refurbished credentials", error=str(e))
            return {"valid": False, "error": str(e)}
    
    async def _validate_back_market_credentials(self, credentials: RefurbishedCredentials) -> Dict[str, Any]:
        """Validate Back Market API credentials."""
        try:
            # Back Market API validation
            # In production, this would make a test API call
            
            if not credentials.api_key:
                return {"valid": False, "error": "API key is required for Back Market"}
            
            # Simulate API validation
            self.logger.info("Back Market credentials validated", seller_id=credentials.seller_id)
            
            return {"valid": True, "message": "Back Market credentials validated successfully"}
        
        except Exception as e:
            return {"valid": False, "error": f"Back Market validation failed: {str(e)}"}
    
    async def _validate_refurbed_credentials(self, credentials: RefurbishedCredentials) -> Dict[str, Any]:
        """Validate Refurbed API credentials."""
        try:
            # Refurbed API validation
            if not credentials.api_key:
                return {"valid": False, "error": "API key is required for Refurbed"}
            
            # Simulate API validation
            self.logger.info("Refurbed credentials validated", seller_id=credentials.seller_id)
            
            return {"valid": True, "message": "Refurbed credentials validated successfully"}
        
        except Exception as e:
            return {"valid": False, "error": f"Refurbed validation failed: {str(e)}"}
    
    async def _create_refurbished_listing(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new refurbished product listing in the marketplace.

        This method takes listing data, validates it, and then attempts to create
        a new product listing in the appropriate refurbished marketplace.

        Args:
            listing_data (Dict[str, Any]): A dictionary containing all necessary data
                                           to create a refurbished product listing.
                                           Expected keys include 'marketplace_type', 'product_id',
                                           'title', 'description', 'price', 'quantity', etc.

        Returns:
            Dict[str, Any]: A dictionary containing the status and details of the
                            newly created listing, including its `listing_id`.

        Raises:
            HTTPException: If required listing data is missing or if the marketplace
                           API call fails.
        """

        try:
            # Create refurbished product
            product = RefurbishedProduct(
                listing_id=listing_data.get("listing_id", str(uuid4())),
                marketplace_type=RefurbishedMarketplace(listing_data["marketplace_type"]),
                marketplace_id=listing_data["marketplace_id"],
                product_id=listing_data["product_id"],
                title=listing_data["title"],
                description=listing_data["description"],
                brand=listing_data["brand"],
                model=listing_data["model"],
                category=listing_data["category"],
                sku=listing_data["sku"],
                condition=ProductCondition(listing_data["condition"]),
                condition_description=listing_data.get("condition_description", ""),
                aesthetic_grade=listing_data.get("aesthetic_grade"),
                functional_grade=listing_data.get("functional_grade"),
                price=listing_data["price"],
                original_price=listing_data.get("original_price"),
                currency=listing_data.get("currency", "EUR"),
                quantity=listing_data["quantity"],
                specifications=listing_data.get("specifications", {}),
                warranty_type=WarrantyType(listing_data.get("warranty_type", "marketplace_warranty")),
                warranty_duration_months=listing_data.get("warranty_duration_months", 12),
                certification_level=CertificationLevel(listing_data.get("certification_level", "certified")),
                quality_checks=listing_data.get("quality_checks", []),
                images=listing_data.get("images", []),
                videos=listing_data.get("videos", []),
                marketplace_category_id=listing_data.get("marketplace_category_id"),
                shipping_profile=listing_data.get("shipping_profile"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Validate grading against marketplace standards
            grading_validation = await self._validate_product_grading_data(product)
            
            if not grading_validation["valid"]:
                raise ValueError(f"Invalid grading: {grading_validation['error']}")
            
            # Create listing on marketplace
            marketplace_result = await self._create_marketplace_refurbished_listing(product)
            
            if marketplace_result["success"]:
                product.marketplace_product_id = marketplace_result.get("marketplace_product_id")
                product.status = "active"
                product.last_sync = datetime.utcnow()
                
                # Store product
                await self._save_refurbished_product(product)
                
                # Send notification
                await self.send_message(
                    recipient_agent="product_agent",
                    message_type=MessageType.LISTING_CREATED,
                    payload={
                        "listing_id": product.listing_id,
                        "product_id": product.product_id,
                        "marketplace_type": product.marketplace_type.value,
                        "condition": product.condition.value,
                        "price": product.price
                    }
                )
                
                return product.dict()
            else:
                product.status = "rejected"
                self.refurbished_products[product.listing_id] = product
                raise Exception(f"Failed to create marketplace listing: {marketplace_result.get('error')}")
        
        except Exception as e:
            self.logger.error("Failed to create refurbished listing", error=str(e))
            raise
    
    async def _validate_product_grading_data(self, product: RefurbishedProduct) -> Dict[str, Any]:
        """Validates a product's grading against marketplace-specific standards.

        This method checks if the product's condition, aesthetic grade, and functional grade
        meet the minimum requirements defined by the grading system of its associated marketplace.

        Args:
            product (RefurbishedProduct): The refurbished product object to validate.

        Returns:
            Dict[str, Any]: A dictionary indicating whether the product grading is 'valid'
                            and a 'message' or 'error' detailing the validation result.
        """
        try:
            grading_system = self.grading_systems.get(product.marketplace_type.value)
            
            if not grading_system:
                return {"valid": True, "message": "No specific grading system found"}
            
            condition_requirements = grading_system["conditions"].get(product.condition.value)
            
            if not condition_requirements:
                return {"valid": False, "error": f"Invalid condition {product.condition.value} for {product.marketplace_type.value}"}
            
            # Check aesthetic grade if provided
            if product.aesthetic_grade:
                try:
                    aesthetic_score = int(product.aesthetic_grade)
                    min_aesthetic = condition_requirements.get("aesthetic_score_min", 0)
                    
                    if aesthetic_score < min_aesthetic:
                        return {
                            "valid": False,
                            "error": f"Aesthetic score {aesthetic_score} below minimum {min_aesthetic} for {product.condition.value}"
                        }
                except ValueError:
                    return {"valid": False, "error": "Invalid aesthetic grade format"}
            
            # Check functional grade if provided
            if product.functional_grade:
                try:
                    functional_score = int(product.functional_grade)
                    min_functional = condition_requirements.get("functional_score_min", 0)
                    
                    if functional_score < min_functional:
                        return {
                            "valid": False,
                            "error": f"Functional score {functional_score} below minimum {min_functional} for {product.condition.value}"
                        }
                except ValueError:
                    return {"valid": False, "error": "Invalid functional grade format"}
            
            return {"valid": True, "message": "Grading validation passed"}
        
        except Exception as e:
            self.logger.error("Failed to validate product grading", error=str(e))
            return {"valid": False, "error": str(e)}
    
    async def _create_marketplace_refurbished_listing(self, product: RefurbishedProduct) -> Dict[str, Any]:
        """Creates a listing for a refurbished product on a specific marketplace.

        This method acts as a dispatcher, routing the product creation request
        to the appropriate marketplace-specific method (e.g., Back Market, Refurbed)
        based on the `marketplace_type` specified in the product.

        Args:
            product (RefurbishedProduct): The refurbished product object containing
                                         all details necessary for listing.

        Returns:
            Dict[str, Any]: A dictionary containing the success status and any
                            marketplace-specific product ID or error messages.

        Raises:
            ValueError: If marketplace credentials are not found.
            Exception: If an error occurs during the marketplace-specific listing creation.
        """
        try:
            credentials = self.marketplace_credentials.get(product.marketplace_id)
            if not credentials:
                return {"success": False, "error": "Marketplace credentials not found"}
            
            if product.marketplace_type == RefurbishedMarketplace.BACK_MARKET:
                return await self._create_back_market_listing(product, credentials)
            elif product.marketplace_type == RefurbishedMarketplace.REFURBED:
                return await self._create_refurbed_listing(product, credentials)
            else:
                # Generic refurbished marketplace
                return await self._create_generic_refurbished_listing(product, credentials)
        
        except Exception as e:
            self.logger.error("Failed to create marketplace refurbished listing", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _create_back_market_listing(self, product: RefurbishedProduct, credentials: RefurbishedCredentials) -> Dict[str, Any]:
        """Creates a product listing on the Back Market platform.

        This method simulates the interaction with the Back Market API to create
        a new listing, mapping the internal product data to Back Market-specific
        fields and conditions.

        Args:
            product (RefurbishedProduct): The refurbished product object to be listed.
            credentials (RefurbishedCredentials): The API credentials for Back Market.

        Returns:
            Dict[str, Any]: A dictionary containing the success status and the
                            marketplace-specific product ID if successful, or an error message.

        Raises:
            Exception: If an error occurs during the simulated API call.
        """
        try:
            # Back Market API product creation
            # In production, this would use the actual Back Market API
            
            # Prepare Back Market specific data
            back_market_data = {
                "sku": product.sku,
                "title": product.title,
                "description": product.description,
                "brand": product.brand,
                "model": product.model,
                "condition": self._map_condition_to_back_market(product.condition),
                "price": product.price,
                "currency": product.currency,
                "quantity": product.quantity,
                "warranty_duration": product.warranty_duration_months,
                "images": product.images,
                "specifications": product.specifications,
                "aesthetic_grade": product.aesthetic_grade,
                "functional_grade": product.functional_grade
            }
            
            # Add Back Market specific fields
            if product.marketplace_category_id:
                back_market_data["category_id"] = product.marketplace_category_id
            
            # Simulate API call
            self.logger.info("Back Market listing created", 
                           sku=product.sku, 
                           condition=product.condition.value,
                           price=product.price)
            
            return {
                "success": True,
                "marketplace_product_id": f"BM_{product.sku}_{uuid4().hex[:8]}",
                "message": "Back Market listing created successfully"
            }
        
        except Exception as e:
            self.logger.error("Failed to create Back Market listing", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _create_refurbed_listing(self, product: RefurbishedProduct, credentials: RefurbishedCredentials) -> Dict[str, Any]:
        """Creates a product listing on the Refurbed platform.

        This method simulates the interaction with the Refurbed API to create
        a new listing, mapping the internal product data to Refurbed-specific
        fields and conditions.

        Args:
            product (RefurbishedProduct): The refurbished product object to be listed.
            credentials (RefurbishedCredentials): The API credentials for Refurbed.

        Returns:
            Dict[str, Any]: A dictionary containing the success status and the
                            marketplace-specific product ID if successful, or an error message.

        Raises:
            Exception: If an error occurs during the simulated API call.
        """
        try:
            # Refurbed API product creation
            refurbed_data = {
                "sku": product.sku,
                "name": product.title,
                "description": product.description,
                "brand": product.brand,
                "model": product.model,
                "condition": self._map_condition_to_refurbed(product.condition),
                "price": product.price,
                "currency": product.currency,
                "stock": product.quantity,
                "warranty_months": product.warranty_duration_months,
                "images": product.images,
                "technical_specs": product.specifications
            }
            
            # Simulate API call
            self.logger.info("Refurbed listing created", 
                           sku=product.sku, 
                           condition=product.condition.value,
                           price=product.price)
            
            return {
                "success": True,
                "marketplace_product_id": f"RF_{product.sku}_{uuid4().hex[:8]}",
                "message": "Refurbed listing created successfully"
            }
        
        except Exception as e:
            self.logger.error("Failed to create Refurbed listing", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _create_generic_refurbished_listing(self, product: RefurbishedProduct, credentials: RefurbishedCredentials) -> Dict[str, Any]:
        """Creates a product listing on a generic refurbished marketplace.

        This method handles the creation of listings for marketplaces that do not
        have a specific integration method. It logs the creation and returns a
        simulated marketplace product ID.

        Args:
            product (RefurbishedProduct): The refurbished product object to be listed.
            credentials (RefurbishedCredentials): The API credentials for the generic marketplace.

        Returns:
            Dict[str, Any]: A dictionary containing the success status and the
                            simulated marketplace-specific product ID.

        Raises:
            Exception: If an error occurs during the simulated listing creation.
        """
        try:
            self.logger.info("Generic refurbished listing created", 
                           marketplace=product.marketplace_type.value,
                           sku=product.sku, 
                           condition=product.condition.value)
            
            return {
                "success": True,
                "marketplace_product_id": f"{product.marketplace_type.value.upper()}_{product.sku}",
                "message": f"{product.marketplace_type.value} listing created successfully"
            }
        
        except Exception as e:
            self.logger.error("Failed to create generic refurbished listing", error=str(e))
            return {"success": False, "error": str(e)}
    
    def _map_condition_to_back_market(self, condition: ProductCondition) -> str:
        """Maps an internal `ProductCondition` enum to its corresponding string representation
        used by the Back Market platform.

        Args:
            condition (ProductCondition): The internal product condition enum value.

        Returns:
            str: The Back Market-specific string representation of the condition.
                 Defaults to "good" if no direct mapping is found.
        """
        mapping = {
            ProductCondition.EXCELLENT: "excellent",
            ProductCondition.VERY_GOOD: "very_good",
            ProductCondition.GOOD: "good",
            ProductCondition.CORRECT: "correct"
        }
        return mapping.get(condition, "good")
    
    def _map_condition_to_refurbed(self, condition: ProductCondition) -> str:
        """Maps an internal `ProductCondition` enum to its corresponding string representation
        used by the Refurbed platform.

        Args:
            condition (ProductCondition): The internal product condition enum value.

        Returns:
            str: The Refurbed-specific string representation of the condition.
                 Defaults to "good" if no direct mapping is found.
        """
        mapping = {
            ProductCondition.EXCELLENT: "like_new",
            ProductCondition.VERY_GOOD: "very_good",
            ProductCondition.GOOD: "good",
            ProductCondition.CORRECT: "acceptable"
        }
        return mapping.get(condition, "good")
    
    async def _update_condition_grade(self, listing_id: str, condition_data: Dict[str, Any]) -> Dict[str, Any]:
        """Updates the condition grade of a specific refurbished product listing.

        This method takes a listing ID and new condition data, then updates the
        corresponding product in the database and potentially in the marketplace.

        Args:
            listing_id (str): The unique identifier of the product listing to update.
            condition_data (Dict[str, Any]): A dictionary containing the new condition
                                            information. Expected keys include 'condition',
                                            'aesthetic_grade', 'functional_grade', etc.

        Returns:
            Dict[str, Any]: A dictionary containing the status of the update operation.

        Raises:
            HTTPException: If the listing is not found or if the update operation fails.
        """

        try:
            product_db = await self._get_refurbished_product_by_id(listing_id)
            if not product_db:
                raise ValueError(f"Product listing {listing_id} not found")
            product = RefurbishedProduct(**self.db_helper.to_dict(product_db))
            
            # Update condition fields
            if "condition" in condition_data:
                product.condition = ProductCondition(condition_data["condition"])
            
            if "condition_description" in condition_data:
                product.condition_description = condition_data["condition_description"]
            
            if "aesthetic_grade" in condition_data:
                product.aesthetic_grade = condition_data["aesthetic_grade"]
            
            if "functional_grade" in condition_data:
                product.functional_grade = condition_data["functional_grade"]
            
            # Validate new grading
            grading_validation = await self._validate_product_grading_data(product)
            
            if not grading_validation["valid"]:
                raise ValueError(f"Invalid grading update: {grading_validation['error']}")
            
            # Update pricing based on new condition
            pricing_recommendation = await self._get_condition_pricing_recommendations(product.product_id)
            
            if pricing_recommendation and "recommended_price" in pricing_recommendation:
                product.price = pricing_recommendation["recommended_price"]
            
            product.updated_at = datetime.utcnow()
            
            # Update on marketplace
            marketplace_result = await self._update_marketplace_condition(product, condition_data)
            
            if marketplace_result["success"]:
                product.last_sync = datetime.utcnow()
                
                # Send notification
                await self.send_message(
                    recipient_agent="product_agent",
                    message_type=MessageType.LISTING_UPDATED,
                    payload={
                        "listing_id": listing_id,
                        "product_id": product.product_id,
                        "condition": product.condition.value,
                        "price": product.price
                    }
                )
                
                return product.dict()
            else:
                raise Exception(f"Failed to update marketplace condition: {marketplace_result.get('error')}")
        
        except Exception as e:
            self.logger.error("Failed to update condition grade", error=str(e), listing_id=listing_id)
            raise
    
    async def _update_marketplace_condition(self, product: RefurbishedProduct, condition_data: Dict[str, Any]) -> Dict[str, Any]:
        """Updates the condition of a refurbished product on its respective marketplace.

        This method dispatches the update request to the appropriate marketplace-specific
        method based on the product's `marketplace_type`.

        Args:
            product (RefurbishedProduct): The refurbished product object with updated condition data.
            condition_data (Dict[str, Any]): A dictionary containing the new condition information.

        Returns:
            Dict[str, Any]: A dictionary containing the success status of the update operation.

        Raises:
            ValueError: If marketplace credentials are not found.
            Exception: If an error occurs during the marketplace-specific update.
        """
        try:
            credentials = self.marketplace_credentials.get(product.marketplace_id)
            if not credentials:
                return {"success": False, "error": "Marketplace credentials not found"}
            
            # Marketplace-specific condition update
            if product.marketplace_type == RefurbishedMarketplace.BACK_MARKET:
                return await self._update_back_market_condition(product, condition_data, credentials)
            elif product.marketplace_type == RefurbishedMarketplace.REFURBED:
                return await self._update_refurbed_condition(product, condition_data, credentials)
            else:
                # Generic update
                return {"success": True, "message": "Generic condition updated"}
        
        except Exception as e:
            self.logger.error("Failed to update marketplace condition", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _update_back_market_condition(self, product: RefurbishedProduct, condition_data: Dict[str, Any], credentials: RefurbishedCredentials) -> Dict[str, Any]:
        """Updates the condition of a refurbished product on the Back Market platform.

        This method simulates sending an update request to the Back Market API
        to reflect changes in the product's condition.

        Args:
            product (RefurbishedProduct): The refurbished product object whose condition is to be updated.
            condition_data (Dict[str, Any]): A dictionary containing the new condition information.
            credentials (RefurbishedCredentials): The API credentials for Back Market.

        Returns:
            Dict[str, Any]: A dictionary indicating the success status of the update operation.
        """
        # Simulate Back Market condition update
        self.logger.info("Back Market condition updated", 
                       sku=product.sku, 
                       condition=product.condition.value)
        return {"success": True, "message": "Back Market condition updated"}
    
    async def _update_refurbed_condition(self, product: RefurbishedProduct, condition_data: Dict[str, Any], credentials: RefurbishedCredentials) -> Dict[str, Any]:
        """Updates the condition of a refurbished product on the Refurbed platform.

        This method simulates sending an update request to the Refurbed API
        to reflect changes in the product's condition.

        Args:
            product (RefurbishedProduct): The refurbished product object whose condition is to be updated.
            condition_data (Dict[str, Any]): A dictionary containing the new condition information.
            credentials (RefurbishedCredentials): The API credentials for Refurbed.

        Returns:
            Dict[str, Any]: A dictionary indicating the success status of the update operation.
        """
        # Simulate Refurbed condition update
        self.logger.info("Refurbed condition updated", 
                       sku=product.sku, 
                       condition=product.condition.value)
        return {"success": True, "message": "Refurbed condition updated"}
    
    async def _generate_quality_report(self, product_id: str, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generates and saves a quality report for a given product.

        This method takes product ID and assessment data, then creates a new
        quality report and stores it in the database.

        Args:
            product_id (str): The unique identifier of the product.
            assessment_data (Dict[str, Any]): A dictionary containing the quality
                                             assessment details. Expected keys include
                                             'overall_condition', 'aesthetic_score',
                                             'functional_score', etc.

        Returns:
            Dict[str, Any]: A dictionary containing the status and details of the
                            newly generated quality report.

        Raises:
            HTTPException: If the product is not found or if the report generation fails.
        """

        try:
            # Find product listing
            product_listing: Optional[RefurbishedProduct] = None
            product_listing_db = await self._get_refurbished_product_by_product_id(product_id)
            if product_listing_db:
                product_listing = RefurbishedProduct(**self.db_helper.to_dict(product_listing_db))
            else:
                raise ValueError(f"Product {product_id} not found in refurbished listings")
            
            # Create quality report
            report = QualityReport(
                report_id=str(uuid4()),
                product_id=product_id,
                listing_id=product_listing.listing_id,
                overall_condition=ProductCondition(assessment_data.get("overall_condition", product_listing.condition.value)),
                aesthetic_score=assessment_data.get("aesthetic_score", 8),
                functional_score=assessment_data.get("functional_score", 9),
                battery_health=assessment_data.get("battery_health"),
                screen_condition=assessment_data.get("screen_condition"),
                body_condition=assessment_data.get("body_condition"),
                accessories_included=assessment_data.get("accessories_included", []),
                functional_tests=assessment_data.get("functional_tests", {}),
                performance_benchmarks=assessment_data.get("performance_benchmarks", {}),
                certified_by=assessment_data.get("certified_by", "quality_team"),
                certification_date=datetime.utcnow(),
                certification_valid_until=datetime.utcnow() + timedelta(days=365),
                inspector_notes=assessment_data.get("inspector_notes", ""),
                customer_notes=assessment_data.get("customer_notes")
            )
            
            # Store quality report
            await self._save_quality_report(report)
            
            # Update product grading based on report
            if report.aesthetic_score and report.functional_score:
                await self._update_condition_grade(
                    product_listing.listing_id,
                    {
                        "aesthetic_grade": str(report.aesthetic_score),
                        "functional_grade": str(report.functional_score),
                        "condition": report.overall_condition.value
                    }
                )
            
            # Send notification
            await self.send_message(
                recipient_agent="reverse_logistics_agent",
                message_type=MessageType.QUALITY_ASSESSMENT_COMPLETED,
                payload={
                    "report_id": report.report_id,
                    "product_id": product_id,
                    "overall_condition": report.overall_condition.value,
                    "aesthetic_score": report.aesthetic_score,
                    "functional_score": report.functional_score
                }
            )
            
            return report.dict()
        
        except Exception as e:
            self.logger.error("Failed to generate quality report", error=str(e), product_id=product_id)
            raise
    
    async def _get_condition_pricing_recommendations(self, product_id: str) -> Dict[str, Any]:
        """Retrieves pricing recommendations for a product based on its condition.

        This method calculates a recommended price for a refurbished product by considering
        its original price, current condition, and marketplace-specific grading systems.

        Args:
            product_id (str): The unique identifier of the product for which to get recommendations.

        Returns:
            Dict[str, Any]: A dictionary containing pricing recommendations, including
                            the original price, price factor, recommended price, and current price.

        Raises:
            ValueError: If the product is not found, no grading system is defined,
                        or the condition is not found in the grading system.
        """
        try:
            # Find product listing
            product_listing = None
            products = await self._get_all_refurbished_products()
            for product in products:
                if product.product_id == product_id:
                    product_listing = product
                    break
            
            if not product_listing:
                return {"error": f"Product {product_id} not found in refurbished listings"}
            
            # Get grading system for marketplace
            grading_system = self.grading_systems.get(product_listing.marketplace_type.value)
            
            if not grading_system:
                return {"error": f"No grading system found for {product_listing.marketplace_type.value}"}
            
            # Get condition requirements
            condition_info = grading_system["conditions"].get(product_listing.condition.value)
            
            if not condition_info:
                return {"error": f"Condition {product_listing.condition.value} not found in grading system"}
            
            # Calculate recommended price
            original_price = product_listing.original_price or product_listing.price / 0.7  # Estimate if not provided
            price_factor = condition_info.get("price_factor", 0.7)
            recommended_price = original_price * price_factor
            
            # Adjust based on market conditions (simulated)
            market_adjustment = 1.0  # In production, this would be based on market analysis
            final_price = recommended_price * market_adjustment
            
            return {
                "product_id": product_id,
                "condition": product_listing.condition.value,
                "original_price": original_price,
                "price_factor": price_factor,
                "recommended_price": round(final_price, 2),
                "current_price": product_listing.price,
                "price_difference": round(final_price - product_listing.price, 2),
                "market_adjustment": market_adjustment,
                "condition_info": condition_info
            }
        
        except Exception as e:
            self.logger.error("Failed to get condition pricing recommendations", error=str(e), product_id=product_id)
            raise
    
    async def _validate_product_grading(self, listing_id: str) -> Dict[str, Any]:
        """Validates a product's grading against marketplace standards.

        This method retrieves a product by its listing ID and then uses a helper method
        to validate its grading data against predefined marketplace standards.

        Args:
            listing_id (str): The unique identifier of the product listing to validate.

        Returns:
            Dict[str, Any]: A dictionary containing the validation results.

        Raises:
            ValueError: If the product listing is not found.
            Exception: If the grading validation process fails.
        """
        try:
            product_db = await self._get_refurbished_product_by_id(listing_id)
            if not product_db:
                raise ValueError(f"Product listing {listing_id} not found")
            product = RefurbishedProduct(**self.db_helper.to_dict(product_db))
            
            return await self._validate_product_grading_data(product)
        
        except Exception as e:
            self.logger.error("Failed to validate product grading", error=str(e), listing_id=listing_id)
            raise
    
    async def _sync_orders(self, marketplace_id: str) -> Dict[str, Any]:
        """Synchronizes orders from a specific refurbished marketplace.

        This method fetches new or updated orders from the marketplace API,
        processes them, and stores them in the local database.

        Args:
            marketplace_id (str): The unique identifier of the marketplace to sync orders from.

        Returns:
            Dict[str, Any]: A dictionary containing the status of the synchronization,
                            including the number of new or updated orders.

        Raises:
            HTTPException: If the marketplace credentials are not found or if the
                           marketplace API call fails.
        """

        try:
            credentials = self.marketplace_credentials.get(marketplace_id)
            if not credentials:
                raise ValueError(f"Marketplace credentials not found for {marketplace_id}")
            
            # Fetch orders from marketplace
            orders = await self._fetch_refurbished_orders(credentials)
            
            processed_count = 0
            success_count = 0
            errors = []
            
            for order_data in orders:
                try:
                    # Process order
                    order_db = await self._process_refurbished_order(order_data, credentials)
                    if order_db:
                        order = RefurbishedOrder(**self.db_helper.to_dict(order_db))
                        await self._save_refurbished_order(order_db)
                    
                    if order:

                        success_count += 1
                        
                        # Send order to order agent
                        await self.send_message(
                            recipient_agent="order_agent",
                            message_type=MessageType.ORDER_CREATED,
                            payload=order.dict()
                        )
                    
                    processed_count += 1
                
                except Exception as e:
                    errors.append(f"Order {order_data.get('id', 'unknown')}: {str(e)}")
                    processed_count += 1
            
            return {
                "marketplace_id": marketplace_id,
                "processed_count": processed_count,
                "success_count": success_count,
                "error_count": len(errors),
                "errors": errors
            }
        
        except Exception as e:
            self.logger.error("Failed to sync refurbished orders", error=str(e), marketplace_id=marketplace_id)
            raise
    
    async def _fetch_refurbished_orders(self, credentials: RefurbishedCredentials) -> List[Dict[str, Any]]:
        """Fetches refurbished orders from a specific marketplace using the provided credentials.

        This method simulates fetching order data from a marketplace's API.
        In a real-world scenario, this would involve making actual HTTP requests
        to the marketplace's API endpoint.

        Args:
            credentials (RefurbishedCredentials): The API credentials for the marketplace.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents
                                  an order fetched from the marketplace.

        Raises:
            Exception: If an error occurs during the simulated API call.
        """

        try:
            if credentials.marketplace_type == RefurbishedMarketplace.BACK_MARKET:
                return await self._fetch_back_market_orders(credentials)
            elif credentials.marketplace_type == RefurbishedMarketplace.REFURBED:
                return await self._fetch_refurbed_orders(credentials)
            else:
                # Simulate generic refurbished orders
                return await self._fetch_generic_refurbished_orders(credentials)
        
        except Exception as e:
            self.logger.error("Failed to fetch refurbished orders", error=str(e))
            if not self._db_initialized:
                return []
        
        async with self.db_manager.get_session() as session:
            records = await self.db_helper.get_all(session, MarketplaceOrderDB, limit=100)
            return [self.db_helper.to_dict(r) for r in records]
    
    async def _fetch_back_market_orders(self, credentials: RefurbishedCredentials) -> List[Dict[str, Any]]:
        """Fetches simulated orders from the Back Market API.

        This method generates a mock list of orders, simulating the data structure
        that would be received from the actual Back Market API.

        Args:
            credentials (RefurbishedCredentials): The API credentials for Back Market (not directly used in simulation).

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a simulated Back Market order.
        """
        # Simulate Back Market orders
        return [
            {
                "id": f"BM-{uuid4().hex[:8]}",
                "created_at": datetime.utcnow().isoformat(),
                "status": "confirmed",
                "total_amount": 299.99,
                "currency": "EUR",
                "customer": {
                    "email": "customer@backmarket.com",
                    "first_name": "John",
                    "last_name": "Doe"
                },
                "shipping_address": {
                    "street": "123 Tech Street",
                    "city": "Berlin",
                    "postal_code": "10115",
                    "country": "DE"
                },
                "items": [
                    {
                        "sku": "REFURB-PHONE-001",
                        "quantity": 1,
                        "price": 299.99,
                        "condition": "excellent",
                        "warranty_months": 12,
                        "product_name": "Refurbished iPhone 12"
                    }
                ]
            }
        ]
    
    async def _fetch_refurbed_orders(self, credentials: RefurbishedCredentials) -> List[Dict[str, Any]]:
        """Fetches simulated orders from the Refurbed API.

        This method generates a mock list of orders, simulating the data structure
        that would be received from the actual Refurbed API.

        Args:
            credentials (RefurbishedCredentials): The API credentials for Refurbed (not directly used in simulation).

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a simulated Refurbed order.
        """
        # Simulate Refurbed orders
        return [
            {
                "id": f"RF-{uuid4().hex[:8]}",
                "order_date": datetime.utcnow().isoformat(),
                "status": "pending",
                "total": 199.99,
                "currency": "EUR",
                "buyer": {
                    "email": "buyer@refurbed.com",
                    "name": "Jane Smith"
                },
                "delivery_address": {
                    "address": "456 Green Avenue",
                    "city": "Munich",
                    "zip": "80331",
                    "country": "DE"
                },
                "products": [
                    {
                        "sku": "REFURB-LAPTOP-001",
                        "quantity": 1,
                        "price": 199.99,
                        "condition": "very_good",
                        "warranty": 12,
                        "name": "Refurbished MacBook Air"
                    }
                ]
            }
        ]
    async def _fetch_generic_refurbished_orders(self, credentials: RefurbishedCredentials) -> List[Dict[str, Any]]:
        """Fetches simulated orders from a generic refurbished marketplace.

        This method generates a mock list of orders for a generic marketplace,
        simulating the data structure that would be received from a real API.

        Args:
            credentials (RefurbishedCredentials): The API credentials for the generic marketplace.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a simulated generic order.
        """
        # Simulate generic refurbished orders
        return [
            {
                "id": f"GR-{uuid4().hex[:8]}",
                "date": datetime.utcnow().isoformat(),
                "status": "new",
                "amount": 149.99,
                "currency": "EUR",
                "customer": {
                    "email": "customer@generic.com",
                    "name": "Mike Johnson"
                },
                "address": {
                    "street": "789 Refurb Road",
                    "city": "Hamburg",
                    "postal_code": "20095",
                    "country": "DE"
                },
                "items": [
                    {
                        "sku": "REFURB-TABLET-001",
                        "qty": 1,
                        "price": 149.99,
                        "grade": "good",
                        "warranty_months": 6,
                        "title": "Refurbished iPad"
                    }
                ]
            }
        ]
    
    async def _process_refurbished_order(self, order_data: Dict[str, Any], credentials: RefurbishedCredentials) -> Optional[RefurbishedOrder]:
        """Processes and normalizes raw order data from various refurbished marketplaces.

        This method acts as a dispatcher, routing the raw order data to the
        appropriate marketplace-specific processing method (e.g., Back Market, Refurbed)
        based on the `marketplace_type` in the credentials.

        Args:
            order_data (Dict[str, Any]): The raw order data received from a marketplace.
            credentials (RefurbishedCredentials): The API credentials for the marketplace.

        Returns:
            Optional[RefurbishedOrder]: A normalized `RefurbishedOrder` object if processing
                                        is successful, otherwise `None`.

        Raises:
            Exception: If an error occurs during marketplace-specific order processing.
        """
        try:
            if credentials.marketplace_type == RefurbishedMarketplace.BACK_MARKET:
                return self._process_back_market_order(order_data, credentials)
            elif credentials.marketplace_type == RefurbishedMarketplace.REFURBED:
                return self._process_refurbed_order(order_data, credentials)
            else:
                return self._process_generic_refurbished_order(order_data, credentials)
        
        except Exception as e:
            self.logger.error("Failed to process refurbished order", error=str(e))
            return None
    
    def _process_back_market_order(self, order_data: Dict[str, Any], credentials: RefurbishedCredentials) -> RefurbishedOrder:
        """Processes and normalizes raw order data from Back Market into a `RefurbishedOrder` object.

        This method extracts relevant information from the raw Back Market order data
        and transforms it into a standardized `RefurbishedOrder` format.

        Args:
            order_data (Dict[str, Any]): The raw order data received from Back Market.
            credentials (RefurbishedCredentials): The API credentials for Back Market.

        Returns:
            RefurbishedOrder: A normalized `RefurbishedOrder` object.
        """
        return RefurbishedOrder(
            order_id=str(uuid4()),
            marketplace_type=RefurbishedMarketplace.BACK_MARKET,
            marketplace_id=credentials.marketplace_id,
            marketplace_order_id=order_data["id"],
            customer_info=order_data.get("customer", {}),
            items=[
                {
                    "sku": item["sku"],
                    "quantity": item["quantity"],
                    "price": item["price"],
                    "condition": item["condition"],
                    "warranty_months": item["warranty_months"],
                    "product_name": item["product_name"]
                }
                for item in order_data.get("items", [])
            ],
            total_amount=order_data["total_amount"],
            currency=order_data["currency"],
            status=order_data["status"],
            order_date=datetime.fromisoformat(order_data["created_at"].replace("Z", "+00:00")),
            shipping_address=order_data.get("shipping_address", {}),
            billing_address=order_data.get("shipping_address", {}),
            shipping_method="Standard",
            warranty_activated=False,
            quality_guarantee="Back Market Quality Guarantee",
            last_sync=datetime.utcnow()
        )
    
    def _process_refurbed_order(self, order_data: Dict[str, Any], credentials: RefurbishedCredentials) -> RefurbishedOrder:
        """Processes and normalizes raw order data from Refurbed into a `RefurbishedOrder` object.

        This method extracts relevant information from the raw Refurbed order data
        and transforms it into a standardized `RefurbishedOrder` format.

        Args:
            order_data (Dict[str, Any]): The raw order data received from Refurbed.
            credentials (RefurbishedCredentials): The API credentials for Refurbed.

        Returns:
            RefurbishedOrder: A normalized `RefurbishedOrder` object.
        """
        return RefurbishedOrder(
            order_id=str(uuid4()),
            marketplace_type=RefurbishedMarketplace.REFURBED,
            marketplace_id=credentials.marketplace_id,
            marketplace_order_id=order_data["id"],
            customer_info=order_data.get("buyer", {}),
            items=[
                {
                    "sku": item["sku"],
                    "quantity": item["quantity"],
                    "price": item["price"],
                    "condition": item["condition"],
                    "warranty_months": item["warranty"],
                    "product_name": item["name"]
                }
                for item in order_data.get("products", [])
            ],
            total_amount=order_data["total"],
            currency=order_data["currency"],
            status=order_data["status"],
            order_date=datetime.fromisoformat(order_data["order_date"].replace("Z", "+00:00")),
            shipping_address=order_data.get("delivery_address", {}),
            billing_address=order_data.get("delivery_address", {}),
            shipping_method="Standard",
            warranty_activated=False,
            quality_guarantee="Refurbed Quality Promise",
            last_sync=datetime.utcnow()
        )
    
    def _process_generic_refurbished_order(self, order_data: Dict[str, Any], credentials: RefurbishedCredentials) -> RefurbishedOrder:
        """Processes and normalizes raw order data from a generic refurbished marketplace
        into a `RefurbishedOrder` object.

        This method extracts relevant information from the raw generic order data
        and transforms it into a standardized `RefurbishedOrder` format.

        Args:
            order_data (Dict[str, Any]): The raw order data received from a generic marketplace.
            credentials (RefurbishedCredentials): The API credentials for the generic marketplace.

        Returns:
            RefurbishedOrder: A normalized `RefurbishedOrder` object.
        """
        return RefurbishedOrder(
            order_id=str(uuid4()),
            marketplace_type=credentials.marketplace_type,
            marketplace_id=credentials.marketplace_id,
            marketplace_order_id=order_data["id"],
            customer_info=order_data.get("customer", {}),
            items=[
                {
                    "sku": item["sku"],
                    "quantity": item["qty"],
                    "price": item["price"],
                    "condition": item["grade"],
                    "warranty_months": item["warranty_months"],
                    "product_name": item["title"]
                }
                for item in order_data.get("items", [])
            ],
            total_amount=order_data["amount"],
            currency=order_data["currency"],
            status=order_data["status"],
            order_date=datetime.fromisoformat(order_data["date"].replace("Z", "+00:00")),
            shipping_address=order_data.get("address", {}),
            billing_address=order_data.get("address", {}),
            shipping_method="Standard",
            warranty_activated=False,
            last_sync=datetime.utcnow()
        )
    
    async def _update_warranty_info(self, listing_id: str, warranty_data: Dict[str, Any]) -> Dict[str, Any]:
        """Updates the warranty information for a specific refurbished product.

        This method takes a listing ID and new warranty data, then updates the
        corresponding product in the database and potentially on the marketplace.

        Args:
            listing_id (str): The unique identifier of the product listing to update.
            warranty_data (Dict[str, Any]): A dictionary containing the new warranty
                                           information. Expected keys include 'warranty_type'
                                           and 'warranty_duration_months'.

        Returns:
            Dict[str, Any]: A dictionary containing the status of the update operation.

        Raises:
            ValueError: If the product listing is not found.
            Exception: If the update operation on the marketplace fails.
        """
        try:
            product_db = await self._get_refurbished_product_by_id(listing_id)
            if not product_db:
                raise ValueError(f"Product listing {listing_id} not found")
            product = RefurbishedProduct(**self.db_helper.to_dict(product_db))
            
            # Update warranty fields
            if "warranty_type" in warranty_data:
                product.warranty_type = WarrantyType(warranty_data["warranty_type"])
            
            if "warranty_duration_months" in warranty_data:
                product.warranty_duration_months = warranty_data["warranty_duration_months"]
            
            product.updated_at = datetime.utcnow()
            
            # Update on marketplace
            marketplace_result = await self._update_marketplace_warranty(product, warranty_data)
            
            if marketplace_result["success"]:
                product.last_sync = datetime.utcnow()
                return product.dict()
            else:
                raise Exception(f"Failed to update marketplace warranty: {marketplace_result.get('error')}")
        
        except Exception as e:
            self.logger.error("Failed to update warranty info", error=str(e), listing_id=listing_id)
            raise
    
    async def _update_marketplace_warranty(self, product: RefurbishedProduct, warranty_data: Dict[str, Any]) -> Dict[str, Any]:
        """Updates the warranty information for a refurbished product on its respective marketplace.

        This method simulates sending an update request to the marketplace API
        to reflect changes in the product's warranty details.

        Args:
            product (RefurbishedProduct): The refurbished product object with updated warranty data.
            warranty_data (Dict[str, Any]): A dictionary containing the new warranty information.

        Returns:
            Dict[str, Any]: A dictionary indicating the success status of the update operation.

        Raises:
            Exception: If an error occurs during the simulated API call.
        """
        try:
            # Simulate warranty update
            self.logger.info("Marketplace warranty updated", 
                           sku=product.sku, 
                           warranty_type=product.warranty_type.value,
                           duration=product.warranty_duration_months)
            
            return {"success": True, "message": "Warranty information updated"}
        
        except Exception as e:
            self.logger.error("Failed to update marketplace warranty", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _load_refurbished_credentials(self):
        """Loads refurbished marketplace credentials from a simulated configuration.

        In a production environment, this method would securely load API keys and
        other sensitive credentials from a configuration management system or
        environment variables. For this simulation, it populates `marketplace_credentials`
        with sample data.
        """
        try:
            # In production, this would load from secure configuration
            sample_credentials = [
                RefurbishedCredentials(
                    marketplace_type=RefurbishedMarketplace.BACK_MARKET,
                    marketplace_id="back_market_de",
                    api_key="sample_back_market_key",
                    seller_id="BM_SELLER_123",
                    api_endpoint="https://api.backmarket.com/v1",
                    additional_params={
                        "webhook_url": "https://our-system.com/webhooks/back_market"
                    }
                ),
                RefurbishedCredentials(
                    marketplace_type=RefurbishedMarketplace.REFURBED,
                    marketplace_id="refurbed_de",
                    api_key="sample_refurbed_key",
                    seller_id="RF_SELLER_456",
                    api_endpoint="https://api.refurbed.com/v1",
                    additional_params={
                        "partner_id": "PARTNER_789"
                    }
                )
            ]
            
            for cred in sample_credentials:
                self.marketplace_credentials[cred.marketplace_id] = cred
            
            self.logger.info("Refurbished marketplace credentials loaded", count=len(sample_credentials))
        
        except Exception as e:
            self.logger.error("Failed to load refurbished credentials", error=str(e))
    
    async def _handle_product_updated(self, message: AgentMessage):
        """Handles incoming product update messages by publishing them to a Kafka topic.

        This method extracts product information from the `AgentMessage` payload
        and sends it to the configured Kafka product topic. This ensures that
        other services or agents subscribed to product updates are notified.

        Args:
            message (AgentMessage): The incoming message containing product update details.
        """
        payload = message.payload
        product_id = payload.get("product_id")
        
        if product_id:
            try:
                # Publish to Kafka
                await self.kafka_producer.send_and_wait(self.kafka_product_topic, json.dumps(payload).encode('utf-8'))
                self.logger.info("Published product update to Kafka", topic=self.kafka_product_topic, product_id=product_id)
            except Exception as e:
                self.logger.error("Failed to publish product update to Kafka", topic=self.kafka_product_topic, product_id=product_id, error=str(e))
            

    async def _handle_inventory_updated(self, message: AgentMessage):
        """Handles incoming inventory update messages by publishing them to a Kafka topic.

        This method extracts product and quantity information from the `AgentMessage` payload
        and sends it to the configured Kafka inventory topic. This ensures that
        other services or agents dependent on inventory levels are notified.

        Args:
            message (AgentMessage): The incoming message containing inventory update details.
        """
        payload = message.payload
        product_id = payload.get("product_id")
        new_quantity = payload.get("available_quantity")
        
        if product_id and new_quantity is not None:
            try:
                # Publish to Kafka
                await self.kafka_producer.send_and_wait(self.kafka_inventory_topic, json.dumps(payload).encode("utf-8"))
                self.logger.info("Published inventory update to Kafka", topic=self.kafka_inventory_topic, product_id=product_id, new_quantity=new_quantity)
            except Exception as e:
                self.logger.error("Failed to publish inventory update to Kafka", topic=self.kafka_inventory_topic, product_id=product_id, error=str(e))
    
    async def _handle_quality_assessment(self, message: AgentMessage):
        """Handles incoming quality assessment completion messages by publishing them to a Kafka topic.

        This method extracts quality assessment details from the `AgentMessage` payload
        and sends it to the configured Kafka quality topic. This ensures that
        other services or agents interested in product quality are notified.

        Args:
            message (AgentMessage): The incoming message containing quality assessment details.
        """
        payload = message.payload
        product_id = payload.get("product_id")
        condition = payload.get("final_condition")
        
        if product_id and condition:
            try:
                # Publish to Kafka
                await self.kafka_producer.send_and_wait(self.kafka_quality_topic, json.dumps(payload).encode("utf-8"))
                self.logger.info("Published quality assessment to Kafka", topic=self.kafka_quality_topic, product_id=product_id, condition=condition)
            except Exception as e:
                self.logger.error("Failed to publish quality assessment to Kafka", topic=self.kafka_quality_topic, product_id=product_id, error=str(e))

    async def _handle_refurbishment_completed(self, message: AgentMessage):
        """Handles incoming refurbishment completion messages by publishing them to a Kafka topic.

        This method extracts refurbishment details from the `AgentMessage` payload
        and sends it to the configured Kafka refurbishment topic. This ensures that
        other services or agents interested in refurbishment events are notified.

        Args:
            message (AgentMessage): The incoming message containing refurbishment completion details.
        """
        payload = message.payload
        product_id = payload.get("product_id")
        final_condition = payload.get("final_condition")
        
        if product_id and final_condition:
            try:
                # Publish to Kafka
                await self.kafka_producer.send_and_wait(self.kafka_refurbishment_topic, json.dumps(payload).encode("utf-8"))
                self.logger.info("Published refurbishment completion to Kafka", topic=self.kafka_refurbishment_topic, product_id=product_id, final_condition=final_condition)
            except Exception as e:
                self.logger.error("Failed to publish refurbishment completion to Kafka", topic=self.kafka_refurbishment_topic, product_id=product_id, error=str(e))
    
    async def _sync_refurbished_orders(self):
        """Background task to periodically synchronize refurbished orders from marketplaces.

        This method runs in a loop, periodically fetching new or updated orders
        from all configured marketplaces and processing them. It uses a shutdown
        event to gracefully terminate when the agent is shutting down.
        """
        while not self.shutdown_event.is_set():
            try:
                # Sync orders every 10 minutes
                await asyncio.sleep(600)
                
                if not self.shutdown_event.is_set():
                    for marketplace_id in self.marketplace_credentials.keys():
                        try:
                            await self._sync_orders(marketplace_id)
                        except Exception as e:
                            self.logger.error("Failed to sync refurbished orders for marketplace", 
                                            error=str(e), 
                                            marketplace_id=marketplace_id)
            
            except Exception as e:
                self.logger.error("Error in refurbished order sync", error=str(e))
                await asyncio.sleep(600)
    
    async def _sync_refurbished_inventory(self):
        """Background task to periodically synchronize refurbished product inventory.

        This method runs in a loop, periodically checking and updating the inventory
        levels for all refurbished products. In a real-world scenario, this would
        involve integration with actual inventory management systems.
        """
        while not self.shutdown_event.is_set():
            try:
                # Sync inventory every 20 minutes
                await asyncio.sleep(1200)
                
                if not self.shutdown_event.is_set():
                    # Update inventory for all refurbished products
                    products = await self._get_all_refurbished_products()
                    for product in products:
                        try:
                            # In production, this would sync with actual inventory
                            pass
                        except Exception as e:
                            self.logger.error("Failed to sync inventory for refurbished product", 
                                            error=str(e), 
                                            product_id=product.product_id)
            
            except Exception as e:
                self.logger.error("Error in refurbished inventory sync", error=str(e))
                await asyncio.sleep(1200)
    
    async def _monitor_quality_standards(self):
        """Background task to periodically monitor product quality standards compliance.

        This method runs in a loop, checking if refurbished products have recent
        quality reports and sending alerts if reviews are needed. This ensures
        that product quality is consistently maintained.
        """
        while not self.shutdown_event.is_set():
            try:
                # Monitor quality every 4 hours
                await asyncio.sleep(4 * 3600)
                
                if not self.shutdown_event.is_set():
                    # Check for products that need quality review
                    products_needing_review = []
                    
                    products = await self._get_all_refurbished_products()
                    for product in products:
                        # Check if product has recent quality report
                        product_reports = [r for r in self.quality_reports.values() if r.product_id == product.product_id]
                        
                        if not product_reports:
                            products_needing_review.append(product.product_id)
                        else:
                            # Check if latest report is old
                            latest_report = max(product_reports, key=lambda x: x.certification_date)
                            if (datetime.utcnow() - latest_report.certification_date).days > 90:
                                products_needing_review.append(product.product_id)
                    
                    # Send alert if products need review
                    if products_needing_review:
                        await self.send_message(
                            recipient_agent="monitoring_agent",
                            message_type=MessageType.RISK_ALERT,
                            payload={
                                "alert_type": "quality_review_needed",
                                "products_needing_review": products_needing_review,
                                "count": len(products_needing_review)
                            }
                        )
            
            except Exception as e:
                self.logger.error("Error monitoring quality standards", error=str(e))
                await asyncio.sleep(4 * 3600)
    
    async def _update_condition_pricing(self):
        """Background task to periodically update pricing based on product condition changes.

        This method runs in a loop, reviewing pricing for all refurbished products
        and sending price recommendations to the dynamic pricing agent if significant
        differences are found. This helps maintain competitive pricing based on product quality.
        """
        while not self.shutdown_event.is_set():
            try:
                # Update pricing every 6 hours
                await asyncio.sleep(6 * 3600)
                
                if not self.shutdown_event.is_set():
                    # Review pricing for all refurbished products
                    products = await self._get_all_refurbished_products()
                    for product in products:
                        try:
                            # Get pricing recommendations
                            pricing_rec = await self._get_condition_pricing_recommendations(product.product_id)
                            
                            if (pricing_rec and "recommended_price" in pricing_rec and 
                                abs(pricing_rec["recommended_price"] - product.price) > 5.0):  # Significant price difference
                                
                                # Send pricing update recommendation
                                await self.send_message(
                                    recipient_agent="dynamic_pricing_agent",
                                    message_type=MessageType.PRICE_RECOMMENDATION,
                                    payload={
                                        "product_id": product.product_id,
                                        "listing_id": product.listing_id,
                                        "current_price": product.price,
                                        "recommended_price": pricing_rec["recommended_price"],
                                        "reason": "condition_based_pricing"
                                    }
                                )
                        
                        except Exception as e:
                            self.logger.error("Failed to update pricing for refurbished product", 
                                            error=str(e), 
                                            product_id=product.product_id)
            
            except Exception as e:
                self.logger.error("Error updating condition pricing", error=str(e))
                await asyncio.sleep(6 * 3600)


# FastAPI app instance for running the agent as a service
app = FastAPI(title="Refurbished Marketplace Agent", version="1.0.0")

# Global agent instance
refurbished_marketplace_agent: Optional[RefurbishedMarketplaceAgent] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the Refurbished Marketplace Agent on startup."""
    global refurbished_marketplace_agent
    refurbished_marketplace_agent = RefurbishedMarketplaceAgent()
    await refurbished_marketplace_agent.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup the Refurbished Marketplace Agent on shutdown."""
    global refurbished_marketplace_agent
    if refurbished_marketplace_agent:
        await refurbished_marketplace_agent.stop()


# Include agent routes
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if refurbished_marketplace_agent:
        health_status = refurbished_marketplace_agent.get_health_status()
        return {"status": "healthy", "agent_status": health_status.dict()}
    return {"status": "unhealthy", "message": "Agent not initialized"}


# Mount agent's FastAPI app
app.mount("/api/v1", refurbished_marketplace_agent.app if refurbished_marketplace_agent else FastAPI())


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
    )
    if not db_config.password:
        raise ValueError("Database password must be set in environment variables")
    initialize_database_manager(db_config)
    
    # Run the agent
    uvicorn.run(
        "refurbished_marketplace_agent:app",
        host="0.0.0.0",
        port=8012,
        reload=False,
        log_level="info"
    )

'''

    async def _initialize_db(self):
        """Initialize the database tables if they don't exist."""
        self.logger.info("Initializing database for Refurbished Marketplace Agent")
        try:
            async with self.db_manager.engine.begin() as conn:
                await conn.run_sync(self.db_manager.Base.metadata.create_all)
            self._db_initialized = True
            self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            self._db_initialized = False

    async def _load_refurbished_credentials_from_db(self):
        """Load marketplace credentials from the database."""
        if not self._db_initialized: return
        self.logger.info("Loading refurbished credentials from DB")
        async with self.db_manager.get_session() as session:
            credentials_dbs = await self.db_helper.get_all(session, RefurbishedCredentialsDB)
            self.marketplace_credentials = {c.marketplace_id: RefurbishedCredentials(**self.db_helper.to_dict(c)) for c in credentials_dbs}
        self.logger.info(f"Loaded {len(self.marketplace_credentials)} credentials")

    async def _save_refurbished_credentials(self, credentials: RefurbishedCredentials):
        """Save refurbished marketplace credentials to the database."""
        if not self._db_initialized: return
        async with self.db_manager.get_session() as session:
            credentials_db = RefurbishedCredentialsDB(**credentials.dict())
            await self.db_helper.add_or_update(session, credentials_db)
            await session.commit()
        self.logger.info(f"Saved credentials for {credentials.marketplace_id}")

    async def _get_refurbished_credentials_by_id(self, marketplace_id: str) -> Optional[RefurbishedCredentialsDB]:
        """Get refurbished marketplace credentials by ID from the database."""
        if not self._db_initialized: return None
        async with self.db_manager.get_session() as session:
            return await self.db_helper.get_by_id(session, RefurbishedCredentialsDB, marketplace_id)

    async def _get_all_refurbished_credentials(self) -> List[RefurbishedCredentials]:
        """Get all refurbished marketplace credentials from the database."""
        if not self._db_initialized: return []
        async with self.db_manager.get_session() as session:
            credentials_dbs = await self.db_helper.get_all(session, RefurbishedCredentialsDB)
            return [RefurbishedCredentials(**self.db_helper.to_dict(c)) for c in credentials_dbs]

    async def _delete_refurbished_credentials(self, marketplace_id: str):
        """Delete refurbished marketplace credentials from the database."""
        if not self._db_initialized: return
        async with self.db_manager.get_session() as session:
            await self.db_helper.delete(session, RefurbishedCredentialsDB, marketplace_id)
            await session.commit()
        self.logger.info(f"Deleted credentials for {marketplace_id}")
'''


    async def _save_refurbished_product(self, product: RefurbishedProduct):
        """Save a refurbished product to the database."""
        if not self._db_initialized: return
        async with self.db_manager.get_session() as session:
            product_db = RefurbishedProductDB(**product.dict())
            await self.db_helper.add_or_update(session, product_db)
            await session.commit()
        self.logger.info(f"Saved product {product.listing_id}")

    async def _get_refurbished_product_by_id(self, listing_id: str) -> Optional[RefurbishedProductDB]:
        """Get a refurbished product by listing ID from the database."""
        if not self._db_initialized: return None
        async with self.db_manager.get_session() as session:
            return await self.db_helper.get_by_id(session, RefurbishedProductDB, listing_id)

    async def _get_refurbished_product_by_product_id(self, product_id: str) -> Optional[RefurbishedProductDB]:
        """Get a refurbished product by product ID from the database."""
        if not self._db_initialized: return None
        async with self.db_manager.get_session() as session:
            stmt = select(RefurbishedProductDB).where(RefurbishedProductDB.product_id == product_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def _get_all_refurbished_products(self) -> List[RefurbishedProduct]:
        """Get all refurbished products from the database."""
        if not self._db_initialized: return []
        async with self.db_manager.get_session() as session:
            product_dbs = await self.db_helper.get_all(session, RefurbishedProductDB)
            return [RefurbishedProduct(**self.db_helper.to_dict(p)) for p in product_dbs]

    async def _save_refurbished_order(self, order: RefurbishedOrder):
        """Save a refurbished order to the database."""
        if not self._db_initialized: return
        async with self.db_manager.get_session() as session:
            order_db = RefurbishedOrderDB(**order.dict())
            await self.db_helper.add_or_update(session, order_db)
            await session.commit()
        self.logger.info(f"Saved order {order.order_id}")

    async def _save_quality_report(self, report: QualityReport):
        """Save a quality report to the database."""
        if not self._db_initialized: return
        async with self.db_manager.get_session() as session:
            report_db = QualityReportDB(**report.dict())
            await self.db_helper.add_or_update(session, report_db)
            await session.commit()
        self.logger.info(f"Saved quality report {report.report_id}")


