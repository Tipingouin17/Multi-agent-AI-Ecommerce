
"""
Knowledge Management Agent - Multi-Agent E-Commerce System

Manages documentation, FAQs, knowledge base articles, and AI-powered search/suggestions.
"""

import os
import sys
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID
from enum import Enum

from fastapi import FastAPI, HTTPException, Depends, Body, Path, status
from pydantic import BaseModel, Field
import structlog
import uvicorn

# Adjust the path to import from shared
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.database import DatabaseManager, get_database_manager, Base  # Import Base for declarative models
from shared.db_helpers import DatabaseHelper
from shared.agent_core import BaseAgent, AgentMessage, MessageType, AgentType # Import BaseAgent and messaging types
from sqlalchemy import Column, String, DateTime, Integer, Text, ARRAY, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.future import select
from sqlalchemy.orm import relationship


logger = structlog.get_logger(__name__)

# Environment variables
KAFKA_BROKER_URL = os.getenv("KAFKA_BROKER_URL", "localhost:9092")
KAFKA_KNOWLEDGE_TOPIC = os.getenv("KAFKA_KNOWLEDGE_TOPIC", "knowledge_events")
AGENT_ID = os.getenv("AGENT_ID", "knowledge_management_agent_001")
AGENT_TYPE = os.getenv("AGENT_TYPE", "knowledge_management")
API_PORT = int(os.getenv("API_PORT", "8020"))

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
    PRODUCT_INFO = "product_info"
    TROUBLESHOOTING = "troubleshooting"

