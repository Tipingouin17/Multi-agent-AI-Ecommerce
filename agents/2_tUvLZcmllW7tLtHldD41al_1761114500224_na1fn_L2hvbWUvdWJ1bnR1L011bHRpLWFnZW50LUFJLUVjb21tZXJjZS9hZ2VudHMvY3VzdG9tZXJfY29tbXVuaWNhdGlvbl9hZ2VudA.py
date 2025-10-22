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
import uvicorn
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
    from shared.base_agent import BaseAgent, MessageType, AgentMessage
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

from shared.base_agent import BaseAgent, MessageType, AgentMessage
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


class CustomerCommunicationAgent(BaseAgent):
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
        self.app = FastAPI(title="Customer Communication Agent API", version="1.0.0")
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
        
        @self.app.get("/")
        async def root():
            return {"agent_name": "Customer Communication Agent", "status": "running"}

        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "agent_id": self.agent_id}

        @self.app.websocket("/chat/{session_id}")
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
        
        @self.app.post("/chat/message", response_model=APIResponse)
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
        
        @self.app.post("/email/send", response_model=APIResponse)
        async def send_email_api(email_data: Dict[str, Any]):
            """Send an email."""
            try:
                result = await self._send_email(email_data)
                return APIResponse(success=True, message="Email sent successfully", data=result)
            except Exception as e:
                self.logger.error("Failed to send email", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/campaigns/create", response_model=APIResponse)
        async def create_email_campaign_api(campaign_data: Dict[str, Any]):
            """Create a new email campaign."""
            try:
                result = await self._create_email_campaign(campaign_data)
                return APIResponse(success=True, message="Email campaign created successfully", data=result)
            except Exception as e:
                self.logger.error("Failed to create email campaign", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/interactions", response_model=APIResponse)
        async def get_customer_interactions_api(customer_id: Optional[str] = None):
            """Get customer interactions, optionally filtered by customer_id."""
            try:
                result = await self._get_customer_interactions(customer_id)
                return APIResponse(success=True, message="Customer interactions retrieved", data=result)
            except Exception as e:
                self.logger.error("Failed to get customer interactions", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/interactions/escalate", response_model=APIResponse)
        async def escalate_interaction_api(interaction_id: str):
            """Escalate a customer interaction."""
            try:
                result = await self._escalate_interaction(interaction_id)
                return APIResponse(success=True, message="Interaction escalated", data=result)
            except Exception as e:
                self.logger.error("Failed to escalate interaction", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

    async def _initialize_email_templates(self):
        """Initialize default email templates."""
        # Example templates
        welcome_template = EmailTemplate(
            template_id="welcome_email",
            name="Welcome Email",
            subject="Welcome to Our Store!",
            html_content="""<p>Dear {{customer_name}},</p><p>Welcome to our store! Thank you for signing up.</p>""",
            text_content="""Dear {{customer_name}},\nWelcome to our store! Thank you for signing up.""",
            template_type="transactional",
            variables=["customer_name"],
            active=True
        )
        order_confirm_template = EmailTemplate(
            template_id="order_confirmation",
            name="Order Confirmation",
            subject="Your Order #{{order_id}} is Confirmed",
            html_content="""<p>Dear {{customer_name}},</p><p>Your order #{{order_id}} has been confirmed and will be shipped soon.</p>""",
            text_content="""Dear {{customer_name}},\nYour order #{{order_id}} has been confirmed and will be shipped soon.""",
            template_type="transactional",
            variables=["customer_name", "order_id"],
            active=True
        )
        shipping_update_template = EmailTemplate(
            template_id="shipping_update",
            name="Shipping Update",
            subject="Your Order #{{order_id}} has Shipped!",
            html_content="""<p>Dear {{customer_name}},</p><p>Good news! Your order #{{order_id}} has shipped and is on its way.</p>""",
            text_content="""Dear {{customer_name}},\nGood news! Your order #{{order_id}} has shipped and is on its way.""",
            template_type="transactional",
            variables=["customer_name", "order_id"],
            active=True
        )
        return_instructions_template = EmailTemplate(
            template_id="return_instructions",
            name="Return Instructions",
            subject="Return Request for Order #{{order_id}}",
            html_content="""<p>Dear {{customer_name}},</p><p>We have received your return request for order #{{order_id}}. Please follow the instructions...</p>""",
            text_content="""Dear {{customer_name}},\nWe have received your return request for order #{{order_id}}. Please follow the instructions...""",
            template_type="transactional",
            variables=["customer_name", "order_id"],
            active=True
        )
        
        self.email_templates[welcome_template.template_id] = welcome_template
        self.email_templates[order_confirm_template.template_id] = order_confirm_template
        self.email_templates[shipping_update_template.template_id] = shipping_update_template
        self.email_templates[return_instructions_template.template_id] = return_instructions_template
        self.logger.info("Email templates initialized.")

    async def _initialize_chatbot_knowledge(self):
        """Initialize chatbot's knowledge base from a predefined set of FAQs or a database."""
        self.logger.info("Chatbot knowledge base initialized.")
        # In a real system, this would load from a database or external service
        self.chatbot_faqs = {
            "shipping": "Standard shipping takes 5-7 business days. Expedited options are available at checkout.",
            "returns": "You can return most items within 30 days of purchase with a valid receipt.",
            "contact": "You can reach customer support at support@example.com or call us at 1-800-123-4567."
        }

    async def _process_email_campaigns(self):
        """Background task to process and send scheduled email campaigns."""
        while True:
            self.logger.debug("Processing email campaigns...")
            now = datetime.utcnow()
            for campaign_id, campaign in list(self.active_campaigns.items()):
                if campaign.status == "scheduled" and campaign.scheduled_time and campaign.scheduled_time <= now:
                    self.logger.info(f"Executing scheduled campaign: {campaign.name}")
                    await self._execute_email_campaign(campaign)
                    campaign.status = "completed"
                    self.active_campaigns[campaign_id] = campaign # Update status
            await asyncio.sleep(60)  # Check every minute

    async def _monitor_interaction_metrics(self):
        """Background task to monitor interaction metrics and escalate if necessary."""
        while True:
            self.logger.debug("Monitoring interaction metrics...")
            # Example: escalate interactions open for too long
            for interaction_id, interaction in list(self.customer_interactions.items()):
                if interaction.status == "open" and (datetime.utcnow() - interaction.created_at) > timedelta(minutes=60):
                    self.logger.warning(f"Escalating long-pending interaction: {interaction_id}")
                    await self._escalate_interaction(interaction_id, reason="Long pending")
            await asyncio.sleep(300) # Check every 5 minutes

    async def _cleanup_old_sessions(self):
        """Background task to clean up old chat sessions."""
        while True:
            self.logger.debug("Cleaning up old chat sessions...")
            now = datetime.utcnow()
            sessions_to_remove = []
            for session_id, session_data in self.active_chat_sessions.items():
                if (now - session_data["last_activity"]) > timedelta(hours=2):
                    self.logger.info(f"Cleaning up old chat session: {session_id}")
                    sessions_to_remove.append(session_id)
            for session_id in sessions_to_remove:
                del self.active_chat_sessions[session_id]
            await asyncio.sleep(3600) # Check every hour

    async def _process_chat_message(self, message: str, session_id: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
        """Process an incoming chat message, generate a response, and track interaction."""
        self.logger.info("Processing chat message", session_id=session_id, message=message)
        
        # Update session last activity
        if session_id not in self.active_chat_sessions:
            self.active_chat_sessions[session_id] = {
                "session_id": session_id,
                "customer_id": customer_id,
                "messages": [],
                "context": {},
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow()
            }
        else:
            self.active_chat_sessions[session_id]["last_activity"] = datetime.utcnow()
            if customer_id and not self.active_chat_sessions[session_id]["customer_id"]:
                self.active_chat_sessions[session_id]["customer_id"] = customer_id

        # Add customer message to session history
        customer_chat_message = ChatMessage(
            message_id=str(uuid4()),
            session_id=session_id,
            customer_id=customer_id,
            message=message,
            sender="customer",
            timestamp=datetime.utcnow()
        )
        self.active_chat_sessions[session_id]["messages"].append(customer_chat_message.dict())

        # Simple chatbot logic: check for FAQs first, then use LLM if needed
        response_text = self._get_faq_response(message)
        if not response_text:
            # Use LLM for more complex queries
            chat_history = self.active_chat_sessions[session_id]["messages"]
            llm_response = await chat_completion(
                model="gpt-4.1-mini", # Using a smaller, faster model for chat
                messages=[
                    {"role": "system", "content": "You are a helpful customer support chatbot for an e-commerce store. Provide concise and helpful answers. If you cannot answer, suggest escalating to a human."},
                    *[{"role": m["sender"], "content": m["message"]} for m in chat_history]
                ]
            )
            response_text = llm_response.choices[0].message.content
        
        # Generate sentiment and intent (simplified for example)
        sentiment = "neutral" # In a real system, use an NLP model
        intent = "general_query" # In a real system, use an NLP model

        # Determine if escalation is needed (simplified)
        escalate = "human" in response_text.lower() or "escalate" in response_text.lower()

        chatbot_response_obj = ChatbotResponse(
            response=response_text,
            intent=intent,
            confidence=0.9, # Placeholder
            suggested_actions=[],
            escalate_to_human=escalate,
            context_data={}
        )

        # Add bot response to session history
        bot_chat_message = ChatMessage(
            message_id=str(uuid4()),
            session_id=session_id,
            customer_id=customer_id,
            message=response_text,
            sender="bot",
            timestamp=datetime.utcnow(),
            sentiment=sentiment,
            intent=intent
        )
        self.active_chat_sessions[session_id]["messages"].append(bot_chat_message.dict())

        # Track interaction
        if customer_id:
            await self._track_interaction(
                customer_id=customer_id,
                channel="chat",
                interaction_type="support",
                subject=message[:50], # First 50 chars of message as subject
                status="in_progress" if escalate else "resolved",
                priority="high" if escalate else "low"
            )

        return chatbot_response_obj.dict()
    
    def _get_faq_response(self, message: str) -> Optional[str]:
        """Check if message matches a known FAQ and return response."""
        message_lower = message.lower()
        for keyword, answer in self.chatbot_faqs.items():
            if keyword in message_lower:
                return answer
        return None

    async def _generate_welcome_message(self, session_id: str) -> Dict[str, Any]:
        """Generate a welcome message for a new chat session."""
        welcome_text = "Hello! Welcome to our customer support. How can I assist you today?"
        bot_chat_message = ChatMessage(
            message_id=str(uuid4()),
            session_id=session_id,
            customer_id=None,
            message=welcome_text,
            sender="bot",
            timestamp=datetime.utcnow(),
            sentiment="positive",
            intent="welcome"
        )
        self.active_chat_sessions[session_id]["messages"].append(bot_chat_message.dict())
        return ChatbotResponse(
            response=welcome_text,
            intent="welcome",
            confidence=1.0,
            suggested_actions=["browse_faqs", "check_order_status"],
            escalate_to_human=False,
            context_data={}
        ).dict()

    async def _send_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send an email using an SMTP server."""
        self.logger.info("Attempting to send email", recipient=email_data.get("to"))
        try:
            template_id = email_data.get("template_id")
            subject = email_data.get("subject", "")
            body_html = email_data.get("body_html", "")
            body_text = email_data.get("body_text", "")
            to_email = email_data.get("to")
            from_email = os.getenv("SMTP_FROM_EMAIL", "no-reply@example.com")
            smtp_server = os.getenv("SMTP_SERVER", "localhost")
            smtp_port = int(os.getenv("SMTP_PORT", "1025")) # Default to MailHog port
            smtp_user = os.getenv("SMTP_USER")
            smtp_password = os.getenv("SMTP_PASSWORD")

            if template_id and template_id in self.email_templates:
                template = self.email_templates[template_id]
                subject = template.subject
                body_html = template.html_content
                body_text = template.text_content
                
                # Replace variables in template
                for var in template.variables:
                    placeholder = "{{%s}}" % var
                    value = email_data.get(var, "")
                    subject = subject.replace(placeholder, str(value))
                    body_html = body_html.replace(placeholder, str(value))
                    body_text = body_text.replace(placeholder, str(value))

            msg = MIMEMultipart("alternative")
            msg["From"] = from_email
            msg["To"] = to_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body_text, "plain"))
            msg.attach(MIMEText(body_html, "html"))

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if smtp_user and smtp_password:
                    server.starttls() # Use TLS for secure connection
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            self.logger.info("Email sent successfully", recipient=to_email, subject=subject)
            return {"status": "success", "message": "Email sent", "recipient": to_email, "subject": subject}
        except Exception as e:
            self.logger.error("Failed to send email", error=str(e))
            raise

    async def _create_email_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create and schedule an email campaign."""
        campaign_id = str(uuid4())
        campaign = EmailCampaign(
            campaign_id=campaign_id,
            name=campaign_data["name"],
            template_id=campaign_data["template_id"],
            target_audience=campaign_data.get("target_audience", {}),
            schedule_type=campaign_data.get("schedule_type", "immediate"),
            scheduled_time=campaign_data.get("scheduled_time"),
            trigger_event=campaign_data.get("trigger_event"),
            status=campaign_data.get("status", "draft"),
            created_at=datetime.utcnow()
        )
        self.active_campaigns[campaign_id] = campaign
        self.logger.info("Email campaign created", campaign_id=campaign_id, name=campaign.name)
        
        if campaign.schedule_type == "immediate":
            asyncio.create_task(self._execute_email_campaign(campaign))

        return campaign.dict()

    async def _execute_email_campaign(self, campaign: EmailCampaign):
        """Execute a given email campaign by sending emails to the target audience."""
        self.logger.info("Executing email campaign", campaign_id=campaign.campaign_id, name=campaign.name)
        # In a real system, this would involve fetching target audience from DB
        # and sending personalized emails. For now, a placeholder.
        target_customers = ["customer1@example.com", "customer2@example.com"] # Placeholder
        
        for customer_email in target_customers:
            # For simplicity, using a generic email_data. In real scenario, personalize.
            email_data = {
                "to": customer_email,
                "template_id": campaign.template_id,
                "customer_name": customer_email.split("@")[0] # Example variable
            }
            try:
                await self._send_email(email_data)
            except Exception as e:
                self.logger.error(f"Failed to send email for campaign {campaign.campaign_id} to {customer_email}: {e}")
        self.logger.info("Email campaign execution completed", campaign_id=campaign.campaign_id)

    async def _track_interaction(self, customer_id: str, channel: str, interaction_type: str, subject: str, status: str, priority: str, assigned_agent: Optional[str] = None) -> Dict[str, Any]:
        """Track a customer interaction."""
        interaction_id = str(uuid4())
        interaction = CustomerInteraction(
            interaction_id=interaction_id,
            customer_id=customer_id,
            channel=channel,
            interaction_type=interaction_type,
            subject=subject,
            status=status,
            priority=priority,
            assigned_agent=assigned_agent,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.customer_interactions[interaction_id] = interaction
        self.logger.info("Customer interaction tracked", interaction_id=interaction_id, customer_id=customer_id, status=status)
        return interaction.dict()

    async def _get_customer_interactions(self, customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve customer interactions, optionally filtered by customer ID."""
        if customer_id:
            return [i.dict() for i in self.customer_interactions.values() if i.customer_id == customer_id]
        return [i.dict() for i in self.customer_interactions.values()]

    async def _escalate_interaction(self, interaction_id: str, reason: str = "") -> Dict[str, Any]:
        """Escalate a customer interaction to a human agent or another system."""
        if interaction_id not in self.customer_interactions:
            raise ValueError(f"Interaction with ID {interaction_id} not found.")

        interaction = self.customer_interactions[interaction_id]
        interaction.status = "escalated"
        interaction.priority = "urgent"
        interaction.updated_at = datetime.utcnow()
        self.customer_interactions[interaction_id] = interaction
        self.logger.warning("Interaction escalated", interaction_id=interaction_id, reason=reason)

        # In a real system, this would trigger a notification to a human agent
        # or another agent responsible for handling escalations.
        return interaction.dict()

    async def _handle_order_created(self, message: AgentMessage):
        """Handle ORDER_CREATED message: send confirmation email."""
        self.logger.info("Handling ORDER_CREATED message", order_id=message.payload.get("order_id"))
        customer_id = message.payload.get("customer_id")
        order_id = message.payload.get("order_id")
        customer_email = message.payload.get("customer_email")
        customer_name = message.payload.get("customer_name", "Customer")

        if not customer_email or not order_id:
            self.logger.error("Missing customer_email or order_id in ORDER_CREATED message")
            return

        email_data = {
            "to": customer_email,
            "template_id": "order_confirmation",
            "customer_name": customer_name,
            "order_id": order_id
        }
        await self._send_email(email_data)
        await self._track_interaction(
            customer_id=customer_id,
            channel="email",
            interaction_type="transactional",
            subject=f"Order Confirmation {order_id}",
            status="resolved",
            priority="low"
        )

    async def _handle_order_updated(self, message: AgentMessage):
        """Handle ORDER_UPDATED message: send shipping update email."""
        self.logger.info("Handling ORDER_UPDATED message", order_id=message.payload.get("order_id"))
        customer_id = message.payload.get("customer_id")
        order_id = message.payload.get("order_id")
        customer_email = message.payload.get("customer_email")
        customer_name = message.payload.get("customer_name", "Customer")
        status = message.payload.get("status")

        if not customer_email or not order_id or status != "shipped": # Only send shipping update for 'shipped' status
            self.logger.info("Not sending shipping update email", reason="Missing info or not shipped status")
            return

        email_data = {
            "to": customer_email,
            "template_id": "shipping_update",
            "customer_name": customer_name,
            "order_id": order_id
        }
        await self._send_email(email_data)
        await self._track_interaction(
            customer_id=customer_id,
            channel="email",
            interaction_type="transactional",
            subject=f"Shipping Update {order_id}",
            status="resolved",
            priority="low"
        )

    async def _handle_return_requested(self, message: AgentMessage):
        """Handle RETURN_REQUESTED message: send return instructions email."""
        self.logger.info("Handling RETURN_REQUESTED message", order_id=message.payload.get("order_id"))
        customer_id = message.payload.get("customer_id")
        order_id = message.payload.get("order_id")
        customer_email = message.payload.get("customer_email")
        customer_name = message.payload.get("customer_name", "Customer")

        if not customer_email or not order_id:
            self.logger.error("Missing customer_email or order_id in RETURN_REQUESTED message")
            return

        email_data = {
            "to": customer_email,
            "template_id": "return_instructions",
            "customer_name": customer_name,
            "order_id": order_id
        }
        await self._send_email(email_data)
        await self._track_interaction(
            customer_id=customer_id,
            channel="email",
            interaction_type="transactional",
            subject=f"Return Request {order_id}",
            status="in_progress",
            priority="medium"
        )

# This is the main entry point for running the FastAPI application.
# It should be run with `uvicorn customer_communication_agent:agent.app --host 0.0.0.0 --port 8000`
# if __name__ == "__main__":
#     # In a real deployment, the agent would be initialized and run by a supervisor process.
#     # For local testing, you can run it directly.
#     agent = CustomerCommunicationAgent()
#     # To run the FastAPI app, you would typically use uvicorn directly from the command line.
#     # Example: uvicorn customer_communication_agent:agent.app --host 0.0.0.0 --port 8000
#     # If you need to run it programmatically for testing or specific deployment scenarios:
#     import uvicorn
#     import nest_asyncio
#     nest_asyncio.apply()

#     async def start_server():
#         await agent.initialize()
#         config = uvicorn.Config(agent.app, host="0.0.0.0", port=8000, log_level="info")
#         server = uvicorn.Server(config)
#         await server.serve()

#     asyncio.run(start_server())

# The following lines are for integration with a larger system that might mount this agent's app.
# It's assumed that 'app' here refers to a global FastAPI app in a main application file.
# If this agent is meant to be a standalone service, the 'if __name__ == "__main__":' block above is more appropriate.
# For the purpose of this task, we will assume it's part of a larger system that will mount this agent's app.

# Create an instance of the agent globally so its app can be referenced by uvicorn
customer_communication_agent = CustomerCommunicationAgent()
app = customer_communication_agent.app

# Mount agent's FastAPI app
# This line is likely for a multi-agent orchestrator, not for a standalone agent.
# app.mount("/api/v1", customer_communication_agent.app if customer_communication_agent else FastAPI())


if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    
    agent = CustomerCommunicationAgent()

    async def start_server():
        await agent.initialize()
        config = uvicorn.Config(agent.app, host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    asyncio.run(start_server())


