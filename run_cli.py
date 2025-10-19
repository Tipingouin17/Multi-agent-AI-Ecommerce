#!/usr/bin/env python3
"""
Fallback CLI runner for Multi-Agent E-commerce System

This script provides a direct way to run CLI commands when the package
installation might have issues.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    # Try to import and run the CLI
    from multi_agent_ecommerce.cli import main
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Trying alternative import method...")
    
    try:
        # Alternative import method
        import importlib.util
        
        cli_path = current_dir / "multi_agent_ecommerce" / "cli.py"
        spec = importlib.util.spec_from_file_location("cli", cli_path)
        cli_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli_module)
        
        if __name__ == "__main__":
            cli_module.main()
            
    except Exception as e2:
        print(f"Alternative import also failed: {e2}")
        print("\nPlease ensure all dependencies are installed:")
        print("pip install -r requirements.txt")
        print("\nOr run the installer again: install.bat")
        sys.exit(1)
