"""
Product Models for Enhanced Product Agent

This module contains all Pydantic models for the Product Agent enhancements including:
- Product Variants
- Product Bundles
- Product Media
- Product Categories
- Product Attributes
- Pricing Rules
- Product Reviews
- Product Inventory
- Product Relationships
- Product Lifecycle
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator


# =====================================================
# ENUMS
# =====================================================

class AttributeType(str, Enum):
    """Attribute data types."""
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    SELECT = "select"
    MULTISELECT = "multiselect"
    COLOR = "color"


class BundleType(str, Enum):
    """Bundle types."""
    FIXED = "fixed"  # Fixed set of products
    FLEXIBLE = "flexible"  # Customer can choose from options
    CUSTOM = "custom"  # Fully customizable


class PricingStrategy(str, Enum):
    """Bundle pricing strategies."""
    FIXED_PRICE = "fixed_price"
    PERCENTAGE_DISCOUNT = "percentage_discount"
    COMPONENT_SUM = "component_sum"


class MediaType(str, Enum):
    """Product media types."""
    VIDEO = "video"
    VIEW_360 = "360_view"
    PDF = "pdf"
    DOCUMENT = "document"


class ImageVariantType(str, Enum):
    """Image variant types."""
    THUMBNAIL = "thumbnail"
    MEDIUM = "medium"
    LARGE = "large"
    ZOOM = "zoom"


class PricingRuleType(str, Enum):
    """Pricing rule types."""
    TIERED = "tiered"
    SEGMENT = "segment"
    GEOGRAPHIC = "geographic"
    TIME_BASED = "time_based"
    COST_PLUS = "cost_plus"


class PriceChangeType(str, Enum):
    """Price change types."""
    MANUAL = "manual"
    RULE_BASED = "rule_based"
    AUTOMATED = "automated"
    COMPETITOR_MATCH = "competitor_match"


class InventoryTransactionType(str, Enum):
    """Inventory transaction types."""
    RECEIVED = "received"
    SOLD = "sold"
    ADJUSTED = "adjusted"
    TRANSFERRED = "transferred"
    RETURNED = "returned"


class ProductRelationshipType(str, Enum):
    """Product relationship types."""
    RELATED = "related"
    CROSS_SELL = "cross_sell"
    UP_SELL = "up_sell"
    ALTERNATIVE = "alternative"
    ACCESSORY = "accessory"
    FREQUENTLY_BOUGHT_TOGETHER = "frequently_bought_together"


class RecommendationType(str, Enum):
    """AI recommendation types."""
    AI_SIMILAR = "ai_similar"
    AI_COMPLEMENTARY = "ai_complementary"
    AI_TRENDING = "ai_trending"


class ProductStatus(str, Enum):
    """Product lifecycle status."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    ARCHIVED = "archived"


