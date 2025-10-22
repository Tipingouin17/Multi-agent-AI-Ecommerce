#!/usr/bin/env python3
"""
Multi-Agent E-commerce System - Unified Monitor
Starts all PRODUCTION agents and displays their output in one console with color-coded logs
"""

import os
import sys
import time
import subprocess
import signal
import threading
import queue
from datetime import datetime
from typing import Dict, List
import re

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Color codes for different agents
COLORS = {
    "order_agent_production": "\033[94m",  # Blue
    "inventory_agent": "\033[92m",  # Green
    "product_agent_production": "\033[96m",  # Cyan
    "warehouse_agent_production": "\033[93m",  # Yellow
    "transport_agent_production": "\033[95m",  # Magenta
    "marketplace_connector_agent_production": "\033[91m",  # Red
    "after_sales_agent": "\033[94m",  # Light Blue
    "quality_control_agent": "\033[92m",  # Light Green
    "backoffice_agent": "\033[96m",  # Light Cyan
    "payment_agent_enhanced": "\033[95m",  # Light Magenta
    "customer_agent_enhanced": "\033[93m",  # Light Yellow
    "fraud_detection_agent": "\033[91m",  # Light Red
    "document_generation_agent": "\033[35m",  # Purple
    "knowledge_management_agent": "\033[36m",  # Teal
    "risk_anomaly_detection_agent": "\033[33m",  # Orange
}

RESET = "\033[0m"
BOLD = "\033[1m"
ERROR_COLOR = "\033[91m"  # Red
WARNING_COLOR = "\033[93m"  # Yellow
SUCCESS_COLOR = "\033[92m"  # Green
INFO_COLOR = "\033[96m"  # Cyan

# PRODUCTION Agent configuration - All 15 critical agents
AGENTS = [
    # Core Business Agents
    {"name": "order_agent_production", "display": "Order", "file": "agents/order_agent_production.py", "port": 8001},
    {"name": "inventory_agent", "display": "Inventory", "file": "agents/inventory_agent.py", "port": 8002},
    {"name": "product_agent_production", "display": "Product", "file": "agents/product_agent_production.py", "port": 8003},
    {"name": "payment_agent_enhanced", "display": "Payment", "file": "agents/payment_agent_enhanced.py", "port": 8004},
    
    # Logistics & Fulfillment
    {"name": "warehouse_agent_production", "display": "Warehouse", "file": "agents/warehouse_agent_production.py", "port": 8005},
    {"name": "transport_agent_production", "display": "Transport", "file": "agents/transport_agent_production.py", "port": 8006},
    {"name": "marketplace_connector_agent_production", "display": "Marketplace", "file": "agents/marketplace_connector_agent_production.py", "port": 8007},
    
    # Customer Service
    {"name": "customer_agent_enhanced", "display": "Customer", "file": "agents/customer_agent_enhanced.py", "port": 8008},
    {"name": "after_sales_agent", "display": "AfterSales", "file": "agents/after_sales_agent.py", "port": 8009},
    {"name": "document_generation_agent", "display": "Documents", "file": "agents/document_generation_agent.py", "port": 8013},
    
    # Quality & Compliance
    {"name": "quality_control_agent", "display": "Quality", "file": "agents/quality_control_agent.py", "port": 8010},
    {"name": "backoffice_agent", "display": "Backoffice", "file": "agents/backoffice_agent.py", "port": 8011},
    {"name": "knowledge_management_agent", "display": "Knowledge", "file": "agents/knowledge_management_agent.py", "port": 8020},
    
    # Security & Monitoring
    {"name": "fraud_detection_agent", "display": "Fraud", "file": "agents/fraud_detection_agent.py", "port": 8012},
    {"name": "risk_anomaly_detection_agent", "display": "Risk", "file": "agents/risk_anomaly_detection_agent.py", "port": 8021},
]

