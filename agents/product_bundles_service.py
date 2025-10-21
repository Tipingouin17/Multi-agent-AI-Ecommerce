"""
Product Bundles Service - Multi-Agent E-commerce System

This service handles product bundles and kits including:
- Fixed bundles (predefined products)
- Flexible bundles (customer choice from options)
- Custom bundles (build your own)
- Bundle pricing rules (discounts, special pricing)
- Bundle inventory management
"""

from typing import Dict, List, Optional
from datetime import datetime
from uuid import UUID, uuid4
from decimal import Decimal
from pydantic import BaseModel
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


# ===========================
# ENUMS
# ===========================

class BundleType(str, Enum):
    """Type of product bundle."""
    FIXED = "fixed"  # Fixed set of products
    FLEXIBLE = "flexible"  # Customer chooses from options
    CUSTOM = "custom"  # Build your own bundle


class PricingRuleType(str, Enum):
    """Type of bundle pricing rule."""
    PERCENTAGE_DISCOUNT = "percentage_discount"
    FIXED_DISCOUNT = "fixed_discount"
    FIXED_PRICE = "fixed_price"
    BUY_X_GET_Y = "buy_x_get_y"


# ===========================
# PYDANTIC MODELS
# ===========================

class BundleComponent(BaseModel):
    """Component in a product bundle."""
    component_id: Optional[int] = None
    bundle_id: UUID
    product_id: str
    quantity: int
    is_optional: bool = False
    sort_order: int = 0
    
    # Related data
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    product_price: Optional[Decimal] = None


class BundlePricingRule(BaseModel):
    """Pricing rule for a bundle."""
    rule_id: Optional[int] = None
    bundle_id: UUID
    rule_type: PricingRuleType
    discount_value: Optional[Decimal] = None
    min_quantity: int = 1
    max_quantity: Optional[int] = None
    conditions: Optional[Dict] = None


class ProductBundle(BaseModel):
    """Product bundle definition."""
    bundle_id: Optional[UUID] = None
    bundle_name: str
    bundle_description: Optional[str] = None
    bundle_sku: str
    bundle_type: BundleType
    base_product_id: Optional[str] = None
    bundle_price: Optional[Decimal] = None
    discount_percentage: Optional[Decimal] = None
    is_active: bool = True
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    min_items: Optional[int] = None
    max_items: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Related data
    components: Optional[List[BundleComponent]] = []
    pricing_rules: Optional[List[BundlePricingRule]] = []
    total_value: Optional[Decimal] = None
    savings: Optional[Decimal] = None


class CreateBundleRequest(BaseModel):
    """Request to create a new bundle."""
    bundle_name: str
    bundle_description: Optional[str] = None
    bundle_sku: str
    bundle_type: BundleType
    base_product_id: Optional[str] = None
    bundle_price: Optional[Decimal] = None
    discount_percentage: Optional[Decimal] = None
    components: List[Dict]  # [{"product_id": "123", "quantity": 2, "is_optional": False}, ...]
    pricing_rules: Optional[List[Dict]] = []
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    min_items: Optional[int] = None
    max_items: Optional[int] = None


class UpdateBundleRequest(BaseModel):
    """Request to update a bundle."""
    bundle_name: Optional[str] = None
    bundle_description: Optional[str] = None
    bundle_price: Optional[Decimal] = None
    discount_percentage: Optional[Decimal] = None
    is_active: Optional[bool] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None


class BundlePriceCalculation(BaseModel):
    """Result of bundle price calculation."""
    bundle_id: UUID
    original_price: Decimal
    bundle_price: Decimal
    discount_amount: Decimal
    discount_percentage: Decimal
    components_breakdown: List[Dict]


# ===========================
# PRODUCT BUNDLES SERVICE
# ===========================

