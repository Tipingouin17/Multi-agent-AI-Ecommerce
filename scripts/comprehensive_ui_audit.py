#!/usr/bin/env python3
"""
Comprehensive UI Audit Script

This script analyzes all UI components to:
1. Identify all personas and their pages
2. Extract all API calls made by each page
3. Map API calls to backend agent endpoints
4. Verify which endpoints exist in agents
5. Check which endpoints actually query the database
6. Generate a detailed production readiness report
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DASHBOARD_SRC = PROJECT_ROOT / "multi-agent-dashboard" / "src"
AGENTS_DIR = PROJECT_ROOT / "agents"
SHARED_DIR = PROJECT_ROOT / "shared"

# Persona definitions
PERSONAS = {
    "admin": {
        "name": "Administrator",
        "description": "System admin managing the platform",
        "pages_dir": DASHBOARD_SRC / "pages" / "admin"
    },
    "merchant": {
        "name": "Merchant",
        "description": "Seller managing products and orders",
        "pages_dir": DASHBOARD_SRC / "pages" / "merchant"
    },
    "customer": {
        "name": "Customer",
        "description": "End customer browsing and purchasing",
        "pages_dir": DASHBOARD_SRC / "pages" / "customer"
    }
}

def extract_api_calls_from_file(filepath):
    """Extract all API calls from a React component file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return []
    
    api_calls = []
    
    # Pattern 1: apiService.methodName(...)
    pattern1 = r'apiService\.(\w+)\('
    matches1 = re.findall(pattern1, content)
    api_calls.extend(matches1)
    
    # Pattern 2: await apiService.methodName(...)
    pattern2 = r'await\s+apiService\.(\w+)\('
    matches2 = re.findall(pattern2, content)
    api_calls.extend(matches2)
    
    # Pattern 3: clients.agent.method(...)
    pattern3 = r'clients\.(\w+)\.(get|post|put|delete|patch)\([\'"]([^\'"]+)'
    matches3 = re.findall(pattern3, content)
    for agent, method, endpoint in matches3:
        api_calls.append(f"{agent}:{method}:{endpoint}")
    
    return list(set(api_calls))  # Remove duplicates

def scan_persona_pages(persona_key):
    """Scan all pages for a persona"""
    persona = PERSONAS[persona_key]
    pages_dir = persona["pages_dir"]
    
    if not pages_dir.exists():
        return {}
    
    pages = {}
    
    for filepath in pages_dir.glob("*.jsx"):
        page_name = filepath.stem
        api_calls = extract_api_calls_from_file(filepath)
        
        pages[page_name] = {
            "file": str(filepath.relative_to(PROJECT_ROOT)),
            "api_calls": api_calls,
            "api_call_count": len(api_calls)
        }
    
    return pages

