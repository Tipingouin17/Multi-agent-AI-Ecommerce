# Product Agent Phase 2 - Enhancement Design

## Overview

This document outlines the comprehensive enhancements for the Product Agent, following the successful pattern established in Order Agent Phase 1.

---

## Current Product Agent Capabilities

### Existing Features
- ✅ Basic product catalog management (CRUD)
- ✅ Product search by name/description
- ✅ Filter by category, brand, condition
- ✅ Price updates
- ✅ Channel synchronization
- ✅ Basic repository pattern
- ✅ FastAPI endpoints

### Existing Database Schema
- `products` table with basic fields:
  - id, name, description, category, brand, sku
  - price, cost, weight, dimensions
  - condition, grade (for refurbished)
  - created_at, updated_at

---

## Proposed Enhancements

### 1. Product Variants & Options
**Use Case:** Manage products with multiple variants (size, color, material, etc.)

**Features:**
- Product variant management (parent-child relationships)
- Variant attributes (size, color, material, style)
- Variant-specific pricing and inventory
- Variant images and descriptions
- SKU generation for variants

**Database Tables:**
- `product_variants` - Variant records
- `variant_attributes` - Attribute definitions (size, color, etc.)
- `variant_attribute_values` - Specific values for each variant
- `variant_pricing` - Variant-specific pricing rules

---

### 2. Product Bundles & Kits
**Use Case:** Create product bundles and kits for promotions

**Features:**
- Bundle creation (multiple products as one)
- Kit management (products sold together)
- Bundle pricing (fixed or percentage discount)
- Component product tracking
- Inventory synchronization for bundles

**Database Tables:**
- `product_bundles` - Bundle definitions
- `bundle_components` - Products in each bundle
- `bundle_pricing_rules` - Pricing strategies for bundles

---

### 3. Product Images & Media
**Use Case:** Manage multiple images and media for products

**Features:**
- Multiple images per product
- Image ordering and primary image
- Image variants (thumbnail, full-size, zoom)
- Video support
- 360-degree view support
- Image metadata (alt text, captions)

**Database Tables:**
- `product_images` - Image records
- `product_media` - Videos and other media
- `image_variants` - Different sizes/formats

---

### 4. Product Categories & Taxonomy
**Use Case:** Hierarchical category management

**Features:**
- Multi-level category hierarchy
- Category attributes and filters
- Category-specific fields
- Category images and descriptions
- Category SEO metadata

**Database Tables:**
- `product_categories` - Category hierarchy
- `category_attributes` - Category-specific attributes
- `product_category_mapping` - Many-to-many relationship

---

### 5. Product Attributes & Specifications
**Use Case:** Flexible product specifications

**Features:**
- Custom attributes per product
- Attribute groups (Technical Specs, Dimensions, etc.)
- Attribute data types (text, number, boolean, date)
- Searchable and filterable attributes
- Attribute validation rules

**Database Tables:**
- `product_attributes` - Attribute definitions
- `product_attribute_values` - Values for each product
- `attribute_groups` - Logical grouping of attributes

---

### 6. Pricing Rules & Strategies
**Use Case:** Advanced pricing management

**Features:**
- Tiered pricing (quantity-based)
- Customer segment pricing
- Time-based pricing (sales, promotions)
- Geographic pricing
- Cost-plus pricing rules
- Competitor price tracking
- Price history and audit trail

**Database Tables:**
- `pricing_rules` - Rule definitions
- `pricing_tiers` - Quantity-based pricing
- `price_history` - Historical price changes
- `competitor_prices` - Competitor price tracking

---

### 7. Product Reviews & Ratings
**Use Case:** Customer feedback management

**Features:**
- Product reviews with ratings
- Review moderation workflow
- Verified purchase reviews
- Review images
- Helpful votes
- Review responses from sellers
- Review statistics and aggregation

**Database Tables:**
- `product_reviews` - Review records
- `review_images` - Images attached to reviews
- `review_votes` - Helpful/not helpful votes
- `review_responses` - Seller responses

---

### 8. Product Inventory Tracking
**Use Case:** Real-time inventory management

**Features:**
- Multi-location inventory
- Inventory reservations
- Low stock alerts
- Inventory history
- Inventory adjustments
- Batch/lot tracking
- Expiration date tracking

**Database Tables:**
- `product_inventory` - Inventory levels by location
- `inventory_transactions` - Inventory movements
- `inventory_reservations` - Reserved inventory
- `inventory_batches` - Batch/lot tracking

