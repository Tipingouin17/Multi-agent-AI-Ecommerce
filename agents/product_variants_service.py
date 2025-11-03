"""
Product Variants Service - Multi-Agent E-commerce System

This service handles product variant management including:
- Creating and managing product variants (size, color, etc.)
- Variant-specific pricing
- Variant attributes
"""

from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel
import structlog
from shared.base_agent_v2 import BaseAgentV2
from typing import Any

logger = structlog.get_logger(__name__)


# ===========================
# PYDANTIC MODELS
# ===========================

class VariantAttribute(BaseModel):
    """Variant attribute definition (e.g., Size, Color)."""
    attribute_id: Optional[int] = None
    attribute_name: str
    attribute_type: str  # text, color, size, number
    display_order: int = 0
    is_required: bool = False
    is_visible: bool = True


class VariantAttributeValue(BaseModel):
    """Specific value for a variant attribute."""
    value_id: Optional[int] = None
    variant_id: UUID
    attribute_id: int
    attribute_value: str


class ProductVariant(BaseModel):
    """Product variant (e.g., Red T-Shirt Size M)."""
    variant_id: Optional[UUID] = None
    parent_product_id: str
    variant_sku: str
    variant_name: Optional[str] = None
    is_master: bool = False
    is_active: bool = True
    sort_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Related data
    attributes: Optional[List[VariantAttributeValue]] = []
    pricing: Optional['VariantPricing'] = None


class VariantPricing(BaseModel):
    """Variant-specific pricing."""
    pricing_id: Optional[int] = None
    variant_id: UUID
    price: Decimal
    compare_at_price: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    currency: str = "USD"
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    is_active: bool = True


class CreateVariantRequest(BaseModel):
    """Request to create a new product variant."""
    parent_product_id: str
    variant_sku: str
    variant_name: Optional[str] = None
    is_master: bool = False
    attributes: List[Dict[str, Any]]  # [{attribute_id: 1, value: "Red"}, ...]
    price: Decimal
    compare_at_price: Optional[Decimal] = None
    cost: Optional[Decimal] = None


# ===========================
# PRODUCT VARIANTS SERVICE
# ===========================

