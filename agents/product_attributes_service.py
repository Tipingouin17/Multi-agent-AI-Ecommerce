"""
Product Attributes Service - Multi-Agent E-commerce System

This service handles product attributes for advanced filtering and search:
- Dynamic attribute definitions
- Product attribute values
- Attribute-based filtering
- Faceted search support
- Attribute groups and categories
"""

from typing import Dict, List, Optional, Any
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

class AttributeType(str, Enum):
    """Type of product attribute."""
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    SELECT = "select"  # Single choice
    MULTISELECT = "multiselect"  # Multiple choices
    DATE = "date"
    COLOR = "color"
    DIMENSION = "dimension"


class AttributeScope(str, Enum):
    """Scope where attribute can be used."""
    GLOBAL = "global"  # All products
    CATEGORY = "category"  # Specific categories
    PRODUCT_TYPE = "product_type"  # Specific product types


# ===========================
# PYDANTIC MODELS
# ===========================

class AttributeOption(BaseModel):
    """Option for select/multiselect attributes."""
    option_id: Optional[int] = None
    attribute_id: UUID
    option_value: str
    option_label: str
    sort_order: int = 0
    is_active: bool = True


class ProductAttribute(BaseModel):
    """Product attribute definition."""
    attribute_id: Optional[UUID] = None
    attribute_code: str  # Unique code for API/filtering
    attribute_name: str
    attribute_type: AttributeType
    attribute_scope: AttributeScope = AttributeScope.GLOBAL
    is_required: bool = False
    is_filterable: bool = True
    is_searchable: bool = False
    is_comparable: bool = False
    is_visible: bool = True
    sort_order: int = 0
    validation_rules: Optional[Dict] = None
    default_value: Optional[str] = None
    unit: Optional[str] = None  # e.g., "cm", "kg", "GB"
    group_name: Optional[str] = None
    help_text: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Related data
    options: Optional[List[AttributeOption]] = []


class ProductAttributeValue(BaseModel):
    """Value of an attribute for a specific product."""
    value_id: Optional[int] = None
    product_id: str
    attribute_id: UUID
    value: Optional[str] = None
    numeric_value: Optional[Decimal] = None
    boolean_value: Optional[bool] = None
    date_value: Optional[datetime] = None
    
    # Related data
    attribute_code: Optional[str] = None
    attribute_name: Optional[str] = None
    attribute_type: Optional[AttributeType] = None


class CreateAttributeRequest(BaseModel):
    """Request to create a new attribute."""
    attribute_code: str
    attribute_name: str
    attribute_type: AttributeType
    attribute_scope: AttributeScope = AttributeScope.GLOBAL
    is_required: bool = False
    is_filterable: bool = True
    is_searchable: bool = False
    is_comparable: bool = False
    is_visible: bool = True
    sort_order: int = 0
    validation_rules: Optional[Dict] = None
    default_value: Optional[str] = None
    unit: Optional[str] = None
    group_name: Optional[str] = None
    help_text: Optional[str] = None
    options: Optional[List[Dict]] = []  # For select/multiselect types


class SetAttributeValueRequest(BaseModel):
    """Request to set an attribute value for a product."""
    product_id: str
    attribute_code: str
    value: Optional[str] = None
    numeric_value: Optional[Decimal] = None
    boolean_value: Optional[bool] = None
    date_value: Optional[datetime] = None


class AttributeFilter(BaseModel):
    """Filter criteria for product search."""
    attribute_code: str
    operator: str  # eq, ne, gt, lt, gte, lte, in, contains
    value: Any


# ===========================
# PRODUCT ATTRIBUTES SERVICE
# ===========================

