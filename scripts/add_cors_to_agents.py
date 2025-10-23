#!/usr/bin/env python3
"""
Script to add CORS middleware to all agent files that use FastAPI
"""

import os
import re

# List of production agent files
AGENT_FILES = [
    'agents/product_agent_production.py',
    'agents/inventory_agent.py',
    'agents/warehouse_agent_production.py',
    'agents/transport_agent_production.py',
    'agents/marketplace_connector_agent_production.py',
    'agents/customer_agent_enhanced.py',
    'agents/after_sales_agent.py',
    'agents/document_generation_agent.py',
    'agents/quality_control_agent.py',
    'agents/backoffice_agent.py',
    'agents/knowledge_management_agent.py',
    'agents/fraud_detection_agent.py',
    'agents/risk_anomaly_detection_agent.py',
    'agents/payment_agent_enhanced.py',
]

def add_cors_to_agent(filepath):
    """Add CORS middleware to an agent file"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if CORS is already added
    if 'CORSMiddleware' in content:
        print(f"✓ {filepath} - CORS already added")
        return False
    
    # Check if FastAPI is used
    if 'from fastapi import' not in content:
        print(f"⊘ {filepath} - No FastAPI import found")
        return False
    
    modified = False
    
    # Add CORSMiddleware import
    content = re.sub(
        r'(from fastapi import [^\n]+)',
        r'\1\nfrom fastapi.middleware.cors import CORSMiddleware',
        content,
        count=1
    )
    modified = True
    
    # Find where FastAPI app is created and add CORS middleware
    # Pattern: self.app = FastAPI(...)
    pattern = r'(self\.app = FastAPI\([^\)]*\))'
    
    if re.search(pattern, content):
        replacement = r'''\1
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, specify exact origins
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )'''
        
        content = re.sub(pattern, replacement, content, count=1)
        modified = True
    
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ {filepath} - CORS added successfully")
        return True
    else:
        print(f"⊘ {filepath} - Could not add CORS (FastAPI app not found)")
        return False

def main():
    """Main function"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    print("Adding CORS middleware to all agents...")
    print("=" * 60)
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for agent_file in AGENT_FILES:
        filepath = os.path.join(project_root, agent_file)
        
        if not os.path.exists(filepath):
            print(f"✗ {agent_file} - File not found")
            fail_count += 1
            continue
        
        try:
            if add_cors_to_agent(filepath):
                success_count += 1
            else:
                skip_count += 1
        except Exception as e:
            print(f"✗ {agent_file} - Error: {e}")
            fail_count += 1
    
    print("=" * 60)
    print(f"Summary: {success_count} modified, {skip_count} skipped, {fail_count} failed")

if __name__ == '__main__':
    main()

