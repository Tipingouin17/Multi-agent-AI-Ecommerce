"'""
Product Agent API - Multi-Agent E-commerce System

This agent provides comprehensive product management APIs including variants,
bundles, media, categories, attributes, pricing, reviews, inventory, relationships,
and lifecycle management.
"'""

import asyncio
import os
import sys
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel

# Path setup
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.database import DatabaseManager, get_database_manager
from shared.db_helpers import DatabaseHelper
from shared.product_models import *
from agents.services.product_service import ProductServiceFacade

logger = structlog.get_logger(__name__)


class ProductAgent(BaseAgent):
    """
    The ProductAgent is responsible for all aspects of product management in the multi-agent e-commerce system.
    It provides a comprehensive API for creating, retrieving, updating, and deleting product-related information.
    """

    def __init__(self, agent_id: str, agent_type: str, db_manager: DatabaseManager, db_helper: DatabaseHelper):
        """
        Initializes the ProductAgent.

        Args:
            agent_id (str): The unique identifier for the agent.
            agent_type (str): The type of the agent.
            db_manager (DatabaseManager): The database manager for database interactions.
            db_helper (DatabaseHelper): The database helper for CRUD operations.
        """
        super().__init__(agent_id, agent_type)
        self.db_manager = db_manager
        self.db_helper = db_helper
        self._db_initialized = False
        self.product_service = ProductServiceFacade(db_manager)
        self.app = FastAPI(
            title="Product Agent API",
            description="Comprehensive product management for multi-agent e-commerce",
            version="2.0.0"
        )
        self.setup_routes()

    async def startup(self):
        """
        Initializes the database connection.
        """
        try:
            await self.db_manager.initialize()
            self._db_initialized = True
            logger.info("Database initialized successfully.")
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            # Depending on the severity, you might want to re-raise or exit

    def setup_routes(self):
        """
        Sets up the FastAPI routes for the agent.
        """
        self.app.add_api_route("/health", self.health, methods=["GET"])
        self.app.add_api_route("/", self.root, methods=["GET"])

        # 1. PRODUCT VARIANT ENDPOINTS
        self.app.post("/api/v1/products/{product_id}/variants", response_model=ProductVariant)(self.create_product_variant)
        self.app.get("/api/v1/products/{product_id}/variants", response_model=List[ProductVariant])(self.get_product_variants)
        self.app.put("/api/v1/variants/{variant_id}", response_model=ProductVariant)(self.update_product_variant)
        self.app.post("/api/v1/variants/{variant_id}/set-master", response_model=ProductVariant)(self.set_master_variant)
        self.app.post("/api/v1/variant-attributes", response_model=VariantAttribute)(self.create_variant_attribute)

        # 2. PRODUCT BUNDLE ENDPOINTS
        self.app.post("/api/v1/bundles", response_model=BundleDetails)(self.create_product_bundle)
        self.app.get("/api/v1/bundles/{bundle_id}", response_model=BundleDetails)(self.get_bundle_details)
        self.app.get("/api/v1/bundles/{bundle_id}/price", response_model=Dict[str, Decimal])(self.calculate_bundle_price)
        self.app.post("/api/v1/bundles/{bundle_id}/activate", response_model=ProductBundle)(self.activate_bundle)

        # 3. PRODUCT MEDIA ENDPOINTS
        self.app.post("/api/v1/products/{product_id}/images", response_model=ProductImage)(self.add_product_image)
        self.app.get("/api/v1/products/{product_id}/images", response_model=List[ProductImage])(self.get_product_images)
        self.app.post("/api/v1/images/{image_id}/set-primary", response_model=ProductImage)(self.set_primary_image)
        self.app.delete("/api/v1/images/{image_id}")(self.delete_product_image)

        # 4. PRODUCT CATEGORY ENDPOINTS
        self.app.post("/api/v1/categories", response_model=ProductCategory)(self.create_category)
        self.app.get("/api/v1/categories/{category_id}", response_model=ProductCategory)(self.get_category)
        self.app.get("/api/v1/categories", response_model=List[ProductCategory])(self.get_all_categories)
        self.app.put("/api/v1/categories/{category_id}", response_model=ProductCategory)(self.update_category)
        self.app.delete("/api/v1/categories/{category_id}")(self.delete_category)
        self.app.post("/api/v1/categories/{category_id}/assign", response_model=Product)(self.assign_category_to_product)

        # 5. PRODUCT ATTRIBUTE ENDPOINTS
        self.app.post("/api/v1/attributes", response_model=ProductAttribute)(self.create_attribute)
        self.app.get("/api/v1/attributes/{attribute_id}", response_model=ProductAttribute)(self.get_attribute)
        self.app.get("/api/v1/attributes", response_model=List[ProductAttribute])(self.get_all_attributes)
        self.app.put("/api/v1/attributes/{attribute_id}", response_model=ProductAttribute)(self.update_attribute)
        self.app.delete("/api/v1/attributes/{attribute_id}")(self.delete_attribute)
        self.app.post("/api/v1/products/{product_id}/attributes", response_model=ProductAttributeValue)(self.assign_attribute_to_product)
        self.app.put("/api/v1/products/{product_id}/attributes/{attribute_id}", response_model=ProductAttributeValue)(self.update_product_attribute_value)
        self.app.delete("/api/v1/products/{product_id}/attributes/{attribute_id}")(self.remove_product_attribute)

        # 6. PRODUCT PRICING ENDPOINTS
        self.app.post("/api/v1/pricing-rules", response_model=PricingRule)(self.create_pricing_rule)
        self.app.get("/api/v1/products/{product_id}/price", response_model=Dict[str, Any])(self.calculate_product_price)
        self.app.post("/api/v1/products/{product_id}/price", response_model=PriceHistory)(self.update_product_price)
        self.app.post("/api/v1/pricing/bulk-update", response_model=Dict[str, Any])(self.bulk_update_prices)
        self.app.post("/api/v1/competitor-prices", response_model=CompetitorPrice)(self.track_competitor_price)

        # 7. PRODUCT REVIEW ENDPOINTS
        self.app.post("/api/v1/products/{product_id}/reviews", response_model=ProductReview)(self.create_product_review_endpoint)
        self.app.get("/api/v1/products/{product_id}/reviews", response_model=List[ProductReview])(self.get_product_reviews)
        self.app.get("/api/v1/products/{product_id}/reviews/summary", response_model=Dict[str, Any])(self.get_review_summary)
        self.app.post("/api/v1/reviews/{review_id}/approve", response_model=ProductReview)(self.approve_review)
        self.app.post("/api/v1/reviews/{review_id}/vote", response_model=ReviewVote)(self.add_review_vote)
        self.app.post("/api/v1/reviews/{review_id}/response", response_model=ReviewResponse)(self.add_seller_response)

        # 8. PRODUCT INVENTORY ENDPOINTS
        self.app.post("/api/v1/inventory", response_model=ProductInventory)(self.create_inventory)
        self.app.get("/api/v1/products/{product_id}/inventory", response_model=ProductInventory)(self.get_product_inventory)
        self.app.post("/api/v1/inventory/adjust", response_model=InventoryTransaction)(self.adjust_inventory)
        self.app.post("/api/v1/inventory/reserve", response_model=InventoryReservation)(self.reserve_inventory)
        self.app.get("/api/v1/products/{product_id}/availability", response_model=Dict[str, Any])(self.check_availability)
        self.app.get("/api/v1/inventory/low-stock", response_model=List[ProductInventory])(self.get_low_stock_products)

        # 9. PRODUCT RELATIONSHIP ENDPOINTS
        self.app.post("/api/v1/product-relationships", response_model=ProductRelationship)(self.create_product_relationship)
        self.app.get("/api/v1/products/{product_id}/related", response_model=List[ProductRelationship])(self.get_related_products)
        self.app.post("/api/v1/products/{product_id}/recommendations", response_model=List[ProductRecommendation])(self.generate_recommendations)
        self.app.post("/api/v1/product-recommendations", response_model=ProductRecommendation)(self.create_recommendation)

        # 10. PRODUCT LIFECYCLE ENDPOINTS
        self.app.post("/api/v1/products/{product_id}/lifecycle", response_model=ProductLifecycle)(self.create_lifecycle)
        self.app.post("/api/v1/products/{product_id}/status", response_model=ProductLifecycle)(self.update_product_status)
        self.app.post("/api/v1/products/{product_id}/versions", response_model=ProductVersion)(self.create_version_snapshot)
        self.app.post("/api/v1/products/{product_id}/changes", response_model=ProductChange)(self.record_product_change)
        self.app.post("/api/v1/products/{product_id}/approvals", response_model=ProductApproval)(self.request_approval)
        self.app.post("/api/v1/approvals/{approval_id}/review", response_model=ProductApproval)(self.review_approval)


    async def health(self):
        """
        Health check endpoint.
        """
        return {"status": "ok"}

    async def root(self):
        """
        Root endpoint.
        """
        return {"message": "Welcome to the Product Agent API"}

    async def process_message(self, message: AgentMessage):
        """
        Processes incoming Kafka messages.

        Args:
            message (AgentMessage): The incoming agent message.
        """
        logger.info("Processing message", message_type=message.message_type)
        if not self._db_initialized:
            logger.warning("Database not initialized, skipping message processing.")
            return

        try:
            if message.message_type == MessageType.PRODUCT_CREATED:
                logger.info("Product created event received", product_id=message.payload.get("product_id"))
                # Further processing for product creation
            elif message.message_type == MessageType.PRODUCT_UPDATED:
                logger.info("Product updated event received", product_id=message.payload.get("product_id"))
                # Further processing for product update
            elif message.message_type == MessageType.INVENTORY_UPDATE:
                logger.info("Inventory update event received", product_id=message.payload.get("product_id"))
                # Further processing for inventory update
            else:
                logger.warning("Unhandled message type", message_type=message.message_type)
            # Add other message types as needed
        except Exception as e:
            logger.error("Error processing message", error=str(e), message=message.dict())
            await self.send_message(MessageType.ERROR, {"original_message": message.dict(), "error": str(e)})

    # =====================================================
    # 1. PRODUCT VARIANT ENDPOINTS
    # =====================================================

    async def create_product_variant(
        self,
        product_id: str = Path(..., description="Product ID"),
        variant: ProductVariantCreate = Body(...),
        attribute_values: List[VariantAttributeValueCreate] = Body([]),
    ) -> ProductVariant:
        """
        Create a new product variant with attribute values.

        Args:
            product_id (str): ID of the parent product.
            variant (ProductVariantCreate): Variant data.
            attribute_values (List[VariantAttributeValueCreate]): List of attribute values (e.g., size, color).

        Returns:
            ProductVariant: The created product variant.

        Raises:
            HTTPException: If an error occurs during variant creation.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            variant.product_id = product_id
            async with self.db_manager.get_session() as session:
                result = await self.product_service.variants.create_variant(variant, attribute_values)
                await session.commit()
                return result
        except Exception as e:
            logger.error("create_variant_failed", error=str(e), product_id=product_id)
            raise HTTPException(status_code=500, detail=str(e))

    async def get_product_variants(
        self,
        product_id: str = Path(..., description="Product ID"),
    ) -> List[ProductVariant]:
        """
        Get all variants for a product.

        Args:
            product_id (str): ID of the parent product.

        Returns:
            List[ProductVariant]: A list of product variants.

        Raises:
            HTTPException: If an error occurs during retrieval.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                variants = await self.product_service.variants.get_product_variants(product_id)
                return variants
        except Exception as e:
            logger.error("get_variants_failed", error=str(e), product_id=product_id)
            raise HTTPException(status_code=500, detail=str(e))

    async def update_product_variant(
        self,
        variant_id: UUID = Path(..., description="Variant ID"),
        update_data: ProductVariantUpdate = Body(...),
    ) -> ProductVariant:
        """
        Update a product variant.

        Args:
            variant_id (UUID): The ID of the variant to update.
            update_data (ProductVariantUpdate): The data to update the variant with.

        Returns:
            ProductVariant: The updated product variant.

        Raises:
            HTTPException: If the variant is not found or an error occurs.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.variants.update_variant(variant_id, update_data)
                await session.commit()
                if not result:
                    raise HTTPException(status_code=404, detail="Variant not found")
                return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error("update_variant_failed", error=str(e), variant_id=str(variant_id))
            raise HTTPException(status_code=500, detail=str(e))

    async def set_master_variant(
        self,
        variant_id: UUID = Path(..., description="Variant ID"),
        product_id: str = Query(..., description="Product ID"),
    ) -> ProductVariant:
        """
        Set a variant as the master variant for a product.

        Args:
            variant_id (UUID): The ID of the variant to set as master.
            product_id (str): The ID of the parent product.

        Returns:
            ProductVariant: The updated master variant.

        Raises:
            HTTPException: If an error occurs during the operation.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.variants.set_master_variant(variant_id, product_id)
                await session.commit()
                return result
        except Exception as e:
            logger.error("set_master_variant_failed", error=str(e), variant_id=str(variant_id))
            raise HTTPException(status_code=500, detail=str(e))

    async def create_variant_attribute(
        self,
        attribute: VariantAttributeCreate = Body(...),
    ) -> VariantAttribute:
        """
        Create a new variant attribute definition (e.g., 'Size', 'Color').

        Args:
            attribute (VariantAttributeCreate): The data for the new variant attribute.

        Returns:
            VariantAttribute: The created variant attribute.

        Raises:
            HTTPException: If an error occurs during creation.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.variants.repo.create_variant_attribute(attribute)
                await session.commit()
                return result
        except Exception as e:
            logger.error("create_variant_attribute_failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    # =====================================================
    # 2. PRODUCT BUNDLE ENDPOINTS
    # =====================================================

    async def create_product_bundle(
        self,
        bundle: ProductBundleCreate = Body(...),
        components: List[BundleComponentCreate] = Body(...),
        pricing_rules: Optional[List[BundlePricingRuleCreate]] = Body(None),
    ) -> BundleDetails:
        """
        Create a product bundle with components and pricing rules.

        Args:
            bundle (ProductBundleCreate): Bundle data.
            components (List[BundleComponentCreate]): List of products in the bundle.
            pricing_rules (Optional[List[BundlePricingRuleCreate]]): Optional pricing rules.

        Returns:
            BundleDetails: The created bundle details.

        Raises:
            HTTPException: If an error occurs during bundle creation.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.bundles.create_bundle(bundle, components, pricing_rules)
                await session.commit()
                return result
        except Exception as e:
            logger.error("create_bundle_failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    async def get_bundle_details(
        self,
        bundle_id: UUID = Path(..., description="Bundle ID"),
    ) -> BundleDetails:
        """
        Get complete bundle details including components and pricing.

        Args:
            bundle_id (UUID): The ID of the bundle to retrieve.

        Returns:
            BundleDetails: The details of the bundle.

        Raises:
            HTTPException: If the bundle is not found or an error occurs.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.bundles.get_bundle_details(bundle_id)
                if not result:
                    raise HTTPException(status_code=404, detail="Bundle not found")
                return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error("get_bundle_failed", error=str(e), bundle_id=str(bundle_id))
            raise HTTPException(status_code=500, detail=str(e))

    async def calculate_bundle_price(
        self,
        bundle_id: UUID = Path(..., description="Bundle ID"),
    ) -> Dict[str, Decimal]:
        """
        Calculate the effective price of a bundle based on its pricing strategy.

        Args:
            bundle_id (UUID): The ID of the bundle.

        Returns:
            Dict[str, Decimal]: A dictionary containing the bundle ID and calculated price.

        Raises:
            HTTPException: If an error occurs during price calculation.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                price = await self.product_service.bundles.calculate_bundle_price(bundle_id)
                return {"bundle_id": str(bundle_id), "calculated_price": price}
        except Exception as e:
            logger.error("calculate_bundle_price_failed", error=str(e), bundle_id=str(bundle_id))
            raise HTTPException(status_code=500, detail=str(e))

    async def activate_bundle(
        self,
        bundle_id: UUID = Path(..., description="Bundle ID"),
    ) -> ProductBundle:
        """
        Activate a bundle for sale.

        Args:
            bundle_id (UUID): The ID of the bundle to activate.

        Returns:
            ProductBundle: The activated product bundle.

        Raises:
            HTTPException: If the bundle is not found or an error occurs.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.bundles.activate_bundle(bundle_id)
                await session.commit()
                if not result:
                    raise HTTPException(status_code=404, detail="Bundle not found")
                return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error("activate_bundle_failed", error=str(e), bundle_id=str(bundle_id))
            raise HTTPException(status_code=500, detail=str(e))

    # =====================================================
    # 3. PRODUCT MEDIA ENDPOINTS
    # =====================================================

    async def add_product_image(
        self,
        product_id: str = Path(..., description="Product ID"),
        image: ProductImageCreate = Body(...),
        set_as_primary: bool = Query(False, description="Set as primary image"),
    ) -> ProductImage:
        """
        Add an image to a product.

        Args:
            product_id (str): Product ID.
            image (ProductImageCreate): Image data.
            set_as_primary (bool): Whether to set this as the primary image.

        Returns:
            ProductImage: The added product image.

        Raises:
            HTTPException: If an error occurs during image addition.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            image.product_id = product_id
            async with self.db_manager.get_session() as session:
                result = await self.product_service.media.add_product_image(image, set_as_primary)
                await session.commit()
                return result
        except Exception as e:
            logger.error("add_product_image_failed", error=str(e), product_id=product_id)
            raise HTTPException(status_code=500, detail=str(e))

    async def get_product_images(
        self,
        product_id: str = Path(..., description="Product ID"),
    ) -> List[ProductImage]:
        """
        Get all images for a product, ordered by primary first.

        Args:
            product_id (str): Product ID.

        Returns:
            List[ProductImage]: A list of product images.

        Raises:
            HTTPException: If an error occurs during retrieval.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                images = await self.product_service.media.get_product_images(product_id)
                return images
        except Exception as e:
            logger.error("get_product_images_failed", error=str(e), product_id=product_id)
            raise HTTPException(status_code=500, detail=str(e))

    async def set_primary_image(
        self,
        image_id: UUID = Path(..., description="Image ID"),
        product_id: str = Query(..., description="Product ID"),
    ) -> ProductImage:
        """
        Set an image as the primary image for a product.

        Args:
            image_id (UUID): Image ID.
            product_id (str): Product ID.

        Returns:
            ProductImage: The updated product image.

        Raises:
            HTTPException: If an error occurs during the operation.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.media.set_primary_image(image_id, product_id)
                await session.commit()
                return result
        except Exception as e:
            logger.error("set_primary_image_failed", error=str(e), image_id=str(image_id))
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_product_image(
        self,
        image_id: UUID = Path(..., description="Image ID"),
    ):
        """
        Delete a product image.

        Args:
            image_id (UUID): Image ID.

        Raises:
            HTTPException: If the image is not found or an error occurs.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                success = await self.product_service.media.delete_product_image(image_id)
                await session.commit()
                if not success:
                    raise HTTPException(status_code=404, detail="Image not found")
                return {"message": "Image deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error("delete_product_image_failed", error=str(e), image_id=str(image_id))
            raise HTTPException(status_code=500, detail=str(e))

    # =====================================================
    # 4. PRODUCT CATEGORY ENDPOINTS
    # =====================================================

    async def create_category(
        self,
        category: ProductCategoryCreate = Body(...),
    ) -> ProductCategory:
        """
        Create a new product category.

        Args:
            category (ProductCategoryCreate): Category data.

        Returns:
            ProductCategory: The created product category.

        Raises:
            HTTPException: If an error occurs during creation.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.categories.create_category(category)
                await session.commit()
                return result
        except Exception as e:
            logger.error("create_category_failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    async def get_category(
        self,
        category_id: UUID = Path(..., description="Category ID"),
    ) -> ProductCategory:
        """
        Get a product category by ID.

        Args:
            category_id (UUID): Category ID.

        Returns:
            ProductCategory: The product category.

        Raises:
            HTTPException: If the category is not found or an error occurs.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.categories.get_category(category_id)
                if not result:
                    raise HTTPException(status_code=404, detail="Category not found")
                return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error("get_category_failed", error=str(e), category_id=str(category_id))
            raise HTTPException(status_code=500, detail=str(e))

    async def get_all_categories(
        self,
    ) -> List[ProductCategory]:
        """
        Get all product categories.

        Returns:
            List[ProductCategory]: A list of all product categories.

        Raises:
            HTTPException: If an error occurs during retrieval.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.categories.get_all_categories()
                return result
        except Exception as e:
            logger.error("get_all_categories_failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    async def update_category(
        self,
        category_id: UUID = Path(..., description="Category ID"),
        update_data: ProductCategoryUpdate = Body(...),
    ) -> ProductCategory:
        """
        Update a product category.

        Args:
            category_id (UUID): Category ID.
            update_data (ProductCategoryUpdate): Update data.

        Returns:
            ProductCategory: The updated product category.

        Raises:
            HTTPException: If the category is not found or an error occurs.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.categories.update_category(category_id, update_data)
                await session.commit()
                if not result:
                    raise HTTPException(status_code=404, detail="Category not found")
                return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error("update_category_failed", error=str(e), category_id=str(category_id))
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_category(
        self,
        category_id: UUID = Path(..., description="Category ID"),
    ):
        """
        Delete a product category.

        Args:
            category_id (UUID): Category ID.

        Raises:
            HTTPException: If the category is not found or an error occurs.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                success = await self.product_service.categories.delete_category(category_id)
                await session.commit()
                if not success:
                    raise HTTPException(status_code=404, detail="Category not found")
                return {"message": "Category deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error("delete_category_failed", error=str(e), category_id=str(category_id))
            raise HTTPException(status_code=500, detail=str(e))

    async def assign_category_to_product(
        self,
        product_id: str = Path(..., description="Product ID"),
        category_id: UUID = Body(..., description="Category ID to assign"),
    ) -> Product:
        """
        Assign a category to a product.

        Args:
            product_id (str): Product ID.
            category_id (UUID): Category ID to assign.

        Returns:
            Product: The updated product.

        Raises:
            HTTPException: If the product or category is not found or an error occurs.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.categories.assign_category_to_product(product_id, category_id)
                await session.commit()
                if not result:
                    raise HTTPException(status_code=404, detail="Product or Category not found")
                return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error("assign_category_to_product_failed", error=str(e), product_id=product_id, category_id=str(category_id))
            raise HTTPException(status_code=500, detail=str(e))

    # =====================================================
    # 5. PRODUCT ATTRIBUTE ENDPOINTS
    # =====================================================

    async def create_attribute(
        self,
        attribute: ProductAttributeCreate = Body(...),
    ) -> ProductAttribute:
        """
        Create a new product attribute.

        Args:
            attribute (ProductAttributeCreate): Attribute data.

        Returns:
            ProductAttribute: The created product attribute.

        Raises:
            HTTPException: If an error occurs during creation.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.attributes.create_attribute(attribute)
                await session.commit()
                return result
        except Exception as e:
            logger.error("create_attribute_failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    async def get_attribute(
        self,
        attribute_id: UUID = Path(..., description="Attribute ID"),
    ) -> ProductAttribute:
        """
        Get a product attribute by ID.

        Args:
            attribute_id (UUID): Attribute ID.

        Returns:
            ProductAttribute: The product attribute.

        Raises:
            HTTPException: If the attribute is not found or an error occurs.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.attributes.get_attribute(attribute_id)
                if not result:
                    raise HTTPException(status_code=404, detail="Attribute not found")
                return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error("get_attribute_failed", error=str(e), attribute_id=str(attribute_id))
            raise HTTPException(status_code=500, detail=str(e))

    async def get_all_attributes(
        self,
    ) -> List[ProductAttribute]:
        """
        Get all product attributes.

        Returns:
            List[ProductAttribute]: A list of all product attributes.

        Raises:
            HTTPException: If an error occurs during retrieval.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.attributes.get_all_attributes()
                return result
        except Exception as e:
            logger.error("get_all_attributes_failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    async def update_attribute(
        self,
        attribute_id: UUID = Path(..., description="Attribute ID"),
        update_data: ProductAttributeUpdate = Body(...),
    ) -> ProductAttribute:
        """
        Update a product attribute.

        Args:
            attribute_id (UUID): Attribute ID.
            update_data (ProductAttributeUpdate): Update data.

        Returns:
            ProductAttribute: The updated product attribute.

        Raises:
            HTTPException: If the attribute is not found or an error occurs.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.attributes.update_attribute(attribute_id, update_data)
                await session.commit()
                if not result:
                    raise HTTPException(status_code=404, detail="Attribute not found")
                return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error("update_attribute_failed", error=str(e), attribute_id=str(attribute_id))
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_attribute(
        self,
        attribute_id: UUID = Path(..., description="Attribute ID"),
    ):
        """
        Delete a product attribute.

        Args:
            attribute_id (UUID): Attribute ID.

        Raises:
            HTTPException: If the attribute is not found or an error occurs.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                success = await self.product_service.attributes.delete_attribute(attribute_id)
                await session.commit()
                if not success:
                    raise HTTPException(status_code=404, detail="Attribute not found")
                return {"message": "Attribute deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error("delete_attribute_failed", error=str(e), attribute_id=str(attribute_id))
            raise HTTPException(status_code=500, detail=str(e))

    async def assign_attribute_to_product(
        self,
        product_id: str = Path(..., description="Product ID"),
        attribute_value: ProductAttributeValueCreate = Body(...),
    ) -> ProductAttributeValue:
        """
        Assign an attribute value to a product.

        Args:
            product_id (str): Product ID.
            attribute_value (ProductAttributeValueCreate): Attribute value data.

        Returns:
            ProductAttributeValue: The created product attribute value.

        Raises:
            HTTPException: If an error occurs during assignment.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            attribute_value.product_id = product_id
            async with self.db_manager.get_session() as session:
                result = await self.product_service.attributes.assign_attribute_to_product(attribute_value)
                await session.commit()
                return result
        except Exception as e:
            logger.error("assign_attribute_to_product_failed", error=str(e), product_id=product_id)
            raise HTTPException(status_code=500, detail=str(e))

    async def update_product_attribute_value(
        self,
        product_id: str = Path(..., description="Product ID"),
        attribute_id: UUID = Path(..., description="Attribute ID"),
        update_data: ProductAttributeValueUpdate = Body(...),
    ) -> ProductAttributeValue:
        """
        Update a product's attribute value.

        Args:
            product_id (str): Product ID.
            attribute_id (UUID): Attribute ID.
            update_data (ProductAttributeValueUpdate): Update data.

        Returns:
            ProductAttributeValue: The updated product attribute value.

        Raises:
            HTTPException: If the attribute value is not found or an error occurs.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.attributes.update_product_attribute_value(product_id, attribute_id, update_data)
                await session.commit()
                if not result:
                    raise HTTPException(status_code=404, detail="Product attribute value not found")
                return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error("update_product_attribute_value_failed", error=str(e), product_id=product_id, attribute_id=str(attribute_id))
            raise HTTPException(status_code=500, detail=str(e))

    async def remove_product_attribute(
        self,
        product_id: str = Path(..., description="Product ID"),
        attribute_id: UUID = Path(..., description="Attribute ID"),
    ):
        """
        Remove an attribute from a product.

        Args:
            product_id (str): Product ID.
            attribute_id (UUID): Attribute ID.

        Raises:
            HTTPException: If the attribute value is not found or an error occurs.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                success = await self.product_service.attributes.remove_product_attribute(product_id, attribute_id)
                await session.commit()
                if not success:
                    raise HTTPException(status_code=404, detail="Product attribute value not found")
                return {"message": "Product attribute removed successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error("remove_product_attribute_failed", error=str(e), product_id=product_id, attribute_id=str(attribute_id))
            raise HTTPException(status_code=500, detail=str(e))

    # =====================================================
    # 6. PRODUCT PRICING ENDPOINTS
    # =====================================================

    async def create_pricing_rule(
        self,
        rule: PricingRuleCreate = Body(...),
        tiers: Optional[List[PricingTierCreate]] = Body(None),
    ) -> PricingRule:
        """
        Create a new pricing rule with optional tiers.

        Args:
            rule (PricingRuleCreate): Pricing rule data.
            tiers (Optional[List[PricingTierCreate]]): Optional list of pricing tiers.

        Returns:
            PricingRule: The created pricing rule.

        Raises:
            HTTPException: If an error occurs during creation.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.pricing.create_pricing_rule(rule, tiers)
                await session.commit()
                return result
        except Exception as e:
            logger.error("create_pricing_rule_failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    async def calculate_product_price(
        self,
        product_id: str = Path(..., description="Product ID"),
        quantity: int = Query(1, description="Quantity"),
        customer_id: Optional[str] = Query(None, description="Customer ID for personalized pricing"),
    ) -> Dict[str, Any]:
        """
        Calculate the effective price for a product based on active pricing rules.

        Args:
            product_id (str): Product ID.
            quantity (int): Quantity being purchased.
            customer_id (Optional[str]): Optional customer ID for personalized pricing.

        Returns:
            Dict[str, Any]: A dictionary containing product ID, quantity, calculated price, and total price.

        Raises:
            HTTPException: If an error occurs during price calculation.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                price = await self.product_service.pricing.calculate_price(product_id, quantity, customer_id)
                return {
                    "product_id": product_id,
                    "quantity": quantity,
                    "calculated_price": price,
                    "total_price": price * quantity
                }
        except Exception as e:
            logger.error("calculate_price_failed", error=str(e), product_id=product_id)
            raise HTTPException(status_code=500, detail=str(e))

    async def update_product_price(
        self,
        product_id: str = Path(..., description="Product ID"),
        new_price: Decimal = Body(..., description="New price"),
        reason: str = Body(..., description="Reason for price change"),
        changed_by: str = Body(..., description="User making the change"),
        effective_date: Optional[date] = Body(None, description="Effective date"),
    ) -> PriceHistory:
        """
        Update product price and record in history.

        Args:
            product_id (str): Product ID.
            new_price (Decimal): New price.
            reason (str): Reason for price change.
            changed_by (str): User making the change.
            effective_date (Optional[date]): When the price takes effect.

        Returns:
            PriceHistory: The recorded price history entry.

        Raises:
            HTTPException: If an error occurs during price update.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.pricing.update_price(
                    product_id, new_price, reason, changed_by, effective_date
                )
                await session.commit()
                return result
        except Exception as e:
            logger.error("update_price_failed", error=str(e), product_id=product_id)
            raise HTTPException(status_code=500, detail=str(e))

    async def bulk_update_prices(
        self,
        request: BulkPriceUpdateRequest = Body(...),
    ) -> Dict[str, Any]:
        """
        Update prices for multiple products.

        Args:
            request (BulkPriceUpdateRequest): Bulk price update request.

        Returns:
            Dict[str, Any]: A dictionary indicating the result of the bulk update.

        Raises:
            HTTPException: If an error occurs during bulk update.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.pricing.bulk_update_prices(request)
                await session.commit()
                return result
        except Exception as e:
            logger.error("bulk_update_prices_failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    async def track_competitor_price(
        self,
        price: CompetitorPriceCreate = Body(...),
    ) -> CompetitorPrice:
        """
        Track a competitor's price for a product.

        Args:
            price (CompetitorPriceCreate): Competitor price data.

        Returns:
            CompetitorPrice: The tracked competitor price entry.

        Raises:
            HTTPException: If an error occurs during tracking.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.pricing.track_competitor_price(price)
                await session.commit()
                return result
        except Exception as e:
            logger.error("track_competitor_price_failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    # =====================================================
    # 7. PRODUCT REVIEW ENDPOINTS
    # =====================================================

    async def create_product_review_endpoint(
        self,
        product_id: str = Path(..., description="Product ID"),
        review: ProductReviewCreate = Body(...),
    ) -> ProductReview:
        """
        Create a new product review.

        Args:
            product_id (str): Product ID.
            review (ProductReviewCreate): Review data.

        Returns:
            ProductReview: The created product review.

        Raises:
            HTTPException: If an error occurs during review creation.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            review.product_id = product_id
            async with self.db_manager.get_session() as session:
                result = await self.product_service.reviews.create_review(review)
                await session.commit()
                return result
        except Exception as e:
            logger.error("create_review_failed", error=str(e), product_id=product_id)
            raise HTTPException(status_code=500, detail=str(e))

    async def get_product_reviews(
        self,
        product_id: str = Path(..., description="Product ID"),
        approved_only: bool = Query(True, description="Show only approved reviews"),
    ) -> List[ProductReview]:
        """
        Get all reviews for a product.

        Args:
            product_id (str): Product ID.
            approved_only (bool): Show only approved reviews.

        Returns:
            List[ProductReview]: A list of product reviews.

        Raises:
            HTTPException: If an error occurs during retrieval.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                reviews = await self.product_service.reviews.get_product_reviews(product_id, approved_only)
                return reviews
        except Exception as e:
            logger.error("get_reviews_failed", error=str(e), product_id=product_id)
            raise HTTPException(status_code=500, detail=str(e))

    async def get_review_summary(
        self,
        product_id: str = Path(..., description="Product ID"),
    ) -> Dict[str, Any]:
        """
        Get rating summary statistics for a product.

        Args:
            product_id (str): Product ID.

        Returns:
            Dict[str, Any]: A dictionary containing the review summary (average rating, total reviews, etc.).

        Raises:
            HTTPException: If an error occurs during summary calculation.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                summary = await self.product_service.reviews.calculate_rating_summary(product_id)
                return summary
        except Exception as e:
            logger.error("get_review_summary_failed", error=str(e), product_id=product_id)
            raise HTTPException(status_code=500, detail=str(e))

    async def approve_review(
        self,
        review_id: UUID = Path(..., description="Review ID"),
        approved_by: str = Body(..., description="User approving the review"),
    ) -> ProductReview:
        """
        Approve a review for public display.

        Args:
            review_id (UUID): Review ID.
            approved_by (str): User approving the review.

        Returns:
            ProductReview: The approved product review.

        Raises:
            HTTPException: If the review is not found or an error occurs.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.reviews.approve_review(review_id, approved_by)
                await session.commit()
                if not result:
                    raise HTTPException(status_code=404, detail="Review not found")
                return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error("approve_review_failed", error=str(e), review_id=str(review_id))
            raise HTTPException(status_code=500, detail=str(e))

    async def add_review_vote(
        self,
        review_id: UUID = Path(..., description="Review ID"),
        vote: ReviewVoteCreate = Body(...),
    ) -> ReviewVote:
        """
        Add a helpful/not helpful vote to a review.

        Args:
            review_id (UUID): Review ID.
            vote (ReviewVoteCreate): Vote data.

        Returns:
            ReviewVote: The created review vote.

        Raises:
            HTTPException: If an error occurs during vote addition.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            vote.review_id = review_id
            async with self.db_manager.get_session() as session:
                result = await self.product_service.reviews.add_review_vote(vote)
                await session.commit()
                return result
        except Exception as e:
            logger.error("add_review_vote_failed", error=str(e), review_id=str(review_id))
            raise HTTPException(status_code=500, detail=str(e))

    async def add_seller_response(
        self,
        review_id: UUID = Path(..., description="Review ID"),
        response: ReviewResponseCreate = Body(...),
    ) -> ReviewResponse:
        """
        Add a seller response to a review.

        Args:
            review_id (UUID): Review ID.
            response (ReviewResponseCreate): Response data.

        Returns:
            ReviewResponse: The created seller response.

        Raises:
            HTTPException: If an error occurs during response addition.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.reviews.add_seller_response(review_id, response)
                await session.commit()
                return result
        except Exception as e:
            logger.error("add_seller_response_failed", error=str(e), review_id=str(review_id))
            raise HTTPException(status_code=500, detail=str(e))

    # =====================================================
    # 8. PRODUCT INVENTORY ENDPOINTS
    # =====================================================

    async def create_inventory(
        self,
        inventory: ProductInventoryCreate = Body(...),
    ) -> ProductInventory:
        """
        Create inventory record for a product at a location.

        Args:
            inventory (ProductInventoryCreate): Inventory data.

        Returns:
            ProductInventory: The created inventory record.

        Raises:
            HTTPException: If an error occurs during creation.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.inventory.create_inventory(inventory)
                await session.commit()
                return result
        except Exception as e:
            logger.error("create_inventory_failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    async def get_product_inventory(
        self,
        product_id: str = Path(..., description="Product ID"),
        location_id: str = Query(..., description="Location ID"),
    ) -> ProductInventory:
        """
        Get inventory for a product at a location.

        Args:
            product_id (str): Product ID.
            location_id (str): Location ID.

        Returns:
            ProductInventory: The product inventory record.

        Raises:
            HTTPException: If the inventory is not found or an error occurs.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.inventory.repo.get_inventory(product_id, location_id)
                if not result:
                    raise HTTPException(status_code=404, detail="Inventory not found")
                return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error("get_inventory_failed", error=str(e), product_id=product_id)
            raise HTTPException(status_code=500, detail=str(e))

    async def adjust_inventory(
        self,
        product_id: str = Body(..., description="Product ID"),
        location_id: str = Body(..., description="Location ID"),
        quantity: int = Body(..., description="Quantity to adjust"),
        transaction_type: InventoryTransactionType = Body(..., description="Transaction type"),
        reference_id: Optional[str] = Body(None, description="Reference ID"),
        reference_type: Optional[str] = Body(None, description="Reference type"),
        notes: Optional[str] = Body(None, description="Notes"),
        created_by: str = Body("system", description="User making adjustment"),
    ) -> InventoryTransaction:
        """
        Adjust inventory levels and record transaction.

        Args:
            product_id (str): Product ID.
            location_id (str): Location ID.
            quantity (int): Quantity to adjust (positive for increase, negative for decrease).
            transaction_type (InventoryTransactionType): Type of transaction.
            reference_id (Optional[str]): Optional reference ID (order, shipment, etc.).
            reference_type (Optional[str]): Optional reference type.
            notes (Optional[str]): Optional notes.
            created_by (str): User/system making the adjustment.

        Returns:
            InventoryTransaction: The recorded inventory transaction.

        Raises:
            HTTPException: If an error occurs during adjustment.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.inventory.adjust_inventory(
                    product_id, location_id, quantity, transaction_type,
                    reference_id, reference_type, notes, created_by
                )
                await session.commit()
                return result
        except Exception as e:
            logger.error("adjust_inventory_failed", error=str(e), product_id=product_id)
            raise HTTPException(status_code=500, detail=str(e))

    async def reserve_inventory(
        self,
        product_id: str = Body(..., description="Product ID"),
        location_id: str = Body(..., description="Location ID"),
        order_id: str = Body(..., description="Order ID"),
        quantity: int = Body(..., description="Quantity to reserve"),
        reserved_until: datetime = Body(..., description="Reservation expiry"),
    ) -> InventoryReservation:
        """
        Reserve inventory for an order.

        Args:
            product_id (str): Product ID.
            location_id (str): Location ID.
            order_id (str): Order ID.
            quantity (int): Quantity to reserve.
            reserved_until (datetime): Reservation expiry datetime.

        Returns:
            InventoryReservation: The created inventory reservation.

        Raises:
            HTTPException: If an error occurs during reservation.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.inventory.reserve_inventory(
                    product_id, location_id, order_id, quantity, reserved_until
                )
                await session.commit()
                return result
        except Exception as e:
            logger.error("reserve_inventory_failed", error=str(e), product_id=product_id)
            raise HTTPException(status_code=500, detail=str(e))

    async def check_availability(
        self,
        product_id: str = Path(..., description="Product ID"),
        quantity: int = Query(..., description="Quantity needed"),
        location_id: Optional[str] = Query(None, description="Location ID"),
    ) -> Dict[str, Any]:
        """
        Check if sufficient inventory is available.

        Args:
            product_id (str): Product ID.
            quantity (int): Quantity needed.
            location_id (Optional[str]): Optional location ID (checks all locations if not provided).

        Returns:
            Dict[str, Any]: A dictionary indicating availability status.

        Raises:
            HTTPException: If an error occurs during availability check.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.inventory.check_availability(product_id, quantity, location_id)
                return result
        except Exception as e:
            logger.error("check_availability_failed", error=str(e), product_id=product_id)
            raise HTTPException(status_code=500, detail=str(e))

    async def get_low_stock_products(
        self,
        location_id: Optional[str] = Query(None, description="Location ID"),
    ) -> List[ProductInventory]:
        """
        Get products that are below their reorder point.

        Args:
            location_id (Optional[str]): Location ID.

        Returns:
            List[ProductInventory]: A list of low-stock product inventory records.

        Raises:
            HTTPException: If an error occurs during retrieval.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.inventory.get_low_stock_products(location_id)
                return result
        except Exception as e:
            logger.error("get_low_stock_failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    # =====================================================
    # 9. PRODUCT RELATIONSHIP ENDPOINTS
    # =====================================================

    async def create_product_relationship(
        self,
        relationship: ProductRelationshipCreate = Body(...),
    ) -> ProductRelationship:
        """
        Create a product relationship (related, cross-sell, up-sell, etc.).

        Args:
            relationship (ProductRelationshipCreate): Relationship data.

        Returns:
            ProductRelationship: The created product relationship.

        Raises:
            HTTPException: If an error occurs during creation.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.relationships.create_relationship(relationship)
                await session.commit()
                return result
        except Exception as e:
            logger.error("create_relationship_failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    async def get_related_products(
        self,
        product_id: str = Path(..., description="Product ID"),
        relationship_type: Optional[ProductRelationshipType] = Query(None, description="Relationship type"),
    ) -> List[ProductRelationship]:
        """
        Get related products.

        Args:
            product_id (str): Product ID.
            relationship_type (Optional[ProductRelationshipType]): Optional filter by relationship type.

        Returns:
            List[ProductRelationship]: A list of related products.

        Raises:
            HTTPException: If an error occurs during retrieval.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.relationships.get_related_products(product_id, relationship_type)
                return result
        except Exception as e:
            logger.error("get_related_products_failed", error=str(e), product_id=product_id)
            raise HTTPException(status_code=500, detail=str(e))

    async def generate_recommendations(
        self,
        product_id: str = Path(..., description="Product ID"),
        request: GenerateRecommendationsRequest = Body(...),
    ) -> List[ProductRecommendation]:
        """
        Generate AI-powered product recommendations.

        Args:
            product_id (str): Product ID.
            request (GenerateRecommendationsRequest): Recommendation request parameters.

        Returns:
            List[ProductRecommendation]: A list of generated product recommendations.

        Raises:
            HTTPException: If an error occurs during recommendation generation.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            request.product_id = product_id
            async with self.db_manager.get_session() as session:
                result = await self.product_service.relationships.generate_recommendations(request)
                await session.commit()
                return result
        except Exception as e:
            logger.error("generate_recommendations_failed", error=str(e), product_id=product_id)
            raise HTTPException(status_code=500, detail=str(e))

    async def create_recommendation(
        self,
        recommendation: ProductRecommendationCreate = Body(...),
    ) -> ProductRecommendation:
        """
        Create a product recommendation.

        Args:
            recommendation (ProductRecommendationCreate): Recommendation data.

        Returns:
            ProductRecommendation: The created product recommendation.

        Raises:
            HTTPException: If an error occurs during creation.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.relationships.create_recommendation(recommendation)
                await session.commit()
                return result
        except Exception as e:
            logger.error("create_recommendation_failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    # =====================================================
    # 10. PRODUCT LIFECYCLE ENDPOINTS
    # =====================================================

    async def create_lifecycle(
        self,
        product_id: str = Path(..., description="Product ID"),
        lifecycle: ProductLifecycleCreate = Body(...),
    ) -> ProductLifecycle:
        """
        Create a product lifecycle record.

        Args:
            product_id (str): Product ID.
            lifecycle (ProductLifecycleCreate): Lifecycle data.

        Returns:
            ProductLifecycle: The created product lifecycle record.

        Raises:
            HTTPException: If an error occurs during creation.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            lifecycle.product_id = product_id
            async with self.db_manager.get_session() as session:
                result = await self.product_service.lifecycle.create_lifecycle(lifecycle)
                await session.commit()
                return result
        except Exception as e:
            logger.error("create_lifecycle_failed", error=str(e), product_id=product_id)
            raise HTTPException(status_code=500, detail=str(e))

    async def update_product_status(
        self,
        product_id: str = Path(..., description="Product ID"),
        new_status: ProductStatus = Body(..., description="New status"),
        reason: str = Body(..., description="Reason for status change"),
        changed_by: str = Body(..., description="User making the change"),
    ) -> ProductLifecycle:
        """
        Update product status.

        Args:
            product_id (str): Product ID.
            new_status (ProductStatus): New status.
            reason (str): Reason for status change.
            changed_by (str): User making the change.

        Returns:
            ProductLifecycle: The updated product lifecycle record.

        Raises:
            HTTPException: If an error occurs during status update.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.lifecycle.update_status(product_id, new_status, reason, changed_by)
                await session.commit()
                return result
        except Exception as e:
            logger.error("update_status_failed", error=str(e), product_id=product_id)
            raise HTTPException(status_code=500, detail=str(e))

    async def create_version_snapshot(
        self,
        product_id: str = Path(..., description="Product ID"),
        version_number: str = Body(..., description="Version number"),
        product_data: Dict[str, Any] = Body(..., description="Product data snapshot"),
        change_summary: str = Body(..., description="Change summary"),
        created_by: str = Body(..., description="User creating the version"),
    ) -> ProductVersion:
        """
        Create a version snapshot of a product.

        Args:
            product_id (str): Product ID.
            version_number (str): Version number.
            product_data (Dict[str, Any]): Product data snapshot.
            change_summary (str): Change summary.
            created_by (str): User creating the version.

        Returns:
            ProductVersion: The created product version snapshot.

        Raises:
            HTTPException: If an error occurs during snapshot creation.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.lifecycle.create_version_snapshot(
                    product_id, version_number, product_data, change_summary, created_by
                )
                await session.commit()
                return result
        except Exception as e:
            logger.error("create_version_snapshot_failed", error=str(e), product_id=product_id)
            raise HTTPException(status_code=500, detail=str(e))

    async def record_product_change(
        self,
        product_id: str = Path(..., description="Product ID"),
        field_name: str = Body(..., description="Field name"),
        old_value: Any = Body(..., description="Old value"),
        new_value: Any = Body(..., description="New value"),
        change_type: str = Body(..., description="Change type"),
        changed_by: str = Body(..., description="User making the change"),
        reason: Optional[str] = Body(None, description="Reason for change"),
    ) -> ProductChange:
        """
        Record a product change.

        Args:
            product_id (str): Product ID.
            field_name (str): Field name.
            old_value (Any): Old value.
            new_value (Any): New value.
            change_type (str): Change type.
            changed_by (str): User making the change.
            reason (Optional[str]): Reason for change.

        Returns:
            ProductChange: The recorded product change.

        Raises:
            HTTPException: If an error occurs during change recording.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.lifecycle.record_change(
                    product_id, field_name, old_value, new_value, change_type, changed_by, reason
                )
                await session.commit()
                return result
        except Exception as e:
            logger.error("record_change_failed", error=str(e), product_id=product_id)
            raise HTTPException(status_code=500, detail=str(e))

    async def request_approval(
        self,
        product_id: str = Path(..., description="Product ID"),
        approval_type: ApprovalType = Body(..., description="Approval type"),
        requested_by: str = Body(..., description="User requesting approval"),
        approval_data: Optional[Dict[str, Any]] = Body(None, description="Approval data"),
    ) -> ProductApproval:
        """
        Request approval for a product change.

        Args:
            product_id (str): Product ID.
            approval_type (ApprovalType): Approval type.
            requested_by (str): User requesting approval.
            approval_data (Optional[Dict[str, Any]]): Approval data.

        Returns:
            ProductApproval: The created product approval request.

        Raises:
            HTTPException: If an error occurs during approval request.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.lifecycle.request_approval(
                    product_id, approval_type, requested_by, approval_data
                )
                await session.commit()
                return result
        except Exception as e:
            logger.error("request_approval_failed", error=str(e), product_id=product_id)
            raise HTTPException(status_code=500, detail=str(e))

    async def review_approval(
        self,
        approval_id: UUID = Path(..., description="Approval ID"),
        review: ProductApprovalReview = Body(...),
    ) -> ProductApproval:
        """
        Review an approval request.

        Args:
            approval_id (UUID): Approval ID.
            review (ProductApprovalReview): Review data.

        Returns:
            ProductApproval: The updated product approval.

        Raises:
            HTTPException: If the approval is not found or an error occurs.
        """
        if not self._db_initialized:
            raise HTTPException(status_code=503, detail="Database not initialized")
        try:
            async with self.db_manager.get_session() as session:
                result = await self.product_service.lifecycle.review_approval(approval_id, review)
                await session.commit()
                if not result:
                    raise HTTPException(status_code=404, detail="Approval not found")
                return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error("review_approval_failed", error=str(e), approval_id=str(approval_id))
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/testdb")
    AGENT_ID = os.getenv("AGENT_ID", "product_agent_1")
    AGENT_TYPE = os.getenv("AGENT_TYPE", "ProductAgent")
    UVICORN_HOST = os.getenv("UVICORN_HOST", "0.0.0.0")
    UVICORN_PORT = int(os.getenv("UVICORN_PORT", 8000))

    db_manager = DatabaseManager(DATABASE_URL)
    db_helper = DatabaseHelper(db_manager)

    product_agent = ProductAgent(AGENT_ID, AGENT_TYPE, db_manager, db_helper)

    @product_agent.app.on_event("startup")
    async def on_startup():
        await product_agent.startup()

    uvicorn.run(product_agent.app, host=UVICORN_HOST, port=UVICORN_PORT)

