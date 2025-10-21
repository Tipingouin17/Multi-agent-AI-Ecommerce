
import asyncio
import json
import os
import sys
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import structlog
import uvicorn
from fastapi import Body, Depends, FastAPI, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

# Add project root to Python path
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.base_agent import AgentMessage, BaseAgent, MessageType
from shared.database import DatabaseManager, get_database_manager
from shared.db_helpers import DatabaseHelper
from shared.kafka_manager import KafkaManager

# Configure logging
logger = structlog.get_logger(__name__)


# ENUMS
class POStatus(str, Enum):
    """Represents the status of a Purchase Order."""
    DRAFT = "draft"
    SENT = "sent"
    CONFIRMED = "confirmed"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


# Pydantic Models
class Supplier(BaseModel):
    """Defines the data structure for a supplier, including contact and performance details."""
    supplier_id: UUID
    supplier_code: str
    supplier_name: str
    contact_info: Dict[str, Any]
    payment_terms: Optional[str]
    lead_time_days: int
    rating: Decimal
    is_active: bool

    class Config:
        from_attributes = True


class SupplierProduct(BaseModel):
    """Represents a product offered by a supplier, including cost, MOQ, and lead time."""
    supplier_product_id: UUID
    supplier_id: UUID
    product_id: str
    supplier_sku: Optional[str]
    cost: Decimal
    moq: int
    lead_time_days: Optional[int]
    is_preferred: bool

    class Config:
        from_attributes = True


class POItem(BaseModel):
    """Specifies an item within a purchase order, including product ID, quantity, and cost."""
    product_id: str
    quantity: int
    unit_cost: Decimal


class PurchaseOrderCreate(BaseModel):
    """Defines the required data for creating a new purchase order."""
    supplier_id: UUID
    items: List[POItem]
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None
    created_by: str


class PurchaseOrder(BaseModel):
    """Represents a complete purchase order, including its status, items, and total amount."""
    po_id: UUID
    po_number: str
    supplier_id: UUID
    status: POStatus
    items: List[Dict[str, Any]]
    total_amount: Decimal
    expected_delivery_date: Optional[date]
    created_at: datetime

    class Config:
        from_attributes = True


class POReceiptCreate(BaseModel):
    """Defines the data needed to record the receipt of a purchase order."""
    po_id: UUID
    received_items: List[Dict[str, Any]]
    received_by: str
    notes: Optional[str] = None


class SupplierPerformanceMetrics(BaseModel):
    """Contains key performance indicators (KPIs) for a supplier."""
    supplier_id: UUID
    on_time_delivery_rate: Decimal
    quality_score: Decimal
    cost_competitiveness: Decimal
    responsiveness_score: Decimal
    overall_rating: Decimal


