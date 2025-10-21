"""
Secured API Main Entry Point with Authentication and Rate Limiting
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from slowapi.errors import RateLimitExceeded

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.auth import (
    get_current_user, 
    require_admin, 
    require_merchant,
    User,
    UserRole,
    create_tokens,
    verify_password
)
from shared.rate_limit import limiter, rate_limit_exceeded_handler

# Database configuration
DB_CONFIG = {
    "host": os.environ.get('DATABASE_HOST', 'localhost'),
    "port": int(os.environ.get('DATABASE_PORT', '5432')),
    "database": os.environ.get('DATABASE_NAME', 'ecommerce'),
    "user": os.environ.get('DATABASE_USER', 'postgres'),
    "password": os.environ.get('DATABASE_PASSWORD')
}

# Validate required environment variables
if not DB_CONFIG["password"]:
    raise ValueError("DATABASE_PASSWORD environment variable must be set")

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent E-commerce API",
    description="Secured API with authentication and rate limiting",
    version="2.0.0"
)

# Add rate limiter to app state
app.state.limiter = limiter

# Add exception handler for rate limiting
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS middleware with configurable origins
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", 
    "http://localhost:3000,http://localhost:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)


# Database connection helper
def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


# Models
class LoginRequest(BaseModel):
    username: str
    password: str


class Product(BaseModel):
    name: str
    description: str
    price: float
    category: str
    stock_quantity: int


class ProductResponse(BaseModel):
    product_id: str
    name: str
    description: str
    price: float
    category: str
    stock_quantity: int
    created_at: datetime


# ============================================================================
# PUBLIC ENDPOINTS (No authentication required)
# ============================================================================

@app.get("/api/health")
@limiter.limit("100/minute")
async def health_check(request: Request):
    """Health check endpoint - no authentication required"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }


@app.post("/api/auth/login")
@limiter.limit("5/minute")  # Strict rate limit for login attempts
async def login(request: Request, credentials: LoginRequest):
    """
    Login endpoint - returns JWT tokens
    Rate limited to prevent brute force attacks
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch user from database
        cursor.execute(
            "SELECT user_id, username, email, password_hash, role, is_active FROM users WHERE username = %s",
            (credentials.username,)
        )
        user_data = cursor.fetchone()
        
        if not user_data:
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )
        
        # Verify password
        if not verify_password(credentials.password, user_data['password_hash']):
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )
        
        # Check if user is active
        if not user_data['is_active']:
            raise HTTPException(
                status_code=403,
                detail="User account is inactive"
            )
        
        # Create user object
        user = User(
            user_id=str(user_data['user_id']),
            username=user_data['username'],
            email=user_data['email'],
            role=UserRole(user_data['role']),
            is_active=user_data['is_active']
        )
        
        # Generate tokens
        tokens = create_tokens(user)
        
        cursor.close()
        conn.close()
        
        return {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "token_type": tokens.token_type,
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


# ============================================================================
# PROTECTED ENDPOINTS (Authentication required)
# ============================================================================

@app.get("/api/me")
@limiter.limit("100/minute")
async def get_current_user_info(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role.value,
        "is_active": current_user.is_active
    }


@app.get("/api/products")
@limiter.limit("100/minute")
async def get_products(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get all products - requires authentication"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT product_id, name, description, price, category, 
                   stock_quantity, created_at 
            FROM products 
            ORDER BY created_at DESC 
            LIMIT %s OFFSET %s
            """,
            (limit, skip)
        )
        products = cursor.fetchall()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as count FROM products")
        total = cursor.fetchone()['count']
        
        cursor.close()
        conn.close()
        
        return {
            "products": products,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/products")
@limiter.limit("50/minute")
async def create_product(
    request: Request,
    product: Product,
    current_user: User = Depends(require_merchant)
):
    """Create new product - requires merchant or admin role"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO products (name, description, price, category, stock_quantity)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING product_id, name, description, price, category, 
                      stock_quantity, created_at
            """,
            (product.name, product.description, product.price, 
             product.category, product.stock_quantity)
        )
        new_product = cursor.fetchone()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "message": "Product created successfully",
            "product": new_product
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products/{product_id}")
@limiter.limit("100/minute")
async def get_product(
    request: Request,
    product_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get product by ID - requires authentication"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT product_id, name, description, price, category, 
                   stock_quantity, created_at 
            FROM products 
            WHERE product_id = %s
            """,
            (product_id,)
        )
        product = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return product
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/orders")
@limiter.limit("100/minute")
async def get_orders(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get orders - filters by user role"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Customers can only see their own orders
        if current_user.role == UserRole.CUSTOMER:
            cursor.execute(
                """
                SELECT order_id, customer_id, status, total_amount, created_at
                FROM orders
                WHERE customer_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (current_user.user_id, limit, skip)
            )
        else:
            # Admins and merchants can see all orders
            cursor.execute(
                """
                SELECT order_id, customer_id, status, total_amount, created_at
                FROM orders
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (limit, skip)
            )
        
        orders = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "orders": orders,
            "skip": skip,
            "limit": limit
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/users")
@limiter.limit("50/minute")
async def get_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin)
):
    """Get all users - admin only"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT user_id, username, email, role, is_active, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (limit, skip)
        )
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "users": users,
            "skip": skip,
            "limit": limit
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics/dashboard")
@limiter.limit("50/minute")
async def get_dashboard_metrics(
    request: Request,
    current_user: User = Depends(require_admin)
):
    """Get dashboard metrics - admin only"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get various metrics
        cursor.execute("SELECT COUNT(*) as count FROM products")
        product_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM orders")
        order_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM users")
        user_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT SUM(total_amount) as total FROM orders WHERE status = 'completed'")
        revenue = cursor.fetchone()['total'] or 0
        
        cursor.close()
        conn.close()
        
        return {
            "products": product_count,
            "orders": order_count,
            "users": user_count,
            "revenue": float(revenue),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_secured:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

