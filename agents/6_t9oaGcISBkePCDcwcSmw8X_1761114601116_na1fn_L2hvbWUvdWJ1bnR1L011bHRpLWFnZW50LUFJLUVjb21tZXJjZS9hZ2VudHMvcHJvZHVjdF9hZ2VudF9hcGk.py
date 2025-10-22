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
import uvicorn
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

@app.get("/")
async def root():
    return {"agent_name": "Product Agent", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)

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
        if not result:
            raise HTTPException(status_code=404, detail="Image not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("set_primary_image_failed", error=str(e), image_id=str(image_id))
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/images/{image_id}", response_model=Dict[str, str])
async def delete_product_image(
    image_id: UUID = Path(..., description="Image ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Delete a product image."""
    try:
        success = await services.media.delete_product_image(image_id)
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

@app.post("/api/v1/categories", response_model=ProductCategory)
async def create_product_category(
    category: ProductCategoryCreate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Create a new product category."""
    try:
        result = await services.categories.create_category(category)
        return result
    except Exception as e:
        logger.error("create_category_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/categories/{category_id}", response_model=ProductCategory)
async def get_product_category(
    category_id: UUID = Path(..., description="Category ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Get product category by ID."""
    try:
        category = await services.categories.get_category(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        return category
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_category_failed", error=str(e), category_id=str(category_id))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/categories", response_model=List[ProductCategory])
async def get_all_product_categories(
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Get all product categories."""
    try:
        categories = await services.categories.get_all_categories()
        return categories
    except Exception as e:
        logger.error("get_all_categories_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/categories/{category_id}", response_model=ProductCategory)
async def update_product_category(
    category_id: UUID = Path(..., description="Category ID"),
    update_data: ProductCategoryUpdate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Update an existing product category."""
    try:
        result = await services.categories.update_category(category_id, update_data)
        if not result:
            raise HTTPException(status_code=404, detail="Category not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_category_failed", error=str(e), category_id=str(category_id))
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/categories/{category_id}", response_model=Dict[str, str])
async def delete_product_category(
    category_id: UUID = Path(..., description="Category ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Delete a product category."""
    try:
        success = await services.categories.delete_category(category_id)
        if not success:
            raise HTTPException(status_code=404, detail="Category not found")
        return {"message": "Category deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_category_failed", error=str(e), category_id=str(category_id))
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# 5. PRODUCT ATTRIBUTE ENDPOINTS
# =====================================================

@app.post("/api/v1/attributes", response_model=ProductAttribute)
async def create_product_attribute(
    attribute: ProductAttributeCreate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Create a new product attribute (e.g., 'Material', 'Weight')."""
    try:
        result = await services.attributes.create_attribute(attribute)
        return result
    except Exception as e:
        logger.error("create_attribute_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/attributes/{attribute_id}", response_model=ProductAttribute)
async def get_product_attribute(
    attribute_id: UUID = Path(..., description="Attribute ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Get product attribute by ID."""
    try:
        attribute = await services.attributes.get_attribute(attribute_id)
        if not attribute:
            raise HTTPException(status_code=404, detail="Attribute not found")
        return attribute
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_attribute_failed", error=str(e), attribute_id=str(attribute_id))
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/attributes/{attribute_id}", response_model=ProductAttribute)
async def update_product_attribute(
    attribute_id: UUID = Path(..., description="Attribute ID"),
    update_data: ProductAttributeUpdate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Update an existing product attribute."""
    try:
        result = await services.attributes.update_attribute(attribute_id, update_data)
        if not result:
            raise HTTPException(status_code=404, detail="Attribute not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_attribute_failed", error=str(e), attribute_id=str(attribute_id))
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/attributes/{attribute_id}", response_model=Dict[str, str])
async def delete_product_attribute(
    attribute_id: UUID = Path(..., description="Attribute ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Delete a product attribute."""
    try:
        success = await services.attributes.delete_attribute(attribute_id)
        if not success:
            raise HTTPException(status_code=404, detail="Attribute not found")
        return {"message": "Attribute deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_attribute_failed", error=str(e), attribute_id=str(attribute_id))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/products/{product_id}/attributes", response_model=List[ProductAttribute])
async def get_product_attributes(
    product_id: str = Path(..., description="Product ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Get all attributes associated with a product."""
    try:
        attributes = await services.attributes.get_product_attributes(product_id)
        return attributes
    except Exception as e:
        logger.error("get_product_attributes_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# 6. PRODUCT PRICING ENDPOINTS
# =====================================================

@app.post("/api/v1/products/{product_id}/pricing", response_model=ProductPricing)
async def create_product_pricing(
    product_id: str = Path(..., description="Product ID"),
    pricing: ProductPricingCreate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Create or update pricing for a product."""
    try:
        pricing.product_id = product_id
        result = await services.pricing.create_or_update_pricing(pricing)
        return result
    except Exception as e:
        logger.error("create_pricing_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/products/{product_id}/pricing", response_model=ProductPricing)
async def get_product_pricing(
    product_id: str = Path(..., description="Product ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Get current pricing for a product."""
    try:
        pricing = await services.pricing.get_pricing(product_id)
        if not pricing:
            raise HTTPException(status_code=404, detail="Pricing not found")
        return pricing
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_pricing_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/pricing/{pricing_id}", response_model=ProductPricing)
async def update_product_pricing(
    pricing_id: UUID = Path(..., description="Pricing ID"),
    update_data: ProductPricingUpdate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Update existing product pricing details."""
    try:
        result = await services.pricing.update_pricing(pricing_id, update_data)
        if not result:
            raise HTTPException(status_code=404, detail="Pricing not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_pricing_failed", error=str(e), pricing_id=str(pricing_id))
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/pricing/{pricing_id}", response_model=Dict[str, str])
async def delete_product_pricing(
    pricing_id: UUID = Path(..., description="Pricing ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Delete product pricing."""
    try:
        success = await services.pricing.delete_pricing(pricing_id)
        if not success:
            raise HTTPException(status_code=404, detail="Pricing not found")
        return {"message": "Pricing deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_pricing_failed", error=str(e), pricing_id=str(pricing_id))
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# 7. PRODUCT REVIEW ENDPOINTS
# =====================================================

@app.post("/api/v1/products/{product_id}/reviews", response_model=ProductReview)
async def add_product_review(
    product_id: str = Path(..., description="Product ID"),
    review: ProductReviewCreate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Add a new review to a product."""
    try:
        review.product_id = product_id
        result = await services.reviews.add_review(review)
        return result
    except Exception as e:
        logger.error("add_review_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/products/{product_id}/reviews", response_model=List[ProductReview])
async def get_product_reviews(
    product_id: str = Path(..., description="Product ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Get all reviews for a product."""
    try:
        reviews = await services.reviews.get_reviews_by_product(product_id)
        return reviews
    except Exception as e:
        logger.error("get_reviews_by_product_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/reviews/{review_id}", response_model=ProductReview)
async def get_product_review(
    review_id: UUID = Path(..., description="Review ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Get a specific product review by ID."""
    try:
        review = await services.reviews.get_review(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        return review
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_review_failed", error=str(e), review_id=str(review_id))
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/reviews/{review_id}", response_model=ProductReview)
async def update_product_review(
    review_id: UUID = Path(..., description="Review ID"),
    update_data: ProductReviewUpdate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Update an existing product review."""
    try:
        result = await services.reviews.update_review(review_id, update_data)
        if not result:
            raise HTTPException(status_code=404, detail="Review not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_review_failed", error=str(e), review_id=str(review_id))
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/reviews/{review_id}", response_model=Dict[str, str])
async def delete_product_review(
    review_id: UUID = Path(..., description="Review ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Delete a product review."""
    try:
        success = await services.reviews.delete_review(review_id)
        if not success:
            raise HTTPException(status_code=404, detail="Review not found")
        return {"message": "Review deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_review_failed", error=str(e), review_id=str(review_id))
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# 8. PRODUCT INVENTORY ENDPOINTS
# =====================================================

@app.post("/api/v1/inventory", response_model=InventoryItem)
async def create_inventory_item(
    item: InventoryItemCreate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Create a new inventory item."""
    try:
        result = await services.inventory.create_item(item)
        return result
    except Exception as e:
        logger.error("create_inventory_item_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/inventory/{item_id}", response_model=InventoryItem)
async def get_inventory_item(
    item_id: UUID = Path(..., description="Inventory Item ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Get inventory item by ID."""
    try:
        item = await services.inventory.get_item(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_inventory_item_failed", error=str(e), item_id=str(item_id))
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/inventory/{item_id}", response_model=InventoryItem)
async def update_inventory_item(
    item_id: UUID = Path(..., description="Inventory Item ID"),
    update_data: InventoryItemUpdate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Update an existing inventory item."""
    try:
        result = await services.inventory.update_item(item_id, update_data)
        if not result:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_inventory_item_failed", error=str(e), item_id=str(item_id))
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/inventory/{item_id}", response_model=Dict[str, str])
async def delete_inventory_item(
    item_id: UUID = Path(..., description="Inventory Item ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Delete an inventory item."""
    try:
        success = await services.inventory.delete_item(item_id)
        if not success:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        return {"message": "Inventory item deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_inventory_item_failed", error=str(e), item_id=str(item_id))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/inventory/{item_id}/adjust", response_model=InventoryItem)
async def adjust_inventory_quantity(
    item_id: UUID = Path(..., description="Inventory Item ID"),
    adjustment: InventoryAdjustment = Body(..., description="Quantity adjustment"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Adjust the quantity of an inventory item."""
    try:
        result = await services.inventory.adjust_quantity(item_id, adjustment.quantity_change, adjustment.reason)
        if not result:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("adjust_inventory_quantity_failed", error=str(e), item_id=str(item_id))
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# 9. PRODUCT RELATIONSHIP ENDPOINTS
# =====================================================

@app.post("/api/v1/relationships", response_model=ProductRelationship)
async def create_product_relationship(
    relationship: ProductRelationshipCreate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Create a new product relationship (e.g., 'accessory', 'cross-sell')."""
    try:
        result = await services.relationships.create_relationship(relationship)
        return result
    except Exception as e:
        logger.error("create_relationship_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/products/{product_id}/relationships", response_model=List[ProductRelationship])
async def get_product_relationships(
    product_id: str = Path(..., description="Product ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Get all relationships for a product."""
    try:
        relationships = await services.relationships.get_relationships_by_product(product_id)
        return relationships
    except Exception as e:
        logger.error("get_relationships_by_product_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/relationships/{relationship_id}", response_model=Dict[str, str])
async def delete_product_relationship(
    relationship_id: UUID = Path(..., description="Relationship ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Delete a product relationship."""
    try:
        success = await services.relationships.delete_relationship(relationship_id)
        if not success:
            raise HTTPException(status_code=404, detail="Relationship not found")
        return {"message": "Relationship deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_relationship_failed", error=str(e), relationship_id=str(relationship_id))
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# 10. PRODUCT LIFECYCLE ENDPOINTS
# =====================================================

@app.post("/api/v1/products/{product_id}/lifecycle/status", response_model=ProductLifecycle)
async def update_product_lifecycle_status(
    product_id: str = Path(..., description="Product ID"),
    status_update: ProductLifecycleStatusUpdate = Body(...),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Update the lifecycle status of a product (e.g., 'active', 'discontinued')."""
    try:
        result = await services.lifecycle.update_status(product_id, status_update.status, status_update.reason)
        if not result:
            raise HTTPException(status_code=404, detail="Product not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_lifecycle_status_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/products/{product_id}/lifecycle", response_model=ProductLifecycle)
async def get_product_lifecycle(
    product_id: str = Path(..., description="Product ID"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Get the current lifecycle status of a product."""
    try:
        lifecycle = await services.lifecycle.get_lifecycle(product_id)
        if not lifecycle:
            raise HTTPException(status_code=404, detail="Product lifecycle not found")
        return lifecycle
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_product_lifecycle_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# 11. PRODUCT SEARCH AND FILTER ENDPOINTS
# =====================================================

@app.get("/api/v1/products/search", response_model=List[ProductDetails])
async def search_products(
    query: Optional[str] = Query(None, description="Search query for product name or description"),
    category_id: Optional[UUID] = Query(None, description="Filter by category ID"),
    min_price: Optional[Decimal] = Query(None, description="Filter by minimum price"),
    max_price: Optional[Decimal] = Query(None, description="Filter by maximum price"),
    attribute_filters: Optional[List[str]] = Query(None, description="Filter by attribute values (e.g., 'color:red')"),
    sort_by: Optional[str] = Query(None, description="Sort results by field (e.g., 'price_asc', 'name_desc')"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Search and filter products based on various criteria."""
    try:
        products = await services.search.search_products(
            query=query, category_id=category_id, min_price=min_price, max_price=max_price,
            attribute_filters=attribute_filters, sort_by=sort_by, limit=limit, offset=offset
        )
        return products
    except Exception as e:
        logger.error("search_products_failed", error=str(e), query=query, category_id=category_id)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/products/recommendations/{product_id}", response_model=List[ProductDetails])
async def get_product_recommendations(
    product_id: str = Path(..., description="Product ID"),
    limit: int = Query(5, ge=1, le=10, description="Number of recommendations to return"),
    services: ProductServiceFacade = Depends(get_product_services)
):
    """Get product recommendations based on a given product."""
    try:
        recommendations = await services.search.get_product_recommendations(product_id, limit)
        return recommendations
    except Exception as e:
        logger.error("get_product_recommendations_failed", error=str(e), product_id=product_id)
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# 12. AGENT MANAGEMENT ENDPOINTS
# =====================================================

class AgentStatus(BaseModel):
    status: str
    agent_name: str
    version: str
    uptime: str = None


@app.get("/agent/status", response_model=AgentStatus)
async def get_agent_status():
    """Returns the current status of the agent."""
    return AgentStatus(status="running", agent_name="ProductAgent", version="2.0.0", uptime="N/A")


@app.get("/agent/health", response_model=Dict[str, str])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "product_agent", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

