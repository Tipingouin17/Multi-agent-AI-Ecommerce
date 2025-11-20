"""
Test script to debug customer profile 403 error
"""

import requests
import json
from jose import jwt

# Configuration
AUTH_URL = "http://localhost:8100/api/auth/login"
CUSTOMER_PROFILE_URL = "http://localhost:8007/api/profile"

def test_customer_profile():
    print("=" * 80)
    print("CUSTOMER PROFILE 403 DEBUG TEST")
    print("=" * 80)
    
    # Step 1: Login as customer
    print("\n1. Logging in as customer...")
    login_data = {
        "email": "customer1@example.com",
        "password": "customer123"
    }
    
    try:
        response = requests.post(AUTH_URL, json=login_data)
        print(f"   Login Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   Login failed: {response.text}")
            return
        
        login_result = response.json()
        access_token = login_result.get("access_token")
        print(f"   ✓ Login successful")
        print(f"   Access token: {access_token[:50]}...")
        
        # Step 2: Decode JWT token to see its contents
        print("\n2. Decoding JWT token...")
        try:
            # Decode without verification to see contents
            decoded = jwt.get_unverified_claims(access_token)
            print(f"   JWT Payload:")
            print(json.dumps(decoded, indent=4))
            
            # Check for expected fields
            has_user_id = "user_id" in decoded
            has_username = "username" in decoded
            has_role = "role" in decoded
            has_token_type = "token_type" in decoded
            
            print(f"\n   Field Check:")
            print(f"   - user_id: {'✓' if has_user_id else '✗'}")
            print(f"   - username: {'✓' if has_username else '✗'}")
            print(f"   - role: {'✓' if has_role else '✗'}")
            print(f"   - token_type: {'✓' if has_token_type else '✗'}")
            
        except Exception as e:
            print(f"   ✗ Failed to decode token: {e}")
        
        # Step 3: Call customer profile endpoint
        print("\n3. Calling customer profile endpoint...")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            profile_response = requests.get(CUSTOMER_PROFILE_URL, headers=headers)
            print(f"   Profile Status: {profile_response.status_code}")
            
            if profile_response.status_code == 200:
                print(f"   ✓ Profile retrieved successfully!")
                profile_data = profile_response.json()
                print(f"   Profile Data:")
                print(json.dumps(profile_data, indent=4))
            else:
                print(f"   ✗ Profile request failed")
                print(f"   Response: {profile_response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ✗ Connection refused - Customer agent not running on port 8007")
        except Exception as e:
            print(f"   ✗ Error: {e}")
            
    except requests.exceptions.ConnectionError:
        print(f"   ✗ Connection refused - Auth agent not running on port 8100")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_customer_profile()