---

### 9. Product Relationships
**Use Case:** Related products and cross-selling

**Features:**
- Related products
- Cross-sell recommendations
- Up-sell recommendations
- Frequently bought together
- Alternative products
- Accessory products

**Database Tables:**
- `product_relationships` - Relationship definitions
- `product_recommendations` - AI-generated recommendations

---

### 10. Product Lifecycle Management
**Use Case:** Track product status through lifecycle

**Features:**
- Product status (draft, active, discontinued, archived)
- Launch dates and end-of-life dates
- Product versioning
- Change history
- Approval workflows
- Product retirement process

**Database Tables:**
- `product_lifecycle` - Lifecycle status tracking
- `product_versions` - Version history
- `product_changes` - Change audit trail
- `product_approvals` - Approval workflow

---

## Database Schema Design

### Summary of New Tables

1. **Product Variants (4 tables)**
   - product_variants
   - variant_attributes
   - variant_attribute_values
   - variant_pricing

2. **Product Bundles (3 tables)**
   - product_bundles
   - bundle_components
   - bundle_pricing_rules

3. **Product Media (3 tables)**
   - product_images
   - product_media
   - image_variants

4. **Product Categories (3 tables)**
   - product_categories
   - category_attributes
   - product_category_mapping

5. **Product Attributes (3 tables)**
   - product_attributes
   - product_attribute_values
   - attribute_groups

6. **Pricing Rules (4 tables)**
   - pricing_rules
   - pricing_tiers
   - price_history
   - competitor_prices

7. **Product Reviews (4 tables)**
   - product_reviews
   - review_images
   - review_votes
   - review_responses

8. **Product Inventory (4 tables)**
   - product_inventory
   - inventory_transactions
   - inventory_reservations
   - inventory_batches

9. **Product Relationships (2 tables)**
   - product_relationships
   - product_recommendations

10. **Product Lifecycle (4 tables)**
    - product_lifecycle
    - product_versions
    - product_changes
    - product_approvals

**Total: 38 new tables**

---

## Indexes Strategy

### High-Priority Indexes
- product_variants: (parent_product_id, is_active)
- product_bundles: (is_active, valid_from, valid_to)
- product_images: (product_id, display_order)
- product_categories: (parent_id, is_active)
- product_attributes: (product_id, attribute_id)
- pricing_rules: (product_id, is_active, valid_from, valid_to)
- product_reviews: (product_id, is_approved, created_at)
- product_inventory: (product_id, location_id)
- product_relationships: (product_id, relationship_type)
- product_lifecycle: (product_id, status)

**Total: ~50 indexes**

---

## Materialized Views

### 1. product_inventory_summary
```sql
SELECT 
    product_id,
    SUM(quantity_available) as total_available,
    SUM(quantity_reserved) as total_reserved,
    COUNT(DISTINCT location_id) as location_count,
    MIN(quantity_available) as min_location_stock
FROM product_inventory
GROUP BY product_id;
```

### 2. product_rating_summary
```sql
SELECT 
    product_id,
    COUNT(*) as review_count,
    AVG(rating) as average_rating,
    COUNT(CASE WHEN rating = 5 THEN 1 END) as five_star_count,
    COUNT(CASE WHEN rating = 4 THEN 1 END) as four_star_count,
    COUNT(CASE WHEN rating = 3 THEN 1 END) as three_star_count,
    COUNT(CASE WHEN rating = 2 THEN 1 END) as two_star_count,
    COUNT(CASE WHEN rating = 1 THEN 1 END) as one_star_count
FROM product_reviews
WHERE is_approved = true
GROUP BY product_id;
```

### 3. product_pricing_summary
```sql
SELECT 
    p.id as product_id,
    p.price as base_price,
    MIN(pr.price) as min_price,
    MAX(pr.price) as max_price,
    COUNT(pr.id) as active_rules_count
FROM products p
LEFT JOIN pricing_rules pr ON p.id = pr.product_id 
    AND pr.is_active = true 
    AND CURRENT_TIMESTAMP BETWEEN pr.valid_from AND pr.valid_to
GROUP BY p.id, p.price;
```

**Total: 3 materialized views**

---

## Pydantic Models Design

### Model Categories

1. **Product Variants (12 models)**
   - ProductVariant, ProductVariantCreate, ProductVariantUpdate
   - VariantAttribute, VariantAttributeCreate
   - VariantAttributeValue, VariantAttributeValueCreate
   - VariantPricing, VariantPricingCreate

