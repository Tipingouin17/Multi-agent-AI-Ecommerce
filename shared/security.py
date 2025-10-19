"""
Security utilities for the multi-agent system.

This module provides security-related functionality including:
- Secret management
- Input validation
- Encryption/decryption
- Token generation
"""

import os
import secrets
import hashlib
import hmac
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64


class SecretManager:
    """Manages encryption and decryption of secrets."""
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize secret manager.
        
        Args:
            master_key: Master encryption key (will use env var if not provided)
        """
        if master_key is None:
            master_key = os.getenv('SECRET_KEY', self._generate_key())
        
        # Derive encryption key from master key
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'multi_agent_ecommerce_salt',  # In production, use random salt
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        self.cipher = Fernet(key)
    
    @staticmethod
    def _generate_key() -> str:
        """Generate a random encryption key."""
        return secrets.token_urlsafe(32)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.
        
        Args:
            plaintext: String to encrypt
        
        Returns:
            Encrypted string (base64 encoded)
        """
        encrypted_bytes = self.cipher.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted_bytes).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a ciphertext string.
        
        Args:
            ciphertext: Encrypted string (base64 encoded)
        
        Returns:
            Decrypted plaintext string
        """
        encrypted_bytes = base64.urlsafe_b64decode(ciphertext.encode())
        decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
        return decrypted_bytes.decode()
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using SHA-256.
        
        Args:
            password: Password to hash
        
        Returns:
            Hashed password (hex encoded)
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Password to verify
            hashed: Hashed password to compare against
        
        Returns:
            True if password matches, False otherwise
        """
        return self.hash_password(password) == hashed


class MessageSigner:
    """Signs and verifies message integrity using HMAC."""
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize message signer.
        
        Args:
            secret_key: Secret key for signing (will use env var if not provided)
        """
        if secret_key is None:
            secret_key = os.getenv('SECRET_KEY', secrets.token_urlsafe(32))
        self.secret_key = secret_key.encode()
    
    def sign(self, message: str) -> str:
        """
        Sign a message using HMAC-SHA256.
        
        Args:
            message: Message to sign
        
        Returns:
            Message signature (hex encoded)
        """
        return hmac.new(
            self.secret_key,
            message.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify(self, message: str, signature: str) -> bool:
        """
        Verify a message signature.
        
        Args:
            message: Original message
            signature: Signature to verify
        
        Returns:
            True if signature is valid, False otherwise
        """
        expected_signature = self.sign(message)
        return hmac.compare_digest(expected_signature, signature)


class TokenGenerator:
    """Generates secure random tokens."""
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """
        Generate a secure random token.
        
        Args:
            length: Length of the token in bytes
        
        Returns:
            URL-safe token string
        """
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_api_key() -> str:
        """
        Generate an API key.
        
        Returns:
            API key string
        """
        return f"mak_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def generate_session_id() -> str:
        """
        Generate a session ID.
        
        Returns:
            Session ID string
        """
        return f"sess_{secrets.token_urlsafe(24)}"


class InputValidator:
    """Validates and sanitizes user input."""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """
        Sanitize a string input.
        
        Args:
            value: String to sanitize
            max_length: Maximum allowed length
        
        Returns:
            Sanitized string
        
        Raises:
            ValueError: If input is invalid
        """
        if not isinstance(value, str):
            raise ValueError("Input must be a string")
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Trim whitespace
        value = value.strip()
        
        # Check length
        if len(value) > max_length:
            raise ValueError(f"Input exceeds maximum length of {max_length}")
        
        return value
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email address to validate
        
        Returns:
            True if valid, False otherwise
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
        
        Returns:
            True if valid, False otherwise
        """
        import re
        pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def sanitize_sql_input(value: str) -> str:
        """
        Sanitize input to prevent SQL injection.
        
        Note: This is a basic sanitization. Always use parameterized queries.
        
        Args:
            value: Input to sanitize
        
        Returns:
            Sanitized input
        """
        # Remove common SQL injection patterns
        dangerous_patterns = [
            '--', ';--', '/*', '*/', 'xp_', 'sp_', 
            'exec', 'execute', 'drop', 'delete', 'insert', 'update'
        ]
        
        sanitized = value
        for pattern in dangerous_patterns:
            sanitized = sanitized.replace(pattern, '')
        
        return sanitized


# Global instances
_secret_manager: Optional[SecretManager] = None
_message_signer: Optional[MessageSigner] = None


def get_secret_manager() -> SecretManager:
    """Get or create global secret manager instance."""
    global _secret_manager
    if _secret_manager is None:
        _secret_manager = SecretManager()
    return _secret_manager


def get_message_signer() -> MessageSigner:
    """Get or create global message signer instance."""
    global _message_signer
    if _message_signer is None:
        _message_signer = MessageSigner()
    return _message_signer

