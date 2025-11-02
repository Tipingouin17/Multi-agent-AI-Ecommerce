
"""
Customer Agent Enhanced - Multi-Agent E-Commerce System

This agent provides comprehensive customer management including profiles, addresses,
preferences, loyalty programs, segmentation, and customer interactions.
"""

import asyncio
import contextlib
import os
import sys
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

import structlog
from fastapi import Body, Depends, FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

# Path setup
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.base_agent_v2 import AgentMessage, BaseAgentV2, MessageType
from shared.db_helpers import DatabaseHelper
from shared.database import DatabaseManager, DatabaseConfig, initialize_database_manager

logger = structlog.get_logger(__name__)


# =====================================================
# ENUMS
# =====================================================

class CustomerType(str, Enum):
    """Enumeration for customer types."""
    INDIVIDUAL = "individual"
    BUSINESS = "business"


class AccountStatus(str, Enum):
    """Enumeration for customer account statuses."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"


class LoyaltyTier(str, Enum):
    """Enumeration for customer loyalty tiers."""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


class InteractionType(str, Enum):
    """Enumeration for types of customer interactions."""
    SUPPORT_TICKET = "support_ticket"
    CHAT = "chat"
    EMAIL = "email"
    PHONE = "phone"
    REVIEW = "review"
    FEEDBACK = "feedback"


# =====================================================
# PYDANTIC MODELS
# =====================================================

class CustomerProfileBase(BaseModel):
    """Base Pydantic model for customer profile data."""
    email: EmailStr = Field(..., description="Customer's email address")
    phone: Optional[str] = Field(None, description="Customer's phone number")
    first_name: Optional[str] = Field(None, description="Customer's first name")
    last_name: Optional[str] = Field(None, description="Customer's last name")
    date_of_birth: Optional[date] = Field(None, description="Customer's date of birth")
    gender: Optional[str] = Field(None, description="Customer's gender")
    customer_type: CustomerType = Field(CustomerType.INDIVIDUAL, description="Type of customer (individual or business)")


class CustomerProfileCreate(CustomerProfileBase):
    """Pydantic model for creating a new customer profile."""
    customer_id: str = Field(..., description="Unique identifier for the customer")


class CustomerProfile(CustomerProfileBase):
    """Pydantic model for a complete customer profile, including system-generated fields."""
    customer_id: str = Field(..., description="Unique identifier for the customer")
    account_status: AccountStatus = Field(AccountStatus.ACTIVE, description="Current status of the customer's account")
    email_verified: bool = Field(False, description="Indicates if the customer's email has been verified")
    phone_verified: bool = Field(False, description="Indicates if the customer's phone has been verified")
    registration_date: datetime = Field(..., description="Date and time of customer registration")
    last_login_at: Optional[datetime] = Field(None, description="Last login date and time of the customer")
    created_at: datetime = Field(..., description="Timestamp when the record was created")
    updated_at: datetime = Field(..., description="Timestamp when the record was last updated")

    class Config:
        from_attributes = True


class CustomerAddressBase(BaseModel):
    """Base Pydantic model for customer address data."""
    address_type: str = Field(..., description="Type of address (e.g., shipping, billing)")
    address_label: Optional[str] = Field(None, description="User-defined label for the address")
    first_name: Optional[str] = Field(None, description="Recipient's first name for this address")
    last_name: Optional[str] = Field(None, description="Recipient's last name for this address")
    street_address_1: str = Field(..., description="First line of the street address")
    street_address_2: Optional[str] = Field(None, description="Second line of the street address")
    city: str = Field(..., description="City of the address")
    state_province: Optional[str] = Field(None, description="State or province of the address")
    postal_code: str = Field(..., description="Postal code of the address")
    country_code: str = Field(..., description="Country code (e.g., US, CA)")
    phone: Optional[str] = Field(None, description="Phone number associated with this address")
    is_default: bool = Field(False, description="Indicates if this is the default address")


class CustomerAddressCreate(CustomerAddressBase):
    """Pydantic model for creating a new customer address."""
    customer_id: str = Field(..., description="Unique identifier of the customer this address belongs to")


class CustomerAddress(CustomerAddressBase):
    """Pydantic model for a complete customer address, including system-generated fields."""
    address_id: UUID = Field(..., description="Unique identifier for the address")
    customer_id: str = Field(..., description="Unique identifier of the customer this address belongs to")
    is_verified: bool = Field(False, description="Indicates if the address has been verified")
    created_at: datetime = Field(..., description="Timestamp when the record was created")
    updated_at: datetime = Field(..., description="Timestamp when the record was last updated")

    class Config:
        from_attributes = True


class LoyaltyBase(BaseModel):
    """Base Pydantic model for customer loyalty data."""
    customer_id: str = Field(..., description="Unique identifier of the customer")
    loyalty_tier: LoyaltyTier = Field(LoyaltyTier.BRONZE, description="Current loyalty tier of the customer")
    points_balance: int = Field(0, description="Current loyalty points balance")


class Loyalty(LoyaltyBase):
    """Pydantic model for complete customer loyalty information, including system-generated fields."""
    loyalty_id: UUID = Field(..., description="Unique identifier for the loyalty record")
    points_lifetime: int = Field(0, description="Total loyalty points accumulated over customer's lifetime")
    tier_start_date: date = Field(..., description="Date when the current loyalty tier started")
    referral_code: Optional[str] = Field(None, description="Referral code associated with the customer")
    referrals_count: int = Field(0, description="Number of successful referrals by the customer")
    created_at: datetime = Field(..., description="Timestamp when the record was created")
    updated_at: datetime = Field(..., description="Timestamp when the record was last updated")

    class Config:
        from_attributes = True


class CustomerInteractionCreate(BaseModel):
    """Pydantic model for creating a new customer interaction record."""
    customer_id: str = Field(..., description="Unique identifier of the customer involved in the interaction")
    interaction_type: InteractionType = Field(..., description="Type of interaction (e.g., support ticket, chat)")
    interaction_channel: Optional[str] = Field(None, description="Channel through which the interaction occurred")
    subject: Optional[str] = Field(None, description="Subject of the interaction")
    description: Optional[str] = Field(None, description="Detailed description of the interaction")
    priority: str = Field("medium", description="Priority level of the interaction")


class CustomerInteraction(CustomerInteractionCreate):
    """Pydantic model for a complete customer interaction record, including system-generated fields."""
    interaction_id: UUID = Field(..., description="Unique identifier for the interaction record")
    status: str = Field("open", description="Current status of the interaction")
    assigned_to: Optional[str] = Field(None, description="Agent or team assigned to the interaction")
    created_at: datetime = Field(..., description="Timestamp when the record was created")
    updated_at: datetime = Field(..., description="Timestamp when the record was last updated")

    class Config:
        from_attributes = True


# =====================================================
# AGENT
# =====================================================

class CustomerAgent(BaseAgentV2):
    """
    Customer Agent Enhanced - Manages customer profiles, addresses, loyalty, and interactions.

    This agent handles all customer-related data and operations, including:
    - Creating, retrieving, updating, and deleting customer profiles.
    - Managing customer addresses.
    - Tracking customer loyalty information.
    - Recording customer interactions.
    - Communicating with other agents via Kafka.
    - Exposing functionalities via a FastAPI interface.
    """

    def __init__(self, agent_id: str, agent_type: str = "customer_agent"):
        """Initializes the CustomerAgent with a unique ID and type."""
        super().__init__(agent_id=agent_id)
        
        self.db_manager: Optional[DatabaseManager] = None
        self.db_helper_profile: Optional[DatabaseHelper] = None
        self.db_helper_address: Optional[DatabaseHelper] = None
        self.db_helper_loyalty: Optional[DatabaseHelper] = None
        self.db_helper_interaction: Optional[DatabaseHelper] = None
        self._db_initialized = False

    async def initialize_db(self):
        """Initializes the database manager and helper for customer data."""
        if self._db_initialized:
            logger.info("Database already initialized.")
            return
        try:
            # Initialize database manager with config from environment
            db_config = DatabaseConfig()
            self.db_manager = initialize_database_manager(db_config)
            await self.db_manager.initialize_async()
            self.db_helper_profile = DatabaseHelper(self.db_manager)
            self.db_helper_address = DatabaseHelper(self.db_manager)
            self.db_helper_loyalty = DatabaseHelper(self.db_manager)
            self.db_helper_interaction = DatabaseHelper(self.db_manager)
            self._db_initialized = True
            logger.info("Database initialized for CustomerAgent.")
        except Exception as e:
            logger.error("Failed to initialize database for CustomerAgent", error=str(e))
            raise

    async def get_all_customer_profiles(self) -> List[CustomerProfile]:
        """Retrieve all customer profiles from the database."""
        if not self._db_initialized: 
            logger.warning("Database not initialized. Cannot retrieve all customer profiles.")
            return []
        try:
            async with self.db_manager.get_session() as session:
                return [CustomerProfile(**data) for data in await self.db_helper_profile.get_all(session)]
        except Exception as e:
            logger.error("Error retrieving all customer profiles", error=str(e))
            return []

    async def get_customer_profile_by_id(self, customer_id: str) -> Optional[CustomerProfile]:
        """Retrieve a single customer profile by its ID.

        Args:
            customer_id: The unique identifier of the customer.

        Returns:
            The CustomerProfile if found, otherwise None.
        """
        if not self._db_initialized: 
            logger.warning(f"Database not initialized. Cannot retrieve customer profile for ID: {customer_id}.")
            return None
        try:
            async with self.db_manager.get_session() as session:
                data = await self.db_helper_profile.get_by_id(session, customer_id)
                return CustomerProfile(**data) if data else None
        except Exception as e:
            logger.error("Error retrieving customer profile by ID", customer_id=customer_id, error=str(e))
            return None

    async def get_customer_profile_by_email(self, email: EmailStr) -> Optional[CustomerProfile]:
        """Retrieve a single customer profile by its email address.

        Args:
            email: The email address of the customer.

        Returns:
            The CustomerProfile if found, otherwise None.
        """
        if not self._db_initialized: 
            logger.warning(f"Database not initialized. Cannot retrieve customer profile for email: {email}.")
            return None
        try:
            async with self.db_manager.get_session() as session:
                # Assuming db_helper supports get_by_field or similar for non-PK fields
                # For now, we'll simulate it or require a direct query
                query = "SELECT * FROM customer_profiles WHERE email = :email"
                data = await self.db_manager.fetch_one(query, {"email": email})
                return CustomerProfile(**data) if data else None
        except Exception as e:
            logger.error("Error retrieving customer profile by email", email=email, error=str(e))
            return None

    async def create_customer_profile(self, customer_data: CustomerProfileCreate) -> Optional[CustomerProfile]:
        """Create a new customer profile in the database.

        Args:
            customer_data: The data for the new customer profile.

        Returns:
            The created CustomerProfile if successful, otherwise None.
        """
        if not self._db_initialized: 
            logger.warning("Database not initialized. Cannot create customer profile.")
            return None
        try:
            async with self.db_manager.get_session() as session:
                # Ensure default values for new customer
                now = datetime.utcnow()
                profile_dict = customer_data.model_dump()
                profile_dict.update({
                    "account_status": AccountStatus.ACTIVE.value,
                    "email_verified": False,
                    "phone_verified": False,
                    "registration_date": now,
                    "created_at": now,
                    "updated_at": now,
                })
                created_data = await self.db_helper_profile.create(session, profile_dict)
                return CustomerProfile(**created_data) if created_data else None
        except Exception as e:
            logger.error("Error creating customer profile", email=customer_data.email, error=str(e))
            return None

    async def update_customer_profile(self, customer_id: str, update_data: Dict[str, Any]) -> Optional[CustomerProfile]:
        """Update an existing customer profile.

        Args:
            customer_id: The unique identifier of the customer to update.
            update_data: A dictionary containing the fields to update and their new values.

        Returns:
            The updated CustomerProfile if successful, otherwise None.
        """
        if not self._db_initialized: 
            logger.warning(f"Database not initialized. Cannot update customer profile for ID: {customer_id}.")
            return None
        try:
            async with self.db_manager.get_session() as session:
                update_data["updated_at"] = datetime.utcnow()
                updated_data = await self.db_helper_profile.update(session, customer_id, update_data)
                return CustomerProfile(**updated_data) if updated_data else None
        except Exception as e:
            logger.error("Error updating customer profile", customer_id=customer_id, error=str(e))
            return None

    async def delete_customer_profile(self, customer_id: str) -> bool:
        """Delete a customer profile from the database.

        Args:
            customer_id: The unique identifier of the customer to delete.

        Returns:
            True if deletion was successful, False otherwise.
        """
        if not self._db_initialized: 
            logger.warning(f"Database not initialized. Cannot delete customer profile for ID: {customer_id}.")
            return False
        try:
            async with self.db_manager.get_session() as session:
                return await self.db_helper_profile.delete(session, customer_id)
        except Exception as e:
            logger.error("Error deleting customer profile", customer_id=customer_id, error=str(e))
            return False

    async def add_customer_address(self, address_data: CustomerAddressCreate) -> Optional[CustomerAddress]:
        """Add a new address for a customer.

        Args:
            address_data: The data for the new customer address.

        Returns:
            The created CustomerAddress if successful, otherwise None.
        """
        if not self._db_initialized: 
            logger.warning("Database not initialized. Cannot add customer address.")
            return None
        try:
            async with self.db_manager.get_session() as session:
                now = datetime.utcnow()
                address_dict = address_data.model_dump()
                address_dict.update({
                    "address_id": str(uuid4()),
                    "is_verified": False,
                    "created_at": now,
                    "updated_at": now,
                })
                created_data = await self.db_helper_address.create(session, address_dict)
                return CustomerAddress(**created_data) if created_data else None
        except Exception as e:
            logger.error("Error adding customer address", customer_id=address_data.customer_id, error=str(e))
            return None

    async def get_customer_addresses(self, customer_id: str) -> List[CustomerAddress]:
        """Retrieve all addresses for a given customer.

        Args:
            customer_id: The unique identifier of the customer.

        Returns:
            A list of CustomerAddress objects.
        """
        if not self._db_initialized: 
            logger.warning(f"Database not initialized. Cannot retrieve addresses for customer ID: {customer_id}.")
            return []
        try:
            async with self.db_manager.get_session() as session:
                # Assuming db_helper can filter by a non-PK field or we use direct query
                query = "SELECT * FROM customer_addresses WHERE customer_id = :customer_id ORDER BY is_default DESC"
                results = await self.db_manager.fetch_all(query, {"customer_id": customer_id})
                return [CustomerAddress(**data) for data in results]
        except Exception as e:
            logger.error("Error retrieving customer addresses", customer_id=customer_id, error=str(e))
            return []

    async def get_customer_loyalty(self, customer_id: str) -> Optional[Loyalty]:
        """Retrieve loyalty information for a given customer.

        Args:
            customer_id: The unique identifier of the customer.

        Returns:
            The Loyalty object if found, otherwise None.
        """
        if not self._db_initialized: 
            logger.warning(f"Database not initialized. Cannot retrieve loyalty for customer ID: {customer_id}.")
            return None
        try:
            async with self.db_manager.get_session() as session:
                query = "SELECT * FROM customer_loyalty WHERE customer_id = :customer_id"
                data = await self.db_manager.fetch_one(query, {"customer_id": customer_id})
                return Loyalty(**data) if data else None
        except Exception as e:
            logger.error("Error retrieving customer loyalty", customer_id=customer_id, error=str(e))
            return None

    async def create_customer_interaction(self, interaction_data: CustomerInteractionCreate) -> Optional[CustomerInteraction]:
        """Create a new customer interaction record.

        Args:
            interaction_data: The data for the new customer interaction.

        Returns:
            The created CustomerInteraction if successful, otherwise None.
        """
        if not self._db_initialized: 
            logger.warning("Database not initialized. Cannot create customer interaction.")
            return None
        try:
            async with self.db_manager.get_session() as session:
                now = datetime.utcnow()
                interaction_dict = interaction_data.model_dump()
                interaction_dict.update({
                    "interaction_id": str(uuid4()),
                    "status": "open",
                    "created_at": now,
                    "updated_at": now,
                })
                created_data = await self.db_helper_interaction.create(session, interaction_dict)
                return CustomerInteraction(**created_data) if created_data else None
        except Exception as e:
            logger.error("Error creating customer interaction", customer_id=interaction_data.customer_id, error=str(e))
            return None

    async def process_message(self, message: AgentMessage):
        """
        Processes incoming messages from the Kafka bus.

        Args:
            message: The AgentMessage object to process.
        """
        logger.info("Processing message", message_type=message.type, sender=message.sender, correlation_id=message.correlation_id)
        try:
            if message.type == MessageType.CUSTOMER_REGISTERED:
                customer_id = message.data.get("customer_id")
                email = message.data.get("email")
                logger.info("Received CUSTOMER_REGISTERED message", customer_id=customer_id, email=email)
                # Potentially trigger loyalty program enrollment or welcome email
                await self.send_message(
                    "loyalty_agent",
                    MessageType.CUSTOMER_ENROLLED_LOYALTY,
                    {"customer_id": customer_id, "email": email, "tier": LoyaltyTier.BRONZE.value},
                    correlation_id=message.correlation_id
                )
            elif message.type == MessageType.ORDER_PLACED:
                customer_id = message.data.get("customer_id")
                order_id = message.data.get("order_id")
                total_amount = message.data.get("total_amount")
                logger.info("Received ORDER_PLACED message", customer_id=customer_id, order_id=order_id, total_amount=total_amount)
                # Update customer's purchase history, notify loyalty agent for points
                await self.send_message(
                    "loyalty_agent",
                    MessageType.POINTS_EARNED,
                    {"customer_id": customer_id, "order_id": order_id, "amount": total_amount},
                    correlation_id=message.correlation_id
                )
            elif message.type == MessageType.CUSTOMER_ACCOUNT_UPDATE:
                customer_id = message.data.get("customer_id")
                updates = message.data.get("updates")
                logger.info("Received CUSTOMER_ACCOUNT_UPDATE message", customer_id=customer_id, updates=updates)
                await self.update_customer_profile(customer_id, updates)
            else:
                logger.warning("Unhandled message type", message_type=message.type)
        except Exception as e:
            logger.error("Error processing Kafka message", message=message.model_dump_json(), error=str(e))
    
    async def initialize(self):
        """Initialize agent-specific components"""
        await super().initialize()
        logger.info(f"{self.agent_name} initialized successfully")
    
    async def cleanup(self):
        """Cleanup agent resources"""
        try:
            if hasattr(self, 'db_manager') and self.db_manager:
                await self.db_manager.close()
            await super().cleanup()
            logger.info(f"{self.agent_name} cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    @contextlib.asynccontextmanager
    async def lifespan_context(self, app: FastAPI):
        """Context manager for managing the lifespan of the FastAPI application.
        
        Initializes the agent resources before the server starts and cleans them up after the server shuts down.
        """
        logger.info("Customer Agent starting up...")
        try:
            await self.initialize_db()
            # Kafka consumer is started automatically by BaseAgent if configured
            logger.info("Customer Agent startup complete.")
        except Exception as e:
            logger.error("Customer Agent startup failed", error=str(e))
            # Log error but don't exit - let the agent run in degraded mode
            # The health endpoint will report the issue

        yield

        logger.info("Customer Agent shutting down...")
        try:
            await self.stop_kafka_consumer()
            if self.db_manager:
                await self.db_manager.disconnect()
            logger.info("Customer Agent shutdown complete.")
        except Exception as e:
            logger.error("Customer Agent shutdown failed", error=str(e))
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process customer-specific business logic
        
        Args:
            data: Dictionary containing operation type and parameters
            
        Returns:
            Dictionary with processing results
        """
        try:
            operation = data.get("operation", "get_profile")
            
            if operation == "get_profile":
                customer_id = data.get("customer_id")
                profile = await self.get_customer_profile(customer_id)
                return {"status": "success", "profile": profile}
            
            elif operation == "create_profile":
                profile_data = CustomerProfileCreate(**data.get("profile", {}))
                customer_id = await self.create_customer_profile(profile_data)
                return {"status": "success", "customer_id": customer_id}
            
            elif operation == "update_profile":
                customer_id = data.get("customer_id")
                updates = data.get("updates", {})
                result = await self.update_customer_profile(customer_id, updates)
                return {"status": "success", "result": result}
            
            elif operation == "add_address":
                customer_id = data.get("customer_id")
                address = data.get("address", {})
                address_id = await self.add_customer_address(customer_id, address)
                return {"status": "success", "address_id": address_id}
            
            elif operation == "update_loyalty":
                customer_id = data.get("customer_id")
                points = data.get("points", 0)
                result = await self.update_loyalty_points(customer_id, points)
                return {"status": "success", "result": result}
            
            else:
                return {"status": "error", "message": f"Unknown operation: {operation}"}
                
        except Exception as e:
            logger.error(f"Error in process_business_logic: {e}")
            return {"status": "error", "message": str(e)}


