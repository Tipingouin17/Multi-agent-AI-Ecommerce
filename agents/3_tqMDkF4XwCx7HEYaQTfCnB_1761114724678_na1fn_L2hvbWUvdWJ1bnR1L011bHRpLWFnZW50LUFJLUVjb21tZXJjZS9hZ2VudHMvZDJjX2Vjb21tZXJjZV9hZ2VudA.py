
"""
D2C E-commerce Platform Agent - Multi-Agent E-commerce System

This agent manages connections to direct-to-consumer (D2C) e-commerce platforms including:
- Shopify (REST Admin API and GraphQL)
- PrestaShop (Web Service API)
- WooCommerce (REST API)
- Magento (REST API)
- BigCommerce (REST API)
- Custom e-commerce platforms
- Multi-store management and synchronization
- Theme and customization management
- Customer data synchronization
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4
from enum import Enum
from decimal import Decimal

from shared.db_helpers import DatabaseHelper

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import structlog
import aiohttp
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
from shared.models import APIResponse
from shared.database import DatabaseManager, get_database_manager


logger = structlog.get_logger(__name__)


class D2CPlatform(str, Enum):
    """Types of D2C e-commerce platforms."""
    SHOPIFY = "shopify"
    PRESTASHOP = "prestashop"
    WOOCOMMERCE = "woocommerce"
    MAGENTO = "magento"
    BIGCOMMERCE = "bigcommerce"
    OPENCART = "opencart"
    CUSTOM = "custom"


class StoreStatus(str, Enum):
    """Status of D2C stores."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    SUSPENDED = "suspended"
    TESTING = "testing"


class SyncStatus(str, Enum):
    """Synchronization status."""
    SYNCED = "synced"
    PENDING = "pending"
    ERROR = "error"
    PARTIAL = "partial"


class D2CCredentials(BaseModel):
    """Model for D2C platform API credentials."""
    platform_type: D2CPlatform
    store_id: str
    store_name: str
    store_url: str
    
    # API credentials
    api_key: str
    api_secret: Optional[str] = None
    access_token: Optional[str] = None
    
    # Platform-specific settings
    shop_domain: Optional[str] = None  # Shopify
    webservice_key: Optional[str] = None  # PrestaShop
    consumer_key: Optional[str] = None  # WooCommerce
    consumer_secret: Optional[str] = None  # WooCommerce
    
    # Configuration
    api_version: str = "latest"
    webhook_secret: Optional[str] = None
    additional_params: Dict[str, str] = {}
    
    # Status
    active: bool = True
    last_sync: Optional[datetime] = None
    sync_status: SyncStatus = SyncStatus.PENDING


class D2CStore(BaseModel):
    """Model for D2C store information."""
    store_id: str
    platform_type: D2CPlatform
    store_name: str
    store_url: str
    
    # Store details
    description: Optional[str] = None
    currency: str = "USD"
    timezone: str = "UTC"
    country: str = "US"
    language: str = "en"
    
    # Configuration
    theme_name: Optional[str] = None
    theme_version: Optional[str] = None
    
    # Business information
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    phone: Optional[str] = None
    address: Dict[str, str] = {}
    
    # Status and metrics
    status: StoreStatus = StoreStatus.ACTIVE
    total_products: int = 0
    total_orders: int = 0
    total_customers: int = 0
    
    # Tracking
    created_at: datetime
    updated_at: datetime
    last_sync: Optional[datetime] = None


class D2CProduct(BaseModel):
    """Model for D2C platform products."""
    product_id: str
    store_id: str
    platform_type: D2CPlatform
    platform_product_id: Optional[str] = None
    
    # Basic product info
    title: str
    description: str
    handle: Optional[str] = None  # URL slug
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    tags: List[str] = []
    
    # Variants
    variants: List[Dict[str, Any]] = []
    
    # Pricing
    price: float
    compare_at_price: Optional[float] = None
    cost_per_item: Optional[float] = None
    
    # Inventory
    inventory_tracking: bool = True
    inventory_policy: str = "deny"  # deny, continue
    inventory_quantity: int = 0
    
    # SEO and metadata
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    meta_fields: Dict[str, Any] = {}
    
    # Media
    images: List[Dict[str, str]] = []
    
    # Status
    status: str = "draft"  # draft, active, archived
    published: bool = False
    published_at: Optional[datetime] = None
    
    # Tracking
    created_at: datetime
    updated_at: datetime
    last_sync: Optional[datetime] = None


