"""
Product Categories Service - Multi-Agent E-commerce System

This service handles hierarchical product category management including:
- Creating and managing category trees
- Category-product mapping
- SEO for categories
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
import structlog
import re

logger = structlog.get_logger(__name__)


# ===========================
# PYDANTIC MODELS
# ===========================

class ProductCategory(BaseModel):
    """Product category with hierarchical structure."""
    category_id: Optional[int] = None
    parent_id: Optional[int] = None
    category_name: str
    category_slug: str
    category_description: Optional[str] = None
    category_image_url: Optional[str] = None
    level: int = 0
    path: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    
    # SEO fields
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Related data
    children: Optional[List['ProductCategory']] = []
    product_count: Optional[int] = 0


class CreateCategoryRequest(BaseModel):
    """Request to create a new category."""
    category_name: str
    parent_id: Optional[int] = None
    category_description: Optional[str] = None
    category_image_url: Optional[str] = None
    display_order: int = 0
    
    # SEO fields
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = None


class UpdateCategoryRequest(BaseModel):
    """Request to update a category."""
    category_name: Optional[str] = None
    category_description: Optional[str] = None
    category_image_url: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    
    # SEO fields
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = None


# ===========================
# PRODUCT CATEGORIES SERVICE
# ===========================

class ProductCategoriesService:
    """Service for managing product categories."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logger.bind(service="product_categories")
    
    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from category name."""
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        return slug
    
    async def _calculate_path(self, parent_id: Optional[int]) -> tuple[int, str]:
        """Calculate level and materialized path for a category."""
        if not parent_id:
            return 0, "/"
        
        async with self.db_manager.get_async_session() as session:
            query = """
                SELECT level, path, category_id
                FROM product_categories
                WHERE category_id = $1
            """
            
            result = await session.execute(query, parent_id)
            row = result.fetchone()
            
            if not row:
                return 0, "/"
            
            parent_level, parent_path, parent_cat_id = row
            new_level = parent_level + 1
            new_path = f"{parent_path}{parent_cat_id}/"
            
            return new_level, new_path
    
    async def create_category(self, request: CreateCategoryRequest) -> ProductCategory:
        """Create a new product category."""
        slug = self._generate_slug(request.category_name)
        level, path = await self._calculate_path(request.parent_id)
        
        async with self.db_manager.get_async_session() as session:
            try:
                query = """
                    INSERT INTO product_categories (
                        parent_id, category_name, category_slug,
                        category_description, category_image_url,
                        level, path, display_order, is_active,
                        seo_title, seo_description, seo_keywords
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    RETURNING category_id, created_at, updated_at
                """
                
                result = await session.execute(
                    query,
                    request.parent_id,
                    request.category_name,
                    slug,
                    request.category_description,
                    request.category_image_url,
                    level,
                    path,
                    request.display_order,
                    True,
                    request.seo_title or request.category_name,
                    request.seo_description or request.category_description,
                    request.seo_keywords
                )
                
                row = result.fetchone()
                await session.commit()
                
                category_id = row[0]
                
                self.logger.info("Created category",
                               category_id=category_id,
                               name=request.category_name,
                               slug=slug)
                
                return await self.get_category(category_id)
                
            except Exception as e:
                await session.rollback()
                self.logger.error("Failed to create category",
                                error=str(e),
                                name=request.category_name)
                raise
    
    async def get_category(self, category_id: int, include_children: bool = False) -> Optional[ProductCategory]:
        """Get a category by ID."""
        async with self.db_manager.get_async_session() as session:
            query = """
                SELECT 
                    c.category_id, c.parent_id, c.category_name, c.category_slug,
                    c.category_description, c.category_image_url, c.level, c.path,
                    c.display_order, c.is_active, c.seo_title, c.seo_description,
                    c.seo_keywords, c.created_at, c.updated_at,
                    COUNT(DISTINCT pcm.product_id) as product_count
                FROM product_categories c
                LEFT JOIN product_category_mapping pcm ON c.category_id = pcm.category_id
                WHERE c.category_id = $1
                GROUP BY c.category_id
            """
            
            result = await session.execute(query, category_id)
            row = result.fetchone()
            
            if not row:
                return None
            
            category = ProductCategory(
                category_id=row[0],
                parent_id=row[1],
                category_name=row[2],
                category_slug=row[3],
                category_description=row[4],
                category_image_url=row[5],
                level=row[6],
                path=row[7],
                display_order=row[8],
                is_active=row[9],
                seo_title=row[10],
                seo_description=row[11],
                seo_keywords=row[12],
                created_at=row[13],
                updated_at=row[14],
                product_count=row[15]
            )
            
            if include_children:
                category.children = await self.get_child_categories(category_id)
            
            return category
    
    async def get_child_categories(self, parent_id: int) -> List[ProductCategory]:
        """Get direct children of a category."""
        async with self.db_manager.get_async_session() as session:
            query = """
                SELECT category_id
                FROM product_categories
                WHERE parent_id = $1 AND is_active = true
                ORDER BY display_order, category_name
            """
            
            result = await session.execute(query, parent_id)
            category_ids = [row[0] for row in result.fetchall()]
            
            categories = []
            for cat_id in category_ids:
                category = await self.get_category(cat_id)
                if category:
                    categories.append(category)
            
            return categories
    
    async def get_category_tree(self, root_id: Optional[int] = None) -> List[ProductCategory]:
        """Get the full category tree or subtree."""
        if root_id:
            root = await self.get_category(root_id, include_children=False)
            if not root:
                return []
            categories = [root]
        else:
            # Get root categories (no parent)
            async with self.db_manager.get_async_session() as session:
                query = """
                    SELECT category_id
                    FROM product_categories
                    WHERE parent_id IS NULL AND is_active = true
                    ORDER BY display_order, category_name
                """
                
                result = await session.execute(query)
                category_ids = [row[0] for row in result.fetchall()]
                
                categories = []
                for cat_id in category_ids:
                    category = await self.get_category(cat_id)
                    if category:
                        categories.append(category)
        
        # Recursively load children
        for category in categories:
            category.children = await self._load_category_tree_recursive(category.category_id)
        
        return categories
    
    async def _load_category_tree_recursive(self, parent_id: int) -> List[ProductCategory]:
        """Recursively load category tree."""
        children = await self.get_child_categories(parent_id)
        
        for child in children:
            child.children = await self._load_category_tree_recursive(child.category_id)
        
        return children
    
    async def update_category(self, category_id: int, request: UpdateCategoryRequest) -> Optional[ProductCategory]:
        """Update a category."""
        async with self.db_manager.get_async_session() as session:
            try:
                # Build dynamic update query
                updates = []
                params = []
                param_num = 1
                
                if request.category_name is not None:
                    updates.append(f"category_name = ${param_num}")
                    params.append(request.category_name)
                    param_num += 1
                    
                    # Update slug if name changes
                    slug = self._generate_slug(request.category_name)
                    updates.append(f"category_slug = ${param_num}")
                    params.append(slug)
                    param_num += 1
                
                if request.category_description is not None:
                    updates.append(f"category_description = ${param_num}")
                    params.append(request.category_description)
                    param_num += 1
                
                if request.category_image_url is not None:
                    updates.append(f"category_image_url = ${param_num}")
                    params.append(request.category_image_url)
                    param_num += 1
                
                if request.display_order is not None:
                    updates.append(f"display_order = ${param_num}")
                    params.append(request.display_order)
                    param_num += 1
                
                if request.is_active is not None:
                    updates.append(f"is_active = ${param_num}")
                    params.append(request.is_active)
                    param_num += 1
                
                if request.seo_title is not None:
                    updates.append(f"seo_title = ${param_num}")
                    params.append(request.seo_title)
                    param_num += 1
                
                if request.seo_description is not None:
                    updates.append(f"seo_description = ${param_num}")
                    params.append(request.seo_description)
                    param_num += 1
                
                if request.seo_keywords is not None:
                    updates.append(f"seo_keywords = ${param_num}")
                    params.append(request.seo_keywords)
                    param_num += 1
                
                if not updates:
                    return await self.get_category(category_id)
                
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(category_id)
                
                query = f"""
                    UPDATE product_categories
                    SET {', '.join(updates)}
                    WHERE category_id = ${param_num}
                """
                
                await session.execute(query, *params)
                await session.commit()
                
                self.logger.info("Updated category", category_id=category_id)
                
                return await self.get_category(category_id)
                
            except Exception as e:
                await session.rollback()
                self.logger.error("Failed to update category",
                                error=str(e),
                                category_id=category_id)
                raise
    
    async def assign_product_to_category(
        self,
        product_id: str,
        category_id: int,
        is_primary: bool = False
    ) -> bool:
        """Assign a product to a category."""
        async with self.db_manager.get_async_session() as session:
            try:
                # If this is primary, unset other primary mappings
                if is_primary:
                    await session.execute(
                        """
                        UPDATE product_category_mapping
                        SET is_primary = false
                        WHERE product_id = $1
                        """,
                        product_id
                    )
                
                query = """
                    INSERT INTO product_category_mapping (
                        product_id, category_id, is_primary
                    ) VALUES ($1, $2, $3)
                    ON CONFLICT (product_id, category_id)
                    DO UPDATE SET is_primary = $3
                """
                
                await session.execute(query, product_id, category_id, is_primary)
                await session.commit()
                
                self.logger.info("Assigned product to category",
                               product_id=product_id,
                               category_id=category_id,
                               is_primary=is_primary)
                
                return True
                
            except Exception as e:
                await session.rollback()
                self.logger.error("Failed to assign product to category",
                                error=str(e),
                                product_id=product_id,
                                category_id=category_id)
                raise
    
    async def get_products_in_category(
        self,
        category_id: int,
        include_subcategories: bool = False
    ) -> List[str]:
        """Get all product IDs in a category."""
        async with self.db_manager.get_async_session() as session:
            if include_subcategories:
                # Get category path
                cat = await self.get_category(category_id)
                if not cat:
                    return []
                
                query = """
                    SELECT DISTINCT pcm.product_id
                    FROM product_category_mapping pcm
                    JOIN product_categories c ON pcm.category_id = c.category_id
                    WHERE c.path LIKE $1 OR c.category_id = $2
                """
                
                result = await session.execute(
                    query,
                    f"{cat.path}{cat.category_id}/%",
                    category_id
                )
            else:
                query = """
                    SELECT product_id
                    FROM product_category_mapping
                    WHERE category_id = $1
                """
                
                result = await session.execute(query, category_id)
            
            return [row[0] for row in result.fetchall()]
    
    async def delete_category(self, category_id: int) -> bool:
        """Soft delete a category."""
        async with self.db_manager.get_async_session() as session:
            query = """
                UPDATE product_categories
                SET is_active = false, updated_at = CURRENT_TIMESTAMP
                WHERE category_id = $1
            """
            
            await session.execute(query, category_id)
            await session.commit()
            
            self.logger.info("Deleted category", category_id=category_id)
            
            return True