class ProductBundlesService:
    """Service for managing product bundles."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logger.bind(service="product_bundles")
    
    async def create_bundle(self, request: CreateBundleRequest) -> ProductBundle:
        """Create a new product bundle."""
        bundle_id = uuid4()
        
        async with self.db_manager.get_async_session() as session:
            try:
                # 1. Validate all product IDs exist
                for component in request.components:
                    product_query = """
                        SELECT id, name, sku, price
                        FROM products
                        WHERE id = $1
                    """
                    
                    result = await session.execute(product_query, component["product_id"])
                    if not result.fetchone():
                        raise ValueError(f"Product {component['product_id']} not found")
                
                # 2. Create bundle
                insert_query = """
                    INSERT INTO product_bundles (
                        bundle_id, bundle_name, bundle_description, bundle_sku,
                        bundle_type, base_product_id, bundle_price, discount_percentage,
                        is_active, valid_from, valid_to, min_items, max_items,
                        created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                    RETURNING created_at, updated_at
                """
                
                result = await session.execute(
                    insert_query,
                    str(bundle_id),
                    request.bundle_name,
                    request.bundle_description,
                    request.bundle_sku,
                    request.bundle_type.value,
                    request.base_product_id,
                    float(request.bundle_price) if request.bundle_price else None,
                    float(request.discount_percentage) if request.discount_percentage else None,
                    True,
                    request.valid_from,
                    request.valid_to,
                    request.min_items,
                    request.max_items,
                    datetime.utcnow(),
                    datetime.utcnow()
                )
                
                row = result.fetchone()
                
                # 3. Add components
                components = []
                for i, comp_data in enumerate(request.components):
                    comp_query = """
                        INSERT INTO bundle_components (
                            bundle_id, product_id, quantity, is_optional, sort_order
                        ) VALUES ($1, $2, $3, $4, $5)
                        RETURNING component_id
                    """
                    
                    comp_result = await session.execute(
                        comp_query,
                        str(bundle_id),
                        comp_data["product_id"],
                        comp_data["quantity"],
                        comp_data.get("is_optional", False),
                        i
                    )
                    
                    component_id = comp_result.fetchone()[0]
                    
                    # Get product details
                    product_query = """
                        SELECT name, sku, price
                        FROM products
                        WHERE id = $1
                    """
                    
                    prod_result = await session.execute(product_query, comp_data["product_id"])
                    prod_row = prod_result.fetchone()
                    
                    components.append(BundleComponent(
                        component_id=component_id,
                        bundle_id=bundle_id,
                        product_id=comp_data["product_id"],
                        quantity=comp_data["quantity"],
                        is_optional=comp_data.get("is_optional", False),
                        sort_order=i,
                        product_name=prod_row[0],
                        product_sku=prod_row[1],
                        product_price=Decimal(str(prod_row[2]))
                    ))
                
                # 4. Add pricing rules
                pricing_rules = []
                for rule_data in (request.pricing_rules or []):
                    rule_query = """
                        INSERT INTO bundle_pricing_rules (
                            bundle_id, rule_type, discount_value, min_quantity,
                            max_quantity, conditions
                        ) VALUES ($1, $2, $3, $4, $5, $6)
                        RETURNING rule_id
                    """
                    
                    rule_result = await session.execute(
                        rule_query,
                        str(bundle_id),
                        rule_data["rule_type"],
                        float(rule_data.get("discount_value", 0)),
                        rule_data.get("min_quantity", 1),
                        rule_data.get("max_quantity"),
                        rule_data.get("conditions")
                    )
                    
                    rule_id = rule_result.fetchone()[0]
                    
                    pricing_rules.append(BundlePricingRule(
                        rule_id=rule_id,
                        bundle_id=bundle_id,
                        rule_type=PricingRuleType(rule_data["rule_type"]),
                        discount_value=Decimal(str(rule_data.get("discount_value", 0))),
                        min_quantity=rule_data.get("min_quantity", 1),
                        max_quantity=rule_data.get("max_quantity"),
                        conditions=rule_data.get("conditions")
                    ))
                
                await session.commit()
                
                self.logger.info("Created product bundle",
                               bundle_id=str(bundle_id),
                               bundle_name=request.bundle_name,
                               components=len(components))
                
                return ProductBundle(
                    bundle_id=bundle_id,
                    bundle_name=request.bundle_name,
                    bundle_description=request.bundle_description,
                    bundle_sku=request.bundle_sku,
                    bundle_type=request.bundle_type,
                    base_product_id=request.base_product_id,
                    bundle_price=request.bundle_price,
                    discount_percentage=request.discount_percentage,
                    is_active=True,
                    valid_from=request.valid_from,
                    valid_to=request.valid_to,
                    min_items=request.min_items,
                    max_items=request.max_items,
                    created_at=row[0],
                    updated_at=row[1],
                    components=components,
                    pricing_rules=pricing_rules
                )
                
            except Exception as e:
                await session.rollback()
                self.logger.error("Failed to create bundle",
                                error=str(e),
                                bundle_name=request.bundle_name)
                raise
    
    async def get_bundle(self, bundle_id: UUID) -> Optional[ProductBundle]:
        """Get a bundle by ID."""
        async with self.db_manager.get_async_session() as session:
            query = """
                SELECT 
                    bundle_id, bundle_name, bundle_description, bundle_sku,
                    bundle_type, base_product_id, bundle_price, discount_percentage,
                    is_active, valid_from, valid_to, min_items, max_items,
                    created_at, updated_at
                FROM product_bundles
                WHERE bundle_id = $1
            """
            
            result = await session.execute(query, str(bundle_id))
            row = result.fetchone()
            
            if not row:
                return None
            
            bundle = ProductBundle(
                bundle_id=UUID(row[0]),
                bundle_name=row[1],
                bundle_description=row[2],
                bundle_sku=row[3],
                bundle_type=BundleType(row[4]),
                base_product_id=row[5],
                bundle_price=Decimal(str(row[6])) if row[6] else None,
                discount_percentage=Decimal(str(row[7])) if row[7] else None,
                is_active=row[8],
                valid_from=row[9],
                valid_to=row[10],
                min_items=row[11],
                max_items=row[12],
                created_at=row[13],
                updated_at=row[14]
            )
            
            # Get components
            comp_query = """
                SELECT 
                    bc.component_id, bc.bundle_id, bc.product_id, bc.quantity,
                    bc.is_optional, bc.sort_order, p.name, p.sku, p.price
                FROM bundle_components bc
                JOIN products p ON bc.product_id = p.id
                WHERE bc.bundle_id = $1
                ORDER BY bc.sort_order
            """
            
            comp_result = await session.execute(comp_query, str(bundle_id))
            bundle.components = [
                BundleComponent(
                    component_id=row[0],
                    bundle_id=UUID(row[1]),
                    product_id=row[2],
                    quantity=row[3],
                    is_optional=row[4],
                    sort_order=row[5],
                    product_name=row[6],
                    product_sku=row[7],
                    product_price=Decimal(str(row[8]))
                )
                for row in comp_result.fetchall()
            ]
            
            # Get pricing rules
            rule_query = """
                SELECT 
                    rule_id, bundle_id, rule_type, discount_value,
                    min_quantity, max_quantity, conditions
                FROM bundle_pricing_rules
                WHERE bundle_id = $1
            """
            
            rule_result = await session.execute(rule_query, str(bundle_id))
            bundle.pricing_rules = [
                BundlePricingRule(
                    rule_id=row[0],
                    bundle_id=UUID(row[1]),
                    rule_type=PricingRuleType(row[2]),
                    discount_value=Decimal(str(row[3])) if row[3] else None,
                    min_quantity=row[4],
                    max_quantity=row[5],
                    conditions=row[6]
                )
                for row in rule_result.fetchall()
            ]
            
            # Calculate total value and savings
            total_value = sum(
                comp.product_price * comp.quantity
                for comp in bundle.components
                if not comp.is_optional
            )
            
            bundle.total_value = total_value
            
            if bundle.bundle_price:
                bundle.savings = total_value - bundle.bundle_price
            elif bundle.discount_percentage:
                bundle.savings = total_value * (bundle.discount_percentage / Decimal('100'))
            
            return bundle
    
    async def calculate_bundle_price(
        self,
        bundle_id: UUID,
        selected_components: Optional[List[str]] = None,
        quantity: int = 1
    ) -> BundlePriceCalculation:
        """Calculate the price for a bundle with optional component selection."""
        bundle = await self.get_bundle(bundle_id)
        
        if not bundle:
            raise ValueError(f"Bundle {bundle_id} not found")
        
        # Calculate original price
        original_price = Decimal('0')
        components_breakdown = []
        
        for component in bundle.components:
            if component.is_optional and selected_components:
                if component.product_id not in selected_components:
                    continue
            
            component_total = component.product_price * component.quantity * quantity
            original_price += component_total
            
            components_breakdown.append({
                "product_id": component.product_id,
                "product_name": component.product_name,
                "quantity": component.quantity * quantity,
                "unit_price": float(component.product_price),
                "total": float(component_total)
            })
        
        # Apply bundle pricing
        if bundle.bundle_price:
            bundle_price = bundle.bundle_price * quantity
        elif bundle.discount_percentage:
            bundle_price = original_price * (Decimal('1') - bundle.discount_percentage / Decimal('100'))
        else:
            bundle_price = original_price
        
        discount_amount = original_price - bundle_price
        discount_percentage = (discount_amount / original_price * Decimal('100')) if original_price > 0 else Decimal('0')
        
        return BundlePriceCalculation(
            bundle_id=bundle_id,
            original_price=original_price,
            bundle_price=bundle_price,
            discount_amount=discount_amount,
            discount_percentage=discount_percentage,
            components_breakdown=components_breakdown
        )
    
    async def list_active_bundles(self) -> List[ProductBundle]:
        """List all active bundles."""
        async with self.db_manager.get_async_session() as session:
            query = """
                SELECT bundle_id
                FROM product_bundles
                WHERE is_active = true
                  AND (valid_from IS NULL OR valid_from <= CURRENT_TIMESTAMP)
                  AND (valid_to IS NULL OR valid_to >= CURRENT_TIMESTAMP)
                ORDER BY created_at DESC
            """
            
            result = await session.execute(query)
            bundle_ids = [UUID(row[0]) for row in result.fetchall()]
            
            bundles = []
            for bid in bundle_ids:
                bundle = await self.get_bundle(bid)
                if bundle:
                    bundles.append(bundle)
            
            return bundles
    
    async def update_bundle(
        self,
        bundle_id: UUID,
        request: UpdateBundleRequest
    ) -> Optional[ProductBundle]:
        """Update a bundle."""
        async with self.db_manager.get_async_session() as session:
            try:
                updates = []
                params = []
                param_num = 1
                
                if request.bundle_name is not None:
                    updates.append(f"bundle_name = ${param_num}")
                    params.append(request.bundle_name)
                    param_num += 1
                
                if request.bundle_description is not None:
                    updates.append(f"bundle_description = ${param_num}")
                    params.append(request.bundle_description)
                    param_num += 1
                
                if request.bundle_price is not None:
                    updates.append(f"bundle_price = ${param_num}")
                    params.append(float(request.bundle_price))
                    param_num += 1
                
                if request.discount_percentage is not None:
                    updates.append(f"discount_percentage = ${param_num}")
                    params.append(float(request.discount_percentage))
                    param_num += 1
                
                if request.is_active is not None:
                    updates.append(f"is_active = ${param_num}")
                    params.append(request.is_active)
                    param_num += 1
                
                if request.valid_from is not None:
                    updates.append(f"valid_from = ${param_num}")
                    params.append(request.valid_from)
                    param_num += 1
                
                if request.valid_to is not None:
                    updates.append(f"valid_to = ${param_num}")
                    params.append(request.valid_to)
                    param_num += 1
                
                if not updates:
                    return await self.get_bundle(bundle_id)
                
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(str(bundle_id))
                
                query = f"""
                    UPDATE product_bundles
                    SET {', '.join(updates)}
                    WHERE bundle_id = ${param_num}
                """
                
                await session.execute(query, *params)
                await session.commit()
                
                self.logger.info("Updated bundle",
                               bundle_id=str(bundle_id))
                
                return await self.get_bundle(bundle_id)
                
            except Exception as e:
                await session.rollback()
                self.logger.error("Failed to update bundle",
                                error=str(e),
                                bundle_id=str(bundle_id))
                raise

