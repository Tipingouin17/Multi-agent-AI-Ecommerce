"""
Script to identify which agents are actually used in production.

This script analyzes the agent monitor and startup scripts to determine
which agents are actually launched in production.
"""

import re
from pathlib import Path

def find_production_agents():
    """Find agents that are actually used in production"""
    
    # Check the agent monitor script
    monitor_script = Path("scripts/monitor_agents.ps1")
    if monitor_script.exists():
        content = monitor_script.read_text()
        print("=== Agents in monitor_agents.ps1 ===")
        # Look for agent definitions
        agent_pattern = r'\$agents\s*=\s*@\((.*?)\)'
        match = re.search(agent_pattern, content, re.DOTALL)
        if match:
            agents_text = match.group(1)
            # Extract agent info
            agent_entries = re.findall(r'@\{[^}]+\}', agents_text)
            for entry in agent_entries:
                name_match = re.search(r'name\s*=\s*[\'"]([^\'"]+)[\'"]', entry)
                file_match = re.search(r'file\s*=\s*[\'"]([^\'"]+)[\'"]', entry)
                port_match = re.search(r'port\s*=\s*(\d+)', entry)
                
                if name_match and file_match:
                    print(f"  - {name_match.group(1)}: {file_match.group(1)} (port {port_match.group(1) if port_match else 'N/A'})")
    
    # Check setup-and-launch script
    setup_script = Path("setup-and-launch.ps1")
    if setup_script.exists():
        content = setup_script.read_text()
        print("\n=== Agents in setup-and-launch.ps1 ===")
        # Look for agent file references
        agent_files = re.findall(r'agents[/\\]([a-z_]+_agent[a-z_]*\.py)', content, re.IGNORECASE)
        for agent_file in set(agent_files):
            print(f"  - {agent_file}")

if __name__ == "__main__":
    find_production_agents()

