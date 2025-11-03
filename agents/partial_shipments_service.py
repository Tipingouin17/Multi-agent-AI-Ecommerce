"""
Partial Shipments Service - Multi-Agent E-commerce System

This service handles partial shipments for orders including:
- Creating multiple shipments for a single order
- Tracking shipment status
- Coordinating with shipping carriers
- Customer notifications for each shipment
"""

from typing import Dict, List, Optional
from datetime import datetime
from uuid import UUID, uuid4
from decimal import Decimal
from pydantic import BaseModel
from enum import Enum
import structlog
from shared.base_agent_v2 import BaseAgentV2
from typing import Any

logger = structlog.get_logger(__name__)


# ===========================
# ENUMS
# ===========================

class ShipmentStatus(str, Enum):
    """Status of a shipment."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETURNED = "returned"


# ===========================
# PYDANTIC MODELS
# ===========================

class ShipmentItem(BaseModel):
    """Item in a shipment."""
    item_id: Optional[int] = None
    shipment_id: str
    order_item_id: int
    product_id: str
    quantity: int
    product_name: Optional[str] = None
    sku: Optional[str] = None


class PartialShipment(BaseModel):
    """Partial shipment for an order."""
    id: Optional[int] = None
    shipment_id: str
    order_id: str
    shipment_number: int  # 1st, 2nd, 3rd shipment for this order
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    status: ShipmentStatus = ShipmentStatus.PENDING
    shipped_at: Optional[datetime] = None
    estimated_delivery: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    shipping_cost: Optional[Decimal] = None
    weight: Optional[Decimal] = None
    dimensions: Optional[Dict] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Related data
    items: Optional[List[ShipmentItem]] = []


class CreateShipmentRequest(BaseModel):
    """Request to create a new shipment."""
    order_id: str
    items: List[Dict]  # [{"order_item_id": 1, "quantity": 2}, ...]
    carrier: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    shipping_cost: Optional[Decimal] = None
    weight: Optional[Decimal] = None
    dimensions: Optional[Dict] = None
    notes: Optional[str] = None


class UpdateShipmentRequest(BaseModel):
    """Request to update a shipment."""
    tracking_number: Optional[str] = None
    status: Optional[ShipmentStatus] = None
    carrier: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    notes: Optional[str] = None


class ShipmentSummary(BaseModel):
    """Summary of shipments for an order."""
    order_id: str
    total_shipments: int
    pending_shipments: int
    shipped_shipments: int
    delivered_shipments: int
    failed_shipments: int
    total_items: int
    shipped_items: int
    remaining_items: int


# ===========================
# PARTIAL SHIPMENTS SERVICE
# ===========================

class PartialShipmentsService(BaseAgentV2):
    """Service for managing partial shipments."""
    
    def __init__(self, agent_id: str = "partial_shipments_service_001", db_manager=None, message_broker=None):
        super().__init__(agent_id=agent_id)
        self.db_manager = db_manager
        self.message_broker = message_broker
        self.logger = logger.bind(service="partial_shipments")
    
    async def create_shipment(
        self,
        request: CreateShipmentRequest
    ) -> PartialShipment:
        """Create a new partial shipment."""
        shipment_id = str(uuid4())
        
        async with self.db_manager.get_async_session() as session:
            try:
                # 1. Verify order exists
                order_query = """
                    SELECT id, status
                    FROM orders
                    WHERE id = $1
                """
                
                order_result = await session.execute(order_query, request.order_id)
                order_row = order_result.fetchone()
                
                if not order_row:
                    raise ValueError(f"Order {request.order_id} not found")
                
                order_id, order_status = order_row
                
                if order_status in ['cancelled', 'refunded']:
                    raise ValueError(f"Cannot create shipment for {order_status} order")
                
                # 2. Get next shipment number
                count_query = """
                    SELECT COUNT(*) + 1
                    FROM partial_shipments
                    WHERE order_id = $1
                """
                
                count_result = await session.execute(count_query, request.order_id)
                shipment_number = count_result.fetchone()[0]
                
                # 3. Create shipment
                insert_query = """
                    INSERT INTO partial_shipments (
                        shipment_id, order_id, shipment_number, carrier,
                        status, estimated_delivery, shipping_cost, weight,
                        dimensions, notes, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    RETURNING id, created_at, updated_at
                """
                
                result = await session.execute(
                    insert_query,
                    shipment_id,
                    request.order_id,
                    shipment_number,
                    request.carrier,
                    ShipmentStatus.PENDING.value,
                    request.estimated_delivery,
                    float(request.shipping_cost) if request.shipping_cost else None,
                    float(request.weight) if request.weight else None,
                    request.dimensions,
                    request.notes,
                    datetime.utcnow(),
                    datetime.utcnow()
                )
                
                row = result.fetchone()
                shipment_db_id = row[0]
                
                # 4. Add shipment items
                items = []
                for item_data in request.items:
                    # Get product info
                    product_query = """
                        SELECT oi.product_id, p.name, p.sku
                        FROM order_items oi
                        JOIN products p ON oi.product_id = p.id
                        WHERE oi.id = $1 AND oi.order_id = $2
                    """
                    
                    product_result = await session.execute(
                        product_query,
                        item_data["order_item_id"],
                        request.order_id
                    )
                    product_row = product_result.fetchone()
                    
                    if not product_row:
                        raise ValueError(f"Order item {item_data['order_item_id']} not found")
                    
                    product_id, product_name, sku = product_row
                    
                    # Insert shipment item
                    item_query = """
                        INSERT INTO shipment_items (
                            shipment_id, order_item_id, product_id, quantity
                        ) VALUES ($1, $2, $3, $4)
                        RETURNING item_id
                    """
                    
                    item_result = await session.execute(
                        item_query,
                        shipment_id,
                        item_data["order_item_id"],
                        product_id,
                        item_data["quantity"]
                    )
                    
                    item_id = item_result.fetchone()[0]
                    
                    items.append(ShipmentItem(
                        item_id=item_id,
                        shipment_id=shipment_id,
                        order_item_id=item_data["order_item_id"],
                        product_id=product_id,
                        quantity=item_data["quantity"],
                        product_name=product_name,
                        sku=sku
                    ))
                
                await session.commit()
                
                self.logger.info("Created partial shipment",
                               shipment_id=shipment_id,
                               order_id=request.order_id,
                               shipment_number=shipment_number,
                               items_count=len(items))
                
                # 5. Send notification
                if self.message_broker:
                    await self._send_shipment_notification(
                        shipment_id=shipment_id,
                        order_id=request.order_id,
                        status=ShipmentStatus.PENDING
                    )
                
                return PartialShipment(
                    id=shipment_db_id,
                    shipment_id=shipment_id,
                    order_id=request.order_id,
                    shipment_number=shipment_number,
                    carrier=request.carrier,
                    status=ShipmentStatus.PENDING,
                    estimated_delivery=request.estimated_delivery,
                    shipping_cost=request.shipping_cost,
                    weight=request.weight,
                    dimensions=request.dimensions,
                    notes=request.notes,
                    created_at=row[1],
                    updated_at=row[2],
                    items=items
                )
                
            except Exception as e:
                await session.rollback()
                self.logger.error("Failed to create shipment",
                                error=str(e),
                                order_id=request.order_id)
                raise
    
    async def update_shipment(
        self,
        shipment_id: str,
        request: UpdateShipmentRequest
    ) -> Optional[PartialShipment]:
        """Update a shipment."""
        async with self.db_manager.get_async_session() as session:
            try:
                # Build dynamic update query
                updates = []
                params = []
                param_num = 1
                
                if request.tracking_number is not None:
                    updates.append(f"tracking_number = ${param_num}")
                    params.append(request.tracking_number)
                    param_num += 1
                
                if request.status is not None:
                    updates.append(f"status = ${param_num}")
                    params.append(request.status.value)
                    param_num += 1
                    
                    # Set timestamps based on status
                    if request.status == ShipmentStatus.SHIPPED:
                        updates.append(f"shipped_at = ${param_num}")
                        params.append(datetime.utcnow())
                        param_num += 1
                    elif request.status == ShipmentStatus.DELIVERED:
                        updates.append(f"delivered_at = ${param_num}")
                        params.append(datetime.utcnow())
                        param_num += 1
                
                if request.carrier is not None:
                    updates.append(f"carrier = ${param_num}")
                    params.append(request.carrier)
                    param_num += 1
                
                if request.estimated_delivery is not None:
                    updates.append(f"estimated_delivery = ${param_num}")
                    params.append(request.estimated_delivery)
                    param_num += 1
                
                if request.delivered_at is not None:
                    updates.append(f"delivered_at = ${param_num}")
                    params.append(request.delivered_at)
                    param_num += 1
                
                if request.notes is not None:
                    updates.append(f"notes = ${param_num}")
                    params.append(request.notes)
                    param_num += 1
                
                if not updates:
                    return await self.get_shipment(shipment_id)
                
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(shipment_id)
                
                query = f"""
                    UPDATE partial_shipments
                    SET {', '.join(updates)}
                    WHERE shipment_id = ${param_num}
                    RETURNING order_id
                """
                
                result = await session.execute(query, *params)
                row = result.fetchone()
                
                if not row:
                    return None
                
                order_id = row[0]
                
                await session.commit()
                
                self.logger.info("Updated shipment",
                               shipment_id=shipment_id,
                               status=request.status.value if request.status else None)
                
                # Send notification
                if self.message_broker and request.status:
                    await self._send_shipment_notification(
                        shipment_id=shipment_id,
                        order_id=order_id,
                        status=request.status
                    )
                
                return await self.get_shipment(shipment_id)
                
            except Exception as e:
                await session.rollback()
                self.logger.error("Failed to update shipment",
                                error=str(e),
                                shipment_id=shipment_id)
                raise
    
    async def get_shipment(self, shipment_id: str) -> Optional[PartialShipment]:
        """Get a shipment by ID."""
        async with self.db_manager.get_async_session() as session:
            query = """
                SELECT 
                    id, shipment_id, order_id, shipment_number, carrier,
                    tracking_number, status, shipped_at, estimated_delivery,
                    delivered_at, shipping_cost, weight, dimensions, notes,
                    created_at, updated_at
                FROM partial_shipments
                WHERE shipment_id = $1
            """
            
            result = await session.execute(query, shipment_id)
            row = result.fetchone()
            
            if not row:
                return None
            
            shipment = PartialShipment(
                id=row[0],
                shipment_id=row[1],
                order_id=row[2],
                shipment_number=row[3],
                carrier=row[4],
                tracking_number=row[5],
                status=ShipmentStatus(row[6]),
                shipped_at=row[7],
                estimated_delivery=row[8],
                delivered_at=row[9],
                shipping_cost=Decimal(str(row[10])) if row[10] else None,
                weight=Decimal(str(row[11])) if row[11] else None,
                dimensions=row[12],
                notes=row[13],
                created_at=row[14],
                updated_at=row[15]
            )
            
            # Get shipment items
            items_query = """
                SELECT 
                    si.item_id, si.shipment_id, si.order_item_id,
                    si.product_id, si.quantity, p.name, p.sku
                FROM shipment_items si
                JOIN products p ON si.product_id = p.id
                WHERE si.shipment_id = $1
            """
            
            items_result = await session.execute(items_query, shipment_id)
            shipment.items = [
                ShipmentItem(
                    item_id=row[0],
                    shipment_id=row[1],
                    order_item_id=row[2],
                    product_id=row[3],
                    quantity=row[4],
                    product_name=row[5],
                    sku=row[6]
                )
                for row in items_result.fetchall()
            ]
            
            return shipment
    
    async def get_order_shipments(self, order_id: str) -> List[PartialShipment]:
        """Get all shipments for an order."""
        async with self.db_manager.get_async_session() as session:
            query = """
                SELECT shipment_id
                FROM partial_shipments
                WHERE order_id = $1
                ORDER BY shipment_number ASC
            """
            
            result = await session.execute(query, order_id)
            shipment_ids = [row[0] for row in result.fetchall()]
            
            shipments = []
            for sid in shipment_ids:
                shipment = await self.get_shipment(sid)
                if shipment:
                    shipments.append(shipment)
            
            return shipments
    
    async def get_shipment_summary(self, order_id: str) -> ShipmentSummary:
        """Get shipment summary for an order."""
        async with self.db_manager.get_async_session() as session:
            query = """
                SELECT 
                    COUNT(*) as total_shipments,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                    COUNT(CASE WHEN status IN ('shipped', 'in_transit', 'out_for_delivery') THEN 1 END) as shipped,
                    COUNT(CASE WHEN status = 'delivered' THEN 1 END) as delivered,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
                FROM partial_shipments
                WHERE order_id = $1
            """
            
            result = await session.execute(query, order_id)
            row = result.fetchone()
            
            # Get item counts
            items_query = """
                SELECT 
                    SUM(oi.quantity) as total_items,
                    COALESCE(SUM(si.quantity), 0) as shipped_items
                FROM order_items oi
                LEFT JOIN shipment_items si ON oi.id = si.order_item_id
                WHERE oi.order_id = $1
            """
            
            items_result = await session.execute(items_query, order_id)
            items_row = items_result.fetchone()
            
            total_items = items_row[0] or 0
            shipped_items = items_row[1] or 0
            
            return ShipmentSummary(
                order_id=order_id,
                total_shipments=row[0],
                pending_shipments=row[1],
                shipped_shipments=row[2],
                delivered_shipments=row[3],
                failed_shipments=row[4],
                total_items=total_items,
                shipped_items=shipped_items,
                remaining_items=total_items - shipped_items
            )
    
    async def _send_shipment_notification(
        self,
        shipment_id: str,
        order_id: str,
        status: ShipmentStatus
    ):
        """Send shipment notification via message broker."""
        if not self.message_broker:
            return
        
        message = {
            "type": "shipment_status_updated",
            "shipment_id": shipment_id,
            "order_id": order_id,
            "status": status.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            await self.message_broker.publish("shipment_events", message)
            self.logger.info("Sent shipment notification",
                           shipment_id=shipment_id,
                           status=status.value)
        except Exception as e:
            self.logger.error("Failed to send shipment notification",
                            error=str(e),
                            shipment_id=shipment_id)
    
    async def initialize(self):
        """Initialize the service."""
        await super().initialize()
        logger.info("PartialShipmentsService initialized successfully")
    
    async def cleanup(self):
        """Cleanup service resources."""
        try:
            await super().cleanup()
            logger.info("PartialShipmentsService cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process service business logic.
        
        Args:
            data: Dictionary containing operation type and parameters
            
        Returns:
            Dictionary with processing results
        """
        try:
            operation = data.get("operation", "process")
            logger.info(f"Processing PartialShipmentsService operation: {operation}")
            return {"status": "success", "operation": operation, "data": data}
        except Exception as e:
            logger.error(f"Error in process_business_logic: {e}")
            return {"status": "error", "message": str(e)}