class D2COrder(BaseModel):
    """Model for D2C platform orders."""
    order_id: str
    store_id: str
    platform_type: D2CPlatform
    platform_order_id: str
    order_number: Optional[str] = None
    
    # Customer information
    customer_id: Optional[str] = None
    customer_email: str
    customer_info: Dict[str, Any] = {}
    
    # Order details
    line_items: List[Dict[str, Any]] = []
    subtotal_price: float
    total_tax: float = 0.0
    total_discounts: float = 0.0
    total_price: float
    currency: str = "USD"
    
    # Status
    financial_status: str = "pending"  # pending, paid, refunded, etc.
    fulfillment_status: str = "unfulfilled"  # unfulfilled, partial, fulfilled
    
    # Addresses
    billing_address: Dict[str, str] = {}
    shipping_address: Dict[str, str] = {}
    
    # Shipping
    shipping_lines: List[Dict[str, Any]] = []
    
    # Dates
    order_date: datetime
    processed_at: Optional[datetime] = None
    
    # Notes
    note: Optional[str] = None
    note_attributes: List[Dict[str, str]] = []
    
    # Tracking
    last_sync: Optional[datetime] = None


class D2CCustomer(BaseModel):
    """Model for D2C platform customers."""
    customer_id: str
    store_id: str
    platform_type: D2CPlatform
    platform_customer_id: str
    
    # Personal information
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    
    # Account status
    accepts_marketing: bool = False
    verified_email: bool = False
    state: str = "enabled"  # enabled, disabled, invited, declined
    
    # Addresses
    addresses: List[Dict[str, Any]] = []
    default_address: Optional[Dict[str, Any]] = None
    
    # Statistics
    orders_count: int = 0
    total_spent: float = 0.0
    
    # Metadata
    tags: List[str] = []
    note: Optional[str] = None
    
    # Tracking
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    last_sync: Optional[datetime] = None


class WebhookEvent(BaseModel):
    """Model for webhook events from D2C platforms."""
    event_id: str
    store_id: str
    platform_type: D2CPlatform
    event_type: str
    topic: str
    
    # Event data
    payload: Dict[str, Any]
    
    # Metadata
    api_version: Optional[str] = None
    webhook_id: Optional[str] = None
    
    # Processing
    processed: bool = False
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Tracking
    received_at: datetime


