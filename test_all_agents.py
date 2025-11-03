#!/usr/bin/env python3.11
"""
Comprehensive Agent Testing Script
Tests all agents for import errors, startup issues, and basic functionality
"""

import os
import sys
import subprocess
import importlib.util
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# List of all agent files
AGENTS = [
    "after_sales_agent_production.py",
    "ai_monitoring_agent_self_healing.py",
    "backoffice_agent_production.py",
    "carrier_selection_agent.py",
    "customer_agent_enhanced.py",
    "customer_communication_agent.py",
    "d2c_ecommerce_agent.py",
    "document_generation_agent.py",
    "dynamic_pricing_agent.py",
    "fraud_detection_agent.py",
    "infrastructure_agents.py",
    "inventory_agent.py",
    "knowledge_management_agent.py",
    "marketplace_connector_agent.py",
    "monitoring_agent.py",
    "order_agent_production_v2.py",
    "payment_agent_enhanced.py",
    "product_agent_production.py",
    "promotion_agent.py",
    "quality_control_agent_production.py",
    "recommendation_agent.py",
    "returns_agent.py",
    "risk_anomaly_detection_agent.py",
    "support_agent.py",
    "transport_management_agent_enhanced.py",
    "warehouse_agent.py",
]

def test_import(agent_file):
    """Test if an agent can be imported without errors"""
    agent_path = project_root / "agents" / agent_file
    
    try:
        # Try to import the module
        result = subprocess.run(
            [sys.executable, "-c", f"import sys; sys.path.insert(0, '{project_root}'); import agents.{agent_file[:-3]}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return {"status": "✅ OK", "error": None}
        else:
            # Extract the actual error
            error_lines = result.stderr.strip().split('\n')
            # Get the last line which usually has the actual error
            error = error_lines[-1] if error_lines else result.stderr
            return {"status": "❌ FAIL", "error": error}
    except subprocess.TimeoutExpired:
        return {"status": "⏱️ TIMEOUT", "error": "Import took too long (>5s)"}
    except Exception as e:
        return {"status": "❌ ERROR", "error": str(e)}

def main():
    print("=" * 80)
    print("COMPREHENSIVE AGENT IMPORT TEST")
    print("=" * 80)
    print(f"Testing {len(AGENTS)} agents...\n")
    
    results = {}
    success_count = 0
    fail_count = 0
    timeout_count = 0
    
    for i, agent in enumerate(AGENTS, 1):
        agent_name = agent.replace(".py", "").replace("_", " ").title()
        print(f"[{i:2d}/{len(AGENTS)}] Testing {agent_name:45} ... ", end="", flush=True)
        
        result = test_import(agent)
        results[agent] = result
        
        print(result["status"])
        if result["error"]:
            print(f"       Error: {result['error'][:100]}")
        
        if result["status"] == "✅ OK":
            success_count += 1
        elif result["status"] == "⏱️ TIMEOUT":
            timeout_count += 1
        else:
            fail_count += 1
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Success: {success_count}/{len(AGENTS)} ({success_count/len(AGENTS)*100:.1f}%)")
    print(f"❌ Failed:  {fail_count}/{len(AGENTS)}")
    print(f"⏱️ Timeout: {timeout_count}/{len(AGENTS)}")
    print("=" * 80)
    
    # Save detailed results
    with open("agent_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n📄 Detailed results saved to: agent_test_results.json")
    
    # List failed agents
    if fail_count > 0 or timeout_count > 0:
        print("\n❌ FAILED AGENTS:")
        for agent, result in results.items():
            if result["status"] != "✅ OK":
                print(f"  - {agent}: {result['error'][:80] if result['error'] else 'Unknown error'}")
    
    return success_count == len(AGENTS)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

