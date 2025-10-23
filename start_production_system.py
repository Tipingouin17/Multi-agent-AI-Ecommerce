#!/usr/bin/env python3
"""
Multi-Agent E-commerce System - Production Startup & Testing
Starts all 16 production-ready agents and runs comprehensive validation tests
"""

import os
import sys
import time
import subprocess
import signal
import threading
import queue
import json
from datetime import datetime
from typing import Dict, List
import re

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Color codes
COLORS = {
    "monitoring": "\033[97m",  # White
    "order": "\033[94m",  # Blue
    "product": "\033[92m",  # Green
    "marketplace": "\033[96m",  # Cyan
    "customer": "\033[93m",  # Yellow
    "inventory": "\033[95m",  # Magenta
    "transport": "\033[91m",  # Red
    "payment": "\033[35m",  # Purple
    "warehouse": "\033[36m",  # Teal
    "document": "\033[33m",  # Orange
    "fraud": "\033[31m",  # Dark Red
    "risk": "\033[32m",  # Dark Green
    "knowledge": "\033[34m",  # Dark Blue
    "aftersales": "\033[35m",  # Dark Purple
    "backoffice": "\033[36m",  # Dark Cyan
    "quality": "\033[37m",  # Light Gray
}

RESET = "\033[0m"
BOLD = "\033[1m"
ERROR_COLOR = "\033[91m"
WARNING_COLOR = "\033[93m"
SUCCESS_COLOR = "\033[92m"
INFO_COLOR = "\033[96m"

# PRODUCTION Agent configuration - All 16 production-ready agents
AGENTS = [
    # Monitoring & Analytics
    {"name": "monitoring", "display": "Monitoring", "file": "agents/monitoring_agent.py", "port": 8000},
    
    # Core Business
    {"name": "order", "display": "Order", "file": "agents/order_agent_production_v2.py", "port": 8001},
    {"name": "product", "display": "Product", "file": "agents/product_agent_production.py", "port": 8002},
    {"name": "marketplace", "display": "Marketplace", "file": "agents/marketplace_connector_agent.py", "port": 8003},
    {"name": "customer", "display": "Customer", "file": "agents/customer_agent_enhanced.py", "port": 8004},
    
    # Operations
    {"name": "inventory", "display": "Inventory", "file": "agents/inventory_agent.py", "port": 8005},
    {"name": "transport", "display": "Transport", "file": "agents/transport_agent_production.py", "port": 8006},
    {"name": "payment", "display": "Payment", "file": "agents/payment_agent_enhanced.py", "port": 8007},
    {"name": "warehouse", "display": "Warehouse", "file": "agents/warehouse_agent_production.py", "port": 8008},
    
    # Support Services
    {"name": "document", "display": "Documents", "file": "agents/document_generation_agent.py", "port": 8009},
    {"name": "fraud", "display": "Fraud", "file": "agents/fraud_detection_agent.py", "port": 8010},
    {"name": "risk", "display": "Risk", "file": "agents/risk_anomaly_detection_agent.py", "port": 8011},
    {"name": "knowledge", "display": "Knowledge", "file": "agents/knowledge_management_agent.py", "port": 8012},
    
    # New Production Agents
    {"name": "aftersales", "display": "AfterSales", "file": "agents/after_sales_agent_production.py", "port": 8020},
    {"name": "backoffice", "display": "Backoffice", "file": "agents/backoffice_agent_production.py", "port": 8021},
    {"name": "quality", "display": "Quality", "file": "agents/quality_control_agent_production.py", "port": 8022},
]


