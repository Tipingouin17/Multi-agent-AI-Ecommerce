from contextlib import asynccontextmanager

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
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logger.info(f"Added {project_root} to Python path")

# Import base agent and shared utilities
try:
    from shared.base_agent_v2 import BaseAgentV2, MessageType, AgentMessage
    from shared.db_helpers import DatabaseManager, DatabaseHelper, ProductDB
    logger.info("Successfully imported shared.base_agent and db_helpers")
except ImportError as e:
    logger.error(f"Import error for shared modules: {e}")
    raise

# Import new services (optional)
try:
    from agents.warehouse_capacity_service import WarehouseCapacityService
    logger.info("Successfully imported warehouse capacity service")
except ImportError as e:
    logger.warning(f"Could not import warehouse capacity service: {e}. Functionality will be limited.")
    WarehouseCapacityService = None

app = FastAPI()


class WarehouseAgent(BaseAgentV2):
    """
    Production-ready Warehouse Agent with capacity management and full database integration.

    This agent handles warehouse operations, including managing inventory, tracking capacity,
    and responding to various agent messages related to warehouse activities.
    It exposes a FastAPI interface for external communication and integrates with a database
    for persistent storage of warehouse-related data.
    """
    def __init__(self):
        """
        Initializes the WarehouseAgent, setting up its ID, type, database connection,
        FastAPI application, and message processing capabilities.
        """
        super().__init__(agent_id=os.getenv("AGENT_ID", "warehouse_agent"))
        self.db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./warehouse.db")
        self.db_manager = None
        self.db_helper = DatabaseHelper(self.db_manager)

        # Initialize capacity service
        self.capacity_service = WarehouseCapacityService(self.db_manager) if WarehouseCapacityService else None

        logger.info("Warehouse Agent initialized. Setting up database and FastAPI.")

        # FastAPI app setup
        
        
        # Add CORS middleware for dashboard integration
        
        # Add CORS middleware
        

