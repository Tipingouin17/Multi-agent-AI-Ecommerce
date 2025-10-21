"""
Tests for Authentication and Authorization Module
"""

import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.auth import (
    User,
    UserRole,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
    get_password_hash,
    RoleChecker
)


class TestPasswordHashing:
    """Test password hashing and verification"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 20
        assert hashed.startswith('$2b$')  # bcrypt format
    
    def test_verify_correct_password(self):
        """Test verifying correct password"""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_incorrect_password(self):
        """Test verifying incorrect password"""
        password = "SecurePassword123!"
        wrong_password = "WrongPassword456!"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_different_hashes_for_same_password(self):
        """Test that same password produces different hashes (salt)"""
        password = "SecurePassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestTokenCreation:
    """Test JWT token creation"""
    
    def test_create_access_token(self):
        """Test access token creation"""
        user = User(
            user_id="123",
            username="testuser",
            email="test@example.com",
            role=UserRole.MERCHANT
        )
        
        token = create_access_token(user)
        
        assert isinstance(token, str)
        assert len(token) > 50
        assert '.' in token  # JWT format
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        user = User(
            user_id="123",
            username="testuser",
            email="test@example.com",
            role=UserRole.MERCHANT
        )
        
        token = create_refresh_token(user)
        
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_access_token_expiration(self):
        """Test access token has correct expiration"""
        user = User(
            user_id="123",
            username="testuser",
            email="test@example.com",
            role=UserRole.ADMIN
        )
        
        token = create_access_token(user)
        token_data = decode_token(token)
        
        # Token should expire in the future
        assert token_data.exp > datetime.utcnow()
        
        # Should expire within 31 minutes (30 min + 1 min buffer)
        assert token_data.exp < datetime.utcnow() + timedelta(minutes=31)


class TestTokenDecoding:
    """Test JWT token decoding and validation"""
    
    def test_decode_valid_token(self):
        """Test decoding valid token"""
        user = User(
            user_id="123",
            username="testuser",
            email="test@example.com",
            role=UserRole.CUSTOMER
        )
        
        token = create_access_token(user)
        token_data = decode_token(token)
        
        assert token_data.user_id == "123"
        assert token_data.username == "testuser"
        assert token_data.role == UserRole.CUSTOMER
        assert token_data.token_type == TokenType.ACCESS
    
    def test_decode_invalid_token(self):
        """Test decoding invalid token raises exception"""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            decode_token(invalid_token)
        
        assert exc_info.value.status_code == 401
    
    def test_decode_expired_token(self):
        """Test decoding expired token"""
        user = User(
            user_id="123",
            username="testuser",
            email="test@example.com",
            role=UserRole.MERCHANT
        )
        
        # Create token that expires immediately
        token = create_access_token(user, expires_delta=timedelta(seconds=-1))
        
        # Decoding should work, but expiration check should fail
        token_data = decode_token(token)
        assert token_data.exp < datetime.utcnow()


class TestRoleChecker:
    """Test role-based access control"""
    
    def test_admin_role_checker(self):
        """Test admin role checker allows admin"""
        admin_user = User(
            user_id="1",
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN
        )
        
        checker = RoleChecker([UserRole.ADMIN])
        result = checker(admin_user)
        
        assert result == admin_user
    
    def test_admin_role_checker_denies_merchant(self):
        """Test admin role checker denies merchant"""
        merchant_user = User(
            user_id="2",
            username="merchant",
            email="merchant@example.com",
            role=UserRole.MERCHANT
        )
        
        checker = RoleChecker([UserRole.ADMIN])
        
        with pytest.raises(HTTPException) as exc_info:
            checker(merchant_user)
        
        assert exc_info.value.status_code == 403
    
    def test_multiple_allowed_roles(self):
        """Test role checker with multiple allowed roles"""
        merchant_user = User(
            user_id="2",
            username="merchant",
            email="merchant@example.com",
            role=UserRole.MERCHANT
        )
        
        checker = RoleChecker([UserRole.ADMIN, UserRole.MERCHANT])
        result = checker(merchant_user)
        
        assert result == merchant_user
    
    def test_customer_role_denied(self):
        """Test customer role denied for merchant-only endpoint"""
        customer_user = User(
            user_id="3",
            username="customer",
            email="customer@example.com",
            role=UserRole.CUSTOMER
        )
        
        checker = RoleChecker([UserRole.ADMIN, UserRole.MERCHANT])
        
        with pytest.raises(HTTPException) as exc_info:
            checker(customer_user)
        
        assert exc_info.value.status_code == 403
        assert 'not authorized' in exc_info.value.detail.lower()


class TestUserModel:
    """Test User model"""
    
    def test_create_user(self):
        """Test creating user instance"""
        user = User(
            user_id="123",
            username="testuser",
            email="test@example.com",
            role=UserRole.MERCHANT
        )
        
        assert user.user_id == "123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.MERCHANT
        assert user.is_active is True
    
    def test_user_inactive(self):
        """Test creating inactive user"""
        user = User(
            user_id="123",
            username="testuser",
            email="test@example.com",
            role=UserRole.CUSTOMER,
            is_active=False
        )
        
        assert user.is_active is False


class TestTokenTypes:
    """Test different token types"""
    
    def test_access_token_type(self):
        """Test access token has correct type"""
        user = User(
            user_id="123",
            username="testuser",
            email="test@example.com",
            role=UserRole.MERCHANT
        )
        
        token = create_access_token(user)
        token_data = decode_token(token)
        
        assert token_data.token_type == TokenType.ACCESS
    
    def test_refresh_token_type(self):
        """Test refresh token has correct type"""
        user = User(
            user_id="123",
            username="testuser",
            email="test@example.com",
            role=UserRole.MERCHANT
        )
        
        token = create_refresh_token(user)
        token_data = decode_token(token)
        
        assert token_data.token_type == TokenType.REFRESH


class TestSecurityFeatures:
    """Test security features"""
    
    def test_token_contains_no_sensitive_data(self):
        """Test that token doesn't contain password or sensitive data"""
        user = User(
            user_id="123",
            username="testuser",
            email="test@example.com",
            role=UserRole.MERCHANT
        )
        
        token = create_access_token(user)
        
        # Token should not contain email or other sensitive data
        assert 'test@example.com' not in token
        assert 'password' not in token.lower()
    
    def test_different_users_different_tokens(self):
        """Test different users get different tokens"""
        user1 = User(
            user_id="1",
            username="user1",
            email="user1@example.com",
            role=UserRole.MERCHANT
        )
        
        user2 = User(
            user_id="2",
            username="user2",
            email="user2@example.com",
            role=UserRole.MERCHANT
        )
        
        token1 = create_access_token(user1)
        token2 = create_access_token(user2)
        
        assert token1 != token2


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])