# Database Models
class DBArticle(Base):
    __tablename__ = "articles"

    article_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    status = Column(String, default=ArticleStatus.DRAFT.value, nullable=False)
    views = Column(Integer, default=0, nullable=False)
    helpful_count = Column(Integer, default=0, nullable=False)
    tags = Column(ARRAY(String), default=[] , nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "article_id": str(self.article_id),
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "status": self.status,
            "views": self.views,
            "helpful_count": self.helpful_count,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

# Pydantic Models
class ArticleCreate(BaseModel):
    title: str = Field(..., description="Title of the knowledge base article.")
    content: str = Field(..., description="Full content of the article.")
    category: ArticleCategory = Field(..., description="Category of the article.")
    tags: Optional[List[str]] = Field(None, description="List of tags for the article.")

class ArticleUpdate(BaseModel):
    title: Optional[str] = Field(None, description="New title for the article.")
    content: Optional[str] = Field(None, description="New content for the article.")
    category: Optional[ArticleCategory] = Field(None, description="New category for the article.")
    status: Optional[ArticleStatus] = Field(None, description="New status for the article.")
    tags: Optional[List[str]] = Field(None, description="New list of tags for the article.")

class ArticleResponse(BaseModel):
    article_id: UUID = Field(..., description="Unique identifier of the article.")
    title: str = Field(..., description="Title of the knowledge base article.")
    content: str = Field(..., description="Full content of the article.")
    category: ArticleCategory = Field(..., description="Category of the article.")
    status: ArticleStatus = Field(..., description="Current status of the article.")
    views: int = Field(0, description="Number of times the article has been viewed.")
    helpful_count: int = Field(0, description="Number of times the article was marked as helpful.")
    tags: List[str] = Field([], description="List of tags associated with the article.")
    created_at: datetime = Field(..., description="Timestamp when the article was created.")
    updated_at: datetime = Field(..., description="Timestamp when the article was last updated.")

    class Config:
        from_attributes = True

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query string.")
    category: Optional[ArticleCategory] = Field(None, description="Optional category to filter search results.")
    limit: int = Field(10, gt=0, description="Maximum number of search results to return.")
    offset: int = Field(0, ge=0, description="Number of results to skip for pagination.")

class SearchResult(BaseModel):
    article_id: UUID = Field(..., description="ID of the found article.")
    title: str = Field(..., description="Title of the found article.")
    excerpt: str = Field(..., description="Brief excerpt from the article content.")
    relevance_score: float = Field(..., description="Relevance score of the search result.")

class SearchResponse(BaseModel):
    results: List[SearchResult] = Field(..., description="List of search results.")
    count: int = Field(..., description="Total number of results found.")

# SERVICE
class KnowledgeManagementService:
    """Service layer for managing knowledge base articles."""
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.db_helper = DatabaseHelper(db_manager, DBArticle)
        self._db_initialized = False

    async def initialize_db(self):
        """Initializes the database tables."""
        if not self._db_initialized:
            await self.db_manager.create_all(Base)
            self._db_initialized = True

    async def create_article(self, article_data: ArticleCreate) -> ArticleResponse:
        """Create a new knowledge base article.

        Args:
            article_data (ArticleCreate): Data for the new article.

        Returns:
            ArticleResponse: The created article.
        
        Raises:
            HTTPException: If there is an error creating the article.
        """
        if not self._db_initialized: return []
        try:
            article_dict = article_data.model_dump()
            db_article = DBArticle(**article_dict)
            created_article = await self.db_helper.create(db_article)
            logger.info("article_created", article_id=str(created_article.article_id), title=created_article.title)
            return ArticleResponse.model_validate(created_article.to_dict())
        except Exception as e:
            logger.error("create_article_failed", error=str(e), article_data=article_data.model_dump_json())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create article: {e}")

    async def get_article(self, article_id: UUID) -> Optional[ArticleResponse]:
        """Retrieve a knowledge base article by its ID.

        Args:
            article_id (UUID): The unique identifier of the article.

        Returns:
            Optional[ArticleResponse]: The article if found, otherwise None.
        
        Raises:
            HTTPException: If there is an error retrieving the article.
        """
        if not self._db_initialized: return None
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(DBArticle).filter(DBArticle.article_id == article_id)
                result = await session.execute(stmt)
                db_article = result.scalar_one_or_none()
                if db_article:
                    db_article.views += 1  # Increment view count
                    await session.commit()
                    await session.refresh(db_article)
                    logger.info("article_retrieved", article_id=str(article_id), title=db_article.title, views=db_article.views)
                    return ArticleResponse.model_validate(db_article.to_dict())
                return None
        except Exception as e:
            logger.error("get_article_failed", error=str(e), article_id=str(article_id))
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve article: {e}")

    async def update_article(self, article_id: UUID, update_data: ArticleUpdate) -> Optional[ArticleResponse]:
        """Update an existing knowledge base article.

        Args:
            article_id (UUID): The unique identifier of the article to update.
            update_data (ArticleUpdate): Data to update the article with.

        Returns:
            Optional[ArticleResponse]: The updated article if found, otherwise None.
        
        Raises:
            HTTPException: If there is an error updating the article.
        """
        if not self._db_initialized: return None
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(DBArticle).filter(DBArticle.article_id == article_id)
                result = await session.execute(stmt)
                db_article = result.scalar_one_or_none()
                if db_article:
                    update_dict = update_data.model_dump(exclude_unset=True)
                    for key, value in update_dict.items():
                        setattr(db_article, key, value)
                    db_article.updated_at = datetime.utcnow() # Manually update timestamp
                    await session.commit()
                    await session.refresh(db_article)
                    logger.info("article_updated", article_id=str(article_id), title=db_article.title)
                    return ArticleResponse.model_validate(db_article.to_dict())
                return None
        except Exception as e:
            logger.error("update_article_failed", error=str(e), article_id=str(article_id), update_data=update_data.model_dump_json())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update article: {e}")

    async def delete_article(self, article_id: UUID) -> bool:
        """Delete a knowledge base article by its ID.

        Args:
            article_id (UUID): The unique identifier of the article to delete.

        Returns:
            bool: True if the article was deleted, False otherwise.
        
        Raises:
            HTTPException: If there is an error deleting the article.
        """
        if not self._db_initialized: return False
        try:
            success = await self.db_helper.delete(article_id)
            if success:
                logger.info("article_deleted", article_id=str(article_id))
            else:
                logger.warning("article_delete_not_found", article_id=str(article_id))
            return success
        except Exception as e:
            logger.error("delete_article_failed", error=str(e), article_id=str(article_id))
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete article: {e}")

    async def search_articles(self, search_request: SearchRequest) -> SearchResponse:
        """Search knowledge base with AI-powered relevance.

        This is a simulated search. In a real-world scenario, this would involve
        a dedicated search index (e.g., Elasticsearch, vector database) and
        AI/LLM integration for semantic search and relevance ranking.

        Args:
            search_request (SearchRequest): The search query and filters.

        Returns:
            SearchResponse: A list of relevant articles.
        
        Raises:
            HTTPException: If there is an error during the search operation.
        """
        if not self._db_initialized: return SearchResponse(results=[], count=0)
        try:
            async with self.db_manager.get_session() as session:
                query = select(DBArticle).filter(DBArticle.status == ArticleStatus.PUBLISHED.value)

                if search_request.category:
                    query = query.filter(DBArticle.category == search_request.category.value)

                # Simple keyword search on title and content for demonstration
                if search_request.query:
                    search_pattern = f"%{search_request.query.lower()}%"
                    query = query.filter(
                        (DBArticle.title.ilike(search_pattern)) |
                        (DBArticle.content.ilike(search_pattern))
                    )
                
                # Order by helpful_count for a simple relevance proxy
                query = query.order_by(DBArticle.helpful_count.desc(), DBArticle.views.desc())

                # Apply offset and limit for pagination
                query = query.offset(search_request.offset).limit(search_request.limit)

                result = await session.execute(query)
                db_articles = result.scalars().all()

                results = []
                for article in db_articles:
                    excerpt = article.content[:200] + "..." if len(article.content) > 200 else article.content
                    results.append(SearchResult(
                        article_id=article.article_id,
                        title=article.title,
                        excerpt=excerpt,
                        relevance_score=1.0 # Placeholder, actual relevance would come from AI
                    ))
                
                # For count, we need to execute a separate count query without limit/offset
                count_query = select(DBArticle).filter(DBArticle.status == ArticleStatus.PUBLISHED.value)
                if search_request.category:
                    count_query = count_query.filter(DBArticle.category == search_request.category.value)
                if search_request.query:
                    search_pattern = f"%{search_request.query.lower()}%"
                    count_query = count_query.filter(
                        (DBArticle.title.ilike(search_pattern)) |
                        (DBArticle.content.ilike(search_pattern))
                    )
                total_count_result = await session.execute(select(func.count()).select_from(count_query))
                total_count = total_count_result.scalar_one()

                logger.info("articles_searched", query=search_request.query, results_count=len(results), total_count=total_count)
                return SearchResponse(results=results, count=total_count)
        except Exception as e:
            logger.error("search_articles_failed", error=str(e), search_request=search_request.model_dump_json())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to search articles: {e}")

    async def mark_article_helpful(self, article_id: UUID) -> Optional[ArticleResponse]:
        """Increments the helpful_count for an article.

        Args:
            article_id (UUID): The ID of the article to mark as helpful.

        Returns:
            Optional[ArticleResponse]: The updated article if found, otherwise None.
        
        Raises:
            HTTPException: If there is an error marking the article as helpful.
        """
        if not self._db_initialized: return None
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(DBArticle).filter(DBArticle.article_id == article_id)
                result = await session.execute(stmt)
                db_article = result.scalar_one_or_none()
                if db_article:
                    db_article.helpful_count += 1
                    await session.commit()
                    await session.refresh(db_article)
                    logger.info("article_marked_helpful", article_id=str(article_id), helpful_count=db_article.helpful_count)
                    return ArticleResponse.model_validate(db_article.to_dict())
                return None
        except Exception as e:
            logger.error("mark_article_helpful_failed", error=str(e), article_id=str(article_id))
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to mark article helpful: {e}")


# Agent Class
class KnowledgeManagementAgent(BaseAgent):
    """Knowledge Management Agent for the E-Commerce system.

    This agent manages knowledge base articles, FAQs, and provides search
    and suggestion capabilities. It integrates with a database for storage
    and Kafka for inter-agent communication.
    """
    def __init__(self, agent_id: str, agent_type: str, db_manager: DatabaseManager):
        super().__init__(agent_id=agent_id, agent_type=agent_type, kafka_broker=KAFKA_BROKER_URL, topic=KAFKA_KNOWLEDGE_TOPIC)
        self.db_manager = db_manager
        self.service = KnowledgeManagementService(db_manager)
        self._db_initialized = False

    async def setup(self):
        """Performs initial setup for the agent, including database initialization."""
        await super().setup()
        await self.service.initialize_db()
        self._db_initialized = True
        logger.info(f"KnowledgeManagementAgent {self.agent_id} setup complete.")

    async def process_message(self, message: AgentMessage):
        """Processes incoming messages from other agents.

        Args:
            message (AgentMessage): The incoming message to process.
        """
        logger.info(f"KnowledgeManagementAgent {self.agent_id} received message: {message.message_type}")
        try:
            if message.message_type == MessageType.REQUEST_KNOWLEDGE_SEARCH:
                search_query = message.payload.get("query")
                if search_query:
                    search_request = SearchRequest(query=search_query)
                    response = await self.service.search_articles(search_request)
                    await self.send_message(
                        recipient_id=message.sender_id,
                        message_type=MessageType.KNOWLEDGE_SEARCH_RESPONSE,
                        payload=response.model_dump()
                    )
                else:
                    logger.warning("Received REQUEST_KNOWLEDGE_SEARCH with no query", message=message.model_dump())
            elif message.message_type == MessageType.CREATE_KNOWLEDGE_ARTICLE:
                article_data = message.payload
                if article_data:
                    try:
                        article_create = ArticleCreate(**article_data)
                        new_article = await self.service.create_article(article_create)
                        await self.send_message(
                            recipient_id=message.sender_id,
                            message_type=MessageType.KNOWLEDGE_ARTICLE_CREATED,
                            payload=new_article.model_dump()
                        )
                    except Exception as e:
                        logger.error("Failed to parse or create article from message", error=str(e), payload=article_data)
                        await self.send_message(
                            recipient_id=message.sender_id,
                            message_type=MessageType.ERROR,
                            payload={"original_message_type": message.message_type, "error": str(e)}
                        )
                else:
                    logger.warning("Received CREATE_KNOWLEDGE_ARTICLE with no payload", message=message.model_dump())
            else:
                logger.warning(f"Unknown message type received: {message.message_type}", message=message.model_dump())
        except Exception as e:
            logger.error(f"Error processing message: {e}", message=message.model_dump())
            await self.send_message(
                recipient_id=message.sender_id,
                message_type=MessageType.ERROR,
                payload={"original_message_type": message.message_type, "error": str(e)}
            )


# FASTAPI APP
app = FastAPI(title="Knowledge Management Agent API",
              version="1.0.0",
              description="API for managing knowledge base articles in the E-Commerce system.")

# Dependency to get the KnowledgeManagementService
async def get_service_dependency(db_manager: DatabaseManager = Depends(get_database_manager)) -> KnowledgeManagementService:
    """Dependency that provides a KnowledgeManagementService instance."""
    service = KnowledgeManagementService(db_manager)
    if not service._db_initialized:
        await service.initialize_db() # Ensure DB is initialized for API calls
    return service

@app.on_event("startup")
async def startup_event():
    """Startup event to initialize the database and agent."""
    logger.info("Knowledge Management Agent API starting up...")
    db_manager = await get_database_manager()
    await db_manager.create_all(Base) # Ensure all tables are created on startup
    
    global knowledge_agent
    knowledge_agent = KnowledgeManagementAgent(AGENT_ID, AGENT_TYPE, db_manager)
    await knowledge_agent.setup()
    asyncio.create_task(knowledge_agent.run()) # Start the agent's Kafka consumer in the background
    logger.info("Knowledge Management Agent and API ready.")

@app.get("/health", response_model=Dict[str, str], summary="Health Check")
async def health_check():
    """Check the health status of the Knowledge Management Agent API."""
    return {"status": "healthy", "agent": AGENT_ID, "type": AGENT_TYPE, "version": app.version}

@app.get("/", response_model=Dict[str, str], summary="Root Endpoint")
async def root():
    """Root endpoint providing basic information about the API."""
    return {"message": "Knowledge Management Agent API is running", "version": app.version}

@app.post("/api/v1/knowledge/articles", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED, summary="Create Article")
async def create_article_endpoint(
    article_data: ArticleCreate = Body(..., description="Data for the new knowledge base article."),
    service: KnowledgeManagementService = Depends(get_service_dependency)
):
    """Create a new knowledge base article.

    Allows for the submission of new articles to the knowledge base.
    """
    return await service.create_article(article_data)

@app.get("/api/v1/knowledge/articles/{article_id}", response_model=ArticleResponse, summary="Get Article by ID")
async def get_article_endpoint(
    article_id: UUID = Path(..., description="The UUID of the article to retrieve."),
    service: KnowledgeManagementService = Depends(get_service_dependency)
):
    """Retrieve a specific knowledge base article by its unique ID.

    Returns the full details of an article if found.
    """
    article = await service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    return article

@app.put("/api/v1/knowledge/articles/{article_id}", response_model=ArticleResponse, summary="Update Article")
async def update_article_endpoint(
    article_id: UUID = Path(..., description="The UUID of the article to update."),
    update_data: ArticleUpdate = Body(..., description="Data to update the knowledge base article."),
    service: KnowledgeManagementService = Depends(get_service_dependency)
):
    """Update an existing knowledge base article.

    Allows for partial or full updates to an article's content, title, category, or status.
    """
    updated_article = await service.update_article(article_id, update_data)
    if not updated_article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    return updated_article

@app.delete("/api/v1/knowledge/articles/{article_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Article")
async def delete_article_endpoint(
    article_id: UUID = Path(..., description="The UUID of the article to delete."),
    service: KnowledgeManagementService = Depends(get_service_dependency)
):
    """Delete a knowledge base article by its unique ID.

    Removes an article from the knowledge base.
    """
    success = await service.delete_article(article_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    return

@app.post("/api/v1/knowledge/search", response_model=SearchResponse, summary="Search Articles")
async def search_articles_endpoint(
    search_request: SearchRequest = Body(..., description="Search query and filters for articles."),
    service: KnowledgeManagementService = Depends(get_service_dependency)
):
    """Search for knowledge base articles.

    Provides a search interface to find relevant articles based on keywords, category, and other filters.
    """
    return await service.search_articles(search_request)

@app.post("/api/v1/knowledge/articles/{article_id}/helpful", response_model=ArticleResponse, summary="Mark Article as Helpful")
async def mark_article_helpful_endpoint(
    article_id: UUID = Path(..., description="The UUID of the article to mark as helpful."),
    service: KnowledgeManagementService = Depends(get_service_dependency)
):
    """Mark a knowledge base article as helpful.

    Increments the helpful count for a given article, indicating its utility.
    """
    updated_article = await service.mark_article_helpful(article_id)
    if not updated_article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    return updated_article



if __name__ == "__main__":
    # This block is for local development/testing and will not be run in the agent's async loop
    # The agent's run() method is started in the startup_event for the FastAPI application.
    logger.info("Starting Knowledge Management Agent API via uvicorn")
    uvicorn.run(app, host="0.0.0.0", port=API_PORT)

from sqlalchemy import func # Imported here to avoid circular dependency with DBArticle for func.count()
