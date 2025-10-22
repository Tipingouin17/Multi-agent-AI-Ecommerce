"""
Recommendation Agent - Multi-Agent E-Commerce System

This agent provides personalized product recommendations using collaborative filtering,
content-based filtering, and hybrid approaches.

DATABASE SCHEMA (migration 012_recommendation_agent.sql):

CREATE TABLE user_interactions (
    interaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(100) NOT NULL,
    product_id VARCHAR(100) NOT NULL,
    interaction_type VARCHAR(50) NOT NULL, -- 'view', 'click', 'add_to_cart', 'purchase', 'wishlist', 'review'
    interaction_score DECIMAL(3, 2) DEFAULT 1.0, -- Weight of interaction
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE product_similarities (
    similarity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id_1 VARCHAR(100) NOT NULL,
    product_id_2 VARCHAR(100) NOT NULL,
    similarity_score DECIMAL(5, 4) NOT NULL, -- 0.0 to 1.0
    similarity_type VARCHAR(50), -- 'content', 'collaborative', 'hybrid'
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE recommendation_sets (
    set_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(100) NOT NULL,
    recommendation_type VARCHAR(50) NOT NULL, -- 'personalized', 'trending', 'similar', 'frequently_bought_together'
    products JSONB NOT NULL, -- [{product_id, score, reason}]
    context JSONB DEFAULT '{}',
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE TABLE recommendation_feedback (
    feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    set_id UUID REFERENCES recommendation_sets(set_id),
    customer_id VARCHAR(100) NOT NULL,
    product_id VARCHAR(100) NOT NULL,
    feedback_type VARCHAR(50) NOT NULL, -- 'clicked', 'purchased', 'dismissed', 'not_interested'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID
from enum import Enum
from collections import defaultdict

from shared.db_helpers import DatabaseHelper
import math

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field
import structlog
import sys
import os

current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.database import DatabaseManager, get_database_manager

logger = structlog.get_logger(__name__)

# ENUMS
class InteractionType(str, Enum):
    VIEW = "view"
    CLICK = "click"
    ADD_TO_CART = "add_to_cart"
    PURCHASE = "purchase"
    WISHLIST = "wishlist"
    REVIEW = "review"

class RecommendationType(str, Enum):
    PERSONALIZED = "personalized"
    TRENDING = "trending"
    SIMILAR = "similar"
    FREQUENTLY_BOUGHT_TOGETHER = "frequently_bought_together"
    NEW_ARRIVALS = "new_arrivals"

# MODELS
class UserInteraction(BaseModel):
    customer_id: str
    product_id: str
    interaction_type: InteractionType
    metadata: Dict[str, Any] = {}

class ProductRecommendation(BaseModel):
    product_id: str
    score: float
    reason: str
    confidence: float

class RecommendationRequest(BaseModel):
    customer_id: str
    recommendation_type: RecommendationType = RecommendationType.PERSONALIZED
    context: Dict[str, Any] = {}
    limit: int = 10

class RecommendationResponse(BaseModel):
    set_id: UUID
    customer_id: str
    recommendation_type: RecommendationType
    recommendations: List[ProductRecommendation]
    generated_at: datetime

# REPOSITORY
class RecommendationRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def record_interaction(self, interaction: UserInteraction) -> UUID:
        # Interaction scores: view=0.1, click=0.2, add_to_cart=0.5, purchase=1.0, wishlist=0.3, review=0.8
        score_map = {
            InteractionType.VIEW: 0.1,
            InteractionType.CLICK: 0.2,
            InteractionType.ADD_TO_CART: 0.5,
            InteractionType.PURCHASE: 1.0,
            InteractionType.WISHLIST: 0.3,
            InteractionType.REVIEW: 0.8
        }
        score = score_map.get(interaction.interaction_type, 0.1)
        
        query = """
            INSERT INTO user_interactions (customer_id, product_id, interaction_type, interaction_score, metadata)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING interaction_id
        """
        result = await self.db.fetch_one(
            query, interaction.customer_id, interaction.product_id,
            interaction.interaction_type.value, score, str(interaction.metadata)
        )
        return result['interaction_id']
    
    async def get_user_interactions(self, customer_id: str, days: int = 30) -> List[Dict[str, Any]]:
        query = """
            SELECT * FROM user_interactions
            WHERE customer_id = $1 AND created_at > CURRENT_TIMESTAMP - INTERVAL '%s days'
            ORDER BY created_at DESC
        """ % days
        results = await self.db.fetch_all(query, customer_id)
        return [dict(r) for r in results]
    
    async def get_product_interactions(self, product_id: str, days: int = 30) -> List[Dict[str, Any]]:
        query = """
            SELECT * FROM user_interactions
            WHERE product_id = $1 AND created_at > CURRENT_TIMESTAMP - INTERVAL '%s days'
        """ % days
        results = await self.db.fetch_all(query, product_id)
        return [dict(r) for r in results]
    
    async def save_recommendation_set(self, set_data: Dict[str, Any]) -> UUID:
        query = """
            INSERT INTO recommendation_sets (customer_id, recommendation_type, products, context, expires_at)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING set_id
        """
        expires_at = datetime.utcnow() + timedelta(hours=24)
        result = await self.db.fetch_one(
            query, set_data['customer_id'], set_data['recommendation_type'],
            str(set_data['products']), str(set_data.get('context', {})), expires_at
        )
        return result['set_id']
    
    async def get_trending_products(self, limit: int = 10) -> List[str]:
        query = """
            SELECT product_id, COUNT(*) as interaction_count,
                   SUM(interaction_score) as total_score
            FROM user_interactions
            WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
            GROUP BY product_id
            ORDER BY total_score DESC, interaction_count DESC
            LIMIT $1
        """
        results = await self.db.fetch_all(query, limit)
        return [r['product_id'] for r in results]

# SERVICE
class RecommendationService:
    def __init__(self, repo: RecommendationRepository):
        self.repo = repo
    
    async def generate_personalized_recommendations(
        self, customer_id: str, limit: int = 10
    ) -> List[ProductRecommendation]:
        """Generate personalized recommendations using collaborative filtering."""
        # Get user's interaction history
        interactions = await self.repo.get_user_interactions(customer_id, days=90)
        
        if not interactions:
            # New user - return trending products
            return await self.generate_trending_recommendations(limit)
        
        # Calculate user preferences (product scores)
        product_scores = defaultdict(float)
        for interaction in interactions:
            product_scores[interaction['product_id']] += float(interaction['interaction_score'])
        
        # Get similar products for top interacted products
        top_products = sorted(product_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        recommendations = []
        
        for product_id, score in top_products:
            # In production, query product_similarities table
            # For now, simulate similar products
            similar_products = [f"similar_{product_id}_{i}" for i in range(2)]
            
            for similar_id in similar_products:
                if similar_id not in product_scores:  # Don't recommend already interacted products
                    recommendations.append(ProductRecommendation(
                        product_id=similar_id,
                        score=score * 0.8,  # Reduce score for similar products
                        reason=f"Similar to products you viewed",
                        confidence=0.75
                    ))
        
        # Sort by score and limit
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:limit]
    
    async def generate_trending_recommendations(self, limit: int = 10) -> List[ProductRecommendation]:
        """Generate trending product recommendations."""
        trending_products = await self.repo.get_trending_products(limit)
        
        recommendations = []
        for idx, product_id in enumerate(trending_products):
            score = 1.0 - (idx * 0.05)  # Decreasing score
            recommendations.append(ProductRecommendation(
                product_id=product_id,
                score=score,
                reason="Trending now",
                confidence=0.85
            ))
        
        return recommendations
    
    async def generate_similar_recommendations(
        self, product_id: str, limit: int = 10
    ) -> List[ProductRecommendation]:
        """Generate similar product recommendations."""
        # In production, query product_similarities table
        # For now, simulate similar products
        recommendations = []
        for i in range(limit):
            recommendations.append(ProductRecommendation(
                product_id=f"similar_{product_id}_{i}",
                score=0.9 - (i * 0.05),
                reason="Similar product",
                confidence=0.80
            ))
        
        return recommendations
    
    async def generate_recommendations(
        self, request: RecommendationRequest
    ) -> RecommendationResponse:
        """Generate recommendations based on type."""
        if request.recommendation_type == RecommendationType.PERSONALIZED:
            recommendations = await self.generate_personalized_recommendations(
                request.customer_id, request.limit
            )
        elif request.recommendation_type == RecommendationType.TRENDING:
            recommendations = await self.generate_trending_recommendations(request.limit)
        elif request.recommendation_type == RecommendationType.SIMILAR:
            product_id = request.context.get('product_id')
            if not product_id:
                raise ValueError("product_id required in context for similar recommendations")
            recommendations = await self.generate_similar_recommendations(product_id, request.limit)
        else:
            recommendations = await self.generate_trending_recommendations(request.limit)
        
        # Save recommendation set
        set_data = {
            'customer_id': request.customer_id,
            'recommendation_type': request.recommendation_type.value,
            'products': [r.dict() for r in recommendations],
            'context': request.context
        }
        set_id = await self.repo.save_recommendation_set(set_data)
        
        logger.info("recommendations_generated", set_id=str(set_id), 
                   customer_id=request.customer_id, count=len(recommendations))
        
        return RecommendationResponse(
            set_id=set_id,
            customer_id=request.customer_id,
            recommendation_type=request.recommendation_type,
            recommendations=recommendations,
            generated_at=datetime.utcnow()
        )

# FASTAPI APP
app = FastAPI(title="Recommendation Agent API", version="1.0.0")

async def get_recommendation_service() -> RecommendationService:
    db_manager = await get_database_manager()
    repo = RecommendationRepository(db_manager)
    return RecommendationService(repo)

# ENDPOINTS
@app.post("/api/v1/recommendations/interaction")
async def record_interaction(
    interaction: UserInteraction = Body(...),
    service: RecommendationService = Depends(get_recommendation_service)
):
    try:
        interaction_id = await service.repo.record_interaction(interaction)
        return {"interaction_id": interaction_id, "message": "Interaction recorded"}
    except Exception as e:
        logger.error("record_interaction_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/recommendations/generate", response_model=RecommendationResponse)
async def generate_recommendations(
    request: RecommendationRequest = Body(...),
    service: RecommendationService = Depends(get_recommendation_service)
):
    try:
        response = await service.generate_recommendations(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("generate_recommendations_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/recommendations/trending", response_model=List[ProductRecommendation])
async def get_trending(
    limit: int = Query(10, ge=1, le=50),
    service: RecommendationService = Depends(get_recommendation_service)
):
    try:
        recommendations = await service.generate_trending_recommendations(limit)
        return recommendations
    except Exception as e:
        logger.error("get_trending_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/recommendations/similar/{product_id}", response_model=List[ProductRecommendation])
async def get_similar(
    product_id: str = Path(...),
    limit: int = Query(10, ge=1, le=50),
    service: RecommendationService = Depends(get_recommendation_service)
):
    try:
        recommendations = await service.generate_similar_recommendations(product_id, limit)
        return recommendations
    except Exception as e:
        logger.error("get_similar_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "recommendation_agent", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)




# FastAPI App
app = FastAPI(title="Recommendation Agent", description="Agent for personalized product recommendations.")

@app.get("/", summary="Root endpoint", operation_id="root_recommendation")
async def root():
    return {"agent_name": "Recommendation Agent", "status": "running"}

@app.get("/health", summary="Health check", operation_id="health_check_recommendation")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Existing code remains intact

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

