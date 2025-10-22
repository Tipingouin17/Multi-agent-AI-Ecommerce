#!/usr/bin/env python3
"""
Comprehensive Agent Startup and Logging Script

This script tests all agents and captures detailed logs for debugging.
Designed to be run in production/staging environments to verify agent health.

Usage:
    python scripts/test_all_agents_with_logging.py

Output:
    - logs/agent_startup_TIMESTAMP.log - Main log file
    - logs/agents/AGENT_NAME_TIMESTAMP.log - Individual agent logs
    - logs/summary_TIMESTAMP.json - JSON summary of all results
"""

import asyncio
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Create logs directory structure
LOGS_DIR = project_root / "logs"
AGENT_LOGS_DIR = LOGS_DIR / "agents"
LOGS_DIR.mkdir(exist_ok=True)
AGENT_LOGS_DIR.mkdir(exist_ok=True)

# Timestamp for this run
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Main log file
MAIN_LOG_FILE = LOGS_DIR / f"agent_startup_{TIMESTAMP}.log"
SUMMARY_FILE = LOGS_DIR / f"summary_{TIMESTAMP}.json"

# Configure main logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(MAIN_LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


# List of all agents to test
AGENTS_TO_TEST = [
    # Phase 1 Critical Agents
    {
        "name": "OrderAgent",
        "module": "agents.order_agent_production",
        "class": "OrderAgent",
        "priority": "critical",
        "init_kwargs": {}
    },
    {
        "name": "InventoryAgent",
        "module": "agents.inventory_agent",
        "class": "InventoryAgent",
        "priority": "critical",
        "init_kwargs": {}
    },
    {
        "name": "ProductAgent",
        "module": "agents.product_agent_production",
        "class": "ProductAgent",
        "priority": "critical",
        "init_kwargs": {}
    },
    {
        "name": "WarehouseAgent",
        "module": "agents.warehouse_agent_production",
        "class": "WarehouseAgent",
        "priority": "critical",
        "init_kwargs": {}
    },
    {
        "name": "TransportAgent",
        "module": "agents.transport_agent_production",
        "class": "TransportAgentProduction",
        "priority": "critical",
        "init_kwargs": {}
    },
    {
        "name": "MarketplaceConnector",
        "module": "agents.marketplace_connector_agent_production",
        "class": "MarketplaceConnectorAgentProduction",
        "priority": "critical",
        "init_kwargs": {}
    },
    {
        "name": "AfterSalesAgent",
        "module": "agents.after_sales_agent",
        "class": "AfterSalesAgent",
        "priority": "critical",
        "init_kwargs": {}
    },
    {
        "name": "QualityControlAgent",
        "module": "agents.quality_control_agent",
        "class": "QualityControlAgent",
        "priority": "critical",
        "init_kwargs": {}
    },
    {
        "name": "BackofficeAgent",
        "module": "agents.backoffice_agent",
        "class": "BackofficeAgent",
        "priority": "critical",
        "init_kwargs": {}
    },
    {
        "name": "PaymentAgent",
        "module": "agents.payment_agent_enhanced",
        "class": "PaymentAgent",
        "priority": "critical",
        "init_kwargs": {}
    },
    # Phase 2 Agents
    {
        "name": "CustomerAgent",
        "module": "agents.customer_agent_enhanced",
        "class": "CustomerAgent",
        "priority": "high",
        "init_kwargs": {"agent_id": "customer_agent_001", "agent_type": "customer_agent"}
    },
    {
        "name": "DocumentGenerationAgent",
        "module": "agents.document_generation_agent",
        "class": "DocumentGenerationAgent",
        "priority": "medium",
        "init_kwargs": {}
    },
    {
        "name": "KnowledgeManagementAgent",
        "module": "agents.knowledge_management_agent",
        "class": "KnowledgeManagementAgent",
        "priority": "medium",
        "init_kwargs": {}
    },
    {
        "name": "FraudDetectionAgent",
        "module": "agents.fraud_detection_agent",
        "class": "FraudDetectionAgent",
        "priority": "high",
        "init_kwargs": {}
    },
    {
        "name": "RiskAnomalyDetectionAgent",
        "module": "agents.risk_anomaly_detection_agent",
        "class": "RiskAnomalyDetectionAgent",
        "priority": "high",
        "init_kwargs": {}
    },
]


