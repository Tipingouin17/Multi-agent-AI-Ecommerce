#!/usr/bin/env python3
"""
Add Health Check Endpoints to All Production Agents

This script automatically adds health check endpoints to all production agents
that don't already have them.

Changes made:
1. Add import for health_checks module
2. Add setup_health_endpoints() call in FastAPI app initialization
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
    backup_path = file_path.with_suffix(file_path.suffix + '.health_backup')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return backup_path


def add_health_check_import(content: str) -> Tuple[str, bool]:
    """
    Add health_checks import if not present.
    
    Returns:
        (modified_content, was_modified)
    """
    # Check if already imported
    if 'from shared.health_checks import' in content or 'import shared.health_checks' in content:
        return content, False
    
    # Find the best place to add the import
    # Look for other shared imports
    shared_import_pattern = r'(from shared\.\w+ import [^\n]+\n)'
    matches = list(re.finditer(shared_import_pattern, content))
    
    if matches:
        # Add after the last shared import
        last_match = matches[-1]
        insert_pos = last_match.end()
        new_import = 'from shared.health_checks import setup_health_endpoints\n'
        content = content[:insert_pos] + new_import + content[insert_pos:]
        return content, True
    
    # If no shared imports, look for FastAPI import
    fastapi_pattern = r'(from fastapi import [^\n]+\n)'
    match = re.search(fastapi_pattern, content)
    if match:
        insert_pos = match.end()
        new_import = '\n# Health checks\nfrom shared.health_checks import setup_health_endpoints\n'
        content = content[:insert_pos] + new_import + content[insert_pos:]
        return content, True
    
    # Last resort: add after all imports
    import_block_end = 0
    for line_num, line in enumerate(content.split('\n')):
        if line.startswith('import ') or line.startswith('from '):
            import_block_end = content.find(line) + len(line) + 1
    
    if import_block_end > 0:
        new_import = '\n# Health checks\nfrom shared.health_checks import setup_health_endpoints\n'
        content = content[:import_block_end] + new_import + content[import_block_end:]
        return content, True
    
    return content, False


def add_health_check_setup(content: str, agent_variable_name: str = 'agent') -> Tuple[str, bool]:
    """
    Add setup_health_endpoints() call after FastAPI app creation.
    
    Returns:
        (modified_content, was_modified)
    """
    # Check if already added
    if 'setup_health_endpoints' in content:
        return content, False
    
    # Pattern 1: Look for "app = FastAPI(...)" followed by some config
    # We want to add our call after the FastAPI app is fully configured
    
    # Find FastAPI app creation
    app_creation_pattern = r'(app = FastAPI\([^)]*\))'
    match = re.search(app_creation_pattern, content)
    
    if not match:
        return content, False
    
    # Find the end of the app configuration block
    # Look for the next blank line or function definition after app creation
    start_pos = match.end()
    lines = content[start_pos:].split('\n')
    
    insert_line_offset = 0
    for i, line in enumerate(lines):
        # Skip empty lines and comments right after app creation
        if line.strip() == '' or line.strip().startswith('#'):
            continue
        # Skip app.add_middleware, app.include_router, etc.
        if line.strip().startswith('app.'):
            insert_line_offset = i + 1
            continue
        # Found a non-app line, insert before it
        break
    
    # Calculate insertion position
    insert_pos = start_pos + sum(len(line) + 1 for line in lines[:insert_line_offset])
    
    # Create the health check setup code
    health_check_code = f'''
# Setup health check endpoints
setup_health_endpoints(app, {agent_variable_name})
'''
    
    content = content[:insert_pos] + health_check_code + content[insert_pos:]
    return content, True


def find_agent_variable_name(content: str) -> str:
    """
    Find the variable name used for the agent instance.
    
    Common patterns:
    - agent = OrderAgent(...)
    - order_agent = OrderAgent(...)
    """
    # Pattern: variable_name = SomeAgent(...)
    pattern = r'(\w+)\s*=\s*\w+Agent\('
    match = re.search(pattern, content)
    if match:
        return match.group(1)
    
    # Default fallback
    return 'agent'


def process_agent_file(file_path: Path, dry_run: bool = False) -> bool:
    """
    Add health checks to a single agent file.
    
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
        
        # Check if it's a FastAPI agent
        if 'FastAPI' not in content:
            print_status(f"  Not a FastAPI agent, skipping", "WARNING")
            return True
        
        # Check if already has health checks
        if 'setup_health_endpoints' in content:
            print_status(f"  Already has health checks, skipping", "WARNING")
            return True
        
        total_changes = 0
        
        # Add import
        content, modified = add_health_check_import(content)
        if modified:
            total_changes += 1
            print_status(f"  Added health_checks import", "SUCCESS")
        
        # Find agent variable name
        agent_var = find_agent_variable_name(content)
        print_status(f"  Detected agent variable: {agent_var}", "INFO")
        
        # Add setup call
        content, modified = add_health_check_setup(content, agent_var)
        if modified:
            total_changes += 1
            print_status(f"  Added setup_health_endpoints() call", "SUCCESS")
        
        if total_changes == 0:
            print_status(f"  No changes needed", "INFO")
            return True
        
        if not dry_run:
            # Create backup
            backup_path = backup_file(file_path)
            print_status(f"  Created backup: {backup_path.name}", "INFO")
            
            # Write modified content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print_status(f"  Added health checks ({total_changes} changes)", "SUCCESS")
        else:
            print_status(f"  Dry run: Would make {total_changes} changes", "INFO")
        
        return True
        
    except Exception as e:
        print_status(f"  Error: {e}", "ERROR")
        return False


