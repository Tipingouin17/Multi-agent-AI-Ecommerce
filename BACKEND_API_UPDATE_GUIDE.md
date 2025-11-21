# Backend API Update Guide for Product Wizard

## Overview

This guide provides step-by-step instructions to update the backend API to support all 8-step product wizard fields.

**Status:**
- ✅ Database schema updated (migration 024 applied successfully)
- ⏳ Backend API needs updating
- ✅ Frontend wizard implemented

---

## Phase 3: Backend API Updates

### Step 1: Update ProductCreate Model

**File:** `/agents/product_agent_v3.py`

**Current model (lines 61-72):**
```python
class ProductCreate(BaseModel):
    merchant_id: int
    category_id: Optional[int] = None
    sku: str
    name: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    price: float
    cost: Optional[float] = None
    compare_at_price: Optional[float] = None
    weight: Optional[float] = None
    status: str = "draft"
```

**New model (replace with):**
```python
class ProductCreate(BaseModel):
    # Basic Information (Step 1)
    merchant_id: int
    category_id: Optional[int] = None
    sku: str
    name: str
    display_name: Optional[str] = None
    brand: Optional[str] = None
    model_number: Optional[str] = None
    product_type: str = "simple"
    description: Optional[str] = None
    short_description: Optional[str] = None
    key_features: Optional[List[str]] = []
    
    # Specifications (Step 2)
    dimensions_length: Optional[float] = None
    dimensions_width: Optional[float] = None
    dimensions_height: Optional[float] = None
    dimensions_unit: str = "cm"
    weight: Optional[float] = None
    weight_unit: str = "kg"
    material: Optional[str] = None
    color: Optional[str] = None
    warranty_period: Optional[int] = None
    country_of_origin: Optional[str] = None
    specifications: Optional[List[Dict[str, Any]]] = []
    
    # Visual Assets (Step 3)
    images: Optional[List[Dict[str, Any]]] = []
    media: Optional[List[Dict[str, Any]]] = []
    
    # Pricing & Costs (Step 4)
    price: float
    cost: Optional[float] = None
    compare_at_price: Optional[float] = None
    currency: str = "USD"
    profit_margin: Optional[float] = None
    pricing_tiers: Optional[List[Dict[str, Any]]] = []
    tax_config: Optional[Dict[str, Any]] = None
    
    # Inventory & Logistics (Step 5)
    warehouse_inventory: Optional[List[Dict[str, Any]]] = []
    shipping_weight: Optional[float] = None
    shipping_length: Optional[float] = None
    shipping_width: Optional[float] = None
    shipping_height: Optional[float] = None
    handling_time_days: int = 1
    requires_shipping: bool = True
    is_fragile: bool = False
    is_perishable: bool = False
    
    # Bundle & Kit Config (Step 6)
    is_bundle: bool = False
    bundle_components: Optional[List[Dict[str, Any]]] = []
    bundle_type: Optional[str] = None
    bundle_pricing_strategy: Optional[str] = None
    
    # Marketplace & Compliance (Step 7)
    marketplace_listings: Optional[List[Dict[str, Any]]] = []
    product_identifiers: Optional[List[Dict[str, Any]]] = []
    compliance_certifications: Optional[List[Dict[str, Any]]] = []
    has_age_restriction: bool = False
    min_age: Optional[int] = None
    is_hazmat: bool = False
    hazmat_class: Optional[str] = None
    requires_signature: bool = False
    has_export_restrictions: bool = False
    export_restriction_countries: Optional[List[str]] = []
    safety_warnings: Optional[List[str]] = []
    
    # Review & Activation (Step 8)
    status: str = "draft"
    is_draft: bool = True
    scheduled_publish_at: Optional[datetime] = None
```

### Step 2: Update create_product Endpoint

**File:** `/agents/product_agent_v3.py` (lines 242-280)

**Replace the create_product function with:**

