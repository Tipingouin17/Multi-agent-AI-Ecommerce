"""
Order Repository Layer for Multi-Agent E-commerce System

This module provides comprehensive database operations for all order-related entities
including orders, modifications, splits, shipments, fulfillment, and cancellations.
"""

import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4

from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from shared.database import DatabaseManager, BaseRepository
from shared.order_models import (
    OrderModification, OrderModificationCreate,
    OrderSplit, OrderSplitRequest,
    PartialShipment, PartialShipmentCreate, PartialShipmentUpdate,
    OrderTimelineEvent, OrderTimelineEventCreate,
    OrderNote, OrderNoteCreate, OrderNoteUpdate,
    OrderTag, OrderTagCreate,
    FulfillmentPlan, FulfillmentPlanCreate, FulfillmentPlanUpdate,
    DeliveryAttempt, DeliveryAttemptCreate,
    CancellationRequest, CancellationRequestCreate, CancellationRequestReview,
    OrderSearchFilters, OrderSummary, OrderAnalytics,
    OrderStatus, ShipmentStatus, FulfillmentStatus, CancellationStatus
)


logger = structlog.get_logger(__name__)


class OrderModificationRepository:
    """Repository for order modifications."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create(self, modification: OrderModificationCreate) -> OrderModification:
        """Create a new order modification record."""
        async with self.db_manager.get_session() as session:
            modification_id = str(uuid4())
            
            query = """
                INSERT INTO order_modifications 
                (modification_id, order_id, modification_type, field_name, old_value, 
                 new_value, reason, modified_by, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING *
            """
            
            result = await session.execute(
                query,
                modification_id,
                modification.order_id,
                modification.modification_type.value,
                modification.field_name,
                modification.old_value,
                modification.new_value,
                modification.reason,
                modification.modified_by,
                modification.metadata
            )
            
            row = result.fetchone()
            await session.commit()
            
            return OrderModification(
                modification_id=row['modification_id'],
                order_id=row['order_id'],
                modification_type=row['modification_type'],
                field_name=row['field_name'],
                old_value=row['old_value'],
                new_value=row['new_value'],
                reason=row['reason'],
                modified_by=row['modified_by'],
                modified_at=row['modified_at'],
                metadata=row['metadata']
            )
    
    async def get_by_order(self, order_id: str) -> List[OrderModification]:
        """Get all modifications for an order."""
        async with self.db_manager.get_session() as session:
            query = """
                SELECT * FROM order_modifications 
                WHERE order_id = $1 
                ORDER BY modified_at DESC
            """
            
            result = await session.execute(query, order_id)
            rows = result.fetchall()
            
            return [
                OrderModification(
                    modification_id=row['modification_id'],
                    order_id=row['order_id'],
                    modification_type=row['modification_type'],
                    field_name=row['field_name'],
                    old_value=row['old_value'],
                    new_value=row['new_value'],
                    reason=row['reason'],
                    modified_by=row['modified_by'],
                    modified_at=row['modified_at'],
                    metadata=row['metadata']
                )
                for row in rows
            ]


class OrderSplitRepository:
    """Repository for order splits."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create(self, parent_order_id: str, child_order_id: str, 
                    split_reason: str, split_by: Optional[str] = None,
                    metadata: Optional[Dict] = None) -> OrderSplit:
        """Create a new order split record."""
        async with self.db_manager.get_session() as session:
            split_id = str(uuid4())
            
            query = """
                INSERT INTO order_splits 
                (split_id, parent_order_id, child_order_id, split_reason, split_by, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
            """
            
            result = await session.execute(
                query,
                split_id,
                parent_order_id,
                child_order_id,
                split_reason,
                split_by,
                metadata
            )
            
            row = result.fetchone()
            await session.commit()
            
            return OrderSplit(
                split_id=row['split_id'],
                parent_order_id=row['parent_order_id'],
                child_order_id=row['child_order_id'],
                split_reason=row['split_reason'],
                split_date=row['split_date'],
                split_by=row['split_by'],
                metadata=row['metadata']
            )
    
    async def get_child_orders(self, parent_order_id: str) -> List[OrderSplit]:
        """Get all child orders for a parent order."""
        async with self.db_manager.get_session() as session:
            query = """
                SELECT * FROM order_splits 
                WHERE parent_order_id = $1 
                ORDER BY split_date ASC
            """
            
            result = await session.execute(query, parent_order_id)
            rows = result.fetchall()
            
            return [
                OrderSplit(
                    split_id=row['split_id'],
                    parent_order_id=row['parent_order_id'],
                    child_order_id=row['child_order_id'],
                    split_reason=row['split_reason'],
                    split_date=row['split_date'],
                    split_by=row['split_by'],
                    metadata=row['metadata']
                )
                for row in rows
            ]


