"""
Product Agent API Endpoints

This module provides FastAPI endpoints for all Product Agent operations.
Implements RESTful API with proper error handling and validation.

Author: Multi-Agent E-Commerce System
Date: January 2025
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from shared.database import DatabaseManager, get_db_manager
from shared.kafka_client import KafkaClient, get_kafka_client
from shared.product_models import *
from services.product_services import (
    ProductVariantService,
    ProductBundleService,
    ProductMediaService,
    ProductCategoryService,
    ProductAttributeService,
    ProductPricingService,
    ProductReviewService,
    ProductInventoryService,
    ProductRelationshipService,
    ProductLifecycleService
)

logger = logging.getLogger(__name__)

# Create routers
variant_router = APIRouter(prefix="/api/products/variants", tags=["Product Variants"])
bundle_router = APIRouter(prefix="/api/products/bundles", tags=["Product Bundles"])
media_router = APIRouter(prefix="/api/products/media", tags=["Product Media"])
category_router = APIRouter(prefix="/api/products/categories", tags=["Product Categories"])
attribute_router = APIRouter(prefix="/api/products/attributes", tags=["Product Attributes"])
pricing_router = APIRouter(prefix="/api/products/pricing", tags=["Product Pricing"])
review_router = APIRouter(prefix="/api/products/reviews", tags=["Product Reviews"])
inventory_router = APIRouter(prefix="/api/products/inventory", tags=["Product Inventory"])
relationship_router = APIRouter(prefix="/api/products/relationships", tags=["Product Relationships"])
lifecycle_router = APIRouter(prefix="/api/products/lifecycle", tags=["Product Lifecycle"])


# =====================================================
# PRODUCT VARIANT ENDPOINTS
# =====================================================

@variant_router.post("/attributes", response_model=VariantAttribute)
async def create_variant_attribute(
    attribute: VariantAttributeCreate,
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Create a new variant attribute (e.g., Size, Color)."""
    try:
        service = ProductVariantService(db, kafka)
        return await service.create_variant_attribute(attribute)
    except Exception as e:
        logger.error(f"Error creating variant attribute: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@variant_router.get("/attributes", response_model=List[VariantAttribute])
async def get_variant_attributes(
    attribute_type: Optional[str] = Query(None),
    is_required: Optional[bool] = Query(None),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Get all variant attributes with optional filters."""
    try:
        service = ProductVariantService(db, kafka)
        filters = VariantAttributeFilter(
            attribute_type=attribute_type,
            is_required=is_required
        )
        return await service.repo.get_variant_attributes(filters)
    except Exception as e:
        logger.error(f"Error getting variant attributes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@variant_router.post("/", response_model=Dict[str, Any])
async def create_product_variant(
    variant: ProductVariantCreate,
    attribute_values: List[VariantAttributeValueCreate] = Body(...),
    pricing: Optional[VariantPricingCreate] = Body(None),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Create a product variant with attributes and pricing."""
    try:
        service = ProductVariantService(db, kafka)
        return await service.create_product_variant(variant, attribute_values, pricing)
    except Exception as e:
        logger.error(f"Error creating product variant: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@variant_router.get("/{product_id}", response_model=List[Dict[str, Any]])
async def get_product_variants(
    product_id: str = Path(..., description="Product ID"),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Get all variants for a product with full details."""
    try:
        service = ProductVariantService(db, kafka)
        return await service.get_product_variants_with_details(product_id)
    except Exception as e:
        logger.error(f"Error getting product variants: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@variant_router.put("/{variant_id}/pricing", response_model=VariantPricing)
async def update_variant_pricing(
    variant_id: UUID = Path(..., description="Variant ID"),
    pricing: VariantPricingCreate = Body(...),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Update pricing for a variant."""
    try:
        service = ProductVariantService(db, kafka)
        return await service.update_variant_pricing(variant_id, pricing)
    except Exception as e:
        logger.error(f"Error updating variant pricing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# PRODUCT BUNDLE ENDPOINTS
# =====================================================

@bundle_router.post("/", response_model=Dict[str, Any])
async def create_bundle(
    bundle: ProductBundleCreate,
    components: List[BundleComponentCreate] = Body(...),
    pricing_rule: BundlePricingRuleCreate = Body(...),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Create a product bundle with components and pricing."""
    try:
        service = ProductBundleService(db, kafka)
        return await service.create_bundle(bundle, components, pricing_rule)
    except Exception as e:
        logger.error(f"Error creating bundle: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@bundle_router.get("/", response_model=List[ProductBundle])
async def get_active_bundles(
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Get all active bundles."""
    try:
        service = ProductBundleService(db, kafka)
        return await service.repo.get_active_bundles()
    except Exception as e:
        logger.error(f"Error getting active bundles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@bundle_router.get("/{bundle_id}/components", response_model=List[BundleComponent])
async def get_bundle_components(
    bundle_id: UUID = Path(..., description="Bundle ID"),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Get all components of a bundle."""
    try:
        service = ProductBundleService(db, kafka)
        return await service.repo.get_bundle_components(bundle_id)
    except Exception as e:
        logger.error(f"Error getting bundle components: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@bundle_router.get("/{bundle_id}/price", response_model=Dict[str, Any])
async def calculate_bundle_price(
    bundle_id: UUID = Path(..., description="Bundle ID"),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Calculate effective price for a bundle."""
    try:
        service = ProductBundleService(db, kafka)
        return await service.calculate_bundle_price(bundle_id)
    except Exception as e:
        logger.error(f"Error calculating bundle price: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# PRODUCT MEDIA ENDPOINTS
# =====================================================

@media_router.post("/images", response_model=ProductImage)
async def add_product_image(
    image: ProductImageCreate,
    set_as_primary: bool = Query(False),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Add an image to a product."""
    try:
        service = ProductMediaService(db, kafka)
        return await service.add_product_image(image, set_as_primary)
    except Exception as e:
        logger.error(f"Error adding product image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@media_router.get("/images/{product_id}", response_model=List[ProductImage])
async def get_product_images(
    product_id: str = Path(..., description="Product ID"),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Get all images for a product."""
    try:
        service = ProductMediaService(db, kafka)
        return await service.repo.get_product_images(product_id)
    except Exception as e:
        logger.error(f"Error getting product images: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@media_router.put("/images/{product_id}/primary/{image_id}")
async def set_primary_image(
    product_id: str = Path(..., description="Product ID"),
    image_id: UUID = Path(..., description="Image ID"),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Set an image as primary for a product."""
    try:
        service = ProductMediaService(db, kafka)
        result = await service.set_primary_image(product_id, image_id)
        if not result:
            raise HTTPException(status_code=404, detail="Image not found")
        return {"success": True, "message": "Primary image updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting primary image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@media_router.post("/media", response_model=ProductMedia)
async def add_product_media(
    media: ProductMediaCreate,
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Add media (video, 360, PDF) to a product."""
    try:
        service = ProductMediaService(db, kafka)
        return await service.add_product_media(media)
    except Exception as e:
        logger.error(f"Error adding product media: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@media_router.get("/media/{product_id}", response_model=List[ProductMedia])
async def get_product_media(
    product_id: str = Path(..., description="Product ID"),
    media_type: Optional[str] = Query(None),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Get media for a product, optionally filtered by type."""
    try:
        service = ProductMediaService(db, kafka)
        return await service.repo.get_product_media(product_id, media_type)
    except Exception as e:
        logger.error(f"Error getting product media: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@media_router.get("/gallery/{product_id}", response_model=Dict[str, Any])
async def get_product_gallery(
    product_id: str = Path(..., description="Product ID"),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Get complete media gallery for a product."""
    try:
        service = ProductMediaService(db, kafka)
        return await service.get_product_gallery(product_id)
    except Exception as e:
        logger.error(f"Error getting product gallery: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# PRODUCT CATEGORY ENDPOINTS
# =====================================================

@category_router.post("/", response_model=ProductCategory)
async def create_category(
    category: ProductCategoryCreate,
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Create a new product category."""
    try:
        service = ProductCategoryService(db, kafka)
        return await service.create_category(category)
    except Exception as e:
        logger.error(f"Error creating category: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@category_router.get("/tree", response_model=List[Dict[str, Any]])
async def get_category_tree(
    parent_id: Optional[int] = Query(None),
    max_depth: int = Query(3, ge=1, le=10),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Get category tree with nested children."""
    try:
        service = ProductCategoryService(db, kafka)
        return await service.get_category_tree(parent_id, max_depth)
    except Exception as e:
        logger.error(f"Error getting category tree: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@category_router.post("/{product_id}/assign", response_model=List[ProductCategoryMapping])
async def assign_product_to_categories(
    product_id: str = Path(..., description="Product ID"),
    category_ids: List[int] = Body(...),
    primary_category_id: int = Body(...),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Assign a product to multiple categories."""
    try:
        service = ProductCategoryService(db, kafka)
        return await service.assign_product_to_categories(
            product_id,
            category_ids,
            primary_category_id
        )
    except Exception as e:
        logger.error(f"Error assigning product to categories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@category_router.get("/{product_id}", response_model=List[ProductCategory])
async def get_product_categories(
    product_id: str = Path(..., description="Product ID"),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Get all categories for a product."""
    try:
        service = ProductCategoryService(db, kafka)
        return await service.repo.get_product_categories(product_id)
    except Exception as e:
        logger.error(f"Error getting product categories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Continue in next part...




# =====================================================
# PRODUCT ATTRIBUTE ENDPOINTS
# =====================================================

@attribute_router.post("/groups", response_model=AttributeGroup)
async def create_attribute_group(
    group: AttributeGroupCreate,
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Create an attribute group."""
    try:
        service = ProductAttributeService(db, kafka)
        return await service.create_attribute_group(group)
    except Exception as e:
        logger.error(f"Error creating attribute group: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@attribute_router.post("/", response_model=ProductAttribute)
async def create_product_attribute(
    attribute: ProductAttributeCreate,
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Create a product attribute."""
    try:
        service = ProductAttributeService(db, kafka)
        return await service.create_product_attribute(attribute)
    except Exception as e:
        logger.error(f"Error creating product attribute: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@attribute_router.post("/{product_id}/values", response_model=List[ProductAttributeValue])
async def set_product_attributes(
    product_id: str = Path(..., description="Product ID"),
    attributes: List[ProductAttributeValueCreate] = Body(...),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Set multiple attributes for a product."""
    try:
        service = ProductAttributeService(db, kafka)
        return await service.set_product_attributes(product_id, attributes)
    except Exception as e:
        logger.error(f"Error setting product attributes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@attribute_router.get("/{product_id}/specifications", response_model=Dict[str, List[Dict[str, Any]]])
async def get_product_specifications(
    product_id: str = Path(..., description="Product ID"),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Get product specifications grouped by attribute group."""
    try:
        service = ProductAttributeService(db, kafka)
        return await service.get_product_specifications(product_id)
    except Exception as e:
        logger.error(f"Error getting product specifications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# PRODUCT PRICING ENDPOINTS
# =====================================================

@pricing_router.post("/rules", response_model=Dict[str, Any])
async def create_pricing_rule(
    rule: PricingRuleCreate,
    tiers: Optional[List[PricingTierCreate]] = Body(None),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Create a pricing rule with optional tiers."""
    try:
        service = ProductPricingService(db, kafka)
        return await service.create_pricing_rule(rule, tiers)
    except Exception as e:
        logger.error(f"Error creating pricing rule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@pricing_router.put("/{product_id}/price", response_model=PriceHistory)
async def update_product_price(
    product_id: str = Path(..., description="Product ID"),
    old_price: float = Body(...),
    new_price: float = Body(...),
    change_reason: str = Body(...),
    changed_by: str = Body(...),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Update product price and record in history."""
    try:
        from decimal import Decimal
        service = ProductPricingService(db, kafka)
        return await service.update_product_price(
            product_id,
            Decimal(str(old_price)),
            Decimal(str(new_price)),
            change_reason,
            changed_by
        )
    except Exception as e:
        logger.error(f"Error updating product price: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@pricing_router.post("/{product_id}/competitor-prices", response_model=List[CompetitorPrice])
async def track_competitor_prices(
    product_id: str = Path(..., description="Product ID"),
    competitor_prices: List[CompetitorPriceCreate] = Body(...),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Track competitor prices for a product."""
    try:
        service = ProductPricingService(db, kafka)
        return await service.track_competitor_prices(product_id, competitor_prices)
    except Exception as e:
        logger.error(f"Error tracking competitor prices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@pricing_router.get("/{product_id}/effective-price", response_model=Dict[str, Any])
async def calculate_effective_price(
    product_id: str = Path(..., description="Product ID"),
    quantity: int = Query(1, ge=1),
    customer_id: Optional[str] = Query(None),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Calculate effective price based on active rules."""
    try:
        service = ProductPricingService(db, kafka)
        return await service.calculate_effective_price(product_id, quantity, customer_id)
    except Exception as e:
        logger.error(f"Error calculating effective price: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@pricing_router.get("/{product_id}/rules", response_model=List[PricingRule])
async def get_active_pricing_rules(
    product_id: str = Path(..., description="Product ID"),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Get active pricing rules for a product."""
    try:
        service = ProductPricingService(db, kafka)
        return await service.repo.get_active_pricing_rules(product_id)
    except Exception as e:
        logger.error(f"Error getting pricing rules: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# PRODUCT REVIEW ENDPOINTS
# =====================================================

@review_router.post("/", response_model=Dict[str, Any])
async def create_review(
    review: ProductReviewCreate,
    images: Optional[List[ReviewImageCreate]] = Body(None),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Create a product review with optional images."""
    try:
        service = ProductReviewService(db, kafka)
        return await service.create_review(review, images)
    except Exception as e:
        logger.error(f"Error creating review: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@review_router.put("/{review_id}/moderate")
async def moderate_review(
    review_id: UUID = Path(..., description="Review ID"),
    approved: bool = Body(...),
    approved_by: str = Body(...),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Moderate (approve/reject) a review."""
    try:
        service = ProductReviewService(db, kafka)
        result = await service.moderate_review(review_id, approved, approved_by)
        if not result:
            raise HTTPException(status_code=404, detail="Review not found")
        return {"success": True, "approved": approved}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moderating review: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@review_router.post("/{review_id}/vote", response_model=ReviewVote)
async def vote_on_review(
    review_id: UUID = Path(..., description="Review ID"),
    customer_id: str = Body(...),
    helpful: bool = Body(...),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Vote on a review as helpful or not helpful."""
    try:
        service = ProductReviewService(db, kafka)
        return await service.vote_on_review(review_id, customer_id, helpful)
    except Exception as e:
        logger.error(f"Error voting on review: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@review_router.post("/{review_id}/response", response_model=ReviewResponse)
async def add_seller_response(
    review_id: UUID = Path(..., description="Review ID"),
    response_text: str = Body(...),
    responded_by: str = Body(...),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Add seller response to a review."""
    try:
        service = ProductReviewService(db, kafka)
        return await service.add_seller_response(review_id, response_text, responded_by)
    except Exception as e:
        logger.error(f"Error adding seller response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@review_router.get("/{product_id}", response_model=List[ProductReview])
async def get_product_reviews(
    product_id: str = Path(..., description="Product ID"),
    approved_only: bool = Query(True),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Get reviews for a product."""
    try:
        service = ProductReviewService(db, kafka)
        return await service.repo.get_product_reviews(product_id, approved_only, limit, offset)
    except Exception as e:
        logger.error(f"Error getting product reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@review_router.get("/{product_id}/summary", response_model=Dict[str, Any])
async def get_product_review_summary(
    product_id: str = Path(..., description="Product ID"),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Get review summary for a product."""
    try:
        service = ProductReviewService(db, kafka)
        return await service.get_product_review_summary(product_id)
    except Exception as e:
        logger.error(f"Error getting review summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# PRODUCT INVENTORY ENDPOINTS
# =====================================================

@inventory_router.post("/", response_model=ProductInventory)
async def create_inventory(
    inventory: ProductInventoryCreate,
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Create inventory record for a product at a location."""
    try:
        service = ProductInventoryService(db, kafka)
        return await service.create_inventory(inventory)
    except Exception as e:
        logger.error(f"Error creating inventory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@inventory_router.post("/transactions", response_model=InventoryTransaction)
async def record_inventory_transaction(
    transaction: InventoryTransactionCreate,
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Record an inventory transaction."""
    try:
        service = ProductInventoryService(db, kafka)
        return await service.record_inventory_transaction(transaction)
    except Exception as e:
        logger.error(f"Error recording inventory transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@inventory_router.post("/reservations", response_model=InventoryReservation)
async def reserve_inventory(
    product_id: str = Body(...),
    location_id: str = Body(...),
    order_id: str = Body(...),
    quantity: int = Body(..., ge=1),
    reserved_until: datetime = Body(...),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Reserve inventory for an order."""
    try:
        service = ProductInventoryService(db, kafka)
        return await service.reserve_inventory(
            product_id,
            location_id,
            order_id,
            quantity,
            reserved_until
        )
    except Exception as e:
        logger.error(f"Error reserving inventory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@inventory_router.delete("/reservations/{reservation_id}")
async def release_inventory_reservation(
    reservation_id: UUID = Path(..., description="Reservation ID"),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Release an inventory reservation."""
    try:
        service = ProductInventoryService(db, kafka)
        result = await service.release_inventory_reservation(reservation_id)
        if not result:
            raise HTTPException(status_code=404, detail="Reservation not found")
        return {"success": True, "message": "Reservation released"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error releasing reservation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@inventory_router.get("/{product_id}/availability", response_model=Dict[str, Any])
async def check_inventory_availability(
    product_id: str = Path(..., description="Product ID"),
    quantity: int = Query(..., ge=1),
    location_id: Optional[str] = Query(None),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Check if inventory is available for a product."""
    try:
        service = ProductInventoryService(db, kafka)
        return await service.check_inventory_availability(product_id, quantity, location_id)
    except Exception as e:
        logger.error(f"Error checking inventory availability: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@inventory_router.get("/{product_id}/summary", response_model=Dict[str, Any])
async def get_inventory_summary(
    product_id: str = Path(..., description="Product ID"),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Get inventory summary from materialized view."""
    try:
        service = ProductInventoryService(db, kafka)
        result = await service.repo.get_inventory_summary(product_id)
        if not result:
            raise HTTPException(status_code=404, detail="Inventory not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting inventory summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# PRODUCT RELATIONSHIP ENDPOINTS
# =====================================================

@relationship_router.post("/", response_model=ProductRelationship)
async def create_relationship(
    relationship: ProductRelationshipCreate,
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Create a product relationship."""
    try:
        service = ProductRelationshipService(db, kafka)
        return await service.create_relationship(relationship)
    except Exception as e:
        logger.error(f"Error creating product relationship: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@relationship_router.get("/{product_id}", response_model=List[ProductRelationship])
async def get_related_products(
    product_id: str = Path(..., description="Product ID"),
    relationship_type: Optional[str] = Query(None),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Get related products."""
    try:
        service = ProductRelationshipService(db, kafka)
        return await service.get_related_products(product_id, relationship_type)
    except Exception as e:
        logger.error(f"Error getting related products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@relationship_router.post("/recommendations", response_model=ProductRecommendation)
async def create_recommendation(
    recommendation: ProductRecommendationCreate,
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Create a product recommendation."""
    try:
        service = ProductRelationshipService(db, kafka)
        return await service.create_recommendation(recommendation)
    except Exception as e:
        logger.error(f"Error creating recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@relationship_router.get("/{product_id}/recommendations", response_model=List[ProductRecommendation])
async def get_recommendations(
    product_id: str = Path(..., description="Product ID"),
    recommendation_type: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Get product recommendations."""
    try:
        service = ProductRelationshipService(db, kafka)
        return await service.repo.get_recommendations(product_id, recommendation_type, limit)
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@relationship_router.post("/{product_id}/generate-recommendations", response_model=List[ProductRecommendation])
async def generate_recommendations(
    product_id: str = Path(..., description="Product ID"),
    recommendation_type: str = Body("ai_based"),
    limit: int = Body(10, ge=1, le=50),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Generate product recommendations (AI/ML placeholder)."""
    try:
        service = ProductRelationshipService(db, kafka)
        return await service.generate_recommendations(product_id, recommendation_type, limit)
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# PRODUCT LIFECYCLE ENDPOINTS
# =====================================================

@lifecycle_router.put("/{product_id}/status", response_model=ProductLifecycle)
async def update_product_status(
    product_id: str = Path(..., description="Product ID"),
    status: ProductStatus = Body(...),
    status_reason: str = Body(...),
    changed_by: str = Body(...),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Update product lifecycle status."""
    try:
        service = ProductLifecycleService(db, kafka)
        return await service.update_product_status(product_id, status, status_reason, changed_by)
    except Exception as e:
        logger.error(f"Error updating product status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@lifecycle_router.get("/{product_id}/status", response_model=Optional[ProductLifecycle])
async def get_current_lifecycle(
    product_id: str = Path(..., description="Product ID"),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Get current lifecycle status for a product."""
    try:
        service = ProductLifecycleService(db, kafka)
        return await service.repo.get_current_lifecycle(product_id)
    except Exception as e:
        logger.error(f"Error getting current lifecycle: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@lifecycle_router.post("/{product_id}/versions", response_model=ProductVersion)
async def create_product_version(
    product_id: str = Path(..., description="Product ID"),
    version_number: str = Body(...),
    version_data: Dict[str, Any] = Body(...),
    change_summary: str = Body(...),
    created_by: str = Body(...),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Create a product version snapshot."""
    try:
        service = ProductLifecycleService(db, kafka)
        return await service.create_product_version(
            product_id,
            version_number,
            version_data,
            change_summary,
            created_by
        )
    except Exception as e:
        logger.error(f"Error creating product version: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@lifecycle_router.post("/{product_id}/changes", response_model=ProductChange)
async def record_product_change(
    product_id: str = Path(..., description="Product ID"),
    field_name: str = Body(...),
    old_value: Optional[str] = Body(None),
    new_value: str = Body(...),
    change_type: str = Body(...),
    changed_by: str = Body(...),
    change_reason: Optional[str] = Body(None),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Record a product change."""
    try:
        service = ProductLifecycleService(db, kafka)
        return await service.record_product_change(
            product_id,
            field_name,
            old_value,
            new_value,
            change_type,
            changed_by,
            change_reason
        )
    except Exception as e:
        logger.error(f"Error recording product change: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@lifecycle_router.post("/approvals", response_model=ProductApproval)
async def request_approval(
    product_id: str = Body(...),
    approval_type: str = Body(...),
    requested_by: str = Body(...),
    approval_data: Dict[str, Any] = Body(...),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Request approval for product changes."""
    try:
        service = ProductLifecycleService(db, kafka)
        return await service.request_approval(
            product_id,
            approval_type,
            requested_by,
            approval_data
        )
    except Exception as e:
        logger.error(f"Error requesting approval: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@lifecycle_router.put("/approvals/{approval_id}/review")
async def review_approval(
    approval_id: UUID = Path(..., description="Approval ID"),
    approved: bool = Body(...),
    reviewed_by: str = Body(...),
    review_notes: Optional[str] = Body(None),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Review an approval request."""
    try:
        service = ProductLifecycleService(db, kafka)
        result = await service.review_approval(approval_id, approved, reviewed_by, review_notes)
        if not result:
            raise HTTPException(status_code=404, detail="Approval not found")
        return {"success": True, "approved": approved}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reviewing approval: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@lifecycle_router.get("/approvals/pending", response_model=List[ProductApproval])
async def get_pending_approvals(
    product_id: Optional[str] = Query(None),
    db: DatabaseManager = Depends(get_db_manager),
    kafka: KafkaClient = Depends(get_kafka_client)
):
    """Get pending approval requests."""
    try:
        service = ProductLifecycleService(db, kafka)
        return await service.repo.get_pending_approvals(product_id)
    except Exception as e:
        logger.error(f"Error getting pending approvals: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# EXPORT ALL ROUTERS
# =====================================================

all_routers = [
    variant_router,
    bundle_router,
    media_router,
    category_router,
    attribute_router,
    pricing_router,
    review_router,
    inventory_router,
    relationship_router,
    lifecycle_router
]

