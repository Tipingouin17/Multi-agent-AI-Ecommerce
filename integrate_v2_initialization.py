#!/usr/bin/env python3
"""
Integrate BaseAgentV2 Initialization into All Agents

This script updates agent initialize() methods to call super().initialize()
so they can leverage BaseAgentV2's features:
- Database retry logic
- Kafka retry logic
- Circuit breakers
- Graceful degradation
- Error recovery

Usage:
    python3 integrate_v2_initialization.py --dry-run
    python3 integrate_v2_initialization.py
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# ANSI color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_status(message: str, status: str = "INFO"):
    """Print colored status message."""
    colors = {
        "INFO": BLUE,
        "SUCCESS": GREEN,
        "WARNING": YELLOW,
        "ERROR": RED
    }
    color = colors.get(status, RESET)
    print(f"{color}[{status}]{RESET} {message}")


def backup_file(file_path: Path) -> Path:
    """Create backup of original file."""
    backup_path = file_path.with_suffix(file_path.suffix + '.v2init_backup')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return backup_path


def find_initialize_method(content: str) -> Tuple[bool, int, int]:
    """
    Find the initialize() method in the agent.
    
    Returns:
        (found, start_pos, end_pos)
    """
    # Pattern to find async def initialize(self):
    pattern = r'async def initialize\(self\):'
    match = re.search(pattern, content)
    
    if not match:
        return False, -1, -1
    
    start_pos = match.start()
    
    # Find the end of the method (next method definition or class end)
    # Look for next "def " or "async def " at the same indentation level
    lines = content[start_pos:].split('\n')
    method_indent = len(lines[0]) - len(lines[0].lstrip())
    
    end_line = 1  # Start from line after the def
    for i, line in enumerate(lines[1:], 1):
        # Skip empty lines and comments
        if not line.strip() or line.strip().startswith('#'):
            continue
        
        # Check indentation
        line_indent = len(line) - len(line.lstrip())
        
        # If we find a line at same or less indentation, we've reached the end
        if line.strip() and line_indent <= method_indent:
            end_line = i
            break
    else:
        # Method goes to end of file
        end_line = len(lines)
    
    end_pos = start_pos + sum(len(line) + 1 for line in lines[:end_line])
    
    return True, start_pos, end_pos


def has_super_initialize_call(content: str, start_pos: int, end_pos: int) -> bool:
    """Check if initialize method already calls super().initialize()."""
    method_content = content[start_pos:end_pos]
    
    # Look for super().initialize() or await super().initialize()
    patterns = [
        r'await\s+super\(\)\.initialize\(',
        r'super\(\)\.initialize\(',
    ]
    
    for pattern in patterns:
        if re.search(pattern, method_content):
            return True
    
    return False


def add_super_initialize_call(content: str, start_pos: int, end_pos: int) -> Tuple[str, bool]:
    """
    Add await super().initialize() call at the start of initialize method.
    
    Returns:
        (modified_content, was_modified)
    """
    method_content = content[start_pos:end_pos]
    lines = method_content.split('\n')
    
    # Find the line after "async def initialize(self):"
    def_line_idx = 0
    for i, line in enumerate(lines):
        if 'async def initialize' in line:
            def_line_idx = i
            break
    
    # Determine indentation (should be method body indent)
    # Look at the first non-empty, non-comment line after the def
    body_indent = None
    first_body_line_idx = def_line_idx + 1
    
    for i in range(def_line_idx + 1, len(lines)):
        line = lines[i]
        if line.strip() and not line.strip().startswith('#'):
            body_indent = len(line) - len(line.lstrip())
            first_body_line_idx = i
            break
    
    if body_indent is None:
        # Empty method, use default indent (8 spaces for method body)
        body_indent = 8
        first_body_line_idx = def_line_idx + 1
    
    # Create the super() call with proper indentation
    indent_str = ' ' * body_indent
    super_call_lines = [
        f"{indent_str}# Initialize BaseAgentV2 features (retry, circuit breaker, degradation)",
        f"{indent_str}await super().initialize()",
        f"{indent_str}",
    ]
    
    # Insert after the def line
    new_lines = (
        lines[:first_body_line_idx] +
        super_call_lines +
        lines[first_body_line_idx:]
    )
    
    new_method_content = '\n'.join(new_lines)
    new_content = content[:start_pos] + new_method_content + content[end_pos:]
    
    return new_content, True


def process_agent_file(file_path: Path, dry_run: bool = False) -> bool:
    """
    Integrate BaseAgentV2 initialization into an agent file.
    
    Args:
        file_path: Path to the agent file
        dry_run: If True, don't write changes
        
    Returns:
        True if successful, False otherwise
    """
    print_status(f"Processing {file_path.name}...", "INFO")
    
    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if it inherits from BaseAgentV2
        if 'BaseAgentV2' not in content:
            print_status(f"  Not a BaseAgentV2 agent, skipping", "WARNING")
            return True
        
        # Find initialize method
        found, start_pos, end_pos = find_initialize_method(content)
        
        if not found:
            print_status(f"  No initialize() method found, skipping", "WARNING")
            return True
        
        # Check if already has super() call
        if has_super_initialize_call(content, start_pos, end_pos):
            print_status(f"  Already calls super().initialize(), skipping", "WARNING")
            return True
        
        # Add super() call
        content, modified = add_super_initialize_call(content, start_pos, end_pos)
        
        if not modified:
            print_status(f"  No changes needed", "INFO")
            return True
        
        if not dry_run:
            # Create backup
            backup_path = backup_file(file_path)
            print_status(f"  Created backup: {backup_path.name}", "INFO")
            
            # Write modified content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print_status(f"  Added super().initialize() call", "SUCCESS")
        else:
            print_status(f"  Dry run: Would add super().initialize() call", "INFO")
        
        return True
        
    except Exception as e:
        print_status(f"  Error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False


def find_production_agents(agents_dir: Path) -> List[Path]:
    """Find all production agent files."""
    production_agents = [
        "order_agent_production.py",
        "product_agent_production.py",
        "warehouse_agent_production.py",
        "transport_agent_production.py",
        "marketplace_connector_agent_production.py",
        "payment_agent_enhanced.py",
        "customer_agent_enhanced.py",
        "inventory_agent.py",
        "after_sales_agent.py",
        "quality_control_agent.py",
        "backoffice_agent.py",
        "fraud_detection_agent.py",
        "document_generation_agent.py",
        "knowledge_management_agent.py",
        "risk_anomaly_detection_agent.py",
    ]
    
    agent_files = []
    for agent_name in production_agents:
        agent_path = agents_dir / agent_name
        if agent_path.exists():
            agent_files.append(agent_path)
    
    return sorted(agent_files)


def main():
    """Main script."""
    print_status("=" * 60, "INFO")
    print_status("Integrate BaseAgentV2 Initialization", "INFO")
    print_status("=" * 60, "INFO")
    print()
    
    # Parse arguments
    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print_status("Running in DRY RUN mode (no files will be modified)", "WARNING")
        print()
    
    # Find project root
    script_dir = Path(__file__).parent
    agents_dir = script_dir / "agents"
    
    if not agents_dir.exists():
        print_status(f"Agents directory not found: {agents_dir}", "ERROR")
        return 1
    
    # Find production agents
    agent_files = find_production_agents(agents_dir)
    
    if not agent_files:
        print_status("No production agent files found", "WARNING")
        return 0
    
    print_status(f"Found {len(agent_files)} production agent(s) to process:", "INFO")
    for f in agent_files:
        print(f"  - {f.name}")
    print()
    
    # Process each agent
    success_count = 0
    failure_count = 0
    modified_count = 0
    
    for agent_file in agent_files:
        if process_agent_file(agent_file, dry_run):
            success_count += 1
            # Check if it was actually modified (not skipped)
            with open(agent_file, 'r') as f:
                if 'await super().initialize()' in f.read():
                    modified_count += 1
        else:
            failure_count += 1
        print()
    
    # Summary
    print_status("=" * 60, "INFO")
    print_status("Summary", "INFO")
    print_status("=" * 60, "INFO")
    print_status(f"Total files: {len(agent_files)}", "INFO")
    print_status(f"Successful: {success_count}", "SUCCESS")
    if not dry_run:
        print_status(f"Modified: {modified_count}", "SUCCESS")
    if failure_count > 0:
        print_status(f"Failed: {failure_count}", "ERROR")
    print()
    
    if not dry_run and modified_count > 0:
        print_status("BaseAgentV2 initialization integrated!", "SUCCESS")
        print_status("Backup files created with .v2init_backup extension", "SUCCESS")
        print_status("Next steps:", "INFO")
        print("  1. Review the changes")
        print("  2. Test the agents")
        print("  3. Run: python3 add_health_checks.py")
        print("  4. Run: python3 test_agents_v2.py")
        print("  5. Commit changes to Git")
    elif dry_run:
        print_status("Dry run complete. Run without --dry-run to apply changes.", "INFO")
    else:
        print_status("No agents needed modification.", "INFO")
    
    return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

