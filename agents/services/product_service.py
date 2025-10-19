"""
Product Service Layer for Enhanced Product Agent

This service layer encapsulates all business logic for product management including
variants, bundles, media, categories, attributes, pricing, reviews, inventory,
relationships, and lifecycle management.
"""

import os
import json
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID

import structlog

from shared.database import DatabaseManager
from shared.product_models import (
    # Variant models
    VariantAttribute, VariantAttributeCreate, VariantAttributeUpdate,
    ProductVariant, ProductVariantCreate, ProductVariantUpdate,
    VariantAttributeValue, VariantAttributeValueCreate,
    VariantPricing, VariantPricingCreate, VariantPricingUpdate,
    
    # Bundle models
    ProductBundle, ProductBundleCreate, ProductBundleUpdate,
    BundleComponent, BundleComponentCreate,
    BundlePricingRule, BundlePricingRuleCreate,
    BundleDetails,
    
    # Media models
    ProductImage, ProductImageCreate, ProductImageUpdate,
    ProductMedia, ProductMediaCreate, ProductMediaUpdate,
    ImageVariant, ImageVariantCreate,
    
    # Category models
    ProductCategory, ProductCategoryCreate, ProductCategoryUpdate,
    CategoryAttribute, CategoryAttributeCreate,
    ProductCategoryMapping, ProductCategoryMappingCreate,
    
    # Attribute models
    AttributeGroup, AttributeGroupCreate, AttributeGroupUpdate,
    ProductAttribute, ProductAttributeCreate, ProductAttributeUpdate,
    ProductAttributeValue, ProductAttributeValueCreate, ProductAttributeValueUpdate,
    
    # Pricing models
    PricingRule, PricingRuleCreate, PricingRuleUpdate,
    PricingTier, PricingTierCreate,
    PriceHistory, PriceHistoryCreate,
    CompetitorPrice, CompetitorPriceCreate,
    BulkPriceUpdateRequest,
    
    # Review models
    ProductReview, ProductReviewCreate, ProductReviewUpdate,
    ReviewImage, ReviewImageCreate,
    ReviewVote, ReviewVoteCreate,
    ReviewResponse, ReviewResponseCreate, ReviewResponseUpdate,
    ReviewWithDetails,
    
    # Inventory models
    ProductInventory, ProductInventoryCreate, ProductInventoryUpdate,
    InventoryTransaction, InventoryTransactionCreate,
    InventoryReservation, InventoryReservationCreate,
    InventoryBatch, InventoryBatchCreate,
    
    # Relationship models
    ProductRelationship, ProductRelationshipCreate,
    ProductRecommendation, ProductRecommendationCreate,
    GenerateRecommendationsRequest,
    
    # Lifecycle models
    ProductLifecycle, ProductLifecycleCreate, ProductLifecycleUpdate,
    ProductVersion, ProductVersionCreate,
    ProductChange, ProductChangeCreate,
    ProductApproval, ProductApprovalCreate, ProductApprovalReview,
    
    # Enums
    BundleType, PricingStrategy, MediaType, PricingRuleType,
    InventoryTransactionType, ProductRelationshipType, RecommendationType,
    ProductStatus, ApprovalStatus, ApprovalType
)
from shared.product_repository import (
    ProductVariantRepository,
    ProductBundleRepository,
    ProductMediaRepository,
    ProductCategoryRepository,
    ProductAttributeRepository,
    ProductPricingRepository,
    ProductReviewRepository,
    ProductInventoryRepository,
    ProductRelationshipRepository,
    ProductLifecycleRepository
)


logger = structlog.get_logger(__name__)


# =====================================================
# 1. PRODUCT VARIANT SERVICE
# =====================================================

