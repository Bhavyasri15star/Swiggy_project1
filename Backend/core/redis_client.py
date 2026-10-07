import os

import redis
from redis.backoff import NoBackoff
from redis.retry import Retry

# Short timeouts, zero retries — same reasoning as main.py's own Redis
# client: this environment's Redis (WSL-hosted) has repeatedly gone down,
# and without this, a caller that fails open on a RedisError (e.g.
# RateLimitMiddleware) still blocks for redis-py's default TCP timeout
# (several seconds) before it gets to fail open, rather than failing fast.
pool = redis.ConnectionPool(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", "6379")),
    db=0,
    decode_responses=True,
    max_connections=20,
    socket_connect_timeout=2,
    socket_timeout=2,
    retry=Retry(NoBackoff(), retries=0),
    retry_on_error=[],
)

def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=pool)