"""
Warehouse Selection Agent - Multi-Agent E-commerce System

This agent optimizes warehouse selection for orders based on multiple factors:
- Distance to customer
- Inventory availability
- Warehouse capacity and operational status
- Shipping costs and delivery times
- Load balancing across warehouses
"""

import asyncio
import math
from datetime import datetime, time
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

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
from shared.models import (
    Warehouse, Address, APIResponse
)
from shared.database import DatabaseManager, BaseRepository, get_database_manager


logger = structlog.get_logger(__name__)


class WarehouseSelectionRequest(BaseModel):
    """Request model for warehouse selection."""
    order_id: str
    shipping_address: Address
    items: List[Dict[str, Any]]  # Product ID, quantity, weight, dimensions
    priority: str = "standard"  # standard, express, economy
    max_distance_km: Optional[float] = None


class WarehouseScore(BaseModel):
    """Model for warehouse scoring."""
    warehouse_id: str
    warehouse_name: str
    score: float
    distance_km: float
    estimated_delivery_days: int
    shipping_cost: float
    inventory_availability: float
    capacity_utilization: float
    reasons: List[str]


class WarehouseSelectionResult(BaseModel):
    """Result model for warehouse selection."""
    order_id: str
    selected_warehouse_id: str
    selected_warehouse_name: str
    selection_score: float
    distance_km: float
    estimated_delivery_days: int
    estimated_shipping_cost: float
    alternative_warehouses: List[WarehouseScore]
    selection_reasons: List[str]


class WarehouseRepository(BaseRepository):
    """Repository for warehouse data operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        from shared.models import WarehouseDB
        super().__init__(db_manager, WarehouseDB)
    
    async def find_operational_warehouses(self) -> List[Warehouse]:
        """Find all operational warehouses."""
        # For now, return all warehouses. In production, this would filter by operational status
        records = await self.get_all()
        return [self._to_pydantic(record) for record in records]
    
    async def find_warehouses_within_radius(self, center_lat: float, center_lon: float, radius_km: float) -> List[Warehouse]:
        """Find warehouses within a specific radius."""
        warehouses = await self.find_operational_warehouses()
        
        nearby_warehouses = []
        for warehouse in warehouses:
            if warehouse.address.get("latitude") and warehouse.address.get("longitude"):
                distance = self._calculate_distance(
                    center_lat, center_lon,
                    warehouse.address["latitude"], warehouse.address["longitude"]
                )
                if distance <= radius_km:
                    nearby_warehouses.append(warehouse)
        
        return nearby_warehouses
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula."""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _to_pydantic(self, db_record) -> Warehouse:
        """Convert database record to Pydantic model."""
        return Warehouse(
            id=db_record.id,
            name=db_record.name,
            address=Address(**db_record.address),
            capacity=db_record.capacity,
            operational_hours=db_record.operational_hours,
            contact_email=db_record.contact_email,
            contact_phone=db_record.contact_phone,
            created_at=db_record.created_at,
            updated_at=db_record.updated_at
        )


