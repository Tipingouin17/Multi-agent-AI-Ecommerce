"""
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
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def get_active_carriers(self) -> List[Carrier]:
        """Get all active carriers."""
        query = "SELECT * FROM carriers WHERE is_active = true ORDER BY carrier_name"
        results = await self.db.fetch_all(query)
        return [Carrier(**r) for r in results]
    
    async def get_carrier(self, carrier_id: int) -> Optional[Carrier]:
        """Get carrier by ID."""
        query = "SELECT * FROM carriers WHERE carrier_id = $1"
        result = await self.db.fetch_one(query, carrier_id)
        return Carrier(**result) if result else None
    
    async def get_carrier_services(self, carrier_id: int) -> List[CarrierService]:
        """Get services for a carrier."""
        query = "SELECT * FROM carrier_services WHERE carrier_id = $1 AND is_active = true"
        results = await self.db.fetch_all(query, carrier_id)
        return [CarrierService(**r) for r in results]
    
    async def create_shipment(self, shipment_data: ShipmentCreate) -> Shipment:
        """Create a new shipment."""
        query = """
            INSERT INTO shipments (order_id, carrier_id, service_id, package_weight_kg,
                                  package_length_cm, package_width_cm, package_height_cm,
                                  package_value_amount, is_fragile, is_dangerous_goods,
                                  origin_address, destination_address, shipping_cost,
                                  insurance_cost, total_cost, estimated_delivery_date,
                                  ai_selection_score, ai_selection_reason, tracking_number)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
            RETURNING *
        """
        total_cost = shipment_data.shipping_cost + shipment_data.insurance_cost
        tracking_number = f"TRK-{uuid4().hex[:12].upper()}"
        
        result = await self.db.fetch_one(
            query,
            shipment_data.order_id,
            shipment_data.carrier_id,
            shipment_data.service_id,
            shipment_data.package.weight_kg,
            shipment_data.package.length_cm,
            shipment_data.package.width_cm,
            shipment_data.package.height_cm,
            shipment_data.package.value_amount,
            shipment_data.package.is_fragile,
            shipment_data.package.is_dangerous_goods,
            shipment_data.origin.model_dump_json(),
            shipment_data.destination.model_dump_json(),
            shipment_data.shipping_cost,
            shipment_data.insurance_cost,
            total_cost,
            shipment_data.estimated_delivery_date,
            shipment_data.ai_selection_score,
            shipment_data.ai_selection_reason,
            tracking_number
        )
        return Shipment(**result)
    
    async def get_shipment(self, shipment_id: UUID) -> Optional[Shipment]:
        """Get shipment by ID."""
        query = "SELECT * FROM shipments WHERE shipment_id = $1"
        result = await self.db.fetch_one(query, shipment_id)
        return Shipment(**result) if result else None
    
    async def get_shipment_by_tracking(self, tracking_number: str) -> Optional[Shipment]:
        """Get shipment by tracking number."""
        query = "SELECT * FROM shipments WHERE tracking_number = $1"
        result = await self.db.fetch_one(query, tracking_number)
        return Shipment(**result) if result else None
    
    async def update_shipment_status(
        self,
        shipment_id: UUID,
        status: ShipmentStatus
    ) -> Optional[Shipment]:
        """Update shipment status."""
        query = """
            UPDATE shipments 
            SET shipment_status = $2,
                delivered_at = CASE WHEN $2 = 'delivered' THEN CURRENT_TIMESTAMP ELSE delivered_at END,
                actual_delivery_date = CASE WHEN $2 = 'delivered' THEN CURRENT_DATE ELSE actual_delivery_date END
            WHERE shipment_id = $1
            RETURNING *
        """
        result = await self.db.fetch_one(query, shipment_id, status.value)
        return Shipment(**result) if result else None
    
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
        query = """
            INSERT INTO tracking_events (shipment_id, event_type, event_status,
                                        event_description, location_city, location_country,
                                        event_timestamp)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
        """
        result = await self.db.fetch_one(
            query, shipment_id, event_type, event_status, event_description,
            location_city, location_country, datetime.utcnow()
        )
        return TrackingEvent(**result)
    
    async def get_tracking_events(self, shipment_id: UUID) -> List[TrackingEvent]:
        """Get all tracking events for a shipment."""
        query = """
            SELECT * FROM tracking_events 
            WHERE shipment_id = $1 
            ORDER BY event_timestamp DESC
        """
        results = await self.db.fetch_all(query, shipment_id)
        return [TrackingEvent(**r) for r in results]
    
    async def log_ai_selection(
        self,
        order_id: str,
        package: PackageCharacteristics,
        origin: Address,
        destination: Address,
        selected_carrier_id: int,
        selected_service_id: Optional[int],
        confidence: Decimal,
        reasoning: str,
        alternatives: List[Dict[str, Any]],
        on_time_weight: Decimal,
        cost_weight: Decimal
    ) -> UUID:
        """Log AI carrier selection decision."""
        query = """
            INSERT INTO ai_carrier_selection_log (
                order_id, package_characteristics, origin_location, destination_location,
                selected_carrier_id, selected_service_id, selection_confidence,
                selection_reasoning, alternatives_evaluated, on_time_weight, cost_weight
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING selection_id
        """
        result = await self.db.fetch_one(
            query, order_id, package.model_dump_json(), origin.model_dump_json(),
            destination.model_dump_json(), selected_carrier_id, selected_service_id,
            confidence, reasoning, str(alternatives), on_time_weight, cost_weight
        )
        return result['selection_id']


# =====================================================
# AI CARRIER SELECTION SERVICE
# =====================================================

class AICarrierSelectionService:
    """AI-powered carrier selection service."""
    
    def __init__(self, repo: ShippingRepository):
        self.repo = repo
    
    async def select_carrier(
        self,
        request: CarrierSelectionRequest
    ) -> CarrierSelectionResult:
        """
        Select optimal carrier using AI-powered decision making.
        
        Factors considered:
        1. On-time delivery performance (70% weight by default)
        2. Cost optimization (30% weight by default)
        3. Package constraints (weight, dimensions, dangerous goods)
        4. Geographic coverage
        5. Historical performance
        """
        # Get all active carriers
        carriers = await self.repo.get_active_carriers()
        
        if not carriers:
            raise ValueError("No active carriers available")
        
        # Filter carriers by capabilities
        eligible_carriers = self._filter_eligible_carriers(
            carriers, request.package, request.destination
        )
        
        if not eligible_carriers:
            raise ValueError("No eligible carriers found for this shipment")
        
        # Score each carrier
        scored_carriers = []
        for carrier in eligible_carriers:
            score = await self._score_carrier(carrier, request)
            scored_carriers.append({
                "carrier": carrier,
                "score": score["total_score"],
                "on_time_score": score["on_time_score"],
                "cost_score": score["cost_score"],
                "estimated_cost": score["estimated_cost"],
                "estimated_days": score["estimated_days"]
            })
        
        # Sort by score (highest first)
        scored_carriers.sort(key=lambda x: x["score"], reverse=True)
        
        # Select best carrier
        best = scored_carriers[0]
        alternatives = scored_carriers[1:4]  # Top 3 alternatives
        
        # Calculate estimated delivery date
        estimated_delivery_date = date.today() + timedelta(days=int(best["estimated_days"]))
        
        # Generate reasoning
        reasoning = self._generate_reasoning(best, request)
        
        # Log AI selection
        await self.repo.log_ai_selection(
            request.order_id,
            request.package,
            request.origin,
            request.destination,
            best["carrier"].carrier_id,
            None,  # service_id
            best["score"],
            reasoning,
            [{"carrier_id": alt["carrier"].carrier_id, "score": float(alt["score"])} 
             for alt in alternatives],
            request.on_time_weight,
            request.cost_weight
        )
        
        logger.info(
            "ai_carrier_selected",
            order_id=request.order_id,
            carrier=best["carrier"].carrier_name,
            confidence=float(best["score"]),
            cost=float(best["estimated_cost"])
        )
        
        return CarrierSelectionResult(
            selected_carrier_id=best["carrier"].carrier_id,
            selected_carrier_name=best["carrier"].carrier_name,
            selection_confidence=best["score"],
            selection_reasoning=reasoning,
            estimated_cost=best["estimated_cost"],
            estimated_delivery_date=estimated_delivery_date,
            alternatives=[
                {
                    "carrier_id": alt["carrier"].carrier_id,
                    "carrier_name": alt["carrier"].carrier_name,
                    "score": float(alt["score"]),
                    "estimated_cost": float(alt["estimated_cost"])
                }
                for alt in alternatives
            ]
        )
    
    def _filter_eligible_carriers(
        self,
        carriers: List[Carrier],
        package: PackageCharacteristics,
        destination: Address
    ) -> List[Carrier]:
        """Filter carriers by capabilities."""
        eligible = []
        
        for carrier in carriers:
            # Check country support
            if destination.country_code not in carrier.supported_countries:
                continue
            
            # Check dangerous goods support
            if package.is_dangerous_goods and not carrier.supports_dangerous_goods:
                continue
            
            eligible.append(carrier)
        
        return eligible
    
    async def _score_carrier(
        self,
        carrier: Carrier,
        request: CarrierSelectionRequest
    ) -> Dict[str, Any]:
        """Score a carrier based on multiple factors."""
        # On-time delivery score (0-100)
        on_time_score = float(carrier.on_time_delivery_rate)
        
        # Estimate cost (simplified - in production, use actual rate calculation)
        base_cost = float(request.package.weight_kg) * 5.0  # €5 per kg base rate
        carrier_multiplier = 1.0
        
        if carrier.carrier_type == CarrierType.EXPRESS:
            carrier_multiplier = 1.5
        elif carrier.carrier_type == CarrierType.STANDARD:
            carrier_multiplier = 1.0
        elif carrier.carrier_type == CarrierType.LOCAL:
            carrier_multiplier = 0.8
        
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
        """Generate human-readable reasoning for carrier selection."""
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


# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI(
    title="Shipping Agent with AI Carrier Selection",
    description="AI-powered shipping management for multi-agent e-commerce",
    version="1.0.0"
)


async def get_shipping_service() -> AICarrierSelectionService:
    """Dependency injection for shipping service."""
    db_manager = await get_database_manager()
    repo = ShippingRepository(db_manager)
    return AICarrierSelectionService(repo)


# =====================================================
# API ENDPOINTS
# =====================================================

@app.get("/api/v1/shipping/carriers", response_model=List[Carrier])
async def get_carriers(
    service: AICarrierSelectionService = Depends(get_shipping_service)
):
    """Get all active carriers."""
    try:
        carriers = await service.repo.get_active_carriers()
        return carriers
    except Exception as e:
        logger.error("get_carriers_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/shipping/select-carrier", response_model=CarrierSelectionResult)
async def select_carrier(
    request: CarrierSelectionRequest = Body(...),
    service: AICarrierSelectionService = Depends(get_shipping_service)
):
    """AI-powered carrier selection."""
    try:
        result = await service.select_carrier(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("select_carrier_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/shipping/shipments", response_model=Shipment)
async def create_shipment(
    shipment: ShipmentCreate = Body(...),
    service: AICarrierSelectionService = Depends(get_shipping_service)
):
    """Create a new shipment."""
    try:
        result = await service.repo.create_shipment(shipment)
        
        # Create initial tracking event
        await service.repo.create_tracking_event(
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
    service: AICarrierSelectionService = Depends(get_shipping_service)
):
    """Get shipment by ID."""
    try:
        shipment = await service.repo.get_shipment(shipment_id)
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
    service: AICarrierSelectionService = Depends(get_shipping_service)
):
    """Track shipment by tracking number."""
    try:
        shipment = await service.repo.get_shipment_by_tracking(tracking_number)
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")
        
        events = await service.repo.get_tracking_events(shipment.shipment_id)
        
        return {
            "shipment": shipment,
            "tracking_events": events
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("track_shipment_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "shipping_agent_ai", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)

