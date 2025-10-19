#!/usr/bin/env python3
"""
Multi-Agent E-commerce System - Unified Monitor
Starts all agents and displays their output in one console with color-coded logs
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
    "order_agent": "\033[94m",  # Blue
    "inventory_agent": "\033[92m",  # Green
    "product_agent": "\033[96m",  # Cyan
    "carrier_selection_agent": "\033[95m",  # Magenta
    "warehouse_selection_agent": "\033[93m",  # Yellow
    "customer_communication_agent": "\033[91m",  # Red
    "demand_forecasting_agent": "\033[94m",  # Light Blue
    "dynamic_pricing_agent": "\033[92m",  # Light Green
    "reverse_logistics_agent": "\033[96m",  # Light Cyan
    "risk_anomaly_detection_agent": "\033[95m",  # Light Magenta
    "ai_monitoring_agent": "\033[93m",  # Light Yellow
    "d2c_ecommerce_agent": "\033[91m",  # Light Red
    "standard_marketplace_agent": "\033[35m",  # Purple
    "refurbished_marketplace_agent": "\033[36m",  # Teal
}

RESET = "\033[0m"
BOLD = "\033[1m"
ERROR_COLOR = "\033[91m"  # Red
WARNING_COLOR = "\033[93m"  # Yellow
SUCCESS_COLOR = "\033[92m"  # Green
INFO_COLOR = "\033[93m"  # Yellow (changed from blue)

# Agent configuration
AGENTS = [
    {"name": "ai_monitoring_agent", "display": "AI Monitor", "file": "agents/ai_monitoring_agent.py"},
    {"name": "product_agent", "display": "Product", "file": "agents/product_agent.py"},
    {"name": "inventory_agent", "display": "Inventory", "file": "agents/inventory_agent.py"},
    {"name": "warehouse_selection_agent", "display": "Warehouse", "file": "agents/warehouse_selection_agent.py"},
    {"name": "carrier_selection_agent", "display": "Carrier", "file": "agents/carrier_selection_agent.py"},
    {"name": "order_agent", "display": "Order", "file": "agents/order_agent.py"},
    {"name": "demand_forecasting_agent", "display": "Forecast", "file": "agents/demand_forecasting_agent.py"},
    {"name": "dynamic_pricing_agent", "display": "Pricing", "file": "agents/dynamic_pricing_agent.py"},
    {"name": "customer_communication_agent", "display": "Customer", "file": "agents/customer_communication_agent.py"},
    {"name": "reverse_logistics_agent", "display": "Returns", "file": "agents/reverse_logistics_agent.py"},
    {"name": "risk_anomaly_detection_agent", "display": "Risk", "file": "agents/risk_anomaly_detection_agent.py"},
    {"name": "standard_marketplace_agent", "display": "Marketplace", "file": "agents/standard_marketplace_agent.py"},
    {"name": "refurbished_marketplace_agent", "display": "Refurb", "file": "agents/refurbished_marketplace_agent.py"},
    {"name": "d2c_ecommerce_agent", "display": "D2C", "file": "agents/d2c_ecommerce_agent.py"},
]

class AgentMonitor:
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.threads: Dict[str, threading.Thread] = {}
        self.output_queue = queue.Queue()
        self.stop_requested = False
        self.error_count = {}
        self.start_time = {}
        
    def get_color(self, agent_name: str) -> str:
        """Get color for agent."""
        return COLORS.get(agent_name, RESET)
    
    def format_message(self, agent_name: str, display_name: str, message: str, is_error: bool = False) -> str:
        """Format message with color and timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = self.get_color(agent_name)
        
        # Detect error/warning/success patterns
        msg_lower = message.lower()
        if "error" in msg_lower or "exception" in msg_lower or "failed" in msg_lower or "crashed" in msg_lower or "traceback" in msg_lower or is_error:
            msg_color = ERROR_COLOR  # Red for errors
            prefix = "✗"
        elif "warning" in msg_lower or "warn" in msg_lower or "deprecated" in msg_lower:
            msg_color = WARNING_COLOR  # Yellow for warnings
            prefix = "⚠"
        elif "success" in msg_lower or "started" in msg_lower or "ready" in msg_lower or "complete" in msg_lower:
            msg_color = SUCCESS_COLOR  # Green for success
            prefix = "✓"
        else:
            msg_color = INFO_COLOR  # Yellow for info
            prefix = "•"
        
        # Format: [HH:MM:SS] [AgentName] • Message
        return f"{INFO_COLOR}[{timestamp}]{RESET} {color}{BOLD}[{display_name:12}]{RESET} {msg_color}{prefix} {message}{RESET}"
    
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
            print(self.format_message(agent_name, display_name, f"File not found: {agent_file}", True))
            return False
        
        try:
            print(self.format_message(agent_name, display_name, "Starting..."))
            
            # Start process
            process = subprocess.Popen(
                [sys.executable, agent_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
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
                print(self.format_message(agent_name, display_name, "Failed to start (immediate crash)", True))
                return False
            
            print(self.format_message(agent_name, display_name, f"Started (PID: {process.pid})"))
            return True
            
        except Exception as e:
            print(self.format_message(agent_name, display_name, f"Start error: {str(e)}", True))
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
        print(f"\n{BOLD}{INFO_COLOR}{'='*70}{RESET}")
        print(f"{BOLD}{INFO_COLOR}Agent Status Summary{RESET}")
        print(f"{BOLD}{INFO_COLOR}{'='*70}{RESET}\n")
        
        running = 0
        stopped = 0
        
        for agent in AGENTS:
            agent_name = agent["name"]
            display_name = agent["display"]
            color = self.get_color(agent_name)
            
            if agent_name in self.processes:
                process = self.processes[agent_name]
                if process.poll() is None:
                    uptime = int(time.time() - self.start_time.get(agent_name, time.time()))
                    errors = self.error_count.get(agent_name, 0)
                    error_str = f"{ERROR_COLOR}{errors} errors{RESET}" if errors > 0 else f"{SUCCESS_COLOR}No errors{RESET}"
                    print(f"{color}{BOLD}{display_name:20}{RESET} {SUCCESS_COLOR}✓ Running{RESET}  PID: {process.pid:6}  Uptime: {uptime}s  {error_str}")
                    running += 1
                else:
                    print(f"{color}{BOLD}{display_name:20}{RESET} {ERROR_COLOR}✗ Crashed{RESET}")
                    stopped += 1
            else:
                print(f"{color}{BOLD}{display_name:20}{RESET} {WARNING_COLOR}○ Not started{RESET}")
                stopped += 1
        
        print(f"\n{BOLD}Total: {len(AGENTS)}  Running: {SUCCESS_COLOR}{running}{RESET}  Stopped: {ERROR_COLOR}{stopped}{RESET}{BOLD}{RESET}\n")
    
    def run(self):
        """Main run loop."""
        # Print header
        print(f"\n{BOLD}{INFO_COLOR}{'='*70}{RESET}")
        print(f"{BOLD}{INFO_COLOR}Multi-Agent E-commerce System - Unified Monitor{RESET}")
        print(f"{BOLD}{INFO_COLOR}{'='*70}{RESET}\n")
        print(f"{INFO_COLOR}Starting all agents... Press Ctrl+C to stop{RESET}\n")
        
        # Start display thread
        display_thread = threading.Thread(target=self.display_output, daemon=True)
        display_thread.start()
        
        # Start all agents with delay
        for i, agent in enumerate(AGENTS, 1):
            self.start_agent(agent)
            print(f"{INFO_COLOR}Progress: {i}/{len(AGENTS)} agents started{RESET}\n")
            time.sleep(2)  # Delay between agent starts
        
        print(f"\n{BOLD}{SUCCESS_COLOR}{'='*70}{RESET}")
        print(f"{BOLD}{SUCCESS_COLOR}All agents started! Monitoring output...{RESET}")
        print(f"{BOLD}{SUCCESS_COLOR}{'='*70}{RESET}\n")
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
                                print(self.format_message(
                                    agent_name,
                                    agent["display"],
                                    f"Crashed with exit code {process.returncode}",
                                    True
                                ))
                    last_check = time.time()
                    
        except KeyboardInterrupt:
            pass
        
        # Show final status
        self.show_status()
        self.stop_all()
        
        print(f"\n{BOLD}{SUCCESS_COLOR}All agents stopped. Goodbye!{RESET}\n")

def signal_handler(sig, frame):
    """Handle Ctrl+C."""
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    monitor = AgentMonitor()
    monitor.run()

if __name__ == "__main__":
    main()

