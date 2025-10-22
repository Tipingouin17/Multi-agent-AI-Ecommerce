#!/usr/bin/env python3
"""
Automatic Agent Migration Script

Migrates all agents from BaseAgent to BaseAgentV2 with minimal manual intervention.

Changes made:
1. Update import from base_agent to base_agent_v2
2. Update class inheritance from BaseAgent to BaseAgentV2
3. Remove manual database initialization (now handled by BaseAgentV2)
4. Remove manual Kafka initialization (now handled by BaseAgentV2)
5. Update initialize() method to call super().initialize()
6. Update cleanup() method to call super().cleanup()
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
    backup_path = file_path.with_suffix(file_path.suffix + '.backup')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return backup_path


def migrate_imports(content: str) -> Tuple[str, int]:
    """Migrate imports from base_agent to base_agent_v2."""
    changes = 0
    
    # Pattern 1: from shared.base_agent import BaseAgent
    pattern1 = r'from shared\.base_agent import BaseAgent'
    if re.search(pattern1, content):
        content = re.sub(pattern1, 'from shared.base_agent_v2 import BaseAgentV2', content)
        changes += 1
    
    # Pattern 2: from shared.base_agent import BaseAgent, MessageType, ...
    pattern2 = r'from shared\.base_agent import ([^;\n]+)'
    matches = re.findall(pattern2, content)
    for match in matches:
        if 'BaseAgent' in match:
            new_import = match.replace('BaseAgent', 'BaseAgentV2')
            content = content.replace(f'from shared.base_agent import {match}', 
                                     f'from shared.base_agent_v2 import {new_import}')
            changes += 1
    
    return content, changes


def migrate_class_inheritance(content: str) -> Tuple[str, int]:
    """Migrate class inheritance from BaseAgent to BaseAgentV2."""
    changes = 0
    
    # Pattern: class SomeAgent(BaseAgent):
    pattern = r'class\s+(\w+Agent)\(BaseAgent\):'
    matches = re.findall(pattern, content)
    for match in matches:
        content = content.replace(f'class {match}(BaseAgent):', 
                                 f'class {match}(BaseAgentV2):')
        changes += 1
    
    return content, changes


def migrate_initialize_method(content: str) -> Tuple[str, int]:
    """
    Migrate initialize() method to use BaseAgentV2 pattern.
    
    BaseAgentV2 handles database and Kafka initialization automatically,
    so we remove manual initialization code and just call super().initialize().
    """
    changes = 0
    
    # Find initialize method
    init_pattern = r'async def initialize\(self\):(.*?)(?=\n    async def |\n    def |\nclass |\Z)'
    matches = list(re.finditer(init_pattern, content, re.DOTALL))
    
    for match in matches:
        old_method = match.group(0)
        method_body = match.group(1)
        
        # Check if it already calls super().initialize()
        if 'super().initialize()' in method_body or 'await super().initialize()' in method_body:
            # Already migrated, skip
            continue
        
        # Check if it calls await self.initialize_database()
        if 'await self.initialize_database()' in method_body:
            # Remove the manual database initialization
            method_body = re.sub(r'\s*await self\.initialize_database\(\)\s*\n', '', method_body)
            changes += 1
        
        # Add super().initialize() at the beginning
        new_method_body = '\n        await super().initialize()\n' + method_body
        
        new_method = f'async def initialize(self):{new_method_body}'
        content = content.replace(old_method, new_method)
        changes += 1
    
    return content, changes


def migrate_cleanup_method(content: str) -> Tuple[str, int]:
    """
    Migrate cleanup() method to use BaseAgentV2 pattern.
    """
    changes = 0
    
    # Find cleanup method
    cleanup_pattern = r'async def cleanup\(self\):(.*?)(?=\n    async def |\n    def |\nclass |\Z)'
    matches = list(re.finditer(cleanup_pattern, content, re.DOTALL))
    
    for match in matches:
        old_method = match.group(0)
        method_body = match.group(1)
        
        # Check if it already calls super().cleanup()
        if 'super().cleanup()' in method_body or 'await super().cleanup()' in method_body:
            # Already migrated, skip
            continue
        
        # Add super().cleanup() at the end
        new_method_body = method_body.rstrip() + '\n        await super().cleanup()\n'
        
        new_method = f'async def cleanup(self):{new_method_body}'
        content = content.replace(old_method, new_method)
        changes += 1
    
    return content, changes


def migrate_agent_file(file_path: Path, dry_run: bool = False) -> bool:
    """
    Migrate a single agent file to BaseAgentV2.
    
    Args:
        file_path: Path to the agent file
        dry_run: If True, don't write changes
        
    Returns:
        True if migration successful, False otherwise
    """
    print_status(f"Migrating {file_path.name}...", "INFO")
    
    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already migrated
        if 'base_agent_v2' in content or 'BaseAgentV2' in content:
            print_status(f"  Already migrated to V2, skipping", "WARNING")
            return True
        
        # Check if it uses BaseAgent
        if 'BaseAgent' not in content or 'from shared.base_agent' not in content:
            print_status(f"  Doesn't use BaseAgent, skipping", "WARNING")
            return True
        
        total_changes = 0
        
        # Apply migrations
        content, changes = migrate_imports(content)
        total_changes += changes
        if changes > 0:
            print_status(f"  Updated {changes} import(s)", "SUCCESS")
        
        content, changes = migrate_class_inheritance(content)
        total_changes += changes
        if changes > 0:
            print_status(f"  Updated {changes} class inheritance(s)", "SUCCESS")
        
        content, changes = migrate_initialize_method(content)
        total_changes += changes
        if changes > 0:
            print_status(f"  Updated {changes} initialize() method(s)", "SUCCESS")
        
        content, changes = migrate_cleanup_method(content)
        total_changes += changes
        if changes > 0:
            print_status(f"  Updated {changes} cleanup() method(s)", "SUCCESS")
        
        if total_changes == 0:
            print_status(f"  No changes needed", "INFO")
            return True
        
        if not dry_run:
            # Create backup
            backup_path = backup_file(file_path)
            print_status(f"  Created backup: {backup_path.name}", "INFO")
            
            # Write migrated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print_status(f"  Migration complete ({total_changes} changes)", "SUCCESS")
        else:
            print_status(f"  Dry run: Would make {total_changes} changes", "INFO")
        
        return True
        
    except Exception as e:
        print_status(f"  Error: {e}", "ERROR")
        return False


def find_agent_files(agents_dir: Path) -> List[Path]:
    """Find all agent files in the agents directory."""
    agent_files = []
    
    # Production agents
    production_agents = list(agents_dir.glob("*_agent_production.py"))
    agent_files.extend(production_agents)
    
    # Regular agents (excluding base_agent.py and test files)
    regular_agents = [
        f for f in agents_dir.glob("*_agent.py")
        if f.name != "base_agent.py" and not f.name.startswith("test_")
    ]
    agent_files.extend(regular_agents)
    
    return sorted(set(agent_files))


def main():
    """Main migration script."""
    print_status("=" * 60, "INFO")
    print_status("Agent Migration Script: BaseAgent -> BaseAgentV2", "INFO")
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
    
    # Find agent files
    agent_files = find_agent_files(agents_dir)
    
    if not agent_files:
        print_status("No agent files found", "WARNING")
        return 0
    
    print_status(f"Found {len(agent_files)} agent file(s) to migrate:", "INFO")
    for f in agent_files:
        print(f"  - {f.name}")
    print()
    
    # Migrate each agent
    success_count = 0
    failure_count = 0
    
    for agent_file in agent_files:
        if migrate_agent_file(agent_file, dry_run):
            success_count += 1
        else:
            failure_count += 1
        print()
    
    # Summary
    print_status("=" * 60, "INFO")
    print_status("Migration Summary", "INFO")
    print_status("=" * 60, "INFO")
    print_status(f"Total files: {len(agent_files)}", "INFO")
    print_status(f"Successful: {success_count}", "SUCCESS")
    if failure_count > 0:
        print_status(f"Failed: {failure_count}", "ERROR")
    print()
    
    if not dry_run:
        print_status("Migration complete! Backup files created with .backup extension", "SUCCESS")
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