class AgentTester:
    """Test individual agents and capture detailed logs"""
    
    def __init__(self, agent_config: Dict[str, Any]):
        self.config = agent_config
        self.name = agent_config["name"]
        self.log_file = AGENT_LOGS_DIR / f"{self.name}_{TIMESTAMP}.log"
        
        # Create agent-specific logger
        self.logger = logging.getLogger(f"AgentTester.{self.name}")
        handler = logging.FileHandler(self.log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
        
        self.results = {
            "name": self.name,
            "module": agent_config["module"],
            "class": agent_config["class"],
            "priority": agent_config["priority"],
            "timestamp": datetime.now().isoformat(),
            "import_success": False,
            "instantiate_success": False,
            "initialize_success": False,
            "has_cleanup": False,
            "has_process_business_logic": False,
            "cleanup_success": False,
            "errors": [],
            "warnings": [],
            "log_file": str(self.log_file)
        }
    
    async def test_agent(self) -> Dict[str, Any]:
        """Test agent lifecycle and capture results"""
        self.logger.info(f"Starting test for {self.name}")
        
        try:
            # Step 1: Import module
            self.logger.info(f"Importing module: {self.config['module']}")
            try:
                module = __import__(self.config['module'], fromlist=[self.config['class']])
                agent_class = getattr(module, self.config['class'])
                self.results["import_success"] = True
                self.logger.info(f"✅ Successfully imported {self.config['class']}")
            except Exception as e:
                error_msg = f"Import failed: {str(e)}\n{traceback.format_exc()}"
                self.logger.error(error_msg)
                self.results["errors"].append(error_msg)
                self.results["status"] = "❌ FAIL"
                return self.results
            
            # Step 2: Instantiate agent
            self.logger.info(f"Instantiating {self.name}")
            try:
                agent = agent_class(**self.config["init_kwargs"])
                self.results["instantiate_success"] = True
                self.logger.info(f"✅ Successfully instantiated {self.name}")
            except Exception as e:
                error_msg = f"Instantiation failed: {str(e)}\n{traceback.format_exc()}"
                self.logger.error(error_msg)
                self.results["errors"].append(error_msg)
                self.results["status"] = "❌ FAIL"
                return self.results
            
            # Step 3: Check for required methods
            self.logger.info("Checking for required abstract methods")
            self.results["has_cleanup"] = hasattr(agent, 'cleanup') and callable(getattr(agent, 'cleanup'))
            self.results["has_process_business_logic"] = hasattr(agent, 'process_business_logic') and callable(getattr(agent, 'process_business_logic'))
            
            if not self.results["has_cleanup"]:
                self.results["warnings"].append("Missing cleanup() method")
                self.logger.warning("⚠️  Missing cleanup() method")
            
            if not self.results["has_process_business_logic"]:
                self.results["warnings"].append("Missing process_business_logic() method")
                self.logger.warning("⚠️  Missing process_business_logic() method")
            
            # Step 4: Try to initialize (with timeout)
            self.logger.info("Attempting to initialize agent (30s timeout)")
            try:
                await asyncio.wait_for(agent.initialize(), timeout=30.0)
                self.results["initialize_success"] = True
                self.logger.info(f"✅ Successfully initialized {self.name}")
            except asyncio.TimeoutError:
                error_msg = "Initialization timeout (30s) - likely waiting for Kafka/DB connection"
                self.logger.error(error_msg)
                self.results["errors"].append(error_msg)
                self.results["warnings"].append("Agent may require external services (Kafka/PostgreSQL)")
                # Don't return, try cleanup anyway
            except Exception as e:
                error_msg = f"Initialization failed: {str(e)}\n{traceback.format_exc()}"
                self.logger.error(error_msg)
                self.results["errors"].append(error_msg)
            
            # Step 5: Try cleanup (with timeout)
            if self.results["has_cleanup"]:
                self.logger.info("Attempting cleanup (10s timeout)")
                try:
                    await asyncio.wait_for(agent.cleanup(), timeout=10.0)
                    self.results["cleanup_success"] = True
                    self.logger.info(f"✅ Successfully cleaned up {self.name}")
                except asyncio.TimeoutError:
                    error_msg = "Cleanup timeout (10s)"
                    self.logger.error(error_msg)
                    self.results["errors"].append(error_msg)
                except Exception as e:
                    error_msg = f"Cleanup failed: {str(e)}\n{traceback.format_exc()}"
                    self.logger.error(error_msg)
                    self.results["errors"].append(error_msg)
            
            # Overall status
            if self.results["import_success"] and self.results["instantiate_success"]:
                if self.results["initialize_success"] and self.results["cleanup_success"]:
                    self.results["status"] = "✅ PASS"
                elif len(self.results["errors"]) > 0:
                    self.results["status"] = "❌ FAIL"
                else:
                    self.results["status"] = "⚠️  PARTIAL"
            else:
                self.results["status"] = "❌ FAIL"
            
            self.logger.info(f"Test completed for {self.name}: {self.results['status']}")
            
        except Exception as e:
            error_msg = f"Unexpected error during test: {str(e)}\n{traceback.format_exc()}"
            self.logger.error(error_msg)
            self.results["errors"].append(error_msg)
            self.results["status"] = "❌ FAIL"
        
        return self.results


async def test_all_agents():
    """Test all agents and generate comprehensive report"""
    logger.info("="*80)
    logger.info("MULTI-AGENT E-COMMERCE SYSTEM - PRODUCTION READINESS TEST")
    logger.info("="*80)
    logger.info(f"Timestamp: {TIMESTAMP}")
    logger.info(f"Main log file: {MAIN_LOG_FILE}")
    logger.info(f"Agent logs directory: {AGENT_LOGS_DIR}")
    logger.info(f"Summary file: {SUMMARY_FILE}")
    logger.info("="*80)
    
    all_results = []
    
    # Test each agent
    for agent_config in AGENTS_TO_TEST:
        logger.info(f"\nTesting {agent_config['name']} ({agent_config['priority']} priority)...")
        tester = AgentTester(agent_config)
        results = await tester.test_agent()
        all_results.append(results)
        logger.info(f"Status: {results['status']}")
    
    # Generate summary
    summary = {
        "timestamp": TIMESTAMP,
        "total_agents": len(all_results),
        "passed": sum(1 for r in all_results if r["status"] == "✅ PASS"),
        "failed": sum(1 for r in all_results if r["status"] == "❌ FAIL"),
        "partial": sum(1 for r in all_results if r["status"] == "⚠️  PARTIAL"),
        "critical_agents": {
            "total": sum(1 for r in all_results if r["priority"] == "critical"),
            "passed": sum(1 for r in all_results if r["priority"] == "critical" and r["status"] == "✅ PASS"),
            "failed": sum(1 for r in all_results if r["priority"] == "critical" and r["status"] == "❌ FAIL"),
        },
        "agents": all_results,
        "log_files": {
            "main_log": str(MAIN_LOG_FILE),
            "agent_logs_dir": str(AGENT_LOGS_DIR),
            "summary": str(SUMMARY_FILE)
        }
    }
    
    # Save summary to JSON
    with open(SUMMARY_FILE, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    logger.info(f"Total Agents Tested: {summary['total_agents']}")
    logger.info(f"Passed: {summary['passed']} ({100*summary['passed']//summary['total_agents']}%)")
    logger.info(f"Failed: {summary['failed']} ({100*summary['failed']//summary['total_agents']}%)")
    logger.info(f"Partial: {summary['partial']} ({100*summary['partial']//summary['total_agents']}%)")
    logger.info("")
    logger.info(f"Critical Agents: {summary['critical_agents']['passed']}/{summary['critical_agents']['total']} passed")
    logger.info("="*80)
    
    logger.info("\nDETAILED RESULTS BY PRIORITY:")
    
    for priority in ["critical", "high", "medium"]:
        agents = [r for r in all_results if r["priority"] == priority]
        if agents:
            logger.info(f"\n{priority.upper()} PRIORITY ({len(agents)} agents):")
            for result in agents:
                status_icon = result["status"]
                logger.info(f"  {status_icon} {result['name']}")
                if result["errors"]:
                    logger.info(f"     Errors: {len(result['errors'])}")
                if result["warnings"]:
                    logger.info(f"     Warnings: {len(result['warnings'])}")
                logger.info(f"     Log: {result['log_file']}")
    
    logger.info("\n" + "="*80)
    logger.info("NEXT STEPS:")
    logger.info("="*80)
    logger.info("1. Review the summary file:")
    logger.info(f"   {SUMMARY_FILE}")
    logger.info("")
    logger.info("2. Check individual agent logs for errors:")
    logger.info(f"   {AGENT_LOGS_DIR}/")
    logger.info("")
    logger.info("3. For failed agents, check the error messages in:")
    logger.info(f"   {MAIN_LOG_FILE}")
    logger.info("")
    logger.info("4. Common issues to check:")
    logger.info("   - Kafka connection (localhost:9092)")
    logger.info("   - PostgreSQL connection (localhost:5432)")
    logger.info("   - Environment variables (.env file)")
    logger.info("   - Missing dependencies (requirements.txt)")
    logger.info("="*80)
    
    return summary


if __name__ == "__main__":
    print("\n" + "="*80)
    print("MULTI-AGENT E-COMMERCE SYSTEM - PRODUCTION READINESS TEST")
    print("="*80)
    print(f"Starting test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Logs will be saved to: {LOGS_DIR}")
    print("="*80 + "\n")
    
    try:
        summary = asyncio.run(test_all_agents())
        
        print("\n" + "="*80)
        print("TEST COMPLETED")
        print("="*80)
        print(f"Summary saved to: {SUMMARY_FILE}")
        print(f"Main log saved to: {MAIN_LOG_FILE}")
        print(f"Agent logs saved to: {AGENT_LOGS_DIR}")
        print("="*80 + "\n")
        
        # Exit with appropriate code
        if summary["failed"] > 0:
            sys.exit(1)
        elif summary["partial"] > 0:
            sys.exit(2)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {str(e)}")
        print(traceback.format_exc())
        sys.exit(1)

