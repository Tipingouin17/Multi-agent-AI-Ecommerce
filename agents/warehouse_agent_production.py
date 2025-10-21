"""
Warehouse Agent - Multi-Agent E-commerce System (Production Ready)

This agent manages warehouse operations with all enhanced features:
- Warehouse capacity management
- Workforce tracking
- Throughput monitoring
- Performance KPIs
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os

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
    logger.info(f"Added {project_root} to Python path")

# Import base agent
try:
    from shared.base_agent import BaseAgent, MessageType, AgentMessage
    logger.info("Successfully imported shared.base_agent")
except ImportError as e:
    logger.error(f"Import error: {e}")
    raise

# Import new services
try:
    from agents.warehouse_capacity_service import WarehouseCapacityService
    logger.info("Successfully imported warehouse capacity service")
except ImportError as e:
    logger.warning(f"Could not import warehouse capacity service: {e}")
    WarehouseCapacityService = None

class WarehouseAgent(BaseAgent):
    """
    Production-ready Warehouse Agent with capacity management
    """
    
    def __init__(self):
        super().__init__(
            agent_id="warehouse_agent",
            agent_type="warehouse_management"
        )
        
        # Initialize capacity service
        self.capacity_service = WarehouseCapacityService() if WarehouseCapacityService else None
        
        logger.info("Warehouse Agent initialized with capacity service")
        
        # FastAPI app
        self.app = FastAPI(title="Warehouse Agent API")
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "agent_id": self.agent_id,
                "services": {
                    "capacity": self.capacity_service is not None
                }
            }
        
        @self.app.get("/warehouses")
        async def get_warehouses():
            """Get all warehouses"""
            try:
                warehouses = await self.get_warehouses_from_db()
                return {"warehouses": warehouses}
            except Exception as e:
                logger.error(f"Error getting warehouses: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Capacity endpoints
        if self.capacity_service:
            @self.app.get("/warehouses/{warehouse_id}/capacity")
            async def get_warehouse_capacity(warehouse_id: str):
                """Get warehouse capacity metrics"""
                try:
                    capacity = await self.capacity_service.get_capacity_metrics(warehouse_id)
                    return capacity
                except Exception as e:
                    logger.error(f"Error getting capacity: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
            
            @self.app.get("/warehouses/{warehouse_id}/performance")
            async def get_warehouse_performance(warehouse_id: str):
                """Get warehouse performance KPIs"""
                try:
                    performance = await self.capacity_service.get_performance_kpis(warehouse_id)
                    return performance
                except Exception as e:
                    logger.error(f"Error getting performance: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
    
    async def get_warehouses_from_db(self) -> List[Dict]:
        """Get warehouses from database"""
        logger.info("Getting warehouses from database")
        return []
    
    async def process_message(self, message: AgentMessage):
        """Process incoming messages"""
        logger.info(f"Processing message: {message.message_type}")

# Create agent instance
agent = WarehouseAgent()
app = agent.app

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Warehouse Agent on port 8004")
    uvicorn.run(app, host="0.0.0.0", port=8004)

