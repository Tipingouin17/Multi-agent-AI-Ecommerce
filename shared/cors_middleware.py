"""
CORS Middleware for Multi-Agent E-commerce Platform

This module provides CORS (Cross-Origin Resource Sharing) configuration
for all agents to enable dashboard integration.

Usage:
    from shared.cors_middleware import add_cors_middleware
    
    app = FastAPI()
    add_cors_middleware(app)
"""

from fastapi.middleware.cors import CORSMiddleware
from typing import List


def add_cors_middleware(app, 
                       allowed_origins: List[str] = None,
                       allow_credentials: bool = True,
                       allowed_methods: List[str] = None,
                       allowed_headers: List[str] = None):
    """
    Add CORS middleware to a FastAPI application.
    
    This enables the dashboard (running on a different port) to communicate
    with the agent APIs.
    
    Args:
        app: FastAPI application instance
        allowed_origins: List of allowed origins. Defaults to common development origins.
        allow_credentials: Whether to allow credentials (cookies, authorization headers)
        allowed_methods: List of allowed HTTP methods
        allowed_headers: List of allowed HTTP headers
    """
    
    # Default allowed origins for development and production
    if allowed_origins is None:
        allowed_origins = [
            "http://localhost:3000",      # React default
            "http://localhost:5173",      # Vite default
            "http://localhost:8080",      # Alternative dev server
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8080",
            # Add production domains here when deploying
            # "https://yourdomain.com",
        ]
    
    # Default allowed methods (all common HTTP methods)
    if allowed_methods is None:
        allowed_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    
    # Default allowed headers
    if allowed_headers is None:
        allowed_headers = [
            "Content-Type",
            "Authorization",
            "Accept",
            "Origin",
            "User-Agent",
            "DNT",
            "Cache-Control",
            "X-Requested-With",
        ]
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=allow_credentials,
        allow_methods=allowed_methods,
        allow_headers=allowed_headers,
        expose_headers=["Content-Length", "Content-Type"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )
    
    print(f"[CORS] Enabled for origins: {', '.join(allowed_origins)}")


def add_permissive_cors(app):
    """
    Add permissive CORS configuration (allows all origins).
    
    WARNING: Only use this in development! In production, specify exact origins.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers
    )
    
    print("[CORS] WARNING: Permissive CORS enabled (allows all origins)")

