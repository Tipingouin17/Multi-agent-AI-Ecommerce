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
    print(f"Added {project_root} to Python path")

# Now try the import
try:
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
        self.app = FastAPI(title="D2C E-commerce Platform Agent API", version="1.0.0")
        self.setup_routes()
        
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
    
    async def initialize(self):
        """Initialize the D2C E-commerce Agent."""
        self.logger.info("Initializing D2C E-commerce Agent")
        
        # Initialize HTTP session
        self.session = aiohttp.ClientSession()
        
        # Load store credentials
        await self._load_store_credentials()
        
        # Start background tasks
        asyncio.create_task(self._sync_d2c_orders())
        asyncio.create_task(self._sync_d2c_products())
        asyncio.create_task(self._sync_d2c_customers())
        asyncio.create_task(self._process_webhook_events())
        asyncio.create_task(self._monitor_store_health())
        
        self.logger.info("D2C E-commerce Agent initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up D2C E-commerce Agent")
        
        if self.session:
            await self.session.close()
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process D2C e-commerce business logic."""
        action = data.get("action")
        
        if action == "create_product":
            return await self._create_d2c_product(data["store_id"], data["product_data"])
        elif action == "update_product":
            return await self._update_d2c_product(data["product_id"], data["updates"])
        elif action == "sync_orders":
            return await self._sync_orders(data["store_id"])
        elif action == "sync_customers":
            return await self._sync_customers(data["store_id"])
        elif action == "process_webhook":
            return await self._process_webhook(data["webhook_data"])
        elif action == "update_inventory":
            return await self._update_d2c_inventory(data["product_id"], data["quantity"])
        elif action == "fulfill_order":
            return await self._fulfill_d2c_order(data["order_id"], data["fulfillment_data"])
        elif action == "get_store_analytics":
            return await self._get_store_analytics(data["store_id"])
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def setup_routes(self):
        """Setup FastAPI routes for the D2C E-commerce Agent."""
        
        @self.app.post("/stores/credentials", response_model=APIResponse)
        async def add_store_credentials(credentials: D2CCredentials):
            """Add D2C store API credentials."""
            try:
                # Validate credentials
                validation_result = await self._validate_store_credentials(credentials)
                
                if validation_result["valid"]:
                    self.store_credentials[credentials.store_id] = credentials
                    
                    # Create store record
                    store_info = await self._fetch_store_info(credentials)
                    if store_info:
                        self.stores[credentials.store_id] = store_info
                    
                    return APIResponse(
                        success=True,
                        message="D2C store credentials added successfully",
                        data={"store_id": credentials.store_id, "validation": validation_result}
                    )
                else:
                    raise HTTPException(status_code=400, detail=f"Invalid credentials: {validation_result['error']}")
            
            except Exception as e:
                self.logger.error("Failed to add store credentials", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/stores/{store_id}/products", response_model=APIResponse)
        async def create_product(store_id: str, product_data: D2CProduct):
            """Create a new product on D2C platform."""
            try:
                result = await self._create_d2c_product(store_id, product_data.dict())
                
                return APIResponse(
                    success=True,
                    message="D2C product created successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to create D2C product", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.put("/products/{product_id}", response_model=APIResponse)
        async def update_product(product_id: str, updates: Dict[str, Any]):
            """Update D2C product."""
            try:
                result = await self._update_d2c_product(product_id, updates)
                
                return APIResponse(
                    success=True,
                    message="D2C product updated successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to update D2C product", error=str(e), product_id=product_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/stores/{store_id}/sync/orders", response_model=APIResponse)
        async def sync_orders(store_id: str):
            """Synchronize orders from D2C platform."""
            try:
                result = await self._sync_orders(store_id)
                
                return APIResponse(
                    success=True,
                    message="Orders synchronized successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to sync orders", error=str(e), store_id=store_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/webhooks/{store_id}", response_model=APIResponse)
        async def process_webhook(store_id: str, webhook_data: Dict[str, Any]):
            """Process webhook from D2C platform."""
            try:
                result = await self._process_webhook({
                    "store_id": store_id,
                    **webhook_data
                })
                
                return APIResponse(
                    success=True,
                    message="Webhook processed successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to process webhook", error=str(e), store_id=store_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.put("/products/{product_id}/inventory", response_model=APIResponse)
        async def update_inventory(product_id: str, inventory_data: Dict[str, Any]):
            """Update product inventory on D2C platform."""
            try:
                result = await self._update_d2c_inventory(
                    product_id, 
                    inventory_data.get("quantity", 0)
                )
                
                return APIResponse(
                    success=True,
                    message="Inventory updated successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to update inventory", error=str(e), product_id=product_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/orders/{order_id}/fulfill", response_model=APIResponse)
        async def fulfill_order(order_id: str, fulfillment_data: Dict[str, Any]):
            """Fulfill order on D2C platform."""
            try:
                result = await self._fulfill_d2c_order(order_id, fulfillment_data)
                
                return APIResponse(
                    success=True,
                    message="Order fulfilled successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to fulfill order", error=str(e), order_id=order_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/stores", response_model=APIResponse)
        async def list_stores(platform_type: Optional[D2CPlatform] = None):
            """List D2C stores with optional platform filter."""
            try:
                stores = list(self.stores.values())
                
                if platform_type:
                    stores = [s for s in stores if s.platform_type == platform_type]
                
                return APIResponse(
                    success=True,
                    message="Stores retrieved successfully",
                    data={"stores": [s.dict() for s in stores]}
                )
            
            except Exception as e:
                self.logger.error("Failed to list stores", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/stores/{store_id}/analytics", response_model=APIResponse)
        async def get_store_analytics(store_id: str):
            """Get store analytics and metrics."""
            try:
                result = await self._get_store_analytics(store_id)
                
                return APIResponse(
                    success=True,
                    message="Store analytics retrieved successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to get store analytics", error=str(e), store_id=store_id)
                raise HTTPException(status_code=500, detail=str(e))
    
    def _initialize_platform_configs(self) -> Dict[str, Dict[str, Any]]:
        """Initialize platform-specific configurations."""
        return {
            D2CPlatform.SHOPIFY.value: {
                "api_base": "https://{shop_domain}.myshopify.com/admin/api/{version}",
                "auth_type": "token",
                "rate_limit": 40,  # requests per second
                "webhook_topics": [
                    "orders/create", "orders/updated", "orders/paid",
                    "products/create", "products/update",
                    "customers/create", "customers/update"
                ],
                "required_scopes": [
                    "read_products", "write_products",
                    "read_orders", "write_orders",
                    "read_customers", "write_customers"
                ]
            },
            D2CPlatform.WOOCOMMERCE.value: {
                "api_base": "{store_url}/wp-json/wc/v3",
                "auth_type": "oauth",
                "rate_limit": 10,
                "webhook_topics": [
                    "order.created", "order.updated",
                    "product.created", "product.updated",
                    "customer.created", "customer.updated"
                ],
                "required_permissions": [
                    "read", "write"
                ]
            },
            D2CPlatform.PRESTASHOP.value: {
                "api_base": "{store_url}/api",
                "auth_type": "key",
                "rate_limit": 5,
                "webhook_topics": [
                    "actionOrderStatusUpdate",
                    "actionProductSave",
                    "actionCustomerAccountAdd"
                ],
                "output_format": "JSON"
            },
            D2CPlatform.MAGENTO.value: {
                "api_base": "{store_url}/rest/V1",
                "auth_type": "token",
                "rate_limit": 20,
                "webhook_topics": [
                    "sales_order_save_after",
                    "catalog_product_save_after",
                    "customer_save_after"
                ]
            },
            D2CPlatform.BIGCOMMERCE.value: {
                "api_base": "https://api.bigcommerce.com/stores/{store_hash}/v3",
                "auth_type": "token",
                "rate_limit": 20,
                "webhook_topics": [
                    "store/order/*",
                    "store/product/*",
                    "store/customer/*"
                ]
            }
        }
    
    async def _validate_store_credentials(self, credentials: D2CCredentials) -> Dict[str, Any]:
        """Validate D2C store API credentials."""
        try:
            if credentials.platform_type == D2CPlatform.SHOPIFY:
                return await self._validate_shopify_credentials(credentials)
            elif credentials.platform_type == D2CPlatform.WOOCOMMERCE:
                return await self._validate_woocommerce_credentials(credentials)
            elif credentials.platform_type == D2CPlatform.PRESTASHOP:
                return await self._validate_prestashop_credentials(credentials)
            elif credentials.platform_type == D2CPlatform.MAGENTO:
                return await self._validate_magento_credentials(credentials)
            elif credentials.platform_type == D2CPlatform.BIGCOMMERCE:
                return await self._validate_bigcommerce_credentials(credentials)
            else:
                # Generic validation
                return {"valid": True, "message": "Credentials format validated"}
        
        except Exception as e:
            self.logger.error("Failed to validate store credentials", error=str(e))
            return {"valid": False, "error": str(e)}
    
    async def _validate_shopify_credentials(self, credentials: D2CCredentials) -> Dict[str, Any]:
        """Validate Shopify API credentials."""
        try:
            if not credentials.shop_domain or not credentials.access_token:
                return {"valid": False, "error": "Shop domain and access token are required for Shopify"}
            
            # Test API call to Shopify
            url = f"https://{credentials.shop_domain}.myshopify.com/admin/api/2023-10/shop.json"
            headers = {
                "X-Shopify-Access-Token": credentials.access_token,
                "Content-Type": "application/json"
            }
            
            # In production, this would make an actual API call
            self.logger.info("Shopify credentials validated", shop_domain=credentials.shop_domain)
            
            return {"valid": True, "message": "Shopify credentials validated successfully"}
        
        except Exception as e:
            return {"valid": False, "error": f"Shopify validation failed: {str(e)}"}
    
    async def _validate_woocommerce_credentials(self, credentials: D2CCredentials) -> Dict[str, Any]:
        """Validate WooCommerce API credentials."""
        try:
            if not credentials.consumer_key or not credentials.consumer_secret:
                return {"valid": False, "error": "Consumer key and secret are required for WooCommerce"}
            
            # Test API call to WooCommerce
            # In production, this would make an actual API call
            self.logger.info("WooCommerce credentials validated", store_url=credentials.store_url)
            
            return {"valid": True, "message": "WooCommerce credentials validated successfully"}
        
        except Exception as e:
            return {"valid": False, "error": f"WooCommerce validation failed: {str(e)}"}
    
    async def _validate_prestashop_credentials(self, credentials: D2CCredentials) -> Dict[str, Any]:
        """Validate PrestaShop API credentials."""
        try:
            if not credentials.webservice_key:
                return {"valid": False, "error": "Webservice key is required for PrestaShop"}
            
            # Test API call to PrestaShop
            self.logger.info("PrestaShop credentials validated", store_url=credentials.store_url)
            
            return {"valid": True, "message": "PrestaShop credentials validated successfully"}
        
        except Exception as e:
            return {"valid": False, "error": f"PrestaShop validation failed: {str(e)}"}
    
    async def _validate_magento_credentials(self, credentials: D2CCredentials) -> Dict[str, Any]:
        """Validate Magento API credentials."""
        try:
            if not credentials.access_token:
                return {"valid": False, "error": "Access token is required for Magento"}
            
            # Test API call to Magento
            self.logger.info("Magento credentials validated", store_url=credentials.store_url)
            
            return {"valid": True, "message": "Magento credentials validated successfully"}
        
        except Exception as e:
            return {"valid": False, "error": f"Magento validation failed: {str(e)}"}
    
    async def _validate_bigcommerce_credentials(self, credentials: D2CCredentials) -> Dict[str, Any]:
        """Validate BigCommerce API credentials."""
        try:
            if not credentials.access_token:
                return {"valid": False, "error": "Access token is required for BigCommerce"}
            
            # Test API call to BigCommerce
            self.logger.info("BigCommerce credentials validated", store_id=credentials.store_id)
            
            return {"valid": True, "message": "BigCommerce credentials validated successfully"}
        
        except Exception as e:
            return {"valid": False, "error": f"BigCommerce validation failed: {str(e)}"}
    
    async def _fetch_store_info(self, credentials: D2CCredentials) -> Optional[D2CStore]:
        """Fetch store information from D2C platform."""
        try:
            if credentials.platform_type == D2CPlatform.SHOPIFY:
                return await self._fetch_shopify_store_info(credentials)
            elif credentials.platform_type == D2CPlatform.WOOCOMMERCE:
                return await self._fetch_woocommerce_store_info(credentials)
            elif credentials.platform_type == D2CPlatform.PRESTASHOP:
                return await self._fetch_prestashop_store_info(credentials)
            else:
                # Generic store info
                return D2CStore(
                    store_id=credentials.store_id,
                    platform_type=credentials.platform_type,
                    store_name=credentials.store_name,
                    store_url=credentials.store_url,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
        
        except Exception as e:
            self.logger.error("Failed to fetch store info", error=str(e))
            return None
    
    async def _fetch_shopify_store_info(self, credentials: D2CCredentials) -> D2CStore:
        """Fetch Shopify store information."""
        # Simulate Shopify store info
        return D2CStore(
            store_id=credentials.store_id,
            platform_type=D2CPlatform.SHOPIFY,
            store_name=credentials.store_name,
            store_url=f"https://{credentials.shop_domain}.myshopify.com",
            description="Shopify store",
            currency="USD",
            timezone="America/New_York",
            country="US",
            language="en",
            theme_name="Dawn",
            theme_version="2.0",
            owner_email="owner@shopify-store.com",
            status=StoreStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    async def _fetch_woocommerce_store_info(self, credentials: D2CCredentials) -> D2CStore:
        """Fetch WooCommerce store information."""
        # Simulate WooCommerce store info
        return D2CStore(
            store_id=credentials.store_id,
            platform_type=D2CPlatform.WOOCOMMERCE,
            store_name=credentials.store_name,
            store_url=credentials.store_url,
            description="WooCommerce store",
            currency="USD",
            timezone="UTC",
            country="US",
            language="en",
            status=StoreStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    async def _fetch_prestashop_store_info(self, credentials: D2CCredentials) -> D2CStore:
        """Fetch PrestaShop store information."""
        # Simulate PrestaShop store info
        return D2CStore(
            store_id=credentials.store_id,
            platform_type=D2CPlatform.PRESTASHOP,
            store_name=credentials.store_name,
            store_url=credentials.store_url,
            description="PrestaShop store",
            currency="EUR",
            timezone="Europe/Paris",
            country="FR",
            language="fr",
            status=StoreStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    async def _create_d2c_product(self, store_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product on D2C platform."""
        try:
            credentials = self.store_credentials.get(store_id)
            if not credentials:
                raise ValueError(f"Store credentials not found for {store_id}")
            
            # Create D2C product
            product = D2CProduct(
                product_id=product_data.get("product_id", str(uuid4())),
                store_id=store_id,
                platform_type=credentials.platform_type,
                title=product_data["title"],
                description=product_data["description"],
                handle=product_data.get("handle"),
                vendor=product_data.get("vendor"),
                product_type=product_data.get("product_type"),
                tags=product_data.get("tags", []),
                variants=product_data.get("variants", []),
                price=product_data["price"],
                compare_at_price=product_data.get("compare_at_price"),
                cost_per_item=product_data.get("cost_per_item"),
                inventory_tracking=product_data.get("inventory_tracking", True),
                inventory_policy=product_data.get("inventory_policy", "deny"),
                inventory_quantity=product_data.get("inventory_quantity", 0),
                seo_title=product_data.get("seo_title"),
                seo_description=product_data.get("seo_description"),
                meta_fields=product_data.get("meta_fields", {}),
                images=product_data.get("images", []),
                status=product_data.get("status", "draft"),
                published=product_data.get("published", False),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Create product on platform
            platform_result = await self._create_platform_product(product, credentials)
            
            if platform_result["success"]:
                product.platform_product_id = platform_result.get("platform_product_id")
                product.status = "active"
                product.last_sync = datetime.utcnow()
                
                # Store product
                self.d2c_products[product.product_id] = product
                
                # Send notification
                await self.send_message(
                    recipient_agent="product_agent",
                    message_type=MessageType.LISTING_CREATED,
                    payload={
                        "product_id": product.product_id,
                        "store_id": store_id,
                        "platform_type": product.platform_type.value,
                        "platform_product_id": product.platform_product_id,
                        "title": product.title,
                        "price": product.price
                    }
                )
                
                return product.dict()
            else:
                raise Exception(f"Failed to create platform product: {platform_result.get('error')}")
        
        except Exception as e:
            self.logger.error("Failed to create D2C product", error=str(e))
            raise
    
    async def _create_platform_product(self, product: D2CProduct, credentials: D2CCredentials) -> Dict[str, Any]:
        """Create product on specific D2C platform."""
        try:
            if credentials.platform_type == D2CPlatform.SHOPIFY:
                return await self._create_shopify_product(product, credentials)
            elif credentials.platform_type == D2CPlatform.WOOCOMMERCE:
                return await self._create_woocommerce_product(product, credentials)
            elif credentials.platform_type == D2CPlatform.PRESTASHOP:
                return await self._create_prestashop_product(product, credentials)
            elif credentials.platform_type == D2CPlatform.MAGENTO:
                return await self._create_magento_product(product, credentials)
            elif credentials.platform_type == D2CPlatform.BIGCOMMERCE:
                return await self._create_bigcommerce_product(product, credentials)
            else:
                # Generic product creation
                return await self._create_generic_product(product, credentials)
        
        except Exception as e:
            self.logger.error("Failed to create platform product", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _create_shopify_product(self, product: D2CProduct, credentials: D2CCredentials) -> Dict[str, Any]:
        """Create product on Shopify."""
        try:
            # Shopify product creation
            shopify_data = {
                "product": {
                    "title": product.title,
                    "body_html": product.description,
                    "vendor": product.vendor or "",
                    "product_type": product.product_type or "",
                    "handle": product.handle,
                    "tags": ",".join(product.tags),
                    "status": "active" if product.published else "draft",
                    "variants": [
                        {
                            "price": str(product.price),
                            "compare_at_price": str(product.compare_at_price) if product.compare_at_price else None,
                            "inventory_quantity": product.inventory_quantity,
                            "inventory_management": "shopify" if product.inventory_tracking else None,
                            "inventory_policy": product.inventory_policy
                        }
                    ] if not product.variants else product.variants,
                    "images": [{"src": img.get("src", img)} for img in product.images] if product.images else []
                }
            }
            
            # Add SEO fields
            if product.seo_title or product.seo_description:
                shopify_data["product"]["seo"] = {
                    "title": product.seo_title,
                    "description": product.seo_description
                }
            
            # Simulate Shopify API call
            self.logger.info("Shopify product created", 
                           title=product.title, 
                           price=product.price,
                           shop_domain=credentials.shop_domain)
            
            return {
                "success": True,
                "platform_product_id": f"shopify_{uuid4().hex[:8]}",
                "message": "Shopify product created successfully"
            }
        
        except Exception as e:
            self.logger.error("Failed to create Shopify product", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _create_woocommerce_product(self, product: D2CProduct, credentials: D2CCredentials) -> Dict[str, Any]:
        """Create product on WooCommerce."""
        try:
            # WooCommerce product creation
            wc_data = {
                "name": product.title,
                "description": product.description,
                "short_description": product.description[:100] + "..." if len(product.description) > 100 else product.description,
                "sku": product.product_id,
                "regular_price": str(product.price),
                "sale_price": str(product.compare_at_price) if product.compare_at_price else "",
                "manage_stock": product.inventory_tracking,
                "stock_quantity": product.inventory_quantity if product.inventory_tracking else None,
                "stock_status": "instock" if product.inventory_quantity > 0 else "outofstock",
                "status": "publish" if product.published else "draft",
                "catalog_visibility": "visible",
                "tags": [{"name": tag} for tag in product.tags],
                "images": [{"src": img.get("src", img)} for img in product.images] if product.images else []
            }
            
            # Add categories if product type is specified
            if product.product_type:
                wc_data["categories"] = [{"name": product.product_type}]
            
            # Simulate WooCommerce API call
            self.logger.info("WooCommerce product created", 
                           name=product.title, 
                           price=product.price,
                           store_url=credentials.store_url)
            
            return {
                "success": True,
                "platform_product_id": f"wc_{uuid4().hex[:8]}",
                "message": "WooCommerce product created successfully"
            }
        
        except Exception as e:
            self.logger.error("Failed to create WooCommerce product", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _create_prestashop_product(self, product: D2CProduct, credentials: D2CCredentials) -> Dict[str, Any]:
        """Create product on PrestaShop."""
        try:
            # PrestaShop product creation
            ps_data = {
                "product": {
                    "name": {"language": [{"attrs": {"id": "1"}, "value": product.title}]},
                    "description": {"language": [{"attrs": {"id": "1"}, "value": product.description}]},
                    "price": str(product.price),
                    "quantity": str(product.inventory_quantity),
                    "active": "1" if product.published else "0",
                    "available_for_order": "1",
                    "show_price": "1",
                    "reference": product.product_id
                }
            }
            
            # Simulate PrestaShop API call
            self.logger.info("PrestaShop product created", 
                           name=product.title, 
                           price=product.price,
                           store_url=credentials.store_url)
            
            return {
                "success": True,
                "platform_product_id": f"ps_{uuid4().hex[:8]}",
                "message": "PrestaShop product created successfully"
            }
        
        except Exception as e:
            self.logger.error("Failed to create PrestaShop product", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _create_magento_product(self, product: D2CProduct, credentials: D2CCredentials) -> Dict[str, Any]:
        """Create product on Magento."""
        try:
            # Magento product creation
            magento_data = {
                "product": {
                    "sku": product.product_id,
                    "name": product.title,
                    "attribute_set_id": 4,  # Default attribute set
                    "price": product.price,
                    "status": 1 if product.published else 2,
                    "visibility": 4,  # Catalog, Search
                    "type_id": "simple",
                    "weight": 1,
                    "extension_attributes": {
                        "stock_item": {
                            "qty": product.inventory_quantity,
                            "is_in_stock": product.inventory_quantity > 0,
                            "manage_stock": product.inventory_tracking
                        }
                    },
                    "custom_attributes": [
                        {"attribute_code": "description", "value": product.description}
                    ]
                }
            }
            
            # Simulate Magento API call
            self.logger.info("Magento product created", 
                           name=product.title, 
                           price=product.price,
                           store_url=credentials.store_url)
            
            return {
                "success": True,
                "platform_product_id": f"magento_{uuid4().hex[:8]}",
                "message": "Magento product created successfully"
            }
        
        except Exception as e:
            self.logger.error("Failed to create Magento product", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _create_bigcommerce_product(self, product: D2CProduct, credentials: D2CCredentials) -> Dict[str, Any]:
        """Create product on BigCommerce."""
        try:
            # BigCommerce product creation
            bc_data = {
                "name": product.title,
                "description": product.description,
                "sku": product.product_id,
                "price": product.price,
                "sale_price": product.compare_at_price,
                "inventory_level": product.inventory_quantity,
                "inventory_tracking": "product" if product.inventory_tracking else "none",
                "is_visible": product.published,
                "availability": "available" if product.inventory_quantity > 0 else "disabled",
                "weight": 1,
                "categories": [1],  # Default category
                "images": [{"image_url": img.get("src", img)} for img in product.images] if product.images else []
            }
            
            # Simulate BigCommerce API call
            self.logger.info("BigCommerce product created", 
                           name=product.title, 
                           price=product.price,
                           store_id=credentials.store_id)
            
            return {
                "success": True,
                "platform_product_id": f"bc_{uuid4().hex[:8]}",
                "message": "BigCommerce product created successfully"
            }
        
        except Exception as e:
            self.logger.error("Failed to create BigCommerce product", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _create_generic_product(self, product: D2CProduct, credentials: D2CCredentials) -> Dict[str, Any]:
        """Create product on generic D2C platform."""
        try:
            self.logger.info("Generic D2C product created", 
                           platform=credentials.platform_type.value,
                           name=product.title, 
                           price=product.price)
            
            return {
                "success": True,
                "platform_product_id": f"{credentials.platform_type.value}_{product.product_id}",
                "message": f"{credentials.platform_type.value} product created successfully"
            }
        
        except Exception as e:
            self.logger.error("Failed to create generic D2C product", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _update_d2c_product(self, product_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update D2C product."""
        try:
            product = self.d2c_products.get(product_id)
            if not product:
                raise ValueError(f"Product {product_id} not found")
            
            # Update product fields
            for field, value in updates.items():
                if hasattr(product, field):
                    setattr(product, field, value)
            
            product.updated_at = datetime.utcnow()
            
            # Update on platform
            credentials = self.store_credentials.get(product.store_id)
            if credentials:
                platform_result = await self._update_platform_product(product, credentials, updates)
                
                if platform_result["success"]:
                    product.last_sync = datetime.utcnow()
                    
                    # Send notification
                    await self.send_message(
                        recipient_agent="product_agent",
                        message_type=MessageType.LISTING_UPDATED,
                        payload={
                            "product_id": product_id,
                            "store_id": product.store_id,
                            "platform_type": product.platform_type.value,
                            "updates": updates
                        }
                    )
                    
                    return product.dict()
                else:
                    raise Exception(f"Failed to update platform product: {platform_result.get('error')}")
            else:
                raise ValueError(f"Store credentials not found for {product.store_id}")
        
        except Exception as e:
            self.logger.error("Failed to update D2C product", error=str(e), product_id=product_id)
            raise
    
    async def _update_platform_product(self, product: D2CProduct, credentials: D2CCredentials, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update product on D2C platform."""
        try:
            # Platform-specific product update
            if credentials.platform_type == D2CPlatform.SHOPIFY:
                return await self._update_shopify_product(product, credentials, updates)
            elif credentials.platform_type == D2CPlatform.WOOCOMMERCE:
                return await self._update_woocommerce_product(product, credentials, updates)
            elif credentials.platform_type == D2CPlatform.PRESTASHOP:
                return await self._update_prestashop_product(product, credentials, updates)
            else:
                # Generic update
                return {"success": True, "message": "Generic product updated"}
        
        except Exception as e:
            self.logger.error("Failed to update platform product", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _update_shopify_product(self, product: D2CProduct, credentials: D2CCredentials, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update product on Shopify."""
        # Simulate Shopify product update
        self.logger.info("Shopify product updated", 
                       product_id=product.platform_product_id,
                       updates=list(updates.keys()))
        return {"success": True, "message": "Shopify product updated"}
    
    async def _update_woocommerce_product(self, product: D2CProduct, credentials: D2CCredentials, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update product on WooCommerce."""
        # Simulate WooCommerce product update
        self.logger.info("WooCommerce product updated", 
                       product_id=product.platform_product_id,
                       updates=list(updates.keys()))
        return {"success": True, "message": "WooCommerce product updated"}
    
    async def _update_prestashop_product(self, product: D2CProduct, credentials: D2CCredentials, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update product on PrestaShop."""
        # Simulate PrestaShop product update
        self.logger.info("PrestaShop product updated", 
                       product_id=product.platform_product_id,
                       updates=list(updates.keys()))
        return {"success": True, "message": "PrestaShop product updated"}
    
    async def _sync_orders(self, store_id: str) -> Dict[str, Any]:
        """Synchronize orders from D2C platform."""
        try:
            credentials = self.store_credentials.get(store_id)
            if not credentials:
                raise ValueError(f"Store credentials not found for {store_id}")
            
            # Fetch orders from platform
            orders = await self._fetch_d2c_orders(credentials)
            
            processed_count = 0
            success_count = 0
            errors = []
            
            for order_data in orders:
                try:
                    # Process order
                    order = await self._process_d2c_order(order_data, credentials)
                    
                    if order:
                        self.d2c_orders[order.order_id] = order
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
                "store_id": store_id,
                "processed_count": processed_count,
                "success_count": success_count,
                "error_count": len(errors),
                "errors": errors
            }
        
        except Exception as e:
            self.logger.error("Failed to sync D2C orders", error=str(e), store_id=store_id)
            raise
    
    async def _fetch_d2c_orders(self, credentials: D2CCredentials) -> List[Dict[str, Any]]:
        """Fetch orders from D2C platform API."""
        try:
            if credentials.platform_type == D2CPlatform.SHOPIFY:
                return await self._fetch_shopify_orders(credentials)
            elif credentials.platform_type == D2CPlatform.WOOCOMMERCE:
                return await self._fetch_woocommerce_orders(credentials)
            elif credentials.platform_type == D2CPlatform.PRESTASHOP:
                return await self._fetch_prestashop_orders(credentials)
            else:
                # Simulate generic D2C orders
                return await self._fetch_generic_d2c_orders(credentials)
        
        except Exception as e:
            self.logger.error("Failed to fetch D2C orders", error=str(e))
            return []
    
    async def _fetch_shopify_orders(self, credentials: D2CCredentials) -> List[Dict[str, Any]]:
        """Fetch orders from Shopify API."""
        # Simulate Shopify orders
        return [
            {
                "id": f"shopify_{uuid4().hex[:8]}",
                "order_number": "1001",
                "created_at": datetime.utcnow().isoformat(),
                "financial_status": "paid",
                "fulfillment_status": None,
                "total_price": "99.99",
                "subtotal_price": "89.99",
                "total_tax": "10.00",
                "currency": "USD",
                "customer": {
                    "id": "customer_123",
                    "email": "customer@shopify.com",
                    "first_name": "John",
                    "last_name": "Doe"
                },
                "billing_address": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "address1": "123 Main St",
                    "city": "New York",
                    "province": "NY",
                    "country": "US",
                    "zip": "10001"
                },
                "shipping_address": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "address1": "123 Main St",
                    "city": "New York",
                    "province": "NY",
                    "country": "US",
                    "zip": "10001"
                },
                "line_items": [
                    {
                        "id": "line_item_1",
                        "product_id": "product_123",
                        "variant_id": "variant_456",
                        "title": "Sample Product",
                        "quantity": 1,
                        "price": "89.99",
                        "sku": "SAMPLE-001"
                    }
                ],
                "shipping_lines": [
                    {
                        "title": "Standard Shipping",
                        "price": "0.00",
                        "code": "standard"
                    }
                ]
            }
        ]
    
    async def _fetch_woocommerce_orders(self, credentials: D2CCredentials) -> List[Dict[str, Any]]:
        """Fetch orders from WooCommerce API."""
        # Simulate WooCommerce orders
        return [
            {
                "id": f"wc_{uuid4().hex[:8]}",
                "number": "1002",
                "date_created": datetime.utcnow().isoformat(),
                "status": "processing",
                "total": "149.99",
                "total_tax": "15.00",
                "currency": "USD",
                "customer_id": "customer_456",
                "billing": {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane@woocommerce.com",
                    "address_1": "456 Oak Ave",
                    "city": "Los Angeles",
                    "state": "CA",
                    "postcode": "90210",
                    "country": "US"
                },
                "shipping": {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "address_1": "456 Oak Ave",
                    "city": "Los Angeles",
                    "state": "CA",
                    "postcode": "90210",
                    "country": "US"
                },
                "line_items": [
                    {
                        "id": "line_item_2",
                        "product_id": "product_456",
                        "name": "WooCommerce Product",
                        "quantity": 2,
                        "price": 67.50,
                        "total": "135.00",
                        "sku": "WC-PROD-001"
                    }
                ],
                "shipping_lines": [
                    {
                        "method_title": "Flat Rate",
                        "total": "14.99"
                    }
                ]
            }
        ]
    
    async def _fetch_prestashop_orders(self, credentials: D2CCredentials) -> List[Dict[str, Any]]:
        """Fetch orders from PrestaShop API."""
        # Simulate PrestaShop orders
        return [
            {
                "id": f"ps_{uuid4().hex[:8]}",
                "reference": "PRESTASHOP001",
                "date_add": datetime.utcnow().isoformat(),
                "current_state": "2",  # Payment accepted
                "total_paid": "79.99",
                "total_products": "69.99",
                "total_shipping": "10.00",
                "id_currency": "1",
                "id_customer": "customer_789",
                "customer_email": "customer@prestashop.com",
                "delivery_address": {
                    "firstname": "Pierre",
                    "lastname": "Dupont",
                    "address1": "123 Rue de la Paix",
                    "city": "Paris",
                    "postcode": "75001",
                    "country": "France"
                },
                "invoice_address": {
                    "firstname": "Pierre",
                    "lastname": "Dupont",
                    "address1": "123 Rue de la Paix",
                    "city": "Paris",
                    "postcode": "75001",
                    "country": "France"
                },
                "order_rows": [
                    {
                        "product_id": "product_789",
                        "product_name": "PrestaShop Product",
                        "product_quantity": "1",
                        "unit_price_tax_incl": "69.99",
                        "product_reference": "PS-PROD-001"
                    }
                ]
            }
        ]
    
    async def _fetch_generic_d2c_orders(self, credentials: D2CCredentials) -> List[Dict[str, Any]]:
        """Fetch orders from generic D2C platform."""
        # Simulate generic D2C orders
        return [
            {
                "id": f"generic_{uuid4().hex[:8]}",
                "order_number": "GEN-1003",
                "created_date": datetime.utcnow().isoformat(),
                "status": "confirmed",
                "total_amount": 199.99,
                "currency": "USD",
                "customer": {
                    "email": "customer@generic.com",
                    "name": "Alex Johnson"
                },
                "address": {
                    "street": "789 Generic Street",
                    "city": "Generic City",
                    "state": "GC",
                    "zip": "12345",
                    "country": "US"
                },
                "items": [
                    {
                        "product_id": "generic_product_1",
                        "name": "Generic Product",
                        "quantity": 1,
                        "price": 199.99,
                        "sku": "GEN-PROD-001"
                    }
                ]
            }
        ]
    
    async def _process_d2c_order(self, order_data: Dict[str, Any], credentials: D2CCredentials) -> Optional[D2COrder]:
        """Process and normalize D2C platform order data."""
        try:
            if credentials.platform_type == D2CPlatform.SHOPIFY:
                return self._process_shopify_order(order_data, credentials)
            elif credentials.platform_type == D2CPlatform.WOOCOMMERCE:
                return self._process_woocommerce_order(order_data, credentials)
            elif credentials.platform_type == D2CPlatform.PRESTASHOP:
                return self._process_prestashop_order(order_data, credentials)
            else:
                return self._process_generic_d2c_order(order_data, credentials)
        
        except Exception as e:
            self.logger.error("Failed to process D2C order", error=str(e))
            return None
    
    def _process_shopify_order(self, order_data: Dict[str, Any], credentials: D2CCredentials) -> D2COrder:
        """Process Shopify order data."""
        return D2COrder(
            order_id=str(uuid4()),
            store_id=credentials.store_id,
            platform_type=D2CPlatform.SHOPIFY,
            platform_order_id=order_data["id"],
            order_number=order_data.get("order_number"),
            customer_id=order_data.get("customer", {}).get("id"),
            customer_email=order_data.get("customer", {}).get("email", ""),
            customer_info=order_data.get("customer", {}),
            line_items=[
                {
                    "product_id": item.get("product_id"),
                    "variant_id": item.get("variant_id"),
                    "title": item.get("title"),
                    "quantity": item.get("quantity"),
                    "price": float(item.get("price", 0)),
                    "sku": item.get("sku")
                }
                for item in order_data.get("line_items", [])
            ],
            subtotal_price=float(order_data.get("subtotal_price", 0)),
            total_tax=float(order_data.get("total_tax", 0)),
            total_price=float(order_data.get("total_price", 0)),
            currency=order_data.get("currency", "USD"),
            financial_status=order_data.get("financial_status", "pending"),
            fulfillment_status=order_data.get("fulfillment_status") or "unfulfilled",
            billing_address=order_data.get("billing_address", {}),
            shipping_address=order_data.get("shipping_address", {}),
            shipping_lines=order_data.get("shipping_lines", []),
            order_date=datetime.fromisoformat(order_data["created_at"].replace("Z", "+00:00")),
            note=order_data.get("note"),
            last_sync=datetime.utcnow()
        )
    
    def _process_woocommerce_order(self, order_data: Dict[str, Any], credentials: D2CCredentials) -> D2COrder:
        """Process WooCommerce order data."""
        return D2COrder(
            order_id=str(uuid4()),
            store_id=credentials.store_id,
            platform_type=D2CPlatform.WOOCOMMERCE,
            platform_order_id=order_data["id"],
            order_number=order_data.get("number"),
            customer_id=order_data.get("customer_id"),
            customer_email=order_data.get("billing", {}).get("email", ""),
            customer_info={
                "first_name": order_data.get("billing", {}).get("first_name"),
                "last_name": order_data.get("billing", {}).get("last_name")
            },
            line_items=[
                {
                    "product_id": item.get("product_id"),
                    "name": item.get("name"),
                    "quantity": item.get("quantity"),
                    "price": float(item.get("price", 0)),
                    "total": float(item.get("total", 0)),
                    "sku": item.get("sku")
                }
                for item in order_data.get("line_items", [])
            ],
            subtotal_price=float(order_data.get("total", 0)) - float(order_data.get("total_tax", 0)),
            total_tax=float(order_data.get("total_tax", 0)),
            total_price=float(order_data.get("total", 0)),
            currency=order_data.get("currency", "USD"),
            financial_status="paid" if order_data.get("status") == "completed" else "pending",
            fulfillment_status="fulfilled" if order_data.get("status") == "completed" else "unfulfilled",
            billing_address=order_data.get("billing", {}),
            shipping_address=order_data.get("shipping", {}),
            shipping_lines=order_data.get("shipping_lines", []),
            order_date=datetime.fromisoformat(order_data["date_created"].replace("Z", "+00:00")),
            note=order_data.get("customer_note"),
            last_sync=datetime.utcnow()
        )
    
    def _process_prestashop_order(self, order_data: Dict[str, Any], credentials: D2CCredentials) -> D2COrder:
        """Process PrestaShop order data."""
        return D2COrder(
            order_id=str(uuid4()),
            store_id=credentials.store_id,
            platform_type=D2CPlatform.PRESTASHOP,
            platform_order_id=order_data["id"],
            order_number=order_data.get("reference"),
            customer_id=order_data.get("id_customer"),
            customer_email=order_data.get("customer_email", ""),
            customer_info={
                "first_name": order_data.get("delivery_address", {}).get("firstname"),
                "last_name": order_data.get("delivery_address", {}).get("lastname")
            },
            line_items=[
                {
                    "product_id": item.get("product_id"),
                    "name": item.get("product_name"),
                    "quantity": int(item.get("product_quantity", 0)),
                    "price": float(item.get("unit_price_tax_incl", 0)),
                    "sku": item.get("product_reference")
                }
                for item in order_data.get("order_rows", [])
            ],
            subtotal_price=float(order_data.get("total_products", 0)),
            total_tax=0.0,  # Tax included in PrestaShop prices
            total_price=float(order_data.get("total_paid", 0)),
            currency="EUR",  # Default for PrestaShop
            financial_status="paid" if order_data.get("current_state") == "2" else "pending",
            fulfillment_status="unfulfilled",
            billing_address=order_data.get("invoice_address", {}),
            shipping_address=order_data.get("delivery_address", {}),
            shipping_lines=[{"title": "Standard", "price": float(order_data.get("total_shipping", 0))}],
            order_date=datetime.fromisoformat(order_data["date_add"].replace("Z", "+00:00")),
            last_sync=datetime.utcnow()
        )
    
    def _process_generic_d2c_order(self, order_data: Dict[str, Any], credentials: D2CCredentials) -> D2COrder:
        """Process generic D2C platform order data."""
        return D2COrder(
            order_id=str(uuid4()),
            store_id=credentials.store_id,
            platform_type=credentials.platform_type,
            platform_order_id=order_data["id"],
            order_number=order_data.get("order_number"),
            customer_email=order_data.get("customer", {}).get("email", ""),
            customer_info=order_data.get("customer", {}),
            line_items=[
                {
                    "product_id": item.get("product_id"),
                    "name": item.get("name"),
                    "quantity": item.get("quantity"),
                    "price": float(item.get("price", 0)),
                    "sku": item.get("sku")
                }
                for item in order_data.get("items", [])
            ],
            subtotal_price=float(order_data.get("total_amount", 0)),
            total_price=float(order_data.get("total_amount", 0)),
            currency=order_data.get("currency", "USD"),
            financial_status="paid" if order_data.get("status") == "confirmed" else "pending",
            fulfillment_status="unfulfilled",
            billing_address=order_data.get("address", {}),
            shipping_address=order_data.get("address", {}),
            order_date=datetime.fromisoformat(order_data["created_date"].replace("Z", "+00:00")),
            last_sync=datetime.utcnow()
        )
    
    async def _sync_customers(self, store_id: str) -> Dict[str, Any]:
        """Synchronize customers from D2C platform."""
        try:
            credentials = self.store_credentials.get(store_id)
            if not credentials:
                raise ValueError(f"Store credentials not found for {store_id}")
            
            # Fetch customers from platform
            customers = await self._fetch_d2c_customers(credentials)
            
            processed_count = 0
            success_count = 0
            errors = []
            
            for customer_data in customers:
                try:
                    # Process customer
                    customer = await self._process_d2c_customer(customer_data, credentials)
                    
                    if customer:
                        self.d2c_customers[customer.customer_id] = customer
                        success_count += 1
                        
                        # Send customer to customer communication agent
                        await self.send_message(
                            recipient_agent="customer_communication_agent",
                            message_type=MessageType.CUSTOMER_UPDATED,
                            payload=customer.dict()
                        )
                    
                    processed_count += 1
                
                except Exception as e:
                    errors.append(f"Customer {customer_data.get('id', 'unknown')}: {str(e)}")
                    processed_count += 1
            
            return {
                "store_id": store_id,
                "processed_count": processed_count,
                "success_count": success_count,
                "error_count": len(errors),
                "errors": errors
            }
        
        except Exception as e:
            self.logger.error("Failed to sync D2C customers", error=str(e), store_id=store_id)
            raise
    
    async def _fetch_d2c_customers(self, credentials: D2CCredentials) -> List[Dict[str, Any]]:
        """Fetch customers from D2C platform API."""
        # Simulate customer data for different platforms
        return [
            {
                "id": f"{credentials.platform_type.value}_customer_{uuid4().hex[:8]}",
                "email": f"customer@{credentials.platform_type.value}.com",
                "first_name": "Sample",
                "last_name": "Customer",
                "created_at": datetime.utcnow().isoformat(),
                "orders_count": 2,
                "total_spent": "299.98"
            }
        ]
    
    async def _process_d2c_customer(self, customer_data: Dict[str, Any], credentials: D2CCredentials) -> Optional[D2CCustomer]:
        """Process and normalize D2C platform customer data."""
        try:
            return D2CCustomer(
                customer_id=str(uuid4()),
                store_id=credentials.store_id,
                platform_type=credentials.platform_type,
                platform_customer_id=customer_data["id"],
                first_name=customer_data.get("first_name", ""),
                last_name=customer_data.get("last_name", ""),
                email=customer_data.get("email", ""),
                phone=customer_data.get("phone"),
                accepts_marketing=customer_data.get("accepts_marketing", False),
                verified_email=customer_data.get("verified_email", False),
                state=customer_data.get("state", "enabled"),
                addresses=customer_data.get("addresses", []),
                default_address=customer_data.get("default_address"),
                orders_count=int(customer_data.get("orders_count", 0)),
                total_spent=float(customer_data.get("total_spent", 0)),
                tags=customer_data.get("tags", []),
                note=customer_data.get("note"),
                created_at=datetime.fromisoformat(customer_data["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.utcnow(),
                last_sync=datetime.utcnow()
            )
        
        except Exception as e:
            self.logger.error("Failed to process D2C customer", error=str(e))
            return None
    
    async def _process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process webhook from D2C platform."""
        try:
            # Create webhook event
            event = WebhookEvent(
                event_id=str(uuid4()),
                store_id=webhook_data["store_id"],
                platform_type=D2CPlatform(webhook_data.get("platform_type", "shopify")),
                event_type=webhook_data.get("event_type", "unknown"),
                topic=webhook_data.get("topic", "unknown"),
                payload=webhook_data.get("payload", {}),
                api_version=webhook_data.get("api_version"),
                webhook_id=webhook_data.get("webhook_id"),
                received_at=datetime.utcnow()
            )
            
            # Store webhook event
            self.webhook_events[event.event_id] = event
            
            # Process webhook based on topic
            result = await self._handle_webhook_event(event)
            
            if result["success"]:
                event.processed = True
                event.processed_at = datetime.utcnow()
            else:
                event.error_message = result.get("error")
            
            return result
        
        except Exception as e:
            self.logger.error("Failed to process webhook", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _handle_webhook_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle specific webhook event based on topic."""
        try:
            topic = event.topic.lower()
            
            if "order" in topic:
                return await self._handle_order_webhook(event)
            elif "product" in topic:
                return await self._handle_product_webhook(event)
            elif "customer" in topic:
                return await self._handle_customer_webhook(event)
            else:
                self.logger.info("Unhandled webhook topic", topic=topic)
                return {"success": True, "message": f"Webhook topic {topic} acknowledged"}
        
        except Exception as e:
            self.logger.error("Failed to handle webhook event", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _handle_order_webhook(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle order-related webhook events."""
        try:
            order_data = event.payload
            
            if "create" in event.topic or "new" in event.topic:
                # New order created
                credentials = self.store_credentials.get(event.store_id)
                if credentials:
                    order = await self._process_d2c_order(order_data, credentials)
                    if order:
                        self.d2c_orders[order.order_id] = order
                        
                        # Send to order agent
                        await self.send_message(
                            recipient_agent="order_agent",
                            message_type=MessageType.ORDER_CREATED,
                            payload=order.dict()
                        )
            
            elif "update" in event.topic or "paid" in event.topic:
                # Order updated or paid
                platform_order_id = order_data.get("id")
                if platform_order_id:
                    # Find existing order and update
                    for order in self.d2c_orders.values():
                        if order.platform_order_id == platform_order_id:
                            # Update order status
                            if "paid" in event.topic:
                                order.financial_status = "paid"
                            
                            order.last_sync = datetime.utcnow()
                            
                            # Send update notification
                            await self.send_message(
                                recipient_agent="order_agent",
                                message_type=MessageType.ORDER_STATUS_UPDATED,
                                payload={
                                    "order_id": order.order_id,
                                    "platform_order_id": platform_order_id,
                                    "financial_status": order.financial_status,
                                    "fulfillment_status": order.fulfillment_status
                                }
                            )
                            break
            
            return {"success": True, "message": "Order webhook processed"}
        
        except Exception as e:
            self.logger.error("Failed to handle order webhook", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _handle_product_webhook(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle product-related webhook events."""
        try:
            product_data = event.payload
            
            if "create" in event.topic or "new" in event.topic:
                # New product created externally
                self.logger.info("External product creation detected", 
                               platform_product_id=product_data.get("id"))
            
            elif "update" in event.topic:
                # Product updated externally
                platform_product_id = product_data.get("id")
                if platform_product_id:
                    # Find existing product and sync updates
                    for product in self.d2c_products.values():
                        if product.platform_product_id == platform_product_id:
                            # Update product fields from webhook data
                            if "title" in product_data:
                                product.title = product_data["title"]
                            if "price" in product_data:
                                product.price = float(product_data["price"])
                            
                            product.updated_at = datetime.utcnow()
                            product.last_sync = datetime.utcnow()
                            
                            # Send update notification
                            await self.send_message(
                                recipient_agent="product_agent",
                                message_type=MessageType.LISTING_UPDATED,
                                payload={
                                    "product_id": product.product_id,
                                    "platform_product_id": platform_product_id,
                                    "updates": product_data
                                }
                            )
                            break
            
            return {"success": True, "message": "Product webhook processed"}
        
        except Exception as e:
            self.logger.error("Failed to handle product webhook", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _handle_customer_webhook(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle customer-related webhook events."""
        try:
            customer_data = event.payload
            
            if "create" in event.topic or "new" in event.topic:
                # New customer registered
                credentials = self.store_credentials.get(event.store_id)
                if credentials:
                    customer = await self._process_d2c_customer(customer_data, credentials)
                    if customer:
                        self.d2c_customers[customer.customer_id] = customer
                        
                        # Send to customer communication agent
                        await self.send_message(
                            recipient_agent="customer_communication_agent",
                            message_type=MessageType.CUSTOMER_CREATED,
                            payload=customer.dict()
                        )
            
            elif "update" in event.topic:
                # Customer updated
                platform_customer_id = customer_data.get("id")
                if platform_customer_id:
                    # Find existing customer and update
                    for customer in self.d2c_customers.values():
                        if customer.platform_customer_id == platform_customer_id:
                            # Update customer fields
                            if "email" in customer_data:
                                customer.email = customer_data["email"]
                            if "first_name" in customer_data:
                                customer.first_name = customer_data["first_name"]
                            if "last_name" in customer_data:
                                customer.last_name = customer_data["last_name"]
                            
                            customer.updated_at = datetime.utcnow()
                            customer.last_sync = datetime.utcnow()
                            
                            # Send update notification
                            await self.send_message(
                                recipient_agent="customer_communication_agent",
                                message_type=MessageType.CUSTOMER_UPDATED,
                                payload=customer.dict()
                            )
                            break
            
            return {"success": True, "message": "Customer webhook processed"}
        
        except Exception as e:
            self.logger.error("Failed to handle customer webhook", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _update_d2c_inventory(self, product_id: str, quantity: int) -> Dict[str, Any]:
        """Update product inventory on D2C platform."""
        try:
            product = self.d2c_products.get(product_id)
            if not product:
                raise ValueError(f"Product {product_id} not found")
            
            # Update inventory quantity
            product.inventory_quantity = quantity
            product.updated_at = datetime.utcnow()
            
            # Update on platform
            credentials = self.store_credentials.get(product.store_id)
            if credentials:
                platform_result = await self._update_platform_inventory(product, credentials, quantity)
                
                if platform_result["success"]:
                    product.last_sync = datetime.utcnow()
                    return product.dict()
                else:
                    raise Exception(f"Failed to update platform inventory: {platform_result.get('error')}")
            else:
                raise ValueError(f"Store credentials not found for {product.store_id}")
        
        except Exception as e:
            self.logger.error("Failed to update D2C inventory", error=str(e), product_id=product_id)
            raise
    
    async def _update_platform_inventory(self, product: D2CProduct, credentials: D2CCredentials, quantity: int) -> Dict[str, Any]:
        """Update inventory on D2C platform."""
        try:
            # Platform-specific inventory update
            self.logger.info("Platform inventory updated", 
                           platform=credentials.platform_type.value,
                           product_id=product.platform_product_id,
                           quantity=quantity)
            
            return {"success": True, "message": "Platform inventory updated"}
        
        except Exception as e:
            self.logger.error("Failed to update platform inventory", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _fulfill_d2c_order(self, order_id: str, fulfillment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fulfill order on D2C platform."""
        try:
            order = self.d2c_orders.get(order_id)
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            # Update fulfillment status
            order.fulfillment_status = "fulfilled"
            
            # Add tracking information if provided
            tracking_number = fulfillment_data.get("tracking_number")
            if tracking_number:
                order.shipping_lines.append({
                    "tracking_number": tracking_number,
                    "carrier": fulfillment_data.get("carrier", "Unknown")
                })
            
            # Update on platform
            credentials = self.store_credentials.get(order.store_id)
            if credentials:
                platform_result = await self._fulfill_platform_order(order, credentials, fulfillment_data)
                
                if platform_result["success"]:
                    order.last_sync = datetime.utcnow()
                    
                    # Send fulfillment notification
                    await self.send_message(
                        recipient_agent="order_agent",
                        message_type=MessageType.ORDER_FULFILLED,
                        payload={
                            "order_id": order_id,
                            "platform_order_id": order.platform_order_id,
                            "tracking_number": tracking_number,
                            "fulfillment_status": order.fulfillment_status
                        }
                    )
                    
                    return order.dict()
                else:
                    raise Exception(f"Failed to fulfill platform order: {platform_result.get('error')}")
            else:
                raise ValueError(f"Store credentials not found for {order.store_id}")
        
        except Exception as e:
            self.logger.error("Failed to fulfill D2C order", error=str(e), order_id=order_id)
            raise
    
    async def _fulfill_platform_order(self, order: D2COrder, credentials: D2CCredentials, fulfillment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fulfill order on D2C platform."""
        try:
            # Platform-specific order fulfillment
            self.logger.info("Platform order fulfilled", 
                           platform=credentials.platform_type.value,
                           order_id=order.platform_order_id,
                           tracking_number=fulfillment_data.get("tracking_number"))
            
            return {"success": True, "message": "Platform order fulfilled"}
        
        except Exception as e:
            self.logger.error("Failed to fulfill platform order", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _get_store_analytics(self, store_id: str) -> Dict[str, Any]:
        """Get store analytics and metrics."""
        try:
            store = self.stores.get(store_id)
            if not store:
                raise ValueError(f"Store {store_id} not found")
            
            # Calculate analytics
            store_orders = [o for o in self.d2c_orders.values() if o.store_id == store_id]
            store_products = [p for p in self.d2c_products.values() if p.store_id == store_id]
            store_customers = [c for c in self.d2c_customers.values() if c.store_id == store_id]
            
            # Revenue analytics
            total_revenue = sum(order.total_price for order in store_orders)
            avg_order_value = total_revenue / len(store_orders) if store_orders else 0
            
            # Product analytics
            published_products = len([p for p in store_products if p.published])
            total_inventory_value = sum(p.price * p.inventory_quantity for p in store_products)
            
            # Customer analytics
            total_customers = len(store_customers)
            repeat_customers = len([c for c in store_customers if c.orders_count > 1])
            
            # Recent activity (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_orders = [o for o in store_orders if o.order_date >= thirty_days_ago]
            recent_revenue = sum(order.total_price for order in recent_orders)
            
            return {
                "store_id": store_id,
                "store_name": store.store_name,
                "platform_type": store.platform_type.value,
                "analytics": {
                    "overview": {
                        "total_products": len(store_products),
                        "published_products": published_products,
                        "total_orders": len(store_orders),
                        "total_customers": total_customers,
                        "total_revenue": round(total_revenue, 2)
                    },
                    "financial": {
                        "total_revenue": round(total_revenue, 2),
                        "average_order_value": round(avg_order_value, 2),
                        "total_inventory_value": round(total_inventory_value, 2),
                        "recent_revenue_30d": round(recent_revenue, 2)
                    },
                    "products": {
                        "total_products": len(store_products),
                        "published_products": published_products,
                        "draft_products": len(store_products) - published_products,
                        "total_inventory_items": sum(p.inventory_quantity for p in store_products),
                        "low_stock_products": len([p for p in store_products if p.inventory_quantity < 10])
                    },
                    "customers": {
                        "total_customers": total_customers,
                        "repeat_customers": repeat_customers,
                        "repeat_customer_rate": round((repeat_customers / total_customers * 100) if total_customers > 0 else 0, 2),
                        "average_customer_value": round(sum(c.total_spent for c in store_customers) / total_customers if total_customers > 0 else 0, 2)
                    },
                    "recent_activity": {
                        "orders_last_30d": len(recent_orders),
                        "revenue_last_30d": round(recent_revenue, 2),
                        "new_customers_last_30d": len([c for c in store_customers if c.created_at >= thirty_days_ago])
                    }
                },
                "generated_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error("Failed to get store analytics", error=str(e), store_id=store_id)
            raise
    
    async def _load_store_credentials(self):
        """Load D2C store credentials from configuration."""
        try:
            # In production, this would load from secure configuration
            sample_credentials = [
                D2CCredentials(
                    platform_type=D2CPlatform.SHOPIFY,
                    store_id="shopify_store_1",
                    store_name="Sample Shopify Store",
                    store_url="https://sample-store.myshopify.com",
                    api_key="sample_shopify_key",
                    access_token="sample_access_token",
                    shop_domain="sample-store",
                    webhook_secret="sample_webhook_secret"
                ),
                D2CCredentials(
                    platform_type=D2CPlatform.WOOCOMMERCE,
                    store_id="woocommerce_store_1",
                    store_name="Sample WooCommerce Store",
                    store_url="https://sample-woocommerce.com",
                    api_key="sample_wc_key",
                    consumer_key="ck_sample_consumer_key",
                    consumer_secret="cs_sample_consumer_secret"
                ),
                D2CCredentials(
                    platform_type=D2CPlatform.PRESTASHOP,
                    store_id="prestashop_store_1",
                    store_name="Sample PrestaShop Store",
                    store_url="https://sample-prestashop.com",
                    api_key="sample_ps_key",
                    webservice_key="sample_webservice_key"
                )
            ]
            
            for cred in sample_credentials:
                self.store_credentials[cred.store_id] = cred
            
            self.logger.info("D2C store credentials loaded", count=len(sample_credentials))
        
        except Exception as e:
            self.logger.error("Failed to load store credentials", error=str(e))
    
    async def _handle_product_updated(self, message: AgentMessage):
        """Handle product update messages."""
        payload = message.payload
        product_id = payload.get("product_id")
        
        if product_id:
            try:
                # Find D2C products for this product
                d2c_products = [p for p in self.d2c_products.values() if p.product_id == product_id]
                
                # Update each D2C product
                for product in d2c_products:
                    updates = {}
                    
                    if "title" in payload:
                        updates["title"] = payload["title"]
                    if "description" in payload:
                        updates["description"] = payload["description"]
                    if "images" in payload:
                        updates["images"] = payload["images"]
                    
                    if updates:
                        await self._update_d2c_product(product.product_id, updates)
            
            except Exception as e:
                self.logger.error("Failed to handle product update", error=str(e), product_id=product_id)
    
    async def _handle_inventory_updated(self, message: AgentMessage):
        """Handle inventory update messages."""
        payload = message.payload
        product_id = payload.get("product_id")
        new_quantity = payload.get("available_quantity")
        
        if product_id and new_quantity is not None:
            try:
                # Find D2C products for this product
                d2c_products = [p for p in self.d2c_products.values() if p.product_id == product_id]
                
                # Update inventory for each D2C product
                for product in d2c_products:
                    await self._update_d2c_inventory(product.product_id, new_quantity)
            
            except Exception as e:
                self.logger.error("Failed to handle inventory update", error=str(e), product_id=product_id)
    
    async def _handle_order_status_updated(self, message: AgentMessage):
        """Handle order status update messages."""
        payload = message.payload
        order_id = payload.get("order_id")
        new_status = payload.get("status")
        
        if order_id and new_status:
            try:
                # Find D2C order
                d2c_order = self.d2c_orders.get(order_id)
                
                if d2c_order:
                    # Update order status
                    if new_status in ["shipped", "delivered"]:
                        d2c_order.fulfillment_status = "fulfilled"
                    elif new_status == "cancelled":
                        d2c_order.fulfillment_status = "cancelled"
                    
                    d2c_order.last_sync = datetime.utcnow()
            
            except Exception as e:
                self.logger.error("Failed to handle order status update", error=str(e), order_id=order_id)
    
    async def _handle_price_updated(self, message: AgentMessage):
        """Handle price update messages."""
        payload = message.payload
        product_id = payload.get("product_id")
        new_price = payload.get("price")
        
        if product_id and new_price is not None:
            try:
                # Find D2C products for this product
                d2c_products = [p for p in self.d2c_products.values() if p.product_id == product_id]
                
                # Update price for each D2C product
                for product in d2c_products:
                    await self._update_d2c_product(product.product_id, {"price": new_price})
            
            except Exception as e:
                self.logger.error("Failed to handle price update", error=str(e), product_id=product_id)
    
    async def _sync_d2c_orders(self):
        """Background task to sync D2C orders."""
        while not self.shutdown_event.is_set():
            try:
                # Sync orders every 5 minutes
                await asyncio.sleep(300)
                
                if not self.shutdown_event.is_set():
                    for store_id in self.store_credentials.keys():
                        try:
                            await self._sync_orders(store_id)
                        except Exception as e:
                            self.logger.error("Failed to sync D2C orders for store", 
                                            error=str(e), 
                                            store_id=store_id)
            
            except Exception as e:
                self.logger.error("Error in D2C order sync", error=str(e))
                await asyncio.sleep(300)
    
    async def _sync_d2c_products(self):
        """Background task to sync D2C products."""
        while not self.shutdown_event.is_set():
            try:
                # Sync products every 15 minutes
                await asyncio.sleep(900)
                
                if not self.shutdown_event.is_set():
                    # Update product information from platforms
                    for product in self.d2c_products.values():
                        try:
                            # In production, this would fetch latest product data from platform
                            pass
                        except Exception as e:
                            self.logger.error("Failed to sync D2C product", 
                                            error=str(e), 
                                            product_id=product.product_id)
            
            except Exception as e:
                self.logger.error("Error in D2C product sync", error=str(e))
                await asyncio.sleep(900)
    
    async def _sync_d2c_customers(self):
        """Background task to sync D2C customers."""
        while not self.shutdown_event.is_set():
            try:
                # Sync customers every 30 minutes
                await asyncio.sleep(1800)
                
                if not self.shutdown_event.is_set():
                    for store_id in self.store_credentials.keys():
                        try:
                            await self._sync_customers(store_id)
                        except Exception as e:
                            self.logger.error("Failed to sync D2C customers for store", 
                                            error=str(e), 
                                            store_id=store_id)
            
            except Exception as e:
                self.logger.error("Error in D2C customer sync", error=str(e))
                await asyncio.sleep(1800)
    
    async def _process_webhook_events(self):
        """Background task to process webhook events."""
        while not self.shutdown_event.is_set():
            try:
                # Process webhooks every minute
                await asyncio.sleep(60)
                
                if not self.shutdown_event.is_set():
                    # Process unprocessed webhook events
                    unprocessed_events = [e for e in self.webhook_events.values() if not e.processed]
                    
                    for event in unprocessed_events:
                        try:
                            result = await self._handle_webhook_event(event)
                            
                            if result["success"]:
                                event.processed = True
                                event.processed_at = datetime.utcnow()
                            else:
                                event.error_message = result.get("error")
                        
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
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if d2c_ecommerce_agent:
        health_status = d2c_ecommerce_agent.get_health_status()
        return {"status": "healthy", "agent_status": health_status.dict()}
    return {"status": "unhealthy", "message": "Agent not initialized"}


# Mount agent's FastAPI app
app.mount("/api/v1", d2c_ecommerce_agent.app if d2c_ecommerce_agent else FastAPI())


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
        "d2c_ecommerce_agent:app",
        host="0.0.0.0",
        port=8013,
        reload=False,
        log_level="info"
    )
