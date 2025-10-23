
"""
Marketplace Connector Agent (Production-Ready with API Integration)
Handles all marketplace integrations: orders, listings, inventory, prices, messages
"""

import os
import sys
import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pydantic import BaseModel
from decimal import Decimal
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from shared.base_agent_v2 import BaseAgentV2, AgentMessage, MessageType
from shared.db_helpers import DatabaseHelper
from shared.kafka_config import KafkaProducer, KafkaConsumer
from shared.marketplace_apis import (
    get_marketplace_manager,
    MarketplaceOrderStatus,
    ProductListing,
    ListingStatus
)

logger = structlog.get_logger(__name__)


class MarketplaceConnectorAgentProduction(BaseAgentV2):
    """
    Marketplace Connector Agent - Production Ready
    
    Responsibilities:
    - Sync orders from all marketplaces
    - Update order status and tracking
    - Manage product listings across marketplaces
    - Sync inventory levels
    - Sync prices
    - Handle customer messages
    - Monitor marketplace performance
    """
    
    def __init__(self):
        """
        Initializes the MarketplaceConnectorAgentProduction.
        """
        super().__init__(agent_id="marketplace_connector_agent")
        self.kafka_producer = None
        self.kafka_consumer = None
        self.marketplace_manager = get_marketplace_manager()
        self.sync_interval = int(os.getenv("SYNC_INTERVAL", 300))  # 5 minutes
        self.db_helper = DatabaseHelper(os.getenv("DATABASE_URL", "sqlite:///./marketplace_connector.db"))
        self._db_initialized = False

    async def initialize(self):
        """Initialize agent, Kafka producers/consumers, and database."""
        await super().initialize()
        try:
            self.kafka_producer = KafkaProducer()
            self.kafka_consumer = KafkaConsumer(*[
                    "marketplace_order_status_update",
                    "inventory_updated",
                    "price_updated",
                    "product_listing_created",
                    "agent_message"
                ],
                group_id="marketplace_connector_production"
            )
            self._db_initialized = True
            logger.info("Marketplace Connector Agent (Production) initialized")
        except Exception as e:
            logger.error("Failed to initialize Marketplace Connector Agent", error=str(e))
            raise

    async def process_message(self, message: AgentMessage):
        """
        Processes incoming messages from other agents or internal systems.

        Args:
            message (AgentMessage): The incoming message to process.
        """
        logger.info("Processing incoming message", message_type=message.message_type, sender=message.sender)
        try:
            if message.message_type == MessageType.ORDER_UPDATE:
                # Example: Update order status on marketplace based on internal system message
                payload = message.payload
                await self.update_order_status(
                    payload.get("marketplace"),
                    payload.get("marketplace_order_id"),
                    MarketplaceOrderStatus(payload.get("status")),
                    payload.get("tracking_number")
                )
            elif message.message_type == MessageType.INVENTORY_UPDATE:
                payload = message.payload
                await self.sync_inventory_to_marketplaces(
                    payload.get("sku"),
                    payload.get("quantity")
                )
            elif message.message_type == MessageType.PRICE_UPDATE:
                payload = message.payload
                await self.sync_price_to_marketplaces(
                    payload.get("sku"),
                    Decimal(str(payload.get("price")))
                )
            elif message.message_type == MessageType.PRODUCT_LISTING_CREATE:
                payload = message.payload
                listing = ProductListing(**payload.get("listing"))
                await self.create_listing_on_marketplace(
                    payload.get("marketplace"),
                    listing
                )
            else:
                logger.warning("Unhandled message type", message_type=message.message_type)
        except Exception as e:
            logger.error("Error processing message", message=message.json(), error=str(e))
            await self.send_message(
                recipient_agent_id=message.sender,
                message_type=MessageType.ERROR,
                payload={"original_message": message.json(), "error": str(e)}
            )

    async def sync_all_orders(self) -> Dict[str, Any]:
        """
        Syncs orders from all configured marketplaces and stores them in the database.
        Publishes new orders to Kafka.
        
        Returns:
            Dict[str, Any]: A dictionary containing sync results.
        """
        if not self._db_initialized: return {"success": False, "error": "Database not initialized"}
        try:
            logger.info("Starting marketplace order sync")
            
            start_date = datetime.utcnow() - timedelta(hours=24)
            orders = await self.marketplace_manager.get_all_orders(start_date=start_date)
            
            logger.info(f"Retrieved {len(orders)} orders from marketplaces")
            
            new_orders = 0
            async with self.db_helper.get_session() as session:
                for order_data in orders:
                    # Check if order already exists in our system
                    existing_order = await self.db_helper.get_by_id(session, "Order", order_data.marketplace_order_id)
                    
                    if not existing_order:
                        # Create order in DB
                        await self.db_helper.create(session, "Order", {
                            "id": order_data.marketplace_order_id,
                            "marketplace": order_data.marketplace,
                            "order_date": order_data.order_date,
                            "customer_name": order_data.customer_name,
                            "customer_email": order_data.customer_email,
                            "shipping_address": order_data.shipping_address,
                            "items": [item.dict() for item in order_data.items], # Assuming items are Pydantic models
                            "total_amount": float(order_data.total_amount),
                            "currency": order_data.currency,
                            "status": order_data.status.value,
                            "commission": float(order_data.commission) if order_data.commission else None
                        })
                        # Publish new order event
                        await self.kafka_producer.send(
                            "marketplace_order_received",
                            {
                                "marketplace_order_id": order_data.marketplace_order_id,
                                "marketplace": order_data.marketplace,
                                "order_date": order_data.order_date.isoformat(),
                                "customer_name": order_data.customer_name,
                                "customer_email": order_data.customer_email,
                                "shipping_address": order_data.shipping_address,
                                "items": [item.dict() for item in order_data.items],
                                "total_amount": float(order_data.total_amount),
                                "currency": order_data.currency,
                                "status": order_data.status.value,
                                "commission": float(order_data.commission) if order_data.commission else None
                            }
                        )
                        new_orders += 1
            
            logger.info(f"Processed {new_orders} new orders")
            
            return {"success": True, "total_orders": len(orders), "new_orders": new_orders}
            
        except Exception as e:
            logger.error("Failed to sync marketplace orders", error=str(e))
            return {"success": False, "error": str(e)}

    async def update_order_status(
        self,
        marketplace: str,
        marketplace_order_id: str,
        status: MarketplaceOrderStatus,
        tracking_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Updates the status of an order on a specific marketplace and in the database.
        
        Args:
            marketplace (str): The code of the marketplace.
            marketplace_order_id (str): The order ID on the marketplace.
            status (MarketplaceOrderStatus): The new status for the order.
            tracking_number (Optional[str]): The tracking number for shipped orders.
            
        Returns:
            Dict[str, Any]: A dictionary containing the update result.
        """
        if not self._db_initialized: return {"success": False, "error": "Database not initialized"}
        try:
            logger.info("Updating marketplace order status",
                       marketplace=marketplace,
                       order_id=marketplace_order_id,
                       status=status.value)
            
            marketplace_api = self.marketplace_manager.get_marketplace(marketplace)
            if not marketplace_api:
                raise ValueError(f"Marketplace {marketplace} not found")
            
            success = await marketplace_api.update_order_status(
                marketplace_order_id,
                status,
                tracking_number
            )
            
            if success:
                async with self.db_helper.get_session() as session:
                    await self.db_helper.update(session, "Order", marketplace_order_id, {"status": status.value})
                logger.info("Order status updated successfully",
                           marketplace=marketplace,
                           order_id=marketplace_order_id)
            
            return {"success": success, "marketplace": marketplace, "order_id": marketplace_order_id, "status": status.value}
            
        except Exception as e:
            logger.error("Failed to update order status", error=str(e))
            return {"success": False, "error": str(e)}

    async def sync_inventory_to_marketplaces(
        self,
        sku: str,
        quantity: int
    ) -> Dict[str, Any]:
        """
        Syncs inventory levels for a product to all configured marketplaces and updates the database.
        
        Args:
            sku (str): The SKU of the product.
            quantity (int): The new inventory quantity.
            
        Returns:
            Dict[str, Any]: A dictionary containing sync results.
        """
        if not self._db_initialized: return {"success": False, "error": "Database not initialized"}
        try:
            logger.info("Syncing inventory to marketplaces",
                       sku=sku,
                       quantity=quantity)
            
            results = await self.marketplace_manager.sync_inventory_to_all(
                sku,
                quantity
            )
            
            success_count = sum(1 for v in results.values() if v)
            total_count = len(results)

            async with self.db_helper.get_session() as session:
                # Assuming there's a 'Product' model or similar to store inventory
                await self.db_helper.update(session, "Product", sku, {"inventory": quantity})
            
            logger.info(f"Inventory synced to {success_count}/{total_count} marketplaces")
            
            return {"success": True, "sku": sku, "quantity": quantity, "results": results, "success_count": success_count, "total_count": total_count}
            
        except Exception as e:
            logger.error("Failed to sync inventory", error=str(e))
            return {"success": False, "error": str(e)}

    async def sync_price_to_marketplaces(
        self,
        sku: str,
        price: Decimal
    ) -> Dict[str, Any]:
        """
        Syncs product prices to all configured marketplaces and updates the database.
        
        Args:
            sku (str): The SKU of the product.
            price (Decimal): The new price for the product.
            
        Returns:
            Dict[str, Any]: A dictionary containing sync results.
        """
        if not self._db_initialized: return {"success": False, "error": "Database not initialized"}
        try:
            logger.info("Syncing price to marketplaces",
                       sku=sku,
                       price=float(price))
            
            results = await self.marketplace_manager.sync_price_to_all(
                sku,
                price
            )
            
            success_count = sum(1 for v in results.values() if v)
            total_count = len(results)

            async with self.db_helper.get_session() as session:
                # Assuming there's a 'Product' model or similar to store price
                await self.db_helper.update(session, "Product", sku, {"price": float(price)})
            
            logger.info(f"Price synced to {success_count}/{total_count} marketplaces")
            
            return {"success": True, "sku": sku, "price": float(price), "results": results, "success_count": success_count, "total_count": total_count}
            
        except Exception as e:
            logger.error("Failed to sync price", error=str(e))
            return {"success": False, "error": str(e)}

    async def create_listing_on_marketplace(
        self,
        marketplace: str,
        listing: ProductListing
    ) -> Dict[str, Any]:
        """
        Creates a product listing on a specific marketplace and stores it in the database.
        
        Args:
            marketplace (str): The code of the marketplace.
            listing (ProductListing): The product listing details.
            
        Returns:
            Dict[str, Any]: A dictionary containing the creation result.
        """
        if not self._db_initialized: return {"success": False, "error": "Database not initialized"}
        try:
            logger.info("Creating marketplace listing",
                       marketplace=marketplace,
                       sku=listing.sku)
            
            marketplace_api = self.marketplace_manager.get_marketplace(marketplace)
            if not marketplace_api:
                raise ValueError(f"Marketplace {marketplace} not found")
            
            listing_id = await marketplace_api.create_listing(listing)

            async with self.db_helper.get_session() as session:
                # Store listing in DB
                await self.db_helper.create(session, "Listing", {
                    "id": listing_id,
                    "marketplace": marketplace,
                    "sku": listing.sku,
                    "title": listing.title,
                    "description": listing.description,
                    "price": float(listing.price),
                    "currency": listing.currency,
                    "quantity": listing.quantity,
                    "status": ListingStatus.ACTIVE.value # Assuming active upon creation
                })
            
            logger.info("Listing created",
                       marketplace=marketplace,
                       listing_id=listing_id)
            
            return {"success": True, "marketplace": marketplace, "listing_id": listing_id, "sku": listing.sku}
            
        except Exception as e:
            logger.error("Failed to create listing", error=str(e))
            return {"success": False, "error": str(e)}

    async def sync_messages_from_marketplaces(self) -> Dict[str, Any]:
        """
        Retrieves customer messages from all configured marketplaces and stores them in the database.
        Publishes new messages to Kafka.
        
        Returns:
            Dict[str, Any]: A dictionary containing the sync results.
        """
        if not self._db_initialized: return {"success": False, "error": "Database not initialized"}
        try:
            logger.info("Syncing messages from marketplaces")
            
            all_messages = []
            
            for marketplace_code, marketplace_api in self.marketplace_manager.marketplaces.items():
                try:
                    messages = await marketplace_api.get_messages(unread_only=True)
                    all_messages.extend(messages)
                    
                    async with self.db_helper.get_session() as session:
                        for msg_data in messages:
                            # Check if message already exists
                            existing_message = await self.db_helper.get_by_id(session, "Message", msg_data.message_id)
                            if not existing_message:
                                # Create message in DB
                                await self.db_helper.create(session, "Message", {
                                    "id": msg_data.message_id,
                                    "marketplace": msg_data.marketplace,
                                    "order_id": msg_data.order_id,
                                    "customer_name": msg_data.customer_name,
                                    "subject": msg_data.subject,
                                    "message_content": msg_data.message, # Renamed to avoid conflict with class name
                                    "received_at": msg_data.received_at,
                                    "requires_response": msg_data.requires_response
                                })
                                # Publish each message
                                await self.kafka_producer.send(
                                    "marketplace_message_received",
                                    {
                                        "message_id": msg_data.message_id,
                                        "marketplace": msg_data.marketplace,
                                        "order_id": msg_data.order_id,
                                        "customer_name": msg_data.customer_name,
                                        "subject": msg_data.subject,
                                        "message": msg_data.message,
                                        "received_at": msg_data.received_at.isoformat(),
                                        "requires_response": msg_data.requires_response
                                    }
                                )
                except Exception as e:
                    logger.error(f"Failed to get messages from {marketplace_code}",
                               error=str(e))
            
            logger.info(f"Retrieved {len(all_messages)} messages from marketplaces")
            
            return {"success": True, "message_count": len(all_messages)}
            
        except Exception as e:
            logger.error("Failed to sync messages", error=str(e))
            return {"success": False, "error": str(e)}

    async def run(self):
        """Main agent loop that initializes, starts periodic sync, and processes Kafka messages."""
        logger.info("Marketplace Connector Agent (Production) starting...")
        await self.initialize()
        
        # Start periodic sync task
        sync_task = asyncio.create_task(self._periodic_sync())
        
        try:
            async for message_envelope in self.kafka_consumer:
                topic = message_envelope.topic
                data = message_envelope.value
                
                # Wrap Kafka message in AgentMessage for consistent processing
                agent_message = AgentMessage(
                    sender="kafka_consumer", # Or derive from Kafka message metadata
                    recipient_agent_id=self.agent_id,
                    message_type=MessageType.from_topic(topic), # Assuming a method to map topic to MessageType
                    payload=data
                )
                await self.process_message(agent_message)

        except Exception as e:
            logger.error("Error in agent loop", error=str(e))
        finally:
            sync_task.cancel()
            await self.marketplace_manager.close_all()
            await self.cleanup()

    async def _periodic_sync(self):
        """Internal periodic task to sync orders and messages from marketplaces."""
        while True:
            try:
                # Sync orders
                await self.sync_all_orders()
                
                # Sync messages
                await self.sync_messages_from_marketplaces()
                
                # Wait for next sync
                await asyncio.sleep(self.sync_interval)
                
            except asyncio.CancelledError:
                logger.info("Periodic sync task cancelled.")
                break
            except Exception as e:
                logger.error("Error in periodic sync", error=str(e))
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def cleanup(self):
        """Cleanup agent resources"""
        try:
            if self.kafka_producer:
                await self.kafka_producer.stop()
            if self.kafka_consumer:
                await self.kafka_consumer.stop()
            if self.db_manager:
                await self.db_manager.close()
            await super().cleanup()
            logger.info(f"{self.agent_name} cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process marketplace-specific business logic
        
        Args:
            data: Dictionary containing operation type and parameters
            
        Returns:
            Dictionary with processing results
        """
        try:
            operation = data.get("operation", "sync_products")
            
            if operation == "sync_products":
                # Sync products to marketplaces
                marketplace = data.get("marketplace")
                result = await self.sync_products_to_marketplace(marketplace)
                return {"status": "success", "result": result}
            
            elif operation == "sync_inventory":
                # Sync inventory levels
                marketplace = data.get("marketplace")
                result = await self.sync_inventory_to_marketplace(marketplace)
                return {"status": "success", "result": result}
            
            elif operation == "sync_orders":
                # Sync orders from marketplaces
                result = await self.sync_all_orders()
                return {"status": "success", "result": result}
            
            elif operation == "sync_messages":
                # Sync customer messages
                result = await self.sync_messages_from_marketplaces()
                return {"status": "success", "result": result}
            
            else:
                return {"status": "error", "message": f"Unknown operation: {operation}"}
                
        except Exception as e:
            logger.error(f"Error in process_business_logic: {e}")
            return {"status": "error", "message": str(e)}

# FastAPI Server Setup
app = FastAPI(
    title="Marketplace Connector Agent Production",
    description="Marketplace Connector Agent Production - Multi-Agent E-commerce Platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoints
@app.get("/health", summary="Health check", response_description="Status of the agent")
async def health_check():
    """Provides a health check endpoint for the agent."""
    return {"status": "healthy", "agent": "marketplace_connector_agent_production"}

@app.get("/", summary="Root endpoint", response_description="Basic agent information")
async def root():
    """Provides basic information about the agent."""
    return {
        "agent": "marketplace_connector_agent_production",
        "status": "running",
        "version": "1.0.0"
    }

@app.post("/orders/sync", summary="Manually trigger order synchronization")
async def trigger_order_sync():
    """Triggers a manual synchronization of orders from all configured marketplaces."""
    try:
        agent_instance = MarketplaceConnectorAgentProduction() # Create a temporary instance for API call
        await agent_instance.initialize() # Initialize to ensure DB and Kafka are ready
        result = await agent_instance.sync_all_orders()
        await agent_instance.shutdown() # Clean up resources
        if result["success"]:
            return {"message": "Order sync initiated successfully", "details": result}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    except Exception as e:
        logger.error("API: Failed to trigger order sync", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to trigger order sync: {e}")

@app.post("/inventory/sync", summary="Manually trigger inventory synchronization")
async def trigger_inventory_sync(sku: str, quantity: int):
    """Triggers a manual synchronization of inventory for a specific SKU to all configured marketplaces."""
    try:
        agent_instance = MarketplaceConnectorAgentProduction()
        await agent_instance.initialize()
        result = await agent_instance.sync_inventory_to_marketplaces(sku, quantity)
        await agent_instance.shutdown()
        if result["success"]:
            return {"message": "Inventory sync initiated successfully", "details": result}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    except Exception as e:
        logger.error("API: Failed to trigger inventory sync", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to trigger inventory sync: {e}")

@app.post("/price/sync", summary="Manually trigger price synchronization")
async def trigger_price_sync(sku: str, price: Decimal):
    """Triggers a manual synchronization of price for a specific SKU to all configured marketplaces."""
    try:
        agent_instance = MarketplaceConnectorAgentProduction()
        await agent_instance.initialize()
        result = await agent_instance.sync_price_to_marketplaces(sku, price)
        await agent_instance.shutdown()
        if result["success"]:
            return {"message": "Price sync initiated successfully", "details": result}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    except Exception as e:
        logger.error("API: Failed to trigger price sync", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to trigger price sync: {e}")

@app.post("/listing/create", summary="Create a product listing on a specific marketplace")
async def create_product_listing(marketplace: str, listing: ProductListing):
    """Creates a product listing on the specified marketplace."""
    try:
        agent_instance = MarketplaceConnectorAgentProduction()
        await agent_instance.initialize()
        result = await agent_instance.create_listing_on_marketplace(marketplace, listing)
        await agent_instance.shutdown()
        if result["success"]:
            return {"message": "Listing created successfully", "details": result}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])
    except Exception as e:
        logger.error("API: Failed to create listing", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create listing: {e}")

# Main execution block for running the agent and FastAPI app
if __name__ == "__main__":
    # Run FastAPI app (agent logic runs via FastAPI lifespan/startup events)
    port = int(os.getenv("MARKETPLACE_AGENT_PORT", 8007))
    uvicorn.run(app, host="0.0.0.0", port=port)

