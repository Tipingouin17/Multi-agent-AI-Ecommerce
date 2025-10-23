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
            "kafka_integration": None
        }
    
    async def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation tests"""
        logger.info("=" * 100)
        logger.info("STARTING COMPREHENSIVE PRODUCTION VALIDATION")
        logger.info("=" * 100)
        logger.info(f"Start Time: {self.start_time}")
        logger.info("")
        
        # Phase 1: Workflow Tests
        logger.info("\n" + "=" * 100)
        logger.info("PHASE 1: WORKFLOW VALIDATION (100+ scenarios)")
        logger.info("=" * 100)
        
        try:
            async with WorkflowTestSuite() as workflow_suite:
                self.results["workflow_tests"] = await workflow_suite.run_all_tests()
                logger.info("✅ Workflow tests completed")
        except Exception as e:
            logger.error(f"❌ Workflow tests failed: {e}")
            self.results["workflow_tests"] = {"error": str(e)}
        
        # Phase 2: UI Tests
        logger.info("\n" + "=" * 100)
        logger.info("PHASE 2: UI VALIDATION (70+ scenarios)")
        logger.info("=" * 100)
        
        try:
            ui_suite = UITestSuite()
            self.results["ui_tests"] = await ui_suite.run_all_tests()
            logger.info("✅ UI tests completed")
        except Exception as e:
            logger.error(f"❌ UI tests failed: {e}")
            self.results["ui_tests"] = {"error": str(e)}
        
        # Phase 3: Agent Health Checks
        logger.info("\n" + "=" * 100)
        logger.info("PHASE 3: AGENT HEALTH VALIDATION")
        logger.info("=" * 100)
        
        self.results["agent_health"] = await self.validate_agent_health()
        
        # Phase 4: Database Connectivity
        logger.info("\n" + "=" * 100)
        logger.info("PHASE 4: DATABASE CONNECTIVITY VALIDATION")
        logger.info("=" * 100)
        
        self.results["database_connectivity"] = await self.validate_database_connectivity()
        
        # Phase 5: Kafka Integration
        logger.info("\n" + "=" * 100)
        logger.info("PHASE 5: KAFKA INTEGRATION VALIDATION")
        logger.info("=" * 100)
        
        self.results["kafka_integration"] = await self.validate_kafka_integration()
        
        # Generate final report
        return self.generate_production_readiness_report()
    
    async def validate_agent_health(self) -> Dict[str, Any]:
        """Validate health of all agents"""
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
        
        health_results = []
        
        async with aiohttp.ClientSession() as session:
            for agent_name, port in agents.items():
                try:
                    url = f"http://localhost:{port}/health"
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            data = await response.json()
                            health_results.append({
                                "agent": agent_name,
                                "status": "healthy",
                                "port": port,
                                "response": data
                            })
                            logger.info(f"✅ {agent_name}: healthy")
                        else:
                            health_results.append({
                                "agent": agent_name,
                                "status": "unhealthy",
                                "port": port,
                                "http_status": response.status
                            })
                            logger.warning(f"⚠️  {agent_name}: unhealthy (HTTP {response.status})")
                except Exception as e:
                    health_results.append({
                        "agent": agent_name,
                        "status": "offline",
                        "port": port,
                        "error": str(e)
                    })
                    logger.error(f"❌ {agent_name}: offline ({e})")
        
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
            
            db_config = DatabaseConfig()
            db_manager = DatabaseManager(db_config)
            
            # Try to get a session
            async with db_manager.get_session() as session:
                # Try a simple query
                result = await session.execute("SELECT 1")
                row = result.fetchone()
                
                if row and row[0] == 1:
                    logger.info("✅ Database connectivity: OK")
                    return {
                        "status": "connected",
                        "database": db_config.database,
                        "host": db_config.host,
                        "port": db_config.port
                    }
                else:
                    logger.error("❌ Database connectivity: Failed (unexpected result)")
                    return {
                        "status": "error",
                        "error": "Unexpected query result"
                    }
        except Exception as e:
            logger.error(f"❌ Database connectivity: Failed ({e})")
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
            
            logger.info("✅ Kafka integration: OK")
            
            return {
                "status": "connected",
                "producer": "working",
                "test_message_sent": True
            }
        except Exception as e:
            logger.error(f"❌ Kafka integration: Failed ({e})")
            return {
                "status": "error",
                "error": str(e)
            }
    
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
            ui_pass_rate * 0.30 +         # 30% weight
            agent_health_rate * 0.20 +    # 20% weight
            (100 if self.results["database_connectivity"]["status"] == "connected" else 0) * 0.05 +  # 5% weight
            (100 if self.results["kafka_integration"]["status"] == "connected" else 0) * 0.05  # 5% weight
        )
        
        # Determine production readiness status
        if overall_score >= 95:
            readiness_status = "PRODUCTION READY ✅"
            recommendation = "System is ready for production deployment"
        elif overall_score >= 80:
            readiness_status = "MOSTLY READY ⚠️"
            recommendation = "System is mostly ready, but some issues need attention"
        elif overall_score >= 60:
            readiness_status = "NEEDS WORK ⚠️"
            recommendation = "Significant issues need to be resolved before production"
        else:
            readiness_status = "NOT READY ❌"
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
                    "kafka": self.results["kafka_integration"]["status"]
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
        logger.info("")
        logger.info(f"Report saved: {report_file}")
        logger.info("=" * 100)
        
        return report


# =====================================================
# MAIN EXECUTION
# =====================================================

async def main():
    """Main validation execution"""
    suite = ProductionValidationSuite()
    report = await suite.run_all_validations()
    
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

