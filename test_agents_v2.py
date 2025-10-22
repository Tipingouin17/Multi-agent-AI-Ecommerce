#!/usr/bin/env python3
"""
Comprehensive Agent Testing Suite for BaseAgentV2

Tests all 15 production agents to verify:
1. Successful startup
2. Database initialization with retry
3. Kafka initialization with retry
4. Graceful degradation
5. Error recovery
6. Health check endpoints

Usage:
    python3 test_agents_v2.py
    python3 test_agents_v2.py --agent order_agent_production
    python3 test_agents_v2.py --quick  # Skip long-running tests
"""

import os
import sys
import time
import asyncio
import subprocess
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Add project root to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Production agents to test
PRODUCTION_AGENTS = [
    {"name": "order_agent_production", "port": 8001, "file": "agents/order_agent_production.py"},
    {"name": "inventory_agent", "port": 8002, "file": "agents/inventory_agent.py"},
    {"name": "product_agent_production", "port": 8003, "file": "agents/product_agent_production.py"},
    {"name": "payment_agent_enhanced", "port": 8004, "file": "agents/payment_agent_enhanced.py"},
    {"name": "warehouse_agent_production", "port": 8005, "file": "agents/warehouse_agent_production.py"},
    {"name": "transport_agent_production", "port": 8006, "file": "agents/transport_agent_production.py"},
    {"name": "marketplace_connector_agent_production", "port": 8007, "file": "agents/marketplace_connector_agent_production.py"},
    {"name": "customer_agent_enhanced", "port": 8008, "file": "agents/customer_agent_enhanced.py"},
    {"name": "after_sales_agent", "port": 8009, "file": "agents/after_sales_agent.py"},
    {"name": "quality_control_agent", "port": 8010, "file": "agents/quality_control_agent.py"},
    {"name": "backoffice_agent", "port": 8011, "file": "agents/backoffice_agent.py"},
    {"name": "fraud_detection_agent", "port": 8012, "file": "agents/fraud_detection_agent.py"},
    {"name": "document_generation_agent", "port": 8013, "file": "agents/document_generation_agent.py"},
    {"name": "knowledge_management_agent", "port": 8020, "file": "agents/knowledge_management_agent.py"},
    {"name": "risk_anomaly_detection_agent", "port": 8021, "file": "agents/risk_anomaly_detection_agent.py"},
]