class ProductVariantsService(BaseAgentV2):
    """Service for managing product variants."""
    
    def __init__(self, agent_id: str = "productvariantsservice_001", db_manager=None):
        super().__init__(agent_id=agent_id)
        self.db_manager = db_manager
        self.logger = logger.bind(service="product_variants")
    
    async def create_variant_attribute(self, attribute: VariantAttribute) -> int:
        """Create a new variant attribute type (e.g., Size, Color)."""
        async with self.db_manager.get_async_session() as session:
            query = """
                INSERT INTO variant_attributes (
                    attribute_name, attribute_type, display_order,
                    is_required, is_visible
                ) VALUES ($1, $2, $3, $4, $5)
                RETURNING attribute_id
            """
            
            result = await session.execute(
                query,
                attribute.attribute_name,
                attribute.attribute_type,
                attribute.display_order,
                attribute.is_required,
                attribute.is_visible
            )
            
            attribute_id = result.fetchone()[0]
            await session.commit()
            
            self.logger.info("Created variant attribute", 
                           attribute_id=attribute_id,
                           name=attribute.attribute_name)
            
            return attribute_id
    
    async def create_variant(self, request: CreateVariantRequest) -> ProductVariant:
        """Create a new product variant with attributes and pricing."""
        variant_id = uuid4()
        
        async with self.db_manager.get_async_session() as session:
            try:
                # 1. Create the variant
                variant_query = """
                    INSERT INTO product_variants (
                        variant_id, parent_product_id, variant_sku,
                        variant_name, is_master, is_active, sort_order
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING variant_id, created_at, updated_at
                """
                
                variant_result = await session.execute(
                    variant_query,
                    str(variant_id),
                    request.parent_product_id,
                    request.variant_sku,
                    request.variant_name,
                    request.is_master,
                    True,
                    0
                )
                
                variant_data = variant_result.fetchone()
                
                # 2. Add variant attributes
                for attr in request.attributes:
                    attr_query = """
                        INSERT INTO variant_attribute_values (
                            variant_id, attribute_id, attribute_value
                        ) VALUES ($1, $2, $3)
                    """
                    
                    await session.execute(
                        attr_query,
                        str(variant_id),
                        attr["attribute_id"],
                        attr["value"]
                    )
                
                # 3. Add variant pricing
                pricing_query = """
                    INSERT INTO variant_pricing (
                        variant_id, price, compare_at_price, cost,
                        currency, is_active
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING pricing_id
                """
                
                await session.execute(
                    pricing_query,
                    str(variant_id),
                    float(request.price),
                    float(request.compare_at_price) if request.compare_at_price else None,
                    float(request.cost) if request.cost else None,
                    "USD",
                    True
                )
                
                await session.commit()
                
                self.logger.info("Created product variant",
                               variant_id=str(variant_id),
                               sku=request.variant_sku,
                               parent_id=request.parent_product_id)
                
                # Return the created variant
                return await self.get_variant(variant_id)
                
            except Exception as e:
                await session.rollback()
                self.logger.error("Failed to create variant",
                                error=str(e),
                                sku=request.variant_sku)
                raise
    
    async def get_variant(self, variant_id: UUID) -> Optional[ProductVariant]:
        """Get a product variant by ID with all related data."""
        async with self.db_manager.get_async_session() as session:
            query = """
                SELECT 
                    v.variant_id, v.parent_product_id, v.variant_sku,
                    v.variant_name, v.is_master, v.is_active, v.sort_order,
                    v.created_at, v.updated_at
                FROM product_variants v
                WHERE v.variant_id = $1
            """
            
            result = await session.execute(query, str(variant_id))
            row = result.fetchone()
            
            if not row:
                return None
            
            variant = ProductVariant(
                variant_id=UUID(row[0]),
                parent_product_id=row[1],
                variant_sku=row[2],
                variant_name=row[3],
                is_master=row[4],
                is_active=row[5],
                sort_order=row[6],
                created_at=row[7],
                updated_at=row[8]
            )
            
            # Get variant attributes
            attr_query = """
                SELECT vav.value_id, vav.variant_id, vav.attribute_id,
                       vav.attribute_value
                FROM variant_attribute_values vav
                WHERE vav.variant_id = $1
            """
            
            attr_result = await session.execute(attr_query, str(variant_id))
            variant.attributes = [
                VariantAttributeValue(
                    value_id=row[0],
                    variant_id=UUID(row[1]),
                    attribute_id=row[2],
                    attribute_value=row[3]
                )
                for row in attr_result.fetchall()
            ]
            
            # Get variant pricing
            pricing_query = """
                SELECT pricing_id, variant_id, price, compare_at_price,
                       cost, currency, valid_from, valid_to, is_active
                FROM variant_pricing
                WHERE variant_id = $1 AND is_active = true
                ORDER BY valid_from DESC
                LIMIT 1
            """
            
            pricing_result = await session.execute(pricing_query, str(variant_id))
            pricing_row = pricing_result.fetchone()
            
            if pricing_row:
                variant.pricing = VariantPricing(
                    pricing_id=pricing_row[0],
                    variant_id=UUID(pricing_row[1]),
                    price=Decimal(str(pricing_row[2])),
                    compare_at_price=Decimal(str(pricing_row[3])) if pricing_row[3] else None,
                    cost=Decimal(str(pricing_row[4])) if pricing_row[4] else None,
                    currency=pricing_row[5],
                    valid_from=pricing_row[6],
                    valid_to=pricing_row[7],
                    is_active=pricing_row[8]
                )
            
            return variant
    
    async def get_product_variants(self, product_id: str) -> List[ProductVariant]:
        """Get all variants for a product."""
        async with self.db_manager.get_async_session() as session:
            query = """
                SELECT variant_id
                FROM product_variants
                WHERE parent_product_id = $1 AND is_active = true
                ORDER BY sort_order, variant_name
            """
            
            result = await session.execute(query, product_id)
            variant_ids = [UUID(row[0]) for row in result.fetchall()]
            
            variants = []
            for variant_id in variant_ids:
                variant = await self.get_variant(variant_id)
                if variant:
                    variants.append(variant)
            
            return variants
    
    async def update_variant_price(
        self,
        variant_id: UUID,
        price: Decimal,
        compare_at_price: Optional[Decimal] = None
    ) -> bool:
        """Update variant pricing."""
        async with self.db_manager.get_async_session() as session:
            query = """
                UPDATE variant_pricing
                SET price = $1, compare_at_price = $2, updated_at = CURRENT_TIMESTAMP
                WHERE variant_id = $3 AND is_active = true
            """
            
            await session.execute(
                query,
                float(price),
                float(compare_at_price) if compare_at_price else None,
                str(variant_id)
            )
            
            await session.commit()
            
            self.logger.info("Updated variant price",
                           variant_id=str(variant_id),
                           price=float(price))
            
            return True
    
    async def delete_variant(self, variant_id: UUID) -> bool:
        """Soft delete a variant."""
        async with self.db_manager.get_async_session() as session:
            query = """
                UPDATE product_variants
                SET is_active = false, updated_at = CURRENT_TIMESTAMP
                WHERE variant_id = $1
            """
            
            await session.execute(query, str(variant_id))
            await session.commit()
            
            self.logger.info("Deleted variant", variant_id=str(variant_id))
            
            return True
    async def initialize(self):
        """Initialize the service."""
        await super().initialize()
        logger.info(f"{self.__class__.__name__} initialized successfully")
    
    async def cleanup(self):
        """Cleanup service resources."""
        try:
            await super().cleanup()
            logger.info(f"{self.__class__.__name__} cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process service business logic.
        
        Args:
            data: Dictionary containing operation type and parameters
            
        Returns:
            Dictionary with processing results
        """
        try:
            operation = data.get("operation", "process")
            logger.info(f"Processing {self.__class__.__name__} operation: {operation}")
            return {"status": "success", "operation": operation, "data": data}
        except Exception as e:
            logger.error(f"Error in process_business_logic: {e}")
            return {"status": "error", "message": str(e)}

