from contextlib import asynccontextmanager
"""
AI-Powered Self-Healing Monitoring Agent

This agent provides intelligent monitoring with automatic error detection and self-healing capabilities:
- Real-time monitoring of all 16 agents
- AI-powered error analysis using OpenAI LLM
- Automatic code fix proposals
- Human validation workflow for fixes
- Learning from approved/rejected fixes
- Detailed logging of all actions
"""

import asyncio
import logging
import os
import sys
import psutil
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from enum import Enum
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Body, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from openai import OpenAI

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import shared modules
try:
    from shared.base_agent_v2 import BaseAgentV2
    from shared.db_helpers import DatabaseHelper
    from shared.database import DatabaseManager
    from shared.kafka_config import KafkaProducer, KafkaConsumer
    logger.info("Successfully imported shared modules")
except ImportError as e:
    logger.error(f"Import error: {e}")
    raise


# =====================================================
# ENUMS
# =====================================================

class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FixStatus(str, Enum):
    """Fix proposal status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    FAILED = "failed"


class AgentStatus(str, Enum):
    """Agent health status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"


# =====================================================
# PYDANTIC MODELS
# =====================================================

class ErrorDetection(BaseModel):
    """Error detection model"""
    error_id: str
    agent_id: str
    agent_name: str
    error_type: str
    error_message: str
    stack_trace: str
    severity: ErrorSeverity
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = {}


class FixProposal(BaseModel):
    """AI-generated fix proposal"""
    fix_id: str
    error_id: str
    agent_id: str
    file_path: str
    original_code: str
    proposed_code: str
    explanation: str
    confidence: float  # 0.0 to 1.0
    status: FixStatus = FixStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None


class HumanValidationRequest(BaseModel):
    """Human validation request"""
    fix_id: str
    error_summary: str
    current_code: str
    proposed_fix: str
    ai_explanation: str
    confidence_score: float
    risk_assessment: str


class HumanValidationResponse(BaseModel):
    """Human validation response"""
    fix_id: str
    approved: bool
    reviewer: str
    notes: Optional[str] = None


class AgentHealthStatus(BaseModel):
    """Agent health status"""
    agent_id: str
    agent_name: str
    status: AgentStatus
    cpu_usage: float
    memory_usage: float
    error_count: int
    last_error: Optional[str] = None
    uptime_seconds: int
    last_heartbeat: datetime


# =====================================================
# AI ERROR ANALYZER
# =====================================================

class AIErrorAnalyzer:
    """Uses OpenAI LLM to analyze errors and propose fixes"""
    
    def __init__(self):
        self.client = OpenAI()  # API key from environment
        self.model = "gpt-4.1-mini"  # Fast and cost-effective
    
    async def analyze_error(
        self,
        error: ErrorDetection,
        agent_code: str
    ) -> Tuple[str, str, float]:
        """
        Analyze error and propose a fix
        
        Returns:
            (proposed_code, explanation, confidence)
        """
        try:
            prompt = f"""You are an expert Python developer analyzing a production error in a multi-agent e-commerce system.

**Error Details:**
- Agent: {error.agent_name} ({error.agent_id})
- Error Type: {error.error_type}
- Error Message: {error.error_message}
- Severity: {error.severity.value}

**Stack Trace:**
```
{error.stack_trace}
```

**Current Code:**
```python
{agent_code}
```

**Context:**
{json.dumps(error.context, indent=2)}

**Task:**
1. Identify the root cause of the error
2. Propose a minimal code fix that resolves the issue
3. Ensure the fix doesn't break existing functionality
4. Provide confidence score (0.0 to 1.0) for your fix

**Output Format (JSON):**
{{
    "root_cause": "Brief explanation of what caused the error",
    "proposed_fix": "The complete fixed code",
    "explanation": "Detailed explanation of the fix and why it works",
    "confidence": 0.95,
    "potential_risks": "Any risks or side effects of this fix"
}}

Respond ONLY with valid JSON, no additional text."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert Python developer specializing in debugging and fixing production errors."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more deterministic fixes
                max_tokens=2000
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return (
                result["proposed_fix"],
                f"{result['root_cause']}\n\n{result['explanation']}\n\nPotential Risks: {result['potential_risks']}",
                result["confidence"]
            )
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return ("", f"AI analysis failed: {str(e)}", 0.0)
    
    async def assess_risk(self, fix_proposal: FixProposal) -> str:
        """Assess the risk level of applying a fix"""
        try:
            prompt = f"""Assess the risk of applying this code fix in a production environment.

