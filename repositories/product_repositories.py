"""
Product Agent Repository Layer

This module provides data access layer for all Product Agent entities.
Implements repository pattern for clean separation of concerns.

Author: Multi-Agent E-Commerce System
Date: January 2025
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import select, update, delete, and_, or_, func, desc, asc
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from shared.database import DatabaseManager
from shared.product_models import (
    # Variant models
    VariantAttribute, ProductVariant, VariantAttributeValue, VariantPricing,
    VariantAttributeCreate, ProductVariantCreate, VariantAttributeValueCreate,
    VariantPricingCreate, VariantAttributeFilter,
    
    # Bundle models
    ProductBundle, BundleComponent, BundlePricingRule,
    ProductBundleCreate, BundleComponentCreate, BundlePricingRuleCreate,
    
    # Media models
    ProductImage, ProductMedia, ImageVariant,
    ProductImageCreate, ProductMediaCreate, ImageVariantCreate,
    
    # Category models
    ProductCategory, CategoryAttribute, ProductCategoryMapping,
    ProductCategoryCreate, CategoryAttributeCreate,
    
    # Attribute models
    AttributeGroup, ProductAttribute, ProductAttributeValue,
    AttributeGroupCreate, ProductAttributeCreate, ProductAttributeValueCreate,
    
    # Pricing models
    PricingRule, PricingTier, PriceHistory, CompetitorPrice,
    PricingRuleCreate, PricingTierCreate, PriceHistoryCreate, CompetitorPriceCreate,
    
    # Review models
    ProductReview, ReviewImage, ReviewVote, ReviewResponse,
    ProductReviewCreate, ReviewImageCreate, ReviewVoteCreate, ReviewResponseCreate,
    
    # Inventory models
    ProductInventory, InventoryTransaction, InventoryReservation, InventoryBatch,
    ProductInventoryCreate, InventoryTransactionCreate, InventoryReservationCreate,
    InventoryBatchCreate,
    
    # Relationship models
    ProductRelationship, ProductRecommendation,
    ProductRelationshipCreate, ProductRecommendationCreate,
    
    # Lifecycle models
    ProductLifecycle, ProductVersion, ProductChange, ProductApproval,
    ProductLifecycleCreate, ProductVersionCreate, ProductChangeCreate,
    ProductApprovalCreate,
    
    # Enums
    ProductStatus, ApprovalStatus, InventoryTransactionType
)


# =====================================================
# 1. PRODUCT VARIANT REPOSITORY
# =====================================================

class ProductVariantRepository:
    """Repository for product variant operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize repository with database manager."""
        self.db = db_manager
    
    async def create_variant_attribute(
        self,
        attribute: VariantAttributeCreate
    ) -> VariantAttribute:
        """Create a new variant attribute."""
        query = """
            INSERT INTO variant_attributes (attribute_name, attribute_type, display_order, is_required)
            VALUES ($1, $2, $3, $4)
            RETURNING attribute_id, attribute_name, attribute_type, display_order, 
                      is_required, created_at
        """
        row = await self.db.fetchrow(
            query,
            attribute.attribute_name,
            attribute.attribute_type,
            attribute.display_order,
            attribute.is_required
        )
        return VariantAttribute(**dict(row))
    
    async def get_variant_attributes(
        self,
        filters: Optional[VariantAttributeFilter] = None
    ) -> List[VariantAttribute]:
        """Get variant attributes with optional filters."""
        query = "SELECT * FROM variant_attributes WHERE 1=1"
        params = []
        
        if filters:
            if filters.attribute_type:
                query += f" AND attribute_type = ${len(params) + 1}"
                params.append(filters.attribute_type)
            if filters.is_required is not None:
                query += f" AND is_required = ${len(params) + 1}"
                params.append(filters.is_required)
        
        query += " ORDER BY display_order, attribute_name"
        rows = await self.db.fetch(query, *params)
        return [VariantAttribute(**dict(row)) for row in rows]
    
    async def create_product_variant(
        self,
        variant: ProductVariantCreate
    ) -> ProductVariant:
        """Create a new product variant."""
        query = """
            INSERT INTO product_variants (
                product_id, parent_variant_id, variant_sku, variant_name,
                is_master, is_active, sort_order
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING variant_id, product_id, parent_variant_id, variant_sku,
                      variant_name, is_master, is_active, sort_order, created_at, updated_at
        """
        row = await self.db.fetchrow(
            query,
            variant.product_id,
            variant.parent_variant_id,
            variant.variant_sku,
            variant.variant_name,
            variant.is_master,
            variant.is_active,
            variant.sort_order
        )
        return ProductVariant(**dict(row))
    
    async def get_product_variants(
        self,
        product_id: str,
        include_inactive: bool = False
    ) -> List[ProductVariant]:
        """Get all variants for a product."""
        query = """
            SELECT * FROM product_variants
            WHERE product_id = $1
        """
        if not include_inactive:
            query += " AND is_active = true"
        
        query += " ORDER BY sort_order, variant_name"
        rows = await self.db.fetch(query, product_id)
        return [ProductVariant(**dict(row)) for row in rows]
    
    async def get_variant_by_id(self, variant_id: UUID) -> Optional[ProductVariant]:
        """Get variant by ID."""
        query = "SELECT * FROM product_variants WHERE variant_id = $1"
        row = await self.db.fetchrow(query, variant_id)
        return ProductVariant(**dict(row)) if row else None
    
    async def add_variant_attribute_value(
        self,
        value: VariantAttributeValueCreate
    ) -> VariantAttributeValue:
        """Add attribute value to a variant."""
        query = """
            INSERT INTO variant_attribute_values (variant_id, attribute_id, attribute_value)
            VALUES ($1, $2, $3)
            RETURNING value_id, variant_id, attribute_id, attribute_value, created_at
        """
        row = await self.db.fetchrow(
            query,
            value.variant_id,
            value.attribute_id,
            value.attribute_value
        )
        return VariantAttributeValue(**dict(row))
    
    async def get_variant_attribute_values(
        self,
        variant_id: UUID
    ) -> List[VariantAttributeValue]:
        """Get all attribute values for a variant."""
        query = """
            SELECT vav.*, va.attribute_name, va.attribute_type
            FROM variant_attribute_values vav
            JOIN variant_attributes va ON vav.attribute_id = va.attribute_id
            WHERE vav.variant_id = $1
            ORDER BY va.display_order
        """
        rows = await self.db.fetch(query, variant_id)
        return [VariantAttributeValue(**dict(row)) for row in rows]
    
    async def set_variant_pricing(
        self,
        pricing: VariantPricingCreate
    ) -> VariantPricing:
        """Set pricing for a variant."""
        query = """
            INSERT INTO variant_pricing (
                variant_id, base_price, sale_price, cost_price,
                price_currency, effective_from, effective_to
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (variant_id) DO UPDATE SET
                base_price = EXCLUDED.base_price,
                sale_price = EXCLUDED.sale_price,
                cost_price = EXCLUDED.cost_price,
                price_currency = EXCLUDED.price_currency,
                effective_from = EXCLUDED.effective_from,
                effective_to = EXCLUDED.effective_to,
                updated_at = CURRENT_TIMESTAMP
            RETURNING pricing_id, variant_id, base_price, sale_price, cost_price,
                      price_currency, effective_from, effective_to, created_at, updated_at
        """
        row = await self.db.fetchrow(
            query,
            pricing.variant_id,
            pricing.base_price,
            pricing.sale_price,
            pricing.cost_price,
            pricing.price_currency,
            pricing.effective_from,
            pricing.effective_to
        )
        return VariantPricing(**dict(row))
    
    async def get_variant_pricing(self, variant_id: UUID) -> Optional[VariantPricing]:
        """Get pricing for a variant."""
        query = "SELECT * FROM variant_pricing WHERE variant_id = $1"
        row = await self.db.fetchrow(query, variant_id)
        return VariantPricing(**dict(row)) if row else None


# =====================================================
# 2. PRODUCT BUNDLE REPOSITORY
# =====================================================

class ProductBundleRepository:
    """Repository for product bundle operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize repository with database manager."""
        self.db = db_manager
    
    async def create_bundle(self, bundle: ProductBundleCreate) -> ProductBundle:
        """Create a new product bundle."""
        query = """
            INSERT INTO product_bundles (
                bundle_name, bundle_description, bundle_type, bundle_sku,
                is_active, valid_from, valid_to, min_quantity, max_quantity
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING bundle_id, bundle_name, bundle_description, bundle_type,
                      bundle_sku, is_active, valid_from, valid_to, min_quantity,
                      max_quantity, created_at, updated_at
        """
        row = await self.db.fetchrow(
            query,
            bundle.bundle_name,
            bundle.bundle_description,
            bundle.bundle_type,
            bundle.bundle_sku,
            bundle.is_active,
            bundle.valid_from,
            bundle.valid_to,
            bundle.min_quantity,
            bundle.max_quantity
        )
        return ProductBundle(**dict(row))
    
    async def add_bundle_component(
        self,
        component: BundleComponentCreate
    ) -> BundleComponent:
        """Add a product to a bundle."""
        query = """
            INSERT INTO bundle_components (
                bundle_id, product_id, variant_id, quantity,
                is_required, display_order
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING component_id, bundle_id, product_id, variant_id,
                      quantity, is_required, display_order, created_at
        """
        row = await self.db.fetchrow(
            query,
            component.bundle_id,
            component.product_id,
            component.variant_id,
            component.quantity,
            component.is_required,
            component.display_order
        )
        return BundleComponent(**dict(row))
    
    async def get_bundle_components(
        self,
        bundle_id: UUID
    ) -> List[BundleComponent]:
        """Get all components of a bundle."""
        query = """
            SELECT * FROM bundle_components
            WHERE bundle_id = $1
            ORDER BY display_order, component_id
        """
        rows = await self.db.fetch(query, bundle_id)
        return [BundleComponent(**dict(row)) for row in rows]
    
    async def set_bundle_pricing_rule(
        self,
        rule: BundlePricingRuleCreate
    ) -> BundlePricingRule:
        """Set pricing rule for a bundle."""
        query = """
            INSERT INTO bundle_pricing_rules (
                bundle_id, pricing_strategy, fixed_price, discount_percentage,
                discount_amount, rule_config
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING rule_id, bundle_id, pricing_strategy, fixed_price,
                      discount_percentage, discount_amount, rule_config, created_at
        """
        row = await self.db.fetchrow(
            query,
            rule.bundle_id,
            rule.pricing_strategy,
            rule.fixed_price,
            rule.discount_percentage,
            rule.discount_amount,
            rule.rule_config
        )
        return BundlePricingRule(**dict(row))
    
    async def get_active_bundles(self) -> List[ProductBundle]:
        """Get all active bundles."""
        query = """
            SELECT * FROM product_bundles
            WHERE is_active = true
              AND (valid_from IS NULL OR valid_from <= CURRENT_TIMESTAMP)
              AND (valid_to IS NULL OR valid_to >= CURRENT_TIMESTAMP)
            ORDER BY bundle_name
        """
        rows = await self.db.fetch(query)
        return [ProductBundle(**dict(row)) for row in rows]


# =====================================================
# 3. PRODUCT MEDIA REPOSITORY
# =====================================================

class ProductMediaRepository:
    """Repository for product media operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize repository with database manager."""
        self.db = db_manager
    
    async def add_product_image(self, image: ProductImageCreate) -> ProductImage:
        """Add an image to a product."""
        query = """
            INSERT INTO product_images (
                product_id, image_url, image_alt_text, image_caption,
                is_primary, display_order
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING image_id, product_id, image_url, image_alt_text,
                      image_caption, is_primary, display_order, created_at
        """
        row = await self.db.fetchrow(
            query,
            image.product_id,
            image.image_url,
            image.image_alt_text,
            image.image_caption,
            image.is_primary,
            image.display_order
        )
        return ProductImage(**dict(row))
    
    async def get_product_images(self, product_id: str) -> List[ProductImage]:
        """Get all images for a product."""
        query = """
            SELECT * FROM product_images
            WHERE product_id = $1
            ORDER BY is_primary DESC, display_order, created_at
        """
        rows = await self.db.fetch(query, product_id)
        return [ProductImage(**dict(row)) for row in rows]
    
    async def set_primary_image(self, product_id: str, image_id: UUID) -> bool:
        """Set an image as primary for a product."""
        # First, unset all primary images for the product
        await self.db.execute(
            "UPDATE product_images SET is_primary = false WHERE product_id = $1",
            product_id
        )
        # Then set the specified image as primary
        result = await self.db.execute(
            "UPDATE product_images SET is_primary = true WHERE image_id = $1",
            image_id
        )
        return result == "UPDATE 1"
    
    async def add_product_media(self, media: ProductMediaCreate) -> ProductMedia:
        """Add media (video, 360, PDF) to a product."""
        query = """
            INSERT INTO product_media (
                product_id, media_type, media_url, media_title,
                media_description, thumbnail_url, duration_seconds, file_size_bytes
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING media_id, product_id, media_type, media_url, media_title,
                      media_description, thumbnail_url, duration_seconds,
                      file_size_bytes, created_at
        """
        row = await self.db.fetchrow(
            query,
            media.product_id,
            media.media_type,
            media.media_url,
            media.media_title,
            media.media_description,
            media.thumbnail_url,
            media.duration_seconds,
            media.file_size_bytes
        )
        return ProductMedia(**dict(row))
    
    async def get_product_media(
        self,
        product_id: str,
        media_type: Optional[str] = None
    ) -> List[ProductMedia]:
        """Get media for a product, optionally filtered by type."""
        query = "SELECT * FROM product_media WHERE product_id = $1"
        params = [product_id]
        
        if media_type:
            query += " AND media_type = $2"
            params.append(media_type)
        
        query += " ORDER BY created_at"
        rows = await self.db.fetch(query, *params)
        return [ProductMedia(**dict(row)) for row in rows]


# =====================================================
# 4. PRODUCT CATEGORY REPOSITORY
# =====================================================

class ProductCategoryRepository:
    """Repository for product category operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize repository with database manager."""
        self.db = db_manager
    
    async def create_category(self, category: ProductCategoryCreate) -> ProductCategory:
        """Create a new product category."""
        query = """
            INSERT INTO product_categories (
                category_name, category_slug, category_description,
                parent_category_id, category_path, category_level,
                display_order, is_active, seo_title, seo_description,
                seo_keywords, category_image_url
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING category_id, category_name, category_slug, category_description,
                      parent_category_id, category_path, category_level, display_order,
                      is_active, seo_title, seo_description, seo_keywords,
                      category_image_url, created_at, updated_at
        """
        row = await self.db.fetchrow(
            query,
            category.category_name,
            category.category_slug,
            category.category_description,
            category.parent_category_id,
            category.category_path,
            category.category_level,
            category.display_order,
            category.is_active,
            category.seo_title,
            category.seo_description,
            category.seo_keywords,
            category.category_image_url
        )
        return ProductCategory(**dict(row))
    
    async def get_category_tree(self, parent_id: Optional[int] = None) -> List[ProductCategory]:
        """Get category tree starting from parent."""
        if parent_id is None:
            query = """
                SELECT * FROM product_categories
                WHERE parent_category_id IS NULL AND is_active = true
                ORDER BY display_order, category_name
            """
            rows = await self.db.fetch(query)
        else:
            query = """
                SELECT * FROM product_categories
                WHERE parent_category_id = $1 AND is_active = true
                ORDER BY display_order, category_name
            """
            rows = await self.db.fetch(query, parent_id)
        
        return [ProductCategory(**dict(row)) for row in rows]
    
    async def assign_product_to_category(
        self,
        product_id: str,
        category_id: int,
        is_primary: bool = False
    ) -> ProductCategoryMapping:
        """Assign a product to a category."""
        query = """
            INSERT INTO product_category_mapping (product_id, category_id, is_primary)
            VALUES ($1, $2, $3)
            RETURNING mapping_id, product_id, category_id, is_primary, created_at
        """
        row = await self.db.fetchrow(query, product_id, category_id, is_primary)
        return ProductCategoryMapping(**dict(row))
    
    async def get_product_categories(self, product_id: str) -> List[ProductCategory]:
        """Get all categories for a product."""
        query = """
            SELECT c.* FROM product_categories c
            JOIN product_category_mapping pcm ON c.category_id = pcm.category_id
            WHERE pcm.product_id = $1
            ORDER BY pcm.is_primary DESC, c.category_name
        """
        rows = await self.db.fetch(query, product_id)
        return [ProductCategory(**dict(row)) for row in rows]


# =====================================================
# 5. PRODUCT ATTRIBUTE REPOSITORY
# =====================================================

class ProductAttributeRepository:
    """Repository for product attribute operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize repository with database manager."""
        self.db = db_manager
    
    async def create_attribute_group(
        self,
        group: AttributeGroupCreate
    ) -> AttributeGroup:
        """Create an attribute group."""
        query = """
            INSERT INTO attribute_groups (group_name, group_description, display_order)
            VALUES ($1, $2, $3)
            RETURNING group_id, group_name, group_description, display_order, created_at
        """
        row = await self.db.fetchrow(
            query,
            group.group_name,
            group.group_description,
            group.display_order
        )
        return AttributeGroup(**dict(row))
    
    async def create_product_attribute(
        self,
        attribute: ProductAttributeCreate
    ) -> ProductAttribute:
        """Create a product attribute."""
        query = """
            INSERT INTO product_attributes (
                attribute_name, attribute_type, group_id, unit_of_measure,
                is_filterable, is_searchable, is_comparable, validation_rules,
                display_order
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING attribute_id, attribute_name, attribute_type, group_id,
                      unit_of_measure, is_filterable, is_searchable, is_comparable,
                      validation_rules, display_order, created_at
        """
        row = await self.db.fetchrow(
            query,
            attribute.attribute_name,
            attribute.attribute_type,
            attribute.group_id,
            attribute.unit_of_measure,
            attribute.is_filterable,
            attribute.is_searchable,
            attribute.is_comparable,
            attribute.validation_rules,
            attribute.display_order
        )
        return ProductAttribute(**dict(row))
    
    async def set_product_attribute_value(
        self,
        value: ProductAttributeValueCreate
    ) -> ProductAttributeValue:
        """Set attribute value for a product."""
        query = """
            INSERT INTO product_attribute_values (product_id, attribute_id, attribute_value)
            VALUES ($1, $2, $3)
            ON CONFLICT (product_id, attribute_id) DO UPDATE SET
                attribute_value = EXCLUDED.attribute_value,
                updated_at = CURRENT_TIMESTAMP
            RETURNING value_id, product_id, attribute_id, attribute_value,
                      created_at, updated_at
        """
        row = await self.db.fetchrow(
            query,
            value.product_id,
            value.attribute_id,
            value.attribute_value
        )
        return ProductAttributeValue(**dict(row))
    
    async def get_product_attributes(self, product_id: str) -> List[Dict[str, Any]]:
        """Get all attributes and values for a product."""
        query = """
            SELECT 
                pa.attribute_id,
                pa.attribute_name,
                pa.attribute_type,
                pa.unit_of_measure,
                ag.group_name,
                pav.attribute_value
            FROM product_attribute_values pav
            JOIN product_attributes pa ON pav.attribute_id = pa.attribute_id
            LEFT JOIN attribute_groups ag ON pa.group_id = ag.group_id
            WHERE pav.product_id = $1
            ORDER BY ag.display_order, pa.display_order, pa.attribute_name
        """
        rows = await self.db.fetch(query, product_id)
        return [dict(row) for row in rows]


# Continue in next part due to length...




# =====================================================
# 6. PRODUCT PRICING REPOSITORY
# =====================================================

class ProductPricingRepository:
    """Repository for product pricing operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize repository with database manager."""
        self.db = db_manager
    
    async def create_pricing_rule(self, rule: PricingRuleCreate) -> PricingRule:
        """Create a pricing rule."""
        query = """
            INSERT INTO pricing_rules (
                product_id, rule_name, rule_type, rule_config, priority,
                is_active, valid_from, valid_to, created_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING rule_id, product_id, rule_name, rule_type, rule_config,
                      priority, is_active, valid_from, valid_to, created_by,
                      created_at, updated_at
        """
        row = await self.db.fetchrow(
            query,
            rule.product_id,
            rule.rule_name,
            rule.rule_type,
            rule.rule_config,
            rule.priority,
            rule.is_active,
            rule.valid_from,
            rule.valid_to,
            rule.created_by
        )
        return PricingRule(**dict(row))
    
    async def add_pricing_tier(self, tier: PricingTierCreate, rule_id: UUID) -> PricingTier:
        """Add a pricing tier to a rule."""
        query = """
            INSERT INTO pricing_tiers (
                rule_id, min_quantity, max_quantity, price, discount_percentage
            )
            VALUES ($1, $2, $3, $4, $5)
            RETURNING tier_id, rule_id, min_quantity, max_quantity, price,
                      discount_percentage, created_at
        """
        row = await self.db.fetchrow(
            query,
            rule_id,
            tier.min_quantity,
            tier.max_quantity,
            tier.price,
            tier.discount_percentage
        )
        return PricingTier(**dict(row))
    
    async def record_price_change(self, change: PriceHistoryCreate) -> PriceHistory:
        """Record a price change in history."""
        query = """
            INSERT INTO price_history (
                product_id, old_price, new_price, change_reason, changed_by,
                change_type, effective_date
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING history_id, product_id, old_price, new_price, change_reason,
                      changed_by, change_type, effective_date, created_at
        """
        row = await self.db.fetchrow(
            query,
            change.product_id,
            change.old_price,
            change.new_price,
            change.change_reason,
            change.changed_by,
            change.change_type,
            change.effective_date
        )
        return PriceHistory(**dict(row))
    
    async def track_competitor_price(
        self,
        price: CompetitorPriceCreate
    ) -> CompetitorPrice:
        """Track a competitor's price."""
        query = """
            INSERT INTO competitor_prices (
                product_id, competitor_name, competitor_url, competitor_price,
                currency, is_available, last_checked
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING tracking_id, product_id, competitor_name, competitor_url,
                      competitor_price, currency, is_available, last_checked, created_at
        """
        row = await self.db.fetchrow(
            query,
            price.product_id,
            price.competitor_name,
            price.competitor_url,
            price.competitor_price,
            price.currency,
            price.is_available,
            price.last_checked
        )
        return CompetitorPrice(**dict(row))
    
    async def get_active_pricing_rules(
        self,
        product_id: str
    ) -> List[PricingRule]:
        """Get active pricing rules for a product."""
        query = """
            SELECT * FROM pricing_rules
            WHERE product_id = $1
              AND is_active = true
              AND (valid_from IS NULL OR valid_from <= CURRENT_TIMESTAMP)
              AND (valid_to IS NULL OR valid_to >= CURRENT_TIMESTAMP)
            ORDER BY priority DESC, created_at
        """
        rows = await self.db.fetch(query, product_id)
        return [PricingRule(**dict(row)) for row in rows]


# =====================================================
# 7. PRODUCT REVIEW REPOSITORY
# =====================================================

class ProductReviewRepository:
    """Repository for product review operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize repository with database manager."""
        self.db = db_manager
    
    async def create_review(self, review: ProductReviewCreate) -> ProductReview:
        """Create a product review."""
        query = """
            INSERT INTO product_reviews (
                product_id, customer_id, order_id, rating, review_title,
                review_text, is_verified_purchase
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING review_id, product_id, customer_id, order_id, rating,
                      review_title, review_text, is_verified_purchase, is_approved,
                      approved_by, approved_at, helpful_count, not_helpful_count,
                      created_at, updated_at
        """
        row = await self.db.fetchrow(
            query,
            review.product_id,
            review.customer_id,
            review.order_id,
            review.rating,
            review.review_title,
            review.review_text,
            review.is_verified_purchase
        )
        return ProductReview(**dict(row))
    
    async def approve_review(
        self,
        review_id: UUID,
        approved_by: str
    ) -> bool:
        """Approve a review."""
        query = """
            UPDATE product_reviews
            SET is_approved = true,
                approved_by = $2,
                approved_at = CURRENT_TIMESTAMP
            WHERE review_id = $1
        """
        result = await self.db.execute(query, review_id, approved_by)
        return result == "UPDATE 1"
    
    async def add_review_image(self, image: ReviewImageCreate) -> ReviewImage:
        """Add an image to a review."""
        query = """
            INSERT INTO review_images (review_id, image_url, image_caption, display_order)
            VALUES ($1, $2, $3, $4)
            RETURNING image_id, review_id, image_url, image_caption, display_order, created_at
        """
        row = await self.db.fetchrow(
            query,
            image.review_id,
            image.image_url,
            image.image_caption,
            image.display_order
        )
        return ReviewImage(**dict(row))
    
    async def vote_review(self, vote: ReviewVoteCreate) -> ReviewVote:
        """Vote on a review (helpful/not helpful)."""
        query = """
            INSERT INTO review_votes (review_id, customer_id, vote_type)
            VALUES ($1, $2, $3)
            ON CONFLICT (review_id, customer_id) DO UPDATE SET
                vote_type = EXCLUDED.vote_type
            RETURNING vote_id, review_id, customer_id, vote_type, created_at
        """
        row = await self.db.fetchrow(
            query,
            vote.review_id,
            vote.customer_id,
            vote.vote_type
        )
        
        # Update helpful counts
        await self._update_review_vote_counts(vote.review_id)
        
        return ReviewVote(**dict(row))
    
    async def _update_review_vote_counts(self, review_id: UUID):
        """Update helpful/not helpful counts for a review."""
        query = """
            UPDATE product_reviews
            SET helpful_count = (
                    SELECT COUNT(*) FROM review_votes
                    WHERE review_id = $1 AND vote_type = 'helpful'
                ),
                not_helpful_count = (
                    SELECT COUNT(*) FROM review_votes
                    WHERE review_id = $1 AND vote_type = 'not_helpful'
                )
            WHERE review_id = $1
        """
        await self.db.execute(query, review_id)
    
    async def add_seller_response(
        self,
        response: ReviewResponseCreate,
        review_id: UUID
    ) -> ReviewResponse:
        """Add seller response to a review."""
        query = """
            INSERT INTO review_responses (review_id, response_text, responded_by)
            VALUES ($1, $2, $3)
            RETURNING response_id, review_id, response_text, responded_by,
                      created_at, updated_at
        """
        row = await self.db.fetchrow(
            query,
            review_id,
            response.response_text,
            response.responded_by
        )
        return ReviewResponse(**dict(row))
    
    async def get_product_reviews(
        self,
        product_id: str,
        approved_only: bool = True,
        limit: int = 20,
        offset: int = 0
    ) -> List[ProductReview]:
        """Get reviews for a product."""
        query = """
            SELECT * FROM product_reviews
            WHERE product_id = $1
        """
        params = [product_id]
        
        if approved_only:
            query += " AND is_approved = true"
        
        query += " ORDER BY created_at DESC LIMIT $2 OFFSET $3"
        params.extend([limit, offset])
        
        rows = await self.db.fetch(query, *params)
        return [ProductReview(**dict(row)) for row in rows]


# =====================================================
# 8. PRODUCT INVENTORY REPOSITORY
# =====================================================

class ProductInventoryRepository:
    """Repository for product inventory operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize repository with database manager."""
        self.db = db_manager
    
    async def create_inventory(
        self,
        inventory: ProductInventoryCreate
    ) -> ProductInventory:
        """Create inventory record for a product at a location."""
        query = """
            INSERT INTO product_inventory (
                product_id, location_id, quantity_available, quantity_reserved,
                quantity_on_order, reorder_point, reorder_quantity, last_counted
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING inventory_id, product_id, location_id, quantity_available,
                      quantity_reserved, quantity_on_order, reorder_point,
                      reorder_quantity, last_counted, last_updated
        """
        row = await self.db.fetchrow(
            query,
            inventory.product_id,
            inventory.location_id,
            inventory.quantity_available,
            inventory.quantity_reserved,
            inventory.quantity_on_order,
            inventory.reorder_point,
            inventory.reorder_quantity,
            inventory.last_counted
        )
        return ProductInventory(**dict(row))
    
    async def record_transaction(
        self,
        transaction: InventoryTransactionCreate
    ) -> InventoryTransaction:
        """Record an inventory transaction."""
        query = """
            INSERT INTO inventory_transactions (
                product_id, location_id, transaction_type, quantity,
                reference_id, reference_type, notes, created_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING transaction_id, product_id, location_id, transaction_type,
                      quantity, reference_id, reference_type, notes, created_by, created_at
        """
        row = await self.db.fetchrow(
            query,
            transaction.product_id,
            transaction.location_id,
            transaction.transaction_type,
            transaction.quantity,
            transaction.reference_id,
            transaction.reference_type,
            transaction.notes,
            transaction.created_by
        )
        
        # Update inventory levels
        await self._update_inventory_levels(
            transaction.product_id,
            transaction.location_id,
            transaction.transaction_type,
            transaction.quantity
        )
        
        return InventoryTransaction(**dict(row))
    
    async def _update_inventory_levels(
        self,
        product_id: str,
        location_id: str,
        transaction_type: InventoryTransactionType,
        quantity: int
    ):
        """Update inventory levels based on transaction."""
        if transaction_type in ['received', 'adjustment_increase', 'return']:
            query = """
                UPDATE product_inventory
                SET quantity_available = quantity_available + $3,
                    last_updated = CURRENT_TIMESTAMP
                WHERE product_id = $1 AND location_id = $2
            """
        elif transaction_type in ['sold', 'adjustment_decrease', 'damaged', 'lost']:
            query = """
                UPDATE product_inventory
                SET quantity_available = quantity_available - $3,
                    last_updated = CURRENT_TIMESTAMP
                WHERE product_id = $1 AND location_id = $2
            """
        elif transaction_type == 'transfer_out':
            query = """
                UPDATE product_inventory
                SET quantity_available = quantity_available - $3,
                    last_updated = CURRENT_TIMESTAMP
                WHERE product_id = $1 AND location_id = $2
            """
        elif transaction_type == 'transfer_in':
            query = """
                UPDATE product_inventory
                SET quantity_available = quantity_available + $3,
                    last_updated = CURRENT_TIMESTAMP
                WHERE product_id = $1 AND location_id = $2
            """
        else:
            return
        
        await self.db.execute(query, product_id, location_id, abs(quantity))
    
    async def create_reservation(
        self,
        reservation: InventoryReservationCreate
    ) -> InventoryReservation:
        """Create an inventory reservation."""
        query = """
            INSERT INTO inventory_reservations (
                product_id, location_id, order_id, quantity_reserved, reserved_until
            )
            VALUES ($1, $2, $3, $4, $5)
            RETURNING reservation_id, product_id, location_id, order_id,
                      quantity_reserved, reserved_until, is_active, created_at, released_at
        """
        row = await self.db.fetchrow(
            query,
            reservation.product_id,
            reservation.location_id,
            reservation.order_id,
            reservation.quantity_reserved,
            reservation.reserved_until
        )
        
        # Update reserved quantity
        await self.db.execute(
            """
            UPDATE product_inventory
            SET quantity_reserved = quantity_reserved + $3
            WHERE product_id = $1 AND location_id = $2
            """,
            reservation.product_id,
            reservation.location_id,
            reservation.quantity_reserved
        )
        
        return InventoryReservation(**dict(row))
    
    async def release_reservation(self, reservation_id: UUID) -> bool:
        """Release an inventory reservation."""
        # Get reservation details
        reservation = await self.db.fetchrow(
            "SELECT * FROM inventory_reservations WHERE reservation_id = $1",
            reservation_id
        )
        
        if not reservation or not reservation['is_active']:
            return False
        
        # Mark reservation as released
        await self.db.execute(
            """
            UPDATE inventory_reservations
            SET is_active = false, released_at = CURRENT_TIMESTAMP
            WHERE reservation_id = $1
            """,
            reservation_id
        )
        
        # Update reserved quantity
        await self.db.execute(
            """
            UPDATE product_inventory
            SET quantity_reserved = quantity_reserved - $3
            WHERE product_id = $1 AND location_id = $2
            """,
            reservation['product_id'],
            reservation['location_id'],
            reservation['quantity_reserved']
        )
        
        return True
    
    async def get_inventory_summary(self, product_id: str) -> Dict[str, Any]:
        """Get inventory summary from materialized view."""
        query = "SELECT * FROM product_inventory_summary WHERE product_id = $1"
        row = await self.db.fetchrow(query, product_id)
        return dict(row) if row else None


# =====================================================
# 9. PRODUCT RELATIONSHIP REPOSITORY
# =====================================================

class ProductRelationshipRepository:
    """Repository for product relationship operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize repository with database manager."""
        self.db = db_manager
    
    async def create_relationship(
        self,
        relationship: ProductRelationshipCreate
    ) -> ProductRelationship:
        """Create a product relationship."""
        query = """
            INSERT INTO product_relationships (
                product_id, related_product_id, relationship_type,
                display_order, is_active
            )
            VALUES ($1, $2, $3, $4, $5)
            RETURNING relationship_id, product_id, related_product_id,
                      relationship_type, display_order, is_active, created_at
        """
        row = await self.db.fetchrow(
            query,
            relationship.product_id,
            relationship.related_product_id,
            relationship.relationship_type,
            relationship.display_order,
            relationship.is_active
        )
        return ProductRelationship(**dict(row))
    
    async def get_related_products(
        self,
        product_id: str,
        relationship_type: Optional[str] = None
    ) -> List[ProductRelationship]:
        """Get related products."""
        query = """
            SELECT * FROM product_relationships
            WHERE product_id = $1 AND is_active = true
        """
        params = [product_id]
        
        if relationship_type:
            query += " AND relationship_type = $2"
            params.append(relationship_type)
        
        query += " ORDER BY display_order, created_at"
        rows = await self.db.fetch(query, *params)
        return [ProductRelationship(**dict(row)) for row in rows]
    
    async def create_recommendation(
        self,
        recommendation: ProductRecommendationCreate
    ) -> ProductRecommendation:
        """Create a product recommendation."""
        query = """
            INSERT INTO product_recommendations (
                product_id, recommended_product_id, recommendation_type,
                confidence_score, recommendation_reason, display_order,
                is_active, expires_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING recommendation_id, product_id, recommended_product_id,
                      recommendation_type, confidence_score, recommendation_reason,
                      display_order, is_active, expires_at, generated_at
        """
        row = await self.db.fetchrow(
            query,
            recommendation.product_id,
            recommendation.recommended_product_id,
            recommendation.recommendation_type,
            recommendation.confidence_score,
            recommendation.recommendation_reason,
            recommendation.display_order,
            recommendation.is_active,
            recommendation.expires_at
        )
        return ProductRecommendation(**dict(row))
    
    async def get_recommendations(
        self,
        product_id: str,
        recommendation_type: Optional[str] = None,
        limit: int = 10
    ) -> List[ProductRecommendation]:
        """Get product recommendations."""
        query = """
            SELECT * FROM product_recommendations
            WHERE product_id = $1
              AND is_active = true
              AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
        """
        params = [product_id]
        
        if recommendation_type:
            query += " AND recommendation_type = $2"
            params.append(recommendation_type)
        
        query += " ORDER BY confidence_score DESC, display_order LIMIT $" + str(len(params) + 1)
        params.append(limit)
        
        rows = await self.db.fetch(query, *params)
        return [ProductRecommendation(**dict(row)) for row in rows]


# =====================================================
# 10. PRODUCT LIFECYCLE REPOSITORY
# =====================================================

class ProductLifecycleRepository:
    """Repository for product lifecycle operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize repository with database manager."""
        self.db = db_manager
    
    async def create_lifecycle_entry(
        self,
        lifecycle: ProductLifecycleCreate
    ) -> ProductLifecycle:
        """Create a product lifecycle entry."""
        query = """
            INSERT INTO product_lifecycle (
                product_id, status, launch_date, discontinue_date,
                end_of_life_date, status_reason, changed_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING lifecycle_id, product_id, status, launch_date,
                      discontinue_date, end_of_life_date, status_reason,
                      changed_by, changed_at
        """
        row = await self.db.fetchrow(
            query,
            lifecycle.product_id,
            lifecycle.status,
            lifecycle.launch_date,
            lifecycle.discontinue_date,
            lifecycle.end_of_life_date,
            lifecycle.status_reason,
            lifecycle.changed_by
        )
        return ProductLifecycle(**dict(row))
    
    async def get_current_lifecycle(self, product_id: str) -> Optional[ProductLifecycle]:
        """Get current lifecycle status for a product."""
        query = """
            SELECT * FROM product_lifecycle
            WHERE product_id = $1
            ORDER BY changed_at DESC
            LIMIT 1
        """
        row = await self.db.fetchrow(query, product_id)
        return ProductLifecycle(**dict(row)) if row else None
    
    async def create_version(self, version: ProductVersionCreate) -> ProductVersion:
        """Create a product version snapshot."""
        query = """
            INSERT INTO product_versions (
                product_id, version_number, version_data, change_summary, created_by
            )
            VALUES ($1, $2, $3, $4, $5)
            RETURNING version_id, product_id, version_number, version_data,
                      change_summary, created_by, created_at
        """
        row = await self.db.fetchrow(
            query,
            version.product_id,
            version.version_number,
            version.version_data,
            version.change_summary,
            version.created_by
        )
        return ProductVersion(**dict(row))
    
    async def record_change(self, change: ProductChangeCreate) -> ProductChange:
        """Record a product change."""
        query = """
            INSERT INTO product_changes (
                product_id, field_name, old_value, new_value,
                change_type, changed_by, change_reason
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING change_id, product_id, field_name, old_value, new_value,
                      change_type, changed_by, change_reason, created_at
        """
        row = await self.db.fetchrow(
            query,
            change.product_id,
            change.field_name,
            change.old_value,
            change.new_value,
            change.change_type,
            change.changed_by,
            change.change_reason
        )
        return ProductChange(**dict(row))
    
    async def create_approval_request(
        self,
        approval: ProductApprovalCreate
    ) -> ProductApproval:
        """Create a product approval request."""
        query = """
            INSERT INTO product_approvals (
                product_id, approval_type, requested_by, approval_data
            )
            VALUES ($1, $2, $3, $4)
            RETURNING approval_id, product_id, approval_type, requested_by,
                      approval_data, requested_at, reviewed_by, reviewed_at,
                      status, review_notes
        """
        row = await self.db.fetchrow(
            query,
            approval.product_id,
            approval.approval_type,
            approval.requested_by,
            approval.approval_data
        )
        return ProductApproval(**dict(row))
    
    async def review_approval(
        self,
        approval_id: UUID,
        status: ApprovalStatus,
        reviewed_by: str,
        review_notes: Optional[str] = None
    ) -> bool:
        """Review an approval request."""
        query = """
            UPDATE product_approvals
            SET status = $2,
                reviewed_by = $3,
                reviewed_at = CURRENT_TIMESTAMP,
                review_notes = $4
            WHERE approval_id = $1
        """
        result = await self.db.execute(
            query,
            approval_id,
            status,
            reviewed_by,
            review_notes
        )
        return result == "UPDATE 1"
    
    async def get_pending_approvals(
        self,
        product_id: Optional[str] = None
    ) -> List[ProductApproval]:
        """Get pending approval requests."""
        query = """
            SELECT * FROM product_approvals
            WHERE status = 'pending'
        """
        params = []
        
        if product_id:
            query += " AND product_id = $1"
            params.append(product_id)
        
        query += " ORDER BY requested_at"
        rows = await self.db.fetch(query, *params)
        return [ProductApproval(**dict(row)) for row in rows]