class PartialShipmentRepository:
    """Repository for partial shipments."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create(self, shipment: PartialShipmentCreate) -> PartialShipment:
        """Create a new partial shipment."""
        async with self.db_manager.get_session() as session:
            shipment_id = str(uuid4())
            
            # Insert shipment
            query = """
                INSERT INTO partial_shipments 
                (shipment_id, order_id, shipment_number, carrier, estimated_delivery, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
            """
            
            result = await session.execute(
                query,
                shipment_id,
                shipment.order_id,
                shipment.shipment_number,
                shipment.carrier,
                shipment.estimated_delivery,
                shipment.metadata
            )
            
            row = result.fetchone()
            
            # Insert shipment items
            for item in shipment.items:
                item_query = """
                    INSERT INTO partial_shipment_items 
                    (shipment_id, order_item_id, quantity)
                    VALUES ($1, $2, $3)
                """
                await session.execute(
                    item_query,
                    shipment_id,
                    item['order_item_id'],
                    item['quantity']
                )
            
            await session.commit()
            
            # Get items
            items = await self._get_shipment_items(session, shipment_id)
            
            return PartialShipment(
                shipment_id=row['shipment_id'],
                order_id=row['order_id'],
                shipment_number=row['shipment_number'],
                tracking_number=row['tracking_number'],
                carrier=row['carrier'],
                shipped_at=row['shipped_at'],
                estimated_delivery=row['estimated_delivery'],
                actual_delivery=row['actual_delivery'],
                status=ShipmentStatus(row['status']),
                items=items,
                metadata=row['metadata'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
    async def update(self, shipment_id: str, updates: PartialShipmentUpdate) -> PartialShipment:
        """Update a partial shipment."""
        async with self.db_manager.get_session() as session:
            # Build update query dynamically
            update_fields = []
            params = []
            param_count = 1
            
            if updates.tracking_number is not None:
                update_fields.append(f"tracking_number = ${param_count}")
                params.append(updates.tracking_number)
                param_count += 1
            
            if updates.carrier is not None:
                update_fields.append(f"carrier = ${param_count}")
                params.append(updates.carrier)
                param_count += 1
            
            if updates.shipped_at is not None:
                update_fields.append(f"shipped_at = ${param_count}")
                params.append(updates.shipped_at)
                param_count += 1
            
            if updates.estimated_delivery is not None:
                update_fields.append(f"estimated_delivery = ${param_count}")
                params.append(updates.estimated_delivery)
                param_count += 1
            
            if updates.actual_delivery is not None:
                update_fields.append(f"actual_delivery = ${param_count}")
                params.append(updates.actual_delivery)
                param_count += 1
            
            if updates.status is not None:
                update_fields.append(f"status = ${param_count}")
                params.append(updates.status.value)
                param_count += 1
            
            if updates.metadata is not None:
                update_fields.append(f"metadata = ${param_count}")
                params.append(updates.metadata)
                param_count += 1
            
            if not update_fields:
                return await self.get_by_id(shipment_id)
            
            params.append(shipment_id)
            
            query = f"""
                UPDATE partial_shipments 
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE shipment_id = ${param_count}
                RETURNING *
            """
            
            result = await session.execute(query, *params)
            row = result.fetchone()
            await session.commit()
            
            items = await self._get_shipment_items(session, shipment_id)
            
            return PartialShipment(
                shipment_id=row['shipment_id'],
                order_id=row['order_id'],
                shipment_number=row['shipment_number'],
                tracking_number=row['tracking_number'],
                carrier=row['carrier'],
                shipped_at=row['shipped_at'],
                estimated_delivery=row['estimated_delivery'],
                actual_delivery=row['actual_delivery'],
                status=ShipmentStatus(row['status']),
                items=items,
                metadata=row['metadata'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
    async def get_by_id(self, shipment_id: str) -> Optional[PartialShipment]:
        """Get a shipment by ID."""
        async with self.db_manager.get_session() as session:
            query = "SELECT * FROM partial_shipments WHERE shipment_id = $1"
            result = await session.execute(query, shipment_id)
            row = result.fetchone()
            
            if not row:
                return None
            
            items = await self._get_shipment_items(session, shipment_id)
            
            return PartialShipment(
                shipment_id=row['shipment_id'],
                order_id=row['order_id'],
                shipment_number=row['shipment_number'],
                tracking_number=row['tracking_number'],
                carrier=row['carrier'],
                shipped_at=row['shipped_at'],
                estimated_delivery=row['estimated_delivery'],
                actual_delivery=row['actual_delivery'],
                status=ShipmentStatus(row['status']),
                items=items,
                metadata=row['metadata'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
    async def get_by_order(self, order_id: str) -> List[PartialShipment]:
        """Get all shipments for an order."""
        async with self.db_manager.get_session() as session:
            query = """
                SELECT * FROM partial_shipments 
                WHERE order_id = $1 
                ORDER BY shipment_number ASC
            """
            
            result = await session.execute(query, order_id)
            rows = result.fetchall()
            
            shipments = []
            for row in rows:
                items = await self._get_shipment_items(session, row['shipment_id'])
                shipments.append(PartialShipment(
                    shipment_id=row['shipment_id'],
                    order_id=row['order_id'],
                    shipment_number=row['shipment_number'],
                    tracking_number=row['tracking_number'],
                    carrier=row['carrier'],
                    shipped_at=row['shipped_at'],
                    estimated_delivery=row['estimated_delivery'],
                    actual_delivery=row['actual_delivery'],
                    status=ShipmentStatus(row['status']),
                    items=items,
                    metadata=row['metadata'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ))
            
            return shipments
    
    async def _get_shipment_items(self, session: AsyncSession, shipment_id: str) -> List[Dict]:
        """Get items for a shipment."""
        query = """
            SELECT * FROM partial_shipment_items 
            WHERE shipment_id = $1
        """
        
        result = await session.execute(query, shipment_id)
        rows = result.fetchall()
        
        return [
            {
                'shipment_id': row['shipment_id'],
                'order_item_id': row['order_item_id'],
                'quantity': row['quantity']
            }
            for row in rows
        ]


class OrderTimelineRepository:
    """Repository for order timeline events."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create(self, event: OrderTimelineEventCreate) -> OrderTimelineEvent:
        """Create a new timeline event."""
        async with self.db_manager.get_session() as session:
            event_id = str(uuid4())
            
            query = """
                INSERT INTO order_timeline 
                (event_id, order_id, event_type, event_description, event_data, triggered_by)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
            """
            
            result = await session.execute(
                query,
                event_id,
                event.order_id,
                event.event_type,
                event.event_description,
                event.event_data,
                event.triggered_by
            )
            
            row = result.fetchone()
            await session.commit()
            
            return OrderTimelineEvent(
                event_id=row['event_id'],
                order_id=row['order_id'],
                event_type=row['event_type'],
                event_description=row['event_description'],
                event_data=row['event_data'],
                triggered_by=row['triggered_by'],
                occurred_at=row['occurred_at']
            )
    
    async def get_by_order(self, order_id: str) -> List[OrderTimelineEvent]:
        """Get timeline for an order."""
        async with self.db_manager.get_session() as session:
            query = """
                SELECT * FROM order_timeline 
                WHERE order_id = $1 
                ORDER BY occurred_at DESC
            """
            
            result = await session.execute(query, order_id)
            rows = result.fetchall()
            
            return [
                OrderTimelineEvent(
                    event_id=row['event_id'],
                    order_id=row['order_id'],
                    event_type=row['event_type'],
                    event_description=row['event_description'],
                    event_data=row['event_data'],
                    triggered_by=row['triggered_by'],
                    occurred_at=row['occurred_at']
                )
                for row in rows
            ]


class OrderNoteRepository:
    """Repository for order notes."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create(self, note: OrderNoteCreate) -> OrderNote:
        """Create a new order note."""
        async with self.db_manager.get_session() as session:
            note_id = str(uuid4())
            
            query = """
                INSERT INTO order_notes 
                (note_id, order_id, note_type, note_text, is_visible_to_customer, created_by)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
            """
            
            result = await session.execute(
                query,
                note_id,
                note.order_id,
                note.note_type.value,
                note.note_text,
                note.is_visible_to_customer,
                note.created_by
            )
            
            row = result.fetchone()
            await session.commit()
            
            return OrderNote(
                note_id=row['note_id'],
                order_id=row['order_id'],
                note_type=row['note_type'],
                note_text=row['note_text'],
                is_visible_to_customer=row['is_visible_to_customer'],
                created_by=row['created_by'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
    async def update(self, note_id: str, updates: OrderNoteUpdate) -> OrderNote:
        """Update an order note."""
        async with self.db_manager.get_session() as session:
            update_fields = []
            params = []
            param_count = 1
            
            if updates.note_text is not None:
                update_fields.append(f"note_text = ${param_count}")
                params.append(updates.note_text)
                param_count += 1
            
            if updates.is_visible_to_customer is not None:
                update_fields.append(f"is_visible_to_customer = ${param_count}")
                params.append(updates.is_visible_to_customer)
                param_count += 1
            
            if not update_fields:
                return await self.get_by_id(note_id)
            
            params.append(note_id)
            
            query = f"""
                UPDATE order_notes 
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE note_id = ${param_count}
                RETURNING *
            """
            
            result = await session.execute(query, *params)
            row = result.fetchone()
            await session.commit()
            
            return OrderNote(
                note_id=row['note_id'],
                order_id=row['order_id'],
                note_type=row['note_type'],
                note_text=row['note_text'],
                is_visible_to_customer=row['is_visible_to_customer'],
                created_by=row['created_by'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
    async def get_by_id(self, note_id: str) -> Optional[OrderNote]:
        """Get a note by ID."""
        async with self.db_manager.get_session() as session:
            query = "SELECT * FROM order_notes WHERE note_id = $1"
            result = await session.execute(query, note_id)
            row = result.fetchone()
            
            if not row:
                return None
            
            return OrderNote(
                note_id=row['note_id'],
                order_id=row['order_id'],
                note_type=row['note_type'],
                note_text=row['note_text'],
                is_visible_to_customer=row['is_visible_to_customer'],
                created_by=row['created_by'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
    async def get_by_order(self, order_id: str, visible_to_customer: Optional[bool] = None) -> List[OrderNote]:
        """Get notes for an order."""
        async with self.db_manager.get_session() as session:
            if visible_to_customer is not None:
                query = """
                    SELECT * FROM order_notes 
                    WHERE order_id = $1 AND is_visible_to_customer = $2
                    ORDER BY created_at DESC
                """
                result = await session.execute(query, order_id, visible_to_customer)
            else:
                query = """
                    SELECT * FROM order_notes 
                    WHERE order_id = $1 
                    ORDER BY created_at DESC
                """
                result = await session.execute(query, order_id)
            
            rows = result.fetchall()
            
            return [
                OrderNote(
                    note_id=row['note_id'],
                    order_id=row['order_id'],
                    note_type=row['note_type'],
                    note_text=row['note_text'],
                    is_visible_to_customer=row['is_visible_to_customer'],
                    created_by=row['created_by'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                for row in rows
            ]
    
    async def delete(self, note_id: str) -> bool:
        """Delete a note."""
        async with self.db_manager.get_session() as session:
            query = "DELETE FROM order_notes WHERE note_id = $1"
            result = await session.execute(query, note_id)
            await session.commit()
            return result.rowcount > 0


class OrderTagRepository:
    """Repository for order tags."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def add_tag(self, tag: OrderTagCreate) -> OrderTag:
        """Add a tag to an order."""
        async with self.db_manager.get_session() as session:
            query = """
                INSERT INTO order_tags (order_id, tag, added_by)
                VALUES ($1, $2, $3)
                ON CONFLICT (order_id, tag) DO NOTHING
                RETURNING *
            """
            
            result = await session.execute(
                query,
                tag.order_id,
                tag.tag,
                tag.added_by
            )
            
            row = result.fetchone()
            await session.commit()
            
            if not row:
                # Tag already exists, fetch it
                return await self.get_tag(tag.order_id, tag.tag)
            
            return OrderTag(
                order_id=row['order_id'],
                tag=row['tag'],
                added_by=row['added_by'],
                added_at=row['added_at']
            )
    
    async def get_tag(self, order_id: str, tag: str) -> Optional[OrderTag]:
        """Get a specific tag."""
        async with self.db_manager.get_session() as session:
            query = "SELECT * FROM order_tags WHERE order_id = $1 AND tag = $2"
            result = await session.execute(query, order_id, tag)
            row = result.fetchone()
            
            if not row:
                return None
            
            return OrderTag(
                order_id=row['order_id'],
                tag=row['tag'],
                added_by=row['added_by'],
                added_at=row['added_at']
            )
    
    async def get_by_order(self, order_id: str) -> List[OrderTag]:
        """Get all tags for an order."""
        async with self.db_manager.get_session() as session:
            query = "SELECT * FROM order_tags WHERE order_id = $1 ORDER BY added_at ASC"
            result = await session.execute(query, order_id)
            rows = result.fetchall()
            
            return [
                OrderTag(
                    order_id=row['order_id'],
                    tag=row['tag'],
                    added_by=row['added_by'],
                    added_at=row['added_at']
                )
                for row in rows
            ]
    
    async def remove_tag(self, order_id: str, tag: str) -> bool:
        """Remove a tag from an order."""
        async with self.db_manager.get_session() as session:
            query = "DELETE FROM order_tags WHERE order_id = $1 AND tag = $2"
            result = await session.execute(query, order_id, tag)
            await session.commit()
            return result.rowcount > 0
    
    async def get_orders_by_tag(self, tag: str) -> List[str]:
        """Get all order IDs with a specific tag."""
        async with self.db_manager.get_session() as session:
            query = "SELECT order_id FROM order_tags WHERE tag = $1"
            result = await session.execute(query, tag)
            rows = result.fetchall()
            return [row['order_id'] for row in rows]


# Due to size constraints, I'll create the remaining repositories in a continuation file
# This includes: FulfillmentPlanRepository, DeliveryAttemptRepository, CancellationRequestRepository

