
"""
Tax Agent - Multi-Agent E-Commerce System

This agent handles tax calculation by jurisdiction, tax exemption management,
tax reporting, compliance tracking, and multi-country support.

DATABASE SCHEMA (migration 017_tax_agent.sql):

CREATE TABLE tax_jurisdictions (
    jurisdiction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_code VARCHAR(2) NOT NULL,
    state_code VARCHAR(10),
    city VARCHAR(100),
    postal_code VARCHAR(20),
    tax_rate DECIMAL(5, 4) NOT NULL,
    tax_name VARCHAR(100), -- 'VAT', 'GST', 'Sales Tax'
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE tax_exemptions (
    exemption_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(100) NOT NULL,
    exemption_type VARCHAR(50) NOT NULL, -- 'resale', 'nonprofit', 'government', 'diplomatic'
    jurisdiction_id UUID REFERENCES tax_jurisdictions(jurisdiction_id),
    certificate_number VARCHAR(200),
    valid_from DATE NOT NULL,
    valid_until DATE,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE tax_calculations (
    calculation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id VARCHAR(100) NOT NULL,
    customer_id VARCHAR(100),
    subtotal DECIMAL(10, 2) NOT NULL,
    tax_amount DECIMAL(10, 2) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    jurisdiction_breakdown JSONB, -- Breakdown by jurisdiction
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tax_reports (
    report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_type VARCHAR(50) NOT NULL, -- 'monthly', 'quarterly', 'annual'
    jurisdiction_id UUID REFERENCES tax_jurisdictions(jurisdiction_id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    total_sales DECIMAL(12, 2) NOT NULL,
    total_tax_collected DECIMAL(12, 2) NOT NULL,
    report_data JSONB,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID
from enum import Enum

from shared.db_helpers import DatabaseHelper

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field
import structlog
import sys
import os

from dotenv import load_dotenv
load_dotenv()

current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.base_agent import BaseAgent, MessageType, AgentMessage
from shared.database import DatabaseManager, get_database_manager

logger = structlog.get_logger(__name__)

# MODELS
class Address(BaseModel):
    """Represents a physical address for tax jurisdiction determination."""
    country_code: str
    state_code: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None

class TaxJurisdiction(BaseModel):
    """Represents a tax jurisdiction with its associated tax rate and details."""
    jurisdiction_id: UUID
    country_code: str
    state_code: Optional[str]
    tax_rate: Decimal
    tax_name: str
    is_active: bool

    class Config:
        from_attributes = True

class TaxCalculationRequest(BaseModel):
    """Request model for calculating tax on an order."""
    order_id: str
    customer_id: str
    subtotal: Decimal
    shipping_address: Address
    billing_address: Address
    items: List[Dict[str, Any]] = []

class TaxBreakdown(BaseModel):
    """Represents the tax breakdown for a single jurisdiction."""
    jurisdiction_id: UUID
    jurisdiction_name: str
    taxable_amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal

class TaxCalculationResponse(BaseModel):
    """Response model for a tax calculation, including total tax and breakdown."""
    calculation_id: UUID
    order_id: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    breakdown: List[TaxBreakdown]
    is_exempt: bool = False
    exemption_reason: Optional[str] = None

class TaxExemptionCreate(BaseModel):
    """Request model for creating a new tax exemption."""
    customer_id: str
    exemption_type: str
    jurisdiction_id: Optional[UUID] = None
    certificate_number: str
    valid_from: date
    valid_until: Optional[date] = None

class TaxReportRequest(BaseModel):
    """Request model for generating a tax report."""
    report_type: str  # 'monthly', 'quarterly', 'annual'
    jurisdiction_id: Optional[UUID] = None
    period_start: date
    period_end: date

# REPOSITORY
class TaxRepository:
    """Manages database operations for tax-related data."""
    def __init__(self, db_helper: DatabaseHelper):
        """Initializes the TaxRepository with a DatabaseHelper instance.

        Args:
            db_helper (DatabaseHelper): The database helper for interacting with the database.
        """
        self.db_helper = db_helper
    
    async def get_jurisdiction_by_address(self, address: Address) -> Optional[TaxJurisdiction]:
        """Find tax jurisdiction for address."""
        query = """
            SELECT * FROM tax_jurisdictions
            WHERE country_code = $1 AND is_active = true
        """
        params = [address.country_code]
        
        if address.state_code:
            query += " AND (state_code = $2 OR state_code IS NULL)"
            params.append(address.state_code)
        
        query += " ORDER BY state_code DESC NULLS LAST LIMIT 1"
        
        async with self.db_helper.db_manager.get_session() as session:
            result = await self.db_helper.get_one(session, query, *params)
            return TaxJurisdiction(**result) if result else None
    
    async def check_tax_exemption(
        self, customer_id: str, jurisdiction_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Check if customer has valid tax exemption."""
        query = """
            SELECT * FROM tax_exemptions
            WHERE customer_id = $1
            AND (jurisdiction_id = $2 OR jurisdiction_id IS NULL)
            AND is_active = true
            AND valid_from <= CURRENT_DATE
            AND (valid_until IS NULL OR valid_until >= CURRENT_DATE)
            LIMIT 1
        """
        async with self.db_helper.db_manager.get_session() as session:
            result = await self.db_helper.get_one(session, query, customer_id, jurisdiction_id)
            return dict(result) if result else None
    
    async def save_tax_calculation(self, calc_data: Dict[str, Any]) -> UUID:
        """Saves a tax calculation record to the database.

        Args:
            calc_data (Dict[str, Any]): A dictionary containing the tax calculation data.

        Returns:
            UUID: The ID of the saved tax calculation.
        """
        query = """
            INSERT INTO tax_calculations (order_id, customer_id, subtotal, tax_amount,
                                         total_amount, jurisdiction_breakdown)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING calculation_id
        """
        async with self.db_helper.db_manager.get_session() as session:
            result = await self.db_helper.create(session, query, calc_data['order_id'], calc_data['customer_id'],
                                                calc_data['subtotal'], calc_data['tax_amount'],
                                                calc_data['total_amount'], str(calc_data.get('breakdown', [])))
        return result['calculation_id']
    
    async def create_tax_exemption(self, exemption_data: TaxExemptionCreate) -> UUID:
        """Creates a new tax exemption record in the database.

        Args:
            exemption_data (TaxExemptionCreate): The data for the tax exemption to create.

        Returns:
            UUID: The ID of the created tax exemption.
        """
        query = """
            INSERT INTO tax_exemptions (customer_id, exemption_type, jurisdiction_id,
                                       certificate_number, valid_from, valid_until)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING exemption_id
        """
        async with self.db_helper.db_manager.get_session() as session:
            result = await self.db_helper.create(session, query, exemption_data.customer_id, exemption_data.exemption_type,
                                                exemption_data.jurisdiction_id, exemption_data.certificate_number,
                                                exemption_data.valid_from, exemption_data.valid_until)
        return result['exemption_id']
    
    async def generate_tax_report(self, report_request: TaxReportRequest) -> UUID:
        """Generates and saves a tax report to the database.

        Args:
            report_request (TaxReportRequest): The request data for generating the report.

        Returns:
            UUID: The ID of the generated tax report.
        """
        # In production, aggregate tax_calculations table
        query = """
            INSERT INTO tax_reports (report_type, jurisdiction_id, period_start, period_end,
                                    total_sales, total_tax_collected, report_data)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING report_id
        """
        # Simulated values
        total_sales = Decimal("10000.00")
        total_tax = Decimal("1000.00")
        
        async with self.db_helper.db_manager.get_session() as session:
            result = await self.db_helper.create(session, query, report_request.report_type, report_request.jurisdiction_id,
                                                report_request.period_start, report_request.period_end,
                                                total_sales, total_tax, str({}))
        return result['report_id']