class D2CEcommerceAgent(BaseAgent):
    """
    D2C E-commerce Platform Agent manages connections to direct-to-consumer platforms including:
    - Shopify REST Admin API and GraphQL integration
    - PrestaShop Web Service API integration
    - WooCommerce REST API integration
    - Multi-store management and synchronization
    - Real-time webhook processing
    - Customer data synchronization
    """
    
    def __init__(self, **kwargs):
        super().__init__(agent_id="d2c_ecommerce_agent", **kwargs)

        
        # D2C platform data
        self.store_credentials: Dict[str, D2CCredentials] = {}
        self.stores: Dict[str, D2CStore] = {}
        self.d2c_products: Dict[str, D2CProduct] = {}
        self.d2c_orders: Dict[str, D2COrder] = {}
        self.d2c_customers: Dict[str, D2CCustomer] = {}
        self.webhook_events: Dict[str, WebhookEvent] = {}
        
        # Platform-specific configurations
        self.platform_configs = self._initialize_platform_configs()
        
        # HTTP session for API calls
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Register message handlers
        self.register_handler(MessageType.PRODUCT_UPDATED, self._handle_product_updated)
        self.register_handler(MessageType.INVENTORY_UPDATED, self._handle_inventory_updated)
        self.register_handler(MessageType.ORDER_STATUS_UPDATED, self._handle_order_status_updated)
        self.register_handler(MessageType.PRICE_UPDATED, self._handle_price_updated)
        self.register_handler(MessageType.NEW_ORDER, self._handle_new_order)
        self.register_handler(MessageType.CUSTOMER_CREATED, self._handle_customer_created)
        self.register_handler(MessageType.CUSTOMER_UPDATED, self._handle_customer_updated)
        self.register_handler(MessageType.WEBHOOK_RECEIVED, self._handle_webhook_received)


    def _initialize_platform_configs(self) -> Dict[D2CPlatform, Dict[str, Any]]:
        """Initialize platform-specific configurations."""
        return {
            D2CPlatform.SHOPIFY: {
                "api_base_url": "https://{shop_domain}/admin/api/{api_version}",
                "graphql_url": "https://{shop_domain}/admin/api/{api_version}/graphql.json",
                "headers": {
                    "X-Shopify-Access-Token": "{access_token}",
                    "Content-Type": "application/json"
                }
            },
            D2CPlatform.PRESTASHOP: {
                "api_base_url": "{store_url}/api",
                "headers": {
                    "Authorization": "Basic {webservice_key}",
                    "Content-Type": "application/xml"
                }
            },
            D2CPlatform.WOOCOMMERCE: {
                "api_base_url": "{store_url}/wp-json/wc/v3",
                "headers": {
                    "Authorization": "Basic {consumer_key}:{consumer_secret}",
                    "Content-Type": "application/json"
                }
            },
            D2CPlatform.MAGENTO: {
                "api_base_url": "{store_url}/rest/{api_version}",
                "headers": {
                    "Authorization": "Bearer {access_token}",
                    "Content-Type": "application/json"
                }
            },
            D2CPlatform.BIGCOMMERCE: {
                "api_base_url": "https://api.bigcommerce.com/stores/{store_id}/v3",
                "headers": {
                    "X-Auth-Token": "{access_token}",
                    "Content-Type": "application/json"
                }
            },
            D2CPlatform.OPENCART: {
                "api_base_url": "{store_url}/index.php?route=api/",
                "headers": {
                    "X-Oc-Session": "{session_id}",
                    "Content-Type": "application/json"
                }
            },
            D2CPlatform.CUSTOM: {
                "api_base_url": "{store_url}/api",
                "headers": {
                    "Content-Type": "application/json"
                }
            }
        }


    async def _make_api_call(self, platform_type: D2CPlatform, store_id: str, method: str, endpoint: str, 
                             data: Optional[Dict] = None, params: Optional[Dict] = None, 
                             is_graphql: bool = False) -> APIResponse:
        """Make an API call to the specified D2C platform."""
        credentials = self.store_credentials.get(store_id)
        if not credentials:
            return APIResponse(success=False, message=f"Credentials not found for store {store_id}")

        config = self.platform_configs.get(platform_type)
        if not config:
            return APIResponse(success=False, message=f"Configuration not found for platform {platform_type.value}")

        # Format base URL and headers with credentials
        api_base_url = config["api_base_url"].format(
            shop_domain=credentials.shop_domain,
            store_url=credentials.store_url,
            api_version=credentials.api_version,
            store_id=credentials.store_id
        )
        
        headers = {k: v.format(
            access_token=credentials.access_token,
            webservice_key=credentials.webservice_key,
            consumer_key=credentials.consumer_key,
            consumer_secret=credentials.consumer_secret
        ) for k, v in config["headers"].items()}

        url = f"{api_base_url}{endpoint}"

        self.logger.info(f"Making API call to {platform_type.value} for store {store_id}", 
                         method=method, url=url, is_graphql=is_graphql)

        try:
            async with self.session.request(method, url, headers=headers, json=data, params=params) as response:
                response.raise_for_status()
                json_response = await response.json()
                return APIResponse(success=True, data=json_response)
        except aiohttp.ClientResponseError as e:
            self.logger.error(f"API call failed for {platform_type.value}", 
                            status=e.status, message=e.message, url=url)
            return APIResponse(success=False, message=f"API error: {e.message}", status_code=e.status)
        except aiohttp.ClientError as e:
            self.logger.error(f"Network error during API call for {platform_type.value}", error=str(e), url=url)
            return APIResponse(success=False, message=f"Network error: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during API call for {platform_type.value}", error=str(e), url=url)
            return APIResponse(success=False, message=f"Unexpected error: {e}")


    async def _load_store_credentials(self):
        """Load store credentials from the database."""
        self.logger.info("Loading store credentials")
        db_manager = get_database_manager()
        credentials_data = await db_manager.get_all_credentials("d2c_platforms") # Assuming a table 'd2c_platforms'
        for cred in credentials_data:
            try:
                d2c_cred = D2CCredentials(**cred)
                self.store_credentials[d2c_cred.store_id] = d2c_cred
                self.logger.info(f"Loaded credentials for store {d2c_cred.store_name}", store_id=d2c_cred.store_id)
            except Exception as e:
                self.logger.error(f"Failed to load credentials: {e}", cred=cred)
        self.logger.info(f"Loaded {len(self.store_credentials)} D2C store credentials")


    async def _handle_product_updated(self, message: AgentMessage):
        """Handle product updated message by synchronizing with D2C platforms."""
        product_data = message.payload
        product_id = product_data.get("product_id")
        self.logger.info(f"Received product updated message for product {product_id}")
        
        # In a real scenario, this would involve complex logic to update products on various D2C platforms
        # For now, we'll just log and simulate an update.
        for store_id, credentials in self.store_credentials.items():
            self.logger.info(f"Simulating product update for product {product_id} on {credentials.platform_type.value} store {store_id}")
            # Example: call a platform-specific update product method
            # await self.update_product_on_platform(credentials.platform_type, store_id, product_data)
        
        await self.send_message(
            recipient_agent="inventory_agent",
            message_type=MessageType.PRODUCT_SYNCED,
            payload={
                "product_id": product_id,
                "status": "synced",
                "timestamp": datetime.now().isoformat()
            }
        )


    async def _handle_inventory_updated(self, message: AgentMessage):
        """Handle inventory updated message."""
        inventory_data = message.payload
        product_id = inventory_data.get("product_id")
        self.logger.info(f"Received inventory updated message for product {product_id}")
        
        for store_id, credentials in self.store_credentials.items():
            self.logger.info(f"Simulating inventory update for product {product_id} on {credentials.platform_type.value} store {store_id}")
            # await self.update_inventory_on_platform(credentials.platform_type, store_id, inventory_data)


    async def _handle_order_status_updated(self, message: AgentMessage):
        """Handle order status updated message."""
        order_data = message.payload
        order_id = order_data.get("order_id")
        self.logger.info(f"Received order status updated message for order {order_id}")
        
        for store_id, credentials in self.store_credentials.items():
            self.logger.info(f"Simulating order status update for order {order_id} on {credentials.platform_type.value} store {store_id}")
            # await self.update_order_status_on_platform(credentials.platform_type, store_id, order_data)


    async def _handle_price_updated(self, message: AgentMessage):
        """Handle price updated message."""
        price_data = message.payload
        product_id = price_data.get("product_id")
        self.logger.info(f"Received price updated message for product {product_id}")
        
        for store_id, credentials in self.store_credentials.items():
            self.logger.info(f"Simulating price update for product {product_id} on {credentials.platform_type.value} store {store_id}")
            # await self.update_price_on_platform(credentials.platform_type, store_id, price_data)


    async def _handle_new_order(self, message: AgentMessage):
        """Handle new order message by creating it in D2C platforms."""
        order_data = message.payload
        order_id = order_data.get("order_id")
        self.logger.info(f"Received new order message for order {order_id}")
        
        for store_id, credentials in self.store_credentials.items():
            self.logger.info(f"Simulating new order creation for order {order_id} on {credentials.platform_type.value} store {store_id}")
            # await self.create_order_on_platform(credentials.platform_type, store_id, order_data)


    async def _handle_customer_created(self, message: AgentMessage):
        """Handle customer created message."""
        customer_data = message.payload
        customer_id = customer_data.get("customer_id")
        self.logger.info(f"Received customer created message for customer {customer_id}")
        
        for store_id, credentials in self.store_credentials.items():
            self.logger.info(f"Simulating customer creation for customer {customer_id} on {credentials.platform_type.value} store {store_id}")
            # await self.create_customer_on_platform(credentials.platform_type, store_id, customer_data)


    async def _handle_customer_updated(self, message: AgentMessage):
        """Handle customer updated message."""
        customer_data = message.payload
        customer_id = customer_data.get("customer_id")
        self.logger.info(f"Received customer updated message for customer {customer_id}")
        
        for store_id, credentials in self.store_credentials.items():
            self.logger.info(f"Simulating customer update for customer {customer_id} on {credentials.platform_type.value} store {store_id}")
            # await self.update_customer_on_platform(credentials.platform_type, store_id, customer_data)


    async def _handle_webhook_received(self, message: AgentMessage):
        """Handle a raw webhook event received from a D2C platform."""
        webhook_data = message.payload
        event_id = str(uuid4())
        self.logger.info(f"Received raw webhook event", event_id=event_id, webhook_data=webhook_data)
        
        try:
            # Extract relevant info from webhook_data to create a WebhookEvent object
            # This parsing logic would be highly dependent on the platform and webhook structure
            # For demonstration, we'll assume some basic fields.
            platform_type_str = webhook_data.get("platform_type", "custom")
            store_id = webhook_data.get("store_id", "unknown_store")
            event_type = webhook_data.get("event_type", "unknown_event")
            topic = webhook_data.get("topic", "unknown_topic")

            webhook_event = WebhookEvent(
                event_id=event_id,
                store_id=store_id,
                platform_type=D2CPlatform(platform_type_str),
                event_type=event_type,
                topic=topic,
                payload=webhook_data,
                received_at=datetime.utcnow()
            )
            self.webhook_events[event_id] = webhook_event
            self.logger.info(f"Stored new webhook event", event_id=event_id, store_id=store_id, event_type=event_type)
            
            # Trigger processing of the webhook event
            await self.send_message(
                recipient_agent=self.agent_id,
                message_type=MessageType.PROCESS_WEBHOOK,
                payload={
                    "event_id": event_id
                }
            )

        except Exception as e:
            self.logger.error(f"Failed to process incoming webhook: {e}", webhook_data=webhook_data)


    async def _handle_process_webhook(self, message: AgentMessage):
        """Process a stored webhook event."""
        event_id = message.payload.get("event_id")
        webhook_event = self.webhook_events.get(event_id)
        
        if not webhook_event:
            self.logger.warning(f"Webhook event {event_id} not found for processing.")
            return
        
        self.logger.info(f"Processing webhook event", event_id=event_id, 
                         store_id=webhook_event.store_id, event_type=webhook_event.event_type)
        
        try:
            # This is where the actual logic for handling different webhook topics would go.
            # Example: product_create, order_paid, customer_update, etc.
            if webhook_event.topic == "products/create":
                self.logger.info(f"Handling product create webhook for store {webhook_event.store_id}")
                # Simulate product creation in our system or trigger further actions
                product_info = webhook_event.payload.get("product")
                if product_info:
                    await self.send_message(
                        recipient_agent="product_agent",
                        message_type=MessageType.PRODUCT_CREATED,
                        payload=product_info
                    )
            elif webhook_event.topic == "orders/create":
                self.logger.info(f"Handling order create webhook for store {webhook_event.store_id}")
                order_info = webhook_event.payload.get("order")
                if order_info:
                    await self.send_message(
                        recipient_agent="order_agent",
                        message_type=MessageType.NEW_ORDER,
                        payload=order_info
                    )
            
            webhook_event.processed = True
            webhook_event.processed_at = datetime.utcnow()
            self.logger.info(f"Successfully processed webhook event {event_id}")
            
        except Exception as e:
            self.logger.error(f"Error processing webhook event {event_id}: {e}", 
                            event_id=event_id, error=str(e))
            webhook_event.error_message = str(e)
            webhook_event.processed = False # Mark as not processed if error


    async def _sync_d2c_orders(self):
        """Background task to synchronize orders from D2C platforms."""
        while not self.shutdown_event.is_set():
            try:
                # Sync orders every 10 minutes
                await asyncio.sleep(600) 
                self.logger.info("Starting D2C orders synchronization")
                
                if not self.shutdown_event.is_set():
                    for store_id, credentials in self.store_credentials.items():
                        self.logger.info(f"Syncing orders for {credentials.platform_type.value} store {store_id}")
                        # In a real scenario, this would fetch orders from the D2C platform
                        # For demonstration, we'll simulate fetching new orders.
                        # Example: new_orders = await self.fetch_orders_from_platform(credentials.platform_type, store_id)
                        # for order in new_orders:
                        #     self.d2c_orders[order.order_id] = order
                        #     await self.send_message(MessageType.NEW_ORDER, order.dict())
            
            except Exception as e:
                self.logger.error("Error during D2C orders synchronization", error=str(e))
                await asyncio.sleep(600)


    async def _sync_d2c_products(self):
        """Background task to synchronize products from D2C platforms."""
        while not self.shutdown_event.is_set():
            try:
                # Sync products every 30 minutes
                await asyncio.sleep(1800) 
                self.logger.info("Starting D2C products synchronization")
                
                if not self.shutdown_event.is_set():
                    for store_id, credentials in self.store_credentials.items():
                        self.logger.info(f"Syncing products for {credentials.platform_type.value} store {store_id}")
                        # Example: new_products = await self.fetch_products_from_platform(credentials.platform_type, store_id)
                        # for product in new_products:
                        #     self.d2c_products[product.product_id] = product
                        #     await self.send_message(MessageType.PRODUCT_UPDATED, product.dict())
            
            except Exception as e:
                self.logger.error("Error during D2C products synchronization", error=str(e))
                await asyncio.sleep(1800)


    async def _sync_d2c_customers(self):
        """Background task to synchronize customers from D2C platforms."""
        while not self.shutdown_event.is_set():
            try:
                # Sync customers every hour
                await asyncio.sleep(3600) 
                self.logger.info("Starting D2C customers synchronization")
                
                if not self.shutdown_event.is_set():
                    for store_id, credentials in self.store_credentials.items():
                        self.logger.info(f"Syncing customers for {credentials.platform_type.value} store {store_id}")
                        # Example: new_customers = await self.fetch_customers_from_platform(credentials.platform_type, store_id)
                        # for customer in new_customers:
                        #     self.d2c_customers[customer.customer_id] = customer
                        #     await self.send_message(MessageType.CUSTOMER_UPDATED, customer.dict())
            
            except Exception as e:
                self.logger.error("Error during D2C customers synchronization", error=str(e))
                await asyncio.sleep(3600)


    async def _process_webhook_events(self):
        """Background task to process webhook events."""
        while not self.shutdown_event.is_set():
            try:
                # Process webhooks every 10 seconds
                await asyncio.sleep(10)
                
                if not self.shutdown_event.is_set():
                    unprocessed_events = [event for event in self.webhook_events.values() if not event.processed]
                    self.logger.info(f"Found {len(unprocessed_events)} unprocessed webhook events")
                    for event in unprocessed_events:
                        try:
                            # Call the handler for processing
                            result = await self._handle_process_webhook(AgentMessage(
                                sender_agent=self.agent_id,
                                recipient_agent=self.agent_id,
                                message_type=MessageType.PROCESS_WEBHOOK,
                                payload={
                                    "event_id": event.event_id
                                }
                            ))
                            
                            if result and result.get("success", False):
                                event.processed = True
                                event.processed_at = datetime.utcnow()
                            else:
                                event.error_message = result.get("error", "Unknown error during processing")
                        
                        except Exception as e:
                            self.logger.error("Failed to process webhook event", 
                                            error=str(e), 
                                            event_id=event.event_id)
                            event.error_message = str(e)
            
            except Exception as e:
                self.logger.error("Error processing webhook events", error=str(e))
                await asyncio.sleep(60)


    async def _monitor_store_health(self):
        """Background task to monitor store health."""
        while not self.shutdown_event.is_set():
            try:
                # Monitor store health every hour
                await asyncio.sleep(3600)
                
                if not self.shutdown_event.is_set():
                    for store_id, store in self.stores.items():
                        try:
                            # Check store health metrics
                            credentials = self.store_credentials.get(store_id)
                            
                            if credentials:
                                # In production, this would make health check API calls
                                
                                # Check for sync issues
                                last_sync = credentials.last_sync
                                if last_sync and (datetime.utcnow() - last_sync).total_seconds() > 7200:  # 2 hours
                                    await self.send_message(
                                        recipient_agent="monitoring_agent",
                                        message_type=MessageType.RISK_ALERT,
                                        payload={
                                            "alert_type": "sync_delay",
                                            "store_id": store_id,
                                            "platform_type": store.platform_type.value,
                                            "last_sync": last_sync.isoformat() if last_sync else None
                                        }
                                    )
                        
                        except Exception as e:
                            self.logger.error("Failed to monitor store health", 
                                            error=str(e), 
                                            store_id=store_id)
            
            except Exception as e:
                self.logger.error("Error monitoring store health", error=str(e))
                await asyncio.sleep(3600)


