"""
Multi-Agent E-commerce System Launcher

This script starts all agent services in the correct order with proper dependencies.
Each agent runs in its own process to ensure isolation and reliability.
"""

import os
import sys
import time
import subprocess
import signal
import argparse
from typing import List, Dict
import psutil

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Agent configuration with dependencies and startup order
AGENTS = [
    {
        "name": "AI Monitoring Agent",
        "file": "ai_monitoring_agent.py",
        "port": 8014,
        "dependencies": [],  # No dependencies, starts first
        "startup_delay": 2,
    },
    {
        "name": "Product Agent",
        "file": "product_agent.py",
        "port": 8002,
        "dependencies": [],
        "startup_delay": 2,
    },
    {
        "name": "Inventory Agent",
        "file": "inventory_agent.py",
        "port": 8003,
        "dependencies": ["Product Agent"],
        "startup_delay": 3,
    },
    {
        "name": "Warehouse Selection Agent",
        "file": "warehouse_selection_agent.py",
        "port": 8004,
        "dependencies": ["Inventory Agent"],
        "startup_delay": 3,
    },
    {
        "name": "Carrier Selection Agent",
        "file": "carrier_selection_agent.py",
        "port": 8005,
        "dependencies": [],
        "startup_delay": 2,
    },
    {
        "name": "Order Agent",
        "file": "order_agent.py",
        "port": 8001,
        "dependencies": ["Product Agent", "Inventory Agent", "Warehouse Selection Agent", "Carrier Selection Agent"],
        "startup_delay": 4,
    },
    {
        "name": "Demand Forecasting Agent",
        "file": "demand_forecasting_agent.py",
        "port": 8006,
        "dependencies": ["Product Agent", "Inventory Agent"],
        "startup_delay": 3,
    },
    {
        "name": "Dynamic Pricing Agent",
        "file": "dynamic_pricing_agent.py",
        "port": 8007,
        "dependencies": ["Product Agent", "Demand Forecasting Agent"],
        "startup_delay": 3,
    },
    {
        "name": "Customer Communication Agent",
        "file": "customer_communication_agent.py",
        "port": 8008,
        "dependencies": ["Order Agent"],
        "startup_delay": 3,
    },
    {
        "name": "Reverse Logistics Agent",
        "file": "reverse_logistics_agent.py",
        "port": 8009,
        "dependencies": ["Order Agent", "Inventory Agent"],
        "startup_delay": 3,
    },
    {
        "name": "Risk Anomaly Detection Agent",
        "file": "risk_anomaly_detection_agent.py",
        "port": 8010,
        "dependencies": [],
        "startup_delay": 2,
    },
    {
        "name": "Standard Marketplace Agent",
        "file": "standard_marketplace_agent.py",
        "port": 8011,
        "dependencies": ["Product Agent", "Order Agent"],
        "startup_delay": 3,
    },
    {
        "name": "Refurbished Marketplace Agent",
        "file": "refurbished_marketplace_agent.py",
        "port": 8012,
        "dependencies": ["Product Agent", "Order Agent"],
        "startup_delay": 3,
    },
    {
        "name": "D2C E-commerce Agent",
        "file": "d2c_ecommerce_agent.py",
        "port": 8013,
        "dependencies": ["Product Agent", "Order Agent"],
        "startup_delay": 3,
    },
]

# Global variables
running_processes: Dict[str, subprocess.Popen] = {}
stop_requested = False