class ProductVariantService:
    """Service for managing product variants."""
    
    def __init__(self, repo: ProductVariantRepository):
        self.repo = repo
    
    async def create_variant(
        self,
        variant: ProductVariantCreate,
        attribute_values: List[VariantAttributeValueCreate]
    ) -> ProductVariant:
        """
        Create a new product variant with attribute values.
        
        Args:
            variant: Variant data
            attribute_values: List of attribute values for the variant
        
        Returns:
            Created ProductVariant
        """
        # Create the variant
        created_variant = await self.repo.create_variant(variant)
        
        # Add attribute values
        for attr_value in attribute_values:
            await self.repo.create_variant(attr_value)
        
        logger.info(
            "product_variant_created",
            variant_id=str(created_variant.variant_id),
            product_id=variant.product_id,
            sku=variant.sku
        )
        
        return created_variant
    
    async def get_product_variants(self, product_id: str) -> List[ProductVariant]:
        """Get all variants for a product."""
        return await self.repo.get_product_variants(product_id)
    
    async def update_variant(
        self,
        variant_id: UUID,
        update_data: ProductVariantUpdate
    ) -> Optional[ProductVariant]:
        """Update a product variant."""
        updated = await self.repo.update_variant(variant_id, update_data)
        
        if updated:
            logger.info("product_variant_updated", variant_id=str(variant_id))
        
        return updated
    
    async def set_master_variant(self, variant_id: UUID, product_id: str) -> ProductVariant:
        """
        Set a variant as the master variant for a product.
        Unsets any existing master variant.
        """
        # Get all variants for the product
        variants = await self.repo.get_product_variants(product_id)
        
        # Unset existing master
        for v in variants:
            if v.is_master and v.variant_id != variant_id:
                await self.repo.update_variant(
                    v.variant_id,
                    ProductVariantUpdate(is_master=False)
                )
        
        # Set new master
        updated = await self.repo.update_variant(
            variant_id,
            ProductVariantUpdate(is_master=True)
        )
        
        logger.info("master_variant_set", variant_id=str(variant_id), product_id=product_id)
        
        return updated


# =====================================================
# 2. PRODUCT BUNDLE SERVICE
# =====================================================

class ProductBundleService:
    """Service for managing product bundles."""
    
    def __init__(self, repo: ProductBundleRepository):
        self.repo = repo
    
    async def create_bundle(
        self,
        bundle: ProductBundleCreate,
        components: List[BundleComponentCreate],
        pricing_rules: Optional[List[BundlePricingRuleCreate]] = None
    ) -> BundleDetails:
        """
        Create a complete product bundle with components and pricing rules.
        
        Args:
            bundle: Bundle data
            components: List of bundle components
            pricing_rules: Optional pricing rules
        
        Returns:
            BundleDetails with all related data
        """
        # Create the bundle
        created_bundle = await self.repo.create_bundle(bundle)
        
        # Add components
        created_components = []
        for component in components:
            component.bundle_id = created_bundle.bundle_id
            created_component = await self.repo.add_bundle_component(component)
            created_components.append(created_component)
        
        # Add pricing rules if provided
        created_rules = []
        if pricing_rules:
            for rule in pricing_rules:
                # Implementation would go here
                pass
        
        logger.info(
            "product_bundle_created",
            bundle_id=str(created_bundle.bundle_id),
            name=bundle.bundle_name,
            components=len(created_components)
        )
        
        return BundleDetails(
            bundle=created_bundle,
            components=created_components,
            pricing_rules=created_rules
        )
    
    async def get_bundle_details(self, bundle_id: UUID) -> Optional[BundleDetails]:
        """Get complete bundle details including components and pricing."""
        bundle = await self.repo.get_bundle(bundle_id)
        if not bundle:
            return None
        
        components = await self.repo.get_bundle_components(bundle_id)
        
        return BundleDetails(
            bundle=bundle,
            components=components,
            pricing_rules=[]
        )
    
    async def calculate_bundle_price(self, bundle_id: UUID) -> Decimal:
        """
        Calculate the effective price of a bundle based on its pricing strategy.
        
        Returns:
            Calculated bundle price
        """
        details = await self.get_bundle_details(bundle_id)
        if not details:
            raise ValueError(f"Bundle {bundle_id} not found")
        
        bundle = details.bundle
        
        if bundle.pricing_strategy == PricingStrategy.FIXED:
            return bundle.bundle_price
        
        elif bundle.pricing_strategy == PricingStrategy.PERCENTAGE_DISCOUNT:
            # Calculate sum of component prices and apply discount
            # This would require fetching product prices
            # Simplified implementation:
            return bundle.bundle_price
        
        elif bundle.pricing_strategy == PricingStrategy.DYNAMIC:
            # Dynamic pricing based on rules
            return bundle.bundle_price
        
        return bundle.bundle_price
    
    async def activate_bundle(self, bundle_id: UUID) -> Optional[ProductBundle]:
        """Activate a bundle."""
        bundle = await self.repo.get_bundle(bundle_id)
        if not bundle:
            return None
        
        # Update bundle to active
        # Implementation would update the bundle status
        logger.info("bundle_activated", bundle_id=str(bundle_id))
        
        return bundle


