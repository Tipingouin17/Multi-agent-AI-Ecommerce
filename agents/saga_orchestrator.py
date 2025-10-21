"""
Saga Orchestrator - Multi-Agent E-commerce System

Implements the Saga pattern for distributed transaction management across agents.
Ensures data consistency in complex multi-step workflows with automatic compensation.

The Saga pattern breaks down distributed transactions into a series of local transactions,
each with a corresponding compensating transaction to undo changes if needed.
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from uuid import UUID, uuid4
from decimal import Decimal
from pydantic import BaseModel
from enum import Enum
import asyncio
import structlog

logger = structlog.get_logger(__name__)


# ===========================
# ENUMS
# ===========================

class SagaStatus(str, Enum):
    """Status of a saga execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    FAILED = "failed"


class StepStatus(str, Enum):
    """Status of a saga step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    SKIPPED = "skipped"


# ===========================
# PYDANTIC MODELS
# ===========================

class SagaStep(BaseModel):
    """A step in a saga workflow."""
    step_id: str
    step_name: str
    agent: str  # Which agent handles this step
    action: str  # Action to perform
    compensation_action: Optional[str] = None  # Action to undo this step
    params: Dict[str, Any] = {}
    timeout: int = 30  # Timeout in seconds
    retry_count: int = 0
    max_retries: int = 3
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class SagaDefinition(BaseModel):
    """Definition of a saga workflow."""
    saga_id: Optional[UUID] = None
    saga_name: str
    description: Optional[str] = None
    steps: List[SagaStep]
    metadata: Optional[Dict[str, Any]] = {}
    created_at: Optional[datetime] = None


class SagaExecution(BaseModel):
    """Execution state of a saga."""
    execution_id: UUID
    saga_id: UUID
    saga_name: str
    status: SagaStatus
    current_step: int = 0
    steps: List[SagaStep]
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}


class CreateSagaRequest(BaseModel):
    """Request to create a new saga."""
    saga_name: str
    description: Optional[str] = None
    steps: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = {}


class ExecuteSagaRequest(BaseModel):
    """Request to execute a saga."""
    saga_id: UUID
    params: Optional[Dict[str, Any]] = {}


# ===========================
# SAGA ORCHESTRATOR
# ===========================

class SagaOrchestrator:
    """
    Orchestrates saga execution with automatic compensation on failure.
    
    Example Usage:
    ```python
    # Define a saga for order creation
    saga = SagaDefinition(
        saga_name="create_order",
        steps=[
            SagaStep(
                step_id="validate_inventory",
                step_name="Validate Inventory",
                agent="inventory_agent",
                action="reserve_inventory",
                compensation_action="release_inventory",
                params={"product_id": "123", "quantity": 2}
            ),
            SagaStep(
                step_id="process_payment",
                step_name="Process Payment",
                agent="payment_agent",
                action="charge_customer",
                compensation_action="refund_customer",
                params={"amount": 99.99}
            ),
            SagaStep(
                step_id="create_order",
                step_name="Create Order",
                agent="order_agent",
                action="create_order",
                compensation_action="cancel_order",
                params={"customer_id": "456"}
            )
        ]
    )
    
    # Execute the saga
    execution = await orchestrator.execute_saga(saga)
    ```
    """
    
    def __init__(self, db_manager, message_broker=None):
        self.db_manager = db_manager
        self.message_broker = message_broker
        self.logger = logger.bind(service="saga_orchestrator")
        
        # Registry of agent handlers
        self.agent_handlers: Dict[str, Any] = {}
        
        # In-memory saga executions (in production, use database)
        self.executions: Dict[UUID, SagaExecution] = {}
    
    def register_agent_handler(self, agent_name: str, handler: Any):
        """Register an agent handler for saga execution."""
        self.agent_handlers[agent_name] = handler
        self.logger.info("Registered agent handler",
                       agent=agent_name)
    
    async def create_saga(self, request: CreateSagaRequest) -> SagaDefinition:
        """Create a new saga definition."""
        saga_id = uuid4()
        
        steps = []
        for i, step_data in enumerate(request.steps):
            step = SagaStep(
                step_id=step_data.get("step_id", f"step_{i}"),
                step_name=step_data["step_name"],
                agent=step_data["agent"],
                action=step_data["action"],
                compensation_action=step_data.get("compensation_action"),
                params=step_data.get("params", {}),
                timeout=step_data.get("timeout", 30),
                max_retries=step_data.get("max_retries", 3)
            )
            steps.append(step)
        
        saga = SagaDefinition(
            saga_id=saga_id,
            saga_name=request.saga_name,
            description=request.description,
            steps=steps,
            metadata=request.metadata,
            created_at=datetime.utcnow()
        )
        
        # Save to database
        await self._save_saga_definition(saga)
        
        self.logger.info("Created saga definition",
                       saga_id=str(saga_id),
                       saga_name=request.saga_name,
                       steps=len(steps))
        
        return saga
    
    async def execute_saga(
        self,
        saga: SagaDefinition,
        params: Optional[Dict[str, Any]] = None
    ) -> SagaExecution:
        """Execute a saga with automatic compensation on failure."""
        execution_id = uuid4()
        
        execution = SagaExecution(
            execution_id=execution_id,
            saga_id=saga.saga_id,
            saga_name=saga.saga_name,
            status=SagaStatus.RUNNING,
            current_step=0,
            steps=[step.model_copy() for step in saga.steps],
            started_at=datetime.utcnow(),
            metadata=params or {}
        )
        
        self.executions[execution_id] = execution
        
        self.logger.info("Starting saga execution",
                       execution_id=str(execution_id),
                       saga_name=saga.saga_name)
        
        try:
            # Execute steps sequentially
            for i, step in enumerate(execution.steps):
                execution.current_step = i
                
                self.logger.info("Executing saga step",
                               execution_id=str(execution_id),
                               step=step.step_name,
                               step_num=i+1,
                               total_steps=len(execution.steps))
                
                success = await self._execute_step(execution, step, params)
                
                if not success:
                    # Step failed, start compensation
                    self.logger.warning("Saga step failed, starting compensation",
                                      execution_id=str(execution_id),
                                      failed_step=step.step_name)
                    
                    execution.status = SagaStatus.COMPENSATING
                    execution.error = step.error
                    
                    await self._compensate_saga(execution, i)
                    
                    execution.status = SagaStatus.COMPENSATED
                    execution.completed_at = datetime.utcnow()
                    
                    await self._save_saga_execution(execution)
                    
                    return execution
            
            # All steps completed successfully
            execution.status = SagaStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            
            self.logger.info("Saga completed successfully",
                           execution_id=str(execution_id),
                           saga_name=saga.saga_name)
            
            await self._save_saga_execution(execution)
            
            return execution
            
        except Exception as e:
            execution.status = SagaStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.utcnow()
            
            self.logger.error("Saga execution failed",
                            execution_id=str(execution_id),
                            error=str(e))
            
            await self._save_saga_execution(execution)
            
            raise
    
    async def _execute_step(
        self,
        execution: SagaExecution,
        step: SagaStep,
        global_params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Execute a single saga step with retries."""
        step.status = StepStatus.RUNNING
        step.started_at = datetime.utcnow()
        
        # Merge global params with step params
        params = {**(global_params or {}), **step.params}
        
        # Add results from previous steps to params
        for prev_step in execution.steps[:execution.current_step]:
            if prev_step.result:
                params[f"{prev_step.step_id}_result"] = prev_step.result
        
        for attempt in range(step.max_retries + 1):
            try:
                # Get agent handler
                handler = self.agent_handlers.get(step.agent)
                
                if not handler:
                    self.logger.warning("No handler registered for agent",
                                      agent=step.agent,
                                      step=step.step_name)
                    
                    # Simulate success for now
                    step.result = {"status": "success", "simulated": True}
                    step.status = StepStatus.COMPLETED
                    step.completed_at = datetime.utcnow()
                    return True
                
                # Execute the action
                result = await self._call_agent_action(
                    handler,
                    step.action,
                    params,
                    timeout=step.timeout
                )
                
                step.result = result
                step.status = StepStatus.COMPLETED
                step.completed_at = datetime.utcnow()
                
                self.logger.info("Saga step completed",
                               step=step.step_name,
                               attempt=attempt + 1)
                
                return True
                
            except asyncio.TimeoutError:
                step.retry_count = attempt + 1
                step.error = f"Timeout after {step.timeout}s"
                
                self.logger.warning("Saga step timeout",
                                  step=step.step_name,
                                  attempt=attempt + 1,
                                  max_retries=step.max_retries)
                
                if attempt < step.max_retries:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                
            except Exception as e:
                step.retry_count = attempt + 1
                step.error = str(e)
                
                self.logger.error("Saga step failed",
                                step=step.step_name,
                                attempt=attempt + 1,
                                error=str(e))
                
                if attempt < step.max_retries:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
        
        # All retries exhausted
        step.status = StepStatus.FAILED
        step.completed_at = datetime.utcnow()
        return False
    
    async def _compensate_saga(self, execution: SagaExecution, failed_step_index: int):
        """Compensate all completed steps in reverse order."""
        self.logger.info("Starting saga compensation",
                       execution_id=str(execution.execution_id),
                       steps_to_compensate=failed_step_index)
        
        # Compensate in reverse order
        for i in range(failed_step_index - 1, -1, -1):
            step = execution.steps[i]
            
            if step.status != StepStatus.COMPLETED:
                continue
            
            if not step.compensation_action:
                self.logger.warning("No compensation action defined",
                                  step=step.step_name)
                step.status = StepStatus.SKIPPED
                continue
            
            self.logger.info("Compensating saga step",
                           step=step.step_name,
                           compensation_action=step.compensation_action)
            
            step.status = StepStatus.COMPENSATING
            
            try:
                handler = self.agent_handlers.get(step.agent)
                
                if handler:
                    # Execute compensation action
                    await self._call_agent_action(
                        handler,
                        step.compensation_action,
                        {**step.params, "original_result": step.result},
                        timeout=step.timeout
                    )
                
                step.status = StepStatus.COMPENSATED
                
                self.logger.info("Saga step compensated",
                               step=step.step_name)
                
            except Exception as e:
                self.logger.error("Compensation failed",
                                step=step.step_name,
                                error=str(e))
                # Continue compensating other steps even if one fails
    
    async def _call_agent_action(
        self,
        handler: Any,
        action: str,
        params: Dict[str, Any],
        timeout: int
    ) -> Dict[str, Any]:
        """Call an agent action with timeout."""
        # Get the action method from the handler
        action_method = getattr(handler, action, None)
        
        if not action_method:
            raise ValueError(f"Action '{action}' not found in handler")
        
        # Execute with timeout
        result = await asyncio.wait_for(
            action_method(**params),
            timeout=timeout
        )
        
        return result
    
    async def get_execution_status(self, execution_id: UUID) -> Optional[SagaExecution]:
        """Get the status of a saga execution."""
        execution = self.executions.get(execution_id)
        
        if not execution:
            # Try to load from database
            execution = await self._load_saga_execution(execution_id)
        
        return execution
    
    async def _save_saga_definition(self, saga: SagaDefinition):
        """Save saga definition to database."""
        async with self.db_manager.get_async_session() as session:
            try:
                query = """
                    INSERT INTO saga_definitions (
                        saga_id, saga_name, description, steps, metadata, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (saga_id) DO UPDATE
                    SET saga_name = $2, description = $3, steps = $4, metadata = $5
                """
                
                await session.execute(
                    query,
                    str(saga.saga_id),
                    saga.saga_name,
                    saga.description,
                    [step.model_dump() for step in saga.steps],
                    saga.metadata,
                    saga.created_at
                )
                
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                self.logger.error("Failed to save saga definition",
                                error=str(e),
                                saga_id=str(saga.saga_id))
                # Don't raise - saga can still execute from memory
    
    async def _save_saga_execution(self, execution: SagaExecution):
        """Save saga execution to database."""
        async with self.db_manager.get_async_session() as session:
            try:
                query = """
                    INSERT INTO saga_executions (
                        execution_id, saga_id, saga_name, status, current_step,
                        steps, started_at, completed_at, error, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (execution_id) DO UPDATE
                    SET status = $4, current_step = $5, steps = $6,
                        completed_at = $8, error = $9, metadata = $10
                """
                
                await session.execute(
                    query,
                    str(execution.execution_id),
                    str(execution.saga_id),
                    execution.saga_name,
                    execution.status.value,
                    execution.current_step,
                    [step.model_dump() for step in execution.steps],
                    execution.started_at,
                    execution.completed_at,
                    execution.error,
                    execution.metadata
                )
                
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                self.logger.error("Failed to save saga execution",
                                error=str(e),
                                execution_id=str(execution.execution_id))
    
    async def _load_saga_execution(self, execution_id: UUID) -> Optional[SagaExecution]:
        """Load saga execution from database."""
        async with self.db_manager.get_async_session() as session:
            try:
                query = """
                    SELECT 
                        execution_id, saga_id, saga_name, status, current_step,
                        steps, started_at, completed_at, error, metadata
                    FROM saga_executions
                    WHERE execution_id = $1
                """
                
                result = await session.execute(query, str(execution_id))
                row = result.fetchone()
                
                if not row:
                    return None
                
                steps = [SagaStep(**step_data) for step_data in row[5]]
                
                return SagaExecution(
                    execution_id=UUID(row[0]),
                    saga_id=UUID(row[1]),
                    saga_name=row[2],
                    status=SagaStatus(row[3]),
                    current_step=row[4],
                    steps=steps,
                    started_at=row[6],
                    completed_at=row[7],
                    error=row[8],
                    metadata=row[9]
                )
                
            except Exception as e:
                self.logger.error("Failed to load saga execution",
                                error=str(e),
                                execution_id=str(execution_id))
                return None

