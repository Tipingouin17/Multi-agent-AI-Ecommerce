#!/usr/bin/env python3.11
"""Extract actual port numbers from agent files"""

import re
from pathlib import Path

agents_dir = Path("agents")
agents = sorted([f for f in agents_dir.glob("*agent*.py") if f.name != "start_agents.py"])

print("=" * 100)
print(f"{'Agent File':<50} {'Port':<10} {'Method'}")
print("=" * 100)

port_map = {}
port_conflicts = {}

for agent_file in agents:
    content = agent_file.read_text()
    port = None
    method = ""
    
    # Method 1: Look for uvicorn.run with port parameter
    match = re.search(r'uvicorn\.run\([^)]*port\s*=\s*(\d+)', content)
    if match:
        port = int(match.group(1))
        method = "uvicorn.run(port=...)"
    
    # Method 2: Look for API_PORT environment variable with default
    if not port:
        match = re.search(r'API_PORT.*?int.*?[\'"]API_PORT[\'"].*?(\d+)', content)
        if match:
            port = int(match.group(1))
            method = "API_PORT env var"
    
    # Method 3: Look for port in if __name__ == "__main__" block
    if not port:
        main_block = re.search(r'if __name__.*?__main__.*?$', content, re.DOTALL | re.MULTILINE)
        if main_block:
            port_match = re.search(r'port\s*=\s*(\d+)', main_block.group(0))
            if port_match:
                port = int(port_match.group(1))
                method = "__main__ block"
    
    # Method 4: Look for any port assignment
    if not port:
        matches = re.findall(r'(?:port|PORT)\s*=\s*(?:int\(.*?(\d+).*?\)|(\d+))', content)
        if matches:
            for match in matches:
                p = match[0] or match[1]
                if p and int(p) >= 8000:  # Only consider ports >= 8000
                    port = int(p)
                    method = "port assignment"
                    break
    
    port_str = str(port) if port else "UNKNOWN"
    print(f"{agent_file.name:<50} {port_str:<10} {method}")
    
    if port:
        if port in port_conflicts:
            port_conflicts[port].append(agent_file.name)
        else:
            port_conflicts[port] = [agent_file.name]
        port_map[agent_file.name] = port

print("=" * 100)

# Show conflicts
if any(len(agents) > 1 for agents in port_conflicts.values()):
    print("\n⚠️  PORT CONFLICTS DETECTED:")
    print("=" * 100)
    for port, agent_list in sorted(port_conflicts.items()):
        if len(agent_list) > 1:
            print(f"Port {port}: {', '.join(agent_list)}")
    print("=" * 100)

# Save to JSON
import json
with open("agent_ports.json", "w") as f:
    json.dump(port_map, f, indent=2, sort_keys=True)

print("\n📄 Port mapping saved to: agent_ports.json")

