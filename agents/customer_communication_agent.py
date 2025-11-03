from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
"""
Customer Communication Agent - Multi-Agent E-commerce System

This agent provides comprehensive customer communication including:
- AI-powered chatbot for real-time customer support
- Automated email campaigns and transactional emails
- Multi-channel communication management
- Customer sentiment analysis and escalation
- Personalized messaging and recommendations
"""

import asyncio
import json
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

from shared.db_helpers import DatabaseHelper

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, EmailStr
import structlog
import sys
import os

# Get the absolute path of the current file
current_file_path = os.path.abspath(__file__)

# Get the directory containing the current file
current_dir = os.path.dirname(current_file_path)

# Get the parent directory (project root)
project_root = os.path.dirname(current_dir)

# Add the project root to the Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logger.info(f"Added {project_root} to Python path")

# Now try the import
try:
    from shared.openai_helper import chat_completion
    from shared.base_agent_v2 import BaseAgentV2, MessageType, AgentMessage
    logger.info("Successfully imported shared.base_agent")
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.info(f"Current sys.path: {sys.path}")
    
    # List files in the shared directory to verify it exists
    shared_dir = os.path.join(project_root, "shared")
    if os.path.exists(shared_dir):
        logger.info(f"Contents of {shared_dir}:")
        for item in os.listdir(shared_dir):
            logger.info(f"  - {item}")
    else:
        logger.info(f"Directory not found: {shared_dir}")

from shared.base_agent_v2 import BaseAgentV2, MessageType, AgentMessage
from shared.models import APIResponse
from shared.database import DatabaseManager, get_database_manager


logger = structlog.get_logger(__name__)


class ChatMessage(BaseModel):
    """Model for chat messages."""
    message_id: str
    session_id: str
    customer_id: Optional[str] = None
    message: str
    sender: str  # "customer", "agent", "bot"
    timestamp: datetime
    sentiment: Optional[str] = None  # "positive", "neutral", "negative"
    intent: Optional[str] = None  # "order_status", "return", "complaint", etc.
    resolved: bool = False


class EmailTemplate(BaseModel):
    """Model for email templates."""
    template_id: str
    name: str
    subject: str
    html_content: str
    text_content: str
    template_type: str  # "transactional", "marketing", "notification"
    variables: List[str]  # List of template variables
    active: bool = True


class EmailCampaign(BaseModel):
    """Model for email campaigns."""
    campaign_id: str
    name: str
    template_id: str
    target_audience: Dict[str, Any]  # Criteria for targeting
    schedule_type: str  # "immediate", "scheduled", "triggered"
    scheduled_time: Optional[datetime] = None
    trigger_event: Optional[str] = None
    status: str = "draft"  # "draft", "active", "paused", "completed"
    created_at: datetime


class CustomerInteraction(BaseModel):
    """Model for customer interaction tracking."""
    interaction_id: str
    customer_id: str
    channel: str  # "chat", "email", "phone"
    interaction_type: str  # "support", "sales", "complaint"
    subject: str
    status: str  # "open", "in_progress", "resolved", "escalated"
    priority: str  # "low", "medium", "high", "urgent"
    assigned_agent: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolution_time: Optional[int] = None  # minutes


class ChatbotResponse(BaseModel):
    """Model for chatbot responses."""
    response: str
    intent: str
    confidence: float
    suggested_actions: List[str]
    escalate_to_human: bool
    context_data: Dict[str, Any]


