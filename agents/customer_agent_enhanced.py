"""
Customer Agent Enhanced - Multi-Agent E-Commerce System

This agent provides comprehensive customer management including profiles, addresses,
preferences, loyalty programs, segmentation, and customer interactions.
"""

import asyncio
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID
from enum import Enum

from shared.db_helpers import DatabaseHelper

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field, EmailStr
import structlog
import sys
import os

# Path setup
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.database import DatabaseManager, get_database_manager


logger = structlog.get_logger(__name__)


# =====================================================
# ENUMS
# =====================================================

class CustomerType(str, Enum):
    INDIVIDUAL = "individual"
    BUSINESS = "business"


class AccountStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"


class LoyaltyTier(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


class InteractionType(str, Enum):
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
    email: EmailStr
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    customer_type: CustomerType = CustomerType.INDIVIDUAL


class CustomerProfileCreate(CustomerProfileBase):
    customer_id: str


class CustomerProfile(CustomerProfileBase):
    customer_id: str
    account_status: AccountStatus
    email_verified: bool = False
    phone_verified: bool = False
    registration_date: datetime
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerAddressBase(BaseModel):
    address_type: str
    address_label: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    street_address_1: str
    street_address_2: Optional[str] = None
    city: str
    state_province: Optional[str] = None
    postal_code: str
    country_code: str
    phone: Optional[str] = None
    is_default: bool = False


class CustomerAddressCreate(CustomerAddressBase):
    customer_id: str


class CustomerAddress(CustomerAddressBase):
    address_id: UUID
    customer_id: str
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LoyaltyBase(BaseModel):
    customer_id: str
    loyalty_tier: LoyaltyTier = LoyaltyTier.BRONZE
    points_balance: int = 0


class Loyalty(LoyaltyBase):
    loyalty_id: UUID
    points_lifetime: int = 0
    tier_start_date: date
    referral_code: Optional[str] = None
    referrals_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerInteractionCreate(BaseModel):
    customer_id: str
    interaction_type: InteractionType
    interaction_channel: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    priority: str = "medium"


class CustomerInteraction(CustomerInteractionCreate):
    interaction_id: UUID
    status: str = "open"
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# REPOSITORY
# =====================================================

class CustomerRepository:
    """Repository for customer operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_customer(self, customer: CustomerProfileCreate) -> CustomerProfile:
        """Create a new customer profile."""
        query = """
            INSERT INTO customer_profiles (customer_id, email, phone, first_name, last_name,
                                          date_of_birth, gender, customer_type)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING *
        """
        result = await self.db.fetch_one(
            query, customer.customer_id, customer.email, customer.phone,
            customer.first_name, customer.last_name, customer.date_of_birth,
            customer.gender, customer.customer_type.value
        )
        return CustomerProfile(**result)
    
    async def get_customer(self, customer_id: str) -> Optional[CustomerProfile]:
        """Get customer profile by ID."""
        query = "SELECT * FROM customer_profiles WHERE customer_id = $1"
        result = await self.db.fetch_one(query, customer_id)
        return CustomerProfile(**result) if result else None
    
    async def get_customer_by_email(self, email: str) -> Optional[CustomerProfile]:
        """Get customer profile by email."""
        query = "SELECT * FROM customer_profiles WHERE email = $1"
        result = await self.db.fetch_one(query, email)
        return CustomerProfile(**result) if result else None
    
    async def update_customer(
        self,
        customer_id: str,
        updates: Dict[str, Any]
    ) -> Optional[CustomerProfile]:
        """Update customer profile."""
        set_clause = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(updates.keys())])
        query = f"""
            UPDATE customer_profiles 
            SET {set_clause}
            WHERE customer_id = $1
            RETURNING *
        """
        values = [customer_id] + list(updates.values())
        result = await self.db.fetch_one(query, *values)
        return CustomerProfile(**result) if result else None
    
    async def add_address(self, address: CustomerAddressCreate) -> CustomerAddress:
        """Add a new customer address."""
        query = """
            INSERT INTO customer_addresses (customer_id, address_type, address_label,
                                           first_name, last_name, street_address_1,
                                           street_address_2, city, state_province,
                                           postal_code, country_code, phone, is_default)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING *
        """
        result = await self.db.fetch_one(
            query, address.customer_id, address.address_type, address.address_label,
            address.first_name, address.last_name, address.street_address_1,
            address.street_address_2, address.city, address.state_province,
            address.postal_code, address.country_code, address.phone, address.is_default
        )
        return CustomerAddress(**result)
    
    async def get_customer_addresses(self, customer_id: str) -> List[CustomerAddress]:
        """Get all addresses for a customer."""
        query = "SELECT * FROM customer_addresses WHERE customer_id = $1 ORDER BY is_default DESC"
        results = await self.db.fetch_all(query, customer_id)
        return [CustomerAddress(**r) for r in results]
    
    async def get_loyalty(self, customer_id: str) -> Optional[Loyalty]:
        """Get customer loyalty information."""
        query = "SELECT * FROM customer_loyalty WHERE customer_id = $1"
        result = await self.db.fetch_one(query, customer_id)
        return Loyalty(**result) if result else None
    
    async def create_interaction(
        self,
        interaction: CustomerInteractionCreate
    ) -> CustomerInteraction:
        """Create a new customer interaction."""
        query = """
            INSERT INTO customer_interactions (customer_id, interaction_type, interaction_channel,
                                              subject, description, priority)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
        """
        result = await self.db.fetch_one(
            query, interaction.customer_id, interaction.interaction_type.value,
            interaction.interaction_channel, interaction.subject,
            interaction.description, interaction.priority
        )
        return CustomerInteraction(**result)


# =====================================================
# SERVICE
# =====================================================

class CustomerService:
    """Service for customer operations."""
    
    def __init__(self, repo: CustomerRepository):
        self.repo = repo
    
    async def register_customer(
        self,
        customer_data: CustomerProfileCreate
    ) -> Dict[str, Any]:
        """Register a new customer."""
        # Check if email already exists
        existing = await self.repo.get_customer_by_email(customer_data.email)
        if existing:
            raise ValueError(f"Customer with email {customer_data.email} already exists")
        
        # Create customer profile
        customer = await self.repo.create_customer(customer_data)
        
        logger.info(
            "customer_registered",
            customer_id=customer.customer_id,
            email=customer.email
        )
        
        return {
            "customer": customer,
            "success": True,
            "message": "Customer registered successfully"
        }
    
    async def get_customer_details(self, customer_id: str) -> Dict[str, Any]:
        """Get complete customer details including addresses and loyalty."""
        customer = await self.repo.get_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        addresses = await self.repo.get_customer_addresses(customer_id)
        loyalty = await self.repo.get_loyalty(customer_id)
        
        return {
            "customer": customer,
            "addresses": addresses,
            "loyalty": loyalty
        }


# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI(
    title="Customer Agent Enhanced API",
    description="Comprehensive customer management for multi-agent e-commerce",
    version="1.0.0"
)


async def get_customer_service() -> CustomerService:
    """Dependency injection for customer service."""
    db_manager = await get_database_manager()
    repo = CustomerRepository(db_manager)
    return CustomerService(repo)


# =====================================================
# API ENDPOINTS
# =====================================================

@app.post("/api/v1/customers", response_model=CustomerProfile)
async def create_customer(
    customer: CustomerProfileCreate = Body(...),
    service: CustomerService = Depends(get_customer_service)
):
    """Create a new customer profile."""
    try:
        result = await service.register_customer(customer)
        return result["customer"]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("create_customer_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/customers/{customer_id}", response_model=Dict[str, Any])
async def get_customer(
    customer_id: str = Path(...),
    service: CustomerService = Depends(get_customer_service)
):
    """Get customer details."""
    try:
        result = await service.get_customer_details(customer_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("get_customer_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/customers/{customer_id}/addresses", response_model=CustomerAddress)
async def add_customer_address(
    customer_id: str = Path(...),
    address: CustomerAddressBase = Body(...),
    service: CustomerService = Depends(get_customer_service)
):
    """Add a new customer address."""
    try:
        address_create = CustomerAddressCreate(customer_id=customer_id, **address.dict())
        result = await service.repo.add_address(address_create)
        return result
    except Exception as e:
        logger.error("add_address_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/customers/{customer_id}/addresses", response_model=List[CustomerAddress])
async def get_customer_addresses(
    customer_id: str = Path(...),
    service: CustomerService = Depends(get_customer_service)
):
    """Get all customer addresses."""
    try:
        results = await service.repo.get_customer_addresses(customer_id)
        return results
    except Exception as e:
        logger.error("get_addresses_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/customers/{customer_id}/loyalty", response_model=Loyalty)
async def get_customer_loyalty(
    customer_id: str = Path(...),
    service: CustomerService = Depends(get_customer_service)
):
    """Get customer loyalty information."""
    try:
        result = await service.repo.get_loyalty(customer_id)
        if not result:
            raise HTTPException(status_code=404, detail="Loyalty information not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_loyalty_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/customers/{customer_id}/interactions", response_model=CustomerInteraction)
async def create_customer_interaction(
    customer_id: str = Path(...),
    interaction: CustomerInteractionCreate = Body(...),
    service: CustomerService = Depends(get_customer_service)
):
    """Create a new customer interaction."""
    try:
        result = await service.repo.create_interaction(interaction)
        return result
    except Exception as e:
        logger.error("create_interaction_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "customer_agent_enhanced", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