class SupplierRepository:
    """Handles all database interactions related to suppliers, products, and purchase orders."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initializes the repository with a database manager and helpers for each table.

        Args:
            db_manager: An instance of DatabaseManager for database connectivity.
        """
        self.db_manager = db_manager
        self.suppliers_db_helper = DatabaseHelper(db_manager, "suppliers")
        self.supplier_products_db_helper = DatabaseHelper(db_manager, "supplier_products")
        self.purchase_orders_db_helper = DatabaseHelper(db_manager, "purchase_orders")
        self.po_receipts_db_helper = DatabaseHelper(db_manager, "po_receipts")
        self.supplier_performance_db_helper = DatabaseHelper(db_manager, "supplier_performance")

    async def get_suppliers(self, active_only: bool = True) -> List[Supplier]:
        """
        Retrieves a list of suppliers, with an option to filter for active ones.

        Args:
            active_only: If True, returns only active suppliers.

        Returns:
            A list of Supplier objects.
        """
        try:
            async with self.db_manager.get_session() as session:
                conditions = {"is_active": True} if active_only else {}
                suppliers_data = await self.suppliers_db_helper.get_all(session, conditions=conditions, order_by="rating DESC")
                return [Supplier(**s) for s in suppliers_data]
        except Exception as e:
            logger.error(f"Error getting suppliers: {e}", exc_info=True)
            return []

    async def get_supplier(self, supplier_id: UUID) -> Optional[Supplier]:
        """
        Fetches a single supplier by their unique ID.

        Args:
            supplier_id: The UUID of the supplier to retrieve.

        Returns:
            A Supplier object if found, otherwise None.
        """
        try:
            async with self.db_manager.get_session() as session:
                supplier_data = await self.suppliers_db_helper.get_by_id(session, supplier_id)
                return Supplier(**supplier_data) if supplier_data else None
        except Exception as e:
            logger.error(f"Error getting supplier {supplier_id}: {e}", exc_info=True)
            return None

    async def get_supplier_products(
        self, supplier_id: UUID, product_id: Optional[str] = None
    ) -> List[SupplierProduct]:
        """
        Retrieves all products for a given supplier, with an option to filter by product ID.

        Args:
            supplier_id: The UUID of the supplier.
            product_id: Optional product ID to filter the results.

        Returns:
            A list of SupplierProduct objects.
        """
        try:
            async with self.db_manager.get_session() as session:
                conditions = {"supplier_id": supplier_id}
                if product_id:
                    conditions["product_id"] = product_id
                products_data = await self.supplier_products_db_helper.get_all(session, conditions=conditions)
                return [SupplierProduct(**p) for p in products_data]
        except Exception as e:
            logger.error(f"Error getting supplier products for supplier {supplier_id}: {e}", exc_info=True)
            return []

    async def create_purchase_order(self, po_data: PurchaseOrderCreate) -> Optional[PurchaseOrder]:
        """
        Creates a new purchase order in the database.

        Args:
            po_data: A PurchaseOrderCreate object with the PO details.

        Returns:
            The created PurchaseOrder object if successful, otherwise None.
        """
        try:
            async with self.db_manager.get_session() as session:
                po_number = f"PO-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
                total_amount = sum(item.quantity * item.unit_cost for item in po_data.items)

                po_dict = po_data.model_dump()
                po_dict["po_number"] = po_number
                po_dict["total_amount"] = total_amount
                po_dict["items"] = json.dumps([item.model_dump() for item in po_data.items])

                created_po_data = await self.purchase_orders_db_helper.create(session, po_dict)
                return PurchaseOrder(**created_po_data) if created_po_data else None
        except Exception as e:
            logger.error(f"Error creating purchase order: {e}", exc_info=True)
            return None

    async def get_purchase_order(self, po_id: UUID) -> Optional[PurchaseOrder]:
        """
        Retrieves a purchase order by its unique ID.

        Args:
            po_id: The UUID of the purchase order.

        Returns:
            A PurchaseOrder object if found, otherwise None.
        """
        try:
            async with self.db_manager.get_session() as session:
                po_data = await self.purchase_orders_db_helper.get_by_id(session, po_id)
                return PurchaseOrder(**po_data) if po_data else None
        except Exception as e:
            logger.error(f"Error getting purchase order {po_id}: {e}", exc_info=True)
            return None

    async def update_po_status(self, po_id: UUID, status: POStatus) -> Optional[PurchaseOrder]:
        """
        Updates the status of a specific purchase order.

        Args:
            po_id: The UUID of the purchase order to update.
            status: The new status to set.

        Returns:
            The updated PurchaseOrder object if successful, otherwise None.
        """
        try:
            async with self.db_manager.get_session() as session:
                update_data = {"status": status.value}
                if status == POStatus.RECEIVED:
                    update_data["actual_delivery_date"] = date.today()
                
                updated_po_data = await self.purchase_orders_db_helper.update(session, po_id, update_data)
                return PurchaseOrder(**updated_po_data) if updated_po_data else None
        except Exception as e:
            logger.error(f"Error updating PO {po_id} status to {status.value}: {e}", exc_info=True)
            return None

    async def create_po_receipt(self, receipt_data: POReceiptCreate) -> Optional[UUID]:
        """
        Records the receipt of a purchase order.

        Args:
            receipt_data: A POReceiptCreate object with receipt details.

        Returns:
            The UUID of the created receipt if successful, otherwise None.
        """
        try:
            async with self.db_manager.get_session() as session:
                receipt_dict = receipt_data.model_dump()
                receipt_dict["received_items"] = json.dumps(receipt_data.received_items)
                created_receipt_data = await self.po_receipts_db_helper.create(session, receipt_dict)
                return created_receipt_data.get("receipt_id") if created_receipt_data else None
        except Exception as e:
            logger.error(f"Error creating PO receipt for PO {receipt_data.po_id}: {e}", exc_info=True)
            return None

    async def get_supplier_performance(self, supplier_id: UUID) -> Optional[SupplierPerformanceMetrics]:
        """
        Retrieves performance metrics for a specific supplier.

        Args:
            supplier_id: The UUID of the supplier.

        Returns:
            A SupplierPerformanceMetrics object if found, otherwise simulated metrics.
        """
        try:
            async with self.db_manager.get_session() as session:
                performance_data = await self.supplier_performance_db_helper.get_all(session, conditions={"supplier_id": supplier_id}, limit=1, order_by="calculated_at DESC")
                if performance_data:
                    return SupplierPerformanceMetrics(**performance_data[0])
                else:
                    return SupplierPerformanceMetrics(
                        supplier_id=supplier_id,
                        on_time_delivery_rate=Decimal("92.5"),
                        quality_score=Decimal("88.0"),
                        cost_competitiveness=Decimal("85.0"),
                        responsiveness_score=Decimal("90.0"),
                        overall_rating=Decimal("88.9")
                    )
        except Exception as e:
            logger.error(f"Error getting supplier performance for {supplier_id}: {e}", exc_info=True)
            return None