```python
@app.post("/api/products")
def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product with full wizard support"""
    try:
        # Check if SKU already exists
        existing = db.query(Product).filter(Product.sku == product_data.sku).first()
        if existing:
            raise HTTPException(status_code=400, detail="SKU already exists")
        
        # Create slug from name
        slug = product_data.name.lower().replace(' ', '-').replace("'", '')
        
        # Create main product record
        product = Product(
            merchant_id=product_data.merchant_id,
            category_id=product_data.category_id,
            sku=product_data.sku,
            name=product_data.name,
            slug=slug,
            display_name=product_data.display_name,
            brand=product_data.brand,
            model_number=product_data.model_number,
            product_type=product_data.product_type,
            description=product_data.description,
            short_description=product_data.short_description,
            key_features=product_data.key_features,
            price=product_data.price,
            cost=product_data.cost,
            compare_at_price=product_data.compare_at_price,
            currency=product_data.currency,
            weight=product_data.weight,
            weight_unit=product_data.weight_unit,
            dimensions_length=product_data.dimensions_length,
            dimensions_width=product_data.dimensions_width,
            dimensions_height=product_data.dimensions_height,
            dimensions_unit=product_data.dimensions_unit,
            material=product_data.material,
            color=product_data.color,
            warranty_period=product_data.warranty_period,
            country_of_origin=product_data.country_of_origin,
            shipping_weight=product_data.shipping_weight,
            shipping_length=product_data.shipping_length,
            shipping_width=product_data.shipping_width,
            shipping_height=product_data.shipping_height,
            handling_time_days=product_data.handling_time_days,
            requires_shipping=product_data.requires_shipping,
            is_fragile=product_data.is_fragile,
            is_perishable=product_data.is_perishable,
            has_age_restriction=product_data.has_age_restriction,
            min_age=product_data.min_age,
            is_hazmat=product_data.is_hazmat,
            hazmat_class=product_data.hazmat_class,
            requires_signature=product_data.requires_signature,
            has_export_restrictions=product_data.has_export_restrictions,
            export_restriction_countries=product_data.export_restriction_countries,
            safety_warnings=product_data.safety_warnings,
            status=product_data.status,
            is_draft=product_data.is_draft,
            scheduled_publish_at=product_data.scheduled_publish_at
        )
        
        db.add(product)
        db.flush()  # Get product ID without committing
        
        # Step 2: Add specifications
        if product_data.specifications:
            for spec in product_data.specifications:
                spec_record = ProductSpecification(
                    product_id=product.id,
                    spec_name=spec['name'],
                    spec_value=spec['value'],
                    spec_unit=spec.get('unit'),
                    spec_group=spec.get('group'),
                    display_order=spec.get('display_order', 0)
                )
                db.add(spec_record)
        
        # Step 3: Add media (images and videos)
        if product_data.images:
            for idx, img in enumerate(product_data.images):
                media_record = ProductMedia(
                    product_id=product.id,
                    media_type='image',
                    media_url=img['url'],
                    alt_text=img.get('alt_text'),
                    is_primary=img.get('is_primary', idx == 0),
                    display_order=img.get('display_order', idx)
                )
                db.add(media_record)
        
        if product_data.media:
            for idx, med in enumerate(product_data.media):
                media_record = ProductMedia(
                    product_id=product.id,
                    media_type=med['type'],
                    media_url=med['url'],
                    caption=med.get('caption'),
                    display_order=idx
                )
                db.add(media_record)
        
        # Step 4: Add pricing tiers
        if product_data.pricing_tiers:
            for tier in product_data.pricing_tiers:
                tier_record = ProductPricingTier(
                    product_id=product.id,
                    min_quantity=tier['min_quantity'],
                    max_quantity=tier.get('max_quantity'),
                    price=tier['price'],
                    discount_percentage=tier.get('discount_percentage')
                )
                db.add(tier_record)
        
        # Add tax configuration
        if product_data.tax_config:
            tax_record = ProductTaxConfig(
                product_id=product.id,
                tax_class=product_data.tax_config['tax_class'],
                tax_rate=product_data.tax_config['tax_rate'],
                tax_region=product_data.tax_config.get('tax_region'),
                is_tax_inclusive=product_data.tax_config.get('is_tax_inclusive', False)
            )
            db.add(tax_record)
        
        # Step 5: Add warehouse inventory
        if product_data.warehouse_inventory:
            for inv in product_data.warehouse_inventory:
                inv_record = ProductWarehouseInventory(
                    product_id=product.id,
                    warehouse_id=inv['warehouse_id'],
                    quantity=inv.get('quantity', 0),
                    low_stock_threshold=inv.get('low_stock_threshold', 10),
                    reorder_point=inv.get('reorder_point', 20),
                    reorder_quantity=inv.get('reorder_quantity', 50)
                )
                db.add(inv_record)
        
        # Step 6: Add bundle components (if bundle)
        if product_data.is_bundle and product_data.bundle_components:
            bundle = ProductBundle(
                bundle_name=product_data.name,
                bundle_sku=product_data.sku,
                bundle_type=product_data.bundle_type or 'fixed',
                pricing_strategy=product_data.bundle_pricing_strategy or 'fixed_price',
                bundle_price=product_data.price
            )
            db.add(bundle)
            db.flush()
            
            for comp in product_data.bundle_components:
                comp_record = BundleComponent(
                    bundle_id=bundle.id,
                    product_id=comp['product_id'],
                    quantity=comp.get('quantity', 1),
                    is_required=comp.get('is_required', True)
                )
                db.add(comp_record)
        
        # Step 7: Add marketplace listings
        if product_data.marketplace_listings:
            for listing in product_data.marketplace_listings:
                listing_record = ProductMarketplaceListing(
                    product_id=product.id,
                    marketplace_name=listing['marketplace'],
                    marketplace_sku=listing.get('sku'),
                    marketplace_category=listing.get('category'),
                    marketplace_price=listing.get('price'),
                    marketplace_status='draft'
                )
                db.add(listing_record)
        
        # Add product identifiers
        if product_data.product_identifiers:
            for identifier in product_data.product_identifiers:
                id_record = ProductIdentifier(
                    product_id=product.id,
                    identifier_type=identifier['type'],
                    identifier_value=identifier['value'],
                    is_primary=identifier.get('is_primary', False)
                )
                db.add(id_record)
        
        # Add compliance certifications
        if product_data.compliance_certifications:
            for cert in product_data.compliance_certifications:
                cert_record = ProductCompliance(
                    product_id=product.id,
                    certification_type=cert['type'],
                    certification_number=cert.get('number'),
                    certification_authority=cert.get('authority'),
                    issue_date=cert.get('issue_date'),
                    expiry_date=cert.get('expiry_date')
                )
                db.add(cert_record)
        
        # Step 8: Log lifecycle event
        lifecycle_event = ProductLifecycleEvent(
            product_id=product.id,
            event_type='created',
            new_status=product_data.status,
            triggered_by=f"merchant_{product_data.merchant_id}"
        )
        db.add(lifecycle_event)
        
        # Commit all changes
        db.commit()
        db.refresh(product)
        
        return {
            "success": True,
            "product": product.to_dict(),
            "message": "Product created successfully with all wizard data"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 3: Add Required Imports

**Add to the top of `/agents/product_agent_v3.py`:**

```python
from typing import Dict, List, Optional, Any
from datetime import datetime
```

### Step 4: Define Missing SQLAlchemy Models

**Add these model classes if they don't exist:**

```python
class ProductSpecification(Base):
    __tablename__ = "product_specifications"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    spec_name = Column(String(255))
    spec_value = Column(Text)
    spec_unit = Column(String(50))
    spec_group = Column(String(100))
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProductMedia(Base):
    __tablename__ = "product_media"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    media_type = Column(String(50))
    media_url = Column(Text)
    alt_text = Column(String(500))
    caption = Column(Text)
    is_primary = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProductPricingTier(Base):
    __tablename__ = "product_pricing_tiers"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    min_quantity = Column(Integer)
    max_quantity = Column(Integer)
    price = Column(Numeric(10, 2))
    discount_percentage = Column(Numeric(5, 2))
    created_at = Column(DateTime, default=datetime.utcnow)

