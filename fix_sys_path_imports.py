#!/usr/bin/env python3.11
"""
Fix sys.path import order in agents that import shared modules before setting up sys.path
"""

import re
from pathlib import Path

# Agents that need fixing
AGENTS_TO_FIX = [
    "carrier_selection_agent.py",
    "customer_communication_agent.py",
    "d2c_ecommerce_agent.py",
    "recommendation_agent.py",
    "support_agent.py",
]

def fix_agent(agent_path):
    """Fix import order in an agent file"""
    content = agent_path.read_text()
    
    # Pattern to match: shared imports before sys.path setup
    # We need to move sys.path setup before shared imports
    
    # Find all shared imports at the top
    shared_imports = []
    lines = content.split('\n')
    
    # Find where shared imports start
    shared_import_start = None
    shared_import_end = None
    sys_path_start = None
    sys_path_end = None
    
    for i, line in enumerate(lines):
        if 'from shared.' in line and shared_import_start is None:
            shared_import_start = i
        if shared_import_start is not None and shared_import_end is None:
            if not line.strip().startswith('from shared.') and not line.strip().startswith('import') and line.strip():
                shared_import_end = i
                break
        
        if 'project_root' in line and 'os.path.dirname' in line:
            if sys_path_start is None:
                sys_path_start = i - 2  # Include comments above
        
        if sys_path_start is not None and 'sys.path.insert' in line:
            sys_path_end = i + 1
            break
    
    if shared_import_start and sys_path_start and shared_import_start < sys_path_start:
        print(f"  Fixing {agent_path.name}...")
        print(f"    Shared imports at lines {shared_import_start}-{shared_import_end}")
        print(f"    sys.path setup at lines {sys_path_start}-{sys_path_end}")
        
        # Extract the sections
        before_shared = '\n'.join(lines[:shared_import_start])
        shared_section = '\n'.join(lines[shared_import_start:shared_import_end])
        between = '\n'.join(lines[shared_import_end:sys_path_start])
        sys_path_section = '\n'.join(lines[sys_path_start:sys_path_end])
        after_sys_path = '\n'.join(lines[sys_path_end:])
        
        # Reconstruct with correct order
        new_content = f"""{before_shared}
{between.strip()}

{sys_path_section}

# Now import shared modules
{shared_section}
{after_sys_path}"""
        
        # Write back
        agent_path.write_text(new_content)
        print(f"    ✅ Fixed!")
        return True
    else:
        print(f"  ⚠️  {agent_path.name}: Could not find pattern to fix")
        return False

def main():
    agents_dir = Path("agents")
    fixed_count = 0
    
    print("=" * 80)
    print("FIXING SYS.PATH IMPORT ORDER")
    print("=" * 80)
    
    for agent_file in AGENTS_TO_FIX:
        agent_path = agents_dir / agent_file
        if agent_path.exists():
            if fix_agent(agent_path):
                fixed_count += 1
        else:
            print(f"  ❌ {agent_file} not found")
    
    print("=" * 80)
    print(f"Fixed {fixed_count}/{len(AGENTS_TO_FIX)} agents")
    print("=" * 80)

if __name__ == "__main__":
    main()

