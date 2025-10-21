"""
Standard Marketplace Agent - Multi-Agent E-commerce System

This agent manages connections to standard marketplaces including:
- Amazon Marketplace (Seller Central API)
- eBay Marketplace (Trading API)
- Mirakl-powered marketplaces
- Other major e-commerce marketplaces
- Order synchronization and inventory management
- Product listing and pricing updates
"""

import asyncio
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4
from enum import Enum

from shared.db_helpers import DatabaseHelper
import base64
import hmac
import hashlib
import urllib.parse

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


class MarketplaceType(str, Enum):
    """Types of marketplaces."""
    AMAZON = "amazon"
    EBAY = "ebay"
    MIRAKL = "mirakl"
    ALLEGRO = "allegro"
    CDISCOUNT = "cdiscount"
    FNAC = "fnac"
    RAKUTEN = "rakuten"


class ListingStatus(str, Enum):
    """Product listing status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    REJECTED = "rejected"
    OUT_OF_STOCK = "out_of_stock"
    SUSPENDED = "suspended"


class OrderStatus(str, Enum):
    """Marketplace order status."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class MarketplaceCredentials(BaseModel):
    """Model for marketplace API credentials."""
    marketplace_type: MarketplaceType
    marketplace_id: str
    api_key: str
    secret_key: str
    seller_id: str
    additional_params: Dict[str, str] = {}
    active: bool = True
    last_sync: Optional[datetime] = None


class ProductListing(BaseModel):
    """Model for marketplace product listings."""
    listing_id: str
    marketplace_type: MarketplaceType
    marketplace_id: str
    product_id: str
    marketplace_product_id: Optional[str] = None
    title: str
    description: str
    price: float
    currency: str = "EUR"
    quantity: int
    sku: str
    category: str
    images: List[str]
    attributes: Dict[str, Any] = {}
    status: ListingStatus = ListingStatus.PENDING
    created_at: datetime
    updated_at: datetime
    last_sync: Optional[datetime] = None


class MarketplaceOrder(BaseModel):
    """Model for marketplace orders."""
    order_id: str
    marketplace_type: MarketplaceType
    marketplace_id: str
    marketplace_order_id: str
    customer_info: Dict[str, Any]
    items: List[Dict[str, Any]]
    total_amount: float
    currency: str = "EUR"
    status: OrderStatus
    order_date: datetime
    shipping_address: Dict[str, str]
    billing_address: Dict[str, str]
    payment_method: str
    shipping_method: str
    tracking_number: Optional[str] = None
    notes: Optional[str] = None
    last_sync: Optional[datetime] = None


class SyncResult(BaseModel):
    """Model for synchronization results."""
    sync_id: str
    marketplace_type: MarketplaceType
    marketplace_id: str
    sync_type: str  # "orders", "inventory", "listings", "prices"
    started_at: datetime
    completed_at: Optional[datetime] = None
    success: bool = False
    items_processed: int = 0
    items_success: int = 0
    items_failed: int = 0
    errors: List[str] = []
    summary: Dict[str, Any] = {}