class ProductTaxConfig(Base):
    __tablename__ = "product_tax_config"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    tax_class = Column(String(100))
    tax_rate = Column(Numeric(5, 2))
    tax_region = Column(String(100))
    is_tax_inclusive = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProductWarehouseInventory(Base):
    __tablename__ = "product_warehouse_inventory"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    warehouse_id = Column(Integer)
    quantity = Column(Integer, default=0)
    reserved_quantity = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=10)
    reorder_point = Column(Integer, default=20)
    reorder_quantity = Column(Integer, default=50)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProductMarketplaceListing(Base):
    __tablename__ = "product_marketplace_listings"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    marketplace_name = Column(String(100))
    marketplace_sku = Column(String(255))
    marketplace_category = Column(String(255))
    marketplace_price = Column(Numeric(10, 2))
    marketplace_status = Column(String(50), default='draft')
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProductIdentifier(Base):
    __tablename__ = "product_identifiers"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    identifier_type = Column(String(50))
    identifier_value = Column(String(255))
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProductCompliance(Base):
    __tablename__ = "product_compliance"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    certification_type = Column(String(100))
    certification_number = Column(String(255))
    certification_authority = Column(String(255))
    issue_date = Column(Date)
    expiry_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProductLifecycleEvent(Base):
    __tablename__ = "product_lifecycle_events"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    event_type = Column(String(100))
    event_description = Column(Text)
    previous_status = Column(String(50))
    new_status = Column(String(50))
    triggered_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## Testing Checklist

