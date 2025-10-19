"""
Product Agent Service Layer

This module provides business logic layer for all Product Agent operations.
Implements service pattern with Kafka event publishing for inter-agent communication.

Author: Multi-Agent E-Commerce System
Date: January 2025
"""

import json
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from shared.database import DatabaseManager
from shared.kafka_client import KafkaClient
from shared.product_models import *
from repositories.product_repositories import (
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

logger = logging.getLogger(__name__)


# =====================================================
# 1. PRODUCT VARIANT SERVICE
# =====================================================

class ProductVariantService:
    """Service for product variant business logic."""
    
    def __init__(self, db_manager: DatabaseManager, kafka_client: KafkaClient):
        """Initialize service with dependencies."""
        self.db = db_manager
        self.kafka = kafka_client
        self.repo = ProductVariantRepository(db_manager)
    
    async def create_variant_attribute(
        self,
        attribute: VariantAttributeCreate
    ) -> VariantAttribute:
        """Create a new variant attribute."""
        try:
            result = await self.repo.create_variant_attribute(attribute)
            
            # Publish event
            await self.kafka.publish(
                'product.variant.attribute.created',
                {
                    'attribute_id': result.attribute_id,
                    'attribute_name': result.attribute_name,
                    'attribute_type': result.attribute_type,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Created variant attribute: {result.attribute_name}")
            return result
        except Exception as e:
            logger.error(f"Error creating variant attribute: {str(e)}")
            raise
    
    async def create_product_variant(
        self,
        variant: ProductVariantCreate,
        attribute_values: List[VariantAttributeValueCreate],
        pricing: Optional[VariantPricingCreate] = None
    ) -> Dict[str, Any]:
        """Create a product variant with attributes and pricing."""
        try:
            # Create variant
            variant_result = await self.repo.create_product_variant(variant)
            
            # Add attribute values
            attribute_values_result = []
            for attr_value in attribute_values:
                attr_value.variant_id = variant_result.variant_id
                value_result = await self.repo.add_variant_attribute_value(attr_value)
                attribute_values_result.append(value_result)
            
            # Set pricing if provided
            pricing_result = None
            if pricing:
                pricing.variant_id = variant_result.variant_id
                pricing_result = await self.repo.set_variant_pricing(pricing)
            
            # Publish event
            await self.kafka.publish(
                'product.variant.created',
                {
                    'variant_id': str(variant_result.variant_id),
                    'product_id': variant_result.product_id,
                    'variant_sku': variant_result.variant_sku,
                    'is_master': variant_result.is_master,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Created product variant: {variant_result.variant_sku}")
            
            return {
                'variant': variant_result,
                'attributes': attribute_values_result,
                'pricing': pricing_result
            }
        except Exception as e:
            logger.error(f"Error creating product variant: {str(e)}")
            raise
    
    async def get_product_variants_with_details(
        self,
        product_id: str
    ) -> List[Dict[str, Any]]:
        """Get all variants for a product with full details."""
        try:
            variants = await self.repo.get_product_variants(product_id)
            
            result = []
            for variant in variants:
                attributes = await self.repo.get_variant_attribute_values(variant.variant_id)
                pricing = await self.repo.get_variant_pricing(variant.variant_id)
                
                result.append({
                    'variant': variant,
                    'attributes': attributes,
                    'pricing': pricing
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting product variants: {str(e)}")
            raise
    
    async def update_variant_pricing(
        self,
        variant_id: UUID,
        pricing: VariantPricingCreate
    ) -> VariantPricing:
        """Update pricing for a variant."""
        try:
            pricing.variant_id = variant_id
            result = await self.repo.set_variant_pricing(pricing)
            
            # Publish event
            await self.kafka.publish(
                'product.variant.pricing.updated',
                {
                    'variant_id': str(variant_id),
                    'base_price': str(result.base_price),
                    'sale_price': str(result.sale_price) if result.sale_price else None,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Updated variant pricing: {variant_id}")
            return result
        except Exception as e:
            logger.error(f"Error updating variant pricing: {str(e)}")
            raise


# =====================================================
# 2. PRODUCT BUNDLE SERVICE
# =====================================================

class ProductBundleService:
    """Service for product bundle business logic."""
    
    def __init__(self, db_manager: DatabaseManager, kafka_client: KafkaClient):
        """Initialize service with dependencies."""
        self.db = db_manager
        self.kafka = kafka_client
        self.repo = ProductBundleRepository(db_manager)
    
    async def create_bundle(
        self,
        bundle: ProductBundleCreate,
        components: List[BundleComponentCreate],
        pricing_rule: BundlePricingRuleCreate
    ) -> Dict[str, Any]:
        """Create a complete bundle with components and pricing."""
        try:
            # Create bundle
            bundle_result = await self.repo.create_bundle(bundle)
            
            # Add components
            components_result = []
            for component in components:
                component.bundle_id = bundle_result.bundle_id
                comp_result = await self.repo.add_bundle_component(component)
                components_result.append(comp_result)
            
            # Set pricing rule
            pricing_rule.bundle_id = bundle_result.bundle_id
            pricing_result = await self.repo.set_bundle_pricing_rule(pricing_rule)
            
            # Publish event
            await self.kafka.publish(
                'product.bundle.created',
                {
                    'bundle_id': str(bundle_result.bundle_id),
                    'bundle_name': bundle_result.bundle_name,
                    'bundle_type': bundle_result.bundle_type,
                    'component_count': len(components_result),
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Created product bundle: {bundle_result.bundle_name}")
            
            return {
                'bundle': bundle_result,
                'components': components_result,
                'pricing': pricing_result
            }
        except Exception as e:
            logger.error(f"Error creating bundle: {str(e)}")
            raise
    
    async def calculate_bundle_price(
        self,
        bundle_id: UUID
    ) -> Dict[str, Decimal]:
        """Calculate effective price for a bundle."""
        try:
            # Get bundle and components
            components = await self.repo.get_bundle_components(bundle_id)
            
            # Calculate total component price
            # Note: This is simplified - would need to fetch actual product prices
            total_component_price = Decimal('0.00')
            
            # Get pricing rule
            # Note: Would need to implement get_bundle_pricing_rule in repo
            
            # Apply pricing strategy
            # This is a placeholder - actual implementation would be more complex
            
            return {
                'total_component_price': total_component_price,
                'effective_price': total_component_price,
                'savings': Decimal('0.00')
            }
        except Exception as e:
            logger.error(f"Error calculating bundle price: {str(e)}")
            raise
    
    async def get_active_bundles_for_product(
        self,
        product_id: str
    ) -> List[ProductBundle]:
        """Get all active bundles containing a product."""
        try:
            # Note: Would need to implement this query in repo
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Error getting bundles for product: {str(e)}")
            raise


# =====================================================
# 3. PRODUCT MEDIA SERVICE
# =====================================================

class ProductMediaService:
    """Service for product media business logic."""
    
    def __init__(self, db_manager: DatabaseManager, kafka_client: KafkaClient):
        """Initialize service with dependencies."""
        self.db = db_manager
        self.kafka = kafka_client
        self.repo = ProductMediaRepository(db_manager)
    
    async def add_product_image(
        self,
        image: ProductImageCreate,
        set_as_primary: bool = False
    ) -> ProductImage:
        """Add an image to a product."""
        try:
            result = await self.repo.add_product_image(image)
            
            if set_as_primary:
                await self.repo.set_primary_image(image.product_id, result.image_id)
            
            # Publish event
            await self.kafka.publish(
                'product.image.added',
                {
                    'image_id': str(result.image_id),
                    'product_id': result.product_id,
                    'is_primary': set_as_primary,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Added product image: {result.image_id}")
            return result
        except Exception as e:
            logger.error(f"Error adding product image: {str(e)}")
            raise
    
    async def set_primary_image(
        self,
        product_id: str,
        image_id: UUID
    ) -> bool:
        """Set an image as primary for a product."""
        try:
            result = await self.repo.set_primary_image(product_id, image_id)
            
            if result:
                # Publish event
                await self.kafka.publish(
                    'product.image.primary.changed',
                    {
                        'product_id': product_id,
                        'image_id': str(image_id),
                        'timestamp': datetime.now().isoformat()
                    }
                )
            
            logger.info(f"Set primary image for product: {product_id}")
            return result
        except Exception as e:
            logger.error(f"Error setting primary image: {str(e)}")
            raise
    
    async def add_product_media(
        self,
        media: ProductMediaCreate
    ) -> ProductMedia:
        """Add media (video, 360, PDF) to a product."""
        try:
            result = await self.repo.add_product_media(media)
            
            # Publish event
            await self.kafka.publish(
                'product.media.added',
                {
                    'media_id': str(result.media_id),
                    'product_id': result.product_id,
                    'media_type': result.media_type,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Added product media: {result.media_id}")
            return result
        except Exception as e:
            logger.error(f"Error adding product media: {str(e)}")
            raise
    
    async def get_product_gallery(
        self,
        product_id: str
    ) -> Dict[str, Any]:
        """Get complete media gallery for a product."""
        try:
            images = await self.repo.get_product_images(product_id)
            videos = await self.repo.get_product_media(product_id, 'video')
            view_360 = await self.repo.get_product_media(product_id, '360_view')
            documents = await self.repo.get_product_media(product_id, 'document')
            
            return {
                'images': images,
                'videos': videos,
                '360_views': view_360,
                'documents': documents
            }
        except Exception as e:
            logger.error(f"Error getting product gallery: {str(e)}")
            raise


# =====================================================
# 4. PRODUCT CATEGORY SERVICE
# =====================================================

class ProductCategoryService:
    """Service for product category business logic."""
    
    def __init__(self, db_manager: DatabaseManager, kafka_client: KafkaClient):
        """Initialize service with dependencies."""
        self.db = db_manager
        self.kafka = kafka_client
        self.repo = ProductCategoryRepository(db_manager)
    
    async def create_category(
        self,
        category: ProductCategoryCreate
    ) -> ProductCategory:
        """Create a new product category."""
        try:
            # Calculate category path and level if parent exists
            if category.parent_category_id:
                # Note: Would need to fetch parent category to build path
                pass
            
            result = await self.repo.create_category(category)
            
            # Publish event
            await self.kafka.publish(
                'product.category.created',
                {
                    'category_id': result.category_id,
                    'category_name': result.category_name,
                    'category_slug': result.category_slug,
                    'parent_category_id': result.parent_category_id,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Created product category: {result.category_name}")
            return result
        except Exception as e:
            logger.error(f"Error creating category: {str(e)}")
            raise
    
    async def get_category_tree(
        self,
        parent_id: Optional[int] = None,
        max_depth: int = 3
    ) -> List[Dict[str, Any]]:
        """Get category tree with nested children."""
        try:
            categories = await self.repo.get_category_tree(parent_id)
            
            result = []
            for category in categories:
                category_dict = category.dict()
                
                # Recursively get children if not at max depth
                if max_depth > 0:
                    children = await self.get_category_tree(
                        category.category_id,
                        max_depth - 1
                    )
                    category_dict['children'] = children
                
                result.append(category_dict)
            
            return result
        except Exception as e:
            logger.error(f"Error getting category tree: {str(e)}")
            raise
    
    async def assign_product_to_categories(
        self,
        product_id: str,
        category_ids: List[int],
        primary_category_id: int
    ) -> List[ProductCategoryMapping]:
        """Assign a product to multiple categories."""
        try:
            results = []
            
            for category_id in category_ids:
                is_primary = (category_id == primary_category_id)
                result = await self.repo.assign_product_to_category(
                    product_id,
                    category_id,
                    is_primary
                )
                results.append(result)
            
            # Publish event
            await self.kafka.publish(
                'product.categories.assigned',
                {
                    'product_id': product_id,
                    'category_ids': category_ids,
                    'primary_category_id': primary_category_id,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Assigned product {product_id} to {len(category_ids)} categories")
            return results
        except Exception as e:
            logger.error(f"Error assigning product to categories: {str(e)}")
            raise


# =====================================================
# 5. PRODUCT ATTRIBUTE SERVICE
# =====================================================

class ProductAttributeService:
    """Service for product attribute business logic."""
    
    def __init__(self, db_manager: DatabaseManager, kafka_client: KafkaClient):
        """Initialize service with dependencies."""
        self.db = db_manager
        self.kafka = kafka_client
        self.repo = ProductAttributeRepository(db_manager)
    
    async def create_attribute_group(
        self,
        group: AttributeGroupCreate
    ) -> AttributeGroup:
        """Create an attribute group."""
        try:
            result = await self.repo.create_attribute_group(group)
            
            logger.info(f"Created attribute group: {result.group_name}")
            return result
        except Exception as e:
            logger.error(f"Error creating attribute group: {str(e)}")
            raise
    
    async def create_product_attribute(
        self,
        attribute: ProductAttributeCreate
    ) -> ProductAttribute:
        """Create a product attribute."""
        try:
            result = await self.repo.create_product_attribute(attribute)
            
            logger.info(f"Created product attribute: {result.attribute_name}")
            return result
        except Exception as e:
            logger.error(f"Error creating product attribute: {str(e)}")
            raise
    
    async def set_product_attributes(
        self,
        product_id: str,
        attributes: List[ProductAttributeValueCreate]
    ) -> List[ProductAttributeValue]:
        """Set multiple attributes for a product."""
        try:
            results = []
            
            for attr_value in attributes:
                attr_value.product_id = product_id
                result = await self.repo.set_product_attribute_value(attr_value)
                results.append(result)
            
            # Publish event
            await self.kafka.publish(
                'product.attributes.updated',
                {
                    'product_id': product_id,
                    'attribute_count': len(results),
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Set {len(results)} attributes for product: {product_id}")
            return results
        except Exception as e:
            logger.error(f"Error setting product attributes: {str(e)}")
            raise
    
    async def get_product_specifications(
        self,
        product_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get product specifications grouped by attribute group."""
        try:
            attributes = await self.repo.get_product_attributes(product_id)
            
            # Group by attribute group
            grouped = {}
            for attr in attributes:
                group_name = attr.get('group_name', 'General')
                if group_name not in grouped:
                    grouped[group_name] = []
                grouped[group_name].append(attr)
            
            return grouped
        except Exception as e:
            logger.error(f"Error getting product specifications: {str(e)}")
            raise


# Continue in next part...




# =====================================================
# 6. PRODUCT PRICING SERVICE
# =====================================================

class ProductPricingService:
    """Service for product pricing business logic."""
    
    def __init__(self, db_manager: DatabaseManager, kafka_client: KafkaClient):
        """Initialize service with dependencies."""
        self.db = db_manager
        self.kafka = kafka_client
        self.repo = ProductPricingRepository(db_manager)
    
    async def create_pricing_rule(
        self,
        rule: PricingRuleCreate,
        tiers: Optional[List[PricingTierCreate]] = None
    ) -> Dict[str, Any]:
        """Create a pricing rule with optional tiers."""
        try:
            # Create rule
            rule_result = await self.repo.create_pricing_rule(rule)
            
            # Add tiers if provided
            tier_results = []
            if tiers:
                for tier in tiers:
                    tier_result = await self.repo.add_pricing_tier(tier, rule_result.rule_id)
                    tier_results.append(tier_result)
            
            # Publish event
            await self.kafka.publish(
                'product.pricing.rule.created',
                {
                    'rule_id': str(rule_result.rule_id),
                    'product_id': rule_result.product_id,
                    'rule_type': rule_result.rule_type,
                    'tier_count': len(tier_results),
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Created pricing rule: {rule_result.rule_name}")
            
            return {
                'rule': rule_result,
                'tiers': tier_results
            }
        except Exception as e:
            logger.error(f"Error creating pricing rule: {str(e)}")
            raise
    
    async def update_product_price(
        self,
        product_id: str,
        old_price: Decimal,
        new_price: Decimal,
        change_reason: str,
        changed_by: str
    ) -> PriceHistory:
        """Update product price and record in history."""
        try:
            # Record price change
            change = PriceHistoryCreate(
                product_id=product_id,
                old_price=old_price,
                new_price=new_price,
                change_reason=change_reason,
                changed_by=changed_by,
                change_type='manual',
                effective_date=datetime.now()
            )
            
            result = await self.repo.record_price_change(change)
            
            # Publish event
            await self.kafka.publish(
                'product.price.updated',
                {
                    'product_id': product_id,
                    'old_price': str(old_price),
                    'new_price': str(new_price),
                    'change_reason': change_reason,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Updated price for product {product_id}: {old_price} -> {new_price}")
            return result
        except Exception as e:
            logger.error(f"Error updating product price: {str(e)}")
            raise
    
    async def track_competitor_prices(
        self,
        product_id: str,
        competitor_prices: List[CompetitorPriceCreate]
    ) -> List[CompetitorPrice]:
        """Track competitor prices for a product."""
        try:
            results = []
            
            for comp_price in competitor_prices:
                comp_price.product_id = product_id
                result = await self.repo.track_competitor_price(comp_price)
                results.append(result)
            
            logger.info(f"Tracked {len(results)} competitor prices for product: {product_id}")
            return results
        except Exception as e:
            logger.error(f"Error tracking competitor prices: {str(e)}")
            raise
    
    async def calculate_effective_price(
        self,
        product_id: str,
        quantity: int = 1,
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate effective price based on active rules."""
        try:
            # Get active pricing rules
            rules = await self.repo.get_active_pricing_rules(product_id)
            
            # Sort by priority
            rules.sort(key=lambda x: x.priority, reverse=True)
            
            # Apply rules (simplified logic)
            base_price = Decimal('0.00')  # Would fetch from product
            effective_price = base_price
            applied_rules = []
            
            for rule in rules:
                # Apply rule logic based on type
                # This is simplified - actual implementation would be more complex
                applied_rules.append({
                    'rule_id': str(rule.rule_id),
                    'rule_name': rule.rule_name,
                    'rule_type': rule.rule_type
                })
            
            return {
                'base_price': base_price,
                'effective_price': effective_price,
                'discount': base_price - effective_price,
                'applied_rules': applied_rules
            }
        except Exception as e:
            logger.error(f"Error calculating effective price: {str(e)}")
            raise


# =====================================================
# 7. PRODUCT REVIEW SERVICE
# =====================================================

class ProductReviewService:
    """Service for product review business logic."""
    
    def __init__(self, db_manager: DatabaseManager, kafka_client: KafkaClient):
        """Initialize service with dependencies."""
        self.db = db_manager
        self.kafka = kafka_client
        self.repo = ProductReviewRepository(db_manager)
    
    async def create_review(
        self,
        review: ProductReviewCreate,
        images: Optional[List[ReviewImageCreate]] = None
    ) -> Dict[str, Any]:
        """Create a product review with optional images."""
        try:
            # Create review
            review_result = await self.repo.create_review(review)
            
            # Add images if provided
            image_results = []
            if images:
                for image in images:
                    image.review_id = review_result.review_id
                    image_result = await self.repo.add_review_image(image)
                    image_results.append(image_result)
            
            # Publish event
            await self.kafka.publish(
                'product.review.created',
                {
                    'review_id': str(review_result.review_id),
                    'product_id': review_result.product_id,
                    'customer_id': review_result.customer_id,
                    'rating': review_result.rating,
                    'is_verified_purchase': review_result.is_verified_purchase,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Created review for product: {review_result.product_id}")
            
            return {
                'review': review_result,
                'images': image_results
            }
        except Exception as e:
            logger.error(f"Error creating review: {str(e)}")
            raise
    
    async def moderate_review(
        self,
        review_id: UUID,
        approved: bool,
        approved_by: str
    ) -> bool:
        """Moderate (approve/reject) a review."""
        try:
            if approved:
                result = await self.repo.approve_review(review_id, approved_by)
                
                if result:
                    # Publish event
                    await self.kafka.publish(
                        'product.review.approved',
                        {
                            'review_id': str(review_id),
                            'approved_by': approved_by,
                            'timestamp': datetime.now().isoformat()
                        }
                    )
                
                logger.info(f"Approved review: {review_id}")
                return result
            else:
                # Would implement rejection logic here
                logger.info(f"Rejected review: {review_id}")
                return True
        except Exception as e:
            logger.error(f"Error moderating review: {str(e)}")
            raise
    
    async def vote_on_review(
        self,
        review_id: UUID,
        customer_id: str,
        helpful: bool
    ) -> ReviewVote:
        """Vote on a review as helpful or not helpful."""
        try:
            vote = ReviewVoteCreate(
                review_id=review_id,
                customer_id=customer_id,
                vote_type='helpful' if helpful else 'not_helpful'
            )
            
            result = await self.repo.vote_review(vote)
            
            logger.info(f"Recorded vote on review: {review_id}")
            return result
        except Exception as e:
            logger.error(f"Error voting on review: {str(e)}")
            raise
    
    async def add_seller_response(
        self,
        review_id: UUID,
        response_text: str,
        responded_by: str
    ) -> ReviewResponse:
        """Add seller response to a review."""
        try:
            response = ReviewResponseCreate(
                response_text=response_text,
                responded_by=responded_by
            )
            
            result = await self.repo.add_seller_response(response, review_id)
            
            # Publish event
            await self.kafka.publish(
                'product.review.response.added',
                {
                    'review_id': str(review_id),
                    'response_id': str(result.response_id),
                    'responded_by': responded_by,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Added seller response to review: {review_id}")
            return result
        except Exception as e:
            logger.error(f"Error adding seller response: {str(e)}")
            raise
    
    async def get_product_review_summary(
        self,
        product_id: str
    ) -> Dict[str, Any]:
        """Get review summary for a product."""
        try:
            # Get reviews
            reviews = await self.repo.get_product_reviews(product_id, approved_only=True)
            
            # Calculate statistics
            total_reviews = len(reviews)
            if total_reviews == 0:
                return {
                    'total_reviews': 0,
                    'average_rating': 0.0,
                    'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                }
            
            total_rating = sum(r.rating for r in reviews)
            average_rating = total_rating / total_reviews
            
            # Rating distribution
            rating_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for review in reviews:
                rating_dist[review.rating] += 1
            
            return {
                'total_reviews': total_reviews,
                'average_rating': round(average_rating, 2),
                'rating_distribution': rating_dist,
                'verified_purchase_count': sum(1 for r in reviews if r.is_verified_purchase)
            }
        except Exception as e:
            logger.error(f"Error getting review summary: {str(e)}")
            raise


# =====================================================
# 8. PRODUCT INVENTORY SERVICE
# =====================================================

class ProductInventoryService:
    """Service for product inventory business logic."""
    
    def __init__(self, db_manager: DatabaseManager, kafka_client: KafkaClient):
        """Initialize service with dependencies."""
        self.db = db_manager
        self.kafka = kafka_client
        self.repo = ProductInventoryRepository(db_manager)
    
    async def create_inventory(
        self,
        inventory: ProductInventoryCreate
    ) -> ProductInventory:
        """Create inventory record for a product at a location."""
        try:
            result = await self.repo.create_inventory(inventory)
            
            # Publish event
            await self.kafka.publish(
                'product.inventory.created',
                {
                    'inventory_id': str(result.inventory_id),
                    'product_id': result.product_id,
                    'location_id': result.location_id,
                    'quantity_available': result.quantity_available,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Created inventory for product {result.product_id} at {result.location_id}")
            return result
        except Exception as e:
            logger.error(f"Error creating inventory: {str(e)}")
            raise
    
    async def record_inventory_transaction(
        self,
        transaction: InventoryTransactionCreate
    ) -> InventoryTransaction:
        """Record an inventory transaction."""
        try:
            result = await self.repo.record_transaction(transaction)
            
            # Publish event
            await self.kafka.publish(
                'product.inventory.transaction',
                {
                    'transaction_id': str(result.transaction_id),
                    'product_id': result.product_id,
                    'location_id': result.location_id,
                    'transaction_type': result.transaction_type,
                    'quantity': result.quantity,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Recorded inventory transaction: {result.transaction_type}")
            return result
        except Exception as e:
            logger.error(f"Error recording inventory transaction: {str(e)}")
            raise
    
    async def reserve_inventory(
        self,
        product_id: str,
        location_id: str,
        order_id: str,
        quantity: int,
        reserved_until: datetime
    ) -> InventoryReservation:
        """Reserve inventory for an order."""
        try:
            reservation = InventoryReservationCreate(
                product_id=product_id,
                location_id=location_id,
                order_id=order_id,
                quantity_reserved=quantity,
                reserved_until=reserved_until
            )
            
            result = await self.repo.create_reservation(reservation)
            
            # Publish event
            await self.kafka.publish(
                'product.inventory.reserved',
                {
                    'reservation_id': str(result.reservation_id),
                    'product_id': product_id,
                    'location_id': location_id,
                    'order_id': order_id,
                    'quantity': quantity,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Reserved {quantity} units of product {product_id} for order {order_id}")
            return result
        except Exception as e:
            logger.error(f"Error reserving inventory: {str(e)}")
            raise
    
    async def release_inventory_reservation(
        self,
        reservation_id: UUID
    ) -> bool:
        """Release an inventory reservation."""
        try:
            result = await self.repo.release_reservation(reservation_id)
            
            if result:
                # Publish event
                await self.kafka.publish(
                    'product.inventory.reservation.released',
                    {
                        'reservation_id': str(reservation_id),
                        'timestamp': datetime.now().isoformat()
                    }
                )
            
            logger.info(f"Released inventory reservation: {reservation_id}")
            return result
        except Exception as e:
            logger.error(f"Error releasing inventory reservation: {str(e)}")
            raise
    
    async def check_inventory_availability(
        self,
        product_id: str,
        quantity: int,
        location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check if inventory is available for a product."""
        try:
            # Get inventory summary
            summary = await self.repo.get_inventory_summary(product_id)
            
            if not summary:
                return {
                    'available': False,
                    'reason': 'No inventory found'
                }
            
            total_available = summary.get('total_available', 0)
            
            if total_available >= quantity:
                return {
                    'available': True,
                    'total_available': total_available,
                    'requested_quantity': quantity
                }
            else:
                return {
                    'available': False,
                    'reason': 'Insufficient inventory',
                    'total_available': total_available,
                    'requested_quantity': quantity,
                    'shortfall': quantity - total_available
                }
        except Exception as e:
            logger.error(f"Error checking inventory availability: {str(e)}")
            raise


# =====================================================
# 9. PRODUCT RELATIONSHIP SERVICE
# =====================================================

class ProductRelationshipService:
    """Service for product relationship business logic."""
    
    def __init__(self, db_manager: DatabaseManager, kafka_client: KafkaClient):
        """Initialize service with dependencies."""
        self.db = db_manager
        self.kafka = kafka_client
        self.repo = ProductRelationshipRepository(db_manager)
    
    async def create_relationship(
        self,
        relationship: ProductRelationshipCreate
    ) -> ProductRelationship:
        """Create a product relationship."""
        try:
            result = await self.repo.create_relationship(relationship)
            
            logger.info(f"Created product relationship: {relationship.relationship_type}")
            return result
        except Exception as e:
            logger.error(f"Error creating product relationship: {str(e)}")
            raise
    
    async def get_related_products(
        self,
        product_id: str,
        relationship_type: Optional[str] = None
    ) -> List[ProductRelationship]:
        """Get related products."""
        try:
            return await self.repo.get_related_products(product_id, relationship_type)
        except Exception as e:
            logger.error(f"Error getting related products: {str(e)}")
            raise
    
    async def generate_recommendations(
        self,
        product_id: str,
        recommendation_type: str = 'ai_based',
        limit: int = 10
    ) -> List[ProductRecommendation]:
        """Generate product recommendations (placeholder for AI integration)."""
        try:
            # This is a placeholder - actual implementation would use AI/ML
            # For now, just return existing recommendations
            recommendations = await self.repo.get_recommendations(
                product_id,
                recommendation_type,
                limit
            )
            
            logger.info(f"Generated {len(recommendations)} recommendations for product: {product_id}")
            return recommendations
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            raise
    
    async def create_recommendation(
        self,
        recommendation: ProductRecommendationCreate
    ) -> ProductRecommendation:
        """Create a product recommendation."""
        try:
            result = await self.repo.create_recommendation(recommendation)
            
            logger.info(f"Created product recommendation: {recommendation.recommendation_type}")
            return result
        except Exception as e:
            logger.error(f"Error creating recommendation: {str(e)}")
            raise


# =====================================================
# 10. PRODUCT LIFECYCLE SERVICE
# =====================================================

class ProductLifecycleService:
    """Service for product lifecycle business logic."""
    
    def __init__(self, db_manager: DatabaseManager, kafka_client: KafkaClient):
        """Initialize service with dependencies."""
        self.db = db_manager
        self.kafka = kafka_client
        self.repo = ProductLifecycleRepository(db_manager)
    
    async def update_product_status(
        self,
        product_id: str,
        status: ProductStatus,
        status_reason: str,
        changed_by: str
    ) -> ProductLifecycle:
        """Update product lifecycle status."""
        try:
            lifecycle = ProductLifecycleCreate(
                product_id=product_id,
                status=status,
                status_reason=status_reason,
                changed_by=changed_by
            )
            
            result = await self.repo.create_lifecycle_entry(lifecycle)
            
            # Publish event
            await self.kafka.publish(
                'product.status.changed',
                {
                    'product_id': product_id,
                    'status': status,
                    'status_reason': status_reason,
                    'changed_by': changed_by,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Updated product status: {product_id} -> {status}")
            return result
        except Exception as e:
            logger.error(f"Error updating product status: {str(e)}")
            raise
    
    async def create_product_version(
        self,
        product_id: str,
        version_number: str,
        version_data: Dict[str, Any],
        change_summary: str,
        created_by: str
    ) -> ProductVersion:
        """Create a product version snapshot."""
        try:
            version = ProductVersionCreate(
                product_id=product_id,
                version_number=version_number,
                version_data=version_data,
                change_summary=change_summary,
                created_by=created_by
            )
            
            result = await self.repo.create_version(version)
            
            logger.info(f"Created product version: {version_number}")
            return result
        except Exception as e:
            logger.error(f"Error creating product version: {str(e)}")
            raise
    
    async def record_product_change(
        self,
        product_id: str,
        field_name: str,
        old_value: Optional[str],
        new_value: str,
        change_type: str,
        changed_by: str,
        change_reason: Optional[str] = None
    ) -> ProductChange:
        """Record a product change."""
        try:
            change = ProductChangeCreate(
                product_id=product_id,
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                change_type=change_type,
                changed_by=changed_by,
                change_reason=change_reason
            )
            
            result = await self.repo.record_change(change)
            
            logger.info(f"Recorded product change: {field_name}")
            return result
        except Exception as e:
            logger.error(f"Error recording product change: {str(e)}")
            raise
    
    async def request_approval(
        self,
        product_id: str,
        approval_type: str,
        requested_by: str,
        approval_data: Dict[str, Any]
    ) -> ProductApproval:
        """Request approval for product changes."""
        try:
            approval = ProductApprovalCreate(
                product_id=product_id,
                approval_type=approval_type,
                requested_by=requested_by,
                approval_data=approval_data
            )
            
            result = await self.repo.create_approval_request(approval)
            
            # Publish event
            await self.kafka.publish(
                'product.approval.requested',
                {
                    'approval_id': str(result.approval_id),
                    'product_id': product_id,
                    'approval_type': approval_type,
                    'requested_by': requested_by,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Requested approval for product: {product_id}")
            return result
        except Exception as e:
            logger.error(f"Error requesting approval: {str(e)}")
            raise
    
    async def review_approval(
        self,
        approval_id: UUID,
        approved: bool,
        reviewed_by: str,
        review_notes: Optional[str] = None
    ) -> bool:
        """Review an approval request."""
        try:
            status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
            
            result = await self.repo.review_approval(
                approval_id,
                status,
                reviewed_by,
                review_notes
            )
            
            if result:
                # Publish event
                await self.kafka.publish(
                    'product.approval.reviewed',
                    {
                        'approval_id': str(approval_id),
                        'status': status,
                        'reviewed_by': reviewed_by,
                        'timestamp': datetime.now().isoformat()
                    }
                )
            
            logger.info(f"Reviewed approval: {approval_id} -> {status}")
            return result
        except Exception as e:
            logger.error(f"Error reviewing approval: {str(e)}")
            raise

