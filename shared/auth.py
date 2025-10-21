"""
Authentication and Authorization Module
Provides JWT-based authentication and role-based access control (RBAC)
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel


# Configuration
SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET environment variable must be set")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Security
security = HTTPBearer()


class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    MERCHANT = "merchant"
    CUSTOMER = "customer"
    AGENT = "agent"  # For inter-agent communication


class TokenType(str, Enum):
    """Token types"""
    ACCESS = "access"
    REFRESH = "refresh"


class User(BaseModel):
    """User model"""
    user_id: str
    username: str
    email: str
    role: UserRole
    is_active: bool = True
    
    class Config:
        from_attributes = True


class TokenData(BaseModel):
    """Token payload data"""
    user_id: str
    username: str
    role: UserRole
    token_type: TokenType
    exp: datetime


class Token(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(user: User, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role.value,
        "token_type": TokenType.ACCESS.value,
        "exp": expire
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(user: User) -> str:
    """Create JWT refresh token"""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role.value,
        "token_type": TokenType.REFRESH.value,
        "exp": expire
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_tokens(user: User) -> Token:
    """Create both access and refresh tokens"""
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


def decode_token(token: str) -> TokenData:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        username: str = payload.get("username")
        role: str = payload.get("role")
        token_type: str = payload.get("token_type")
        exp: int = payload.get("exp")
        
        if user_id is None or username is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        return TokenData(
            user_id=user_id,
            username=username,
            role=UserRole(role),
            token_type=TokenType(token_type),
            exp=datetime.fromtimestamp(exp)
        )
    
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    Usage: current_user = Depends(get_current_user)
    """
    token = credentials.credentials
    token_data = decode_token(token)
    
    # Verify token type
    if token_data.token_type != TokenType.ACCESS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    # Check if token is expired
    if token_data.exp < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    
    # In a real application, you would fetch the user from database here
    # For now, we return the user from token data
    user = User(
        user_id=token_data.user_id,
        username=token_data.username,
        email=f"{token_data.username}@example.com",  # Would come from DB
        role=token_data.role,
        is_active=True
    )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


class RoleChecker:
    """
    Dependency class to check if user has required role(s)
    Usage: Depends(RoleChecker([UserRole.ADMIN, UserRole.MERCHANT]))
    """
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{user.role}' is not authorized for this operation"
            )
        return user


# Convenience role checkers
require_admin = RoleChecker([UserRole.ADMIN])
require_merchant = RoleChecker([UserRole.ADMIN, UserRole.MERCHANT])
require_customer = RoleChecker([UserRole.ADMIN, UserRole.CUSTOMER])
require_agent = RoleChecker([UserRole.AGENT])


def create_api_key(user: User, name: str, expires_days: int = 365) -> str:
    """
    Create a long-lived API key for programmatic access
    Used for agent-to-agent communication
    """
    expire = datetime.utcnow() + timedelta(days=expires_days)
    
    to_encode = {
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role.value,
        "token_type": "api_key",
        "key_name": name,
        "exp": expire
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Example usage in FastAPI endpoints:
"""
from shared.auth import get_current_user, require_admin, User

@app.get("/api/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.username}"}

@app.get("/api/admin-only")
async def admin_only_route(current_user: User = Depends(require_admin)):
    return {"message": "Admin access granted"}

@app.post("/api/products")
async def create_product(
    product_data: dict,
    current_user: User = Depends(require_merchant)
):
    # Only admins and merchants can create products
    return {"message": "Product created"}
"""

