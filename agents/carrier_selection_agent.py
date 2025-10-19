"""
Carrier Selection Agent - Multi-Agent E-commerce System

This agent uses AI to select the optimal shipping carrier based on multiple factors:
- Package characteristics (size, weight, fragility, dangerous goods)
- Delivery requirements (speed, destination, cost)
- Carrier performance history and reliability
- Real-time carrier capacity and pricing
- Customer preferences and service levels
"""

import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

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
    print(f"Added {project_root} to Python path")

# Now try the import
try:
    from shared.openai_helper import chat_completion
    from shared.base_agent import BaseAgent, MessageType, AgentMessage
    print("Successfully imported shared.base_agent")
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current sys.path: {sys.path}")
    
    # List files in the shared directory to verify it exists
    shared_dir = os.path.join(project_root, "shared")
    if os.path.exists(shared_dir):
        print(f"Contents of {shared_dir}:")
        for item in os.listdir(shared_dir):
            print(f"  - {item}")
    else:
        print(f"Directory not found: {shared_dir}")

# Now import the module
from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.models import (
    Carrier, CarrierType, APIResponse
)
from shared.database import DatabaseManager, BaseRepository, get_database_manager


logger = structlog.get_logger(__name__)


class PackageDetails(BaseModel):
    """Model for package details."""
    weight: float  # kg
    length: float  # cm
    width: float   # cm
    height: float  # cm
    value: float   # EUR
    is_fragile: bool = False
    is_dangerous: bool = False
    special_handling: Optional[str] = None


class DeliveryRequirements(BaseModel):
    """Model for delivery requirements."""
    destination_country: str
    destination_postal_code: str
    destination_city: str
    required_delivery_date: Optional[datetime] = None
    max_delivery_days: Optional[int] = None
    max_cost: Optional[float] = None
    service_level: str = "standard"  # economy, standard, express, premium
    signature_required: bool = False
    insurance_required: bool = False


class CarrierQuote(BaseModel):
    """Model for carrier quote."""
    carrier_id: str
    carrier_name: str
    carrier_type: CarrierType
    service_name: str
    cost: float
    estimated_delivery_days: int
    estimated_delivery_date: datetime
    tracking_included: bool
    insurance_included: bool
    signature_confirmation: bool
    pickup_available: bool
    confidence_score: float  # AI confidence in this selection
    reasons: List[str]


class CarrierSelectionRequest(BaseModel):
    """Request model for carrier selection."""
    order_id: str
    warehouse_id: str
    package_details: PackageDetails
    delivery_requirements: DeliveryRequirements
    customer_preferences: Optional[Dict[str, Any]] = None


class CarrierSelectionResult(BaseModel):
    """Result model for carrier selection."""
    order_id: str
    selected_carrier_id: str
    selected_carrier_name: str
    selected_service: str
    final_cost: float
    estimated_delivery_date: datetime
    tracking_number: Optional[str] = None
    ai_confidence: float
    selection_reasons: List[str]
    alternative_quotes: List[CarrierQuote]


