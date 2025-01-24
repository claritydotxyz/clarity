from typing import Optional
import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from clarity.core.cache import RedisCache
import structlog

logger = structlog.get_logger()

class CacheMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, cache_instance: Optional[RedisCache] = None):
        super().__init__(app)
        self.cache = cache_instance or RedisCache()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method != "GET":
            return await call_next(request)
        
        cache_key = self._generate_cache_key(request)
        cached_response = await self.cache.get(cache_key)
        
        if cached_response:
            return Response(
                content=cached_response,
                media_type="application/json",
                headers={"X-Cache": "HIT"}
            )
        
        response = await call_next(request)
        
        if response.status_code == 200:
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            await self.cache.set(
                cache_key,
                response_body,
                expire=300  # 5 minutes default TTL
            )
            
            return Response(
                content=response_body,
                media_type=response.media_type,
                status_code=response.status_code,
                headers={"X-Cache": "MISS"}
            )
        
        return response
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate a unique cache key for the request."""
        key_parts = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items())),
            request.headers.get("authorization", "")
        ]
        return ":".join(key_parts)
