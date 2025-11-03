"""
Product SEO Service - Multi-Agent E-commerce System

This service handles SEO optimization for products including:
- Meta tags management
- URL slug generation
- Sitemap generation
- SEO analytics
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
import structlog
import re
import xml.etree.ElementTree as ET
from shared.base_agent_v2 import BaseAgentV2

logger = structlog.get_logger(__name__)


# ===========================
# PYDANTIC MODELS
# ===========================

class ProductSEO(BaseModel):
    """SEO data for a product."""
    product_id: str
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    url_slug: Optional[str] = None
    canonical_url: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    twitter_card: str = "summary_large_image"
    schema_markup: Optional[Dict] = None
    robots_meta: str = "index, follow"
    updated_at: Optional[datetime] = None


class UpdateSEORequest(BaseModel):
    """Request to update product SEO."""
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    url_slug: Optional[str] = None
    canonical_url: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    robots_meta: Optional[str] = None


class SitemapEntry(BaseModel):
    """Entry in XML sitemap."""
    loc: str
    lastmod: str
    changefreq: str = "weekly"
    priority: float = 0.8


# ===========================
# PRODUCT SEO SERVICE
# ===========================

class ProductSEOService(BaseAgentV2):
    """Service for managing product SEO."""
    
    def __init__(self, agent_id: str = "productseoservice_001", db_manager=None):
        super().__init__(agent_id=agent_id)
        self.db_manager = db_manager
        self.logger = logger.bind(service="product_seo")
    
    def _generate_slug(self, text: str) -> str:
        """Generate URL-friendly slug."""
        slug = text.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        slug = slug[:100]  # Limit length
        return slug
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to max length with ellipsis."""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    async def generate_product_seo(
        self,
        product_id: str,
        product_name: str,
        product_description: Optional[str] = None,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        price: Optional[float] = None,
        image_url: Optional[str] = None
    ) -> ProductSEO:
        """Auto-generate SEO data for a product."""
        
        # Generate meta title (max 60 chars)
        meta_title = product_name
        if brand:
            meta_title = f"{product_name} - {brand}"
        if category:
            meta_title = f"{product_name} | {category}"
        meta_title = self._truncate_text(meta_title, 60)
        
        # Generate meta description (max 160 chars)
        meta_description = product_description or f"Buy {product_name}"
        if price:
            meta_description += f" for ${price:.2f}"
        if brand:
            meta_description += f" from {brand}"
        meta_description = self._truncate_text(meta_description, 160)
        
        # Generate keywords
        keywords = [product_name.lower()]
        if brand:
            keywords.append(brand.lower())
        if category:
            keywords.append(category.lower())
        meta_keywords = ", ".join(keywords)
        
        # Generate URL slug
        url_slug = self._generate_slug(product_name)
        
        # Generate Schema.org markup
        schema_markup = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": product_name,
            "description": product_description or product_name,
            "brand": {
                "@type": "Brand",
                "name": brand
            } if brand else None,
            "offers": {
                "@type": "Offer",
                "price": price,
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock"
            } if price else None,
            "image": image_url
        }
        
        # Remove None values
        schema_markup = {k: v for k, v in schema_markup.items() if v is not None}
        
        seo = ProductSEO(
            product_id=product_id,
            meta_title=meta_title,
            meta_description=meta_description,
            meta_keywords=meta_keywords,
            url_slug=url_slug,
            og_title=meta_title,
            og_description=meta_description,
            og_image=image_url,
            schema_markup=schema_markup,
            robots_meta="index, follow"
        )
        
        # Save to database
        await self.save_product_seo(seo)
        
        return seo
    
    async def save_product_seo(self, seo: ProductSEO) -> bool:
        """Save or update product SEO data."""
        async with self.db_manager.get_async_session() as session:
            try:
                # Check if products table has SEO columns
                # If not, we'll store in metadata JSONB field
                query = """
                    UPDATE products
                    SET metadata = COALESCE(metadata, '{}'::jsonb) || $1::jsonb,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $2
                """
                
                seo_data = {
                    "seo": {
                        "meta_title": seo.meta_title,
                        "meta_description": seo.meta_description,
                        "meta_keywords": seo.meta_keywords,
                        "url_slug": seo.url_slug,
                        "canonical_url": seo.canonical_url,
                        "og_title": seo.og_title,
                        "og_description": seo.og_description,
                        "og_image": seo.og_image,
                        "twitter_card": seo.twitter_card,
                        "schema_markup": seo.schema_markup,
                        "robots_meta": seo.robots_meta
                    }
                }
                
                await session.execute(
                    query,
                    seo_data,
                    seo.product_id
                )
                
                await session.commit()
                
                self.logger.info("Saved product SEO",
                               product_id=seo.product_id,
                               slug=seo.url_slug)
                
                return True
                
            except Exception as e:
                await session.rollback()
                self.logger.error("Failed to save product SEO",
                                error=str(e),
                                product_id=seo.product_id)
                raise
    
    async def get_product_seo(self, product_id: str) -> Optional[ProductSEO]:
        """Get SEO data for a product."""
        async with self.db_manager.get_async_session() as session:
            query = """
                SELECT metadata->'seo', updated_at
                FROM products
                WHERE id = $1
            """
            
            result = await session.execute(query, product_id)
            row = result.fetchone()
            
            if not row or not row[0]:
                return None
            
            seo_data = row[0]
            
            return ProductSEO(
                product_id=product_id,
                meta_title=seo_data.get("meta_title"),
                meta_description=seo_data.get("meta_description"),
                meta_keywords=seo_data.get("meta_keywords"),
                url_slug=seo_data.get("url_slug"),
                canonical_url=seo_data.get("canonical_url"),
                og_title=seo_data.get("og_title"),
                og_description=seo_data.get("og_description"),
                og_image=seo_data.get("og_image"),
                twitter_card=seo_data.get("twitter_card", "summary_large_image"),
                schema_markup=seo_data.get("schema_markup"),
                robots_meta=seo_data.get("robots_meta", "index, follow"),
                updated_at=row[1]
            )
    
    async def update_product_seo(
        self,
        product_id: str,
        request: UpdateSEORequest
    ) -> Optional[ProductSEO]:
        """Update product SEO data."""
        # Get existing SEO
        existing_seo = await self.get_product_seo(product_id)
        
        if not existing_seo:
            # Create new SEO entry
            async with self.db_manager.get_async_session() as session:
                query = """
                    SELECT name, description, category, brand, price
                    FROM products
                    WHERE id = $1
                """
                
                result = await session.execute(query, product_id)
                row = result.fetchone()
                
                if not row:
                    return None
                
                existing_seo = await self.generate_product_seo(
                    product_id=product_id,
                    product_name=row[0],
                    product_description=row[1],
                    category=row[2],
                    brand=row[3],
                    price=float(row[4]) if row[4] else None
                )
        
        # Update fields
        if request.meta_title is not None:
            existing_seo.meta_title = request.meta_title
        if request.meta_description is not None:
            existing_seo.meta_description = request.meta_description
        if request.meta_keywords is not None:
            existing_seo.meta_keywords = request.meta_keywords
        if request.url_slug is not None:
            existing_seo.url_slug = self._generate_slug(request.url_slug)
        if request.canonical_url is not None:
            existing_seo.canonical_url = request.canonical_url
        if request.og_title is not None:
            existing_seo.og_title = request.og_title
        if request.og_description is not None:
            existing_seo.og_description = request.og_description
        if request.og_image is not None:
            existing_seo.og_image = request.og_image
        if request.robots_meta is not None:
            existing_seo.robots_meta = request.robots_meta
        
        # Save updated SEO
        await self.save_product_seo(existing_seo)
        
        return existing_seo
    
    async def generate_sitemap(
        self,
        base_url: str = "https://example.com",
        limit: Optional[int] = None
    ) -> str:
        """Generate XML sitemap for all products."""
        async with self.db_manager.get_async_session() as session:
            query = """
                SELECT 
                    p.id,
                    p.metadata->'seo'->>'url_slug' as slug,
                    p.updated_at
                FROM products p
                WHERE p.status = 'active'
                ORDER BY p.updated_at DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            result = await session.execute(query)
            rows = result.fetchall()
            
            # Create XML sitemap
            urlset = ET.Element("urlset")
            urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
            
            for row in rows:
                product_id, slug, updated_at = row
                
                if not slug:
                    slug = product_id
                
                url = ET.SubElement(urlset, "url")
                
                loc = ET.SubElement(url, "loc")
                loc.text = f"{base_url}/products/{slug}"
                
                lastmod = ET.SubElement(url, "lastmod")
                lastmod.text = updated_at.strftime("%Y-%m-%d")
                
                changefreq = ET.SubElement(url, "changefreq")
                changefreq.text = "weekly"
                
                priority = ET.SubElement(url, "priority")
                priority.text = "0.8"
            
            # Convert to string
            xml_string = ET.tostring(urlset, encoding="unicode", method="xml")
            
            # Add XML declaration
            sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_string
            
            self.logger.info("Generated sitemap",
                           product_count=len(rows))
            
            return sitemap
    
    async def get_seo_analytics(self) -> Dict:
        """Get SEO analytics and recommendations."""
        async with self.db_manager.get_async_session() as session:
            query = """
                SELECT 
                    COUNT(*) as total_products,
                    COUNT(CASE WHEN metadata->'seo' IS NOT NULL THEN 1 END) as products_with_seo,
                    COUNT(CASE WHEN metadata->'seo'->>'meta_title' IS NOT NULL THEN 1 END) as with_meta_title,
                    COUNT(CASE WHEN metadata->'seo'->>'meta_description' IS NOT NULL THEN 1 END) as with_meta_description,
                    COUNT(CASE WHEN metadata->'seo'->>'url_slug' IS NOT NULL THEN 1 END) as with_url_slug
                FROM products
                WHERE status = 'active'
            """
            
            result = await session.execute(query)
            row = result.fetchone()
            
            total = row[0]
            with_seo = row[1]
            with_title = row[2]
            with_desc = row[3]
            with_slug = row[4]
            
            analytics = {
                "total_products": total,
                "products_with_seo": with_seo,
                "seo_coverage_percentage": (with_seo / total * 100) if total > 0 else 0,
                "meta_title_coverage": (with_title / total * 100) if total > 0 else 0,
                "meta_description_coverage": (with_desc / total * 100) if total > 0 else 0,
                "url_slug_coverage": (with_slug / total * 100) if total > 0 else 0,
                "recommendations": []
            }
            
            # Generate recommendations
            if analytics["seo_coverage_percentage"] < 80:
                analytics["recommendations"].append(
                    "Low SEO coverage. Consider auto-generating SEO for products without it."
                )
            
            if analytics["meta_description_coverage"] < 90:
                analytics["recommendations"].append(
                    "Many products missing meta descriptions. This impacts search engine rankings."
                )
            
            if analytics["url_slug_coverage"] < 95:
                analytics["recommendations"].append(
                    "Some products missing URL slugs. Generate slugs for better URLs."
                )
            
            return analytics
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