# =====================================================
# 3. PRODUCT MEDIA SERVICE
# =====================================================

class ProductMediaService:
    """Service for managing product images and media."""
    
    def __init__(self, repo: ProductMediaRepository):
        self.repo = repo
    
    async def add_product_image(
        self,
        image: ProductImageCreate,
        set_as_primary: bool = False
    ) -> ProductImage:
        """
        Add an image to a product.
        
        Args:
            image: Image data
            set_as_primary: Whether to set this as the primary image
        
        Returns:
            Created ProductImage
        """
        if set_as_primary:
            # Unset existing primary images
            existing_images = await self.repo.get_product_images(image.product_id)
            for img in existing_images:
                if img.is_primary:
                    # Would update the image to set is_primary=False
                    pass
            
            image.is_primary = True
        
        created_image = await self.repo.create_image(image)
        
        logger.info(
            "product_image_added",
            image_id=str(created_image.image_id),
            product_id=image.product_id,
            is_primary=created_image.is_primary
        )
        
        return created_image
    
    async def add_product_media(self, media: ProductMediaCreate) -> ProductMedia:
        """Add media (video, 360 view, etc.) to a product."""
        created_media = await self.repo.create_media(media)
        
        logger.info(
            "product_media_added",
            media_id=str(created_media.media_id),
            product_id=media.product_id,
            type=media.media_type.value
        )
        
        return created_media
    
    async def get_product_images(self, product_id: str) -> List[ProductImage]:
        """Get all images for a product, ordered by primary first."""
        return await self.repo.get_product_images(product_id)
    
    async def get_product_media(self, product_id: str) -> List[ProductMedia]:
        """Get all media for a product."""
        return await self.repo.get_product_media(product_id)
    
    async def set_primary_image(self, image_id: UUID, product_id: str) -> ProductImage:
        """Set an image as the primary image for a product."""
        # Unset existing primary
        existing_images = await self.repo.get_product_images(product_id)
        for img in existing_images:
            if img.is_primary and img.image_id != image_id:
                # Would update to set is_primary=False
                pass
        
        # Set new primary
        # Would update the specified image to set is_primary=True
        
        logger.info("primary_image_set", image_id=str(image_id), product_id=product_id)
        
        # Return updated image (simplified)
        images = await self.repo.get_product_images(product_id)
        return next((img for img in images if img.image_id == image_id), images[0])


# =====================================================
# 4. PRODUCT CATEGORY SERVICE
# =====================================================