class CustomerCommunicationAgent(BaseAgentV2):
    """
    Customer Communication Agent provides comprehensive communication services including:
    - AI-powered chatbot for instant customer support
    - Email automation and campaign management
    - Multi-channel interaction tracking
    - Sentiment analysis and escalation management
    - Personalized customer messaging
    """
    
    def __init__(self, **kwargs):
        super().__init__(agent_id="customer_communication_agent", **kwargs)
        
        self.setup_routes()
        # OpenAI client is initialized in openai_helper
        # Communication data
        self.active_chat_sessions: Dict[str, Dict[str, Any]] = {}
        self.email_templates: Dict[str, EmailTemplate] = {}
        self.active_campaigns: Dict[str, EmailCampaign] = {}
        self.customer_interactions: Dict[str, CustomerInteraction] = {}
        
        # WebSocket connections for real-time chat
        self.websocket_connections: Dict[str, WebSocket] = {}
        
        # Register message handlers
        self.register_handler(MessageType.ORDER_CREATED, self._handle_order_created)
        self.register_handler(MessageType.ORDER_UPDATED, self._handle_order_updated)
        self.register_handler(MessageType.RETURN_REQUESTED, self._handle_return_requested)
    
    async def initialize(self):
        await super().initialize()

        """Initialize the Customer Communication Agent."""
        self.logger.info("Initializing Customer Communication Agent")
        
        # Initialize email templates
        await self._initialize_email_templates()
        
        # Initialize chatbot knowledge base
        await self._initialize_chatbot_knowledge()
        
        # Start background tasks
        asyncio.create_task(self._process_email_campaigns())
        asyncio.create_task(self._monitor_interaction_metrics())
        asyncio.create_task(self._cleanup_old_sessions())
        
        self.logger.info("Customer Communication Agent initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up Customer Communication Agent")
        
        # Close all WebSocket connections
        for session_id, websocket in self.websocket_connections.items():
            try:
                await websocket.close()
            except:
                pass
        await super().cleanup()

    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process customer communication business logic."""
        action = data.get("action")
        
        if action == "send_chat_message":
            return await self._process_chat_message(data["message"], data["session_id"])
        elif action == "send_email":
            return await self._send_email(data["email_data"])
        elif action == "create_campaign":
            return await self._create_email_campaign(data["campaign_data"])
        elif action == "get_customer_interactions":
            return await self._get_customer_interactions(data.get("customer_id"))
        elif action == "escalate_interaction":
            return await self._escalate_interaction(data["interaction_id"])
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def setup_routes(self):
        """Setup FastAPI routes for the Customer Communication Agent."""
        
        @app.websocket("/chat/{session_id}")
        async def websocket_chat(websocket: WebSocket, session_id: str):
            """WebSocket endpoint for real-time chat."""
            await websocket.accept()
            self.websocket_connections[session_id] = websocket
            
            try:
                # Initialize chat session
                if session_id not in self.active_chat_sessions:
                    self.active_chat_sessions[session_id] = {
                        "session_id": session_id,
                        "customer_id": None,
                        "messages": [],
                        "context": {},
                        "created_at": datetime.utcnow(),
                        "last_activity": datetime.utcnow()
                    }
                
                # Send welcome message
                welcome_response = await self._generate_welcome_message(session_id)
                await websocket.send_text(json.dumps(welcome_response))
                
                while True:
                    # Receive message from client
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    # Process the message
                    response = await self._process_chat_message(
                        message_data["message"], 
                        session_id,
                        message_data.get("customer_id")
                    )
                    
                    # Send response back to client
                    await websocket.send_text(json.dumps(response))
            
            except WebSocketDisconnect:
                self.logger.info("WebSocket disconnected", session_id=session_id)
            except Exception as e:
                self.logger.error("WebSocket error", error=str(e), session_id=session_id)
            finally:
                # Cleanup
                if session_id in self.websocket_connections:
                    del self.websocket_connections[session_id]
        
        @app.post("/chat/message", response_model=APIResponse)
        async def send_chat_message(message: str, session_id: str, customer_id: Optional[str] = None):
            """Send a chat message (REST API alternative to WebSocket)."""
            try:
                result = await self._process_chat_message(message, session_id, customer_id)
                
                return APIResponse(
                    success=True,
                    message="Chat message processed successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to process chat message", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/email/send", response_model=APIResponse)
        async def send_email(email_data: Dict[str, Any]):
            """Send an email."""
            try:
                result = await self._send_email(email_data)
                
                return APIResponse(
                    success=True,
                    message="Email sent successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to send email", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/campaigns", response_model=APIResponse)
        async def create_campaign(campaign_data: EmailCampaign):
            """Create an email campaign."""
            try:
                result = await self._create_email_campaign(campaign_data.dict())
                
                return APIResponse(
                    success=True,
                    message="Email campaign created successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to create email campaign", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/interactions", response_model=APIResponse)
        async def get_customer_interactions(customer_id: Optional[str] = None):
            """Get customer interactions."""
            try:
                result = await self._get_customer_interactions(customer_id)
                
                return APIResponse(
                    success=True,
                    message="Customer interactions retrieved successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to get customer interactions", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/interactions/{interaction_id}/escalate", response_model=APIResponse)
        async def escalate_interaction(interaction_id: str):
            """Escalate an interaction to human agent."""
            try:
                result = await self._escalate_interaction(interaction_id)
                
                return APIResponse(
                    success=True,
                    message="Interaction escalated successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to escalate interaction", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/templates", response_model=APIResponse)
        async def list_email_templates():
            """List all email templates."""
            try:
                templates = [template.dict() for template in self.email_templates.values()]
                
                return APIResponse(
                    success=True,
                    message="Email templates retrieved successfully",
                    data={"templates": templates}
                )
            
            except Exception as e:
                self.logger.error("Failed to list email templates", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/campaigns", response_model=APIResponse)
        async def list_campaigns():
            """List all email campaigns."""
            try:
                campaigns = [campaign.dict() for campaign in self.active_campaigns.values()]
                
                return APIResponse(
                    success=True,
                    message="Email campaigns retrieved successfully",
                    data={"campaigns": campaigns}
                )
            
            except Exception as e:
                self.logger.error("Failed to list email campaigns", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _process_chat_message(self, message: str, session_id: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
        """Process incoming chat message and generate response."""
        try:
            # Update session
            if session_id not in self.active_chat_sessions:
                self.active_chat_sessions[session_id] = {
                    "session_id": session_id,
                    "customer_id": customer_id,
                    "messages": [],
                    "context": {},
                    "created_at": datetime.utcnow(),
                    "last_activity": datetime.utcnow()
                }
            
            session = self.active_chat_sessions[session_id]
            session["last_activity"] = datetime.utcnow()
            
            if customer_id:
                session["customer_id"] = customer_id
            
            # Create message record
            chat_message = ChatMessage(
                message_id=str(uuid4()),
                session_id=session_id,
                customer_id=customer_id,
                message=message,
                sender="customer",
                timestamp=datetime.utcnow()
            )
            
            # Analyze message sentiment and intent
            sentiment, intent = await self._analyze_message(message)
            chat_message.sentiment = sentiment
            chat_message.intent = intent
            
            # Add to session history
            session["messages"].append(chat_message.dict())
            
            # Generate AI response
            bot_response = await self._generate_chatbot_response(message, session, intent)
            
            # Create response message
            response_message = ChatMessage(
                message_id=str(uuid4()),
                session_id=session_id,
                customer_id=customer_id,
                message=bot_response.response,
                sender="bot",
                timestamp=datetime.utcnow(),
                intent=bot_response.intent
            )
            
            session["messages"].append(response_message.dict())
            
            # Check if escalation is needed
            if bot_response.escalate_to_human or sentiment == "negative":
                await self._create_interaction_for_escalation(session_id, customer_id, message, intent)
            
            # Update context
            session["context"].update(bot_response.context_data)
            
            return {
                "message_id": response_message.message_id,
                "response": bot_response.response,
                "intent": bot_response.intent,
                "confidence": bot_response.confidence,
                "suggested_actions": bot_response.suggested_actions,
                "escalated": bot_response.escalate_to_human,
                "sentiment": sentiment,
                "timestamp": response_message.timestamp.isoformat()
            }
        
        except Exception as e:
            self.logger.error("Failed to process chat message", error=str(e), session_id=session_id)
            
            # Return error response
            return {
                "message_id": str(uuid4()),
                "response": "I apologize, but I'm experiencing technical difficulties. Please try again or contact our support team.",
                "intent": "error",
                "confidence": 0.0,
                "suggested_actions": ["contact_support"],
                "escalated": True,
                "sentiment": "neutral",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _analyze_message(self, message: str) -> Tuple[str, str]:
        """Analyze message sentiment and intent."""
        try:
            if not os.getenv("OPENAI_API_KEY"):
                # Fallback analysis
                return self._simple_sentiment_analysis(message), self._simple_intent_detection(message)
            
            # Use AI for analysis
            prompt = f"""
            Analyze the following customer message for sentiment and intent:
            
            Message: "{message}"
            
            Respond with JSON format:
            {{
                "sentiment": "positive|neutral|negative",
                "intent": "order_status|return|complaint|product_info|shipping|payment|general"
            }}
            """
            
            response = await chat_completion(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert customer service analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            content = response["choices"][0]["message"]["content"]
            analysis = json.loads(content)
            
            return analysis.get("sentiment", "neutral"), analysis.get("intent", "general")
        
        except Exception as e:
            self.logger.error("Failed to analyze message", error=str(e))
            return "neutral", "general"
    
    def _simple_sentiment_analysis(self, message: str) -> str:
        """Simple rule-based sentiment analysis."""
        message_lower = message.lower()
        
        negative_words = ["angry", "frustrated", "terrible", "awful", "hate", "worst", "problem", "issue", "broken", "defective"]
        positive_words = ["great", "excellent", "love", "amazing", "perfect", "thank", "happy", "satisfied"]
        
        negative_count = sum(1 for word in negative_words if word in message_lower)
        positive_count = sum(1 for word in positive_words if word in message_lower)
        
        if negative_count > positive_count:
            return "negative"
        elif positive_count > negative_count:
            return "positive"
        else:
            return "neutral"
    
    def _simple_intent_detection(self, message: str) -> str:
        """Simple rule-based intent detection."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["order", "status", "tracking", "delivery"]):
            return "order_status"
        elif any(word in message_lower for word in ["return", "refund", "exchange"]):
            return "return"
        elif any(word in message_lower for word in ["complaint", "problem", "issue", "wrong"]):
            return "complaint"
        elif any(word in message_lower for word in ["product", "item", "specification", "feature"]):
            return "product_info"
        elif any(word in message_lower for word in ["shipping", "delivery", "carrier"]):
            return "shipping"
        elif any(word in message_lower for word in ["payment", "billing", "charge", "card"]):
            return "payment"
        else:
            return "general"
    
    async def _generate_chatbot_response(self, message: str, session: Dict[str, Any], intent: str) -> ChatbotResponse:
        """Generate AI-powered chatbot response."""
        try:
            if not os.getenv("OPENAI_API_KEY"):
                return self._generate_rule_based_response(message, intent)
            
            # Prepare context from session history
            context = self._prepare_conversation_context(session)
            
            # Create AI prompt
            prompt = f"""
            You are a helpful customer service chatbot for an e-commerce platform. Respond to the customer's message professionally and helpfully.
            
            Customer Intent: {intent}
            Conversation Context: {context}
            Customer Message: "{message}"
            
            Guidelines:
            - Be friendly, professional, and helpful
            - Provide specific information when possible
            - If you cannot help, suggest escalation to human agent
            - Keep responses concise but informative
            - Suggest relevant actions the customer can take
            
            Respond in JSON format:
            {{
                "response": "Your helpful response here",
                "confidence": 0.85,
                "suggested_actions": ["action1", "action2"],
                "escalate_to_human": false,
                "context_data": {{"key": "value"}}
            }}
            """
            
            response = await chat_completion(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional customer service chatbot."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            content = response["choices"][0]["message"]["content"]
            ai_response = json.loads(content)
            
            return ChatbotResponse(
                response=ai_response.get("response", "I'm here to help! How can I assist you today?"),
                intent=intent,
                confidence=ai_response.get("confidence", 0.7),
                suggested_actions=ai_response.get("suggested_actions", []),
                escalate_to_human=ai_response.get("escalate_to_human", False),
                context_data=ai_response.get("context_data", {})
            )
        
        except Exception as e:
            self.logger.error("Failed to generate AI chatbot response", error=str(e))
            return self._generate_rule_based_response(message, intent)
    
    def _generate_rule_based_response(self, message: str, intent: str) -> ChatbotResponse:
        """Generate rule-based chatbot response as fallback."""
        responses = {
            "order_status": {
                "response": "I can help you check your order status. Could you please provide your order number?",
                "actions": ["provide_order_number", "check_email"]
            },
            "return": {
                "response": "I'd be happy to help you with your return. What item would you like to return and what's the reason?",
                "actions": ["start_return_process", "check_return_policy"]
            },
            "complaint": {
                "response": "I'm sorry to hear you're experiencing an issue. Let me connect you with a specialist who can help resolve this.",
                "actions": ["escalate_to_human", "provide_details"]
            },
            "product_info": {
                "response": "I can help you find product information. What specific details are you looking for?",
                "actions": ["search_products", "view_specifications"]
            },
            "shipping": {
                "response": "I can help with shipping questions. Are you asking about delivery times, tracking, or shipping options?",
                "actions": ["track_shipment", "view_shipping_options"]
            },
            "payment": {
                "response": "I can assist with payment-related questions. Are you having trouble with a payment or need billing information?",
                "actions": ["check_payment_status", "update_payment_method"]
            },
            "general": {
                "response": "Hello! I'm here to help you with any questions about your orders, returns, or our products. How can I assist you today?",
                "actions": ["browse_help", "contact_support"]
            }
        }
        
        response_data = responses.get(intent, responses["general"])
        
        return ChatbotResponse(
            response=response_data["response"],
            intent=intent,
            confidence=0.6,
            suggested_actions=response_data["actions"],
            escalate_to_human=intent == "complaint",
            context_data={"intent": intent}
        )
    
    def _prepare_conversation_context(self, session: Dict[str, Any]) -> str:
        """Prepare conversation context for AI."""
        messages = session.get("messages", [])
        context_messages = messages[-5:]  # Last 5 messages for context
        
        context_parts = []
        for msg in context_messages:
            sender = msg["sender"]
            content = msg["message"]
            context_parts.append(f"{sender}: {content}")
        
        return " | ".join(context_parts) if context_parts else "No previous context"
    
    async def _generate_welcome_message(self, session_id: str) -> Dict[str, Any]:
        """Generate welcome message for new chat sessions."""
        return {
            "message_id": str(uuid4()),
            "response": "Hello! Welcome to our customer support. I'm here to help you with any questions about your orders, returns, or products. How can I assist you today?",
            "intent": "welcome",
            "confidence": 1.0,
            "suggested_actions": ["check_order_status", "start_return", "browse_products", "contact_human"],
            "escalated": False,
            "sentiment": "positive",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _create_interaction_for_escalation(self, session_id: str, customer_id: Optional[str], message: str, intent: str):
        """Create customer interaction record for escalation."""
        try:
            interaction = CustomerInteraction(
                interaction_id=str(uuid4()),
                customer_id=customer_id or f"session_{session_id}",
                channel="chat",
                interaction_type="support",
                subject=f"Chat escalation - {intent}",
                status="open",
                priority="medium" if intent != "complaint" else "high",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.customer_interactions[interaction.interaction_id] = interaction
            
            # Send escalation notification
            await self.send_message(
                recipient_agent="monitoring_agent",
                message_type=MessageType.ESCALATION_REQUIRED,
                payload={
                    "interaction_id": interaction.interaction_id,
                    "customer_id": customer_id,
                    "session_id": session_id,
                    "intent": intent,
                    "message": message,
                    "priority": interaction.priority
                }
            )
        
        except Exception as e:
            self.logger.error("Failed to create interaction for escalation", error=str(e))
    
    async def _send_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send an email using template or custom content."""
        try:
            recipient = email_data["recipient"]
            subject = email_data.get("subject", "")
            template_id = email_data.get("template_id")
            custom_content = email_data.get("content")
            variables = email_data.get("variables", {})
            
            # Prepare email content
            if template_id and template_id in self.email_templates:
                template = self.email_templates[template_id]
                subject = template.subject
                html_content = template.html_content
                text_content = template.text_content
                
                # Replace template variables
                for var, value in variables.items():
                    placeholder = f"{{{{{var}}}}}"
                    subject = subject.replace(placeholder, str(value))
                    html_content = html_content.replace(placeholder, str(value))
                    text_content = text_content.replace(placeholder, str(value))
            
            elif custom_content:
                html_content = custom_content.get("html", "")
                text_content = custom_content.get("text", "")
            
            else:
                raise ValueError("Either template_id or custom_content must be provided")
            
            # Send email (simulated - in production, use actual email service)
            email_id = str(uuid4())
            
            # In production, this would use services like SendGrid, AWS SES, etc.
            self.logger.info("Email sent", 
                           email_id=email_id,
                           recipient=recipient,
                           subject=subject,
                           template_id=template_id)
            
            return {
                "email_id": email_id,
                "recipient": recipient,
                "subject": subject,
                "status": "sent",
                "sent_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error("Failed to send email", error=str(e))
            raise
    
    async def _create_email_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create and manage email campaigns."""
        try:
            campaign = EmailCampaign(
                campaign_id=str(uuid4()),
                name=campaign_data["name"],
                template_id=campaign_data["template_id"],
                target_audience=campaign_data.get("target_audience", {}),
                schedule_type=campaign_data.get("schedule_type", "immediate"),
                scheduled_time=datetime.fromisoformat(campaign_data["scheduled_time"]) if campaign_data.get("scheduled_time") else None,
                trigger_event=campaign_data.get("trigger_event"),
                status="active" if campaign_data.get("schedule_type") == "immediate" else "scheduled",
                created_at=datetime.utcnow()
            )
            
            self.active_campaigns[campaign.campaign_id] = campaign
            
            # If immediate campaign, start sending
            if campaign.schedule_type == "immediate":
                asyncio.create_task(self._execute_campaign(campaign.campaign_id))
            
            return campaign.dict()
        
        except Exception as e:
            self.logger.error("Failed to create email campaign", error=str(e))
            raise
    
    async def _execute_campaign(self, campaign_id: str):
        """Execute an email campaign."""
        try:
            campaign = self.active_campaigns.get(campaign_id)
            if not campaign:
                return
            
            # Get target audience (simulated)
            target_customers = await self._get_campaign_audience(campaign.target_audience)
            
            sent_count = 0
            failed_count = 0
            
            for customer in target_customers:
                try:
                    # Send email to customer
                    email_data = {
                        "recipient": customer["email"],
                        "template_id": campaign.template_id,
                        "variables": {
                            "customer_name": customer.get("name", "Valued Customer"),
                            "customer_id": customer["id"]
                        }
                    }
                    
                    await self._send_email(email_data)
                    sent_count += 1
                
                except Exception as e:
                    self.logger.error("Failed to send campaign email", error=str(e), customer_id=customer["id"])
                    failed_count += 1
            
            # Update campaign status
            campaign.status = "completed"
            
            self.logger.info("Campaign executed", 
                           campaign_id=campaign_id,
                           sent_count=sent_count,
                           failed_count=failed_count)
        
        except Exception as e:
            self.logger.error("Failed to execute campaign", error=str(e), campaign_id=campaign_id)
    
    async def _get_campaign_audience(self, target_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get target audience for campaign based on criteria."""
        # In production, this would query customer database with filters
        # For now, return sample customers
        
        sample_customers = [
            {"id": "customer_1", "email": "customer1@example.com", "name": "John Doe"},
            {"id": "customer_2", "email": "customer2@example.com", "name": "Jane Smith"},
            {"id": "customer_3", "email": "customer3@example.com", "name": "Bob Johnson"}
        ]
        
        return sample_customers
    
    async def _get_customer_interactions(self, customer_id: Optional[str] = None) -> Dict[str, Any]:
        """Get customer interactions."""
        try:
            if customer_id:
                # Filter interactions for specific customer
                customer_interactions = [
                    interaction.dict() for interaction in self.customer_interactions.values()
                    if interaction.customer_id == customer_id
                ]
            else:
                # Get all interactions
                customer_interactions = [interaction.dict() for interaction in self.customer_interactions.values()]
            
            # Calculate metrics
            total_interactions = len(customer_interactions)
            open_interactions = len([i for i in customer_interactions if i["status"] == "open"])
            resolved_interactions = len([i for i in customer_interactions if i["status"] == "resolved"])
            
            return {
                "interactions": customer_interactions,
                "metrics": {
                    "total": total_interactions,
                    "open": open_interactions,
                    "resolved": resolved_interactions,
                    "resolution_rate": (resolved_interactions / total_interactions * 100) if total_interactions > 0 else 0
                }
            }
        
        except Exception as e:
            self.logger.error("Failed to get customer interactions", error=str(e))
            raise
    
    async def _escalate_interaction(self, interaction_id: str) -> Dict[str, Any]:
        """Escalate interaction to human agent."""
        try:
            interaction = self.customer_interactions.get(interaction_id)
            if not interaction:
                raise ValueError(f"Interaction {interaction_id} not found")
            
            # Update interaction status
            interaction.status = "escalated"
            interaction.priority = "high"
            interaction.updated_at = datetime.utcnow()
            
            # Send escalation notification
            await self.send_message(
                recipient_agent="monitoring_agent",
                message_type=MessageType.ESCALATION_REQUIRED,
                payload={
                    "interaction_id": interaction_id,
                    "customer_id": interaction.customer_id,
                    "priority": interaction.priority,
                    "escalation_reason": "manual_escalation"
                }
            )
            
            return {
                "interaction_id": interaction_id,
                "status": "escalated",
                "escalated_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.logger.error("Failed to escalate interaction", error=str(e))
            raise
    
    async def _initialize_email_templates(self):
        """Initialize default email templates."""
        try:
            templates = [
                EmailTemplate(
                    template_id="order_confirmation",
                    name="Order Confirmation",
                    subject="Order Confirmation - #{order_number}",
                    html_content="""
                    <h2>Thank you for your order, {{customer_name}}!</h2>
                    <p>Your order #{order_number} has been confirmed and is being processed.</p>
                    <p>Order Total: €{{order_total}}</p>
                    <p>Estimated Delivery: {{delivery_date}}</p>
                    """,
                    text_content="""
                    Thank you for your order, {{customer_name}}!
                    Your order #{order_number} has been confirmed and is being processed.
                    Order Total: €{{order_total}}
                    Estimated Delivery: {{delivery_date}}
                    """,
                    template_type="transactional",
                    variables=["customer_name", "order_number", "order_total", "delivery_date"]
                ),
                EmailTemplate(
                    template_id="shipping_notification",
                    name="Shipping Notification",
                    subject="Your order is on its way! - #{order_number}",
                    html_content="""
                    <h2>Your order has shipped, {{customer_name}}!</h2>
                    <p>Order #{order_number} is now on its way to you.</p>
                    <p>Tracking Number: {{tracking_number}}</p>
                    <p>Carrier: {{carrier_name}}</p>
                    <p>Estimated Delivery: {{delivery_date}}</p>
                    """,
                    text_content="""
                    Your order has shipped, {{customer_name}}!
                    Order #{order_number} is now on its way to you.
                    Tracking Number: {{tracking_number}}
                    Carrier: {{carrier_name}}
                    Estimated Delivery: {{delivery_date}}
                    """,
                    template_type="transactional",
                    variables=["customer_name", "order_number", "tracking_number", "carrier_name", "delivery_date"]
                ),
                EmailTemplate(
                    template_id="return_confirmation",
                    name="Return Confirmation",
                    subject="Return Request Confirmed - #{return_number}",
                    html_content="""
                    <h2>Return request confirmed, {{customer_name}}</h2>
                    <p>Your return request #{return_number} has been approved.</p>
                    <p>Return Label: Please print the attached return label</p>
                    <p>Expected Refund: €{{refund_amount}}</p>
                    """,
                    text_content="""
                    Return request confirmed, {{customer_name}}
                    Your return request #{return_number} has been approved.
                    Return Label: Please print the attached return label
                    Expected Refund: €{{refund_amount}}
                    """,
                    template_type="transactional",
                    variables=["customer_name", "return_number", "refund_amount"]
                ),
                EmailTemplate(
                    template_id="promotional_offer",
                    name="Promotional Offer",
                    subject="Special Offer Just for You, {{customer_name}}!",
                    html_content="""
                    <h2>Exclusive Offer for {{customer_name}}</h2>
                    <p>Get {{discount_percent}}% off your next order!</p>
                    <p>Use code: {{promo_code}}</p>
                    <p>Valid until: {{expiry_date}}</p>
                    """,
                    text_content="""
                    Exclusive Offer for {{customer_name}}
                    Get {{discount_percent}}% off your next order!
                    Use code: {{promo_code}}
                    Valid until: {{expiry_date}}
                    """,
                    template_type="marketing",
                    variables=["customer_name", "discount_percent", "promo_code", "expiry_date"]
                )
            ]
            
            for template in templates:
                self.email_templates[template.template_id] = template
            
            self.logger.info("Email templates initialized", count=len(templates))
        
        except Exception as e:
            self.logger.error("Failed to initialize email templates", error=str(e))
    
    async def _initialize_chatbot_knowledge(self):
        """Initialize chatbot knowledge base."""
        try:
            # In production, this would load from a knowledge base or training data
            # For now, we rely on the AI model's general knowledge and rule-based fallbacks
            
            self.logger.info("Chatbot knowledge base initialized")
        
        except Exception as e:
            self.logger.error("Failed to initialize chatbot knowledge", error=str(e))
    
    async def _handle_order_created(self, message: AgentMessage):
        """Handle order created events to send confirmation emails."""
        payload = message.payload
        order_id = payload.get("order_id")
        customer_email = payload.get("customer_email")
        customer_name = payload.get("customer_name", "Valued Customer")
        order_total = payload.get("total_amount", 0)
        
        if order_id and customer_email:
            try:
                # Send order confirmation email
                email_data = {
                    "recipient": customer_email,
                    "template_id": "order_confirmation",
                    "variables": {
                        "customer_name": customer_name,
                        "order_number": order_id,
                        "order_total": f"{order_total:.2f}",
                        "delivery_date": (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d")
                    }
                }
                
                await self._send_email(email_data)
                
            except Exception as e:
                self.logger.error("Failed to send order confirmation email", error=str(e), order_id=order_id)
    
    async def _handle_order_updated(self, message: AgentMessage):
        """Handle order status updates to send notifications."""
        payload = message.payload
        order_id = payload.get("order_id")
        new_status = payload.get("new_status")
        customer_email = payload.get("customer_email")
        customer_name = payload.get("customer_name", "Valued Customer")
        
        if order_id and new_status and customer_email:
            try:
                if new_status == "shipped":
                    # Send shipping notification
                    email_data = {
                        "recipient": customer_email,
                        "template_id": "shipping_notification",
                        "variables": {
                            "customer_name": customer_name,
                            "order_number": order_id,
                            "tracking_number": payload.get("tracking_number", "TRK123456789"),
                            "carrier_name": payload.get("carrier_name", "Standard Carrier"),
                            "delivery_date": (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d")
                        }
                    }
                    
                    await self._send_email(email_data)
                
            except Exception as e:
                self.logger.error("Failed to send order update email", error=str(e), order_id=order_id)
    
    async def _handle_return_requested(self, message: AgentMessage):
        """Handle return requests to send confirmation emails."""
        payload = message.payload
        return_id = payload.get("return_id")
        customer_email = payload.get("customer_email")
        customer_name = payload.get("customer_name", "Valued Customer")
        refund_amount = payload.get("refund_amount", 0)
        
        if return_id and customer_email:
            try:
                # Send return confirmation email
                email_data = {
                    "recipient": customer_email,
                    "template_id": "return_confirmation",
                    "variables": {
                        "customer_name": customer_name,
                        "return_number": return_id,
                        "refund_amount": f"{refund_amount:.2f}"
                    }
                }
                
                await self._send_email(email_data)
                
            except Exception as e:
                self.logger.error("Failed to send return confirmation email", error=str(e), return_id=return_id)
    
    async def _process_email_campaigns(self):
        """Background task to process scheduled email campaigns."""
        while not self.shutdown_event.is_set():
            try:
                current_time = datetime.utcnow()
                
                # Check for scheduled campaigns
                for campaign_id, campaign in self.active_campaigns.items():
                    if (campaign.status == "scheduled" and 
                        campaign.scheduled_time and 
                        campaign.scheduled_time <= current_time):
                        
                        campaign.status = "active"
                        asyncio.create_task(self._execute_campaign(campaign_id))
                
                # Sleep for 1 minute before next check
                await asyncio.sleep(60)
            
            except Exception as e:
                self.logger.error("Error processing email campaigns", error=str(e))
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _monitor_interaction_metrics(self):
        """Background task to monitor interaction metrics."""
        while not self.shutdown_event.is_set():
            try:
                # Monitor metrics every 30 minutes
                await asyncio.sleep(1800)
                
                if not self.shutdown_event.is_set():
                    # Calculate metrics
                    total_interactions = len(self.customer_interactions)
                    open_interactions = len([i for i in self.customer_interactions.values() if i.status == "open"])
                    escalated_interactions = len([i for i in self.customer_interactions.values() if i.status == "escalated"])
                    
                    # Send metrics to monitoring agent
                    await self.send_message(
                        recipient_agent="monitoring_agent",
                        message_type=MessageType.RISK_ALERT,
                        payload={
                            "alert_type": "communication_metrics",
                            "total_interactions": total_interactions,
                            "open_interactions": open_interactions,
                            "escalated_interactions": escalated_interactions,
                            "active_chat_sessions": len(self.active_chat_sessions),
                            "severity": "info"
                        }
                    )
            
            except Exception as e:
                self.logger.error("Error monitoring interaction metrics", error=str(e))
                await asyncio.sleep(1800)  # Wait 30 minutes on error
    
    async def _cleanup_old_sessions(self):
        """Background task to cleanup old chat sessions."""
        while not self.shutdown_event.is_set():
            try:
                # Cleanup every hour
                await asyncio.sleep(3600)
                
                if not self.shutdown_event.is_set():
                    current_time = datetime.utcnow()
                    cutoff_time = current_time - timedelta(hours=24)  # 24 hours old
                    
                    # Remove old sessions
                    old_sessions = [
                        session_id for session_id, session in self.active_chat_sessions.items()
                        if session["last_activity"] < cutoff_time
                    ]
                    
                    for session_id in old_sessions:
                        del self.active_chat_sessions[session_id]
                        if session_id in self.websocket_connections:
                            try:
                                await self.websocket_connections[session_id].close()
                                del self.websocket_connections[session_id]
                            except:
                                pass
                    
                    if old_sessions:
                        self.logger.info("Cleaned up old chat sessions", count=len(old_sessions))
            
            except Exception as e:
                self.logger.error("Error cleaning up old sessions", error=str(e))
                await asyncio.sleep(3600)  # Wait 1 hour on error


# FastAPI app instance for running the agent as a service
app = FastAPI(title="Customer Communication Agent", version="1.0.0")

# Global agent instance
customer_communication_agent: Optional[CustomerCommunicationAgent] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the Customer Communication Agent on startup."""
    global customer_communication_agent
    customer_communication_agent = CustomerCommunicationAgent()
    await customer_communication_agent.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup the Customer Communication Agent on shutdown."""
    global customer_communication_agent
    if customer_communication_agent:
        await customer_communication_agent.stop()


# Include agent routes
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if customer_communication_agent:
        health_status = customer_communication_agent.get_health_status()
        return {"status": "healthy", "agent_status": health_status.dict()}
    return {"status": "unhealthy", "message": "Agent not initialized"}


# Mount agent's FastAPI app
app.mount("/api/v1", customer_communication_agent.app if customer_communication_agent else FastAPI())



# Create agent instance at module level to ensure routes are registered
agent = CustomerCommunicationAgent()

if __name__ == "__main__":
    import uvicorn
    from shared.database import initialize_database_manager, DatabaseConfig
    import os
    
    # Initialize database
    db_config = DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "multi_agent_ecommerce"),
        username=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD")
        if not password:
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
    pass
            pass
            raise ValueError("Database password must be set in environment variables")
    )
    initialize_database_manager(db_config)
    
    # Run the agent
    uvicorn.run(
        "customer_communication_agent:app",
        host="0.0.0.0",
        port=8008,
        reload=False,
        log_level="info"
    )
