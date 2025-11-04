#!/usr/bin/env python3
"""
Automated testing script for all dashboard pages.
Tests each page and reports which ones load successfully vs which have errors.
"""

import requests
import json
from urllib.parse import urljoin

BASE_URL = "http://localhost:5173"

# Define all pages to test
PAGES = {
    "Admin Portal": [
        "/dashboard",
        "/agents",
        "/monitoring",
        "/alerts",
        "/analytics",
        "/configuration"
    ],
    "Merchant Portal": [
        "/dashboard",
        "/products",
        "/products/new",
        "/orders",
        "/inventory",
        "/marketplaces",
        "/analytics",
        "/product-form",
        "/order-details",
        "/bulk-upload",
        "/fulfillment",
        "/product-analytics",
        "/returns",
        "/shipping",
        "/inventory-alerts",
        "/order-analytics",
        "/refunds",
        "/customers",
        "/customer-profile",
        "/campaigns",
        "/promotions",
        "/reviews",
        "/marketing-analytics",
        "/segmentation",
        "/loyalty",
        "/email-campaigns",
        "/automation",
        "/store-settings",
        "/payment-settings",
        "/shipping-settings",
        "/tax-settings",
        "/email-templates",
        "/notifications",
        "/domain",
        "/api-settings",
        "/financial-dashboard",
        "/sales-reports",
        "/profit-loss",
        "/revenue-analytics",
        "/expenses",
        "/tax-reports"
    ],
    "Customer Portal": [
        "/",
        "/products",
        "/cart",
        "/checkout",
        "/order-confirmation",
        "/search",
        "/order-detail",
        "/account",
        "/addresses",
        "/wishlist",
        "/reviews",
        "/help"
    ]
}

def test_page(url):
    """Test if a page loads without 404 error"""
    try:
        response = requests.get(url, timeout=5)
        return {
            "status": response.status_code,
            "success": response.status_code == 200
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "success": False,
            "error": str(e)
        }

def main():
    results = {}
    total_pages = 0
    working_pages = 0
    
    print("=" * 80)
    print("AUTOMATED PAGE TESTING")
    print("=" * 80)
    print()
    
    for portal, pages in PAGES.items():
        print(f"\n{portal}:")
        print("-" * 80)
        portal_results = []
        
        for page in pages:
            url = urljoin(BASE_URL, page)
            result = test_page(url)
            total_pages += 1
            
            status_icon = "✅" if result["success"] else "❌"
            status_text = f"{result['status']}"
            
            if result["success"]:
                working_pages += 1
                
            print(f"  {status_icon} {page:40} {status_text}")
            portal_results.append({
                "page": page,
                "url": url,
                **result
            })
        
        results[portal] = portal_results
    
    print()
    print("=" * 80)
    print(f"SUMMARY: {working_pages}/{total_pages} pages accessible ({working_pages/total_pages*100:.1f}%)")
    print("=" * 80)
    print()
    print("Note: This only tests if pages return 200 OK.")
    print("It does NOT test if pages render correctly or have React errors.")
    print("Manual browser testing is still required for full validation.")
    
    # Save results to JSON
    with open('/home/ubuntu/Multi-agent-AI-Ecommerce/page_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\nResults saved to: page_test_results.json")

if __name__ == "__main__":
    main()