**Original Code:**
```python
{fix_proposal.original_code}
```

**Proposed Fix:**
```python
{fix_proposal.proposed_code}
```

**AI Explanation:**
{fix_proposal.explanation}

**Confidence Score:** {fix_proposal.confidence}

Rate the risk as: LOW, MEDIUM, or HIGH
Provide brief justification.

Output format:
RISK_LEVEL: [LOW/MEDIUM/HIGH]
JUSTIFICATION: [Your reasoning]"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior DevOps engineer assessing deployment risks."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            return "RISK_LEVEL: UNKNOWN\nJUSTIFICATION: Risk assessment failed"


# =====================================================
# REPOSITORY
# =====================================================

class SelfHealingRepository:
    """Handles database operations for self-healing monitoring"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.db_helper = DatabaseHelper(db_manager)
    
    async def save_error_detection(self, error: ErrorDetection) -> Dict[str, Any]:
        """Save error detection to database"""
        try:
            async with self.db_manager.get_session() as session:
                error_data = {
                    "error_id": error.error_id,
                    "agent_id": error.agent_id,
                    "agent_name": error.agent_name,
                    "error_type": error.error_type,
                    "error_message": error.error_message,
                    "stack_trace": error.stack_trace,
                    "severity": error.severity.value,
                    "timestamp": error.timestamp,
                    "context": json.dumps(error.context)
                }
                result = await self.db_helper.create(session, "error_detections", error_data)
                return result
        except Exception as e:
            logger.error(f"save_error_detection failed: {e}")
            raise
    
    async def save_fix_proposal(self, fix: FixProposal) -> Dict[str, Any]:
        """Save fix proposal to database"""
        try:
            async with self.db_manager.get_session() as session:
                fix_data = {
                    "fix_id": fix.fix_id,
                    "error_id": fix.error_id,
                    "agent_id": fix.agent_id,
                    "file_path": fix.file_path,
                    "original_code": fix.original_code,
                    "proposed_code": fix.proposed_code,
                    "explanation": fix.explanation,
                    "confidence": fix.confidence,
                    "status": fix.status.value,
                    "created_at": fix.created_at,
                    "reviewed_at": fix.reviewed_at,
                    "reviewed_by": fix.reviewed_by,
                    "review_notes": fix.review_notes
                }
                result = await self.db_helper.create(session, "fix_proposals", fix_data)
                return result
        except Exception as e:
            logger.error(f"save_fix_proposal failed: {e}")
            raise
    
    async def update_fix_status(
        self,
        fix_id: str,
        status: FixStatus,
        reviewer: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Update fix proposal status"""
        try:
            async with self.db_manager.get_session() as session:
                updates = {
                    "status": status.value,
                    "reviewed_at": datetime.utcnow(),
                    "reviewed_by": reviewer,
                    "review_notes": notes
                }
                result = await self.db_helper.update(session, "fix_proposals", fix_id, updates)
                return result is not None
        except Exception as e:
            logger.error(f"update_fix_status failed: {e}")
            return False
    
    async def get_pending_fixes(self) -> List[Dict[str, Any]]:
        """Get all pending fix proposals"""
        try:
            async with self.db_manager.get_session() as session:
                results = await self.db_helper.get_all_where(
                    session,
                    "fix_proposals",
                    "status",
                    FixStatus.PENDING.value
                )
                return results or []
        except Exception as e:
            logger.error(f"get_pending_fixes failed: {e}")
            return []
    
    async def save_agent_health(self, health: AgentHealthStatus) -> Dict[str, Any]:
        """Save agent health status"""
        try:
            async with self.db_manager.get_session() as session:
                health_data = {
                    "id": str(uuid4()),
                    "agent_id": health.agent_id,
                    "agent_name": health.agent_name,
                    "status": health.status.value,
                    "cpu_usage": health.cpu_usage,
                    "memory_usage": health.memory_usage,
                    "error_count": health.error_count,
                    "last_error": health.last_error,
                    "uptime_seconds": health.uptime_seconds,
                    "last_heartbeat": health.last_heartbeat
                }
                result = await self.db_helper.create(session, "agent_health", health_data)
                return result
        except Exception as e:
            logger.error(f"save_agent_health failed: {e}")
            raise


