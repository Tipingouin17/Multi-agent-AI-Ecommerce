"""
Fraud Detection Agent - Multi-Agent E-Commerce System

This agent provides ML-based fraud detection, risk scoring, and anomaly detection
for transactions, orders, and user behavior.

DATABASE SCHEMA (migration 011_fraud_detection_agent.sql):

CREATE TABLE fraud_rules (
    rule_id SERIAL PRIMARY KEY,
    rule_name VARCHAR(200) NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- 'velocity', 'amount', 'location', 'device', 'behavior'
    conditions JSONB NOT NULL,
    risk_score INTEGER NOT NULL, -- 0-100
    action VARCHAR(50) DEFAULT 'flag', -- 'flag', 'block', 'review', 'challenge'
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE fraud_checks (
    check_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL, -- 'order', 'payment', 'account', 'login'
    entity_id VARCHAR(100) NOT NULL,
    customer_id VARCHAR(100),
    risk_score INTEGER DEFAULT 0, -- 0-100
    risk_level VARCHAR(20), -- 'low', 'medium', 'high', 'critical'
    triggered_rules JSONB DEFAULT '[]',
    signals JSONB DEFAULT '{}', -- All fraud signals detected
    decision VARCHAR(50), -- 'approved', 'flagged', 'blocked', 'manual_review'
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fraud_signals (
    signal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    check_id UUID REFERENCES fraud_checks(check_id),
    signal_type VARCHAR(100) NOT NULL,
    signal_value VARCHAR(500),
    risk_contribution INTEGER, -- How much this signal contributed to risk score
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE blocked_entities (
    block_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL, -- 'email', 'ip', 'device', 'card', 'phone'
    entity_value VARCHAR(500) NOT NULL,
    reason TEXT,
    blocked_by VARCHAR(100),
    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import uuid4, UUID
from enum import Enum

from shared.db_helpers import DatabaseHelper
import hashlib

from fastapi import FastAPI, HTTPException, Depends, Body, Path
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
class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FraudDecision(str, Enum):
    APPROVED = "approved"
    FLAGGED = "flagged"
    BLOCKED = "blocked"
    MANUAL_REVIEW = "manual_review"

# MODELS
class FraudCheckRequest(BaseModel):
    entity_type: str  # 'order', 'payment', 'account', 'login'
    entity_id: str
    customer_id: Optional[str] = None
    data: Dict[str, Any]  # Entity-specific data for analysis

class FraudSignal(BaseModel):
    signal_type: str
    signal_value: str
    risk_contribution: int

class FraudCheckResult(BaseModel):
    check_id: UUID
    entity_type: str
    entity_id: str
    risk_score: int
    risk_level: RiskLevel
    decision: FraudDecision
    triggered_rules: List[Dict[str, Any]]
    signals: List[FraudSignal]
    recommendations: List[str]
    created_at: datetime

class BlockEntityRequest(BaseModel):
    entity_type: str  # 'email', 'ip', 'device', 'card', 'phone'
    entity_value: str
    reason: str
    duration_hours: Optional[int] = None  # None = permanent

# REPOSITORY
class FraudDetectionRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_fraud_check(self, check_data: Dict[str, Any]) -> UUID:
        query = """
            INSERT INTO fraud_checks (entity_type, entity_id, customer_id, risk_score,
                                     risk_level, triggered_rules, signals, decision)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING check_id
        """
        result = await self.db.fetch_one(
            query, check_data['entity_type'], check_data['entity_id'],
            check_data.get('customer_id'), check_data['risk_score'],
            check_data['risk_level'], str(check_data.get('triggered_rules', [])),
            str(check_data.get('signals', {})), check_data['decision']
        )
        return result['check_id']
    
    async def get_fraud_check(self, check_id: UUID) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM fraud_checks WHERE check_id = $1"
        result = await self.db.fetch_one(query, check_id)
        return dict(result) if result else None
    
    async def is_entity_blocked(self, entity_type: str, entity_value: str) -> bool:
        query = """
            SELECT COUNT(*) as count FROM blocked_entities
            WHERE entity_type = $1 AND entity_value = $2 AND is_active = true
            AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
        """
        result = await self.db.fetch_one(query, entity_type, entity_value)
        return result['count'] > 0
    
    async def block_entity(self, block_data: BlockEntityRequest, blocked_by: str) -> UUID:
        expires_at = None
        if block_data.duration_hours:
            expires_at = datetime.utcnow() + timedelta(hours=block_data.duration_hours)
        
        query = """
            INSERT INTO blocked_entities (entity_type, entity_value, reason, blocked_by, expires_at)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING block_id
        """
        result = await self.db.fetch_one(
            query, block_data.entity_type, block_data.entity_value,
            block_data.reason, blocked_by, expires_at
        )
        return result['block_id']
    
    async def get_customer_fraud_history(self, customer_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        query = """
            SELECT * FROM fraud_checks
            WHERE customer_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """
        results = await self.db.fetch_all(query, customer_id, limit)
        return [dict(r) for r in results]

# SERVICE
class FraudDetectionService:
    def __init__(self, repo: FraudDetectionRepository):
        self.repo = repo
    
    def calculate_risk_score(self, data: Dict[str, Any]) -> tuple[int, List[FraudSignal]]:
        """Calculate risk score based on various signals."""
        risk_score = 0
        signals = []
        
        # Check amount anomaly (high value orders)
        if 'amount' in data:
            amount = float(data['amount'])
            if amount > 1000:
                contribution = min(30, int((amount - 1000) / 100))
                risk_score += contribution
                signals.append(FraudSignal(
                    signal_type="high_amount",
                    signal_value=f"${amount:.2f}",
                    risk_contribution=contribution
                ))
        
        # Check velocity (multiple orders in short time)
        if 'order_count_24h' in data and data['order_count_24h'] > 5:
            contribution = min(25, data['order_count_24h'] * 3)
            risk_score += contribution
            signals.append(FraudSignal(
                signal_type="high_velocity",
                signal_value=f"{data['order_count_24h']} orders in 24h",
                risk_contribution=contribution
            ))
        
        # Check IP reputation
        if 'ip_reputation' in data and data['ip_reputation'] == 'bad':
            contribution = 40
            risk_score += contribution
            signals.append(FraudSignal(
                signal_type="bad_ip_reputation",
                signal_value=data.get('ip_address', 'unknown'),
                risk_contribution=contribution
            ))
        
        # Check shipping/billing mismatch
        if 'address_mismatch' in data and data['address_mismatch']:
            contribution = 20
            risk_score += contribution
            signals.append(FraudSignal(
                signal_type="address_mismatch",
                signal_value="Shipping and billing addresses differ significantly",
                risk_contribution=contribution
            ))
        
        # Check new account
        if 'account_age_days' in data and data['account_age_days'] < 1:
            contribution = 15
            risk_score += contribution
            signals.append(FraudSignal(
                signal_type="new_account",
                signal_value=f"Account created {data['account_age_days']} days ago",
                risk_contribution=contribution
            ))
        
        # Check payment method changes
        if 'payment_method_changes_7d' in data and data['payment_method_changes_7d'] > 2:
            contribution = 15
            risk_score += contribution
            signals.append(FraudSignal(
                signal_type="frequent_payment_changes",
                signal_value=f"{data['payment_method_changes_7d']} changes in 7 days",
                risk_contribution=contribution
            ))
        
        return min(100, risk_score), signals
    
    def determine_risk_level(self, risk_score: int) -> RiskLevel:
        """Determine risk level based on score."""
        if risk_score >= 75:
            return RiskLevel.CRITICAL
        elif risk_score >= 50:
            return RiskLevel.HIGH
        elif risk_score >= 25:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def determine_decision(self, risk_level: RiskLevel) -> FraudDecision:
        """Determine action based on risk level."""
        if risk_level == RiskLevel.CRITICAL:
            return FraudDecision.BLOCKED
        elif risk_level == RiskLevel.HIGH:
            return FraudDecision.MANUAL_REVIEW
        elif risk_level == RiskLevel.MEDIUM:
            return FraudDecision.FLAGGED
        else:
            return FraudDecision.APPROVED
    
    def generate_recommendations(self, risk_level: RiskLevel, signals: List[FraudSignal]) -> List[str]:
        """Generate recommendations based on fraud analysis."""
        recommendations = []
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("Contact customer to verify order details")
            recommendations.append("Request additional identity verification")
        
        for signal in signals:
            if signal.signal_type == "high_amount":
                recommendations.append("Verify payment method with issuing bank")
            elif signal.signal_type == "address_mismatch":
                recommendations.append("Confirm shipping address with customer")
            elif signal.signal_type == "new_account":
                recommendations.append("Require email/phone verification before processing")
        
        return recommendations
    
    async def check_fraud(self, request: FraudCheckRequest) -> FraudCheckResult:
        """Perform comprehensive fraud check."""
        # Check if entity is already blocked
        if 'email' in request.data:
            if await self.repo.is_entity_blocked('email', request.data['email']):
                return FraudCheckResult(
                    check_id=uuid4(),
                    entity_type=request.entity_type,
                    entity_id=request.entity_id,
                    risk_score=100,
                    risk_level=RiskLevel.CRITICAL,
                    decision=FraudDecision.BLOCKED,
                    triggered_rules=[{"rule": "blocked_entity", "type": "email"}],
                    signals=[],
                    recommendations=["Entity is blocked"],
                    created_at=datetime.utcnow()
                )
        
        # Calculate risk score
        risk_score, signals = self.calculate_risk_score(request.data)
        risk_level = self.determine_risk_level(risk_score)
        decision = self.determine_decision(risk_level)
        recommendations = self.generate_recommendations(risk_level, signals)
        
        # Save fraud check
        check_data = {
            'entity_type': request.entity_type,
            'entity_id': request.entity_id,
            'customer_id': request.customer_id,
            'risk_score': risk_score,
            'risk_level': risk_level.value,
            'decision': decision.value,
            'triggered_rules': [],
            'signals': {s.signal_type: s.signal_value for s in signals}
        }
        check_id = await self.repo.create_fraud_check(check_data)
        
        logger.info("fraud_check_completed", check_id=str(check_id), risk_score=risk_score,
                   decision=decision.value)
        
        return FraudCheckResult(
            check_id=check_id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            risk_score=risk_score,
            risk_level=risk_level,
            decision=decision,
            triggered_rules=[],
            signals=signals,
            recommendations=recommendations,
            created_at=datetime.utcnow()
        )

# FASTAPI APP
app = FastAPI(title="Fraud Detection Agent API", version="1.0.0")

async def get_fraud_service() -> FraudDetectionService:
    db_manager = await get_database_manager()
    repo = FraudDetectionRepository(db_manager)
    return FraudDetectionService(repo)

# ENDPOINTS
@app.post("/api/v1/fraud/check", response_model=FraudCheckResult)
async def check_fraud(
    request: FraudCheckRequest = Body(...),
    service: FraudDetectionService = Depends(get_fraud_service)
):
    try:
        result = await service.check_fraud(request)
        return result
    except Exception as e:
        logger.error("fraud_check_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/fraud/check/{check_id}")
async def get_fraud_check(
    check_id: UUID = Path(...),
    service: FraudDetectionService = Depends(get_fraud_service)
):
    try:
        check = await service.repo.get_fraud_check(check_id)
        if not check:
            raise HTTPException(status_code=404, detail="Fraud check not found")
        return check
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_fraud_check_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/fraud/block")
async def block_entity(
    request: BlockEntityRequest = Body(...),
    blocked_by: str = Body(..., embed=True),
    service: FraudDetectionService = Depends(get_fraud_service)
):
    try:
        block_id = await service.repo.block_entity(request, blocked_by)
        logger.info("entity_blocked", block_id=str(block_id), entity_type=request.entity_type)
        return {"block_id": block_id, "message": "Entity blocked successfully"}
    except Exception as e:
        logger.error("block_entity_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/fraud/customer/{customer_id}/history")
async def get_customer_fraud_history(
    customer_id: str = Path(...),
    service: FraudDetectionService = Depends(get_fraud_service)
):
    try:
        history = await service.repo.get_customer_fraud_history(customer_id)
        return {"customer_id": customer_id, "checks": history}
    except Exception as e:
        logger.error("get_fraud_history_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "fraud_detection_agent", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)

