"""
Production Validation Suite

Unified test runner that executes all validation tests:
1. Workflow tests (100+ scenarios)
2. UI tests (70+ scenarios)
3. Agent health checks
4. Database connectivity tests
5. Kafka integration tests

Generates comprehensive production readiness report with detailed logs.
"""

import asyncio
import subprocess
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

# Import test suites
try:
    from comprehensive_workflow_tests import WorkflowTestSuite
    from ui_automation_tests import UITestSuite
except ImportError:
    print("Warning: Could not import test suites. Make sure they are in the same directory.")

# Setup detailed logging
log_dir = Path("test_logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'production_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# =====================================================
# PRODUCTION VALIDATION SUITE
# =====================================================

class ProductionValidationSuite:
    """
    Comprehensive production validation suite
    
    Runs all tests and generates detailed production readiness report
    """
    
    def __init__(self):
        self.start_time = datetime.now()
        self.results = {
            "workflow_tests": None,
            "ui_tests": None,
            "agent_health": None,
            "database_connectivity": None,
            "kafka_integration": None,
            "ui_connectivity": None
        }
    
    async def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation tests"""
        logger.info("=" * 100)
        logger.info("STARTING COMPREHENSIVE PRODUCTION VALIDATION")
        logger.info("=" * 100)
        logger.info(f"Start Time: {self.start_time}")
        logger.info("")
        
        # Phase 1: Infrastructure and Agent Health Checks (with Retries)
        logger.info("\n" + "=" * 100)
        logger.info("PHASE 1: INFRASTRUCTURE & AGENT HEALTH VALIDATION (with Retries)")
        logger.info("=" * 100)
        
        # 1.1 Agent Health Check (includes retry loop)
        self.results["agent_health"] = await self.validate_agent_health()
        
        # 1.2 Database Connectivity
        self.results["database_connectivity"] = await self.validate_database_connectivity()
        
        # 1.3 Kafka Integration
        self.results["kafka_integration"] = await self.validate_kafka_integration()
        
        # 1.4 UI (Vite) Connectivity
        self.results["ui_connectivity"] = await self.validate_ui_connectivity()

        # Check if critical components are up before running heavy tests
        if self.results["agent_health"]["health_rate"] < 90 or \
           self.results["database_connectivity"]["status"] != "connected" or \
           self.results["kafka_integration"]["status"] != "connected":
            logger.error("CRITICAL INFRASTRUCTURE FAILURE: Aborting workflow and UI tests.")
            return self.generate_production_readiness_report()

        # Phase 2: Workflow Tests
        logger.info("\n" + "=" * 100)
        logger.info("PHASE 2: WORKFLOW VALIDATION (100+ scenarios)")
        logger.info("=" * 100)
        
        try:
            async with WorkflowTestSuite() as workflow_suite:
                self.results["workflow_tests"] = await workflow_suite.run_all_tests()
                logger.info("[OK] Workflow tests completed")
        except Exception as e:
            logger.error(f"[ERROR] Workflow tests failed: {e}")
            self.results["workflow_tests"] = {"error": str(e)}
        
        # Phase 3: UI Tests
        logger.info("\n" + "=" * 100)
        logger.info("PHASE 3: UI VALIDATION (70+ scenarios)")
        logger.info("=" * 100)
        
        try:
            ui_suite = UITestSuite()
            self.results["ui_tests"] = await ui_suite.run_all_tests()
            logger.info("[OK] UI tests completed")
        except Exception as e:
            logger.error(f"[ERROR] UI tests failed: {e}")
            self.results["ui_tests"] = {"error": str(e)}
        
        # Generate final report
        return self.generate_production_readiness_report()
    
    async def validate_agent_health(self, max_retries=10, delay=5) -> Dict[str, Any]:
        """Validate health of all agents with retries"""
        import aiohttp
        
        agents = {
            "monitoring": 8000,
            "order": 8001,
            "product": 8002,
            "marketplace": 8003,
            "customer": 8004,
            "inventory": 8005,
            "transport": 8006,
            "payment": 8007,
            "warehouse": 8008,
            "document": 8009,
            "fraud": 8010,
            "risk": 8011,
            "knowledge": 8012,
            "aftersales": 8020,
            "backoffice": 8021,
            "quality": 8022
        }
        
        # Initial check and retry loop
        for attempt in range(max_retries):
            logger.info(f"Agent Health Check Attempt {attempt + 1}/{max_retries}...")
            
            health_results = []
            all_healthy = True
            
            async with aiohttp.ClientSession() as session:
                for agent_name, port in agents.items():
                    try:
                        url = f"http://localhost:{port}/health"
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as response:
                            if response.status == 200:
                                data = await response.json()
                                health_results.append({
                                    "agent": agent_name,
                                    "status": "healthy",
                                    "port": port,
                                    "response": data
                                })
                            else:
                                all_healthy = False
                                health_results.append({
                                    "agent": agent_name,
                                    "status": "unhealthy",
                                    "port": port,
                                    "http_status": response.status
                                })
                    except Exception as e:
                        all_healthy = False
                        health_results.append({
                            "agent": agent_name,
                            "status": "offline",
                            "port": port,
                            "error": str(e)
                        })

            if all_healthy:
                logger.info("[OK] All agents reported healthy.")
                break
            
            # Log status for the current attempt
            healthy_count = sum(1 for r in health_results if r["status"] == "healthy")
            offline_count = sum(1 for r in health_results if r["status"] == "offline")
            logger.warning(f"Status: {healthy_count}/{len(agents)} agents healthy. {offline_count} offline.")
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                logger.error("FATAL: Max retries reached. Not all agents are healthy.")

        # Final logging of results
        for r in health_results:
            if r["status"] == "healthy":
                logger.info(f"[OK] {r['agent']}: healthy")
            elif r["status"] == "unhealthy":
                logger.warning(f"[WARNING] {r['agent']}: unhealthy (HTTP {r['http_status']})")
            else:
                logger.error(f"[ERROR] {r['agent']}: offline ({r['error']})")
        
        healthy_count = sum(1 for r in health_results if r["status"] == "healthy")
        total_count = len(health_results)
        
        return {
            "total_agents": total_count,
            "healthy": healthy_count,
            "unhealthy": sum(1 for r in health_results if r["status"] == "unhealthy"),
            "offline": sum(1 for r in health_results if r["status"] == "offline"),
            "health_rate": (healthy_count / total_count * 100) if total_count > 0 else 0,
            "details": health_results
        }
    
    async def validate_database_connectivity(self) -> Dict[str, Any]:
        """Validate database connectivity"""
        try:
            import sys
            import os
            
            # Add project root to path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            from shared.database import DatabaseManager
            from shared.models import DatabaseConfig
            from sqlalchemy import text # Import text
            
            db_config = DatabaseConfig()
            db_manager = DatabaseManager(db_config)
            
            # Try to get a session
            async with db_manager.get_session() as session:
                # Try a simple query
                result = await session.execute(text("SELECT 1")) # Use text() for raw SQL
                row = result.fetchone()
                
                if row and row[0] == 1:
                    logger.info("[OK] Database connectivity: OK")
                    return {
                        "status": "connected",
                        "database": db_config.database,
                        "host": db_config.host,
                        "port": db_config.port
                    }
                else:
                    logger.error("[ERROR] Database connectivity: Failed (unexpected result)")
                    return {
                        "status": "error",
                        "error": "Unexpected query result"
                    }
        except Exception as e:
            logger.error(f"[ERROR] Database connectivity: Failed ({e})")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def validate_kafka_integration(self) -> Dict[str, Any]:
        """Validate Kafka integration"""
        try:
            import sys
            import os
            
            # Add project root to path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            from shared.kafka_config import KafkaProducer, KafkaConsumer
            
            # Try to create producer
            producer = KafkaProducer()
            
            # Try to send a test message
            test_message = {
                "test": "production_validation",
                "timestamp": datetime.now().isoformat()
            }
            
            await producer.send("test_topic", test_message)
            
            logger.info("[OK] Kafka integration: OK")
            
            return {
                "status": "connected",
                "producer": "working",
                "test_message_sent": True
            }
        except Exception as e:
            logger.error(f"[ERROR] Kafka integration: Failed ({e})")
            return {
                "status": "error",
                "error": str(e)
            }

    async def validate_ui_connectivity(self, url: str = "http://localhost:5173", max_retries=5, delay=5) -> Dict[str, Any]:
        """Validate UI (Vite) connectivity with retries"""
        import aiohttp
        
        for attempt in range(max_retries):
            logger.info(f"UI Connectivity Check Attempt {attempt + 1}/{max_retries}...")
            try:
                async with aiohttp.ClientSession() as session:
                    # Use a short timeout for a quick check
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            logger.info("[OK] UI connectivity: OK")
                            return {"status": "connected", "url": url}
                        else:
                            logger.warning(f"[WARNING] UI returned HTTP {response.status}. Retrying.")
            except Exception as e:
                logger.warning(f"[WARNING] UI connection failed: {e}. Retrying.")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
            else:
                logger.error("FATAL: UI connectivity failed after max retries.")
                return {"status": "error", "error": f"Failed to connect to UI at {url} after {max_retries} attempts."}

    
    def generate_production_readiness_report(self) -> Dict[str, Any]:
        """Generate comprehensive production readiness report"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calculate overall scores
        workflow_pass_rate = 0
        ui_pass_rate = 0
        agent_health_rate = 0
        
        if self.results["workflow_tests"] and "summary" in self.results["workflow_tests"]:
            workflow_pass_rate = self.results["workflow_tests"]["summary"]["pass_rate"]
        
        if self.results["ui_tests"] and "summary" in self.results["ui_tests"]:
            ui_pass_rate = self.results["ui_tests"]["summary"]["pass_rate"]
        
        if self.results["agent_health"]:
            agent_health_rate = self.results["agent_health"]["health_rate"]
        
        # Calculate overall production readiness score
        overall_score = (
            workflow_pass_rate * 0.40 +  # 40% weight
            ui_pass_rate * 0.25 +         # 25% weight
            agent_health_rate * 0.20 +    # 20% weight
            (100 if self.results["database_connectivity"]["status"] == "connected" else 0) * 0.05 +  # 5% weight
            (100 if self.results["kafka_integration"]["status"] == "connected" else 0) * 0.05 +  # 5% weight
            (100 if self.results["ui_connectivity"]["status"] == "connected" else 0) * 0.05  # 5% weight
        )
        
        # Determine production readiness status
        if overall_score >= 95:
            readiness_status = "PRODUCTION READY [OK]"
            recommendation = "System is ready for production deployment"
        elif overall_score >= 80:
            readiness_status = "MOSTLY READY [WARNING]"
            recommendation = "System is mostly ready, but some issues need attention"
        elif overall_score >= 60:
            readiness_status = "NEEDS WORK [WARNING]"
            recommendation = "Significant issues need to be resolved before production"
        else:
            readiness_status = "NOT READY [ERROR]"
            recommendation = "System is not ready for production deployment"
        
        report = {
            "validation_metadata": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_duration_seconds": total_duration,
                "validation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "production_readiness": {
                "overall_score": round(overall_score, 2),
                "status": readiness_status,
                "recommendation": recommendation
            },
            "test_results": {
                "workflow_tests": {
                    "pass_rate": workflow_pass_rate,
                    "total_tests": self.results["workflow_tests"]["summary"]["total_tests"] if self.results["workflow_tests"] and "summary" in self.results["workflow_tests"] else 0,
                    "passed": self.results["workflow_tests"]["summary"]["passed"] if self.results["workflow_tests"] and "summary" in self.results["workflow_tests"] else 0,
                    "failed": self.results["workflow_tests"]["summary"]["failed"] if self.results["workflow_tests"] and "summary" in self.results["workflow_tests"] else 0
                },
                "ui_tests": {
                    "pass_rate": ui_pass_rate,
                    "total_tests": self.results["ui_tests"]["summary"]["total_tests"] if self.results["ui_tests"] and "summary" in self.results["ui_tests"] else 0,
                    "passed": self.results["ui_tests"]["summary"]["passed"] if self.results["ui_tests"] and "summary" in self.results["ui_tests"] else 0,
                    "failed": self.results["ui_tests"]["summary"]["failed"] if self.results["ui_tests"] and "summary" in self.results["ui_tests"] else 0
                },
                "agent_health": {
                    "health_rate": agent_health_rate,
                    "total_agents": self.results["agent_health"]["total_agents"],
                    "healthy": self.results["agent_health"]["healthy"],
                    "offline": self.results["agent_health"]["offline"]
                },
                "infrastructure": {
            "database": self.results["database_connectivity"]["status"],
            "kafka": self.results["kafka_integration"]["status"],
            "ui_app": self.results["ui_connectivity"]["status"]
        }
            },
            "detailed_results": self.results
        }
        
        # Save report to file
        report_file = Path("test_logs") / f"production_readiness_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        logger.info("\n" + "=" * 100)
        logger.info("PRODUCTION READINESS REPORT")
        logger.info("=" * 100)
        logger.info(f"Overall Score: {overall_score:.2f}/100")
        logger.info(f"Status: {readiness_status}")
        logger.info(f"Recommendation: {recommendation}")
        logger.info("")
        logger.info(f"Workflow Tests: {workflow_pass_rate:.1f}% pass rate")
        logger.info(f"UI Tests: {ui_pass_rate:.1f}% pass rate")
        logger.info(f"Agent Health: {agent_health_rate:.1f}% healthy")
        logger.info(f"Database: {self.results['database_connectivity']['status']}")
        logger.info(f"Kafka: {self.results['kafka_integration']['status']}")
        logger.info(f"UI App: {self.results['ui_connectivity']['status']}")
        logger.info("")
        logger.info(f"Report saved: {report_file}")
        logger.info("=" * 100)
        
        return report


