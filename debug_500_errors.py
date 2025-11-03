#!/usr/bin/env python3
"""
Debug HTTP 500 Errors in Agents
Tests failing endpoints and captures detailed error responses
"""

import asyncio
import httpx
import json
from datetime import datetime

# Endpoints with HTTP 500 errors
FAILING_ENDPOINTS = [
    {"agent": "monitoring", "port": 8000, "endpoint": "/agents", "method": "GET"},
    {"agent": "product", "port": 8002, "endpoint": "/products", "method": "GET"},
    {"agent": "inventory", "port": 8003, "endpoint": "/inventory", "method": "GET"},
    {"agent": "customer", "port": 8008, "endpoint": "/customers", "method": "GET"},
]

async def test_endpoint(endpoint_info: dict) -> dict:
    """Test a single endpoint and capture full error details."""
    agent = endpoint_info["agent"]
    port = endpoint_info["port"]
    endpoint = endpoint_info["endpoint"]
    method = endpoint_info["method"]
    
    url = f"http://localhost:{port}{endpoint}"
    
    print(f"\n{'='*80}")
    print(f"Testing: {agent.upper()} - {method} {endpoint}")
    print(f"URL: {url}")
    print('='*80)
    
    result = {
        "agent": agent,
        "url": url,
        "method": method,
        "status_code": None,
        "error": None,
        "response_body": None,
        "headers": None
    }
    
    try:
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, timeout=10.0)
            elif method == "POST":
                response = await client.post(url, json={}, timeout=10.0)
            
            result["status_code"] = response.status_code
            result["headers"] = dict(response.headers)
            
            # Try to parse response body
            try:
                result["response_body"] = response.json()
            except:
                result["response_body"] = response.text[:500]
            
            print(f"Status Code: {response.status_code}")
            print(f"\nResponse Headers:")
            for key, value in response.headers.items():
                print(f"  {key}: {value}")
            
            print(f"\nResponse Body:")
            if isinstance(result["response_body"], dict):
                print(json.dumps(result["response_body"], indent=2))
            else:
                print(result["response_body"])
            
            # Extract error details if available
            if response.status_code == 500:
                print(f"\n⚠️  HTTP 500 ERROR DETAILS:")
                if isinstance(result["response_body"], dict):
                    if "detail" in result["response_body"]:
                        print(f"  Detail: {result['response_body']['detail']}")
                        result["error"] = result["response_body"]["detail"]
                    if "error" in result["response_body"]:
                        print(f"  Error: {result['response_body']['error']}")
                        result["error"] = result["response_body"]["error"]
                    if "message" in result["response_body"]:
                        print(f"  Message: {result['response_body']['message']}")
                        result["error"] = result["response_body"]["message"]
                else:
                    result["error"] = result["response_body"]
                
    except httpx.TimeoutException:
        result["error"] = "Request timeout (10s)"
        print(f"❌ Error: Request timeout")
    except httpx.ConnectError:
        result["error"] = "Connection refused"
        print(f"❌ Error: Connection refused")
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ Error: {e}")
    
    return result

async def main():
    """Test all failing endpoints and generate diagnostic report."""
    print("="*80)
    print("DEBUGGING HTTP 500 ERRORS")
    print("="*80)
    print(f"Start Time: {datetime.now()}")
    print(f"Endpoints to test: {len(FAILING_ENDPOINTS)}")
    
    results = []
    
    for endpoint_info in FAILING_ENDPOINTS:
        result = await test_endpoint(endpoint_info)
        results.append(result)
        await asyncio.sleep(0.5)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    
    for result in results:
        print(f"\n{result['agent'].upper()}:")
        print(f"  URL: {result['url']}")
        print(f"  Status: {result['status_code']}")
        if result['error']:
            print(f"  Error: {result['error'][:200]}")
    
    # Save detailed results
    output_file = "debug_500_errors_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_endpoints": len(FAILING_ENDPOINTS),
            "results": results
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {output_file}")
    
    # Analysis
    print(f"\n{'='*80}")
    print("ANALYSIS")
    print('='*80)
    
    for result in results:
        if result['status_code'] == 500 and result['error']:
            print(f"\n{result['agent'].upper()}:")
            error_str = str(result['error']).lower()
            
            if 'database' in error_str or 'sql' in error_str or 'table' in error_str:
                print("  ⚠️  DATABASE ERROR - likely missing table or query failure")
            elif 'attribute' in error_str:
                print("  ⚠️  ATTRIBUTE ERROR - likely missing object property")
            elif 'key' in error_str:
                print("  ⚠️  KEY ERROR - likely missing dictionary key")
            elif 'none' in error_str or 'nonetype' in error_str:
                print("  ⚠️  NULL ERROR - likely uninitialized variable")
            else:
                print("  ⚠️  UNKNOWN ERROR - needs manual investigation")

if __name__ == "__main__":
    asyncio.run(main())