2. **Product Bundles (9 models)**
   - ProductBundle, ProductBundleCreate, ProductBundleUpdate
   - BundleComponent, BundleComponentCreate
   - BundlePricingRule, BundlePricingRuleCreate

3. **Product Media (12 models)**
   - ProductImage, ProductImageCreate, ProductImageUpdate
   - ProductMedia, ProductMediaCreate
   - ImageVariant, ImageVariantCreate

4. **Product Categories (9 models)**
   - ProductCategory, ProductCategoryCreate, ProductCategoryUpdate
   - CategoryAttribute, CategoryAttributeCreate

5. **Product Attributes (12 models)**
   - ProductAttribute, ProductAttributeCreate
   - ProductAttributeValue, ProductAttributeValueCreate
   - AttributeGroup, AttributeGroupCreate

6. **Pricing Rules (15 models)**
   - PricingRule, PricingRuleCreate, PricingRuleUpdate
   - PricingTier, PricingTierCreate
   - PriceHistory, CompetitorPrice

7. **Product Reviews (15 models)**
   - ProductReview, ProductReviewCreate, ProductReviewUpdate
   - ReviewImage, ReviewVote, ReviewResponse

8. **Product Inventory (15 models)**
   - ProductInventory, InventoryTransaction, InventoryReservation
   - InventoryBatch, InventoryAdjustment

9. **Product Relationships (6 models)**
   - ProductRelationship, ProductRecommendation

10. **Product Lifecycle (12 models)**
    - ProductLifecycle, ProductVersion, ProductChange, ProductApproval

**Total: ~120 Pydantic models**

---

## Service Layer Design

### Service Classes

1. **ProductVariantService** - Manage product variants
2. **ProductBundleService** - Manage bundles and kits
3. **ProductMediaService** - Manage images and media
4. **ProductCategoryService** - Manage category hierarchy
5. **ProductAttributeService** - Manage custom attributes
6. **ProductPricingService** - Manage pricing rules
7. **ProductReviewService** - Manage reviews and ratings
8. **ProductInventoryService** - Manage inventory tracking
9. **ProductRelationshipService** - Manage product relationships
10. **ProductLifecycleService** - Manage product lifecycle

**Total: 10 service classes**

### Main Orchestrator
- **EnhancedProductService** - Unified facade for all services

---

## API Endpoints Design

### Endpoint Categories

1. **Product Variants (8 endpoints)**
   - POST /products/{id}/variants
   - GET /products/{id}/variants
   - PUT /variants/{id}
   - DELETE /variants/{id}
   - GET /variants/{id}/attributes
   - POST /variants/{id}/attributes
   - GET /variants/{id}/pricing
   - PUT /variants/{id}/pricing

2. **Product Bundles (6 endpoints)**
   - POST /bundles
   - GET /bundles
   - GET /bundles/{id}
   - PUT /bundles/{id}
   - POST /bundles/{id}/components
   - DELETE /bundles/{id}/components/{component_id}

3. **Product Media (8 endpoints)**
   - POST /products/{id}/images
   - GET /products/{id}/images
   - PUT /images/{id}
   - DELETE /images/{id}
   - POST /products/{id}/media
   - GET /products/{id}/media
   - PUT /media/{id}
   - DELETE /media/{id}

4. **Product Categories (6 endpoints)**
   - POST /categories
   - GET /categories
   - GET /categories/{id}
   - PUT /categories/{id}
   - GET /categories/{id}/products
   - POST /products/{id}/categories

5. **Product Attributes (6 endpoints)**
   - POST /products/{id}/attributes
   - GET /products/{id}/attributes
   - PUT /attributes/{id}
   - DELETE /attributes/{id}
   - GET /attribute-groups
   - POST /attribute-groups

6. **Pricing Rules (8 endpoints)**
   - POST /products/{id}/pricing-rules
   - GET /products/{id}/pricing-rules
   - PUT /pricing-rules/{id}
   - DELETE /pricing-rules/{id}
   - GET /products/{id}/price-history
   - POST /products/{id}/competitor-prices
   - GET /products/{id}/effective-price
   - POST /pricing-rules/bulk-update

7. **Product Reviews (8 endpoints)**
   - POST /products/{id}/reviews
   - GET /products/{id}/reviews
   - PUT /reviews/{id}
   - DELETE /reviews/{id}
   - POST /reviews/{id}/vote
   - POST /reviews/{id}/response
   - PUT /reviews/{id}/approve
   - GET /reviews/pending

