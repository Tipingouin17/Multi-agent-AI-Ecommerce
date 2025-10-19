"""
Product Repository Layer for Multi-Agent E-commerce System

This module provides comprehensive database operations for all product-related entities
including variants, bundles, media, categories, attributes, pricing, reviews, inventory,
relationships, and lifecycle management.
"""

import os
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID

from sqlalchemy import select, update, delete, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from shared.database import DatabaseManager, BaseRepository
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
    
    # Review models
    ProductReview, ProductReviewCreate, ProductReviewUpdate,
    ReviewImage, ReviewImageCreate,
    ReviewVote, ReviewVoteCreate,
    ReviewResponse, ReviewResponseCreate, ReviewResponseUpdate,
    
    # Inventory models
    ProductInventory, ProductInventoryCreate, ProductInventoryUpdate,
    InventoryTransaction, InventoryTransactionCreate,
    InventoryReservation, InventoryReservationCreate,
    InventoryBatch, InventoryBatchCreate,
    
    # Relationship models
    ProductRelationship, ProductRelationshipCreate,
    ProductRecommendation, ProductRecommendationCreate,
    
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


logger = structlog.get_logger(__name__)


# =====================================================
# 1. PRODUCT VARIANT REPOSITORY
# =====================================================

class ProductVariantRepository:
    """Repository for product variants and variant attributes."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create_variant_attribute(self, attr: VariantAttributeCreate) -> VariantAttribute:
        """Create a new variant attribute definition."""
        async with self.db_manager.get_session() as session:
            query = """
                INSERT INTO variant_attributes 
                (attribute_name, attribute_type, display_order, is_required)
                VALUES ($1, $2, $3, $4)
                RETURNING attribute_id, attribute_name, attribute_type, display_order, 
                          is_required, created_at
            """
            
            result = await session.execute(
                text(query),
                [attr.attribute_name, attr.attribute_type, attr.display_order, attr.is_required]
            )
            row = result.fetchone()
            
            logger.info("variant_attribute_created", attribute_id=row[0], name=attr.attribute_name)
            
            return VariantAttribute(
                attribute_id=row[0],
                attribute_name=row[1],
                attribute_type=row[2],
                display_order=row[3],
                is_required=row[4],
                created_at=row[5]
            )
    
    async def create_variant(self, variant: ProductVariantCreate) -> ProductVariant:
        """Create a new product variant."""
        async with self.db_manager.get_session() as session:
            variant_id = str(uuid4())
            
            query = """
                INSERT INTO product_variants 
                (variant_id, product_id, parent_variant_id, sku, variant_name, 
                 is_master, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING variant_id, product_id, parent_variant_id, sku, variant_name,
                          is_master, is_active, created_at, updated_at
            """
            
            result = await session.execute(
                text(query),
                [variant_id, variant.product_id, variant.parent_variant_id, 
                 variant.sku, variant.variant_name, variant.is_master, variant.is_active]
            )
            row = result.fetchone()
            
            logger.info("product_variant_created", variant_id=variant_id, sku=variant.sku)
            
            return ProductVariant(
                variant_id=UUID(row[0]),
                product_id=row[1],
                parent_variant_id=UUID(row[2]) if row[2] else None,
                sku=row[3],
                variant_name=row[4],
                is_master=row[5],
                is_active=row[6],
                created_at=row[7],
                updated_at=row[8]
            )
    
    async def get_product_variants(self, product_id: str) -> List[ProductVariant]:
        """Get all variants for a product."""
        async with self.db_manager.get_session() as session:
            query = """
                SELECT variant_id, product_id, parent_variant_id, sku, variant_name,
                       is_master, is_active, created_at, updated_at
                FROM product_variants
                WHERE product_id = $1
                ORDER BY is_master DESC, variant_name
            """
            
            result = await session.execute(text(query), [product_id])
            rows = result.fetchall()
            
            return [
                ProductVariant(
                    variant_id=UUID(row[0]),
                    product_id=row[1],
                    parent_variant_id=UUID(row[2]) if row[2] else None,
                    sku=row[3],
                    variant_name=row[4],
                    is_master=row[5],
                    is_active=row[6],
                    created_at=row[7],
                    updated_at=row[8]
                )
                for row in rows
            ]
    
    async def update_variant(self, variant_id: UUID, update_data: ProductVariantUpdate) -> Optional[ProductVariant]:
        """Update a product variant."""
        async with self.db_manager.get_session() as session:
            set_clauses = []
            params = []
            param_idx = 1
            
            if update_data.variant_name is not None:
                set_clauses.append(f"variant_name = ${param_idx}")
                params.append(update_data.variant_name)
                param_idx += 1
            
            if update_data.is_master is not None:
                set_clauses.append(f"is_master = ${param_idx}")
                params.append(update_data.is_master)
                param_idx += 1
            
            if update_data.is_active is not None:
                set_clauses.append(f"is_active = ${param_idx}")
                params.append(update_data.is_active)
                param_idx += 1
            
            if not set_clauses:
                return await self.get_variant(variant_id)
            
            params.append(str(variant_id))
            query = f"""
                UPDATE product_variants
                SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
                WHERE variant_id = ${param_idx}
                RETURNING variant_id, product_id, parent_variant_id, sku, variant_name,
                          is_master, is_active, created_at, updated_at
            """
            
            result = await session.execute(text(query), params)
            row = result.fetchone()
            
            if not row:
                return None
            
            logger.info("product_variant_updated", variant_id=str(variant_id))
            
            return ProductVariant(
                variant_id=UUID(row[0]),
                product_id=row[1],
                parent_variant_id=UUID(row[2]) if row[2] else None,
                sku=row[3],
                variant_name=row[4],
                is_master=row[5],
                is_active=row[6],
                created_at=row[7],
                updated_at=row[8]
            )
    
    async def get_variant(self, variant_id: UUID) -> Optional[ProductVariant]:
        """Get a variant by ID."""
        async with self.db_manager.get_session() as session:
            query = """
                SELECT variant_id, product_id, parent_variant_id, sku, variant_name,
                       is_master, is_active, created_at, updated_at
                FROM product_variants
                WHERE variant_id = $1
            """
            
            result = await session.execute(text(query), [str(variant_id)])
            row = result.fetchone()
            
            if not row:
                return None
            
            return ProductVariant(
                variant_id=UUID(row[0]),
                product_id=row[1],
                parent_variant_id=UUID(row[2]) if row[2] else None,
                sku=row[3],
                variant_name=row[4],
                is_master=row[5],
                is_active=row[6],
                created_at=row[7],
                updated_at=row[8]
            )


# =====================================================
# 2. PRODUCT BUNDLE REPOSITORY
# =====================================================

class ProductBundleRepository:
    """Repository for product bundles and bundle components."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create_bundle(self, bundle: ProductBundleCreate) -> ProductBundle:
        """Create a new product bundle."""
        async with self.db_manager.get_session() as session:
            bundle_id = str(uuid4())
            
            query = """
                INSERT INTO product_bundles 
                (bundle_id, bundle_name, bundle_description, bundle_type, 
                 pricing_strategy, bundle_price, is_active, valid_from, valid_to)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING bundle_id, bundle_name, bundle_description, bundle_type,
                          pricing_strategy, bundle_price, is_active, valid_from, 
                          valid_to, created_at, updated_at
            """
            
            result = await session.execute(
                text(query),
                [bundle_id, bundle.bundle_name, bundle.bundle_description, 
                 bundle.bundle_type.value, bundle.pricing_strategy.value,
                 float(bundle.bundle_price) if bundle.bundle_price else None,
                 bundle.is_active, bundle.valid_from, bundle.valid_to]
            )
            row = result.fetchone()
            
            logger.info("product_bundle_created", bundle_id=bundle_id, name=bundle.bundle_name)
            
            return ProductBundle(
                bundle_id=UUID(row[0]),
                bundle_name=row[1],
                bundle_description=row[2],
                bundle_type=BundleType(row[3]),
                pricing_strategy=PricingStrategy(row[4]),
                bundle_price=Decimal(str(row[5])) if row[5] else None,
                is_active=row[6],
                valid_from=row[7],
                valid_to=row[8],
                created_at=row[9],
                updated_at=row[10]
            )
    
    async def add_bundle_component(self, component: BundleComponentCreate) -> BundleComponent:
        """Add a component to a bundle."""
        async with self.db_manager.get_session() as session:
            query = """
                INSERT INTO bundle_components 
                (bundle_id, product_id, quantity, is_required, display_order)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING component_id, bundle_id, product_id, quantity, 
                          is_required, display_order, created_at
            """
            
            result = await session.execute(
                text(query),
                [str(component.bundle_id), component.product_id, component.quantity,
                 component.is_required, component.display_order]
            )
            row = result.fetchone()
            
            logger.info("bundle_component_added", component_id=row[0], 
                       bundle_id=str(component.bundle_id))
            
            return BundleComponent(
                component_id=row[0],
                bundle_id=UUID(row[1]),
                product_id=row[2],
                quantity=row[3],
                is_required=row[4],
                display_order=row[5],
                created_at=row[6]
            )
    
    async def get_bundle(self, bundle_id: UUID) -> Optional[ProductBundle]:
        """Get a bundle by ID."""
        async with self.db_manager.get_session() as session:
            query = """
                SELECT bundle_id, bundle_name, bundle_description, bundle_type,
                       pricing_strategy, bundle_price, is_active, valid_from,
                       valid_to, created_at, updated_at
                FROM product_bundles
                WHERE bundle_id = $1
            """
            
            result = await session.execute(text(query), [str(bundle_id)])
            row = result.fetchone()
            
            if not row:
                return None
            
            return ProductBundle(
                bundle_id=UUID(row[0]),
                bundle_name=row[1],
                bundle_description=row[2],
                bundle_type=BundleType(row[3]),
                pricing_strategy=PricingStrategy(row[4]),
                bundle_price=Decimal(str(row[5])) if row[5] else None,
                is_active=row[6],
                valid_from=row[7],
                valid_to=row[8],
                created_at=row[9],
                updated_at=row[10]
            )
    
    async def get_bundle_components(self, bundle_id: UUID) -> List[BundleComponent]:
        """Get all components of a bundle."""
        async with self.db_manager.get_session() as session:
            query = """
                SELECT component_id, bundle_id, product_id, quantity,
                       is_required, display_order, created_at
                FROM bundle_components
                WHERE bundle_id = $1
                ORDER BY display_order, component_id
            """
            
            result = await session.execute(text(query), [str(bundle_id)])
            rows = result.fetchall()
            
            return [
                BundleComponent(
                    component_id=row[0],
                    bundle_id=UUID(row[1]),
                    product_id=row[2],
                    quantity=row[3],
                    is_required=row[4],
                    display_order=row[5],
                    created_at=row[6]
                )
                for row in rows
            ]


# =====================================================
# 3. PRODUCT MEDIA REPOSITORY
# =====================================================

class ProductMediaRepository:
    """Repository for product images and media."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create_image(self, image: ProductImageCreate) -> ProductImage:
        """Create a new product image."""
        async with self.db_manager.get_session() as session:
            image_id = str(uuid4())
            
            query = """
                INSERT INTO product_images 
                (image_id, product_id, image_url, alt_text, is_primary, display_order)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING image_id, product_id, image_url, alt_text, is_primary,
                          display_order, created_at
            """
            
            result = await session.execute(
                text(query),
                [image_id, image.product_id, image.image_url, image.alt_text,
                 image.is_primary, image.display_order]
            )
            row = result.fetchone()
            
            logger.info("product_image_created", image_id=image_id, 
                       product_id=image.product_id)
            
            return ProductImage(
                image_id=UUID(row[0]),
                product_id=row[1],
                image_url=row[2],
                alt_text=row[3],
                is_primary=row[4],
                display_order=row[5],
                created_at=row[6]
            )
    
    async def create_media(self, media: ProductMediaCreate) -> ProductMedia:
        """Create a new product media item."""
        async with self.db_manager.get_session() as session:
            media_id = str(uuid4())
            
            query = """
                INSERT INTO product_media 
                (media_id, product_id, media_type, media_url, media_title, 
                 media_description, display_order)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING media_id, product_id, media_type, media_url, media_title,
                          media_description, display_order, created_at
            """
            
            result = await session.execute(
                text(query),
                [media_id, media.product_id, media.media_type.value, media.media_url,
                 media.media_title, media.media_description, media.display_order]
            )
            row = result.fetchone()
            
            logger.info("product_media_created", media_id=media_id, 
                       type=media.media_type.value)
            
            return ProductMedia(
                media_id=UUID(row[0]),
                product_id=row[1],
                media_type=MediaType(row[2]),
                media_url=row[3],
                media_title=row[4],
                media_description=row[5],
                display_order=row[6],
                created_at=row[7]
            )
    
    async def get_product_images(self, product_id: str) -> List[ProductImage]:
        """Get all images for a product."""
        async with self.db_manager.get_session() as session:
            query = """
                SELECT image_id, product_id, image_url, alt_text, is_primary,
                       display_order, created_at
                FROM product_images
                WHERE product_id = $1
                ORDER BY is_primary DESC, display_order, created_at
            """
            
            result = await session.execute(text(query), [product_id])
            rows = result.fetchall()
            
            return [
                ProductImage(
                    image_id=UUID(row[0]),
                    product_id=row[1],
                    image_url=row[2],
                    alt_text=row[3],
                    is_primary=row[4],
                    display_order=row[5],
                    created_at=row[6]
                )
                for row in rows
            ]
    
    async def get_product_media(self, product_id: str) -> List[ProductMedia]:
        """Get all media for a product."""
        async with self.db_manager.get_session() as session:
            query = """
                SELECT media_id, product_id, media_type, media_url, media_title,
                       media_description, display_order, created_at
                FROM product_media
                WHERE product_id = $1
                ORDER BY display_order, created_at
            """
            
            result = await session.execute(text(query), [product_id])
            rows = result.fetchall()
            
            return [
                ProductMedia(
                    media_id=UUID(row[0]),
                    product_id=row[1],
                    media_type=MediaType(row[2]),
                    media_url=row[3],
                    media_title=row[4],
                    media_description=row[5],
                    display_order=row[6],
                    created_at=row[7]
                )
                for row in rows
            ]


# =====================================================
# 4. PRODUCT CATEGORY REPOSITORY
# =====================================================

class ProductCategoryRepository:
    """Repository for product categories and taxonomy."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create_category(self, category: ProductCategoryCreate) -> ProductCategory:
        """Create a new product category."""
        async with self.db_manager.get_session() as session:
            query = """
                INSERT INTO product_categories 
                (parent_category_id, category_name, category_slug, category_description,
                 category_image_url, seo_title, seo_description, seo_keywords,
                 display_order, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING category_id, parent_category_id, category_name, category_slug,
                          category_description, category_path, category_level,
                          category_image_url, seo_title, seo_description, seo_keywords,
                          display_order, is_active, created_at, updated_at
            """
            
            result = await session.execute(
                text(query),
                [category.parent_category_id, category.category_name, category.category_slug,
                 category.category_description, category.category_image_url,
                 category.seo_title, category.seo_description, category.seo_keywords,
                 category.display_order, category.is_active]
            )
            row = result.fetchone()
            
            logger.info("product_category_created", category_id=row[0], 
                       name=category.category_name)
            
            return ProductCategory(
                category_id=row[0],
                parent_category_id=row[1],
                category_name=row[2],
                category_slug=row[3],
                category_description=row[4],
                category_path=row[5],
                category_level=row[6],
                category_image_url=row[7],
                seo_title=row[8],
                seo_description=row[9],
                seo_keywords=row[10],
                display_order=row[11],
                is_active=row[12],
                created_at=row[13],
                updated_at=row[14]
            )
    
    async def get_category(self, category_id: int) -> Optional[ProductCategory]:
        """Get a category by ID."""
        async with self.db_manager.get_session() as session:
            query = """
                SELECT category_id, parent_category_id, category_name, category_slug,
                       category_description, category_path, category_level,
                       category_image_url, seo_title, seo_description, seo_keywords,
                       display_order, is_active, created_at, updated_at
                FROM product_categories
                WHERE category_id = $1
            """
            
            result = await session.execute(text(query), [category_id])
            row = result.fetchone()
            
            if not row:
                return None
            
            return ProductCategory(
                category_id=row[0],
                parent_category_id=row[1],
                category_name=row[2],
                category_slug=row[3],
                category_description=row[4],
                category_path=row[5],
                category_level=row[6],
                category_image_url=row[7],
                seo_title=row[8],
                seo_description=row[9],
                seo_keywords=row[10],
                display_order=row[11],
                is_active=row[12],
                created_at=row[13],
                updated_at=row[14]
            )
    
    async def get_subcategories(self, parent_category_id: Optional[int] = None) -> List[ProductCategory]:
        """Get all subcategories of a parent category."""
        async with self.db_manager.get_session() as session:
            if parent_category_id is None:
                query = """
                    SELECT category_id, parent_category_id, category_name, category_slug,
                           category_description, category_path, category_level,
                           category_image_url, seo_title, seo_description, seo_keywords,
                           display_order, is_active, created_at, updated_at
                    FROM product_categories
                    WHERE parent_category_id IS NULL
                    ORDER BY display_order, category_name
                """
                result = await session.execute(text(query))
            else:
                query = """
                    SELECT category_id, parent_category_id, category_name, category_slug,
                           category_description, category_path, category_level,
                           category_image_url, seo_title, seo_description, seo_keywords,
                           display_order, is_active, created_at, updated_at
                    FROM product_categories
                    WHERE parent_category_id = $1
                    ORDER BY display_order, category_name
                """
                result = await session.execute(text(query), [parent_category_id])
            
            rows = result.fetchall()
            
            return [
                ProductCategory(
                    category_id=row[0],
                    parent_category_id=row[1],
                    category_name=row[2],
                    category_slug=row[3],
                    category_description=row[4],
                    category_path=row[5],
                    category_level=row[6],
                    category_image_url=row[7],
                    seo_title=row[8],
                    seo_description=row[9],
                    seo_keywords=row[10],
                    display_order=row[11],
                    is_active=row[12],
                    created_at=row[13],
                    updated_at=row[14]
                )
                for row in rows
            ]
    
    async def add_product_to_category(self, mapping: ProductCategoryMappingCreate) -> ProductCategoryMapping:
        """Add a product to a category."""
        async with self.db_manager.get_session() as session:
            query = """
                INSERT INTO product_category_mapping 
                (product_id, category_id, is_primary)
                VALUES ($1, $2, $3)
                RETURNING mapping_id, product_id, category_id, is_primary, created_at
            """
            
            result = await session.execute(
                text(query),
                [mapping.product_id, mapping.category_id, mapping.is_primary]
            )
            row = result.fetchone()
            
            logger.info("product_added_to_category", mapping_id=row[0],
                       product_id=mapping.product_id, category_id=mapping.category_id)
            
            return ProductCategoryMapping(
                mapping_id=row[0],
                product_id=row[1],
                category_id=row[2],
                is_primary=row[3],
                created_at=row[4]
            )


# =====================================================
# 5. PRODUCT ATTRIBUTE REPOSITORY
# =====================================================

class ProductAttributeRepository:
    """Repository for product attributes and specifications."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create_attribute_group(self, group: AttributeGroupCreate) -> AttributeGroup:
        """Create a new attribute group."""
        async with self.db_manager.get_session() as session:
            query = """
                INSERT INTO attribute_groups 
                (group_name, group_description, display_order)
                VALUES ($1, $2, $3)
                RETURNING group_id, group_name, group_description, display_order, created_at
            """
            
            result = await session.execute(
                text(query),
                [group.group_name, group.group_description, group.display_order]
            )
            row = result.fetchone()
            
            logger.info("attribute_group_created", group_id=row[0], name=group.group_name)
            
            return AttributeGroup(
                group_id=row[0],
                group_name=row[1],
                group_description=row[2],
                display_order=row[3],
                created_at=row[4]
            )
    
    async def create_attribute(self, attr: ProductAttributeCreate) -> ProductAttribute:
        """Create a new product attribute."""
        async with self.db_manager.get_session() as session:
            query = """
                INSERT INTO product_attributes 
                (attribute_name, attribute_type, group_id, unit_of_measure,
                 validation_rules, is_filterable, is_searchable, is_comparable,
                 display_order)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING attribute_id, attribute_name, attribute_type, group_id,
                          unit_of_measure, validation_rules, is_filterable,
                          is_searchable, is_comparable, display_order, created_at
            """
            
            result = await session.execute(
                text(query),
                [attr.attribute_name, attr.attribute_type, attr.group_id,
                 attr.unit_of_measure, attr.validation_rules, attr.is_filterable,
                 attr.is_searchable, attr.is_comparable, attr.display_order]
            )
            row = result.fetchone()
            
            logger.info("product_attribute_created", attribute_id=row[0], 
                       name=attr.attribute_name)
            
            return ProductAttribute(
                attribute_id=row[0],
                attribute_name=row[1],
                attribute_type=row[2],
                group_id=row[3],
                unit_of_measure=row[4],
                validation_rules=row[5],
                is_filterable=row[6],
                is_searchable=row[7],
                is_comparable=row[8],
                display_order=row[9],
                created_at=row[10]
            )
    
    async def set_attribute_value(self, value: ProductAttributeValueCreate) -> ProductAttributeValue:
        """Set an attribute value for a product."""
        async with self.db_manager.get_session() as session:
            query = """
                INSERT INTO product_attribute_values 
                (product_id, attribute_id, attribute_value)
                VALUES ($1, $2, $3)
                ON CONFLICT (product_id, attribute_id) 
                DO UPDATE SET attribute_value = EXCLUDED.attribute_value,
                              updated_at = CURRENT_TIMESTAMP
                RETURNING value_id, product_id, attribute_id, attribute_value,
                          created_at, updated_at
            """
            
            result = await session.execute(
                text(query),
                [value.product_id, value.attribute_id, value.attribute_value]
            )
            row = result.fetchone()
            
            logger.info("product_attribute_value_set", value_id=row[0],
                       product_id=value.product_id, attribute_id=value.attribute_id)
            
            return ProductAttributeValue(
                value_id=row[0],
                product_id=row[1],
                attribute_id=row[2],
                attribute_value=row[3],
                created_at=row[4],
                updated_at=row[5]
            )
    
    async def get_product_attributes(self, product_id: str) -> List[ProductAttributeValue]:
        """Get all attribute values for a product."""
        async with self.db_manager.get_session() as session:
            query = """
                SELECT pav.value_id, pav.product_id, pav.attribute_id, pav.attribute_value,
                       pav.created_at, pav.updated_at
                FROM product_attribute_values pav
                JOIN product_attributes pa ON pav.attribute_id = pa.attribute_id
                WHERE pav.product_id = $1
                ORDER BY pa.display_order, pa.attribute_name
            """
            
            result = await session.execute(text(query), [product_id])
            rows = result.fetchall()
            
            return [
                ProductAttributeValue(
                    value_id=row[0],
                    product_id=row[1],
                    attribute_id=row[2],
                    attribute_value=row[3],
                    created_at=row[4],
                    updated_at=row[5]
                )
                for row in rows
            ]


# =====================================================
# 6. PRODUCT PRICING REPOSITORY
# =====================================================

class ProductPricingRepository:
    """Repository for pricing rules and price history."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create_pricing_rule(self, rule: PricingRuleCreate) -> PricingRule:
        """Create a new pricing rule."""
        async with self.db_manager.get_session() as session:
            rule_id = str(uuid4())
            
            query = """
                INSERT INTO pricing_rules 
                (rule_id, product_id, rule_name, rule_type, rule_config, priority,
                 is_active, valid_from, valid_to, created_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING rule_id, product_id, rule_name, rule_type, rule_config,
                          priority, is_active, valid_from, valid_to, created_by,
                          created_at, updated_at
            """
            
            result = await session.execute(
                text(query),
                [rule_id, rule.product_id, rule.rule_name, rule.rule_type.value,
                 rule.rule_config, rule.priority, rule.is_active, rule.valid_from,
                 rule.valid_to, rule.created_by]
            )
            row = result.fetchone()
            
            logger.info("pricing_rule_created", rule_id=rule_id, name=rule.rule_name)
            
            return PricingRule(
                rule_id=UUID(row[0]),
                product_id=row[1],
                rule_name=row[2],
                rule_type=PricingRuleType(row[3]),
                rule_config=row[4],
                priority=row[5],
                is_active=row[6],
                valid_from=row[7],
                valid_to=row[8],
                created_by=row[9],
                created_at=row[10],
                updated_at=row[11]
            )
    
    async def add_pricing_tier(self, tier: PricingTierCreate, rule_id: UUID) -> PricingTier:
        """Add a pricing tier to a rule."""
        async with self.db_manager.get_session() as session:
            query = """
                INSERT INTO pricing_tiers 
                (rule_id, min_quantity, max_quantity, price, discount_percentage)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING tier_id, rule_id, min_quantity, max_quantity, price,
                          discount_percentage, created_at
            """
            
            result = await session.execute(
                text(query),
                [str(rule_id), tier.min_quantity, tier.max_quantity,
                 float(tier.price), float(tier.discount_percentage) if tier.discount_percentage else None]
            )
            row = result.fetchone()
            
            logger.info("pricing_tier_added", tier_id=row[0], rule_id=str(rule_id))
            
            return PricingTier(
                tier_id=row[0],
                rule_id=UUID(row[1]),
                min_quantity=row[2],
                max_quantity=row[3],
                price=Decimal(str(row[4])),
                discount_percentage=Decimal(str(row[5])) if row[5] else None,
                created_at=row[6]
            )
    
    async def record_price_change(self, change: PriceHistoryCreate) -> PriceHistory:
        """Record a price change in history."""
        async with self.db_manager.get_session() as session:
            query = """
                INSERT INTO price_history 
                (product_id, old_price, new_price, change_reason, changed_by,
                 change_type, effective_date)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING history_id, product_id, old_price, new_price, change_reason,
                          changed_by, change_type, effective_date, created_at
            """
            
            result = await session.execute(
                text(query),
                [change.product_id, float(change.old_price) if change.old_price else None,
                 float(change.new_price), change.change_reason, change.changed_by,
                 change.change_type.value, change.effective_date]
            )
            row = result.fetchone()
            
            logger.info("price_change_recorded", history_id=row[0], 
                       product_id=change.product_id)
            
            return PriceHistory(
                history_id=row[0],
                product_id=row[1],
                old_price=Decimal(str(row[2])) if row[2] else None,
                new_price=Decimal(str(row[3])),
                change_reason=row[4],
                changed_by=row[5],
                change_type=row[6],
                effective_date=row[7],
                created_at=row[8]
            )
    
    async def track_competitor_price(self, price: CompetitorPriceCreate) -> CompetitorPrice:
        """Track a competitor's price."""
        async with self.db_manager.get_session() as session:
            query = """
                INSERT INTO competitor_prices 
                (product_id, competitor_name, competitor_url, competitor_price,
                 currency, is_available, last_checked)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING tracking_id, product_id, competitor_name, competitor_url,
                          competitor_price, currency, is_available, last_checked, created_at
            """
            
            result = await session.execute(
                text(query),
                [price.product_id, price.competitor_name, price.competitor_url,
                 float(price.competitor_price), price.currency, price.is_available,
                 price.last_checked]
            )
            row = result.fetchone()
            
            logger.info("competitor_price_tracked", tracking_id=row[0],
                       product_id=price.product_id, competitor=price.competitor_name)
            
            return CompetitorPrice(
                tracking_id=row[0],
                product_id=row[1],
                competitor_name=row[2],
                competitor_url=row[3],
                competitor_price=Decimal(str(row[4])),
                currency=row[5],
                is_available=row[6],
                last_checked=row[7],
                created_at=row[8]
            )


# =====================================================
# 7. PRODUCT REVIEW REPOSITORY
# =====================================================

class ProductReviewRepository:
    """Repository for product reviews and ratings."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create_review(self, review: ProductReviewCreate) -> ProductReview:
        """Create a new product review."""
        async with self.db_manager.get_session() as session:
            review_id = str(uuid4())
            
            query = """
                INSERT INTO product_reviews 
                (review_id, product_id, customer_id, order_id, rating, review_title,
                 review_text, is_verified_purchase)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING review_id, product_id, customer_id, order_id, rating,
                          review_title, review_text, is_verified_purchase, is_approved,
                          approved_by, approved_at, helpful_count, not_helpful_count,
                          created_at, updated_at
            """
            
            result = await session.execute(
                text(query),
                [review_id, review.product_id, review.customer_id, review.order_id,
                 review.rating, review.review_title, review.review_text,
                 review.is_verified_purchase]
            )
            row = result.fetchone()
            
            logger.info("product_review_created", review_id=review_id,
                       product_id=review.product_id, rating=review.rating)
            
            return ProductReview(
                review_id=UUID(row[0]),
                product_id=row[1],
                customer_id=row[2],
                order_id=row[3],
                rating=row[4],
                review_title=row[5],
                review_text=row[6],
                is_verified_purchase=row[7],
                is_approved=row[8],
                approved_by=row[9],
                approved_at=row[10],
                helpful_count=row[11],
                not_helpful_count=row[12],
                created_at=row[13],
                updated_at=row[14]
            )
    
    async def approve_review(self, review_id: UUID, approved_by: str) -> Optional[ProductReview]:
        """Approve a review."""
        async with self.db_manager.get_session() as session:
            query = """
                UPDATE product_reviews
                SET is_approved = TRUE, approved_by = $1, approved_at = CURRENT_TIMESTAMP
                WHERE review_id = $2
                RETURNING review_id, product_id, customer_id, order_id, rating,
                          review_title, review_text, is_verified_purchase, is_approved,
                          approved_by, approved_at, helpful_count, not_helpful_count,
                          created_at, updated_at
            """
            
            result = await session.execute(text(query), [approved_by, str(review_id)])
            row = result.fetchone()
            
            if not row:
                return None
            
            logger.info("review_approved", review_id=str(review_id), approved_by=approved_by)
            
            return ProductReview(
                review_id=UUID(row[0]),
                product_id=row[1],
                customer_id=row[2],
                order_id=row[3],
                rating=row[4],
                review_title=row[5],
                review_text=row[6],
                is_verified_purchase=row[7],
                is_approved=row[8],
                approved_by=row[9],
                approved_at=row[10],
                helpful_count=row[11],
                not_helpful_count=row[12],
                created_at=row[13],
                updated_at=row[14]
            )
    
    async def add_review_vote(self, vote: ReviewVoteCreate) -> ReviewVote:
        """Add a helpful/not helpful vote to a review."""
        async with self.db_manager.get_session() as session:
            query = """
                INSERT INTO review_votes 
                (review_id, customer_id, vote_type)
                VALUES ($1, $2, $3)
                ON CONFLICT (review_id, customer_id) 
                DO UPDATE SET vote_type = EXCLUDED.vote_type
                RETURNING vote_id, review_id, customer_id, vote_type, created_at
            """
            
            result = await session.execute(
                text(query),
                [str(vote.review_id), vote.customer_id, vote.vote_type]
            )
            row = result.fetchone()
            
            # Update helpful count
            if vote.vote_type == "helpful":
                await session.execute(
                    text("UPDATE product_reviews SET helpful_count = helpful_count + 1 WHERE review_id = $1"),
                    [str(vote.review_id)]
                )
            else:
                await session.execute(
                    text("UPDATE product_reviews SET not_helpful_count = not_helpful_count + 1 WHERE review_id = $1"),
                    [str(vote.review_id)]
                )
            
            logger.info("review_vote_added", vote_id=row[0], review_id=str(vote.review_id))
            
            return ReviewVote(
                vote_id=row[0],
                review_id=UUID(row[1]),
                customer_id=row[2],
                vote_type=row[3],
                created_at=row[4]
            )
    
    async def add_review_response(self, response: ReviewResponseCreate, review_id: UUID) -> ReviewResponse:
        """Add a seller response to a review."""
        async with self.db_manager.get_session() as session:
            response_id = str(uuid4())
            
            query = """
                INSERT INTO review_responses 
                (response_id, review_id, response_text, responded_by)
                VALUES ($1, $2, $3, $4)
                RETURNING response_id, review_id, response_text, responded_by,
                          created_at, updated_at
            """
            
            result = await session.execute(
                text(query),
                [response_id, str(review_id), response.response_text, response.responded_by]
            )
            row = result.fetchone()
            
            logger.info("review_response_added", response_id=response_id, 
                       review_id=str(review_id))
            
            return ReviewResponse(
                response_id=UUID(row[0]),
                review_id=UUID(row[1]),
                response_text=row[2],
                responded_by=row[3],
                created_at=row[4],
                updated_at=row[5]
            )
    
    async def get_product_reviews(self, product_id: str, approved_only: bool = True) -> List[ProductReview]:
        """Get all reviews for a product."""
        async with self.db_manager.get_session() as session:
            if approved_only:
                query = """
                    SELECT review_id, product_id, customer_id, order_id, rating,
                           review_title, review_text, is_verified_purchase, is_approved,
                           approved_by, approved_at, helpful_count, not_helpful_count,
                           created_at, updated_at
                    FROM product_reviews
                    WHERE product_id = $1 AND is_approved = TRUE
                    ORDER BY created_at DESC
                """
            else:
                query = """
                    SELECT review_id, product_id, customer_id, order_id, rating,
                           review_title, review_text, is_verified_purchase, is_approved,
                           approved_by, approved_at, helpful_count, not_helpful_count,
                           created_at, updated_at
                    FROM product_reviews
                    WHERE product_id = $1
                    ORDER BY created_at DESC
                """
            
            result = await session.execute(text(query), [product_id])
            rows = result.fetchall()
            
            return [
                ProductReview(
                    review_id=UUID(row[0]),
                    product_id=row[1],
                    customer_id=row[2],
                    order_id=row[3],
                    rating=row[4],
                    review_title=row[5],
                    review_text=row[6],
                    is_verified_purchase=row[7],
                    is_approved=row[8],
                    approved_by=row[9],
                    approved_at=row[10],
                    helpful_count=row[11],
                    not_helpful_count=row[12],
                    created_at=row[13],
                    updated_at=row[14]
                )
                for row in rows
            ]


# =====================================================
# 8. PRODUCT INVENTORY REPOSITORY
# =====================================================

class ProductInventoryRepository:
    """Repository for product inventory management."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create_inventory(self, inventory: ProductInventoryCreate) -> ProductInventory:
        """Create inventory record for a product at a location."""
        async with self.db_manager.get_session() as session:
            query = """
                INSERT INTO product_inventory 
                (product_id, location_id, quantity_available, quantity_reserved,
                 quantity_on_order, reorder_point, reorder_quantity, last_counted)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING inventory_id, product_id, location_id, quantity_available,
                          quantity_reserved, quantity_on_order, reorder_point,
                          reorder_quantity, last_counted, last_updated
            """
            
            result = await session.execute(
                text(query),
                [inventory.product_id, inventory.location_id, inventory.quantity_available,
                 inventory.quantity_reserved, inventory.quantity_on_order,
                 inventory.reorder_point, inventory.reorder_quantity, inventory.last_counted]
            )
            row = result.fetchone()
            
            logger.info("inventory_created", inventory_id=row[0],
                       product_id=inventory.product_id, location=inventory.location_id)
            
            return ProductInventory(
                inventory_id=row[0],
                product_id=row[1],
                location_id=row[2],
                quantity_available=row[3],
                quantity_reserved=row[4],
                quantity_on_order=row[5],
                reorder_point=row[6],
                reorder_quantity=row[7],
                last_counted=row[8],
                last_updated=row[9]
            )
    
    async def record_transaction(self, transaction: InventoryTransactionCreate) -> InventoryTransaction:
        """Record an inventory transaction."""
        async with self.db_manager.get_session() as session:
            transaction_id = str(uuid4())
            
            query = """
                INSERT INTO inventory_transactions 
                (transaction_id, product_id, location_id, transaction_type, quantity,
                 reference_id, reference_type, notes, created_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING transaction_id, product_id, location_id, transaction_type,
                          quantity, reference_id, reference_type, notes, created_by,
                          created_at
            """
            
            result = await session.execute(
                text(query),
                [transaction_id, transaction.product_id, transaction.location_id,
                 transaction.transaction_type.value, transaction.quantity,
                 transaction.reference_id, transaction.reference_type,
                 transaction.notes, transaction.created_by]
            )
            row = result.fetchone()
            
            # Update inventory levels
            if transaction.quantity > 0:
                await session.execute(
                    text("UPDATE product_inventory SET quantity_available = quantity_available + $1 WHERE product_id = $2 AND location_id = $3"),
                    [transaction.quantity, transaction.product_id, transaction.location_id]
                )
            else:
                await session.execute(
                    text("UPDATE product_inventory SET quantity_available = quantity_available + $1 WHERE product_id = $2 AND location_id = $3"),
                    [transaction.quantity, transaction.product_id, transaction.location_id]
                )
            
            logger.info("inventory_transaction_recorded", transaction_id=transaction_id,
                       type=transaction.transaction_type.value, quantity=transaction.quantity)
            
            return InventoryTransaction(
                transaction_id=UUID(row[0]),
                product_id=row[1],
                location_id=row[2],
                transaction_type=InventoryTransactionType(row[3]),
                quantity=row[4],
                reference_id=row[5],
                reference_type=row[6],
                notes=row[7],
                created_by=row[8],
                created_at=row[9]
            )
    
    async def create_reservation(self, reservation: InventoryReservationCreate) -> InventoryReservation:
        """Create an inventory reservation."""
        async with self.db_manager.get_session() as session:
            reservation_id = str(uuid4())
            
            query = """
                INSERT INTO inventory_reservations 
                (reservation_id, product_id, location_id, order_id, quantity_reserved,
                 reserved_until)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING reservation_id, product_id, location_id, order_id,
                          quantity_reserved, reserved_until, is_active, created_at,
                          released_at
            """
            
            result = await session.execute(
                text(query),
                [reservation_id, reservation.product_id, reservation.location_id,
                 reservation.order_id, reservation.quantity_reserved, reservation.reserved_until]
            )
            row = result.fetchone()
            
            # Update reserved quantity
            await session.execute(
                text("UPDATE product_inventory SET quantity_reserved = quantity_reserved + $1 WHERE product_id = $2 AND location_id = $3"),
                [reservation.quantity_reserved, reservation.product_id, reservation.location_id]
            )
            
            logger.info("inventory_reservation_created", reservation_id=reservation_id,
                       order_id=reservation.order_id, quantity=reservation.quantity_reserved)
            
            return InventoryReservation(
                reservation_id=UUID(row[0]),
                product_id=row[1],
                location_id=row[2],
                order_id=row[3],
                quantity_reserved=row[4],
                reserved_until=row[5],
                is_active=row[6],
                created_at=row[7],
                released_at=row[8]
            )
    
    async def get_inventory(self, product_id: str, location_id: str) -> Optional[ProductInventory]:
        """Get inventory for a product at a location."""
        async with self.db_manager.get_session() as session:
            query = """
                SELECT inventory_id, product_id, location_id, quantity_available,
                       quantity_reserved, quantity_on_order, reorder_point,
                       reorder_quantity, last_counted, last_updated
                FROM product_inventory
                WHERE product_id = $1 AND location_id = $2
            """
            
            result = await session.execute(text(query), [product_id, location_id])
            row = result.fetchone()
            
            if not row:
                return None
            
            return ProductInventory(
                inventory_id=row[0],
                product_id=row[1],
                location_id=row[2],
                quantity_available=row[3],
                quantity_reserved=row[4],
                quantity_on_order=row[5],
                reorder_point=row[6],
                reorder_quantity=row[7],
                last_counted=row[8],
                last_updated=row[9]
            )


# =====================================================
# 9. PRODUCT RELATIONSHIP REPOSITORY
# =====================================================

class ProductRelationshipRepository:
    """Repository for product relationships and recommendations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create_relationship(self, relationship: ProductRelationshipCreate) -> ProductRelationship:
        """Create a product relationship."""
        async with self.db_manager.get_session() as session:
            query = """
                INSERT INTO product_relationships 
                (product_id, related_product_id, relationship_type, display_order, is_active)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING relationship_id, product_id, related_product_id, relationship_type,
                          display_order, is_active, created_at
            """
            
            result = await session.execute(
                text(query),
                [relationship.product_id, relationship.related_product_id,
                 relationship.relationship_type.value, relationship.display_order,
                 relationship.is_active]
            )
            row = result.fetchone()
            
            logger.info("product_relationship_created", relationship_id=row[0],
                       type=relationship.relationship_type.value)
            
            return ProductRelationship(
                relationship_id=row[0],
                product_id=row[1],
                related_product_id=row[2],
                relationship_type=ProductRelationshipType(row[3]),
                display_order=row[4],
                is_active=row[5],
                created_at=row[6]
            )
    
    async def create_recommendation(self, recommendation: ProductRecommendationCreate) -> ProductRecommendation:
        """Create a product recommendation."""
        async with self.db_manager.get_session() as session:
            query = """
                INSERT INTO product_recommendations 
                (product_id, recommended_product_id, recommendation_type, confidence_score,
                 recommendation_reason, display_order, is_active, expires_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING recommendation_id, product_id, recommended_product_id,
                          recommendation_type, confidence_score, recommendation_reason,
                          display_order, is_active, expires_at, generated_at
            """
            
            result = await session.execute(
                text(query),
                [recommendation.product_id, recommendation.recommended_product_id,
                 recommendation.recommendation_type.value,
                 float(recommendation.confidence_score) if recommendation.confidence_score else None,
                 recommendation.recommendation_reason, recommendation.display_order,
                 recommendation.is_active, recommendation.expires_at]
            )
            row = result.fetchone()
            
            logger.info("product_recommendation_created", recommendation_id=row[0],
                       type=recommendation.recommendation_type.value)
            
            return ProductRecommendation(
                recommendation_id=row[0],
                product_id=row[1],
                recommended_product_id=row[2],
                recommendation_type=RecommendationType(row[3]),
                confidence_score=Decimal(str(row[4])) if row[4] else None,
                recommendation_reason=row[5],
                display_order=row[6],
                is_active=row[7],
                expires_at=row[8],
                generated_at=row[9]
            )
    
    async def get_related_products(self, product_id: str, relationship_type: Optional[ProductRelationshipType] = None) -> List[ProductRelationship]:
        """Get related products."""
        async with self.db_manager.get_session() as session:
            if relationship_type:
                query = """
                    SELECT relationship_id, product_id, related_product_id, relationship_type,
                           display_order, is_active, created_at
                    FROM product_relationships
                    WHERE product_id = $1 AND relationship_type = $2 AND is_active = TRUE
                    ORDER BY display_order, created_at
                """
                result = await session.execute(text(query), [product_id, relationship_type.value])
            else:
                query = """
                    SELECT relationship_id, product_id, related_product_id, relationship_type,
                           display_order, is_active, created_at
                    FROM product_relationships
                    WHERE product_id = $1 AND is_active = TRUE
                    ORDER BY display_order, created_at
                """
                result = await session.execute(text(query), [product_id])
            
            rows = result.fetchall()
            
            return [
                ProductRelationship(
                    relationship_id=row[0],
                    product_id=row[1],
                    related_product_id=row[2],
                    relationship_type=ProductRelationshipType(row[3]),
                    display_order=row[4],
                    is_active=row[5],
                    created_at=row[6]
                )
                for row in rows
            ]


# =====================================================
# 10. PRODUCT LIFECYCLE REPOSITORY
# =====================================================

class ProductLifecycleRepository:
    """Repository for product lifecycle management."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create_lifecycle(self, lifecycle: ProductLifecycleCreate) -> ProductLifecycle:
        """Create a product lifecycle record."""
        async with self.db_manager.get_session() as session:
            query = """
                INSERT INTO product_lifecycle 
                (product_id, status, launch_date, discontinue_date, end_of_life_date,
                 status_reason, changed_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING lifecycle_id, product_id, status, launch_date, discontinue_date,
                          end_of_life_date, status_reason, changed_by, changed_at
            """
            
            result = await session.execute(
                text(query),
                [lifecycle.product_id, lifecycle.status.value, lifecycle.launch_date,
                 lifecycle.discontinue_date, lifecycle.end_of_life_date,
                 lifecycle.status_reason, lifecycle.changed_by]
            )
            row = result.fetchone()
            
            logger.info("product_lifecycle_created", lifecycle_id=row[0],
                       product_id=lifecycle.product_id, status=lifecycle.status.value)
            
            return ProductLifecycle(
                lifecycle_id=row[0],
                product_id=row[1],
                status=ProductStatus(row[2]),
                launch_date=row[3],
                discontinue_date=row[4],
                end_of_life_date=row[5],
                status_reason=row[6],
                changed_by=row[7],
                changed_at=row[8]
            )
    
    async def create_version(self, version: ProductVersionCreate) -> ProductVersion:
        """Create a product version snapshot."""
        async with self.db_manager.get_session() as session:
            version_id = str(uuid4())
            
            query = """
                INSERT INTO product_versions 
                (version_id, product_id, version_number, version_data, change_summary,
                 created_by)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING version_id, product_id, version_number, version_data,
                          change_summary, created_by, created_at
            """
            
            result = await session.execute(
                text(query),
                [version_id, version.product_id, version.version_number,
                 version.version_data, version.change_summary, version.created_by]
            )
            row = result.fetchone()
            
            logger.info("product_version_created", version_id=version_id,
                       product_id=version.product_id, version=version.version_number)
            
            return ProductVersion(
                version_id=UUID(row[0]),
                product_id=row[1],
                version_number=row[2],
                version_data=row[3],
                change_summary=row[4],
                created_by=row[5],
                created_at=row[6]
            )
    
    async def record_change(self, change: ProductChangeCreate) -> ProductChange:
        """Record a product change."""
        async with self.db_manager.get_session() as session:
            change_id = str(uuid4())
            
            query = """
                INSERT INTO product_changes 
                (change_id, product_id, field_name, old_value, new_value, change_type,
                 changed_by, change_reason)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING change_id, product_id, field_name, old_value, new_value,
                          change_type, changed_by, change_reason, created_at
            """
            
            result = await session.execute(
                text(query),
                [change_id, change.product_id, change.field_name, change.old_value,
                 change.new_value, change.change_type, change.changed_by, change.change_reason]
            )
            row = result.fetchone()
            
            logger.info("product_change_recorded", change_id=change_id,
                       product_id=change.product_id, field=change.field_name)
            
            return ProductChange(
                change_id=UUID(row[0]),
                product_id=row[1],
                field_name=row[2],
                old_value=row[3],
                new_value=row[4],
                change_type=row[5],
                changed_by=row[6],
                change_reason=row[7],
                created_at=row[8]
            )
    
    async def create_approval(self, approval: ProductApprovalCreate) -> ProductApproval:
        """Create a product approval request."""
        async with self.db_manager.get_session() as session:
            approval_id = str(uuid4())
            
            query = """
                INSERT INTO product_approvals 
                (approval_id, product_id, approval_type, requested_by, approval_data)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING approval_id, product_id, approval_type, requested_by,
                          approval_data, requested_at, reviewed_by, reviewed_at,
                          status, review_notes
            """
            
            result = await session.execute(
                text(query),
                [approval_id, approval.product_id, approval.approval_type.value,
                 approval.requested_by, approval.approval_data]
            )
            row = result.fetchone()
            
            logger.info("product_approval_created", approval_id=approval_id,
                       product_id=approval.product_id, type=approval.approval_type.value)
            
            return ProductApproval(
                approval_id=UUID(row[0]),
                product_id=row[1],
                approval_type=ApprovalType(row[2]),
                requested_by=row[3],
                approval_data=row[4],
                requested_at=row[5],
                reviewed_by=row[6],
                reviewed_at=row[7],
                status=ApprovalStatus(row[8]),
                review_notes=row[9]
            )
    
    async def review_approval(self, approval_id: UUID, review: ProductApprovalReview) -> Optional[ProductApproval]:
        """Review a product approval request."""
        async with self.db_manager.get_session() as session:
            query = """
                UPDATE product_approvals
                SET status = $1, reviewed_by = $2, reviewed_at = CURRENT_TIMESTAMP,
                    review_notes = $3
                WHERE approval_id = $4
                RETURNING approval_id, product_id, approval_type, requested_by,
                          approval_data, requested_at, reviewed_by, reviewed_at,
                          status, review_notes
            """
            
            result = await session.execute(
                text(query),
                [review.status.value, review.reviewed_by, review.review_notes, str(approval_id)]
            )
            row = result.fetchone()
            
            if not row:
                return None
            
            logger.info("product_approval_reviewed", approval_id=str(approval_id),
                       status=review.status.value, reviewed_by=review.reviewed_by)
            
            return ProductApproval(
                approval_id=UUID(row[0]),
                product_id=row[1],
                approval_type=ApprovalType(row[2]),
                requested_by=row[3],
                approval_data=row[4],
                requested_at=row[5],
                reviewed_by=row[6],
                reviewed_at=row[7],
                status=ApprovalStatus(row[8]),
                review_notes=row[9]
            )