# =====================================================
# FASTAPI APP
# =====================================================

# FastAPI app moved to __init__ method as self.app

AGENT_ID = os.getenv("AGENT_ID", "customer_agent_001")
AGENT_TYPE = "customer_agent"
customer_agent = CustomerAgent(agent_id=AGENT_ID, agent_type=AGENT_TYPE)

# Apply CORS middleware to the module-level app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create module-level FastAPI app (Already done below)
app = FastAPI(title="Customer Agent API", lifespan=customer_agent.lifespan_context)

# The CORS middleware is now applied below the agent instantiation
# to ensure the agent object is fully initialized.

# Add CORS middleware for dashboard integration (Moved to agent instantiation block)




@app.get("/", tags=["General"])
async def root():
    """Root endpoint for the customer agent.

    Returns:
        A dictionary with a welcome message.
    """
    logger.info("Root endpoint accessed.")
    return {"message": "Customer agent is running."}


@app.get("/health", tags=["General"])
async def health_check():
    """Health check endpoint.

    Returns:
        A dictionary with the status of the agent.
    """
    logger.info("Health check endpoint accessed.")
    # Check database connection status
    db_status = "ok"
    if not customer_agent._db_initialized:
        db_status = "not initialized"
        logger.error("Health check: Database not initialized.")
    elif not customer_agent.db_manager:
        db_status = "disconnected"
        logger.error("Health check: Database disconnected.")

    # Check Kafka consumer status (assuming BaseAgent has a way to expose this)
    kafka_status = "ok" # Placeholder, actual implementation depends on BaseAgent details

    return {"status": "ok", "database": db_status, "kafka_consumer": kafka_status}