# SERVICE
class TaxService:
    """Provides business logic for tax calculations, exemptions, and reporting."""
    def __init__(self, repo: TaxRepository):
        """Initializes the TaxService with a TaxRepository instance.

        Args:
            repo (TaxRepository): The repository for database operations.
        """
        self.repo = repo
    
    async def calculate_tax(self, request: TaxCalculationRequest) -> TaxCalculationResponse:
        """Calculates tax for a given order based on shipping address and exemptions.

        Args:
            request (TaxCalculationRequest): The tax calculation request data.

        Returns:
            TaxCalculationResponse: The response containing the calculated tax and breakdown.
        """
        # Get jurisdiction for shipping address
        jurisdiction = await self.repo.get_jurisdiction_by_address(request.shipping_address)

            if not jurisdiction:
                # No tax jurisdiction found - return zero tax
                calculation_id = await self.repo.save_tax_calculation({
                    'order_id': request.order_id,
                    'customer_id': request.customer_id,
                    'subtotal': request.subtotal,
                    'tax_amount': Decimal("0.00"),
                    'total_amount': request.subtotal,
                    'breakdown': []
                })

                return TaxCalculationResponse(
                    calculation_id=calculation_id,
                    order_id=request.order_id,
                    subtotal=request.subtotal,
                    tax_amount=Decimal("0.00"),
                    total_amount=request.subtotal,
                    breakdown=[]
                )

            # Check for tax exemption
            exemption = await self.repo.check_tax_exemption(
                request.customer_id, jurisdiction.jurisdiction_id
            )

            if exemption:
                calculation_id = await self.repo.save_tax_calculation({
                    'order_id': request.order_id,
                    'customer_id': request.customer_id,
                    'subtotal': request.subtotal,
                    'tax_amount': Decimal("0.00"),
                    'total_amount': request.subtotal,
                    'breakdown': []
                })

                return TaxCalculationResponse(
                    calculation_id=calculation_id,
                    order_id=request.order_id,
                    subtotal=request.subtotal,
                    tax_amount=Decimal("0.00"),
                    total_amount=request.subtotal,
                    breakdown=[],
                    is_exempt=True,
                    exemption_reason=exemption['exemption_type']
                )

            # Calculate tax
            tax_amount = request.subtotal * jurisdiction.tax_rate
            total_amount = request.subtotal + tax_amount

            breakdown = [TaxBreakdown(
                jurisdiction_id=jurisdiction.jurisdiction_id,
                jurisdiction_name=f"{jurisdiction.country_code} {jurisdiction.tax_name}",
                taxable_amount=request.subtotal,
                tax_rate=jurisdiction.tax_rate,
                tax_amount=tax_amount
            )]

            # Save calculation
            calculation_id = await self.repo.save_tax_calculation({
                'order_id': request.order_id,
                'customer_id': request.customer_id,
                'subtotal': request.subtotal,
                'tax_amount': tax_amount,
                'total_amount': total_amount,
                'breakdown': [b.dict() for b in breakdown]
            })

            logger.info("tax_calculated", order_id=request.order_id,
                       tax_amount=float(tax_amount), jurisdiction=jurisdiction.country_code)

        try:
            if not jurisdiction:
                # No tax jurisdiction found - return zero tax
                calculation_id = await self.repo.save_tax_calculation({
                    'order_id': request.order_id,
                    'customer_id': request.customer_id,
                    'subtotal': request.subtotal,
                    'tax_amount': Decimal("0.00"),
                    'total_amount': request.subtotal,
                    'breakdown': []
                })

                return TaxCalculationResponse(
                    calculation_id=calculation_id,
                    order_id=request.order_id,
                    subtotal=request.subtotal,
                    tax_amount=Decimal("0.00"),
                    total_amount=request.subtotal,
                    breakdown=[]
                )

            # Check for tax exemption
            exemption = await self.repo.check_tax_exemption(
                request.customer_id, jurisdiction.jurisdiction_id
            )

            if exemption:
                calculation_id = await self.repo.save_tax_calculation({
                    'order_id': request.order_id,
                    'customer_id': request.customer_id,
                    'subtotal': request.subtotal,
                    'tax_amount': Decimal("0.00"),
                    'total_amount': request.subtotal,
                    'breakdown': []
                })

                return TaxCalculationResponse(
                    calculation_id=calculation_id,
                    order_id=request.order_id,
                    subtotal=request.subtotal,
                    tax_amount=Decimal("0.00"),
                    total_amount=request.subtotal,
                    breakdown=[],
                    is_exempt=True,
                    exemption_reason=exemption['exemption_type']
                )

            # Calculate tax
            tax_amount = request.subtotal * jurisdiction.tax_rate
            total_amount = request.subtotal + tax_amount

            breakdown = [TaxBreakdown(
                jurisdiction_id=jurisdiction.jurisdiction_id,
                jurisdiction_name=f"{jurisdiction.country_code} {jurisdiction.tax_name}",
                taxable_amount=request.subtotal,
                tax_rate=jurisdiction.tax_rate,
                tax_amount=tax_amount
            )]

            # Save calculation
            calculation_id = await self.repo.save_tax_calculation({
                'order_id': request.order_id,
                'customer_id': request.customer_id,
                'subtotal': request.subtotal,
                'tax_amount': tax_amount,
                'total_amount': total_amount,
                'breakdown': [b.dict() for b in breakdown]
            })

            logger.info("tax_calculated", order_id=request.order_id,
                       tax_amount=float(tax_amount), jurisdiction=jurisdiction.country_code)

            return TaxCalculationResponse(
                calculation_id=calculation_id,
                order_id=request.order_id,
                subtotal=request.subtotal,
                tax_amount=tax_amount,
                total_amount=total_amount,
                breakdown=breakdown
            )
        except Exception as e:
            logger.error("Error calculating tax", error=str(e), order_id=request.order_id)
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred during tax calculation: {e}")

