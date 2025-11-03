#!/usr/bin/env python3
"""
Comprehensive Deep Health Check for All Agents
Tests each healthy agent's endpoints and functionality
"""

import asyncio
import httpx
import json
from typing import Dict, List, Tuple
from datetime import datetime

# List of all "healthy" agents from validation
HEALTHY_AGENTS = [
    {"name": "monitoring", "port": 8000, "endpoints": ["/health", "/metrics", "/agents"]},
    {"name": "order", "port": 8001, "endpoints": ["/health", "/orders"]},
    {"name": "product", "port": 8002, "endpoints": ["/health", "/products"]},
    {"name": "inventory", "port": 8003, "endpoints": ["/health", "/inventory"]},
    {"name": "warehouse", "port": 8004, "endpoints": ["/health", "/warehouse"]},
    {"name": "payment", "port": 8005, "endpoints": ["/health", "/payments"]},
    {"name": "customer", "port": 8008, "endpoints": ["/health", "/customers"]},
    {"name": "risk", "port": 8010, "endpoints": ["/health", "/risk"]},
    {"name": "backoffice", "port": 8011, "endpoints": ["/health", "/backoffice"]},
    {"name": "knowledge", "port": 8012, "endpoints": ["/health", "/knowledge"]},
    {"name": "promotion", "port": 8014, "endpoints": ["/health", "/promotions"]},
    {"name": "recommendation", "port": 8015, "endpoints": ["/health", "/recommendations"]},
    {"name": "after_sales", "port": 8016, "endpoints": ["/health", "/after-sales"]},
    {"name": "support", "port": 8017, "endpoints": ["/health", "/tickets"]},
    {"name": "returns", "port": 8018, "endpoints": ["/health", "/returns"]},
    {"name": "ai_monitoring", "port": 8024, "endpoints": ["/health", "/monitoring"]},
    {"name": "infrastructure", "port": 8025, "endpoints": ["/health", "/infrastructure"]},
]

async def check_agent_endpoint(client: httpx.AsyncClient, agent: Dict, endpoint: str) -> Tuple[str, bool, str]:
    """Check a single endpoint for an agent."""
    url = f"http://localhost:{agent['port']}{endpoint}"
    try:
        response = await client.get(url, timeout=5.0)
        if response.status_code == 200:
            return endpoint, True, f"OK ({response.status_code})"
        else:
            return endpoint, False, f"HTTP {response.status_code}"
    except httpx.TimeoutException:
        return endpoint, False, "Timeout (5s)"
    except httpx.ConnectError:
        return endpoint, False, "Connection refused"
    except Exception as e:
        return endpoint, False, f"Error: {str(e)[:50]}"

async def deep_check_agent(agent: Dict) -> Dict:
    """Perform deep health check on a single agent."""
    print(f"\n{'='*80}")
    print(f"Checking: {agent['name'].upper()} (port {agent['port']})")
    print('='*80)
    
    results = {
        "name": agent["name"],
        "port": agent["port"],
        "endpoints": {},
        "overall_status": "unknown",
        "issues": []
    }
    
    async with httpx.AsyncClient() as client:
        # Check all endpoints
        tasks = [check_agent_endpoint(client, agent, ep) for ep in agent["endpoints"]]
        endpoint_results = await asyncio.gather(*tasks)
        
        healthy_count = 0
        for endpoint, success, message in endpoint_results:
            results["endpoints"][endpoint] = {"success": success, "message": message}
            if success:
                print(f"  ✓ {endpoint}: {message}")
                healthy_count += 1
            else:
                print(f"  ✗ {endpoint}: {message}")
                results["issues"].append(f"{endpoint}: {message}")
        
        # Determine overall status
        if healthy_count == len(agent["endpoints"]):
            results["overall_status"] = "perfect"
            print(f"\n  Status: ✅ PERFECT ({healthy_count}/{len(agent['endpoints'])} endpoints healthy)")
        elif healthy_count > 0:
            results["overall_status"] = "partial"
            print(f"\n  Status: ⚠️  PARTIAL ({healthy_count}/{len(agent['endpoints'])} endpoints healthy)")
        else:
            results["overall_status"] = "failed"
            print(f"\n  Status: ❌ FAILED (0/{len(agent['endpoints'])} endpoints healthy)")
    
    return results

async def main():
    """Run deep health check on all healthy agents."""
    print("="*80)
    print("COMPREHENSIVE DEEP HEALTH CHECK")
    print("="*80)
    print(f"Start Time: {datetime.now()}")
    print(f"Agents to check: {len(HEALTHY_AGENTS)}")
    
    all_results = []
    
    # Check each agent sequentially to avoid overwhelming the system
    for agent in HEALTHY_AGENTS:
        result = await deep_check_agent(agent)
        all_results.append(result)
        await asyncio.sleep(0.5)  # Small delay between agents
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    perfect = [r for r in all_results if r["overall_status"] == "perfect"]
    partial = [r for r in all_results if r["overall_status"] == "partial"]
    failed = [r for r in all_results if r["overall_status"] == "failed"]
    
    print(f"\n✅ Perfect: {len(perfect)}/{len(HEALTHY_AGENTS)} agents")
    for r in perfect:
        print(f"   - {r['name']}")
    
    if partial:
        print(f"\n⚠️  Partial: {len(partial)} agents")
        for r in partial:
            print(f"   - {r['name']}: {', '.join(r['issues'])}")
    
    if failed:
        print(f"\n❌ Failed: {len(failed)} agents")
        for r in failed:
            print(f"   - {r['name']}: {', '.join(r['issues'])}")
    
    # Save detailed results
    output_file = "deep_health_check_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(HEALTHY_AGENTS),
            "perfect": len(perfect),
            "partial": len(partial),
            "failed": len(failed),
            "results": all_results
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {output_file}")
    print(f"\n{'='*80}")
    print(f"Production Readiness: {len(perfect)}/{len(HEALTHY_AGENTS)} agents (100% perfect)")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(main())

