import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import redis
from core.redis_client import get_redis


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time-ms"] = f"{duration_ms:.2f}"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.limit = limit
        self.window = window_seconds

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        key = f"ratelimit:{client_ip}"

        try:
            r = get_redis()
            current = r.incr(key)
            if current == 1:
                r.expire(key, self.window)
        except redis.exceptions.RedisError:
            # Same philosophy as main.py's _cache_get/set: Redis is what
            # enforces this, not what the API depends on to function. A
            # dead Redis should degrade to "no rate limiting" (fail open),
            # not take down every request with an unhandled 500 — this
            # runs outside FastAPI's own exception handlers (middleware
            # wraps around them), so an uncaught error here would bypass
            # those entirely and fall through to Starlette's raw response.
            return await call_next(request)

        if current > self.limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
            )

        return await call_next(request)