class SupplierAgent(BaseAgent):
    """
    Manages supplier relationships, products, and purchase orders through a FastAPI interface and Kafka messaging.
    """

    def __init__(self, agent_id: str, agent_type: str, db_manager: DatabaseManager, kafka_manager=None):
        """
        Initializes the agent, setting up database and messaging components.

        Args:
            agent_id: Unique identifier for this agent.
            agent_type: The type of this agent.
            db_manager: Manager for database connections.
            kafka_manager: Manager for Kafka messaging.
        """
        super().__init__(agent_id, agent_type, db_manager, kafka_manager)
        self.db_helper_suppliers = DatabaseHelper(db_manager, "suppliers")
        self.db_helper_supplier_products = DatabaseHelper(db_manager, "supplier_products")
        self.db_helper_purchase_orders = DatabaseHelper(db_manager, "purchase_orders")
        self.kafka_manager = kafka_manager
        self._db_initialized = False
        self.app = self._create_fastapi_app()

    async def startup(self):
        """Initializes asynchronous components like database and Kafka connections."""
        await super().startup()
        if self.kafka_manager:
            await self.kafka_manager.start_producer()
            asyncio.create_task(self.kafka_manager.start_consumer(self.agent_id, self.process_message))
        self._db_initialized = True
        logger.info("SupplierAgent started and database and Kafka initialized.")

    def _create_fastapi_app(self) -> FastAPI:
        """
        Sets up the FastAPI application, including routes and exception handlers.

        Returns:
            A configured FastAPI application instance.
        """
        app = FastAPI(title="Supplier Agent API", version="1.0.0",
                      description="API for managing supplier relationships, products, and purchase orders.")

        @app.exception_handler(StarletteHTTPException)
        async def http_exception_handler(request: Request, exc: StarletteHTTPException):
            logger.error(f"HTTP Exception: {exc.detail}", exc_info=True, status_code=exc.status_code)
            return JSONResponse(
                status_code=exc.status_code,
                content={"message": exc.detail}
            )

        @app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            logger.error(f"Unhandled Exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"message": "Internal Server Error"}
            )

        def get_supplier_repository() -> SupplierRepository:
            return SupplierRepository(self.db_manager)

        @app.get("/health", summary="Health Check")
        async def health_check():
            return {"status": "healthy"}

        @app.get("/", summary="Root Endpoint")
        async def root():
            return {"agent_id": self.agent_id, "agent_type": self.agent_type}

        @app.get("/suppliers", response_model=List[Supplier], summary="List all suppliers")
        async def get_suppliers(
            active_only: bool = Query(True, description="Filter for active suppliers only"),
            repo: SupplierRepository = Depends(get_supplier_repository)
        ):
            return await repo.get_suppliers(active_only)

        @app.get("/suppliers/{supplier_id}", response_model=Supplier, summary="Get a specific supplier by ID")
        async def get_supplier(
            supplier_id: UUID = Path(..., description="The ID of the supplier to retrieve"),
            repo: SupplierRepository = Depends(get_supplier_repository)
        ):
            supplier = await repo.get_supplier(supplier_id)
            if not supplier:
                raise HTTPException(status_code=404, detail="Supplier not found")
            return supplier

        @app.get("/suppliers/{supplier_id}/products", response_model=List[SupplierProduct], summary="Get products for a specific supplier")
        async def get_supplier_products(
            supplier_id: UUID = Path(..., description="The ID of the supplier"),
            product_id: Optional[str] = Query(None, description="Optional product ID to filter by"),
            repo: SupplierRepository = Depends(get_supplier_repository)
        ):
            return await repo.get_supplier_products(supplier_id, product_id)

        @app.post("/purchase-orders", response_model=PurchaseOrder, status_code=201, summary="Create a new purchase order")
        async def create_purchase_order(
            po_data: PurchaseOrderCreate,
            repo: SupplierRepository = Depends(get_supplier_repository)
        ):
            created_po = await repo.create_purchase_order(po_data)
            if not created_po:
                raise HTTPException(status_code=500, detail="Failed to create purchase order")
            return created_po

        @app.get("/purchase-orders/{po_id}", response_model=PurchaseOrder, summary="Get a specific purchase order by ID")
        async def get_purchase_order(
            po_id: UUID = Path(..., description="The ID of the purchase order to retrieve"),
            repo: SupplierRepository = Depends(get_supplier_repository)
        ):
            po = await repo.get_purchase_order(po_id)
            if not po:
                raise HTTPException(status_code=404, detail="Purchase order not found")
            return po

        @app.patch("/purchase-orders/{po_id}/status", response_model=PurchaseOrder, summary="Update the status of a purchase order")
        async def update_po_status(
            po_id: UUID = Path(..., description="The ID of the purchase order to update"),
            status: POStatus = Body(..., embed=True, description="The new status for the purchase order"),
            repo: SupplierRepository = Depends(get_supplier_repository)
        ):
            updated_po = await repo.update_po_status(po_id, status)
            if not updated_po:
                raise HTTPException(status_code=404, detail="Purchase order not found or failed to update")
            return updated_po

        @app.post("/po-receipts", response_model=UUID, status_code=201, summary="Create a purchase order receipt")
        async def create_po_receipt(
            receipt_data: POReceiptCreate,
            repo: SupplierRepository = Depends(get_supplier_repository)
        ):
            receipt_id = await repo.create_po_receipt(receipt_data)
            if not receipt_id:
                raise HTTPException(status_code=500, detail="Failed to create purchase order receipt")
            return receipt_id

        @app.get("/suppliers/{supplier_id}/performance", response_model=SupplierPerformanceMetrics, summary="Get supplier performance metrics")
        async def get_supplier_performance(
            supplier_id: UUID = Path(..., description="The ID of the supplier"),
            repo: SupplierRepository = Depends(get_supplier_repository)
        ):
            performance = await repo.get_supplier_performance(supplier_id)
            if not performance:
                raise HTTPException(status_code=404, detail="Supplier performance data not found")
            return performance

        return app

    async def process_message(self, message: AgentMessage):
        """
        Handles incoming Kafka messages, routing them based on message type.

        Args:
            message: The incoming message to process.
        """
        if not self._db_initialized:
            logger.warning("Database not initialized, skipping message processing.")
            return

        logger.info(f"Received message of type: {message.type}")
        try:
            if message.type == MessageType.REQUEST_BEST_SUPPLIER:
                product_id = message.data.get("product_id")
                quantity = message.data.get("quantity")
                if product_id is None or quantity is None:
                    logger.error("Received REQUEST_BEST_SUPPLIER message with missing product_id or quantity.")
                    return

                best_supplier = await self.find_best_supplier(product_id, quantity)
                response_message = AgentMessage(
                    sender_id=self.agent_id,
                    receiver_id=message.sender_id,
                    type=MessageType.RESPONSE_BEST_SUPPLIER,
                    data={"best_supplier": best_supplier},
                )
                if self.kafka_manager:
                    await self.send_message(response_message)
                else:
                    logger.warning("KafkaManager not initialized, cannot send response message.")

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

    async def find_best_supplier(self, product_id: str, quantity: int) -> Optional[Dict[str, Any]]:
        """
        Analyzes suppliers to find the best option for a given product and quantity.

        Args:
            product_id: The ID of the product to source.
            quantity: The required quantity.

        Returns:
            A dictionary with the best supplier and their product details, or None.
        """
        if not self._db_initialized:
            logger.warning("Database not initialized, cannot find best supplier.")
            return None
        try:
            async with self.db_manager.get_session() as session:
                suppliers = await self.suppliers_db_helper.get_all(session, conditions={"is_active": True})
                best_supplier = None
                best_score = -1

                for supplier in suppliers:
                    supplier_products = await self.db_helper_supplier_products.get_all(
                        session, conditions={"supplier_id": supplier["supplier_id"], "product_id": product_id}
                    )
                    if not supplier_products:
                        continue

                    product = supplier_products[0]
                    if quantity < product["moq"]:
                        continue

                    cost_score = 100 - min(100, float(product["cost"]))
                    lead_time_score = 100 - min(100, product["lead_time_days"] or supplier["lead_time_days"])
                    rating_score = float(supplier["rating"]) * 10
                    total_score = (cost_score * 0.4) + (lead_time_score * 0.3) + (rating_score * 0.3)

                    if total_score > best_score:
                        best_score = total_score
                        best_supplier = {
                            "supplier": supplier,
                            "product": product,
                            "score": total_score,
                        }
                return best_supplier
        except Exception as e:
            logger.error(f"Error finding best supplier: {e}", exc_info=True)
            return None


if __name__ == "__main__":
    # Configuration
    AGENT_ID = os.getenv("SUPPLIER_AGENT_ID", "supplier_agent_001")
    AGENT_TYPE = "SupplierAgent"
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    PORT = int(os.getenv("SUPPLIER_AGENT_PORT", 8001))

    # Initialize components
    db_manager = DatabaseManager(DATABASE_URL)
    kafka_manager = KafkaManager(KAFKA_BOOTSTRAP_SERVERS)

    # Create and run agent
    supplier_agent = SupplierAgent(AGENT_ID, AGENT_TYPE, db_manager, kafka_manager)

    @supplier_agent.app.on_event("startup")
    async def startup_event():
        await supplier_agent.startup()

    @supplier_agent.app.on_event("shutdown")
    async def shutdown_event():
        if supplier_agent.kafka_manager:
            await supplier_agent.kafka_manager.stop_producer()
            await supplier_agent.kafka_manager.stop_consumer()

    uvicorn.run(supplier_agent.app, host="0.0.0.0", port=PORT)