class WarehouseSelectionAgent(BaseAgent):
    """
    Warehouse Selection Agent handles optimal warehouse selection for orders based on:
    - Geographic proximity to customer
    - Inventory availability
    - Warehouse operational capacity
    - Shipping costs and delivery times
    - Load balancing and efficiency
    """
    
    def __init__(self, **kwargs):
        super().__init__(agent_id="warehouse_selection_agent", **kwargs)
        self.repository: Optional[WarehouseRepository] = None
        self.app = FastAPI(title="Warehouse Selection Agent API", version="1.0.0")
        self.setup_routes()
        
        # Warehouse performance metrics (in production, this would be in a database)
        self.warehouse_metrics: Dict[str, Dict[str, float]] = {}
        
        # Register message handlers
        self.register_handler(MessageType.ORDER_CREATED, self._handle_order_created)
        self.register_handler(MessageType.INVENTORY_UPDATE, self._handle_inventory_update)
    
    async def initialize(self):
        """Initialize the Warehouse Selection Agent."""
        self.logger.info("Initializing Warehouse Selection Agent")
        
        # Initialize database repository
        db_manager = get_database_manager()
        self.repository = WarehouseRepository(db_manager)
        
        # Initialize warehouse metrics
        await self._initialize_warehouse_metrics()
        
        # Start background tasks
        asyncio.create_task(self._update_warehouse_metrics())
        asyncio.create_task(self._monitor_warehouse_performance())
        
        self.logger.info("Warehouse Selection Agent initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up Warehouse Selection Agent")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process warehouse selection business logic."""
        action = data.get("action")
        
        if action == "select_warehouse":
            return await self._select_optimal_warehouse(data["selection_request"])
        elif action == "get_warehouse_scores":
            return await self._get_warehouse_scores(data["selection_request"])
        elif action == "get_warehouse_metrics":
            return await self._get_warehouse_metrics(data.get("warehouse_id"))
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def setup_routes(self):
        """Setup FastAPI routes for the Warehouse Selection Agent."""
        
        @self.app.post("/warehouse-selection", response_model=APIResponse)
        async def select_warehouse(request: WarehouseSelectionRequest):
            """Select optimal warehouse for an order."""
            try:
                result = await self._select_optimal_warehouse(request.dict())
                
                return APIResponse(
                    success=True,
                    message="Warehouse selected successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to select warehouse", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/warehouse-selection/scores", response_model=APIResponse)
        async def get_warehouse_scores(request: WarehouseSelectionRequest):
            """Get scores for all warehouses for an order."""
            try:
                result = await self._get_warehouse_scores(request.dict())
                
                return APIResponse(
                    success=True,
                    message="Warehouse scores calculated successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to calculate warehouse scores", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/warehouses/{warehouse_id}/metrics", response_model=APIResponse)
        async def get_warehouse_metrics(warehouse_id: str):
            """Get performance metrics for a warehouse."""
            try:
                result = await self._get_warehouse_metrics(warehouse_id)
                
                return APIResponse(
                    success=True,
                    message="Warehouse metrics retrieved successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to get warehouse metrics", error=str(e), warehouse_id=warehouse_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/warehouses", response_model=APIResponse)
        async def list_warehouses():
            """List all operational warehouses."""
            try:
                warehouses = await self.repository.find_operational_warehouses()
                
                return APIResponse(
                    success=True,
                    message="Warehouses retrieved successfully",
                    data={"warehouses": [warehouse.dict() for warehouse in warehouses]}
                )
            
            except Exception as e:
                self.logger.error("Failed to list warehouses", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _select_optimal_warehouse(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Select the optimal warehouse for an order."""
        try:
            order_id = request_data["order_id"]
            shipping_address = Address(**request_data["shipping_address"])
            items = request_data["items"]
            priority = request_data.get("priority", "standard")
            max_distance_km = request_data.get("max_distance_km")
            
            # Get warehouse scores
            warehouse_scores = await self._calculate_warehouse_scores(
                shipping_address, items, priority, max_distance_km
            )
            
            if not warehouse_scores:
                raise ValueError("No suitable warehouses found for this order")
            
            # Select the best warehouse (highest score)
            best_warehouse = max(warehouse_scores, key=lambda w: w.score)
            alternative_warehouses = [w for w in warehouse_scores if w.warehouse_id != best_warehouse.warehouse_id]
            
            # Create selection result
            result = WarehouseSelectionResult(
                order_id=order_id,
                selected_warehouse_id=best_warehouse.warehouse_id,
                selected_warehouse_name=best_warehouse.warehouse_name,
                selection_score=best_warehouse.score,
                distance_km=best_warehouse.distance_km,
                estimated_delivery_days=best_warehouse.estimated_delivery_days,
                estimated_shipping_cost=best_warehouse.shipping_cost,
                alternative_warehouses=alternative_warehouses[:3],  # Top 3 alternatives
                selection_reasons=best_warehouse.reasons
            )
            
            # Send warehouse selection notification
            await self.send_message(
                recipient_agent="order_agent",
                message_type=MessageType.WAREHOUSE_SELECTED,
                payload={
                    "order_id": order_id,
                    "warehouse_id": best_warehouse.warehouse_id,
                    "warehouse_name": best_warehouse.warehouse_name,
                    "shipping_address": shipping_address.dict(),
                    "estimated_delivery_days": best_warehouse.estimated_delivery_days,
                    "estimated_shipping_cost": best_warehouse.shipping_cost,
                    "items": items,
                    "package_details": self._calculate_package_details(items)
                }
            )
            
            # Update warehouse metrics
            await self._update_warehouse_selection_metrics(best_warehouse.warehouse_id)
            
            self.logger.info("Warehouse selected", order_id=order_id, warehouse_id=best_warehouse.warehouse_id, score=best_warehouse.score)
            
            return result.dict()
        
        except Exception as e:
            self.logger.error("Failed to select optimal warehouse", error=str(e))
            raise
    
    async def _get_warehouse_scores(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get scores for all warehouses for an order."""
        try:
            shipping_address = Address(**request_data["shipping_address"])
            items = request_data["items"]
            priority = request_data.get("priority", "standard")
            max_distance_km = request_data.get("max_distance_km")
            
            warehouse_scores = await self._calculate_warehouse_scores(
                shipping_address, items, priority, max_distance_km
            )
            
            return {
                "warehouse_scores": [score.dict() for score in warehouse_scores],
                "total_warehouses": len(warehouse_scores)
            }
        
        except Exception as e:
            self.logger.error("Failed to get warehouse scores", error=str(e))
            raise
    
    async def _calculate_warehouse_scores(
        self, 
        shipping_address: Address, 
        items: List[Dict[str, Any]], 
        priority: str,
        max_distance_km: Optional[float]
    ) -> List[WarehouseScore]:
        """Calculate scores for all warehouses."""
        try:
            # Get all operational warehouses
            warehouses = await self.repository.find_operational_warehouses()
            
            if not shipping_address.latitude or not shipping_address.longitude:
                # If no coordinates, use a default scoring method
                self.logger.warning("No coordinates for shipping address, using simplified scoring")
            
            warehouse_scores = []
            
            for warehouse in warehouses:
                try:
                    score_data = await self._score_warehouse(warehouse, shipping_address, items, priority)
                    
                    # Apply distance filter if specified
                    if max_distance_km and score_data["distance_km"] > max_distance_km:
                        continue
                    
                    warehouse_score = WarehouseScore(
                        warehouse_id=warehouse.id,
                        warehouse_name=warehouse.name,
                        score=score_data["total_score"],
                        distance_km=score_data["distance_km"],
                        estimated_delivery_days=score_data["delivery_days"],
                        shipping_cost=score_data["shipping_cost"],
                        inventory_availability=score_data["inventory_score"],
                        capacity_utilization=score_data["capacity_score"],
                        reasons=score_data["reasons"]
                    )
                    
                    warehouse_scores.append(warehouse_score)
                
                except Exception as e:
                    self.logger.error("Failed to score warehouse", error=str(e), warehouse_id=warehouse.id)
            
            # Sort by score (highest first)
            warehouse_scores.sort(key=lambda w: w.score, reverse=True)
            
            return warehouse_scores
        
        except Exception as e:
            self.logger.error("Failed to calculate warehouse scores", error=str(e))
            raise
    
    async def _score_warehouse(
        self, 
        warehouse: Warehouse, 
        shipping_address: Address, 
        items: List[Dict[str, Any]], 
        priority: str
    ) -> Dict[str, Any]:
        """Score a single warehouse for an order."""
        try:
            reasons = []
            
            # 1. Distance Score (40% weight)
            distance_km = self._calculate_distance_to_warehouse(warehouse, shipping_address)
            distance_score = max(0, 100 - (distance_km / 10))  # Decrease by 10 points per 100km
            reasons.append(f"Distance: {distance_km:.1f}km")
            
            # 2. Inventory Availability Score (30% weight)
            inventory_score = await self._calculate_inventory_score(warehouse.id, items)
            if inventory_score >= 90:
                reasons.append("Excellent inventory availability")
            elif inventory_score >= 70:
                reasons.append("Good inventory availability")
            else:
                reasons.append("Limited inventory availability")
            
            # 3. Warehouse Capacity Score (15% weight)
            capacity_score = await self._calculate_capacity_score(warehouse.id)
            if capacity_score >= 80:
                reasons.append("High capacity available")
            elif capacity_score >= 60:
                reasons.append("Moderate capacity available")
            else:
                reasons.append("Limited capacity")
            
            # 4. Operational Efficiency Score (10% weight)
            efficiency_score = await self._calculate_efficiency_score(warehouse.id)
            
            # 5. Priority Adjustment (5% weight)
            priority_score = self._calculate_priority_score(priority, distance_km)
            
            # Calculate weighted total score
            total_score = (
                distance_score * 0.40 +
                inventory_score * 0.30 +
                capacity_score * 0.15 +
                efficiency_score * 0.10 +
                priority_score * 0.05
            )
            
            # Calculate delivery estimate
            delivery_days = self._estimate_delivery_days(distance_km, priority)
            
            # Calculate shipping cost
            package_details = self._calculate_package_details(items)
            shipping_cost = self._estimate_shipping_cost(distance_km, package_details)
            
            return {
                "total_score": round(total_score, 2),
                "distance_km": round(distance_km, 2),
                "delivery_days": delivery_days,
                "shipping_cost": round(shipping_cost, 2),
                "inventory_score": inventory_score,
                "capacity_score": capacity_score,
                "efficiency_score": efficiency_score,
                "reasons": reasons
            }
        
        except Exception as e:
            self.logger.error("Failed to score warehouse", error=str(e), warehouse_id=warehouse.id)
            raise
    
    def _calculate_distance_to_warehouse(self, warehouse: Warehouse, shipping_address: Address) -> float:
        """Calculate distance between warehouse and shipping address."""
        if (not warehouse.address.latitude or not warehouse.address.longitude or
            not shipping_address.latitude or not shipping_address.longitude):
            # If coordinates are missing, use a default distance based on postal codes or cities
            return self._estimate_distance_by_location(warehouse.address, shipping_address)
        
        return self.repository._calculate_distance(
            warehouse.address.latitude, warehouse.address.longitude,
            shipping_address.latitude, shipping_address.longitude
        )
    
    def _estimate_distance_by_location(self, warehouse_address: Address, shipping_address: Address) -> float:
        """Estimate distance when coordinates are not available."""
        # Simple heuristic based on postal codes or cities
        if warehouse_address.city.lower() == shipping_address.city.lower():
            return 10.0  # Same city
        elif warehouse_address.postal_code[:2] == shipping_address.postal_code[:2]:
            return 50.0  # Same region
        else:
            return 200.0  # Different region
    
    async def _calculate_inventory_score(self, warehouse_id: str, items: List[Dict[str, Any]]) -> float:
        """Calculate inventory availability score for a warehouse."""
        try:
            # Request inventory information from inventory agent
            total_items = len(items)
            available_items = 0
            
            for item in items:
                product_id = item.get("product_id")
                required_quantity = item.get("quantity", 1)
                
                if product_id:
                    # In a real implementation, this would query the inventory agent
                    # For now, we'll simulate inventory availability
                    available_quantity = await self._get_product_availability(warehouse_id, product_id)
                    
                    if available_quantity >= required_quantity:
                        available_items += 1
            
            # Calculate percentage of items available
            availability_percentage = (available_items / total_items) * 100 if total_items > 0 else 0
            
            return availability_percentage
        
        except Exception as e:
            self.logger.error("Failed to calculate inventory score", error=str(e), warehouse_id=warehouse_id)
            return 0.0
    
    async def _get_product_availability(self, warehouse_id: str, product_id: str) -> int:
        """Get product availability in a specific warehouse."""
        # This would normally query the inventory agent
        # For now, we'll simulate availability
        import random
        return random.randint(0, 100)
    
    async def _calculate_capacity_score(self, warehouse_id: str) -> float:
        """Calculate warehouse capacity utilization score."""
        try:
            metrics = self.warehouse_metrics.get(warehouse_id, {})
            utilization = metrics.get("capacity_utilization", 50.0)  # Default 50%
            
            # Score inversely related to utilization (lower utilization = higher score)
            capacity_score = max(0, 100 - utilization)
            
            return capacity_score
        
        except Exception as e:
            self.logger.error("Failed to calculate capacity score", error=str(e), warehouse_id=warehouse_id)
            return 50.0
    
    async def _calculate_efficiency_score(self, warehouse_id: str) -> float:
        """Calculate warehouse operational efficiency score."""
        try:
            metrics = self.warehouse_metrics.get(warehouse_id, {})
            
            # Combine multiple efficiency metrics
            order_processing_time = metrics.get("avg_processing_time_hours", 24.0)
            error_rate = metrics.get("error_rate_percent", 5.0)
            on_time_shipment_rate = metrics.get("on_time_shipment_rate", 85.0)
            
            # Calculate efficiency score
            processing_score = max(0, 100 - (order_processing_time - 2) * 10)  # Penalty for slow processing
            error_score = max(0, 100 - error_rate * 10)  # Penalty for errors
            on_time_score = on_time_shipment_rate  # Direct score from on-time rate
            
            efficiency_score = (processing_score + error_score + on_time_score) / 3
            
            return efficiency_score
        
        except Exception as e:
            self.logger.error("Failed to calculate efficiency score", error=str(e), warehouse_id=warehouse_id)
            return 70.0
    
    def _calculate_priority_score(self, priority: str, distance_km: float) -> float:
        """Calculate priority-based score adjustment."""
        if priority == "express":
            # Favor closer warehouses for express delivery
            return max(0, 100 - (distance_km / 5))
        elif priority == "economy":
            # Less penalty for distance in economy mode
            return max(0, 100 - (distance_km / 20))
        else:  # standard
            return max(0, 100 - (distance_km / 10))
    
    def _estimate_delivery_days(self, distance_km: float, priority: str) -> int:
        """Estimate delivery days based on distance and priority."""
        if priority == "express":
            if distance_km <= 50:
                return 1
            elif distance_km <= 200:
                return 2
            else:
                return 3
        elif priority == "economy":
            if distance_km <= 100:
                return 3
            elif distance_km <= 300:
                return 5
            else:
                return 7
        else:  # standard
            if distance_km <= 50:
                return 1
            elif distance_km <= 150:
                return 2
            elif distance_km <= 300:
                return 3
            else:
                return 4
    
    def _calculate_package_details(self, items: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate total package weight and dimensions."""
        total_weight = 0.0
        max_length = 0.0
        max_width = 0.0
        total_height = 0.0
        
        for item in items:
            quantity = item.get("quantity", 1)
            weight = item.get("weight", 0.5)  # Default 0.5kg
            dimensions = item.get("dimensions", {"length": 20, "width": 15, "height": 10})
            
            total_weight += weight * quantity
            max_length = max(max_length, dimensions.get("length", 20))
            max_width = max(max_width, dimensions.get("width", 15))
            total_height += dimensions.get("height", 10) * quantity
        
        return {
            "weight": total_weight,
            "length": max_length,
            "width": max_width,
            "height": min(total_height, 100)  # Cap height at 100cm
        }
    
    def _estimate_shipping_cost(self, distance_km: float, package_details: Dict[str, float]) -> float:
        """Estimate shipping cost based on distance and package details."""
        base_cost = 5.99
        distance_cost = distance_km * 0.02  # 2 cents per km
        weight_cost = package_details["weight"] * 1.50  # €1.50 per kg
        
        # Size surcharge for large packages
        volume = package_details["length"] * package_details["width"] * package_details["height"] / 1000000  # m³
        size_cost = volume * 10.0 if volume > 0.01 else 0.0  # €10 per m³ over 0.01m³
        
        total_cost = base_cost + distance_cost + weight_cost + size_cost
        
        return max(total_cost, 3.99)  # Minimum cost €3.99
    
    async def _get_warehouse_metrics(self, warehouse_id: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics for warehouse(s)."""
        try:
            if warehouse_id:
                metrics = self.warehouse_metrics.get(warehouse_id, {})
                return {"warehouse_id": warehouse_id, "metrics": metrics}
            else:
                return {"all_warehouses": self.warehouse_metrics}
        
        except Exception as e:
            self.logger.error("Failed to get warehouse metrics", error=str(e))
            raise
    
    async def _initialize_warehouse_metrics(self):
        """Initialize warehouse performance metrics."""
        try:
            warehouses = await self.repository.find_operational_warehouses()
            
            for warehouse in warehouses:
                # Initialize with default metrics (in production, load from historical data)
                self.warehouse_metrics[warehouse.id] = {
                    "capacity_utilization": 60.0,  # 60% utilized
                    "avg_processing_time_hours": 4.0,  # 4 hours average processing
                    "error_rate_percent": 2.0,  # 2% error rate
                    "on_time_shipment_rate": 92.0,  # 92% on-time shipments
                    "orders_processed_today": 0,
                    "last_updated": datetime.utcnow().isoformat()
                }
            
            self.logger.info("Warehouse metrics initialized", warehouse_count=len(warehouses))
        
        except Exception as e:
            self.logger.error("Failed to initialize warehouse metrics", error=str(e))
    
    async def _update_warehouse_selection_metrics(self, warehouse_id: str):
        """Update metrics when a warehouse is selected."""
        try:
            if warehouse_id in self.warehouse_metrics:
                self.warehouse_metrics[warehouse_id]["orders_processed_today"] += 1
                self.warehouse_metrics[warehouse_id]["last_updated"] = datetime.utcnow().isoformat()
        
        except Exception as e:
            self.logger.error("Failed to update warehouse selection metrics", error=str(e), warehouse_id=warehouse_id)
    
    async def _handle_order_created(self, message: AgentMessage):
        """Handle order created messages to select warehouse."""
        payload = message.payload
        order_id = payload.get("order_id")
        shipping_address = payload.get("shipping_address")
        items = payload.get("items", [])
        
        if order_id and shipping_address and items:
            try:
                # Create warehouse selection request
                selection_request = {
                    "order_id": order_id,
                    "shipping_address": shipping_address,
                    "items": items,
                    "priority": "standard"
                }
                
                # Select optimal warehouse
                await self._select_optimal_warehouse(selection_request)
                
            except Exception as e:
                self.logger.error("Failed to handle order created", error=str(e), order_id=order_id)
                
                # Send error notification
                await self.send_message(
                    recipient_agent="monitoring_agent",
                    message_type=MessageType.ERROR_DETECTED,
                    payload={
                        "agent_id": self.agent_id,
                        "error_type": "warehouse_selection_failed",
                        "order_id": order_id,
                        "message": f"Failed to select warehouse: {str(e)}"
                    }
                )
    
    async def _handle_inventory_update(self, message: AgentMessage):
        """Handle inventory updates to adjust warehouse scoring."""
        payload = message.payload
        warehouse_id = payload.get("warehouse_id")
        
        if warehouse_id and warehouse_id in self.warehouse_metrics:
            # Update capacity utilization based on inventory changes
            # This is a simplified implementation
            self.warehouse_metrics[warehouse_id]["last_updated"] = datetime.utcnow().isoformat()
    
    async def _update_warehouse_metrics(self):
        """Background task to update warehouse performance metrics."""
        while not self.shutdown_event.is_set():
            try:
                # Update metrics from various sources
                # This would typically pull data from warehouse management systems
                
                for warehouse_id in self.warehouse_metrics:
                    # Simulate metric updates
                    import random
                    
                    metrics = self.warehouse_metrics[warehouse_id]
                    
                    # Slightly adjust metrics to simulate real-world changes
                    metrics["capacity_utilization"] += random.uniform(-2.0, 2.0)
                    metrics["capacity_utilization"] = max(0, min(100, metrics["capacity_utilization"]))
                    
                    metrics["avg_processing_time_hours"] += random.uniform(-0.5, 0.5)
                    metrics["avg_processing_time_hours"] = max(1.0, min(24.0, metrics["avg_processing_time_hours"]))
                    
                    metrics["last_updated"] = datetime.utcnow().isoformat()
                
                # Sleep for 30 minutes before next update
                await asyncio.sleep(1800)
            
            except Exception as e:
                self.logger.error("Error updating warehouse metrics", error=str(e))
                await asyncio.sleep(3600)  # Wait 1 hour on error
    
    async def _monitor_warehouse_performance(self):
        """Background task to monitor warehouse performance and send alerts."""
        while not self.shutdown_event.is_set():
            try:
                for warehouse_id, metrics in self.warehouse_metrics.items():
                    # Check for performance issues
                    if metrics["capacity_utilization"] > 90:
                        await self.send_message(
                            recipient_agent="monitoring_agent",
                            message_type=MessageType.RISK_ALERT,
                            payload={
                                "alert_type": "high_capacity_utilization",
                                "warehouse_id": warehouse_id,
                                "utilization": metrics["capacity_utilization"],
                                "severity": "warning"
                            }
                        )
                    
                    if metrics["error_rate_percent"] > 5:
                        await self.send_message(
                            recipient_agent="monitoring_agent",
                            message_type=MessageType.RISK_ALERT,
                            payload={
                                "alert_type": "high_error_rate",
                                "warehouse_id": warehouse_id,
                                "error_rate": metrics["error_rate_percent"],
                                "severity": "warning"
                            }
                        )
                
                # Sleep for 15 minutes before next check
                await asyncio.sleep(900)
            
            except Exception as e:
                self.logger.error("Error monitoring warehouse performance", error=str(e))
                await asyncio.sleep(1800)  # Wait 30 minutes on error


# FastAPI app instance for running the agent as a service
app = FastAPI(title="Warehouse Selection Agent", version="1.0.0")

# Global agent instance
warehouse_selection_agent: Optional[WarehouseSelectionAgent] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the Warehouse Selection Agent on startup."""
    global warehouse_selection_agent
    warehouse_selection_agent = WarehouseSelectionAgent()
    await warehouse_selection_agent.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup the Warehouse Selection Agent on shutdown."""
    global warehouse_selection_agent
    if warehouse_selection_agent:
        await warehouse_selection_agent.stop()


# Include agent routes
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if warehouse_selection_agent:
        health_status = warehouse_selection_agent.get_health_status()
        return {"status": "healthy", "agent_status": health_status.dict()}
    return {"status": "unhealthy", "message": "Agent not initialized"}


# Mount agent's FastAPI app
app.mount("/api/v1", warehouse_selection_agent.app if warehouse_selection_agent else FastAPI())


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
        "warehouse_selection_agent:app",
        host="0.0.0.0",
        port=8004,
        reload=False,
        log_level="info"
    )
