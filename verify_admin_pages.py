#!/usr/bin/env python3.11
"""
Admin Pages Integration Verification Script
Checks which admin pages have their required API endpoints available
"""

import json
import requests
from typing import Dict, List

# API Gateway base URL
BASE_URL = "http://localhost:8100"

# Define each admin page and its required endpoints
ADMIN_PAGES = {
    "Critical": [
        {
            "name": "Dashboard.jsx",
            "endpoints": [
                "/api/system/overview",
                "/api/agents",
                "/api/alerts"
            ]
        },
        {
            "name": "SystemMonitoring.jsx",
            "endpoints": [
                "/api/system/overview",
                "/metrics/performance"
            ]
        },
        {
            "name": "AgentManagement.jsx",
            "endpoints": [
                "/api/agents",
                "/api/agents/stats"
            ]
        },
        {
            "name": "AlertsManagement.jsx",
            "endpoints": [
                "/api/alerts",
                "/api/alerts/stats"
            ]
        },
        {
            "name": "PerformanceAnalytics.jsx",
            "endpoints": [
                "/api/analytics/performance",
                "/metrics/performance"
            ]
        },
        {
            "name": "OrderManagement.jsx",
            "endpoints": [
                "/api/orders",
                "/api/orders/stats"
            ]
        }
    ],
    "High Priority": [
        {
            "name": "UserManagement.jsx",
            "endpoints": [
                "/api/users"
            ]
        },
        {
            "name": "ProductConfiguration.jsx",
            "endpoints": [
                "/api/products",
                "/api/categories"
            ]
        },
        {
            "name": "SystemConfiguration.jsx",
            "endpoints": [
                "/api/system/config"
            ]
        },
        {
            "name": "MarketplaceIntegration.jsx",
            "endpoints": [
                "/api/marketplace/integrations"
            ]
        },
        {
            "name": "PaymentGatewayConfiguration.jsx",
            "endpoints": [
                "/api/payment/gateways"
            ]
        },
        {
            "name": "CarrierConfiguration.jsx",
            "endpoints": [
                "/api/carriers",
                "/api/shipping/zones"
            ]
        },
        {
            "name": "WarehouseConfiguration.jsx",
            "endpoints": [
                "/api/warehouses"
            ]
        },
        {
            "name": "ProductVariantsManagement.jsx",
            "endpoints": [
                "/api/products"
            ]
        }
    ],
    "Medium Priority": [
        {
            "name": "OrderCancellationsManagement.jsx",
            "endpoints": [
                "/api/orders"
            ]
        },
        {
            "name": "ReturnRMAConfiguration.jsx",
            "endpoints": [
                "/api/returns"
            ]
        },
        {
            "name": "ShippingZonesConfiguration.jsx",
            "endpoints": [
                "/api/shipping/zones"
            ]
        },
        {
            "name": "TaxConfiguration.jsx",
            "endpoints": [
                "/api/tax/config"
            ]
        },
        {
            "name": "NotificationTemplatesConfiguration.jsx",
            "endpoints": [
                "/api/notifications/templates"
            ]
        },
        {
            "name": "DocumentTemplateConfiguration.jsx",
            "endpoints": [
                "/api/documents/templates"
            ]
        },
        {
            "name": "WorkflowConfiguration.jsx",
            "endpoints": [
                "/api/workflows"
            ]
        }
    ],
    "Low Priority": [
        {
            "name": "AIModelConfiguration.jsx",
            "endpoints": []  # Not implemented yet
        },
        {
            "name": "BusinessRulesConfiguration.jsx",
            "endpoints": []  # Not implemented yet
        },
        {
            "name": "CarrierContractManagement.jsx",
            "endpoints": [
                "/api/carriers"
            ]
        },
        {
            "name": "ChannelConfiguration.jsx",
            "endpoints": []  # Not implemented yet
        },
        {
            "name": "WarehouseCapacityManagement.jsx",
            "endpoints": [
                "/api/warehouses"
            ]
        },
        {
            "name": "ThemeSettings.jsx",
            "endpoints": []  # UI only, no API
        },
        {
            "name": "SettingsNavigationHub.jsx",
            "endpoints": []  # Navigation only, no API
        }
    ]
}

def test_endpoint(endpoint: str) -> bool:
    """Test if an endpoint is available and returns 200"""
    try:
        url = f"{BASE_URL}{endpoint}"
        response = requests.get(url, timeout=2)
        return response.status_code == 200
    except:
        return False

def verify_pages():
    """Verify all admin pages and their endpoints"""
    
    print("=" * 80)
    print("ADMIN PAGES INTEGRATION VERIFICATION")
    print("=" * 80)
    print()
    
    total_pages = 0
    ready_pages = 0
    total_endpoints = set()
    working_endpoints = set()
    
    for priority, pages in ADMIN_PAGES.items():
        print(f"\n{'='*80}")
        print(f"{priority} Pages ({len(pages)} pages)")
        print(f"{'='*80}\n")
        
        for page in pages:
            total_pages += 1
            page_name = page["name"]
            endpoints = page["endpoints"]
            
            if not endpoints:
                print(f"✅ {page_name}")
                print(f"   └─ No API dependencies")
                ready_pages += 1
                continue
            
            # Test each endpoint
            results = []
            all_working = True
            
            for endpoint in endpoints:
                total_endpoints.add(endpoint)
                is_working = test_endpoint(endpoint)
                
                if is_working:
                    working_endpoints.add(endpoint)
                    results.append(f"   ✅ {endpoint}")
                else:
                    results.append(f"   ❌ {endpoint}")
                    all_working = False
            
            # Print page status
            if all_working:
                print(f"✅ {page_name}")
                ready_pages += 1
            else:
                print(f"⚠️  {page_name}")
            
            for result in results:
                print(result)
            print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Pages: {total_pages}")
    print(f"Ready Pages: {ready_pages} ({ready_pages/total_pages*100:.1f}%)")
    print(f"Pending Pages: {total_pages - ready_pages}")
    print()
    print(f"Unique Endpoints Required: {len(total_endpoints)}")
    print(f"Working Endpoints: {len(working_endpoints)} ({len(working_endpoints)/len(total_endpoints)*100:.1f}%)")
    print(f"Missing Endpoints: {len(total_endpoints) - len(working_endpoints)}")
    print()
    
    if total_endpoints - working_endpoints:
        print("Missing Endpoints:")
        for endpoint in sorted(total_endpoints - working_endpoints):
            print(f"  ❌ {endpoint}")
    
    print("=" * 80)
    
    # Save detailed report
    report = {
        "summary": {
            "total_pages": total_pages,
            "ready_pages": ready_pages,
            "pending_pages": total_pages - ready_pages,
            "readiness_percentage": round(ready_pages/total_pages*100, 1),
            "total_endpoints": len(total_endpoints),
            "working_endpoints": len(working_endpoints),
            "missing_endpoints": len(total_endpoints) - len(working_endpoints),
            "endpoint_coverage": round(len(working_endpoints)/len(total_endpoints)*100, 1) if total_endpoints else 100
        },
        "pages_by_priority": ADMIN_PAGES,
        "missing_endpoints": list(total_endpoints - working_endpoints)
    }
    
    with open("admin_pages_verification_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("\n📄 Detailed report saved to: admin_pages_verification_report.json")

if __name__ == "__main__":
    verify_pages()