8. **Product Inventory (10 endpoints)**
   - GET /products/{id}/inventory
   - POST /products/{id}/inventory/adjust
   - POST /products/{id}/inventory/reserve
   - DELETE /inventory/reservations/{id}
   - GET /inventory/low-stock
   - POST /inventory/transactions
   - GET /inventory/transactions
   - POST /inventory/batches
   - GET /inventory/batches
   - GET /inventory/summary

9. **Product Relationships (4 endpoints)**
   - POST /products/{id}/relationships
   - GET /products/{id}/relationships
   - GET /products/{id}/recommendations
   - POST /products/{id}/recommendations/generate

10. **Product Lifecycle (6 endpoints)**
    - GET /products/{id}/lifecycle
    - PUT /products/{id}/lifecycle/status
    - GET /products/{id}/versions
    - GET /products/{id}/changes
    - POST /products/{id}/approval-request
    - POST /approvals/{id}/review

**Total: ~70 API endpoints**

---

## UI Components Design

### Main Component
**ProductManagement.tsx** - Comprehensive product management interface

### Sub-Components

1. **ProductVariantManager** - Manage product variants
2. **ProductBundleManager** - Create and manage bundles
3. **ProductMediaGallery** - Image and media management
4. **ProductCategoryTree** - Hierarchical category selector
5. **ProductAttributeEditor** - Custom attribute management
6. **ProductPricingManager** - Pricing rules and history
7. **ProductReviewManager** - Review moderation and responses
8. **ProductInventoryTracker** - Real-time inventory tracking
9. **ProductRelationshipEditor** - Related products management
10. **ProductLifecycleTracker** - Status and version tracking

**Total: ~1000 lines of React/TypeScript code**

---

## Testing Strategy

### Test Categories

1. **Unit Tests (50 tests)**
   - Repository methods
   - Service logic
   - Model validation
   - Utility functions

2. **Integration Tests (30 tests)**
   - API endpoints
   - Database operations
   - Service interactions
   - Kafka messaging

3. **Performance Tests (10 tests)**
   - Bulk operations
   - Query performance
   - Concurrent access
   - Cache effectiveness

4. **Error Handling Tests (10 tests)**
   - Invalid data
   - Missing resources
   - Constraint violations
   - Edge cases

**Total: 100 comprehensive tests**

### Test Fixtures (Lessons Learned Applied)
- ✅ Proper db_config fixture from environment
- ✅ Session-scoped db_manager fixture
- ✅ Test-specific .env.test configuration
- ✅ Proper async/await throughout
- ✅ Graceful skipping if database unavailable
- ✅ Mock fixtures for external services

---

## Implementation Timeline

### Phase 2.1: Foundation (Week 2)
- Database migration (38 tables, 50 indexes, 3 views)
- Core Pydantic models (120 models)
- Base repository classes

### Phase 2.2: Core Services (Week 3)
- 10 service classes
- Business logic implementation
- Kafka event publishing

### Phase 2.3: API Layer (Week 4)
- 70 API endpoints
- Request/response validation
- Error handling

### Phase 2.4: UI Components (Week 5)
- React components (1000+ lines)
- Real-time updates
- Responsive design

### Phase 2.5: Testing & Documentation (Week 6)
- 100 comprehensive tests
- Complete documentation
- Integration guide

**Total: 5 weeks for Product Agent Phase 2**

---

## Success Criteria

- [ ] All 38 tables created with proper indexes
- [ ] All 120 Pydantic models implemented
- [ ] All 10 service classes functional
- [ ] All 70 API endpoints working
- [ ] UI components fully functional
- [ ] 100 tests passing
- [ ] Complete documentation
- [ ] No errors in logs
- [ ] User validation successful

---

## Lessons Learned Applied

From Order Agent Phase 1:
- ✅ Proper test fixtures from the start
- ✅ Environment-based configuration
- ✅ Session-scoped database fixtures
- ✅ Verify model structures before creating fixtures
- ✅ Comprehensive documentation
- ✅ Regular syntax checks
- ✅ Early and frequent testing

---

## Next Steps

1. ✅ Design approved
2. ⏳ Create database migration
3. ⏳ Implement Pydantic models
4. ⏳ Build repository layer
5. ⏳ Implement service layer
6. ⏳ Create API endpoints
7. ⏳ Build UI components
8. ⏳ Write comprehensive tests
9. ⏳ Document and commit

---

**Ready to begin implementation!** 🚀

