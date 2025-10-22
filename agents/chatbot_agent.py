"""
Chatbot Agent - Multi-Agent E-Commerce System

This agent provides AI-powered customer service with Natural Language Understanding (NLU),
intent classification, entity extraction, conversation management, and integration with
other agents for order tracking, product search, and support ticket creation.

DATABASE SCHEMA (migration 020_chatbot_agent.sql):

CREATE TABLE chat_conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(100),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    channel VARCHAR(50), -- 'web', 'mobile', 'whatsapp', 'messenger'
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'ended', 'transferred'
    metadata JSONB
);

CREATE TABLE chat_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES chat_conversations(conversation_id),
    sender_type VARCHAR(20) NOT NULL, -- 'customer', 'bot', 'agent'
    message_text TEXT NOT NULL,
    intent VARCHAR(100), -- 'order_status', 'product_search', 'support', 'faq', 'greeting'
    entities JSONB, -- Extracted entities like order_id, product_name, etc.
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chat_intents (
    intent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    intent_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    training_phrases JSONB, -- Array of example phrases
    response_templates JSONB, -- Array of response templates
    requires_entities JSONB, -- Required entity types
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE chat_entities (
    entity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(100) NOT NULL, -- 'order_id', 'product_name', 'date', 'email'
    entity_value TEXT NOT NULL,
    normalized_value TEXT,
    message_id UUID REFERENCES chat_messages(message_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chat_escalations (
    escalation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES chat_conversations(conversation_id),
    reason VARCHAR(255),
    escalated_to VARCHAR(100), -- Agent ID or queue name
    escalated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chat_feedback (
    feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES chat_conversations(conversation_id),
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    feedback_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID
from enum import Enum

from shared.db_helpers import DatabaseHelper
import re

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
class SenderType(str, Enum):
    CUSTOMER = "customer"
    BOT = "bot"
    AGENT = "agent"
    async def initialize(self):
        """Initialize agent."""
        await super().initialize()
        
    async def cleanup(self):
        """Cleanup agent."""
        await super().cleanup()
        
    async def process_business_logic(self, data):
        """Process business logic."""
        return {"status": "success"}


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    ENDED = "ended"
    TRANSFERRED = "transferred"

# MODELS
class ConversationCreate(BaseModel):
    customer_id: Optional[str] = None
    channel: str = "web"
    metadata: Optional[Dict[str, Any]] = None

class Conversation(BaseModel):
    conversation_id: UUID
    customer_id: Optional[str]
    session_id: str
    channel: str
    started_at: datetime
    status: ConversationStatus

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    conversation_id: UUID
    message_text: str
    sender_type: SenderType = SenderType.CUSTOMER

class ChatMessage(BaseModel):
    message_id: UUID
    conversation_id: UUID
    sender_type: SenderType
    message_text: str
    intent: Optional[str]
    confidence_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    message_id: UUID
    response_text: str
    intent: Optional[str]
    confidence_score: Optional[float]
    suggested_actions: Optional[List[str]] = None

class FeedbackCreate(BaseModel):
    conversation_id: UUID
    rating: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = None

# NLU ENGINE (Simplified AI/ML-based intent classification)
class NLUEngine:
    """Simplified NLU engine with pattern-based intent classification."""
    
    def __init__(self):
        self.intent_patterns = {
            "order_status": [
                r"where.*order",
                r"track.*order",
                r"order.*status",
                r"order.*[0-9]+",
                r"my order"
            ],
            "product_search": [
                r"looking for",
                r"search.*product",
                r"find.*product",
                r"show me",
                r"available.*product"
            ],
            "support": [
                r"help",
                r"problem",
                r"issue",
                r"not working",
                r"complaint"
            ],
            "greeting": [
                r"^hi$",
                r"^hello$",
                r"^hey$",
                r"good morning",
                r"good afternoon"
            ],
            "faq": [
                r"how.*return",
                r"shipping.*cost",
                r"delivery.*time",
                r"payment.*method",
                r"refund"
            ]
        }
    
    def classify_intent(self, text: str) -> tuple[str, float]:
        """Classify intent with confidence score."""
        text_lower = text.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    # Simulate confidence score based on pattern match quality
                    confidence = 0.85 if len(pattern) > 10 else 0.75
                    return intent, confidence
        
        return "unknown", 0.50
    
    def extract_entities(self, text: str, intent: str) -> Dict[str, str]:
        """Extract entities based on intent."""
        entities = {}
        
        # Extract order ID
        order_match = re.search(r'order[:\s#]*([A-Z0-9-]+)', text, re.IGNORECASE)
        if order_match:
            entities['order_id'] = order_match.group(1)
        
        # Extract email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if email_match:
            entities['email'] = email_match.group(0)
        
        # Extract product name (simplified)
        if intent == "product_search":
            # Extract words after "for" or "find"
            product_match = re.search(r'(?:for|find)\s+(.+?)(?:\s+please|$)', text, re.IGNORECASE)
            if product_match:
                entities['product_name'] = product_match.group(1).strip()
        
        return entities
    
    def generate_response(self, intent: str, entities: Dict[str, str]) -> str:
        """Generate response based on intent and entities."""
        responses = {
            "greeting": "Hello! I'm here to help you. How can I assist you today?",
            "order_status": "I can help you track your order. " + 
                          (f"Let me check the status of order {entities.get('order_id', '')}." 
                           if 'order_id' in entities 
                           else "Could you please provide your order number?"),
            "product_search": "I'll help you find the product you're looking for. " +
                            (f"Searching for {entities.get('product_name', '')}..." 
                             if 'product_name' in entities 
                             else "What product are you interested in?"),
            "support": "I understand you need assistance. I can create a support ticket for you, or would you like to speak with a human agent?",
            "faq": "I can answer common questions about returns, shipping, and payments. What would you like to know?",
            "unknown": "I'm not sure I understood that correctly. Could you please rephrase your question?"
        }
        
        return responses.get(intent, responses["unknown"])

# REPOSITORY
class ChatbotRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_conversation(self, conv_data: ConversationCreate) -> Conversation:
        """Create new conversation."""
        session_id = f"CHAT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
        
        query = """
            INSERT INTO chat_conversations (customer_id, session_id, channel, metadata)
            VALUES ($1, $2, $3, $4)
            RETURNING *
        """
        result = await self.db.fetch_one(
            query, conv_data.customer_id, session_id, conv_data.channel,
            str(conv_data.metadata) if conv_data.metadata else None
        )
        return Conversation(**result)
    
    async def save_message(
        self, message_data: MessageCreate, intent: str,
        confidence: float, entities: Dict[str, str]
    ) -> UUID:
        """Save chat message."""
        query = """
            INSERT INTO chat_messages (conversation_id, sender_type, message_text,
                                      intent, entities, confidence_score)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING message_id
        """
        result = await self.db.fetch_one(
            query, message_data.conversation_id, message_data.sender_type.value,
            message_data.message_text, intent, str(entities), confidence
        )
        
        # Save entities
        message_id = result['message_id']
        for entity_type, entity_value in entities.items():
            await self._save_entity(message_id, entity_type, entity_value)
        
        return message_id
    
    async def _save_entity(self, message_id: UUID, entity_type: str, entity_value: str) -> None:
        """Save extracted entity."""
        query = """
            INSERT INTO chat_entities (message_id, entity_type, entity_value, normalized_value)
            VALUES ($1, $2, $3, $4)
        """
        await self.db.execute(query, message_id, entity_type, entity_value, entity_value)
    
    async def get_conversation_messages(self, conversation_id: UUID) -> List[ChatMessage]:
        """Get all messages in conversation."""
        query = """
            SELECT * FROM chat_messages
            WHERE conversation_id = $1
            ORDER BY created_at ASC
        """
        results = await self.db.fetch_all(query, conversation_id)
        return [ChatMessage(**r) for r in results]
    
    async def end_conversation(self, conversation_id: UUID) -> None:
        """End conversation."""
        query = """
            UPDATE chat_conversations
            SET status = 'ended', ended_at = CURRENT_TIMESTAMP
            WHERE conversation_id = $1
        """
        await self.db.execute(query, conversation_id)
    
    async def escalate_conversation(
        self, conversation_id: UUID, reason: str, escalated_to: str
    ) -> UUID:
        """Escalate conversation to human agent."""
        query = """
            INSERT INTO chat_escalations (conversation_id, reason, escalated_to)
            VALUES ($1, $2, $3)
            RETURNING escalation_id
        """
        result = await self.db.fetch_one(query, conversation_id, reason, escalated_to)
        
        # Update conversation status
        update_query = """
            UPDATE chat_conversations
            SET status = 'transferred'
            WHERE conversation_id = $1
        """
        await self.db.execute(update_query, conversation_id)
        
        return result['escalation_id']
    
    async def save_feedback(self, feedback_data: FeedbackCreate) -> UUID:
        """Save conversation feedback."""
        query = """
            INSERT INTO chat_feedback (conversation_id, rating, feedback_text)
            VALUES ($1, $2, $3)
            RETURNING feedback_id
        """
        result = await self.db.fetch_one(
            query, feedback_data.conversation_id, feedback_data.rating,
            feedback_data.feedback_text
        )
        return result['feedback_id']

# SERVICE
class ChatbotService:
    def __init__(self, repo: ChatbotRepository):
        self.repo = repo
        self.nlu_engine = NLUEngine()
    
    async def create_conversation(self, conv_data: ConversationCreate) -> Conversation:
        """Create new conversation."""
        conversation = await self.repo.create_conversation(conv_data)
        
        logger.info("conversation_created", conversation_id=str(conversation.conversation_id),
                   channel=conversation.channel)
        
        return conversation
    
    async def process_message(self, message_data: MessageCreate) -> ChatResponse:
        """Process customer message with NLU."""
        # Classify intent
        intent, confidence = self.nlu_engine.classify_intent(message_data.message_text)
        
        # Extract entities
        entities = self.nlu_engine.extract_entities(message_data.message_text, intent)
        
        # Save customer message
        message_id = await self.repo.save_message(message_data, intent, confidence, entities)
        
        # Generate response
        response_text = self.nlu_engine.generate_response(intent, entities)
        
        # Save bot response
        bot_message = MessageCreate(
            conversation_id=message_data.conversation_id,
            message_text=response_text,
            sender_type=SenderType.BOT
        )
        bot_message_id = await self.repo.save_message(bot_message, intent, confidence, {})
        
        logger.info("message_processed", message_id=str(message_id),
                   intent=intent, confidence=confidence)
        
        # Generate suggested actions
        suggested_actions = self._get_suggested_actions(intent)
        
        return ChatResponse(
            message_id=bot_message_id,
            response_text=response_text,
            intent=intent,
            confidence_score=confidence,
            suggested_actions=suggested_actions
        )
    
    def _get_suggested_actions(self, intent: str) -> List[str]:
        """Get suggested actions based on intent."""
        actions = {
            "order_status": ["Track Order", "Contact Support"],
            "product_search": ["View Products", "Filter by Category"],
            "support": ["Create Ticket", "Talk to Agent"],
            "faq": ["View FAQs", "Search Knowledge Base"],
            "greeting": ["Browse Products", "Check Orders"]
        }
        return actions.get(intent, [])

# FASTAPI APP
app = FastAPI(title="Chatbot Agent API", version="1.0.0")

async def get_chatbot_service() -> ChatbotService:
    db_manager = await get_database_manager()
    repo = ChatbotRepository(db_manager)
    return ChatbotService(repo)

# ENDPOINTS
@app.post("/api/v1/chatbot/conversations", response_model=Conversation)
async def create_conversation(
    conv_data: ConversationCreate = Body(...),
    service: ChatbotService = Depends(get_chatbot_service)
):
    try:
        conversation = await service.create_conversation(conv_data)
        return conversation
    except Exception as e:
        logger.error("create_conversation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chatbot/messages", response_model=ChatResponse)
async def send_message(
    message_data: MessageCreate = Body(...),
    service: ChatbotService = Depends(get_chatbot_service)
):
    try:
        response = await service.process_message(message_data)
        return response
    except Exception as e:
        logger.error("send_message_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/chatbot/conversations/{conversation_id}/messages", response_model=List[ChatMessage])
async def get_conversation_messages(
    conversation_id: UUID = Path(...),
    service: ChatbotService = Depends(get_chatbot_service)
):
    try:
        messages = await service.repo.get_conversation_messages(conversation_id)
        return messages
    except Exception as e:
        logger.error("get_conversation_messages_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chatbot/conversations/{conversation_id}/end")
async def end_conversation(
    conversation_id: UUID = Path(...),
    service: ChatbotService = Depends(get_chatbot_service)
):
    try:
        await service.repo.end_conversation(conversation_id)
        return {"message": "Conversation ended successfully"}
    except Exception as e:
        logger.error("end_conversation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chatbot/conversations/{conversation_id}/escalate")
async def escalate_conversation(
    conversation_id: UUID = Path(...),
    reason: str = Body(..., embed=True),
    escalated_to: str = Body(..., embed=True),
    service: ChatbotService = Depends(get_chatbot_service)
):
    try:
        escalation_id = await service.repo.escalate_conversation(
            conversation_id, reason, escalated_to
        )
        return {"escalation_id": escalation_id, "message": "Conversation escalated successfully"}
    except Exception as e:
        logger.error("escalate_conversation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chatbot/feedback")
async def submit_feedback(
    feedback_data: FeedbackCreate = Body(...),
    service: ChatbotService = Depends(get_chatbot_service)
):
    try:
        feedback_id = await service.repo.save_feedback(feedback_data)
        return {"feedback_id": feedback_id, "message": "Feedback submitted successfully"}
    except Exception as e:
        logger.error("submit_feedback_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "chatbot_agent", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8019)

