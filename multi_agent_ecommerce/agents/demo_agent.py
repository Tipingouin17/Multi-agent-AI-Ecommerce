#!/usr/bin/env python3
"""
Demo Agent for Multi-Agent E-commerce System

This is a simple demo agent that shows the system is working.
It doesn't require external services and just prints status messages.
"""

import time
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def demo_agent():
    """Simple demo agent that runs for a short time."""
    print(f"🤖 Demo Agent started at {datetime.now()}")
    print("📊 Checking system status...")
    
    # Simulate some work
    for i in range(5):
        print(f"   ✓ Processing task {i+1}/5...")
        time.sleep(1)
    
    print("✅ Demo Agent completed successfully!")
    print("🎉 Multi-Agent System is working correctly!")
    
    return True

if __name__ == "__main__":
    try:
        demo_agent()
    except KeyboardInterrupt:
        print("\n⚠️  Demo Agent interrupted by user")
    except Exception as e:
        print(f"❌ Demo Agent error: {e}")
        sys.exit(1)
