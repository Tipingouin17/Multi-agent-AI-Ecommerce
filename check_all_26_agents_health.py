#!/usr/bin/env python3.11
"""
Comprehensive health check for all 26 agents
Tests health endpoints on ports 8000-8025
"""

import requests
import json
from typing import Dict, List

# All 26 agents with their assigned ports
AGENTS = [
    ("order_agent", 8000),
    ("product_agent", 8001),
    ("inventory_agent", 8002),
    ("marketplace_agent", 8003),
    ("payment_agent", 8004),
    ("dynamic_pricing_agent", 8005),
    ("carrier_selection_agent", 8006),
    ("customer_agent", 8007),
    ("customer_communication_agent", 8008),
    ("returns_agent", 8009),
    ("fraud_detection_agent", 8010),
    ("recommendation_agent", 8011),
    ("promotion_agent", 8012),
    ("risk_anomaly_detection_agent", 8013),
    ("knowledge_management_agent", 8014),
    ("transport_agent", 8015),
    ("warehouse_agent", 8016),
    ("document_agent", 8017),
    ("support_agent", 8018),
    ("d2c_ecommerce_agent", 8019),
    ("after_sales_agent", 8020),
    ("backoffice_agent", 8021),
    ("infrastructure_agents", 8022),
    ("ai_monitoring_agent", 8023),
    ("monitoring_agent", 8024),
    ("quality_control_agent", 8025),
]

def check_health(name: str, port: int) -> Dict:
    """Check health endpoint for an agent"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=2)
        if response.status_code == 200:
            return {
                "status": "✅ HEALTHY",
                "code": 200,
                "details": response.json() if response.headers.get('content-type', '').startswith('application/json') else None
            }
        else:
            return {
                "status": "⚠️  UNHEALTHY",
                "code": response.status_code,
                "details": f"HTTP {response.status_code}"
            }
    except requests.exceptions.ConnectionError:
        return {
            "status": "❌ NOT RUNNING",
            "code": None,
            "details": "Connection refused"
        }
    except requests.exceptions.Timeout:
        return {
            "status": "⏱️  TIMEOUT",
            "code": None,
            "details": "Request timeout"
        }
    except Exception as e:
        return {
            "status": "❌ ERROR",
            "code": None,
            "details": str(e)[:50]
        }

def main():
    print("=" * 100)
    print("COMPREHENSIVE HEALTH CHECK - ALL 26 AGENTS")
    print("=" * 100)
    print()
    
    results = {}
    healthy_count = 0
    unhealthy_count = 0
    not_running_count = 0
    
    for name, port in AGENTS:
        result = check_health(name, port)
        results[name] = result
        
        status_icon = result["status"].split()[0]
        print(f"{status_icon:4} Port {port:5} | {name:35} | {result['details'] or 'OK'}")
        
        if result["status"].startswith("✅"):
            healthy_count += 1
        elif result["status"].startswith("⚠️"):
            unhealthy_count += 1
        else:
            not_running_count += 1
    
    print()
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"✅ Healthy:     {healthy_count:2}/26 ({healthy_count/26*100:.1f}%)")
    print(f"⚠️  Unhealthy:  {unhealthy_count:2}/26")
    print(f"❌ Not Running: {not_running_count:2}/26")
    print(f"📊 Total:       {healthy_count + unhealthy_count}/26 agents responding ({(healthy_count + unhealthy_count)/26*100:.1f}%)")
    print("=" * 100)
    
    # Save results
    with open("agent_health_results.json", "w") as f:
        json.dump({
            "summary": {
                "healthy": healthy_count,
                "unhealthy": unhealthy_count,
                "not_running": not_running_count,
                "total": len(AGENTS)
            },
            "agents": results
        }, f, indent=2)
    
    print()
    print("📄 Detailed results saved to: agent_health_results.json")
    
    return healthy_count == len(AGENTS)

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)

