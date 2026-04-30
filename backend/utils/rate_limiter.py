"""
Rate Limiting Middleware
Implements request rate limiting to prevent brute force attacks
"""

from fastapi import Request, HTTPException, status
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
        self._cleanup_task = None
    
    async def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed for identifier
        
        Args:
            identifier: Unique identifier (e.g., IP address, user ID)
            
        Returns:
            True if request allowed, False if rate limited
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # Check if limit exceeded
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # Record new request
        self.requests[identifier].append(now)
        return True
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier"""
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        valid_requests = [
            req_time for req_time in self.requests.get(identifier, [])
            if req_time > window_start
        ]
        
        return max(0, self.max_requests - len(valid_requests))


# Global rate limiters for different endpoints
login_limiter = RateLimiter(max_requests=5, window_seconds=300)  # 5 per 5 minutes
upload_limiter = RateLimiter(max_requests=10, window_seconds=3600)  # 10 per hour
api_limiter = RateLimiter(max_requests=100, window_seconds=60)  # 100 per minute


async def check_rate_limit(request: Request, limiter: RateLimiter, identifier_key: str = "ip") -> None:
    """
    Check if request is within rate limit
    
    Args:
        request: FastAPI Request
        limiter: RateLimiter instance
        identifier_key: How to identify the requester ("ip", "user_id", etc.)
        
    Raises:
        HTTPException: If rate limited
    """
    # Get identifier
    if identifier_key == "ip":
        identifier = request.client.host
    elif identifier_key == "user_id":
        # Extract from token/session if available
        identifier = getattr(request.state, "user_id", request.client.host)
    else:
        identifier = request.client.host
    
    # Check limit
    if not await asyncio.to_thread(limiter.is_allowed, identifier):
        remaining = limiter.get_remaining(identifier)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Try again in {limiter.window_seconds} seconds."
        )