class ProductAttributesService:
    """Service for managing product attributes."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logger.bind(service="product_attributes")
    
    async def create_attribute(self, request: CreateAttributeRequest) -> ProductAttribute:
        """Create a new product attribute."""
        attribute_id = uuid4()
        
        async with self.db_manager.get_async_session() as session:
            try:
                # 1. Create attribute
                insert_query = """
                    INSERT INTO product_attributes (
                        attribute_id, attribute_code, attribute_name, attribute_type,
                        attribute_scope, is_required, is_filterable, is_searchable,
                        is_comparable, is_visible, sort_order, validation_rules,
                        default_value, unit, group_name, help_text,
                        created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                    RETURNING created_at, updated_at
                """
                
                result = await session.execute(
                    insert_query,
                    str(attribute_id),
                    request.attribute_code,
                    request.attribute_name,
                    request.attribute_type.value,
                    request.attribute_scope.value,
                    request.is_required,
                    request.is_filterable,
                    request.is_searchable,
                    request.is_comparable,
                    request.is_visible,
                    request.sort_order,
                    request.validation_rules,
                    request.default_value,
                    request.unit,
                    request.group_name,
                    request.help_text,
                    datetime.utcnow(),
                    datetime.utcnow()
                )
                
                row = result.fetchone()
                
                # 2. Add options for select/multiselect types
                options = []
                if request.attribute_type in [AttributeType.SELECT, AttributeType.MULTISELECT]:
                    for i, opt_data in enumerate(request.options or []):
                        opt_query = """
                            INSERT INTO attribute_options (
                                attribute_id, option_value, option_label, sort_order, is_active
                            ) VALUES ($1, $2, $3, $4, $5)
                            RETURNING option_id
                        """
                        
                        opt_result = await session.execute(
                            opt_query,
                            str(attribute_id),
                            opt_data["option_value"],
                            opt_data["option_label"],
                            i,
                            True
                        )
                        
                        option_id = opt_result.fetchone()[0]
                        
                        options.append(AttributeOption(
                            option_id=option_id,
                            attribute_id=attribute_id,
                            option_value=opt_data["option_value"],
                            option_label=opt_data["option_label"],
                            sort_order=i,
                            is_active=True
                        ))
                
                await session.commit()
                
                self.logger.info("Created product attribute",
                               attribute_id=str(attribute_id),
                               attribute_code=request.attribute_code)
                
                return ProductAttribute(
                    attribute_id=attribute_id,
                    attribute_code=request.attribute_code,
                    attribute_name=request.attribute_name,
                    attribute_type=request.attribute_type,
                    attribute_scope=request.attribute_scope,
                    is_required=request.is_required,
                    is_filterable=request.is_filterable,
                    is_searchable=request.is_searchable,
                    is_comparable=request.is_comparable,
                    is_visible=request.is_visible,
                    sort_order=request.sort_order,
                    validation_rules=request.validation_rules,
                    default_value=request.default_value,
                    unit=request.unit,
                    group_name=request.group_name,
                    help_text=request.help_text,
                    created_at=row[0],
                    updated_at=row[1],
                    options=options
                )
                
            except Exception as e:
                await session.rollback()
                self.logger.error("Failed to create attribute",
                                error=str(e),
                                attribute_code=request.attribute_code)
                raise
    
    async def get_attribute(self, attribute_id: UUID) -> Optional[ProductAttribute]:
        """Get an attribute by ID."""
        async with self.db_manager.get_async_session() as session:
            query = """
                SELECT 
                    attribute_id, attribute_code, attribute_name, attribute_type,
                    attribute_scope, is_required, is_filterable, is_searchable,
                    is_comparable, is_visible, sort_order, validation_rules,
                    default_value, unit, group_name, help_text,
                    created_at, updated_at
                FROM product_attributes
                WHERE attribute_id = $1
            """
            
            result = await session.execute(query, str(attribute_id))
            row = result.fetchone()
            
            if not row:
                return None
            
            attribute = ProductAttribute(
                attribute_id=UUID(row[0]),
                attribute_code=row[1],
                attribute_name=row[2],
                attribute_type=AttributeType(row[3]),
                attribute_scope=AttributeScope(row[4]),
                is_required=row[5],
                is_filterable=row[6],
                is_searchable=row[7],
                is_comparable=row[8],
                is_visible=row[9],
                sort_order=row[10],
                validation_rules=row[11],
                default_value=row[12],
                unit=row[13],
                group_name=row[14],
                help_text=row[15],
                created_at=row[16],
                updated_at=row[17]
            )
            
            # Get options
            opt_query = """
                SELECT option_id, attribute_id, option_value, option_label, sort_order, is_active
                FROM attribute_options
                WHERE attribute_id = $1 AND is_active = true
                ORDER BY sort_order
            """
            
            opt_result = await session.execute(opt_query, str(attribute_id))
            attribute.options = [
                AttributeOption(
                    option_id=row[0],
                    attribute_id=UUID(row[1]),
                    option_value=row[2],
                    option_label=row[3],
                    sort_order=row[4],
                    is_active=row[5]
                )
                for row in opt_result.fetchall()
            ]
            
            return attribute
    
    async def get_attribute_by_code(self, attribute_code: str) -> Optional[ProductAttribute]:
        """Get an attribute by code."""
        async with self.db_manager.get_async_session() as session:
            query = """
                SELECT attribute_id
                FROM product_attributes
                WHERE attribute_code = $1
            """
            
            result = await session.execute(query, attribute_code)
            row = result.fetchone()
            
            if not row:
                return None
            
            return await self.get_attribute(UUID(row[0]))
    
    async def set_product_attribute_value(
        self,
        request: SetAttributeValueRequest
    ) -> ProductAttributeValue:
        """Set an attribute value for a product."""
        async with self.db_manager.get_async_session() as session:
            try:
                # 1. Get attribute
                attribute = await self.get_attribute_by_code(request.attribute_code)
                
                if not attribute:
                    raise ValueError(f"Attribute '{request.attribute_code}' not found")
                
                # 2. Validate product exists
                prod_query = """
                    SELECT id FROM products WHERE id = $1
                """
                
                prod_result = await session.execute(prod_query, request.product_id)
                if not prod_result.fetchone():
                    raise ValueError(f"Product {request.product_id} not found")
                
                # 3. Upsert attribute value
                upsert_query = """
                    INSERT INTO product_attribute_values (
                        product_id, attribute_id, value, numeric_value, boolean_value, date_value
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (product_id, attribute_id)
                    DO UPDATE SET
                        value = $3,
                        numeric_value = $4,
                        boolean_value = $5,
                        date_value = $6
                    RETURNING value_id
                """
                
                result = await session.execute(
                    upsert_query,
                    request.product_id,
                    str(attribute.attribute_id),
                    request.value,
                    float(request.numeric_value) if request.numeric_value else None,
                    request.boolean_value,
                    request.date_value
                )
                
                value_id = result.fetchone()[0]
                
                await session.commit()
                
                self.logger.info("Set product attribute value",
                               product_id=request.product_id,
                               attribute_code=request.attribute_code)
                
                return ProductAttributeValue(
                    value_id=value_id,
                    product_id=request.product_id,
                    attribute_id=attribute.attribute_id,
                    value=request.value,
                    numeric_value=request.numeric_value,
                    boolean_value=request.boolean_value,
                    date_value=request.date_value,
                    attribute_code=attribute.attribute_code,
                    attribute_name=attribute.attribute_name,
                    attribute_type=attribute.attribute_type
                )
                
            except Exception as e:
                await session.rollback()
                self.logger.error("Failed to set attribute value",
                                error=str(e),
                                product_id=request.product_id,
                                attribute_code=request.attribute_code)
                raise
    
    async def get_product_attributes(self, product_id: str) -> List[ProductAttributeValue]:
        """Get all attribute values for a product."""
        async with self.db_manager.get_async_session() as session:
            query = """
                SELECT 
                    pav.value_id, pav.product_id, pav.attribute_id,
                    pav.value, pav.numeric_value, pav.boolean_value, pav.date_value,
                    pa.attribute_code, pa.attribute_name, pa.attribute_type
                FROM product_attribute_values pav
                JOIN product_attributes pa ON pav.attribute_id = pa.attribute_id
                WHERE pav.product_id = $1
                ORDER BY pa.sort_order
            """
            
            result = await session.execute(query, product_id)
            
            return [
                ProductAttributeValue(
                    value_id=row[0],
                    product_id=row[1],
                    attribute_id=UUID(row[2]),
                    value=row[3],
                    numeric_value=Decimal(str(row[4])) if row[4] else None,
                    boolean_value=row[5],
                    date_value=row[6],
                    attribute_code=row[7],
                    attribute_name=row[8],
                    attribute_type=AttributeType(row[9])
                )
                for row in result.fetchall()
            ]
    
    async def list_filterable_attributes(self) -> List[ProductAttribute]:
        """List all filterable attributes."""
        async with self.db_manager.get_async_session() as session:
            query = """
                SELECT attribute_id
                FROM product_attributes
                WHERE is_filterable = true AND is_visible = true
                ORDER BY sort_order, attribute_name
            """
            
            result = await session.execute(query)
            attribute_ids = [UUID(row[0]) for row in result.fetchall()]
            
            attributes = []
            for attr_id in attribute_ids:
                attr = await self.get_attribute(attr_id)
                if attr:
                    attributes.append(attr)
            
            return attributes
    
    async def filter_products_by_attributes(
        self,
        filters: List[AttributeFilter]
    ) -> List[str]:
        """Filter products by attribute values."""
        async with self.db_manager.get_async_session() as session:
            # Build dynamic query based on filters
            conditions = []
            params = []
            param_num = 1
            
            for filter_item in filters:
                # Get attribute
                attr_query = """
                    SELECT attribute_id, attribute_type
                    FROM product_attributes
                    WHERE attribute_code = $1
                """
                
                attr_result = await session.execute(attr_query, filter_item.attribute_code)
                attr_row = attr_result.fetchone()
                
                if not attr_row:
                    continue
                
                attribute_id, attribute_type = attr_row
                
                # Build condition based on operator and type
                if attribute_type == "number":
                    column = "numeric_value"
                elif attribute_type == "boolean":
                    column = "boolean_value"
                elif attribute_type == "date":
                    column = "date_value"
                else:
                    column = "value"
                
                if filter_item.operator == "eq":
                    conditions.append(f"(attribute_id = ${param_num} AND {column} = ${param_num + 1})")
                    params.extend([attribute_id, filter_item.value])
                    param_num += 2
                elif filter_item.operator == "in":
                    # For IN operator with multiple values
                    placeholders = ", ".join([f"${param_num + i}" for i in range(1, len(filter_item.value) + 1)])
                    conditions.append(f"(attribute_id = ${param_num} AND {column} IN ({placeholders}))")
                    params.append(attribute_id)
                    params.extend(filter_item.value)
                    param_num += len(filter_item.value) + 1
                elif filter_item.operator == "contains":
                    conditions.append(f"(attribute_id = ${param_num} AND {column} ILIKE ${param_num + 1})")
                    params.extend([attribute_id, f"%{filter_item.value}%"])
                    param_num += 2
            
            if not conditions:
                return []
            
            query = f"""
                SELECT DISTINCT product_id
                FROM product_attribute_values
                WHERE {' OR '.join(conditions)}
            """
            
            result = await session.execute(query, *params)
            
            return [row[0] for row in result.fetchall()]
    
    async def get_attribute_facets(self, product_ids: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
        """Get faceted search data for filterable attributes."""
        async with self.db_manager.get_async_session() as session:
            # Get all filterable attributes
            filterable = await self.list_filterable_attributes()
            
            facets = {}
            
            for attr in filterable:
                # Build query based on attribute type
                if attr.attribute_type in [AttributeType.SELECT, AttributeType.MULTISELECT]:
                    # For select types, use options
                    query = """
                        SELECT pav.value, COUNT(DISTINCT pav.product_id) as count
                        FROM product_attribute_values pav
                        WHERE pav.attribute_id = $1
                    """
                    
                    if product_ids:
                        query += f" AND pav.product_id = ANY(${2})"
                        result = await session.execute(query, str(attr.attribute_id), product_ids)
                    else:
                        result = await session.execute(query, str(attr.attribute_id))
                    
                    facets[attr.attribute_code] = [
                        {"value": row[0], "count": row[1]}
                        for row in result.fetchall()
                    ]
                
                elif attr.attribute_type == AttributeType.NUMBER:
                    # For numeric types, get min/max
                    query = """
                        SELECT MIN(numeric_value), MAX(numeric_value)
                        FROM product_attribute_values
                        WHERE attribute_id = $1
                    """
                    
                    if product_ids:
                        query += f" AND product_id = ANY(${2})"
                        result = await session.execute(query, str(attr.attribute_id), product_ids)
                    else:
                        result = await session.execute(query, str(attr.attribute_id))
                    
                    row = result.fetchone()
                    facets[attr.attribute_code] = {
                        "min": float(row[0]) if row[0] else 0,
                        "max": float(row[1]) if row[1] else 0
                    }
            
            return facets

