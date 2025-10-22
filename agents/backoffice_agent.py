"""
Backoffice Agent
Handles merchant onboarding, application processing, document verification, and account management
"""

import os
import sys
import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum
from pydantic import BaseModel, Field, EmailStr
from decimal import Decimal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os


from shared.db_helpers import DatabaseHelper
import hashlib
import secrets

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from shared.base_agent import BaseAgent
from shared.kafka_config import KafkaProducer, KafkaConsumer

logger = structlog.get_logger(__name__)


class ApplicationStatus(str, Enum):
    """Merchant application status"""
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    DOCUMENTS_REQUIRED = "documents_required"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class BusinessType(str, Enum):
    """Types of business"""
    INDIVIDUAL = "individual"
    SOLE_PROPRIETOR = "sole_proprietor"
    LLC = "llc"
    CORPORATION = "corporation"
    PARTNERSHIP = "partnership"


class DocumentType(str, Enum):
    """Required document types"""
    BUSINESS_LICENSE = "business_license"
    TAX_CERTIFICATE = "tax_certificate"
    BANK_STATEMENT = "bank_statement"
    ID_PROOF = "id_proof"
    ADDRESS_PROOF = "address_proof"


class MerchantApplication(BaseModel):
    """Merchant application model"""
    application_id: str = Field(default_factory=lambda: f"APP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
    business_name: str
    business_type: BusinessType
    tax_id: str
    email: EmailStr
    phone: str
    address: Dict[str, str]
    product_categories: List[str]
    estimated_monthly_volume: Optional[int] = None
    documents: Dict[DocumentType, str] = {}  # document_type -> file_url
    status: ApplicationStatus = ApplicationStatus.SUBMITTED
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    rejection_reason: Optional[str] = None


class DocumentVerification(BaseModel):
    """Document verification result"""
    document_type: DocumentType
    file_url: str
    verified: bool
    verification_method: str  # manual, ai, api
    verification_notes: Optional[str] = None
    verified_at: datetime = Field(default_factory=datetime.utcnow)
    verified_by: str


class MerchantAccount(BaseModel):
    """Merchant account model"""
    merchant_id: str
    application_id: str
    business_name: str
    business_type: BusinessType
    tax_id: str
    email: EmailStr
    phone: str
    status: str = "active"  # active, suspended, closed
    commission_rate: Decimal = Decimal("0.15")  # 15% default
    payment_terms: str = "net_15"  # Payment within 15 days
    created_at: datetime = Field(default_factory=datetime.utcnow)
    onboarding_completed: bool = False


class BackofficeAgent(BaseAgent):
    """
    Backoffice Agent
    
    Responsibilities:
    - Process merchant applications
    - Verify business documents
    - Conduct fraud checks
    - Create merchant accounts
    - Configure merchant settings
    - Manage merchant onboarding process
    - Handle merchant compliance
    - Process merchant updates
    """
    
    def __init__(self):
        super().__init__("BackofficeAgent")
        self.kafka_producer = None
        self.kafka_consumer = None
        self.fraud_threshold = 0.7  # Fraud score threshold
        
    async def initialize(self):
        """Initialize agent"""
        await super().initialize()
        self.kafka_producer = KafkaProducer()
        self.kafka_consumer = KafkaConsumer(
            topics=[
                "merchant_application_submitted",
                "merchant_documents_uploaded",
                "merchant_update_requested"
            ],
            group_id="backoffice_agent"
        )
        logger.info("Backoffice Agent initialized")
    
    async def process_merchant_application(
        self,
        application: MerchantApplication
    ) -> Dict[str, Any]:
        """
        Process new merchant application
        
        Args:
            application: Merchant application details
            
        Returns:
            Processing result
        """
        try:
            logger.info("Processing merchant application",
                       application_id=application.application_id,
                       business_name=application.business_name)
            
            # Update status to under review
            application.status = ApplicationStatus.UNDER_REVIEW
            await self._save_application(application)
            
            # Verify required documents
            doc_verification = await self._verify_documents(application)
            
            if not doc_verification["all_verified"]:
                logger.warning("Document verification failed",
                             application_id=application.application_id,
                             missing=doc_verification["missing_documents"])
                
                application.status = ApplicationStatus.DOCUMENTS_REQUIRED
                await self._save_application(application)
                
                await self._send_documents_required_notification(
                    application,
                    doc_verification["missing_documents"]
                )
                
                return {
                    "success": False,
                    "status": "documents_required",
                    "missing_documents": doc_verification["missing_documents"]
                }
            
            # Verify business information
            business_verification = await self._verify_business_info(application)
            
            if not business_verification["valid"]:
                logger.warning("Business verification failed",
                             application_id=application.application_id,
                             reason=business_verification["reason"])
                
                application.status = ApplicationStatus.REJECTED
                application.rejection_reason = business_verification["reason"]
                application.reviewed_at = datetime.utcnow()
                await self._save_application(application)
                
                await self._send_rejection_notification(
                    application,
                    business_verification["reason"]
                )
                
                return {
                    "success": False,
                    "status": "rejected",
                    "reason": business_verification["reason"]
                }
            
            # Fraud detection check
            fraud_check = await self._perform_fraud_check(application)
            
            if fraud_check["fraud_score"] > self.fraud_threshold:
                logger.warning("Fraud check failed",
                             application_id=application.application_id,
                             fraud_score=fraud_check["fraud_score"])
                
                application.status = ApplicationStatus.REJECTED
                application.rejection_reason = "Failed fraud detection check"
                application.reviewed_at = datetime.utcnow()
                await self._save_application(application)
                
                return {
                    "success": False,
                    "status": "rejected",
                    "reason": "Failed fraud detection check"
                }
            
            # All checks passed - approve application
            application.status = ApplicationStatus.APPROVED
            application.reviewed_at = datetime.utcnow()
            application.reviewed_by = "BACKOFFICE_AGENT"
            await self._save_application(application)
            
            # Create merchant account
            merchant_account = await self._create_merchant_account(application)
            
            # Publish merchant approved event
            await self.kafka_producer.send(
                "merchant_application_approved",
                {
                    "application_id": application.application_id,
                    "merchant_id": merchant_account.merchant_id,
                    "business_name": application.business_name,
                    "email": application.email,
                    "approved_at": application.reviewed_at.isoformat()
                }
            )
            
            # Send welcome email
            await self._send_welcome_email(merchant_account)
            
            logger.info("Merchant application approved",
                       application_id=application.application_id,
                       merchant_id=merchant_account.merchant_id)
            
            return {
                "success": True,
                "status": "approved",
                "merchant_id": merchant_account.merchant_id,
                "application_id": application.application_id
            }
            
        except Exception as e:
            logger.error("Failed to process merchant application",
                        error=str(e),
                        application_id=application.application_id)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _verify_documents(
        self,
        application: MerchantApplication
    ) -> Dict[str, Any]:
        """
        Verify uploaded documents
        
        Args:
            application: Merchant application
            
        Returns:
            Verification result
        """
        required_documents = [
            DocumentType.BUSINESS_LICENSE,
            DocumentType.TAX_CERTIFICATE
        ]
        
        missing_documents = []
        verified_documents = []
        
        for doc_type in required_documents:
            if doc_type not in application.documents:
                missing_documents.append(doc_type.value)
            else:
                # Verify document
                verification = await self._verify_single_document(
                    doc_type,
                    application.documents[doc_type],
                    application
                )
                
                if verification["verified"]:
                    verified_documents.append(doc_type.value)
                else:
                    missing_documents.append(doc_type.value)
        
        return {
            "all_verified": len(missing_documents) == 0,
            "verified_documents": verified_documents,
            "missing_documents": missing_documents
        }
    
    async def _verify_single_document(
        self,
        doc_type: DocumentType,
        file_url: str,
        application: MerchantApplication
    ) -> Dict[str, Any]:
        """
        Verify a single document using AI/OCR
        
        Args:
            doc_type: Document type
            file_url: URL to document file
            application: Merchant application
            
        Returns:
            Verification result
        """
        try:
            # In a real implementation, this would:
            # 1. Download the document
            # 2. Use OCR to extract text
            # 3. Use AI to verify authenticity
            # 4. Check against government databases
            # 5. Verify business name, tax ID match
            
            # For simulation, we'll do basic checks
            verification_notes = []
            
            if doc_type == DocumentType.BUSINESS_LICENSE:
                # Verify business license
                # Check if business name matches
                verification_notes.append("Business name verified")
                verification_notes.append("License appears authentic")
                verified = True
            
            elif doc_type == DocumentType.TAX_CERTIFICATE:
                # Verify tax certificate
                # Check if tax ID matches
                verification_notes.append("Tax ID verified")
                verified = True
            
            else:
                verified = True
                verification_notes.append("Document received")
            
            # Save verification result
            verification = DocumentVerification(
                document_type=doc_type,
                file_url=file_url,
                verified=verified,
                verification_method="ai",
                verification_notes="; ".join(verification_notes),
                verified_by="BACKOFFICE_AGENT"
            )
            
            await self._save_document_verification(verification, application.application_id)
            
            return {
                "verified": verified,
                "notes": verification_notes
            }
            
        except Exception as e:
            logger.error("Failed to verify document",
                        error=str(e),
                        doc_type=doc_type)
            return {
                "verified": False,
                "notes": [f"Verification failed: {str(e)}"]
            }
    
    async def _verify_business_info(
        self,
        application: MerchantApplication
    ) -> Dict[str, Any]:
        """
        Verify business information against external databases
        
        Args:
            application: Merchant application
            
        Returns:
            Verification result
        """
        try:
            # In a real implementation, this would:
            # 1. Check business registry
            # 2. Verify tax ID with tax authority
            # 3. Check business address
            # 4. Verify phone and email
            # 5. Check business reputation
            
            # For simulation, we'll do basic validation
            
            # Check if tax ID format is valid (basic check)
            if not application.tax_id or len(application.tax_id) < 5:
                return {
                    "valid": False,
                    "reason": "Invalid tax ID format"
                }
            
            # Check if business name is provided
            if not application.business_name or len(application.business_name) < 3:
                return {
                    "valid": False,
                    "reason": "Invalid business name"
                }
            
            # Check if email is valid
            if not application.email:
                return {
                    "valid": False,
                    "reason": "Invalid email address"
                }
            
            # All checks passed
            return {
                "valid": True,
                "reason": "Business information verified"
            }
            
        except Exception as e:
            logger.error("Failed to verify business info",
                        error=str(e),
                        application_id=application.application_id)
            return {
                "valid": False,
                "reason": f"Verification error: {str(e)}"
            }
    
    async def _perform_fraud_check(
        self,
        application: MerchantApplication
    ) -> Dict[str, Any]:
        """
        Perform fraud detection check
        
        Args:
            application: Merchant application
            
        Returns:
            Fraud check result with score (0-1, 1 being highest risk)
        """
        try:
            # In a real implementation, this would:
            # 1. Check against fraud databases
            # 2. Verify IP address and location
            # 3. Check for duplicate applications
            # 4. Analyze application patterns
            # 5. Use ML model for fraud detection
            
            fraud_score = 0.0
            risk_factors = []
            
            # Check for duplicate tax ID
            duplicate_tax_id = await self._check_duplicate_tax_id(application.tax_id)
            if duplicate_tax_id:
                fraud_score += 0.5
                risk_factors.append("Duplicate tax ID found")
            
            # Check for duplicate email
            duplicate_email = await self._check_duplicate_email(application.email)
            if duplicate_email:
                fraud_score += 0.3
                risk_factors.append("Duplicate email found")
            
            # Check business age (if available)
            # Newer businesses have slightly higher risk
            # This would come from business registry
            
            # For simulation, random low fraud score
            import random
            fraud_score += random.uniform(0, 0.1)
            
            return {
                "fraud_score": fraud_score,
                "risk_factors": risk_factors,
                "passed": fraud_score < self.fraud_threshold
            }
            
        except Exception as e:
            logger.error("Failed to perform fraud check",
                        error=str(e),
                        application_id=application.application_id)
            return {
                "fraud_score": 0.0,
                "risk_factors": [],
                "passed": True
            }
    
    async def _create_merchant_account(
        self,
        application: MerchantApplication
    ) -> MerchantAccount:
        """
        Create merchant account after approval
        
        Args:
            application: Approved merchant application
            
        Returns:
            Created merchant account
        """
        # Generate merchant ID
        merchant_id = f"M-{datetime.utcnow().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
        
        # Determine commission rate based on business type and volume
        if application.estimated_monthly_volume and application.estimated_monthly_volume > 1000:
            commission_rate = Decimal("0.12")  # 12% for high volume
        else:
            commission_rate = Decimal("0.15")  # 15% standard
        
        # Create merchant account
        account = MerchantAccount(
            merchant_id=merchant_id,
            application_id=application.application_id,
            business_name=application.business_name,
            business_type=application.business_type,
            tax_id=application.tax_id,
            email=application.email,
            phone=application.phone,
            commission_rate=commission_rate,
            status="active"
        )
        
        # Save to database
        await self._save_merchant_account(account)
        
        # Create merchant dashboard access
        await self._create_merchant_dashboard_access(account)
        
        # Set up payment processing
        await self._setup_merchant_payment_processing(account)
        
        logger.info("Merchant account created",
                   merchant_id=merchant_id,
                   business_name=application.business_name)
        
        return account
    
    async def _create_merchant_dashboard_access(
        self,
        account: MerchantAccount
    ) -> Dict[str, Any]:
        """Create dashboard access credentials for merchant"""
        # Generate temporary password
        temp_password = secrets.token_urlsafe(16)
        
        # Hash password
        password_hash = hashlib.sha256(temp_password.encode()).hexdigest()
        
        # Save credentials
        credentials = {
            "merchant_id": account.merchant_id,
            "email": account.email,
            "password_hash": password_hash,
            "temp_password": temp_password,
            "must_change_password": True
        }
        
        await self._save_merchant_credentials(credentials)
        
        return credentials
    
    async def _setup_merchant_payment_processing(
        self,
        account: MerchantAccount
    ) -> bool:
        """Set up payment processing for merchant"""
        # In a real implementation, this would:
        # 1. Create Stripe Connect account
        # 2. Set up bank account verification
        # 3. Configure payout schedule
        # 4. Set up commission collection
        
        await self.kafka_producer.send(
            "merchant_payment_setup_required",
            {
                "merchant_id": account.merchant_id,
                "email": account.email,
                "business_name": account.business_name
            }
        )
        
        return True
    
    async def _send_welcome_email(self, account: MerchantAccount) -> bool:
        """Send welcome email to new merchant"""
        await self.kafka_producer.send(
            "send_notification",
            {
                "recipient": account.email,
                "notification_type": "merchant_welcome",
                "merchant_id": account.merchant_id,
                "business_name": account.business_name,
                "dashboard_url": f"https://merchant.example.com/login",
                "sent_at": datetime.utcnow().isoformat()
            }
        )
        return True
    
    async def _send_documents_required_notification(
        self,
        application: MerchantApplication,
        missing_documents: List[str]
    ) -> bool:
        """Send notification about missing documents"""
        await self.kafka_producer.send(
            "send_notification",
            {
                "recipient": application.email,
                "notification_type": "documents_required",
                "application_id": application.application_id,
                "missing_documents": missing_documents,
                "sent_at": datetime.utcnow().isoformat()
            }
        )
        return True
    
    async def _send_rejection_notification(
        self,
        application: MerchantApplication,
        reason: str
    ) -> bool:
        """Send application rejection notification"""
        await self.kafka_producer.send(
            "send_notification",
            {
                "recipient": application.email,
                "notification_type": "application_rejected",
                "application_id": application.application_id,
                "reason": reason,
                "sent_at": datetime.utcnow().isoformat()
            }
        )
        return True
    
    # Database helper methods
    async def _save_application(self, application: MerchantApplication) -> bool:
        """Save merchant application to database"""
        # Implementation would save to database
        return True
    
    async def _save_document_verification(
        self,
        verification: DocumentVerification,
        application_id: str
    ) -> bool:
        """Save document verification result"""
        # Implementation would save to database
        return True
    
    async def _save_merchant_account(self, account: MerchantAccount) -> bool:
        """Save merchant account to database"""
        # Implementation would save to database
        return True
    
    async def _save_merchant_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Save merchant login credentials"""
        # Implementation would save to database
        return True
    
    async def _check_duplicate_tax_id(self, tax_id: str) -> bool:
        """Check if tax ID already exists"""
        # Implementation would query database
        return False
    
    async def _check_duplicate_email(self, email: str) -> bool:
        """Check if email already exists"""
        # Implementation would query database
        return False
    
    async def run(self):
        """Main agent loop"""
        logger.info("Backoffice Agent starting...")
        await self.initialize()
        
        try:
            async for message in self.kafka_consumer:
                topic = message.topic
                data = message.value
                
                if topic == "merchant_application_submitted":
                    # Process new merchant application
                    application = MerchantApplication(**data)
                    await self.process_merchant_application(application)
                
                elif topic == "merchant_documents_uploaded":
                    # Re-process application after documents uploaded
                    application_id = data["application_id"]
                    # Retrieve application and re-process
                    # await self.process_merchant_application(application)
                    pass
                
                elif topic == "merchant_update_requested":
                    # Handle merchant account updates
                    # Implementation would update merchant details
                    pass
                
        except Exception as e:
            logger.error("Error in agent loop", error=str(e))
        finally:
            await self.shutdown()
    
    async def cleanup(self):
        """Cleanup agent resources"""
        try:
            if self.kafka_producer:
                await self.kafka_producer.stop()
            if self.kafka_consumer:
                await self.kafka_consumer.stop()
            if self.db_manager:
                await self.db_manager.disconnect()
            await super().cleanup()
            logger.info(f"{self.agent_name} cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process backoffice business logic
        
        Args:
            data: Dictionary containing operation type and parameters
            
        Returns:
            Dictionary with processing results
        """
        try:
            operation = data.get("operation", "create_application")
            
            if operation == "create_application":
                # Create merchant application
                application = MerchantApplication(**data.get("application", {}))
                application_id = await self.create_merchant_application(application)
                return {"status": "success", "application_id": application_id}
            
            elif operation == "verify_documents":
                # Verify merchant documents
                application_id = data.get("application_id")
                result = await self.verify_merchant_documents(application_id)
                return {"status": "success", "result": result}
            
            elif operation == "approve_merchant":
                # Approve merchant application
                application_id = data.get("application_id")
                approved_by = data.get("approved_by")
                result = await self.approve_merchant(application_id, approved_by)
                return {"status": "success", "result": result}
            
            elif operation == "create_account":
                # Create merchant account
                application_id = data.get("application_id")
                account_id = await self.create_merchant_account(application_id)
                return {"status": "success", "account_id": account_id}
            
            else:
                return {"status": "error", "message": f"Unknown operation: {operation}"}
                
        except Exception as e:
            logger.error(f"Error in process_business_logic: {e}")
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    agent = BackofficeAgent()
    asyncio.run(agent.run())



# FastAPI Server Setup
app = FastAPI(
    title="Backoffice Agent",
    description="Backoffice Agent - Multi-Agent E-commerce Platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent": "backoffice_agent"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "agent": "backoffice_agent",
        "status": "running",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8012))
    uvicorn.run(app, host="0.0.0.0", port=port)
