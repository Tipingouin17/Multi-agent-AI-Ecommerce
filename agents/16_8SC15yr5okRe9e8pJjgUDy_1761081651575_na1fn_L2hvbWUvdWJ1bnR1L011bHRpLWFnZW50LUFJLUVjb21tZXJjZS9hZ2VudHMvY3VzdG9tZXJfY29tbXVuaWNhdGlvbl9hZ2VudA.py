
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

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
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

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=False,
)

logger = structlog.get_logger(__name__)

try:
    from shared.openai_helper import chat_completion
    from shared.base_agent import BaseAgent, MessageType, AgentMessage
    from shared.models import APIResponse
    from shared.database import DatabaseManager, get_database_manager
    logger.info("Successfully imported shared modules")
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.info(f"Current sys.path: {sys.path}")
    shared_dir = os.path.join(project_root, "shared")
    if os.path.exists(shared_dir):
        logger.info(f"Contents of {shared_dir}:")
        for item in os.listdir(shared_dir):
            logger.info(f"  - {item}")
    else:
        logger.info(f"Directory not found: {shared_dir}")
    sys.exit(1)


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
    
    def __init__(self, agent_id: str = "customer_communication_agent", **kwargs):
        super().__init__(agent_id=agent_id, agent_type="customer_communication", **kwargs)
        self.app = FastAPI(title="Customer Communication Agent API", version="1.0.0")
        self.setup_routes()
        
        self._db_initialized = False
        self.db_manager: Optional[DatabaseManager] = None
        self.db_helper: Optional[DatabaseHelper] = None

        # Communication data (will be replaced by DB operations)
        self.active_chat_sessions: Dict[str, Dict[str, Any]] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
        
        # Register message handlers
        self.register_handler(MessageType.ORDER_CREATED, self._handle_order_created)
        self.register_handler(MessageType.ORDER_UPDATED, self._handle_order_updated)
        self.register_handler(MessageType.RETURN_REQUESTED, self._handle_return_requested)

        # Load environment variables
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.example.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "user@example.com")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "password")
        self.sender_email = os.getenv("SENDER_EMAIL", "no-reply@example.com")
        self.database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")


    async def initialize(self):
        """Initialize the Customer Communication Agent, including database and other resources."""
        self.logger.info("Initializing Customer Communication Agent")
        try:
            self.db_manager = get_database_manager(self.database_url)
            await self.db_manager.connect()
            self.db_helper = DatabaseHelper(self.db_manager)
            self._db_initialized = True
            self.logger.info("Database initialized successfully")

            await self._initialize_email_templates()
            await self._initialize_chatbot_knowledge()

            asyncio.create_task(self._process_email_campaigns())
            asyncio.create_task(self._monitor_interaction_metrics())
            asyncio.create_task(self._cleanup_old_sessions())
            
            self.logger.info("Customer Communication Agent initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Customer Communication Agent: {e}", error=str(e))
            raise

    async def cleanup(self):
        """Cleanup resources, including closing database connection and WebSockets."""
        self.logger.info("Cleaning up Customer Communication Agent")
        try:
            if self.db_manager:
                await self.db_manager.disconnect()
                self.logger.info("Database disconnected successfully")
            for session_id, websocket in self.websocket_connections.items():
                try:
                    await websocket.close()
                except Exception as e:
                    self.logger.warning(f"Error closing WebSocket for session {session_id}: {e}")
            self.logger.info("Customer Communication Agent cleanup complete")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}", error=str(e))

    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process customer communication business logic based on the action provided."""
        if not self._db_initialized: 
            self.logger.warning("Database not initialized. Cannot process business logic.")
            return {"status": "error", "message": "Database not initialized"}

        action = data.get("action")
        try:
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
        except Exception as e:
            self.logger.error(f"Error processing business logic for action {action}: {e}", error=str(e))
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    def setup_routes(self):
        """Setup FastAPI routes for the Customer Communication Agent.

        Includes WebSocket endpoint for real-time chat and REST API endpoints
        for various communication functionalities.
        """
        @self.app.get("/health", response_model=APIResponse)
        async def health_check():
            """Health check endpoint to verify agent status."""
            return APIResponse(success=True, message="Customer Communication Agent is healthy")

        @self.app.get("/", response_model=APIResponse)
        async def root_endpoint():
            """Root endpoint providing basic agent information."""
            return APIResponse(success=True, message="Welcome to Customer Communication Agent API")

        @self.app.websocket("/chat/{session_id}")
        async def websocket_chat(websocket: WebSocket, session_id: str):
            """WebSocket endpoint for real-time chat.

            Args:
                websocket (WebSocket): The WebSocket connection object.
                session_id (str): The ID of the chat session.
            """
            await websocket.accept()
            self.websocket_connections[session_id] = websocket
            
            try:
                if not self._db_initialized: 
                    await websocket.send_text(json.dumps({"status": "error", "message": "Database not initialized"}))
                    return

                # Initialize chat session (or retrieve from DB)
                chat_session = await self._get_chat_session(session_id)
                if not chat_session:
                    chat_session = {
                        "session_id": session_id,
                        "customer_id": None,
                        "messages": [],
                        "context": {},
                        "created_at": datetime.utcnow(),
                        "last_activity": datetime.utcnow()
                    }
                    await self._create_chat_session(chat_session)
                
                # Send welcome message
                welcome_response = await self._generate_welcome_message(session_id)
                await websocket.send_text(json.dumps(welcome_response))
                
                while True:
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    response = await self._process_chat_message(
                        message_data["message"], 
                        session_id,
                        message_data.get("customer_id")
                    )
                    
                    await websocket.send_text(json.dumps(response))
            
            except WebSocketDisconnect:
                self.logger.info("WebSocket disconnected", session_id=session_id)
            except Exception as e:
                self.logger.error("WebSocket error", error=str(e), session_id=session_id)
            finally:
                if session_id in self.websocket_connections:
                    del self.websocket_connections[session_id]
        
        @self.app.post("/chat/message", response_model=APIResponse)
        async def send_chat_message_rest(message: str, session_id: str, customer_id: Optional[str] = None):
            """Send a chat message (REST API alternative to WebSocket).

            Args:
                message (str): The content of the message.
                session_id (str): The ID of the chat session.
                customer_id (Optional[str]): The ID of the customer, if available.

            Returns:
                APIResponse: The response from processing the chat message.
            """
            if not self._db_initialized: 
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not initialized")
            try:
                result = await self._process_chat_message(message, session_id, customer_id)
                
                return APIResponse(
                    success=True,
                    message="Chat message processed successfully",
                    data=result
                )
            
            except Exception as e:
                self.logger.error("Failed to process chat message", error=str(e))
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        @self.app.post("/email/send", response_model=APIResponse)
        async def send_email_rest(email_data: Dict[str, Any]):
            """Send an email using predefined templates or custom content.

            Args:
                email_data (Dict[str, Any]): Dictionary containing email details.

            Returns:
                APIResponse: The response from the email sending operation.
            """
            if not self._db_initialized: 
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not initialized")
            try:
                result = await self._send_email(email_data)
                return APIResponse(success=True, message="Email sent successfully", data=result)
            except Exception as e:
                self.logger.error(f"Failed to send email: {e}", error=str(e))
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        @self.app.post("/campaigns/create", response_model=APIResponse)
        async def create_email_campaign_rest(campaign_data: EmailCampaign):
            """Create a new email campaign.

            Args:
                campaign_data (EmailCampaign): The data for the email campaign.

            Returns:
                APIResponse: The response from the campaign creation operation.
            """
            if not self._db_initialized: 
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not initialized")
            try:
                result = await self._create_email_campaign(campaign_data.dict())
                return APIResponse(success=True, message="Email campaign created successfully", data=result)
            except Exception as e:
                self.logger.error(f"Failed to create email campaign: {e}", error=str(e))
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        @self.app.get("/interactions/{customer_id}", response_model=APIResponse)
        async def get_customer_interactions_rest(customer_id: str):
            """Retrieve all interactions for a given customer.

            Args:
                customer_id (str): The ID of the customer.

            Returns:
                APIResponse: A list of customer interactions.
            """
            if not self._db_initialized: 
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not initialized")
            try:
                interactions = await self._get_customer_interactions(customer_id)
                return APIResponse(success=True, message="Customer interactions retrieved", data=interactions)
            except Exception as e:
                self.logger.error(f"Failed to retrieve customer interactions for {customer_id}: {e}", error=str(e))
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        @self.app.post("/interactions/{interaction_id}/escalate", response_model=APIResponse)
        async def escalate_interaction_rest(interaction_id: str):
            """Escalate a customer interaction.

            Args:
                interaction_id (str): The ID of the interaction to escalate.

            Returns:
                APIResponse: The response from the escalation operation.
            """
            if not self._db_initialized: 
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not initialized")
            try:
                result = await self._escalate_interaction(interaction_id)
                return APIResponse(success=True, message="Interaction escalated successfully", data=result)
            except Exception as e:
                self.logger.error(f"Failed to escalate interaction {interaction_id}: {e}", error=str(e))
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        @self.app.post("/templates", response_model=APIResponse)
        async def create_email_template_rest(template: EmailTemplate):
            """Create a new email template."
            if not self._db_initialized: 
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not initialized")
            try:
                created_template = await self._create_email_template(template)
                return APIResponse(success=True, message="Email template created successfully", data=created_template)
            except Exception as e:
                self.logger.error(f"Failed to create email template: {e}", error=str(e))
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        @self.app.get("/templates/{template_id}", response_model=APIResponse)
        async def get_email_template_rest(template_id: str):
            """Get an email template by ID."
            if not self._db_initialized: 
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not initialized")
            try:
                template = await self._get_email_template(template_id)
                if template:
                    return APIResponse(success=True, message="Email template retrieved successfully", data=template)
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
            except Exception as e:
                self.logger.error(f"Failed to get email template {template_id}: {e}", error=str(e))
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        @self.app.put("/templates/{template_id}", response_model=APIResponse)
        async def update_email_template_rest(template_id: str, template: EmailTemplate):
            """Update an existing email template."
            if not self._db_initialized: 
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not initialized")
            try:
                updated_template = await self._update_email_template(template_id, template)
                if updated_template:
                    return APIResponse(success=True, message="Email template updated successfully", data=updated_template)
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
            except Exception as e:
                self.logger.error(f"Failed to update email template {template_id}: {e}", error=str(e))
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        @self.app.delete("/templates/{template_id}", response_model=APIResponse)
        async def delete_email_template_rest(template_id: str):
            """Delete an email template."
            if not self._db_initialized: 
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not initialized")
            try:
                success = await self._delete_email_template(template_id)
                if success:
                    return APIResponse(success=True, message="Email template deleted successfully")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
            except Exception as e:
                self.logger.error(f"Failed to delete email template {template_id}: {e}", error=str(e))
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


    async def _get_chat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a chat session from the database.

        Args:
            session_id (str): The ID of the chat session.

        Returns:
            Optional[Dict[str, Any]]: The chat session data if found, otherwise None.
        """
        if not self._db_initialized: return None
        try:
            async with self.db_manager.get_session() as session:
                # Assuming ChatMessage is stored as JSON or a similar structure
                # This is a simplified example, actual implementation might need a dedicated ChatSession model
                result = await self.db_helper.get_by_id(session, "chat_sessions", session_id)
                return result.to_dict() if result else None
        except Exception as e:
            self.logger.error(f"Error retrieving chat session {session_id}: {e}", error=str(e))
            return None

    async def _create_chat_session(self, session_data: Dict[str, Any]):
        """Creates a new chat session in the database.

        Args:
            session_data (Dict[str, Any]): The data for the new chat session.
        """
        if not self._db_initialized: return
        try:
            async with self.db_manager.get_session() as session:
                await self.db_helper.create(session, "chat_sessions", session_data)
                self.logger.info(f"Chat session {session_data['session_id']} created in DB.")
        except Exception as e:
            self.logger.error(f"Error creating chat session {session_data.get('session_id')}: {e}", error=str(e))

    async def _update_chat_session(self, session_id: str, updates: Dict[str, Any]):
        """Updates an existing chat session in the database.

        Args:
            session_id (str): The ID of the chat session to update.
            updates (Dict[str, Any]): A dictionary of fields to update.
        """
        if not self._db_initialized: return
        try:
            async with self.db_manager.get_session() as session:
                await self.db_helper.update(session, "chat_sessions", session_id, updates)
                self.logger.info(f"Chat session {session_id} updated in DB.")
        except Exception as e:
            self.logger.error(f"Error updating chat session {session_id}: {e}", error=str(e))

    async def _delete_chat_session(self, session_id: str):
        """Deletes a chat session from the database.

        Args:
            session_id (str): The ID of the chat session to delete.
        """
        if not self._db_initialized: return
        try:
            async with self.db_manager.get_session() as session:
                await self.db_helper.delete(session, "chat_sessions", session_id)
                self.logger.info(f"Chat session {session_id} deleted from DB.")
        except Exception as e:
            self.logger.error(f"Error deleting chat session {session_id}: {e}", error=str(e))

    async def _initialize_email_templates(self):
        """Initializes email templates from the database or creates defaults if none exist."""
        if not self._db_initialized: return
        self.logger.info("Initializing email templates...")
        try:
            async with self.db_manager.get_session() as session:
                templates = await self.db_helper.get_all(session, "email_templates")
                if not templates:
                    self.logger.info("No email templates found, creating defaults.")
                    default_template_data = {
                        "template_id": "welcome_email",
                        "name": "Welcome Email",
                        "subject": "Welcome to Our Service!",
                        "html_content": "<p>Dear {{customer_name}}, welcome!</p>",
                        "text_content": "Dear {{customer_name}}, welcome!",
                        "template_type": "transactional",
                        "variables": ["customer_name"],
                        "active": True
                    }
                    default_template = EmailTemplate(**default_template_data)
                    await self._create_email_template(default_template)
                    self.email_templates[default_template.template_id] = default_template
                else:
                    for template_data in templates:
                        template = EmailTemplate(**template_data.to_dict())
                        self.email_templates[template.template_id] = template
                self.logger.info(f"Loaded {len(self.email_templates)} email templates.")
        except Exception as e:
            self.logger.error(f"Error initializing email templates: {e}", error=str(e))

    async def _create_email_template(self, template: EmailTemplate) -> Optional[EmailTemplate]:
        """Creates a new email template in the database.

        Args:
            template (EmailTemplate): The email template to create.

        Returns:
            Optional[EmailTemplate]: The created email template if successful, otherwise None.
        """
        if not self._db_initialized: return None
        try:
            async with self.db_manager.get_session() as session:
                await self.db_helper.create(session, "email_templates", template.dict())
                self.email_templates[template.template_id] = template
                self.logger.info(f"Email template {template.template_id} created.")
                return template
        except Exception as e:
            self.logger.error(f"Error creating email template {template.template_id}: {e}", error=str(e))
            return None

    async def _get_email_template(self, template_id: str) -> Optional[EmailTemplate]:
        """Retrieves an email template by its ID.

        Args:
            template_id (str): The ID of the email template.

        Returns:
            Optional[EmailTemplate]: The email template if found, otherwise None.
        """
        if not self._db_initialized: return None
        if template_id in self.email_templates: # Check cache first
            return self.email_templates[template_id]
        try:
            async with self.db_manager.get_session() as session:
                result = await self.db_helper.get_by_id(session, "email_templates", template_id)
                if result:
                    template = EmailTemplate(**result.to_dict())
                    self.email_templates[template_id] = template # Cache it
                    return template
                return None
        except Exception as e:
            self.logger.error(f"Error retrieving email template {template_id}: {e}", error=str(e))
            return None

    async def _update_email_template(self, template_id: str, updates: EmailTemplate) -> Optional[EmailTemplate]:
        """Updates an existing email template in the database.

        Args:
            template_id (str): The ID of the email template to update.
            updates (EmailTemplate): The updated email template data.

        Returns:
            Optional[EmailTemplate]: The updated email template if successful, otherwise None.
        """
        if not self._db_initialized: return None
        try:
            async with self.db_manager.get_session() as session:
                success = await self.db_helper.update(session, "email_templates", template_id, updates.dict(exclude_unset=True))
                if success:
                    # Refresh cache
                    self.email_templates[template_id] = updates
                    self.logger.info(f"Email template {template_id} updated.")
                    return updates
                return None
        except Exception as e:
            self.logger.error(f"Error updating email template {template_id}: {e}", error=str(e))
            return None

    async def _delete_email_template(self, template_id: str) -> bool:
        """Deletes an email template from the database.

        Args:
            template_id (str): The ID of the email template to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        if not self._db_initialized: return False
        try:
            async with self.db_manager.get_session() as session:
                success = await self.db_helper.delete(session, "email_templates", template_id)
                if success and template_id in self.email_templates:
                    del self.email_templates[template_id]
                    self.logger.info(f"Email template {template_id} deleted.")
                return success
        except Exception as e:
            self.logger.error(f"Error deleting email template {template_id}: {e}", error=str(e))
            return False

    async def _initialize_chatbot_knowledge(self):
        """Initializes the chatbot's knowledge base, potentially from a database or external source."""
        if not self._db_initialized: return
        self.logger.info("Initializing chatbot knowledge base...")
        # In a real scenario, this would load FAQs, common responses, etc. from DB
        # For now, it's a placeholder
        self.chatbot_knowledge = {
            "greeting": "Hello! How can I assist you today?",
            "order_status_query": "Please provide your order number to check its status."
        }
        self.logger.info("Chatbot knowledge base initialized.")

    async def _process_chat_message(self, message: str, session_id: str, customer_id: Optional[str] = None) -> ChatbotResponse:
        """Processes a customer chat message, generates a response, and stores the interaction.

        Args:
            message (str): The customer's message.
            session_id (str): The ID of the chat session.
            customer_id (Optional[str]): The ID of the customer.

        Returns:
            ChatbotResponse: The chatbot's response.
        """
        if not self._db_initialized: 
            return ChatbotResponse(
                response="System temporarily unavailable. Please try again later.",
                intent="system_error", confidence=1.0, suggested_actions=[], escalate_to_human=True, context_data={}
            )
        try:
            # Retrieve or create session
            chat_session = await self._get_chat_session(session_id)
            if not chat_session:
                chat_session = {
                    "session_id": session_id,
                    "customer_id": customer_id,
                    "messages": [],
                    "context": {},
                    "created_at": datetime.utcnow(),
                    "last_activity": datetime.utcnow()
                }
                await self._create_chat_session(chat_session)
            
            # Update session with new message
            chat_message = ChatMessage(
                message_id=str(uuid4()),
                session_id=session_id,
                customer_id=customer_id,
                message=message,
                sender="customer",
                timestamp=datetime.utcnow()
            )
            chat_session["messages"].append(chat_message.dict())
            chat_session["last_activity"] = datetime.utcnow()
            await self._update_chat_session(session_id, {"messages": chat_session["messages"], "last_activity": chat_session["last_activity"]})

            # Simulate AI processing (replace with actual LLM call)
            ai_response_text = await chat_completion(prompt=f"Customer message: {message}. Provide a concise and helpful response.")
            
            # Simulate sentiment and intent analysis
            sentiment = "neutral" # Placeholder
            intent = "general_query" # Placeholder
            escalate = False
            suggested_actions = []

            if "order status" in message.lower():
                intent = "order_status"
                ai_response_text = self.chatbot_knowledge.get("order_status_query", ai_response_text)
            elif "hello" in message.lower() or "hi" in message.lower():
                intent = "greeting"
                ai_response_text = self.chatbot_knowledge.get("greeting", ai_response_text)
            elif "speak to human" in message.lower() or "escalate" in message.lower():
                escalate = True
                ai_response_text = "I'm escalating your request to a human agent. Please wait a moment."
                suggested_actions.append("notify_human_agent")
            
            response_message = ChatMessage(
                message_id=str(uuid4()),
                session_id=session_id,
                customer_id=customer_id,
                message=ai_response_text,
                sender="bot",
                timestamp=datetime.utcnow(),
                sentiment=sentiment,
                intent=intent,
                resolved=not escalate
            )
            chat_session["messages"].append(response_message.dict())
            await self._update_chat_session(session_id, {"messages": chat_session["messages"]})

            self.logger.info("Chat message processed", session_id=session_id, customer_id=customer_id, intent=intent)
            return ChatbotResponse(
                response=ai_response_text,
                intent=intent,
                confidence=0.9, # Placeholder
                suggested_actions=suggested_actions,
                escalate_to_human=escalate,
                context_data={}
            )
        except Exception as e:
            self.logger.error(f"Error processing chat message for session {session_id}: {e}", error=str(e))
            return ChatbotResponse(
                response="An error occurred while processing your request. Please try again.",
                intent="error", confidence=1.0, suggested_actions=[], escalate_to_human=True, context_data={}
            )

    async def _generate_welcome_message(self, session_id: str) -> Dict[str, Any]:
        """Generates a welcome message for a new chat session.

        Args:
            session_id (str): The ID of the chat session.

        Returns:
            Dict[str, Any]: A dictionary containing the welcome message.
        """
        if not self._db_initialized: return {"message": "Welcome! System temporarily unavailable.", "sender": "bot"}
        try:
            # This could be more dynamic, e.g., based on customer history
            welcome_text = self.chatbot_knowledge.get("greeting", "Hello! How can I help you today?")
            return {"message": welcome_text, "sender": "bot"}
        except Exception as e:
            self.logger.error(f"Error generating welcome message for session {session_id}: {e}", error=str(e))
            return {"message": "Hello! An error occurred.", "sender": "bot"}

    async def _send_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sends an email using SMTP.

        Args:
            email_data (Dict[str, Any]): Dictionary containing recipient, subject, body, and optional template_id.

        Returns:
            Dict[str, Any]: Status of the email sending operation.
        """
        if not self._db_initialized: return {"status": "error", "message": "Database not initialized. Email not sent."}
        try:
            recipient_email = email_data["recipient_email"]
            subject = email_data.get("subject")
            body = email_data.get("body")
            template_id = email_data.get("template_id")
            template_vars = email_data.get("template_vars", {})

            msg = MIMEMultipart("alternative")
            msg["From"] = self.sender_email
            msg["To"] = recipient_email

            if template_id:
                template = await self._get_email_template(template_id)
                if not template:
                    raise ValueError(f"Email template {template_id} not found.")
                subject = template.subject
                html_body = template.html_content
                text_body = template.text_content

                for key, value in template_vars.items():
                    html_body = html_body.replace(f"{{{{{key}}}}}", str(value))
                    text_body = text_body.replace(f"{{{{{key}}}}}", str(value))
            else:
                html_body = body
                text_body = body
            
            msg["Subject"] = subject

            part1 = MIMEText(text_body, "plain")
            part2 = MIMEText(html_body, "html")

            msg.attach(part1)
            msg.attach(part2)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.sender_email, recipient_email, msg.as_string())

            self.logger.info("Email sent successfully", recipient=recipient_email, subject=subject)
            return {"status": "success", "message": "Email sent successfully"}
        except Exception as e:
            self.logger.error(f"Failed to send email to {email_data.get('recipient_email')}: {e}", error=str(e))
            raise

    async def _create_email_campaign(self, campaign_data: Dict[str, Any]) -> Optional[EmailCampaign]:
        """Creates a new email campaign in the database.

        Args:
            campaign_data (Dict[str, Any]): The data for the email campaign.

        Returns:
            Optional[EmailCampaign]: The created email campaign if successful, otherwise None.
        """
        if not self._db_initialized: return None
        try:
            campaign = EmailCampaign(
                campaign_id=str(uuid4()),
                created_at=datetime.utcnow(),
                **campaign_data
            )
            async with self.db_manager.get_session() as session:
                await self.db_helper.create(session, "email_campaigns", campaign.dict())
                self.active_campaigns[campaign.campaign_id] = campaign
                self.logger.info(f"Email campaign {campaign.campaign_id} created.")
                return campaign
        except Exception as e:
            self.logger.error(f"Error creating email campaign: {e}", error=str(e))
            return None

    async def _get_email_campaign(self, campaign_id: str) -> Optional[EmailCampaign]:
        """Retrieves an email campaign by its ID."
        if not self._db_initialized: return None
        try:
            async with self.db_manager.get_session() as session:
                result = await self.db_helper.get_by_id(session, "email_campaigns", campaign_id)
                return EmailCampaign(**result.to_dict()) if result else None
        except Exception as e:
            self.logger.error(f"Error retrieving email campaign {campaign_id}: {e}", error=str(e))
            return None

    async def _update_email_campaign(self, campaign_id: str, updates: Dict[str, Any]) -> Optional[EmailCampaign]:
        """Updates an existing email campaign."
        if not self._db_initialized: return None
        try:
            async with self.db_manager.get_session() as session:
                success = await self.db_helper.update(session, "email_campaigns", campaign_id, updates)
                if success:
                    # Optionally refresh local cache if needed
                    self.logger.info(f"Email campaign {campaign_id} updated.")
                    return await self._get_email_campaign(campaign_id)
                return None
        except Exception as e:
            self.logger.error(f"Error updating email campaign {campaign_id}: {e}", error=str(e))
            return None

    async def _delete_email_campaign(self, campaign_id: str) -> bool:
        """Deletes an email campaign."
        if not self._db_initialized: return False
        try:
            async with self.db_manager.get_session() as session:
                success = await self.db_helper.delete(session, "email_campaigns", campaign_id)
                if success and campaign_id in self.active_campaigns:
                    del self.active_campaigns[campaign_id]
                    self.logger.info(f"Email campaign {campaign_id} deleted.")
                return success
        except Exception as e:
            self.logger.error(f"Error deleting email campaign {campaign_id}: {e}", error=str(e))
            return False

    async def _get_customer_interactions(self, customer_id: Optional[str] = None) -> List[CustomerInteraction]:
        """Retrieves customer interactions, optionally filtered by customer ID.

        Args:
            customer_id (Optional[str]): The ID of the customer to filter interactions.

        Returns:
            List[CustomerInteraction]: A list of customer interactions.
        """
        if not self._db_initialized: return []
        try:
            async with self.db_manager.get_session() as session:
                if customer_id:
                    # Assuming db_helper.get_all can take filters
                    results = await self.db_helper.get_all(session, "customer_interactions", filter_by={"customer_id": customer_id})
                else:
                    results = await self.db_helper.get_all(session, "customer_interactions")
                return [CustomerInteraction(**r.to_dict()) for r in results]
        except Exception as e:
            self.logger.error(f"Error retrieving customer interactions for customer {customer_id}: {e}", error=str(e))
            return []

    async def _create_customer_interaction(self, interaction: CustomerInteraction) -> Optional[CustomerInteraction]:
        """Creates a new customer interaction in the database."
        if not self._db_initialized: return None
        try:
            async with self.db_manager.get_session() as session:
                await self.db_helper.create(session, "customer_interactions", interaction.dict())
                self.logger.info(f"Customer interaction {interaction.interaction_id} created.")
                return interaction
        except Exception as e:
            self.logger.error(f"Error creating customer interaction {interaction.interaction_id}: {e}", error=str(e))
            return None

    async def _update_customer_interaction(self, interaction_id: str, updates: Dict[str, Any]) -> Optional[CustomerInteraction]:
        """Updates an existing customer interaction."
        if not self._db_initialized: return None
        try:
            async with self.db_manager.get_session() as session:
                success = await self.db_helper.update(session, "customer_interactions", interaction_id, updates)
                if success:
                    self.logger.info(f"Customer interaction {interaction_id} updated.")
                    return await self._get_customer_interaction_by_id(interaction_id)
                return None
        except Exception as e:
            self.logger.error(f"Error updating customer interaction {interaction_id}: {e}", error=str(e))
            return None

    async def _get_customer_interaction_by_id(self, interaction_id: str) -> Optional[CustomerInteraction]:
        """Retrieves a single customer interaction by its ID."
        if not self._db_initialized: return None
        try:
            async with self.db_manager.get_session() as session:
                result = await self.db_helper.get_by_id(session, "customer_interactions", interaction_id)
                return CustomerInteraction(**result.to_dict()) if result else None
        except Exception as e:
            self.logger.error(f"Error retrieving customer interaction {interaction_id}: {e}", error=str(e))
            return None

    async def _escalate_interaction(self, interaction_id: str) -> Dict[str, Any]:
        """Escalates a customer interaction, updating its status in the database and notifying relevant agents.

        Args:
            interaction_id (str): The ID of the interaction to escalate.

        Returns:
            Dict[str, Any]: Status of the escalation operation.
        """
        if not self._db_initialized: return {"status": "error", "message": "Database not initialized. Cannot escalate interaction."}
        try:
            interaction = await self._get_customer_interaction_by_id(interaction_id)
            if not interaction:
                raise ValueError(f"Interaction with ID {interaction_id} not found.")
            
            # Update interaction status to escalated
            updates = {"status": "escalated", "updated_at": datetime.utcnow(), "priority": "urgent"}
            await self._update_customer_interaction(interaction_id, updates)

            # Send a message to a human agent or another agent for escalation
            escalation_message = AgentMessage(
                sender_id=self.agent_id,
                receiver_id="human_agent_or_escalation_agent", # Placeholder
                message_type=MessageType.CUSTOMER_ESCALATION,
                payload={"interaction_id": interaction_id, "customer_id": interaction.customer_id, "subject": interaction.subject}
            )
            await self.send_message(escalation_message)

            self.logger.info("Interaction escalated", interaction_id=interaction_id)
            return {"status": "success", "message": "Interaction escalated successfully"}
        except Exception as e:
            self.logger.error(f"Failed to escalate interaction {interaction_id}: {e}", error=str(e))
            raise

    async def _process_email_campaigns(self):
        """Background task to process and send scheduled email campaigns."""
        if not self._db_initialized: return
        self.logger.info("Starting email campaign processing background task.")
        while True:
            try:
                async with self.db_manager.get_session() as session:
                    # Retrieve active and scheduled campaigns
                    # Assuming get_all can filter by status and schedule_type
                    campaigns_data = await self.db_helper.get_all(session, "email_campaigns", 
                                                                 filter_by={"status": "active", "schedule_type": "scheduled"})
                    
                    now = datetime.utcnow()
                    for campaign_data in campaigns_data:
                        campaign = EmailCampaign(**campaign_data.to_dict())
                        if campaign.scheduled_time and campaign.scheduled_time <= now:
                            self.logger.info(f"Processing scheduled campaign: {campaign.name}")
                            # Simulate sending emails to target audience
                            # In a real system, this would involve fetching customer lists and sending personalized emails
                            await self._send_email({
                                "recipient_email": "customer@example.com", # Placeholder
                                "template_id": campaign.template_id,
                                "template_vars": {"customer_name": "Valued Customer"}
                            })
                            # Update campaign status to completed or sent
                            await self._update_email_campaign(campaign.campaign_id, {"status": "completed", "updated_at": now})

                await asyncio.sleep(60) # Check every minute
            except Exception as e:
                self.logger.error(f"Error in email campaign processing task: {e}", error=str(e))
                await asyncio.sleep(60) # Wait before retrying

    async def _monitor_interaction_metrics(self):
        """Background task to monitor customer interaction metrics."""
        if not self._db_initialized: return
        self.logger.info("Starting interaction metrics monitoring background task.")
        while True:
            try:
                async with self.db_manager.get_session() as session:
                    # Example: Count open interactions
                    all_interactions = await self.db_helper.get_all(session, "customer_interactions")
                    open_interactions = [i for i in all_interactions if i.to_dict().get("status") == "open"]
                    self.logger.info(f"Currently {len(open_interactions)} open customer interactions.")
                    # More sophisticated metrics, e.g., average resolution time, sentiment trends, etc.

                await asyncio.sleep(300) # Check every 5 minutes
            except Exception as e:
                self.logger.error(f"Error in interaction metrics monitoring task: {e}", error=str(e))
                await asyncio.sleep(300) # Wait before retrying

    async def _cleanup_old_sessions(self):
        """Background task to clean up old chat sessions from the database."""
        if not self._db_initialized: return
        self.logger.info("Starting old chat session cleanup background task.")
        while True:
            try:
                async with self.db_manager.get_session() as session:
                    # Define what 

is considered 'old' - e.g., inactive for more than 24 hours
                    threshold = datetime.utcnow() - timedelta(hours=24)
                    # Assuming db_helper has a method to delete based on a condition
                    # This would need to be implemented in DatabaseHelper
                    # await self.db_helper.delete_many(session, "chat_sessions", filter_by={"last_activity_lt": threshold})
                    self.logger.info("Cleaned up old chat sessions (placeholder).")

                await asyncio.sleep(3600) # Check every hour
            except Exception as e:
                self.logger.error(f"Error in old chat session cleanup task: {e}", error=str(e))
                await asyncio.sleep(3600) # Wait before retrying

    async def process_message(self, message: AgentMessage):
        """Processes incoming messages from the message broker (Kafka).

        Args:
            message (AgentMessage): The incoming message to process.
        """
        self.logger.info(f"Received message: {message.message_type} from {message.sender_id}")
        try:
            if message.message_type == MessageType.ORDER_CREATED:
                await self._handle_order_created(message.payload)
            elif message.message_type == MessageType.ORDER_UPDATED:
                await self._handle_order_updated(message.payload)
            elif message.message_type == MessageType.RETURN_REQUESTED:
                await self._handle_return_requested(message.payload)
            elif message.message_type == MessageType.CUSTOMER_QUERY:
                # Example: process a customer query received via Kafka
                session_id = message.payload.get("session_id", str(uuid4()))
                customer_id = message.payload.get("customer_id")
                query = message.payload.get("query")
                if query:
                    response = await self._process_chat_message(query, session_id, customer_id)
                    # Send response back via Kafka or update a persistent chat log
                    response_message = AgentMessage(
                        sender_id=self.agent_id,
                        receiver_id=message.sender_id, # Reply to the sender
                        message_type=MessageType.CHAT_RESPONSE,
                        payload=response.dict()
                    )
                    await self.send_message(response_message)
                else:
                    self.logger.warning(f"Received CUSTOMER_QUERY with no query in payload: {message.payload}")
            else:
                self.logger.info(f"Unhandled message type: {message.message_type}")
        except Exception as e:
            self.logger.error(f"Error processing message of type {message.message_type}: {e}", error=str(e))

    async def _handle_order_created(self, payload: Dict[str, Any]):
        """Handles ORDER_CREATED messages by sending a confirmation email.

        Args:
            payload (Dict[str, Any]): The payload containing order details.
        """
        self.logger.info(f"Handling ORDER_CREATED for order {payload.get("order_id")}")
        try:
            customer_email = payload.get("customer_email")
            order_id = payload.get("order_id")
            if customer_email and order_id:
                email_data = {
                    "recipient_email": customer_email,
                    "template_id": "order_confirmation", # Assuming this template exists
                    "template_vars": {"customer_name": payload.get("customer_name", "Customer"), "order_id": order_id}
                }
                await self._send_email(email_data)
                self.logger.info(f"Order confirmation email sent for order {order_id} to {customer_email}")
            else:
                self.logger.warning(f"Missing customer_email or order_id in ORDER_CREATED payload: {payload}")
        except Exception as e:
            self.logger.error(f"Error handling ORDER_CREATED for order {payload.get("order_id")}: {e}", error=str(e))

    async def _handle_order_updated(self, payload: Dict[str, Any]):
        """Handles ORDER_UPDATED messages by sending an update email.

        Args:
            payload (Dict[str, Any]): The payload containing updated order details.
        """
        self.logger.info(f"Handling ORDER_UPDATED for order {payload.get("order_id")}")
        try:
            customer_email = payload.get("customer_email")
            order_id = payload.get("order_id")
            new_status = payload.get("new_status")
            if customer_email and order_id and new_status:
                email_data = {
                    "recipient_email": customer_email,
                    "template_id": "order_status_update", # Assuming this template exists
                    "template_vars": {"customer_name": payload.get("customer_name", "Customer"), "order_id": order_id, "new_status": new_status}
                }
                await self._send_email(email_data)
                self.logger.info(f"Order status update email sent for order {order_id} to {customer_email} with status {new_status}")
            else:
                self.logger.warning(f"Missing customer_email, order_id or new_status in ORDER_UPDATED payload: {payload}")
        except Exception as e:
            self.logger.error(f"Error handling ORDER_UPDATED for order {payload.get("order_id")}: {e}", error=str(e))

    async def _handle_return_requested(self, payload: Dict[str, Any]):
        """Handles RETURN_REQUESTED messages by sending a confirmation email for the return.

        Args:
            payload (Dict[str, Any]): The payload containing return request details.
        """
        self.logger.info(f"Handling RETURN_REQUESTED for order {payload.get("order_id")}")
        try:
            customer_email = payload.get("customer_email")
            order_id = payload.get("order_id")
            return_id = payload.get("return_id")
            if customer_email and order_id and return_id:
                email_data = {
                    "recipient_email": customer_email,
                    "template_id": "return_confirmation", # Assuming this template exists
                    "template_vars": {"customer_name": payload.get("customer_name", "Customer"), "order_id": order_id, "return_id": return_id}
                }
                await self._send_email(email_data)
                self.logger.info(f"Return confirmation email sent for order {order_id} to {customer_email}")
            else:
                self.logger.warning(f"Missing customer_email, order_id or return_id in RETURN_REQUESTED payload: {payload}")
        except Exception as e:
            self.logger.error(f"Error handling RETURN_REQUESTED for order {payload.get("order_id")}: {e}", error=str(e))



async def main():
    """Main function to initialize and run the Customer Communication Agent."""
    agent = CustomerCommunicationAgent()
    await agent.initialize()
    
    # Start the FastAPI application using uvicorn
    # This needs to be run in a separate process or managed by an ASGI server
    # For demonstration, we'll run it directly if not already running
    import uvicorn
    config = uvicorn.Config(agent.app, host="0.0.0.0", port=int(os.getenv("AGENT_PORT", "8000")))
    server = uvicorn.Server(config)
    
    # Run the uvicorn server in a separate task
    api_task = asyncio.create_task(server.serve())
    
    # Keep the main agent running to process Kafka messages
    await agent.run()

    # Wait for the API task to complete (e.g., if it's shut down externally)
    await api_task


if __name__ == "__main__":
    # This block is for direct execution and testing.
    # In a production multi-agent system, agents might be managed by a central orchestrator.
    asyncio.run(main())