class ApprovalStatus(str, Enum):
    """Approval workflow status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalType(str, Enum):
    """Types of approvals."""
    NEW_PRODUCT = "new_product"
    PRICE_CHANGE = "price_change"
    MAJOR_UPDATE = "major_update"


# =====================================================
# 1. PRODUCT VARIANTS MODELS
# =====================================================

class VariantAttributeBase(BaseModel):
    """Base model for variant attributes."""
    attribute_name: str = Field(..., max_length=100)
    attribute_type: str = Field(..., max_length=50)
    display_order: int = 0
    is_required: bool = False
    is_visible: bool = True


class VariantAttributeCreate(VariantAttributeBase):
    """Model for creating a variant attribute."""
    pass


class VariantAttribute(VariantAttributeBase):
    """Complete variant attribute model."""
    attribute_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VariantAttributeValueBase(BaseModel):
    """Base model for variant attribute values."""
    variant_id: UUID
    attribute_id: int
    attribute_value: str


class VariantAttributeValueCreate(VariantAttributeValueBase):
    """Model for creating a variant attribute value."""
    pass


class VariantAttributeValue(VariantAttributeValueBase):
    """Complete variant attribute value model."""
    value_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProductVariantBase(BaseModel):
    """Base model for product variants."""
    parent_product_id: str = Field(..., max_length=255)
    variant_sku: str = Field(..., max_length=255)
    variant_name: Optional[str] = Field(None, max_length=255)
    is_master: bool = False
    is_active: bool = True
    sort_order: int = 0


class ProductVariantCreate(ProductVariantBase):
    """Model for creating a product variant."""
    attributes: List[Dict[str, Any]] = []  # List of {attribute_id, attribute_value}


class ProductVariantUpdate(BaseModel):
    """Model for updating a product variant."""
    variant_name: Optional[str] = None
    is_master: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class ProductVariant(ProductVariantBase):
    """Complete product variant model."""
    variant_id: UUID
    created_at: datetime
    updated_at: datetime
    attributes: List[VariantAttributeValue] = []

    class Config:
        from_attributes = True


class VariantPricingBase(BaseModel):
    """Base model for variant pricing."""
    variant_id: UUID
    price: Decimal = Field(..., ge=0, decimal_places=2)
    compare_at_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    valid_from: datetime = Field(default_factory=datetime.now)
    valid_to: Optional[datetime] = None
    is_active: bool = True


class VariantPricingCreate(VariantPricingBase):
    """Model for creating variant pricing."""
    pass


class VariantPricing(VariantPricingBase):
    """Complete variant pricing model."""
    pricing_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# 2. PRODUCT BUNDLES MODELS
# =====================================================

class BundleComponentBase(BaseModel):
    """Base model for bundle components."""
    product_id: str = Field(..., max_length=255)
    quantity: int = Field(default=1, gt=0)
    is_required: bool = True
    can_substitute: bool = False
    sort_order: int = 0


class BundleComponentCreate(BundleComponentBase):
    """Model for creating a bundle component."""
    pass


class BundleComponent(BundleComponentBase):
    """Complete bundle component model."""
    component_id: int
    bundle_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class BundlePricingRuleBase(BaseModel):
    """Base model for bundle pricing rules."""
    rule_type: str = Field(..., max_length=50)
    rule_condition: Dict[str, Any]
    discount_type: str = Field(..., max_length=50)
    discount_value: Decimal = Field(..., ge=0, decimal_places=2)
    priority: int = 0
    is_active: bool = True
    valid_from: datetime = Field(default_factory=datetime.now)
    valid_to: Optional[datetime] = None


class BundlePricingRuleCreate(BundlePricingRuleBase):
    """Model for creating a bundle pricing rule."""
    pass


class BundlePricingRule(BundlePricingRuleBase):
    """Complete bundle pricing rule model."""
    rule_id: int
    bundle_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ProductBundleBase(BaseModel):
    """Base model for product bundles."""
    bundle_name: str = Field(..., max_length=255)
    bundle_description: Optional[str] = None
    bundle_sku: str = Field(..., max_length=255)
    bundle_type: BundleType
    pricing_strategy: PricingStrategy
    bundle_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    is_active: bool = True
    valid_from: datetime = Field(default_factory=datetime.now)
    valid_to: Optional[datetime] = None
    max_quantity: Optional[int] = None
    created_by: Optional[str] = None


class ProductBundleCreate(ProductBundleBase):
    """Model for creating a product bundle."""
    components: List[BundleComponentCreate] = []
    pricing_rules: List[BundlePricingRuleCreate] = []


class ProductBundleUpdate(BaseModel):
    """Model for updating a product bundle."""
    bundle_name: Optional[str] = None
    bundle_description: Optional[str] = None
    bundle_price: Optional[Decimal] = None
    discount_percentage: Optional[Decimal] = None
    is_active: Optional[bool] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None


class ProductBundle(ProductBundleBase):
    """Complete product bundle model."""
    bundle_id: UUID
    created_at: datetime
    updated_at: datetime
    components: List[BundleComponent] = []
    pricing_rules: List[BundlePricingRule] = []

    class Config:
        from_attributes = True


# =====================================================
# 3. PRODUCT MEDIA MODELS
# =====================================================

class ImageVariantBase(BaseModel):
    """Base model for image variants."""
    variant_type: ImageVariantType
    image_url: str
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None


class ImageVariantCreate(ImageVariantBase):
    """Model for creating an image variant."""
    pass


class ImageVariant(ImageVariantBase):
    """Complete image variant model."""
    variant_id: int
    image_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ProductImageBase(BaseModel):
    """Base model for product images."""
    product_id: str = Field(..., max_length=255)
    image_url: str
    image_alt_text: Optional[str] = Field(None, max_length=255)
    image_caption: Optional[str] = None
    is_primary: bool = False
    display_order: int = 0
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = Field(None, max_length=50)


class ProductImageCreate(ProductImageBase):
    """Model for creating a product image."""
    variants: List[ImageVariantCreate] = []


class ProductImageUpdate(BaseModel):
    """Model for updating a product image."""
    image_alt_text: Optional[str] = None
    image_caption: Optional[str] = None
    is_primary: Optional[bool] = None
    display_order: Optional[int] = None


class ProductImage(ProductImageBase):
    """Complete product image model."""
    image_id: UUID
    created_at: datetime
    updated_at: datetime
    variants: List[ImageVariant] = []

    class Config:
        from_attributes = True


class ProductMediaBase(BaseModel):
    """Base model for product media."""
    product_id: str = Field(..., max_length=255)
    media_type: MediaType
    media_url: str
    thumbnail_url: Optional[str] = None
    media_title: Optional[str] = Field(None, max_length=255)
    media_description: Optional[str] = None
    duration: Optional[int] = None  # For videos, in seconds
    file_size: Optional[int] = None
    mime_type: Optional[str] = Field(None, max_length=50)
    display_order: int = 0
    is_active: bool = True


class ProductMediaCreate(ProductMediaBase):
    """Model for creating product media."""
    pass


class ProductMediaUpdate(BaseModel):
    """Model for updating product media."""
    media_title: Optional[str] = None
    media_description: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class ProductMedia(ProductMediaBase):
    """Complete product media model."""
    media_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# 4. PRODUCT CATEGORIES MODELS
# =====================================================

class CategoryAttributeBase(BaseModel):
    """Base model for category attributes."""
    attribute_name: str = Field(..., max_length=100)
    attribute_type: AttributeType
    is_required: bool = False
    is_filterable: bool = True
    is_searchable: bool = True
    default_value: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None
    display_order: int = 0


class CategoryAttributeCreate(CategoryAttributeBase):
    """Model for creating a category attribute."""
    category_id: int


class CategoryAttribute(CategoryAttributeBase):
    """Complete category attribute model."""
    attribute_id: int
    category_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProductCategoryBase(BaseModel):
    """Base model for product categories."""
    parent_id: Optional[int] = None
    category_name: str = Field(..., max_length=255)
    category_slug: str = Field(..., max_length=255)
    category_description: Optional[str] = None
    category_image_url: Optional[str] = None
    level: int = 0
    path: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    seo_title: Optional[str] = Field(None, max_length=255)
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = None


class ProductCategoryCreate(ProductCategoryBase):
    """Model for creating a product category."""
    pass


class ProductCategoryUpdate(BaseModel):
    """Model for updating a product category."""
    category_name: Optional[str] = None
    category_description: Optional[str] = None
    category_image_url: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None


class ProductCategory(ProductCategoryBase):
    """Complete product category model."""
    category_id: int
    created_at: datetime
    updated_at: datetime
    attributes: List[CategoryAttribute] = []
    children: List['ProductCategory'] = []

    class Config:
        from_attributes = True


# Enable forward references
ProductCategory.model_rebuild()


class ProductCategoryMapping(BaseModel):
    """Model for product-category mapping."""
    mapping_id: int
    product_id: str
    category_id: int
    is_primary: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# 5. PRODUCT ATTRIBUTES MODELS
# =====================================================

class AttributeGroupBase(BaseModel):
    """Base model for attribute groups."""
    group_name: str = Field(..., max_length=100)
    group_description: Optional[str] = None
    display_order: int = 0
    is_active: bool = True


class AttributeGroupCreate(AttributeGroupBase):
    """Model for creating an attribute group."""
    pass


class AttributeGroup(AttributeGroupBase):
    """Complete attribute group model."""
    group_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductAttributeBase(BaseModel):
    """Base model for product attributes."""
    group_id: Optional[int] = None
    attribute_name: str = Field(..., max_length=100)
    attribute_code: str = Field(..., max_length=100)
    attribute_type: AttributeType
    unit: Optional[str] = Field(None, max_length=50)
    is_required: bool = False
    is_filterable: bool = True
    is_searchable: bool = True
    is_comparable: bool = True
    validation_rules: Optional[Dict[str, Any]] = None
    possible_values: Optional[List[str]] = None
    display_order: int = 0


class ProductAttributeCreate(ProductAttributeBase):
    """Model for creating a product attribute."""
    pass


class ProductAttribute(ProductAttributeBase):
    """Complete product attribute model."""
    attribute_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductAttributeValueBase(BaseModel):
    """Base model for product attribute values."""
    product_id: str = Field(..., max_length=255)
    attribute_id: int
    attribute_value: str


class ProductAttributeValueCreate(ProductAttributeValueBase):
    """Model for creating a product attribute value."""
    pass


class ProductAttributeValue(ProductAttributeValueBase):
    """Complete product attribute value model."""
    value_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# FILTER MODELS
# =====================================================

class ProductVariantFilter(BaseModel):
    """Filter model for product variants."""
    parent_product_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_master: Optional[bool] = None


class ProductBundleFilter(BaseModel):
    """Filter model for product bundles."""
    bundle_type: Optional[BundleType] = None
    is_active: Optional[bool] = None
    valid_at: Optional[datetime] = None


class ProductImageFilter(BaseModel):
    """Filter model for product images."""
    product_id: Optional[str] = None
    is_primary: Optional[bool] = None


class ProductCategoryFilter(BaseModel):
    """Filter model for product categories."""
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None
    level: Optional[int] = None




# =====================================================
# 6. PRICING RULES MODELS
# =====================================================

class PricingTierBase(BaseModel):
    """Base model for pricing tiers."""
    min_quantity: int = Field(..., gt=0)
    max_quantity: Optional[int] = None
    price: Decimal = Field(..., ge=0, decimal_places=2)
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)


class PricingTierCreate(PricingTierBase):
    """Model for creating a pricing tier."""
    pass


class PricingTier(PricingTierBase):
    """Complete pricing tier model."""
    tier_id: int
    rule_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class PricingRuleBase(BaseModel):
    """Base model for pricing rules."""
    product_id: str = Field(..., max_length=255)
    rule_name: str = Field(..., max_length=255)
    rule_type: PricingRuleType
    rule_config: Dict[str, Any]
    priority: int = 0
    is_active: bool = True
    valid_from: datetime = Field(default_factory=datetime.now)
    valid_to: Optional[datetime] = None
    created_by: Optional[str] = None


class PricingRuleCreate(PricingRuleBase):
    """Model for creating a pricing rule."""
    tiers: List[PricingTierCreate] = []


class PricingRuleUpdate(BaseModel):
    """Model for updating a pricing rule."""
    rule_name: Optional[str] = None
    rule_config: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None


class PricingRule(PricingRuleBase):
    """Complete pricing rule model."""
    rule_id: UUID
    created_at: datetime
    updated_at: datetime
    tiers: List[PricingTier] = []

    class Config:
        from_attributes = True


class PriceHistoryBase(BaseModel):
    """Base model for price history."""
    product_id: str = Field(..., max_length=255)
    old_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    new_price: Decimal = Field(..., ge=0, decimal_places=2)
    change_reason: Optional[str] = None
    changed_by: Optional[str] = None
    change_type: PriceChangeType
    effective_date: datetime = Field(default_factory=datetime.now)


class PriceHistoryCreate(PriceHistoryBase):
    """Model for creating a price history entry."""
    pass


class PriceHistory(PriceHistoryBase):
    """Complete price history model."""
    history_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CompetitorPriceBase(BaseModel):
    """Base model for competitor prices."""
    product_id: str = Field(..., max_length=255)
    competitor_name: str = Field(..., max_length=255)
    competitor_url: Optional[str] = None
    competitor_price: Decimal = Field(..., ge=0, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    is_available: bool = True
    last_checked: datetime = Field(default_factory=datetime.now)


class CompetitorPriceCreate(CompetitorPriceBase):
    """Model for creating a competitor price entry."""
    pass


class CompetitorPrice(CompetitorPriceBase):
    """Complete competitor price model."""
    tracking_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# 7. PRODUCT REVIEWS MODELS
# =====================================================

class ReviewImageBase(BaseModel):
    """Base model for review images."""
    image_url: str
    image_caption: Optional[str] = None
    display_order: int = 0


class ReviewImageCreate(ReviewImageBase):
    """Model for creating a review image."""
    pass


class ReviewImage(ReviewImageBase):
    """Complete review image model."""
    image_id: UUID
    review_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewVoteBase(BaseModel):
    """Base model for review votes."""
    review_id: UUID
    customer_id: str = Field(..., max_length=255)
    vote_type: str = Field(..., max_length=20)  # helpful, not_helpful


class ReviewVoteCreate(ReviewVoteBase):
    """Model for creating a review vote."""
    pass


class ReviewVote(ReviewVoteBase):
    """Complete review vote model."""
    vote_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewResponseBase(BaseModel):
    """Base model for review responses."""
    response_text: str
    responded_by: str = Field(..., max_length=255)


class ReviewResponseCreate(ReviewResponseBase):
    """Model for creating a review response."""
    pass


class ReviewResponseUpdate(BaseModel):
    """Model for updating a review response."""
    response_text: str


class ReviewResponse(ReviewResponseBase):
    """Complete review response model."""
    response_id: UUID
    review_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductReviewBase(BaseModel):
    """Base model for product reviews."""
    product_id: str = Field(..., max_length=255)
    customer_id: str = Field(..., max_length=255)
    order_id: Optional[str] = Field(None, max_length=255)
    rating: int = Field(..., ge=1, le=5)
    review_title: Optional[str] = Field(None, max_length=255)
    review_text: Optional[str] = None
    is_verified_purchase: bool = False


class ProductReviewCreate(ProductReviewBase):
    """Model for creating a product review."""
    images: List[ReviewImageCreate] = []


class ProductReviewUpdate(BaseModel):
    """Model for updating a product review."""
    rating: Optional[int] = Field(None, ge=1, le=5)
    review_title: Optional[str] = None
    review_text: Optional[str] = None


class ProductReview(ProductReviewBase):
    """Complete product review model."""
    review_id: UUID
    is_approved: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    helpful_count: int = 0
    not_helpful_count: int = 0
    created_at: datetime
    updated_at: datetime
    images: List[ReviewImage] = []
    response: Optional[ReviewResponse] = None

    class Config:
        from_attributes = True


# =====================================================
# 8. PRODUCT INVENTORY MODELS
# =====================================================

class ProductInventoryBase(BaseModel):
    """Base model for product inventory."""
    product_id: str = Field(..., max_length=255)
    location_id: str = Field(..., max_length=255)
    quantity_available: int = Field(default=0, ge=0)
    quantity_reserved: int = Field(default=0, ge=0)
    quantity_on_order: int = Field(default=0, ge=0)
    reorder_point: int = Field(default=0, ge=0)
    reorder_quantity: int = Field(default=0, ge=0)
    last_counted: Optional[datetime] = None


class ProductInventoryCreate(ProductInventoryBase):
    """Model for creating product inventory."""
    pass


class ProductInventoryUpdate(BaseModel):
    """Model for updating product inventory."""
    quantity_available: Optional[int] = None
    quantity_reserved: Optional[int] = None
    quantity_on_order: Optional[int] = None
    reorder_point: Optional[int] = None
    reorder_quantity: Optional[int] = None
    last_counted: Optional[datetime] = None


class ProductInventory(ProductInventoryBase):
    """Complete product inventory model."""
    inventory_id: int
    last_updated: datetime

    class Config:
        from_attributes = True


class InventoryTransactionBase(BaseModel):
    """Base model for inventory transactions."""
    product_id: str = Field(..., max_length=255)
    location_id: str = Field(..., max_length=255)
    transaction_type: InventoryTransactionType
    quantity: int  # Positive for additions, negative for reductions
    reference_id: Optional[str] = Field(None, max_length=255)
    reference_type: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    created_by: Optional[str] = None


class InventoryTransactionCreate(InventoryTransactionBase):
    """Model for creating an inventory transaction."""
    pass


class InventoryTransaction(InventoryTransactionBase):
    """Complete inventory transaction model."""
    transaction_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class InventoryReservationBase(BaseModel):
    """Base model for inventory reservations."""
    product_id: str = Field(..., max_length=255)
    location_id: str = Field(..., max_length=255)
    order_id: str = Field(..., max_length=255)
    quantity_reserved: int = Field(..., gt=0)
    reserved_until: datetime


class InventoryReservationCreate(InventoryReservationBase):
    """Model for creating an inventory reservation."""
    pass


class InventoryReservation(InventoryReservationBase):
    """Complete inventory reservation model."""
    reservation_id: UUID
    is_active: bool = True
    created_at: datetime
    released_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InventoryBatchBase(BaseModel):
    """Base model for inventory batches."""
    product_id: str = Field(..., max_length=255)
    location_id: str = Field(..., max_length=255)
    batch_number: str = Field(..., max_length=255)
    quantity: int = Field(..., gt=0)
    manufacture_date: Optional[date] = None
    expiration_date: Optional[date] = None
    received_date: date = Field(default_factory=date.today)
    supplier_id: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    is_active: bool = True


class InventoryBatchCreate(InventoryBatchBase):
    """Model for creating an inventory batch."""
    pass


class InventoryBatch(InventoryBatchBase):
    """Complete inventory batch model."""
    batch_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class InventoryAdjustmentRequest(BaseModel):
    """Request model for inventory adjustments."""
    product_id: str
    location_id: str
    adjustment_quantity: int  # Can be positive or negative
    reason: str
    adjusted_by: str


# =====================================================
# 9. PRODUCT RELATIONSHIPS MODELS
# =====================================================

class ProductRelationshipBase(BaseModel):
    """Base model for product relationships."""
    product_id: str = Field(..., max_length=255)
    related_product_id: str = Field(..., max_length=255)
    relationship_type: ProductRelationshipType
    display_order: int = 0
    is_active: bool = True


class ProductRelationshipCreate(ProductRelationshipBase):
    """Model for creating a product relationship."""
    pass


class ProductRelationship(ProductRelationshipBase):
    """Complete product relationship model."""
    relationship_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProductRecommendationBase(BaseModel):
    """Base model for product recommendations."""
    product_id: str = Field(..., max_length=255)
    recommended_product_id: str = Field(..., max_length=255)
    recommendation_type: RecommendationType
    confidence_score: Optional[Decimal] = Field(None, ge=0, le=1, decimal_places=4)
    recommendation_reason: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    expires_at: Optional[datetime] = None


class ProductRecommendationCreate(ProductRecommendationBase):
    """Model for creating a product recommendation."""
    pass


class ProductRecommendation(ProductRecommendationBase):
    """Complete product recommendation model."""
    recommendation_id: int
    generated_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# 10. PRODUCT LIFECYCLE MODELS
# =====================================================

class ProductLifecycleBase(BaseModel):
    """Base model for product lifecycle."""
    product_id: str = Field(..., max_length=255)
    status: ProductStatus
    launch_date: Optional[date] = None
    discontinue_date: Optional[date] = None
    end_of_life_date: Optional[date] = None
    status_reason: Optional[str] = None
    changed_by: Optional[str] = None


class ProductLifecycleCreate(ProductLifecycleBase):
    """Model for creating product lifecycle entry."""
    pass


class ProductLifecycleUpdate(BaseModel):
    """Model for updating product lifecycle."""
    status: Optional[ProductStatus] = None
    launch_date: Optional[date] = None
    discontinue_date: Optional[date] = None
    end_of_life_date: Optional[date] = None
    status_reason: Optional[str] = None


class ProductLifecycle(ProductLifecycleBase):
    """Complete product lifecycle model."""
    lifecycle_id: int
    changed_at: datetime

    class Config:
        from_attributes = True


class ProductVersionBase(BaseModel):
    """Base model for product versions."""
    product_id: str = Field(..., max_length=255)
    version_number: int
    version_data: Dict[str, Any]
    change_summary: Optional[str] = None
    created_by: Optional[str] = None


class ProductVersionCreate(ProductVersionBase):
    """Model for creating a product version."""
    pass


class ProductVersion(ProductVersionBase):
    """Complete product version model."""
    version_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ProductChangeBase(BaseModel):
    """Base model for product changes."""
    product_id: str = Field(..., max_length=255)
    field_name: str = Field(..., max_length=100)
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    change_type: Optional[str] = Field(None, max_length=50)
    changed_by: Optional[str] = None
    change_reason: Optional[str] = None


class ProductChangeCreate(ProductChangeBase):
    """Model for creating a product change entry."""
    pass


class ProductChange(ProductChangeBase):
    """Complete product change model."""
    change_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ProductApprovalBase(BaseModel):
    """Base model for product approvals."""
    product_id: str = Field(..., max_length=255)
    approval_type: ApprovalType
    requested_by: str = Field(..., max_length=255)
    approval_data: Optional[Dict[str, Any]] = None


class ProductApprovalCreate(ProductApprovalBase):
    """Model for creating a product approval request."""
    pass


class ProductApprovalReview(BaseModel):
    """Model for reviewing a product approval."""
    status: ApprovalStatus
    review_notes: Optional[str] = None
    reviewed_by: str


class ProductApproval(ProductApprovalBase):
    """Complete product approval model."""
    approval_id: UUID
    requested_at: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    review_notes: Optional[str] = None

    class Config:
        from_attributes = True


# =====================================================
# SUMMARY AND ANALYTICS MODELS
# =====================================================

class ProductInventorySummary(BaseModel):
    """Summary model for product inventory across locations."""
    product_id: str
    total_available: int
    total_reserved: int
    total_on_order: int
    sellable_quantity: int
    location_count: int
    min_location_stock: int
    max_location_stock: int
    last_inventory_update: datetime

    class Config:
        from_attributes = True


class ProductRatingSummary(BaseModel):
    """Summary model for product ratings and reviews."""
    product_id: str
    total_reviews: int
    verified_reviews: int
    average_rating: Decimal
    five_star_count: int
    four_star_count: int
    three_star_count: int
    two_star_count: int
    one_star_count: int
    total_helpful_votes: int
    latest_review_date: datetime

    class Config:
        from_attributes = True


class ProductPricingSummary(BaseModel):
    """Summary model for product pricing."""
    product_id: str
    base_price: Decimal
    base_cost: Decimal
    min_tiered_price: Decimal
    max_tiered_price: Decimal
    active_pricing_rules: int
    last_price_change: Optional[datetime]
    avg_competitor_price: Decimal
    min_competitor_price: Decimal

    class Config:
        from_attributes = True


# =====================================================
# REQUEST/RESPONSE MODELS
# =====================================================

class BulkPriceUpdateRequest(BaseModel):
    """Request model for bulk price updates."""
    product_ids: List[str]
    price_adjustment: Decimal  # Can be positive or negative
    adjustment_type: str  # percentage, fixed_amount
    reason: str
    changed_by: str


class GenerateRecommendationsRequest(BaseModel):
    """Request model for generating AI recommendations."""
    product_id: str
    recommendation_types: List[RecommendationType]
    max_recommendations: int = 10


class ProductSearchRequest(BaseModel):
    """Request model for advanced product search."""
    query: Optional[str] = None
    category_ids: Optional[List[int]] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    min_rating: Optional[int] = None
    attributes: Optional[Dict[str, Any]] = None
    in_stock_only: bool = False
    page: int = 1
    per_page: int = 20
    sort_by: Optional[str] = "relevance"  # relevance, price_asc, price_desc, rating, newest


class ProductVariantWithInventory(BaseModel):
    """Product variant with inventory information."""
    variant: ProductVariant
    inventory: Optional[ProductInventorySummary] = None
    pricing: Optional[VariantPricing] = None


class ProductBundleWithDetails(BaseModel):
    """Product bundle with full component details."""
    bundle: ProductBundle
    total_component_price: Decimal
    effective_price: Decimal
    savings: Decimal
    savings_percentage: Decimal


class ProductWithFullDetails(BaseModel):
    """Complete product information with all enhancements."""
    product_id: str
    name: str
    description: str
    base_price: Decimal
    variants: List[ProductVariant] = []
    bundles: List[ProductBundle] = []
    images: List[ProductImage] = []
    media: List[ProductMedia] = []
    categories: List[ProductCategory] = []
    attributes: List[ProductAttributeValue] = []
    reviews_summary: Optional[ProductRatingSummary] = None
    inventory_summary: Optional[ProductInventorySummary] = None
    pricing_summary: Optional[ProductPricingSummary] = None
    related_products: List[ProductRelationship] = []
    recommendations: List[ProductRecommendation] = []
    lifecycle: Optional[ProductLifecycle] = None