@app.get("/customers", response_model=List[CustomerProfile], tags=["Customers"])
async def get_all_customers_api():
    """Retrieve a list of all customer profiles.

    Returns:
        A list of CustomerProfile objects.

    Raises:
        HTTPException: If no customers are found or a server error occurs.
    """
    logger.info("API call: get_all_customers_api")
    try:
        customers = await customer_agent.get_all_customer_profiles()
        if not customers:
            raise HTTPException(status_code=404, detail="No customers found")
        return customers
    except Exception as e:
        logger.error("API Error: Failed to retrieve all customers", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve customers: {e}")


@app.get("/customers/{customer_id}", response_model=CustomerProfile, tags=["Customers"])
async def get_customer_api(customer_id: str = Path(..., description="The ID of the customer to retrieve")):
    """Retrieve a specific customer profile by ID.

    Args:
        customer_id: The unique identifier of the customer.

    Returns:
        The CustomerProfile object.

    Raises:
        HTTPException: If the customer is not found or a server error occurs.
    """
    logger.info("API call: get_customer_api", customer_id=customer_id)
    try:
        customer = await customer_agent.get_customer_profile_by_id(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer with ID {customer_id} not found")
        return customer
    except Exception as e:
        logger.error("API Error: Failed to retrieve customer", customer_id=customer_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve customer: {e}")


@app.post("/customers", response_model=CustomerProfile, status_code=201, tags=["Customers"])
async def create_customer_api(customer_data: CustomerProfileCreate = Body(..., description="Data for the new customer profile")):
    """Create a new customer profile.

    Args:
        customer_data: The data for the new customer profile.

    Returns:
        The newly created CustomerProfile object.

    Raises:
        HTTPException: If a customer with the email already exists or creation fails.
    """
    logger.info("API call: create_customer_api", email=customer_data.email)
    try:
        existing_customer = await customer_agent.get_customer_profile_by_email(customer_data.email)
        if existing_customer:
            raise HTTPException(status_code=409, detail=f"Customer with email {customer_data.email} already exists")

        customer = await customer_agent.create_customer_profile(customer_data)
        if not customer:
            raise HTTPException(status_code=500, detail="Failed to create customer profile")

        # Send message after successful creation
        await customer_agent.send_message(
            "all",
            MessageType.CUSTOMER_REGISTERED,
            {"customer_id": customer.customer_id, "email": customer.email},
            correlation_id=str(uuid4())
        )
        return customer
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("API Error: Failed to create customer profile", email=customer_data.email, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create customer profile: {e}")


@app.put("/customers/{customer_id}", response_model=CustomerProfile, tags=["Customers"])
async def update_customer_api(
    customer_id: str = Path(..., description="The ID of the customer to update"),
    update_data: Dict[str, Any] = Body(..., description="Fields to update for the customer profile")
):
    """Update an existing customer profile.

    Args:
        customer_id: The unique identifier of the customer.
        update_data: A dictionary containing the fields to update.

    Returns:
        The updated CustomerProfile object.

    Raises:
        HTTPException: If the customer is not found or update fails.
    """
    logger.info("API call: update_customer_api", customer_id=customer_id, update_data=update_data)
    try:
        customer = await customer_agent.update_customer_profile(customer_id, update_data)
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer with ID {customer_id} not found or update failed")
        
        # Send message about customer update
        await customer_agent.send_message(
            "all",
            MessageType.CUSTOMER_ACCOUNT_UPDATE,
            {"customer_id": customer.customer_id, "updates": update_data},
            correlation_id=str(uuid4())
        )
        return customer
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("API Error: Failed to update customer profile", customer_id=customer_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update customer profile: {e}")


@app.delete("/customers/{customer_id}", status_code=204, tags=["Customers"])
async def delete_customer_api(customer_id: str = Path(..., description="The ID of the customer to delete")):
    """Delete a customer profile.

    Args:
        customer_id: The unique identifier of the customer.

    Raises:
        HTTPException: If the customer is not found or deletion fails.
    """
    logger.info("API call: delete_customer_api", customer_id=customer_id)
    try:
        success = await customer_agent.delete_customer_profile(customer_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Customer with ID {customer_id} not found or delete failed")
        
        # Send message about customer deletion
        await customer_agent.send_message(
            "all",
            MessageType.CUSTOMER_DELETED,
            {"customer_id": customer_id},
            correlation_id=str(uuid4())
        )
        return
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("API Error: Failed to delete customer profile", customer_id=customer_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete customer profile: {e}")


@app.post("/customers/{customer_id}/addresses", response_model=CustomerAddress, status_code=201, tags=["Addresses"])
async def add_address_api(
    customer_id: str = Path(..., description="The ID of the customer to add address for"),
    address_data: CustomerAddressCreate = Body(..., description="Data for the new customer address")
):
    """Add a new address for a specific customer.

    Args:
        customer_id: The unique identifier of the customer.
        address_data: The data for the new address.

    Returns:
        The newly created CustomerAddress object.

    Raises:
        HTTPException: If the customer is not found or address creation fails.
    """
    logger.info("API call: add_address_api", customer_id=customer_id)
    try:
        # Ensure the customer exists before adding an address
        customer = await customer_agent.get_customer_profile_by_id(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer with ID {customer_id} not found")
        
        # Override customer_id in address_data to ensure consistency
        address_data.customer_id = customer_id
        new_address = await customer_agent.add_customer_address(address_data)
        if not new_address:
            raise HTTPException(status_code=500, detail="Failed to add address")
        
        await customer_agent.send_message(
            "all",
            MessageType.CUSTOMER_ADDRESS_ADDED,
            {"customer_id": customer_id, "address_id": str(new_address.address_id)},
            correlation_id=str(uuid4())
        )
        return new_address
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("API Error: Failed to add address", customer_id=customer_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to add address: {e}")


@app.get("/customers/{customer_id}/addresses", response_model=List[CustomerAddress], tags=["Addresses"])
async def get_addresses_api(customer_id: str = Path(..., description="The ID of the customer to retrieve addresses for")):
    """Retrieve all addresses for a specific customer.

    Args:
        customer_id: The unique identifier of the customer.

    Returns:
        A list of CustomerAddress objects.

    Raises:
        HTTPException: If the customer is not found or a server error occurs.
    """
    logger.info("API call: get_addresses_api", customer_id=customer_id)
    try:
        customer = await customer_agent.get_customer_profile_by_id(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer with ID {customer_id} not found")

        addresses = await customer_agent.get_customer_addresses(customer_id)
        return addresses
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("API Error: Failed to retrieve addresses", customer_id=customer_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve addresses: {e}")


@app.get("/customers/{customer_id}/loyalty", response_model=Loyalty, tags=["Loyalty"])
async def get_loyalty_api(customer_id: str = Path(..., description="The ID of the customer to retrieve loyalty info for")):
    """Retrieve loyalty information for a specific customer.

    Args:
        customer_id: The unique identifier of the customer.

    Returns:
        The Loyalty object.

    Raises:
        HTTPException: If loyalty information is not found or a server error occurs.
    """
    logger.info("API call: get_loyalty_api", customer_id=customer_id)
    try:
        loyalty = await customer_agent.get_customer_loyalty(customer_id)
        if not loyalty:
            raise HTTPException(status_code=404, detail=f"Loyalty information for customer ID {customer_id} not found")
        return loyalty
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("API Error: Failed to retrieve loyalty information", customer_id=customer_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve loyalty information: {e}")


@app.post("/customers/{customer_id}/interactions", response_model=CustomerInteraction, status_code=201, tags=["Interactions"])
async def create_interaction_api(
    customer_id: str = Path(..., description="The ID of the customer for the interaction"),
    interaction_data: CustomerInteractionCreate = Body(..., description="Data for the new customer interaction")
):
    """Create a new customer interaction record.

    Args:
        customer_id: The unique identifier of the customer.
        interaction_data: The data for the new interaction.

    Returns:
        The newly created CustomerInteraction object.

    Raises:
        HTTPException: If interaction creation fails.
    """
    logger.info("API call: create_interaction_api", customer_id=customer_id, interaction_type=interaction_data.interaction_type)
    try:
        # Ensure the customer exists
        customer = await customer_agent.get_customer_profile_by_id(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer with ID {customer_id} not found")

        interaction_data.customer_id = customer_id
        new_interaction = await customer_agent.create_customer_interaction(interaction_data)
        if not new_interaction:
            raise HTTPException(status_code=500, detail="Failed to create customer interaction")
        
        await customer_agent.send_message(
            "all",
            MessageType.CUSTOMER_INTERACTION_CREATED,
            {"customer_id": customer_id, "interaction_id": str(new_interaction.interaction_id), "type": new_interaction.interaction_type.value},
            correlation_id=str(uuid4())
        )
        return new_interaction
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("API Error: Failed to create interaction", customer_id=customer_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create interaction: {e}")


# =====================================================
# Uvicorn Runner
# =====================================================
# Uvicorn runner for FastAPI
if __name__ == "__main__":
    import uvicorn
    # Use environment variable for port, default to 8008
    port = int(os.getenv("CUSTOMER_AGENT_PORT", 8008))
    host = os.getenv("CUSTOMER_AGENT_HOST", "0.0.0.0")
    logger.info(f"Starting Customer Agent API on {host}:{port}")
    uvicorn.run(app, host=host, port=port)