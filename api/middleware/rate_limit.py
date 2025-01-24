from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from redis.asyncio import Redis
from clarity.config.settings import settings
from clarity.utils.monitoring.metrics import rate_limit_counter, rate_limit_exceeded
import structlog

logger = structlog.get_logger()

class RateLimiter:
    """
    Rate limiting implementation using Redis sliding window counter.
    Supports different rate limits per user and endpoint.
    """
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.default_rate_limits = {
            "authenticated": {
                "window_size": 60,  # 1 minute
                "max_requests": 100
            },
            "anonymous": {
                "window_size": 60,
                "max_requests": 30
            },
            "api_key": {
                "window_size": 60,
                "max_requests": 300
            }
        }
        
        # Endpoint-specific rate limits
        self.endpoint_limits = {
            "/api/v1/insights": {
                "window_size": 60,
                "max_requests": 50
            },
            "/api/v1/analysis": {
                "window_size": 300,  # 5 minutes
                "max_requests": 10
            }
        }
    
    async def is_rate_limited(
        self, 
        key: str, 
        window_size: int,
        max_requests: int
    ) -> Tuple[bool, int, int]:
        """
        Check if request should be rate limited using sliding window counter.
        
        Args:
            key: Unique identifier for the rate limit bucket
            window_size: Time window in seconds
            max_requests: Maximum number of requests allowed in window
            
        Returns:
            Tuple of (is_limited, remaining_requests, retry_after)
        """
        current_time = int(datetime.utcnow().timestamp())
        window_start = current_time - window_size
        
        async with self.redis.pipeline() as pipe:
            try:
                # Remove old entries outside current window
                await pipe.zremrangebyscore(key, 0, window_start)
                
                # Count requests in current window
                await pipe.zcard(key)
                
                # Add current request
                await pipe.zadd(key, {str(current_time): current_time})
                
                # Set expiry on bucket
                await pipe.expire(key, window_size)
                
                results = await pipe.execute()
                current_requests = results[1]
                
                is_limited = current_requests >= max_requests
                remaining = max(0, max_requests - current_requests)
                retry_after = window_size - (current_time - window_start)
                
                return is_limited, remaining, retry_after
                
            except Exception as e:
                logger.error(
                    "rate_limit.redis.error",
                    error=str(e),
                    key=key
                )
                return False, max_requests, 0
    
    def get_rate_limit_config(
        self,
        request: Request,
        user_type: str = "anonymous"
    ) -> Dict[str, int]:
        """Get rate limit configuration for request."""
        # Check for endpoint-specific limits
        for endpoint, limits in self.endpoint_limits.items():
            if request.url.path.startswith(endpoint):
                return limits
        
        # Fall back to default limits based on user type
        return self.default_rate_limits.get(
            user_type,
            self.default_rate_limits["anonymous"]
        )

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting requests based on IP, user ID, or API key.
    Uses Redis for distributed rate limit tracking.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        redis_client: Optional[Redis] = None,
        enabled: bool = True
    ):
        super().__init__(app)
        self.enabled = enabled
        self.redis_client = redis_client or Redis.from_url(settings.REDIS_URI)
        self.rate_limiter = RateLimiter(self.redis_client)
    
    async def dispatch(
        self,
        request: Request,
        call_next
    ) -> Response:
        """Process request and apply rate limiting."""
        if not self.enabled:
            return await call_next(request)
            
        try:
            # Get client identifier (IP, user ID, or API key)
            client_id = self._get_client_id(request)
            user_type = self._get_user_type(request)
            
            # Get rate limit config
            rate_limit_config = self.rate_limiter.get_rate_limit_config(
                request,
                user_type
            )
            
            # Generate rate limit key
            rate_limit_key = f"ratelimit:{client_id}:{request.url.path}"
            
            # Check rate limit
            is_limited, remaining, retry_after = await self.rate_limiter.is_rate_limited(
                rate_limit_key,
                rate_limit_config["window_size"],
                rate_limit_config["max_requests"]
            )
            
            # Update metrics
            rate_limit_counter.labels(
                path=request.url.path,
                method=request.method,
                user_type=user_type
            ).inc()
            
            if is_limited:
                rate_limit_exceeded.labels(
                    path=request.url.path,
                    method=request.method,
                    user_type=user_type
                ).inc()
                
                return Response(
                    content={"error": "Rate limit exceeded"},
                    status_code=429,
                    headers={
                        "X-RateLimit-Limit": str(rate_limit_config["max_requests"]),
                        "X-RateLimit-Remaining": str(remaining),
                        "X-RateLimit-Reset": str(retry_after),
                        "Retry-After": str(retry_after)
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers to response
            response.headers["X-RateLimit-Limit"] = str(rate_limit_config["max_requests"])
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(retry_after)
            
            return response
            
        except Exception as e:
            logger.error(
                "rate_limit.middleware.error",
                error=str(e),
                path=request.url.path,
                method=request.method
            )
            return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier from request."""
        # Try to get user ID from request state
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"
            
        # Try to get API key from headers
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"apikey:{api_key}"
            
        # Fall back to IP address
        return f"ip:{request.client.host}"
    
    def _get_user_type(self, request: Request) -> str:
        """Determine user type for rate limiting."""
        if hasattr(request.state, "user_id"):
            return "authenticated"
        elif request.headers.get("X-API-Key"):
            return "api_key"
        return "anonymous"