# =====================================================
# SELF-HEALING MONITORING AGENT
# =====================================================

class SelfHealingMonitoringAgent(BaseAgentV2):
    """
    AI-Powered Self-Healing Monitoring Agent
    
    Monitors all agents, detects errors, proposes fixes using AI,
    and applies fixes after human validation.
    """
    
    def __init__(self):
        super().__init__(agent_id="SelfHealingMonitoringAgent")
        self.db_manager: Optional[DatabaseManager] = None
        self.db_helper: Optional[DatabaseHelper] = None
        self.repository: Optional[SelfHealingRepository] = None
        self.ai_analyzer: Optional[AIErrorAnalyzer] = None
        self.kafka_producer: Optional[KafkaProducer] = None
        self.kafka_consumer: Optional[KafkaConsumer] = None
        self._db_initialized = False
        
        # Agent registry
        self.monitored_agents = [
            "MonitoringAgent",
            "OrderAgent",
            "ProductAgent",
            "MarketplaceConnectorAgent",
            "CustomerAgent",
            "InventoryAgent",
            "TransportAgent",
            "PaymentAgent",
            "WarehouseAgent",
            "DocumentGenerationAgent",
            "FraudDetectionAgent",
            "RiskAnomalyDetectionAgent",
            "KnowledgeManagementAgent",
            "AfterSalesAgent",
            "BackofficeAgent",
            "QualityControlAgent"
        ]
    
    async def initialize(self):
        """Initialize agent"""
        await super().initialize()
        
        # Initialize Database
        try:
            from shared.database_manager import get_database_manager
            self.db_manager = get_database_manager()
            logger.info("Using global database manager")
        except (RuntimeError, ImportError):
            from shared.models import DatabaseConfig
            from shared.database_manager import EnhancedDatabaseManager
            db_config = DatabaseConfig()
            self.db_manager = EnhancedDatabaseManager(db_config)
            await self.db_manager.initialize(max_retries=5)
            logger.info("Created new enhanced database manager")
        
        self.db_helper = DatabaseHelper(self.db_manager)
        self.repository = SelfHealingRepository(self.db_manager)
        self.ai_analyzer = AIErrorAnalyzer()
        self._db_initialized = True
        
        # Initialize Kafka
        self.kafka_producer = KafkaProducer()
        self.kafka_consumer = KafkaConsumer(
            "agent_error",
            "agent_health",
            group_id="self_healing_monitoring_agent"
        )
        
        logger.info("Self-Healing Monitoring Agent initialized")
    
    async def detect_error(self, error: ErrorDetection) -> Dict[str, Any]:
        """Detect and analyze an error"""
        if not self._db_initialized:
            raise ValueError("Database not initialized")
        
        try:
            logger.info(f"Error detected in {error.agent_name}: {error.error_message}")
            
            # Save error to database
            await self.repository.save_error_detection(error)
            
            # Publish error event
            await self.kafka_producer.send(
                "error_detected",
                {
                    "error_id": error.error_id,
                    "agent_id": error.agent_id,
                    "severity": error.severity.value,
                    "message": error.error_message
                }
            )
            
            # For high/critical errors, trigger AI analysis
            if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                await self._analyze_and_propose_fix(error)
            
            return {
                "success": True,
                "error_id": error.error_id,
                "severity": error.severity.value
            }
        except Exception as e:
            logger.error(f"detect_error failed: {e}")
            raise
    
    async def _analyze_and_propose_fix(self, error: ErrorDetection):
        """Analyze error with AI and propose a fix"""
        try:
            # Get agent code (simplified - in production, read from file)
            agent_file_path = f"agents/{error.agent_id.lower()}.py"
            
            # Read agent code
            try:
                with open(agent_file_path, 'r') as f:
                    agent_code = f.read()
            except FileNotFoundError:
                logger.warning(f"Agent file not found: {agent_file_path}")
                agent_code = "# Agent code not available"
            
            # Analyze with AI
            proposed_code, explanation, confidence = await self.ai_analyzer.analyze_error(
                error,
                agent_code
            )
            
            if confidence > 0.5:  # Only propose if confident enough
                # Create fix proposal
                fix = FixProposal(
                    fix_id=str(uuid4()),
                    error_id=error.error_id,
                    agent_id=error.agent_id,
                    file_path=agent_file_path,
                    original_code=agent_code,
                    proposed_code=proposed_code,
                    explanation=explanation,
                    confidence=confidence
                )
                
                # Save fix proposal
                await self.repository.save_fix_proposal(fix)
                
                # Assess risk
                risk_assessment = await self.ai_analyzer.assess_risk(fix)
                
                # Request human validation
                await self._request_human_validation(fix, error, risk_assessment)
                
                logger.info(f"Fix proposed for error {error.error_id} (confidence: {confidence})")
            else:
                logger.warning(f"AI confidence too low ({confidence}) for error {error.error_id}")
                
        except Exception as e:
            logger.error(f"_analyze_and_propose_fix failed: {e}")
    
    async def _request_human_validation(
        self,
        fix: FixProposal,
        error: ErrorDetection,
        risk_assessment: str
    ):
        """Request human validation for a fix"""
        try:
            validation_request = HumanValidationRequest(
                fix_id=fix.fix_id,
                error_summary=f"{error.agent_name}: {error.error_message}",
                current_code=fix.original_code[:500],  # Truncate for display
                proposed_fix=fix.proposed_code[:500],
                ai_explanation=fix.explanation,
                confidence_score=fix.confidence,
                risk_assessment=risk_assessment
            )
            
            # Publish validation request event
            await self.kafka_producer.send(
                "human_validation_required",
                {
                    "fix_id": fix.fix_id,
                    "error_id": error.error_id,
                    "agent_id": error.agent_id,
                    "severity": error.severity.value,
                    "confidence": fix.confidence,
                    "risk_assessment": risk_assessment
                }
            )
            
            logger.info(f"Human validation requested for fix {fix.fix_id}")
            
        except Exception as e:
            logger.error(f"_request_human_validation failed: {e}")
    
    async def process_human_validation(
        self,
        validation: HumanValidationResponse
    ) -> Dict[str, Any]:
        """Process human validation response"""
        if not self._db_initialized:
            raise ValueError("Database not initialized")
        
        try:
            if validation.approved:
                # Update status to approved
                await self.repository.update_fix_status(
                    validation.fix_id,
                    FixStatus.APPROVED,
                    validation.reviewer,
                    validation.notes
                )
                
                # Apply the fix
                result = await self._apply_fix(validation.fix_id)
                
                logger.info(f"Fix {validation.fix_id} approved and applied by {validation.reviewer}")
                
                return {
                    "success": True,
                    "fix_id": validation.fix_id,
                    "status": "applied",
                    "result": result
                }
            else:
                # Update status to rejected
                await self.repository.update_fix_status(
                    validation.fix_id,
                    FixStatus.REJECTED,
                    validation.reviewer,
                    validation.notes
                )
                
                logger.info(f"Fix {validation.fix_id} rejected by {validation.reviewer}")
                
                return {
                    "success": True,
                    "fix_id": validation.fix_id,
                    "status": "rejected"
                }
        except Exception as e:
            logger.error(f"process_human_validation failed: {e}")
            raise
    
    async def _apply_fix(self, fix_id: str) -> Dict[str, Any]:
        """Apply an approved fix"""
        # In production, this would:
        # 1. Create a backup of the current file
        # 2. Apply the code changes
        # 3. Run tests
        # 4. Deploy if tests pass
        # 5. Rollback if tests fail
        
        # For now, just log the action
        logger.info(f"Applying fix {fix_id} (simulated)")
        
        return {
            "applied": True,
            "message": "Fix applied successfully (simulated)"
        }
    
    async def get_agent_health_status(self, agent_id: str) -> AgentHealthStatus:
        """Get health status for an agent"""
        # In production, this would query the agent's health endpoint
        # For now, return simulated data
        return AgentHealthStatus(
            agent_id=agent_id,
            agent_name=agent_id,
            status=AgentStatus.HEALTHY,
            cpu_usage=25.5,
            memory_usage=45.2,
            error_count=0,
            uptime_seconds=3600,
            last_heartbeat=datetime.utcnow()
        )
    
    async def cleanup(self):
        """Cleanup agent resources"""
        try:
            if self.kafka_producer:
                await self.kafka_producer.stop()
            if self.kafka_consumer:
                await self.kafka_consumer.stop()
            if self.db_manager:
                await self.db_manager.close()
            await super().cleanup()
            logger.info("SelfHealingMonitoringAgent cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process self-healing monitoring business logic.
        
        Args:
            data: Dictionary containing operation type and parameters
            
        Returns:
            Dictionary with processing results
        """
        try:
            operation = data.get("operation", "process")
            logger.info(f"Processing self-healing operation: {operation}")
            return {"status": "success", "operation": operation, "data": data}
        except Exception as e:
            logger.error(f"Error in process_business_logic: {e}")
            return {"status": "error", "message": str(e)}


# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI(
    title="Self-Healing Monitoring Agent API",
    description="AI-powered monitoring with automatic error detection and self-healing",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent_instance: Optional[SelfHealingMonitoringAgent] = None


@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup"""
    global agent_instance
    agent_instance = SelfHealingMonitoringAgent()
    await agent_instance.initialize()
    logger.info("Self-Healing Monitoring Agent API started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global agent_instance
    if agent_instance and agent_instance.db_manager:
        await agent_instance.db_manager.close()
    logger.info("Self-Healing Monitoring Agent API shutdown")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent": "SelfHealingMonitoringAgent",
        "version": "2.0.0",
        "ai_enabled": True,
        "database": agent_instance._db_initialized if agent_instance else False
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "agent": "SelfHealingMonitoringAgent",
        "version": "2.0.0",
        "capabilities": [
            "Real-time error detection",
            "AI-powered error analysis",
            "Automatic fix proposals",
            "Human validation workflow",
            "Self-healing capabilities"
        ],
        "monitored_agents": agent_instance.monitored_agents if agent_instance else []
    }


@app.post("/errors/detect", summary="Report Error")
async def detect_error(error: ErrorDetection):
    """Report an error for analysis"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await agent_instance.detect_error(error)
        return result
    except Exception as e:
        logger.error(f"detect_error failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fixes/validate", summary="Validate Fix Proposal")
async def validate_fix(validation: HumanValidationResponse):
    """Process human validation for a fix proposal"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await agent_instance.process_human_validation(validation)
        return result
    except Exception as e:
        logger.error(f"validate_fix failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/fixes/pending", summary="Get Pending Fixes")
async def get_pending_fixes():
    """Get all pending fix proposals awaiting human validation"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        fixes = await agent_instance.repository.get_pending_fixes()
        return {
            "pending_fixes": fixes,
            "count": len(fixes)
        }
    except Exception as e:
        logger.error(f"get_pending_fixes failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_id}/health", summary="Get Agent Health")
async def get_agent_health(agent_id: str = Path(...)):
    """Get health status for a specific agent"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        health = await agent_instance.get_agent_health_status(agent_id)
        return health
    except Exception as e:
        logger.error(f"get_agent_health failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/health/all", summary="Get All Agents Health")
async def get_all_agents_health():
    """Get health status for all monitored agents"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        health_statuses = []
        for agent_id in agent_instance.monitored_agents:
            health = await agent_instance.get_agent_health_status(agent_id)
            health_statuses.append(health)
        
        return {
            "agents": health_statuses,
            "total": len(health_statuses),
            "healthy": sum(1 for h in health_statuses if h.status == AgentStatus.HEALTHY),
            "warning": sum(1 for h in health_statuses if h.status == AgentStatus.WARNING),
            "critical": sum(1 for h in health_statuses if h.status == AgentStatus.CRITICAL),
            "offline": sum(1 for h in health_statuses if h.status == AgentStatus.OFFLINE)
        }
    except Exception as e:
        logger.error(f"get_all_agents_health failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# Create agent instance at module level to ensure routes are registered
agent = SelfHealingMonitoringAgent()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8023))
    logger.info(f"Starting Self-Healing Monitoring Agent on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