class StandardMarketplaceAgent(BaseAgent):
    """
    Standard Marketplace Agent manages connections to major marketplaces including:
    - Amazon Seller Central API integration
    - eBay Trading API integration
    - Mirakl marketplace platform integration
    - Order synchronization and fulfillment
    - Inventory and pricing updates
    - Product listing management
    """
    
    def __init__(self, **kwargs):
        super().__init__(agent_id="standard_marketplace_agent", **kwargs)
        self.app = FastAPI(title="Standard Marketplace Agent API", version="1.0.0")
        self.setup_routes()
        
        # Marketplace data
        self.marketplace_credentials: Dict[str, MarketplaceCredentials] = {}
        self.product_listings: Dict[str, ProductListing] = {}
        self.marketplace_orders: Dict[str, MarketplaceOrder] = {}
        self.sync_results: Dict[str, SyncResult] = {}
        
        # HTTP session for API calls
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Register message handlers
        self.register_handler(MessageType.PRODUCT_UPDATED, self._handle_product_updated)
        self.register_handler(MessageType.INVENTORY_UPDATED, self._handle_inventory_updated)
        self.register_handler(MessageType.PRICE_UPDATED, self._handle_price_updated)
        self.register_handler(MessageType.ORDER_FULFILLMENT_REQUIRED, self._handle_order_fulfillment)
    
    async def initialize(self):
        """Initialize the Standard Marketplace Agent."""
        self.logger.info("Initializing Standard Marketplace Agent")
        
        # Initialize HTTP session
        self.session = aiohttp.ClientSession()
        
        # Load marketplace credentials
        await self._load_marketplace_credentials()
        
        # Start background synchronization tasks
        asyncio.create_task(self._sync_orders_periodically())
        asyncio.create_task(self._sync_inventory_periodically())
        asyncio.create_task(self._monitor_listing_performance())
        asyncio.create_task(self._handle_marketplace_notifications())
        
        self.logger.info("Standard Marketplace Agent initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up Standard Marketplace Agent")
        
        if self.session:
            await self.session.close()
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process marketplace business logic."""
        action = data.get("action")
        
        if action == "sync_orders":
            return await self._sync_orders(data["marketplace_id"])
        elif action == "sync_inventory":
            return await self._sync_inventory(data["marketplace_id"])
        elif action == "create_listing":
            return await self._create_product_listing(data["listing_data"])
        elif action == "update_listing":
            return await self._update_product_listing(data["listing_id"], data["updates"])
        elif action == "update_price":
            return await self._update_listing_price(data["listing_id"], data["new_price"])
        elif action == "fulfill_order":
            return await self._fulfill_marketplace_order(data["order_id"], data["fulfillment_data"])
        elif action == "get_performance_metrics":
            return await self._get_marketplace_performance(data.get("marketplace_id"))
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def setup_routes(self):
        """Setup FastAPI routes for the Standard Marketplace Agent."""
        
        @self.app.post("/credentials", response_model=APIResponse)
        async def add_marketplace_credentials(credentials: MarketplaceCredentials):
            """Add marketplace API credentials."""
            try:
                # Validate credentials
                validation_result = await self._validate_credentials(credentials)
                
                if validation_result["valid"]:
                    self.marketplace_credentials[credentials.marketplace_id] = credentials
                    
                    return APIResponse(
                        success=True,
                        message="Marketplace credentials added successfully",
                        data={"marketplace_id": credentials.marketplace_id, "validation": validation_result}
                    )
                else:
                    raise HTTPException(status_code=400, detail=f"Invalid credentials: {validation_result['error']}")
            
            except Exception as e:
                self.logger.error("Failed to add marketplace credentials", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/listings", response_model=APIResponse)
        async def create_product_listing(listing_data: ProductListing):
            """Create a new product listing on marketplace."""
            try:
                result = await self._create_product_listing(listing_data.dict())
                
                return APIResponse(
                    success=True,
                    message="Product listing created successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to create product listing", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.put("/listings/{listing_id}", response_model=APIResponse)
        async def update_product_listing(listing_id: str, updates: Dict[str, Any]):
            """Update an existing product listing."""
            try:
                result = await self._update_product_listing(listing_id, updates)
                
                return APIResponse(
                    success=True,
                    message="Product listing updated successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to update product listing", error=str(e), listing_id=listing_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/sync/orders/{marketplace_id}", response_model=APIResponse)
        async def sync_orders(marketplace_id: str):
            """Synchronize orders from marketplace."""
            try:
                result = await self._sync_orders(marketplace_id)
                
                return APIResponse(
                    success=True,
                    message="Orders synchronized successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to sync orders", error=str(e), marketplace_id=marketplace_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/sync/inventory/{marketplace_id}", response_model=APIResponse)
        async def sync_inventory(marketplace_id: str):
            """Synchronize inventory to marketplace."""
            try:
                result = await self._sync_inventory(marketplace_id)
                
                return APIResponse(
                    success=True,
                    message="Inventory synchronized successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to sync inventory", error=str(e), marketplace_id=marketplace_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/orders/{order_id}/fulfill", response_model=APIResponse)
        async def fulfill_order(order_id: str, fulfillment_data: Dict[str, Any]):
            """Fulfill a marketplace order."""
            try:
                result = await self._fulfill_marketplace_order(order_id, fulfillment_data)
                
                return APIResponse(
                    success=True,
                    message="Order fulfilled successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to fulfill order", error=str(e), order_id=order_id)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/performance", response_model=APIResponse)
        async def get_performance_metrics(marketplace_id: Optional[str] = None):
            """Get marketplace performance metrics."""
            try:
                result = await self._get_marketplace_performance(marketplace_id)
                
                return APIResponse(
                    success=True,
                    message="Performance metrics retrieved successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to get performance metrics", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/listings", response_model=APIResponse)
        async def list_product_listings(marketplace_id: Optional[str] = None, status: Optional[ListingStatus] = None):
            """List product listings with optional filters."""
            try:
                listings = list(self.product_listings.values())
                
                if marketplace_id:
                    listings = [l for l in listings if l.marketplace_id == marketplace_id]
                
                if status:
                    listings = [l for l in listings if l.status == status]
                
                return APIResponse(
                    success=True,
                    message="Product listings retrieved successfully",
                    data={"listings": [l.dict() for l in listings]}
                )
            
            except Exception as e:
                self.logger.error("Failed to list product listings", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/orders", response_model=APIResponse)
        async def list_marketplace_orders(marketplace_id: Optional[str] = None, status: Optional[OrderStatus] = None):
            """List marketplace orders with optional filters."""
            try:
                orders = list(self.marketplace_orders.values())
                
                if marketplace_id:
                    orders = [o for o in orders if o.marketplace_id == marketplace_id]
                
                if status:
                    orders = [o for o in orders if o.status == status]
                
                return APIResponse(
                    success=True,
                    message="Marketplace orders retrieved successfully",
                    data={"orders": [o.dict() for o in orders]}
                )
            
            except Exception as e:
                self.logger.error("Failed to list marketplace orders", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _validate_credentials(self, credentials: MarketplaceCredentials) -> Dict[str, Any]:
        """Validate marketplace API credentials."""
        try:
            if credentials.marketplace_type == MarketplaceType.AMAZON:
                return await self._validate_amazon_credentials(credentials)
            elif credentials.marketplace_type == MarketplaceType.EBAY:
                return await self._validate_ebay_credentials(credentials)
            elif credentials.marketplace_type == MarketplaceType.MIRAKL:
                return await self._validate_mirakl_credentials(credentials)
            else:
                # For other marketplaces, perform basic validation
                return {"valid": True, "message": "Credentials format validated"}
        
        except Exception as e:
            self.logger.error("Failed to validate credentials", error=str(e))
            return {"valid": False, "error": str(e)}
    
    async def _validate_amazon_credentials(self, credentials: MarketplaceCredentials) -> Dict[str, Any]:
        """Validate Amazon Seller Central API credentials."""
        try:
            # Amazon SP-API validation
            # In production, this would make a test API call to validate credentials
            
            required_params = ["marketplace_id", "refresh_token", "client_id", "client_secret"]
            missing_params = [p for p in required_params if p not in credentials.additional_params]
            
            if missing_params:
                return {"valid": False, "error": f"Missing required parameters: {missing_params}"}
            
            # Simulate API validation call
            # In production: Make actual call to Amazon SP-API
            
            return {"valid": True, "message": "Amazon credentials validated successfully"}
        
        except Exception as e:
            return {"valid": False, "error": f"Amazon validation failed: {str(e)}"}
    
    async def _validate_ebay_credentials(self, credentials: MarketplaceCredentials) -> Dict[str, Any]:
        """Validate eBay Trading API credentials."""
        try:
            # eBay API validation
            required_params = ["app_id", "dev_id", "cert_id", "user_token"]
            missing_params = [p for p in required_params if p not in credentials.additional_params]
            
            if missing_params:
                return {"valid": False, "error": f"Missing required parameters: {missing_params}"}
            
            # Simulate API validation call
            # In production: Make actual call to eBay Trading API
            
            return {"valid": True, "message": "eBay credentials validated successfully"}
        
        except Exception as e:
            return {"valid": False, "error": f"eBay validation failed: {str(e)}"}
    
    async def _validate_mirakl_credentials(self, credentials: MarketplaceCredentials) -> Dict[str, Any]:
        """Validate Mirakl API credentials."""
        try:
            # Mirakl API validation
            if not credentials.api_key:
                return {"valid": False, "error": "API key is required for Mirakl"}
            
            # Simulate API validation call
            # In production: Make actual call to Mirakl API
            
            return {"valid": True, "message": "Mirakl credentials validated successfully"}
        
        except Exception as e:
            return {"valid": False, "error": f"Mirakl validation failed: {str(e)}"}
    
    async def _create_product_listing(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product listing on marketplace."""
        try:
            listing = ProductListing(
                listing_id=listing_data.get("listing_id", str(uuid4())),
                marketplace_type=MarketplaceType(listing_data["marketplace_type"]),
                marketplace_id=listing_data["marketplace_id"],
                product_id=listing_data["product_id"],
                title=listing_data["title"],
                description=listing_data["description"],
                price=listing_data["price"],
                currency=listing_data.get("currency", "EUR"),
                quantity=listing_data["quantity"],
                sku=listing_data["sku"],
                category=listing_data["category"],
                images=listing_data.get("images", []),
                attributes=listing_data.get("attributes", {}),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Create listing on marketplace
            marketplace_result = await self._create_marketplace_listing(listing)
            
            if marketplace_result["success"]:
                listing.marketplace_product_id = marketplace_result.get("marketplace_product_id")
                listing.status = ListingStatus.ACTIVE
                listing.last_sync = datetime.utcnow()
                
                # Store listing
                self.product_listings[listing.listing_id] = listing
                
                # Send notification
                await self.send_message(
                    recipient_agent="product_agent",
                    message_type=MessageType.LISTING_CREATED,
                    payload={
                        "listing_id": listing.listing_id,
                        "product_id": listing.product_id,
                        "marketplace_type": listing.marketplace_type.value,
                        "marketplace_id": listing.marketplace_id,
                        "status": listing.status.value
                    }
                )
                
                return listing.dict()
            else:
                listing.status = ListingStatus.REJECTED
                self.product_listings[listing.listing_id] = listing
                raise Exception(f"Failed to create marketplace listing: {marketplace_result.get('error')}")
        
        except Exception as e:
            self.logger.error("Failed to create product listing", error=str(e))
            raise
    
    async def _create_marketplace_listing(self, listing: ProductListing) -> Dict[str, Any]:
        """Create listing on specific marketplace."""
        try:
            credentials = self.marketplace_credentials.get(listing.marketplace_id)
            if not credentials:
                return {"success": False, "error": "Marketplace credentials not found"}
            
            if listing.marketplace_type == MarketplaceType.AMAZON:
                return await self._create_amazon_listing(listing, credentials)
            elif listing.marketplace_type == MarketplaceType.EBAY:
                return await self._create_ebay_listing(listing, credentials)
            elif listing.marketplace_type == MarketplaceType.MIRAKL:
                return await self._create_mirakl_listing(listing, credentials)
            else:
                # Generic marketplace listing creation
                return await self._create_generic_listing(listing, credentials)
        
        except Exception as e:
            self.logger.error("Failed to create marketplace listing", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _create_amazon_listing(self, listing: ProductListing, credentials: MarketplaceCredentials) -> Dict[str, Any]:
        """Create listing on Amazon Marketplace."""
        try:
            # Amazon SP-API Listings API
            # In production, this would use the actual Amazon SP-API
            
            # Prepare listing data for Amazon
            amazon_listing = {
                "sku": listing.sku,
                "product_type": "PRODUCT",
                "requirements": "LISTING",
                "attributes": {
                    "item_name": [{"value": listing.title, "language_tag": "en_US"}],
                    "description": [{"value": listing.description, "language_tag": "en_US"}],
                    "bullet_point": [{"value": listing.description[:500], "language_tag": "en_US"}],
                    "brand": [{"value": listing.attributes.get("brand", "Generic"), "language_tag": "en_US"}],
                    "manufacturer": [{"value": listing.attributes.get("manufacturer", "Generic"), "language_tag": "en_US"}],
                    "item_type_name": [{"value": listing.category, "language_tag": "en_US"}],
                    "list_price": [{"value": listing.price, "currency": listing.currency}],
                    "main_product_image_locator": [{"media_location": listing.images[0]}] if listing.images else [],
                    "other_product_image_locator": [{"media_location": img} for img in listing.images[1:6]] if len(listing.images) > 1 else []
                }
            }
            
            # Simulate API call
            # In production: Make actual call to Amazon SP-API
            
            self.logger.info("Amazon listing created", sku=listing.sku, title=listing.title)
            
            return {
                "success": True,
                "marketplace_product_id": f"ASIN_{listing.sku}",
                "message": "Amazon listing created successfully"
            }
        
        except Exception as e:
            self.logger.error("Failed to create Amazon listing", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _create_ebay_listing(self, listing: ProductListing, credentials: MarketplaceCredentials) -> Dict[str, Any]:
        """Create listing on eBay Marketplace."""
        try:
            # eBay Trading API
            # In production, this would use the actual eBay Trading API
            
            # Prepare listing data for eBay
            ebay_listing = {
                "Title": listing.title,
                "Description": listing.description,
                "PrimaryCategory": {"CategoryID": listing.attributes.get("category_id", "1")},
                "StartPrice": listing.price,
                "Currency": listing.currency,
                "Country": "DE",
                "Location": "Germany",
                "Quantity": listing.quantity,
                "ListingType": "FixedPriceItem",
                "ListingDuration": "GTC",
                "SKU": listing.sku,
                "PictureDetails": {
                    "PictureURL": listing.images[:12]  # eBay allows up to 12 images
                } if listing.images else {}
            }
            
            # Simulate API call
            # In production: Make actual call to eBay Trading API
            
            self.logger.info("eBay listing created", sku=listing.sku, title=listing.title)
            
            return {
                "success": True,
                "marketplace_product_id": f"EBAY_{listing.sku}_{uuid4().hex[:8]}",
                "message": "eBay listing created successfully"
            }
        
        except Exception as e:
            self.logger.error("Failed to create eBay listing", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _create_mirakl_listing(self, listing: ProductListing, credentials: MarketplaceCredentials) -> Dict[str, Any]:
        """Create listing on Mirakl-powered marketplace."""
        try:
            # Mirakl API
            # In production, this would use the actual Mirakl API
            
            # Prepare listing data for Mirakl
            mirakl_offer = {
                "product-id": listing.product_id,
                "product-id-type": "SHOP_SKU",
                "quantity": listing.quantity,
                "price": listing.price,
                "price-additional-info": listing.currency,
                "description": listing.description,
                "state-code": "11",  # New condition
                "shop-sku": listing.sku,
                "available-start-date": datetime.utcnow().isoformat(),
                "leadtime-to-ship": 2,
                "logistic-class": "M"
            }
            
            # Add product attributes
            for key, value in listing.attributes.items():
                mirakl_offer[f"product-{key}"] = value
            
            # Simulate API call
            # In production: Make actual call to Mirakl API
            
            self.logger.info("Mirakl listing created", sku=listing.sku, title=listing.title)
            
            return {
                "success": True,
                "marketplace_product_id": f"MIRAKL_{listing.sku}",
                "message": "Mirakl listing created successfully"
            }
        
        except Exception as e:
            self.logger.error("Failed to create Mirakl listing", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _create_generic_listing(self, listing: ProductListing, credentials: MarketplaceCredentials) -> Dict[str, Any]:
        """Create listing on generic marketplace."""
        try:
            # Generic marketplace API simulation
            self.logger.info("Generic listing created", 
                           marketplace_type=listing.marketplace_type.value,
                           sku=listing.sku, 
                           title=listing.title)
            
            return {
                "success": True,
                "marketplace_product_id": f"{listing.marketplace_type.value.upper()}_{listing.sku}",
                "message": f"{listing.marketplace_type.value} listing created successfully"
            }
        
        except Exception as e:
            self.logger.error("Failed to create generic listing", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _update_product_listing(self, listing_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing product listing."""
        try:
            listing = self.product_listings.get(listing_id)
            if not listing:
                raise ValueError(f"Listing {listing_id} not found")
            
            # Update listing fields
            for field, value in updates.items():
                if hasattr(listing, field):
                    setattr(listing, field, value)
            
            listing.updated_at = datetime.utcnow()
            
            # Update on marketplace
            marketplace_result = await self._update_marketplace_listing(listing, updates)
            
            if marketplace_result["success"]:
                listing.last_sync = datetime.utcnow()
                
                # Send notification
                await self.send_message(
                    recipient_agent="product_agent",
                    message_type=MessageType.LISTING_UPDATED,
                    payload={
                        "listing_id": listing_id,
                        "product_id": listing.product_id,
                        "marketplace_type": listing.marketplace_type.value,
                        "updates": updates
                    }
                )
                
                return listing.dict()
            else:
                raise Exception(f"Failed to update marketplace listing: {marketplace_result.get('error')}")
        
        except Exception as e:
            self.logger.error("Failed to update product listing", error=str(e), listing_id=listing_id)
            raise
    
    async def _update_marketplace_listing(self, listing: ProductListing, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update listing on specific marketplace."""
        try:
            credentials = self.marketplace_credentials.get(listing.marketplace_id)
            if not credentials:
                return {"success": False, "error": "Marketplace credentials not found"}
            
            # Marketplace-specific update logic
            if listing.marketplace_type == MarketplaceType.AMAZON:
                return await self._update_amazon_listing(listing, updates, credentials)
            elif listing.marketplace_type == MarketplaceType.EBAY:
                return await self._update_ebay_listing(listing, updates, credentials)
            elif listing.marketplace_type == MarketplaceType.MIRAKL:
                return await self._update_mirakl_listing(listing, updates, credentials)
            else:
                # Generic update
                return {"success": True, "message": "Generic listing updated"}
        
        except Exception as e:
            self.logger.error("Failed to update marketplace listing", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _update_amazon_listing(self, listing: ProductListing, updates: Dict[str, Any], credentials: MarketplaceCredentials) -> Dict[str, Any]:
        """Update Amazon listing."""
        # Simulate Amazon SP-API update
        self.logger.info("Amazon listing updated", sku=listing.sku, updates=list(updates.keys()))
        return {"success": True, "message": "Amazon listing updated"}
    
    async def _update_ebay_listing(self, listing: ProductListing, updates: Dict[str, Any], credentials: MarketplaceCredentials) -> Dict[str, Any]:
        """Update eBay listing."""
        # Simulate eBay Trading API update
        self.logger.info("eBay listing updated", sku=listing.sku, updates=list(updates.keys()))
        return {"success": True, "message": "eBay listing updated"}
    
    async def _update_mirakl_listing(self, listing: ProductListing, updates: Dict[str, Any], credentials: MarketplaceCredentials) -> Dict[str, Any]:
        """Update Mirakl listing."""
        # Simulate Mirakl API update
        self.logger.info("Mirakl listing updated", sku=listing.sku, updates=list(updates.keys()))
        return {"success": True, "message": "Mirakl listing updated"}
    
    async def _update_listing_price(self, listing_id: str, new_price: float) -> Dict[str, Any]:
        """Update listing price."""
        return await self._update_product_listing(listing_id, {"price": new_price})
    
    async def _sync_orders(self, marketplace_id: str) -> Dict[str, Any]:
        """Synchronize orders from marketplace."""
        try:
            credentials = self.marketplace_credentials.get(marketplace_id)
            if not credentials:
                raise ValueError(f"Marketplace credentials not found for {marketplace_id}")
            
            # Create sync result
            sync_result = SyncResult(
                sync_id=str(uuid4()),
                marketplace_type=credentials.marketplace_type,
                marketplace_id=marketplace_id,
                sync_type="orders",
                started_at=datetime.utcnow()
            )
            
            # Fetch orders from marketplace
            orders = await self._fetch_marketplace_orders(credentials)
            
            processed_count = 0
            success_count = 0
            errors = []
            
            for order_data in orders:
                try:
                    # Process order
                    order = await self._process_marketplace_order(order_data, credentials)
                    
                    if order:
                        self.marketplace_orders[order.order_id] = order
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
            
            # Complete sync result
            sync_result.completed_at = datetime.utcnow()
            sync_result.success = len(errors) == 0
            sync_result.items_processed = processed_count
            sync_result.items_success = success_count
            sync_result.items_failed = processed_count - success_count
            sync_result.errors = errors
            sync_result.summary = {
                "new_orders": success_count,
                "total_processed": processed_count
            }
            
            # Store sync result
            self.sync_results[sync_result.sync_id] = sync_result
            
            # Update credentials last sync
            credentials.last_sync = datetime.utcnow()
            
            return sync_result.dict()
        
        except Exception as e:
            self.logger.error("Failed to sync orders", error=str(e), marketplace_id=marketplace_id)
            raise
    
    async def _fetch_marketplace_orders(self, credentials: MarketplaceCredentials) -> List[Dict[str, Any]]:
        """Fetch orders from marketplace API."""
        try:
            if credentials.marketplace_type == MarketplaceType.AMAZON:
                return await self._fetch_amazon_orders(credentials)
            elif credentials.marketplace_type == MarketplaceType.EBAY:
                return await self._fetch_ebay_orders(credentials)
            elif credentials.marketplace_type == MarketplaceType.MIRAKL:
                return await self._fetch_mirakl_orders(credentials)
            else:
                # Simulate generic orders
                return await self._fetch_generic_orders(credentials)
        
        except Exception as e:
            self.logger.error("Failed to fetch marketplace orders", error=str(e))
            if not self._db_initialized:
            return []
        
        async with self.db_manager.get_session() as session:
            records = await self.db_helper.get_all(session, MarketplaceOrderDB, limit=100)
            return [self.db_helper.to_dict(r) for r in records]
    
    async def _fetch_amazon_orders(self, credentials: MarketplaceCredentials) -> List[Dict[str, Any]]:
        """Fetch orders from Amazon SP-API."""
        # Simulate Amazon orders
        return [
            {
                "id": f"AMZ-{uuid4().hex[:8]}",
                "purchase_date": datetime.utcnow().isoformat(),
                "order_status": "Unshipped",
                "fulfillment_channel": "MFN",
                "sales_channel": "Amazon.de",
                "order_total": {"amount": "49.99", "currency_code": "EUR"},
                "buyer_email": "customer@example.com",
                "shipping_address": {
                    "name": "John Doe",
                    "address_line_1": "123 Main St",
                    "city": "Berlin",
                    "postal_code": "10115",
                    "country_code": "DE"
                },
                "order_items": [
                    {
                        "sku": "PROD-001",
                        "quantity_ordered": 1,
                        "item_price": {"amount": "49.99", "currency_code": "EUR"},
                        "title": "Sample Product"
                    }
                ]
            }
        ]
    
    async def _fetch_ebay_orders(self, credentials: MarketplaceCredentials) -> List[Dict[str, Any]]:
        """Fetch orders from eBay Trading API."""
        # Simulate eBay orders
        return [
            {
                "id": f"EBAY-{uuid4().hex[:8]}",
                "created_time": datetime.utcnow().isoformat(),
                "order_fulfillment_status": "NOT_STARTED",
                "order_payment_status": "PAID",
                "pricing_summary": {"total": {"value": "39.99", "currency": "EUR"}},
                "buyer": {"username": "ebaybuyer123"},
                "fulfillment_start_instructions": [
                    {
                        "shipping_step": {
                            "ship_to": {
                                "full_name": "Jane Smith",
                                "contact": {
                                    "primary_phone": {"phone_number": "+49123456789"}
                                },
                                "primary_address": {
                                    "address_line_1": "456 Oak Ave",
                                    "city": "Munich",
                                    "postal_code": "80331",
                                    "country_code": "DE"
                                }
                            }
                        }
                    }
                ],
                "line_items": [
                    {
                        "sku": "PROD-002",
                        "quantity": 1,
                        "line_item_cost": {"value": "39.99", "currency": "EUR"},
                        "title": "Another Product"
                    }
                ]
            }
        ]
    
    async def _fetch_mirakl_orders(self, credentials: MarketplaceCredentials) -> List[Dict[str, Any]]:
        """Fetch orders from Mirakl API."""
        # Simulate Mirakl orders
        return [
            {
                "id": f"MKL-{uuid4().hex[:8]}",
                "created_date": datetime.utcnow().isoformat(),
                "state": "WAITING_ACCEPTANCE",
                "total_price": 29.99,
                "currency_iso_code": "EUR",
                "customer": {
                    "firstname": "Mike",
                    "lastname": "Johnson",
                    "email": "mike@example.com"
                },
                "shipping_address": {
                    "firstname": "Mike",
                    "lastname": "Johnson",
                    "street_1": "789 Pine St",
                    "city": "Hamburg",
                    "zip_code": "20095",
                    "country_iso_code": "DE"
                },
                "order_lines": [
                    {
                        "offer_sku": "PROD-003",
                        "quantity": 1,
                        "price": 29.99,
                        "offer_state_code": "11",
                        "product_title": "Third Product"
                    }
                ]
            }
        ]
    
    async def _fetch_generic_orders(self, credentials: MarketplaceCredentials) -> List[Dict[str, Any]]:
        """Fetch orders from generic marketplace."""
        # Simulate generic orders
        return [
            {
                "id": f"GEN-{uuid4().hex[:8]}",
                "date": datetime.utcnow().isoformat(),
                "status": "pending",
                "total": 19.99,
                "currency": "EUR",
                "customer": {
                    "name": "Generic Customer",
                    "email": "generic@example.com"
                },
                "address": {
                    "street": "Generic Street 1",
                    "city": "Generic City",
                    "postal_code": "12345",
                    "country": "DE"
                },
                "items": [
                    {
                        "sku": "PROD-004",
                        "quantity": 1,
                        "price": 19.99,
                        "name": "Generic Product"
                    }
                ]
            }
        ]
    
    async def _process_marketplace_order(self, order_data: Dict[str, Any], credentials: MarketplaceCredentials) -> Optional[MarketplaceOrder]:
        """Process and normalize marketplace order data."""
        try:
            if credentials.marketplace_type == MarketplaceType.AMAZON:
                return self._process_amazon_order(order_data, credentials)
            elif credentials.marketplace_type == MarketplaceType.EBAY:
                return self._process_ebay_order(order_data, credentials)
            elif credentials.marketplace_type == MarketplaceType.MIRAKL:
                return self._process_mirakl_order(order_data, credentials)
            else:
                return self._process_generic_order(order_data, credentials)
        
        except Exception as e:
            self.logger.error("Failed to process marketplace order", error=str(e))
            return None
    
    def _process_amazon_order(self, order_data: Dict[str, Any], credentials: MarketplaceCredentials) -> MarketplaceOrder:
        """Process Amazon order data."""
        return MarketplaceOrder(
            order_id=str(uuid4()),
            marketplace_type=MarketplaceType.AMAZON,
            marketplace_id=credentials.marketplace_id,
            marketplace_order_id=order_data["id"],
            customer_info={
                "email": order_data.get("buyer_email", ""),
                "name": order_data.get("shipping_address", {}).get("name", "")
            },
            items=[
                {
                    "sku": item["sku"],
                    "quantity": item["quantity_ordered"],
                    "price": float(item["item_price"]["amount"]),
                    "title": item["title"]
                }
                for item in order_data.get("order_items", [])
            ],
            total_amount=float(order_data["order_total"]["amount"]),
            currency=order_data["order_total"]["currency_code"],
            status=OrderStatus.PENDING,
            order_date=datetime.fromisoformat(order_data["purchase_date"].replace("Z", "+00:00")),
            shipping_address=order_data.get("shipping_address", {}),
            billing_address=order_data.get("shipping_address", {}),  # Amazon doesn't always provide separate billing
            payment_method="Amazon Payments",
            shipping_method="Standard",
            last_sync=datetime.utcnow()
        )
    
    def _process_ebay_order(self, order_data: Dict[str, Any], credentials: MarketplaceCredentials) -> MarketplaceOrder:
        """Process eBay order data."""
        shipping_info = order_data.get("fulfillment_start_instructions", [{}])[0].get("shipping_step", {}).get("ship_to", {})
        
        return MarketplaceOrder(
            order_id=str(uuid4()),
            marketplace_type=MarketplaceType.EBAY,
            marketplace_id=credentials.marketplace_id,
            marketplace_order_id=order_data["id"],
            customer_info={
                "username": order_data.get("buyer", {}).get("username", ""),
                "name": shipping_info.get("full_name", "")
            },
            items=[
                {
                    "sku": item["sku"],
                    "quantity": item["quantity"],
                    "price": float(item["line_item_cost"]["value"]),
                    "title": item["title"]
                }
                for item in order_data.get("line_items", [])
            ],
            total_amount=float(order_data["pricing_summary"]["total"]["value"]),
            currency=order_data["pricing_summary"]["total"]["currency"],
            status=OrderStatus.PENDING,
            order_date=datetime.fromisoformat(order_data["created_time"].replace("Z", "+00:00")),
            shipping_address=shipping_info.get("primary_address", {}),
            billing_address=shipping_info.get("primary_address", {}),
            payment_method="PayPal",
            shipping_method="Standard",
            last_sync=datetime.utcnow()
        )
    
    def _process_mirakl_order(self, order_data: Dict[str, Any], credentials: MarketplaceCredentials) -> MarketplaceOrder:
        """Process Mirakl order data."""
        return MarketplaceOrder(
            order_id=str(uuid4()),
            marketplace_type=MarketplaceType.MIRAKL,
            marketplace_id=credentials.marketplace_id,
            marketplace_order_id=order_data["id"],
            customer_info={
                "email": order_data.get("customer", {}).get("email", ""),
                "name": f"{order_data.get('customer', {}).get('firstname', '')} {order_data.get('customer', {}).get('lastname', '')}"
            },
            items=[
                {
                    "sku": item["offer_sku"],
                    "quantity": item["quantity"],
                    "price": item["price"],
                    "title": item["product_title"]
                }
                for item in order_data.get("order_lines", [])
            ],
            total_amount=order_data["total_price"],
            currency=order_data["currency_iso_code"],
            status=OrderStatus.PENDING,
            order_date=datetime.fromisoformat(order_data["created_date"].replace("Z", "+00:00")),
            shipping_address=order_data.get("shipping_address", {}),
            billing_address=order_data.get("shipping_address", {}),
            payment_method="Mirakl Payments",
            shipping_method="Standard",
            last_sync=datetime.utcnow()
        )
    
    def _process_generic_order(self, order_data: Dict[str, Any], credentials: MarketplaceCredentials) -> MarketplaceOrder:
        """Process generic marketplace order data."""
        return MarketplaceOrder(
            order_id=str(uuid4()),
            marketplace_type=credentials.marketplace_type,
            marketplace_id=credentials.marketplace_id,
            marketplace_order_id=order_data["id"],
            customer_info=order_data.get("customer", {}),
            items=[
                {
                    "sku": item["sku"],
                    "quantity": item["quantity"],
                    "price": item["price"],
                    "title": item["name"]
                }
                for item in order_data.get("items", [])
            ],
            total_amount=order_data["total"],
            currency=order_data["currency"],
            status=OrderStatus.PENDING,
            order_date=datetime.fromisoformat(order_data["date"].replace("Z", "+00:00")),
            shipping_address=order_data.get("address", {}),
            billing_address=order_data.get("address", {}),
            payment_method="Generic Payment",
            shipping_method="Standard",
            last_sync=datetime.utcnow()
        )
    
    async def _sync_inventory(self, marketplace_id: str) -> Dict[str, Any]:
        """Synchronize inventory to marketplace."""
        try:
            credentials = self.marketplace_credentials.get(marketplace_id)
            if not credentials:
                raise ValueError(f"Marketplace credentials not found for {marketplace_id}")
            
            # Get current inventory from inventory agent
            inventory_data = await self._get_current_inventory()
            
            # Create sync result
            sync_result = SyncResult(
                sync_id=str(uuid4()),
                marketplace_type=credentials.marketplace_type,
                marketplace_id=marketplace_id,
                sync_type="inventory",
                started_at=datetime.utcnow()
            )
            
            processed_count = 0
            success_count = 0
            errors = []
            
            # Update inventory for each listing
            marketplace_listings = [l for l in self.product_listings.values() if l.marketplace_id == marketplace_id]
            
            for listing in marketplace_listings:
                try:
                    # Get inventory for this product
                    product_inventory = inventory_data.get(listing.product_id, {})
                    available_quantity = product_inventory.get("available_quantity", 0)
                    
                    # Update listing quantity
                    if listing.quantity != available_quantity:
                        update_result = await self._update_marketplace_inventory(listing, available_quantity, credentials)
                        
                        if update_result["success"]:
                            listing.quantity = available_quantity
                            listing.last_sync = datetime.utcnow()
                            success_count += 1
                        else:
                            errors.append(f"Listing {listing.listing_id}: {update_result.get('error')}")
                    else:
                        success_count += 1  # No update needed
                    
                    processed_count += 1
                
                except Exception as e:
                    errors.append(f"Listing {listing.listing_id}: {str(e)}")
                    processed_count += 1
            
            # Complete sync result
            sync_result.completed_at = datetime.utcnow()
            sync_result.success = len(errors) == 0
            sync_result.items_processed = processed_count
            sync_result.items_success = success_count
            sync_result.items_failed = processed_count - success_count
            sync_result.errors = errors
            sync_result.summary = {
                "listings_updated": success_count,
                "total_processed": processed_count
            }
            
            # Store sync result
            self.sync_results[sync_result.sync_id] = sync_result
            
            # Update credentials last sync
            credentials.last_sync = datetime.utcnow()
            
            return sync_result.dict()
        
        except Exception as e:
            self.logger.error("Failed to sync inventory", error=str(e), marketplace_id=marketplace_id)
            raise
    
    async def _get_current_inventory(self) -> Dict[str, Dict[str, Any]]:
        """Get current inventory data from inventory agent."""
        try:
            # In production, this would call the inventory agent
            # For now, simulate inventory data
            
            return {
                "PROD-001": {"available_quantity": 25, "reserved_quantity": 5},
                "PROD-002": {"available_quantity": 15, "reserved_quantity": 2},
                "PROD-003": {"available_quantity": 30, "reserved_quantity": 0},
                "PROD-004": {"available_quantity": 8, "reserved_quantity": 1}
            }
        
        except Exception as e:
            self.logger.error("Failed to get current inventory", error=str(e))
            if not self._db_initialized:
            return {}
        
        async with self.db_manager.get_session() as session:
            record = await self.db_helper.get_by_id(session, MarketplaceOrderDB, record_id)
            return self.db_helper.to_dict(record) if record else {}
    
    async def _update_marketplace_inventory(self, listing: ProductListing, new_quantity: int, credentials: MarketplaceCredentials) -> Dict[str, Any]:
        """Update inventory quantity on marketplace."""
        try:
            if credentials.marketplace_type == MarketplaceType.AMAZON:
                return await self._update_amazon_inventory(listing, new_quantity, credentials)
            elif credentials.marketplace_type == MarketplaceType.EBAY:
                return await self._update_ebay_inventory(listing, new_quantity, credentials)
            elif credentials.marketplace_type == MarketplaceType.MIRAKL:
                return await self._update_mirakl_inventory(listing, new_quantity, credentials)
            else:
                # Generic inventory update
                return {"success": True, "message": "Generic inventory updated"}
        
        except Exception as e:
            self.logger.error("Failed to update marketplace inventory", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _update_amazon_inventory(self, listing: ProductListing, new_quantity: int, credentials: MarketplaceCredentials) -> Dict[str, Any]:
        """Update Amazon inventory."""
        # Simulate Amazon inventory update
        self.logger.info("Amazon inventory updated", sku=listing.sku, quantity=new_quantity)
        return {"success": True, "message": "Amazon inventory updated"}
    
    async def _update_ebay_inventory(self, listing: ProductListing, new_quantity: int, credentials: MarketplaceCredentials) -> Dict[str, Any]:
        """Update eBay inventory."""
        # Simulate eBay inventory update
        self.logger.info("eBay inventory updated", sku=listing.sku, quantity=new_quantity)
        return {"success": True, "message": "eBay inventory updated"}
    
    async def _update_mirakl_inventory(self, listing: ProductListing, new_quantity: int, credentials: MarketplaceCredentials) -> Dict[str, Any]:
        """Update Mirakl inventory."""
        # Simulate Mirakl inventory update
        self.logger.info("Mirakl inventory updated", sku=listing.sku, quantity=new_quantity)
        return {"success": True, "message": "Mirakl inventory updated"}
    
    async def _fulfill_marketplace_order(self, order_id: str, fulfillment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fulfill a marketplace order."""
        try:
            order = self.marketplace_orders.get(order_id)
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            # Update order with fulfillment information
            order.status = OrderStatus.SHIPPED
            order.tracking_number = fulfillment_data.get("tracking_number")
            order.last_sync = datetime.utcnow()
            
            # Send fulfillment to marketplace
            credentials = self.marketplace_credentials.get(order.marketplace_id)
            if credentials:
                fulfillment_result = await self._send_marketplace_fulfillment(order, fulfillment_data, credentials)
                
                if not fulfillment_result["success"]:
                    self.logger.warning("Failed to send fulfillment to marketplace", 
                                      order_id=order_id, 
                                      error=fulfillment_result.get("error"))
            
            return order.dict()
        
        except Exception as e:
            self.logger.error("Failed to fulfill marketplace order", error=str(e), order_id=order_id)
            raise
    
    async def _send_marketplace_fulfillment(self, order: MarketplaceOrder, fulfillment_data: Dict[str, Any], credentials: MarketplaceCredentials) -> Dict[str, Any]:
        """Send fulfillment information to marketplace."""
        try:
            if credentials.marketplace_type == MarketplaceType.AMAZON:
                return await self._send_amazon_fulfillment(order, fulfillment_data, credentials)
            elif credentials.marketplace_type == MarketplaceType.EBAY:
                return await self._send_ebay_fulfillment(order, fulfillment_data, credentials)
            elif credentials.marketplace_type == MarketplaceType.MIRAKL:
                return await self._send_mirakl_fulfillment(order, fulfillment_data, credentials)
            else:
                # Generic fulfillment
                return {"success": True, "message": "Generic fulfillment sent"}
        
        except Exception as e:
            self.logger.error("Failed to send marketplace fulfillment", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _send_amazon_fulfillment(self, order: MarketplaceOrder, fulfillment_data: Dict[str, Any], credentials: MarketplaceCredentials) -> Dict[str, Any]:
        """Send fulfillment to Amazon."""
        # Simulate Amazon fulfillment
        self.logger.info("Amazon fulfillment sent", order_id=order.marketplace_order_id, tracking=order.tracking_number)
        return {"success": True, "message": "Amazon fulfillment sent"}
    
    async def _send_ebay_fulfillment(self, order: MarketplaceOrder, fulfillment_data: Dict[str, Any], credentials: MarketplaceCredentials) -> Dict[str, Any]:
        """Send fulfillment to eBay."""
        # Simulate eBay fulfillment
        self.logger.info("eBay fulfillment sent", order_id=order.marketplace_order_id, tracking=order.tracking_number)
        return {"success": True, "message": "eBay fulfillment sent"}
    
    async def _send_mirakl_fulfillment(self, order: MarketplaceOrder, fulfillment_data: Dict[str, Any], credentials: MarketplaceCredentials) -> Dict[str, Any]:
        """Send fulfillment to Mirakl."""
        # Simulate Mirakl fulfillment
        self.logger.info("Mirakl fulfillment sent", order_id=order.marketplace_order_id, tracking=order.tracking_number)
        return {"success": True, "message": "Mirakl fulfillment sent"}
    
    async def _get_marketplace_performance(self, marketplace_id: Optional[str] = None) -> Dict[str, Any]:
        """Get marketplace performance metrics."""
        try:
            # Filter data by marketplace if specified
            if marketplace_id:
                listings = [l for l in self.product_listings.values() if l.marketplace_id == marketplace_id]
                orders = [o for o in self.marketplace_orders.values() if o.marketplace_id == marketplace_id]
            else:
                listings = list(self.product_listings.values())
                orders = list(self.marketplace_orders.values())
            
            # Calculate performance metrics
            total_listings = len(listings)
            active_listings = len([l for l in listings if l.status == ListingStatus.ACTIVE])
            
            total_orders = len(orders)
            total_revenue = sum(o.total_amount for o in orders)
            
            # Orders by status
            orders_by_status = {}
            for status in OrderStatus:
                orders_by_status[status.value] = len([o for o in orders if o.status == status])
            
            # Listings by marketplace
            listings_by_marketplace = {}
            for marketplace_type in MarketplaceType:
                count = len([l for l in listings if l.marketplace_type == marketplace_type])
                if count > 0:
                    listings_by_marketplace[marketplace_type.value] = count
            
            # Recent sync results
            recent_syncs = [s for s in self.sync_results.values() 
                          if (datetime.utcnow() - s.started_at).days <= 7]
            
            sync_success_rate = (
                sum(1 for s in recent_syncs if s.success) / len(recent_syncs) * 100
                if recent_syncs else 0
            )
            
            return {
                "listings": {
                    "total": total_listings,
                    "active": active_listings,
                    "by_marketplace": listings_by_marketplace
                },
                "orders": {
                    "total": total_orders,
                    "total_revenue": total_revenue,
                    "by_status": orders_by_status
                },
                "sync_performance": {
                    "recent_syncs": len(recent_syncs),
                    "success_rate": sync_success_rate
                },
                "generated_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error("Failed to get marketplace performance", error=str(e))
            raise
    
    async def _load_marketplace_credentials(self):
        """Load marketplace credentials from configuration."""
        try:
            # In production, this would load from secure configuration
            # For now, create sample credentials
            
            sample_credentials = [
                MarketplaceCredentials(
                    marketplace_type=MarketplaceType.AMAZON,
                    marketplace_id="amazon_de",
                    api_key="sample_amazon_key",
                    secret_key="sample_amazon_secret",
                    seller_id="A1SAMPLE123",
                    additional_params={
                        "marketplace_id": "A1PA6795UKMFR9",
                        "refresh_token": "sample_refresh_token",
                        "client_id": "sample_client_id",
                        "client_secret": "sample_client_secret"
                    }
                ),
                MarketplaceCredentials(
                    marketplace_type=MarketplaceType.EBAY,
                    marketplace_id="ebay_de",
                    api_key="sample_ebay_key",
                    secret_key="sample_ebay_secret",
                    seller_id="sample_ebay_seller",
                    additional_params={
                        "app_id": "sample_app_id",
                        "dev_id": "sample_dev_id",
                        "cert_id": "sample_cert_id",
                        "user_token": "sample_user_token"
                    }
                )
            ]
            
            for cred in sample_credentials:
                self.marketplace_credentials[cred.marketplace_id] = cred
            
            self.logger.info("Marketplace credentials loaded", count=len(sample_credentials))
        
        except Exception as e:
            self.logger.error("Failed to load marketplace credentials", error=str(e))
    
    async def _handle_product_updated(self, message: AgentMessage):
        """Handle product update messages."""
        payload = message.payload
        product_id = payload.get("product_id")
        
        if product_id:
            try:
                # Find listings for this product
                product_listings = [l for l in self.product_listings.values() if l.product_id == product_id]
                
                # Update each listing
                for listing in product_listings:
                    updates = {}
                    
                    if "title" in payload:
                        updates["title"] = payload["title"]
                    if "description" in payload:
                        updates["description"] = payload["description"]
                    if "price" in payload:
                        updates["price"] = payload["price"]
                    if "images" in payload:
                        updates["images"] = payload["images"]
                    
                    if updates:
                        await self._update_product_listing(listing.listing_id, updates)
            
            except Exception as e:
                self.logger.error("Failed to handle product update", error=str(e), product_id=product_id)
    
    async def _handle_inventory_updated(self, message: AgentMessage):
        """Handle inventory update messages."""
        payload = message.payload
        product_id = payload.get("product_id")
        new_quantity = payload.get("available_quantity")
        
        if product_id and new_quantity is not None:
            try:
                # Find listings for this product
                product_listings = [l for l in self.product_listings.values() if l.product_id == product_id]
                
                # Update quantity for each listing
                for listing in product_listings:
                    if listing.quantity != new_quantity:
                        await self._update_product_listing(listing.listing_id, {"quantity": new_quantity})
            
            except Exception as e:
                self.logger.error("Failed to handle inventory update", error=str(e), product_id=product_id)
    
    async def _handle_price_updated(self, message: AgentMessage):
        """Handle price update messages."""
        payload = message.payload
        product_id = payload.get("product_id")
        new_price = payload.get("new_price")
        
        if product_id and new_price is not None:
            try:
                # Find listings for this product
                product_listings = [l for l in self.product_listings.values() if l.product_id == product_id]
                
                # Update price for each listing
                for listing in product_listings:
                    if listing.price != new_price:
                        await self._update_listing_price(listing.listing_id, new_price)
            
            except Exception as e:
                self.logger.error("Failed to handle price update", error=str(e), product_id=product_id)
    
    async def _handle_order_fulfillment(self, message: AgentMessage):
        """Handle order fulfillment messages."""
        payload = message.payload
        order_id = payload.get("order_id")
        fulfillment_data = payload.get("fulfillment_data", {})
        
        if order_id:
            try:
                await self._fulfill_marketplace_order(order_id, fulfillment_data)
            
            except Exception as e:
                self.logger.error("Failed to handle order fulfillment", error=str(e), order_id=order_id)
    
    async def _sync_orders_periodically(self):
        """Background task to sync orders periodically."""
        while not self.shutdown_event.is_set():
            try:
                # Sync orders every 15 minutes
                await asyncio.sleep(900)
                
                if not self.shutdown_event.is_set():
                    for marketplace_id in self.marketplace_credentials.keys():
                        try:
                            await self._sync_orders(marketplace_id)
                        except Exception as e:
                            self.logger.error("Failed to sync orders for marketplace", 
                                            error=str(e), 
                                            marketplace_id=marketplace_id)
            
            except Exception as e:
                self.logger.error("Error in periodic order sync", error=str(e))
                await asyncio.sleep(900)
    
    async def _sync_inventory_periodically(self):
        """Background task to sync inventory periodically."""
        while not self.shutdown_event.is_set():
            try:
                # Sync inventory every 30 minutes
                await asyncio.sleep(1800)
                
                if not self.shutdown_event.is_set():
                    for marketplace_id in self.marketplace_credentials.keys():
                        try:
                            await self._sync_inventory(marketplace_id)
                        except Exception as e:
                            self.logger.error("Failed to sync inventory for marketplace", 
                                            error=str(e), 
                                            marketplace_id=marketplace_id)
            
            except Exception as e:
                self.logger.error("Error in periodic inventory sync", error=str(e))
                await asyncio.sleep(1800)
    
    async def _monitor_listing_performance(self):
        """Background task to monitor listing performance."""
        while not self.shutdown_event.is_set():
            try:
                # Monitor performance every 2 hours
                await asyncio.sleep(7200)
                
                if not self.shutdown_event.is_set():
                    # Check for listings with issues
                    problematic_listings = []
                    
                    for listing in self.product_listings.values():
                        # Check if listing hasn't been synced recently
                        if (listing.last_sync and 
                            (datetime.utcnow() - listing.last_sync).total_seconds() > 86400):  # 24 hours
                            
                            problematic_listings.append({
                                "listing_id": listing.listing_id,
                                "issue": "sync_overdue",
                                "marketplace": listing.marketplace_type.value
                            })
                        
                        # Check for rejected listings
                        if listing.status == ListingStatus.REJECTED:
                            problematic_listings.append({
                                "listing_id": listing.listing_id,
                                "issue": "rejected_status",
                                "marketplace": listing.marketplace_type.value
                            })
                    
                    # Send alerts for problematic listings
                    if problematic_listings:
                        await self.send_message(
                            recipient_agent="monitoring_agent",
                            message_type=MessageType.RISK_ALERT,
                            payload={
                                "alert_type": "listing_performance",
                                "problematic_listings": problematic_listings,
                                "count": len(problematic_listings)
                            }
                        )
            
            except Exception as e:
                self.logger.error("Error monitoring listing performance", error=str(e))
                await asyncio.sleep(7200)
    
    async def _handle_marketplace_notifications(self):
        """Background task to handle marketplace notifications."""
        while not self.shutdown_event.is_set():
            try:
                # Check for notifications every 5 minutes
                await asyncio.sleep(300)
                
                if not self.shutdown_event.is_set():
                    # In production, this would check for:
                    # - Amazon SQS notifications
                    # - eBay platform notifications
                    # - Mirakl webhooks
                    # - Other marketplace notifications
                    
                    pass
            
            except Exception as e:
                self.logger.error("Error handling marketplace notifications", error=str(e))
                await asyncio.sleep(300)


# FastAPI app instance for running the agent as a service
app = FastAPI(title="Standard Marketplace Agent", version="1.0.0")

# Global agent instance
standard_marketplace_agent: Optional[StandardMarketplaceAgent] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the Standard Marketplace Agent on startup."""
    global standard_marketplace_agent
    standard_marketplace_agent = StandardMarketplaceAgent()
    await standard_marketplace_agent.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup the Standard Marketplace Agent on shutdown."""
    global standard_marketplace_agent
    if standard_marketplace_agent:
        await standard_marketplace_agent.stop()


# Include agent routes
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if standard_marketplace_agent:
        health_status = standard_marketplace_agent.get_health_status()
        return {"status": "healthy", "agent_status": health_status.dict()}
    return {"status": "unhealthy", "message": "Agent not initialized"}


# Mount agent's FastAPI app
app.mount("/api/v1", standard_marketplace_agent.app if standard_marketplace_agent else FastAPI())


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
        "standard_marketplace_agent:app",
        host="0.0.0.0",
        port=8011,
        reload=False,
        log_level="info"
    )