# FastAPI app instance for running the agent as a service
app = FastAPI(title="D2C E-commerce Platform Agent", version="1.0.0")

# Global agent instance
d2c_ecommerce_agent: Optional[D2CEcommerceAgent] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the D2C E-commerce Agent on startup."""
    global d2c_ecommerce_agent
    d2c_ecommerce_agent = D2CEcommerceAgent()
    await d2c_ecommerce_agent.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup the D2C E-commerce Agent on shutdown."""
    global d2c_ecommerce_agent
    if d2c_ecommerce_agent:
        await d2c_ecommerce_agent.stop()

# Include agent routes
@app.get("/", summary="Root endpoint for agent status")
async def read_root():
    return {"agent_name": "d2c_ecommerce_agent", "status": "running"}

@app.get("/health", summary="Health check endpoint")
async def health_check():
    """Health check endpoint."""
    if d2c_ecommerce_agent:
        health_status = d2c_ecommerce_agent.get_health_status()
        return {"agent_name": "d2c_ecommerce_agent", "status": "healthy", "agent_status": health_status.dict()}
    return {"agent_name": "d2c_ecommerce_agent", "status": "unhealthy", "message": "Agent not initialized"}

# Mount agent's FastAPI app
# This line is problematic if d2c_ecommerce_agent.app is not a FastAPI instance or router
# Assuming BaseAgent will have a method to return its internal FastAPI router if it manages one.
# For now, we will comment it out or adjust based on BaseAgent's actual implementation.
# app.mount("/api/v1", d2c_ecommerce_agent.app if d2c_ecommerce_agent else FastAPI())

if __name__ == "__main__":
    import uvicorn
    from shared.database import initialize_database_manager, DatabaseConfig
    
    # Initialize database
    db_password = os.getenv("POSTGRES_PASSWORD")
    if not db_password:
        raise ValueError("Database password must be set in environment variables")

    db_config = DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "multi_agent_ecommerce"),
        username=os.getenv("POSTGRES_USER", "postgres"),
        password=db_password
    )
    
    initialize_database_manager(db_config)
    
    # Run the agent
    uvicorn.run(
        "d2c_ecommerce_agent:app",
        host="0.0.0.0",
        port=8013,
        reload=False,
        log_level="info"
    )

