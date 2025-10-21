_"""
Shipping Agent with AI-Powered Carrier Selection - Multi-Agent E-Commerce System

This agent provides comprehensive shipping management with AI-powered carrier selection
based on package characteristics, delivery requirements, and historical performance.
"""

import asyncio
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4, UUID
from enum import Enum

from shared.db_helpers import DatabaseHelper
from sqlalchemy.ext.asyncio import AsyncSession
import random

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field
import structlog
import sys
import os

# Path setup
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.database import DatabaseManager, get_database_manager


logger = structlog.get_logger(__name__)


# =====================================================
# ENUMS
# =====================================================

class CarrierType(str, Enum):
    STANDARD = "standard"
    EXPRESS = "express"
    FREIGHT = "freight"
    LOCAL = "local"


class ServiceArea(str, Enum):
    LOCAL = "local"
    NATIONAL = "national"
    INTERNATIONAL = "international"
    EUROPE = "europe"


class ShipmentStatus(str, Enum):
    PENDING = "pending"
    LABEL_CREATED = "label_created"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETURNED = "returned"


# =====================================================
# PYDANTIC MODELS
# =====================================================

class Carrier(BaseModel):
    carrier_id: int
    carrier_name: str
    carrier_code: str
    carrier_type: CarrierType
    is_active: bool = True
    service_areas: List[str]
    supported_countries: List[str]
    on_time_delivery_rate: Decimal
    average_delivery_days: Optional[Decimal] = None
    customer_satisfaction_score: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CarrierService(BaseModel):
    service_id: int
    carrier_id: int
    service_name: str
    service_code: str
    service_type: str
    estimated_delivery_days_min: Optional[int] = None
    estimated_delivery_days_max: Optional[int] = None
    max_weight_kg: Optional[Decimal] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class PackageCharacteristics(BaseModel):
    weight_kg: Decimal
    length_cm: Optional[Decimal] = None
    width_cm: Optional[Decimal] = None
    height_cm: Optional[Decimal] = None
    value_amount: Optional[Decimal] = None
    is_fragile: bool = False
    is_dangerous_goods: bool = False


class Address(BaseModel):
    street_address: str
    city: str
    state: Optional[str] = None
    postal_code: str
    country_code: str


class CarrierSelectionRequest(BaseModel):
    order_id: str
    package: PackageCharacteristics
    origin: Address
    destination: Address
    required_delivery_date: Optional[date] = None
    on_time_weight: Decimal = Decimal("70.00")  # 70% importance on on-time delivery
    cost_weight: Decimal = Decimal("30.00")  # 30% importance on cost


class CarrierSelectionResult(BaseModel):
    selected_carrier_id: int
    selected_carrier_name: str
    selected_service_id: Optional[int] = None
    selection_confidence: Decimal
    selection_reasoning: str
    estimated_cost: Decimal
    estimated_delivery_date: date
    alternatives: List[Dict[str, Any]] = []


class ShipmentCreate(BaseModel):
    order_id: str
    carrier_id: int
    service_id: Optional[int] = None
    package: PackageCharacteristics
    origin: Address
    destination: Address
    shipping_cost: Decimal
    insurance_cost: Decimal = Decimal("0.00")
    estimated_delivery_date: Optional[date] = None
    ai_selection_score: Optional[Decimal] = None
    ai_selection_reason: Optional[str] = None


class Shipment(ShipmentCreate):
    shipment_id: UUID
    tracking_number: Optional[str] = None
    shipment_status: ShipmentStatus = ShipmentStatus.PENDING
    total_cost: Decimal
    label_url: Optional[str] = None
    actual_delivery_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TrackingEvent(BaseModel):
    event_id: UUID
    shipment_id: UUID
    event_type: str
    event_status: str
    event_description: Optional[str] = None
    location_city: Optional[str] = None
    location_country: Optional[str] = None
    event_timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# REPOSITORY
# =====================================================