class TaxAgent(BaseAgent):
    """Tax Agent for calculating taxes, managing exemptions, and generating reports."""
    def __init__(self, agent_id: str, agent_type: str):
        super().__init__(agent_id, agent_type)
        self.db_manager: Optional[DatabaseManager] = None
        self.db_helper: Optional[DatabaseHelper] = None
        self.tax_service: Optional[TaxService] = None
        self._db_initialized: bool = False

    async def setup(self):
        """Initialize database connections and tax service."""
        logger.info("TaxAgent setup started")
        try:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                logger.error("DATABASE_URL environment variable not set")
                raise ValueError("DATABASE_URL environment variable not set")
            self.db_manager = await get_database_manager(db_url)
            self.db_helper = DatabaseHelper(self.db_manager, logger)
            self.tax_service = TaxService(TaxRepository(self.db_helper))
            self._db_initialized = True
            logger.info("TaxAgent setup complete")
        except Exception as e:
            logger.error("TaxAgent setup failed", error=str(e))
            self._db_initialized = False

    async def process_message(self, message: AgentMessage) -> List[AgentMessage]:
        """Process incoming messages for the Tax Agent."""
        logger.info("TaxAgent received message", message_type=message.message_type, payload=message.payload)
        
        if not self._db_initialized:
            logger.error("Database not initialized, cannot process message.")
            return []

        response_messages = []

        try:
            if message.message_type == MessageType.CALCULATE_TAX:
                request = TaxCalculationRequest(**message.payload)
                calculation_response = await self.tax_service.calculate_tax(request)
                response_messages.append(AgentMessage(
                    agent_id=self.agent_id,
                    agent_type=self.agent_type,
                    message_type=MessageType.TAX_CALCULATION_RESULT,
                    payload=calculation_response.dict()
                ))
            elif message.message_type == MessageType.CREATE_TAX_EXEMPTION:
                exemption_data = TaxExemptionCreate(**message.payload)
                exemption_id = await self.tax_service.repo.create_tax_exemption(exemption_data)
                response_messages.append(AgentMessage(
                    agent_id=self.agent_id,
                    agent_type=self.agent_type,
                    message_type=MessageType.TAX_EXEMPTION_CREATED,
                    payload={"exemption_id": str(exemption_id), "message": "Tax exemption created"}
                ))
            elif message.message_type == MessageType.GENERATE_TAX_REPORT:
                report_request = TaxReportRequest(**message.payload)
                report_id = await self.tax_service.repo.generate_tax_report(report_request)
                response_messages.append(AgentMessage(
                    agent_id=self.agent_id,
                    agent_type=self.agent_type,
                    message_type=MessageType.TAX_REPORT_GENERATED,
                    payload={"report_id": str(report_id), "message": "Tax report generated"}
                ))
            else:
                logger.warning("Unknown message type received", message_type=message.message_type)
        except Exception as e:
            logger.error("Error processing message", error=str(e), message_type=message.message_type)
            response_messages.append(AgentMessage(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                message_type=MessageType.ERROR,
                payload={"error": str(e), "original_message_type": message.message_type.value}
            ))
        
        return response_messages