def scan_api_service():
    """Scan api.js to find all defined methods"""
    api_file = DASHBOARD_SRC / "lib" / "api.js"
    
    if not api_file.exists():
        return {}
    
    with open(api_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    methods = {}
    
    # Find all async methods
    pattern = r'async\s+(\w+)\s*\([^)]*\)\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for method_name, method_body in matches:
        # Check if it uses mock data
        has_mock = 'getMock' in method_body or 'mock' in method_body.lower()
        
        # Extract agent and endpoint
        agent_match = re.search(r'clients\.(\w+)\.(get|post|put|delete|patch)\([\'"]([^\'"]+)', method_body)
        
        if agent_match:
            agent, http_method, endpoint = agent_match.groups()
            methods[method_name] = {
                "agent": agent,
                "http_method": http_method,
                "endpoint": endpoint,
                "has_mock_fallback": has_mock,
                "type": "real_api_with_fallback" if has_mock else "real_api"
            }
        else:
            methods[method_name] = {
                "type": "mock_only",
                "has_mock_fallback": True
            }
    
    return methods

def scan_agent_endpoints(agent_name):
    """Scan an agent file to find all defined endpoints"""
    agent_files = list(AGENTS_DIR.glob(f"{agent_name}_agent*.py"))
    
    if not agent_files:
        return []
    
    endpoints = []
    
    for agent_file in agent_files:
        try:
            with open(agent_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            continue
        
        # Find FastAPI route decorators
        # Pattern: @app.get("/endpoint") or @self.app.post("/endpoint")
        pattern = r'@(?:self\.)?app\.(get|post|put|delete|patch)\([\'"]([^\'"]+)'
        matches = re.findall(pattern, content)
        
        for method, endpoint in matches:
            # Check if endpoint queries database
            # Look for the function body after the decorator
            func_pattern = rf'@(?:self\.)?app\.{method}\([\'"]' + re.escape(endpoint) + r'[\'"][^\n]*\n\s*(?:async\s+)?def\s+\w+[^:]*:\s*([^@]+?)(?=\n\s*@|\n\s*async\s+def|\Z)'
            func_match = re.search(func_pattern, content, re.DOTALL)
            
            queries_db = False
            if func_match:
                func_body = func_match.group(1)
                # Check for database operations
                if any(keyword in func_body for keyword in ['session', 'query', 'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'db_helper', 'repository']):
                    queries_db = True
            
            endpoints.append({
                "method": method,
                "endpoint": endpoint,
                "queries_database": queries_db,
                "file": str(agent_file.relative_to(PROJECT_ROOT))
            })
    
    return endpoints

def generate_report():
    """Generate comprehensive audit report"""
    print("=" * 80)
    print("COMPREHENSIVE UI PRODUCTION READINESS AUDIT")
    print("=" * 80)
    print()
    
    # Scan API service
    print("📊 Scanning API Service...")
    api_methods = scan_api_service()
    print(f"   Found {len(api_methods)} API methods")
    print()
    
    # Scan all personas
    all_persona_data = {}
    
    for persona_key, persona_info in PERSONAS.items():
        print(f"👤 Scanning {persona_info['name']} Persona...")
        pages = scan_persona_pages(persona_key)
        print(f"   Found {len(pages)} pages")
        
        total_api_calls = sum(p["api_call_count"] for p in pages.values())
        print(f"   Total API calls: {total_api_calls}")
        print()
        
        all_persona_data[persona_key] = {
            "info": persona_info,
            "pages": pages
        }
    
    # Scan agent endpoints
    print("🤖 Scanning Agent Endpoints...")
    agent_endpoints = {}
    
    agent_names = ['order', 'product', 'inventory', 'warehouse', 'payment', 
                   'transport', 'marketplace', 'customer', 'fraud', 'risk',
                   'backoffice', 'knowledge', 'quality', 'document']
    
    for agent_name in agent_names:
        endpoints = scan_agent_endpoints(agent_name)
        if endpoints:
            agent_endpoints[agent_name] = endpoints
            db_count = sum(1 for e in endpoints if e['queries_database'])
            print(f"   {agent_name}: {len(endpoints)} endpoints ({db_count} query DB)")
    
    print()
    
    # Generate detailed report
    report = {
        "summary": {
            "total_personas": len(PERSONAS),
            "total_pages": sum(len(p["pages"]) for p in all_persona_data.values()),
            "total_api_methods": len(api_methods),
            "total_agents_with_endpoints": len(agent_endpoints),
            "total_agent_endpoints": sum(len(e) for e in agent_endpoints.values())
        },
        "personas": all_persona_data,
        "api_methods": api_methods,
        "agent_endpoints": agent_endpoints
    }
    
    # Convert Path objects to strings for JSON serialization
    def convert_paths(obj):
        if isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: convert_paths(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_paths(item) for item in obj]
        return obj
    
    report = convert_paths(report)
    
    # Save report
    report_file = PROJECT_ROOT / "UI_PRODUCTION_READINESS_AUDIT.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Report saved to: {report_file}")
    print()
    
    return report

def analyze_gaps(report):
    """Analyze gaps between UI needs and backend implementation"""
    print("=" * 80)
    print("GAP ANALYSIS")
    print("=" * 80)
    print()
    
    api_methods = report["api_methods"]
    agent_endpoints = report["agent_endpoints"]
    
    # Categorize API methods
    mock_only = []
    real_with_fallback = []
    real_only = []
    
    for method_name, method_info in api_methods.items():
        if method_info["type"] == "mock_only":
            mock_only.append(method_name)
        elif method_info["type"] == "real_api_with_fallback":
            real_with_fallback.append(method_name)
        else:
            real_only.append(method_name)
    
    print(f"📊 API Methods Status:")
    print(f"   ✅ Real API only: {len(real_only)}")
    print(f"   ⚠️  Real API with mock fallback: {len(real_with_fallback)}")
    print(f"   ❌ Mock data only: {len(mock_only)}")
    print()
    
    # Check which endpoints actually exist
    missing_endpoints = []
    
    for method_name, method_info in api_methods.items():
        if method_info["type"] != "mock_only":
            agent = method_info.get("agent")
            endpoint = method_info.get("endpoint")
            
            if agent and endpoint:
                # Check if endpoint exists in agent
                agent_eps = agent_endpoints.get(agent, [])
                endpoint_exists = any(
                    e["endpoint"] == endpoint 
                    for e in agent_eps
                )
                
                if not endpoint_exists:
                    missing_endpoints.append({
                        "method": method_name,
                        "agent": agent,
                        "endpoint": endpoint
                    })
    
    print(f"❌ Missing Backend Endpoints: {len(missing_endpoints)}")
    if missing_endpoints:
        for item in missing_endpoints[:10]:  # Show first 10
            print(f"   - {item['method']}: {item['agent']}.{item['endpoint']}")
        if len(missing_endpoints) > 10:
            print(f"   ... and {len(missing_endpoints) - 10} more")
    print()
    
    # Calculate production readiness score
    total_methods = len(api_methods)
    working_methods = len(real_only)
    fallback_methods = len(real_with_fallback)
    
    # Methods with real endpoints that exist
    working_with_endpoints = working_methods + fallback_methods - len(missing_endpoints)
    
    readiness_score = (working_with_endpoints / total_methods * 100) if total_methods > 0 else 0
    
    print(f"📈 Production Readiness Score: {readiness_score:.1f}%")
    print()
    
    return {
        "mock_only": mock_only,
        "real_with_fallback": real_with_fallback,
        "real_only": real_only,
        "missing_endpoints": missing_endpoints,
        "readiness_score": readiness_score
    }

def main():
    """Main function"""
    report = generate_report()
    gaps = analyze_gaps(report)
    
    print("=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Review UI_PRODUCTION_READINESS_AUDIT.json for detailed findings")
    print("2. Implement missing backend endpoints")
    print("3. Replace mock data with real database queries")
    print("4. Re-run audit to verify improvements")
    print()

if __name__ == '__main__':
    main()