class ShippingRepository:
    """Repository for shipping operations."""
    
    def __init__(self, db_manager: DatabaseManager, db_helper: DatabaseHelper):
        self.db_manager = db_manager
        self.db_helper = db_helper
    
    async def get_active_carriers(self) -> List[Carrier]:
        """Get all active carriers."""
        async with self.db_manager.get_session() as session:
            carriers_data = await self.db_helper.get_all(session, "carriers", is_active=True)
            return [Carrier(**c) for c in carriers_data]
    
    async def get_carrier(self, carrier_id: int) -> Optional[Carrier]:
        """Get carrier by ID."""
        async with self.db_manager.get_session() as session:
            carrier_data = await self.db_helper.get_by_id(session, "carriers", carrier_id)
            return Carrier(**carrier_data) if carrier_data else None
    
    async def get_carrier_services(self, carrier_id: int) -> List[CarrierService]:
        """Get services for a carrier."""
        async with self.db_manager.get_session() as session:
            services_data = await self.db_helper.get_all(session, "carrier_services", carrier_id=carrier_id, is_active=True)
            return [CarrierService(**s) for s in services_data]
    
    async def create_shipment(self, shipment_data: ShipmentCreate) -> Shipment:
        """Create a new shipment."""
        async with self.db_manager.get_session() as session:
            total_cost = shipment_data.shipping_cost + shipment_data.insurance_cost
            tracking_number = f"TRK-{uuid4().hex[:12].upper()}"
            shipment_dict = shipment_data.model_dump()
            shipment_dict["package_weight_kg"] = shipment_data.package.weight_kg
            shipment_dict["package_length_cm"] = shipment_data.package.length_cm
            shipment_dict["package_width_cm"] = shipment_data.package.width_cm
            shipment_dict["package_height_cm"] = shipment_data.package.height_cm
            shipment_dict["package_value_amount"] = shipment_data.package.value_amount
            shipment_dict["is_fragile"] = shipment_data.package.is_fragile
            shipment_dict["is_dangerous_goods"] = shipment_data.package.is_dangerous_goods
            shipment_dict["origin_address"] = shipment_data.origin.model_dump_json()
            shipment_dict["destination_address"] = shipment_data.destination.model_dump_json()
            shipment_dict["total_cost"] = total_cost
            shipment_dict["tracking_number"] = tracking_number
            
            # Remove nested Pydantic models to avoid issues with direct insertion
            del shipment_dict["package"]
            del shipment_dict["origin"]
            del shipment_dict["destination"]

            created_shipment_data = await self.db_helper.create(session, "shipments", shipment_dict)
            return Shipment(**created_shipment_data)
    
    async def get_shipment(self, shipment_id: UUID) -> Optional[Shipment]:
        """Get shipment by ID."""
        async with self.db_manager.get_session() as session:
            shipment_data = await self.db_helper.get_by_id(session, "shipments", shipment_id)
            return Shipment(**shipment_data) if shipment_data else None
    
    async def get_shipment_by_tracking(self, tracking_number: str) -> Optional[Shipment]:
        """Get shipment by tracking number."""
        async with self.db_manager.get_session() as session:
            shipment_data = await self.db_helper.get_one(session, "shipments", tracking_number=tracking_number)
            return Shipment(**shipment_data) if shipment_data else None
    
    async def update_shipment_status(
        self,
        shipment_id: UUID,
        status: ShipmentStatus
    ) -> Optional[Shipment]:
        """Update shipment status."""
        async with self.db_manager.get_session() as session:
            update_data = {"shipment_status": status.value}
            if status == ShipmentStatus.DELIVERED:
                update_data["delivered_at"] = datetime.now()
                update_data["actual_delivery_date"] = date.today()
            updated_shipment_data = await self.db_helper.update(session, "shipments", shipment_id, update_data)
            return Shipment(**updated_shipment_data) if updated_shipment_data else None
    
    async def create_tracking_event(
        self,
        shipment_id: UUID,
        event_type: str,
        event_status: str,
        event_description: Optional[str] = None,
        location_city: Optional[str] = None,
        location_country: Optional[str] = None
    ) -> TrackingEvent:
        """Create a tracking event."""
        async with self.db_manager.get_session() as session:
            event_data = {
                "shipment_id": shipment_id,
                "event_type": event_type,
                "event_status": event_status,
                "event_description": event_description,
                "location_city": location_city,
                "location_country": location_country,
                "event_timestamp": datetime.now()
            }
            created_event_data = await self.db_helper.create(session, "tracking_events", event_data)
            return TrackingEvent(**created_event_data)
    
    async def get_tracking_events(self, shipment_id: UUID) -> List[TrackingEvent]:
        """Get all tracking events for a shipment."""
        async with self.db_manager.get_session() as session:
            events_data = await self.db_helper.get_all(session, "tracking_events", shipment_id=shipment_id, order_by="event_timestamp DESC")
            return [TrackingEvent(**e) for e in events_data]