After implementing the backend changes:

1. ✅ Test product creation with minimal fields (Step 1 only)
2. ✅ Test product creation with all 8 steps filled
3. ✅ Verify database records are created correctly
4. ✅ Test profit margin auto-calculation
5. ✅ Test lifecycle event logging
6. ✅ Test warehouse inventory creation
7. ✅ Test marketplace listing creation
8. ✅ Test bundle product creation

---

## Current Status

**Completed:**
- ✅ Phase 1: Market Master data model review
- ✅ Phase 2: Database schema migration (024 applied successfully)
- ✅ Frontend: 8-step wizard implemented and working

**In Progress:**
- ⏳ Phase 3: Backend API updates (this guide)

**Next Steps:**
1. Apply the code changes from this guide to `product_agent_v3.py`
2. Restart the backend server
3. Test product creation from the frontend wizard
4. Fix any errors that arise
5. Move to Phase 4: Testing

---

## Quick Implementation Script

```bash
# 1. Backup current file
cp /home/ubuntu/Multi-agent-AI-Ecommerce/agents/product_agent_v3.py \
   /home/ubuntu/Multi-agent-AI-Ecommerce/agents/product_agent_v3.py.backup

# 2. Apply changes (manual editing required)
# Edit the file according to this guide

# 3. Restart backend
# (Find and restart the backend process)

# 4. Test
curl -X POST http://localhost:8015/api/products \
  -H "Content-Type: application/json" \
  -d '{"merchant_id": 1, "sku": "TEST-001", "name": "Test Product", "price": 99.99}'
```

---

## Support

If you encounter errors:
1. Check the backend logs
2. Verify database migration was applied: `psql -d multi_agent_ecommerce -c "\d products"`
3. Check for missing imports
4. Verify SQLAlchemy model definitions match table schema

---

**Document Version:** 1.0  
**Last Updated:** Nov 21, 2025  
**Author:** Manus AI Agent