class AgentMonitor:
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
        log_filename = f"logs/agent_monitor_{timestamp}.log"
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
            # Remove ANSI color codes for file logging
            clean_message = re.sub(r'\033\[[0-9;]+m', '', message)
            self.log_file.write(clean_message + '\n')
            self.log_file.flush()
    
    def format_message(self, agent_name: str, display_name: str, message: str, is_error: bool = False) -> str:
        """Format message with color and timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = self.get_color(agent_name)
        
        # Detect error/warning/success patterns
        msg_lower = message.lower()
        if "error" in msg_lower or "exception" in msg_lower or "failed" in msg_lower or "crashed" in msg_lower or "traceback" in msg_lower or is_error:
            msg_color = ERROR_COLOR  # Red for errors
            prefix = "[X]"
        elif "warning" in msg_lower or "warn" in msg_lower or "deprecated" in msg_lower:
            msg_color = WARNING_COLOR  # Yellow for warnings
            prefix = "[!]"
        elif "success" in msg_lower or "started" in msg_lower or "ready" in msg_lower or "complete" in msg_lower or "running" in msg_lower:
            msg_color = SUCCESS_COLOR  # Green for success
            prefix = "[OK]"
        else:
            msg_color = INFO_COLOR  # Cyan for info
            prefix = "•"
        
        # Format: [HH:MM:SS] [AgentName] • Message
        formatted = f"{INFO_COLOR}[{timestamp}]{RESET} {color}{BOLD}[{display_name:12}]{RESET} {msg_color}{prefix} {message}{RESET}"
        
        # Log to file
        self.log_to_file(formatted)
        
        return formatted
    
    def read_output(self, agent_name: str, display_name: str, stream, is_error: bool = False):
        """Read output from agent process."""
        try:
            for line in iter(stream.readline, ''):
                if line:
                    line = line.strip()
                    if line:
                        # Track errors
                        if is_error or any(pattern in line.lower() for pattern in ['error', 'exception', 'failed', 'traceback']):
                            self.error_count[agent_name] = self.error_count.get(agent_name, 0) + 1
                        
                        formatted = self.format_message(agent_name, display_name, line, is_error)
                        self.output_queue.put(formatted)
        except Exception as e:
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
            
            # Prepare environment with database/Kafka settings
            env = os.environ.copy()
            
            # CRITICAL: Add project root to PYTHONPATH so agents can import 'shared' module
            project_root = os.path.dirname(os.path.abspath(__file__))
            pythonpath = env.get('PYTHONPATH', '')
            if pythonpath:
                env['PYTHONPATH'] = f"{project_root}{os.pathsep}{pythonpath}"
            else:
                env['PYTHONPATH'] = project_root
            
            # Ensure critical environment variables are set
            if 'DATABASE_HOST' not in env:
                env['DATABASE_HOST'] = 'localhost'
            if 'KAFKA_BOOTSTRAP_SERVERS' not in env:
                env['KAFKA_BOOTSTRAP_SERVERS'] = 'localhost:9092'
            if 'DATABASE_PASSWORD' not in env:
                env['DATABASE_PASSWORD'] = 'postgres'  # Default for local dev
            
            # Start process with environment
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
            
            # Start threads to read stdout and stderr
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
            
            # Wait a moment to check for immediate crashes
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
    
    def stop_agent(self, agent_name: str, display_name: str):
        """Stop an agent process."""
        if agent_name not in self.processes:
            return
        
        process = self.processes[agent_name]
        if process.poll() is None:
            print(self.format_message(agent_name, display_name, "Stopping..."))
            process.terminate()
            try:
                process.wait(timeout=5)
                print(self.format_message(agent_name, display_name, "Stopped"))
            except subprocess.TimeoutExpired:
                process.kill()
                print(self.format_message(agent_name, display_name, "Force killed"))
    
    def stop_all(self):
        """Stop all agents."""
        self.stop_requested = True
        print(f"\n{BOLD}{WARNING_COLOR}Stopping all agents...{RESET}\n")
        
        for agent in reversed(AGENTS):
            self.stop_agent(agent["name"], agent["display"])
        
        self.processes.clear()
    
    def show_status(self):
        """Show status of all agents."""
        print(f"\n{BOLD}{INFO_COLOR}{'='*80}{RESET}")
        print(f"{BOLD}{INFO_COLOR}Agent Status Summary{RESET}")
        print(f"{BOLD}{INFO_COLOR}{'='*80}{RESET}\n")
        
        running = 0
        stopped = 0
        
        for agent in AGENTS:
            agent_name = agent["name"]
            display_name = agent["display"]
            port = agent.get("port", "N/A")
            color = self.get_color(agent_name)
            
            if agent_name in self.processes:
                process = self.processes[agent_name]
                if process.poll() is None:
                    uptime = int(time.time() - self.start_time.get(agent_name, time.time()))
                    errors = self.error_count.get(agent_name, 0)
                    error_str = f"{ERROR_COLOR}{errors} errors{RESET}" if errors > 0 else f"{SUCCESS_COLOR}No errors{RESET}"
                    print(f"{color}{BOLD}{display_name:15}{RESET} {SUCCESS_COLOR}[OK] Running{RESET}  Port: {port:5}  PID: {process.pid:6}  Uptime: {uptime:4}s  {error_str}")
                    running += 1
                else:
                    print(f"{color}{BOLD}{display_name:15}{RESET} {ERROR_COLOR}[X] Crashed{RESET}  (exit code: {process.returncode})")
                    stopped += 1
            else:
                print(f"{color}{BOLD}{display_name:15}{RESET} {WARNING_COLOR}○ Not started{RESET}")
                stopped += 1
        
        print(f"\n{BOLD}Total: {len(AGENTS)}  Running: {SUCCESS_COLOR}{running}{RESET}  Stopped: {ERROR_COLOR}{stopped}{RESET}{BOLD}{RESET}\n")
    
    def run(self):
        """Main run loop."""
        # Print header
        print(f"\n{BOLD}{INFO_COLOR}{'='*80}{RESET}")
        print(f"{BOLD}{INFO_COLOR}Multi-Agent E-commerce System - Production Monitor{RESET}")
        print(f"{BOLD}{INFO_COLOR}{'='*80}{RESET}\n")
        print(f"{INFO_COLOR}Starting all {len(AGENTS)} production agents... Press Ctrl+C to stop{RESET}\n")
        
        # Check environment
        print(f"{INFO_COLOR}Environment Configuration:{RESET}")
        print(f"  DATABASE_HOST: {os.environ.get('DATABASE_HOST', 'localhost')}")
        print(f"  KAFKA_BOOTSTRAP_SERVERS: {os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')}")
        print(f"  DATABASE_PASSWORD: {'***' if os.environ.get('DATABASE_PASSWORD') else 'Not set (using default)'}")
        print()
        
        # Start display thread
        display_thread = threading.Thread(target=self.display_output, daemon=True)
        display_thread.start()
        
        # Start all agents with delay
        for i, agent in enumerate(AGENTS, 1):
            self.start_agent(agent)
            print(f"{INFO_COLOR}Progress: {i}/{len(AGENTS)} agents started{RESET}\n")
            time.sleep(2)  # Delay between agent starts
        
        print(f"\n{BOLD}{SUCCESS_COLOR}{'='*80}{RESET}")
        print(f"{BOLD}{SUCCESS_COLOR}All {len(AGENTS)} agents started! Monitoring output...{RESET}")
        print(f"{BOLD}{SUCCESS_COLOR}{'='*80}{RESET}\n")
        print(f"{INFO_COLOR}Commands: Press Ctrl+C to stop all agents{RESET}\n")
        
        # Monitor processes
        try:
            check_interval = 10
            last_check = time.time()
            
            while not self.stop_requested:
                time.sleep(1)
                
                # Periodically check for crashed agents
                if time.time() - last_check > check_interval:
                    for agent in AGENTS:
                        agent_name = agent["name"]
                        if agent_name in self.processes:
                            process = self.processes[agent_name]
                            if process.poll() is not None:
                                msg = self.format_message(
                                    agent_name,
                                    agent["display"],
                                    f"Crashed with exit code {process.returncode}",
                                    True
                                )
                                print(msg)
                    last_check = time.time()
                    
        except KeyboardInterrupt:
            pass
        
        # Show final status
        self.show_status()
        self.stop_all()
        
        print(f"\n{BOLD}{SUCCESS_COLOR}All agents stopped. Goodbye!{RESET}\n")
        
        # Close log file
        if self.log_file and not self.log_file.closed:
            self.log_file.close()

def signal_handler(sig, frame):
    """Handle Ctrl+C."""
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    monitor = AgentMonitor()
    monitor.run()

if __name__ == "__main__":
    main()