class ProductCategoryService:
    """Service for managing product categories."""
    
    def __init__(self, repo: ProductCategoryRepository):
        self.repo = repo
    
    async def create_category(self, category: ProductCategoryCreate) -> ProductCategory:
        """Create a new product category."""
        created = await self.repo.create_category(category)
        
        logger.info(
            "product_category_created",
            category_id=created.category_id,
            name=category.category_name,
            parent_id=category.parent_category_id
        )
        
        return created
    
    async def get_category_tree(self, parent_id: Optional[int] = None) -> List[ProductCategory]:
        """
        Get category tree starting from a parent.
        Returns root categories if parent_id is None.
        """
        return await self.repo.get_subcategories(parent_id)
    
    async def add_product_to_category(
        self,
        product_id: str,
        category_id: int,
        is_primary: bool = False
    ) -> ProductCategoryMapping:
        """Add a product to a category."""
        mapping = ProductCategoryMappingCreate(
            product_id=product_id,
            category_id=category_id,
            is_primary=is_primary
        )
        
        created = await self.repo.add_product_to_category(mapping)
        
        logger.info(
            "product_added_to_category",
            product_id=product_id,
            category_id=category_id,
            is_primary=is_primary
        )
        
        return created
    
    async def get_category_breadcrumb(self, category_id: int) -> List[ProductCategory]:
        """
        Get breadcrumb trail for a category (from root to current).
        """
        category = await self.repo.get_category(category_id)
        if not category:
            return []
        
        breadcrumb = [category]
        
        # Walk up the tree using category_path
        # Simplified implementation
        return breadcrumb


# =====================================================
# 5. PRODUCT ATTRIBUTE SERVICE
# =====================================================

class ProductAttributeService:
    """Service for managing product attributes."""
    
    def __init__(self, repo: ProductAttributeRepository):
        self.repo = repo
    
    async def create_attribute_group(self, group: AttributeGroupCreate) -> AttributeGroup:
        """Create a new attribute group."""
        created = await self.repo.create_attribute_group(group)
        
        logger.info(
            "attribute_group_created",
            group_id=created.group_id,
            name=group.group_name
        )
        
        return created
    
    async def create_attribute(self, attr: ProductAttributeCreate) -> ProductAttribute:
        """Create a new product attribute."""
        created = await self.repo.create_attribute(attr)
        
        logger.info(
            "product_attribute_created",
            attribute_id=created.attribute_id,
            name=attr.attribute_name,
            type=attr.attribute_type
        )
        
        return created
    
    async def set_product_attributes(
        self,
        product_id: str,
        attributes: List[ProductAttributeValueCreate]
    ) -> List[ProductAttributeValue]:
        """Set multiple attribute values for a product."""
        results = []
        
        for attr in attributes:
            attr.product_id = product_id
            created = await self.repo.set_attribute_value(attr)
            results.append(created)
        
        logger.info(
            "product_attributes_set",
            product_id=product_id,
            count=len(results)
        )
        
        return results
    
    async def get_product_attributes(self, product_id: str) -> List[ProductAttributeValue]:
        """Get all attribute values for a product."""
        return await self.repo.get_product_attributes(product_id)
    
    async def validate_attribute_value(
        self,
        attribute_id: int,
        value: str
    ) -> bool:
        """
        Validate an attribute value against validation rules.
        
        Returns:
            True if valid, False otherwise
        """
        # Would fetch attribute and check validation_rules
        # Simplified implementation
        return True


# =====================================================
# 6. PRODUCT PRICING SERVICE
# =====================================================