class CarrierRepository(BaseRepository):
    """Repository for carrier data operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        from shared.models import CarrierDB
        super().__init__(db_manager, CarrierDB)
    
    async def find_by_type(self, carrier_type: CarrierType) -> List[Carrier]:
        """Find carriers by type."""
        records = await self.find_by_criteria(carrier_type=carrier_type.value)
        return [self._to_pydantic(record) for record in records]
    
    async def find_available_carriers(self, max_weight: float, max_dimensions: Dict[str, float]) -> List[Carrier]:
        """Find carriers that can handle the package specifications."""
        all_carriers = await self.get_all()
        suitable_carriers = []
        
        for carrier in all_carriers:
            carrier_obj = self._to_pydantic(carrier)
            
            # Check weight limit
            if carrier_obj.max_weight >= max_weight:
                # Check dimension limits
                carrier_dims = carrier_obj.max_dimensions
                if (carrier_dims.get("length", 0) >= max_dimensions.get("length", 0) and
                    carrier_dims.get("width", 0) >= max_dimensions.get("width", 0) and
                    carrier_dims.get("height", 0) >= max_dimensions.get("height", 0)):
                    suitable_carriers.append(carrier_obj)
        
        return suitable_carriers
    
    def _to_pydantic(self, db_record) -> Carrier:
        """Convert database record to Pydantic model."""
        return Carrier(
            id=db_record.id,
            name=db_record.name,
            carrier_type=CarrierType(db_record.carrier_type),
            api_endpoint=db_record.api_endpoint,
            api_key=db_record.api_key,
            base_rate=db_record.base_rate,
            per_kg_rate=db_record.per_kg_rate,
            max_weight=db_record.max_weight,
            max_dimensions=db_record.max_dimensions,
            delivery_time_days=db_record.delivery_time_days,
            tracking_url_template=db_record.tracking_url_template,
            created_at=db_record.created_at,
            updated_at=db_record.updated_at
        )


class CarrierSelectionAgent(BaseAgent):
    """
    Carrier Selection Agent uses AI to select optimal shipping carriers based on:
    - Package characteristics and constraints
    - Delivery requirements and deadlines
    - Historical carrier performance data
    - Real-time pricing and capacity
    - Customer preferences and service levels
    """
    
    def __init__(self, **kwargs):
        super().__init__(agent_id="carrier_selection_agent", **kwargs)
        self.repository: Optional[CarrierRepository] = None
        self.app = FastAPI(title="Carrier Selection Agent API", version="1.0.0")
        self.setup_routes()
        
        # Initialize OpenAI client
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        # Carrier performance metrics (in production, this would be in a database)
        self.carrier_performance: Dict[str, Dict[str, float]] = {}
        
        # Register message handlers
        self.register_handler(MessageType.WAREHOUSE_SELECTED, self._handle_warehouse_selected)
        self.register_handler(MessageType.ORDER_UPDATED, self._handle_order_updated)
    
    async def initialize(self):
        """Initialize the Carrier Selection Agent."""
        self.logger.info("Initializing Carrier Selection Agent")
        
        # Initialize database repository
        db_manager = get_database_manager()
        self.repository = CarrierRepository(db_manager)
        
        # Initialize carrier performance metrics
        await self._initialize_carrier_performance()
        
        # Start background tasks
        asyncio.create_task(self._update_carrier_performance())
        asyncio.create_task(self._monitor_carrier_capacity())
        
        self.logger.info("Carrier Selection Agent initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up Carrier Selection Agent")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process carrier selection business logic."""
        action = data.get("action")
        
        if action == "select_carrier":
            return await self._select_optimal_carrier(data["selection_request"])
        elif action == "get_carrier_quotes":
            return await self._get_carrier_quotes(data["selection_request"])
        elif action == "get_carrier_performance":
            return await self._get_carrier_performance(data.get("carrier_id"))
        elif action == "track_shipment":
            return await self._track_shipment(data["tracking_number"], data["carrier_id"])
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def setup_routes(self):
        """Setup FastAPI routes for the Carrier Selection Agent."""
        
        @self.app.post("/carrier-selection", response_model=APIResponse)
        async def select_carrier(request: CarrierSelectionRequest):
            """Select optimal carrier for a shipment."""
            try:
                result = await self._select_optimal_carrier(request.dict())
                
                return APIResponse(
                    success=True,
                    message="Carrier selected successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to select carrier", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/carrier-selection/quotes", response_model=APIResponse)
        async def get_carrier_quotes(request: CarrierSelectionRequest):
            """Get quotes from all available carriers."""
            try:
                result = await self._get_carrier_quotes(request.dict())
                
                return APIResponse(
                    success=True,
                    message="Carrier quotes retrieved successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to get carrier quotes", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/carriers/{carrier_id}/performance", response_model=APIResponse)
        async def get_carrier_performance(carrier_id: str):
            """Get performance metrics for a carrier."""
            try:
                result = await self._get_carrier_performance(carrier_id)
                
                return APIResponse(
                    success=True,
                    message="Carrier performance retrieved successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to get carrier performance", error=str(e), carrier_id=carrier_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/tracking/{tracking_number}", response_model=APIResponse)
        async def track_shipment(tracking_number: str, carrier_id: str):
            """Track a shipment."""
            try:
                result = await self._track_shipment(tracking_number, carrier_id)
                
                return APIResponse(
                    success=True,
                    message="Shipment tracking retrieved successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to track shipment", error=str(e), tracking_number=tracking_number)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/carriers", response_model=APIResponse)
        async def list_carriers():
            """List all available carriers."""
            try:
                carriers = await self.repository.get_all()
                
                return APIResponse(
                    success=True,
                    message="Carriers retrieved successfully",
                    data={"carriers": [carrier.__dict__ for carrier in carriers]}
                )
            
            except Exception as e:
                self.logger.error("Failed to list carriers", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _select_optimal_carrier(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Select the optimal carrier using AI analysis."""
        try:
            order_id = request_data["order_id"]
            warehouse_id = request_data["warehouse_id"]
            package_details = PackageDetails(**request_data["package_details"])
            delivery_requirements = DeliveryRequirements(**request_data["delivery_requirements"])
            customer_preferences = request_data.get("customer_preferences", {})
            
            # Get carrier quotes
            quotes = await self._calculate_carrier_quotes(package_details, delivery_requirements, warehouse_id)
            
            if not quotes:
                raise ValueError("No suitable carriers found for this shipment")
            
            # Use AI to select the best carrier
            best_quote = await self._ai_select_carrier(quotes, delivery_requirements, customer_preferences)
            
            # Generate tracking number (in production, this would come from the carrier API)
            tracking_number = self._generate_tracking_number(best_quote.carrier_id)
            
            # Create selection result
            result = CarrierSelectionResult(
                order_id=order_id,
                selected_carrier_id=best_quote.carrier_id,
                selected_carrier_name=best_quote.carrier_name,
                selected_service=best_quote.service_name,
                final_cost=best_quote.cost,
                estimated_delivery_date=best_quote.estimated_delivery_date,
                tracking_number=tracking_number,
                ai_confidence=best_quote.confidence_score,
                selection_reasons=best_quote.reasons,
                alternative_quotes=[q for q in quotes if q.carrier_id != best_quote.carrier_id][:3]
            )
            
            # Send carrier selection notification
            await self.send_message(
                recipient_agent="order_agent",
                message_type=MessageType.CARRIER_SELECTED,
                payload={
                    "order_id": order_id,
                    "carrier_id": best_quote.carrier_id,
                    "carrier_name": best_quote.carrier_name,
                    "service_name": best_quote.service_name,
                    "cost": best_quote.cost,
                    "estimated_delivery": best_quote.estimated_delivery_date.isoformat(),
                    "tracking_number": tracking_number
                }
            )
            
            # Update carrier performance metrics
            await self._update_carrier_selection_metrics(best_quote.carrier_id)
            
            self.logger.info("Carrier selected", order_id=order_id, carrier_id=best_quote.carrier_id, confidence=best_quote.confidence_score)
            
            return result.dict()
        
        except Exception as e:
            self.logger.error("Failed to select optimal carrier", error=str(e))
            raise
    
    async def _get_carrier_quotes(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get quotes from all available carriers."""
        try:
            package_details = PackageDetails(**request_data["package_details"])
            delivery_requirements = DeliveryRequirements(**request_data["delivery_requirements"])
            warehouse_id = request_data["warehouse_id"]
            
            quotes = await self._calculate_carrier_quotes(package_details, delivery_requirements, warehouse_id)
            
            return {
                "quotes": [quote.dict() for quote in quotes],
                "total_carriers": len(quotes)
            }
        
        except Exception as e:
            self.logger.error("Failed to get carrier quotes", error=str(e))
            raise
    
    async def _calculate_carrier_quotes(
        self, 
        package_details: PackageDetails, 
        delivery_requirements: DeliveryRequirements,
        warehouse_id: str
    ) -> List[CarrierQuote]:
        """Calculate quotes from all suitable carriers."""
        try:
            # Find carriers that can handle the package
            suitable_carriers = await self.repository.find_available_carriers(
                package_details.weight,
                {
                    "length": package_details.length,
                    "width": package_details.width,
                    "height": package_details.height
                }
            )
            
            quotes = []
            
            for carrier in suitable_carriers:
                try:
                    quote = await self._calculate_carrier_quote(carrier, package_details, delivery_requirements, warehouse_id)
                    if quote:
                        quotes.append(quote)
                
                except Exception as e:
                    self.logger.error("Failed to calculate quote for carrier", error=str(e), carrier_id=carrier.id)
            
            # Sort quotes by a combination of cost and delivery time
            quotes.sort(key=lambda q: (q.cost, q.estimated_delivery_days))
            
            return quotes
        
        except Exception as e:
            self.logger.error("Failed to calculate carrier quotes", error=str(e))
            raise
    
    async def _calculate_carrier_quote(
        self, 
        carrier: Carrier, 
        package_details: PackageDetails, 
        delivery_requirements: DeliveryRequirements,
        warehouse_id: str
    ) -> Optional[CarrierQuote]:
        """Calculate a quote for a specific carrier."""
        try:
            # Check if carrier can deliver to destination
            if not self._can_deliver_to_destination(carrier, delivery_requirements.destination_country):
                return None
            
            # Calculate base cost
            base_cost = float(carrier.base_rate)
            weight_cost = float(carrier.per_kg_rate) * package_details.weight
            
            # Add surcharges
            surcharges = self._calculate_surcharges(carrier, package_details, delivery_requirements)
            
            total_cost = base_cost + weight_cost + surcharges
            
            # Calculate delivery time
            base_delivery_days = carrier.delivery_time_days
            delivery_adjustment = self._calculate_delivery_adjustment(carrier, delivery_requirements)
            estimated_delivery_days = base_delivery_days + delivery_adjustment
            
            # Calculate estimated delivery date
            estimated_delivery_date = datetime.now() + timedelta(days=estimated_delivery_days)
            
            # Get carrier performance metrics
            performance = self.carrier_performance.get(carrier.id, {})
            
            # Calculate confidence score based on performance and suitability
            confidence_score = self._calculate_confidence_score(carrier, package_details, delivery_requirements, performance)
            
            # Generate reasons for this quote
            reasons = self._generate_quote_reasons(carrier, package_details, delivery_requirements, performance)
            
            quote = CarrierQuote(
                carrier_id=carrier.id,
                carrier_name=carrier.name,
                carrier_type=carrier.carrier_type,
                service_name=self._get_service_name(carrier, delivery_requirements.service_level),
                cost=round(total_cost, 2),
                estimated_delivery_days=estimated_delivery_days,
                estimated_delivery_date=estimated_delivery_date,
                tracking_included=True,  # Assume all carriers provide tracking
                insurance_included=package_details.value > 100,  # Insurance for valuable items
                signature_confirmation=delivery_requirements.signature_required,
                pickup_available=carrier.carrier_type in [CarrierType.UPS, CarrierType.FEDEX, CarrierType.DHL],
                confidence_score=confidence_score,
                reasons=reasons
            )
            
            return quote
        
        except Exception as e:
            self.logger.error("Failed to calculate carrier quote", error=str(e), carrier_id=carrier.id)
            return None
    
    def _can_deliver_to_destination(self, carrier: Carrier, destination_country: str) -> bool:
        """Check if carrier can deliver to the destination country."""
        # Simplified logic - in production, this would check carrier coverage areas
        if destination_country.upper() == "FRANCE":
            return True  # All carriers can deliver within France
        elif destination_country.upper() in ["GERMANY", "SPAIN", "ITALY", "BELGIUM", "NETHERLANDS"]:
            return carrier.carrier_type in [CarrierType.UPS, CarrierType.FEDEX, CarrierType.DHL, CarrierType.CHRONOPOST]
        else:
            return carrier.carrier_type in [CarrierType.UPS, CarrierType.FEDEX, CarrierType.DHL]
    
    def _calculate_surcharges(self, carrier: Carrier, package_details: PackageDetails, delivery_requirements: DeliveryRequirements) -> float:
        """Calculate additional surcharges."""
        surcharges = 0.0
        
        # Fragile item surcharge
        if package_details.is_fragile:
            surcharges += 5.0
        
        # Dangerous goods surcharge
        if package_details.is_dangerous:
            surcharges += 15.0
        
        # Insurance surcharge
        if delivery_requirements.insurance_required or package_details.value > 100:
            surcharges += package_details.value * 0.01  # 1% of value
        
        # Signature confirmation surcharge
        if delivery_requirements.signature_required:
            surcharges += 3.0
        
        # Express delivery surcharge
        if delivery_requirements.service_level == "express":
            surcharges += 10.0
        elif delivery_requirements.service_level == "premium":
            surcharges += 20.0
        
        # International delivery surcharge
        if delivery_requirements.destination_country.upper() != "FRANCE":
            surcharges += 8.0
        
        return surcharges
    
    def _calculate_delivery_adjustment(self, carrier: Carrier, delivery_requirements: DeliveryRequirements) -> int:
        """Calculate delivery time adjustment based on requirements."""
        adjustment = 0
        
        # Express service reduces delivery time
        if delivery_requirements.service_level == "express":
            adjustment -= 1
        elif delivery_requirements.service_level == "premium":
            adjustment -= 2
        elif delivery_requirements.service_level == "economy":
            adjustment += 1
        
        # International delivery adds time
        if delivery_requirements.destination_country.upper() != "FRANCE":
            adjustment += 2
        
        # Signature required may add time
        if delivery_requirements.signature_required:
            adjustment += 1
        
        return max(adjustment, -carrier.delivery_time_days + 1)  # Minimum 1 day delivery
    
    def _calculate_confidence_score(self, carrier: Carrier, package_details: PackageDetails, delivery_requirements: DeliveryRequirements, performance: Dict[str, float]) -> float:
        """Calculate AI confidence score for carrier selection."""
        score = 70.0  # Base confidence
        
        # Performance-based adjustments
        on_time_rate = performance.get("on_time_delivery_rate", 85.0)
        score += (on_time_rate - 85.0) * 0.3  # Adjust based on on-time performance
        
        damage_rate = performance.get("damage_rate", 2.0)
        score -= damage_rate * 5.0  # Penalty for high damage rates
        
        customer_satisfaction = performance.get("customer_satisfaction", 4.0)
        score += (customer_satisfaction - 4.0) * 10.0  # Boost for high satisfaction
        
        # Package suitability adjustments
        if package_details.is_fragile and carrier.carrier_type in [CarrierType.UPS, CarrierType.FEDEX]:
            score += 10.0  # Premium carriers better for fragile items
        
        if package_details.is_dangerous and carrier.carrier_type == CarrierType.DHL:
            score += 15.0  # DHL specializes in dangerous goods
        
        # Service level matching
        if delivery_requirements.service_level == "premium" and carrier.carrier_type in [CarrierType.UPS, CarrierType.FEDEX, CarrierType.DHL]:
            score += 10.0
        elif delivery_requirements.service_level == "economy" and carrier.carrier_type in [CarrierType.COLIS_PRIVE, CarrierType.COLISSIMO]:
            score += 5.0
        
        return max(0.0, min(100.0, score))
    
    def _generate_quote_reasons(self, carrier: Carrier, package_details: PackageDetails, delivery_requirements: DeliveryRequirements, performance: Dict[str, float]) -> List[str]:
        """Generate human-readable reasons for the quote."""
        reasons = []
        
        # Performance-based reasons
        on_time_rate = performance.get("on_time_delivery_rate", 85.0)
        if on_time_rate >= 95.0:
            reasons.append("Excellent on-time delivery record")
        elif on_time_rate >= 90.0:
            reasons.append("Good on-time delivery record")
        
        # Cost competitiveness
        reasons.append(f"Competitive pricing for {delivery_requirements.service_level} service")
        
        # Special capabilities
        if package_details.is_fragile and carrier.carrier_type in [CarrierType.UPS, CarrierType.FEDEX]:
            reasons.append("Specialized handling for fragile items")
        
        if package_details.is_dangerous:
            reasons.append("Certified for dangerous goods transport")
        
        # Service level matching
        if delivery_requirements.service_level == "express":
            reasons.append("Fast express delivery service")
        elif delivery_requirements.service_level == "economy":
            reasons.append("Cost-effective economy service")
        
        # Coverage
        if delivery_requirements.destination_country.upper() != "FRANCE":
            reasons.append("International delivery capability")
        
        return reasons
    
    def _get_service_name(self, carrier: Carrier, service_level: str) -> str:
        """Get service name based on carrier and service level."""
        service_names = {
            CarrierType.UPS: {
                "economy": "UPS Standard",
                "standard": "UPS Express Saver",
                "express": "UPS Express",
                "premium": "UPS Express Plus"
            },
            CarrierType.FEDEX: {
                "economy": "FedEx Ground",
                "standard": "FedEx Express Saver",
                "express": "FedEx Priority Overnight",
                "premium": "FedEx First Overnight"
            },
            CarrierType.DHL: {
                "economy": "DHL Europlus",
                "standard": "DHL Express Worldwide",
                "express": "DHL Express 12:00",
                "premium": "DHL Express 9:00"
            },
            CarrierType.COLIS_PRIVE: {
                "economy": "Colis Privé Eco",
                "standard": "Colis Privé Standard",
                "express": "Colis Privé Express",
                "premium": "Colis Privé Premium"
            },
            CarrierType.CHRONOPOST: {
                "economy": "Chronopost Relais",
                "standard": "Chronopost Express",
                "express": "Chronopost Same Day",
                "premium": "Chronopost Premium"
            },
            CarrierType.COLISSIMO: {
                "economy": "Colissimo Access",
                "standard": "Colissimo Domicile",
                "express": "Colissimo Express",
                "premium": "Colissimo Premium"
            }
        }
        
        return service_names.get(carrier.carrier_type, {}).get(service_level, f"{carrier.name} {service_level.title()}")
    
    async def _ai_select_carrier(self, quotes: List[CarrierQuote], delivery_requirements: DeliveryRequirements, customer_preferences: Dict[str, Any]) -> CarrierQuote:
        """Use AI to select the best carrier from available quotes."""
        try:
            # Prepare data for AI analysis
            quotes_data = []
            for quote in quotes:
                quotes_data.append({
                    "carrier_name": quote.carrier_name,
                    "cost": quote.cost,
                    "delivery_days": quote.estimated_delivery_days,
                    "confidence_score": quote.confidence_score,
                    "reasons": quote.reasons
                })
            
            # Create AI prompt
            prompt = f"""
            You are an expert logistics AI assistant. Analyze the following shipping quotes and select the best carrier based on the delivery requirements and customer preferences.

            Delivery Requirements:
            - Destination: {delivery_requirements.destination_city}, {delivery_requirements.destination_country}
            - Service Level: {delivery_requirements.service_level}
            - Max Delivery Days: {delivery_requirements.max_delivery_days or 'No limit'}
            - Max Cost: €{delivery_requirements.max_cost or 'No limit'}
            - Required Delivery Date: {delivery_requirements.required_delivery_date or 'Flexible'}

            Customer Preferences:
            {json.dumps(customer_preferences, indent=2) if customer_preferences else 'None specified'}

            Available Quotes:
            {json.dumps(quotes_data, indent=2)}

            Please select the best carrier and provide your reasoning. Consider:
            1. Meeting delivery requirements
            2. Cost effectiveness
            3. Reliability (confidence score)
            4. Customer preferences
            5. Service quality

            Respond with JSON format:
            {{
                "selected_carrier": "carrier_name",
                "reasoning": ["reason1", "reason2", "reason3"],
                "confidence": 0.95
            }}
            """
            
            # Call OpenAI API
            response = await self._call_openai_api(prompt)
            
            if response:
                selected_carrier_name = response.get("selected_carrier")
                ai_reasoning = response.get("reasoning", [])
                ai_confidence = response.get("confidence", 0.8)
                
                # Find the selected quote
                for quote in quotes:
                    if quote.carrier_name == selected_carrier_name:
                        # Update quote with AI reasoning and confidence
                        quote.reasons.extend(ai_reasoning)
                        quote.confidence_score = ai_confidence * 100
                        return quote
            
            # Fallback to highest confidence score if AI selection fails
            return max(quotes, key=lambda q: q.confidence_score)
        
        except Exception as e:
            self.logger.error("AI carrier selection failed, using fallback", error=str(e))
            # Fallback to rule-based selection
            return self._rule_based_carrier_selection(quotes, delivery_requirements)
    
    async def _call_openai_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call OpenAI API for carrier selection."""
        try:
            if not openai.api_key:
                self.logger.warning("OpenAI API key not configured, skipping AI selection")
                return None
            
            response = await chat_completion(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert logistics AI assistant that helps select optimal shipping carriers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response["choices"][0]["message"]["content"]
            
            # Try to parse JSON response
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                self.logger.error("Failed to parse AI response as JSON", response=content)
                return None
        
        except Exception as e:
            self.logger.error("OpenAI API call failed", error=str(e))
            return None
    
    def _rule_based_carrier_selection(self, quotes: List[CarrierQuote], delivery_requirements: DeliveryRequirements) -> CarrierQuote:
        """Fallback rule-based carrier selection."""
        # Filter quotes that meet requirements
        suitable_quotes = []
        
        for quote in quotes:
            # Check delivery time requirement
            if delivery_requirements.max_delivery_days and quote.estimated_delivery_days > delivery_requirements.max_delivery_days:
                continue
            
            # Check cost requirement
            if delivery_requirements.max_cost and quote.cost > delivery_requirements.max_cost:
                continue
            
            # Check delivery date requirement
            if delivery_requirements.required_delivery_date and quote.estimated_delivery_date > delivery_requirements.required_delivery_date:
                continue
            
            suitable_quotes.append(quote)
        
        if not suitable_quotes:
            suitable_quotes = quotes  # Use all quotes if none meet strict requirements
        
        # Select based on service level priority
        if delivery_requirements.service_level == "premium":
            # Prioritize fastest delivery
            return min(suitable_quotes, key=lambda q: q.estimated_delivery_days)
        elif delivery_requirements.service_level == "economy":
            # Prioritize lowest cost
            return min(suitable_quotes, key=lambda q: q.cost)
        else:
            # Balance cost and speed
            return min(suitable_quotes, key=lambda q: q.cost + (q.estimated_delivery_days * 5))
    
    def _generate_tracking_number(self, carrier_id: str) -> str:
        """Generate a tracking number for the shipment."""
        # In production, this would call the carrier's API to create a shipment
        import random
        import string
        
        prefix_map = {
            "ups": "1Z",
            "fedex": "FX",
            "dhl": "DH",
            "colis_prive": "CP",
            "chronopost": "CH",
            "colissimo": "CO"
        }
        
        # Get carrier from database to determine prefix
        carrier_prefix = "TR"  # Default prefix
        
        # Generate random tracking number
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        
        return f"{carrier_prefix}{random_part}"
    
    async def _get_carrier_performance(self, carrier_id: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics for carrier(s)."""
        try:
            if carrier_id:
                performance = self.carrier_performance.get(carrier_id, {})
                return {"carrier_id": carrier_id, "performance": performance}
            else:
                return {"all_carriers": self.carrier_performance}
        
        except Exception as e:
            self.logger.error("Failed to get carrier performance", error=str(e))
            raise
    
    async def _track_shipment(self, tracking_number: str, carrier_id: str) -> Dict[str, Any]:
        """Track a shipment (mock implementation)."""
        try:
            # In production, this would call the carrier's tracking API
            # For now, we'll return mock tracking data
            
            statuses = ["Label Created", "Picked Up", "In Transit", "Out for Delivery", "Delivered"]
            current_status = statuses[min(len(statuses) - 1, hash(tracking_number) % len(statuses))]
            
            tracking_info = {
                "tracking_number": tracking_number,
                "carrier_id": carrier_id,
                "status": current_status,
                "estimated_delivery": (datetime.now() + timedelta(days=2)).isoformat(),
                "last_updated": datetime.now().isoformat(),
                "tracking_events": [
                    {
                        "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                        "status": "Label Created",
                        "location": "Warehouse"
                    },
                    {
                        "timestamp": datetime.now().isoformat(),
                        "status": current_status,
                        "location": "Distribution Center"
                    }
                ]
            }
            
            return tracking_info
        
        except Exception as e:
            self.logger.error("Failed to track shipment", error=str(e), tracking_number=tracking_number)
            raise
    
    async def _initialize_carrier_performance(self):
        """Initialize carrier performance metrics."""
        try:
            carriers = await self.repository.get_all()
            
            for carrier in carriers:
                carrier_obj = self.repository._to_pydantic(carrier)
                
                # Initialize with realistic performance metrics
                self.carrier_performance[carrier_obj.id] = {
                    "on_time_delivery_rate": 88.0 + (hash(carrier_obj.id) % 10),  # 88-97%
                    "damage_rate": 1.0 + (hash(carrier_obj.id) % 3),  # 1-3%
                    "customer_satisfaction": 3.8 + (hash(carrier_obj.id) % 12) / 10,  # 3.8-4.9
                    "average_delivery_time": carrier_obj.delivery_time_days + (hash(carrier_obj.id) % 2),
                    "cost_competitiveness": 75.0 + (hash(carrier_obj.id) % 20),  # 75-94%
                    "shipments_this_month": hash(carrier_obj.id) % 1000,
                    "last_updated": datetime.utcnow().isoformat()
                }
            
            self.logger.info("Carrier performance metrics initialized", carrier_count=len(carriers))
        
        except Exception as e:
            self.logger.error("Failed to initialize carrier performance", error=str(e))
    
    async def _update_carrier_selection_metrics(self, carrier_id: str):
        """Update metrics when a carrier is selected."""
        try:
            if carrier_id in self.carrier_performance:
                self.carrier_performance[carrier_id]["shipments_this_month"] += 1
                self.carrier_performance[carrier_id]["last_updated"] = datetime.utcnow().isoformat()
        
        except Exception as e:
            self.logger.error("Failed to update carrier selection metrics", error=str(e), carrier_id=carrier_id)
    
    async def _handle_warehouse_selected(self, message: AgentMessage):
        """Handle warehouse selection to select carrier."""
        payload = message.payload
        order_id = payload.get("order_id")
        warehouse_id = payload.get("warehouse_id")
        shipping_address = payload.get("shipping_address")
        package_details = payload.get("package_details")
        
        if order_id and warehouse_id and shipping_address and package_details:
            try:
                # Create carrier selection request
                selection_request = {
                    "order_id": order_id,
                    "warehouse_id": warehouse_id,
                    "package_details": package_details,
                    "delivery_requirements": {
                        "destination_country": shipping_address.get("country", "France"),
                        "destination_postal_code": shipping_address.get("postal_code", ""),
                        "destination_city": shipping_address.get("city", ""),
                        "service_level": "standard"
                    }
                }
                
                # Select optimal carrier
                await self._select_optimal_carrier(selection_request)
                
            except Exception as e:
                self.logger.error("Failed to handle warehouse selected", error=str(e), order_id=order_id)
                
                # Send error notification
                await self.send_message(
                    recipient_agent="monitoring_agent",
                    message_type=MessageType.ERROR_DETECTED,
                    payload={
                        "agent_id": self.agent_id,
                        "error_type": "carrier_selection_failed",
                        "order_id": order_id,
                        "message": f"Failed to select carrier: {str(e)}"
                    }
                )
    
    async def _handle_order_updated(self, message: AgentMessage):
        """Handle order status updates."""
        payload = message.payload
        order_id = payload.get("order_id")
        new_status = payload.get("new_status")
        
        # Track delivery performance when order is delivered
        if new_status == "delivered":
            # Update carrier performance metrics
            # This would typically involve checking if delivery was on time
            self.logger.info("Order delivered, updating carrier performance", order_id=order_id)
    
    async def _update_carrier_performance(self):
        """Background task to update carrier performance metrics."""
        while not self.shutdown_event.is_set():
            try:
                # Update performance metrics from various sources
                # This would typically pull data from carrier APIs, customer feedback, etc.
                
                for carrier_id in self.carrier_performance:
                    # Simulate metric updates
                    import random
                    
                    metrics = self.carrier_performance[carrier_id]
                    
                    # Slightly adjust metrics to simulate real-world changes
                    metrics["on_time_delivery_rate"] += random.uniform(-1.0, 1.0)
                    metrics["on_time_delivery_rate"] = max(70.0, min(99.0, metrics["on_time_delivery_rate"]))
                    
                    metrics["customer_satisfaction"] += random.uniform(-0.1, 0.1)
                    metrics["customer_satisfaction"] = max(3.0, min(5.0, metrics["customer_satisfaction"]))
                    
                    metrics["last_updated"] = datetime.utcnow().isoformat()
                
                # Sleep for 1 hour before next update
                await asyncio.sleep(3600)
            
            except Exception as e:
                self.logger.error("Error updating carrier performance", error=str(e))
                await asyncio.sleep(1800)  # Wait 30 minutes on error
    
    async def _monitor_carrier_capacity(self):
        """Background task to monitor carrier capacity and availability."""
        while not self.shutdown_event.is_set():
            try:
                # Monitor carrier capacity and send alerts if needed
                for carrier_id, performance in self.carrier_performance.items():
                    shipments_this_month = performance.get("shipments_this_month", 0)
                    
                    # Alert if carrier is getting overloaded
                    if shipments_this_month > 800:  # Threshold for high volume
                        await self.send_message(
                            recipient_agent="monitoring_agent",
                            message_type=MessageType.RISK_ALERT,
                            payload={
                                "alert_type": "high_carrier_volume",
                                "carrier_id": carrier_id,
                                "shipments_this_month": shipments_this_month,
                                "severity": "warning"
                            }
                        )
                
                # Sleep for 30 minutes before next check
                await asyncio.sleep(1800)
            
            except Exception as e:
                self.logger.error("Error monitoring carrier capacity", error=str(e))
                await asyncio.sleep(3600)  # Wait 1 hour on error


# FastAPI app instance for running the agent as a service
app = FastAPI(title="Carrier Selection Agent", version="1.0.0")

# Global agent instance
carrier_selection_agent: Optional[CarrierSelectionAgent] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the Carrier Selection Agent on startup."""
    global carrier_selection_agent
    carrier_selection_agent = CarrierSelectionAgent()
    await carrier_selection_agent.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup the Carrier Selection Agent on shutdown."""
    global carrier_selection_agent
    if carrier_selection_agent:
        await carrier_selection_agent.stop()


# Include agent routes
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if carrier_selection_agent:
        health_status = carrier_selection_agent.get_health_status()
        return {"status": "healthy", "agent_status": health_status.dict()}
    return {"status": "unhealthy", "message": "Agent not initialized"}


# Mount agent's FastAPI app
app.mount("/api/v1", carrier_selection_agent.app if carrier_selection_agent else FastAPI())


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
        password=os.getenv("POSTGRES_PASSWORD", "postgres123")
    )
    initialize_database_manager(db_config)
    
    # Run the agent
    uvicorn.run(
        "carrier_selection_agent:app",
        host="0.0.0.0",
        port=8005,
        reload=False,
        log_level="info"
    )