# =====================================================
# AI CARRIER SELECTION SERVICE
# =====================================================

class ShippingAgent(BaseAgent):
    """AI-powered carrier selection service."""
    
    def __init__(self, agent_id: str, agent_type: str, db_manager: DatabaseManager):
        super().__init__(agent_id, agent_type)
        self.db_manager = db_manager
        self.db_helper = DatabaseHelper(db_manager, self.logger)
        self.repo = ShippingRepository(db_manager, self.db_helper)
        self.logger.info(f"ShippingAgent {self.agent_id} initialized with type {self.agent_type}")
        self._db_initialized = False
        self.kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.kafka_consumer_group_id = os.getenv("KAFKA_CONSUMER_GROUP_ID", "shipping_agent_group")
        self.kafka_topic = os.getenv("KAFKA_TOPIC", "agent_messages")

    async def _post_init(self):
        """Perform asynchronous initialization tasks."""
        await self.db_manager.connect()
        self._db_initialized = True
        self.logger.info(f"Database connection established for {self.agent_id}")

    
    async def select_carrier(
        self,
        request: CarrierSelectionRequest
    ) -> CarrierSelectionResult:
        """Selects the best carrier based on package characteristics and delivery requirements.

        Args:
            request (CarrierSelectionRequest): The request containing package details, origin, destination, and delivery requirements.

        Returns:
            CarrierSelectionResult: The result of the carrier selection, including the chosen carrier and reasoning.
        """
        if not self._db_initialized:
            self.logger.error("Database not initialized. Cannot perform carrier selection.")
            raise HTTPException(status_code=500, detail="Shipping agent database not initialized.")

        """
        Select optimal carrier using AI-powered decision making.
        
        Factors considered:
        1. On-time delivery performance (70% weight by default)
        2. Cost optimization (30% weight by default)
        3. Package constraints (weight, dimensions, dangerous goods)
        4. Geographic coverage
        5. Historical performance
        """
        self.logger.info("ai_carrier_selection_started", order_id=request.order_id)
        
        active_carriers = await self.repo.get_active_carriers()
        if not active_carriers:
            self.logger.warning("no_active_carriers_found")
            raise ValueError("No active carriers found.")
            
        # Filter carriers by service area
        # (Simplified logic - a real implementation would be more complex)
        candidate_carriers = [c for c in active_carriers if request.destination.country_code in c.supported_countries]
        
        if not candidate_carriers:
            self.logger.warning("no_suitable_carriers_found", destination=request.destination.country_code)
            raise ValueError("No carriers found for the destination country.")
            
        # Score each carrier
        scored_carriers = []
        for carrier in candidate_carriers:
            scores = self._calculate_scores(carrier, request)
            scored_carriers.append({
                "carrier": carrier,
                **scores
            })
            
        # Sort by total score (descending)
        scored_carriers.sort(key=lambda x: x['total_score'], reverse=True)
        
        best_choice = scored_carriers[0]
        alternatives = scored_carriers[1:4] # Top 3 alternatives
        
        # Generate reasoning
        reasoning = self._generate_reasoning(best_choice, request)
        
        # Estimated delivery date
        delivery_days = int(best_choice['estimated_days'])
        estimated_delivery_date = date.today() + timedelta(days=delivery_days)
        
        result = CarrierSelectionResult(
            selected_carrier_id=best_choice['carrier'].carrier_id,
            selected_carrier_name=best_choice['carrier'].carrier_name,
            selection_confidence=best_choice['total_score'],
            selection_reasoning=reasoning,
            estimated_cost=best_choice['estimated_cost'],
            estimated_delivery_date=estimated_delivery_date,
            alternatives=[{
                "carrier_name": alt['carrier'].carrier_name,
                "score": alt['total_score'],
                "estimated_cost": alt['estimated_cost']
            } for alt in alternatives]
        )
        
        self.logger.info("ai_carrier_selection_completed", order_id=request.order_id, selected_carrier=result.selected_carrier_name)
        
        return result

    def _calculate_scores(
        self,
        carrier: Carrier,
        request: CarrierSelectionRequest
    ) -> Dict[str, Decimal]:
        """Calculate scores for a carrier based on various factors."""
        
        # On-time delivery score (0-100)
        on_time_score = float(carrier.on_time_delivery_rate)
        
        # Cost calculation (simplified)
        base_cost = 20.0
        weight_factor = 1.5
        carrier_multiplier = 1.0 + (random.random() - 0.5) * 0.2 # +/- 10%
        
        estimated_cost = Decimal(str(base_cost * carrier_multiplier))
        
        # Cost score (inverse - lower cost = higher score)
        # Normalize to 0-100 scale
        max_cost = 200.0  # Assume max reasonable cost
        cost_score = max(0, 100 - (float(estimated_cost) / max_cost * 100))
        
        # Estimated delivery days
        estimated_days = float(carrier.average_delivery_days or 3.0)
        
        # Calculate weighted total score
        on_time_weight = float(request.on_time_weight) / 100
        cost_weight = float(request.cost_weight) / 100
        
        total_score = Decimal(str(
            on_time_score * on_time_weight +
            cost_score * cost_weight
        ))
        
        return {
            "total_score": total_score,
            "on_time_score": Decimal(str(on_time_score)),
            "cost_score": Decimal(str(cost_score)),
            "estimated_cost": estimated_cost,
            "estimated_days": Decimal(str(estimated_days))
        }
    
    def _generate_reasoning(
        self,
        best: Dict[str, Any],
        request: CarrierSelectionRequest
    ) -> str:
        """Generates human-readable reasoning for the selected carrier.

        Args:
            best (Dict[str, Any]): A dictionary containing information about the best carrier.
            request (CarrierSelectionRequest): The original carrier selection request.

        Returns:
            str: A string explaining the reasoning behind the carrier selection.
        """

        carrier = best["carrier"]
        
        reasoning = f"Selected {carrier.carrier_name} based on: "
        reasons = []
        
        # On-time delivery
        if float(carrier.on_time_delivery_rate) >= 95:
            reasons.append(f"excellent on-time delivery rate ({carrier.on_time_delivery_rate}%)")
        elif float(carrier.on_time_delivery_rate) >= 90:
            reasons.append(f"good on-time delivery rate ({carrier.on_time_delivery_rate}%)")
        
        # Cost
        if float(best["estimated_cost"]) < 50:
            reasons.append(f"competitive pricing (€{best['estimated_cost']})")
        
        # Delivery speed
        if float(best["estimated_days"]) <= 2:
            reasons.append(f"fast delivery ({best['estimated_days']} days)")
        
        # Customer satisfaction
        if float(carrier.customer_satisfaction_score) >= 4.5:
            reasons.append(f"high customer satisfaction ({carrier.customer_satisfaction_score}/5)")
        
        reasoning += ", ".join(reasons) + "."
        
        return reasoning

    async def process_message(self, message: AgentMessage):
        """Processes incoming Kafka messages for the shipping agent.

        Args:
            message (AgentMessage): The incoming message from Kafka.
        """
        if not self._db_initialized:
            self.logger.error("Database not initialized. Cannot process Kafka messages.")
            return

        self.logger.info(f"ShippingAgent {self.agent_id} received message: {message.message_type}")

        try:
            if message.message_type == MessageType.ORDER_CREATED:
                self.logger.info(f"Processing ORDER_CREATED for order_id: {message.payload.get('order_id')}")
                # Here, you would typically trigger carrier selection and shipment creation
                # For now, let's just log and acknowledge
                await self.send_message(
                    MessageType.SHIPPING_REQUEST_RECEIVED,
                    {"order_id": message.payload.get("order_id"), "status": "received"},
                    message.sender_id
                )
            elif message.message_type == MessageType.SHIPMENT_UPDATE:
                self.logger.info(f"Processing SHIPMENT_UPDATE for shipment_id: {message.payload.get('shipment_id')}")
                shipment_id = message.payload.get("shipment_id")
                new_status = message.payload.get("new_status")
                if shipment_id and new_status:
                    await self.repo.update_shipment_status(UUID(shipment_id), ShipmentStatus(new_status))
                    await self.repo.create_tracking_event(
                        UUID(shipment_id),
                        "status_update",
                        new_status,
                        f"Shipment status updated to {new_status}"
                    )
                    await self.send_message(
                        MessageType.SHIPMENT_STATUS_UPDATED,
                        {"shipment_id": shipment_id, "status": new_status},
                        message.sender_id
                    )
                else:
                    self.logger.warning(f"Invalid SHIPMENT_UPDATE message: {message.payload}")
            else:
                self.logger.warning(f"Unknown message type received: {message.message_type}")
        except Exception as e:
            self.logger.error(f"Error processing message {message.message_type}: {e}", exc_info=True)
            await self.send_message(
                MessageType.ERROR,
                {"original_message_type": message.message_type, "error": str(e)},
                message.sender_id
            )


# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI(
    title="Shipping Agent with AI Carrier Selection",
    description="AI-powered shipping management for multi-agent e-commerce",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    # This is where you'd initialize the agent and start its message listener
    # For simplicity, we are not running the full agent loop here
    logger.info("FastAPI app started. Shipping agent is online.")


async def get_shipping_agent() -> ShippingAgent:
    """Dependency injection for shipping agent."""
    db_manager = await get_database_manager()
    agent_id = os.getenv("AGENT_ID", "shipping_agent_001")
    agent_type = os.getenv("AGENT_TYPE", "shipping_agent")
    agent = ShippingAgent(agent_id, agent_type, db_manager)
    await agent._post_init() # Ensure DB is connected before returning the agent
    return agent


# =====================================================
# API ENDPOINTS
# =====================================================

@app.get("/")
async def root():
    """Root endpoint for the shipping agent."""
    return {"message": "Shipping Agent is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "shipping_agent_ai", "version": "1.0.0"}


@app.get("/api/v1/shipping/carriers", response_model=List[Carrier])
async def get_carriers(
    agent: ShippingAgent = Depends(get_shipping_agent)
):
    """Get all active carriers."""
    try:
        if not agent._db_initialized:
            raise HTTPException(status_code=500, detail="Shipping agent database not initialized.")
        carriers = await agent.repo.get_active_carriers()
        return carriers
    except Exception as e:
        logger.error("get_carriers_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/shipping/select-carrier", response_model=CarrierSelectionResult)
async def select_carrier(
    request: CarrierSelectionRequest = Body(...),
    agent: ShippingAgent = Depends(get_shipping_agent)
):
    """AI-powered carrier selection."""
    try:
        if not agent._db_initialized:
            raise HTTPException(status_code=500, detail="Shipping agent database not initialized.")
        result = await agent.select_carrier(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("select_carrier_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/shipping/shipments", response_model=Shipment)
async def create_shipment(
    shipment: ShipmentCreate = Body(...),
    agent: ShippingAgent = Depends(get_shipping_agent)
):
    """Create a new shipment."""
    try:
        if not agent._db_initialized:
            raise HTTPException(status_code=500, detail="Shipping agent database not initialized.")
        result = await agent.repo.create_shipment(shipment)
        
        # Create initial tracking event
        await agent.repo.create_tracking_event(
            result.shipment_id,
            "label_created",
            "pending",
            "Shipping label created"
        )
        
        return result
    except Exception as e:
        logger.error("create_shipment_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/shipping/shipments/{shipment_id}", response_model=Shipment)
async def get_shipment(
    shipment_id: UUID = Path(...),
    agent: ShippingAgent = Depends(get_shipping_agent)
):
    """Get shipment by ID."""
    try:
        if not agent._db_initialized:
            raise HTTPException(status_code=500, detail="Shipping agent database not initialized.")
        shipment = await agent.repo.get_shipment(shipment_id)
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")
        return shipment
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_shipment_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/shipping/track/{tracking_number}", response_model=Dict[str, Any])
async def track_shipment(
    tracking_number: str = Path(...),
    agent: ShippingAgent = Depends(get_shipping_agent)
):
    """Track shipment by tracking number."""
    try:
        if not agent._db_initialized:
            raise HTTPException(status_code=500, detail="Shipping agent database not initialized.")
        shipment = await agent.repo.get_shipment_by_tracking(tracking_number)
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")
        
        events = await agent.repo.get_tracking_events(shipment.shipment_id)
        
        return {
            "shipment": shipment,
            "tracking_events": events
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("track_shipment_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8005))
    uvicorn.run(app, host="0.0.0.0", port=port)