# =====================================================
# MAIN EXECUTION
# =====================================================

async def start_local_environment():
    """Starts the local development environment using the shell script."""
    script_path = Path(__file__).parent.parent / "scripts" / "start_local_dev.sh"
    logger.info(f"Attempting to start local environment using: {script_path}")
    
    try:
        # Use subprocess.Popen to run the script in the background
        # Note: This assumes the script is designed to start background processes (e.g., using 'nohup' or similar)
        # For a clean test environment, we'll rely on the shell script to start the agents.
        # Use nohup to ensure the script continues running even if the parent process dies,
        # and redirect output to a file for later inspection.
        log_file = script_path.parent.parent / "start_local_dev.log"
        process = subprocess.Popen(
            ["/usr/bin/nohup", "/bin/bash", str(script_path)],
            cwd=script_path.parent.parent, # Run from the project root
            stdout=open(log_file, "w"),
            stderr=open(log_file, "a"),
            start_new_session=True # Start in a new session to detach
        )
        logger.info(f"Local environment startup script started with PID: {process.pid}")
        # Give the script a moment to start the background processes
        await asyncio.sleep(5) 
        return process
    except Exception as e:
        logger.error(f"Failed to execute startup script: {e}")
        return None

async def main():
    """Main validation execution"""
    
    # 1. Start Local Environment
    startup_process = await start_local_environment()
    if startup_process is None:
        logger.error("FATAL: Could not start local environment. Aborting validation.")
        return
    
    # 2. Run Validation Suite
    suite = ProductionValidationSuite()
    report = await suite.run_all_validations()
    
    # 3. Cleanup (Optional, but good practice to stop processes if possible)
    # The start_local_dev.sh script is assumed to start background services.
    # Stopping them cleanly is difficult from a Python script without knowing their PIDs.
    # For now, we rely on the user to manually stop the services after the test.
    # logger.info("Please remember to stop the local environment services manually.")
    
    # 3. Cleanup (Optional, but good practice to stop processes if possible)
    # The start_local_dev.sh script is assumed to start background services.
    # Stopping them cleanly is difficult from a Python script without knowing their PIDs.
    # For now, we rely on the user to manually stop the services after the test.
    # logger.info("Please remember to stop the local environment services manually.")
    
    print("\n" + "=" * 100)
    print("PRODUCTION VALIDATION COMPLETE")
    print("=" * 100)
    print(f"Overall Score: {report['production_readiness']['overall_score']}/100")
    print(f"Status: {report['production_readiness']['status']}")
    print(f"Recommendation: {report['production_readiness']['recommendation']}")
    print("=" * 100)
    
    return report


if __name__ == "__main__":
    asyncio.run(main())