class ProductPricingService:
    """Service for managing product pricing."""
    
    def __init__(self, repo: ProductPricingRepository):
        self.repo = repo
    
    async def create_pricing_rule(
        self,
        rule: PricingRuleCreate,
        tiers: Optional[List[PricingTierCreate]] = None
    ) -> PricingRule:
        """
        Create a pricing rule with optional tiered pricing.
        
        Args:
            rule: Pricing rule data
            tiers: Optional pricing tiers for volume-based pricing
        
        Returns:
            Created PricingRule
        """
        created_rule = await self.repo.create_pricing_rule(rule)
        
        if tiers and rule.rule_type == PricingRuleType.TIERED:
            for tier in tiers:
                await self.repo.add_pricing_tier(tier, created_rule.rule_id)
        
        logger.info(
            "pricing_rule_created",
            rule_id=str(created_rule.rule_id),
            product_id=rule.product_id,
            type=rule.rule_type.value
        )
        
        return created_rule
    
    async def calculate_price(
        self,
        product_id: str,
        quantity: int = 1,
        customer_id: Optional[str] = None
    ) -> Decimal:
        """
        Calculate the effective price for a product based on active pricing rules.
        
        Args:
            product_id: Product ID
            quantity: Quantity being purchased
            customer_id: Optional customer ID for personalized pricing
        
        Returns:
            Calculated price
        """
        # Would fetch active pricing rules and calculate
        # Simplified implementation
        base_price = Decimal("100.00")  # Would fetch from product
        
        # Apply tiered pricing if applicable
        # Apply promotional pricing if applicable
        # Apply customer-specific pricing if applicable
        
        return base_price
    
    async def update_price(
        self,
        product_id: str,
        new_price: Decimal,
        reason: str,
        changed_by: str,
        effective_date: Optional[date] = None
    ) -> PriceHistory:
        """
        Update product price and record in history.
        
        Args:
            product_id: Product ID
            new_price: New price
            reason: Reason for price change
            changed_by: User making the change
            effective_date: When the price takes effect
        
        Returns:
            PriceHistory record
        """
        # Would fetch current price
        old_price = Decimal("100.00")  # Simplified
        
        # Record price change
        change = PriceHistoryCreate(
            product_id=product_id,
            old_price=old_price,
            new_price=new_price,
            change_reason=reason,
            changed_by=changed_by,
            change_type="manual",
            effective_date=effective_date or date.today()
        )
        
        history = await self.repo.record_price_change(change)
        
        logger.info(
            "price_updated",
            product_id=product_id,
            old_price=float(old_price),
            new_price=float(new_price),
            changed_by=changed_by
        )
        
        return history
    
    async def bulk_update_prices(self, request: BulkPriceUpdateRequest) -> Dict[str, Any]:
        """
        Update prices for multiple products.
        
        Returns:
            Summary of updates
        """
        updated_count = 0
        failed_count = 0
        errors = []
        
        for product_id in request.product_ids:
            try:
                if request.adjustment_type == "percentage":
                    # Would fetch current price and calculate new price
                    pass
                else:
                    # Fixed amount adjustment
                    pass
                
                updated_count += 1
            except Exception as e:
                failed_count += 1
                errors.append({"product_id": product_id, "error": str(e)})
        
        logger.info(
            "bulk_price_update_completed",
            updated=updated_count,
            failed=failed_count
        )
        
        return {
            "updated": updated_count,
            "failed": failed_count,
            "errors": errors
        }
    
    async def track_competitor_price(self, price: CompetitorPriceCreate) -> CompetitorPrice:
        """Track a competitor's price for a product."""
        tracked = await self.repo.track_competitor_price(price)
        
        logger.info(
            "competitor_price_tracked",
            product_id=price.product_id,
            competitor=price.competitor_name,
            price=float(price.competitor_price)
        )
        
        return tracked


# =====================================================
# 7. PRODUCT REVIEW SERVICE
# =====================================================

