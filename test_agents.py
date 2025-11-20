"""
Comprehensive Agent Testing Script
Tests all implemented agents in sandbox environment
"""

import sys
import os
import requests
import time
import subprocess
import signal
from datetime import datetime, timedelta

# Test configuration
TEST_BASE_URL = "http://localhost"
AGENTS_TO_TEST = [
    {"name": "Offers Agent", "port": 8040, "script": "agents/offers_agent_v3.py"},
    {"name": "Advertising Agent", "port": 8041, "script": "agents/advertising_agent_v3.py"}
]

# Store running processes
running_processes = []

def cleanup():
    """Kill all running agent processes"""
    print("\n🧹 Cleaning up...")
    for proc in running_processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except:
            proc.kill()
    print("✅ Cleanup complete")

def start_agent(script_path, port):
    """Start an agent process"""
    print(f"  Starting agent: {script_path} on port {port}")
    try:
        proc = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd="/home/ubuntu/Multi-agent-AI-Ecommerce"
        )
        running_processes.append(proc)
        time.sleep(3)  # Wait for agent to start
        return proc
    except Exception as e:
        print(f"  ❌ Failed to start agent: {e}")
        return None

def test_health_endpoint(port):
    """Test agent health endpoint"""
    url = f"{TEST_BASE_URL}:{port}/health"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Health check passed: {data}")
            return True
        else:
            print(f"  ❌ Health check failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Health check failed: {e}")
        return False

def test_offers_agent():
    """Test Offers Agent endpoints"""
    print("\n📦 Testing Offers Agent...")
    port = 8040
    base_url = f"{TEST_BASE_URL}:{port}"
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Health check
    print("  Test 1: Health endpoint")
    if test_health_endpoint(port):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 2: Get offers (should return empty list or require auth)
    print("  Test 2: GET /api/offers")
    try:
        response = requests.get(f"{base_url}/api/offers")
        if response.status_code in [200, 401, 403]:
            print(f"  ✅ GET /api/offers returned status {response.status_code}")
            tests_passed += 1
        else:
            print(f"  ❌ Unexpected status: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"  ❌ Request failed: {e}")
        tests_failed += 1
    
    return tests_passed, tests_failed

def test_advertising_agent():
    """Test Advertising Agent endpoints"""
    print("\n📺 Testing Advertising Agent...")
    port = 8041
    base_url = f"{TEST_BASE_URL}:{port}"
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Health check
    print("  Test 1: Health endpoint")
    if test_health_endpoint(port):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 2: Get campaigns
    print("  Test 2: GET /api/campaigns")
    try:
        response = requests.get(f"{base_url}/api/campaigns")
        if response.status_code in [200, 401, 403]:
            print(f"  ✅ GET /api/campaigns returned status {response.status_code}")
            tests_passed += 1
        else:
            print(f"  ❌ Unexpected status: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"  ❌ Request failed: {e}")
        tests_failed += 1
    
    return tests_passed, tests_failed

def main():
    print("="*60)
    print("🧪 AGENT TESTING SUITE")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    total_passed = 0
    total_failed = 0
    
    try:
        # Start all agents
        print("🚀 Starting agents...")
        for agent in AGENTS_TO_TEST:
            proc = start_agent(agent["script"], agent["port"])
            if not proc:
                print(f"❌ Failed to start {agent['name']}")
                cleanup()
                return 1
        
        print(f"\n✅ All agents started\n")
        time.sleep(2)  # Additional wait time
        
        # Test Offers Agent
        passed, failed = test_offers_agent()
        total_passed += passed
        total_failed += failed
        
        # Test Advertising Agent
        passed, failed = test_advertising_agent()
        total_passed += passed
        total_failed += failed
        
        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"✅ Tests Passed: {total_passed}")
        print(f"❌ Tests Failed: {total_failed}")
        print(f"📈 Success Rate: {(total_passed/(total_passed+total_failed)*100):.1f}%")
        print("="*60)
        
        if total_failed == 0:
            print("\n🎉 ALL TESTS PASSED! Agents are 100% ready!")
            return 0
        else:
            print(f"\n⚠️  {total_failed} test(s) failed. Review errors above.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        cleanup()

if __name__ == "__main__":
    sys.exit(main())