class ProductionSystemManager:
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.threads: Dict[str, threading.Thread] = {}
        self.output_queue = queue.Queue()
        self.stop_requested = False
        self.error_count = {}
        self.start_time = {}
        self.log_file = None
        
        # Create logs directory
        os.makedirs("logs", exist_ok=True)
        
        # Open log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"logs/production_system_{timestamp}.log"
        self.log_file = open(log_filename, 'w', encoding='utf-8')
        print(f"{INFO_COLOR}Logging to: {log_filename}{RESET}\n")
        
    def __del__(self):
        """Close log file on cleanup."""
        if self.log_file and not self.log_file.closed:
            self.log_file.close()
    
    def get_color(self, agent_name: str) -> str:
        """Get color for agent."""
        return COLORS.get(agent_name, RESET)
    
    def log_to_file(self, message: str):
        """Write message to log file without color codes."""
        if self.log_file and not self.log_file.closed:
            # Remove ANSI color codes
            clean_message = re.sub(r'\033\[[0-9;]+m', '', message)
            self.log_file.write(clean_message + '\n')
            self.log_file.flush()
    
    def format_message(self, agent_name: str, display_name: str, message: str, is_error: bool = False) -> str:
        """Format message with color and timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = self.get_color(agent_name)
        
        # Detect error/warning/success patterns
        msg_lower = message.lower()
        if "error" in msg_lower or "exception" in msg_lower or "failed" in msg_lower or is_error:
            msg_color = ERROR_COLOR
            prefix = "[X]"
        elif "warning" in msg_lower or "warn" in msg_lower:
            msg_color = WARNING_COLOR
            prefix = "[!]"
        elif "success" in msg_lower or "started" in msg_lower or "ready" in msg_lower:
            msg_color = SUCCESS_COLOR
            prefix = "[OK]"
        else:
            msg_color = INFO_COLOR
            prefix = "•"
        
        formatted = f"{INFO_COLOR}[{timestamp}]{RESET} {color}{BOLD}[{display_name:12}]{RESET} {msg_color}{prefix} {message}{RESET}"
        self.log_to_file(formatted)
        return formatted
    
    def read_output(self, agent_name: str, display_name: str, stream, is_error: bool = False):
        """Read output from agent process."""
        try:
            for line in iter(stream.readline, ''):
                if line:
                    line = line.strip()
                    if line:
                        if is_error or any(pattern in line.lower() for pattern in ['error', 'exception', 'failed']):
                            self.error_count[agent_name] = self.error_count.get(agent_name, 0) + 1
                        
                        formatted = self.format_message(agent_name, display_name, line, is_error)
                        self.output_queue.put(formatted)
        except Exception:
            pass
    
    def display_output(self):
        """Display output from all agents."""
        while not self.stop_requested:
            try:
                message = self.output_queue.get(timeout=0.1)
                print(message, flush=True)
            except queue.Empty:
                continue
    
    def start_agent(self, agent: Dict) -> bool:
        """Start an agent and monitor its output."""
        agent_name = agent["name"]
        display_name = agent["display"]
        agent_file = agent["file"]
        
        if not os.path.exists(agent_file):
            msg = self.format_message(agent_name, display_name, f"File not found: {agent_file}", True)
            print(msg)
            return False
        
        try:
            print(self.format_message(agent_name, display_name, "Starting..."))
            
            # Prepare environment
            env = os.environ.copy()
            
            # Add project root to PYTHONPATH
            project_root = os.path.dirname(os.path.abspath(__file__))
            pythonpath = env.get('PYTHONPATH', '')
            if pythonpath:
                env['PYTHONPATH'] = f"{project_root}{os.pathsep}{pythonpath}"
            else:
                env['PYTHONPATH'] = project_root
            
            # Set default environment variables if not set
            if 'DATABASE_HOST' not in env:
                env['DATABASE_HOST'] = 'localhost'
            if 'KAFKA_BOOTSTRAP_SERVERS' not in env:
                env['KAFKA_BOOTSTRAP_SERVERS'] = 'localhost:9092'
            if 'DATABASE_PASSWORD' not in env:
                env['DATABASE_PASSWORD'] = 'postgres'
            if 'DATABASE_URL' not in env:
                env['DATABASE_URL'] = 'postgresql+asyncpg://postgres:postgres@localhost:5432/multi_agent_ecommerce'
            
            # Start process
            process = subprocess.Popen(
                [sys.executable, agent_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env
            )
            
            self.processes[agent_name] = process
            self.start_time[agent_name] = time.time()
            self.error_count[agent_name] = 0
            
            # Start output monitoring threads
            stdout_thread = threading.Thread(
                target=self.read_output,
                args=(agent_name, display_name, process.stdout, False),
                daemon=True
            )
            stderr_thread = threading.Thread(
                target=self.read_output,
                args=(agent_name, display_name, process.stderr, True),
                daemon=True
            )
            
            stdout_thread.start()
            stderr_thread.start()
            
            self.threads[f"{agent_name}_stdout"] = stdout_thread
            self.threads[f"{agent_name}_stderr"] = stderr_thread
            
            # Check for immediate crashes
            time.sleep(0.5)
            if process.poll() is not None:
                msg = self.format_message(agent_name, display_name, "Failed to start (immediate crash)", True)
                print(msg)
                return False
            
            msg = self.format_message(agent_name, display_name, f"Started (PID: {process.pid}, Port: {agent.get('port', 'N/A')})")
            print(msg)
            return True
            
        except Exception as e:
            msg = self.format_message(agent_name, display_name, f"Start error: {str(e)}", True)
            print(msg)
            return False
    
    def stop_all_agents(self):
        """Stop all running agents."""
        print(f"\n{WARNING_COLOR}Stopping all agents...{RESET}")
        
        for agent_name, process in self.processes.items():
            if process and process.poll() is None:
                print(f"Stopping {agent_name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        
        self.processes = {}
        print(f"{SUCCESS_COLOR}All agents stopped{RESET}")
    
    def check_agent_health(self) -> Dict[str, any]:
        """Check health of all agents."""
        import requests
        
        results = {
            "total": len(AGENTS),
            "healthy": 0,
            "unhealthy": 0,
            "details": []
        }
        
        for agent in AGENTS:
            try:
                response = requests.get(f"http://localhost:{agent['port']}/health", timeout=2)
                if response.status_code == 200:
                    results["healthy"] += 1
                    results["details"].append({
                        "agent": agent["name"],
                        "status": "healthy",
                        "port": agent["port"]
                    })
                else:
                    results["unhealthy"] += 1
                    results["details"].append({
                        "agent": agent["name"],
                        "status": "unhealthy",
                        "port": agent["port"],
                        "http_status": response.status_code
                    })
            except Exception as e:
                results["unhealthy"] += 1
                results["details"].append({
                    "agent": agent["name"],
                    "status": "offline",
                    "port": agent["port"],
                    "error": str(e)
                })
        
        return results
    
    def start_all_agents(self):
        """Start all agents."""
        print(f"\n{BOLD}{SUCCESS_COLOR}{'='*80}{RESET}")
        print(f"{BOLD}{SUCCESS_COLOR}Multi-Agent E-commerce System - Production Startup{RESET}")
        print(f"{BOLD}{SUCCESS_COLOR}{'='*80}{RESET}\n")
        
        # Start output display thread
        display_thread = threading.Thread(target=self.display_output, daemon=True)
        display_thread.start()
        
        # Start all agents
        started_count = 0
        for agent in AGENTS:
            if self.start_agent(agent):
                started_count += 1
            time.sleep(1)  # Delay between agent starts
        
        print(f"\n{SUCCESS_COLOR}Started {started_count}/{len(AGENTS)} agents{RESET}\n")
        
        # Wait for agents to initialize
        print(f"{INFO_COLOR}Waiting 10 seconds for agents to initialize...{RESET}")
        time.sleep(10)
        
        # Check health
        print(f"\n{BOLD}Checking agent health...{RESET}")
        health = self.check_agent_health()
        
        print(f"\n{BOLD}Health Check Results:{RESET}")
        print(f"  Total Agents: {health['total']}")
        print(f"  {SUCCESS_COLOR}Healthy: {health['healthy']}{RESET}")
        print(f"  {ERROR_COLOR}Offline: {health['unhealthy']}{RESET}")
        print(f"  Health Rate: {health['healthy']/health['total']*100:.1f}%\n")
        
        return health
    
    def run_tests(self):
        """Run comprehensive validation tests."""
        print(f"\n{BOLD}{INFO_COLOR}{'='*80}{RESET}")
        print(f"{BOLD}{INFO_COLOR}Running Comprehensive Validation Tests{RESET}")
        print(f"{BOLD}{INFO_COLOR}{'='*80}{RESET}\n")
        
        # Run workflow tests
        print(f"{INFO_COLOR}Running workflow tests...{RESET}")
        workflow_result = subprocess.run(
            [sys.executable, "testing/comprehensive_workflow_tests.py"],
            capture_output=True,
            text=True
        )
        
        # Run UI tests
        print(f"{INFO_COLOR}Running UI tests...{RESET}")
        ui_result = subprocess.run(
            [sys.executable, "testing/ui_automation_tests.py"],
            capture_output=True,
            text=True
        )
        
        # Run production validation
        print(f"{INFO_COLOR}Running production validation suite...{RESET}")
        validation_result = subprocess.run(
            [sys.executable, "testing/production_validation_suite.py"],
            capture_output=True,
            text=True
        )
        
        print(f"\n{SUCCESS_COLOR}All tests completed!{RESET}")
        print(f"{INFO_COLOR}Check test_logs/ directory for detailed results{RESET}\n")
    
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C."""
        self.stop_requested = True
        self.stop_all_agents()
        sys.exit(0)


def main():
    """Main entry point."""
    manager = ProductionSystemManager()
    
    # Register signal handler
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    # Start all agents
    health = manager.start_all_agents()
    
    # Ask if user wants to run tests
    if health['healthy'] >= 15:  # At least 15 out of 16 agents healthy
        print(f"\n{BOLD}System is ready!{RESET}")
        print(f"\nOptions:")
        print(f"  1. Run comprehensive validation tests")
        print(f"  2. Keep agents running (press Ctrl+C to stop)")
        print(f"  3. Stop all agents and exit")
        
        choice = input(f"\n{INFO_COLOR}Enter choice (1-3): {RESET}").strip()
        
        if choice == "1":
            manager.run_tests()
            print(f"\n{INFO_COLOR}Agents are still running. Press Ctrl+C to stop.{RESET}")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                manager.stop_all_agents()
        elif choice == "2":
            print(f"\n{INFO_COLOR}Agents are running. Press Ctrl+C to stop.{RESET}")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                manager.stop_all_agents()
        else:
            manager.stop_all_agents()
    else:
        print(f"\n{ERROR_COLOR}Too many agents failed to start. Please check logs.{RESET}")
        manager.stop_all_agents()


if __name__ == "__main__":
    main()