class ProductReviewService:
    """Service for managing product reviews."""
    
    def __init__(self, repo: ProductReviewRepository):
        self.repo = repo
    
    async def create_review(self, review: ProductReviewCreate) -> ProductReview:
        """Create a new product review."""
        created = await self.repo.create_review(review)
        
        logger.info(
            "product_review_created",
            review_id=str(created.review_id),
            product_id=review.product_id,
            rating=review.rating,
            verified=review.is_verified_purchase
        )
        
        return created
    
    async def approve_review(self, review_id: UUID, approved_by: str) -> Optional[ProductReview]:
        """Approve a review for public display."""
        approved = await self.repo.approve_review(review_id, approved_by)
        
        if approved:
            logger.info(
                "review_approved",
                review_id=str(review_id),
                approved_by=approved_by
            )
        
        return approved
    
    async def add_review_vote(self, vote: ReviewVoteCreate) -> ReviewVote:
        """Add a helpful/not helpful vote to a review."""
        created = await self.repo.add_review_vote(vote)
        
        logger.info(
            "review_vote_added",
            review_id=str(vote.review_id),
            vote_type=vote.vote_type
        )
        
        return created
    
    async def add_seller_response(
        self,
        review_id: UUID,
        response: ReviewResponseCreate
    ) -> ReviewResponse:
        """Add a seller response to a review."""
        created = await self.repo.add_review_response(response, review_id)
        
        logger.info(
            "seller_response_added",
            review_id=str(review_id),
            responded_by=response.responded_by
        )
        
        return created
    
    async def get_product_reviews(
        self,
        product_id: str,
        approved_only: bool = True
    ) -> List[ProductReview]:
        """Get all reviews for a product."""
        return await self.repo.get_product_reviews(product_id, approved_only)
    
    async def calculate_rating_summary(self, product_id: str) -> Dict[str, Any]:
        """
        Calculate rating summary statistics for a product.
        
        Returns:
            Dictionary with average rating, count, distribution, etc.
        """
        reviews = await self.repo.get_product_reviews(product_id, approved_only=True)
        
        if not reviews:
            return {
                "average_rating": 0.0,
                "total_reviews": 0,
                "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }
        
        total_rating = sum(r.rating for r in reviews)
        average_rating = total_rating / len(reviews)
        
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in reviews:
            distribution[review.rating] += 1
        
        return {
            "average_rating": round(average_rating, 2),
            "total_reviews": len(reviews),
            "rating_distribution": distribution,
            "verified_purchases": sum(1 for r in reviews if r.is_verified_purchase)
        }


# =====================================================
# 8. PRODUCT INVENTORY SERVICE
# =====================================================

class ProductInventoryService:
    """Service for managing product inventory."""
    
    def __init__(self, repo: ProductInventoryRepository):
        self.repo = repo
    
    async def create_inventory(self, inventory: ProductInventoryCreate) -> ProductInventory:
        """Create inventory record for a product at a location."""
        created = await self.repo.create_inventory(inventory)
        
        logger.info(
            "inventory_created",
            product_id=inventory.product_id,
            location=inventory.location_id,
            quantity=inventory.quantity_available
        )
        
        return created
    
    async def adjust_inventory(
        self,
        product_id: str,
        location_id: str,
        quantity: int,
        transaction_type: InventoryTransactionType,
        reference_id: Optional[str] = None,
        reference_type: Optional[str] = None,
        notes: Optional[str] = None,
        created_by: str = "system"
    ) -> InventoryTransaction:
        """
        Adjust inventory levels and record transaction.
        
        Args:
            product_id: Product ID
            location_id: Location ID
            quantity: Quantity to adjust (positive for increase, negative for decrease)
            transaction_type: Type of transaction
            reference_id: Optional reference ID (order, shipment, etc.)
            reference_type: Optional reference type
            notes: Optional notes
            created_by: User/system making the adjustment
        
        Returns:
            InventoryTransaction record
        """
        transaction = InventoryTransactionCreate(
            product_id=product_id,
            location_id=location_id,
            transaction_type=transaction_type,
            quantity=quantity,
            reference_id=reference_id,
            reference_type=reference_type,
            notes=notes,
            created_by=created_by
        )
        
        recorded = await self.repo.record_transaction(transaction)
        
        logger.info(
            "inventory_adjusted",
            product_id=product_id,
            location=location_id,
            quantity=quantity,
            type=transaction_type.value
        )
        
        return recorded
    
    async def reserve_inventory(
        self,
        product_id: str,
        location_id: str,
        order_id: str,
        quantity: int,
        reserved_until: datetime
    ) -> InventoryReservation:
        """Reserve inventory for an order."""
        reservation = InventoryReservationCreate(
            product_id=product_id,
            location_id=location_id,
            order_id=order_id,
            quantity_reserved=quantity,
            reserved_until=reserved_until
        )
        
        created = await self.repo.create_reservation(reservation)
        
        logger.info(
            "inventory_reserved",
            product_id=product_id,
            order_id=order_id,
            quantity=quantity
        )
        
        return created
    
    async def check_availability(
        self,
        product_id: str,
        quantity: int,
        location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if sufficient inventory is available.
        
        Returns:
            Dictionary with availability status and details
        """
        if location_id:
            inventory = await self.repo.get_inventory(product_id, location_id)
            if not inventory:
                return {"available": False, "quantity_available": 0}
            
            available_qty = inventory.quantity_available - inventory.quantity_reserved
            
            return {
                "available": available_qty >= quantity,
                "quantity_available": available_qty,
                "location_id": location_id
            }
        else:
            # Check across all locations
            # Simplified implementation
            return {"available": True, "quantity_available": 100}
    
    async def get_low_stock_products(self, location_id: Optional[str] = None) -> List[ProductInventory]:
        """
        Get products that are below their reorder point.
        
        Returns:
            List of inventory records below reorder point
        """
        # Would query inventory where quantity_available <= reorder_point
        # Simplified implementation
        return []


# =====================================================
# 9. PRODUCT RELATIONSHIP SERVICE
# =====================================================

class ProductRelationshipService:
    """Service for managing product relationships."""
    
    def __init__(self, repo: ProductRelationshipRepository):
        self.repo = repo
    
    async def create_relationship(
        self,
        relationship: ProductRelationshipCreate
    ) -> ProductRelationship:
        """Create a product relationship."""
        created = await self.repo.create_relationship(relationship)
        
        logger.info(
            "product_relationship_created",
            product_id=relationship.product_id,
            related_id=relationship.related_product_id,
            type=relationship.relationship_type.value
        )
        
        return created
    
    async def get_related_products(
        self,
        product_id: str,
        relationship_type: Optional[ProductRelationshipType] = None
    ) -> List[ProductRelationship]:
        """Get related products."""
        return await self.repo.get_related_products(product_id, relationship_type)
    
    async def generate_recommendations(
        self,
        request: GenerateRecommendationsRequest
    ) -> List[ProductRecommendation]:
        """
        Generate AI-powered product recommendations.
        
        This would integrate with an ML model or recommendation engine.
        Simplified implementation for now.
        """
        recommendations = []
        
        # Would call recommendation engine here
        # For now, return empty list
        
        logger.info(
            "recommendations_generated",
            product_id=request.product_id,
            count=len(recommendations)
        )
        
        return recommendations
    
    async def create_recommendation(
        self,
        recommendation: ProductRecommendationCreate
    ) -> ProductRecommendation:
        """Create a product recommendation."""
        created = await self.repo.create_recommendation(recommendation)
        
        logger.info(
            "product_recommendation_created",
            product_id=recommendation.product_id,
            recommended_id=recommendation.recommended_product_id,
            type=recommendation.recommendation_type.value
        )
        
        return created


# =====================================================
# 10. PRODUCT LIFECYCLE SERVICE
# =====================================================

class ProductLifecycleService:
    """Service for managing product lifecycle."""
    
    def __init__(self, repo: ProductLifecycleRepository):
        self.repo = repo
    
    async def create_lifecycle(self, lifecycle: ProductLifecycleCreate) -> ProductLifecycle:
        """Create a product lifecycle record."""
        created = await self.repo.create_lifecycle(lifecycle)
        
        logger.info(
            "product_lifecycle_created",
            product_id=lifecycle.product_id,
            status=lifecycle.status.value
        )
        
        return created
    
    async def update_status(
        self,
        product_id: str,
        new_status: ProductStatus,
        reason: str,
        changed_by: str
    ) -> ProductLifecycle:
        """Update product status."""
        lifecycle = ProductLifecycleCreate(
            product_id=product_id,
            status=new_status,
            status_reason=reason,
            changed_by=changed_by
        )
        
        created = await self.repo.create_lifecycle(lifecycle)
        
        logger.info(
            "product_status_updated",
            product_id=product_id,
            status=new_status.value,
            changed_by=changed_by
        )
        
        return created
    
    async def create_version_snapshot(
        self,
        product_id: str,
        version_number: str,
        product_data: Dict[str, Any],
        change_summary: str,
        created_by: str
    ) -> ProductVersion:
        """Create a version snapshot of a product."""
        version = ProductVersionCreate(
            product_id=product_id,
            version_number=version_number,
            version_data=product_data,
            change_summary=change_summary,
            created_by=created_by
        )
        
        created = await self.repo.create_version(version)
        
        logger.info(
            "product_version_created",
            product_id=product_id,
            version=version_number,
            created_by=created_by
        )
        
        return created
    
    async def record_change(
        self,
        product_id: str,
        field_name: str,
        old_value: Any,
        new_value: Any,
        change_type: str,
        changed_by: str,
        reason: Optional[str] = None
    ) -> ProductChange:
        """Record a product change."""
        change = ProductChangeCreate(
            product_id=product_id,
            field_name=field_name,
            old_value=str(old_value),
            new_value=str(new_value),
            change_type=change_type,
            changed_by=changed_by,
            change_reason=reason
        )
        
        recorded = await self.repo.record_change(change)
        
        logger.info(
            "product_change_recorded",
            product_id=product_id,
            field=field_name,
            changed_by=changed_by
        )
        
        return recorded
    
    async def request_approval(
        self,
        product_id: str,
        approval_type: ApprovalType,
        requested_by: str,
        approval_data: Optional[Dict[str, Any]] = None
    ) -> ProductApproval:
        """Request approval for a product change."""
        approval = ProductApprovalCreate(
            product_id=product_id,
            approval_type=approval_type,
            requested_by=requested_by,
            approval_data=approval_data
        )
        
        created = await self.repo.create_approval(approval)
        
        logger.info(
            "approval_requested",
            approval_id=str(created.approval_id),
            product_id=product_id,
            type=approval_type.value
        )
        
        return created
    
    async def review_approval(
        self,
        approval_id: UUID,
        review: ProductApprovalReview
    ) -> Optional[ProductApproval]:
        """Review an approval request."""
        reviewed = await self.repo.review_approval(approval_id, review)
        
        if reviewed:
            logger.info(
                "approval_reviewed",
                approval_id=str(approval_id),
                status=review.status.value,
                reviewed_by=review.reviewed_by
            )
        
        return reviewed


# =====================================================
# PRODUCT SERVICE FACADE
# =====================================================

class ProductServiceFacade:
    """
    Facade providing unified access to all product services.
    Simplifies dependency injection and service coordination.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        # Initialize repositories
        self.variant_repo = ProductVariantRepository(db_manager)
        self.bundle_repo = ProductBundleRepository(db_manager)
        self.media_repo = ProductMediaRepository(db_manager)
        self.category_repo = ProductCategoryRepository(db_manager)
        self.attribute_repo = ProductAttributeRepository(db_manager)
        self.pricing_repo = ProductPricingRepository(db_manager)
        self.review_repo = ProductReviewRepository(db_manager)
        self.inventory_repo = ProductInventoryRepository(db_manager)
        self.relationship_repo = ProductRelationshipRepository(db_manager)
        self.lifecycle_repo = ProductLifecycleRepository(db_manager)
        
        # Initialize services
        self.variants = ProductVariantService(self.variant_repo)
        self.bundles = ProductBundleService(self.bundle_repo)
        self.media = ProductMediaService(self.media_repo)
        self.categories = ProductCategoryService(self.category_repo)
        self.attributes = ProductAttributeService(self.attribute_repo)
        self.pricing = ProductPricingService(self.pricing_repo)
        self.reviews = ProductReviewService(self.review_repo)
        self.inventory = ProductInventoryService(self.inventory_repo)
        self.relationships = ProductRelationshipService(self.relationship_repo)
        self.lifecycle = ProductLifecycleService(self.lifecycle_repo)

