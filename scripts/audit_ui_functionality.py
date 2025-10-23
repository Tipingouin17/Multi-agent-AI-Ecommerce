#!/usr/bin/env python3
"""
UI Functionality Audit Script
Analyzes all UI components and verifies API endpoint mappings
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict

# Base paths
UI_DIR = Path("/home/ubuntu/Multi-agent-AI-Ecommerce/multi-agent-dashboard/src")
AGENTS_DIR = Path("/home/ubuntu/Multi-agent-AI-Ecommerce/agents")

def extract_api_calls(file_path):
    """Extract API calls from a React component"""
    api_calls = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find fetch calls
        fetch_pattern = r'fetch\([\'"`]([^\'"`]+)[\'"`]'
        fetches = re.findall(fetch_pattern, content)
        api_calls.extend(fetches)
        
        # Find axios calls
        axios_pattern = r'axios\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]'
        axios_calls = re.findall(axios_pattern, content)
        api_calls.extend([call[1] for call in axios_calls])
        
        # Find API_BASE_URL usage
        api_base_pattern = r'\$\{API_BASE_URL\}([^\'"`\}]+)'
        api_base_calls = re.findall(api_base_pattern, content)
        api_calls.extend(api_base_calls)
        
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return api_calls

def extract_agent_endpoints(file_path):
    """Extract API endpoints from agent files"""
    endpoints = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find FastAPI route decorators
        route_patterns = [
            r'@app\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]',
            r'@router\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]'
        ]
        
        for pattern in route_patterns:
            matches = re.findall(pattern, content)
            for method, path in matches:
                endpoints.append({
                    'method': method.upper(),
                    'path': path,
                    'agent': file_path.stem
                })
    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return endpoints

def analyze_ui_components():
    """Analyze all UI components for API calls"""
    print("=" * 80)
    print("UI FUNCTIONALITY AUDIT")
    print("=" * 80)
    print()
    
    # Find all React components
    components = list(UI_DIR.rglob("*.jsx")) + list(UI_DIR.rglob("*.tsx"))
    
    print(f"Found {len(components)} React components")
    print()
    
    # Extract API calls from each component
    component_apis = {}
    all_api_calls = set()
    
    for component in components:
        api_calls = extract_api_calls(component)
        if api_calls:
            rel_path = component.relative_to(UI_DIR)
            component_apis[str(rel_path)] = api_calls
            all_api_calls.update(api_calls)
    
    print(f"Components making API calls: {len(component_apis)}")
    print(f"Unique API endpoints called: {len(all_api_calls)}")
    print()
    
    return component_apis, all_api_calls

def analyze_agent_endpoints():
    """Analyze all agent files for exposed endpoints"""
    print("=" * 80)
    print("AGENT API ENDPOINTS")
    print("=" * 80)
    print()
    
    # Find all agent files
    agent_files = list(AGENTS_DIR.glob("*_agent*.py"))
    
    print(f"Found {len(agent_files)} agent files")
    print()
    
    # Extract endpoints from each agent
    all_endpoints = []
    agent_endpoint_map = defaultdict(list)
    
    for agent_file in agent_files:
        endpoints = extract_agent_endpoints(agent_file)
        all_endpoints.extend(endpoints)
        if endpoints:
            agent_endpoint_map[agent_file.stem] = endpoints
    
    print(f"Agents with API endpoints: {len(agent_endpoint_map)}")
    print(f"Total API endpoints: {len(all_endpoints)}")
    print()
    
    return agent_endpoint_map, all_endpoints

def match_ui_to_agents(component_apis, all_endpoints):
    """Match UI API calls to agent endpoints"""
    print("=" * 80)
    print("UI TO AGENT MAPPING")
    print("=" * 80)
    print()
    
    # Create endpoint lookup
    endpoint_lookup = {}
    for endpoint in all_endpoints:
        path = endpoint['path']
        if path not in endpoint_lookup:
            endpoint_lookup[path] = []
        endpoint_lookup[path].append(endpoint)
    
    # Check each UI API call
    matched = []
    unmatched = []
    
    for component, api_calls in component_apis.items():
        for api_call in api_calls:
            # Clean up the API call
            clean_call = api_call.strip()
            
            # Try to match
            found = False
            for endpoint_path in endpoint_lookup.keys():
                if endpoint_path in clean_call or clean_call in endpoint_path:
                    matched.append({
                        'component': component,
                        'ui_call': clean_call,
                        'agent_endpoint': endpoint_path,
                        'agent': endpoint_lookup[endpoint_path][0]['agent']
                    })
                    found = True
                    break
            
            if not found:
                unmatched.append({
                    'component': component,
                    'ui_call': clean_call
                })
    
    print(f"Matched API calls: {len(matched)}")
    print(f"Unmatched API calls: {len(unmatched)}")
    print()
    
    return matched, unmatched

def generate_report(component_apis, agent_endpoint_map, matched, unmatched):
    """Generate comprehensive audit report"""
    report = []
    
    report.append("# UI Functionality Audit Report")
    report.append("")
    report.append("## Summary")
    report.append("")
    report.append(f"- **UI Components analyzed:** {len(component_apis)}")
    report.append(f"- **Agents with APIs:** {len(agent_endpoint_map)}")
    report.append(f"- **Matched API calls:** {len(matched)}")
    report.append(f"- **Unmatched API calls:** {len(unmatched)}")
    report.append("")
    
    # Coverage percentage
    total_calls = len(matched) + len(unmatched)
    if total_calls > 0:
        coverage = (len(matched) / total_calls) * 100
        report.append(f"**API Coverage:** {coverage:.1f}%")
    else:
        report.append("**API Coverage:** N/A (no API calls found)")
    report.append("")
    
    # Unmatched API calls (potential issues)
    if unmatched:
        report.append("## ⚠️ Unmatched API Calls (Potential Missing Endpoints)")
        report.append("")
        report.append("These UI components are calling APIs that don't exist in any agent:")
        report.append("")
        
        for item in unmatched[:20]:  # Limit to first 20
            report.append(f"- **Component:** `{item['component']}`")
            report.append(f"  - **API Call:** `{item['ui_call']}`")
            report.append("")
    
    # Agent endpoint summary
    report.append("## Agent API Endpoints")
    report.append("")
    
    for agent, endpoints in sorted(agent_endpoint_map.items()):
        report.append(f"### {agent}")
        report.append("")
        for endpoint in endpoints:
            report.append(f"- `{endpoint['method']} {endpoint['path']}`")
        report.append("")
    
    # Matched API calls
    if matched:
        report.append("## ✅ Successfully Matched API Calls")
        report.append("")
        
        for item in matched[:20]:  # Limit to first 20
            report.append(f"- **Component:** `{item['component']}`")
            report.append(f"  - **UI Call:** `{item['ui_call']}`")
            report.append(f"  - **Agent:** `{item['agent']}`")
            report.append(f"  - **Endpoint:** `{item['agent_endpoint']}`")
            report.append("")
    
    return "\n".join(report)

def main():
    """Main audit function"""
    # Analyze UI components
    component_apis, all_api_calls = analyze_ui_components()
    
    # Analyze agent endpoints
    agent_endpoint_map, all_endpoints = analyze_agent_endpoints()
    
    # Match UI to agents
    matched, unmatched = match_ui_to_agents(component_apis, all_endpoints)
    
    # Generate report
    report = generate_report(component_apis, agent_endpoint_map, matched, unmatched)
    
    # Save report
    report_path = Path("/home/ubuntu/Multi-agent-AI-Ecommerce/UI_FUNCTIONALITY_AUDIT.md")
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"Report saved to: {report_path}")
    print()
    
    # Print summary
    print("=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)
    print()
    print(f"✅ Matched API calls: {len(matched)}")
    print(f"⚠️  Unmatched API calls: {len(unmatched)}")
    print()
    
    if unmatched:
        print("WARNING: Some UI components are calling APIs that don't exist!")
        print(f"Check {report_path} for details.")
    else:
        print("SUCCESS: All UI API calls are matched to agent endpoints!")

if __name__ == "__main__":
    main()

