"""
Rate Limiting Module
Provides rate limiting for API endpoints to prevent abuse
"""

import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse


# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[
        os.getenv("DEFAULT_RATE_LIMIT", "100/minute"),
        os.getenv("DEFAULT_RATE_LIMIT_HOURLY", "1000/hour")
    ],
    storage_uri=os.getenv("REDIS_URL", "redis://localhost:6379"),
    strategy="fixed-window"
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors
    """
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": f"Too many requests. Please try again later.",
            "retry_after": exc.detail
        },
        headers={
            "Retry-After": str(exc.detail)
        }
    )


# Rate limit decorators for different endpoint types
def rate_limit_strict(func):
    """Strict rate limit: 10 requests per minute"""
    return limiter.limit("10/minute")(func)


def rate_limit_moderate(func):
    """Moderate rate limit: 50 requests per minute"""
    return limiter.limit("50/minute")(func)


def rate_limit_relaxed(func):
    """Relaxed rate limit: 100 requests per minute"""
    return limiter.limit("100/minute")(func)


# Example usage:
"""
from fastapi import FastAPI, Request
from shared.rate_limit import limiter, rate_limit_exceeded_handler, rate_limit_strict

app = FastAPI()

# Add rate limiter to app state
app.state.limiter = limiter

# Add exception handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Use on endpoints
@app.get("/api/data")
@limiter.limit("100/minute")
async def get_data(request: Request):
    return {"data": "value"}

@app.post("/api/login")
@limiter.limit("5/minute")  # Strict limit for login attempts
async def login(request: Request, credentials: dict):
    return {"token": "..."}
"""