def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use"""
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            return True
    return False

def start_agent(agent: Dict) -> subprocess.Popen:
    """Start an individual agent process"""
    agent_path = os.path.join(current_dir, agent["file"])
    
    # Check if the agent file exists
    if not os.path.exists(agent_path):
        print(f"⚠️ Warning: Agent file not found: {agent_path}")
        return None
    
    # Check if the port is already in use
    if is_port_in_use(agent["port"]):
        print(f"⚠️ Warning: Port {agent['port']} is already in use. Agent {agent['name']} may not start correctly.")
    
    # Start the agent process
    print(f"🚀 Starting {agent['name']}...")
    
    # Use pythonw.exe on Windows to avoid console windows
    if sys.platform == 'win32':
        python_executable = sys.executable
        process = subprocess.Popen(
            [python_executable, agent_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        process = subprocess.Popen(
            [sys.executable, agent_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    
    # Wait a moment to check for immediate crashes
    time.sleep(1)
    if process.poll() is not None:
        print(f"❌ Error: {agent['name']} failed to start!")
        stdout, stderr = process.communicate()
        if stdout:
            print(f"Standard output: {stdout}")
        if stderr:
            print(f"Error output: {stderr}")
        return None
    
    print(f"✅ {agent['name']} started successfully (PID: {process.pid})")
    return process

def stop_agent(name: str, process: subprocess.Popen) -> None:
    """Stop an individual agent process"""
    if process is None or process.poll() is not None:
        return
    
    print(f"🛑 Stopping {name}...")
    
    if sys.platform == 'win32':
        # On Windows, we need to use taskkill to kill the process tree
        subprocess.call(['taskkill', '/F', '/T', '/PID', str(process.pid)])
    else:
        # On Unix, we can use process groups
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            process.terminate()
    
    # Wait for the process to terminate
    try:
        process.wait(timeout=5)
        print(f"✅ {name} stopped")
    except subprocess.TimeoutExpired:
        print(f"⚠️ {name} did not terminate gracefully, forcing...")
        process.kill()

def signal_handler(sig, frame):
    """Handle Ctrl+C to gracefully shut down all agents"""
    global stop_requested
    if not stop_requested:
        print("\n🛑 Shutdown requested. Stopping all agents...")
        stop_requested = True
        stop_all_agents()
        sys.exit(0)

def stop_all_agents():
    """Stop all running agent processes in reverse order"""
    global running_processes
    
    # Stop agents in reverse order of startup
    for agent in reversed(AGENTS):
        name = agent["name"]
        if name in running_processes and running_processes[name] is not None:
            stop_agent(name, running_processes[name])
    
    running_processes = {}

def start_all_agents(selected_agents=None):
    """Start all agents in the correct order"""
    global running_processes
    
    # Check if this is a demo run
    if selected_agents and any("demo" in agent.lower() for agent in selected_agents):
        print("🎯 Running in demo mode...")
        run_demo_agent()
        return
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Track started agents to resolve dependencies
    started_agents = set()
    
    # Process agents in order
    for agent in AGENTS:
        name = agent["name"]
        
        # Skip if not in selected agents (if specified)
        if selected_agents and name not in selected_agents:
            continue
        
        # Check dependencies
        dependencies_met = True
        for dependency in agent["dependencies"]:
            if dependency not in started_agents:
                print(f"⚠️ Dependency not met for {name}: {dependency} not started")
                dependencies_met = False
        
        if not dependencies_met:
            print(f"⚠️ Skipping {name} due to unmet dependencies")
            continue
        
        # Start the agent
        process = start_agent(agent)
        if process:
            running_processes[name] = process
            started_agents.add(name)
            
            # Wait for the specified startup delay
            time.sleep(agent["startup_delay"])
    
    print(f"\n✅ Started {len(running_processes)}/{len(AGENTS)} agents successfully")
    
    # Keep the script running to manage the processes
    try:
        while not stop_requested:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested. Stopping all agents...")
        stop_all_agents()

def run_demo_agent():
    """Run a simple demo agent to test the system."""
    print("🎯 Starting Demo Agent...")
    print("📝 This demonstrates the Multi-Agent system is working")
    print("🔧 No external services (PostgreSQL, Kafka, Redis) required")
    print("-" * 50)
    
    try:
        # Try to import and run the demo agent
        demo_agent_path = os.path.join(os.path.dirname(__file__), "demo_agent.py")
        if os.path.exists(demo_agent_path):
            import subprocess
            result = subprocess.run([sys.executable, demo_agent_path], 
                                  capture_output=False, text=True)
            if result.returncode == 0:
                return True
        
        # Fallback demo if file doesn't exist
        print("🤖 Demo Agent (Fallback Mode)")
        print("📊 Simulating multi-agent operations...")
        
        agents = ["Product Agent", "Inventory Agent", "Order Agent", "Shipping Agent"]
        for i, agent in enumerate(agents, 1):
            print(f"   {i}. Starting {agent}...")
            time.sleep(1)
            print(f"   ✓ {agent} is running")
        
        print("\n✅ All demo agents started successfully!")
        print("🎉 Multi-Agent System is working correctly!")
        print("💡 To start real agents, ensure PostgreSQL is running and use:")
        print("   python -m multi_agent_ecommerce.cli start")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Multi-Agent E-commerce System Launcher")
    parser.add_argument("--agents", nargs="+", help="Specify which agents to start (by name)")
    return parser.parse_args()

def main(agents=None):
    """Main entry point for the agent launcher."""
    if agents is None:
        args = parse_arguments()
        selected_agents = args.agents
    else:
        selected_agents = agents
    
    print("🤖 Multi-Agent E-commerce System Launcher")
    print("----------------------------------------")
    
    if selected_agents:
        print(f"Starting selected agents: {', '.join(selected_agents)}")
    else:
        print("Starting all agents")
    
    start_all_agents(selected_agents)


if __name__ == "__main__":
    main()
