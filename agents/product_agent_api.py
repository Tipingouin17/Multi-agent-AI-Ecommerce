"""
Product Agent API - Multi-Agent E-commerce System

This agent provides comprehensive product management APIs including variants,
bundles, media, categories, attributes, pricing, reviews, inventory, relationships,
and lifecycle management.
"""

import asyncio
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID

from shared.db_helpers import DatabaseHelper

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel
import structlog
import sys
import os

# Path setup
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.database import DatabaseManager, get_database_manager
from shared.product_models import *
from agents.services.product_service import ProductServiceFacade


logger = structlog.get_logger(__name__)


# =====================================================
# FASTAPI APP INITIALIZATION
# =====================================================

app = FastAPI(
    title="Product Agent API",
    description="Comprehensive product management for multi-agent e-commerce",
    version="2.0.0"
)


# =====================================================
# DEPENDENCY INJECTION
# =====================================================

async def get_product_services() -> ProductServiceFacade:
    """Dependency injection for product services."""
    db_manager = await get_database_manager()
    return ProductServiceFacade(db_manager)


# =====================================================
# 1. PRODUCT VARIANT ENDPOINTS
# =====================================================

@app.post("/api/v1/products/{product_id}/variants", response_model=ProductVariant)
async def create_product_variant(
    product_id: str = Path(..., description="Product ID"),
    variant: ProductVariantCreate = Body(...),
    attribute_values: List[VariantAttributeValueCreate] = Body([]),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """
    Create a new product variant with attribute values.
    
    - **product_id**: ID of the parent product
    - **variant**: Variant data
    - **attribute_values**: List of attribute values (e.g., size, color)
    """
    try:
        variant.product_id = product_id
        result = await services.variants.create_variant(variant, attribute_values)
        return result
    except Exception as e:
        logger.error("create_variant_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/products/{product_id}/variants", response_model=List[ProductVariant])
async def get_product_variants(
    product_id: str = Path(..., description="Product ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Get all variants for a product."""
    try:
        variants = await services.variants.get_product_variants(product_id)
        return variants
    except Exception as e:
        logger.error("get_variants_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/variants/{variant_id}", response_model=ProductVariant)
async def update_product_variant(
    variant_id: UUID = Path(..., description="Variant ID"),
    update_data: ProductVariantUpdate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Update a product variant."""
    try:
        result = await services.variants.update_variant(variant_id, update_data)
        if not result:
            raise HTTPException(status_code=404, detail="Variant not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_variant_failed", error=str(e), variant_id=str(variant_id))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/variants/{variant_id}/set-master", response_model=ProductVariant)
async def set_master_variant(
    variant_id: UUID = Path(..., description="Variant ID"),
    product_id: str = Query(..., description="Product ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Set a variant as the master variant for a product."""
    try:
        result = await services.variants.set_master_variant(variant_id, product_id)
        return result
    except Exception as e:
        logger.error("set_master_variant_failed", error=str(e), variant_id=str(variant_id))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/variant-attributes", response_model=VariantAttribute)
async def create_variant_attribute(
    attribute: VariantAttributeCreate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Create a new variant attribute definition (e.g., 'Size', 'Color')."""
    try:
        result = await services.variants.repo.create_variant_attribute(attribute)
        return result
    except Exception as e:
        logger.error("create_variant_attribute_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# 2. PRODUCT BUNDLE ENDPOINTS
# =====================================================

@app.post("/api/v1/bundles", response_model=BundleDetails)
async def create_product_bundle(
    bundle: ProductBundleCreate = Body(...),
    components: List[BundleComponentCreate] = Body(...),
    pricing_rules: Optional[List[BundlePricingRuleCreate]] = Body(None),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """
    Create a product bundle with components and pricing rules.
    
    - **bundle**: Bundle data
    - **components**: List of products in the bundle
    - **pricing_rules**: Optional pricing rules
    """
    try:
        result = await services.bundles.create_bundle(bundle, components, pricing_rules)
        return result
    except Exception as e:
        logger.error("create_bundle_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/bundles/{bundle_id}", response_model=BundleDetails)
async def get_bundle_details(
    bundle_id: UUID = Path(..., description="Bundle ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Get complete bundle details including components and pricing."""
    try:
        result = await services.bundles.get_bundle_details(bundle_id)
        if not result:
            raise HTTPException(status_code=404, detail="Bundle not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_bundle_failed", error=str(e), bundle_id=str(bundle_id))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/bundles/{bundle_id}/price", response_model=Dict[str, Decimal])
async def calculate_bundle_price(
    bundle_id: UUID = Path(..., description="Bundle ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Calculate the effective price of a bundle based on its pricing strategy."""
    try:
        price = await services.bundles.calculate_bundle_price(bundle_id)
        return {"bundle_id": str(bundle_id), "calculated_price": price}
    except Exception as e:
        logger.error("calculate_bundle_price_failed", error=str(e), bundle_id=str(bundle_id))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/bundles/{bundle_id}/activate", response_model=ProductBundle)
async def activate_bundle(
    bundle_id: UUID = Path(..., description="Bundle ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Activate a bundle for sale."""
    try:
        result = await services.bundles.activate_bundle(bundle_id)
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

@app.post("/api/v1/products/{product_id}/images", response_model=ProductImage)
async def add_product_image(
    product_id: str = Path(..., description="Product ID"),
    image: ProductImageCreate = Body(...),
    set_as_primary: bool = Query(False, description="Set as primary image"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """
    Add an image to a product.
    
    - **product_id**: Product ID
    - **image**: Image data
    - **set_as_primary**: Whether to set this as the primary image
    """
    try:
        image.product_id = product_id
        result = await services.media.add_product_image(image, set_as_primary)
        return result
    except Exception as e:
        logger.error("add_product_image_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/products/{product_id}/images", response_model=List[ProductImage])
async def get_product_images(
    product_id: str = Path(..., description="Product ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Get all images for a product, ordered by primary first."""
    try:
        images = await services.media.get_product_images(product_id)
        return images
    except Exception as e:
        logger.error("get_product_images_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/images/{image_id}/set-primary", response_model=ProductImage)
async def set_primary_image(
    image_id: UUID = Path(..., description="Image ID"),
    product_id: str = Query(..., description="Product ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Set an image as the primary image for a product."""
    try:
        result = await services.media.set_primary_image(image_id, product_id)
        return result
    except Exception as e:
        logger.error("set_primary_image_failed", error=str(e), image_id=str(image_id))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/products/{product_id}/media", response_model=ProductMedia)
async def add_product_media(
    product_id: str = Path(..., description="Product ID"),
    media: ProductMediaCreate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """
    Add media (video, 360 view, etc.) to a product.
    
    - **product_id**: Product ID
    - **media**: Media data
    """
    try:
        media.product_id = product_id
        result = await services.media.add_product_media(media)
        return result
    except Exception as e:
        logger.error("add_product_media_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/products/{product_id}/media", response_model=List[ProductMedia])
async def get_product_media(
    product_id: str = Path(..., description="Product ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Get all media for a product."""
    try:
        media = await services.media.get_product_media(product_id)
        return media
    except Exception as e:
        logger.error("get_product_media_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# 4. PRODUCT CATEGORY ENDPOINTS
# =====================================================

@app.post("/api/v1/categories", response_model=ProductCategory)
async def create_category(
    category: ProductCategoryCreate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """
    Create a new product category.
    
    - **category**: Category data
    """
    try:
        result = await services.categories.create_category(category)
        return result
    except Exception as e:
        logger.error("create_category_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/categories", response_model=List[ProductCategory])
async def get_categories(
    parent_id: Optional[int] = Query(None, description="Parent category ID (null for root)"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """
    Get categories. Returns root categories if parent_id is null.
    
    - **parent_id**: Parent category ID (null for root categories)
    """
    try:
        categories = await services.categories.get_category_tree(parent_id)
        return categories
    except Exception as e:
        logger.error("get_categories_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/categories/{category_id}", response_model=ProductCategory)
async def get_category(
    category_id: int = Path(..., description="Category ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Get a category by ID."""
    try:
        result = await services.categories.repo.get_category(category_id)
        if not result:
            raise HTTPException(status_code=404, detail="Category not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_category_failed", error=str(e), category_id=category_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/categories/{category_id}/breadcrumb", response_model=List[ProductCategory])
async def get_category_breadcrumb(
    category_id: int = Path(..., description="Category ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Get breadcrumb trail for a category (from root to current)."""
    try:
        breadcrumb = await services.categories.get_category_breadcrumb(category_id)
        return breadcrumb
    except Exception as e:
        logger.error("get_breadcrumb_failed", error=str(e), category_id=category_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/products/{product_id}/categories", response_model=ProductCategoryMapping)
async def add_product_to_category(
    product_id: str = Path(..., description="Product ID"),
    category_id: int = Query(..., description="Category ID"),
    is_primary: bool = Query(False, description="Is primary category"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Add a product to a category."""
    try:
        result = await services.categories.add_product_to_category(
            product_id, category_id, is_primary
        )
        return result
    except Exception as e:
        logger.error("add_product_to_category_failed", error=str(e), 
                    product_id=product_id, category_id=category_id)
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# 5. PRODUCT ATTRIBUTE ENDPOINTS
# =====================================================

@app.post("/api/v1/attribute-groups", response_model=AttributeGroup)
async def create_attribute_group(
    group: AttributeGroupCreate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Create a new attribute group (e.g., 'Technical Specifications')."""
    try:
        result = await services.attributes.create_attribute_group(group)
        return result
    except Exception as e:
        logger.error("create_attribute_group_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/attributes", response_model=ProductAttribute)
async def create_attribute(
    attribute: ProductAttributeCreate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Create a new product attribute (e.g., 'Weight', 'Dimensions')."""
    try:
        result = await services.attributes.create_attribute(attribute)
        return result
    except Exception as e:
        logger.error("create_attribute_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/products/{product_id}/attributes", response_model=List[ProductAttributeValue])
async def set_product_attributes(
    product_id: str = Path(..., description="Product ID"),
    attributes: List[ProductAttributeValueCreate] = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Set multiple attribute values for a product."""
    try:
        result = await services.attributes.set_product_attributes(product_id, attributes)
        return result
    except Exception as e:
        logger.error("set_product_attributes_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/products/{product_id}/attributes", response_model=List[ProductAttributeValue])
async def get_product_attributes(
    product_id: str = Path(..., description="Product ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Get all attribute values for a product."""
    try:
        attributes = await services.attributes.get_product_attributes(product_id)
        return attributes
    except Exception as e:
        logger.error("get_product_attributes_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# HEALTH CHECK
# =====================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "product_agent", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)




# =====================================================
# 6. PRODUCT PRICING ENDPOINTS
# =====================================================

@app.post("/api/v1/pricing-rules", response_model=PricingRule)
async def create_pricing_rule(
    rule: PricingRuleCreate = Body(...),
    tiers: Optional[List[PricingTierCreate]] = Body(None),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """
    Create a pricing rule with optional tiered pricing.
    
    - **rule**: Pricing rule data
    - **tiers**: Optional pricing tiers for volume-based pricing
    """
    try:
        result = await services.pricing.create_pricing_rule(rule, tiers)
        return result
    except Exception as e:
        logger.error("create_pricing_rule_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/products/{product_id}/price", response_model=Dict[str, Any])
async def calculate_product_price(
    product_id: str = Path(..., description="Product ID"),
    quantity: int = Query(1, description="Quantity"),
    customer_id: Optional[str] = Query(None, description="Customer ID for personalized pricing"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """
    Calculate the effective price for a product based on active pricing rules.
    
    - **product_id**: Product ID
    - **quantity**: Quantity being purchased
    - **customer_id**: Optional customer ID for personalized pricing
    """
    try:
        price = await services.pricing.calculate_price(product_id, quantity, customer_id)
        return {
            "product_id": product_id,
            "quantity": quantity,
            "calculated_price": price,
            "total_price": price * quantity
        }
    except Exception as e:
        logger.error("calculate_price_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/products/{product_id}/price", response_model=PriceHistory)
async def update_product_price(
    product_id: str = Path(..., description="Product ID"),
    new_price: Decimal = Body(..., description="New price"),
    reason: str = Body(..., description="Reason for price change"),
    changed_by: str = Body(..., description="User making the change"),
    effective_date: Optional[date] = Body(None, description="Effective date"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """
    Update product price and record in history.
    
    - **product_id**: Product ID
    - **new_price**: New price
    - **reason**: Reason for price change
    - **changed_by**: User making the change
    - **effective_date**: When the price takes effect
    """
    try:
        result = await services.pricing.update_price(
            product_id, new_price, reason, changed_by, effective_date
        )
        return result
    except Exception as e:
        logger.error("update_price_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/pricing/bulk-update", response_model=Dict[str, Any])
async def bulk_update_prices(
    request: BulkPriceUpdateRequest = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """
    Update prices for multiple products.
    
    - **request**: Bulk price update request
    """
    try:
        result = await services.pricing.bulk_update_prices(request)
        return result
    except Exception as e:
        logger.error("bulk_update_prices_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/competitor-prices", response_model=CompetitorPrice)
async def track_competitor_price(
    price: CompetitorPriceCreate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Track a competitor's price for a product."""
    try:
        result = await services.pricing.track_competitor_price(price)
        return result
    except Exception as e:
        logger.error("track_competitor_price_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# 7. PRODUCT REVIEW ENDPOINTS
# =====================================================

@app.post("/api/v1/products/{product_id}/reviews", response_model=ProductReview)
async def create_product_review(
    product_id: str = Path(..., description="Product ID"),
    review: ProductReviewCreate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """
    Create a new product review.
    
    - **product_id**: Product ID
    - **review**: Review data
    """
    try:
        review.product_id = product_id
        result = await services.reviews.create_review(review)
        return result
    except Exception as e:
        logger.error("create_review_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/products/{product_id}/reviews", response_model=List[ProductReview])
async def get_product_reviews(
    product_id: str = Path(..., description="Product ID"),
    approved_only: bool = Query(True, description="Show only approved reviews"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """
    Get all reviews for a product.
    
    - **product_id**: Product ID
    - **approved_only**: Show only approved reviews
    """
    try:
        reviews = await services.reviews.get_product_reviews(product_id, approved_only)
        return reviews
    except Exception as e:
        logger.error("get_reviews_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/products/{product_id}/reviews/summary", response_model=Dict[str, Any])
async def get_review_summary(
    product_id: str = Path(..., description="Product ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """
    Get rating summary statistics for a product.
    
    Returns average rating, total reviews, rating distribution, etc.
    """
    try:
        summary = await services.reviews.calculate_rating_summary(product_id)
        return summary
    except Exception as e:
        logger.error("get_review_summary_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/reviews/{review_id}/approve", response_model=ProductReview)
async def approve_review(
    review_id: UUID = Path(..., description="Review ID"),
    approved_by: str = Body(..., description="User approving the review"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Approve a review for public display."""
    try:
        result = await services.reviews.approve_review(review_id, approved_by)
        if not result:
            raise HTTPException(status_code=404, detail="Review not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("approve_review_failed", error=str(e), review_id=str(review_id))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/reviews/{review_id}/vote", response_model=ReviewVote)
async def add_review_vote(
    review_id: UUID = Path(..., description="Review ID"),
    vote: ReviewVoteCreate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Add a helpful/not helpful vote to a review."""
    try:
        vote.review_id = review_id
        result = await services.reviews.add_review_vote(vote)
        return result
    except Exception as e:
        logger.error("add_review_vote_failed", error=str(e), review_id=str(review_id))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/reviews/{review_id}/response", response_model=ReviewResponse)
async def add_seller_response(
    review_id: UUID = Path(..., description="Review ID"),
    response: ReviewResponseCreate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Add a seller response to a review."""
    try:
        result = await services.reviews.add_seller_response(review_id, response)
        return result
    except Exception as e:
        logger.error("add_seller_response_failed", error=str(e), review_id=str(review_id))
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# 8. PRODUCT INVENTORY ENDPOINTS
# =====================================================

@app.post("/api/v1/inventory", response_model=ProductInventory)
async def create_inventory(
    inventory: ProductInventoryCreate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Create inventory record for a product at a location."""
    try:
        result = await services.inventory.create_inventory(inventory)
        return result
    except Exception as e:
        logger.error("create_inventory_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/products/{product_id}/inventory", response_model=ProductInventory)
async def get_product_inventory(
    product_id: str = Path(..., description="Product ID"),
    location_id: str = Query(..., description="Location ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Get inventory for a product at a location."""
    try:
        result = await services.inventory.repo.get_inventory(product_id, location_id)
        if not result:
            raise HTTPException(status_code=404, detail="Inventory not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_inventory_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/inventory/adjust", response_model=InventoryTransaction)
async def adjust_inventory(
    product_id: str = Body(..., description="Product ID"),
    location_id: str = Body(..., description="Location ID"),
    quantity: int = Body(..., description="Quantity to adjust"),
    transaction_type: InventoryTransactionType = Body(..., description="Transaction type"),
    reference_id: Optional[str] = Body(None, description="Reference ID"),
    reference_type: Optional[str] = Body(None, description="Reference type"),
    notes: Optional[str] = Body(None, description="Notes"),
    created_by: str = Body("system", description="User making adjustment"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """
    Adjust inventory levels and record transaction.
    
    - **product_id**: Product ID
    - **location_id**: Location ID
    - **quantity**: Quantity to adjust (positive for increase, negative for decrease)
    - **transaction_type**: Type of transaction
    - **reference_id**: Optional reference ID (order, shipment, etc.)
    - **reference_type**: Optional reference type
    - **notes**: Optional notes
    - **created_by**: User/system making the adjustment
    """
    try:
        result = await services.inventory.adjust_inventory(
            product_id, location_id, quantity, transaction_type,
            reference_id, reference_type, notes, created_by
        )
        return result
    except Exception as e:
        logger.error("adjust_inventory_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/inventory/reserve", response_model=InventoryReservation)
async def reserve_inventory(
    product_id: str = Body(..., description="Product ID"),
    location_id: str = Body(..., description="Location ID"),
    order_id: str = Body(..., description="Order ID"),
    quantity: int = Body(..., description="Quantity to reserve"),
    reserved_until: datetime = Body(..., description="Reservation expiry"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Reserve inventory for an order."""
    try:
        result = await services.inventory.reserve_inventory(
            product_id, location_id, order_id, quantity, reserved_until
        )
        return result
    except Exception as e:
        logger.error("reserve_inventory_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/products/{product_id}/availability", response_model=Dict[str, Any])
async def check_availability(
    product_id: str = Path(..., description="Product ID"),
    quantity: int = Query(..., description="Quantity needed"),
    location_id: Optional[str] = Query(None, description="Location ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """
    Check if sufficient inventory is available.
    
    - **product_id**: Product ID
    - **quantity**: Quantity needed
    - **location_id**: Optional location ID (checks all locations if not provided)
    """
    try:
        result = await services.inventory.check_availability(product_id, quantity, location_id)
        return result
    except Exception as e:
        logger.error("check_availability_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/inventory/low-stock", response_model=List[ProductInventory])
async def get_low_stock_products(
    location_id: Optional[str] = Query(None, description="Location ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Get products that are below their reorder point."""
    try:
        result = await services.inventory.get_low_stock_products(location_id)
        return result
    except Exception as e:
        logger.error("get_low_stock_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# 9. PRODUCT RELATIONSHIP ENDPOINTS
# =====================================================

@app.post("/api/v1/product-relationships", response_model=ProductRelationship)
async def create_product_relationship(
    relationship: ProductRelationshipCreate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """
    Create a product relationship (related, cross-sell, up-sell, etc.).
    
    - **relationship**: Relationship data
    """
    try:
        result = await services.relationships.create_relationship(relationship)
        return result
    except Exception as e:
        logger.error("create_relationship_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/products/{product_id}/related", response_model=List[ProductRelationship])
async def get_related_products(
    product_id: str = Path(..., description="Product ID"),
    relationship_type: Optional[ProductRelationshipType] = Query(None, description="Relationship type"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """
    Get related products.
    
    - **product_id**: Product ID
    - **relationship_type**: Optional filter by relationship type
    """
    try:
        result = await services.relationships.get_related_products(product_id, relationship_type)
        return result
    except Exception as e:
        logger.error("get_related_products_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/products/{product_id}/recommendations", response_model=List[ProductRecommendation])
async def generate_recommendations(
    product_id: str = Path(..., description="Product ID"),
    request: GenerateRecommendationsRequest = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """
    Generate AI-powered product recommendations.
    
    - **product_id**: Product ID
    - **request**: Recommendation request parameters
    """
    try:
        request.product_id = product_id
        result = await services.relationships.generate_recommendations(request)
        return result
    except Exception as e:
        logger.error("generate_recommendations_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/product-recommendations", response_model=ProductRecommendation)
async def create_recommendation(
    recommendation: ProductRecommendationCreate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Create a product recommendation."""
    try:
        result = await services.relationships.create_recommendation(recommendation)
        return result
    except Exception as e:
        logger.error("create_recommendation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# 10. PRODUCT LIFECYCLE ENDPOINTS
# =====================================================

@app.post("/api/v1/products/{product_id}/lifecycle", response_model=ProductLifecycle)
async def create_lifecycle(
    product_id: str = Path(..., description="Product ID"),
    lifecycle: ProductLifecycleCreate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Create a product lifecycle record."""
    try:
        lifecycle.product_id = product_id
        result = await services.lifecycle.create_lifecycle(lifecycle)
        return result
    except Exception as e:
        logger.error("create_lifecycle_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/products/{product_id}/status", response_model=ProductLifecycle)
async def update_product_status(
    product_id: str = Path(..., description="Product ID"),
    new_status: ProductStatus = Body(..., description="New status"),
    reason: str = Body(..., description="Reason for status change"),
    changed_by: str = Body(..., description="User making the change"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Update product status."""
    try:
        result = await services.lifecycle.update_status(product_id, new_status, reason, changed_by)
        return result
    except Exception as e:
        logger.error("update_status_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/products/{product_id}/versions", response_model=ProductVersion)
async def create_version_snapshot(
    product_id: str = Path(..., description="Product ID"),
    version_number: str = Body(..., description="Version number"),
    product_data: Dict[str, Any] = Body(..., description="Product data snapshot"),
    change_summary: str = Body(..., description="Change summary"),
    created_by: str = Body(..., description="User creating the version"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Create a version snapshot of a product."""
    try:
        result = await services.lifecycle.create_version_snapshot(
            product_id, version_number, product_data, change_summary, created_by
        )
        return result
    except Exception as e:
        logger.error("create_version_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/products/{product_id}/changes", response_model=ProductChange)
async def record_product_change(
    product_id: str = Path(..., description="Product ID"),
    field_name: str = Body(..., description="Field name"),
    old_value: Any = Body(..., description="Old value"),
    new_value: Any = Body(..., description="New value"),
    change_type: str = Body(..., description="Change type"),
    changed_by: str = Body(..., description="User making the change"),
    reason: Optional[str] = Body(None, description="Reason for change"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Record a product change."""
    try:
        result = await services.lifecycle.record_change(
            product_id, field_name, old_value, new_value, change_type, changed_by, reason
        )
        return result
    except Exception as e:
        logger.error("record_change_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/products/{product_id}/approvals", response_model=ProductApproval)
async def request_approval(
    product_id: str = Path(..., description="Product ID"),
    approval_type: ApprovalType = Body(..., description="Approval type"),
    requested_by: str = Body(..., description="User requesting approval"),
    approval_data: Optional[Dict[str, Any]] = Body(None, description="Approval data"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Request approval for a product change."""
    try:
        result = await services.lifecycle.request_approval(
            product_id, approval_type, requested_by, approval_data
        )
        return result
    except Exception as e:
        logger.error("request_approval_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/approvals/{approval_id}/review", response_model=ProductApproval)
async def review_approval(
    approval_id: UUID = Path(..., description="Approval ID"),
    review: ProductApprovalReview = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Review an approval request."""
    try:
        result = await services.lifecycle.review_approval(approval_id, review)
        if not result:
            raise HTTPException(status_code=404, detail="Approval not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("review_approval_failed", error=str(e), approval_id=str(approval_id))
        raise HTTPException(status_code=500, detail=str(e))

