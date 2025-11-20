# JWT TOKEN FORMAT FIX

**Date:** November 20, 2025  
**Bug:** Customer profile 403 error (Bug #12)  
**Root Cause:** JWT token format mismatch between auth agent and shared auth module

---

## PROBLEM DESCRIPTION

After restarting the platform, customer login worked but accessing the customer profile page resulted in a 403 Forbidden error:

```
Failed to get customer profile: Request failed with status code 403
```

## ROOT CAUSE ANALYSIS

The auth agent was creating JWT tokens with a different format than what the shared auth module expected:

**Auth Agent Token Format (INCORRECT):**
```json
{
  "sub": "user_id",
  "role": "customer",
  "exp": 1234567890,
  "type": "access"
}
```

**Shared Auth Module Expected Format (CORRECT):**
```json
{
  "user_id": "user_id",
  "username": "username",
  "role": "customer",
  "token_type": "access",
  "exp": 1234567890
}
```

The `get_current_user()` function in `shared/auth.py` was looking for `user_id` and `username` fields, but the auth agent was only setting `sub` and `role`. This caused the JWT decoding to fail silently and return invalid user data.

---

## FIX APPLIED

### File: `/home/ubuntu/Multi-agent-AI-Ecommerce/agents/auth_agent.py`

**Change 1: Updated `create_access_token()` method**

```python
# BEFORE
def create_access_token(self, user_id: str, role: str) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": user_id,
        "role": role,
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# AFTER
def create_access_token(self, user_id: str, role: str, username: str = None, email: str = None) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "user_id": user_id,
        "username": username or email or user_id,
        "role": role,
        "token_type": "access",
        "exp": expire
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

**Change 2: Updated login endpoint call**

```python
# BEFORE
access_token = self.create_access_token(user.id, user.role)

# AFTER
access_token = self.create_access_token(user.id, user.role, username=user.username, email=user.email)
```

**Change 3: Updated refresh endpoint call**

```python
# BEFORE
access_token = self.create_access_token(user.id, user.role)

# AFTER
access_token = self.create_access_token(user.id, user.role, username=user.username, email=user.email)
```

---

## VERIFICATION STEPS

1. **Restart auth agent** to apply the JWT token format fix
2. **Clear browser cache/cookies** to remove old tokens
3. **Login as customer** (customer1@example.com / customer123)
4. **Navigate to Account/Profile page**
5. **Verify profile data loads** without 403 error

---

## RELATED FILES

- `/home/ubuntu/Multi-agent-AI-Ecommerce/agents/auth_agent.py` - Fixed JWT token creation
- `/home/ubuntu/Multi-agent-AI-Ecommerce/shared/auth.py` - JWT token validation (no changes needed)
- `/home/ubuntu/Multi-agent-AI-Ecommerce/agents/customer_agent_v3.py` - Profile endpoint (no changes needed)

---

## STATUS

- ✅ **Code fix applied** to auth_agent.py
- ⏳ **Pending verification** - Requires auth agent restart
- ⏳ **Testing required** - Customer profile page access

---

## NOTES

This fix also resolves any other endpoints that depend on `get_current_user()` for authentication, as the JWT token format is now consistent across all agents.

**Impact:** All authenticated endpoints (customer, merchant, admin) will benefit from this fix.

---

**Document Status:** FINAL  
**Last Updated:** November 20, 2025