def find_production_agents(agents_dir: Path) -> List[Path]:
    """Find all production agent files."""
    # Production agents
    production_agents = [
        "order_agent_production.py",
        "product_agent_production.py",
        "warehouse_agent_production.py",
        "transport_agent_production.py",
        "marketplace_connector_agent_production.py",
    ]
    
    # Enhanced agents
    enhanced_agents = [
        "payment_agent_enhanced.py",
        "customer_agent_enhanced.py",
    ]
    
    # Other critical agents
    other_agents = [
        "inventory_agent.py",
        "after_sales_agent.py",
        "quality_control_agent.py",
        "backoffice_agent.py",
        "fraud_detection_agent.py",
        "document_generation_agent.py",
        "knowledge_management_agent.py",
        "risk_anomaly_detection_agent.py",
    ]
    
    all_agents = production_agents + enhanced_agents + other_agents
    
    agent_files = []
    for agent_name in all_agents:
        agent_path = agents_dir / agent_name
        if agent_path.exists():
            agent_files.append(agent_path)
    
    return sorted(agent_files)


def main():
    """Main script."""
    print_status("=" * 60, "INFO")
    print_status("Add Health Checks to Production Agents", "INFO")
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
    
    for agent_file in agent_files:
        if process_agent_file(agent_file, dry_run):
            success_count += 1
        else:
            failure_count += 1
        print()
    
    # Summary
    print_status("=" * 60, "INFO")
    print_status("Summary", "INFO")
    print_status("=" * 60, "INFO")
    print_status(f"Total files: {len(agent_files)}", "INFO")
    print_status(f"Successful: {success_count}", "SUCCESS")
    if failure_count > 0:
        print_status(f"Failed: {failure_count}", "ERROR")
    print()
    
    if not dry_run:
        print_status("Health checks added! Backup files created with .health_backup extension", "SUCCESS")
        print_status("Next steps:", "INFO")
        print("  1. Review the changes")
        print("  2. Test the agents")
        print("  3. Delete backup files if everything works")
        print("  4. Commit changes to Git")
    else:
        print_status("Dry run complete. Run without --dry-run to apply changes.", "INFO")
    
    return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