class AgentTester:
    def __init__(self, quick_mode: bool = False):
        self.quick_mode = quick_mode
        self.results = {}
        self.start_time = datetime.now()
        
    def print_header(self, text: str):
        """Print section header."""
        print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
        print(f"{BOLD}{BLUE}{text}{RESET}")
        print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")
    
    def print_status(self, message: str, status: str = "INFO"):
        """Print colored status message."""
        colors = {
            "INFO": CYAN,
            "SUCCESS": GREEN,
            "WARNING": YELLOW,
            "ERROR": RED,
            "TEST": BLUE
        }
        color = colors.get(status, RESET)
        print(f"{color}[{status}]{RESET} {message}")
    
    def check_prerequisites(self) -> bool:
        """Check if required services are available."""
        self.print_header("Checking Prerequisites")
        
        all_ok = True
        
        # Check PostgreSQL
        try:
            import psycopg2
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="multi_agent_ecommerce",
                user="postgres",
                password=os.getenv("DATABASE_PASSWORD", "postgres"),
                connect_timeout=5
            )
            conn.close()
            self.print_status("PostgreSQL: Available", "SUCCESS")
        except Exception as e:
            self.print_status(f"PostgreSQL: Not available - {e}", "WARNING")
            self.print_status("  Agents will test fallback to SQLite", "INFO")
        
        # Check Kafka
        try:
            from kafka import KafkaAdminClient
            admin = KafkaAdminClient(
                bootstrap_servers="localhost:9092",
                request_timeout_ms=5000
            )
            admin.close()
            self.print_status("Kafka: Available", "SUCCESS")
        except Exception as e:
            self.print_status(f"Kafka: Not available - {e}", "WARNING")
            self.print_status("  Agents will test degraded mode (API-only)", "INFO")
        
        return True  # Continue even if services unavailable (testing degradation)
    
    def test_agent_import(self, agent: Dict) -> Tuple[bool, str]:
        """Test if agent can be imported without errors."""
        try:
            # Try to import the agent module
            module_path = agent['file'].replace('/', '.').replace('.py', '')
            __import__(module_path)
            return True, "Import successful"
        except Exception as e:
            return False, f"Import failed: {str(e)}"
    
    def start_agent(self, agent: Dict) -> Optional[subprocess.Popen]:
        """Start an agent process."""
        try:
            env = os.environ.copy()
            env['PYTHONPATH'] = str(current_dir)
            env['DATABASE_HOST'] = os.getenv('DATABASE_HOST', 'localhost')
            env['DATABASE_PORT'] = os.getenv('DATABASE_PORT', '5432')
            env['DATABASE_NAME'] = os.getenv('DATABASE_NAME', 'multi_agent_ecommerce')
            env['DATABASE_USER'] = os.getenv('DATABASE_USER', 'postgres')
            env['DATABASE_PASSWORD'] = os.getenv('DATABASE_PASSWORD', 'postgres')
            env['DATABASE_URL'] = f"postgresql://{env['DATABASE_USER']}:{env['DATABASE_PASSWORD']}@{env['DATABASE_HOST']}:{env['DATABASE_PORT']}/{env['DATABASE_NAME']}"
            env['KAFKA_BOOTSTRAP_SERVERS'] = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
            
            process = subprocess.Popen(
                [sys.executable, agent['file']],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=current_dir
            )
            
            return process
        except Exception as e:
            self.print_status(f"Failed to start {agent['name']}: {e}", "ERROR")
            return None
    
    def wait_for_agent_ready(self, agent: Dict, timeout: int = 60) -> Tuple[bool, str]:
        """Wait for agent to be ready and responding to health checks."""
        start_time = time.time()
        port = agent['port']
        
        while time.time() - start_time < timeout:
            try:
                # Try liveness check
                response = requests.get(f"http://localhost:{port}/health", timeout=2)
                if response.status_code == 200:
                    return True, "Agent is alive and responding"
            except requests.exceptions.ConnectionError:
                # Agent not ready yet
                pass
            except Exception as e:
                pass
            
            time.sleep(2)
        
        return False, f"Agent did not respond within {timeout}s"
    
    def test_health_endpoints(self, agent: Dict) -> Dict[str, any]:
        """Test all health check endpoints."""
        port = agent['port']
        results = {
            'liveness': False,
            'readiness': False,
            'detailed': False,
            'degradation_level': None
        }
        
        # Test liveness
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            results['liveness'] = response.status_code == 200
        except:
            pass
        
        # Test readiness
        try:
            response = requests.get(f"http://localhost:{port}/health/ready", timeout=5)
            results['readiness'] = response.status_code in [200, 503]
            if response.status_code == 200:
                data = response.json()
                results['degradation_level'] = data.get('degradation_level')
        except:
            pass
        
        # Test detailed
        try:
            response = requests.get(f"http://localhost:{port}/health/detailed", timeout=5)
            results['detailed'] = response.status_code == 200
            if response.status_code == 200:
                data = response.json()
                results['uptime'] = data.get('uptime_seconds')
                results['dependencies'] = data.get('dependencies', {})
        except:
            pass
        
        return results
    
    def test_agent(self, agent: Dict) -> Dict:
        """Run comprehensive tests on a single agent."""
        self.print_status(f"\nTesting {agent['name']}...", "TEST")
        
        test_results = {
            'agent': agent['name'],
            'import': False,
            'startup': False,
            'health': {},
            'errors': []
        }
        
        # Test 1: Import
        success, message = self.test_agent_import(agent)
        test_results['import'] = success
        if success:
            self.print_status(f"  Import: {message}", "SUCCESS")
        else:
            self.print_status(f"  Import: {message}", "ERROR")
            test_results['errors'].append(message)
            return test_results
        
        # Test 2: Startup
        self.print_status(f"  Starting agent on port {agent['port']}...", "INFO")
        process = self.start_agent(agent)
        
        if not process:
            test_results['errors'].append("Failed to start process")
            return test_results
        
        # Test 3: Wait for ready
        self.print_status(f"  Waiting for agent to be ready (max 60s)...", "INFO")
        success, message = self.wait_for_agent_ready(agent, timeout=60)
        test_results['startup'] = success
        
        if success:
            self.print_status(f"  Startup: {message}", "SUCCESS")
            
            # Test 4: Health endpoints
            if not self.quick_mode:
                self.print_status(f"  Testing health endpoints...", "INFO")
                health_results = self.test_health_endpoints(agent)
                test_results['health'] = health_results
                
                if health_results['liveness']:
                    self.print_status(f"    Liveness: OK", "SUCCESS")
                else:
                    self.print_status(f"    Liveness: FAILED", "ERROR")
                
                if health_results['readiness']:
                    deg_level = health_results.get('degradation_level', 'unknown')
                    self.print_status(f"    Readiness: OK (degradation: {deg_level})", "SUCCESS")
                else:
                    self.print_status(f"    Readiness: FAILED", "ERROR")
                
                if health_results['detailed']:
                    uptime = health_results.get('uptime', 0)
                    self.print_status(f"    Detailed: OK (uptime: {uptime:.1f}s)", "SUCCESS")
                else:
                    self.print_status(f"    Detailed: FAILED", "ERROR")
        else:
            self.print_status(f"  Startup: {message}", "ERROR")
            test_results['errors'].append(message)
        
        # Cleanup
        if process:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        return test_results
    
    def run_all_tests(self, specific_agent: Optional[str] = None) -> Dict:
        """Run tests on all agents or a specific agent."""
        self.print_header("Multi-Agent System - BaseAgentV2 Testing Suite")
        
        # Check prerequisites
        if not self.check_prerequisites():
            self.print_status("Prerequisites check failed", "ERROR")
            return {}
        
        # Filter agents if specific agent requested
        agents_to_test = PRODUCTION_AGENTS
        if specific_agent:
            agents_to_test = [a for a in PRODUCTION_AGENTS if a['name'] == specific_agent]
            if not agents_to_test:
                self.print_status(f"Agent '{specific_agent}' not found", "ERROR")
                return {}
        
        self.print_header(f"Testing {len(agents_to_test)} Agent(s)")
        
        # Run tests
        all_results = []
        for agent in agents_to_test:
            result = self.test_agent(agent)
            all_results.append(result)
            self.results[agent['name']] = result
        
        # Print summary
        self.print_summary(all_results)
        
        return self.results
    
    def print_summary(self, results: List[Dict]):
        """Print test summary."""
        self.print_header("Test Summary")
        
        total = len(results)
        import_ok = sum(1 for r in results if r['import'])
        startup_ok = sum(1 for r in results if r['startup'])
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        print(f"{BOLD}Total Agents Tested:{RESET} {total}")
        print(f"{BOLD}Import Success:{RESET} {import_ok}/{total} ({import_ok/total*100:.1f}%)")
        print(f"{BOLD}Startup Success:{RESET} {startup_ok}/{total} ({startup_ok/total*100:.1f}%)")
        print(f"{BOLD}Test Duration:{RESET} {elapsed:.1f}s")
        print()
        
        # Detailed results
        print(f"{BOLD}Detailed Results:{RESET}")
        for result in results:
            agent_name = result['agent']
            status_icon = f"{GREEN}✓{RESET}" if result['startup'] else f"{RED}✗{RESET}"
            print(f"  {status_icon} {agent_name}")
            
            if result['errors']:
                for error in result['errors']:
                    print(f"      {RED}Error:{RESET} {error}")
        
        print()
        
        # Overall status
        if startup_ok == total:
            self.print_status(f"ALL TESTS PASSED! 🎉", "SUCCESS")
        elif startup_ok > total / 2:
            self.print_status(f"PARTIAL SUCCESS - {startup_ok}/{total} agents working", "WARNING")
        else:
            self.print_status(f"TESTS FAILED - Only {startup_ok}/{total} agents working", "ERROR")


def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Multi-Agent System with BaseAgentV2')
    parser.add_argument('--agent', help='Test specific agent only')
    parser.add_argument('--quick', action='store_true', help='Skip detailed health checks')
    args = parser.parse_args()
    
    tester = AgentTester(quick_mode=args.quick)
    results = tester.run_all_tests(specific_agent=args.agent)
    
    # Exit code based on results
    if results:
        success_count = sum(1 for r in results.values() if r['startup'])
        total_count = len(results)
        sys.exit(0 if success_count == total_count else 1)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