# FASTAPI APP
app = FastAPI(title="Tax Agent API", version="1.0.0")

tax_agent_instance: Optional['TaxAgent'] = None

async def get_tax_agent() -> 'TaxAgent':
    """Dependency that provides a singleton TaxAgent instance."""
    global tax_agent_instance
    if tax_agent_instance is None:
        tax_agent_instance = TaxAgent(agent_id="tax_agent_01", agent_type="tax_agent")
        await tax_agent_instance.setup()
    return tax_agent_instance

async def get_tax_service(agent: 'TaxAgent' = Depends(get_tax_agent)) -> TaxService:
    """Dependency that provides the TaxService instance, ensuring the agent is initialized."""
    if not agent._db_initialized or agent.tax_service is None:
        logger.error("Database not initialized for TaxAgent")
        raise HTTPException(status_code=500, detail="Database not initialized")
    return agent.tax_service

# ENDPOINTS
@app.get("/")
async def root():
    """Root endpoint for the Tax Agent API."""
    return {"message": "Tax Agent is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint to verify the agent's status."""
    return {"status": "healthy", "agent": "tax_agent", "version": "1.0.0"}

@app.post("/api/v1/tax/calculate", response_model=TaxCalculationResponse)
async def calculate_tax(
    request: TaxCalculationRequest = Body(...),
    service: TaxService = Depends(get_tax_service),
    agent: 'TaxAgent' = Depends(get_tax_agent)
):
    """Calculates tax for an order based on the provided request.

    Args:
        request (TaxCalculationRequest): The tax calculation request data.
        service (TaxService): The TaxService instance, injected via dependency.
        agent (TaxAgent): The TaxAgent instance, injected via dependency.

    Returns:
        TaxCalculationResponse: The calculated tax details.
    """
    if not agent._db_initialized:
        logger.error("TaxAgent not initialized for endpoint")
        raise HTTPException(status_code=500, detail="TaxAgent not initialized")
    try:
        response = await service.calculate_tax(request)
        return response
    except Exception as e:
        logger.error("calculate_tax_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/tax/exemptions")
async def create_exemption(
    exemption_data: TaxExemptionCreate = Body(...),
    service: TaxService = Depends(get_tax_service),
    agent: 'TaxAgent' = Depends(get_tax_agent)
):
    """Creates a new tax exemption.

    Args:
        exemption_data (TaxExemptionCreate): The data for the tax exemption to create.
        service (TaxService): The TaxService instance, injected via dependency.
        agent (TaxAgent): The TaxAgent instance, injected via dependency.

    Returns:
        Dict[str, Any]: A dictionary containing the exemption ID and a success message.
    """
    if not agent._db_initialized:
        logger.error("TaxAgent not initialized for endpoint")
        raise HTTPException(status_code=500, detail="TaxAgent not initialized")
    try:
        exemption_id = await service.repo.create_tax_exemption(exemption_data)
        return {"exemption_id": exemption_id, "message": "Tax exemption created"}
    except Exception as e:
        logger.error("create_exemption_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/tax/reports")
async def generate_report(
    report_request: TaxReportRequest = Body(...),
    service: TaxService = Depends(get_tax_service),
    agent: 'TaxAgent' = Depends(get_tax_agent)
):
    """Generates a tax report.

    Args:
        report_request (TaxReportRequest): The request data for generating the report.
        service (TaxService): The TaxService instance, injected via dependency.
        agent (TaxAgent): The TaxAgent instance, injected via dependency.

    Returns:
        Dict[str, Any]: A dictionary containing the report ID and a success message.
    """
    if not agent._db_initialized:
        logger.error("TaxAgent not initialized for endpoint")
        raise HTTPException(status_code=500, detail="TaxAgent not initialized")
    try:
        report_id = await service.repo.generate_tax_report(report_request)
        return {"report_id": report_id, "message": "Tax report generated"}
    except Exception as e:
        logger.error("generate_report_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("TAX_AGENT_PORT", 8016))
    uvicorn.run(app, host="0.0.0.0", port=port)

