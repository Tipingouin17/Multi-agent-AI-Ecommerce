#!/usr/bin/env python3
"""
Script to remove mock data fallbacks from UI components
and replace them with proper error handling.
"""

import re
import os
from pathlib import Path

# Component configurations
COMPONENTS = [
    {
        'file': 'multi-agent-dashboard/src/pages/admin/CarrierConfiguration.jsx',
        'api_port': 8006,
        'api_endpoint': '/api/carriers/config',
        'agent_name': 'Transport',
        'data_key': 'carriers'
    },
    {
        'file': 'multi-agent-dashboard/src/pages/admin/ChannelConfiguration.jsx',
        'api_port': 8007,
        'api_endpoint': '/api/connections',
        'agent_name': 'Marketplace',
        'data_key': 'connections'
    },
    {
        'file': 'multi-agent-dashboard/src/pages/admin/ProductConfiguration.jsx',
        'api_port': 8003,
        'api_endpoint': '/api/categories',
        'agent_name': 'Product',
        'data_key': 'categories',
        'multiple_endpoints': [
            {'endpoint': '/api/categories', 'data_key': 'categories'},
            {'endpoint': '/api/attributes', 'data_key': 'attributes'},
            {'endpoint': '/api/templates', 'data_key': 'templates'}
        ]
    },
    {
        'file': 'multi-agent-dashboard/src/pages/admin/TaxConfiguration.jsx',
        'api_port': 8011,
        'api_endpoint': '/api/tax/rules',
        'agent_name': 'Backoffice',
        'data_key': 'taxRules',
        'multiple_endpoints': [
            {'endpoint': '/api/tax/rules', 'data_key': 'taxRules'},
            {'endpoint': '/api/tax/categories', 'data_key': 'taxCategories'}
        ]
    },
    {
        'file': 'multi-agent-dashboard/src/pages/admin/UserManagement.jsx',
        'api_port': 8011,
        'api_endpoint': '/api/users',
        'agent_name': 'Backoffice',
        'data_key': 'users',
        'multiple_endpoints': [
            {'endpoint': '/api/users', 'data_key': 'users'},
            {'endpoint': '/api/roles', 'data_key': 'roles'}
        ]
    },
    {
        'file': 'multi-agent-dashboard/src/pages/admin/WarehouseConfiguration.jsx',
        'api_port': 8005,
        'api_endpoint': '/api/warehouses',
        'agent_name': 'Warehouse',
        'data_key': 'warehouses'
    }
]

def find_mock_data_fallback(content):
    """Find mock data fallback patterns in the content"""
    # Pattern: } catch (error) { ... setData([...mock data...]) }
    pattern = r'}\s*catch\s*\([^)]+\)\s*\{[^}]*?//[^\n]*(?:Fallback|Mock|mock|fallback)[^\n]*\n\s*set\w+\(\['
    matches = list(re.finditer(pattern, content, re.DOTALL))
    return matches

def remove_mock_data_from_file(filepath, api_port, api_endpoint, agent_name, data_key):
    """Remove mock data fallbacks from a file"""
    
    full_path = Path('/home/ubuntu/Multi-agent-AI-Ecommerce') / filepath
    
    if not full_path.exists():
        print(f"❌ File not found: {filepath}")
        return False
    
    with open(full_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Find and remove mock data fallbacks
    matches = find_mock_data_fallback(content)
    
    if not matches:
        print(f"✓ No mock data found in {filepath}")
        return True
    
    print(f"🔧 Fixing {filepath}...")
    print(f"   Found {len(matches)} mock data fallback(s)")
    
    # Replace mock data fallbacks with proper error handling
    # This is a simplified approach - for complex cases, manual review is needed
    
    # Pattern 1: Simple setData([...]) fallback
    content = re.sub(
        r'}\s*catch\s*\([^)]+\)\s*\{[^}]*?console\.error\([^)]+\);[^}]*?//[^\n]*(?:Fallback|Mock|mock|fallback)[^\n]*\n\s*set(\w+)\(\[[^\]]*\]\);',
        lambda m: f'''}} catch (error) {{
      console.error('Error fetching {data_key}:', error);
      setError({{
        message: 'Failed to load {data_key} from database',
        details: error.message,
        retry: fetch{m.group(1).replace('set', '')}
      }});
      set{m.group(1)}([]); // Empty array, NO mock data''',
        content,
        flags=re.DOTALL
    )
    
    # Update API endpoint to correct port
    content = re.sub(
        r"fetch\('http://localhost:\d+/api/[^']+'\)",
        f"fetch('http://localhost:{api_port}{api_endpoint}')",
        content
    )
    
    # Add error state if not present
    if 'const [error, setError]' not in content and 'useState(null); // error' not in content:
        # Find the component function and add error state
        content = re.sub(
            r'(const \w+Configuration = \(\) => \{[^}]*?const \[[^,]+, set[^\]]+\] = useState\([^)]+\);)',
            r'\1\n  const [error, setError] = useState(null);',
            content,
            count=1
        )
    
    if content != original_content:
        with open(full_path, 'w') as f:
            f.write(content)
        print(f"✅ Fixed {filepath}")
        return True
    else:
        print(f"⚠️  No changes made to {filepath}")
        return False

def main():
    print("=" * 60)
    print("Removing Mock Data Fallbacks from UI Components")
    print("=" * 60)
    print()
    
    fixed_count = 0
    failed_count = 0
    
    for component in COMPONENTS:
        try:
            if remove_mock_data_from_file(
                component['file'],
                component['api_port'],
                component['api_endpoint'],
                component['agent_name'],
                component['data_key']
            ):
                fixed_count += 1
            else:
                failed_count += 1
        except Exception as e:
            print(f"❌ Error processing {component['file']}: {e}")
            failed_count += 1
        print()
    
    print("=" * 60)
    print(f"Summary: {fixed_count} fixed, {failed_count} failed")
    print("=" * 60)
    print()
    print("⚠️  IMPORTANT: Manual review recommended for complex components")
    print("✅ All mock data fallbacks should now be removed")
    print("🔄 Components will show errors instead of fake data")
    print()

if __name__ == '__main__':
    main()

